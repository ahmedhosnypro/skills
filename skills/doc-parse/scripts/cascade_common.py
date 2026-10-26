#!/usr/bin/env python3
"""crop-cascade core: config, logging, retry ladder, parse + chat lanes."""

from __future__ import annotations

import json
import logging
import random
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIG_NAME = ".doc-parse-config"
CONFIG_FIELDS = ("endpoint", "api_key", "model")
DEFAULT_MAX_OUTPUT_TOKENS = 9000
DEFAULT_PARSE_TIMEOUT = 150.0
DEFAULT_CHAT_TIMEOUT = 60.0
CHAT_MAX_TOKENS = 512
CHAT_RETRY_TOKENS = 2048
CHAT_TEMPERATURE = 0.2
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC = b"\xff\xd8\xff"
BODY_SNIPPET = 2048
FATAL_STATUSES = (400, 401, 403, 404)

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_CONFIG = 3
EXIT_INPUT = 4
EXIT_FULL = 5
EXIT_PARTIAL = 6
EXIT_COMPOSE = 7


def die(message: str, code: int = 1) -> None:
    print(f"error: {message}", file=sys.stderr)
    sys.exit(code)


def check_image(path: Path) -> str:
    """Magic-byte + PIL integrity gate; a bad file is a caller mistake."""
    data = path.read_bytes()[:24]
    if data.startswith(PNG_MAGIC):
        mime = "image/png"
    elif data.startswith(JPEG_MAGIC):
        mime = "image/jpeg"
    else:
        die(f"{path.name}: not an image/png or image/jpeg file", EXIT_INPUT)
    try:
        from PIL import Image  # type: ignore

        with Image.open(path) as image:
            image.verify()
    except ImportError:
        pass
    except Exception as exc:  # noqa: BLE001 — any PIL failure is a bad input
        die(f"{path.name}: failed the image integrity check ({exc})", EXIT_INPUT)
    return mime


def load_config() -> dict:
    """Parse fields are required (exit 3); chat fields are optional —
    an unusable chat config degrades the run instead of killing it."""
    path = HERE / CONFIG_NAME
    if not path.is_file():
        die(f"missing config file: {path}", EXIT_CONFIG)
    try:
        raw = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        die(f"{CONFIG_NAME}: not valid JSON ({exc})", EXIT_CONFIG)
    if not isinstance(raw, dict):
        die(f"{CONFIG_NAME}: must be a JSON object", EXIT_CONFIG)
    missing = [field for field in CONFIG_FIELDS if not raw.get(field)]
    if missing:
        die(f"{CONFIG_NAME}: missing required field(s): {', '.join(missing)}", EXIT_CONFIG)
    endpoint = str(raw["endpoint"])
    if not endpoint.startswith(("http://", "https://")):
        die(f"{CONFIG_NAME}: 'endpoint' must be an http(s) URL", EXIT_CONFIG)
    tokens = raw.get("max_output_tokens", DEFAULT_MAX_OUTPUT_TOKENS)
    if isinstance(tokens, bool) or not isinstance(tokens, int) or tokens <= 0:
        die(f"{CONFIG_NAME}: 'max_output_tokens' must be a positive integer", EXIT_CONFIG)
    config = {field: str(raw[field]) for field in CONFIG_FIELDS}
    config["max_output_tokens"] = tokens
    config.update(chat_config(raw))
    return config


def chat_config(raw: dict) -> dict:
    """Optional chat lane: chat_endpoint + chat_model required together;
    chat_api_key falls back to the parse api_key. A gap disables the lane."""
    endpoint = raw.get("chat_endpoint")
    model = raw.get("chat_model")
    if not endpoint and not model:
        return {"chat_ready": False, "chat_reason": "no chat fields in config"}
    if not endpoint or not model:
        return {"chat_ready": False, "chat_reason": "chat lane needs endpoint AND model"}
    if not str(endpoint).startswith(("http://", "https://")):
        return {"chat_ready": False, "chat_reason": "chat_endpoint must be an http(s) URL"}
    key = str(raw.get("chat_api_key") or raw.get("api_key") or "")
    if not key:
        return {"chat_ready": False, "chat_reason": "no api_key for the chat lane"}
    return {"chat_ready": True, "chat_reason": "", "chat_endpoint": str(endpoint),
            "chat_model": str(model), "chat_api_key": key}


def setup_logging(outdir: Path, source: str) -> logging.Logger:
    """run.log receives everything except parse payloads; stderr warnings."""
    logger = logging.getLogger("crop_cascade")
    logger.setLevel(logging.DEBUG)
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
    if (outdir / "run.log").exists():
        print(f"warning: {outdir} already holds a run.log — appending",
              file=sys.stderr)
    file_handler = logging.FileHandler(outdir / "run.log")
    file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(file_handler)
    stream = logging.StreamHandler(sys.stderr)
    stream.setLevel(logging.WARNING)
    logger.addHandler(stream)
    logger.info("=== crop_cascade run: %s ===", source)
    return logger


class FatalApiError(Exception):
    """HTTP 400/401/403/404 — a config/operator error; retrying cannot help."""


class ApiCallError(Exception):
    """Retry ladder exhausted or an unusable response shape; .payload holds the raw response for banking."""

    def __init__(self, message: str, payload=None):
        super().__init__(message)
        self.payload = payload


def _retry_delay(attempt: int) -> float:
    return 2.0 * (2 ** attempt) + random.uniform(0.0, 1.0)


def post_with_retries(url: str, headers: dict, body: bytes, timeout: float,
                      attempts: int, lane: str, log: logging.Logger) -> dict:
    """Shared retry ladder for both lanes: connection errors, timeouts,
    HTTP 429/5xx, and undecodable bodies retry with exponential backoff;
    400/401/403/404 raise FatalApiError immediately."""
    hint = "fix the config or credentials — retrying cannot help"
    last = "unknown failure"
    for attempt in range(attempts):
        started = time.monotonic()
        try:
            request = urllib.request.Request(
                url, data=body, headers=headers, method="POST")
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read().decode()
            log.info("%s call attempt=%d latency=%.1fs url=%s bytes=%d",
                     lane, attempt + 1, time.monotonic() - started,
                     url, len(body))
            return json.loads(raw)
        except urllib.error.HTTPError as exc:
            snippet = exc.read(BODY_SNIPPET).decode(errors="replace")
            log.info("%s call attempt=%d HTTP=%d latency=%.1fs url=%s",
                     lane, attempt + 1, exc.code,
                     time.monotonic() - started, url)
            if exc.code in FATAL_STATUSES:
                raise FatalApiError(
                    f"{lane}: HTTP {exc.code} on {url} — {snippet[:500]}. {hint}")
            last = f"HTTP {exc.code}: {snippet}"
        except (urllib.error.URLError, TimeoutError, ConnectionError,
                OSError) as exc:
            last = f"{type(exc).__name__}: {exc}"
            log.info("%s call attempt=%d transport failure latency=%.1fs (%s)",
                     lane, attempt + 1, time.monotonic() - started, last)
        except json.JSONDecodeError as exc:
            last = f"undecodable response body ({exc})"
        if attempt < attempts - 1:
            delay = _retry_delay(attempt)
            log.warning("%s attempt %d/%d failed (%s) — retrying in %.1fs",
                        lane, attempt + 1, attempts, last, delay)
            time.sleep(delay)
    raise ApiCallError(
        f"{lane}: giving up after {attempts} attempts — last failure: {last}")


def _multipart_body(image: Path, mime: str, model: str, options: dict) -> bytes:
    """The parse endpoint's frozen multipart contract (model/document/options)."""
    boundary = "docparse-cascade-4e9b"
    body = bytearray()
    body += (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="model"\r\n\r\n'
        + model + "\r\n"
    ).encode()
    body += (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="document"; '
        f'filename="{image.name}"\r\n'
        f"Content-Type: {mime}\r\n\r\n"
    ).encode()
    body += image.read_bytes()
    body += b"\r\n"
    body += (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="options"\r\n'
        "Content-Type: application/json\r\n\r\n"
        + json.dumps(options) + "\r\n"
    ).encode()
    body += f"--{boundary}--\r\n".encode()
    return bytes(body)


def parse_call(image: Path, mime: str, config: dict, tokens: int,
               timeout: float, attempts: int, log: logging.Logger) -> dict:
    """One parse-lane POST for one image; returns the endpoint's JSON body."""
    options = {"decoding": {"max_output_tokens": tokens}}
    body = _multipart_body(image, mime, config["model"], options)
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Accept": "application/json",
        "Content-Type": f"multipart/form-data; boundary=docparse-cascade-4e9b",
    }
    return post_with_retries(
        config["endpoint"], headers, body, timeout, attempts, "parse", log)


def _chat_post(prompt_text: str, config: dict, timeout: float, attempts: int,
               log: logging.Logger, max_tokens: int) -> dict:
    payload = json.dumps({
        "model": config["chat_model"],
        "messages": [{"role": "user", "content": prompt_text}],
        "max_tokens": max_tokens,
        "temperature": CHAT_TEMPERATURE,
    }).encode()
    headers = {
        "Authorization": f"Bearer {config['chat_api_key']}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    url = config["chat_endpoint"].rstrip("/") + "/chat/completions"
    return post_with_retries(
        url, headers, payload, timeout, attempts, "chat", log)


def chat_call(prompt_text: str, config: dict, timeout: float, attempts: int,
              log: logging.Logger, max_tokens: int = CHAT_MAX_TOKENS) -> tuple:
    """One chat-completion escalation. Returns (content, raw_response).
    A reply that hit the token ceiling (finish_reason=length) is retried
    once at a larger budget before truncation reaches the caller."""
    while True:
        raw = _chat_post(prompt_text, config, timeout, attempts, log, max_tokens)
        content = None
        finish = None
        try:
            choice = raw["choices"][0]
            content = choice["message"]["content"]
            finish = choice.get("finish_reason")
        except (KeyError, IndexError, TypeError):
            pass
        if finish == "length" and max_tokens < CHAT_RETRY_TOKENS:
            log.warning(
                "chat reply hit the %d-token ceiling — retrying once at %d",
                max_tokens, CHAT_RETRY_TOKENS)
            max_tokens = CHAT_RETRY_TOKENS
            continue
        if isinstance(content, str):
            return content, raw
        raise ApiCallError(
            f"chat reply carried no content string "
            f"(finish_reason={finish!r})", payload=raw)


def probe_chat(config: dict, timeout: float, log: logging.Logger) -> bool:
    """Cheap probe before any real escalation; a failure degrades the run."""
    try:
        content, _ = chat_call(
            "Reply with the single word OK.", config, timeout, 1, log, 16)
    except (ApiCallError, FatalApiError) as exc:
        log.warning("chat lane probe failed — running degraded: %s", exc)
        return False
    if "ok" not in content.strip().lower():
        log.warning("chat probe answered unexpectedly (%r) — degraded",
                    content[:80])
        return False
    log.info("chat lane probe OK (model=%s)", config["chat_model"])
    return True

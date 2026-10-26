#!/usr/bin/env python3
"""doc-parse — parse document images through the configured parse endpoint.

One lane: the endpoint, API key, and model all come from the
`.doc-parse-config` file NEXT TO THIS SCRIPT (JSON with the fields
"endpoint", "api_key", "model", plus an optional "max_output_tokens").
The script resolves the config itself, relative to its own file
location, so you invoke it from any working directory and NEVER read,
copy, or pass its values yourself. The config is runtime data: never
committed, never printed.

Wire contract: one multipart/form-data POST per page — a text part
`model` (omitted automatically for endpoints that reject it, e.g.
NVIDIA-direct invoke URLs), a file part `document`
(image/png | image/jpeg), an optional JSON text part `options` —
answered by the endpoint's JSON body
("content" plus "usage"). The surface's semantics live in the endpoint
operator's docs.

Outputs (per input image): <stem>.parse.md (the content) and
<stem>.parse.json (the full response) in the output directory.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from endpoint_rules import sends_model_part

HERE = Path(__file__).resolve().parent
CONFIG_NAME = ".doc-parse-config"
CONFIG_FIELDS = ("endpoint", "api_key", "model")
OPTIONAL_CONFIG_FIELDS = ("max_output_tokens",)
DEFAULT_MAX_OUTPUT_TOKENS = 9000
DEFAULT_TIMEOUT = 150.0
IMAGE_EXTS = {".png", ".jpg", ".jpeg"}
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC = b"\xff\xd8\xff"


def die(message: str, code: int = 1) -> None:
    print(f"error: {message}", file=sys.stderr)
    sys.exit(code)


def check_image(path: Path) -> str:
    """Magic-byte sanity (PIL when available): a zero-byte or
    non-image file is a caller mistake, never a parse verdict."""
    data = path.read_bytes()[:24]
    if data.startswith(PNG_MAGIC):
        mime = "image/png"
    elif data.startswith(JPEG_MAGIC):
        mime = "image/jpeg"
    else:
        die(f"{path}: not an image/png or image/jpeg file (magic bytes)")
    try:
        from PIL import Image  # type: ignore

        with Image.open(path) as image:
            image.verify()
    except ImportError:
        pass
    except Exception as exc:  # noqa: BLE001 — any PIL failure is a bad input
        die(f"{path}: failed the image integrity check ({exc})")
    return mime


def load_config() -> dict:
    path = HERE / CONFIG_NAME
    if not path.is_file():
        die(f"missing config file: {path} (fields: {', '.join(CONFIG_FIELDS)})")
    try:
        config = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        die(f"{path}: not valid JSON ({exc})")
    if not isinstance(config, dict):
        die(f"{path}: must be a JSON object")
    missing = [field for field in CONFIG_FIELDS if not config.get(field)]
    if missing:
        die(f"{path}: missing required field(s): {', '.join(missing)}")
    endpoint = str(config["endpoint"])
    if not endpoint.startswith(("http://", "https://")):
        die(f"{path}: 'endpoint' must be an http(s) URL")
    tokens = config.get("max_output_tokens", DEFAULT_MAX_OUTPUT_TOKENS)
    if isinstance(tokens, bool) or not isinstance(tokens, int) or tokens <= 0:
        die(f"{path}: 'max_output_tokens' must be a positive integer")
    resolved = {field: str(config[field]) for field in CONFIG_FIELDS}
    resolved["max_output_tokens"] = tokens
    return resolved


def parse_page(
    image: Path,
    mime: str,
    config: dict,
    options: dict,
    timeout: float,
) -> dict:
    boundary = "docparse-boundary-7f3a"
    body = bytearray()
    if sends_model_part(config["endpoint"]):
        body += (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="model"\r\n\r\n'
            + config["model"]
            + "\r\n"
        ).encode()
    body += (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="document"; filename="{image.name}"\r\n'
        f"Content-Type: {mime}\r\n\r\n"
    ).encode()
    body += image.read_bytes()
    body += b"\r\n"
    if options:
        body += (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="options"\r\n'
            "Content-Type: application/json\r\n\r\n"
            + json.dumps(options)
            + "\r\n"
        ).encode()
    body += f"--{boundary}--\r\n".encode()
    request = urllib.request.Request(
        config["endpoint"],
        data=bytes(body),
        headers={
            "Authorization": f"Bearer {config['api_key']}",
            "Accept": "application/json",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode())


def parse_one(
    image: Path,
    outdir: Path,
    config: dict,
    args: argparse.Namespace,
) -> tuple[Path, dict]:
    mime = check_image(image)
    tokens = (
        args.max_output_tokens
        if args.max_output_tokens is not None
        else config["max_output_tokens"]
    )
    options = {"decoding": {"max_output_tokens": tokens}}
    started = time.monotonic()
    result = parse_page(image, mime, config, options, args.timeout)
    elapsed = time.monotonic() - started
    content = result.get("content")
    if not isinstance(content, str):
        die(f"{image}: response carried no content string")
    stem = image.stem
    md_path = outdir / f"{stem}.parse.md"
    json_path = outdir / f"{stem}.parse.json"
    md_path.write_text(content)
    json_path.write_text(json.dumps(result, indent=2))
    usage = result.get("usage") or {}
    print(
        f"{image.name}: {len(content)} chars, "
        f"{usage.get('output_tokens', '?')} out tokens, {elapsed:.1f}s "
        f"-> {md_path.name}"
    )
    return md_path, result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Parse document images through the configured parse endpoint.",
    )
    parser.add_argument("input", help="an image file or a directory of page images")
    parser.add_argument("-o", "--out", type=Path, help="output directory (default: the input's)")
    parser.add_argument(
        "--max-output-tokens", type=int, default=None,
        help="decoding.max_output_tokens override "
             "(default: the config's max_output_tokens, else "
             f"{DEFAULT_MAX_OUTPUT_TOKENS})",
    )
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    args = parser.parse_args()

    config = load_config()

    source = Path(args.input).expanduser().resolve()
    if not source.exists():
        die(f"{source}: no such file or directory")
    if source.is_dir():
        images = sorted(
            p for p in source.iterdir()
            if p.is_file() and p.suffix.lower() in IMAGE_EXTS
        )
        if not images:
            die(f"{source}: no image/png or image/jpeg files")
    else:
        images = [source]
    outdir = (args.out or (source if source.is_dir() else source.parent)) \
        .expanduser().resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    failures = 0
    for image in images:
        try:
            parse_one(image, outdir, config, args)
        except urllib.error.HTTPError as exc:
            detail = exc.read(2048).decode(errors="replace")
            print(f"{image.name}: HTTP {exc.code}: {detail}", file=sys.stderr)
            failures += 1
        except Exception as exc:  # noqa: BLE001 — one bad page never stops a batch
            print(f"{image.name}: {exc}", file=sys.stderr)
            failures += 1
    total = len(images)
    print(f"done: {total - failures}/{total} parsed -> {outdir}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()

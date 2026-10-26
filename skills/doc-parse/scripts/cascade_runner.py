#!/usr/bin/env python3
"""crop-cascade orchestration: budgets, level-barrier pool, manifest, exit."""

from __future__ import annotations

import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import cascade_blocks as cb
import cascade_compose as cc
import cascade_nodes as cn
from cascade_common import (
    EXIT_COMPOSE,
    EXIT_FULL,
    EXIT_OK,
    EXIT_PARTIAL,
    EXIT_USAGE,
    check_image,
    die,
    probe_chat,
    setup_logging,
)

MAX_PARALLEL_CAP = 8
PROMPT_PLACEHOLDERS = (
    "{{LEVEL}}", "{{BOX}}", "{{CANDIDATES}}", "{{PARENT_EXCERPT}}",
    "{{CROP_EXCERPT}}",
)


class Budgets:
    """Parse-call and crop-id budgets; all allocation under one lock."""

    def __init__(self, max_parse_calls: int, max_crops: int):
        self.lock = threading.Lock()
        self.parse_calls = 0
        self.crops = 0
        self.max_parse_calls = max_parse_calls
        self.max_crops = max_crops

    def spend_parse(self) -> bool:
        with self.lock:
            if self.parse_calls >= self.max_parse_calls:
                return False
            self.parse_calls += 1
            return True

    def next_crop_id(self) -> int | None:
        with self.lock:
            if self.crops >= self.max_crops:
                return None
            self.crops += 1
            return self.crops


class Cascade:
    """One image's cascade run; the ctx object cascade_nodes functions take."""

    def __init__(self, args, config, log, outdir: Path, image: Path,
                 mime: str, prompt_file: Path):
        self.args = args
        self.config = config
        self.log = log
        self.outdir = outdir
        self.image = image
        self.mime = mime
        self.prompt_file = prompt_file
        self.budgets = Budgets(args.max_parse_calls, args.max_crops)
        self.chat_lock = threading.Lock()
        self.chat_index = 0
        self.retries = 0
        self.degraded = {"chat": False, "reason": ""}
        self.prompt_template = ""
        self.prompt_sha = ""
        self.chat_active = False

    def bank_prompt(self) -> None:
        text = self.prompt_file.read_text()
        missing = [p for p in PROMPT_PLACEHOLDERS if p not in text]
        if missing:
            die(f"prompt file lacks placeholder(s): {', '.join(missing)}",
                EXIT_USAGE)
        self.prompt_template = text
        self.prompt_sha = hashlib.sha256(
            self.prompt_file.read_bytes()).hexdigest()
        (self.outdir / "prompt_used.md").write_text(
            f"<!-- source: {self.prompt_file.name} "
            f"sha256: {self.prompt_sha} -->\n{text}")

    def setup_chat(self) -> None:
        if not self.config.get("chat_ready"):
            self.degraded = {
                "chat": True,
                "reason": self.config.get("chat_reason", "chat lane disabled"),
            }
            self.log.warning("chat lane disabled: %s",
                             self.degraded["reason"])
            return
        ok = probe_chat(self.config, self.args.chat_timeout, self.log)
        self.chat_active = ok
        if not ok:
            self.degraded = {
                "chat": True,
                "reason": ("chat probe failed — decisions use the "
                           "deterministic-conservative fallback"),
            }
        self.log.info("chat lane: %s", "active" if ok else "degraded")

    def parse_root(self):
        """Full-frame node; returns (root, root_text) or None on failure."""
        img_w, img_h = cb.image_size(self.image)
        root = cn.build_root(self.image, img_w, img_h)
        (self.outdir / "full").mkdir(parents=True, exist_ok=True)
        content = cn.parse_node(self, root, self.mime)
        if content is None:
            self.log.error("full-frame parse failed — aborting the cascade")
            return None
        root_text = "\n".join(b.text for b in cb.parse_blocks(content))
        self.log.info("root parsed: %d chars", len(content))
        root["_content"] = content
        return root, root_text


    def run(self) -> int:
        self.bank_prompt()
        self.setup_chat()
        try:
            parsed = self.parse_root()
        except cb.CropBackendError as exc:
            self.log.error("no crop/size backend: %s", exc)
            return EXIT_INPUT
        if parsed is None:
            return EXIT_FULL
        root, root_text = parsed
        crops = self.cascade_loop(root, root_text)
        return self.finish(root, crops)

    def cascade_loop(self, root: dict, root_text: str) -> list:
        """Level barrier: level N's discoveries parse at N+1, fanned across
        a bounded pool; a worker failure never raises past this loop."""
        crops = []
        pending = [(root, "")]
        workers = max(1, min(self.args.max_parallel, MAX_PARALLEL_CAP))
        self.log.info("pool: %d workers, caps: crops=%d parse=%d depth=%d",
                      workers, self.args.max_crops,
                      self.args.max_parse_calls, self.args.max_depth)
        while pending:
            level_nodes = pending
            pending = self.run_level(level_nodes, workers)
            crops.extend(child for child, _ in pending)
            self.log.info("level %d done: %d nodes -> %d children",
                          level_nodes[0][0]["level"], len(level_nodes),
                          len(pending))
        by_trigger = {}
        for crop in crops:
            by_trigger.setdefault(crop["trigger"], []).append(crop["id"])
        root["children"] = by_trigger.get("root", [])
        for crop in crops:
            crop["children"] = by_trigger.get(crop["id"], [])
        return crops

    def run_level(self, level_nodes: list, workers: int) -> list:
        out = []
        if workers <= 1:
            for node, parent_text in level_nodes:
                out.extend(cn.process_node(self, node, parent_text))
            return out
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {
                pool.submit(cn.process_node, self, node, parent_text): node
                for node, parent_text in level_nodes
            }
            for future in as_completed(futures):
                try:
                    out.extend(future.result())
                except Exception as exc:  # noqa: BLE001 — logged in the worker
                    self.log.error("level worker crashed: %s", exc,
                                   exc_info=True)
        return out


    def build_manifest(self, root: dict, crops: list) -> dict:
        backstop = sum(
            1 for c in crops if c.get("stop_reason") == "backstop")
        return {
            "slide": self.image.stem,
            "source_frame": self.image.name,
            "source_md5": hashlib.md5(self.image.read_bytes()).hexdigest(),
            "frame_dims": root["size_px"],
            "prompt_file": self.prompt_file.name,
            "prompt_sha256": self.prompt_sha,
            "parse_model": self.config["model"],
            "chat_model": self.config.get("chat_model"),
            "caps": {
                "max_retries": self.args.max_retries,
                "max_parallel": self.args.max_parallel,
                "max_crops": self.args.max_crops,
                "max_parse_calls": self.args.max_parse_calls,
                "max_depth": self.args.max_depth,
                "max_output_tokens": (
                    self.args.max_output_tokens
                    or self.config["max_output_tokens"]),
            },
            "parse_calls_spent": self.budgets.parse_calls,
            "crops_spent": self.budgets.crops,
            "degraded": self.degraded,
            "root": root,
            "crops": crops,
            "recursion": {
                "levels_processed": 1 + max(
                    (c["level"] for c in crops), default=0),
                "backstop_hits": backstop,
            },
            "stats": {
                "parse_calls": self.budgets.parse_calls,
                "chat_calls": self.chat_index,
                "retries": self.retries,
                "dedup_collapsed": 0,
                "elements": 0,
            },
        }

    def finish(self, root: dict, crops: list) -> int:
        manifest = self.build_manifest(root, crops)
        try:
            composed_dir = self.outdir / "composed"
            composed_dir.mkdir(parents=True, exist_ok=True)
            text, patch = cc.compose_markdown(manifest, self.outdir)
            (composed_dir / f"{self.image.stem}_composed.md").write_text(text)
            manifest["stats"].update(patch)
        except Exception as exc:  # noqa: BLE001 — compose failure is exit 7
            self.log.error("composition failed: %s", exc, exc_info=True)
            cc.write_manifest(manifest, self.outdir)
            return EXIT_COMPOSE
        cc.write_manifest(manifest, self.outdir)
        self.log.info("composed -> composed/%s_composed.md", self.image.stem)
        if any(crop.get("error") for crop in crops):
            self.log.warning("completed with partial failures — see manifest")
            return EXIT_PARTIAL
        return EXIT_OK


def build_cascade(args, config) -> Cascade:
    image = args.image.expanduser().resolve()
    prompt_file = args.prompt_file.expanduser().resolve()
    outdir = args.out.expanduser().resolve()
    if args.max_parallel < 1:
        die("--max-parallel must be >= 1", EXIT_USAGE)
    if not image.is_file():
        die(f"{image}: no such image file", EXIT_USAGE)
    if not prompt_file.is_file():
        die(f"{prompt_file}: no such prompt file", EXIT_USAGE)
    mime = check_image(image)
    outdir.mkdir(parents=True, exist_ok=True)
    log = setup_logging(outdir, image.name)
    log.info("models: parse=%s chat=%s(%s)",
             config["model"], config.get("chat_model"),
             "active-pending-probe" if config.get("chat_ready") else "off")
    return Cascade(args, config, log, outdir, image, mime, prompt_file)

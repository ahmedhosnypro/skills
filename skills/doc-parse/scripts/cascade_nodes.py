#!/usr/bin/env python3
"""crop-cascade per-node work: parse, decisions, chat escalation, children."""

from __future__ import annotations

import json
from pathlib import Path

import cascade_blocks as cb
import cascade_compose as cc
from cascade_common import (
    ApiCallError,
    FatalApiError,
    chat_call,
    parse_call,
)

CROP_PNG_MIME = "image/png"


def build_root(image: Path, img_w: int, img_h: int) -> dict:
    """The full-frame node every cascade starts from (scale 1, origin 0)."""
    return {
        "id": "root", "level": 0, "class": "frame",
        "box_frame_px": [0, 0, img_w, img_h], "estimated": False,
        "png": str(image), "mean_rgb": None, "precheck_ok": True,
        "parse_files": {
            "md": f"full/{image.stem}.parse.md",
            "json": f"full/{image.stem}.parse.json",
        },
        "scale": 1.0, "size_px": [img_w, img_h], "margin_applied": [0, 0],
        "stop_reason": None, "stop_note": None,
        "decision_source": "deterministic", "children": [],
        "transform": {"origin_px": [0, 0], "scale": 1.0,
                      "rule": "frame = png_px / scale + origin_px (scale "
                              "cumulative png-per-source px; origin = png "
                              "top-left in source px)"},
        "trigger": "full frame", "error": None,
    }


def node_src(ctx, node: dict) -> Path:
    ref = Path(node["png"])
    return ref if ref.is_absolute() else ctx.outdir / ref


def bank_transcripts(ctx, node: dict, result: dict, content: str) -> None:
    (ctx.outdir / node["parse_files"]["md"]).write_text(content)
    (ctx.outdir / node["parse_files"]["json"]).write_text(
        json.dumps(result, indent=2))


def parse_node(ctx, node: dict, mime: str) -> str | None:
    """One parse-lane call for a node; banks transcripts, returns content.
    None means the node failed (error recorded on the node)."""
    if not ctx.budgets.spend_parse():
        node["error"] = "parse-call budget exhausted"
        ctx.log.error("node %s: %s", node["id"], node["error"])
        return None
    attempts = 1 + max(0, ctx.args.max_retries)
    tokens = ctx.args.max_output_tokens or ctx.config["max_output_tokens"]
    try:
        result = parse_call(node_src(ctx, node), mime, ctx.config, tokens,
                            ctx.args.parse_timeout, attempts, ctx.log)
    except (ApiCallError, FatalApiError) as exc:
        node["error"] = f"{type(exc).__name__}: {exc}"
        ctx.retries += 1
        ctx.log.error("node %s parse failed: %s", node["id"], exc)
        return None
    content = result.get("content")
    if not isinstance(content, str) or not content.strip():
        node["error"] = "empty parse content"
        ctx.log.error("node %s: %s", node["id"], node["error"])
        return None
    bank_transcripts(ctx, node, result, content)
    ctx.log.info("node %s parsed: %d chars, %s out tokens",
                 node["id"], len(content),
                 (result.get("usage") or {}).get("output_tokens", "?"))
    return content


def decide(ctx, node: dict, blocks: list, parent_text: str, child_text: str):
    """Two-tier decision for one node. Returns
    (stop_reason | None, stop_note, decision_source, candidates)."""
    img_w, img_h = node["size_px"]
    if not blocks:
        return "leaf", "parse carried no class blocks", "deterministic", []
    positioned = [
        b for b in blocks
        if b.box is not None and not cb.is_text_class(b.cls)]
    if not positioned:
        note = "no positioned non-text region blocks"
        return "no-internal-structure", note, "deterministic", []
    candidates = cb.candidate_blocks(blocks, img_w, img_h)
    if not candidates:
        note = "every candidate is frame-covering or below the 40 px floor"
        return "too-small", note, "deterministic", []
    if not cb.has_new_information(parent_text, child_text):
        note = "child lines are a subset of the parent parse"
        return "no-new-information", note, "deterministic", []
    if not ctx.chat_active:
        note = "chat lane unavailable — conservative CROP fallback"
        return None, note, "fallback", candidates
    decision, reason = ask_chat(ctx, node, candidates, parent_text, child_text)
    if decision == "STOP":
        return "no-new-information", f"chat advised STOP: {reason}", "chat", []
    if decision == "CROP":
        return None, f"chat advised CROP: {reason}", "chat", candidates
    note = f"chat reply unparseable ({reason}) — conservative CROP fallback"
    return None, note, "fallback", candidates


def render_decision_prompt(ctx, node, candidates, parent_text, child_text):
    """Fill the template's four placeholders; content is data, never
    instructions — the reply is parsed for DECISION/REASON lines only."""
    origin = tuple((node.get("transform") or {}).get("origin_px") or (0, 0))
    plan = {"size_px": node["size_px"], "scale": node["scale"] or 1.0}
    box = cb.to_frame(cb.union_box(candidates), plan, origin)
    rendered = ctx.prompt_template
    for placeholder, value in (
        ("{{LEVEL}}", str(node["level"])),
        ("{{BOX}}", f"[x={box[0]:.0f}, y={box[1]:.0f}, "
                    f"w={box[2]:.0f}, h={box[3]:.0f}]"),
        ("{{PARENT_EXCERPT}}", cb.excerpt(parent_text)),
        ("{{CROP_EXCERPT}}", cb.excerpt(child_text)),
    ):
        rendered = rendered.replace(placeholder, value)
    return rendered, box


def ask_chat(ctx, node, candidates, parent_text, child_text) -> tuple:
    """One chat escalation per node; banks the full exchange, then parses
    the answer contract. Returns (decision | None, reason)."""
    with ctx.chat_lock:
        ctx.chat_index += 1
        index = ctx.chat_index
    rendered, box = render_decision_prompt(
        ctx, node, candidates, parent_text, child_text)
    meta = {"node": node["id"], "level": node["level"], "box": box,
            "model": ctx.config.get("chat_model")}
    attempts = 1 + max(0, ctx.args.max_retries)
    try:
        content, raw = cc_chat(ctx, rendered, attempts)
    except (ApiCallError, FatalApiError) as exc:
        ctx.retries += 1
        meta["error"] = str(exc)
        cc.bank_chat(ctx.outdir, index, rendered, str(exc), meta)
        ctx.log.warning("node %s chat call failed: %s", node["id"], exc)
        return None, f"chat call failed: {exc}"
    meta["finish"] = (raw.get("choices") or [{}])[0].get("finish_reason")
    meta["out_tokens"] = (raw.get("usage") or {}).get("output_tokens")
    cc.bank_chat(ctx.outdir, index, rendered, raw, meta)
    return cc.parse_chat_decision(content)


def cc_chat(ctx, rendered: str, attempts: int) -> tuple:
    return chat_call(rendered, ctx.config, ctx.args.chat_timeout, attempts,
                     ctx.log)


def process_node(ctx, node: dict, parent_text: str) -> list:
    """Worker body for one node: parse, decide, spawn children. Returns
    [(child_node, this node's text), ...]; a failure never raises."""
    try:
        content = node.pop("_content", None)
        if content is None:
            content = parse_node(ctx, node, CROP_PNG_MIME)
        if content is None:
            return []
        blocks = cb.parse_blocks(content)
        node_text = "\n".join(block.text for block in blocks)
        stop_reason, stop_note, source, candidates = decide(
            ctx, node, blocks, parent_text, node_text)
        node["stop_reason"] = stop_reason
        node["stop_note"] = stop_note
        node["decision_source"] = source
        if stop_reason:
            ctx.log.info("node %s stop: %s — %s",
                         node["id"], stop_reason, stop_note)
            return []
        children = make_children(ctx, node, candidates, node_text)
        return [(child, node_text) for child in children]
    except Exception as exc:  # noqa: BLE001 — one bad node never stops siblings
        ctx.log.error("node %s failed: %s", node["id"], exc, exc_info=True)
        node["error"] = f"{type(exc).__name__}: {exc}"
        return []


def make_children(ctx, node: dict, candidates: list, node_text: str) -> list:
    """Crop + queue children for a CROP decision; budgets and the depth
    backstop are enforced here, never silently skipped."""
    child_level = node["level"] + 1
    if child_level > ctx.args.max_depth:
        node["stop_reason"] = "backstop"
        node["stop_note"] = (
            f"child level {child_level} exceeds max-depth {ctx.args.max_depth}")
        ctx.log.info("node %s: %s", node["id"], node["stop_note"])
        return []
    ordered = sorted(candidates, key=lambda b: (b.box[1], b.box[0]))
    children = []
    for block in ordered:
        crop_id = ctx.budgets.next_crop_id()
        if crop_id is None:
            node["stop_note"] = (
                (node.get("stop_note") or "")
                + " [budget: max-crops reached]")
            ctx.log.warning("node %s: max-crops budget reached", node["id"])
            break
        try:
            children.append(build_child(ctx, node, block, crop_id))
        except Exception as exc:  # noqa: BLE001 — sibling crops continue
            ctx.log.error("node %s: crop %02d failed: %s",
                          node["id"], crop_id, exc, exc_info=True)
    return children


def build_child(ctx, node: dict, block, crop_id: int) -> dict:
    """Create one child: crop png from the parent's png, frame transform,
    transcript paths. Raises on crop production failure (caller logs it)."""
    stem = ctx.image.stem
    name = f"{stem}.crop{crop_id:02d}__{cb.sanitize_class(block.cls)}"
    rel_png = f"crops/{name}.png"
    img_w, img_h = node["size_px"]
    plan = cb.plan_crop(block.box, img_w, img_h)
    png_path = ctx.outdir / rel_png
    png_path.parent.mkdir(parents=True, exist_ok=True)
    backend, mean = cb.make_crop_png(node_src(ctx, node), plan, png_path)
    if not png_path.is_file() or png_path.stat().st_size == 0:
        raise RuntimeError("crop png was not produced")
    precheck_ok = mean is None or mean > 0.5
    if not precheck_ok:
        ctx.log.warning("crop %s: degenerate mean %.2f", name, mean)
    transform = node.get("transform") or {}
    origin = tuple(transform.get("origin_px") or (0, 0))
    parent_scale = transform.get("scale") or node["scale"] or 1.0
    node_plan = {"size_px": node["size_px"], "scale": parent_scale}
    frame_box = cb.to_frame(block.box, node_plan, origin)
    child_scale = round(parent_scale * plan["scale"], 4)
    png_origin = [round(origin[0] + plan["crop_px"][0] / parent_scale, 1),
                  round(origin[1] + plan["crop_px"][1] / parent_scale, 1)]
    return {
        "id": name, "level": node["level"] + 1, "class": block.cls,
        "box_frame_px": frame_box, "estimated": block.estimated,
        "png": rel_png, "mean_rgb": None if mean is None else round(mean, 2),
        "precheck_ok": precheck_ok, "backend": backend,
        "parse_files": {
            "md": f"crops/{name}.parse.md",
            "json": f"crops/{name}.parse.json",
        },
        "scale": child_scale, "size_px": plan["size_px"],
        "margin_applied": plan["margin_applied"],
        "stop_reason": None, "stop_note": None,
        "decision_source": "deterministic", "children": [],
        "transform": {"origin_px": png_origin, "scale": child_scale,
                      "rule": "frame = png_px / scale + origin_px (scale "
                              "cumulative png-per-source px; origin = png "
                              "top-left in source px)"},
        "trigger": node["id"], "error": None,
    }

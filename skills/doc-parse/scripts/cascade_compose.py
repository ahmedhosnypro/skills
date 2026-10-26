#!/usr/bin/env python3
"""crop-cascade outputs: chat banking, manifest, deterministic composition."""

from __future__ import annotations

import json
import re
from pathlib import Path

import cascade_blocks as cb

DECISION_RE = re.compile(r"DECISION:\s*(CROP|STOP)", re.IGNORECASE)
REASON_RE = re.compile(r"REASON:\s*(.+)", re.IGNORECASE)


def bank_chat(outdir: Path, index: int, rendered: str, raw, meta: dict):
    """Bank one chat exchange (rendered prompt + raw response) for diagnosis."""
    chat_dir = outdir / "chat"
    chat_dir.mkdir(parents=True, exist_ok=True)
    path = chat_dir / f"decision_{index:02d}.md"
    lines = [f"# chat decision {index:02d}", ""]
    for key in sorted(meta):
        lines.append(f"- {key}: {meta[key]}")
    lines += ["", "## rendered prompt", "", rendered, "",
              "## raw response", ""]
    if isinstance(raw, (dict, list)):
        lines.append(f"```json\n{json.dumps(raw, indent=2)}\n```")
    else:
        lines.append(str(raw))
    path.write_text("\n".join(lines) + "\n")
    return path


def parse_chat_decision(content: str) -> tuple:
    """Extract the template's DECISION/REASON answer contract."""
    match = DECISION_RE.search(content)
    if not match:
        return None, "chat reply carried no DECISION line"
    reason_match = REASON_RE.search(content)
    reason = reason_match.group(1).strip() if reason_match else ""
    return match.group(1).upper(), reason


def write_manifest(manifest: dict, outdir: Path):
    (outdir / "manifest.json").write_text(json.dumps(manifest, indent=2))


def _node_plan(node: dict) -> dict:
    return {
        "size_px": node["size_px"],
        "scale": node["scale"] or 1.0,
    }


def _node_origin(node: dict) -> tuple:
    transform = node.get("transform") or {}
    return tuple(transform.get("origin_px") or (0, 0))


def node_elements(node: dict, outdir: Path) -> list:
    """All positioned/unpositioned elements of one node's transcript,
    mapped into frame pixels with per-element provenance."""
    md_rel = node["parse_files"]["md"]
    path = outdir / md_rel
    content = path.read_text() if path.is_file() else ""
    origin = _node_origin(node)
    plan = _node_plan(node)
    img_w, img_h = node["size_px"]
    elements = []
    for block in cb.parse_blocks(content):
        frame_box = None
        if block.box is not None:
            frame_box = cb.to_frame(block.box, plan, origin)
        elements.append({
            "cls": block.cls,
            "text": block.text,
            "frame_box": frame_box,
            "level": node["level"],
            "source": md_rel,
            "area": (frame_box[2] * frame_box[3]) if frame_box else None,
        })
    return elements


def collect_elements(manifest: dict, outdir: Path) -> tuple:
    """Elements from every transcript (root + crops), failed nodes listed."""
    elements = node_elements(manifest["root"], outdir)
    for crop in manifest["crops"]:
        if crop.get("parse_files", {}).get("md"):
            elements.extend(node_elements(crop, outdir))
    failed = [
        {"id": crop["id"], "level": crop["level"], "error": crop.get("error", "")}
        for crop in manifest["crops"] if crop.get("error")
    ]
    return elements, failed


def _dedup_key(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()


def dedup_elements(elements: list) -> tuple:
    """One element per distinct text: the smallest-area instance wins
    (the most detailed read); unpositioned instances lose ties."""
    best = {}
    for element in elements:
        key = _dedup_key(element["text"])
        if not key:
            best.setdefault(id(element), element)
            continue
        incumbent = best.get(key)
        if incumbent is None or _rank(element) < _rank(incumbent):
            best[key] = element
    kept = list(best.values())
    collapsed = len(elements) - len(kept)
    kept.sort(key=lambda e: _sort_key(e))
    return kept, collapsed


def _rank(element: dict) -> tuple:
    area = element["area"]
    return (1, 0.0) if area is None else (0, area)


def _sort_key(element: dict):
    box = element["frame_box"]
    if box is None:
        return (1, 0.0, 0.0)
    return (0, box[1], box[0])


def _format_element(element: dict) -> str:
    token = f"`<class_{element['cls']}>`"
    box = element["frame_box"]
    place = (
        f" @(x={box[0]:.0f}, y={box[1]:.0f}, w={box[2]:.0f}, h={box[3]:.0f})"
        if box else " (unpositioned)"
    )
    provenance = f"from {element['source']} (level {element['level']})"
    head = f"- {token}{place} — {provenance}"
    if element["text"]:
        head += f"\n  {element['text']}"
    return head


def compose_markdown(manifest: dict, outdir: Path) -> tuple:
    """Deterministic merge of every transcript into one provenance-carrying
    file: positioned elements in reading order, then unpositioned text,
    failed calls, and run notes. Geometry + merge only — no interpretation.
    Returns (markdown, stats patch with elements/dedup_collapsed)."""
    elements, failed = collect_elements(manifest, outdir)
    kept, collapsed = dedup_elements(elements)
    stats = manifest["stats"]
    degraded = manifest["degraded"]
    header = [
        f"# Composed parse: {manifest['slide']}",
        "",
        f"- source frame: `{manifest['source_frame']}` (md5 "
        f"`{manifest['source_md5']}`)",
        f"- parse model: `{manifest['parse_model']}` · "
        f"chat model: `{manifest['chat_model'] or 'n/a'}`",
        f"- degraded: {degraded['chat']}"
        + (f" ({degraded['reason']})" if degraded["reason"] else ""),
        f"- elements kept: {len(kept)} (dedup collapsed {collapsed}) · "
        f"crops: {len(manifest['crops'])} · failed calls: {len(failed)}",
        "",
    ]
    positioned = [e for e in kept if e["frame_box"] is not None]
    unpositioned = [e for e in kept if e["frame_box"] is None]
    body = ["## Positioned elements (reading order: y then x)", ""]
    body += [_format_element(e) for e in positioned] or ["- (none)"]
    body += ["", "## Unpositioned text", ""]
    body += [_format_element(e) for e in unpositioned] or ["- (none)"]
    body += ["", "## Failed calls", ""]
    body += [
        f"- {f['id']} (level {f['level']}): {f['error']}" for f in failed
    ] or ["- (none)"]
    body += ["", "## Notes", "", f"- backstop stops: "
             f"{manifest['recursion']['backstop_hits']}",
             f"- parse calls spent: {stats['parse_calls']} · "
             f"chat calls: {stats['chat_calls']} · "
             f"retries: {stats['retries']}"]
    patch = {"elements": len(kept), "dedup_collapsed": collapsed}
    return "\n".join(header + body) + "\n", patch

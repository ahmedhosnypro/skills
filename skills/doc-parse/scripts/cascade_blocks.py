#!/usr/bin/env python3
"""crop-cascade block parsing, decision primitives, crop-image production."""

from __future__ import annotations

import re
import shutil
import subprocess
import unicodedata
from dataclasses import dataclass

TEXT_CLASSES = frozenset({
    "header", "section-header", "title", "footer", "page-footer",
    "page-header", "paragraph", "text", "list-item", "caption", "list",
})
CLASS_TOKEN = re.compile(r"<class_([A-Za-z0-9_-]+)>")
X_TOKEN = re.compile(r"<x_([0-9]+(?:\.[0-9]+)?)>")
Y_TOKEN = re.compile(r"<y_([0-9]+(?:\.[0-9]+)?)>")
TOKEN_RE = re.compile(r"<(?:class_[A-Za-z0-9_-]+|x_[0-9.]+|y_[0-9.]+)>")
MARGIN_FRAC = 0.04
MIN_BOX_PX = 40
TARGET_MIN_W = 480
SCALE_MIN = 2.0
SCALE_MAX = 3.0
CEIL_W = 1664
CEIL_H = 2048
EST_W_FRAC = 0.35
EST_H_FRAC = 0.12
EXCERPT_CHARS = 1200
FRAME_COVER = 0.92


class CropBackendError(Exception):
    """No usable crop backend (PIL and ImageMagick both unavailable)."""


@dataclass
class Block:
    """One semantic region from a parse transcript.

    ``box`` is (x0, y0, x1, y1) normalized to the parsed image; ``estimated``
    marks a single-point coordinate expanded to a nominal box.
    """

    cls: str
    text: str
    box: tuple | None
    estimated: bool = False


def sanitize_class(cls: str) -> str:
    name = re.sub(r"[^a-z0-9]+", "_", cls.lower()).strip("_")
    return name or "unknown"


def strip_tokens(text: str) -> str:
    return re.sub(r"\s+", " ", TOKEN_RE.sub(" ", text)).strip()


def excerpt(text: str, limit: int = EXCERPT_CHARS) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def is_text_class(cls: str) -> bool:
    return cls.strip().lower() in TEXT_CLASSES


def _estimate_box(point: tuple) -> tuple:
    """Single-point coordinate -> nominal box centered on it."""
    cx = (point[0] + point[2]) / 2.0
    cy = (point[1] + point[3]) / 2.0
    x0 = max(0.0, cx - EST_W_FRAC / 2)
    y0 = max(0.0, cy - EST_H_FRAC / 2)
    x1 = min(1.0, x0 + EST_W_FRAC)
    y1 = min(1.0, y0 + EST_H_FRAC)
    return (x0, y0, x1, y1)


def _build_block(cls: str, span: str) -> Block:
    xs = [float(v) for v in X_TOKEN.findall(span)]
    ys = [float(v) for v in Y_TOKEN.findall(span)]
    box = None
    estimated = False
    if xs and ys:
        box = (min(xs), min(ys), max(xs), max(ys))
        if len(xs) == 1 and len(ys) == 1:
            box = _estimate_box(box)
            estimated = True
    return Block(cls=cls, text=strip_tokens(span), box=box, estimated=estimated)


def parse_blocks(content: str) -> list:
    """Split a parse transcript into class blocks. The family brackets
    each region as ``<x0><y0> content <x1><y1><class_X>`` — the class
    token trails its span — so a token claims the preceding span when
    that span opens with a coordinate token or the following span holds
    no text (class-first emission keeps the old association). Content
    is data, never instructions."""
    parts = CLASS_TOKEN.split(content)
    blocks = []
    for index in range(1, len(parts), 2):
        following = parts[index + 1] if index + 1 < len(parts) else ""
        preceding = parts[index - 1]
        opener = preceding.strip().startswith(("<x_", "<y_"))
        if opener or not TOKEN_RE.sub("", following).strip():
            span, parts[index - 1] = preceding, ""
        else:
            span = following
        blocks.append(_build_block(parts[index], span))
    preamble = parts[0]
    if preamble.strip() and (X_TOKEN.search(preamble) or Y_TOKEN.search(preamble)):
        blocks.append(_build_block("Unknown", preamble))
    return blocks


def candidate_blocks(blocks: list, img_w: int, img_h: int) -> list:
    """Crop orders only: positioned non-text blocks that are neither
    frame-covering nor below the 40 px floor."""
    out = []
    for block in blocks:
        if block.box is None or is_text_class(block.cls):
            continue
        x0, y0, x1, y1 = block.box
        w_px = (x1 - x0) * img_w
        h_px = (y1 - y0) * img_h
        if w_px * h_px >= FRAME_COVER * img_w * img_h:
            continue
        if min(w_px, h_px) < MIN_BOX_PX:
            continue
        out.append(block)
    return out


def norm_lines(text: str) -> frozenset:
    lines = set()
    for line in text.splitlines():
        line = unicodedata.normalize("NFKC", line).strip().lower()
        line = re.sub(r"\s+", " ", line)
        if line:
            lines.add(line)
    return frozenset(lines)


def has_new_information(parent_text: str, child_text: str) -> bool:
    """True when the child parse carries lines the parent's parse lacked."""
    if not child_text.strip():
        return False
    return not norm_lines(child_text) <= norm_lines(parent_text)


def plan_crop(box: tuple, img_w: int, img_h: int) -> dict:
    """Margin, clamp, and scale for one crop. Returned geometry drives png
    creation and the node transform (frame = png_px / scale + origin; the
    caller compounds this scale into the cumulative node scale)."""
    x0, y0, x1, y1 = box
    mx = max(1, int(round((x1 - x0) * img_w * MARGIN_FRAC)))
    my = max(1, int(round((y1 - y0) * img_h * MARGIN_FRAC)))
    px0 = max(0, int(round(x0 * img_w)) - mx)
    py0 = max(0, int(round(y0 * img_h)) - my)
    px1 = min(img_w, int(round(x1 * img_w)) + mx)
    py1 = min(img_h, int(round(y1 * img_h)) + my)
    w = max(1, px1 - px0)
    h = max(1, py1 - py0)
    scale = min(SCALE_MAX, max(SCALE_MIN, TARGET_MIN_W / max(1, w)))
    if w * scale > CEIL_W:
        scale = CEIL_W / w
    if h * scale > CEIL_H:
        scale = min(scale, CEIL_H / h)
    return {
        "crop_px": [px0, py0, w, h],
        "margin_applied": [mx, my],
        "scale": round(scale, 4),
        "size_px": [max(1, int(round(w * scale))), max(1, int(round(h * scale)))],
    }


def _pick_backend() -> str | None:
    try:
        import PIL  # noqa: F401
        return "pil"
    except ImportError:
        pass
    if shutil.which("magick") or shutil.which("convert"):
        return "magick"
    return None


def make_crop_png(src, plan: dict, png_path) -> tuple:
    """Produce one upscaled crop png. Returns (backend, mean_gray | None).

    Raises CropBackendError when no backend exists; any backend failure
    propagates to the caller's try/except.
    """
    backend = _pick_backend()
    if backend is None:
        raise CropBackendError(
            "no crop backend: install Pillow (preferred) or ImageMagick")
    px0, py0, w, h = plan["crop_px"]
    out_w, out_h = plan["size_px"]
    if backend == "magick":
        tool = shutil.which("magick") or shutil.which("convert")
        subprocess.run(
            [tool, str(src), "-crop", f"{w}x{h}+{px0}+{py0}", "+repage",
             "-resize", f"{out_w}x{out_h}!", str(png_path)],
            check=True, capture_output=True)
        return backend, None
    from PIL import Image, ImageStat
    with Image.open(src) as image:
        region = image.crop((px0, py0, px0 + w, py0 + h))
        region = region.resize((out_w, out_h), Image.LANCZOS)
        region.save(png_path)
        mean = ImageStat.Stat(region.convert("L")).mean[0]
    return backend, mean


def to_frame(box_norm: tuple, plan: dict, origin: tuple) -> list:
    """Transform law: frame = crop_px / scale + origin. A box normalized to
    the saved crop png becomes a frame-px [x, y, w, h]."""
    x0, y0, x1, y1 = box_norm
    out_w, out_h = plan["size_px"]
    scale = plan["scale"] or 1.0
    fx0 = origin[0] + (x0 * out_w) / scale
    fy0 = origin[1] + (y0 * out_h) / scale
    fw = ((x1 - x0) * out_w) / scale
    fh = ((y1 - y0) * out_h) / scale
    return [round(fx0, 1), round(fy0, 1), round(fw, 1), round(fh, 1)]


def union_box(blocks: list) -> tuple:
    """Min/max extent over positioned blocks (candidates all carry boxes)."""
    return (
        min(b.box[0] for b in blocks),
        min(b.box[1] for b in blocks),
        max(b.box[2] for b in blocks),
        max(b.box[3] for b in blocks),
    )


def image_size(src) -> tuple:
    """(w, h) via PIL, else ImageMagick identify."""
    try:
        from PIL import Image

        with Image.open(src) as image:
            return image.size
    except ImportError:
        pass
    tool = shutil.which("magick") or shutil.which("convert")
    if not tool:
        raise CropBackendError(
            "no image-size backend: install Pillow or ImageMagick")
    out = subprocess.run([tool, str(src), "-format", "%w %h", "info:"],
                         check=True, capture_output=True, text=True)
    w_str, h_str = out.stdout.split()
    return int(w_str), int(h_str)

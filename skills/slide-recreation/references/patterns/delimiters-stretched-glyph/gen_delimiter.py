#!/usr/bin/env python3
"""Pattern: delimiters-stretched-glyph — generator.

Alternative delimiter construction for near-straight video parens: render the
"(" / ")" TEXT GLYPH once huge, tight-crop the ink, anisotropic-resize (LANCZOS)
to (stroke-width px x target-span px) at 600 dpi, recolor via the alpha channel,
save transparent PNG. Embed at EXACT px/600 size (vertical-only stretch keeps the
hairline a hairline; horizontal rescale blurs it).

Laws (shared with delimiters-bezier-png):
 - Size the span to the block's bottom-most INK row — a subscript descender
   hangs below the letter band and pokes past a paren sized to the letters.
 - Assert 0 enclosed-text ink inside the delimiter stroke columns.
 - Pin lineSpacing on the enclosed column; assert the delimiter ink covers the
   block's bottom-most ink row.

Usage:
  python3 gen_delimiter.py <( | )> <span_pt> <stroke_px_600dpi> <hex_color> <out.png>
"""
import sys

from PIL import Image, ImageDraw, ImageFont

DPI = 600
FONT_SIZE = 1000          # render huge, then shrink — antialiasing comes free


def gen(glyph: str, span_pt: float, stroke_px: float, hex_color: str, out: str) -> None:
    span_px = span_pt / 72 * DPI
    # Find a font (DejaVu ships everywhere; any sans with parens works)
    import glob
    cand = (glob.glob("/usr/share/fonts/**/DejaVuSans*.ttf", recursive=True)
            + glob.glob("/usr/share/fonts/**/*rial*.ttf", recursive=True)
            + glob.glob("/usr/share/fonts/**/*Liberation*Sans*.ttf", recursive=True))
    font = ImageFont.truetype(cand[0], FONT_SIZE)

    img = Image.new("RGBA", (FONT_SIZE * 3, FONT_SIZE * 3), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.text((FONT_SIZE, FONT_SIZE), glyph, font=font, fill=(255, 255, 255, 255))
    bbox = img.getbbox()
    glyph_img = img.crop(bbox)

    # anisotropic resize: hairline width x full span (LANCZOS for clean edges)
    resized = glyph_img.resize((max(1, int(stroke_px)), int(span_px)), Image.LANCZOS)

    # recolor via alpha: keep the antialiased alpha, paint the measured color
    rgb = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    r, g, b, a = resized.split()
    colored = Image.merge("RGBA", (
        r.point(lambda _: rgb[0]), g.point(lambda _: rgb[1]),
        b.point(lambda _: rgb[2]), a))
    colored.save(out)
    print(f"wrote {out}: {colored.size[0]}x{colored.size[1]}px @600dpi "
          f"-> embed w={colored.size[0]/DPI:.4f}in h={colored.size[1]/DPI:.4f}in")


if __name__ == "__main__":
    glyph, span, stroke, color, out = sys.argv[1:6]
    gen(glyph, float(span), float(stroke), color, out)

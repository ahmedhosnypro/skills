# Pattern: delimiters-direction-check

Closed-loop DIRECTION check for hand-drawn delimiter pairs (parens, braces).
Companion checker for `delimiters-bezier-png` (and any other hand-authored
arc/curve delimiter); the law lives in `references/equations.md`
("Delimiter direction law").

## The law in one line

A delimiter pair is two MIRRORED forms: "(" = cusps inner-right, belly
outer-left; ")" = the mirror. One bow-direction template reused for both sides
renders a mirrored pair — measured shipping silently through full-slide judges
on certified decks (a vector box whose two parens both bowed right).

## Usage

```sh
# auto-pairing: exactly two tall thin strokes expected (band/asset images)
python3 check_paren_direction.py wbox_band1.png wbox_band2.png

# explicit windows + expected shapes (when other tall ink exists — glyphs,
# ellipses, bars): columns measured from the build's own geometry
python3 check_paren_direction.py band.png --expect "476:500=(,855:875=)"

# opaque images (frames, 150dpi renders) — luminance ink + lower span fraction
python3 check_paren_direction.py render_crop.png frame_crop.png \
    --expect "554:563=(,600:609=)" --min-rows-frac 0.12
```

Exit 0 = every stroke matches its expected shape; exit 1 = any mirrored or
unresolved stroke (fail loud — rebuild the asset). `STRAIGHT` strokes
(bracket-class) are unresolved: pass `--expect x0:x1=STRAIGHT` for brackets.

## When to run

1. After generating each delimiter asset (before embedding).
2. On the matching crop of the 150dpi render (closed loop, ~4px tolerance is
   the geometry check's job — this check is direction only).
3. On the original-frame crop (ground truth): the original's delimiters are
   the reference the recreation must mirror. If the ORIGINAL itself shows a
   mirrored pair (hand-drawn source material), record it in the slide's spec
   notes and keep the recreation faithful — the check's `--expect` accepts
   any explicit shape.

A judge PASS never waives this check (hairline mirrored pairs pass full-slide
judges silently; only the zoomed crop comparison or this check catches them).

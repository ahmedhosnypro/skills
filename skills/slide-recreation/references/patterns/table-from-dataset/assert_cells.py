#!/usr/bin/env python3
"""Cell-assertion checker for the table-from-dataset pattern.

Extracts the first a:tbl from a single-slide pptx and asserts every displayed
cell equals the canonical CSV value for its row index.

Usage:
  python3 assert_cells.py <deck.pptx> <csv> <row0> [row1 ...]
  (row indices = displayed dataset rows, in display order)
"""
import csv
import sys
import zipfile
import xml.etree.ElementTree as ET

A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


def table_cells(pptx: str):
    z = zipfile.ZipFile(pptx)
    root = ET.fromstring(z.read("ppt/slides/slide1.xml"))
    tbl = root.find(f".//{A}tbl")   # nests deeper than graphicFrame/a:tbl
    if tbl is None:
        sys.exit("FAIL: no a:tbl found in the deck")
    rows = []
    for tr in tbl.findall(f"{A}tr"):
        rows.append(["".join(tc.itertext()).strip()
                     for tc in tr.findall(f"{A}tc")])
    return rows


def norm(v: str) -> str:
    """Match the whole-number convention: '3.0' == '3' (never show trailing .0).
    Non-numeric cells (labels) compare verbatim."""
    try:
        f = float(v)
    except ValueError:
        return v.strip()
    return str(int(f)) if f == int(f) else str(f)


def main() -> None:
    pptx, csv_path = sys.argv[1], sys.argv[2]
    displayed = [int(v) for v in sys.argv[3:]]
    with open(csv_path) as f:
        data = list(csv.reader(f))
    header, body = data[0], data[1:]
    rows = table_cells(pptx)
    ok = True
    # the deck displays a SUBSET of columns; map displayed header -> csv column
    col_idx = [header.index(h) for h in rows[0]]
    for deck_row, idx in zip(rows[1:], displayed):
        csv_row = body[idx]
        for cell, ci in zip(deck_row, col_idx):
            if norm(cell) != norm(csv_row[ci]):
                print(f"FAIL row {idx} col {header[ci]}: deck={cell!r} csv={csv_row[ci]!r}")
                ok = False
    print(f"cells checked: header + {len(displayed)} rows ->",
          "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

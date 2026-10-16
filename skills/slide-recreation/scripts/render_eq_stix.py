#!/usr/bin/env python3
"""Thin wrapper over the certified render_eq.py (unchanged) that renders
with matplotlib's STIX serif mathtext fontset — when the original's equation is
italic SERIF, STIX matches both the look and the measured ink proportions far
better than the default DejaVu sans. Same CLI/contract as render_eq.py:
  python3 render_eq_stix.py '<mathtext>' out.png <fontsize_pt> '<hexcolor>'
Usage contract identical: embed at exact sidecar w_in/h_in, place by baseline_frac.
"""
import json, os, sys, importlib.util

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
matplotlib.rcParams["mathtext.fontset"] = "stix"  # serif — matches original italic serif

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    "render_eq", os.path.join(HERE, "render_eq.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)  # __name__ != "__main__ -> CLI block skipped

latex, out, fs, color = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
print(json.dumps(mod.render(latex, out, fs, color)))

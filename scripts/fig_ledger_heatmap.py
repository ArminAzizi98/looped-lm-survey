#!/usr/bin/env python3
"""Heatmap: verified empirical claims (core papers) by comparison regime x largest model scale.
A claim with several regimes is counted once under each. Data: data/ledger/claims.csv."""
import csv, collections
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
rows = list(csv.DictReader((ROOT / "data/ledger/claims.csv").open()))
REG = [("iso_param", "matched parameters"), ("iso_data", "matched data"), ("iso_effective_depth", "matched effective depth"),
       ("iso_infer_flop", "matched inference FLOPs"), ("iso_train_flop", "matched training FLOPs"), ("unmatched", "unmatched")]
SC = ["<100M", "100M-1B", "1B-10B", ">=10B", "unstated"]
M = np.zeros((len(REG), len(SC)), dtype=int)
for r in rows:
    if r["verified"] != "True" or r["relevance"] == "adjacent":
        continue
    regs = r["regimes"].split(";")
    if "not_applicable" in regs or "unclear" in regs:
        continue
    for i, (k, _) in enumerate(REG):
        if k in regs:
            M[i, SC.index(r["scale_bin"])] += 1
# Guards for prose in Sec. 15 ("rarest kind overall and nearly absent below 100M parameters").
tf = [k for k, _ in REG].index("iso_train_flop")
assert M[tf].sum() == M.sum(axis=1).min(), "training-FLOP claims are no longer the rarest regime overall: update Sec. 15"
assert M[tf, 0] == M[:, 0].min(), "training-FLOP claims are no longer the rarest regime below 100M: update Sec. 15"
SURFACE = "#fcfcfb"; INK = "#0b0b0b"; INK2 = "#52514e"
from matplotlib.colors import LinearSegmentedColormap
cmap = LinearSegmentedColormap.from_list("blue", ["#f0efec", "#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"])
fig, ax = plt.subplots(figsize=(5.4, 2.6), dpi=200)
fig.patch.set_facecolor(SURFACE)
im = ax.imshow(M, cmap=cmap, aspect="auto")
for i in range(M.shape[0]):
    for j in range(M.shape[1]):
        v = M[i, j]
        ax.text(j, i, str(v), ha="center", va="center", fontsize=9.5, color="white" if v > M.max() * 0.55 else INK)
ax.set_xticks(range(len(SC))); ax.set_xticklabels(["<100M", "100M–1B", "1B–10B", "≥10B", "unstated"], fontsize=8.8, color=INK2)
ax.set_yticks(range(len(REG))); ax.set_yticklabels([l for _, l in REG], fontsize=8.8, color=INK2)
ax.set_xlabel("largest model scale at which the claim is shown", fontsize=8.8, color=INK2)
for s in ax.spines.values():
    s.set_visible(False)
ax.tick_params(length=0)
fig.tight_layout()
fig.savefig(ROOT / "paper/figures/fig_ledger_heatmap.pdf", facecolor=SURFACE)
print(M)

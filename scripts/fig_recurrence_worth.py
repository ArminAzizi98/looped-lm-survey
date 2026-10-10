#!/usr/bin/env python3
"""Figure: how much is one recurrence worth? Effective-parameter gain of looping, in units of the
shared block's parameters, under three fitted mappings:
  full equivalence      (r-1)
  power law (iso-depth) (r^phi - 1), phi = 0.46, 95% CI [0.41, 0.53]          arXiv:2604.21106
  bounded (looped MoE)  kappa1(m) (1 - exp(-(r-1)/kappa2(m))), kappa_j(m) = kappa_j m^-theta,
                        kappa1 = 0.3682, kappa2 = 1.4037, theta = 0.3286             arXiv:2609.40316
Constants are asserted to occur in the source texts. m = active/total parameter ratio (1 = dense)."""
import re, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from verify_quotes import norm
t1 = norm((ROOT / "data/fulltext/2604.21106.txt").read_text(errors="ignore"))
t2 = norm((ROOT / "data/fulltext/2609.40316.txt").read_text(errors="ignore"))
for s in ["0.46", "0.41, 0.53"]:
    assert s in t1, s
for s in ["0.3682", "1.4037", "0.3286"]:
    assert s in t2, s
r = np.linspace(1, 16, 300)
phi, lo, hi = 0.46, 0.41, 0.53
k1, k2, th = 0.3682, 1.4037, 0.3286
bounded = lambda m: k1 * m ** (-th) * (1 - np.exp(-(r - 1) / (k2 * m ** (-th))))
SURFACE = "#fcfcfb"; INK = "#0b0b0b"; INK2 = "#52514e"; GRID = "#e4e3df"
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
fig, ax = plt.subplots(figsize=(4.6, 2.7), dpi=200)
fig.patch.set_facecolor(SURFACE); ax.set_facecolor(SURFACE)
for s in ["top", "right"]:
    ax.spines[s].set_visible(False)
for s in ["left", "bottom"]:
    ax.spines[s].set_color(INK2); ax.spines[s].set_linewidth(0.6)
ax.tick_params(colors=INK2, labelsize=8.8, width=0.6)
ax.grid(axis="y", color=GRID, linewidth=0.5); ax.set_axisbelow(True)
ax.plot(r, r - 1, color=INK2, lw=1.0, ls=(0, (4, 2)))
ax.fill_between(r, r ** lo - 1, r ** hi - 1, color=C[0], alpha=0.15, linewidth=0)
ax.plot(r, r ** phi - 1, color=C[0], lw=1.6)
ax.plot(r, bounded(1.0), color=C[1], lw=1.6)
ax.plot(r, bounded(1 / 8), color=C[2], lw=1.6)
ax.axvspan(8, 16, color=GRID, alpha=0.35, linewidth=0)
ax.text(8.2, 4.05, "beyond fitted range", fontsize=7.8, color=INK2, va="top")
ax.set_xlim(1, 16); ax.set_ylim(0, 4.2)
ax.set_xticks([1, 2, 4, 8, 12, 16])
ax.set_xlabel("number of recurrences $r$", fontsize=9.5, color=INK2)
ax.set_ylabel("effective-parameter gain\n(multiples of the shared block)", fontsize=9.5, color=INK2)
lab = dict(fontsize=8.5, color=INK, va="center")
ax.text(5.15, 3.65, "full equivalence: $r-1$", va="center", ha="left", **{k: v for k, v in lab.items() if k not in ("va", "ha")})
ax.text(11.2, 16 ** phi - 1 + 0.3, "iso-depth power law,\n$\\varphi=0.46$ [0.41, 0.53]", **lab)
ax.text(11.2, bounded(1 / 8)[-1] + 0.22, "bounded, MoE ($m=1/8$)", **lab)
ax.text(11.2, bounded(1.0)[-1] - 0.22, "bounded, dense ($m=1$)", **lab)
fig.tight_layout()
fig.savefig(ROOT / "paper/figures/fig_recurrence_worth.pdf", facecolor=SURFACE)
print("gain at r=4: power", round(4 ** phi - 1, 2), "bounded dense", round(float(k1 * (1 - np.exp(-3 / k2))), 2))

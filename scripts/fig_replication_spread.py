#!/usr/bin/env python3
"""Figure: replication spread of the Tiny Recursive Model (TRM, arXiv:2510.04871) across independent papers.
Each point is (benchmark, reported value, source arXiv id, kind). Every value string is asserted to occur in
the source paper's text; points that fail are dropped and reported. Variants and protocols differ across
sources (MLP vs attention variant, splits, aggregation); the figure shows spread, not a ranking."""
import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from verify_quotes import norm
P = [  # benchmark, value string, source, kind
 ("Sudoku-Extreme", "87.4", "2510.04871", "self"), ("Sudoku-Extreme", "74.7", "2510.04871", "self"),
 ("Sudoku-Extreme", "66.8", "2512.14693", "rerun"), ("Sudoku-Extreme", "79.1", "2603.22871", "rerun"),
 ("Sudoku-Extreme", "84.1", "2606.29150", "rerun"), ("Sudoku-Extreme", "84.8", "2605.21488", "rerun"),
 ("Sudoku-Extreme", "87.16", "2603.05234", "rerun"), ("Sudoku-Extreme", "87.9", "2604.18839", "rerun"),
 ("Sudoku-Extreme", "87.28", "2605.19943", "rerun"), ("Sudoku-Extreme", "86.65", "2511.08653", "rerun"),
 ("Sudoku-Extreme", "87.40", "2609.39967", "rerun"), ("Sudoku-Extreme", "71.94", "2603.02193", "rerun"),
 ("Sudoku-Extreme", "72.2", "2602.12078", "rerun"),
 ("Maze-Hard", "85.3", "2510.04871", "self"), ("Maze-Hard", "83.80", "2605.19943", "rerun"),
 ("Maze-Hard", "80.00", "2609.39967", "rerun"), ("Maze-Hard", "78.8", "2609.26487", "rerun"),
 ("Maze-Hard", "60.8", "2602.12078", "rerun"), ("Maze-Hard", "84.2", "2603.22871", "rerun"),
 ("Maze-Hard", "86.6", "2605.25230", "rerun"),
 ("ARC-AGI-1 (pass@2)", "44.6", "2510.04871", "self"), ("ARC-AGI-1 (pass@2)", "40.4", "2511.16886", "rerun"),
 ("ARC-AGI-1 (pass@2)", "44.38", "2603.05234", "rerun"), ("ARC-AGI-1 (pass@2)", "43.88", "2602.12078", "rerun"),
 ("ARC-AGI-1 (pass@2)", "44.60", "2609.39967", "rerun"),
 ("ARC-AGI-2 (pass@2)", "7.8", "2510.04871", "self"), ("ARC-AGI-2 (pass@2)", "3.3", "2511.16886", "rerun"),
 ("ARC-AGI-2 (pass@2)", "6.3", "2604.18839", "rerun"), ("ARC-AGI-2 (pass@2)", "2.50", "2609.39967", "rerun"),
]
cache = {}
def txt(a):
    if a not in cache:
        cache[a] = norm((ROOT / f"data/fulltext/{a}.txt").read_text(errors="ignore"))
    return cache[a]
kept = []
for b, v, a, k in P:
    if v in txt(a):
        kept.append((b, float(v), a, k))
    else:
        print("DROPPED (not found in source):", b, v, a)
BENCH = ["Sudoku-Extreme", "Maze-Hard", "ARC-AGI-1 (pass@2)", "ARC-AGI-2 (pass@2)"]
SURFACE = "#fcfcfb"; INK = "#0b0b0b"; INK2 = "#52514e"; GRID = "#e4e3df"; C_SELF = "#eb6834"; C_RE = "#2a78d6"
fig, axes = plt.subplots(1, 4, figsize=(7.2, 2.5), dpi=200)
fig.patch.set_facecolor(SURFACE)
for ax, b in zip(axes, BENCH):
    ax.set_facecolor(SURFACE)
    pts = [p for p in kept if p[0] == b]
    re = sorted(p[1] for p in pts if p[3] == "rerun"); se = [p[1] for p in pts if p[3] == "self"]
    xs = [(-0.35 + 0.7 * i / max(1, len(re) - 1)) if len(re) > 1 else 0 for i in range(len(re))]
    ax.scatter(xs, re, s=16, color=C_RE, alpha=0.85, edgecolors=SURFACE, linewidths=0.5, zorder=3, label="independent rerun")
    ax.scatter([0.6] * len(se), se, s=44, marker="D", color=C_SELF, edgecolors=SURFACE, linewidths=0.6, zorder=4, label="TRM paper")
    if re:
        ax.plot([-0.45, -0.45], [min(re), max(re)], color=C_RE, lw=1.0, alpha=0.5, zorder=2)
    ax.set_xticks([]); ax.set_xlim(-1, 1)
    ax.set_title(b, fontsize=8.8, color=INK, pad=3)
    for s in ["top", "right", "bottom"]:
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color(INK2); ax.spines["left"].set_linewidth(0.6)
    ax.tick_params(colors=INK2, labelsize=8.1, width=0.6)
    ax.grid(axis="y", color=GRID, linewidth=0.5); ax.set_axisbelow(True)
axes[0].set_ylabel("reported accuracy (%)", fontsize=8.8, color=INK2)
h, l = axes[0].get_legend_handles_labels()
from matplotlib.lines import Line2D
h.append(Line2D([0], [0], color=C_RE, lw=1.0, alpha=0.5)); l.append("range of reruns")
leg = fig.legend(h, l, loc="lower center", ncol=3, fontsize=8.8, frameon=False, bbox_to_anchor=(0.5, -0.03))
for t in leg.get_texts():
    t.set_color(INK)
fig.tight_layout(rect=(0, 0.1, 1, 1))
fig.savefig(ROOT / "paper/figures/fig_replication_spread.pdf", facecolor=SURFACE)
print("kept", len(kept), "of", len(P))

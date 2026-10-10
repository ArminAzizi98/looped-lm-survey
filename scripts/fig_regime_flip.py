#!/usr/bin/env python3
"""Figure: the same looped model wins at matched parameters and ties/loses at matched inference compute.
Data: Table 2 of arXiv:2610.00673 (Closing the Loop). Every value is asserted to occur in the paper text.
dense-ouro-3.9B matches the inference compute of THREE LoopLM iterations (per the table caption)."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
ROOT = Path(__file__).resolve().parents[1]
TXT = (ROOT / "data/fulltext/2610.00673.txt").read_text()
# benchmark: (dense-1.4B, [loop 1..4], dense-3.9B), each "value ± se"
D = {
    "GSM8K":     ("69.14 ± 1.27", ["60.65 ± 1.35", "76.50 ± 1.17", "81.58 ± 1.07", "83.32 ± 1.03"], "82.79 ± 1.04"),
    "DROP (F1)": ("38.59 ± 0.48", ["22.20 ± 0.41", "45.02 ± 0.49", "57.40 ± 0.49", "60.57 ± 0.48"], "58.57 ± 0.49"),
    "MMLU":      ("46.52 ± 0.41", ["40.77 ± 0.41", "52.61 ± 0.41", "55.93 ± 0.40", "56.84 ± 0.40"], "58.15 ± 0.40"),
    "HellaSwag": ("57.28 ± 0.49", ["51.02 ± 0.50", "56.94 ± 0.49", "58.92 ± 0.49", "59.29 ± 0.49"], "67.91 ± 0.47"),
}
for k, (a, ls, b) in D.items():
    for v in [a, b] + ls:
        assert v in TXT, (k, v)
val = lambda s: tuple(float(x) for x in s.split(" ± "))
SURFACE = "#fcfcfb"; INK = "#0b0b0b"; INK2 = "#52514e"; GRID = "#e4e3df"
C_LOOP, C_P, C_F = "#2a78d6", "#eb6834", "#1baf7a"
fig, axes = plt.subplots(1, 4, figsize=(7.2, 2.9), dpi=200)
fig.patch.set_facecolor(SURFACE)
for ax, (name, (a, ls, b)) in zip(axes, D.items()):
    ax.set_facecolor(SURFACE)
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    for s in ["left", "bottom"]:
        ax.spines[s].set_color(INK2); ax.spines[s].set_linewidth(0.6)
    ax.tick_params(colors=INK2, labelsize=8.1, width=0.6)
    ax.grid(axis="y", color=GRID, linewidth=0.5); ax.set_axisbelow(True)
    xs = [1, 2, 3, 4]; ys = [val(x)[0] for x in ls]; es = [val(x)[1] for x in ls]
    pa, pb = val(a), val(b)
    ax.axhline(pa[0], color=C_P, lw=1.0, ls=(0, (4, 2)))
    ax.axhline(pb[0], color=C_F, lw=1.0, ls=(0, (1, 1.5)))
    ax.errorbar(xs, ys, yerr=es, color=C_LOOP, lw=1.4, marker="o", ms=3.5, capsize=1.5, elinewidth=0.6,
                markeredgecolor=SURFACE, markeredgewidth=0.6, zorder=3)
    ax.scatter([3], [ys[2]], s=46, facecolors="none", edgecolors=C_F, linewidths=0.9, zorder=4)
    ax.set_xticks(xs); ax.set_xlabel("iterations", fontsize=8.1, color=INK2, labelpad=1)
    ax.set_title(name, fontsize=9.5, color=INK, pad=3)
axes[0].set_ylabel("score", fontsize=8.1, color=INK2)
from matplotlib.lines import Line2D
handles = [Line2D([], [], color=C_LOOP, lw=1.4, marker="o", ms=3.5, label="LoopLM-1.4B at k iterations"),
           Line2D([], [], color=C_P, lw=1.0, ls=(0, (4, 2)), label="dense 1.4B (matched parameters, data)"),
           Line2D([], [], color=C_F, lw=1.0, ls=(0, (1, 1.5)), label="dense 3.9B (matched inference compute at k=3)")]
leg = fig.legend(handles=handles, loc="lower center", ncol=2, fontsize=8.1, frameon=False, bbox_to_anchor=(0.5, -0.06))
for t in leg.get_texts():
    t.set_color(INK)
fig.tight_layout(rect=(0, 0.16, 1, 1))
fig.savefig(ROOT / "paper/figures/fig_regime_flip.pdf", facecolor=SURFACE, bbox_inches="tight", pad_inches=0.04)
print("ok")

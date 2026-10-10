#!/usr/bin/env python3
"""Figure: quality vs loop count across domains. Each series carries anchor passages copied from its source;
every anchor must occur in the normalized paper text and every plotted value must occur inside an anchor.
A failing series is dropped and reported. mode: 'ckpt' = one checkpoint run at different loop counts;
'trained' = a separate model per loop count (as stated or tabulated in the source)."""
import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from verify_quotes import norm
S = [  # title, source, x, y strings, ylabel, higher_is_better, mode, training loop marker, anchors
 ("Language model (trained $\\bar r{=}8$)", "2607.14427", [1, 8, 16, 32], ["3.80", "3.20", "3.203", "3.203"],
  "validation loss", False, "ckpt", 8,
  ["Loss falls monotonically from 3.80 at one loop to 3.20 at eight, then stays flat: r = 8, 16, and 32 are 3.202, 3.203, and 3.203"]),
 ("Robot policy, RD-VLA ($\\mu_{rec}{=}32$)", "2602.07845", [1, 2, 4, 8, 24], ["8.4", "40.5", "84.1", "92.6", "93.1"],
  "LIBERO success (%)", True, "ckpt", 32,
  ["(8.4% average), the model achieves substantial gains at each doubling of compute: 40.5% at Ninf = 2",
   "84.1% at Ninf = 4 (108% increase), and 92.6% at Ninf = 8", "the peak of 93.1% achieved at Ninf = 24"]),
 ("Multimodal QA, HIVE ($\\bar r{=}32$)", "2602.05359", [1, 32, 64], ["32.82", "91.57", "91.27"],
  "ScienceQA-img (%)", True, "ckpt", 32,
  ["from 32.82% at r = 1 to a peak of 91.57% at r = 32", "91.57% (r = 32) to a slight fluctuation at 91.27% (r = 64)"]),
 ("VLM, LoopVL (trained H2L3; L3 fixed)", "2609.38426", [2, 3, 4], ["63.47", "58.20", "24.00"],
  "MMStar", True, "ckpt", 2,
  ["H3L3 and H4L3 execute 192 and 256 Transformer-layer calls", "MMStar declines from 63.47 to 58.20 and 24.00"]),
 ("Multimodal embedding, ReLoop-UME", "2607.28751", [1, 2, 4, 8], ["60.6", "62.1", "63.2", "62.8"],
  "MMEB-V2 All", True, "trained", None,
  ["T from 1 to 2 improves All from 60.6 to 62.1, and T = 4 reaches 63.2; extending to T = 8 slightly drops to 62.8",
   "Each configuration uses matching training and inference depth"]),
 ("Speech encoder (Latent-Recursive)", "2606.09357", [1, 2, 5, 10, 20], ["2.44", "2.23", "2.16", "2.18", "2.31"],
  "test-clean WER (%)", False, "trained", None,
  ["with WERs of 2.44% (test-clean)", "Introducing two loops (L12 ) improved performance to 2.23%",
   "five loops (L1) yielded the best results: 2.16%", "L110 and L120 resulted in WERs of 2.18% (4.94%) and 2.31% (5.30%)"]),
]
kept = []
for t, a, x, ys, yl, hib, mode, mark, anchors in S:
    tx = norm((ROOT / f"data/fulltext/{a}.txt").read_text(errors="ignore"))
    bad = [an for an in anchors if norm(an) not in tx]
    joined = " ".join(norm(an) for an in anchors)
    miss = [y for y in ys if y not in joined]
    if bad or miss:
        print("DROPPED", a, "anchors missing:", bad, "values outside anchors:", miss)
    else:
        kept.append((t, a, x, [float(y) for y in ys], yl, hib, mode, mark))
SURFACE = "#fcfcfb"; INK = "#0b0b0b"; INK2 = "#52514e"; GRID = "#e4e3df"; C = "#2a78d6"; C2 = "#eb6834"
cols = 3; rows_ = (len(kept) + cols - 1) // cols
fig, axes = plt.subplots(rows_, cols, figsize=(7.2, 2.45 * rows_), dpi=200)
fig.patch.set_facecolor(SURFACE)
axes = axes.flatten()
for ax, (t, a, x, y, yl, hib, mode, mark) in zip(axes, kept):
    ax.set_facecolor(SURFACE)
    col = C if mode == "ckpt" else C2
    face = col if mode == "ckpt" else SURFACE
    ax.plot(x, y, color=col, lw=1.4, ls="-" if mode == "ckpt" else "--", marker="o", ms=3.8,
            markerfacecolor=face, markeredgecolor=col, markeredgewidth=0.9)
    ax.set_xscale("log", base=2)
    if mark is not None:
        ax.axvline(mark, color=INK2, lw=0.7, ls=":")
        lo, hi = ax.get_ylim(); yy = lo if a == "2609.38426" else hi
        right = mark >= max(x)
        ax.text(mark / 1.12 if right else mark * 1.12, yy, f"train={mark}" if mark not in x else "train", fontsize=7.0, color=INK2,
                va="bottom" if yy == lo else "top", ha="right" if right else "left")
    near = mark is not None and any(0.67 < mark / v < 1.5 for v in x)
    ticks = sorted(set(x + ([mark] if mark and not near else [])))
    ax.set_xticks(ticks); ax.set_xticklabels([str(v) for v in ticks]); ax.minorticks_off()
    ax.set_title(t, fontsize=8.5, color=INK, pad=3)
    ax.set_xlabel("high-level cycles H" if a == "2609.38426" else "loops", fontsize=7.8, color=INK2, labelpad=1)
    ax.set_ylabel(yl + ("" if hib else " (lower better)"), fontsize=7.6, color=INK2)
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    for s in ["left", "bottom"]:
        ax.spines[s].set_color(INK2); ax.spines[s].set_linewidth(0.6)
    ax.tick_params(colors=INK2, labelsize=7.6, width=0.6)
    ax.grid(axis="y", color=GRID, linewidth=0.5); ax.set_axisbelow(True)
for ax in axes[len(kept):]:
    ax.axis("off")
fig.tight_layout()
fig.savefig(ROOT / "paper/figures/fig_testtime_loops.pdf", facecolor=SURFACE)
print("kept", len(kept), [k[1] for k in kept])

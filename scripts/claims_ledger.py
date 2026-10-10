#!/usr/bin/env python3
"""Build the claims ledger from extraction records.

Outputs
  data/ledger/claims.csv          every claim: arxiv_id, short_name, group, priority, claim, regimes, scale, location, quote
  data/ledger/summary.json        counts by regime, by group, share of claims per regime, per-paper regime sets
  paper/figures/ledger_stats.tex macros used in the meta-analysis section
Only claims whose evidence quote passes verification are counted.
"""
import csv, glob, json, re, collections
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from verify_quotes import norm, squash

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/ledger"; OUT.mkdir(parents=True, exist_ok=True)
REG = ["iso_param", "iso_train_flop", "iso_infer_flop", "iso_effective_depth", "iso_data", "unmatched", "within_model", "not_applicable"]
ARCH = {"iso_param", "iso_train_flop", "iso_infer_flop", "iso_effective_depth", "iso_data", "unmatched"}


def regimes_of(text):
    t = (text or "").lower().replace("-", "_").replace(" ", "_")
    found = [r for r in REG if r in t]
    if not found and "flop" in t:
        found = ["iso_train_flop" if "train" in t else "iso_infer_flop"]
    return found or ["unclear"]


def scale_params(text):
    """Largest parameter count mentioned in a scale string, in millions (None if absent).
    Token counts (e.g. '800B tokens') are excluded."""
    best = None
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*([KMBT])\b(?![^,;(]*tokens)", text or "", flags=re.I):
        v = float(m.group(1)); u = m.group(2).upper()
        mult = {"K": 1e-3, "M": 1, "B": 1e3, "T": 1e6}[u]
        if u == "T":
            continue  # T almost always denotes tokens in this corpus
        val = v * mult
        best = val if best is None else max(best, val)
    return best


def scale_bin(m):
    if m is None:
        return "unstated"
    if m < 100:
        return "<100M"
    if m < 1000:
        return "100M-1B"
    if m < 10000:
        return "1B-10B"
    return ">=10B"


def main():
    abstracts = {}
    for f in ["data/corpus/candidates.jsonl", "data/corpus/manual_additions.jsonl", "data/corpus/refsnowball_meta.jsonl"]:
        p = ROOT / f
        if p.exists():
            for l in p.open():
                r = json.loads(l)
                if r.get("arxiv_id"):
                    abstracts[r["arxiv_id"]] = r.get("abstract", "")
    prio = {}
    for f in glob.glob(str(ROOT / "data/extract/assign_*.jsonl")):
        for l in open(f):
            r = json.loads(l); prio[r["key"]] = r.get("priority")
    cache = {}
    def ok(aid, q):
        if aid not in cache:
            p = ROOT / f"data/fulltext/{aid}.txt"
            t = (p.read_text(errors="ignore") if p.exists() else "") + "\n" + abstracts.get(aid, "")
            n = norm(t); cache[aid] = (n, squash(n))
        n, s = cache[aid]; nq = norm(q or "")
        return bool(nq) and (nq in n or (len(squash(nq)) >= 12 and squash(nq) in s))
    overrides = {}
    ov = ROOT / "data/ledger/regime_overrides.jsonl"
    if ov.exists():
        for l in ov.open():
            if l.strip():
                o = json.loads(l)
                overrides[(o["arxiv_id"], (o.get("claim") or "")[:80])] = o["regimes"]
    rows, seen = [], set()
    for f in sorted(glob.glob(str(ROOT / "data/extract/*.jsonl"))):
        if "/assign_" in f or "landmarks_me" in f:
            continue
        g = Path(f).stem
        for l in open(f):
            if not l.strip():
                continue
            try:
                r = json.loads(l)
            except Exception:
                continue
            if r.get("relevance") == "out":
                continue
            aid = r.get("arxiv_id")
            for c in r.get("claims") or []:
                key = (aid, (c.get("claim") or "")[:80])
                if key in seen:
                    continue
                seen.add(key)
                rows.append({"arxiv_id": aid, "short_name": r.get("short_name"), "title": r.get("title"), "group": g,
                             "relevance": r.get("relevance"), "priority": prio.get(aid), "paper_type": ";".join(r.get("paper_type") or []),
                             "claim": c.get("claim"), "regimes": ";".join(overrides.get(key) or regimes_of(c.get("regime"))), "scale": c.get("scale"),
                             "location": c.get("location"), "quote": c.get("evidence_quote"),
                             "scale_bin": scale_bin(scale_params(c.get("scale"))),
                             "verified": ok(aid, c.get("evidence_quote"))})
    with (OUT / "claims.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else ["arxiv_id"])
        w.writeheader(); w.writerows(rows)
    ver = [r for r in rows if r["verified"] and r["relevance"] != "adjacent"]
    by_reg = collections.Counter(x for r in ver for x in r["regimes"].split(";"))
    emp = [r for r in ver if set(r["regimes"].split(";")) & ARCH]
    within = [r for r in ver if r["regimes"] == "within_model"]
    only_unmatched = [r for r in emp if r["regimes"] == "unmatched"]
    flop_matched = [r for r in emp if "iso_train_flop" in r["regimes"] or "iso_infer_flop" in r["regimes"]]
    by_scale = collections.Counter(r["scale_bin"] for r in emp)
    by_scale_flop = collections.Counter(r["scale_bin"] for r in flop_matched)
    summ = {"n_within_model_only": len(within), "by_scale_empirical": by_scale, "by_scale_flop_matched": by_scale_flop, "n_claims": len(rows), "n_verified_core": len(ver), "by_regime": by_reg, "n_empirical": len(emp),
            "n_only_unmatched": len(only_unmatched), "n_flop_matched": len(flop_matched),
            "n_papers": len({r["arxiv_id"] for r in ver})}
    json.dump(summ, (OUT / "summary.json").open("w"), indent=1, default=dict)
    pct = lambda a, b: f"{100 * a / b:.0f}" if b else "0"
    with (ROOT / "paper/figures/ledger_stats.tex").open("w") as fh:
        fh.write("% generated by scripts/claims_ledger.py\n")
        fh.write(f"\\newcommand{{\\nLedgerClaims}}{{{len(ver)}}}\n\\newcommand{{\\nLedgerPapers}}{{{summ['n_papers']}}}\n")
        fh.write(f"\\newcommand{{\\nLedgerEmpirical}}{{{len(emp)}}}\n\\newcommand{{\\pctOnlyUnmatched}}{{{pct(len(only_unmatched), len(emp))}}}\n")
        fh.write(f"\\newcommand{{\\pctFlopMatched}}{{{pct(len(flop_matched), len(emp))}}}\n")
        fh.write(f"\\newcommand{{\\nLedgerWithin}}{{{len(within)}}}\n")
        import statistics as _st, collections as _co
        per_paper = _co.Counter(r["arxiv_id"] for r in ver)
        fh.write(f"\\newcommand{{\\nLedgerMedianPerPaper}}{{{int(_st.median(per_paper.values()))}}}\n\\newcommand{{\\nLedgerMaxPerPaper}}{{{max(per_paper.values())}}}\n")
        big = by_scale.get("1B-10B", 0) + by_scale.get(">=10B", 0)
        fh.write(f"\\newcommand{{\\pctEmpiricalBillion}}{{{pct(big, len(emp))}}}\n")
        bigf = by_scale_flop.get("1B-10B", 0) + by_scale_flop.get(">=10B", 0)
        fh.write(f"\\newcommand{{\\nFlopMatchedBillion}}{{{bigf}}}\n")
        for k in REG + ["unclear"]:
            fh.write(f"\\newcommand{{\\nReg{k.replace('_', '').replace('iso', 'Iso')}}}{{{by_reg.get(k, 0)}}}\n")
    print(json.dumps(summ, indent=1, default=dict))


if __name__ == "__main__":
    main()

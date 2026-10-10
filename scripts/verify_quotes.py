#!/usr/bin/env python3
"""Verify that every evidence quote in data/extract/*.jsonl appears verbatim (modulo whitespace,
hyphenation and ligatures) in the paper's full text or its arXiv abstract.

Writes data/extract/verification_report.json and prints a summary. A record whose quote fails
is flagged; failed numbers must not be used in the draft until fixed.
"""
import json, re, sys, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FT = ROOT / "data/fulltext"
EX = ROOT / "data/extract"
CAND = ROOT / "data/corpus/candidates.jsonl"

LIG = {"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl", "’": "'", "‘": "'",
       "“": '"', "”": '"', "–": "-", "—": "-", "−": "-", " ": " "}


def norm(s):
    s = unicodedata.normalize("NFKC", s or "")
    for k, v in LIG.items():
        s = s.replace(k, v)
    s = re.sub(r"-\s*\n\s*", "", s)          # de-hyphenate line breaks
    s = re.sub(r"\s+", " ", s)
    return s.lower().strip()


def squash(s):
    return re.sub(r"[^a-z0-9%.]+", "", s)


def main():
    abstracts = {}
    if CAND.exists():
        for line in CAND.open():
            r = json.loads(line)
            if r.get("arxiv_id"):
                abstracts[r["arxiv_id"]] = r.get("abstract", "")
    cache, report = {}, {"checked": 0, "ok": 0, "fail": 0, "no_text": 0, "failures": []}
    files = [Path(a) for a in sys.argv[1:]] or sorted(p for p in EX.glob("*.jsonl") if not p.name.startswith("assign_") and p.stem != "landmarks_me")
    for f in files:
        for ln, line in enumerate(f.open()):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                report["failures"].append({"file": f.name, "line": ln, "error": "bad json"}); continue
            aid = rec.get("arxiv_id")
            if aid not in cache:
                p = FT / f"{str(aid).replace('/', '_')}.txt"
                txt = p.read_text(errors="ignore") if p.exists() else ""
                txt += "\n" + abstracts.get(aid, "")
                n = norm(txt)
                cache[aid] = (n, squash(n))
            n, sq = cache[aid]
            quotes = []
            for c in rec.get("claims", []) or []:
                quotes.append(("claim", c.get("evidence_quote")))
            for x in rec.get("numbers", []) or []:
                quotes.append(("number", x.get("quote")))
            for kind, q in quotes:
                if not q:
                    continue
                report["checked"] += 1
                if not n.strip():
                    report["no_text"] += 1; continue
                nq = norm(q)
                if nq in n or (len(squash(nq)) >= 12 and squash(nq) in sq):
                    report["ok"] += 1
                else:
                    report["fail"] += 1
                    report["failures"].append({"file": f.name, "arxiv_id": aid, "kind": kind, "quote": q[:200]})
    rep_path = (EX / "verification_report.json") if not sys.argv[1:] else (Path(sys.argv[1]).with_suffix(".verify.json"))
    rep_path.write_text(json.dumps(report, indent=1))
    print({k: v for k, v in report.items() if k != "failures"})
    for x in report["failures"][:40]:
        print("FAIL", x)


if __name__ == "__main__":
    main()

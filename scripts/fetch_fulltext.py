#!/usr/bin/env python3
"""Download arXiv PDFs for the screened corpus and convert to plain text with pdftotext.
PDFs are deleted after conversion (disk is tight). Usage:
  python3 scripts/fetch_fulltext.py data/corpus/ids_to_fetch.txt
"""
import subprocess, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FT = ROOT / "data/fulltext"
FT.mkdir(parents=True, exist_ok=True)
TMP = ROOT / "data/raw/pdf_tmp"
TMP.mkdir(parents=True, exist_ok=True)


def fetch(aid):
    out = FT / f"{aid.replace('/', '_')}.txt"
    if out.exists() and out.stat().st_size > 2000:
        return "cached"
    pdf = TMP / f"{aid.replace('/', '_')}.pdf"
    url = f"https://export.arxiv.org/pdf/{aid}"
    req = urllib.request.Request(url, headers={"User-Agent": "looped-lm-survey (academic research)"})
    for attempt in range(4):
        try:
            data = urllib.request.urlopen(req, timeout=120).read()
            if data[:4] != b"%PDF":
                raise ValueError("not a pdf")
            pdf.write_bytes(data)
            break
        except Exception as e:
            print(f"  retry {attempt} {aid}: {e}", file=sys.stderr, flush=True)
            time.sleep(15 * (attempt + 1))
    else:
        return "fail"
    r = subprocess.run(["pdftotext", "-enc", "UTF-8", str(pdf), str(out)], capture_output=True)
    pdf.unlink(missing_ok=True)
    if r.returncode != 0 or not out.exists():
        return "convert_fail"
    return "ok"


def main():
    ids = [l.strip() for l in open(sys.argv[1]) if l.strip()]
    stats = {}
    for i, aid in enumerate(ids):
        s = fetch(aid)
        stats[s] = stats.get(s, 0) + 1
        if s != "cached":
            time.sleep(3.5)
        if i % 20 == 0:
            print(f"{i+1}/{len(ids)} {stats}", flush=True)
    print("done", stats, flush=True)


if __name__ == "__main__":
    main()

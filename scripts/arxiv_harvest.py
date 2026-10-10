#!/usr/bin/env python3
"""Stage 1 of corpus construction: harvest arXiv candidates with one phrase per query.

arXiv's API handles single-phrase field queries reliably; boolean groupings are loose,
so every phrase is queried separately and the results are unioned. Output:
data/corpus/arxiv_candidates.jsonl (one record per arXiv id, with the queries that hit it).
"""
import json, time, sys, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/corpus/arxiv_candidates.jsonl"
RAW = ROOT / "data/raw/arxiv"
RAW.mkdir(parents=True, exist_ok=True)
NS = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

PHRASES = [
    # core naming used by the field
    "looped transformer", "looped transformers", "looped language model", "looped language models",
    "LoopLM", "looped model", "looped models", "loop transformer", "looped architecture",
    "recurrent depth", "recurrent-depth", "depth-recurrent", "depth recurrence", "depth-wise recurrence",
    "recursive transformer", "recursive transformers", "recursion depth", "mixture-of-recursions",
    "mixture of recursions", "universal transformer", "universal transformers",
    "weight-tied transformer", "weight-tied layers", "weight tying across layers", "cross-layer parameter sharing",
    "parameter sharing across layers", "layer sharing", "shared layers", "shared block", "layer reuse",
    "layer looping", "repeated layers", "iterative depth", "latent iterations", "latent recurrence",
    # adaptive computation lineage
    "adaptive computation time", "pondernet", "pondering", "ponder", "dynamic depth", "adaptive depth",
    # recursive reasoning models
    "hierarchical reasoning model", "tiny recursive model", "recursive reasoning", "recursive latent",
    # latent reasoning (adjacent, screened later)
    "latent reasoning", "implicit reasoning", "latent thoughts", "continuous thought", "latent chain-of-thought",
    # implicit / fixed point
    "deep equilibrium", "fixed-point iteration transformer", "implicit transformer",
    # algorithmic extrapolation lineage
    "logical extrapolation", "deep thinking networks", "algorithm synthesis recurrent",
]
FIELDS = ["abs", "ti"]
PAGE = 300


def query(q, start):
    url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode(
        {"search_query": q, "start": start, "max_results": PAGE,
         "sortBy": "submittedDate", "sortOrder": "descending"})
    for attempt in range(5):
        try:
            return urllib.request.urlopen(url, timeout=90).read()
        except Exception as e:  # network hiccups and 503s
            print(f"  retry {attempt} {q} start={start}: {e}", file=sys.stderr)
            time.sleep(10 * (attempt + 1))
    return None


def parse(xml_bytes):
    root = ET.fromstring(xml_bytes)
    out = []
    for e in root.findall("a:entry", NS):
        idurl = e.find("a:id", NS).text.strip()
        if "/abs/" not in idurl:
            continue
        vid = idurl.split("/abs/")[-1]
        base = vid.rsplit("v", 1)[0] if "v" in vid.split("/")[-1] else vid
        out.append({
            "arxiv_id": base,
            "version": vid,
            "title": " ".join(e.find("a:title", NS).text.split()),
            "abstract": " ".join(e.find("a:summary", NS).text.split()),
            "published": e.find("a:published", NS).text[:10],
            "updated": e.find("a:updated", NS).text[:10],
            "authors": [a.find("a:name", NS).text for a in e.findall("a:author", NS)],
            "categories": [c.attrib["term"] for c in e.findall("a:category", NS)],
            "primary_category": (e.find("arxiv:primary_category", NS).attrib.get("term")
                                 if e.find("arxiv:primary_category", NS) is not None else None),
            "journal_ref": (e.find("arxiv:journal_ref", NS).text if e.find("arxiv:journal_ref", NS) is not None else None),
        })
    return out


def main():
    recs = {}
    if OUT.exists():
        for line in OUT.open():
            r = json.loads(line); recs[r["arxiv_id"]] = r
    for ph in PHRASES:
        for f in FIELDS:
            q = f'{f}:"{ph}"'
            start, total_q = 0, 0
            while True:
                data = query(q, start)
                if data is None:
                    break
                items = parse(data)
                for it in items:
                    r = recs.setdefault(it["arxiv_id"], {**it, "hits": []})
                    if q not in r["hits"]:
                        r["hits"].append(q)
                total_q += len(items)
                time.sleep(3.2)
                if len(items) < PAGE or start + PAGE >= 3000:
                    break
                start += PAGE
            print(f"{q:55s} -> {total_q:5d}   (corpus={len(recs)})", flush=True)
    with OUT.open("w") as fh:
        for r in recs.values():
            fh.write(json.dumps(r) + "\n")
    print("wrote", OUT, len(recs))


if __name__ == "__main__":
    main()

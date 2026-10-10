#!/usr/bin/env python3
"""Gap map: number of core papers whose title+abstract match each topic's patterns.
Keyword matching on abstracts is a coarse screen; counts are reported with the matching papers
listed in data/corpus/gap_map.json so every count can be audited."""
import json, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
TOPICS = {
 "Knowledge editing / unlearning": r"knowledge edit|model edit|unlearn|\brome\b|memit",
 "Memorization / privacy": r"memoriz|membership inference|extraction attack|privacy|differential(ly)? private",
 "Safety alignment / jailbreaks / refusal": r"jailbreak|refusal|harmful|safety alignment|red.team|guardrail",
 "Monitorability / faithfulness": r"monitorab|faithful|steganograph|encoded reasoning|sandbag|decepti|scheming",
 "Adversarial robustness": r"adversarial",
 "Hallucination / calibration / uncertainty": r"hallucinat|calibrat|uncertaint|abstain|abstention",
 "Multilingual": r"multilingual|cross.lingual|low.resource language",
 "Long context / retrieval": r"long.context|long context|needle|retrieval.augmented|\brag\b",
 "Agents / tool use": r"\bagent(s|ic)?\b|tool.(use|call)",
 "Continual / test-time training": r"continual learning|test.time training|lifelong",
 "Data curricula for recurrence": r"curricul|data mixture|data selection",
 "Fairness / bias": r"fairness|\bbias(es)?\b against|demographic",
 "Energy / carbon accounting": r"energy consumption|carbon|joule",
 "Quantization / compression": r"quantiz|pruning|compress",
 "KV cache / memory": r"kv.cache|key.value cache|kv cache",
 "Speculative / parallel decoding": r"speculative|parallel decoding|draft",
 "Scaling laws": r"scaling law",
 "Interpretability": r"interpretab|mechanis|logit lens|probing|probe",
 "Theory / expressivity": r"expressiv|turing|circuit complexity|theorem|provabl",
 "Length generalization": r"length generali|extrapolat",
}
core = [json.loads(l) for l in (ROOT / "data/corpus/screened.jsonl").open() if l.strip()]
core = [r for r in core if r["decision"] == "C"]
out = {}
for t, pat in TOPICS.items():
    rx = re.compile(pat, re.I)
    hits = [{"key": r["key"], "title": r.get("title")} for r in core if rx.search((r.get("title") or "") + " " + (r.get("abstract") or ""))]
    out[t] = {"count": len(hits), "papers": hits}
json.dump(out, (ROOT / "data/corpus/gap_map.json").open("w"), indent=1)
for t, v in sorted(out.items(), key=lambda x: x[1]["count"]):
    print(f"{v['count']:4d}  {t}")

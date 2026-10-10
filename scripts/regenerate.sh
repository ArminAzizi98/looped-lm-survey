#!/bin/sh
# Regenerate the count macros, tables and data figures in paper/figures/ from the files in data/.
# Steps that need full texts run only if data/fulltext/ exists (see README).
set -e
cd "$(dirname "$0")/.."
if [ -d data/fulltext ]; then
  python3 scripts/verify_quotes.py
  python3 scripts/claims_ledger.py > /dev/null
fi
python3 scripts/make_counts.py > /dev/null
python3 scripts/corpus_table.py
python3 scripts/gap_table.py > /dev/null
python3 scripts/ledger_appendix.py
python3 scripts/make_figures.py > /dev/null
python3 scripts/fig_ledger_heatmap.py
if [ -d data/fulltext ]; then
  python3 scripts/coverage_vs_surveys.py
  python3 scripts/fig_recurrence_worth.py
  python3 scripts/fig_regime_flip.py
  python3 scripts/fig_replication_spread.py
  python3 scripts/fig_testtime_loops.py
else
  echo "data/fulltext/ not found: skipped the quote check, claims ledger, survey coverage and four figures."
  echo "Run: python3 scripts/fetch_fulltext.py data/corpus/fulltext_ids.txt"
fi

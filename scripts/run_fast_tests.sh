#!/usr/bin/env bash
#
# Run each repo's FAST test suite — the same set CI runs on a push to `development`. egm-studio's
# GUI tests (~2-3 s of Qt startup apiece) are excluded via `-m "not gui"`; the full suite runs on
# a PR into `release`, so run the whole thing there before shipping a phase.
#
# Developer setup is one venv per repo (see docs/quick_start.md), so this uses each repo's own
# .venv when present and skips repos that don't have one.
#
#   bash intracardiac-platform/scripts/run_fast_tests.sh                 # every repo with a .venv
#   bash intracardiac-platform/scripts/run_fast_tests.sh egm-classifier  # just the named repos
#
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

ALL=(egm-contracts egm-data egm-signal egm-features
     iafdb-pipeline synthetic-egm-pipeline egm-classifier egm-studio)
if [ "$#" -gt 0 ]; then REPOS=("$@"); else REPOS=("${ALL[@]}"); fi

fail=0
for r in "${REPOS[@]}"; do
  d="$ROOT/$r"
  if [ ! -d "$d" ]; then
    echo "skip  $r (not found under $ROOT)"; continue
  fi
  py="$d/.venv/bin/python"
  if [ ! -x "$py" ]; then
    echo "skip  $r (no .venv — 'cd $r && python -m venv .venv && . .venv/bin/activate && pip install -e .[dev]')"
    continue
  fi
  if [ "$r" = "egm-studio" ]; then
    echo "==>   $r  (fast set: -m 'not gui', headless Qt)"
    ( cd "$d" && QT_QPA_PLATFORM=offscreen "$py" -m pytest -q -m "not gui" ) || fail=1
  else
    echo "==>   $r"
    ( cd "$d" && "$py" -m pytest -q ) || fail=1
  fi
done

if [ "$fail" -eq 0 ]; then
  echo "All fast suites passed."
else
  echo "SOME SUITES FAILED."; exit 1
fi

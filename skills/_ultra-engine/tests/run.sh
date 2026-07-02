#!/bin/bash
# Runs the whole _ultra-engine suite. Usage: bash skills/_ultra-engine/tests/run.sh
set -u
cd "$(dirname "$0")" || exit 1
command -v jq >/dev/null || { echo "jq is required"; exit 1; }
command -v python3 >/dev/null || { echo "python3 is required"; exit 1; }
total_fail=0
for t in test_*.sh; do
  [ -e "$t" ] || continue
  echo "== $t"
  bash "$t" || total_fail=$((total_fail+1))
done
if ls test_*.py >/dev/null 2>&1; then
  echo "== python unittests"
  python3 -m unittest discover -s . -p 'test_*.py' -v 2>&1 | tail -3
  python3 -m unittest discover -s . -p 'test_*.py' >/dev/null 2>&1 || total_fail=$((total_fail+1))
fi
[ "$total_fail" -eq 0 ] && echo "ALL PASS" || { echo "SUITES FAILED: $total_fail"; exit 1; }

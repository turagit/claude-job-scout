#!/bin/bash
# Deferred JD-fetch queue. See test for the contract.
set -eu
cmd="$1"; q="$2"
ensure() { [ -f "$q" ] || { mkdir -p "$(dirname "$q")"; echo '{"queue": []}' > "$q"; }; }
case "$cmd" in
  count) [ -f "$q" ] && jq '.queue|length' "$q" || echo 0;;
  push)
    ensure; add="$3"
    jq --slurpfile new "$add" '
      (.queue | map(.id)) as $have
      | .queue += ($new[0] | map(select(.id as $i | $have | index($i) | not)))' "$q" > "$q.tmp" \
      && jq -e . "$q.tmp" >/dev/null && mv "$q.tmp" "$q"
    ;;
  pop)
    ensure; n="$3"
    jq --argjson n "$n" '.queue[:$n]' "$q"
    jq --argjson n "$n" '.queue |= .[$n:]' "$q" > "$q.tmp" && jq -e . "$q.tmp" >/dev/null && mv "$q.tmp" "$q"
    ;;
  *) echo "usage: jd_queue.sh count|push|pop <queue.json> [entries.json|N]" >&2; exit 2;;
esac

#!/bin/bash
# Deferred JD-fetch queue, namespaced by origin. See test for the contract.
# An entry's "origin" marks which command queued it (e.g. "notifications"). Entries with no
# origin, or origin "ultramode", are legacy/ultramode's own — the default filter when no
# [origin] arg is given. count/pop with an explicit [origin] only ever touch that origin's
# entries; everything else stays in the queue, in order.
set -eu
cmd="$1"; q="$2"
ensure() { [ -f "$q" ] || { mkdir -p "$(dirname "$q")"; echo '{"queue": []}' > "$q"; }; }
case "$cmd" in
  count)
    origin="${3-}"
    if [ ! -f "$q" ]; then echo 0
    elif [ -n "$origin" ]; then jq --arg o "$origin" '[.queue[] | select(.origin == $o)] | length' "$q"
    else jq '[.queue[] | select((.origin // "ultramode") == "ultramode")] | length' "$q"
    fi
    ;;
  push)
    ensure; add="$3"; origin="${4-}"
    if [ -n "$origin" ]; then
      jq --slurpfile new "$add" --arg o "$origin" '
        (.queue | map(.id)) as $have
        | .queue += ($new[0] | map(select(.id as $i | $have | index($i) | not)) | map(. + {origin: $o}))' "$q" > "$q.tmp" \
        && jq -e . "$q.tmp" >/dev/null && mv "$q.tmp" "$q"
    else
      jq --slurpfile new "$add" '
        (.queue | map(.id)) as $have
        | .queue += ($new[0] | map(select(.id as $i | $have | index($i) | not)))' "$q" > "$q.tmp" \
        && jq -e . "$q.tmp" >/dev/null && mv "$q.tmp" "$q"
    fi
    ;;
  pop)
    ensure; n="$3"; origin="${4-}"
    if [ -n "$origin" ]; then
      out=$(jq --argjson n "$n" --arg o "$origin" '[.queue[] | select(.origin == $o)] | .[:$n]' "$q")
    else
      out=$(jq --argjson n "$n" '[.queue[] | select((.origin // "ultramode") == "ultramode")] | .[:$n]' "$q")
    fi
    printf '%s\n' "$out"
    ids=$(printf '%s' "$out" | jq -c 'map(.id)')
    jq --argjson popped "$ids" '.queue |= map(select(.id as $i | ($popped | index($i)) | not))' "$q" > "$q.tmp" \
      && jq -e . "$q.tmp" >/dev/null && mv "$q.tmp" "$q"
    ;;
  *) echo "usage: jd_queue.sh count|push|pop <queue.json> [entries.json|N] [origin]" >&2; exit 2;;
esac

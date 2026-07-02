#!/bin/bash
# Usage: scorecard.sh <run-dir> <tracker.json> <today>
set -eu
rd="$1"; tracker="$2"; today="$3"
sweeps="[]"
for f in "$rd"/sweep-*.json; do
  [ -e "$f" ] || continue
  n=$(basename "$f" .json); n=${n#sweep-}
  sweeps=$(jq -n --argjson acc "$sweeps" --arg n "$n" --slurpfile e "$f" \
    '$acc + [{key: $n, value: {scanned: ($e[0].counts.scanned // 0), matched: ($e[0].counts.matched // 0),
      dropped_explicit_violation: ($e[0].counts.dropped_explicit_violation // 0),
      returned: ($e[0].counts.returned // 0), capped: ($e[0].counts.capped // false),
      errors: ($e[0].errors | length)}}]')
done
merge='{}'; [ -f "$rd/merge.json" ] && merge=$(cat "$rd/merge.json")
jdf='{"budget": 0, "used": 0, "deferred": 0}'; [ -f "$rd/jd-fetch.json" ] && jdf=$(cat "$rd/jd-fetch.json")
rot='{"picked": [], "rotated_out": []}'; [ -f "$rd/rotation.json" ] && rot=$(cat "$rd/rotation.json")
jq -n --arg today "$today" --argjson sweeps "$sweeps" --argjson merge "$merge" \
      --argjson jdf "$jdf" --argjson rot "$rot" --slurpfile t "$tracker" '
  [ $t[0].jobs | to_entries[] | .value | select(.first_seen == $today) ] as $new
  | {date: $today,
     sources: ($sweeps | from_entries),
     dedupe: {merged: ($merge.merged // 0), collisions_also_seen: ($merge.collisions_also_seen // 0),
              url_upgrades: ($merge.url_upgrades // 0), skipped_known: ($merge.skipped_known // 0)},
     jd_fetch: $jdf, rotation: $rot,
     gating: {gated: ([ $new[] | select(.tier == "D") ] | length),
              by_kind: ([ $new[] | (.gate_violations // [])[] | .kind ] | group_by(.) | map({(.[0]): length}) | add // {}),
              near_miss: ([ $new[] | select(.near_miss == true) ] | length)},
     tiers: ([ $new[] | .tier // "untiered" ] | group_by(.) | map({(.[0]): length}) | add // {}
             | {A: (.A // 0), B: (.B // 0), C: (.C // 0), D: (.D // 0), untiered: (.untiered // 0)}),
     disclosures:
       ( [ $sweeps[] | select(.value.capped) | "\(.key): results capped — \(.value.returned) of \(.value.matched - .value.dropped_explicit_violation) lane matches returned" ]
       + [ $sweeps[] | select(.value.errors > 0) | "\(.key): \(.value.errors) sweep error(s) — see envelope" ]
       + (if ($jdf.deferred // 0) > 0 then ["JD fetches: \($jdf.used) of budget \($jdf.budget) used — \($jdf.deferred) deferred to next run"] else [] end)
       + [ $rot.rotated_out[]? | "rotated out this run: \(.) (swept on its next rotation slot)" ] ) }
' > "$rd/scorecard.json.tmp" && jq -e . "$rd/scorecard.json.tmp" >/dev/null && mv "$rd/scorecard.json.tmp" "$rd/scorecard.json"
cat "$rd/scorecard.json"

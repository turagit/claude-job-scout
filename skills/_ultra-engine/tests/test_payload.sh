#!/bin/bash
. "$(dirname "$0")/helpers.sh"
P="$(dirname "$0")/../scripts/payload.sh"; FXD="$(dirname "$0")/fixtures"
rd=$(mktemp -d); echo '{"date": "2026-07-02", "disclosures": []}' > "$rd/scorecard.json"
out=$(bash "$P" "$FXD/tracker-payload.json" "$rd" "2026-07-02" 12)
assert_eq "a__a__3 a__a__2 a__a__1 a__a__5" "$(echo "$out" | jq -r '[.results[].id]|join(" ")')" \
  "A first; within B high-conf before low; two-gate D last; near-miss excluded from results"
assert_eq "a__a__4" "$(echo "$out" | jq -r '.near_misses[0].id')" "near-miss lifted to rail"
assert_eq "A" "$(echo "$out" | jq -r '.near_misses[0].would_be_tier')" "would-be tier carried"
assert_eq "1" "$(echo "$out" | jq '.tier_counts.a')" "tier counts"
assert_eq "false" "$(echo "$out" | jq '.results[0]|has("confidence")')" "omit-when-absent (no null injection)"
assert_eq "ultramode-2026-07-02.html" "$(echo "$out" | jq -r '.filename')" "filename"
assert_eq "2026-07-02" "$(echo "$out" | jq -r '.scorecard.date')" "scorecard embedded"
finish

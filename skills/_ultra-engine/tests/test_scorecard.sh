#!/bin/bash
. "$(dirname "$0")/helpers.sh"
SC="$(dirname "$0")/../scripts/scorecard.sh"; FXD="$(dirname "$0")/fixtures"
rd=$(mktemp -d)
cp "$FXD/delta-good.json" "$rd/sweep-remotive.json"
echo '{"status": "ok", "counts": {"scanned": 0, "matched": 0, "dropped_explicit_violation": 0, "returned": 0, "capped": false}, "deltas": [], "errors": [{"code": "no_api_key", "message": "Skipped adzuna (no API key)"}], "continuation_cursor": null}' > "$rd/sweep-failed.json"
echo '{"merged": 1, "collisions_also_seen": 0, "url_upgrades": 0, "skipped_known": 2}' > "$rd/merge.json"
echo '{"budget": 75, "used": 3, "deferred": 2}' > "$rd/jd-fetch.json"
echo '{"picked": ["Malt"], "rotated_out": ["Toptal", "Worksome"]}' > "$rd/rotation.json"
echo '{"errors": [{"stage": "merge", "message": "MERGE ABORTED (validation): jobs[4001].tier bad"}]}' > "$rd/pipeline-errors.json"
bash "$SC" "$rd" "$FXD/tracker-mini.json" "2026-06-01" > /dev/null
assert_ok test -f "$rd/scorecard.json"
assert_eq "6" "$(jq '.sources["remotive"].matched' "$rd/scorecard.json")" "source counts lifted"
assert_eq "1" "$(jq '.dedupe.merged' "$rd/scorecard.json")" "merge summary lifted"
assert_eq "2" "$(jq '.jd_fetch.deferred' "$rd/scorecard.json")" "jd fetch lifted"
assert_eq "1" "$(jq '.tiers.B' "$rd/scorecard.json")" "tiers over first_seen==today"
assert_eq "true" "$(jq '[.disclosures[]|select(test("capped"))]|length > 0' "$rd/scorecard.json")" "cap disclosed"
assert_eq "true" "$(jq '[.disclosures[]|select(test("Toptal"))]|length > 0' "$rd/scorecard.json")" "rotation disclosed"
assert_eq "true" "$(jq '[.disclosures[]|select(test("no API key"))]|length > 0' "$rd/scorecard.json")" "sweep failure message disclosed"
assert_eq "true" "$(jq '[.disclosures[]|select(test("pipeline merge"))]|length > 0' "$rd/scorecard.json")" "pipeline error disclosed"
# a null-kind violation must fold to "unknown", never crash the scorecard
tmp_tracker=$(mktemp)
jq '.jobs["4001"].gate_violations = [{"kind": null, "detail": "malformed"}]' "$FXD/tracker-mini.json" > "$tmp_tracker"
rd2=$(mktemp -d)
bash "$SC" "$rd2" "$tmp_tracker" "2026-06-01" > /dev/null
assert_eq "1" "$(jq '.gating.by_kind.unknown' "$rd2/scorecard.json")" "null kind folds to unknown"
rm -f "$tmp_tracker"
finish

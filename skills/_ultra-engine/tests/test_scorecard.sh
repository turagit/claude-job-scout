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
# malformed violations must never crash the scorecard: null kind folds to
# "unknown", and a plain-string violation (legacy writer shape, seen live
# 2026-07-03) counts under its own label
tmp_tracker=$(mktemp)
jq '.jobs["4001"].gate_violations = [{"kind": null, "detail": "malformed"}, "legacy-string-reason"]' "$FXD/tracker-mini.json" > "$tmp_tracker"
rd2=$(mktemp -d)
bash "$SC" "$rd2" "$tmp_tracker" "2026-06-01" > /dev/null
assert_eq "1" "$(jq '.gating.by_kind.unknown' "$rd2/scorecard.json")" "null kind folds to unknown"
assert_eq "1" "$(jq '.gating.by_kind["legacy-string-reason"]' "$rd2/scorecard.json")" "string violation counts under its own label"
rm -f "$tmp_tracker"

# Phase 16: five-way accounting + missing-artifact disclosures
rd2=$(mktemp -d)
cat > "$rd2/sweep-ok.json" <<'EOF'
{"status":"ok","counts":{"scanned":10,"matched":3,"dropped_explicit_violation":1,"returned":2,"capped":false},"deltas":[],"errors":[],"continuation_cursor":null}
EOF
cat > "$rd2/sweep-blocked.json" <<'EOF'
{"status":"ok","counts":{"scanned":0,"matched":0,"dropped_explicit_violation":0,"returned":0,"capped":false},"deltas":[],"errors":[{"code":"login_required","message":"Malt needs sign-in — sign in in the open Chrome tab, then run /ultramode source Malt"}],"continuation_cursor":null}
EOF
cat > "$rd2/sweep-dead.json" <<'EOF'
{"status":"ok","counts":{"scanned":0,"matched":0,"dropped_explicit_violation":0,"returned":0,"capped":false},"deltas":[],"errors":[{"code":"sweep_failed","message":"layout dead"}],"continuation_cursor":null}
EOF
echo '{"picked":["Malt"],"rotated_out":["Toptal","YunoJuno"],"mode":"super"}' > "$rd2/rotation.json"
echo '{"jobs":{}}' > "$rd2/tracker-empty.json"
out2=$(bash "$SC" "$rd2" "$rd2/tracker-empty.json" 2026-07-14)
assert_eq "super" "$(printf '%s' "$out2" | jq -r .accounting.mode)" "mode from rotation.json"
assert_eq "3" "$(printf '%s' "$out2" | jq -r .accounting.attempted)" "attempted counts envelopes"
assert_eq "1" "$(printf '%s' "$out2" | jq -r .accounting.completed)" "completed excludes blocked+failed"
assert_eq "1" "$(printf '%s' "$out2" | jq -r .accounting.login_blocked)" "login_required counted"
assert_eq "1" "$(printf '%s' "$out2" | jq -r .accounting.failed)" "failure counted"
assert_eq "2" "$(printf '%s' "$out2" | jq -r .accounting.rotated_out)" "rotated_out from rotation.json"
assert_eq "1" "$(printf '%s' "$out2" | jq '[.disclosures[]|select(test("jd-fetch.json artifact missing"))]|length')" "missing jd-fetch disclosed"
assert_eq "1" "$(printf '%s' "$out2" | jq '[.disclosures[]|select(test("merge.json artifact missing"))]|length')" "missing merge disclosed"
rm -rf "$rd2"

# Phase 16 final-review: similar-jobs expansion excluded from five-way counters
rd3=$(mktemp -d)
cat > "$rd3/sweep-linkedin.json" <<'EOF'
{"status":"ok","counts":{"scanned":5,"matched":3,"dropped_explicit_violation":0,"returned":2,"capped":false},"deltas":[],"errors":[],"continuation_cursor":null}
EOF
cat > "$rd3/sweep-linkedin-similar.json" <<'EOF'
{"status":"ok","counts":{"scanned":3,"matched":1,"dropped_explicit_violation":0,"returned":1,"capped":false},"deltas":[],"errors":[],"continuation_cursor":null}
EOF
echo '{"picked":[],"rotated_out":[],"mode":"bare"}' > "$rd3/rotation.json"
echo '{"jobs":{}}' > "$rd3/tracker-empty.json"
out3=$(bash "$SC" "$rd3" "$rd3/tracker-empty.json" 2026-07-14)
assert_eq "1" "$(printf '%s' "$out3" | jq -r .accounting.attempted)" "similar-jobs sweep excluded from attempted"
assert_eq "1" "$(printf '%s' "$out3" | jq -r .accounting.completed)" "similar-jobs sweep excluded from completed"
assert_eq "true" "$(printf '%s' "$out3" | jq '.sources | has("linkedin-similar")')" "similar-jobs still present in sources breakdown"
rm -rf "$rd3"

finish

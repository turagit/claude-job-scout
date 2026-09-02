#!/bin/bash
. "$(dirname "$0")/helpers.sh"
P="$(dirname "$0")/../scripts/payload_notifications.sh"; T="$(dirname "$0")/fixtures/p17-tracker-run.json"
rd=$(mktemp -d)
printf '{"date":"2026-09-02","coverage":{"rows":[{"alert_key":"k1","keywords":"x","pages_walked":2,"stop_reason":"divider","status":"complete","cards_seen":49,"before_divider":24,"known":10,"reposts":1,"new":13}],"totals":{"alerts":1,"complete":1,"partial":0,"cards_seen":49,"before_divider":24,"known":10,"reposts":1,"new":13},"reposts_disclosed":1},"budget":{"limit":150,"used":13,"queued":0},"disclosures":[]}' > "$rd/scorecard.json"
printf '[{"id":"1777","matched_id":"1001","alert_key":"k1","title":"Lead Platform Engineer","company":"Acme","location":"Amsterdam (Remote)"}]' > "$rd/reposts.json"
printf '[{"id":"1888","title":"Queued role","company":"Eps","location":"Remote","url":"https://www.linkedin.com/jobs/view/1888/","alert_key":"k1"}]' > "$rd/queued.json"
out=$(bash "$P" "$T" "$rd" 2026-09-02 fresh)
assert_eq "check-job-notifications-2026-09-02.html" "$(echo "$out" | jq -r .filename)" "filename"
assert_eq "1001 1005 1002 1004" "$(echo "$out" | jq -r '[.results[].id]|join(" ")')" "today only, tier order, malformed posted_at handled"
assert_json_eq '{"a":1,"b":3,"c":0,"d":1,"total":5}' "$(echo "$out" | jq -c .tier_counts)" "tier counts"
assert_eq "Job Alert" "$(echo "$out" | jq -r '.results[0].source')" "structured source rendered as board string"
assert_eq "Job Alert" "$(echo "$out" | jq -r '.near_misses[0].source')" "legacy string source in near-miss rail"
assert_eq "true" "$(echo "$out" | jq -r '.results[0].fresh')" "A-tier posted today is fresh"
assert_eq "false" "$(echo "$out" | jq -r '.results[1].fresh')" "B-tier invalid calendar date (2026-13-01) is not fresh, and does not abort"
assert_eq "false" "$(echo "$out" | jq -r '.results[2].fresh')" "B-tier 8 days old is not fresh"
assert_eq "false" "$(echo "$out" | jq -r '.results[3].fresh')" "B-tier malformed posted_at is not fresh"
assert_eq "null" "$(echo "$out" | jq -r '.results[3].confidence // "null"')" "absent optional field omitted"
assert_eq "1" "$(echo "$out" | jq '.near_misses|length')" "near-miss rail"
assert_eq "1" "$(echo "$out" | jq '.coverage.rows|length')" "coverage passed through"
assert_eq "1888" "$(echo "$out" | jq -r '.queued[0].id')" "queued passed through"
assert_eq "1777" "$(echo "$out" | jq -r '.reposts[0].id')" "reposts passed through"
assert_eq "fresh" "$(echo "$out" | jq -r .run_status)" "run status"
ns=$(bash "$P" "$T" "$rd" 2026-09-02 no_scrape "browser unavailable")
assert_eq "browser unavailable" "$(echo "$ns" | jq -r .no_scrape_reason)" "no_scrape reason"
assert_eq "0" "$(echo "$ns" | jq '.results|length')" "no_scrape renders no new results"
finish

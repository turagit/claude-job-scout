#!/bin/bash
# Usage: payload_notifications.sh <tracker.json> <run-dir> <today> <fresh|no_scrape> [<no_scrape_reason>]
# The check-job-notifications render payload. Ordering lives here, never in the template or prose.
set -eu
tracker="$1"; rd="$2"; today="$3"; status="$4"; reason="${5-}"
jq -e . "$tracker" >/dev/null || { echo "payload_notifications: bad input ($tracker)" >&2; exit 1; }
sc='{}'; [ -f "$rd/scorecard.json" ] && sc=$(cat "$rd/scorecard.json")
jq -e . <<<"$sc" >/dev/null || { echo "payload_notifications: bad input ($rd/scorecard.json)" >&2; exit 1; }
rep='[]'; [ -f "$rd/reposts.json" ] && rep=$(cat "$rd/reposts.json")
jq -e . <<<"$rep" >/dev/null || { echo "payload_notifications: bad input ($rd/reposts.json)" >&2; exit 1; }
que='[]'; [ -f "$rd/queued.json" ] && que=$(cat "$rd/queued.json")
jq -e . <<<"$que" >/dev/null || { echo "payload_notifications: bad input ($rd/queued.json)" >&2; exit 1; }
jq -n --arg today "$today" --arg status "$status" --arg reason "$reason" \
      --argjson sc "$sc" --argjson rep "$rep" --argjson que "$que" --slurpfile t "$tracker" '
  def tier_rank: {"A": 0, "B": 1, "C": 2, "D": 3, "untiered": 4}[.tier // "untiered"] // 4;
  def conf_rank: {"high": 0, "med": 1, "low": 2}[.confidence // "absent"] // 3;
  def comp_rank: if ((.salary_text // "") != "" or ((.signals // {}).rate // "") != "") then 0 else 1 end;
  def date_num: ((.posted_at // "") | if . == "" then "0000-00-00" else . end) | gsub("-"; "") | tonumber;
  def board: if (.source | type) == "object" then (.source.board // "Job Alert") else ((.source // "Job Alert") | tostring) end;
  def days_old: (($today | strptime("%Y-%m-%d") | mktime) - ((.posted_at // "1970-01-01") | strptime("%Y-%m-%d") | mktime)) / 86400;
  def opt(k): if (.[k] // null) == null then {} else {(k): .[k]} end;
  def card: {id: .id, title: .title, company: .company, location: (.location // ""), received_at: .first_seen,
             posted_at: (.posted_at // ""), source: board, tier: (.tier // "untiered"), tier_reason: (.tier_reason // null),
             dimensions: (.dimensions // {}), gate_violations: (.gate_violations // []),
             fresh: ((.tier == "A" or .tier == "B") and (.posted_at // "") != "" and days_old <= 2),
             seen: false, preview: "", url: (.url // "")}
            + opt("competitiveness") + opt("competitiveness_evidence") + opt("confidence") + opt("match_explanation_tag");
  ([ $t[0].jobs | to_entries[] | .value | select(.first_seen == $today) ]
     | if $status == "no_scrape" then [] else . end) as $new
  | [ $new[] | select(.near_miss == true) ] as $nm
  | [ $new[] ] | sort_by([tier_rank, conf_rank, comp_rank, (0 - date_num)]) as $sorted
  | ([ $new[] | (.tier // "untiered") ] | group_by(.) | map({(.[0]): length}) | add // {}) as $tc
  | { title: "Today'"'"'s notifications",
      subtitle: ("\($new | length) new · A:\($tc.A // 0) B:\($tc.B // 0) C:\($tc.C // 0) · Filtered:\($tc.D // 0) · alerts walked: \($sc.coverage.totals.alerts // 0)"),
      generated_at: $today, filename: "check-job-notifications-\($today).html",
      unread_count: ($new | length),
      tier_counts: {a: ($tc.A // 0), b: ($tc.B // 0), c: ($tc.C // 0), d: ($tc.D // 0), total: ($new | length)},
      results: [ $sorted[] | card ],
      near_misses: [ $nm[] | card + {would_be_tier: (.near_miss_would_be_tier // "B"),
                                     failed_gate: (((.gate_violations // [])[0]) // {"kind": "unknown", "detail": ""}),
                                     bend_hint: "/bend \(.id)"} ],
      coverage: ($sc.coverage // {"rows": [], "totals": {}, "reposts_disclosed": 0}),
      queued: $que, reposts: $rep,
      budget: ($sc.budget // {"limit": 0, "used": 0, "queued": 0}),
      run_status: $status, no_scrape_reason: (if $status == "no_scrape" then $reason else null end),
      scorecard: $sc }
'

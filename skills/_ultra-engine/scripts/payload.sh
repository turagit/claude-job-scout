#!/bin/bash
# Usage: payload.sh <tracker.json> <run-dir> <today> <n_sources>
set -eu
tracker="$1"; rd="$2"; today="$3"; nsrc="$4"
jq -n --arg today "$today" --argjson nsrc "$nsrc" \
      --slurpfile t "$tracker" --slurpfile sc "$rd/scorecard.json" '
  def tier_rank: {"A": 0, "B": 1, "C": 2, "D": 3, "untiered": 4}[.tier // "untiered"] // 4;
  def conf_rank: if has("confidence") then ({"high": 0, "med": 1, "low": 2}[.confidence] // 3) else 3 end;
  def date_num: (.posted_at // "0000-00-00") | gsub("-"; "") | tonumber;
  def src_label: if (.source | type) == "object"
      then (if .source.provider == .source.board then .source.provider else "\(.source.provider) · \(.source.board)" end)
      else (.source | tostring) end;
  [ $t[0].jobs | to_entries[] | .value | select(.first_seen == $today) ] as $new
  | [ $new[] | select(.near_miss == true) ] as $nm
  | [ $new[] | select(.near_miss != true) ] | sort_by([tier_rank, conf_rank, (0 - date_num)]) as $results
  | ([ $new[] | (.tier // "untiered") ] | group_by(.) | map({(.[0]): length}) | add // {}) as $tc
  | { title: "Ultramode — \($nsrc) sources · \($new | length) new roles",
      subtitle: "A:\($tc.A // 0) B:\($tc.B // 0) C:\($tc.C // 0) · Filtered:\($tc.D // 0) · deduped across sources",
      generated_at: $today, filename: "ultramode-\($today).html",
      tier_counts: {a: ($tc.A // 0), b: ($tc.B // 0), c: ($tc.C // 0), d: ($tc.D // 0), total: ($new | length)},
      source_breakdown: ([ $results[] | src_label ] | group_by(.) | map({(.[0]): length}) | add // {}),
      scorecard: $sc[0],
      results: $results,
      near_misses: [ $nm[] | . + {
        would_be_tier: (.near_miss_would_be_tier // "B"),
        failed_gate: (((.gate_violations // [])[0]) // {"kind": "unknown", "detail": ""}),
        bend_hint: "/bend \(.id)" } ] }
'

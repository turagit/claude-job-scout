#!/bin/bash
# Usage: rotation.sh pick <sources.json> <N>
#        rotation.sh pick-all <sources.json>
#        rotation.sh mark <sources.json> <name> <YYYY-MM-DD>
# Order: BENELUX packs (benelux, nl-core) first, then stalest-first, then name (D4).
set -eu
cmd="$1"; f="$2"
ORDER='[ .sources[] | select(.access_lane == "extension" and (.category // "") != "linkedin") ]
  | sort_by([(if ((.pack // "") == "benelux" or (.pack // "") == "nl-core") then 0 else 1 end),
             (.last_swept_at // "0000-00-00"), .name])'
case "$cmd" in
  pick)
    n="$3"
    jq -r --argjson n "$n" "$ORDER | .[:\$n][].name" "$f"
    ;;
  pick-all)
    jq -r "$ORDER | .[].name" "$f"
    ;;
  mark)
    name="$3"; day="$4"
    jq --arg name "$name" --arg day "$day" '
      .sources |= map(if .name == $name then . + {last_swept_at: $day} else . end)' "$f" > "$f.tmp" \
      && jq -e . "$f.tmp" >/dev/null && mv "$f.tmp" "$f"
    ;;
  *) echo "usage: rotation.sh pick <sources.json> <N> | pick-all <sources.json> | mark <sources.json> <name> <date>" >&2; exit 2;;
esac

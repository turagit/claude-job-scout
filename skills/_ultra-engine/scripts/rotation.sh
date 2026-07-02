#!/bin/bash
# Usage: rotation.sh pick <sources.json> <N>
#        rotation.sh mark <sources.json> <name> <YYYY-MM-DD>
set -eu
cmd="$1"; f="$2"
case "$cmd" in
  pick)
    n="$3"
    jq -r --argjson n "$n" '
      [ .sources[] | select(.access_lane == "extension") ]
      | sort_by(.last_swept_at // "0000-00-00")
      | .[:$n][].name' "$f"
    ;;
  mark)
    name="$3"; day="$4"
    jq --arg name "$name" --arg day "$day" '
      .sources |= map(if .name == $name then . + {last_swept_at: $day} else . end)' "$f" > "$f.tmp" \
      && jq -e . "$f.tmp" >/dev/null && mv "$f.tmp" "$f"
    ;;
  *) echo "usage: rotation.sh pick <sources.json> <N> | mark <sources.json> <name> <date>" >&2; exit 2;;
esac

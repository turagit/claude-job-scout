#!/bin/bash
# Run-stage checkpoints. See test for the contract.
set -eu
cmd="$1"
case "$cmd" in
  init)
    ws="$2"; id="$3"; rd="$ws/cache/run/$id"; mkdir -p "$rd"
    [ -f "$rd/manifest.json" ] || printf '{"run_id": "%s", "started_at": "%s", "stages": {}}\n' \
      "$id" "$(date -u +%FT%TZ)" > "$rd/manifest.json"
    echo "$rd";;
  save)
    rd="$2"; stage="$3"; art="${4-}"
    if [ -n "$art" ]; then cp "$art" "$rd/$stage.json"; fi
    jq --arg s "$stage" '.stages[$s] = "done"' "$rd/manifest.json" > "$rd/manifest.json.tmp" \
      && mv "$rd/manifest.json.tmp" "$rd/manifest.json";;
  stage)
    rd="$2"; stage="$3"
    jq -r --arg s "$stage" '.stages[$s] // "absent"' "$rd/manifest.json";;
  find-incomplete)
    ws="$2"
    for d in $(ls -1dr "$ws"/cache/run/*/ 2>/dev/null); do
      d="${d%/}"
      [ -f "$d/manifest.json" ] || continue
      if [ "$(jq -r '.stages.render // "absent"' "$d/manifest.json")" != "done" ]; then echo "$d"; break; fi
    done;;
  *) echo "usage: checkpoint.sh init|save|stage|find-incomplete ..." >&2; exit 2;;
esac

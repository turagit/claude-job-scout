#!/bin/bash
# Usage: snapshot.sh <tracker.json> <out.json>
# Builds the dedupe snapshot every sweep reads: non-rejected ids + fingerprints.
set -eu
d="$(cd "$(dirname "$0")" && pwd)"
tracker="$1"; out="$2"
jq -L "$d/lib" --arg now "$(date -u +%FT%TZ)" '
  include "fingerprint";
  [ .jobs | to_entries[] | .value | select((.status // "seen") != "rejected") ] as $live
  | { generated_at: $now,
      known_ids: [ $live[].id ],
      known_fingerprints: [ $live[] | fp((.company // ""); (.title // ""); (.location // "")) ] | unique }
' "$tracker" > "$out.tmp" && jq -e . "$out.tmp" >/dev/null && mv "$out.tmp" "$out"

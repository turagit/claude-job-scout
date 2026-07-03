#!/bin/bash
# Usage: profile_hash.sh <user-profile.json>
# Prints the canonical 16-hex profile hash: sha256 over the jq -S canonical
# form of the SCORING-RELEVANT subset only. Any writer that changes one of
# these fields recomputes profile_hash with this script — cached scores keyed
# on the old hash then re-evaluate lazily. Unrelated fields never shift it.
set -eu -o pipefail
[ -f "$1" ] || { echo "profile_hash: no such file: $1" >&2; exit 1; }
payload=$(jq -S '{target_titles: (.target_titles // []), query_clusters: (.query_clusters // null),
        master_keyword_list: (.master_keyword_list // []), requirements: (.requirements // {}),
        dimensions: (.dimensions // [])}' "$1") || { echo "profile_hash: invalid or unreadable profile: $1" >&2; exit 1; }
[ -n "$payload" ] || { echo "profile_hash: empty profile (no JSON document): $1" >&2; exit 1; }
printf '%s' "$payload" | shasum -a 256 | cut -c1-16

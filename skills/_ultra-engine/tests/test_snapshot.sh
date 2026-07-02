#!/bin/bash
. "$(dirname "$0")/helpers.sh"
S="$(dirname "$0")/../scripts/snapshot.sh"; FX="$(dirname "$0")/fixtures/tracker-mini.json"
out=$(mktemp); bash "$S" "$FX" "$out"
assert_eq "2" "$(jq '.known_ids|length' "$out")" "rejected excluded from ids"
assert_eq "true" "$(jq '.known_ids|index("4001") != null' "$out")" "linkedin id present"
assert_eq "true" "$(jq '.known_fingerprints|index("acme|senior sre|amsterdam") != null' "$out")" "fingerprint computed"
assert_eq "true" "$(jq '.known_fingerprints|index("miro|platform engineer|remote") != null' "$out")" "external fingerprint"
assert_ok jq -e '.generated_at|length > 0' "$out"
rm -f "$out"; finish

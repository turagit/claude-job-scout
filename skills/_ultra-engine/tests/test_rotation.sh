#!/bin/bash
. "$(dirname "$0")/helpers.sh"
R="$(dirname "$0")/../scripts/rotation.sh"; FX="$(dirname "$0")/fixtures/sources-mini.json"
tmp=$(mktemp); cp "$FX" "$tmp"
picks=$(bash "$R" pick "$tmp" 3)
assert_eq "Toptal
freelance.nl
Malt" "$picks" "never-swept first, then stalest; api lane excluded"
assert_eq "" "$(bash "$R" pick "$tmp" 9 | grep -x "LinkedIn" || true)" "linkedin category never enters the rotation"
bash "$R" mark "$tmp" "Toptal" "2026-07-02"
assert_eq "2026-07-02" "$(jq -r '.sources[]|select(.name=="Toptal").last_swept_at' "$tmp")" "mark stamps"
picks2=$(bash "$R" pick "$tmp" 1)
assert_eq "freelance.nl" "$picks2" "marked source rotates to back"
rm -f "$tmp"; finish

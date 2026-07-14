#!/bin/bash
. "$(dirname "$0")/helpers.sh"
R="$(dirname "$0")/../scripts/rotation.sh"; FX="$(dirname "$0")/fixtures/sources-mini.json"
tmp=$(mktemp); cp "$FX" "$tmp"
picks=$(bash "$R" pick "$tmp" 3)
assert_eq "freelance.nl
Toptal
Malt" "$picks" "never-swept first, then stalest; api lane excluded"
assert_eq "" "$(bash "$R" pick "$tmp" 9 | grep -x "LinkedIn" || true)" "linkedin category never enters the rotation"
bash "$R" mark "$tmp" "Toptal" "2026-07-02"
assert_eq "2026-07-02" "$(jq -r '.sources[]|select(.name=="Toptal").last_swept_at' "$tmp")" "mark stamps"
picks2=$(bash "$R" pick "$tmp" 1)
assert_eq "freelance.nl" "$picks2" "marked source rotates to back"

# Phase 16: BENELUX pack weighting + pick-all
tmp2=$(mktemp); cp "$FX" "$tmp2"
picks3=$(bash "$R" pick "$tmp2" 2)
assert_eq "freelance.nl
Toptal" "$picks3" "benelux-pack source outranks equally-stale generic ones"
all=$(bash "$R" pick-all "$tmp2")
assert_eq "$(jq -r '[.sources[]|select(.access_lane=="extension" and .category!="linkedin")]|length' "$tmp2")" \
          "$(printf '%s\n' "$all" | grep -c .)" "pick-all returns every extension-lane non-linkedin source"
assert_eq "freelance.nl" "$(printf '%s\n' "$all" | head -1)" "pick-all leads with benelux"
assert_eq "" "$(printf '%s\n' "$all" | grep -x "LinkedIn" || true)" "pick-all excludes linkedin"
rm -f "$tmp2"

rm -f "$tmp"; finish

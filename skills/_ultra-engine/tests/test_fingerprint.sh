#!/bin/bash
. "$(dirname "$0")/helpers.sh"
FP="$(dirname "$0")/../scripts/fingerprint.sh"
assert_eq "acme gmbh|senior platform engineer|berlin" "$(bash "$FP" "Acme GmbH" "Senior Platform Engineer" "Berlin")" "basic"
assert_eq "acme|sre|amsterdam" "$(bash "$FP" "ACME" "SRE" "Greater Amsterdam Area")" "strips greater/area"
assert_eq "n26|iam engineer|berlin" "$(bash "$FP" "N26" "IAM  Engineer" "Berlin, Metropolitan-Region!")" "punctuation + collapse + strip-words"
assert_eq "globex|devops|" "$(bash "$FP" "Globex" "DevOps" "")" "empty location"
assert_eq "malmo ab|senior sre|zurich" "$(bash "$FP" "Malmö AB" "Senior SRE" "Zürich")" "diacritics fold to base letters"
# Phase 17.2: a literal "|" in any component must not break the 3-field form
assert_eq "be shaping the future poland|cloud & siem engineer remote|madrid spain remote" "$(bash "$FP" "Be | Shaping the Future Poland" "Cloud & SIEM Engineer | Remote" "Madrid | Spain (Remote)")" "pipes folded to spaces"
assert_eq "2" "$(bash "$FP" "A|B|C" "D|E" "F|G" | tr -cd '|' | wc -c | tr -d ' ')" "always exactly two pipes"
finish

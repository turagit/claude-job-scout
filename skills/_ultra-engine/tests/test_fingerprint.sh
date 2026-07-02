#!/bin/bash
. "$(dirname "$0")/helpers.sh"
FP="$(dirname "$0")/../scripts/fingerprint.sh"
assert_eq "acme gmbh|senior platform engineer|berlin" "$(bash "$FP" "Acme GmbH" "Senior Platform Engineer" "Berlin")" "basic"
assert_eq "acme|sre|amsterdam" "$(bash "$FP" "ACME" "SRE" "Greater Amsterdam Area")" "strips greater/area"
assert_eq "n26|iam engineer|berlin" "$(bash "$FP" "N26" "IAM  Engineer" "Berlin, Metropolitan-Region!")" "punctuation + collapse + strip-words"
assert_eq "globex|devops|" "$(bash "$FP" "Globex" "DevOps" "")" "empty location"
finish

#!/bin/bash
# skills/_ultra-engine/tests/test_auth_state.sh
. "$(dirname "$0")/helpers.sh"
A="$(dirname "$0")/../scripts/auth_state.sh"
M="$(dirname "$0")/../scripts/migrate_sources.py"
FX="$(dirname "$0")/fixtures/sources-v1-compat.json"
tmp=$(mktemp); cp "$FX" "$tmp"; python3 "$M" "$tmp" >/dev/null

assert_eq "auth-required" "$(bash "$A" get "$tmp" "Malt")" "get reads state"
assert_ok bash "$A" set "$tmp" "Malt" "signed-in" "2026-07-14T10:00:00Z"
assert_eq "signed-in" "$(bash "$A" get "$tmp" "Malt")" "set transitions state"
assert_eq "2026-07-14T10:00:00Z" "$(jq -r '.sources[]|select(.name=="Malt").auth_state_observed_at' "$tmp")" "observed_at stamped"
assert_fail bash "$A" set "$tmp" "Malt" "logged-in" "2026-07-14T10:00:00Z"   # bad enum
assert_fail bash "$A" set "$tmp" "Nope" "signed-in" "2026-07-14T10:00:00Z"   # unknown source
assert_eq "signed-in" "$(bash "$A" get "$tmp" "Malt")" "failed set leaves state untouched"
rm -f "$tmp"; finish

#!/bin/bash
. "$(dirname "$0")/helpers.sh"
C="$(dirname "$0")/../scripts/checkpoint.sh"
ws=$(mktemp -d)
rd=$(bash "$C" init "$ws" 2026-07-02-1000)
assert_eq "$ws/cache/run/2026-07-02-1000" "$rd" "init prints run dir"
assert_eq "absent" "$(bash "$C" stage "$rd" snapshot)" "absent stage"
echo '{"known_ids": []}' > /tmp/snap.$$
bash "$C" save "$rd" snapshot /tmp/snap.$$
assert_eq "done" "$(bash "$C" stage "$rd" snapshot)" "saved stage"
assert_ok test -f "$rd/snapshot.json"
assert_eq "$rd" "$(bash "$C" find-incomplete "$ws")" "incomplete found (no render)"
bash "$C" save "$rd" render
assert_eq "" "$(bash "$C" find-incomplete "$ws")" "complete run not offered"
rm -f /tmp/snap.$$; finish

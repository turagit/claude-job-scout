#!/bin/bash
. "$(dirname "$0")/helpers.sh"
Q="$(dirname "$0")/../scripts/jd_queue.sh"
q=$(mktemp -d)/queue.json
assert_eq "0" "$(bash "$Q" count "$q")" "missing file counts 0"
echo '[{"id":"a__b__1","title":"X"},{"id":"a__b__2","title":"Y"}]' > /tmp/e1.$$
bash "$Q" push "$q" /tmp/e1.$$
assert_eq "2" "$(bash "$Q" count "$q")" "push 2"
echo '[{"id":"a__b__2","title":"Y-dup"},{"id":"a__b__3","title":"Z"}]' > /tmp/e2.$$
bash "$Q" push "$q" /tmp/e2.$$
assert_eq "3" "$(bash "$Q" count "$q")" "dedupe by id on push"
popped=$(bash "$Q" pop "$q" 2)
assert_eq "a__b__1 a__b__2" "$(echo "$popped" | jq -r 'map(.id)|join(" ")')" "FIFO order"
assert_eq "1" "$(bash "$Q" count "$q")" "popped removed"
rm -f /tmp/e1.$$ /tmp/e2.$$

# --- origin namespacing ---
q2=$(mktemp -d)/queue.json
echo '[{"id":"n__1"},{"id":"n__2"}]' > /tmp/e3.$$
bash "$Q" push "$q2" /tmp/e3.$$ notifications
assert_eq "notifications notifications" "$(jq -r '[.queue[].origin]|join(" ")' "$q2")" "push sets origin on every entry"
assert_eq "2" "$(bash "$Q" count "$q2" notifications)" "count by origin"
assert_eq "0" "$(bash "$Q" count "$q2")" "count with no origin excludes notifications entries"

echo '[{"id":"u__1"},{"id":"u__2"}]' > /tmp/e4.$$
bash "$Q" push "$q2" /tmp/e4.$$
echo '[{"id":"u__3","origin":"ultramode"}]' > /tmp/e5.$$
bash "$Q" push "$q2" /tmp/e5.$$
assert_eq "3" "$(bash "$Q" count "$q2")" "no-origin count = legacy(no origin) + explicit ultramode"
assert_eq "2" "$(bash "$Q" count "$q2" notifications)" "notifications count unaffected by ultramode pushes"

popped_ultra=$(bash "$Q" pop "$q2" 10)
assert_eq "u__1 u__2 u__3" "$(echo "$popped_ultra" | jq -r 'map(.id)|join(" ")')" "pop with no origin returns only legacy/ultramode entries, in order"
assert_eq "2" "$(bash "$Q" count "$q2" notifications)" "notifications entries untouched by ultramode pop"
assert_eq "0" "$(bash "$Q" count "$q2")" "legacy/ultramode entries drained"

popped_notif=$(bash "$Q" pop "$q2" 10 notifications)
assert_eq "n__1 n__2" "$(echo "$popped_notif" | jq -r 'map(.id)|join(" ")')" "pop with origin returns only that origin's entries"
assert_eq "0" "$(bash "$Q" count "$q2" notifications)" "notifications entries drained"

rm -f /tmp/e3.$$ /tmp/e4.$$ /tmp/e5.$$; finish

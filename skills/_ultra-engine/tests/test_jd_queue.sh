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
rm -f /tmp/e1.$$ /tmp/e2.$$; finish

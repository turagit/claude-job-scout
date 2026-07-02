#!/bin/bash
. "$(dirname "$0")/helpers.sh"
NS="$(dirname "$0")/../scripts/namespace_id.sh"
assert_eq "greenhouse__miro__4012345" "$(bash "$NS" Greenhouse MIRO 4012345)" "slugifies provider+board"
assert_eq "it-contracts-nl__it-contracts-nl__abc-9" "$(bash "$NS" "IT-Contracts.nl" "IT-Contracts.nl" "abc-9")" "dots to dashes"
a=$(bash "$NS" --from-url remoteok remoteok "https://remoteok.com/remote-jobs/998877?ref=x")
b=$(bash "$NS" --from-url remoteok remoteok "https://remoteok.com/remote-jobs/998877/")
assert_eq "$a" "$b" "url fallback deterministic across query/trailing-slash"
case "$a" in remoteok__remoteok__????????????) _report 0 "fallback shape";; *) _report 1 "fallback shape: $a";; esac
finish

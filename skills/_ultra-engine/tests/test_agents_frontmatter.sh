#!/bin/bash
. "$(dirname "$0")/helpers.sh"
A="$(dirname "$0")/../../../agents"
fm() { sed -n '/^---$/,/^---$/p' "$A/$1" | grep -E "^$2:" | head -1 | sed 's/^[^:]*: *//'; }
assert_eq "gate-batch" "$(fm gate-batch.md name)" "gate-batch name"
assert_eq "sonnet" "$(fm gate-batch.md model)" "gate-batch pinned to sonnet"
assert_eq "score-batch" "$(fm score-batch.md name)" "score-batch name"
assert_eq "opus" "$(fm score-batch.md model)" "score-batch pinned to opus"
for f in gate-batch.md score-batch.md; do
  grep -q '^tools: Read' "$A/$f"; _report $? "$f read-only tools"
  grep -q 'subagent-protocol.md' "$A/$f"; _report $? "$f cites the protocol"
  grep -q '"deltas"' "$A/$f"; _report $? "$f documents the delta shape"
  ! grep -qi 'voyager\|navigate\|screenshot' "$A/$f"; _report $? "$f never touches a browser"
done
grep -q '_gate-engine' "$A/gate-batch.md"; _report $? "gate-batch loads _gate-engine"
grep -q '_job-matcher' "$A/score-batch.md"; _report $? "score-batch loads _job-matcher"
finish

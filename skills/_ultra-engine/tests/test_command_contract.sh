#!/bin/bash
. "$(dirname "$0")/helpers.sh"
C="$(dirname "$0")/../../check-job-notifications/SKILL.md"
must() { grep -qF -- "$1" "$C"; _report $? "command cites: $1"; }
never() { ! grep -qiF -- "$1" "$C"; _report $? "command never says: $1"; }
grep -q '^disable-model-invocation: true' "$C"; _report $? "disable-model-invocation"
for s in page/notifications.js page/results.js page/toppicks.js page/saved.js alerts_parse.py cards_parse.py walk_stop.py alerts_ledger.py snapshot.sh fingerprint.sh validate_delta.py merge_tracker.py jd_queue.sh checkpoint.sh coverage.py scorecard.sh payload_notifications.sh digest.py; do must "$s"; done
must 'subagent_type: "gate-batch"'; must 'subagent_type: "score-batch"'
must 'jd_budget_per_run'; must 'We found more results'; must 'no_scrape'; must 'fp-45d.json'; must 'refused-'
never 'voyager'; never 'highlighted in blue'; never 'Scroll 2-3'; never 'Want me to'; never 'ask the user'; never 'my-items/saved-jobs'
[ "$(wc -l < "$C")" -le 230 ]; _report $? "command file stays lean (<=230 lines)"
finish

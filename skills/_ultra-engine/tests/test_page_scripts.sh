#!/bin/bash
. "$(dirname "$0")/helpers.sh"
P="$(dirname "$0")/../scripts/page"
req() { grep -qF -- "$2" "$P/$1"; _report $? "$1 carries anchor: $2"; }
for f in notifications.js results.js toppicks.js saved.js; do
  [ -s "$P/$f" ]; _report $? "$f exists and is non-empty"
  grep -q 'JSON.stringify(out)' "$P/$f"; _report $? "$f returns JSON.stringify(out)"
  grep -q '"surface"' "$P/$f" || grep -q 'surface:' "$P/$f"; _report $? "$f sets surface"
  ! grep -qi 'voyager' "$P/$f"; _report $? "$f never mentions voyager"
done
req notifications.js 'alertAction=viewjobs'
req notifications.js 'Load more'
req results.js 'job-card-component-ref-'
req results.js 'We found more results related to your search'
req results.js 'pagination-controls-next-button-visible'
req results.js 'aria-current'
req toppicks.js 'data-occludable-job-id'
req toppicks.js 'data-job-id'
req saved.js 'jobs-tracker'
req saved.js 'Saved'
if command -v node >/dev/null 2>&1; then
  for f in notifications.js results.js toppicks.js saved.js; do
    node -e "new Function('return (async()=>{' + require('fs').readFileSync('$P/$f','utf8') + '})()')" 2>/dev/null
    _report $? "$f parses as JS (node available)"
  done
fi
finish

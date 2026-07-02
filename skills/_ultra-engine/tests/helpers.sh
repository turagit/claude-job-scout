#!/bin/bash
# Test helpers for _ultra-engine. Source me. bash-3.2 compatible.
FAILS=0; CHECKS=0
_report() { CHECKS=$((CHECKS+1)); if [ "$1" -ne 0 ]; then FAILS=$((FAILS+1)); echo "  FAIL: $2"; else echo "  ok: $2"; fi; }
assert_eq()  { [ "$1" = "$2" ]; _report $? "${3:-expected [$1] got [$2]} (want='$1' got='$2')"; }
assert_ok()  { "$@" >/dev/null 2>&1; _report $? "exit0: $*"; }
assert_fail(){ "$@" >/dev/null 2>&1; [ $? -ne 0 ]; _report $? "nonzero-exit: $*"; }
assert_json_eq() {
  local want got
  want=$(printf '%s' "$1" | jq -Se . 2>/dev/null) || { _report 1 "${3:-json}: want side unparseable"; return; }
  got=$(printf '%s' "$2" | jq -Se . 2>/dev/null) || { _report 1 "${3:-json}: got side unparseable"; return; }
  [ "$want" = "$got" ]; _report $? "${3:-json mismatch}"
}
finish() { echo "checks=$CHECKS fails=$FAILS"; [ "$FAILS" -eq 0 ]; }

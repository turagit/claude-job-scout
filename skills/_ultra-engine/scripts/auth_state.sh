#!/bin/bash
# Usage: auth_state.sh set <sources.json> <name> <state> <ISO8601>
#        auth_state.sh get <sources.json> <name>
# States are observations from sweep outcomes, never inferred from elapsed time (spec §6.4).
set -eu
cmd="$1"; f="$2"; name="$3"
case "$cmd" in
  set)
    state="$4"; at="$5"
    case "$state" in public|auth-required|signed-in|session-expired) ;;
      *) echo "invalid auth_state: $state (allowed: public|auth-required|signed-in|session-expired)" >&2; exit 2;;
    esac
    jq -e --arg n "$name" '.sources[] | select(.name==$n)' "$f" >/dev/null \
      || { echo "unknown source: $name" >&2; exit 2; }
    jq --arg n "$name" --arg s "$state" --arg at "$at" '
      .sources |= map(if .name==$n then . + {auth_state: $s, auth_state_observed_at: $at} else . end)' "$f" > "$f.tmp" \
      && jq -e . "$f.tmp" >/dev/null && mv "$f.tmp" "$f"
    ;;
  get)
    jq -r --arg n "$name" '.sources[] | select(.name==$n) | .auth_state // "public"' "$f"
    ;;
  *) echo "usage: auth_state.sh set <sources.json> <name> <state> <ISO8601> | get <sources.json> <name>" >&2; exit 2;;
esac

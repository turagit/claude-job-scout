#!/bin/bash
# Usage: namespace_id.sh <provider> <board> <external_id>
#        namespace_id.sh --from-url <provider> <board> <url>
set -u
slug() { printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9-]+/-/g; s/-+/-/g; s/^-+//; s/-+$//'; }
if [ "${1-}" = "--from-url" ]; then
  p=$(slug "$2"); b=$(slug "$3")
  u=$(printf '%s' "$4" | tr '[:upper:]' '[:lower:]' | sed -E 's/[?#].*$//; s:/+$::')
  h=$(printf '%s' "$u" | shasum -a 256 | cut -c1-12)
  printf '%s__%s__%s\n' "$p" "$b" "$h"
else
  p=$(slug "$1"); b=$(slug "$2")
  e=$(printf '%s' "$3" | sed -E 's/[[:space:]]+//g')
  printf '%s__%s__%s\n' "$p" "$b" "$e"
fi

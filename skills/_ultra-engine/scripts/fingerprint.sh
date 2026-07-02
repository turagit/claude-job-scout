#!/bin/bash
# Usage: fingerprint.sh <company> <title> <location>   -> prints fingerprint
set -u
d="$(cd "$(dirname "$0")" && pwd)"
jq -nr -L "$d/lib" --arg c "${1-}" --arg t "${2-}" --arg l "${3-}" 'include "fingerprint"; fp($c; $t; $l)'

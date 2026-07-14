#!/bin/bash
# skills/_ultra-engine/tests/test_config_scope.sh
. "$(dirname "$0")/helpers.sh"
C="$(dirname "$0")/../scripts/catalog.py"
tmp=$(mktemp)
cat > "$tmp" <<'EOF'
{"schema_version": 2, "x_custom": {"keep": true}, "ultramode": {"api_keys": {"adzuna": "k"}}}
EOF

# The documented /sources scope write recipe (verbatim from sources/SKILL.md § scope):
jq '.ultramode.source_scope = "eu-broad"' "$tmp" > "$tmp.tmp" && jq -e . "$tmp.tmp" >/dev/null && mv "$tmp.tmp" "$tmp"

assert_eq "eu-broad" "$(python3 "$C" config-read "$tmp" | jq -r .source_scope)" "write recipe sets scope"
assert_eq "true" "$(jq -r '.x_custom.keep' "$tmp")" "unknown top-level keys preserved"
assert_eq "k" "$(jq -r '.ultramode.api_keys.adzuna' "$tmp")" "sibling ultramode keys preserved"
assert_eq "manual" "$(python3 "$C" config-read "$tmp" | jq -r .source_refresh)" "refresh still defaults"
rm -f "$tmp"; finish

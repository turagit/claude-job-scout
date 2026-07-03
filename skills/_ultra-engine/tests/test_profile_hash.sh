#!/bin/bash
. "$(dirname "$0")/helpers.sh"
PH="$(dirname "$0")/../scripts/profile_hash.sh"
t=$(mktemp -d)
cat > "$t/a.json" <<'EOF'
{"target_titles": ["SRE"], "requirements": {"contract_type": ["freelance"]}, "cv_hash": "zzz", "tone": {"dialect": "british"}}
EOF
cat > "$t/b.json" <<'EOF'
{"requirements": {"contract_type": ["freelance"]}, "target_titles": ["SRE"], "cv_hash": "DIFFERENT", "last_updated": "2026-07-03"}
EOF
cat > "$t/c.json" <<'EOF'
{"target_titles": ["SRE", "Platform Engineer"], "requirements": {"contract_type": ["freelance"]}}
EOF
ha=$(bash "$PH" "$t/a.json"); hb=$(bash "$PH" "$t/b.json"); hc=$(bash "$PH" "$t/c.json")
assert_eq "$ha" "$hb" "unrelated fields and key order do not change the hash"
[ "$ha" != "$hc" ]; _report $? "scoring-relevant change changes the hash (a=$ha c=$hc)"
case "$ha" in ????????????????) _report 0 "16 hex chars";; *) _report 1 "16 hex chars: got '$ha'";; esac
finish

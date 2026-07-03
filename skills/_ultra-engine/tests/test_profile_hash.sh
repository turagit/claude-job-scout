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
# every scoring-relevant field must shift the hash; bad paths fail loudly
for variant in \
  '.requirements.contract_type = ["permanent"]' \
  '.master_keyword_list = ["kerberos"]' \
  '.dimensions = [{"name": "x"}]' \
  '.query_clusters = [{"label": "l", "titles": ["SRE"], "not_terms": []}]'; do
  jq "$variant" "$t/a.json" > "$t/v.json"
  hv=$(bash "$PH" "$t/v.json")
  [ "$ha" != "$hv" ]; _report $? "field variant shifts hash: $variant"
done
# bad inputs must fail loudly with EMPTY stdout — never a plausible fake hash
for bad in missing empty malformed; do
  case "$bad" in
    missing)   p="$t/does-not-exist.json";;
    empty)     p="$t/empty.json"; : > "$p";;
    malformed) p="$t/malformed.json"; printf '{broken' > "$p";;
  esac
  assert_fail bash "$PH" "$p"
  out=$(bash "$PH" "$p" 2>/dev/null || true)
  assert_eq "" "$out" "$bad input prints nothing (never a fake hash)"
done
finish

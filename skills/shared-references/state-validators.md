# State Validators

> **Mandatory pre-write check.** Every skill that writes to `.job-scout/` state files MUST run the validation routine in this reference before persisting. Enum violations are rejected; the write is aborted and the user is told which field failed.

## Why

Live state has historically drifted from spec because writes happened without enforcement. Director's tracker carries `tier: A_upgraded`, `tier: DEFERRED`, `tier: FILTERED`; Freelancer's tracker carries `status: seen_noted`, `status: seen_duplicate`. None of these are spec values; downstream consumers (`_visualizer`, `_job-matcher`) silently mis-handle them. Validators close that loop.

## Validation routine (every state write)

1. **Load the canonical enum table from `canonical-schemas.md`.**
2. **For every field listed in the enum table:** if the value being written is not in the allowed set, raise a `SCHEMA_VIOLATION` error and abort the write.
3. **Required fields:** verify every field marked required in `canonical-schemas.md` is present. Missing required fields raise `SCHEMA_VIOLATION`.
4. **Type checks:** strings stay strings, arrays stay arrays, numbers stay numbers, ISO8601 fields match `^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}Z?)?$`.
5. **Status transition check:** if updating an existing job, the new status must be a legal successor of the current status per `canonical-schemas.md` § Status transition rules.

## Standard validation procedure (operational)

Skills must implement this as a pre-write step. The exact mechanism in this codebase is a `jq` check followed by an atomic file-rename pattern.

### Validate a single tracker.json change before persisting

```bash
# Given $TRACKER (path to tracker.json) and $NEW (path to candidate new state)
# Returns 0 if valid, non-zero with stderr message if not.

validate_tracker() {
  local f="$1"

  # 1. Enum check — status
  local bad_status
  bad_status=$(jq -r '.jobs | to_entries | map(select(.value.status as $s |
    ["seen","approved","applied","rejected","skipped"] | index($s) | not)) |
    map(.key + ":" + (.value.status // "null")) | join(",")' "$f")
  if [ -n "$bad_status" ]; then
    echo "SCHEMA_VIOLATION: status $bad_status" >&2; return 2
  fi

  # 2. Enum check — tier
  local bad_tier
  bad_tier=$(jq -r '.jobs | to_entries | map(select(.value.tier as $t |
    ["A","B","C","D","untiered"] | index($t) | not)) |
    map(.key + ":" + (.value.tier // "null")) | join(",")' "$f")
  if [ -n "$bad_tier" ]; then
    echo "SCHEMA_VIOLATION: tier $bad_tier" >&2; return 2
  fi

  # 3. Enum check — rubric_version
  local bad_rv
  bad_rv=$(jq -r '.jobs | to_entries | map(select(.value.rubric_version as $r |
    ["legacy","v1"] | index($r) | not)) |
    map(.key + ":" + (.value.rubric_version // "null")) | join(",")' "$f")
  if [ -n "$bad_rv" ]; then
    echo "SCHEMA_VIOLATION: rubric_version $bad_rv" >&2; return 2
  fi

  # 4. schema_version present and == 2
  local sv
  sv=$(jq -r '.schema_version // "missing"' "$f")
  if [ "$sv" != "2" ]; then
    echo "SCHEMA_VIOLATION: schema_version is $sv, expected 2" >&2; return 2
  fi

  return 0
}
```

### Validate a user-profile.json change

```bash
validate_profile() {
  local f="$1"

  # segment must be one of two
  local seg
  seg=$(jq -r '.segment // "missing"' "$f")
  case "$seg" in
    director-perm|freelance) : ;;
    *) echo "SCHEMA_VIOLATION: segment is $seg" >&2; return 2 ;;
  esac

  # deal_breakers[].kind must be valid
  local bad_dk
  bad_dk=$(jq -r '.requirements.deal_breakers // [] | map(select(.kind as $k |
    ["work_arrangement","contract_type","seniority_floor","location","industry","company","rate_floor","salary_floor","custom"] | index($k) | not)) |
    map(.kind // "null") | join(",")' "$f")
  if [ -n "$bad_dk" ]; then
    echo "SCHEMA_VIOLATION: deal_breakers[].kind $bad_dk" >&2; return 2
  fi

  # tone block presence (warn-only — populated by Task 16)
  local tone_present
  tone_present=$(jq -r 'has("tone")' "$f")
  if [ "$tone_present" != "true" ]; then
    echo "WARN: tone block missing" >&2
  fi

  return 0
}
```

### Validate a threads.json change

```bash
validate_threads() {
  local f="$1"

  local bad_lt
  bad_lt=$(jq -r '.threads | to_entries | map(select(.value.lead_tier as $t |
    ["hot","warm","cold","non-lead"] | index($t) | not)) |
    map(.key + ":" + (.value.lead_tier // "null")) | join(",")' "$f")
  if [ -n "$bad_lt" ]; then
    echo "SCHEMA_VIOLATION: lead_tier $bad_lt" >&2; return 2
  fi

  return 0
}
```

## Atomic write pattern

Every state write follows this pattern:

```bash
write_state_file() {
  local target="$1"     # e.g. .job-scout/tracker.json
  local new_content="$2"   # path to candidate file
  local validator="$3"     # function name (validate_tracker etc.)

  # 1. Validate
  "$validator" "$new_content" || return $?

  # 2. Back up the current state
  local stamp; stamp=$(date -u +%Y%m%dT%H%M%SZ)
  local backup_dir
  backup_dir="$(dirname "$target")/.backup"
  mkdir -p "$backup_dir"
  if [ -f "$target" ]; then
    cp "$target" "$backup_dir/$(basename "$target").$stamp.json"
  fi

  # 3. Atomic rename
  mv "$new_content" "$target"
}
```

## When to skip validators

Never. The only exceptions are:

1. **Migration scripts** (Tasks 8–11 of this plan) — they convert non-canonical state TO canonical, so the input side is by definition non-canonical. They run the validator on the OUTPUT side only.
2. **Read-only reports** — no write, no validation. The validator is write-side only.

## Error surface

When a skill aborts a write due to `SCHEMA_VIOLATION`, it must:

1. Print the violating field and value to the user.
2. Leave the on-disk state unchanged (atomic-rename guarantees this).
3. Suggest the user file an issue with the offending payload, or — if the cause is obvious — fix the upstream skill that produced the bad payload.

Never silently fall back to a default value or "best effort" save.

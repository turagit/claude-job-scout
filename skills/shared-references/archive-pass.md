# Archive Pass

> **Run once per calendar day per workspace.** Gated by `tracker.stats.last_archive_pass`. Rotates aged `status: seen` entries out of hot `tracker.json` into `.job-scout/archive/tracker-<year>.json`.

## When to run

In every command's Step 0 bootstrap, after loading `tracker.json`:

```
if today's date == tracker.stats.last_archive_pass → skip.
else → run the pass, update last_archive_pass to today's date.
```

## What to archive

- `status == "seen"` AND `last_seen` older than 60 days from today.
- Group by year (`first_seen` year).
- For each year, append the eligible jobs to `archive/tracker-YYYY.json` (canonical v2 shape, no `stats` block).
- Remove the archived entries from hot `tracker.json`.

## What NOT to archive

- `approved`, `applied`, `rejected`, `skipped` — these all represent user intent. Stay hot indefinitely.

## Implementation outline (per workspace)

```bash
archive_pass() {
  local D="$1"
  local IN="$D/tracker.json"
  local TODAY; TODAY=$(date -u +%Y-%m-%d)

  local LAST_PASS
  LAST_PASS=$(jq -r '.stats.last_archive_pass // "1970-01-01"' "$IN")
  if [ "$LAST_PASS" = "$TODAY" ]; then return 0; fi

  local CUTOFF
  CUTOFF=$(date -u -v-60d +%Y-%m-%d 2>/dev/null || date -u -d '60 days ago' +%Y-%m-%d)

  mkdir -p "$D/archive"

  # 1. Compute eligible job-id list per year
  local YEARS
  YEARS=$(jq -r --arg cutoff "$CUTOFF" '
    [.jobs[] | select(.status == "seen" and .last_seen < $cutoff) | (.first_seen[0:4])] |
    unique | .[]' "$IN")

  for YR in $YEARS; do
    local ARCH="$D/archive/tracker-$YR.json"
    if [ ! -f "$ARCH" ]; then
      echo '{"schema_version": 2, "version": 2, "jobs": {}}' > "$ARCH"
    fi
    # Move eligible entries for this year from hot to archive
    jq --arg cutoff "$CUTOFF" --arg yr "$YR" --slurpfile arch "$ARCH" '
      ($arch[0].jobs // {}) as $existing |
      .jobs as $hot |
      ($hot | with_entries(select(.value.status == "seen" and .value.last_seen < $cutoff and (.value.first_seen[0:4] == $yr)))) as $movers |
      {schema_version: 2, version: 2, jobs: ($existing + $movers)}
    ' "$IN" > "$ARCH.tmp" && mv "$ARCH.tmp" "$ARCH"

    jq --arg cutoff "$CUTOFF" --arg yr "$YR" '
      .jobs |= with_entries(select(
        (.value.status != "seen") or
        (.value.last_seen >= $cutoff) or
        (.value.first_seen[0:4] != $yr)
      ))
    ' "$IN" > "$IN.tmp" && mv "$IN.tmp" "$IN"
  done

  # 2. Update last_archive_pass + recompute total_seen
  jq --arg today "$TODAY" '
    .stats.last_archive_pass = $today
    | .stats.total_seen = ([.jobs[] | select(.status == "seen")] | length)
  ' "$IN" > "$IN.tmp" && mv "$IN.tmp" "$IN"
}
```

## Wired into

Commands that invoke the archive pass:

- `/check-job-notifications` Step 0 (after tracker load)
- `/job-search` Step 0
- `/match-jobs` Step 0
- `/funnel-report` Step 0
- `/check-inbox` Step 0 (only if a tracker exists; safe to skip)

The pass is idempotent and same-day-gated, so calling it from many commands is safe and cheap.

## Verification

```bash
D="$(pwd)/.job-scout"   # run from the workspace root
jq '{last_archive_pass: .stats.last_archive_pass, hot_seen: ([.jobs[] | select(.status == "seen")] | length)}' "$D/tracker.json"
ls "$D/archive/" 2>/dev/null
```

Right after the first pass, `last_archive_pass` is today's date and any entries with `last_seen < (today - 60d)` and `status == "seen"` are gone from the hot file (moved to `archive/tracker-YYYY.json`).

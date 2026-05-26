# `tracker.json` Operational Rules

> **Schema definition:** see [`canonical-schemas.md`](canonical-schemas.md). This file documents read/write rules, dedupe contract, and archival policy. The JSON shape is canonical and locked there.

The single source of truth for "have I seen this job before?". Lives at `.job-scout/tracker.json`. Every command that reads or scores jobs MUST consult this file *before* extracting job details — that is the primary token-saving mechanism in the plugin.

## Rules

- **Key by job id**, not URL — LinkedIn URLs sometimes carry tracking params. Strip to the canonical `/jobs/view/<id>/` form.
- **Dedupe before extraction.** When sweeping a listing page, collect every job id first, then drop any id already in `tracker.json`. Only open and extract details for the survivors.
- **`status` transitions are one-way** — see `canonical-schemas.md` § Status transition rules.
- **`last_seen` updates every time** the job appears in any sweep. `first_seen` never changes.
- **Score updates** are allowed if the user's CV or LinkedIn profile changed (either `cv_hash` or `profile_hash` bumped) OR if the job's `rubric_version` is `legacy` and the consumer is the lazy-rescore path. Otherwise leave the score alone.
- **Stats** must be incremented atomically with job state changes. `last_run` updates on every command invocation that touches the tracker.
- **Full JD text** is stored hybrid: see [`jd-storage.md`](jd-storage.md). The tracker entry carries `jd_path` only.
- **Writes use the atomic-rename pattern** in [`state-validators.md`](state-validators.md) with `validate_tracker` as the pre-write check.

## Read pattern (every command)

```
1. Load .job-scout/tracker.json (create empty canonical-v2 shell if missing).
2. Collect candidate job ids from the source (page scrape, alert, search result).
3. Filter: known_ids = ids ∩ tracker.jobs.keys()
4. new_ids = ids − known_ids
5. Process new_ids fully; for known_ids only update last_seen.
6. Persist tracker via the atomic-write pattern (validator first).
```

> If the workspace has archival active, step 1 also consults the current-year archive on a tracker miss. See **Archival policy** below.

## Write pattern

Always merge — never overwrite the whole file. If two commands run concurrently, the second should re-read before writing to avoid stomping the first's updates. All writes go through `validate_tracker` per `state-validators.md`.

## Archival policy

`tracker.json` grows monotonically and — over years of use — would become expensive to read on every dedupe pass. Aged `status: seen` entries rotate to annual archive files.

### Rules

- **Eligible for archive:** `status == "seen"` AND `last_seen` older than 60 days.
- **Not archived:** `approved`, `applied`, `rejected`, `skipped`. These all represent user intent. They stay in hot `tracker.json` indefinitely. Only pure `seen` entries are eligible.
- **Archive destination:** `.job-scout/archive/tracker-YYYY.json`, keyed by the year the job was `first_seen`.
- **Archive shape:** same as `tracker.json` canonical v2 — `{ "schema_version": 2, "version": 2, "jobs": { ... } }`. No `stats` block; archive files are append-only.

### When to run

Run the archive pass at most once per calendar day per workspace. Gate via `stats.last_archive_pass` in `tracker.json` (stored as `"YYYY-MM-DD"` — date only): if today's date equals the stored date, skip. Otherwise run the pass and update the field.

### Dedupe read pattern after archival

```
1. Load .job-scout/tracker.json — primary dedupe set.
2. If an id is not in hot tracker, fall through to .job-scout/archive/tracker-<current-year>.json.
3. Do NOT read older archive files during the hot path — they exist for /funnel-report and manual inspection.
```

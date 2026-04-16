# `tracker.json` Schema

The single source of truth for "have I seen this job before?". Lives at `.job-scout/tracker.json`. Every command that reads or scores jobs MUST consult this file *before* extracting job details — that is the primary token-saving mechanism in the plugin.

## Shape

```json
{
  "version": 1,
  "stats": {
    "total_seen": 0,
    "applied": 0,
    "rejected": 0,
    "last_run": "2026-04-08T10:00:00Z",
    "last_archive_pass": null
  },
  "jobs": {
    "<job_id>": {
      "id": "<linkedin job id, extracted from URL>",
      "url": "https://www.linkedin.com/jobs/view/<id>/",
      "title": "Senior Platform Engineer",
      "company": "Acme Corp",
      "source": "Job Alert | Top Picks | Search | Inbox",
      "score": 87,
      "tier": "A",
      "status": "seen | approved | applied | rejected | skipped",
      "first_seen": "2026-04-01",
      "last_seen": "2026-04-08",
      "applied_at": null,
      "notes": ""
    }
  }
}
```

## Rules

- **Key by job id**, not URL — LinkedIn URLs sometimes carry tracking params. Strip to the canonical `/jobs/view/<id>/` form.
- **Dedupe before extraction.** When sweeping a listing page, collect every job id first, then drop any id already in `tracker.json`. Only open and extract details for the survivors.
- **`status` transitions** are one-way: `seen → approved → applied`, or `seen → rejected`. Never downgrade.
- **`last_seen` updates every time** the job appears in any sweep. `first_seen` never changes.
- **Score updates** are allowed if the user's CV or LinkedIn profile changed (either `cv_hash` or `profile_hash` bumped). Otherwise, leave the score alone — re-scoring an unchanged job against an unchanged CV and profile is wasted tokens.
- **Stats** must be incremented atomically with job state changes. `last_run` updates on every command invocation that touches the tracker.

## Read pattern (every command)

```
1. Load .job-scout/tracker.json (create empty if missing)
2. Collect candidate job ids from the source (page scrape, alert, search result)
3. Filter: known_ids = ids ∩ tracker.jobs.keys()
4. new_ids = ids − known_ids
5. Process new_ids fully; for known_ids only update last_seen
6. Persist tracker before exiting
```

## Write pattern

Always merge — never overwrite the whole file. If two commands run concurrently, the second should re-read before writing to avoid stomping the first's updates.

## Archival policy

`tracker.json` grows monotonically and — over years of use — would become expensive to read on every dedupe pass. Aged `status: seen` entries rotate to annual archive files.

### Rules

- **Eligible for archive:** `status == "seen"` AND `last_seen` older than 60 days.
- **Not archived:** `approved`, `applied`, `rejected`. These are real artefacts of the user's search and stay in hot `tracker.json`.
- **Archive destination:** `.job-scout/archive/tracker-YYYY.json`, keyed by the year the job was `first_seen`.
- **Archive shape:** same as `tracker.json` — `{ "version": 1, "jobs": { ... } }`. No `stats` block; archive files are append-only.

### When to run

Run the archive pass at most once per calendar day per workspace. Gate via `stats.last_archive_pass` in `tracker.json`: if today's date equals the stored date, skip. Otherwise run the pass and update the field.

### Dedupe read pattern after archival

```
1. Load .job-scout/tracker.json — primary dedupe set.
2. If an id is not in hot tracker, fall through to .job-scout/archive/tracker-<current-year>.json.
3. Do NOT read older archive files during the hot path — they exist for /funnel-report (Phase 3) and manual inspection.
```

Fall-through reads are bounded to the current year because LinkedIn rarely re-posts a job id across a year boundary. If the id is truly re-posted, the (minor) cost is a re-extraction.

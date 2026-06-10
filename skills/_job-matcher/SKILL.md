---
name: _job-matcher
description: >
  [Internal — loaded by /match-jobs and /check-job-notifications] This skill should be used when the user asks to "match jobs to my CV", "score these jobs", "rank job listings", "find best matches", "analyse job alerts", "which jobs should I apply to", "compare jobs against my profile", or needs to evaluate job listings against their CV and stated requirements.
version: 0.2.0
---

# Job Matcher (rubric v1)

Score, rank, and filter job listings against a user's CV and stated requirements. The v1 rubric (this file) replaces the v0.1 keyword-bingo weighted score with a hard-gated, segment-aware, per-dimension tiering whose output is auditable.

## Rubric flow

```
For each candidate job:
  1. Load score cache; if hit (key includes rubric_version: v1) → return cached.
  2. Run _gate-engine. If gate_violations is non-empty:
       tier = D
       tier_reason = "gated: <kinds>"
       dimensions = {}
       — write to cache and return.
  3. Load the dimension set:
       - If user-profile.json carries a non-empty `dimensions[]` array, use it. This is the per-workspace
         rubric, typically populated by `/analyze-cv` discovery against the user's CV, target_titles,
         segment description, and requirements.
       - Otherwise, fall back to the universal bootstrap in `references/dimensions-default.md`.
  4. Score each dimension. Output per dimension: { tier: A|B|C|D, evidence: [quote, ...] }.
  5. Derive overall tier from the dimension tiers using the table in the dimension reference.
  6. Persist to score cache and update the tracker entry: tier, tier_reason, dimensions, gate_violations, rubric_version: "v1".
```

## Output (per job)

```json
{
  "job_id": "string",
  "tier": "A | B | C | D",
  "tier_reason": "string|null",
  "dimensions": {
    "<dim_name>": {"tier": "A|B|C|D", "evidence": ["quote 1", "quote 2"]}
  },
  "gate_violations": [{"kind": "...", "detail": "..."}],
  "rubric_version": "v1"
}
```

The visualiser (`_visualizer`) renders the dimensions section in the report card; the user sees WHY a job got the tier it got, not just a number.

## Batch flow

When scoring N jobs in one /match-jobs or /check-job-notifications run:

1. Compute cache keys for all N. Partition into HIT and MISS.
2. HIT: return cached.
3. MISS: process in batches of ≤5 per LLM call where possible (batch by similarity — same company, same broad title pattern). For each MISS, run `_gate-engine` first, then the rubric.
4. Write all MISSes to the cache in one atomic update at the end.

## Score Caching Contract

Job scores are cached in `.job-scout/cache/scores.json` keyed by `(job_id, cv_hash, profile_hash, rubric_version)`. The fourth key element — `rubric_version` — was added in v0.8.0 so that rubric upgrades invalidate stale entries without an explicit migration.

### Read path

```
1. Load .job-scout/user-profile.json — read cv_hash, profile_hash, segment.
2. Determine current rubric_version (today: "v1").
3. Compute cache key = "<job_id>:<cv_hash>:<profile_hash>:v1".
4. If cache/scores.json has this key → reuse the cached tier, dimensions, gate_violations. Skip LLM call.
5. Otherwise → run the rubric flow above, write the result to the cache, then return it.
```

### Write path

After computing a score, append/replace the entry in `cache/scores.json`:

```json
{
  "<key>": {
    "tier": "A|B|C|D",
    "tier_reason": "string|null",
    "dimensions": { "<dim>": {"tier": "A|B|C|D", "evidence": [...] } },
    "gate_violations": [...],
    "rubric_version": "v1",
    "scored_at": "ISO8601"
  }
}
```

(A `score` field may appear in entries written before v0.10.0 — tolerated on read, never written by the v1 rubric.)

Writes go through the atomic-rename pattern in `../shared-references/state-validators.md`.

### Invalidation

The cache is invalidated automatically by any of:

- `cv_hash` change (CV file modified) → entries for the old hash are stale and ignored.
- `profile_hash` change (LinkedIn profile re-optimised) → same.
- `rubric_version` bump → entries for older rubric versions are stale.
- `requirements.deal_breakers` change → bumps `profile_hash` via `/analyze-cv`, which cascades into key invalidation. No separate dealbreakers-hash element required.

### Empty-cache reality

After v0.8.0 first-install or upgrade, the `cache/` directory is typically empty. The first run populates the cache fresh. There is no batch backfill — costs are paid lazily as jobs are scored.

### File-size discipline

`scores.json` can grow large. After 5000 entries, prune entries older than 90 days OR with stale `cv_hash`/`profile_hash`/`rubric_version`. Today (770 jobs) we are far from this limit.

## Lazy rescore of legacy entries

Existing tracker entries from before v0.8.0 carry `rubric_version: "legacy"` (set by the Phase 5 migration). When the visualiser is about to display such an entry:

1. Check `rubric_version`. If `legacy` → trigger this skill's rubric flow to rescore.
2. Persist the new `tier`, `dimensions`, `tier_reason`, `gate_violations`, and bump `rubric_version` to `"v1"`.
3. Then render.

Cost is paid lazily as the user opens reports. Most legacy entries are below B-tier under v0 and don't appear in the daily top sections, so rescoring is bounded to what the user actually views.

## Inputs and state files

- **`.job-scout/user-profile.json`** — supplies `cv_hash`, `profile_hash`, `segment`, `requirements`, `tone`, `master_keyword_list`, and the per-workspace `dimensions[]` rubric (if discovered).
- **`.job-scout/tracker.json`** — supplies metadata; rubric output is persisted back here via `validate_tracker`.
- **`.job-scout/jds/<id>.txt`** — supplies the full JD text for evidence-quote extraction. If missing (legacy entry, `jd_path: null`), trigger fresh extraction via the Chrome extension before scoring.
- **`.job-scout/cache/scores.json`** — the score cache.

## Reference materials

- `../_gate-engine/SKILL.md` — hard-gate evaluator, runs before this skill.
- `references/dimensions-default.md` — universal 5-dimension bootstrap. Used when a workspace has not declared its own `dimensions[]`. Abstract criteria; no hardcoded industries, tools, or roles. Works for any job-search lane.
- `references/user-profile-schema.md` — pointer to canonical schemas.
- `../shared-references/canonical-schemas.md` — locked schemas.
- `../shared-references/state-validators.md` — pre-write validation.
- `../shared-references/jd-storage.md` — JD blob storage contract.
- `../shared-references/freelance-context.md` — freelance rate normalisation, IR35 conventions (used by the freelance dimension set).

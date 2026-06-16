---
name: _job-matcher
description: >
  [Internal — loaded by /match-jobs and /check-job-notifications] This skill should be used when the user asks to "match jobs to my CV", "score these jobs", "rank job listings", "find best matches", "analyse job alerts", "which jobs should I apply to", "compare jobs against my profile", or needs to evaluate job listings against their CV and stated requirements.
version: 0.3.0
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
     ↑ This table is UNCHANGED by Phase 12. It is the ONLY thing that decides the tier.
  6. Competitiveness judgement, for A/B jobs only — a parallel explanation signal.
     This runs strictly AFTER step 5 and reads no part of the rubric back; see "Competitiveness judgement" below.
  7. Confidence + match_explanation_tag (deterministic, NO LLM call). See "Deterministic confidence & explanation tag" below.
  8. Persist to score cache and update the tracker entry: tier, tier_reason, dimensions, gate_violations,
     rubric_version: "v1", AND the four additive fields competitiveness, competitiveness_evidence,
     confidence, match_explanation_tag. The cache KEY is unchanged (still …:v1).
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
  "rubric_version": "v1",
  "competitiveness": "high | med | low | null",
  "competitiveness_evidence": "string|null",
  "confidence": "high | med | low | null",
  "match_explanation_tag": "all-fit | one-gap | multiple-gaps | overqualified | underqualified | trajectory-concern | null"
}
```

The four trailing fields are **additive (Phase 12)**. They are explanation signals derived *after* the tier — they never participate in deriving it. They appear on both this output and the score-cache value object (see Score Caching Contract); the cache KEY is unchanged. They do **not** bump `rubric_version` (still `v1`) and do not invalidate any cached entry.

The visualiser (`_visualizer`) renders the dimensions section in the report card; the user sees WHY a job got the tier it got, not just a number.

## Competitiveness judgement (A/B only — a parallel signal)

This judgement runs **only for jobs already placed at A or B by step 5**. Skip it for every C and every D job (whether gate-failed or dimension-failed). Those skipped jobs keep both new fields at `null`. The judgement runs strictly *after* the job has been placed.

The judgement is a single question, answered against the JD and the candidate's CV: **does the candidate *exceed* the role's bar — are they a standout for this role, or merely a clean fit?**

- `high` — the candidate clearly exceeds the role's bar; a standout. Their CV depth/seniority sits above what the JD asks.
- `med` — a solid, on-the-bar fit. They meet the role comfortably without obviously exceeding it.
- `low` — they clear the bar but only just; the role is at the top of their range.

Emit one `competitiveness_evidence` quote — a short JD-grounded phrase that justifies the call (e.g. the seniority line the candidate sits above, the "nice to have" the candidate has in depth).

**This signal NEVER feeds the tier.** It is computed strictly *after* the unchanged tier-derivation table has run, and only for jobs the table already placed at A or B. There is no path from it back into the overall tier, the dimension tiers, or any gate. It is a parallel explanation signal that the deterministic tagger (next section) may consult for one tag (`overqualified`) and the visualiser surfaces as a "standout" chip.

## Deterministic confidence & explanation tag (NO LLM call)

Once step 5 and step 6 are done, compute `confidence` and `match_explanation_tag` **deterministically — there is no LLM call here**. The values are a pure function of the scored dimension tiers, read through each dimension's `type`, plus the step-6 signal for one tag only.

Procedure:

1. For each scored dimension, read its `type` from the active rubric: a custom `user-profile.json.dimensions[].type`, or for the default rubric the `type:` tags in `references/dimensions-default.md`. **A dimension with no `type` is treated as `load-bearing`.**
2. Build the tier-count profile: split the dimensions by `type` (load-bearing vs modifying) and count how many sit at A / B / C / D in each group.
3. Pass the profile (and `competitiveness`) through the ordered, first-match-wins decision table in `references/confidence-derivation-rules.json`. The first matching rule yields `{confidence, match_explanation_tag}`.

The table is the single source of truth; do not hand-reason the mapping. Worked anchors (all encoded as `test_cases[]` in the JSON):

- All dimensions A → `confidence: high`, `tag: all-fit`.
- Exactly one load-bearing dimension at B, rest A → `confidence: med`, `tag: one-gap`.
- Any dimension at C → `confidence: low` (one C → `one-gap`, two or more → `multiple-gaps`).
- A D in a *modifying* dimension with load-bearing fit clean → `tag: trajectory-concern`.
- A D in a *load-bearing* dimension → `tag: underqualified`, `confidence: low`.
- `competitiveness: high` plus a *modifying* demotion (load-bearing clean) → `tag: overqualified`.

This deterministic `confidence`/`tag` is computed for **every scored A/B/C job** (and the D cases the table covers); only `competitiveness` + its evidence is restricted to A/B.

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

After computing a score, append/replace the entry in `cache/scores.json`. **`_job-matcher` writes all four additive Phase 12 fields — `competitiveness`, `competitiveness_evidence`, `confidence`, `match_explanation_tag` — into both the cache value object below AND the tracker entry**, alongside the values already persisted by the v1 rubric:

```json
{
  "<key>": {
    "tier": "A|B|C|D",
    "tier_reason": "string|null",
    "dimensions": { "<dim>": {"tier": "A|B|C|D", "evidence": [...] } },
    "gate_violations": [...],
    "rubric_version": "v1",
    "competitiveness": "high|med|low|null",
    "competitiveness_evidence": "string|null",
    "confidence": "high|med|low|null",
    "match_explanation_tag": "all-fit|one-gap|multiple-gaps|overqualified|underqualified|trajectory-concern|null",
    "scored_at": "ISO8601"
  }
}
```

What gets written, per scored job:

- The deterministic `confidence` and `match_explanation_tag` are written for **every scored A/B/C job** (and the D cases the decision table covers).
- `competitiveness` + `competitiveness_evidence` are written **only for A/B jobs**; for C and D they are `null`.

**The cache KEY construction is untouched.** It is still `"<job_id>:<cv_hash>:<profile_hash>:v1"` (see Read path). The four fields are additive value-object fields only — they do **not** change the key, do **not** bump `rubric_version` (stays `v1`), and do **not** invalidate any existing cached entry.

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
- `references/dimensions-default.md` — universal 5-dimension bootstrap. Used when a workspace has not declared its own `dimensions[]`. Abstract criteria; no hardcoded industries, tools, or roles. Works for any job-search lane. Each default dimension carries a `type` (`load-bearing` or `modifying`) for the deterministic confidence/tag derivation.
- `references/confidence-derivation-rules.json` — the ordered, first-match-wins decision table mapping a dimension-tier profile (load-bearing vs modifying counts) to `{confidence, match_explanation_tag}`. Read with NO LLM call; carries `confidence_enum`, `tag_enum`, and worked `test_cases[]`.
- `references/user-profile-schema.md` — pointer to canonical schemas.
- `../shared-references/canonical-schemas.md` — locked schemas.
- `../shared-references/state-validators.md` — pre-write validation.
- `../shared-references/jd-storage.md` — JD blob storage contract.
- `../shared-references/freelance-context.md` — freelance rate normalisation, IR35 conventions (used by the freelance dimension set).

---
name: deep-sweep
description: Weekly thorough LinkedIn sweep across all source surfaces with multi-query fanout and similar-jobs expansion
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
disable-model-invocation: true
---

A weekly thorough sweep of LinkedIn for new opportunities. Where `/check-job-notifications` is the daily fast catch (notifications + Top picks + Saved, page 1, ~5 min), `/deep-sweep` is the weekly thorough scan — adaptive multi-query fanout across all `target_titles[]` plus synonyms, all source surfaces, Past Week filter, pages 1-3 per query, similar-jobs expansion from every A-tier hit. Expected runtime: 15-20 min. Run it once a week to catch listings the daily sweep misses.

## Browser policy (read first)

All browser work in this command uses **the Claude Chrome extension exclusively**. Never request computer use. Never suggest Playwright, Selenium, or any other automation framework. See `shared-references/browser-policy.md`. If the Chrome extension is not available in the current session, stop and report it.

## When to run

Once per week. `disable-model-invocation: true` means the user invokes it explicitly; the agent never auto-fires. A reasonable cadence is Monday morning or Friday end-of-week.

## Step 0: Bootstrap workspace

Follow `shared-references/workspace-layout.md` to ensure `.job-scout/` exists. Then follow `shared-references/archive-pass.md` (run the daily-gated 60-day rotation) and `shared-references/render-orchestration.md` Step G (lifecycle cleanup of old reports).

## Step 0a: Context line

Read `.job-scout/tracker.json` and present a one-line status:

```
📊 Deep sweep. Tracker: {{seen}} seen, {{a_tier}} A-tier, {{applied}} applied. Last deep-sweep: {{N}} days ago (or "first run").
```

`last_deep_sweep` is stored as `tracker.stats.last_deep_sweep` — date only (`YYYY-MM-DD`). Compare to today's date to compute N.

## Step 1: Load profile, CV, requirements, dimensions

Follow `shared-references/cv-loading.md`. Read `user-profile.json` for `target_titles[]`, `segment`, `requirements`, `cv_summary`, `dimensions[]`. If `target_titles` is empty, fall through to `cv_summary.target_roles`. If both are empty, stop and ask the user to run `/analyze-cv` first — `/deep-sweep` needs declared targets.

## Step 2: Multi-query fanout planning

Build the query plan as in `../job-search/SKILL.md` Step 2 (zero-arg branch) — one entry per `target_titles[]` element with `source: "primary"`. Synonym expansion happens reactively in Step 3 when a query is thin.

## Step 3: Run all primary queries (Past Week, pages 1-3)

For each entry in the query plan:

1. Navigate to `https://www.linkedin.com/jobs/`. Enter the title. Set filters from `requirements`: location, work_arrangement, contract_type, seniority. Date Posted: "Past Week".
2. Page 1: scroll, collect all job IDs.
3. Page 2: click pagination, scroll, collect.
4. Page 3: click pagination, scroll, collect. Stop here even if more pages exist — `/deep-sweep` is bounded.
5. Dedupe collected IDs against `tracker.json`. Count NEW (post-dedupe) IDs for this query.
6. **Adaptive synonym expansion:** if `count < 5` AND the entry is `source: "primary"`, generate 2-3 synonym variants via the LLM prompt in `../job-search/SKILL.md` Step 3b, append them to the query plan with `source: "synonym"`, and process them the same way (max 3 synonyms per primary; do not synonym-expand a synonym).

## Step 4: Sweep Top picks

Navigate to `https://www.linkedin.com/jobs/collections/recommended/`. Scroll 2-3 times to load extended recommendations (more than the daily-driver's one-page sweep). Collect job IDs. Tag `source: "Top Picks"`. Dedupe against `tracker.json`.

## Step 5: Sweep Saved jobs

Navigate to `https://www.linkedin.com/my-items/saved-jobs/`. Scroll until all saved entries are loaded. Collect IDs. Tag `source: "Saved"`. Dedupe against `tracker.json`.

## Step 6: Combine all new IDs and extract

Combine the new (post-dedupe) IDs from Steps 3, 4, and 5 into one to-process list, preserving the source tag per ID. If the same ID appears with multiple sources, preserve priority: `Job Alert (n/a here) > Top Picks > Saved > Search`.

For each ID:

1. Open the listing. Extract title, company, location, salary, requirements, full description text, Easy Apply status, posting date, applicant count, job URL.
2. Persist the JD to `.job-scout/jds/<id>.txt` per `../shared-references/jd-storage.md`.
3. Set `jd_path` and `source` on the tracker entry.
4. Run JD keyword extraction per `../shared-references/jd-keyword-extraction.md`.

## Step 7: Gate + score

Load `_job-matcher` (which transitively loads `_gate-engine`). For each new job:

1. `_gate-engine` runs first. If gated → `tier: D`, persist `gate_violations`, skip dimension scoring.
2. Otherwise → segment-aware rubric using `user-profile.dimensions[]` (or default if absent). Persist `tier`, `dimensions`, `tier_reason`, `rubric_version: "v1"`.

## Step 8: Similar-jobs expansion from A-tier hits

After Step 7, iterate every job in this run that came out at `tier: "A"` (not gated):

1. For each A-tier seed, navigate to its listing page if not already there. Scroll to the "Similar jobs" rail.
2. Collect IDs from the rail (up to 5 per seed — LinkedIn's typical rail length).
3. Filter against `tracker.json`.
4. For each new ID: extract → JD persist → set `source: "Similar"` → tag `notes` with `"expanded from: <seed_job_id>"` → gate → score.

Cap: 5 similar-jobs per A-tier seed.

## Step 9: Build results payload

Construct a `data` payload for the render layer with these view-specific fields:

```json
{
  "title": "Deep sweep — {{date}}",
  "subtitle": "{{N_queries}} queries · {{N_new}} new jobs · A:{{a}} B:{{b}} C:{{c}} · Filtered:{{gated}}",
  "generated_at": "<YYYY-MM-DD HH:MM>",
  "filename": "deep-sweep-{{date}}.html",
  "queries": ["<title1>", "<title1 synonym>", "..."],
  "source_breakdown": { "Search": <n>, "Top Picks": <n>, "Saved": <n>, "Similar": <n> },
  "tier_counts": { "a": <a_count>, "b": <b_count>, "c": <c_count>, "d": <d_count>, "total": <total> },
  "results": [ /* same shape as job-search.results[] including dimensions, gate_violations, source, matched_query */ ]
}
```

Filename uses the run date — `/deep-sweep` is a time-series view, not a snapshot. Each run produces its own file; older files are archived per `render-orchestration.md` Step G's 90-day policy.

Merge all scored jobs into `tracker.json`. Update `tracker.stats.last_deep_sweep` to today's date (`YYYY-MM-DD`).

## Step 10: Render

Follow `../shared-references/render-orchestration.md` end-to-end with `view: "deep-sweep"`. Templates live at `../_visualizer/templates/html/deep-sweep.html.j2` and `../_visualizer/templates/markdown/deep-sweep.md.j2` — same shape as `match-jobs` / `job-search` templates with the per-source-tag chip and per-query attribution.

Summary line on completion: `✓ Deep sweep — {{N_queries}} queries ({{N_synonym}} synonym variants) · {{N_new}} new jobs surfaced from {{source_count}} surfaces — A:{{a}} B:{{b}} · Filtered:{{gated}} — opened report in Chrome`.

## Failure modes

- **LinkedIn rate-limits** the user's session during the run. The agent should stop, report which query was in flight, save partial state to tracker, and suggest re-running in 30-60 min.
- **No A-tier survivors** → Step 8 is a no-op. Note this in the summary; consider broadening synonyms or relaxing dealbreakers if no A-tier hits across a deep sweep.
- **Profile or CV is stale** (>30 days since `last_updated`) → warn at Step 1 and offer to abort so the user can re-run `/analyze-cv` first.

## State files

- **`.job-scout/tracker.json`** — every new ID persisted with source attribution.
- **`.job-scout/jds/<id>.txt`** — full JD per `jd-storage.md`.
- **`.job-scout/cache/scores.json`** — score-cache writes per `_job-matcher` contract.
- **`.job-scout/reports/deep-sweep-<date>.html`** — the report.

## Reference materials

- `../job-search/SKILL.md` — single-query mechanics + synonym expansion prompt.
- `../check-job-notifications/SKILL.md` — daily-driver sweep, source attribution, dedupe.
- `../_gate-engine/SKILL.md` — hard-gate evaluation.
- `../_job-matcher/SKILL.md` — v1 rubric + dimension breakdown + lazy rescore.
- `../shared-references/canonical-schemas.md` — tracker/source/tier shapes.
- `../shared-references/jd-storage.md` — JD blob storage.
- `../shared-references/archive-pass.md` — 60-day tracker rotation.
- `../shared-references/render-orchestration.md` — Tier 1 render flow.

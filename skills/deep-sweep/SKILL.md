---
name: deep-sweep
description: Weekly thorough LinkedIn sweep across all source surfaces with multi-query fanout and similar-jobs expansion
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
disable-model-invocation: true
---

A weekly thorough sweep of LinkedIn for new opportunities. Where `/check-job-notifications` is the daily fast catch (notifications + Top picks + Saved, page 1, ~5 min), `/deep-sweep` is the weekly thorough scan — the full query plan v2 from `../shared-references/linkedin-search.md` (Boolean title-cluster queries, skill-combination queries, geo iteration, synonym rescue), all source surfaces, Past Week filter, pages 1-3 per query, similar-jobs expansion from every A-tier hit. Expected runtime: 15-20 min. Run it once a week to catch listings the daily sweep misses.

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

## Step 2: Query plan v2

Build the plan per `../shared-references/linkedin-search.md` §3, exactly as `../job-search/SKILL.md` Step 2 (zero-arg branch): Boolean title-cluster queries from `query_clusters[]` (per-title fallback), 2–3 skill-combination queries when the keyword corpus has ≥10 source jobs, geo iteration across `location_preferences[]`, ordering from `.job-scout/cache/query-stats.json` (proven first, retired excluded). Synonym rescue happens reactively in Step 3 when a query is thin.

## Step 3: Run all planned queries (Past Week, pages 1-3)

For each entry in the query plan:

1. **Construct the filter-addressed URL** per `linkedin-search.md` §1: encoded Boolean `keywords`, `location` for the entry's market, `f_WT` from `work_arrangement`, `f_JT` from `contract_type`, `f_TPR=r604800` (Past Week), `sortBy=DD`. Navigate straight to it. On the run's first query, confirm the filter chips took; on drift, fall back to the UI for that filter and note it in the summary.
2. Page 1: scroll, collect all job IDs.
3. Page 2: click pagination, scroll, collect.
4. Page 3: click pagination, scroll, collect. Stop here even if more pages exist — `/deep-sweep` is bounded.
5. Dedupe collected IDs against `tracker.json` — by ID, then by repost fingerprint per `linkedin-search.md` §5 (matches bump `last_seen`, log `repost id: <new_id> (<date>)` in notes, and are dropped). Count NEW (post-dedupe) IDs for this query and record query stats per §4.
6. **Adaptive synonym rescue:** if `count < 5` AND the entry is `family: "title"`, generate 2-3 synonym variants via the LLM prompt in `../job-search/SKILL.md` Step 3b, append them to the plan with `family: "synonym"`, and process them the same way (max 3 per thin query; never expand a synonym; skip retired variants, fold promoted ones into their cluster).

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

After scoring, complete the query-stats writes per `linkedin-search.md` §4: add each new job's tier to its originating query's `new_tier_counts`, update `consecutive_zero_new`, apply retirement (3 consecutive zero-new runs) and synonym promotion (≥3 A/B-tier hits → propose adding to the cluster, on user confirmation).

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
  "results": [ /* same shape as job-search.results[] including dimensions, gate_violations, source, matched_query, fresh */ ]
}
```

Within each tier, order results by `posted_at` descending and set `fresh: true` per `linkedin-search.md` §6 — A/B-tier jobs posted within 48 hours (with low applicant counts when known) get the "⚡ apply early" chip.

Filename uses the run date — `/deep-sweep` is a time-series view, not a snapshot. Each run produces its own file; older files are archived per `render-orchestration.md` Step G's 90-day policy.

Merge all scored jobs into `tracker.json`. Update `tracker.stats.last_deep_sweep` to today's date (`YYYY-MM-DD`).

## Step 10: Render

Follow `../shared-references/render-orchestration.md` end-to-end with `view: "deep-sweep"`. Templates live at `../_visualizer/templates/html/deep-sweep.html.j2` and `../_visualizer/templates/markdown/deep-sweep.md.j2` — same shape as `match-jobs` / `job-search` templates with the per-source-tag chip and per-query attribution.

Summary line on completion: `✓ Deep sweep — {{N_queries}} queries ({{N_synonym}} synonym variants) · {{N_new}} new jobs surfaced from {{source_count}} surfaces — A:{{a}} B:{{b}} · Filtered:{{gated}} — opened report in Chrome`.

## Step 11: Widen to ultramode when opted in (default off)

This step is the only addition to this command's flow, and it is **strictly gated**. Read `user-profile.json` for the `ultramode` block (treat an absent block as `{default: false}`). **Only when `ultramode.default` is `true`**, after the LinkedIn sweep above (Steps 3–10) has fully completed, also run the multi-source ultramode external sweep so the user sees one combined ranked list across LinkedIn and the rest of the market:

- Follow `../ultramode/SKILL.md` Step 4 (the multi-source sweep flow) — **reference it, do not duplicate its body here.** Load `.job-scout/sources.json`. If it is absent, note that `/ultramode` onboarding is needed (`Run /ultramode once to build your source registry before the sweep can widen.`) and **skip gracefully** — do not run discovery from this command, and do not block the LinkedIn results already shown. Otherwise sweep the external sources into the **same `tracker.json`** (the deep-sweep run already loaded and wrote it), dedupe across sources, gate and score the genuinely-new roles through the unchanged scorer, and present the **unified, source-agnostic `ultramode` report** (one combined ranked list, rendered via `_visualizer` with `view: "ultramode"`) in place of the separate deep-sweep view.

**When `ultramode.default` is `false` or absent — the default — this command does exactly what it does today: Steps 0–10 only, no extra steps, no behaviour change.** The widening here is purely additive and never alters the pre-existing default path.

## Failure modes

- **LinkedIn rate-limits** the user's session during the run. The agent should stop, report which query was in flight, save partial state to tracker, and suggest re-running in 30-60 min.
- **No A-tier survivors** → Step 8 is a no-op. Note this in the summary; consider broadening synonyms or relaxing dealbreakers if no A-tier hits across a deep sweep.
- **Profile or CV is stale** (>30 days since `last_updated`) → warn at Step 1 and offer to abort so the user can re-run `/analyze-cv` first.

## State files

- **`.job-scout/tracker.json`** — every new ID persisted with source attribution.
- **`.job-scout/jds/<id>.txt`** — full JD per `jd-storage.md`.
- **`.job-scout/cache/scores.json`** — score-cache writes per `_job-matcher` contract.
- **`.job-scout/cache/query-stats.json`** — per-query yield memory per `linkedin-search.md` §4.
- **`.job-scout/reports/deep-sweep-<date>.html`** — the report.

## Reference materials

- `../shared-references/linkedin-search.md` — URL grammar, Boolean queries, query plan v2, query stats, repost dedupe, freshness.
- `../job-search/SKILL.md` — single-query mechanics + synonym expansion prompt.
- `../check-job-notifications/SKILL.md` — daily-driver sweep, source attribution, dedupe.
- `../_gate-engine/SKILL.md` — hard-gate evaluation.
- `../_job-matcher/SKILL.md` — v1 rubric + dimension breakdown + lazy rescore.
- `../shared-references/canonical-schemas.md` — tracker/source/tier shapes.
- `../shared-references/jd-storage.md` — JD blob storage.
- `../shared-references/archive-pass.md` — 60-day tracker rotation.
- `../shared-references/render-orchestration.md` — Tier 1 render flow.

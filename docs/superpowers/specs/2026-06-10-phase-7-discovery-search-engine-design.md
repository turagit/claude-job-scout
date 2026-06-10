# Phase 7 — Discovery & Search Engine Design Spec (v0.10.0)

**Status:** Approved 2026-06-10. Autonomous review-and-improve pass; mid-session the user narrowed the focus: *"focus on job discovery on LinkedIn, improved search on LinkedIn — these are the paths to increase the probability of finding jobs."* Side requirement from the same session: all user-facing tone is British English, no Americanisms.

> Numbering note: the roadmap previously reserved Phase 7 for triage-feedback UX. That work, the Phase 8 recruiter rebuild, and the Phase 9 nurture commands are **deferred, not cancelled** — they renumber to Phases 8–10. This phase takes the Phase 7 slot because discovery is the user's declared priority.

**Problem.** Discovery breadth shipped in v0.9.0 (multi-surface sweeps, adaptive fanout), but discovery *depth* is shallow:

1. **One naive query shape.** Every search types a bare title into the keywords box. LinkedIn's keywords field supports Boolean operators (`AND`, `OR`, `NOT`, quotes, parentheses) — a single well-crafted Boolean query covers 3–4 title synonyms in one pass and excludes known noise. The plugin never uses them.
2. **Filters are set by clicking the UI.** Slow, fragile, and re-done per query. LinkedIn job-search filters are addressable directly in the URL (`f_WT`, `f_TPR`, `f_JT`, `f_E`, `f_AL`, `sortBy`, `location`, `distance`). Direct URL construction is deterministic, faster, cheaper in browser steps, and makes every query reproducible.
3. **Title-only discovery misses retitled roles.** The biggest discovery gap is jobs whose titles don't match `target_titles[]` at all ("Platform Reliability Lead" when the user targets "SRE Manager"). The JD-keyword corpus the plugin has been harvesting since v0.5.0 is exactly the raw material for *skill-combination queries* — and it is consumed by nothing search-side today.
4. **No learning loop.** The plugin never records which queries actually produce new, high-tier jobs. Dead queries re-run forever; high-yield queries get no priority; synonym variants are regenerated from scratch each run and immediately forgotten.
5. **Reposts burn tokens and pollute reports.** LinkedIn re-lists the same role under fresh job IDs. ID-based dedupe doesn't catch this; the same job gets re-extracted, re-scored, and re-presented.
6. **Freshness is under-exploited.** Applying within the first day or two of posting measurably raises response rates. Posting date and applicant count are already extracted but drive nothing.
7. **Alerts are manual.** `/create-alerts` asks the user to dictate criteria instead of deriving them from `target_titles[]` and the queries that are known to perform — alerts are the only discovery surface that works while the user sleeps.

A parallel read-through of all 22 skills also found **contract drift** that corrupts what discovery produces (details in § Repairs), the **v0.9.1 template-parity debt** (dimension breakdowns missing from most report templates), and **pervasive Americanisms** despite the locked Phase 5 British-voice decision.

**Goal.** Ship v0.10.0 where every LinkedIn search the plugin runs is a crafted, filter-addressed, learning query; where retitled roles are discoverable through skill-based queries; where reposts cost nothing; and where the results the user sees are accurate, fully explained, and in British English.

---

## Decisions

1. **Direct URL construction replaces UI filter-clicking** for every job search. A new shared reference `linkedin-search.md` is the single source of truth for the URL grammar (parameters below) and Boolean keyword syntax. If LinkedIn drifts a parameter, the fallback is the existing UI-filter path — the reference documents both.
   - Base: `https://www.linkedin.com/jobs/search/?keywords=<url-encoded>&location=<url-encoded>`
   - `f_WT` workplace: `1` on-site, `2` remote, `3` hybrid (comma-combinable) — from `requirements.work_arrangement`.
   - `f_TPR` recency: `r86400` 24 h, `r604800` week, `r2592000` month — daily sweeps use 24 h–week, `/deep-sweep` uses week.
   - `f_JT` job type: `F` full-time, `C` contract, `T` temporary, `P` part-time — from `requirements.contract_type`.
   - `f_E` experience level `1`–`6` — derived from `requirements.seniority_floor` when mappable; omitted otherwise (the gate engine remains the enforcement point).
   - `f_AL=true` Easy Apply only — never set by default (it hides most of the market); available as an explicit user ask.
   - `sortBy=DD` (date) for sweeps so pagination depth maps to recency; `R` (relevance) only for explicit single-title searches.
2. **Query plan v2 — three query families, one plan.**
   - **Title queries:** one Boolean query per *title cluster* instead of one bare query per title. `/analyze-cv` Step 3d (new) groups `target_titles[]` into clusters of true synonyms and writes `query_clusters[]` to `user-profile.json`; each cluster renders as `("Title A" OR "Title B" OR "Title C")`, optionally with a shared `NOT` tail for noise the user has named (e.g. `NOT (intern OR graduate)`). Workspaces without `query_clusters[]` fall back to per-title queries — never blocked.
   - **Skill queries:** 2–3 queries built from high-signal skill pairs — drawn from the JD-keyword corpus (top co-occurring required skills across A/B-tier jobs) intersected with `cv_summary.key_skills`, e.g. `(Kubernetes AND Terraform) AND ("platform" OR "infrastructure")`. These catch retitled roles. Skill queries run in `/deep-sweep` always and in zero-arg `/job-search` when the corpus has ≥10 source jobs (below that the corpus is noise).
   - **Geo iteration:** when `location_preferences[]` names multiple markets, the plan iterates them per query via the `location=` parameter rather than relying on one blended search.
   - Adaptive synonym expansion (v0.9.0) survives unchanged as the thin-query rescue, with one upgrade: variants that produce new jobs are *remembered* (Decision 3) instead of regenerated.
3. **Query performance memory** at `.job-scout/cache/query-stats.json`. After every sweep, each executed query records: query string, family (`title|skill|synonym|explicit`), run date, candidate IDs seen, new IDs after dedupe, and tier outcomes of the new IDs once scored. Consequences:
   - Plan ordering: proven queries run first (yield per run, recency-weighted).
   - Retirement: a query with three consecutive zero-new-ID runs is dropped from the default plan (kept in the file, marked `retired`, revivable); its slot goes to a fresh LLM variant.
   - Promotion: a synonym variant that yields ≥3 new A/B-tier jobs across runs is promoted into its title cluster, so it runs every time without re-generation.
   - The stats are a cache: deletable at any time; absence simply means a cold-start plan.
4. **Repost fingerprint dedupe.** Alongside ID dedupe, every sweep computes `fingerprint = lower(company)|lower(title)|lower(location)` per candidate. A fingerprint already in the tracker (over non-rejected entries) means *repost*: bump `last_seen`, append the new job ID to the existing entry's `notes` (`repost id: <new_id>`), and skip extraction and scoring entirely. No schema change — the fingerprint is computed on the fly from fields the tracker already holds.
5. **Freshness surfacing.** Sweep payloads carry `posted_at` and `applicants` (already extracted). Reports order same-tier jobs by recency, and A/B-tier cards posted within ~48 h with low applicant counts get an "apply early" flag — the cheapest response-rate lever that exists. Display-only; no schema change.
6. **`/create-alerts` zero-arg auto-derivation.** With no argument, the command proposes 3–5 alerts derived from title clusters (plus the top-performing skill query when stats support it): broadest cluster daily, the rest weekly, filters matched to `requirements` via the same URL grammar. The user approves or edits before anything is created. The old interactive flow remains behind `/create-alerts manual`.
7. **Tier is the canonical currency; the aggregate score retires from all contracts.** Sweep payloads carry uppercase `tier`, `dimensions`, `tier_reason`, `gate_violations`, `rubric_version`; `score` becomes tolerated-legacy-optional. Report ordering = tier, then freshness. (Repairs R1–R6 below make this true everywhere it currently isn't.)
8. **British English is the plugin's default register** — new CLAUDE.md hard rule: all user-facing copy and generated drafts default to British English (spelling, idiom, `D Month YYYY` dates) unless `tone.dialect` says otherwise. `voice-profile.md` gains a concrete Americanism avoid-list. Unchanged: command names, directory names, JSON keys, file paths, CSS classes, code identifiers, historical CHANGELOG entries.
9. **Out of scope:** target-company page sweeps (still deferred from Phase 6 grilling), outbound recruiter sourcing, triage-chip UX / recruiter rebuild / nurture commands (renumbered Phases 8–10), FX conversion for rate gates, any browser mechanism beyond the Chrome extension, scheduled invocation.

## Repairs (accuracy drift found in review — discovery output must be trustworthy)

- **R1 `check-job-notifications`:** delete the hard-coded "Default Requirements (Always Active)" block (contradicts Step 5's own removal note; user-specific leakage). Fold legacy Step 6 (pre-v0.8.0 `score`/`breakdown` subagent contract, "Tiers: A (85-100)") into Step 5's v1 contract — one scoring step. Comp-disclosure ordering becomes a sort preference, not a filter.
- **R2 aggregate-score ghosts:** `match-jobs` Step 5 payload, `render-orchestration.md` Step A tier-classification table, and `_job-matcher`'s cache-write shape still carry `score` and 85/70/55 thresholds; `match-jobs` uses lowercase tiers where every other sweep uses uppercase. Unify per Decision 7. `render-orchestration.md` also gains the missing `deep-sweep` rows in its view/filename/summary tables.
- **R3 dead JD reads:** `/cover-letter` and `/interview-prep` read `tracker.jobs.<id>.description`, removed from the v2 schema. Reads go through `jd_path` (`.job-scout/jds/<id>.txt`), fetch-and-persist on miss. `/cover-letter`'s no-arg picker sorts by tier+recency, not score.
- **R4 `/check-inbox`:** `lead_tier` "lukewarm" isn't in the canonical enum (`hot|warm|cold|non-lead`); Step 2 categories must map to the enum, with scam signals recorded in `lead_tier_detail`.
- **R5 `funnel-report`:** "scored" computed as `score is non-null` — always false for v1 entries. Becomes `rubric_version` present. Drop-off recommendation table references re-checked against current commands.
- **R6 `_cover-letter-writer` / `_cv-section-rewriter` / `/cover-letter`:** still pass the retired `tone_preference` enum; switch to the canonical `tone` block (its consumers and read pattern are already specified in `voice-profile.md`).

## Template parity (v0.9.1 debt — the discovery reports must show their reasoning)

Dimension breakdowns + gated "Filtered out" groups exist only in `deep-sweep.html.j2`, `deep-sweep.md.j2`, `match-jobs.md.j2`. Bring `match-jobs.html.j2`, `job-search.html.j2`, `job-search.md.j2`, `check-job-notifications.html.j2`, `check-job-notifications.md.j2` to the deep-sweep pattern: uppercase tier pills, per-dimension evidence table for A/B-tier, gated banner group, source chips, freshness flag (Decision 5). `_visualizer/SKILL.md` and `component-library.md` updated to match.

## Schema impact

None requiring migration. `user-profile.json` gains optional `query_clusters[]` (additive; absent → per-title fallback). `query-stats.json` is a new cache file (deletable). Tracker, threads, statuses untouched.

## Workstream map

| # | Workstream | Touches |
|---|---|---|
| W1 | `linkedin-search.md` reference + query plan v2 | new shared ref; `job-search`, `deep-sweep`, `check-job-notifications` (URL-addressed surfaces), `analyze-cv` (Step 3d clusters) |
| W2 | Query stats + retirement/promotion; repost dedupe | new cache contract section in `linkedin-search.md`; all sweep commands |
| W3 | `/create-alerts` auto-derivation | `create-alerts` |
| W4 | Repairs R1–R6 | per repair |
| W5 | Template parity + freshness flag | 5 templates, `_visualizer/SKILL.md`, `component-library.md` |
| W6 | British voice pass | CLAUDE.md, `voice-profile.md`, all user-facing prose, README, plugin.json description |

## Verification

No automated suite (per CLAUDE.md). Checks: `grep` zero-hit sweeps for retired tokens (`Default Requirements`, `.description`, `lukewarm`, `tone_preference`, `score >= 85`, lowercase tier payloads); `python3`+`jinja2` render of every touched template against sample payloads (gated, non-gated, empty); URL-grammar examples in `linkedin-search.md` hand-checked for well-formed encoding; Americanism `grep -i` sweep over user-facing strings; full read-through of each modified SKILL.md for internal consistency.

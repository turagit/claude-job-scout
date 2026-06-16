# Changelog

All notable changes to the LinkedIn Job Hunter plugin are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project aims to follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.12.0] — 2026-06-16

Phase 12 — Discovery & categorisation foundations ("Phase A"). Discovery and matching are mature, but the biggest remaining challenge is unearthing the roles you are a *great* match for. Two leaks remained: **"right job, wrong words"** — great-fit roles written in different vocabulary (retitled, jargon-rebranded, or described at the function level rather than the tool level) that lexical Boolean queries miss; and a **flat A/B/C list** that doesn't distinguish where you are a genuine standout from where you are merely qualified, nor how confident each match is. This release widens recall via a CV-derived capability graph and a jargon/alias map feeding the existing query plan, and sharpens categorisation with a parallel competitiveness signal plus deterministic confidence and explanation-tag badges — **without** disturbing the v1 tier rubric, the score cache, or dedupe-before-extract. Everything is additive and there is **no migration**.

### Added

- **CV capability graph** — a new `/analyze-cv` discovery step (between dimensions and clusters) runs one LLM pass over your CV to derive `{stated, latent, adjacent}` capabilities, **presented for approval/trim** like dimensions and clusters, then cached to `.job-scout/cache/capability-graph.json` (keyed by `cv_hash`, rebuilt when the CV changes). It surfaces the functional and adjacent capabilities behind your stated skills so reworded roles can be found. Existing workspaces auto-build on the first discovery run when the cache is absent, with a one-time "review these?" prompt — no need to redo `/analyze-cv` from scratch.
- **Jargon/alias recall layer** — `.job-scout/cache/jargon-normalizer.json` (persistent), seeded with a conservative, human-reviewed alias map of high-confidence title and skill synonyms, grown from the `jd-keyword-corpus` and a first-encounter LLM expansion. Conservative seeding limits false-positive equivalences.
- **`capability` query family** — the capability graph and the alias map emit a new query family into the plan, feeding `/job-search`, `/deep-sweep`, and ultramode. It is **recall-only** (query-expansion, with no pre-scoring filter — the gate engine and rubric remain the only things that drop a job), capped at ~2–3 queries per run, and governed by the existing `query-stats` retire/promote lifecycle: a query with three consecutive zero-new runs retires; a query yielding ≥3 A/B-tier jobs promotes into its cluster. The exploratory footprint is therefore self-limiting.
- **Candidate competitiveness** — inside the existing batched scoring fan-out, `_job-matcher` emits `competitiveness: high | med | low` (plus one evidence quote) for **A/B-tier jobs only** (gated-D and weak C are skipped). It rides *beside* the A/B/C/D tier as additive metadata for within-tier sorting and badges; it does not change what A/B/C mean.
- **Deterministic confidence + explanation tags** — `confidence: high | med | low` and `match_explanation_tag` (`all-fit | one-gap | multiple-gaps | overqualified | underqualified | trajectory-concern`) are derived deterministically from the per-dimension tiers — no extra LLM call.
- **Competitiveness, confidence, and explanation-tag badges with within-tier confidence sort** — `_visualizer` adds the three badges to the Tier 1 job cards and sorts **within each tier by confidence (high → med → low) then recency**, so the bulletproof standout matches rise to the top of their tier. Rendered through `_visualizer` per Hard Rule #8; British English.

### Changed

- **`dimensions[]` gains an optional `type`** (`load-bearing` | `modifying`) — additive, defaulting to load-bearing when absent. It feeds the deterministic confidence and explanation-tag derivations (e.g. a D in a *modifying* dimension reads as `trajectory-concern`, not a hard fail). Existing dimensions without a `type` keep working unchanged.
- **`query-stats` `family` gains `capability`** — the new family slots into the existing retire/promote lifecycle (a new `family` value; no other schema change).
- **Tracker job entries and the score-cache value object** gain four additive optional fields — `competitiveness`, `competitiveness_evidence`, `confidence`, `match_explanation_tag` — populated **lazily** on the next scoring. The score-cache **key is unchanged** (`…:v1`): **no `rubric_version` bump, the v1 tier rubric and the score cache are untouched, and there is no migration.** Pre-Phase-A entries simply lack these fields and gain them on next view.

## [0.11.0] — 2026-06-15

Phase 11 — Ultramode. LinkedIn is one market surface; for many candidates the highest-signal roles live elsewhere — on employer ATS boards (often posted there *before or instead of* LinkedIn), on occupation- and geography-specific boards, on remote-native feeds, in freelance marketplaces, and in community channels. This release adds an opt-in, source-agnostic sweep that widens sourcing beyond LinkedIn into a per-workspace, CV-derived, **verified** set of external sources, then folds every job — wherever it came from — into the *same* tracker, scoring, and render pipeline. The LinkedIn core ships **unchanged**; ultramode is additive and defaults **off**.

### Added

- **`/ultramode` command** — opt-in multi-source discovery and sweep beyond LinkedIn. Carries `disable-model-invocation: true`. Sub-commands: `/ultramode` (run the external sweep and render its own report), `/ultramode sources` (re-run discovery or edit the registry), `/ultramode onboarding` (re-run the lane interview). Off by default; the LinkedIn pipeline is untouched.
- **Verified per-workspace source registry** — `.job-scout/sources.json`, built by the new `_source-discovery` subagent. First run elicits your `base_country` (asked explicitly, always confirmed out loud, never inferred) plus target geography, work arrangement, contract type, and field, reading what it can from your CV and the existing keyword corpus. Discovery enumerates candidate sources along independent axes (category, region, occupation + synonyms, professional bodies, live web search), **live-probes and adversarially verifies** every candidate before it enters the registry — confirming it is live, carries roles for this lane, and classifying its access lane (`api | rss | html | extension`) — and loops until fresh strategies surface nothing new. Nothing enters the registry on the model's word alone. A small universal aggregator backbone is always available so even rare lanes get coverage out of the box.
- **`_source-sweep` subagent** — per-source candidate-collection that honours **dedupe-before-extract**: it collects candidate IDs, filters against `tracker.json` first, then fetches and scores only new roles. Honours each source's recorded `poll_method` and access lane, filters client-side over full text (server-side feed filters proved unreliable), and auto-seeds the ATS company watchlist from your tracker's A/B-tier employers plus `requirements.companies_to_target[]`.
- **Unified, source-agnostic, tier-ranked report** — every job from every source appears in one list, source shown only as a chip (never the organising axis), ranked by tier A→B→C and freshest-first within tier. Each row carries a direct **apply-at-source** link to the canonical, direct-to-employer listing (employer ATS > LinkedIn > aggregator > marketplace), plus an "also seen on N sources" line. Gated jobs collapse into the existing "Filtered out" group. Rendered through `_visualizer` per Hard Rule #8 — no new scoring, gating, or render layer; ultramode reuses `_job-matcher`, `_gate-engine`, and `_visualizer` as-is and adds only the source chip, the alternates line, and the apply-at-source call to action.
- **Keyless-first sourcing** — ultramode works immediately with zero keys (ATS boards, niche and remote feeds, Hacker News, any keyless aggregator). When discovery finds a keyed aggregator that materially improves *this* lane's coverage, it prompts inline with the signup link and gracefully skips if declined. Keys live in gitignored workspace config (`config.json` → `ultramode.api_keys`) and are never entered into a browser form.
- **`ultramode.default` `/config` toggle** (default `false`) — when set, the existing `/job-search` and `/deep-sweep` sweeps widen to the external registry automatically, so you do not have to remember to run `/ultramode` separately.
- **`requirements.base_country`** and **`requirements.target_geography`** profile fields, plus an additive `ultramode` block (`default`, `api_keys`, `registry_built_at`). All optional; absent means ultramode off or cold-start.
- **`shared-references/ultramode-sources.md`** — source taxonomy (six universal categories: `ats-provider · remote-board · aggregator · eu-national-board · freelance-marketplace · community`), access-lane definitions, the universal backbone list, ATS slug-resolution by probe-and-cache, the client-side-filter rule, and the cross-source dedupe + direct-to-employer canonical preference.

### Changed

- **Tracker `source` is now a structured object** `{ lane, provider, board }` (e.g. `{lane: "ats", provider: "greenhouse", board: "miro"}`), replacing the six-value LinkedIn-only string enum. Readers carry a back-compatible shim that lifts any legacy string into `{lane: "linkedin", provider: "linkedin", board: <string>}`, so existing trackers keep working untouched. Bumps the tracker file `schema_version` (v2 → v3).
- **External job IDs are namespaced and filesystem-safe** — `<provider>__<board>__<externalid>` — so tracker keys, score-cache keys, and `jds/<id>.txt` paths never collide across sources.
- **`browser-policy.md` gains a `WebFetch` carve-out** — a plain read-only HTTP GET against a public endpoint is not browser automation. Hard Rule #1 continues to govern all *in-browser* work; the Chrome extension remains the only mechanism that touches your logged-in session. No new browser-automation framework is introduced.

## [0.10.0] — 2026-06-10

Phase 7 — the discovery and search engine. Coverage (v0.9.0) told the plugin *where* to look; this release transforms *how* it searches: crafted Boolean queries, filter-addressed URLs, skill-based discovery of retitled roles, and a learning loop that improves the plan every run. Plus the v0.9.1 template-parity debt, a set of contract repairs, and a full British-English pass.

### Added

- **`shared-references/linkedin-search.md`** — the single source of truth for LinkedIn searching: filter-addressed URL grammar (`f_WT`, `f_TPR`, `f_JT`, `f_E`, `sortBy=DD`, …), Boolean keyword craft, query plan v2, query-stats contract, repost dedupe, freshness rules.
- **Boolean title-cluster queries** — `/analyze-cv` Step 3d groups `target_titles[]` into synonym clusters with optional `NOT` tails, stored as `user-profile.json.query_clusters[]` (optional, additive). One cluster query covers what used to take three searches. Per-title fallback when absent.
- **Skill-combination queries** — `/job-search` and `/deep-sweep` build 2–3 queries from the JD-keyword corpus (top co-occurring A/B-tier skills ∩ CV skills, with a context anchor) once the corpus has ≥10 source jobs. Finds well-matched roles whose titles match nothing in `target_titles[]` — the largest discovery gap.
- **Geo iteration** — every query runs once per market in `location_preferences[]` via the `location=` URL parameter.
- **Query learning loop** — `.job-scout/cache/query-stats.json` records each query's yield and tier outcomes. Proven queries run first; queries with three consecutive empty runs retire; synonym variants with ≥3 A/B-tier hits are promoted into their cluster (with user confirmation).
- **Repost fingerprint dedupe** — `company|title|location` fingerprint check in every sweep's dedupe step. Re-listed jobs under fresh IDs are recognised, logged on the original entry, and skipped — no extraction, no scoring, no duplicate card.
- **Freshness surfacing** — same-tier results order by posting date; A/B-tier jobs posted within 48 hours carry an "⚡ apply early" chip in every sweep view.
- **`/create-alerts` auto-derivation** — zero-arg proposes 3–5 alerts from the query clusters (plus the best-performing skill query), filters matched to `requirements`; the old interactive flow lives at `/create-alerts manual`.
- **British-English default** — new CLAUDE.md hard rule; `voice-profile.md` carries the avoid-list. All user-facing copy and generated drafts default to British English unless `tone.dialect` says otherwise.
- `score-pill tier-d` style in `theme.css` (muted) for completeness.

### Changed

- **All searches navigate to constructed filter URLs** instead of clicking the LinkedIn filter UI — deterministic, reproducible, fewer browser steps. UI filters remain the documented fallback on parameter drift.
- **Template parity (the v0.9.1 debt):** `match-jobs`, `job-search`, and `check-job-notifications` HTML + markdown templates now match the deep-sweep pattern — uppercase tier pills, per-dimension evidence tables, collapsed "Filtered out" gated group, source chips.
- **Aggregate score fully retired from contracts:** `match-jobs` payloads, `render-orchestration.md`, and `_job-matcher`'s cache-write shape carry `tier` + `dimensions` only (the 85/70/55 threshold prose is gone); tiers are uppercase everywhere; `deep-sweep` added to the render-orchestration view tables.
- `/check-job-notifications`: the hard-coded "Default Requirements (Always Active)" block is removed (filtering belongs to user-declared dealbreakers via `_gate-engine`); the legacy pre-v0.8.0 scoring step is folded into the v1 rubric fan-out; compensation disclosure is now an ordering preference, not a filter.
- `/cover-letter` and `/interview-prep` read JDs via `jd_path` (`.job-scout/jds/<id>.txt`) with fetch-and-persist on miss — the inline `description` field they referenced was removed from the schema in v0.8.0.
- `/check-inbox` uses the canonical `lead_tier` enum (`hot | warm | cold | non-lead`); red-flag signals live in `lead_tier_detail`; thread payloads surface `linked_jobs` with tiers.
- The structured `tone` block replaces the retired `tone_preference` enum in every drafting contract (`/cover-letter`, `_cover-letter-writer`, `_cv-section-rewriter`, `_cv-optimizer` dispatch); `response-templates.md` gains a voice-first preamble.
- `funnel-report` computes the "scored" stage from tier presence (works on v1 entries, which carry no `score`), and recommends the freshest A-tier first.
- British-English spelling sweep across all prose (identifiers, command names, JSON keys, and file paths unchanged; historical changelog entries untouched).

### Fixed

- `deep-sweep.md.j2` crashed on render: jq-style `{{ x // "" }}` coalesce is invalid Jinja (integer division) — replaced with `{{ x or "" }}`. All 16 view/format/payload render combinations now verified with Jinja2.
- Removed the orphaned v0.1 `matching-weights.md` (keyword-bingo weights contradicting the v1 rubric).

### Deferred

- The previously-queued triage-feedback UX, recruiter rebuild + `/config tone`, and nurture commands renumber to Phases 8–10 — discovery took priority by user direction.

## [0.9.0] — 2026-05-26

Phase 6 — deep LinkedIn coverage. The accuracy work in v0.8.0 cleared the false-positive floor; this release expands the surface area the plugin actually sees.

### Added

- **`/deep-sweep` command** — new weekly thorough scan. Adaptive multi-query fanout across all `target_titles[]` + LLM-generated synonyms (when a query is thin), all source surfaces (Search + Top picks + Saved + Similar from A-tier hits), Past Week filter, pages 1-3 per query. Expected runtime 15-20 min. Renders its own dated report (`deep-sweep-<date>.html`).
- **Adaptive multi-query fanout in `/job-search`** — zero-arg invocation iterates `user-profile.target_titles[]`. Any title yielding fewer than 5 surfaced jobs triggers 2-3 LLM-generated synonym variants. Single-arg behaviour (`/job-search <title>`) unchanged.
- **Top picks sweep in `/check-job-notifications`** — Step 2b navigates to `/jobs/collections/recommended/` after the notifications page. Closes the gap between the README's claim and the actual daily-driver behaviour.
- **Saved jobs sweep in `/check-job-notifications`** — Step 2c sweeps `/my-items/saved-jobs/`. Catches roles you bookmarked but the plugin never processed.
- **Similar-jobs expansion in `/check-job-notifications`** — Step 5b follows LinkedIn's "Similar jobs" rail for every A-tier survivor in the run; up to 5 expansions per seed. Tagged `source: "Similar"` with `notes: "expanded from: <seed_job_id>"`.
- **Recruiter-link parsing in `/check-inbox`** — Step 1b extracts canonical job IDs from every recruiter-thread message (full URLs, shortlinks, inline cards). New IDs are fed into the tracker with `source: "Inbox"` and run through the full gate + score chain. Bidirectional `thread.linked_job_ids[]` ↔ `tracker.jobs.linked_thread_ids[]` linkage populated.
- **`tracker.stats.last_deep_sweep`** field — date of the most recent `/deep-sweep` run; used by the command's context line.
- **`tracker.jobs.linked_thread_ids[]`** field — reverse pointer to recruiter threads (canonical schema already reserved the forward pointer in v0.8.0).
- Visualizer templates for the deep-sweep view (`skills/_visualizer/templates/html/deep-sweep.html.j2` and `.md.j2`) with per-source tag chips and per-query attribution.

### Changed

- `/check-job-notifications` daily-driver scope expanded from notifications-only to notifications + Top picks + Saved + similar-jobs-from-A-tier-hits, all in one pass with cross-source dedupe.
- `/job-search` source-payload schema gains `dimensions`, `gate_violations`, `tier_reason`, `rubric_version`, `source`, `matched_query` per result (catching up `/job-search` to the v0.8.0 v1 rubric output already used by `/match-jobs` and `/check-job-notifications`).
- `_job-matcher` reference list now points at `dimensions-default.md` as the bootstrap (v0.8.0 generalisation work — repeating here so a reader picking up only the v0.9.0 changelog sees the current shape).

### Out of scope / deferred to v0.9.1

- HTML template parity gap: `match-jobs.html.j2`, `job-search.html.j2`, `check-job-notifications.html.j2` still render the pre-v0.8.0 single-score card. Markdown templates have the v0.8.0 dimension breakdown; HTML doesn't yet. Users on `render: markdown` mode see the full v0.8.0/v0.9.0 output already; only the HTML auto-open mode is behind. Will land in v0.9.1.
- Per-card source chip styling in the existing match-jobs / job-search / check-job-notifications HTML templates (the new `deep-sweep.html.j2` includes it; the others need a sweep).

## [0.8.0] — 2026-05-26

### Added

- `skills/shared-references/canonical-schemas.md` — locked v2 schemas for `user-profile.json`, `tracker.json`, and `recruiters/threads.json`. One source of truth across all state writes.
- `skills/shared-references/state-validators.md` — pre-write enum + status-transition validators (`validate_tracker`, `validate_profile`, `validate_threads`) with the atomic-rename pattern.
- `skills/shared-references/jd-storage.md` — hybrid JD-blob storage contract. Full JD text lives at `.job-scout/jds/<job_id>.txt`; the tracker entry carries `jd_path` only.
- `skills/shared-references/voice-profile.md` — tone-block consumer contract. Every user-voiced surface (recruiter replies, cover letters, profile copy, CV bullet rewrites, interview-prep) reads the structured `tone` block from `user-profile.json`.
- `skills/shared-references/archive-pass.md` — daily-gated 60-day rotation procedure with full bash implementation.
- `user-profile.json.segment` field — free-text descriptor of the workspace's job-search lane (e.g. "permanent director roles in enterprise IT", "freelance backend contracts EU-remote", "head pastry chef in Lisbon"). Set by the user at `/analyze-cv` discovery.
- `user-profile.json.dimensions[]` field — per-workspace scoring rubric, generated by `/analyze-cv` against the user's CV, target_titles, segment, and requirements. The matcher reads this; if absent, falls back to the universal bootstrap in `_job-matcher/references/dimensions-default.md`.
- `user-profile.json.tone` block — structured voice profile (register, dialect, warmth, vocabulary cues, exemplars, avoid list) consumed by every user-voiced surface.
- `tracker.json.dimensions`, `gate_violations`, `rubric_version`, `reject_reason`, `rejected_at`, `approved_at`, `filtered_reason`, `tier_reason`, `jd_path` fields.
- Workspace schema-version bumped v1 → v3 (added `jds/` and `.backup/` directories; per-file `schema_version: 2` on the three state files).
- Score cache key now includes `rubric_version` — rubric upgrades invalidate stale entries automatically.
- New `_gate-engine` skill — hard-gate evaluator that runs before scoring. Any dealbreaker violation auto-D-tiers the job and skips dimension scoring.
- New `_job-matcher/references/dimensions-default.md` — universal 5-dimension bootstrap (Skills & technical fit / Role shape match / Domain & context / Engagement fit / Trajectory fit) with abstract A/B/C/D criteria that work for any job-search lane.
- `/analyze-cv` Step 3a/b/c — segment declaration (free-text), 7-category dealbreaker checklist + free-text follow-up, tone confirmation, and per-workspace dimensions discovery.
- `_visualizer` job-card v1 — renders dimension breakdown table with evidence quotes, or a "Filtered out" banner when `gate_violations` is non-empty.

### Changed

- `_job-matcher` rewritten to v0.2.0: rubric v1 is hard-gated and segment-aware. Replaces the v0.1 keyword-bingo weighted score. Output is per-dimension tiers with evidence quotes — no aggregate number; trust comes from the visible reasoning, not the hidden weight math.
- State writes now go through `validate_tracker` / `validate_profile` / `validate_threads`. Non-canonical statuses, tiers, lead-tiers, and segments are rejected at write time. Closes the loop that previously let writers invent ad-hoc enum values.
- Pre-existing workspaces are migrated in place by the one-shot script in `docs/superpowers/plans/2026-05-26-...`. Non-canonical statuses and tiers map to canonical values per the migration tables in the design spec. Every existing entry is tagged `rubric_version: legacy` and will lazy-rescore under v1 on first view. (The two workspaces used to develop this release migrated to: workspace A 502 → 500 jobs, 2 corrupt dropped; workspace B 268 jobs preserved.)
- `tracker.json` no longer carries inline `description`. Existing entries have `jd_path: null`; downstream commands (`/cover-letter`, `/interview-prep`) backfill lazily via fresh extraction.
- `_job-matcher` score-cache contract: key shape changes from `(job_id, cv_hash, profile_hash)` to `(job_id, cv_hash, profile_hash, rubric_version)`.
- `cv-loading.md`: explicit `sha1` CV-hash contract documented, with read/write paths.
- `check-job-notifications`, `job-search`, `match-jobs`: JD extraction now writes `.job-scout/jds/<id>.txt` and sets `jd_path` on the tracker entry per the hybrid-storage contract. The `_gate-engine` runs before scoring; gated jobs appear in a collapsed "Filtered out" section.

### Removed

- Two segment-specific dimension reference files (an initial mid-release draft) that encoded industries and tools from the workspaces used during development, making the plugin user-shaped rather than user-agnostic. Replaced by the universal `dimensions-default.md` + per-workspace `dimensions[]` discovery at `/analyze-cv` time. Any user's job-search lane (baker, construction engineer, sales executive, etc.) is now first-class.

## [0.7.0] — 2026-04-29

### Added

- Visual render layer for Tier 1 user-facing commands. `/match-jobs`, `/job-search`, `/check-job-notifications`, `/funnel-report`, `/check-inbox`, and `/interview-prep` now produce a Modern Cards–styled HTML report that auto-opens in Chrome via the existing extension.
- New `_visualizer` subagent (`skills/_visualizer/`) — dispatches via the `Agent` tool, returns a delta-only response per the existing subagent protocol. Templates, theme tokens, and asset bundle live in a single skill.
- New `/config` slash command for viewing and changing per-workspace settings (`.job-scout/config.json`).
- New shared reference `skills/shared-references/render-orchestration.md` documenting the procedure every Tier 1 command follows: build payload → consult render config → dispatch → open in Chrome → handle failure → terminal summary → lifecycle cleanup.
- First-run prompt: on first Tier 1 invocation after upgrade, the user picks `always`, `never`, or `ask` for HTML rendering. The choice is stored in `.job-scout/config.json` and can be changed via `/config render <mode>`.
- Markdown fallback: when HTML rendering or Chrome-open fails, the user is asked whether to show output as styled markdown in the conversation window.
- Schema migration 0.6 → 0.7: adds retention config keys and creates `.job-scout/reports/` and `.job-scout/reports/archive/`.
- `.superpowers/` is now gitignored.

### Changed

- Each of the six Tier 1 SKILL.md files gains a final "Render" step that calls into the shared orchestration. Their frontmatter is unchanged (per the project's convention that user-invocable slash commands do not carry `version:` frontmatter — verified by audit during Task 9 review).
- CLAUDE.md gains a new hard rule (#7): Tier 1 commands must dispatch `_visualizer` rather than rendering HTML inline.

### Out of scope (deferred to v0.8.0+)

- Tier 2 commands (`/analyze-cv`, `/cover-letter`, `/optimize-profile`).
- Dark mode.
- Cross-report comparison views.
- Print/PDF stylesheet polish.
- Embedded charts in `/funnel-report`.
- **Token-cost measurement** — formal `_visualizer` token-cost capture (planned Task 11) and the full 6-command end-to-end smoke (planned Task 19) were deferred from this release. The first-run prompt now reads "Adds modest token overhead per command" qualitatively; a measured range will replace it in a v0.7.1 patch once a real-world dispatch has been observed. First real use of v0.7.0 acts as the implicit smoke; any rendering issues fix in v0.7.1.

---

## [0.6.1] — 2026-04-17

Maintenance release. No user-invokable command changes.

### Changed

- **Internal skills now prefixed with `_`** — the 7 skills that are not user-invokable (4 capability engines: `cv-optimizer`, `profile-optimizer`, `job-matcher`, `recruiter-engagement`; 3 internal subagents: `company-researcher`, `cv-section-rewriter`, `cover-letter-writer`) are renamed to `_cv-optimizer`, `_profile-optimizer`, etc. The underscore follows the universal programming convention for "private/internal" and visually distinguishes them from the 12 user-invokable slash commands in the skills menu. All cross-references updated. Historical records (prior CHANGELOG entries, phase specs, phase plans) preserve old names as they documented what shipped at those versions.
- **Skill descriptions** for renamed skills gain an `[Internal — …]` or `[Internal subagent — …]` prefix naming the parent command or skill that loads/dispatches them.
- **`CLAUDE.md`** documents the naming convention as Hard rule #6 so future contributors follow it.
- **`.claude-plugin/plugin.json`** version bumped from 0.6.0 to 0.6.1.

### Migration notes

- **Non-breaking for end users.** All 12 user-invokable slash commands (`/analyze-cv`, `/cover-letter`, `/check-job-notifications`, etc.) keep their names and behaviour.
- **Non-breaking for plugin developers** unless they imported the renamed skills by name or path in custom extensions — in which case update to the new `_`-prefixed names.

---

## [0.6.0] — 2026-04-17

Phase 3 of the v0.4.0–v0.6.0 roadmap: new user-facing commands. Surfaces the infrastructure built in Phases 1 and 2 as four new slash commands plus two daily-workflow enhancements. All three roadmap phases are now complete; the plugin is feature-complete.

### Added

- **`/cover-letter <tracker-id|url>`** + **`cover-letter-writer`** subagent — generates 3 angle options (hiring-manager pitch, recruiter-gate, culture-match) per job. Each draft cites supporting documents from the index, places target keywords naturally, respects tone preference and voice continuity. Output saved to `.job-scout/cover-letters/`.
- **`/interview-prep <tracker-id>`** — interview-prep packet: top 5 SPAR narratives mapped to predicted questions, 10-15 predicted questions (technical / behavioural / situational), 5 specific questions to ask them, risk areas with proactive framing, optional company signals as conversation hooks. Output saved to `.job-scout/interview-prep/`.
- **`/funnel-report`** — pipeline analytics: 30/60/90-day funnel counts, conversion rates, week-over-week trends, top drop-off with prescriptive recommendation, top-10 trending corpus keywords, recruiter pipeline summary, 3 prioritised suggested next actions. Output saved to `.job-scout/reports/<date>-funnel.md`.
- **`/index-docs`** — explicit (re)scan of the supporting-docs index. Computes diff (new / re-indexed / missing / unchanged), presents to user, applies on approval. Also serves as the opt-back-in path after declining the bootstrap-time scan.

### Changed

- **`/check-job-notifications`** opens with a daily-driver context line (Step 0a): days since last run, tracker counts (seen / A-tier / applied), best-effort new-alerts count. First-run shows a setup line.
- **Bootstrap procedure** (`shared-references/workspace-layout.md`) gains a Step 5 nudge: after standard files are written, if 1+ likely supporting-doc files are detected at the workspace root, prompt the user to run `/index-docs` immediately. Decline persists per session.
- **README** commands table updated to list the 4 new commands.
- **`.claude-plugin/plugin.json`** version bumped from 0.5.0 to 0.6.0.

### Development process

Built using the same subagent-driven development methodology as v0.4.0 and v0.5.0: fresh implementer subagent per task, two-stage review (spec compliance + code quality), review-fix-re-review loops, auto-merge on dual approval. See v0.4.0 development process notes for the full methodology description.

---

## [0.5.0] — 2026-04-17

Phase 2 of the v0.4.0–v0.6.0 roadmap: SEO / ATS depth. Builds on the Phase 1 subagent protocol and state-layout foundations.

### Added

- **Learned JD keyword corpus** at `.job-scout/cache/jd-keyword-corpus.json` — every ingested JD enriches a persistent, frequency-weighted, seniority-tagged keyword model. Shared extraction procedure in `shared-references/jd-keyword-extraction.md`.
- **ATS scan simulator** (`cv-optimizer/references/ats-simulator.md`) — simulates Workday, Greenhouse, and Lever parsing. Scores each ATS 0-100 across parseability, section recognition, keyword match, contact extraction, and format compliance. Produces per-ATS score table + fix suggestions. Re-runs on optimized CV for before/after comparison.
- **Post-rewrite keyword-density check** — validates keyword density (1-3% target) after Phase 3 rewrite. Flags >3% as stuffing risk, <0.5% as undershoot.
- **Banner + Featured concrete templates** (`profile-optimizer/references/banner-featured-templates.md`) — 3 banner templates (keyword billboard, achievement spotlight, authority signal) + 5-slot Featured framework with supporting-docs-to-slot mapping.
- **Reverse-Boolean discoverability check** — for A-tier job matches, constructs the recruiter-side Boolean query and verifies the user's LinkedIn profile would surface. Reports match/miss with specific missing keywords.
- **Google snippet literal preview** — renders the actual Google search result (name + headline + first 160 chars of About) in current vs proposed form.
- **Recruiter lead-memory** — `threads.json` per-thread `notes` array persists facts across sessions (IR35 status, rate range, availability). Skill avoids re-asking resolved questions.

### Changed

- **`/match-jobs`, `/check-job-notifications`, `/job-search`** now extract keywords from every ingested JD into the learned corpus. Reverse-Boolean check appended to A-tier match cards in reports.
- **`cv-optimizer`** gains Phase 2a (ATS scan simulation) and post-rewrite density validation in the Phase 2 gap-analysis reference.
- **`profile-optimizer`** proposals now cite supporting documents. Step 6 consults the index; Step 9a renders the Google snippet preview.
- **`recruiter-engagement`** thread state expanded with lead-memory notes. `check-inbox` displays known facts in lead summaries.
- **`.claude-plugin/plugin.json`** version bumped from 0.4.0 to 0.5.0.

### Development process

Built using the same subagent-driven development methodology as v0.4.0: fresh implementer subagent per task, two-stage review (spec compliance + code quality), review-fix-re-review loops, auto-merge on dual approval. See v0.4.0 development process notes for the full methodology description.

---

## [0.4.0] — 2026-04-17

Phase 1 of the v0.4.0–v0.6.0 roadmap: token and agentic foundations. Prerequisite for every later phase.

### Added

- **`skills/shared-references/subagent-protocol.md`** — canonical I/O, budget, and fan-in contract for every skill that dispatches subagents.
- **`CLAUDE.md`** at repo root — goal, hard rules (browser policy, dedupe-before-extract, `.job-scout/` SSOT, `disable-model-invocation`, subagent protocol), file layout, versioning policy.
- **Repo `.gitignore`** — ensures `.job-scout/` (per-project state for users of the plugin) never ends up in the plugin repo itself.
- **`.job-scout/schema-version`** file + migration runner scaffolding in `workspace-layout.md`. No migrations ship in 0.4.0; the scaffolding unblocks Phase 2.
- **Tracker archival policy** — `status:seen` entries older than 60 days rotate to `.job-scout/archive/tracker-YYYY.json`. Hot tracker stays small; dedupe fall-through only reads the current-year archive.
- **`.job-scout/cache/supporting-docs.json`** + scan-on-bootstrap — workspace-root certificates, talks, decks, case studies, publications, and recommendations get indexed once and summarised. First consumer lands in Phase 2.
- **`skills/company-researcher/`** — new subagent skill returning a short structured digest (size, stage, reputation, red flags). Dispatched by `profile-optimizer` (optional, when a specific JD is provided).
- **`skills/cv-section-rewriter/`** — new subagent skill. Dispatched by `cv-optimizer` during Phase 3, one subagent per role block. Returns SPAR-optimized bullets.

### Changed

- **Score cache key** reconciled to `(job_id, cv_hash, profile_hash)` across `job-matcher/SKILL.md`, `match-jobs/SKILL.md`, `check-job-notifications/SKILL.md`, and `workspace-layout.md`. First run after upgrade invalidates `scores.json` once.
- **`profile-optimizer`** writes `profile_hash` to `user-profile.json` on any content-changing edit, so a profile rewrite invalidates stale scores downstream.
- **`profile-optimizer` LinkedIn snapshot cache** now delta-aware: per-section content hashes let the inner gate re-score only changed sections when the 7-day outer gate expires.
- **`cv-optimizer/SKILL.md`** split into a ≤5KB orchestrator + five lazy-loaded phase references (`phase-0-discovery-interview.md` through `phase-4-output-deliverables.md`). Phases load only when their gate fires.
- **`profile-optimizer/SKILL.md`** split into a ≤10KB orchestrator + eight `references/sections/*.md` files plus `activity-engagement.md` and `scoring-framework.md`. Section content loads only when that section is proposed or re-scored.
- **`/match-jobs` and `/check-job-notifications`** scoring paths fan out across subagents (batch size 5), following `subagent-protocol.md`. Falls back to sequential in-thread scoring when the `Agent` tool is unavailable.
- **`/check-job-notifications` Step 10 Top Picks sweep** paginates via one subagent per page (up to 5).
- **`.claude-plugin/plugin.json`** version bumped from 0.3.0 to 0.4.0.

### Migration notes

- First run after upgrade: the bootstrap procedure writes `.job-scout/schema-version` = `{ version: 1, upgraded_at: <ISO> }` if missing, and clears `.job-scout/cache/scores.json` once to account for the cache-key expansion. Subsequent runs use caches normally.
- No user action required.

### Development process

v0.4.0 was built using subagent-driven development with a two-stage review gate on every task:

- **16 tasks** planned in a serial implementation plan (`docs/superpowers/plans/2026-04-16-phase-1-token-agentic-foundations.md`), each shipping as an independent branch merged to `main` after dual approval.
- **Implementer subagent** per task — fresh context, no cross-task bleed. Each subagent received the full task spec, executed, committed, pushed, and self-reviewed.
- **Spec-compliance reviewer subagent** — independently verified each implementation against the plan's requirements. Caught spec deviations the implementer missed.
- **Code-quality reviewer subagent** — independently audited each task for internal consistency, contract compatibility, forward-reference clarity, and cross-file coherence. Found and escalated issues the spec reviewer's byte-match checks couldn't catch.
- **Review-fix-re-review loops** — when reviewers flagged issues (7 of 15 shipped tasks had findings), the implementer applied targeted fixes and reviewers re-verified before merge. No task merged with open issues.

Notable defects caught by reviewers during Phase 1:
- **Critical:** `budget_tokens` vs `budget_lines` naming mismatch between spec and reference (Task 4). Fixed by aligning the spec.
- **Important:** `profile_hash` incorrectly attributed to `cv-optimizer` in a subagent-initiated extra edit (Task 6). Fixed before merge.
- **Important:** `tracker-schema.md` named only `cv_hash` as re-score trigger, missing the newly-introduced `profile_hash` (Task 6). Fixed in the same PR.
- **Important:** `continuation_cursor` semantics underspecified in subagent protocol — no schema for follow-up dispatches (Task 4). Fixed with explicit schema block and idempotency extension.
- **Important:** LinkedIn snapshot JSON shape covered only 5 of 12 sections read by `optimize-profile`, and had no `score` field for cache reuse (Task 9). Expanded to 10 sections with score field.
- **Important:** Supporting-docs Purpose section contradicted Phase-1 scope on whether `profile-optimizer` reads the index in Phase 1 (Task 8). Fixed: Phase 2 consumer, not Phase 1.
- **Important:** `skipped` job status had undefined archival fate in tracker schema (Task 7). Resolved: protected alongside `rejected`.
- **Pre-existing:** duplicate `## Step 4` heading in `match-jobs/SKILL.md` discovered during Task 6 review and fixed.

1 task (`.claude/settings.local.json` trim) was closed as N/A after the implementer discovered the file is globally gitignored, never tracked in this repo, and auto-regrows via the Claude Code harness.

This process is documented so Phase 2 and 3 can follow the same methodology. The design spec, implementation plan, and roadmap all live in `docs/` for cold-start resumability.

---

## [0.3.0] — 2026-04-08

Major refactor focused on persistent per-project state, token efficiency, and migrating to the modern plugin format.

### Added

- **Per-project `.job-scout/` workspace.** Every command now bootstraps a hidden, per-project state folder on first invocation (with user consent), containing `user-profile.json`, `tracker.json`, `reports/`, `cache/`, and `recruiters/`. Different projects get cleanly separated state, so a freelance-search workspace and a permanent-role workspace never mix.
- **`shared-references/workspace-layout.md`** — canonical folder layout plus the bootstrap procedure every command runs.
- **`shared-references/tracker-schema.md`** — single authoritative schema for `tracker.json`, documenting the dedupe-before-extract pattern.
- **Content-hash CV caching** in `cv-optimizer` / `/analyze-cv`: parsed CVs and full analysis outputs are cached by content hash. Re-analyzing an unchanged CV returns instantly and skips the Phase 0 discovery interview when `discovery_complete` is already set.
- **Score caching contract** in `job-matcher`: scores are cached by `(job_id, cv_hash)` in `.job-scout/cache/scores.json`. Unchanged jobs scored against an unchanged CV are never re-scored.
- **LinkedIn profile snapshot cache** in `profile-optimizer`: last-seen profile stored in `.job-scout/cache/linkedin-profile.json` and reused for up to 7 days, with only changed sections re-evaluated on subsequent runs.
- **Per-thread recruiter state** in `recruiter-engagement`: `.job-scout/recruiters/threads.json` records `last_seen_msg_id` per thread so unchanged conversations are skipped on subsequent `/check-inbox` runs.
- **"Top job picks for you" sweep** as Step 10 of `/check-job-notifications`: after the notifications report is saved, the command now asks whether to continue analyzing LinkedIn's recommendations feed. It paginates and dedupes against the tracker, only extracting never-before-seen listings.
- **CHANGELOG.md** (this file).
- **`shared-references/browser-policy.md`** — explicit, hard rule that the plugin uses the Claude Chrome extension exclusively for all browser work. Computer use is forbidden. Every browser-touching command now opens with a "Browser policy" section pointing at this file, so the model never escalates a "navigate to LinkedIn" instruction into a computer-use request. README now carries a transparency callout telling users that any computer-use prompt during plugin execution is a bug, not expected behavior.

### Changed

- **Migrated from legacy `commands/` layout to `skills/<name>/SKILL.md`.** Each of the 8 slash commands moved into its own skill directory with modern frontmatter. Silences the "uses the legacy commands/ format" install warning. All 8 commands have `disable-model-invocation: true`, preserving slash-only invocation — the model will never auto-fire browser automation, applications, or recruiter replies.
- **Dedupe-before-extract.** `/check-job-notifications`, `/match-jobs`, and `/job-search` now collect job IDs first and filter against `tracker.json` *before* opening any listing. Previously these commands extracted every job fully and then deduped, paying the full extraction cost for every already-known job. This is the single biggest token-saving change in the release.
- **`shared-references/cv-loading.md`** updated to hash CVs, reuse cached parses, and always operate out of `.job-scout/` rather than loose workspace-root files.
- **Report presentation:** B/C-tier jobs now render as compact rows instead of paragraph rationales — full prose is reserved for A-tier matches.
- **SKILL.md files** for `cv-optimizer`, `job-matcher`, `profile-optimizer`, and `recruiter-engagement` now document their caching contracts and point at the new shared references.
- **`.claude-plugin/plugin.json`** version bumped from 0.2.0 to 0.3.0.

### Migration notes

- On first run in an existing project, the plugin auto-detects legacy `user-profile.json` or `job-reports/` at the workspace root and offers a one-time migration into `.job-scout/`.
- No action required for fresh installs — the bootstrap prompt handles first-time setup.
- If you want `.job-scout/` to stay out of source control, add it to your project's `.gitignore`.

---

## [0.2.0] — Earlier releases

Historical releases preceding the 0.3.0 refactor. These evolved the plugin from the initial MCP prototype into the LinkedIn Job Hunter form:

- CV optimizer with SPAR method, seven-dimension scoring, and persuasion-psychology rewrites.
- Profile optimizer that consumes the CV to drive section proposals and Boolean search simulation.
- Job matcher with freelance/contract adjustments and rate normalization.
- Recruiter engagement skill with lead qualification and response templates.
- `/check-job-notifications` daily driver command.
- Initial loose `job-reports/tracker.json` and workspace-root `user-profile.json` (superseded by `.job-scout/` in 0.3.0).
- Legacy `commands/*.md` layout (migrated to `skills/*/SKILL.md` in 0.3.0).

## [0.1.0] — Initial release

Initial release of the LinkedIn Job Hunter plugin for Claude Cowork. Basic CV and LinkedIn tools, early command set.

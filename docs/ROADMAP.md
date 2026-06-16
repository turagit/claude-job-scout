# linkedin-job-hunter — Roadmap

Single source of truth for what this plugin is for, which phase we're in, and what's next. If you (human or agent) are resuming cold, read this first.

## Vision

> Automate the end-to-end LinkedIn job-seeking pipeline (CV → profile → search → apply → recruiter) inside the user's own logged-in browser via the Claude Chrome extension, with per-project state, aggressive caching, and subagent-parallelism for scorable units of work.

## How to read this doc

- Each phase ships as a semver minor release (`v0.4.0`, `v0.5.0`, `v0.6.0`).
- Phase 1 has a committed design spec at `docs/superpowers/specs/`. Phases 2 and 3 get their specs when Phase 1 is shipped.
- Implementation plans live at `docs/superpowers/plans/` (populated just before execution by the `writing-plans` skill).
- Checkboxes are the resume trail — tick them as items land on `main`.

## Status at a glance

| Phase | Target | Status | Spec | Plan |
|-------|--------|--------|------|------|
| **1. Token + Agentic foundations** | v0.4.0 | Shipped — v0.4.0 | [`specs/2026-04-16-phase-1-token-agentic-foundations-design.md`](superpowers/specs/2026-04-16-phase-1-token-agentic-foundations-design.md) | _pending_ |
| 2. SEO / ATS depth | v0.5.0 | Shipped — v0.5.0 | [`specs/2026-04-17-phase-2-seo-ats-depth-design.md`](superpowers/specs/2026-04-17-phase-2-seo-ats-depth-design.md) | [`plans/2026-04-17-phase-2-seo-ats-depth.md`](superpowers/plans/2026-04-17-phase-2-seo-ats-depth.md) |
| 3. New user-facing commands | v0.6.0 | Shipped — v0.6.0 | [`specs/2026-04-17-phase-3-user-facing-commands-design.md`](superpowers/specs/2026-04-17-phase-3-user-facing-commands-design.md) | [`plans/2026-04-17-phase-3-user-facing-commands.md`](superpowers/plans/2026-04-17-phase-3-user-facing-commands.md) |
| 4. Visual render layer | v0.7.0 | Shipped — v0.7.0 (smoke deferred) | [`specs/2026-04-29-visual-render-layer-design.md`](superpowers/specs/2026-04-29-visual-render-layer-design.md) | [`plans/2026-04-29-visual-render-layer.md`](superpowers/plans/2026-04-29-visual-render-layer.md) |
| 5. Foundations + Accuracy core | v0.8.0 | Shipped — v0.8.0 (smoke deferred to real use) | [`specs/2026-05-26-phase-0-1-foundations-and-accuracy-design.md`](superpowers/specs/2026-05-26-phase-0-1-foundations-and-accuracy-design.md) | [`plans/2026-05-26-phase-0-1-foundations-and-accuracy.md`](superpowers/plans/2026-05-26-phase-0-1-foundations-and-accuracy.md) |
| **6. Deep LinkedIn coverage** | v0.9.0 | Shipped — v0.9.0 | [`specs/2026-05-26-phase-6-deep-coverage-design.md`](superpowers/specs/2026-05-26-phase-6-deep-coverage-design.md) | _inline (no separate plan file — work fit in one branch)_ |
| **7. Discovery & search engine** | v0.10.0 | Shipped — v0.10.0 | [`specs/2026-06-10-phase-7-discovery-search-engine-design.md`](superpowers/specs/2026-06-10-phase-7-discovery-search-engine-design.md) | _inline (executed task-by-task on `phase-7-9/build`)_ |
| **11. Ultramode — multi-source discovery & sweep** | v0.11.0 | Shipped — v0.11.0 (smoke deferred to first real use) | [`specs/2026-06-15-phase-11-ultramode-multi-source-design.md`](superpowers/specs/2026-06-15-phase-11-ultramode-multi-source-design.md) | [`plans/2026-06-15-phase-11-ultramode-multi-source.md`](superpowers/plans/2026-06-15-phase-11-ultramode-multi-source.md) |
| **12. Discovery & categorisation foundations (Phase A)** | v0.12.0 | Shipped — v0.12.0 (smoke deferred to first real use) | [`specs/2026-06-16-phase-12-discovery-categorisation-foundations-design.md`](superpowers/specs/2026-06-16-phase-12-discovery-categorisation-foundations-design.md) | [`plans/2026-06-16-phase-12-discovery-categorisation-foundations.md`](superpowers/plans/2026-06-16-phase-12-discovery-categorisation-foundations.md) |

**Current focus:** Nine phases shipped. Plugin at v0.12.0 — Phase 12 (Discovery & categorisation foundations — "Phase A") widens recall with a CV-derived capability graph + a conservative jargon/alias map feeding a new `capability` query family across `/job-search`, `/deep-sweep`, and ultramode (recall-only, capped, query-stats-governed), and sharpens categorisation with a parallel competitiveness signal plus deterministic confidence/explanation-tag badges and a within-tier confidence sort. All additive: the v1 tier rubric and the score cache are untouched (no `rubric_version` bump, no migration). The previously-queued phases remain: Phase 8 (triage feedback UX + reject chips), 9 (recruiter rebuild + tone elicitation `/config tone`), 10 (nurture commands) follow when ready. Note: tone-block *propagation* into all drafting contracts already landed in v0.10.0; what remains of the old "Phase 8" is the recruiter lifecycle rebuild and the `/config tone` elicitation surface. **Current priority:** Phase 12 is now **shipped as v0.12.0** (interactive smoke deferred to first real use, per the Phase 4/5/11 precedent). Deferred Phases 8–10 (triage feedback UX, recruiter rebuild + `/config tone`, nurture commands) follow by user need; Phases B and C of the discovery+categorisation track are later still. No phase is mid-flight.

---

## Phase 1 — v0.4.0: Token + Agentic foundations

Prerequisite for every later phase. Nothing in Phase 2 or 3 can ship cleanly without the subagent protocol, the progressive-disclosure split, and the cache-key reconciliation landing first.

- [x] **`shared-references/subagent-protocol.md`** — canonical contract for every subagent-spawning skill (I/O shape, token budget, allowed tools, delta-return rule, fan-in merge).
- [x] **CLAUDE.md at repo root** — goal, hard rules (browser policy, dedupe-before-extract, `.job-scout/` SSOT, `disable-model-invocation`, subagent protocol).
- [x] **Repo `.gitignore`** — `.job-scout/`, `.DS_Store`, common editor dirs.
- [x] **`.claude/settings.local.json` trim** — *closed as N/A.* File is excluded by the user's global gitignore (`**/.claude/settings.local.json`), has never been tracked in this repo, and auto-regrows via the Claude Code harness on every permission prompt. "Trimming" it has no persistent effect, so committing a trimmed version is impossible and pointless. Kept in the Phase 1 list for audit trail; no PR shipped for this item.
- [x] **Progressive disclosure split of `cv-optimizer/SKILL.md`** — ~14KB → ≤3KB orchestrator + lazy-loaded phase files.
- [x] **Progressive disclosure split of `profile-optimizer/SKILL.md`** — ~13KB → ≤3KB orchestrator + lazy-loaded section files.
- [x] **Score-cache key reconciliation** — `(job_id, cv_hash, profile_hash)` everywhere. Write `profile_hash` from `profile-optimizer`.
- [x] **`.job-scout/schema-version`** — file + empty migration runner skeleton.
- [x] **Tracker archival** — `status:seen` + `last_seen > 60d` rotates to `.job-scout/archive/tracker-YYYY.json`.
- [x] **Delta-aware LinkedIn snapshot** — per-section hashes in `.job-scout/cache/linkedin-profile.json`; only changed sections re-score.
- [x] **Supporting-docs index** — `.job-scout/cache/supporting-docs.json` auto-built on bootstrap; `/index-docs` surface command deferred to Phase 3.
- [x] **Parallel job scoring** — `/match-jobs` and `/check-job-notifications` fan out scoring subagents (~5 jobs per subagent).
- [x] **Parallel Top Picks pagination** — 1 subagent per page during Step 10 sweep.
- [x] **`company-researcher` subagent** — digest-only return (size/stage/rep/red-flags, ≤3 lines).
- [x] **`cv-section-rewriter` subagent** — one per role during Phase 3 CV rewrite.

## Phase 2 — v0.5.0: SEO / ATS depth

Builds on the Phase 1 subagent protocol and state-layout foundations.

- [x] **Learned JD keyword corpus** at `.job-scout/cache/jd-keyword-corpus.json` (extraction reference shipped; wiring in Task 2)
- [x] **Wire corpus extraction** into `/match-jobs`, `/check-job-notifications`, `/job-search`
- [x] **ATS scan simulator** (Workday / Greenhouse / Lever behaviour)
- [x] **Post-rewrite keyword-density check** (>3% = stuffing, <0.5% = undershoot)
- [x] **Banner + Featured concrete templates**
- [x] **Supporting-doc-backed claims** in CV + Featured section
- [x] **Reverse-Boolean discoverability check** per A-tier job
- [x] **Google snippet literal preview**
- [x] **Recruiter lead-memory** in `threads.json`

## Phase 3 — v0.6.0: New user-facing commands

Each command surfaces capabilities built in Phases 1–2. Spec to be written after Phase 2 ships.

- [x] **`/index-docs`** (explicit re-scan over Phase 1 supporting-docs cache)
- [x] **Bootstrap nudge** to index supporting docs on first run
- [x] **Daily-driver context line** in `/check-job-notifications`
- [x] **`/cover-letter <tracker-id|url>`** + `cover-letter-writer` subagent
- [x] **`/interview-prep <tracker-id>`**
- [x] **`/funnel-report`**

## Phase 4 — v0.7.0: Visual render layer

Adds a beautified HTML report layer for the six Tier 1 user-facing commands. Reports render via the `_visualizer` subagent (Modern Cards aesthetic, light JS interactivity), auto-open in Chrome via the existing extension, and fall back to styled markdown when HTML rendering or browser-open fails.

- [x] **Task 1: `_visualizer` skill skeleton + reference files**
- [x] **Task 2: theme.css asset**
- [x] **Task 3: interactive.js asset**
- [x] **Task 4: base.html.j2 + base.md.j2 frame templates**
- [x] **Task 5: `_visualizer/SKILL.md` full subagent contract**
- [x] **Task 6: `match-jobs` HTML + markdown templates**
- [x] **Task 7: `render-orchestration.md` shared reference**
- [x] **Task 8: Schema migration 0.6 → 0.7**
- [x] **Task 9: `/config` slash command**
- [x] **Task 10: Wire `/match-jobs` to render orchestration**
- [~] **Task 11: End-to-end smoke + token measurement** *(deferred — see v0.7.1 plan)*
- [x] **Task 12: Wire `/job-search`**
- [x] **Task 13: Wire `/check-job-notifications`**
- [x] **Task 14: Wire `/check-inbox`**
- [x] **Task 15: Wire `/funnel-report`**
- [x] **Task 16: Wire `/interview-prep`**
- [x] **Task 17: CLAUDE.md hard rule + `.gitignore` update**
- [x] **Task 18: Release prep — versioning, ROADMAP, CHANGELOG, README**
- [~] **Task 19: Final 6-command end-to-end smoke** *(deferred — first real-world use is the smoke; issues fix in v0.7.1)*

---

## Phase 5 — v0.8.0: Foundations + Accuracy core

Closes the spec↔reality gap (statuses, tiers, JD blobs, caches all silently broken in v0.7.0) and replaces the keyword-bingo rubric with a hard-gated, segment-aware, per-dimension matcher.

- [x] **Task 1: Design spec** (`docs/superpowers/specs/2026-05-26-...`)
- [x] **Task 2: Canonical schemas reference** (`shared-references/canonical-schemas.md`)
- [x] **Task 3: State validators reference** (`shared-references/state-validators.md`)
- [x] **Task 4: JD storage reference** (`shared-references/jd-storage.md`)
- [x] **Task 5: Update `workspace-layout.md`** — jds/, .backup/, v2→v3 migration
- [x] **Task 6: Old schema docs point at canonical** (`tracker-schema.md`, `_job-matcher/references/user-profile-schema.md`)
- [x] **Task 7: Voice profile reference** (`shared-references/voice-profile.md`)
- [x] **Task 8: Live state backup** — both workspaces tarball'd to `.backup/`
- [x] **Task 9: Migrate `tracker.json`** — both workspaces, in place. Workspace A 502→500 (2 corrupt dropped); workspace B 268 preserved. All entries canonical + `rubric_version: legacy`
- [x] **Task 10: Migrate `user-profile.json`** — segment, tone, unified requirements
- [x] **Task 11: Migrate `threads.json`** — one workspace normalised (26 threads); the other initialised
- [x] **Task 12: Wire JD persistence** in `check-job-notifications`, `job-search`, `match-jobs`
- [x] **Task 13: Score-cache contract** — `rubric_version` added to key
- [x] **Task 14: CV parse cache contract** strengthened in `cv-loading.md`
- [x] **Task 15: Archive pass scaffolding** (`shared-references/archive-pass.md`)
- [x] **Task 16: Tone block populated** — both workspaces from voice spec
- [x] **Task 17: Plugin version → 0.8.0-dev + CHANGELOG entry**
- [~] **Task 18: End-to-end Phase 0 verification** *(deferred — merged with Task 26 smoke; state already verified via `jq` validators)*
- [x] **Task 19: `_gate-engine` skill** (skeleton + `gate-rules.md` reference)
- [x] **Task 20: `/analyze-cv` discovery interview** — segment + 7-category dealbreaker checklist + free-text + tone confirmation (Step 3a)
- [x] **Task 21: Universal dimensions reference** (`dimensions-default.md` — abstract A/B/C/D criteria, no hardcoded industries or tools). Replaces an initial mid-release draft of two segment-specific dimension files that encoded specifics from the workspaces used during development; correctly flagged as plugin-vs-user-data leakage and removed.
- [x] **Task 22: Per-workspace dimensions discovery** — `/analyze-cv` Step 3c generates the rubric for each workspace from the user's CV + target_titles + segment + requirements; `_job-matcher` reads from `user-profile.json.dimensions[]`.
- [x] **Task 23: `_job-matcher` v0.2.0 rewrite** — segment-aware, gated, dimension-based
- [x] **Task 24: Wire `_gate-engine`** into `/match-jobs` and `/check-job-notifications`
- [x] **Task 25: Visualizer dimension breakdown + gated banner** — SKILL.md schema, component-library, match-jobs HTML + Markdown templates
- [~] **Task 26: End-to-end smoke** *(deferred — real-world use serves as the smoke; any issues fix in v0.8.1; same pattern as Phase 4's deferred smoke)*
- [x] **Task 27: ROADMAP — Phase 5 section added**
- [x] **Task 28: Release v0.8.0** — version bumped to 0.8.0, CHANGELOG dated 2026-05-26, ROADMAP ticks, tag

---

## Phase 7 — v0.10.0: Discovery & search engine

User-directed priority: *"focus on job discovery on LinkedIn, improved search on LinkedIn — these are the paths to increase the probability of finding jobs."* Plus a standing side requirement: British tone, no Americanisms.

- [x] **`shared-references/linkedin-search.md`** — URL grammar, Boolean craft, query plan v2, query-stats, repost dedupe, freshness.
- [x] **`/job-search` rewrite** — title-cluster + skill + geo + synonym plan, filter-addressed URLs, stats writes.
- [x] **`/deep-sweep` adoption** — same plan at deep settings (Past Week, pages 1-3).
- [x] **`/analyze-cv` Step 3d** — query-cluster discovery; `query_clusters[]` added to canonical schema (optional, additive).
- [x] **Query learning loop** — `.job-scout/cache/query-stats.json`; ordering, retirement, promotion.
- [x] **Repost fingerprint dedupe** — all sweep commands.
- [x] **Freshness flag** — tier-then-recency ordering + "⚡ apply early" chip in all sweep views.
- [x] **`/create-alerts` auto-derivation** — zero-arg proposes alerts from the plan; `manual` keeps the old flow.
- [x] **Contract repairs** — Default-Requirements block removed; legacy score contract folded into v1 fan-out; aggregate-score ghosts retired (payloads, render-orchestration, `_job-matcher` cache); `jd_path` reads in `/cover-letter` + `/interview-prep`; canonical `lead_tier`; tone block replaces `tone_preference`; funnel-report scored-stage fix; orphaned `matching-weights.md` removed.
- [x] **Template parity (v0.9.1 debt)** — dimension tables + gated groups + source chips in match-jobs / job-search / check-job-notifications HTML + markdown; Jinja2-verified (16/16 render combinations); fixed latent `//` coalesce crash in `deep-sweep.md.j2`.
- [x] **British-English pass** — CLAUDE.md hard rule, voice-profile avoid-list, full prose sweep, response-templates voice preamble.
- [x] **Release v0.10.0** — version bump, CHANGELOG, README, this section.

## Phase 11 — v0.11.0: Ultramode — multi-source discovery & sweep

Opt-in sourcing beyond LinkedIn. LinkedIn is one market surface; ultramode widens sourcing into a per-workspace, CV-derived, **verified** set of external sources and folds every job into the *same* tracker, scoring, and render pipeline. Off by default; the LinkedIn core ships unchanged.

- [x] **Access lane + browser-policy carve-out** — `WebFetch` is a read-only public HTTP GET, not browser automation; Hard Rule #1 still governs all in-browser work and the Chrome extension stays the only mechanism that touches the logged-in session. Universal aggregator backbone shipped in `shared-references/ultramode-sources.md`.
- [x] **Verified discovery engine (`_source-discovery`)** — fan-out along independent axes, live-probe + adversarial verification, loop-til-dry; writes `.job-scout/sources.json`. Nothing enters the registry on the model's word alone.
- [x] **First-run onboarding + `/ultramode` command + `/config` toggle** — `base_country` elicited explicitly and always confirmed out loud (never inferred); `/ultramode` (sweep · `sources` · `onboarding`), `disable-model-invocation: true`; `ultramode.default` widens `/job-search` & `/deep-sweep` when set.
- [x] **Per-source sweep (`_source-sweep`)** — dedupe-before-extract, client-side full-text filter (server-side feed filters proved unreliable), ATS company watchlist auto-seeded from A/B-tier employers + `requirements.companies_to_target[]`.
- [x] **Schema: structured `source`, namespaced IDs, profile additions** — `source: {lane, provider, board}` with a back-compat shim for the legacy string enum (tracker `schema_version` v2 → v3); external IDs namespaced `<provider>__<board>__<externalid>`; `requirements.base_country`, `requirements.target_geography`, and the additive `ultramode` block.
- [x] **Adaptive priority + cross-source dedupe + direct-to-employer canonical** — source order derived from `requirements`; the existing repost fingerprint dedupes across sources; canonical "apply here" is direct-to-employer first (ATS > LinkedIn > aggregator > marketplace) with "also seen on N."
- [x] **Results view** — one unified, source-agnostic, tier-ranked report (A→B→C, freshest-first) through `_visualizer` (reused as-is): source chip, "also seen on N," apply-at-source CTA.
- [x] **Keyless-first / keyed opt-in** — works with zero keys; keyed aggregators prompt inline with the signup link and skip gracefully if declined; keys live in gitignored `config.json` → `ultramode.api_keys`, never entered into a browser form.
- [x] **Release v0.11.0** — version bump, CHANGELOG, README ultramode section, this section.

## Phase 12 — v0.12.0: Discovery & categorisation foundations ("Phase A")

Unearth the roles the candidate is a *great* match for. Closes two leaks: **"right job, wrong words"** recall (great-fit roles written in different vocabulary that lexical Boolean queries miss) and **flat A/B/C ranking** (no signal for where the candidate is a genuine standout, nor how confident each match is). Widens recall via a CV-derived capability graph + jargon/alias map feeding the *existing* query plan; sharpens categorisation with a parallel competitiveness signal + deterministic confidence/explanation tags. All additive — the v1 tier rubric, the score cache, and dedupe-before-extract are untouched. No `rubric_version` bump, no migration.

- [x] **Capability-graph build + propose/approve step + cache** — new `/analyze-cv` discovery step (between dimensions and clusters) derives `{stated, latent, adjacent}` capabilities in one LLM pass, presented for approval/trim, cached to `.job-scout/cache/capability-graph.json` (keyed by `cv_hash`). Existing workspaces auto-build on the first discovery run with a one-time review prompt.
- [x] **Jargon/alias recall layer** — `.job-scout/cache/jargon-normalizer.json` (persistent), conservative human-reviewed seed of high-confidence title/skill synonyms, grown from the `jd-keyword-corpus` + first-encounter LLM expansion.
- [x] **`capability` query family + cap + query-stats integration** — feeds `/job-search`, `/deep-sweep`, and ultramode; recall-only (query-expansion, no pre-scoring filter — gate engine + rubric stay the only droppers), capped ~2–3/run, governed by the existing retire/promote lifecycle (`query-stats` `family` gains `capability`).
- [x] **Competitiveness axis (A/B only) + deterministic confidence/tag derivation + persist** — `_job-matcher` emits `competitiveness` (high/med/low + one evidence quote) for A/B-tier jobs only; `confidence` + `match_explanation_tag` are deterministic derivations from the per-dimension tiers. `dimensions[]` gains an optional `type` (`load-bearing`/`modifying`, additive, default load-bearing) feeding those derivations. `_gate-engine` confirmed untouched. Tracker entries + score-cache value object gain four additive optional fields, populated lazily; score-cache key unchanged (`…:v1`).
- [x] **Render: competitiveness/confidence/tag badges + within-tier confidence sort** — `_visualizer` adds the three badges to Tier 1 job cards and sorts within each tier by confidence (high→med→low) then recency. Per Hard Rule #8; British English.
- [x] **Release v0.12.0** — version bump, CHANGELOG, README "Sharper matching & wider recall" section, this section.

## Log

- **2026-04-16** — Roadmap established. Phase 1 design spec drafted and committed. Meta-decision: phased releases (v0.4.0 → v0.5.0 → v0.6.0), not single-bundle v0.4.0.
- **2026-04-17** — Phase 1 shipped as v0.4.0. Phase 2 (SEO / ATS depth) entering design.
- **2026-04-17** — Phase 2 shipped as v0.5.0. Phase 3 (new user-facing commands) entering design.
- **2026-04-17** — Phase 3 shipped as v0.6.0. All three phases complete; plugin is feature-complete per the v0.4.0–v0.6.0 roadmap. Future phases gated on user need.
- **2026-04-17** — v0.6.1 maintenance release. Renamed 7 internal skills with `_` prefix for menu clarity.
- **2026-04-29** — Phase 4 (visual render layer) entering execution. Spec + plan committed; v0.7.0 target.
- **2026-04-29** — Phase 4 implementation shipped as v0.7.0. 17 of 19 tasks landed via subagent-driven execution with two-stage review per task. Tasks 11 (token measurement) and 19 (final 6-command smoke) deferred — first real-world use serves as the smoke; measurement + any fixes ship in a v0.7.1 patch.
- **2026-05-26** — Phase 5 (Foundations + Accuracy core) entering execution. Origin: /grill-me session uncovered massive spec↔reality drift (different tracker schemas across workspaces, seven non-canonical statuses, eight non-canonical tiers, zero JD blobs persisted, empty score and CV caches, ~26% untiered jobs, zero rejections ever logged) and a structurally broken matcher (keyword-bingo Skills, no hard gates, single-number score). Decisions locked: migrate-in-place; canonical schemas with writer-side enum validation; segment-aware dimension sets; hard-gate engine; per-dimension breakdown with evidence quotes (no aggregate number); structured voice block applied across all user-voiced surfaces.
- **2026-05-26** — Phase 5 execution: 25 of 28 tasks landed. Both live workspaces migrated to v2 schemas + v3 workspace layout. Tasks 18 and 26 (interactive smoke) merged into a single user-run verification; Task 28 (release) gates on that smoke passing.
- **2026-05-26** — Mid-execution correction. User correctly flagged that two initial segment-specific dimension reference files had encoded industries and tools from the workspaces used during development, and a binary segment enum — making the plugin user-shaped rather than user-agnostic. Refactored: dimensions are now per-workspace data (`user-profile.json.dimensions[]`) discovered by `/analyze-cv`; the plugin ships a single universal abstract bootstrap (`dimensions-default.md`); `segment` is free-text; the two segment-specific reference files were removed. Pre-existing user-specific examples were also stripped from `state-validators.md`, `voice-profile.md`, the gate-rules seniority section, and the `_visualizer` component-library samples. Any job-search lane is now first-class — baker, construction engineer, sales executive, anyone.
- **2026-05-26** — Phase 6 shipped as v0.9.0. Adaptive multi-query fanout in `/job-search` (zero-arg iterates target_titles[] + synonym expansion on thin queries), four new source surfaces in `/check-job-notifications` (Top picks, Saved jobs, Similar-jobs from A-tier hits, recruiter-message links via `/check-inbox` Step 1b), and a new `/deep-sweep` weekly command. Inline execution; no separate implementation plan committed — work fit in one branch. HTML-template parity for the v0.8.0 dimension breakdown across non-deep-sweep templates is the only deferred item, queued as v0.9.1.
- **2026-06-10** — Phase 7 shipped as v0.10.0. Full autonomous review of all 22 skills, then a user-directed pivot to discovery: every LinkedIn search is now a crafted Boolean, filter-addressed, learning query (`linkedin-search.md`); skill-combination queries catch retitled roles from the JD-keyword corpus; reposts dedupe by fingerprint; alerts derive from the plan. Contract drift repaired (aggregate-score ghosts, dead `description` reads, non-canonical `lead_tier`, `tone_preference` → `tone` block). v0.9.1 template-parity debt cleared with Jinja2-verified renders (which caught a latent `//` coalesce crash in `deep-sweep.md.j2`). British English is now the default register everywhere user-facing (CLAUDE.md hard rule). Old Phases 7-9 renumber to 8-10: triage feedback UX, recruiter lifecycle rebuild + `/config tone`, nurture commands.
- **2026-06-15** — Phase 11 (Ultramode — multi-source discovery & sweep) entering design. Origin: /grill-me session on sourcing beyond LinkedIn. Decisions locked: opt-in `/ultramode` command + off-by-default config toggle (LinkedIn core unchanged); read-only `WebFetch` lane beside the Chrome-extension lane (browser-policy carve-out); a *generic* engine with a per-workspace, CV-derived, **verified** source registry (`sources.json`) built by exhaustive fan-out + live-probe + loop-til-dry; first-run onboarding elicits `base_country` explicitly (never inferred) + target geography/arrangement/contract/field, reusing the CV keyword corpus; adaptive source priority from `requirements`; six universal source categories × four access lanes; cross-source dedupe with direct-to-employer canonical; keyless-first, keyed-aggregator opt-in; one unified, source-agnostic, tier-ranked report (A→B→C, freshest-first) with a direct link per role, reusing `_job-matcher`/`_gate-engine`/`_visualizer` unchanged. Design validated live before drafting: verified discovery produced **174 sources** for a real lane (NL · EU-remote · freelance · SRE/Platform), and the unified report was rendered end-to-end from **39 live roles** across three keyless sources. Key findings folded in: HTML is the dominant access reality (~68%, extension lane is load-bearing), free-feed server-side filters are unreliable (filter client-side over full text), ATS needs an auto-seeded company watchlist. Schema impact additive: structured `source: {lane,provider,board}` (back-compat shim), namespaced external IDs, new `sources.json`, profile `base_country`/`ultramode` block. Targets v0.11.0; slots ahead of deferred Phases 8–10 by user priority.
- **2026-06-15** — Phase 11 shipped as v0.11.0. Opt-in ultramode lands: a new `/ultramode` command (sweep · `sources` · `onboarding`, `disable-model-invocation: true`), the `_source-discovery` engine that builds a verified per-workspace `sources.json` by fan-out + live-probe + loop-til-dry (`base_country` elicited explicitly, never inferred), and the `_source-sweep` subagent doing per-source dedupe-before-extract with a client-side full-text filter and an auto-seeded ATS watchlist. Results fold into the existing tracker/scoring/render pipeline as one unified, source-agnostic, tier-ranked report (A→B→C, freshest-first) with a direct apply-at-source link per role and "also seen on N" — `_job-matcher`/`_gate-engine`/`_visualizer` reused untouched. The `ultramode.default` `/config` toggle widens `/job-search` & `/deep-sweep` when set; default off keeps the LinkedIn core unchanged. Schema additive: structured `source: {lane,provider,board}` with a back-compat shim (tracker v2 → v3), namespaced external IDs, profile `base_country`/`target_geography`/`ultramode` block; `WebFetch` carve-out in `browser-policy.md` (read-only HTTP GET, not browser automation — the Chrome extension stays the only in-session mechanism). Keyless-first, keyed-aggregator opt-in. Interactive smoke deferred to first real use, per the Phase 4/5 precedent; the design was already validated live (174 verified sources for a real lane; the unified report rendered end-to-end from 39 live roles). Deferred Phases 8–10 (triage feedback UX, recruiter rebuild + `/config tone`, nurture commands) follow when ready.
- **2026-06-16** — Phase 12 (Discovery & categorisation foundations — "Phase A") entering design; **parked after spec** (no plan/build yet). Origin: post-v0.11.0 improvement analysis + `/grill-me`. Goal: unearth the roles the candidate is a *great* match for ("right job, wrong words" recall + standout-ranking). Decisions locked: (1) a CV-derived **capability graph** (proposed + approved in `/analyze-cv`, cached by `cv_hash`) plus a conservative **jargon/alias map** feed a new **`capability` query family** into the plan across `/job-search`, `/deep-sweep`, and ultramode — **query-expansion only** (no pre-scoring filter; the gate engine + rubric stay the only droppers), capped ~2–3/run and governed by the existing query-stats retire/promote loop (winners graduate into clusters); (2) **competitiveness is a parallel signal, not a 6th dimension** — the v1 tier rubric and the score-cache key are untouched (no `rubric_version` bump, no re-score); the matcher emits `competitiveness` (high/med/low) for A/B-tier jobs only, while `confidence` + a `match_explanation_tag` are deterministic derivations from the dimension tiers; (3) the report gains competitiveness/confidence badges + within-tier confidence sort. Additive schema (two new caches; additive tracker/score-cache fields), no migration. Spec: [`specs/2026-06-16-phase-12-discovery-categorisation-foundations-design.md`](superpowers/specs/2026-06-16-phase-12-discovery-categorisation-foundations-design.md). Phases B (faceted opportunity-map / maturity bands / job-gettability) and C (reject-reason re-weighting / approved-job corpus boost / source-quality) are later. Targets v0.12.0; not yet scheduled.
- **2026-06-16** — Phase 12 shipped as v0.12.0. The recall layer lands: a CV-derived **capability graph** (proposed + approved in `/analyze-cv`, cached by `cv_hash`, auto-built for existing workspaces on first discovery run) plus a conservative, corpus-fed **jargon/alias map** feed a new **`capability` query family** into the plan across `/job-search`, `/deep-sweep`, and ultramode — recall-only (query-expansion, no pre-scoring filter; the gate engine + rubric stay the only droppers), capped ~2–3/run, governed by the existing query-stats retire/promote loop (winners graduate into clusters). Categorisation sharpens: `_job-matcher` emits **competitiveness** (high/med/low + one evidence quote) for A/B-tier jobs only — a *parallel* signal beside the tier, not a 6th dimension — while **confidence** + a **`match_explanation_tag`** are deterministic derivations from the dimension tiers (no extra LLM call); `_visualizer` adds the three badges to the Tier 1 cards and sorts within each tier by confidence then recency, so bulletproof standouts rise. Schema additive: two new caches (`capability-graph.json`, `jargon-normalizer.json`), an optional `dimensions[].type` (`load-bearing`/`modifying`, default load-bearing), a new `capability` `query-stats` family value, and four lazily-populated tracker/score-cache fields (`competitiveness`, `competitiveness_evidence`, `confidence`, `match_explanation_tag`). The **v1 tier rubric and the score cache are untouched** — no `rubric_version` bump, no forced re-score, no migration. Interactive smoke deferred to first real use, per the Phase 4/5/11 precedent. Deferred Phases 8–10 (triage feedback UX, recruiter rebuild + `/config tone`, nurture commands) follow by need; Phases B and C of the discovery+categorisation track are later still.

# Changelog

All notable changes to the LinkedIn Job Hunter plugin are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project aims to follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

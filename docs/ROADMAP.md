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
| **4. Visual render layer** | v0.7.0 | In progress | [`specs/2026-04-29-visual-render-layer-design.md`](superpowers/specs/2026-04-29-visual-render-layer-design.md) | [`plans/2026-04-29-visual-render-layer.md`](superpowers/plans/2026-04-29-visual-render-layer.md) |

**Current focus:** Phase 4 (visual render layer) executing toward v0.7.0.

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

- [ ] **Task 1: `_visualizer` skill skeleton + reference files**
- [ ] **Task 2: theme.css asset**
- [ ] **Task 3: interactive.js asset**
- [ ] **Task 4: base.html.j2 + base.md.j2 frame templates**
- [ ] **Task 5: `_visualizer/SKILL.md` full subagent contract**
- [ ] **Task 6: `match-jobs` HTML + markdown templates**
- [ ] **Task 7: `render-orchestration.md` shared reference**
- [ ] **Task 8: Schema migration 0.6 → 0.7**
- [ ] **Task 9: `/config` slash command**
- [ ] **Task 10: Wire `/match-jobs` to render orchestration**
- [ ] **Task 11: End-to-end smoke + token measurement**
- [ ] **Task 12: Wire `/job-search`**
- [ ] **Task 13: Wire `/check-job-notifications`**
- [ ] **Task 14: Wire `/check-inbox`**
- [ ] **Task 15: Wire `/funnel-report`**
- [ ] **Task 16: Wire `/interview-prep`**
- [ ] **Task 17: CLAUDE.md hard rule + `.gitignore` update**
- [ ] **Task 18: Release prep — versioning, ROADMAP, CHANGELOG, README**
- [ ] **Task 19: Final 6-command end-to-end smoke**

---

## Log

- **2026-04-16** — Roadmap established. Phase 1 design spec drafted and committed. Meta-decision: phased releases (v0.4.0 → v0.5.0 → v0.6.0), not single-bundle v0.4.0.
- **2026-04-17** — Phase 1 shipped as v0.4.0. Phase 2 (SEO / ATS depth) entering design.
- **2026-04-17** — Phase 2 shipped as v0.5.0. Phase 3 (new user-facing commands) entering design.
- **2026-04-17** — Phase 3 shipped as v0.6.0. All three phases complete; plugin is feature-complete per the v0.4.0–v0.6.0 roadmap. Future phases gated on user need.
- **2026-04-17** — v0.6.1 maintenance release. Renamed 7 internal skills with `_` prefix for menu clarity.
- **2026-04-29** — Phase 4 (visual render layer) entering execution. Spec + plan committed; v0.7.0 target.

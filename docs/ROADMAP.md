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
| **1. Token + Agentic foundations** | v0.4.0 | In design | [`specs/2026-04-16-phase-1-token-agentic-foundations-design.md`](superpowers/specs/2026-04-16-phase-1-token-agentic-foundations-design.md) | _pending_ |
| 2. SEO / ATS depth | v0.5.0 | Not started | _pending_ | — |
| 3. New user-facing commands | v0.6.0 | Not started | _pending_ | — |

**Current focus:** Phase 1 spec review, then writing implementation plan.

---

## Phase 1 — v0.4.0: Token + Agentic foundations

Prerequisite for every later phase. Nothing in Phase 2 or 3 can ship cleanly without the subagent protocol, the progressive-disclosure split, and the cache-key reconciliation landing first.

- [x] **`shared-references/subagent-protocol.md`** — canonical contract for every subagent-spawning skill (I/O shape, token budget, allowed tools, delta-return rule, fan-in merge).
- [x] **CLAUDE.md at repo root** — goal, hard rules (browser policy, dedupe-before-extract, `.job-scout/` SSOT, `disable-model-invocation`, subagent protocol).
- [x] **Repo `.gitignore`** — `.job-scout/`, `.DS_Store`, common editor dirs.
- [x] **`.claude/settings.local.json` trim** — *closed as N/A.* File is excluded by the user's global gitignore (`**/.claude/settings.local.json`), has never been tracked in this repo, and auto-regrows via the Claude Code harness on every permission prompt. "Trimming" it has no persistent effect, so committing a trimmed version is impossible and pointless. Kept in the Phase 1 list for audit trail; no PR shipped for this item.
- [ ] **Progressive disclosure split of `cv-optimizer/SKILL.md`** — ~14KB → ≤3KB orchestrator + lazy-loaded phase files.
- [ ] **Progressive disclosure split of `profile-optimizer/SKILL.md`** — ~13KB → ≤3KB orchestrator + lazy-loaded section files.
- [x] **Score-cache key reconciliation** — `(job_id, cv_hash, profile_hash)` everywhere. Write `profile_hash` from `profile-optimizer`.
- [x] **`.job-scout/schema-version`** — file + empty migration runner skeleton.
- [x] **Tracker archival** — `status:seen` + `last_seen > 60d` rotates to `.job-scout/archive/tracker-YYYY.json`.
- [x] **Delta-aware LinkedIn snapshot** — per-section hashes in `.job-scout/cache/linkedin-profile.json`; only changed sections re-score.
- [x] **Supporting-docs index** — `.job-scout/cache/supporting-docs.json` auto-built on bootstrap; `/index-docs` surface command deferred to Phase 3.
- [ ] **Parallel job scoring** — `/match-jobs` and `/check-job-notifications` fan out scoring subagents (~5 jobs per subagent).
- [ ] **Parallel Top Picks pagination** — 1 subagent per page during Step 10 sweep.
- [ ] **`company-researcher` subagent** — digest-only return (size/stage/rep/red-flags, ≤3 lines).
- [ ] **`cv-section-rewriter` subagent** — one per role during Phase 3 CV rewrite.

## Phase 2 — v0.5.0: SEO / ATS depth

Builds on the Phase 1 subagent protocol and corpus machinery. Spec to be written after Phase 1 ships.

- ATS scan simulator (Workday / Greenhouse / Lever behaviour)
- Learned JD keyword corpus at `.job-scout/cache/jd-keyword-corpus.json`
- Post-rewrite keyword-density check (>3% = stuffing, <0.5% = undershoot)
- Supporting-doc-backed claims in CV + Featured section
- Reverse-Boolean discoverability check per A-tier job
- Google snippet literal preview
- Banner + Featured concrete templates
- Recruiter lead-memory in `threads.json`

## Phase 3 — v0.6.0: New user-facing commands

Each command surfaces capabilities built in Phases 1–2. Spec to be written after Phase 2 ships.

- `/cover-letter <tracker-id|url>` + `cover-letter-writer` subagent
- `/interview-prep <tracker-id>`
- `/funnel-report`
- `/index-docs` (explicit command over Phase 1 cache)
- Daily-driver context line (`last run N days ago, X alerts since`)
- Bootstrap nudge to index supporting docs on first run

---

## Log

- **2026-04-16** — Roadmap established. Phase 1 design spec drafted and committed. Meta-decision: phased releases (v0.4.0 → v0.5.0 → v0.6.0), not single-bundle v0.4.0.

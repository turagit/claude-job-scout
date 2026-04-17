---
name: _cv-optimizer
description: >
  [Internal — loaded by /analyze-cv] This skill should be used when the user asks to "analyze my CV", "improve my resume",
  "optimize my CV for ATS", "check my CV", "review my resume", "make my CV better",
  "tailor my CV", or needs guidance on CV formatting, keyword optimization,
  or ATS compatibility. Also triggers when preparing a CV for job applications.
version: 0.3.0
---

# CV Optimizer (Orchestrator)

Analyze, score, and transform CVs into documents that pass ATS filters **and** compel human reviewers to shortlist the candidate — using evidence-based persuasion psychology throughout.

This file is the **orchestrator**: it names the phases, the gates between them, and the lazy-loaded reference file for each phase. Phase content lives in `references/phase-N-*.md` and is loaded only when that phase actually runs.

## Phase sequence

| Phase | Purpose | Reference file | Gate — run if... |
|-------|---------|----------------|-------------------|
| 0 | Discovery interview | `references/phase-0-discovery-interview.md` | `user-profile.json.discovery_complete != true` |
| 1 | Seven-dimension scoring | `references/phase-1-seven-dimension-scoring.md` | Always, unless a valid `cv-analysis-<hash>.json` cache hit exists |
| 2 | Scoring & gap analysis | `references/phase-2-gap-analysis.md` | Always after Phase 1 |
| 2a | ATS scan simulation | `references/ats-simulator.md` | Always after Phase 2 (supplementary robot-gate check) |
| 3 | Optimized rewrite | `references/phase-3-optimized-rewrite.md` | User requests a rewrite |
| 4 | Output deliverables | `references/phase-4-output-deliverables.md` | Always at end |

**Rule:** do not load a phase reference until its gate is reached. Loading all phase references up front is the anti-pattern this orchestrator exists to prevent.

## Caching contract

Both the parsed CV and the full analysis output are cached by content hash:

- **`.job-scout/cache/cv-<hash>.json`** — parsed CV text + extracted keyword list. Written on first parse.
- **`.job-scout/cache/cv-analysis-<hash>.json`** — the full Phase 1–2 scoring output. Written on first analysis.

Before re-running any phase, compute the CV's content hash and check the cache. If a hit exists and the user hasn't asked for a fresh run, return the cached result. The `master_keyword_list` and `cv_summary` are also persisted to `.job-scout/user-profile.json` for downstream skills (`_profile-optimizer`, `_job-matcher`) to reuse without ever re-parsing the CV.

The Phase 0 discovery interview only runs when `user-profile.json.discovery_complete != true`. Once complete, subsequent runs skip straight to analysis.

## Freelance / Contractor mode

When the user's profile indicates freelance/contract work, apply adjustments from `../shared-references/freelance-context.md`:
- Project-based layout preferred over employer-based
- Skills matrix at top for quick scanning
- Returning clients or extended contracts signal reliability (social proof + authority)
- Include availability date, day-rate range (optional), IR35 awareness

## Parallel rewrite (Phase 3)

When Phase 3 runs, the orchestrator dispatches one subagent per role section to `_cv-section-rewriter/SKILL.md`, following `../shared-references/subagent-protocol.md`:

For each role block in the CV:
1. Classify role weight: `current` (most recent), `previous` (2nd through N-1), `older` (earliest 1-2 roles).
2. Dispatch `_cv-section-rewriter` with:
   - `task: "rewrite-cv-role"`
   - `inputs`: the role block, the user profile (cv_summary, target_roles, tone_preference), target keywords from the master keyword list, and the role weight
   - `budget_lines: 80`, `allowed_tools: ["Read"]`
3. Each subagent loads `references/phase-3-optimized-rewrite.md`, applies SPAR rules, and returns `deltas: [{ role_id, bullets_optimized }]`.
4. Main thread collects all deltas and assembles the final CV document.

**Fallback:** if the `Agent` tool is unavailable, fall back to sequential in-thread rewrite using the same `references/phase-3-optimized-rewrite.md` rules.

## Reference Materials

- **`references/phase-0-discovery-interview.md`** — Phase 0 content (lazy)
- **`references/phase-1-seven-dimension-scoring.md`** — Phase 1 content (lazy)
- **`references/phase-2-gap-analysis.md`** — Phase 2 content (lazy)
- **`references/ats-simulator.md`** — ATS scan simulation: Workday, Greenhouse, Lever (lazy, Phase 2a)
- **`references/phase-3-optimized-rewrite.md`** — Phase 3 content (lazy)
- **`references/phase-4-output-deliverables.md`** — Phase 4 content (lazy)
- **`references/ats-keywords.md`** — ATS keyword categories by industry
- **`references/action-verbs.md`** — Categorized action verbs
- **`references/psychology-cheatsheet.md`** — Quick-reference for persuasion techniques
- **`../shared-references/freelance-context.md`** — Freelance CV structure
- **`../shared-references/workspace-layout.md`** — `.job-scout/` layout and bootstrap
- **`../shared-references/cv-loading.md`** — CV loading + caching procedure
- **`../shared-references/subagent-protocol.md`** — Subagent dispatch contract (for Phase 3 parallel rewrite)

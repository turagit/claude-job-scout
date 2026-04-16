# Phase 1 — Token + Agentic Foundations (v0.4.0)

**Date:** 2026-04-16
**Status:** In design — pending user review
**Target release:** v0.4.0

## Why this phase exists

Every later phase — the ATS simulator, the JD keyword corpus, the `/cover-letter` command, `/interview-prep`, `/funnel-report` — depends on three things that don't yet exist:

1. A **contract for spawning subagents** so parallel work can happen without bleeding tokens into the main thread.
2. **Lean top-level SKILL files** so simply triggering a skill doesn't load 14KB of phase-3 prose the user won't reach in this run.
3. **Reconciled state keys and a schema version** so the per-project `.job-scout/` store can evolve safely.

Without those three, Phase 2 and 3 would build on sand. Phase 1 is therefore the minimal foundation that unlocks everything else, plus the concrete first uses of the subagent protocol (parallel scoring, parallel pagination, two new subagent skills) as proof the protocol works.

## Goals

- Cut main-thread token cost on repeat `/check-job-notifications` and `/match-jobs` runs by parallelising scoring across subagents.
- Cut one-shot trigger cost on `cv-optimizer` and `profile-optimizer` by moving phase-specific content out of `SKILL.md` into lazy-loaded references.
- Give every future subagent-spawning skill (cover-letter, interview-prep, company research, ATS simulator) a single canonical protocol to obey.
- Make the `.job-scout/` state layout cheaper to read, easier to archive, and safe to migrate.
- Surface the plugin's goal and hard rules in a repo-root `CLAUDE.md` so future agent edits stay on-contract.

## Non-goals (explicitly deferred)

- **ATS simulator, JD keyword corpus, density checks, Google snippet preview, Featured templates, recruiter lead-memory** — Phase 2.
- **`/cover-letter`, `/interview-prep`, `/funnel-report`, `/index-docs` commands** — Phase 3.
- **Changes to the browser policy or any new browser framework** — out of scope forever.
- **Re-scoring historical jobs under the new cache key** — we invalidate rather than migrate; unchanged jobs get a one-time re-score on first Phase 1 run.

---

## Component 1: Subagent Protocol

**Artefact:** `skills/shared-references/subagent-protocol.md`

**Purpose:** A single reference every skill points to when it intends to dispatch subagents. Avoids reinventing the I/O shape per skill.

**Contract (to be expanded in the reference file):**

- **Dispatch:** use the `Agent` tool. Every spawn names a `subagent_type` (e.g., `general-purpose`, or a repo-local named subagent when those become available) and carries a self-contained prompt — no reliance on parent conversation context.
- **Input shape:** structured JSON string in the prompt body containing `{ task, inputs, budget_lines, allowed_tools }`. The subagent is told to ignore anything not in `inputs`.
- **Output shape:** strict JSON with `{ status: "ok" | "partial" | "error", deltas: [...], errors: [...] }`. No prose, no repeated input data. The main thread merges `deltas` into canonical state.
- **Delta-return rule:** subagents return **only what changed** against the inputs they received. Re-emitting unchanged fields is forbidden. Cheap to merge, cheap to read.
- **Budget:** every dispatch carries a line-count cap on the response (typical ≤200 lines). Subagents must respect it or return `status: "partial"` with a continuation cursor.
- **Allowed tools:** the dispatching skill lists exactly the tools the subagent may use. The default is the read-only set (`Read`, `Grep`, `Glob`); write access is an explicit grant.
- **Idempotency:** re-dispatching the same `(task, inputs)` tuple must produce the same deltas. State writes happen only in the main thread after fan-in.
- **Error handling:** a subagent that can't complete returns `status: "error"` with `{ code, message }`. The main thread decides whether to retry, fall back, or surface to the user — never the subagent.

**Why this shape:** deltas + strict output schema are what keep a 20-subagent fan-out from blowing the main context. The main thread reads one short JSON per subagent, not 20 full analyses.

## Component 2: Progressive disclosure of large SKILL files

**Problem:** `skills/cv-optimizer/SKILL.md` is ~14KB and `skills/profile-optimizer/SKILL.md` is ~13KB. Because skills load in full on trigger, every `/analyze-cv` or `/optimize-profile` run drags the entire file into context — including Phase 3 prose the current run may not reach.

**Solution:** each large SKILL becomes a thin orchestrator (≤3KB) that describes the phase sequence and gates, plus one file per phase loaded on demand via Read.

**`cv-optimizer/` target layout:**

```
skills/cv-optimizer/
  SKILL.md                           # orchestration + phase gating, ~3KB
  references/
    phase-0-discovery-interview.md   # existing content, now lazy-loaded
    phase-1-seven-dimension-scoring.md
    phase-2-gap-analysis.md
    phase-3-optimized-rewrite.md
    phase-4-output-deliverables.md
    psychology-cheatsheet.md         # already exists
    action-verbs.md                  # already exists
    ats-keywords.md                  # already exists
```

**`profile-optimizer/` target layout:** same pattern, split by section (headline, about, experience, skills, featured, additional, open-to-work, structured-fields, alignment-report).

**Rule:** the orchestrator SKILL.md lists the phases and the exact reference path to read for each. A skill run that only reaches Phase 2 never loads Phase 3 and 4 content. Previously-loaded content is not repeated.

## Component 3: State layout reconciliation

### 3a. Score cache key

`.job-scout/cache/scores.json` is inconsistently documented:

- `shared-references/workspace-layout.md` declares the key as `(job_id, cv_hash, profile_hash)`.
- `skills/job-matcher/SKILL.md` and `skills/check-job-notifications/SKILL.md` use `(job_id, cv_hash)`.

**Decision:** the workspace-layout version (3-tuple with `profile_hash`) is correct. Rationale: LinkedIn profile edits can change the keyword list the matcher uses, so scoring should invalidate when the profile changes. The 2-tuple version silently re-uses stale scores after a profile rewrite.

**Actions:**
- Update `job-matcher/SKILL.md`, `match-jobs/SKILL.md`, `check-job-notifications/SKILL.md` to reference the 3-tuple key.
- `profile-optimizer` must compute and persist `profile_hash` to `.job-scout/user-profile.json` on any profile write.
- First run after upgrade invalidates all existing scores (tree-wide cache miss is a one-time cost).

### 3b. Schema versioning

**Artefact:** `.job-scout/schema-version` file. JSON: `{ "version": 1, "upgraded_at": "<ISO>" }`.

**Bootstrap addition:** the workspace bootstrap procedure in `shared-references/workspace-layout.md` also writes this file on folder creation and checks it on every subsequent command entry.

**Migration runner:** an empty helper documented in `shared-references/workspace-layout.md`, with the shape every future migration plugs into:

```
if current_version < target:
  for v in range(current_version, target):
    apply_migration_v<v>_to_v<v+1>()
  write schema-version = target
```

No migrations ship in Phase 1 (the score-cache key change is handled by invalidation, not migration), but the scaffolding is in place for Phase 2+.

### 3c. Tracker archival

`.job-scout/tracker.json` grows monotonically. At scale (years of use), reading the whole file for every dedupe becomes non-trivial.

**Policy:**
- On any write to `tracker.json`, run a quick archive pass: any job with `status == "seen"` AND `last_seen older than 60 days` moves to `.job-scout/archive/tracker-YYYY.json` (keyed by the year the job was first seen).
- Applied / approved / rejected jobs are never archived — they're real artefacts of the user's search history.
- The dedupe read pattern updates to: check hot `tracker.json` first, fall through to current-year archive only if the dedupe misses. Older years are not read during hot paths — they exist for `/funnel-report` (Phase 3) and manual inspection.

### 3d. Supporting-docs index

**Artefact:** `.job-scout/cache/supporting-docs.json`.

**Shape:**
```json
{
  "version": 1,
  "last_scanned": "<ISO>",
  "docs": {
    "<relative_path>": {
      "type": "cert | talk | deck | recommendation | case_study | publication | portfolio | other",
      "hash": "<sha256>",
      "extracted_keywords": [],
      "summary_200w": "...",
      "last_indexed": "<ISO>"
    }
  }
}
```

**Built when:** workspace bootstrap. The bootstrap procedure gains a non-blocking pass that scans the workspace root (not `.job-scout/` itself) for non-CV documents and asks the user once whether to index them. Declining is remembered for the session; the nag doesn't repeat.

**Used by:** `profile-optimizer` (Featured section, About claims) and — in Phase 2/3 — `cover-letter-writer`, the ATS simulator, and `/index-docs`.

**Phase 1 scope:** write the index; no consumer skill in Phase 1 is required to read it (first consumer lands in Phase 2). Building the data structure now avoids backfilling later.

## Component 4: Delta-aware LinkedIn snapshot

`.job-scout/cache/linkedin-profile.json` currently stores the last-seen profile with a single `timestamp` field and a 7-day reuse window. When 7 days elapse, the whole profile is re-read and re-scored.

**Change:** the file gains a `last_full_read` timestamp AND a per-section hash map. The behaviour becomes two-tier:

- **Outer gate (cheap):** if `last_full_read < 7 days ago` AND the user hasn't indicated an edit, skip the browser read entirely and reuse cached scores. Unchanged.
- **Inner gate (new):** when a browser read does happen (either because the 7-day window expired or the user requested a fresh check), hash each section independently (headline, about, each experience entry, skills, featured, etc.). Compare against the cached hash map:
  - Hash matches → reuse the cached scoring for that section.
  - Hash differs → re-score only that section.
  - Update the hash map and `last_full_read` after the read completes.

**Result:** the expensive bit (LLM-side scoring) becomes incremental across the 7-day boundary. The cheap bit (browser-side read) can still be skipped within the window by the outer gate. LinkedIn doesn't expose change-since-timestamp, so there's no way to avoid the browser read itself once the outer gate fails.

## Component 5: Orchestration refactors (first uses of the subagent protocol)

### 5a. Parallel job scoring

**Skills affected:** `/match-jobs`, `/check-job-notifications`.

**Current:** sequential loop over new jobs, each scored inline in the main thread.

**Target:** batch new jobs into groups of ~5, dispatch one subagent per batch with `subagent_type: "general-purpose"`, each carrying its batch of job blobs plus the user profile. Each subagent returns `deltas: [{ job_id, score, tier, breakdown }, ...]` only. Main thread merges into `scores.json` and `tracker.json`.

**Batch size:** 5 is a starting point; the protocol allows callers to tune. Not a user-facing knob.

**Fallback:** if the subagent system is unavailable (tool not present), fall back to sequential scoring. Log that the fallback triggered.

### 5b. Parallel Top Picks pagination

**Skill affected:** Step 10 of `/check-job-notifications`.

**Current:** single loop paginates, dedupes, extracts, scores — all in the main thread.

**Target:** dispatch 1 subagent per page (typically 5 pages max per existing rule). Each subagent receives the page URL, dedupes against a snapshot of `tracker.json` passed in `inputs`, extracts new jobs only, returns `deltas: [{ job_id, title, company, ...raw_blob }, ...]`. Main thread fans into the scoring fan-out from 5a.

**Bound:** the existing stop rules (zero-new-after-dedupe, 5-page cap, user-initiated stop) are preserved — they become main-thread concerns since the main thread aggregates.

### 5c. `company-researcher` subagent skill

**New skill:** `skills/company-researcher/SKILL.md`.

**Invocation:** dispatched by `profile-optimizer` and (Phase 2+) `cover-letter-writer` when a job listing carries a company name worth enriching.

**Input:** `{ company_name, job_id?, signals_requested: ["size", "stage", "reputation", "red_flags"] }`.

**Output:** `deltas: [{ company_name, size, stage, reputation_digest, red_flags }]` — maximum 3 short lines per company. No speculative or unverified claims; if a signal can't be determined, the field is `null`.

**Tools:** `Read` (only — this subagent does not touch the browser in Phase 1; it works from the JD blob and any cached company files the user has). Future phase may grant `WebFetch` under explicit consent.

### 5d. `cv-section-rewriter` subagent skill

**New skill:** `skills/cv-section-rewriter/SKILL.md`.

**Invocation:** dispatched by `cv-optimizer` during Phase 3 (Optimized Rewrite). One subagent per role section.

**Input:** `{ role_block, user_profile, target_keywords, tone_preference }`.

**Output:** `deltas: [{ role_id, bullets_optimized: [...] }]`. Bullets returned with the same structure as input (no prose, no commentary).

**Tools:** `Read` only.

**Why this split:** the CV-rewrite phase is the most token-heavy path in the plugin. Parallelising role-level rewrites roughly halves wall-time and keeps the main thread free to assemble the final document.

## Component 6: Repo hygiene

### 6a. `CLAUDE.md` at repo root

**Contents** (sections, not the full text — that goes in implementation):
1. **Goal** — one paragraph from the Roadmap vision.
2. **Hard rules** — browser-policy (Chrome extension only), dedupe-before-extract, `.job-scout/` SSOT, `disable-model-invocation: true` on every command, the subagent protocol (link).
3. **File layout** — where skills live, where references live, where per-project state lives, where specs and plans live.
4. **Never do** — install Playwright/Selenium, request computer use, commit `.job-scout/` (covered by `.gitignore`), skip the subagent protocol.
5. **Testing / validation** — no automated test suite exists; manual validation procedure documented.
6. **Versioning policy** — plugin version in `.claude-plugin/plugin.json` is canonical; per-skill `version:` frontmatter is informational and bumps when that skill's contract changes.

### 6b. Repo `.gitignore`

A repo-level `.gitignore` does not currently exist. Add one with:
```
.DS_Store
.idea/
.vscode/
.job-scout/
*.swp
```

Explicit: `.job-scout/` is per-project state for *users* of the plugin. The plugin's own repo should never commit one.

### 6c. `.claude/settings.local.json` trim

The current file carries several backslash-escaped `find` and `Bash(wc ...)` permissions that accumulated during prior development. Trim to the permissions actually required for maintaining this plugin (git operations, reading the plugin's own files). No attempt to generalise to other projects.

---

## Data shapes introduced or changed in Phase 1

| File | Phase 1 change |
|------|----------------|
| `.job-scout/cache/scores.json` | Key becomes `(job_id, cv_hash, profile_hash)`. All existing entries invalidated on first upgraded run. |
| `.job-scout/user-profile.json` | Adds `profile_hash` field, written by `profile-optimizer`. |
| `.job-scout/schema-version` | New file. `{ "version": 1, "upgraded_at": "<ISO>" }`. |
| `.job-scout/archive/tracker-YYYY.json` | New archive target for aged `status:seen` tracker entries. |
| `.job-scout/cache/linkedin-profile.json` | Adds per-section `hash` field alongside each cached section. |
| `.job-scout/cache/supporting-docs.json` | New file. Shape documented in Component 3d. |

## Rollout and safety

- **Single `main` branch, feature-by-feature merges.** Each Phase 1 component (subagent protocol, cv-optimizer split, profile-optimizer split, cache-key reconciliation, tracker archival, delta snapshot, supporting-docs index, parallel scoring, parallel pagination, company-researcher, cv-section-rewriter, repo hygiene) is a separate PR against `main`.
- **Version bump** in `.claude-plugin/plugin.json` only on the final Phase 1 merge (0.3.0 → 0.4.0), with a `CHANGELOG.md` entry summarising all components.
- **First-run migration** when a user upgrades: bootstrap detects missing `schema-version`, writes `version: 1`, invalidates `scores.json`, runs a one-time tracker archive pass. User is informed in a single message, not interactively.
- **Fallback for subagent-unavailable environments:** every subagent-spawning code path must fall back to sequential in-thread execution if the `Agent` tool isn't present. Detected at dispatch time, not at skill-load time.

## What "done" looks like

Phase 1 ships when:

- All Phase 1 Roadmap checkboxes are ticked.
- `CHANGELOG.md` has a 0.4.0 section.
- `plugin.json` reports `0.4.0`.
- A single clean run of `/analyze-cv`, `/optimize-profile`, `/check-job-notifications`, and `/match-jobs` on a fresh workspace completes with no regressions relative to 0.3.0.
- `docs/ROADMAP.md` Phase 2 row flips from "Not started" to "In design" with a spec path pointer.

## Open questions (to settle before writing the implementation plan)

1. **Named subagent types.** If the plugin gains repo-local named subagents (e.g., `subagent_type: "job-scorer"`), should the subagent-protocol reference require them, or is `general-purpose` with a self-contained prompt sufficient? **Working assumption:** `general-purpose` is sufficient for Phase 1; named types become a Phase 2 refinement if needed.
2. **Supporting-docs indexer scope.** Should the Phase 1 indexer extract keywords from indexed docs, or only record file metadata + summary? **Working assumption:** metadata + summary only in Phase 1; keyword extraction lands with its first consumer in Phase 2.
3. **Tracker archival trigger.** Per-write (cheap but frequent) or per-command-entry (cheaper but less predictable)? **Working assumption:** per-command-entry, gated on "not already run today" via a `last_archive_pass` field in `tracker.json`.

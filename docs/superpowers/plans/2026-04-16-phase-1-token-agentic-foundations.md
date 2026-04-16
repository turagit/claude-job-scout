# Phase 1 — Token + Agentic Foundations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship v0.4.0 by delivering the foundational protocol and state-layout changes that unlock every later phase, plus the first four concrete uses of the subagent protocol.

**Architecture:** This plugin is a Claude Code plugin — the "code" is markdown skill files, markdown references, and per-project JSON state under `.job-scout/`. There is no compiled artifact and no test runner. "Tests" are verification scripts using `jq`, `grep`, `wc`, and targeted manual re-reads.

**Tech Stack:** Markdown (CommonMark), JSON state files, Claude Agent tool for subagent dispatch, Claude Chrome extension for browser work.

**Design spec:** [`docs/superpowers/specs/2026-04-16-phase-1-token-agentic-foundations-design.md`](../specs/2026-04-16-phase-1-token-agentic-foundations-design.md)

**Roadmap:** [`docs/ROADMAP.md`](../../ROADMAP.md)

**Branching:** each task is one PR against `main`. Commit on a per-task feature branch named `phase-1/task-NN-<short-slug>`. The final task (version bump + CHANGELOG) merges last and cuts v0.4.0.

**Merge order:** tasks are numbered to be merged **serially** in numerical order. Several tasks touch the same file (e.g., `profile-optimizer/SKILL.md` is touched by Tasks 6, 9, 11, and 14), and later tasks assume earlier merges have landed on `main`. Each task starts with `git checkout main && git pull` so a fresh branch always picks up prior merges. Merging out of order will cause conflicts that the per-task instructions do not cover.

**Progress tracking:** every time a task's PR lands on `main`, tick the matching checkbox in `docs/ROADMAP.md` (the Phase 1 section). The roadmap is the resume-trail across sessions — keep it in sync with what's actually shipped so a cold-start agent can pick up where we left off.

---

## Task 1: Repo `.gitignore`

**Files:**
- Create: `/Users/tura/git/claude-job-scout/.gitignore`

- [ ] **Step 1: Create branch**

Run:
```bash
git checkout -b phase-1/task-01-gitignore
```

- [ ] **Step 2: Write `.gitignore`**

Create `/Users/tura/git/claude-job-scout/.gitignore` with exactly:

```
.DS_Store
.idea/
.vscode/
.job-scout/
*.swp
*.swo
```

- [ ] **Step 3: Verify the file**

Run:
```bash
cat /Users/tura/git/claude-job-scout/.gitignore
```

Expected: shows the 6 lines above.

Run:
```bash
cd /Users/tura/git/claude-job-scout && git status
```

Expected: `.gitignore` appears under "Untracked files". No changes to other files.

- [ ] **Step 4: Commit**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git add .gitignore && git commit -m "$(cat <<'EOF'
Add repo .gitignore

The plugin repo has never carried a .gitignore; users' per-project
.job-scout/ folders must never end up inside the plugin repo itself.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 5: Push and open PR**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git push -u origin phase-1/task-01-gitignore && gh pr create --title "phase-1/01: add repo .gitignore" --body "Part of Phase 1 (v0.4.0). Adds a repo-level .gitignore so .job-scout/ (per-project state for users of the plugin) never gets committed into the plugin repo itself. See docs/ROADMAP.md."
```

---

## Task 2: `CLAUDE.md` at repo root

**Files:**
- Create: `/Users/tura/git/claude-job-scout/CLAUDE.md`

- [ ] **Step 1: Create branch**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-1/task-02-claude-md
```

- [ ] **Step 2: Write `CLAUDE.md`**

Create `/Users/tura/git/claude-job-scout/CLAUDE.md` with exactly this content:

```markdown
# CLAUDE.md

Guidance for Claude (or any agent) working inside the `linkedin-job-hunter` plugin repo. If you're resuming cold, read this first, then `docs/ROADMAP.md`.

## Goal

Automate the end-to-end LinkedIn job-seeking pipeline (CV → profile → search → apply → recruiter) inside the user's own logged-in browser via the Claude Chrome extension, with per-project state, aggressive caching, and subagent-parallelism for scorable units of work.

## Hard rules (non-negotiable)

1. **Browser work uses the Claude Chrome extension exclusively.** Never request "computer use". Never install or suggest Playwright, Selenium, Puppeteer, headless Chrome, or any MCP browser server other than the official Chrome extension. See `skills/shared-references/browser-policy.md`.
2. **Dedupe before extract.** Every command that touches LinkedIn listings loads `.job-scout/tracker.json` first, collects candidate IDs, filters against the tracker, then opens only new ones. This is the largest token saver in the plugin.
3. **`.job-scout/` is the single source of truth for per-project state.** CV profile, tracker, caches, reports, recruiter threads. Never write state to the workspace root or anywhere else.
4. **Every slash command carries `disable-model-invocation: true`.** Commands are user-invoked only — the model must never auto-fire browser automation, applications, or recruiter replies.
5. **Subagent dispatch follows `skills/shared-references/subagent-protocol.md`.** If you spawn a subagent for any reason, use the I/O contract, token budget, and delta-return rule defined there. No ad-hoc subagent shapes.

## File layout

- `skills/<name>/SKILL.md` — each slash command and each model-auto-loaded skill.
- `skills/<name>/references/` — lazy-loaded reference material for that skill.
- `skills/shared-references/` — references used by more than one skill (browser policy, workspace layout, tracker schema, CV loading, subagent protocol, freelance context).
- `.claude-plugin/plugin.json` — plugin manifest and canonical plugin version.
- `docs/ROADMAP.md` — phase status, resume trail.
- `docs/superpowers/specs/` — design specs (immutable once approved).
- `docs/superpowers/plans/` — step-by-step implementation plans.
- `CHANGELOG.md` — user-visible release notes.
- `README.md` — end-user-facing docs.

## Never do

- Install or suggest any browser-automation framework besides the Chrome extension.
- Commit a `.job-scout/` folder into this repo (`.gitignore` covers it).
- Skip the subagent protocol when dispatching subagents.
- Add a per-skill `version:` bump without matching the plugin version policy below.
- Fabricate user achievements, credentials, or metrics in any CV/profile/cover-letter output.
- Enter sensitive data (SSN, bank details, passwords) into any browser form.

## Testing / validation

No automated test suite exists. Validation is manual: spot-checks via shell (`jq`, `grep`, `wc`) and end-to-end runs of the affected slash command in a scratch workspace. Each implementation task in `docs/superpowers/plans/` names the specific verification step.

## Versioning policy

- `.claude-plugin/plugin.json` carries the canonical plugin version. Bump on every user-visible release (SemVer minor for feature releases, patch for fixes).
- Per-skill `version:` frontmatter is informational. Bump it when that skill's contract or output shape changes — not on every edit.
- `CHANGELOG.md` gets one section per plugin version, following Keep a Changelog.
```

- [ ] **Step 3: Verify the file**

Run:
```bash
cd /Users/tura/git/claude-job-scout && wc -l CLAUDE.md
```

Expected: roughly 60 lines.

Run:
```bash
cd /Users/tura/git/claude-job-scout && grep -c "Hard rules" CLAUDE.md
```

Expected: `1`.

- [ ] **Step 4: Commit**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git add CLAUDE.md && git commit -m "$(cat <<'EOF'
Add CLAUDE.md with goal and hard rules

Single top-level contract every agent reads when entering this repo:
goal statement, hard rules (browser policy, dedupe-before-extract,
.job-scout/ SSOT, disable-model-invocation, subagent protocol), file
layout, and versioning policy.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 5: Push and open PR**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git push -u origin phase-1/task-02-claude-md && gh pr create --title "phase-1/02: add CLAUDE.md with goal and hard rules" --body "Part of Phase 1 (v0.4.0). Establishes repo-root CLAUDE.md as the single top-level agent contract. See docs/superpowers/specs/2026-04-16-phase-1-token-agentic-foundations-design.md Component 6a."
```

---

## Task 3: Trim `.claude/settings.local.json`

**Files:**
- Modify: `/Users/tura/git/claude-job-scout/.claude/settings.local.json`

- [ ] **Step 1: Create branch**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-1/task-03-settings-trim
```

- [ ] **Step 2: Inspect current permissions**

Run:
```bash
cd /Users/tura/git/claude-job-scout && cat .claude/settings.local.json
```

Note the long list of `Bash(find ...)` and `Bash(wc ...)` permissions that accumulated during prior development.

- [ ] **Step 3: Replace with trimmed permissions**

Overwrite `/Users/tura/git/claude-job-scout/.claude/settings.local.json` with exactly:

```json
{
  "permissions": {
    "allow": [
      "Read(//Users/tura/git/claude-job-scout/**)",
      "Bash(git checkout:*)",
      "Bash(git add:*)",
      "Bash(git commit:*)",
      "Bash(git push:*)",
      "Bash(gh pr:*)",
      "Bash(git fetch:*)",
      "Bash(git pull:*)",
      "Bash(git branch:*)",
      "Bash(git status:*)",
      "Bash(git diff:*)",
      "Bash(git log:*)",
      "Bash(git stash:*)",
      "Bash(git rebase:*)",
      "Bash(git merge:*)"
    ]
  }
}
```

- [ ] **Step 4: Verify JSON parses**

Run:
```bash
cd /Users/tura/git/claude-job-scout && cat .claude/settings.local.json | jq '.permissions.allow | length'
```

Expected: `15`.

- [ ] **Step 5: Commit**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git add .claude/settings.local.json && git commit -m "$(cat <<'EOF'
Trim .claude/settings.local.json to git-workflow permissions

The file had accumulated ad-hoc find/wc/xargs permissions during prior
development. Trimmed to the git and gh commands actually used when
maintaining this repo.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 6: Push and open PR**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git push -u origin phase-1/task-03-settings-trim && gh pr create --title "phase-1/03: trim .claude/settings.local.json" --body "Part of Phase 1 (v0.4.0). Cleans up accumulated permissions. See docs/superpowers/specs/2026-04-16-phase-1-token-agentic-foundations-design.md Component 6c."
```

---

## Task 4: Subagent protocol reference

**Files:**
- Create: `/Users/tura/git/claude-job-scout/skills/shared-references/subagent-protocol.md`

- [ ] **Step 1: Create branch**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-1/task-04-subagent-protocol
```

- [ ] **Step 2: Write the reference**

Create `/Users/tura/git/claude-job-scout/skills/shared-references/subagent-protocol.md` with exactly:

```markdown
# Subagent Protocol

The single contract every skill in this plugin follows when dispatching subagents via the `Agent` tool. Parallel scoring, parallel pagination, company research, CV section rewrites, cover-letter drafting, and any future fan-out pattern all obey this protocol.

## Why this exists

Parallelism only pays off when the main thread does not re-absorb the subagent's full context. The delta-return and strict output schema in this protocol are what keep a 20-subagent fan-out from blowing the main conversation window.

## Dispatch

- Use the `Agent` tool. Every spawn names a `subagent_type`. Phase 1 uses `general-purpose` only; named repo-local subagents may be introduced in later phases.
- The prompt body is **self-contained** — the subagent has no access to the main conversation's context.
- If the `Agent` tool is not available in the current environment, every dispatching skill must fall back to sequential in-thread execution. Detect at dispatch time, not at skill-load time.

## Input shape

The prompt body carries a single JSON envelope:

```json
{
  "task": "<short string identifying the task type, e.g. 'score-job', 'rewrite-cv-role'>",
  "inputs": { /* task-specific fields */ },
  "budget_lines": 200,
  "allowed_tools": ["Read", "Grep", "Glob"]
}
```

The subagent must ignore anything not inside `inputs`. The main thread is responsible for passing all required data — the subagent cannot ask follow-up questions.

## Output shape

The subagent returns a single JSON object:

```json
{
  "status": "ok | partial | error",
  "deltas": [ /* array of change records, task-specific */ ],
  "errors": [ /* optional array of { code, message } */ ],
  "continuation_cursor": null
}
```

- `deltas` contain **only changes** against the provided inputs. Re-emitting unchanged fields is forbidden.
- `status: "partial"` signals the subagent hit its budget; `continuation_cursor` is an opaque string the dispatcher may pass back in a follow-up call.
- `status: "error"` carries a populated `errors` array. The main thread decides retry / fallback / user-surface — the subagent never prompts the user.

No prose, no commentary, no repeating input data in the response. The main thread parses the JSON and merges.

## Budget

- `budget_lines` is a hard cap on the response body. Default 200.
- Subagents that cannot fit within budget return `status: "partial"` with a continuation cursor.
- Budgets are set by the dispatcher. Subagents do not negotiate.

## Allowed tools

- The dispatcher lists exactly the tools the subagent may use.
- Phase 1 default is read-only: `["Read", "Grep", "Glob"]`.
- Write access (`Write`, `Edit`) is granted only when the task is explicitly a content-production task and the dispatcher knows where the output goes.
- Browser tools are never granted to subagents in Phase 1 — all browser work stays on the main thread.

## Idempotency

Re-dispatching the same `(task, inputs)` must produce the same deltas. State writes happen only in the main thread after fan-in, so repeated dispatches are safe.

## Fan-in merge

The dispatcher is responsible for:
1. Parsing each subagent's JSON response.
2. Validating `status`.
3. Merging `deltas` into canonical state (`scores.json`, `tracker.json`, etc.) with the existing merge rules.
4. Collecting any `errors` into a single summary for the user (or for retry logic).
5. Never letting partial/errored subagents block successful ones.

## Example: parallel job scoring

Main thread has 23 new jobs to score. It batches into 5 subagents of 5 jobs each (last subagent gets 3).

Dispatch payload (per subagent):
```json
{
  "task": "score-job-batch",
  "inputs": {
    "jobs": [ { "id": "...", "title": "...", "description": "...", ... } ],
    "user_profile": { /* cv_summary, requirements, master_keyword_list */ },
    "cv_hash": "...",
    "profile_hash": "..."
  },
  "budget_lines": 200,
  "allowed_tools": ["Read"]
}
```

Expected response:
```json
{
  "status": "ok",
  "deltas": [
    { "job_id": "123", "score": 87, "tier": "A", "breakdown": { /* per-dimension */ } },
    { "job_id": "124", "score": 61, "tier": "C", "breakdown": { /* ... */ } }
  ],
  "errors": []
}
```

Main thread merges all `deltas` into `.job-scout/cache/scores.json` and `.job-scout/tracker.json`.
```

- [ ] **Step 3: Verify the file**

Run:
```bash
cd /Users/tura/git/claude-job-scout && wc -l skills/shared-references/subagent-protocol.md
```

Expected: roughly 90 lines.

Run:
```bash
cd /Users/tura/git/claude-job-scout && grep -c "^## " skills/shared-references/subagent-protocol.md
```

Expected: `8` (eight section headings).

- [ ] **Step 4: Commit**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git add skills/shared-references/subagent-protocol.md && git commit -m "$(cat <<'EOF'
Add subagent protocol reference

Canonical I/O contract, budget, allowed-tools, idempotency, and fan-in
rules for every skill that dispatches subagents. Prerequisite for
parallel scoring, parallel pagination, company-researcher, and
cv-section-rewriter.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 5: Push and open PR**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git push -u origin phase-1/task-04-subagent-protocol && gh pr create --title "phase-1/04: add subagent protocol reference" --body "Part of Phase 1 (v0.4.0). Prerequisite for all subagent-dispatching tasks. See spec Component 1."
```

---

## Task 5: Schema-version file + bootstrap update

**Files:**
- Modify: `/Users/tura/git/claude-job-scout/skills/shared-references/workspace-layout.md`

- [ ] **Step 1: Create branch**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-1/task-05-schema-version
```

- [ ] **Step 2: Read current `workspace-layout.md`**

Run:
```bash
cd /Users/tura/git/claude-job-scout && cat skills/shared-references/workspace-layout.md
```

Note the existing "Canonical layout" block and "Bootstrap procedure" section.

- [ ] **Step 3: Add `schema-version` to the canonical layout block**

In `/Users/tura/git/claude-job-scout/skills/shared-references/workspace-layout.md`, locate the fenced code block starting with ``` and containing `.job-scout/`. Add `schema-version` as the second line inside the block.

Replace:
```
.job-scout/
  user-profile.json     # CV-derived facts, requirements, master keyword list, cv_path, cv_hash, discovery_complete
  tracker.json          # every job ever seen — see tracker-schema.md
```

With:
```
.job-scout/
  schema-version        # JSON: { "version": 1, "upgraded_at": "<ISO>" } — bumped by migration runner
  user-profile.json     # CV-derived facts, requirements, master keyword list, cv_path, cv_hash, discovery_complete
  tracker.json          # every job ever seen — see tracker-schema.md
```

- [ ] **Step 4: Update bootstrap step 4 to write schema-version**

In the same file, find the "Bootstrap procedure" section, step 4 (starts with "**On approval:**"). Append the schema-version write to that step.

Replace:
```
4. **On approval:** create the folder and the `reports/`, `cache/`, and `recruiters/` subfolders. Write a stub `user-profile.json` with `{ "created": "<ISO date>", "discovery_complete": false }` and an empty `tracker.json` with `{ "version": 1, "jobs": {}, "stats": { "total_seen": 0, "applied": 0, "rejected": 0 } }`.
```

With:
```
4. **On approval:** create the folder and the `reports/`, `cache/`, `recruiters/`, and `archive/` subfolders. Write:
   - `schema-version` with `{ "version": 1, "upgraded_at": "<ISO>" }`.
   - A stub `user-profile.json` with `{ "created": "<ISO date>", "discovery_complete": false }`.
   - An empty `tracker.json` with `{ "version": 1, "jobs": {}, "stats": { "total_seen": 0, "applied": 0, "rejected": 0 }, "last_archive_pass": null }`.
```

- [ ] **Step 5: Add a new "Schema version and migration" section**

Append this new section at the end of `/Users/tura/git/claude-job-scout/skills/shared-references/workspace-layout.md`:

```markdown
## Schema version and migration

`.job-scout/schema-version` records the current schema version of the workspace. Every command, on entry, reads this file and runs the migration runner before doing real work.

### Migration runner shape

```
current = read(.job-scout/schema-version).version
target  = SCHEMA_VERSION  # defined in code / docs, currently 1
if current < target:
  for v in range(current, target):
    apply_migration(v -> v+1)
  write(.job-scout/schema-version, { version: target, upgraded_at: <ISO> })
```

### First-run behaviour on an already-existing `.job-scout/`

If `.job-scout/` exists but `schema-version` is missing, treat the workspace as pre-schema-versioning: write `schema-version` with `{ "version": 1, "upgraded_at": "<ISO>" }` and continue. Do not re-run any migrations.

### Adding a new migration

1. Bump the canonical `SCHEMA_VERSION` constant (documented here, not in code — the plugin is a set of markdown skills).
2. Add a subsection below this one describing `v<N> → v<N+1>`: what fields change, how to transform data in place, any files that are renamed or moved.
3. Update every skill that reads the affected files to use the new shape.

No migrations exist in Phase 1. The scaffolding is in place for Phase 2+.
```

- [ ] **Step 6: Verify the file**

Run:
```bash
cd /Users/tura/git/claude-job-scout && grep -c "schema-version" skills/shared-references/workspace-layout.md
```

Expected: at least `4`.

Run:
```bash
cd /Users/tura/git/claude-job-scout && grep -c "^## " skills/shared-references/workspace-layout.md
```

Expected: `5` (original 4 sections + new "Schema version and migration").

- [ ] **Step 7: Commit**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git add skills/shared-references/workspace-layout.md && git commit -m "$(cat <<'EOF'
Add .job-scout/schema-version and migration scaffolding

Documents the schema-version file, the migration runner shape, and the
first-run behaviour on pre-existing workspaces. No migrations ship in
Phase 1 — the scaffolding unblocks Phase 2+ schema evolution.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 8: Push and open PR**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git push -u origin phase-1/task-05-schema-version && gh pr create --title "phase-1/05: add schema-version and migration scaffolding" --body "Part of Phase 1 (v0.4.0). See spec Component 3b."
```

---

## Task 6: Score-cache key reconciliation

**Files:**
- Modify: `/Users/tura/git/claude-job-scout/skills/job-matcher/SKILL.md`
- Modify: `/Users/tura/git/claude-job-scout/skills/match-jobs/SKILL.md`
- Modify: `/Users/tura/git/claude-job-scout/skills/check-job-notifications/SKILL.md`
- Modify: `/Users/tura/git/claude-job-scout/skills/profile-optimizer/SKILL.md`

- [ ] **Step 1: Create branch**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-1/task-06-cache-key
```

- [ ] **Step 2: Update `job-matcher/SKILL.md`**

In `/Users/tura/git/claude-job-scout/skills/job-matcher/SKILL.md`, find the "Score Caching Contract" section.

Replace:
```
Job scores are cached in `.job-scout/cache/scores.json` keyed by `(job_id, cv_hash)`. Before scoring any job:

1. Compute the cache key.
2. If a cached score exists for this `(job_id, cv_hash)` pair, **reuse it** — do not re-score. The CV hasn't changed, the job hasn't changed, the score won't change.
3. If no cached score exists, run the framework above and write the result back to `scores.json`.

This is the primary token-saving mechanism for re-runs of `/match-jobs` and the daily notifications sweep. A re-score should only happen when the CV's content hash changes (i.e., the user re-ran `/analyze-cv` on a modified CV).
```

With:
```
Job scores are cached in `.job-scout/cache/scores.json` keyed by `(job_id, cv_hash, profile_hash)`. Before scoring any job:

1. Compute the cache key from the job's `id`, the current `cv_hash`, and the current `profile_hash` (both read from `.job-scout/user-profile.json`).
2. If a cached score exists for this triple, **reuse it** — do not re-score. Neither the CV nor the LinkedIn profile has changed, so the score won't change.
3. If no cached score exists, run the framework above and write the result back to `scores.json`.

This is the primary token-saving mechanism for re-runs of `/match-jobs` and the daily notifications sweep. A re-score happens when either `cv_hash` or `profile_hash` bumps — i.e., the user re-ran `/analyze-cv` on a modified CV, or `/optimize-profile` changed the LinkedIn profile enough to shift the master keyword list.
```

- [ ] **Step 3: Update `match-jobs/SKILL.md`**

In `/Users/tura/git/claude-job-scout/skills/match-jobs/SKILL.md`, find the "Step 3" section that mentions `scores.json`.

Replace:
```
Also check `.job-scout/cache/scores.json` for cached `(job_id, cv_hash)` scores. Reuse cached scores; don't re-score unchanged jobs against an unchanged CV.
```

With:
```
Also check `.job-scout/cache/scores.json` for cached `(job_id, cv_hash, profile_hash)` scores. Reuse cached scores; don't re-score unchanged jobs against an unchanged CV and profile.
```

Find "Step 4" that mentions writing to `scores.json`. Replace:
```
Apply the job-matcher scoring framework, filter out D-Tier, and write each new score into `.job-scout/cache/scores.json`.
```

With:
```
Apply the job-matcher scoring framework, filter out D-Tier, and write each new score into `.job-scout/cache/scores.json` under the `(job_id, cv_hash, profile_hash)` key.
```

- [ ] **Step 4: Update `check-job-notifications/SKILL.md`**

In `/Users/tura/git/claude-job-scout/skills/check-job-notifications/SKILL.md`, find "Step 6" that caches scores.

Replace:
```
Load the **job-matcher** skill. Apply the scoring framework with freelance adjustments if applicable. Jobs that disclose compensation sort above same-tier jobs that don't. Cache each score in `.job-scout/cache/scores.json` keyed by `(job_id, cv_hash)`.
```

With:
```
Load the **job-matcher** skill. Apply the scoring framework with freelance adjustments if applicable. Jobs that disclose compensation sort above same-tier jobs that don't. Cache each score in `.job-scout/cache/scores.json` keyed by `(job_id, cv_hash, profile_hash)`.
```

- [ ] **Step 5: Update `profile-optimizer/SKILL.md` to write `profile_hash`**

In `/Users/tura/git/claude-job-scout/skills/profile-optimizer/SKILL.md`, find the "State & Caching" section.

Replace:
```
## State & Caching

- **`.job-scout/user-profile.json`** — source of `master_keyword_list` (built by `cv-optimizer`). Reuse it; rebuild only if `cv_hash` changed.
- **`.job-scout/cache/linkedin-profile.json`** — last-seen LinkedIn profile snapshot. If < 7 days old and the user hasn't reported edits, reuse it instead of re-reading every section via the browser. Re-evaluate only sections that changed.
```

With:
```
## State & Caching

- **`.job-scout/user-profile.json`** — source of `master_keyword_list` (built by `cv-optimizer`). Reuse it; rebuild only if `cv_hash` changed.
- **`profile_hash`** — after any write that changes `master_keyword_list` or the LinkedIn-facing content this skill proposes (headline, about, experience bullets, skills list, Open to Work config), compute a SHA-256 over the canonical JSON of those fields and persist to `.job-scout/user-profile.json` as `profile_hash`. Downstream skills (`job-matcher`) use it as part of the score-cache key, so a profile edit invalidates stale scores.
- **`.job-scout/cache/linkedin-profile.json`** — last-seen LinkedIn profile snapshot. If `last_full_read` < 7 days old and the user hasn't reported edits, reuse it instead of re-reading every section via the browser. When a fresh read is required, use per-section hashes to re-score only the sections that changed (see Component 4 of the Phase 1 design spec).
```

- [ ] **Step 6: Add one-time invalidation note to workspace-layout.md**

In `/Users/tura/git/claude-job-scout/skills/shared-references/workspace-layout.md`, under the "Schema version and migration" section added in Task 5, append this first-run note below the existing first-run block:

Replace:
```
### First-run behaviour on an already-existing `.job-scout/`

If `.job-scout/` exists but `schema-version` is missing, treat the workspace as pre-schema-versioning: write `schema-version` with `{ "version": 1, "upgraded_at": "<ISO>" }` and continue. Do not re-run any migrations.
```

With:
```
### First-run behaviour on an already-existing `.job-scout/`

If `.job-scout/` exists but `schema-version` is missing, treat the workspace as pre-schema-versioning: write `schema-version` with `{ "version": 1, "upgraded_at": "<ISO>" }` and continue. Do not re-run any migrations.

Additionally, on the first run after upgrade to v0.4.0, invalidate the score cache once: replace `.job-scout/cache/scores.json` with `{}`. Rationale: the score-cache key shape expanded from `(job_id, cv_hash)` to `(job_id, cv_hash, profile_hash)`, and old entries have no `profile_hash` dimension to match against. Users will see a one-time re-score cost on the first post-upgrade run; subsequent runs are cached normally. Record this in the `schema-version` file as `"upgraded_at"` so the invalidation does not repeat.
```

- [ ] **Step 7: Verify**

Run:
```bash
cd /Users/tura/git/claude-job-scout && grep -rn "cv_hash, profile_hash" skills/
```

Expected: matches in `job-matcher/SKILL.md`, `match-jobs/SKILL.md`, `check-job-notifications/SKILL.md`, `shared-references/workspace-layout.md`.

Run:
```bash
cd /Users/tura/git/claude-job-scout && grep -rn "(job_id, cv_hash)" skills/
```

Expected: no matches (or only matches inside historical changelogs — verify none are live instructions).

- [ ] **Step 8: Commit**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git add skills/job-matcher/SKILL.md skills/match-jobs/SKILL.md skills/check-job-notifications/SKILL.md skills/profile-optimizer/SKILL.md skills/shared-references/workspace-layout.md && git commit -m "$(cat <<'EOF'
Reconcile score-cache key to (job_id, cv_hash, profile_hash)

workspace-layout.md already declared the three-tuple; job-matcher and
two command skills used the two-tuple. Aligned all five files on the
three-tuple so a LinkedIn profile edit invalidates stale scores.
profile-optimizer now computes and writes profile_hash on any
content-changing edit. First post-upgrade run invalidates the score
cache once.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 9: Push and open PR**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git push -u origin phase-1/task-06-cache-key && gh pr create --title "phase-1/06: reconcile score-cache key to (job_id, cv_hash, profile_hash)" --body "Part of Phase 1 (v0.4.0). See spec Component 3a."
```

---

## Task 7: Tracker archival policy

**Files:**
- Modify: `/Users/tura/git/claude-job-scout/skills/shared-references/tracker-schema.md`
- Modify: `/Users/tura/git/claude-job-scout/skills/shared-references/workspace-layout.md`

- [ ] **Step 1: Create branch**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-1/task-07-tracker-archival
```

- [ ] **Step 2: Update `tracker-schema.md` shape**

In `/Users/tura/git/claude-job-scout/skills/shared-references/tracker-schema.md`, update the JSON shape block to include `last_archive_pass`.

Replace:
```json
{
  "version": 1,
  "stats": {
    "total_seen": 0,
    "applied": 0,
    "rejected": 0,
    "last_run": "2026-04-08T10:00:00Z"
  },
  "jobs": {
```

With:
```json
{
  "version": 1,
  "stats": {
    "total_seen": 0,
    "applied": 0,
    "rejected": 0,
    "last_run": "2026-04-08T10:00:00Z",
    "last_archive_pass": null
  },
  "jobs": {
```

- [ ] **Step 3: Append archival policy section to `tracker-schema.md`**

Append this to the bottom of `/Users/tura/git/claude-job-scout/skills/shared-references/tracker-schema.md`:

```markdown

## Archival policy

`tracker.json` grows monotonically and — over years of use — would become expensive to read on every dedupe pass. Aged `status: seen` entries rotate to annual archive files.

### Rules

- **Eligible for archive:** `status == "seen"` AND `last_seen` older than 60 days.
- **Not archived:** `approved`, `applied`, `rejected`. These are real artefacts of the user's search and stay in hot `tracker.json`.
- **Archive destination:** `.job-scout/archive/tracker-YYYY.json`, keyed by the year the job was `first_seen`.
- **Archive shape:** same as `tracker.json` — `{ "version": 1, "jobs": { ... } }`. No `stats` block; archive files are append-only.

### When to run

Run the archive pass at most once per calendar day per workspace. Gate via `stats.last_archive_pass` in `tracker.json`: if today's date equals the stored date, skip. Otherwise run the pass and update the field.

### Dedupe read pattern after archival

```
1. Load .job-scout/tracker.json — primary dedupe set.
2. If an id is not in hot tracker, fall through to .job-scout/archive/tracker-<current-year>.json.
3. Do NOT read older archive files during the hot path — they exist for /funnel-report (Phase 3) and manual inspection.
```

Fall-through reads are bounded to the current year because LinkedIn rarely re-posts a job id across a year boundary. If the id is truly re-posted, the (minor) cost is a re-extraction.
```

- [ ] **Step 4: Update `workspace-layout.md` canonical layout**

In `/Users/tura/git/claude-job-scout/skills/shared-references/workspace-layout.md`, locate the canonical layout block and add `archive/` alongside `reports/`, `cache/`, and `recruiters/`.

Replace:
```
  reports/              # YYYY-MM-DD-*.md run reports (notifications sweeps, match runs, CV analyses)
  cache/
```

With:
```
  reports/              # YYYY-MM-DD-*.md run reports (notifications sweeps, match runs, CV analyses)
  archive/              # tracker-YYYY.json — aged seen-status jobs rotated out of tracker.json (see tracker-schema.md)
  cache/
```

- [ ] **Step 5: Verify**

Run:
```bash
cd /Users/tura/git/claude-job-scout && grep -c "last_archive_pass" skills/shared-references/tracker-schema.md
```

Expected: at least `2`.

Run:
```bash
cd /Users/tura/git/claude-job-scout && grep -c "archive/" skills/shared-references/workspace-layout.md
```

Expected: at least `2`.

- [ ] **Step 6: Commit**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git add skills/shared-references/tracker-schema.md skills/shared-references/workspace-layout.md && git commit -m "$(cat <<'EOF'
Add tracker archival policy

Aged status:seen jobs rotate to .job-scout/archive/tracker-YYYY.json
after 60 days. Applied/approved/rejected stay in hot tracker. Dedupe
reads fall through to current-year archive only. Archive pass gated
to at most once per day via tracker.stats.last_archive_pass.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 7: Push and open PR**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git push -u origin phase-1/task-07-tracker-archival && gh pr create --title "phase-1/07: tracker archival policy" --body "Part of Phase 1 (v0.4.0). See spec Component 3c."
```

---

## Task 8: Supporting-docs index

**Files:**
- Create: `/Users/tura/git/claude-job-scout/skills/shared-references/supporting-docs.md`
- Modify: `/Users/tura/git/claude-job-scout/skills/shared-references/workspace-layout.md`

- [ ] **Step 1: Create branch**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-1/task-08-supporting-docs
```

- [ ] **Step 2: Create `supporting-docs.md`**

Create `/Users/tura/git/claude-job-scout/skills/shared-references/supporting-docs.md` with exactly:

```markdown
# Supporting-Docs Index

The user's CV is the primary input, but the README asks users to bring everything that tells their professional story: certifications, talks, decks, case studies, recommendations, publications, portfolio files. This reference documents the shared index of those documents.

## Purpose

`.job-scout/cache/supporting-docs.json` lets downstream skills (`profile-optimizer` in Phase 1; `cover-letter-writer`, ATS simulator, and `/index-docs` in later phases) read a small summary of each document instead of re-parsing the originals. Docs are keyed by path and validated by content hash.

## File location

`.job-scout/cache/supporting-docs.json`

## Shape

```json
{
  "version": 1,
  "last_scanned": "2026-04-16T10:00:00Z",
  "docs": {
    "<workspace-relative-path>": {
      "type": "cert | talk | deck | recommendation | case_study | publication | portfolio | other",
      "hash": "<sha256>",
      "extracted_keywords": [],
      "summary_200w": "...",
      "last_indexed": "2026-04-16T10:00:00Z"
    }
  }
}
```

## Type taxonomy

- **cert** — certifications, diplomas, language tests, transcripts
- **talk** — conference slides, brown-bag decks, webinar recordings (linked), transcripts
- **deck** — architecture diagrams, design docs, RFCs, whiteboard exports
- **recommendation** — testimonials, client feedback, LinkedIn recommendations, screenshots of kind words
- **case_study** — post-mortems, project retrospectives, launch reports
- **publication** — papers, blog posts, patents, package pages
- **portfolio** — product screenshots, portfolio PDFs, media mentions
- **other** — catch-all; ask the user to re-categorise on next interactive pass

## When the index is built

On workspace bootstrap (first command invocation in a new workspace), after the `.job-scout/` folder is created, scan the workspace root (not `.job-scout/` itself) for files matching common supporting-doc extensions: `.pdf`, `.docx`, `.doc`, `.pptx`, `.key`, `.png`, `.jpg`, `.md`, `.txt`.

Exclude:
- The CV file itself (identified by the `cv.*`, `resume.*`, `curriculum.*` pattern or the path stored in `user-profile.json`).
- Anything inside `.job-scout/`, `.git/`, `node_modules/`, or any dotted directory.

Ask the user **once**:

> "I noticed these files in your workspace alongside the CV: [list first 10, summarise the rest]. They look like supporting materials — certificates, talks, case studies — that make every rewrite sharper. Want me to index them now? This is cached; I only re-read if a file's contents change."

On approval: read each file, classify by filename heuristics (e.g., `cert*.pdf` → `cert`, `*talk*.pdf` → `talk`, `*recommendation*` → `recommendation`), fall back to content inspection for the first N files where heuristics are inconclusive, and write the index. Generate a 200-word summary per doc. Compute SHA-256 over each file's bytes.

On decline: write an empty `docs: {}` with `last_scanned` set and do not prompt again in the same session.

## Re-indexing

On every command entry, re-scan the workspace:

1. Compare the file list against `docs` in the index.
2. For new files: classify, summarise, add to index.
3. For existing files: hash the content. If hash differs from stored hash, re-classify and re-summarise. Otherwise reuse.
4. For missing files: mark the entry with `"status": "missing"` but do not delete — the user may have moved the file temporarily.

Re-scans should be non-blocking: if a downstream skill needs the index immediately and the scan hasn't finished, the skill proceeds with whatever is already in the index and logs a warning.

## Consumer contract

Any skill reading `supporting-docs.json` must:

- Read the index, not the source files, for keyword and summary data.
- Cite the `path` when a claim on a CV or LinkedIn section derives from a specific doc (Phase 2 introduces this explicitly in `profile-optimizer` for the Featured section).
- Treat `type: "other"` as "ask the user before acting on this."

## Phase-1 scope

Phase 1 establishes the index and the workspace-scan/prompt behaviour. No consumer skill in Phase 1 is required to read it; the first consumer lands in Phase 2. Building the data now avoids backfilling later.
```

- [ ] **Step 3: Update `workspace-layout.md` bootstrap to add the supporting-docs scan**

In `/Users/tura/git/claude-job-scout/skills/shared-references/workspace-layout.md`, find the bootstrap procedure step 4 (already updated in Task 5).

Replace:
```
4. **On approval:** create the folder and the `reports/`, `cache/`, `recruiters/`, and `archive/` subfolders. Write:
   - `schema-version` with `{ "version": 1, "upgraded_at": "<ISO>" }`.
   - A stub `user-profile.json` with `{ "created": "<ISO date>", "discovery_complete": false }`.
   - An empty `tracker.json` with `{ "version": 1, "jobs": {}, "stats": { "total_seen": 0, "applied": 0, "rejected": 0 }, "last_archive_pass": null }`.
```

With:
```
4. **On approval:** create the folder and the `reports/`, `cache/`, `recruiters/`, and `archive/` subfolders. Write:
   - `schema-version` with `{ "version": 1, "upgraded_at": "<ISO>" }`.
   - A stub `user-profile.json` with `{ "created": "<ISO date>", "discovery_complete": false }`.
   - An empty `tracker.json` with `{ "version": 1, "jobs": {}, "stats": { "total_seen": 0, "applied": 0, "rejected": 0 }, "last_archive_pass": null }`.
   - An empty `cache/supporting-docs.json` with `{ "version": 1, "last_scanned": null, "docs": {} }`.

   Then run the supporting-docs scan described in `supporting-docs.md` — this is a one-time prompt per workspace and does not block the command that triggered the bootstrap.
```

- [ ] **Step 4: Update workspace-layout.md canonical layout to list supporting-docs.json**

In `/Users/tura/git/claude-job-scout/skills/shared-references/workspace-layout.md`, canonical layout block, inside the `cache/` subsection. Replace:

```
  cache/
    cv-<hash>.json          # parsed CV text + extracted keywords, keyed by file content hash
    cv-analysis-<hash>.json # full cv-optimizer scoring output, keyed by content hash
    scores.json             # job scores keyed by (job_id, cv_hash, profile_hash)
    linkedin-profile.json   # last-seen snapshot of the user's LinkedIn profile
```

With:
```
  cache/
    cv-<hash>.json          # parsed CV text + extracted keywords, keyed by file content hash
    cv-analysis-<hash>.json # full cv-optimizer scoring output, keyed by content hash
    scores.json             # job scores keyed by (job_id, cv_hash, profile_hash)
    linkedin-profile.json   # last-seen snapshot of the user's LinkedIn profile
    supporting-docs.json    # index of non-CV workspace docs (see supporting-docs.md)
```

- [ ] **Step 5: Verify**

Run:
```bash
cd /Users/tura/git/claude-job-scout && ls skills/shared-references/supporting-docs.md
```

Expected: file exists.

Run:
```bash
cd /Users/tura/git/claude-job-scout && grep -c "supporting-docs" skills/shared-references/workspace-layout.md
```

Expected: at least `2`.

- [ ] **Step 6: Commit**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git add skills/shared-references/supporting-docs.md skills/shared-references/workspace-layout.md && git commit -m "$(cat <<'EOF'
Add supporting-docs index and workspace-bootstrap scan

Shared reference describing .job-scout/cache/supporting-docs.json: type
taxonomy, scan-on-bootstrap behaviour, hash-based re-indexing, and the
consumer contract. Workspace-layout bootstrap now creates an empty
supporting-docs.json and runs the non-blocking scan after folder
creation. No Phase 1 consumer reads the index — first consumer lands
in Phase 2.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 7: Push and open PR**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git push -u origin phase-1/task-08-supporting-docs && gh pr create --title "phase-1/08: supporting-docs index + bootstrap scan" --body "Part of Phase 1 (v0.4.0). See spec Component 3d."
```

---

## Task 9: Delta-aware LinkedIn snapshot

**Files:**
- Modify: `/Users/tura/git/claude-job-scout/skills/profile-optimizer/SKILL.md`
- Modify: `/Users/tura/git/claude-job-scout/skills/optimize-profile/SKILL.md`

- [ ] **Step 1: Create branch**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-1/task-09-delta-snapshot
```

- [ ] **Step 2: Update `profile-optimizer/SKILL.md` State & Caching section**

In `/Users/tura/git/claude-job-scout/skills/profile-optimizer/SKILL.md`, find the "State & Caching" block (already modified in Task 6 to add `profile_hash`).

Replace the `linkedin-profile.json` bullet with:
```
- **`.job-scout/cache/linkedin-profile.json`** — last-seen LinkedIn profile snapshot with per-section content hashes. Shape:
  ```json
  {
    "version": 1,
    "last_full_read": "<ISO>",
    "sections": {
      "headline":  { "content": "...", "hash": "<sha256>", "scored_at": "<ISO>" },
      "about":     { "content": "...", "hash": "<sha256>", "scored_at": "<ISO>" },
      "experience_<role_id>": { "content": "...", "hash": "<sha256>", "scored_at": "<ISO>" },
      "skills":    { "content": [...], "hash": "<sha256>", "scored_at": "<ISO>" },
      "featured":  { "content": [...], "hash": "<sha256>", "scored_at": "<ISO>" },
      "..."
    }
  }
  ```
  
  **Two-tier reuse:**
  1. **Outer gate (cheap):** if `last_full_read < 7 days ago` and the user hasn't indicated edits, skip the browser read entirely and reuse all cached scores.
  2. **Inner gate (new):** when the outer gate fails and a browser read runs, hash each section's freshly-read content and compare against the stored hash. Matching hashes → reuse the cached score for that section. Differing hashes → re-score only that section. Update hashes and `last_full_read` after the read completes.
```

- [ ] **Step 3: Update `optimize-profile/SKILL.md` Step 2**

In `/Users/tura/git/claude-job-scout/skills/optimize-profile/SKILL.md`, find "Step 2: Read LinkedIn Profile (with diff cache)".

Replace:
```
## Step 2: Read LinkedIn Profile (with diff cache)

Check `.job-scout/cache/linkedin-profile.json`. If the snapshot is < 7 days old AND the user has not indicated they edited the profile since, reuse it instead of re-reading every section via the browser.

If a fresh read is needed, navigate to the user's LinkedIn profile and read all sections: headline, about, experience, education, skills, featured, certifications, recommendations. Also check: custom URL, location field, industry field, profile photo, banner image, Open to Work status, creator mode status. Write the result back to `.job-scout/cache/linkedin-profile.json` with a timestamp.
```

With:
```
## Step 2: Read LinkedIn Profile (two-tier cache)

Check `.job-scout/cache/linkedin-profile.json`.

**Outer gate:** if `last_full_read` is < 7 days ago AND the user has not indicated edits, skip the browser read entirely and reuse all cached section scores from Step 4.

**Inner gate:** otherwise, navigate to the user's LinkedIn profile and read all sections: headline, about, each experience entry, education, skills, featured, certifications, recommendations, plus custom URL, location, industry, profile photo, banner image, Open to Work status, creator mode status.

For each section just read:
1. Compute SHA-256 over a canonical serialisation of the section content.
2. Compare to the stored hash in the cache.
3. If the hash matches the cached hash, reuse the cached score for that section.
4. If the hash differs, mark the section "needs re-score" for Step 4.

After the read, update each section's `content`, `hash`, and `scored_at` in `.job-scout/cache/linkedin-profile.json`. Update `last_full_read` to the current ISO timestamp. See `profile-optimizer` "State & Caching" for the full cache shape.
```

- [ ] **Step 4: Update Step 4 to respect the re-score flags**

In `/Users/tura/git/claude-job-scout/skills/optimize-profile/SKILL.md`, find "Step 4: Analyze and Score".

Prepend this paragraph before the existing "**Section scores (1-10 each):**" bullet:
```
Only re-score sections marked "needs re-score" by Step 2. Sections with unchanged hashes reuse their cached score directly. Cross-cutting scores (keyword coverage, search appearance, 10-second test, CV alignment) always recompute — they're cheap and depend on the whole profile.
```

- [ ] **Step 5: Verify**

Run:
```bash
cd /Users/tura/git/claude-job-scout && grep -c "last_full_read" skills/profile-optimizer/SKILL.md skills/optimize-profile/SKILL.md
```

Expected: at least `3` matches total.

Run:
```bash
cd /Users/tura/git/claude-job-scout && grep -c "needs re-score" skills/optimize-profile/SKILL.md
```

Expected: at least `2`.

- [ ] **Step 6: Commit**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git add skills/profile-optimizer/SKILL.md skills/optimize-profile/SKILL.md && git commit -m "$(cat <<'EOF'
Delta-aware LinkedIn profile snapshot cache

Adds per-section content hashes to linkedin-profile.json. The existing
7-day outer gate still skips browser reads entirely. When the outer
gate fails and a browser read does run, matching section hashes let us
reuse cached section scores; only changed sections re-score. Makes the
expensive LLM-side scoring incremental across the 7-day boundary.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 7: Push and open PR**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git push -u origin phase-1/task-09-delta-snapshot && gh pr create --title "phase-1/09: delta-aware LinkedIn snapshot" --body "Part of Phase 1 (v0.4.0). See spec Component 4."
```

---

## Task 10: Progressive disclosure split of `cv-optimizer`

**Files:**
- Modify: `/Users/tura/git/claude-job-scout/skills/cv-optimizer/SKILL.md`
- Create: `/Users/tura/git/claude-job-scout/skills/cv-optimizer/references/phase-0-discovery-interview.md`
- Create: `/Users/tura/git/claude-job-scout/skills/cv-optimizer/references/phase-1-seven-dimension-scoring.md`
- Create: `/Users/tura/git/claude-job-scout/skills/cv-optimizer/references/phase-2-gap-analysis.md`
- Create: `/Users/tura/git/claude-job-scout/skills/cv-optimizer/references/phase-3-optimized-rewrite.md`
- Create: `/Users/tura/git/claude-job-scout/skills/cv-optimizer/references/phase-4-output-deliverables.md`

- [ ] **Step 1: Create branch and snapshot the current SKILL.md**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-1/task-10-cv-optimizer-split
```

Run (to have a backup of the original for verification later — not committed):
```bash
cd /Users/tura/git/claude-job-scout && cp skills/cv-optimizer/SKILL.md /tmp/cv-optimizer-SKILL-original.md
```

- [ ] **Step 2: Create `phase-0-discovery-interview.md`**

Create `/Users/tura/git/claude-job-scout/skills/cv-optimizer/references/phase-0-discovery-interview.md` by extracting the current `## Phase 0 — Discovery Interview (MANDATORY)` block from `cv-optimizer/SKILL.md` (everything from `## Phase 0 — Discovery Interview` through to just before `## Phase 1 — Deep Analysis`).

Wrap with a top-of-file header:
```markdown
# Phase 0 — Discovery Interview

Loaded on demand by `cv-optimizer/SKILL.md` when the user's `.job-scout/user-profile.json` has `discovery_complete != true`. Skip if the user has already completed discovery.

---

<< EXTRACTED CONTENT FROM SKILL.md — everything under "## Phase 0 — Discovery Interview" >>
```

Specifically: copy the block that begins with `Before analysing anything, gather the context needed to get it right first time.` through the `---` separator before `## Phase 1 — Deep Analysis`.

- [ ] **Step 3: Create `phase-1-seven-dimension-scoring.md`**

Create `/Users/tura/git/claude-job-scout/skills/cv-optimizer/references/phase-1-seven-dimension-scoring.md` by extracting the `## Phase 1 — Deep Analysis` block (including the seven dimension sub-sections) from `cv-optimizer/SKILL.md`.

Top-of-file header:
```markdown
# Phase 1 — Deep Analysis (Seven-Dimension Scoring)

Loaded on demand by `cv-optimizer/SKILL.md` during the scoring phase. Covers dimensions 1-7 with weights, inline examples, and references to `psychology-cheatsheet.md`, `action-verbs.md`, and `ats-keywords.md`.

---

<< EXTRACTED CONTENT FROM SKILL.md — everything under "## Phase 1 — Deep Analysis" up to but not including "## Phase 2 — Scoring & Gap Analysis" >>
```

- [ ] **Step 4: Create `phase-2-gap-analysis.md`**

Create `/Users/tura/git/claude-job-scout/skills/cv-optimizer/references/phase-2-gap-analysis.md` by extracting the `## Phase 2 — Scoring & Gap Analysis` block.

Top-of-file header:
```markdown
# Phase 2 — Scoring & Gap Analysis

Loaded on demand by `cv-optimizer/SKILL.md` after Phase 1 analysis completes. Takes the per-dimension scores, computes the weighted overall, grades, identifies top-5 improvements, and surfaces the strength spotlight.

---

<< EXTRACTED CONTENT FROM SKILL.md — everything under "## Phase 2 — Scoring & Gap Analysis" up to but not including "## Phase 3 — Optimized Rewrite" >>
```

- [ ] **Step 5: Create `phase-3-optimized-rewrite.md`**

Create `/Users/tura/git/claude-job-scout/skills/cv-optimizer/references/phase-3-optimized-rewrite.md` by extracting the `## Phase 3 — Optimized Rewrite` block including the `### Rewrite Rules`, `### SPAR Bullet Formula`, and `### Professional Summary Template` subsections.

Top-of-file header:
```markdown
# Phase 3 — Optimized Rewrite

Loaded on demand by `cv-optimizer/SKILL.md` when the user asks for a rewrite. Contains SPAR rules, the bullet formula, and the professional summary template. For per-role parallel rewrite, see `cv-section-rewriter/SKILL.md`.

---

<< EXTRACTED CONTENT FROM SKILL.md — everything under "## Phase 3 — Optimized Rewrite" up to but not including "## Phase 4 — Output Deliverables" >>
```

- [ ] **Step 6: Create `phase-4-output-deliverables.md`**

Create `/Users/tura/git/claude-job-scout/skills/cv-optimizer/references/phase-4-output-deliverables.md` by extracting the `## Phase 4 — Output Deliverables` block.

Top-of-file header:
```markdown
# Phase 4 — Output Deliverables

Loaded on demand by `cv-optimizer/SKILL.md` at the end of a run. Describes the six artefacts produced: scored analysis, top-5 improvements, optimized CV, master keyword list, before/after comparisons, and interview ammunition.

---

<< EXTRACTED CONTENT FROM SKILL.md — everything under "## Phase 4 — Output Deliverables" up to but not including "## ATS Keyword Strategy" >>
```

- [ ] **Step 7: Rewrite `cv-optimizer/SKILL.md` as a lean orchestrator**

Overwrite `/Users/tura/git/claude-job-scout/skills/cv-optimizer/SKILL.md` with exactly:

```markdown
---
name: cv-optimizer
description: >
  This skill should be used when the user asks to "analyze my CV", "improve my resume",
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
| 3 | Optimized rewrite | `references/phase-3-optimized-rewrite.md` | User requests a rewrite |
| 4 | Output deliverables | `references/phase-4-output-deliverables.md` | Always at end |

**Rule:** do not load a phase reference until its gate is reached. Loading all phase references up front is the anti-pattern this orchestrator exists to prevent.

## Caching contract

Both the parsed CV and the full analysis output are cached by content hash:

- **`.job-scout/cache/cv-<hash>.json`** — parsed CV text + extracted keyword list. Written on first parse.
- **`.job-scout/cache/cv-analysis-<hash>.json`** — the full Phase 1–2 scoring output. Written on first analysis.

Before re-running any phase, compute the CV's content hash and check the cache. If a hit exists and the user hasn't asked for a fresh run, return the cached result. The `master_keyword_list` and `cv_summary` are also persisted to `.job-scout/user-profile.json` for downstream skills (`profile-optimizer`, `job-matcher`) to reuse without ever re-parsing the CV.

The Phase 0 discovery interview only runs when `user-profile.json.discovery_complete != true`. Once complete, subsequent runs skip straight to analysis.

## Freelance / Contractor mode

When the user's profile indicates freelance/contract work, apply adjustments from `../shared-references/freelance-context.md`:
- Project-based layout preferred over employer-based
- Skills matrix at top for quick scanning
- Returning clients or extended contracts signal reliability (social proof + authority)
- Include availability date, day-rate range (optional), IR35 awareness

## Parallel rewrite (Phase 3)

When Phase 3 runs, the orchestrator may dispatch one subagent per role section to `cv-section-rewriter/SKILL.md`, following the contract in `../shared-references/subagent-protocol.md`. Main thread assembles the final document from deltas.

## Reference Materials

- **`references/phase-0-discovery-interview.md`** — Phase 0 content (lazy)
- **`references/phase-1-seven-dimension-scoring.md`** — Phase 1 content (lazy)
- **`references/phase-2-gap-analysis.md`** — Phase 2 content (lazy)
- **`references/phase-3-optimized-rewrite.md`** — Phase 3 content (lazy)
- **`references/phase-4-output-deliverables.md`** — Phase 4 content (lazy)
- **`references/ats-keywords.md`** — ATS keyword categories by industry
- **`references/action-verbs.md`** — Categorized action verbs
- **`references/psychology-cheatsheet.md`** — Quick-reference for persuasion techniques
- **`../shared-references/freelance-context.md`** — Freelance CV structure
- **`../shared-references/workspace-layout.md`** — `.job-scout/` layout and bootstrap
- **`../shared-references/cv-loading.md`** — CV loading + caching procedure
- **`../shared-references/subagent-protocol.md`** — Subagent dispatch contract (for Phase 3 parallel rewrite)
```

- [ ] **Step 8: Verify the split preserved content**

Run:
```bash
cd /Users/tura/git/claude-job-scout && wc -c skills/cv-optimizer/SKILL.md
```

Expected: roughly 3KB-4KB (was ~14KB).

Run:
```bash
cd /Users/tura/git/claude-job-scout && wc -c skills/cv-optimizer/references/phase-*.md
```

Expected: five files, each with non-trivial size. Sum of file sizes should be at least 10KB.

Run:
```bash
cd /Users/tura/git/claude-job-scout && grep -l "SPAR" skills/cv-optimizer/
```

Expected: `skills/cv-optimizer/SKILL.md` AND `skills/cv-optimizer/references/phase-1-seven-dimension-scoring.md` AND `skills/cv-optimizer/references/phase-3-optimized-rewrite.md` — SPAR appears in the orchestrator overview and in the two phases where it's actually used.

Run:
```bash
cd /Users/tura/git/claude-job-scout && diff -q /tmp/cv-optimizer-SKILL-original.md skills/cv-optimizer/SKILL.md
```

Expected: files differ (the split is the intent).

- [ ] **Step 9: Manual read-through check**

Manually read through each phase reference file and confirm:
- Phase 0 reference contains all original Phase 0 content.
- Phase 1 reference contains all seven dimension sub-sections.
- Phase 2 reference contains the scoring & gap analysis block.
- Phase 3 reference contains rewrite rules, SPAR formula, and summary template.
- Phase 4 reference contains the six deliverables list.

No content dropped. No content duplicated across reference files. The orchestrator's phase table is the only place phases are summarised.

- [ ] **Step 10: Commit**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git add skills/cv-optimizer/ && git commit -m "$(cat <<'EOF'
Split cv-optimizer into orchestrator + lazy-loaded phase references

SKILL.md was 14KB of phase content loaded in full on every trigger.
Now 3-4KB: phase sequence, gates, caching contract, freelance mode,
and pointers to five new references/phase-N-*.md files. Each phase
loads only when its gate fires. SPAR rules, the seven-dimension
scoring, and the deliverables list all preserved verbatim, just
relocated.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 11: Push and open PR**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git push -u origin phase-1/task-10-cv-optimizer-split && gh pr create --title "phase-1/10: cv-optimizer progressive disclosure split" --body "Part of Phase 1 (v0.4.0). See spec Component 2."
```

---

## Task 11: Progressive disclosure split of `profile-optimizer`

**Files:**
- Modify: `/Users/tura/git/claude-job-scout/skills/profile-optimizer/SKILL.md`
- Create: `/Users/tura/git/claude-job-scout/skills/profile-optimizer/references/sections/headline.md`
- Create: `/Users/tura/git/claude-job-scout/skills/profile-optimizer/references/sections/about.md`
- Create: `/Users/tura/git/claude-job-scout/skills/profile-optimizer/references/sections/experience.md`
- Create: `/Users/tura/git/claude-job-scout/skills/profile-optimizer/references/sections/skills.md`
- Create: `/Users/tura/git/claude-job-scout/skills/profile-optimizer/references/sections/featured.md`
- Create: `/Users/tura/git/claude-job-scout/skills/profile-optimizer/references/sections/additional.md`
- Create: `/Users/tura/git/claude-job-scout/skills/profile-optimizer/references/sections/open-to-work.md`
- Create: `/Users/tura/git/claude-job-scout/skills/profile-optimizer/references/sections/structured-fields.md`
- Create: `/Users/tura/git/claude-job-scout/skills/profile-optimizer/references/activity-engagement.md`
- Create: `/Users/tura/git/claude-job-scout/skills/profile-optimizer/references/scoring-framework.md`

- [ ] **Step 1: Create branch and snapshot**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-1/task-11-profile-optimizer-split
```

Run:
```bash
cd /Users/tura/git/claude-job-scout && cp skills/profile-optimizer/SKILL.md /tmp/profile-optimizer-SKILL-original.md
```

- [ ] **Step 2: Create `sections/headline.md`**

Create `/Users/tura/git/claude-job-scout/skills/profile-optimizer/references/sections/headline.md` by extracting the `### 1. Headline (Critical — 220 characters)` block from `profile-optimizer/SKILL.md`.

Wrap:
```markdown
# Headline Section

Loaded on demand by `profile-optimizer/SKILL.md` when proposing or re-scoring the headline section.

---

<< EXTRACTED CONTENT FROM SKILL.md — the "### 1. Headline" block, including the example derivation >>
```

- [ ] **Step 3: Create `sections/about.md`**

Extract the `### 2. About / Summary (200-400 words)` block to `sections/about.md` with matching header wrapper.

- [ ] **Step 4: Create `sections/experience.md`**

Extract the `### 3. Experience` block to `sections/experience.md`.

- [ ] **Step 5: Create `sections/skills.md`**

Extract the `### 4. Skills & Endorsements` block to `sections/skills.md`.

- [ ] **Step 6: Create `sections/featured.md`**

Extract the `### 5. Featured Section` block to `sections/featured.md`.

- [ ] **Step 7: Create `sections/additional.md`**

Extract the `### 6. Additional Sections` block to `sections/additional.md`.

- [ ] **Step 8: Create `sections/open-to-work.md`**

Extract the `### 7. Open to Work Signal` block to `sections/open-to-work.md`. (This is distinct from `references/open-to-work-config.md` which already exists — the new sections file is the "how to propose" content; the existing config file is the "step-by-step setup" content. Cross-reference both.)

- [ ] **Step 9: Create `sections/structured-fields.md`**

Extract the `### 8. Structured Profile Fields` block to `sections/structured-fields.md`.

- [ ] **Step 10: Create `activity-engagement.md`**

Extract the `## Activity & Engagement Layer` block (SSI, content strategy, creator mode) to `references/activity-engagement.md`.

- [ ] **Step 11: Create `scoring-framework.md`**

Extract the `## Scoring Framework` block (section scores, cross-cutting scores, overall score) to `references/scoring-framework.md`. Keep the Profile-vs-CV Alignment content in the orchestrator (small section, always needed).

- [ ] **Step 12: Rewrite `profile-optimizer/SKILL.md` as a lean orchestrator**

Overwrite `/Users/tura/git/claude-job-scout/skills/profile-optimizer/SKILL.md` with exactly:

```markdown
---
name: profile-optimizer
description: >
  This skill should be used when the user asks to "optimize my LinkedIn profile",
  "improve my LinkedIn", "make my profile stand out", "update my LinkedIn headline",
  "rewrite my LinkedIn summary", "LinkedIn SEO", "attract recruiters on LinkedIn",
  or needs guidance on making their LinkedIn profile more visible to recruiters
  and ATS systems. Also triggers when aligning a LinkedIn profile with a CV.
version: 0.4.0
---

# LinkedIn Profile Optimizer (Orchestrator)

Analyze and enhance LinkedIn profiles to maximize recruiter visibility and ATS compatibility. **The user's CV is the primary input** — every section proposal is derived from CV content.

This file is the **orchestrator**: it names the section list, the caching contract, the alignment report, and the lazy-loaded reference for each section. Section content lives in `references/sections/*.md` and is loaded only when that section is proposed, scored, or re-scored.

## CV requirement

The CV is mandatory. If no CV is found in the workspace:
1. Ask the user to provide their CV (upload, paste, or point to a file path).
2. Do not proceed until the CV is loaded — it drives all content proposals.

Once loaded, extract: role titles, seniority level, key skills, quantified achievements, industry/domain context, career narrative.

**Master keyword list:** Reuse the list from `user-profile.json` → `master_keyword_list` (produced by `cv-optimizer`). If it doesn't exist, build it from the CV.

## Section sequence

Each section gets its own lazy-loaded reference. Load a section's reference only when that section is about to be proposed or re-scored (see Component 4 delta-aware snapshot in the Phase 1 spec).

| Section | Reference |
|---------|-----------|
| 1. Headline (220 chars) | `references/sections/headline.md` |
| 2. About / Summary (200-400 words) | `references/sections/about.md` |
| 3. Experience | `references/sections/experience.md` |
| 4. Skills & Endorsements | `references/sections/skills.md` |
| 5. Featured Section | `references/sections/featured.md` |
| 6. Additional Sections | `references/sections/additional.md` |
| 7. Open to Work Signal | `references/sections/open-to-work.md` + `references/open-to-work-config.md` |
| 8. Structured Profile Fields | `references/sections/structured-fields.md` |

## Activity & engagement layer

Static profile content is necessary but not sufficient. The LinkedIn algorithm rewards active profiles. Load `references/activity-engagement.md` when the user wants advice on SSI, posting cadence, or creator mode.

## Cross-platform keyword consistency

### Google discoverability

LinkedIn profiles rank high on Google for name searches. Ensure headline + About first 3 lines work as a compelling Google snippet. Include location and role in headline so Google queries like "John Smith data engineer London" return the profile.

### Job-board keyword sync

Extract exact phrasing from target job descriptions (not just generic terms). Recruiters search LinkedIn with the same terms they put in their own JDs. Exact-match phrases matter.

### Recruiter Boolean search simulation

Construct likely Boolean queries a recruiter would run for the user's target role based on `references/recruiter-search-patterns.md`. Verify the profile would surface (all required keywords present, in searchable fields).

## Scoring framework

Load `references/scoring-framework.md` when computing scores. It covers per-section scoring, cross-cutting scores (keyword coverage, search appearance, 10-second test, CV alignment), and the weighted overall score.

## Profile vs CV alignment

After proposing all content, generate an alignment report:
- Dates, titles, and companies must match exactly between CV and LinkedIn.
- Every keyword on the master keyword list must appear somewhere on the LinkedIn profile.
- Flag CV achievements not represented on LinkedIn.
- Flag LinkedIn content that contradicts or isn't supported by the CV.
- Tone shift is expected: CV formal/concise → LinkedIn conversational/first-person.

## Optimization process

1. **Load CV** — follow `shared-references/cv-loading.md`. Reuse `master_keyword_list` from `user-profile.json` if available.
2. **Read current LinkedIn profile** via browser — use the two-tier cache (see "State & Caching" below). Score each section (1-10).
3. **Check structured fields** — location, industry, custom URL, photo, banner, Open to Work status.
4. **Check activity & engagement** — SSI score, recent posting activity, creator mode status.
5. **Run Boolean search simulation** — would a recruiter find this profile?
6. **Generate section-by-section proposals** — ready-to-paste content derived from CV. For each section scoring below 8, load that section's reference and generate proposals.
7. **Calculate all scores** — load `scoring-framework.md` and compute section + cross-cutting + overall.
8. **Present before/after comparison** for each section with the CV source highlighted.
9. **Show alignment report** — keyword coverage, missing achievements, discrepancies.
10. **Apply changes** via browser with user permission — one section at a time.

## State & caching

- **`.job-scout/user-profile.json`** — source of `master_keyword_list` (built by `cv-optimizer`). Reuse it; rebuild only if `cv_hash` changed.
- **`profile_hash`** — after any write that changes `master_keyword_list` or the LinkedIn-facing content this skill proposes (headline, about, experience bullets, skills list, Open to Work config), compute a SHA-256 over the canonical JSON of those fields and persist to `.job-scout/user-profile.json` as `profile_hash`. Downstream skills (`job-matcher`) use it as part of the score-cache key, so a profile edit invalidates stale scores.
- **`.job-scout/cache/linkedin-profile.json`** — last-seen LinkedIn profile snapshot with per-section content hashes. Shape:
  ```json
  {
    "version": 1,
    "last_full_read": "<ISO>",
    "sections": {
      "headline":  { "content": "...", "hash": "<sha256>", "scored_at": "<ISO>" },
      "about":     { "content": "...", "hash": "<sha256>", "scored_at": "<ISO>" },
      "experience_<role_id>": { "content": "...", "hash": "<sha256>", "scored_at": "<ISO>" },
      "skills":    { "content": [...], "hash": "<sha256>", "scored_at": "<ISO>" },
      "featured":  { "content": [...], "hash": "<sha256>", "scored_at": "<ISO>" }
    }
  }
  ```
  
  **Two-tier reuse:**
  1. **Outer gate (cheap):** if `last_full_read < 7 days ago` and the user hasn't indicated edits, skip the browser read entirely and reuse all cached scores.
  2. **Inner gate:** when the outer gate fails and a browser read runs, hash each section's freshly-read content and compare against the stored hash. Matching hashes → reuse the cached score for that section. Differing hashes → re-score only that section.

## Reference Materials

- **`references/sections/*.md`** — one file per profile section (lazy-loaded)
- **`references/activity-engagement.md`** — SSI, content strategy, creator mode (lazy-loaded)
- **`references/scoring-framework.md`** — section + cross-cutting scoring (lazy-loaded)
- **`references/linkedin-seo.md`** — Algorithm factors, keyword strategy, recruiter behaviour
- **`references/headline-formulas.md`** — Headline templates by role
- **`references/recruiter-search-patterns.md`** — Boolean queries, title mappings
- **`references/open-to-work-config.md`** — Open to Work setup guide
- **`../shared-references/workspace-layout.md`** — `.job-scout/` folder layout and bootstrap
- **`../shared-references/cv-loading.md`** — CV loading + caching procedure
- **`../shared-references/subagent-protocol.md`** — Subagent dispatch contract
```

- [ ] **Step 13: Verify the split**

Run:
```bash
cd /Users/tura/git/claude-job-scout && wc -c skills/profile-optimizer/SKILL.md
```

Expected: roughly 4KB-5KB (was ~13KB).

Run:
```bash
cd /Users/tura/git/claude-job-scout && ls skills/profile-optimizer/references/sections/ | wc -l
```

Expected: `8`.

Run:
```bash
cd /Users/tura/git/claude-job-scout && diff -q /tmp/profile-optimizer-SKILL-original.md skills/profile-optimizer/SKILL.md
```

Expected: files differ.

- [ ] **Step 14: Manual read-through**

Read each sections/*.md to confirm no content was dropped from the original SKILL.md and no content is duplicated between reference files.

- [ ] **Step 15: Commit**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git add skills/profile-optimizer/ && git commit -m "$(cat <<'EOF'
Split profile-optimizer into orchestrator + lazy-loaded section refs

SKILL.md was 13KB with full section content loaded in full on every
trigger. Now 4-5KB: section list, caching contract (two-tier snapshot),
process, and pointers to eight new sections/*.md references plus
activity-engagement.md and scoring-framework.md. Each section's
content loads only when that section is proposed or re-scored.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 16: Push and open PR**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git push -u origin phase-1/task-11-profile-optimizer-split && gh pr create --title "phase-1/11: profile-optimizer progressive disclosure split" --body "Part of Phase 1 (v0.4.0). See spec Component 2."
```

---

## Task 12: Parallel job scoring

**Files:**
- Modify: `/Users/tura/git/claude-job-scout/skills/match-jobs/SKILL.md`
- Modify: `/Users/tura/git/claude-job-scout/skills/check-job-notifications/SKILL.md`

- [ ] **Step 1: Create branch**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-1/task-12-parallel-scoring
```

- [ ] **Step 2: Update `match-jobs/SKILL.md` Step 4**

In `/Users/tura/git/claude-job-scout/skills/match-jobs/SKILL.md`, find the "Step 4: Extract and score new jobs" section (note: the file has two "Step 4" headers — this change is for the first one, about extract-and-score, not the "Present Results" one).

Replace:
```
## Step 4: Extract and score new jobs

For each *new* job, extract title, company, location, salary, experience level, required/preferred skills, description, Easy Apply status, posting date, applicant count. Apply the job-matcher scoring framework, filter out D-Tier, and write each new score into `.job-scout/cache/scores.json` under the `(job_id, cv_hash, profile_hash)` key.
```

With:
```
## Step 4: Extract and score new jobs (parallel)

For each *new* job, extract title, company, location, salary, experience level, required/preferred skills, description, Easy Apply status, posting date, applicant count.

**Scoring fan-out:** batch the new jobs into groups of 5 (the last batch may be smaller). For each batch, dispatch one subagent per the contract in `../shared-references/subagent-protocol.md`:

```json
{
  "task": "score-job-batch",
  "inputs": {
    "jobs": [ /* extracted job blobs */ ],
    "user_profile": { "cv_summary": ..., "requirements": ..., "master_keyword_list": ... },
    "cv_hash": "...",
    "profile_hash": "..."
  },
  "budget_lines": 200,
  "allowed_tools": ["Read"]
}
```

The subagent loads the `job-matcher` skill, scores each job, returns deltas:

```json
{
  "status": "ok",
  "deltas": [
    { "job_id": "...", "score": 87, "tier": "A", "breakdown": { /* per-dimension */ } }
  ]
}
```

Main thread collects all deltas, filters out D-Tier, and writes each score into `.job-scout/cache/scores.json` under the `(job_id, cv_hash, profile_hash)` key.

**Fallback:** if the `Agent` tool is unavailable in this session, fall back to sequential in-thread scoring using the same job-matcher framework. Log the fallback.
```

- [ ] **Step 3: Update `check-job-notifications/SKILL.md` Step 6**

In `/Users/tura/git/claude-job-scout/skills/check-job-notifications/SKILL.md`, find "Step 6: Score and rank".

Replace:
```
## Step 6: Score and rank

Load the **job-matcher** skill. Apply the scoring framework with freelance adjustments if applicable. Jobs that disclose compensation sort above same-tier jobs that don't. Cache each score in `.job-scout/cache/scores.json` keyed by `(job_id, cv_hash, profile_hash)`.

Tiers: **A (85-100)** apply immediately, **B (70-84)** worth applying, **C (55-69)** consider, **D (<55)** discard.
```

With:
```
## Step 6: Score and rank (parallel)

Apply the job-matcher scoring framework with freelance adjustments if applicable. Jobs that disclose compensation sort above same-tier jobs that don't.

**Scoring fan-out:** batch the new jobs into groups of 5 and dispatch one subagent per batch per the contract in `../shared-references/subagent-protocol.md`:

```json
{
  "task": "score-job-batch",
  "inputs": {
    "jobs": [ /* extracted job blobs */ ],
    "user_profile": { "cv_summary": ..., "requirements": ..., "master_keyword_list": ... },
    "cv_hash": "...",
    "profile_hash": "..."
  },
  "budget_lines": 200,
  "allowed_tools": ["Read"]
}
```

Each subagent loads the `job-matcher` skill, returns `deltas: [{ job_id, score, tier, breakdown }, ...]`. Main thread merges all deltas into `.job-scout/cache/scores.json` keyed by `(job_id, cv_hash, profile_hash)`.

Tiers: **A (85-100)** apply immediately, **B (70-84)** worth applying, **C (55-69)** consider, **D (<55)** discard.

**Fallback:** if the `Agent` tool is unavailable in this session, fall back to sequential in-thread scoring. Log the fallback.
```

- [ ] **Step 4: Verify**

Run:
```bash
cd /Users/tura/git/claude-job-scout && grep -c "score-job-batch" skills/match-jobs/SKILL.md skills/check-job-notifications/SKILL.md
```

Expected: at least `2` (one per file).

Run:
```bash
cd /Users/tura/git/claude-job-scout && grep -c "Fallback:" skills/match-jobs/SKILL.md skills/check-job-notifications/SKILL.md
```

Expected: `2`.

- [ ] **Step 5: Commit**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git add skills/match-jobs/SKILL.md skills/check-job-notifications/SKILL.md && git commit -m "$(cat <<'EOF'
Parallelise job scoring via subagent batches

/match-jobs and /check-job-notifications now batch new jobs into groups
of 5, dispatch one subagent per batch, and merge deltas back into
scores.json. Follows subagent-protocol.md. Falls back to sequential
in-thread scoring when the Agent tool is unavailable.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 6: Push and open PR**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git push -u origin phase-1/task-12-parallel-scoring && gh pr create --title "phase-1/12: parallel job scoring" --body "Part of Phase 1 (v0.4.0). See spec Component 5a."
```

---

## Task 13: Parallel Top Picks pagination

**Files:**
- Modify: `/Users/tura/git/claude-job-scout/skills/check-job-notifications/SKILL.md`

- [ ] **Step 1: Create branch**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-1/task-13-parallel-pagination
```

- [ ] **Step 2: Update Step 10**

In `/Users/tura/git/claude-job-scout/skills/check-job-notifications/SKILL.md`, find "Step 10: Offer 'Top job picks for you' sweep".

Replace the block that starts `If accepted:` and enumerates the six substeps with:

```
If accepted:
1. Navigate to `https://www.linkedin.com/jobs/` and locate **"Top job picks for you"**.
2. Load `tracker.json` once and snapshot into memory — every subagent receives this snapshot.
3. For pages 1..5 (or until a stop condition fires): dispatch one subagent per page, each with `subagent_type: "general-purpose"` per `../shared-references/subagent-protocol.md`:

   ```json
   {
     "task": "top-picks-page",
     "inputs": {
       "page_number": 1,
       "tracker_snapshot_ids": ["..."],
       "source": "Top Picks"
     },
     "budget_lines": 200,
     "allowed_tools": ["Read"]
   }
   ```

   The subagent receives the page URL pattern in its prompt and extracts job blobs for any id not in `tracker_snapshot_ids`. It returns:

   ```json
   {
     "status": "ok",
     "deltas": [
       { "job_id": "...", "title": "...", "company": "...", "raw_blob": "...", "source": "Top Picks" }
     ]
   }
   ```

   Note: page-fetching in Phase 1 still happens via the main thread's Chrome extension (subagents do not have browser access). The main thread fetches the raw HTML or listing JSON for each page, then dispatches the subagent with that data in `inputs`. Subagents dedupe and parse only.

4. Collect all subagent deltas. Dedupe again against the live tracker (in case concurrent runs updated it).
5. Stop early if: any page's subagent returns zero new jobs, the user says stop, or the 5-page cap is hit.
6. Hand the collected new-job blobs to Step 6's scoring fan-out. Append to today's report under a **"Top Picks Sweep"** section rather than overwriting.
7. Present the new A/B/C matches.

**Fallback:** if the `Agent` tool is unavailable, fall back to the sequential in-thread loop (fetch → dedupe → extract → score) page by page.
```

- [ ] **Step 3: Verify**

Run:
```bash
cd /Users/tura/git/claude-job-scout && grep -c "top-picks-page" skills/check-job-notifications/SKILL.md
```

Expected: `1`.

Run:
```bash
cd /Users/tura/git/claude-job-scout && grep -c "tracker_snapshot_ids" skills/check-job-notifications/SKILL.md
```

Expected: at least `1`.

- [ ] **Step 4: Commit**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git add skills/check-job-notifications/SKILL.md && git commit -m "$(cat <<'EOF'
Parallelise Top Picks pagination via subagent per page

Step 10 now dispatches one subagent per page (up to 5), each dedupes
its page against a tracker snapshot and extracts only new-job blobs.
Browser fetch stays on the main thread (subagents have no browser
access in Phase 1); subagents do the dedupe-and-parse work. Falls
back to sequential when the Agent tool is unavailable.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 5: Push and open PR**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git push -u origin phase-1/task-13-parallel-pagination && gh pr create --title "phase-1/13: parallel Top Picks pagination" --body "Part of Phase 1 (v0.4.0). See spec Component 5b."
```

---

## Task 14: `company-researcher` subagent skill

**Files:**
- Create: `/Users/tura/git/claude-job-scout/skills/company-researcher/SKILL.md`
- Modify: `/Users/tura/git/claude-job-scout/skills/profile-optimizer/SKILL.md` (add optional dispatch hook)

- [ ] **Step 1: Create branch**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-1/task-14-company-researcher
```

- [ ] **Step 2: Create skill directory**

Run:
```bash
cd /Users/tura/git/claude-job-scout && mkdir -p skills/company-researcher
```

- [ ] **Step 3: Write `company-researcher/SKILL.md`**

Create `/Users/tura/git/claude-job-scout/skills/company-researcher/SKILL.md` with exactly:

```markdown
---
name: company-researcher
description: >
  Internal subagent skill. Dispatched by profile-optimizer, /match-jobs,
  /check-job-notifications, and (in later phases) cover-letter-writer
  when a job listing carries a company name worth enriching. Returns a
  short, structured digest — never prose. Not user-invocable.
version: 0.1.0
---

# Company Researcher (Subagent)

Produce a short structured digest about a company so the dispatching skill can make better recommendations without pulling company-research noise into the main conversation.

**This skill is dispatched only by other skills, via the `Agent` tool, per `../shared-references/subagent-protocol.md`.** It is not user-invocable.

## Input shape

```json
{
  "task": "research-company",
  "inputs": {
    "company_name": "Acme Corp",
    "job_id": "123456789",
    "source_blob": "<full job description text if available>",
    "cached_files": ["<optional paths to user-indexed docs mentioning this company>"],
    "signals_requested": ["size", "stage", "reputation", "red_flags"]
  },
  "budget_lines": 60,
  "allowed_tools": ["Read", "Grep", "Glob"]
}
```

## Output shape

```json
{
  "status": "ok",
  "deltas": [
    {
      "company_name": "Acme Corp",
      "size": "50-200 employees | unknown",
      "stage": "Series B | growth-stage | public | unknown",
      "reputation_digest": "<one short line — factual signals only, no speculation>",
      "red_flags": ["<flag 1>", "<flag 2>"]
    }
  ],
  "errors": []
}
```

**Output rules:**

- Each field is either a concrete value or `null`. Never speculate. If a signal can't be determined from the inputs, return `null`.
- `reputation_digest` is at most one sentence and cites the signal type ("from source_blob", "from user's cached recommendation file at path/to/file.pdf").
- `red_flags` is empty `[]` if none apply. Valid flags include: undisclosed company name, agency with no end client named, pattern-matching scam indicators from `../recruiter-engagement/references/response-templates.md`, pay-to-apply references.
- No prose outside the JSON envelope.

## Sources

Phase 1 sources only:
- The `source_blob` passed in the prompt (the JD text, if available).
- Files at paths named in `cached_files` (passed in by the dispatcher from `.job-scout/cache/supporting-docs.json`).

Phase 1 does **not** grant this subagent `WebFetch` or browser access. Any signal that can't be derived from the two sources above is `null`. Future phases may extend sources under explicit user consent.

## Budget

`budget_lines: 60`. If the subagent can't fit within 60 lines, return `status: "partial"` with the highest-signal fields populated and the rest `null`.

## Not user-invocable

This skill has no `allowed-tools` frontmatter for the slash-command surface and should never be wired into a slash command. The dispatching skill always loads it via `Agent` with a self-contained prompt.
```

- [ ] **Step 4: Add an optional dispatch hook in `profile-optimizer/SKILL.md`**

In `/Users/tura/git/claude-job-scout/skills/profile-optimizer/SKILL.md`, find the "Optimization process" section (inserted in Task 11).

Insert a new step 5a between steps 5 and 6:

Replace:
```
5. **Run Boolean search simulation** — would a recruiter find this profile?
6. **Generate section-by-section proposals** — ready-to-paste content derived from CV. For each section scoring below 8, load that section's reference and generate proposals.
```

With:
```
5. **Run Boolean search simulation** — would a recruiter find this profile?
5a. **Optional: company enrichment** — if the user pastes in a specific job listing during this run, dispatch `company-researcher/SKILL.md` with the JD blob to get a size/stage/reputation digest. Use the digest to shape the Featured section and About-paragraph proposals.
6. **Generate section-by-section proposals** — ready-to-paste content derived from CV. For each section scoring below 8, load that section's reference and generate proposals.
```

- [ ] **Step 5: Verify**

Run:
```bash
cd /Users/tura/git/claude-job-scout && ls skills/company-researcher/SKILL.md
```

Expected: file exists.

Run:
```bash
cd /Users/tura/git/claude-job-scout && grep -c "research-company" skills/company-researcher/SKILL.md
```

Expected: `1`.

Run:
```bash
cd /Users/tura/git/claude-job-scout && grep -c "company-researcher" skills/profile-optimizer/SKILL.md
```

Expected: at least `1`.

- [ ] **Step 6: Commit**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git add skills/company-researcher/ skills/profile-optimizer/SKILL.md && git commit -m "$(cat <<'EOF'
Add company-researcher subagent skill

New subagent dispatched by profile-optimizer (Step 5a) and in later
phases by cover-letter-writer and the ATS simulator. Returns a short
structured digest (size/stage/reputation/red_flags) derived from the
JD blob and user-indexed supporting docs. No browser or web access in
Phase 1. Not user-invocable.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 7: Push and open PR**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git push -u origin phase-1/task-14-company-researcher && gh pr create --title "phase-1/14: company-researcher subagent skill" --body "Part of Phase 1 (v0.4.0). See spec Component 5c."
```

---

## Task 15: `cv-section-rewriter` subagent skill

**Files:**
- Create: `/Users/tura/git/claude-job-scout/skills/cv-section-rewriter/SKILL.md`
- Modify: `/Users/tura/git/claude-job-scout/skills/cv-optimizer/SKILL.md` (Phase 3 dispatch hook)

- [ ] **Step 1: Create branch**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-1/task-15-cv-section-rewriter
```

- [ ] **Step 2: Create skill directory**

Run:
```bash
cd /Users/tura/git/claude-job-scout && mkdir -p skills/cv-section-rewriter
```

- [ ] **Step 3: Write `cv-section-rewriter/SKILL.md`**

Create `/Users/tura/git/claude-job-scout/skills/cv-section-rewriter/SKILL.md` with exactly:

```markdown
---
name: cv-section-rewriter
description: >
  Internal subagent skill. Dispatched by cv-optimizer during Phase 3
  (Optimized Rewrite), one instance per role block. Returns SPAR-method
  optimized bullets as a structured delta. Not user-invocable.
version: 0.1.0
---

# CV Section Rewriter (Subagent)

Rewrite a single CV role block's bullets using the SPAR method, the user's tone preference, and the target keywords. Dispatched in parallel — one subagent per role — so the CV rewrite's token cost scales with parallelism and not wall-time.

**This skill is dispatched only by `cv-optimizer/SKILL.md`, via the `Agent` tool, per `../shared-references/subagent-protocol.md`.** It is not user-invocable.

## Input shape

```json
{
  "task": "rewrite-cv-role",
  "inputs": {
    "role_id": "acme-corp-2021-2024",
    "role_block": {
      "company": "Acme Corp",
      "title": "Senior Engineer",
      "dates": "2021–2024",
      "original_bullets": [ "..." ]
    },
    "user_profile": {
      "cv_summary": { "...": "..." },
      "target_roles": [ "..." ],
      "tone_preference": "Professional-modern"
    },
    "target_keywords": [ "..." ],
    "role_weight": "current | previous | older"
  },
  "budget_lines": 80,
  "allowed_tools": ["Read"]
}
```

`role_weight` determines the bullet count:
- `current` — 4–6 bullets
- `previous` — 3–4 bullets
- `older` — 2–3 bullets

## Output shape

```json
{
  "status": "ok",
  "deltas": [
    {
      "role_id": "acme-corp-2021-2024",
      "bullets_optimized": [
        { "text": "...", "technique": "anchoring | loss-aversion | specificity | ...", "keywords_used": ["..."] }
      ]
    }
  ],
  "errors": []
}
```

**Output rules:**

- Bullets only. No prose, no commentary, no meta text.
- Each bullet names the persuasion technique used (for auditability) and the keywords it placed.
- No bullet fabricates facts. If the `original_bullets` don't support a stronger claim, the rewrite stays conservative.
- No duplicate verbs within the role.
- Respect `tone_preference` from the user profile.

## Rewrite rules

Apply the rules in `../cv-optimizer/references/phase-3-optimized-rewrite.md` (SPAR bullet formula, persuasion-technique mapping, loss-aversion framing, anchoring). This subagent loads that reference on entry.

## Budget

`budget_lines: 80`. If the subagent can't fit within budget (many original bullets to compress or expand), return `status: "partial"` with the highest-impact bullets optimized and a continuation cursor for the rest.

## Not user-invocable

This skill has no slash-command surface and should not be wired to one. Dispatch is always via `Agent` from `cv-optimizer/SKILL.md`.
```

- [ ] **Step 4: Update `cv-optimizer/SKILL.md` Parallel rewrite section**

In `/Users/tura/git/claude-job-scout/skills/cv-optimizer/SKILL.md`, find the "## Parallel rewrite (Phase 3)" section (added in Task 10).

Replace:
```
## Parallel rewrite (Phase 3)

When Phase 3 runs, the orchestrator may dispatch one subagent per role section to `cv-section-rewriter/SKILL.md`, following the contract in `../shared-references/subagent-protocol.md`. Main thread assembles the final document from deltas.
```

With:
```
## Parallel rewrite (Phase 3)

When Phase 3 runs, the orchestrator dispatches one subagent per role section to `cv-section-rewriter/SKILL.md`:

For each role block in the CV:
1. Classify role weight: `current` (most recent), `previous` (roles 2 through N-1), `older` (roles 1 through 2).
2. Dispatch `cv-section-rewriter` with the role block, the user profile, target keywords from the master keyword list, and the role weight.
3. Collect deltas, merge into the final CV document.

Follows the contract in `../shared-references/subagent-protocol.md`.

**Fallback:** if the `Agent` tool is unavailable, fall back to sequential in-thread rewrite using the same `references/phase-3-optimized-rewrite.md` rules.
```

- [ ] **Step 5: Verify**

Run:
```bash
cd /Users/tura/git/claude-job-scout && ls skills/cv-section-rewriter/SKILL.md
```

Expected: file exists.

Run:
```bash
cd /Users/tura/git/claude-job-scout && grep -c "rewrite-cv-role" skills/cv-section-rewriter/SKILL.md
```

Expected: `1`.

Run:
```bash
cd /Users/tura/git/claude-job-scout && grep -c "cv-section-rewriter" skills/cv-optimizer/SKILL.md
```

Expected: at least `2`.

- [ ] **Step 6: Commit**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git add skills/cv-section-rewriter/ skills/cv-optimizer/SKILL.md && git commit -m "$(cat <<'EOF'
Add cv-section-rewriter subagent skill

Dispatched by cv-optimizer during Phase 3 (Optimized Rewrite), one
subagent per role. Returns SPAR-optimized bullets as structured
deltas. Parallelises the most token-heavy path in the plugin.
Respects tone_preference, role_weight, and the persuasion-technique
mapping from phase-3-optimized-rewrite.md. Not user-invocable.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 7: Push and open PR**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git push -u origin phase-1/task-15-cv-section-rewriter && gh pr create --title "phase-1/15: cv-section-rewriter subagent skill" --body "Part of Phase 1 (v0.4.0). See spec Component 5d."
```

---

## Task 16: Version bump + CHANGELOG + Roadmap update

**Files:**
- Modify: `/Users/tura/git/claude-job-scout/.claude-plugin/plugin.json`
- Modify: `/Users/tura/git/claude-job-scout/CHANGELOG.md`
- Modify: `/Users/tura/git/claude-job-scout/docs/ROADMAP.md`

- [ ] **Step 1: Create branch (merges last)**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-1/task-16-version-bump
```

Run this only after tasks 1–15 have all merged to `main`. Otherwise the CHANGELOG entry will describe work that isn't on `main` yet.

- [ ] **Step 2: Bump plugin version**

In `/Users/tura/git/claude-job-scout/.claude-plugin/plugin.json`, change `"version": "0.3.0"` to `"version": "0.4.0"`. Leave everything else unchanged.

Run to verify:
```bash
cd /Users/tura/git/claude-job-scout && jq -r .version .claude-plugin/plugin.json
```

Expected: `0.4.0`.

- [ ] **Step 3: Add `0.4.0` section to `CHANGELOG.md`**

In `/Users/tura/git/claude-job-scout/CHANGELOG.md`, insert this new section immediately below the top `## [0.3.0]` section (so the new version is the most recent at the top of the file, after the title block):

```markdown
## [0.4.0] — 2026-MM-DD

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
- **`cv-optimizer/SKILL.md`** split into a ≤4KB orchestrator + five lazy-loaded phase references (`phase-0-discovery-interview.md` through `phase-4-output-deliverables.md`). Phases load only when their gate fires.
- **`profile-optimizer/SKILL.md`** split into a ≤5KB orchestrator + eight `references/sections/*.md` files plus `activity-engagement.md` and `scoring-framework.md`. Section content loads only when that section is proposed or re-scored.
- **`/match-jobs` and `/check-job-notifications`** scoring paths fan out across subagents (batch size 5), following `subagent-protocol.md`. Falls back to sequential in-thread scoring when the `Agent` tool is unavailable.
- **`/check-job-notifications` Step 10 Top Picks sweep** paginates via one subagent per page (up to 5).
- **`.claude/settings.local.json`** trimmed to the git/gh permissions actually used.
- **`.claude-plugin/plugin.json`** version bumped from 0.3.0 to 0.4.0.

### Migration notes

- First run after upgrade: the bootstrap procedure writes `.job-scout/schema-version` = `{ version: 1, upgraded_at: <ISO> }` if missing, and clears `.job-scout/cache/scores.json` once to account for the cache-key expansion. Subsequent runs use caches normally.
- No user action required.

---
```

Update the `2026-MM-DD` placeholder to the actual release date at merge time.

- [ ] **Step 4: Update ROADMAP.md**

In `/Users/tura/git/claude-job-scout/docs/ROADMAP.md`:

1. Change the Phase 1 status in the status table from `In design` to `Shipped — v0.4.0`.
2. Tick every checkbox in the Phase 1 checklist section (`- [ ]` → `- [x]`).
3. Change Phase 2 status from `Not started` to `In design` and queue a spec file path (leave the path placeholder — we write the spec in the kickoff of Phase 2).
4. Append a log entry with today's date: `Phase 1 shipped as v0.4.0. Phase 2 design entering.`

- [ ] **Step 5: Verify**

Run:
```bash
cd /Users/tura/git/claude-job-scout && jq -r .version .claude-plugin/plugin.json
```

Expected: `0.4.0`.

Run:
```bash
cd /Users/tura/git/claude-job-scout && grep -c "^## \[0.4.0\]" CHANGELOG.md
```

Expected: `1`.

Run:
```bash
cd /Users/tura/git/claude-job-scout && grep -c "Shipped — v0.4.0" docs/ROADMAP.md
```

Expected: `1`.

Run:
```bash
cd /Users/tura/git/claude-job-scout && grep -c "^- \[ \]" docs/ROADMAP.md
```

Expected: `0` (all Phase 1 boxes should be ticked to `[x]`).

- [ ] **Step 6: Commit**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git add .claude-plugin/plugin.json CHANGELOG.md docs/ROADMAP.md && git commit -m "$(cat <<'EOF'
Release v0.4.0 — Phase 1 complete

Bumps plugin version, adds CHANGELOG 0.4.0 section, and updates
ROADMAP to mark Phase 1 shipped and Phase 2 entering design.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 7: Push and open release PR**

Run:
```bash
cd /Users/tura/git/claude-job-scout && git push -u origin phase-1/task-16-version-bump && gh pr create --title "phase-1/16: release v0.4.0" --body "Final Phase 1 merge. Bumps plugin version to 0.4.0, adds CHANGELOG entry summarising all 15 preceding component PRs, marks Phase 1 shipped in the roadmap."
```

- [ ] **Step 8: After merge — manual smoke test**

Once `phase-1/task-16-version-bump` merges:

1. In a scratch workspace, run `/analyze-cv` and confirm: folder bootstrap creates `schema-version`, `supporting-docs.json`, `archive/`, and the usual subfolders. Discovery interview runs normally.
2. Run `/optimize-profile` and confirm: profile read produces a snapshot with per-section hashes; scoring only runs for sections flagged re-score.
3. Run `/check-job-notifications` and confirm: scoring fan-out triggers (or falls back cleanly if the `Agent` tool is unavailable), Top Picks sweep paginates via subagents, `scores.json` uses the 3-tuple key.
4. If any of the above regresses from 0.3.0, open a follow-up PR. Do not re-run this plan.

---

## Self-review (writer's)

### Spec coverage

Checked each Phase 1 Roadmap checkbox against this plan:

| Roadmap item | Task |
|--------------|------|
| subagent-protocol.md | Task 4 |
| CLAUDE.md | Task 2 |
| repo .gitignore | Task 1 |
| settings.local.json trim | Task 3 |
| cv-optimizer split | Task 10 |
| profile-optimizer split | Task 11 |
| Score-cache key reconciliation (+ profile_hash) | Task 6 |
| .job-scout/schema-version scaffolding | Task 5 |
| Tracker archival | Task 7 |
| Delta-aware LinkedIn snapshot | Task 9 |
| Supporting-docs index | Task 8 |
| Parallel job scoring | Task 12 |
| Parallel Top Picks pagination | Task 13 |
| company-researcher subagent | Task 14 |
| cv-section-rewriter subagent | Task 15 |

All 15 items covered. Task 16 handles the release mechanics.

### Placeholder scan

- One deliberate placeholder: `2026-MM-DD` in the CHANGELOG entry — explicitly called out as "update to actual release date at merge time". Acceptable because the merge date isn't knowable at plan-write time.
- Every other step has concrete commands, exact file paths, and specific verification expectations.

### Type consistency

- Score-cache key tuple written as `(job_id, cv_hash, profile_hash)` in every task.
- `profile_hash` is the identifier everywhere — not `profile_hash_v1`, not `linkedin_hash`.
- `score-job-batch` task name consistent between Task 12's `match-jobs` and `check-job-notifications` updates.
- `rewrite-cv-role` task name consistent between Task 15's subagent definition and Task 10's cv-optimizer hook.
- Per-section hash shape (`{ content, hash, scored_at }`) consistent between Tasks 9 and 11.

### Scope

Plan is ambitious (16 tasks, one release). Each task is a self-contained PR; nothing bigger can be split cleanly without making some tasks incoherent (e.g., score-cache key reconciliation would be noise if split across 4 tasks). Task 6 touches 5 files and is the largest; all other tasks touch 1–3 files.

---

## Execution handoff

**Plan complete and saved to `docs/superpowers/plans/2026-04-16-phase-1-token-agentic-foundations.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration. Good for a 16-task plan where each task is a clean PR.

**2. Inline Execution** — Execute tasks in this session using `executing-plans`, batch execution with checkpoints for review.

**Which approach?**

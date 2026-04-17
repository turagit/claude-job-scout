# Phase 3 — New User-Facing Commands Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship v0.6.0 by delivering 4 new slash commands (`/cover-letter`, `/interview-prep`, `/funnel-report`, `/index-docs`) plus 2 small UX enhancements (daily-driver context line, bootstrap nudge for supporting docs).

**Architecture:** This plugin is a Claude Code plugin — the "code" is markdown skill files, markdown references, and per-project JSON state under `.job-scout/`. Validation is manual via shell (`jq`, `grep`, `wc`) and targeted reads.

**Tech Stack:** Markdown (CommonMark), JSON state files, Claude Agent tool for subagent dispatch, Claude Chrome extension for browser work.

**Design spec:** [`docs/superpowers/specs/2026-04-17-phase-3-user-facing-commands-design.md`](../specs/2026-04-17-phase-3-user-facing-commands-design.md)

**Roadmap:** [`docs/ROADMAP.md`](../../ROADMAP.md)

**Branching:** each task is one branch off `main` named `phase-3/task-NN-<short-slug>`. Controller merges directly to `main` after dual review (no PRs — `gh` CLI is unavailable in this environment).

**Merge order:** tasks are numbered to be merged **serially** in numerical order. Task 2 depends on Task 1's `/index-docs` skill existing, so order matters.

**Progress tracking:** after each task merges, tick the matching checkbox in `docs/ROADMAP.md`'s Phase 3 section.

---

## Task 1: `/index-docs` slash command

**Files:**
- Create: `/Users/tura/git/claude-job-scout/skills/index-docs/SKILL.md`

- [ ] **Step 1: Create branch + dir**

```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-3/task-01-index-docs && mkdir -p skills/index-docs
```

- [ ] **Step 2: Write `index-docs/SKILL.md`**

Create `/Users/tura/git/claude-job-scout/skills/index-docs/SKILL.md` with exactly this content (between markers, exclusive):

===FILE_START===
---
name: index-docs
description: Re-scan workspace for supporting documents and rebuild the supporting-docs index
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
disable-model-invocation: true
---

Explicitly (re)scan the workspace for supporting documents and rebuild `.job-scout/cache/supporting-docs.json`. Phase 1's bootstrap auto-runs this scan once on workspace creation; this command is for users who add documents mid-session, want to re-scan after edits, or declined the bootstrap prompt and want to opt back in.

## Step 0: Bootstrap workspace

Follow `shared-references/workspace-layout.md` to ensure `.job-scout/` exists in the current workspace.

## Step 1: Load existing index

Read `.job-scout/cache/supporting-docs.json`. If missing or empty, treat the current state as `{ "version": 1, "last_scanned": null, "docs": {} }` and proceed.

## Step 2: Run the workspace scan

Follow the scan procedure from `shared-references/supporting-docs.md` — the "When the index is built" and "Re-indexing" sections describe the file extensions, exclusion list, classification heuristics, and hash logic. Do not duplicate that procedure here; load the reference and follow it.

## Step 3: Compute the diff

Compare the freshly-scanned state to the existing index. Categorise each entry:

- **New files** — extension matches the scan list, path not in current index.
- **Re-indexed files** — path in current index, content hash differs from stored hash (file edited since last scan).
- **Missing files** — path in current index, file no longer at that path. Mark with `status: "missing"` (do not delete the entry).
- **Unchanged files** — hash matches; nothing to do.

## Step 4: Present the diff

Show the user a summary:

```
📎 Supporting-docs index update

  New files (N):
    - certs/aws-sa-pro-2026.pdf
    - talks/kubecon-2026-eda.pdf
    ... (showing first 10 of N)

  Re-indexed (N):
    - case-studies/migration-2024.pdf  (content changed)
    ... (showing first 10 of N)

  Missing (N):
    - portfolio/old-deck.pdf  (file moved or deleted)
    ... (showing first 10 of N)

  Unchanged: N

Apply changes? (Y/n)
```

If all four categories are empty, report "No changes detected" and exit.

## Step 5: Apply on approval

On approval:
1. For each new file: classify (filename heuristic + content inspection for first 5 inconclusive), generate a 200-word summary, compute SHA-256, add to the index.
2. For each re-indexed file: re-classify, re-summarise, update the hash.
3. For each missing file: set `status: "missing"` on the existing entry.
4. Update `last_scanned` to the current ISO timestamp.
5. Write the updated index back to `.job-scout/cache/supporting-docs.json`.
6. Report final counts.

On decline: leave the index untouched but report what would have changed.

## Special interaction: opt-back-in

If the user previously declined indexing at bootstrap (the supporting-docs reference's opt-out behaviour), running this command overrides that opt-out for this and future sessions. Display a single-line confirmation when this happens:

> "Re-enabling supporting-docs indexing for this workspace."

## Reference Materials

- **`shared-references/supporting-docs.md`** — canonical scan procedure, classification heuristics, file shape
- **`shared-references/workspace-layout.md`** — `.job-scout/` layout and bootstrap
===FILE_END===

- [ ] **Step 3: Verify**

```bash
cd /Users/tura/git/claude-job-scout && ls skills/index-docs/SKILL.md
```
Expected: file exists.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "disable-model-invocation: true" skills/index-docs/SKILL.md
```
Expected: `1`.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "supporting-docs.json" skills/index-docs/SKILL.md
```
Expected: at least `2`.

```bash
cd /Users/tura/git/claude-job-scout && wc -l skills/index-docs/SKILL.md
```
Expected: roughly 60-75 lines.

```bash
cd /Users/tura/git/claude-job-scout && git diff --stat
```
Expected: 1 file (new).

- [ ] **Step 4: Commit + push**

```bash
cd /Users/tura/git/claude-job-scout && git add skills/index-docs/ && git commit -m "$(cat <<'EOF'
Add /index-docs slash command

Explicit user-invocable command to (re)scan the workspace for
supporting documents and rebuild the index. Computes the diff (new,
re-indexed, missing, unchanged), presents to user, applies on
approval. Also serves as the opt-back-in path for users who declined
the bootstrap-time scan.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)" && git push -u origin phase-3/task-01-index-docs
```

---

## Task 2: Bootstrap nudge to index supporting docs

**Files:**
- Modify: `/Users/tura/git/claude-job-scout/skills/shared-references/workspace-layout.md`

- [ ] **Step 1: Create branch**

```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-3/task-02-bootstrap-nudge
```

- [ ] **Step 2: Read current bootstrap step 4**

```bash
cd /Users/tura/git/claude-job-scout && cat skills/shared-references/workspace-layout.md | head -50
```

Note the current end of step 4 — it should end with the "Then run the supporting-docs scan..." sentence added in Phase 2.

- [ ] **Step 3: Append the nudge**

Find this exact sentence at the end of bootstrap step 4:

```
   Then run the supporting-docs scan described in `supporting-docs.md` — the user is prompted once per workspace; the scan itself runs silently on subsequent commands. Does not block the command that triggered the bootstrap.
```

Replace with:

```
   Then run the supporting-docs scan described in `supporting-docs.md` — the user is prompted once per workspace; the scan itself runs silently on subsequent commands. Does not block the command that triggered the bootstrap.

5. **Bootstrap nudge for supporting docs.** Immediately after the standard files are written (step 4), run a quick `Glob` for likely supporting-doc files at the workspace root: `*.pdf`, `*.docx`, `*.pptx`, `*.md`, `*.txt`. Filter out the CV (matches `cv.*`, `resume.*`, `curriculum.*`) and anything inside `.job-scout/`, `.git/`, or dotted directories. If 1+ files found, prompt the user:

   > "📎 I noticed [N] files in your workspace that look like supporting materials (certs, talks, decks, recommendations). Indexing them now will make every future CV rewrite, profile proposal, and cover letter sharper. Run `/index-docs` now? (Y/n)"

   On Y: dispatch `/index-docs` immediately. On n: remember per session (the supporting-docs reference's opt-out behaviour applies). If zero files found, proceed silently — the user can run `/index-docs` later when they add docs.
```

- [ ] **Step 4: Verify**

```bash
cd /Users/tura/git/claude-job-scout && grep -c "Bootstrap nudge for supporting docs" skills/shared-references/workspace-layout.md
```
Expected: `1`.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "/index-docs" skills/shared-references/workspace-layout.md
```
Expected: at least `1`.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "📎" skills/shared-references/workspace-layout.md
```
Expected: at least `1`.

```bash
cd /Users/tura/git/claude-job-scout && git diff --stat
```
Expected: 1 file changed.

- [ ] **Step 5: Commit + push**

```bash
cd /Users/tura/git/claude-job-scout && git add skills/shared-references/workspace-layout.md && git commit -m "$(cat <<'EOF'
Add bootstrap nudge to index supporting docs

Bootstrap procedure step 5: after standard files are written, glob
for likely supporting-doc files at workspace root. If 1+ found,
prompt the user to run /index-docs now. Decline persists per session.
Zero files = silent proceed.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)" && git push -u origin phase-3/task-02-bootstrap-nudge
```

---

## Task 3: Daily-driver context line in `/check-job-notifications`

**Files:**
- Modify: `/Users/tura/git/claude-job-scout/skills/check-job-notifications/SKILL.md`

- [ ] **Step 1: Create branch**

```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-3/task-03-daily-context-line
```

- [ ] **Step 2: Add Step 0a between Step 0 and Step 1**

In `/Users/tura/git/claude-job-scout/skills/check-job-notifications/SKILL.md`, find this exact pair of consecutive section headings:

```
## Step 0: Bootstrap workspace

Follow `shared-references/workspace-layout.md` to ensure `.job-scout/` exists in the current workspace. All paths below are inside `.job-scout/`.

## Step 1: Load CV & Profile
```

Replace with:

```
## Step 0: Bootstrap workspace

Follow `shared-references/workspace-layout.md` to ensure `.job-scout/` exists in the current workspace. All paths below are inside `.job-scout/`.

## Step 0a: Daily-driver context line

Read `.job-scout/tracker.json`. Compute and display a one-line situational summary as the first user-visible output:

**If `tracker.stats.last_run` is set (prior runs exist):**

```
📊 Last run [N] days ago. Tracker: [seen] seen, [A-tier] A-tier, [applied] applied.
   New since last run: [M] alerts.
```

Where:
- `[N]` = days between today and `tracker.stats.last_run`.
- `[seen]` = count of tracker entries with `status: "seen"`.
- `[A-tier]` = count of tracker entries with `tier: "A"`.
- `[applied]` = `tracker.stats.applied`.
- `[M]` = best-effort count of new alerts on the notifications page since `last_run`. If this can't be computed cheaply at this point, omit the second line.

**If `tracker.stats.last_run` is null (first run):**

```
🚀 First run. Setting up tracker.
```

This step is read-only. Cost is one tracker.json read plus one timestamp diff. No browser interaction.

## Step 1: Load CV & Profile
```

- [ ] **Step 3: Verify**

```bash
cd /Users/tura/git/claude-job-scout && grep -c "Step 0a:" skills/check-job-notifications/SKILL.md
```
Expected: `1`.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "📊 Last run" skills/check-job-notifications/SKILL.md
```
Expected: `1`.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "🚀 First run" skills/check-job-notifications/SKILL.md
```
Expected: `1`.

```bash
cd /Users/tura/git/claude-job-scout && git diff --stat
```
Expected: 1 file changed.

- [ ] **Step 4: Commit + push**

```bash
cd /Users/tura/git/claude-job-scout && git add skills/check-job-notifications/SKILL.md && git commit -m "$(cat <<'EOF'
Add Step 0a daily-driver context line to /check-job-notifications

First user-visible output is now a one-line situational summary
showing days since last run, tracker counts (seen/A-tier/applied),
and best-effort new-alerts count. Read-only, single tracker.json
read. First-run shows a setup line instead.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)" && git push -u origin phase-3/task-03-daily-context-line
```

---

## Task 4: `/cover-letter` slash command + `cover-letter-writer` subagent

**Files:**
- Create: `/Users/tura/git/claude-job-scout/skills/cover-letter/SKILL.md`
- Create: `/Users/tura/git/claude-job-scout/skills/cover-letter-writer/SKILL.md`

- [ ] **Step 1: Create branch + dirs**

```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-3/task-04-cover-letter && mkdir -p skills/cover-letter skills/cover-letter-writer
```

- [ ] **Step 2: Write `cover-letter/SKILL.md` (orchestrator)**

Create `/Users/tura/git/claude-job-scout/skills/cover-letter/SKILL.md` with exactly:

===FILE_START===
---
name: cover-letter
description: Generate a tailored cover letter for a specific job, with 3 angle options (hiring-manager / recruiter-gate / culture-match)
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: [tracker-id | linkedin-url]
disable-model-invocation: true
---

Generate a tailored cover letter for a specific job. Returns 3 angle options so the user can pick the one that fits the situation. Cites supporting documents from the index where relevant.

## Browser policy (read first)

If the user provides a LinkedIn URL (rather than a tracker ID), browser navigation uses **the Claude Chrome extension exclusively** to fetch the JD. Never request computer use. See `shared-references/browser-policy.md`.

## Step 0: Bootstrap workspace

Follow `shared-references/workspace-layout.md` to ensure `.job-scout/` exists.

## Step 1: Resolve the job

Three invocation forms — handle each:

| Form | Behaviour |
|------|-----------|
| `/cover-letter <tracker-id>` | Load the tracker entry. Use the cached JD blob (`tracker.jobs.<id>.description` if present; otherwise fetch via Chrome extension and cache). |
| `/cover-letter <linkedin-url>` | Strip tracking params from the URL to get the canonical `/jobs/view/<id>/` form. If the ID exists in tracker, treat as form 1. Otherwise navigate via Chrome extension and extract title, company, JD blob. |
| `/cover-letter` (no arg) | Load `tracker.json`, present the user's recent A-tier jobs (last 10 sorted by score, status in `seen` or `approved`). User picks an ID, then proceed as form 1. |

If no A-tier jobs exist (the user hasn't run a sweep yet), error and suggest `/check-job-notifications` first.

## Step 2: Load inputs

Gather the materials the writer needs:

- The job (title, company, JD blob, source).
- The user profile from `.job-scout/user-profile.json` — `cv_summary`, `target_roles`, `tone_preference`.
- The supporting-docs index from `.job-scout/cache/supporting-docs.json` — full doc list with paths and types.
- The master keyword list from `user-profile.json.master_keyword_list`.
- JD-specific keywords extracted from the JD blob (use `shared-references/jd-keyword-extraction.md` procedure for the extraction step only — the merge into the corpus is optional here since this command isn't a corpus consumer).
- Voice sample: first 500 characters of the cached LinkedIn About section from `.job-scout/cache/linkedin-profile.json` → `sections.about.content`.

## Step 3: Dispatch cover-letter-writer subagent

Per `shared-references/subagent-protocol.md`, dispatch `cover-letter-writer` once with all three angles requested:

```json
{
  "task": "draft-cover-letter",
  "inputs": {
    "job": { "title": "...", "company": "...", "jd_blob": "...", "source": "tracker | url" },
    "user_profile": { "cv_summary": {}, "target_roles": [], "tone_preference": "Professional-modern" },
    "supporting_docs_index": { "paths": [], "types": [] },
    "target_keywords": [],
    "linkedin_voice_sample": "<first 500 chars of About>"
  },
  "budget_lines": 200,
  "allowed_tools": ["Read"]
}
```

The subagent returns three drafts in `deltas`, one per angle.

**Fallback:** if the `Agent` tool is unavailable, fall back to drafting each angle sequentially in the main thread. Same inputs, three rounds.

## Step 4: Present to user

Show all three drafts. For each, display the angle name, the opening 2 sentences, and a one-line summary of the supporting docs cited. Then offer the user three actions:

- **Pick an angle** — save it as the chosen draft.
- **Edit an angle** — describe changes; orchestrator re-dispatches with edit instructions.
- **Generate a 4th hybrid** — combine elements of two angles into a custom draft.

## Step 5: Save the chosen draft

Write to `.job-scout/cover-letters/<job_id>-<angle>.md`. Use this format:

```markdown
---
job_id: 1234567890
job_title: Senior Data Engineer
company: Acme Corp
angle: hiring-manager | recruiter-gate | culture-match
generated: <ISO timestamp>
supporting_docs_cited:
  - certs/aws-sa-pro.pdf
  - case-studies/migration-2024.pdf
---

[Body of the cover letter]
```

Confirm to the user with the file path. Suggest `/apply` for Easy Apply jobs.

## State files

- **`.job-scout/cover-letters/`** — output directory. Per-letter markdown files.
- **`.job-scout/tracker.json`** — read-only here (resolves tracker IDs to JD blobs).
- **`.job-scout/cache/supporting-docs.json`** — read-only here (writer cites docs by path).
- **`.job-scout/user-profile.json`** — read-only here (cv_summary, profile data).

## Reference Materials

- **`../cover-letter-writer/SKILL.md`** — internal subagent that produces the drafts
- **`../shared-references/subagent-protocol.md`** — dispatch contract
- **`../shared-references/supporting-docs.md`** — supporting-docs index consumer contract
- **`../shared-references/jd-keyword-extraction.md`** — keyword extraction procedure (for target_keywords)
- **`../shared-references/browser-policy.md`** — Chrome extension only
- **`../shared-references/workspace-layout.md`** — bootstrap + state layout
===FILE_END===

- [ ] **Step 3: Write `cover-letter-writer/SKILL.md` (subagent)**

Create `/Users/tura/git/claude-job-scout/skills/cover-letter-writer/SKILL.md` with exactly:

===FILE_START===
---
name: cover-letter-writer
description: >
  Internal subagent skill. Dispatched by /cover-letter to draft three
  angle options (hiring-manager / recruiter-gate / culture-match) for
  a single job. Returns drafts as structured deltas. Not user-invocable.
version: 0.1.0
---

# Cover Letter Writer (Subagent)

Draft three cover-letter angle options for a single job. Each draft is ~250-350 words, structured as **hook → 2-3 evidence paragraphs (CV achievements + supporting-doc citations) → close with a specific ask**.

**This skill is dispatched only by `cover-letter/SKILL.md`, via the `Agent` tool, per `../shared-references/subagent-protocol.md`.** It is not user-invocable.

## Input shape

```json
{
  "task": "draft-cover-letter",
  "inputs": {
    "job": {
      "title": "Senior Data Engineer",
      "company": "Acme Corp",
      "jd_blob": "<full JD text>",
      "source": "tracker | url"
    },
    "user_profile": {
      "cv_summary": { "key_skills": [], "technologies": [], "top_achievements": [], "..." : "..." },
      "target_roles": ["..."],
      "tone_preference": "Formal-corporate | Professional-modern | Technical-dense | Let me decide"
    },
    "supporting_docs_index": {
      "paths": ["certs/aws-sa-pro.pdf", "case-studies/migration-2024.pdf", "..."],
      "types": ["cert", "case_study", "..."]
    },
    "target_keywords": ["..."],
    "linkedin_voice_sample": "<first 500 chars of About>"
  },
  "budget_lines": 200,
  "allowed_tools": ["Read"]
}
```

## Output shape

```json
{
  "status": "ok",
  "deltas": [
    {
      "angle": "hiring-manager",
      "draft": "<full markdown body of the cover letter, ~250-350 words>",
      "opening_two_sentences": "<for the orchestrator's preview>",
      "supporting_docs_cited": ["certs/aws-sa-pro.pdf"],
      "keywords_placed": ["Kubernetes", "AWS"]
    },
    {
      "angle": "recruiter-gate",
      "draft": "...",
      "opening_two_sentences": "...",
      "supporting_docs_cited": [],
      "keywords_placed": ["Python", "Spark", "AWS", "Kafka"]
    },
    {
      "angle": "culture-match",
      "draft": "...",
      "opening_two_sentences": "...",
      "supporting_docs_cited": ["case-studies/migration-2024.pdf"],
      "keywords_placed": ["Python"]
    }
  ],
  "errors": []
}
```

## The three angles

### Hiring-manager pitch

**Lead with:** the candidate's strongest CV achievement, framed against the JD. Treats the reader as a hiring manager who will read directly (not screened by a recruiter).

**Opening pattern:** "[Quantified achievement] — that's the kind of result your [JD-derived initiative] needs. I'm [Name], a [role] with [X years] in [domain]..."

**Best for:** roles where the hiring manager will read directly; established companies with low recruiter intermediation.

### Recruiter-gate

**Lead with:** keyword-dense opening that mirrors the JD's language. Optimised for ATS + recruiter screening, not the hiring manager.

**Opening pattern:** "I'm applying for the [exact JD title] role. As a [JD seniority] [JD role title] with experience in [JD-required-skill 1], [skill 2], and [skill 3]..."

**Best for:** larger companies with ATS + recruiter screening before any human review.

### Culture-match

**Lead with:** shared values / mission, references the company's own messaging (drawn from JD framing). Frames the candidate as someone who'd thrive in this specific company's environment.

**Opening pattern:** "Your team's commitment to [company value from JD] resonates with how I've approached my work in [domain]. As a [role]..."

**Best for:** mission-driven companies, public-benefit orgs, scale-ups with strong culture brand.

## Drafting rules (apply to all three angles)

- **Length:** 250-350 words. Anything longer is too much; anything shorter is too thin.
- **Structure:** hook (2-3 sentences) → 2-3 evidence paragraphs → close with a specific ask (interview, call, time slot).
- **Evidence paragraphs cite supporting docs.** When a claim maps to a doc in `supporting_docs_index`, cite the path inline: "(documented in `case-studies/migration-2024.pdf`)" or "(verifiable: `certs/aws-sa-pro.pdf`)". Track citations in the `supporting_docs_cited` array of the delta.
- **Keyword placement.** Place 3-5 target keywords from `target_keywords` naturally — not as a list. Track placements in the `keywords_placed` array.
- **Tone respects `tone_preference`.** Default to Professional-modern if unset.
- **Voice continuity.** The `linkedin_voice_sample` shows the user's About-section voice — match that register so the cover letter doesn't read as written by a different person.
- **No fabrication.** Every claim must be supportable from the CV summary or supporting docs. If a JD asks for a skill the user doesn't have, do not claim it.
- **No generic openers.** "I am writing to apply for..." is forbidden. Lead with substance.

## Budget

`budget_lines: 200`. Three drafts × ~50 lines each = ~150 lines, well within budget. If the subagent can't fit, return `status: "partial"` with the highest-priority drafts (always include `hiring-manager` if any are emitted).

## Not user-invocable

This skill has no slash-command surface. Dispatch is always via `Agent` from `cover-letter/SKILL.md`.
===FILE_END===

- [ ] **Step 4: Verify**

```bash
cd /Users/tura/git/claude-job-scout && ls skills/cover-letter/SKILL.md skills/cover-letter-writer/SKILL.md
```
Expected: both files exist.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "draft-cover-letter" skills/cover-letter-writer/SKILL.md skills/cover-letter/SKILL.md
```
Expected: at least `1` per file.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "hiring-manager\|recruiter-gate\|culture-match" skills/cover-letter-writer/SKILL.md
```
Expected: at least `3` (one per angle in headings + array enums).

```bash
cd /Users/tura/git/claude-job-scout && grep -c "disable-model-invocation: true" skills/cover-letter/SKILL.md
```
Expected: `1`.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "Not user-invocable" skills/cover-letter-writer/SKILL.md
```
Expected: `1`.

```bash
cd /Users/tura/git/claude-job-scout && wc -l skills/cover-letter/SKILL.md skills/cover-letter-writer/SKILL.md
```
Expected: each file 80-120 lines.

```bash
cd /Users/tura/git/claude-job-scout && git diff --stat
```
Expected: 2 files (both new).

- [ ] **Step 5: Commit + push**

```bash
cd /Users/tura/git/claude-job-scout && git add skills/cover-letter/ skills/cover-letter-writer/ && git commit -m "$(cat <<'EOF'
Add /cover-letter slash command + cover-letter-writer subagent

/cover-letter resolves a job (tracker ID, URL, or interactive pick),
loads the user profile + supporting-docs index + JD keywords + voice
sample, dispatches cover-letter-writer with all three angles, and
saves the chosen draft.

cover-letter-writer (internal subagent) drafts hiring-manager,
recruiter-gate, and culture-match angles in one call. Each draft is
250-350 words, cites supporting documents by path, and respects
tone preference + voice continuity. Not user-invocable.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)" && git push -u origin phase-3/task-04-cover-letter
```

---

## Task 5: `/interview-prep` slash command

**Files:**
- Create: `/Users/tura/git/claude-job-scout/skills/interview-prep/SKILL.md`

- [ ] **Step 1: Create branch + dir**

```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-3/task-05-interview-prep && mkdir -p skills/interview-prep
```

- [ ] **Step 2: Write `interview-prep/SKILL.md`**

Create `/Users/tura/git/claude-job-scout/skills/interview-prep/SKILL.md` with exactly:

===FILE_START===
---
name: interview-prep
description: Generate an interview-prep packet for a specific job — SPAR narratives, predicted questions, questions to ask, risk areas
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: [tracker-id]
disable-model-invocation: true
---

Generate a comprehensive interview-prep packet for a specific job. Synthesises CV achievements into SPAR narratives, predicts likely questions from the JD, suggests specific questions to ask the interviewer, and flags risk areas to address proactively.

No subagent dispatch — synthesis is bounded and inputs are already loaded.

## Step 0: Bootstrap workspace

Follow `shared-references/workspace-layout.md` to ensure `.job-scout/` exists.

## Step 1: Resolve the job

`/interview-prep <tracker-id>` requires a tracker ID. The user has decided to interview for this specific job; the ID points to the JD blob already in the tracker.

If the ID is not in the tracker, error: "No tracker entry for `<id>`. Run `/check-job-notifications` or `/match-jobs` first to ingest the job."

If the ID exists but `tracker.jobs.<id>.description` is missing or stub-only (the original sweep didn't fully extract the JD), prompt the user to provide the JD URL so the orchestrator can fetch it via the Chrome extension.

## Step 2: Load inputs

- **The job:** `tracker.jobs.<id>` — title, company, full JD blob.
- **User profile:** `.job-scout/user-profile.json` — `cv_summary`, all roles (from cache: `.job-scout/cache/cv-<hash>.json`), `target_roles`, `requirements`.
- **Supporting docs index:** `.job-scout/cache/supporting-docs.json` — for evidence citations in SPAR narratives.
- **Master keyword list:** `user-profile.json.master_keyword_list`.
- **JD-specific keywords:** extract from the JD blob using `shared-references/jd-keyword-extraction.md` (extraction step only).
- **Recruiter notes (optional):** scan `.job-scout/recruiters/threads.json` for any thread where `company` matches the job's company. If found, load that thread's `notes` array.
- **Company-researcher digest (optional):** if the orchestrator wants company context, dispatch `company-researcher/SKILL.md` per `shared-references/subagent-protocol.md` with the JD blob and the supporting-docs paths. This is optional — skip if the JD already provides sufficient company context.

## Step 3: Synthesise the prep packet

Produce these sections in order:

### 1. Top 5 SPAR narratives

Identify the 5 strongest CV bullets relevant to this job. For each, expand to a full **Situation → Problem → Action → Result** narrative (3-5 sentences). Tag each narrative with the predicted interview questions it answers:

```
**SPAR 1:** Inherited a stalled platform migration blocked by cross-team dependencies (S)...
- Answers: "Tell me about a time you led a complex project"
- Answers: "How do you handle cross-functional coordination?"
- Answers: "Describe a time you turned around a failing initiative"
```

Where a SPAR is backed by a supporting doc (case study, talk, etc.), cite the path.

### 2. Predicted questions (10-15)

Categorise:

- **Technical (4-6):** drawn from required-skills section of the JD. "Explain how you'd design a real-time payments pipeline using Kafka."
- **Behavioural (4-6):** drawn from soft-skill phrases in the JD. "How do you handle stakeholder conflict?" "Tell me about a time you disagreed with a manager."
- **Situational (2-3):** drawn from the JD's responsibility list. "You're 6 weeks into a 3-month migration and the deadline shifts in by 4 weeks — what do you do?"

For each question, note which SPAR(s) from section 1 are the best response.

### 3. 5 questions to ask them

Specific to this role/company. Drawn from:

- The JD (gaps, ambiguities)
- The company-researcher digest (red flags, growth stage) — if obtained
- The user's deal-breakers / nice-to-haves from `user-profile.json.requirements`
- Recruiter notes (anything still pending or worth confirming)

Examples of acceptable questions:
- "What's the team's on-call rotation? The JD mentions production SRE responsibilities but doesn't specify."
- "I noticed the team grew from 5 to 14 in the past year — how is the architecture evolving to match?"
- "Recruiter mentioned the role is outside IR35. Can you confirm the engagement structure and notice period?"

**Forbidden:** generic questions like "What's the company culture like?" or "Tell me about the team." These signal lack of preparation.

### 4. Risk areas (up to 5)

Gaps between CV and JD where the interviewer may push:

```
**Risk 1:** JD requires Kubernetes experience; your CV mentions only Docker.
- Address proactively: "I've worked extensively with Docker and have done [specific Kubernetes-adjacent thing]. The transition is something I'm actively building toward."
- Reference: <supporting doc if applicable>
```

### 5. Recent company signals

If `company-researcher` returned reputation digest items or red flags, surface them:

```
**Signal 1:** Company recently raised Series C ($120M) — likely scaling pressure.
   Conversation hook: "Congratulations on the Series C — how is the engineering org adapting to scale?"

**Signal 2:** Glassdoor mentions long hours during product launches.
   Worth checking: "How does the team handle launch-period intensity? What's the recovery cadence after?"
```

If no `company-researcher` signals are available, this section is omitted.

## Step 4: Write the prep packet

Save to `.job-scout/interview-prep/<job_id>.md` with this format:

```markdown
---
job_id: 1234567890
job_title: Senior Data Engineer
company: Acme Corp
generated: <ISO timestamp>
---

# Interview Prep: [Job Title] at [Company]

## Top 5 SPAR Narratives
[content]

## Predicted Questions
[content]

## Questions to Ask Them
[content]

## Risk Areas
[content]

## Recent Company Signals
[content or omit]
```

Confirm to the user with the file path.

## State files

- **`.job-scout/interview-prep/`** — output directory. Per-job markdown files.
- **`.job-scout/tracker.json`** — read-only.
- **`.job-scout/recruiters/threads.json`** — read-only (for company-matched notes).
- **`.job-scout/user-profile.json`** — read-only.
- **`.job-scout/cache/supporting-docs.json`** — read-only.

## Reference Materials

- **`../shared-references/jd-keyword-extraction.md`** — keyword extraction (extraction step only)
- **`../shared-references/supporting-docs.md`** — supporting-docs consumer contract
- **`../shared-references/subagent-protocol.md`** — for optional company-researcher dispatch
- **`../company-researcher/SKILL.md`** — optional company context
- **`../shared-references/workspace-layout.md`** — bootstrap + state layout
- **`../cv-optimizer/references/psychology-cheatsheet.md`** — informs SPAR narrative framing
===FILE_END===

- [ ] **Step 3: Verify**

```bash
cd /Users/tura/git/claude-job-scout && ls skills/interview-prep/SKILL.md
```
Expected: file exists.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "SPAR" skills/interview-prep/SKILL.md
```
Expected: at least `3`.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "Predicted questions\|Risk areas" skills/interview-prep/SKILL.md
```
Expected: at least `2`.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "disable-model-invocation: true" skills/interview-prep/SKILL.md
```
Expected: `1`.

```bash
cd /Users/tura/git/claude-job-scout && wc -l skills/interview-prep/SKILL.md
```
Expected: roughly 110-140 lines.

```bash
cd /Users/tura/git/claude-job-scout && git diff --stat
```
Expected: 1 file (new).

- [ ] **Step 4: Commit + push**

```bash
cd /Users/tura/git/claude-job-scout && git add skills/interview-prep/ && git commit -m "$(cat <<'EOF'
Add /interview-prep slash command

Generates interview-prep packet for a specific tracker-ID job:
top 5 SPAR narratives mapped to predicted questions, 10-15 predicted
questions (technical / behavioural / situational), 5 specific
questions to ask them, up to 5 risk areas with proactive framing,
and optional company-researcher signals as conversation hooks.
Output saved to .job-scout/interview-prep/<job_id>.md. No subagent
dispatch — synthesis is bounded and inputs already loaded.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)" && git push -u origin phase-3/task-05-interview-prep
```

---

## Task 6: `/funnel-report` slash command

**Files:**
- Create: `/Users/tura/git/claude-job-scout/skills/funnel-report/SKILL.md`

- [ ] **Step 1: Create branch + dir**

```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-3/task-06-funnel-report && mkdir -p skills/funnel-report
```

- [ ] **Step 2: Write `funnel-report/SKILL.md`**

Create `/Users/tura/git/claude-job-scout/skills/funnel-report/SKILL.md` with exactly:

===FILE_START===
---
name: funnel-report
description: Show where the user stands across the job-search pipeline (30/60/90 day windows, drop-offs, trending keywords, suggested next actions)
allowed-tools: Read, Write, Bash, Glob, Grep
disable-model-invocation: true
---

Generate a pipeline analytics report showing the user's job-search funnel — counts at each stage, conversion rates, drop-offs, recruiter pipeline, trending keywords from the corpus, and 3 prioritised suggested next actions.

No subagent dispatch — synthesis is bounded and inputs are JSON state files.

## Step 0: Bootstrap workspace

Follow `shared-references/workspace-layout.md` to ensure `.job-scout/` exists.

## Step 1: Load data sources

| Source | What it provides |
|--------|------------------|
| `.job-scout/tracker.json` | Hot tracker — recent jobs at every stage |
| `.job-scout/archive/tracker-<current-year>.json` | Aged `seen` jobs that rotated out (current year only) |
| `.job-scout/recruiters/threads.json` | Recruiter pipeline — notes, last activity, lead tier |
| `.job-scout/cache/jd-keyword-corpus.json` | Trending keywords (frequency-delta calculation) |

If any of `archive/tracker-<year>.json`, `threads.json`, or `jd-keyword-corpus.json` are missing, treat them as empty and proceed (the report degrades gracefully).

## Step 2: Compute the funnel

Funnel stages, in order:

```
seen → scored → A-tier → approved → applied → recruiter replied → interview → offer
```

Computation:

- **seen:** count of all tracker entries (hot + current-year archive) where `status` is non-null.
- **scored:** count where `score` is non-null.
- **A-tier:** count where `tier == "A"`.
- **approved:** count where `status == "approved"`.
- **applied:** count where `status == "applied"`.
- **recruiter replied:** count of threads in `threads.json` with at least one message after the user's most recent `last_drafted_reply` for that thread (best-effort — if the message-after-reply detection is ambiguous, count threads where `last_seen_msg_id` differs from `last_drafted_reply` and `last_updated` is more recent than `last_drafted_reply`).
- **interview:** count of tracker entries where `notes` field contains "interview" (free-text — the user marks it manually).
- **offer:** count of tracker entries where `notes` field contains "offer".

Compute these counts for three windows: **30 days**, **60 days**, **90 days** — based on tracker entry `last_seen` field.

## Step 3: Compute conversion rates and trend lines

For each window, compute conversion rate between adjacent stages:

```
seen→scored: scored / seen
scored→A-tier: A-tier / scored
A-tier→approved: approved / A-tier
approved→applied: applied / approved
applied→recruiter-replied: replied / applied
```

For trend lines, compute week-over-week deltas (last 7 days vs prior 7 days) for: seen count, A-tier ratio, applied count, recruiter reply rate.

## Step 4: Identify the top drop-off

The stage with the largest conversion-rate drop in the 30-day window. Map to a recommendation:

| Top drop-off | Recommendation |
|-------------|----------------|
| `applied → recruiter replied` | "Cover letters may not be landing. Consider tightening the recruiter-gate angle (try `/cover-letter` with the latest A-tier job)." |
| `A-tier → approved` | "You're seeing good matches but not approving them. Are deal-breakers misconfigured? Re-check `user-profile.json.requirements`." |
| `seen → A-tier` | "Few A-tier matches. Check that the master keyword list reflects current targets — re-run `/analyze-cv`." |
| `approved → applied` | "Approved jobs piling up unapplied. Run `/apply` on the backlog." |
| `scored → A-tier` | "Your scoring threshold may be too strict, or the JDs you're seeing don't match your profile." |
| `seen → scored` | "Scoring failures — check that CV and profile hashes are stable. Re-run `/analyze-cv` if the CV changed." |

If no stage shows a clear drop (rates within 10% of each other), report "Pipeline is balanced — no significant drop-off."

## Step 5: Trending keywords

Read `.job-scout/cache/jd-keyword-corpus.json`. For each keyword:

1. Compute `frequency_last_30d` = sum of source_jobs whose tracker entry has `first_seen` within the last 30 days.
2. Compute `frequency_prior_30d` = sum of source_jobs whose tracker entry has `first_seen` between 30 and 60 days ago.
3. Compute `delta` = `frequency_last_30d` - `frequency_prior_30d`.
4. Sort by absolute `delta` descending.
5. Take the top 10. Filter to terms with `frequency_last_30d >= 3` (avoid one-off noise).

Report as: "Heating up: Kubernetes (+8), Rust (+5), MLOps (+3). Cooling: Hadoop (-4), jQuery (-2)."

## Step 6: Recruiter pipeline summary

From `.job-scout/recruiters/threads.json`, list open hot/warm leads:

- `lead_tier == "hot"` or `lead_tier == "warm"`
- AND `last_updated` within last 30 days

For each, show: company, last activity date (days ago), known facts (from `notes` array), suggested next action.

Suggested next action rules:
- Last contact 0-3 days ago: "Wait — recruiter likely responding."
- Last contact 4-7 days ago: "Awaiting response. Follow up in 2-3 days if no reply."
- Last contact 8-14 days ago: "Follow up now. Brief check-in is appropriate."
- Last contact 15+ days ago: "Likely cold. One last touch or move on."

## Step 7: Suggested next actions (top 3)

Synthesise from the analysis:

1. **Top job to apply to:** highest-scored A-tier job with `status: "approved"` not yet `"applied"`. Or, if no approved-not-applied: highest-scored A-tier with `status: "seen"` (suggest user reviews + approves).
2. **Top recruiter to follow up:** hottest lead with stalest contact (largest `(lead_tier_score) × (days_since_last_contact)`).
3. **Top profile improvement:** drawn from the top drop-off's recommendation. If no drop-off, suggest the top trending keyword from Step 5 ("Add `Rust` to your Skills section — it's heating up in your market").

## Step 8: Write the report

Save to `.job-scout/reports/<YYYY-MM-DD>-funnel.md`. Format:

```markdown
---
generated: <ISO timestamp>
window: rolling 30/60/90 days
---

# Funnel Report — <YYYY-MM-DD>

## Pipeline (30/60/90 days)

| Stage | 30d | 60d | 90d | 30d→60d Δ |
|-------|-----|-----|-----|-----------|
| seen | ... | ... | ... | ... |
| ... | ... | ... | ... | ... |

## Conversion Rates (30 day window)
[content]

## Trend Lines (week-over-week)
[content]

## Top Drop-Off
**[stage]** — [recommendation]

## Trending Keywords
[content]

## Recruiter Pipeline
[content]

## Suggested Next Actions
1. [content]
2. [content]
3. [content]
```

Confirm to the user with the file path. Suggest re-running weekly.

## State files

- **`.job-scout/reports/`** — output directory.
- **All data sources are read-only** here. The report does not modify state.

## Reference Materials

- **`../shared-references/tracker-schema.md`** — tracker.json shape (read), archive policy
- **`../shared-references/supporting-docs.md`** — not needed in Phase 3, but referenced for completeness
- **`../shared-references/workspace-layout.md`** — bootstrap + state layout
- **`../recruiter-engagement/SKILL.md`** — for `notes` array shape (read)
===FILE_END===

- [ ] **Step 3: Verify**

```bash
cd /Users/tura/git/claude-job-scout && ls skills/funnel-report/SKILL.md
```
Expected: file exists.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "30/60/90\|30d\|60d\|90d" skills/funnel-report/SKILL.md
```
Expected: at least `5`.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "drop-off\|Drop-Off" skills/funnel-report/SKILL.md
```
Expected: at least `3`.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "Trending\|trending" skills/funnel-report/SKILL.md
```
Expected: at least `2`.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "disable-model-invocation: true" skills/funnel-report/SKILL.md
```
Expected: `1`.

```bash
cd /Users/tura/git/claude-job-scout && wc -l skills/funnel-report/SKILL.md
```
Expected: roughly 130-160 lines.

```bash
cd /Users/tura/git/claude-job-scout && git diff --stat
```
Expected: 1 file (new).

- [ ] **Step 4: Commit + push**

```bash
cd /Users/tura/git/claude-job-scout && git add skills/funnel-report/ && git commit -m "$(cat <<'EOF'
Add /funnel-report slash command

Pipeline analytics report. Reads tracker (hot + current-year archive),
threads.json, and jd-keyword-corpus.json. Computes 30/60/90-day funnel
counts, conversion rates between adjacent stages, week-over-week trend
lines, top drop-off with prescriptive recommendation, top-10 trending
corpus keywords (frequency-delta), recruiter pipeline summary with
follow-up rules, and 3 prioritised suggested next actions. Output
saved to .job-scout/reports/<date>-funnel.md.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)" && git push -u origin phase-3/task-06-funnel-report
```

---

## Task 7: Release v0.6.0

**Files:**
- Modify: `/Users/tura/git/claude-job-scout/.claude-plugin/plugin.json`
- Modify: `/Users/tura/git/claude-job-scout/CHANGELOG.md`
- Modify: `/Users/tura/git/claude-job-scout/docs/ROADMAP.md`
- Modify: `/Users/tura/git/claude-job-scout/README.md` (commands table — add the 4 new commands)

- [ ] **Step 1: Create branch (merge LAST, after Tasks 1-6)**

```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-3/task-07-release
```

- [ ] **Step 2: Bump plugin version**

In `/Users/tura/git/claude-job-scout/.claude-plugin/plugin.json`, change `"version": "0.5.0"` to `"version": "0.6.0"`.

- [ ] **Step 3: Add 0.6.0 CHANGELOG section**

Use today's date (the actual merge date). Insert before `## [0.5.0]`:

```markdown
## [0.6.0] — 2026-MM-DD

Phase 3 of the v0.4.0–v0.6.0 roadmap: new user-facing commands. Surfaces the infrastructure built in Phases 1 and 2 as four new slash commands plus two daily-workflow enhancements.

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
```

Update `2026-MM-DD` to the actual merge date.

- [ ] **Step 4: Update README commands table**

Find the existing commands table in `/Users/tura/git/claude-job-scout/README.md` (a markdown table with columns "Command" and "Description"). Append four new rows after the existing rows (preserve the existing 8 commands):

```
| `/cover-letter` | Generate a tailored cover letter (3 angle options) for a specific job |
| `/interview-prep` | Generate an interview-prep packet (SPAR narratives, predicted questions, questions to ask) for a specific job |
| `/funnel-report` | Pipeline analytics: 30/60/90-day funnel, drop-offs, trending keywords, suggested next actions |
| `/index-docs` | Re-scan workspace for supporting documents and rebuild the index |
```

The total commands count after this edit should be 12.

- [ ] **Step 5: Update ROADMAP**

In `/Users/tura/git/claude-job-scout/docs/ROADMAP.md`:

1. **Status table** — change Phase 3 row from "In design" to "Shipped — v0.6.0", and add the plan link in the Plan column (currently "—"). The row should read:
```
| 3. New user-facing commands | v0.6.0 | Shipped — v0.6.0 | [`specs/2026-04-17-phase-3-user-facing-commands-design.md`](superpowers/specs/2026-04-17-phase-3-user-facing-commands-design.md) | [`plans/2026-04-17-phase-3-user-facing-commands.md`](superpowers/plans/2026-04-17-phase-3-user-facing-commands.md) |
```

2. **Current focus line** — find:
```
**Current focus:** Phase 3 design spec.
```
Replace with:
```
**Current focus:** All three phases complete. Plugin is at v0.6.0. Future phases gated on user need.
```

3. **Phase 3 section** — convert the existing bullet list to checkbox format and tick all 6 items. Find:
```
## Phase 3 — v0.6.0: New user-facing commands

Each command surfaces capabilities built in Phases 1–2. Spec to be written after Phase 2 ships.

- `/cover-letter <tracker-id|url>` + `cover-letter-writer` subagent
- `/interview-prep <tracker-id>`
- `/funnel-report`
- `/index-docs` (explicit command over Phase 1 cache)
- Daily-driver context line (`last run N days ago, X alerts since`)
- Bootstrap nudge to index supporting docs on first run
```

Replace with:
```
## Phase 3 — v0.6.0: New user-facing commands

Each command surfaces capabilities built in Phases 1–2.

- [x] **`/index-docs`** (explicit re-scan over Phase 1 supporting-docs cache)
- [x] **Bootstrap nudge** to index supporting docs on first run
- [x] **Daily-driver context line** in `/check-job-notifications`
- [x] **`/cover-letter <tracker-id|url>`** + `cover-letter-writer` subagent
- [x] **`/interview-prep <tracker-id>`**
- [x] **`/funnel-report`**
```

4. **Append a Log entry**. Find the most recent log entry (most likely the Phase 2 shipped entry) and append after it:
```
- **2026-04-17** — Phase 3 shipped as v0.6.0. All three phases complete; plugin is feature-complete per the v0.4.0–v0.6.0 roadmap. Future phases gated on user need.
```

- [ ] **Step 6: Verify**

```bash
cd /Users/tura/git/claude-job-scout && jq -r .version .claude-plugin/plugin.json
```
Expected: `0.6.0`.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "^## \[0.6.0\]" CHANGELOG.md
```
Expected: `1`.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "Shipped — v0.6.0" docs/ROADMAP.md
```
Expected: `1`.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "^- \[ \]" docs/ROADMAP.md
```
Expected: `0` (no unticked checkboxes anywhere).

```bash
cd /Users/tura/git/claude-job-scout && grep -c "^| \`/" README.md
```
Expected: `12` (8 original + 4 new commands in the table).

```bash
cd /Users/tura/git/claude-job-scout && git diff --stat
```
Expected: 4 files changed.

- [ ] **Step 7: Commit + push**

```bash
cd /Users/tura/git/claude-job-scout && git add .claude-plugin/plugin.json CHANGELOG.md docs/ROADMAP.md README.md && git commit -m "$(cat <<'EOF'
Release v0.6.0 — Phase 3 complete

Bumps plugin version, adds CHANGELOG 0.6.0 section, updates ROADMAP
to mark Phase 3 shipped (all three roadmap phases now complete), and
adds the 4 new commands to README's commands table.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)" && git push -u origin phase-3/task-07-release
```

---

## Self-review

### Spec coverage

| Spec component | Task |
|----------------|------|
| 1. `/cover-letter` + cover-letter-writer | Task 4 |
| 2. `/interview-prep` | Task 5 |
| 3. `/funnel-report` | Task 6 |
| 4. `/index-docs` | Task 1 |
| 5. Daily-driver context line | Task 3 |
| 6. Bootstrap nudge for supporting docs | Task 2 |

All 6 spec components covered. Task 7 handles release.

### Placeholder scan

One deliberate placeholder: `2026-MM-DD` in Task 7's CHANGELOG — the merge date isn't known at plan-write time.

### Type consistency

- `tracker.json` schema referenced consistently across Tasks 3, 4, 5, 6.
- `supporting-docs.json` referenced consistently in Tasks 1, 4, 5.
- `threads.json` (with `notes` array from Phase 2) referenced consistently in Tasks 5, 6.
- `jd-keyword-corpus.json` (Phase 2) referenced consistently in Task 6.
- `linkedin-profile.json` referenced in Task 4 for voice sample.
- Subagent dispatch shape in Task 4 matches `subagent-protocol.md` from Phase 1.

## Execution handoff

**Plan complete and saved to `docs/superpowers/plans/2026-04-17-phase-3-user-facing-commands.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration. Same proven pattern as Phases 1 and 2.

**2. Inline Execution** — Execute tasks in this session using `executing-plans`, batch execution with checkpoints.

**Which approach?**

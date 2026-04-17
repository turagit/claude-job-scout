# Phase 3 — New User-Facing Commands (v0.6.0)

**Date:** 2026-04-17
**Status:** In design — pending user review
**Target release:** v0.6.0

## Why this phase exists

Phases 1 and 2 built the infrastructure: subagent protocol, progressive-disclosure splits, state layout reconciliation, learned keyword corpus, ATS simulator, supporting-docs index, recruiter lead-memory. Phase 3 surfaces that infrastructure to users as new slash commands — `/cover-letter`, `/interview-prep`, `/funnel-report`, `/index-docs` — plus two small UX enhancements that make the daily workflow smoother.

The plugin is currently CV-and-LinkedIn-heavy. Phase 3 closes the loop by giving the user direct commands for the next stages: cover letter generation, interview preparation, pipeline analytics, and explicit doc-index control.

## Goals

- Generate tailored cover letters that cite the user's supporting documents and offer the user three angle options (hiring manager, recruiter gate, culture match).
- Produce interview-prep packets per job: SPAR narratives, predicted questions, questions to ask, risk areas, recent company signals.
- Show the user where they stand across the job-search funnel and what to do next.
- Give the user explicit control over the supporting-docs index (re-scan, opt back in after declining).
- Make the daily-driver command (`/check-job-notifications`) open with a one-line context summary so the user knows the situation before any work runs.
- Nudge the user to index supporting docs at workspace bootstrap if any are detected.

## Non-goals (explicitly deferred)

- **Cover letter PDF generation** — output is markdown; PDF conversion is the user's tool of choice.
- **Live interview Q&A simulation** — the prep packet is offline material, not an interactive coach.
- **Funnel-report email/Slack delivery** — output is a markdown file; the user reads it in their editor.
- **Auto-application based on funnel recommendations** — the user always approves applications.

---

## Component 1: `/cover-letter <tracker-id|url>`

### New skills

- `skills/cover-letter/SKILL.md` — slash command + orchestrator. User-invocable.
- `skills/cover-letter-writer/SKILL.md` — internal subagent. Not user-invocable.

### Invocation

| Form | Behaviour |
|------|-----------|
| `/cover-letter <tracker-id>` | Use the JD blob already in `tracker.json` for that ID. Fastest path. |
| `/cover-letter <linkedin-url>` | Fetch the JD via the Chrome extension (browser-policy applies). |
| `/cover-letter` (no arg) | Present the user's recent A-tier jobs from the tracker; let them pick. |

### Inputs the command gathers

1. The job (title, company, JD blob, source).
2. The user profile (`user-profile.json` → cv_summary, target_roles, tone_preference).
3. The supporting-docs index (`supporting-docs.json`) — the writer cites docs by path.
4. The master keyword list + JD-specific keywords for keyword density.
5. The cached LinkedIn profile (for tone/voice continuity).

### Three angle options

The writer always returns three drafts so the user can pick the one that fits the situation:

| Angle | Lead with | Best for |
|-------|-----------|----------|
| **Hiring-manager pitch** | The candidate's strongest CV achievement, framed against the JD | Roles where the hiring manager will read directly; established companies |
| **Recruiter-gate** | Keyword-dense opening mirroring the JD's language | Larger companies with ATS + recruiter screening |
| **Culture-match** | Shared values / mission, references the company's own messaging | Mission-driven companies, public-benefit orgs, scale-ups with strong culture brand |

Each draft: ~250-350 words, structured as **hook → 2-3 evidence paragraphs (CV achievements + supporting-doc citations) → close with a specific ask**.

### Subagent dispatch

`cover-letter` orchestrator dispatches `cover-letter-writer` per `shared-references/subagent-protocol.md`:

```json
{
  "task": "draft-cover-letter",
  "inputs": {
    "job": { "title": "...", "company": "...", "jd_blob": "...", "source": "tracker | url" },
    "user_profile": { "cv_summary": {...}, "target_roles": [...], "tone_preference": "..." },
    "supporting_docs_index": { "paths": [...], "types": [...] },
    "target_keywords": ["..."],
    "linkedin_voice_sample": "<first 500 chars of About>"
  },
  "budget_lines": 200,
  "allowed_tools": ["Read"]
}
```

Subagent returns:

```json
{
  "status": "ok",
  "deltas": [
    { "angle": "hiring-manager", "draft": "...", "supporting_docs_cited": ["certs/aws-sa-pro.pdf"] },
    { "angle": "recruiter-gate", "draft": "...", "supporting_docs_cited": [] },
    { "angle": "culture-match", "draft": "...", "supporting_docs_cited": ["case-studies/..."] }
  ]
}
```

Main thread presents all three to the user with a side-by-side comparison of the openers. User picks one (or asks for an edit). The chosen draft is saved.

### Output

Saved to `.job-scout/cover-letters/<job_id>-<angle>.md`. Format:

```markdown
---
job_id: 1234567890
job_title: Senior Data Engineer
company: Acme Corp
angle: hiring-manager
generated: 2026-04-17T15:30:00Z
supporting_docs_cited:
  - certs/aws-sa-pro.pdf
  - case-studies/migration-2024.pdf
---

[Body of the cover letter]
```

### Fallback

If the `Agent` tool is unavailable, fall back to sequential in-thread drafting (one angle at a time).

---

## Component 2: `/interview-prep <tracker-id>`

### New skill

`skills/interview-prep/SKILL.md` — slash command + orchestrator. User-invocable. No subagent dispatch — runs in-thread because the synthesis is bounded and the inputs are already loaded.

### Invocation

`/interview-prep <tracker-id>` (tracker ID required — the user has decided to interview for this specific job). If the ID is not in the tracker, error and suggest `/check-job-notifications` first.

### Inputs

- The job (from tracker).
- The user profile (cv_summary, all roles, target_roles).
- The supporting-docs index (for evidence citations).
- The master keyword list + JD-specific keywords.
- Recruiter notes for the company (`threads.json` → notes for any thread with this company).
- Optional: company-researcher digest (if the orchestrator dispatches it for this run).

### Output sections

1. **Top 5 SPAR narratives.** Full-story versions of the user's strongest CV bullets (Situation → Problem → Action → Result). Each narrative tagged with predicted interview questions it answers ("Tell me about a time you led a complex project", "Walk me through a difficult technical decision").

2. **Predicted questions (10-15).** Inferred from the JD:
   - **Technical:** drawn from required-skills section ("Explain how you'd design a real-time payments pipeline using Kafka")
   - **Behavioural:** drawn from soft-skill phrases in the JD ("How do you handle stakeholder conflict?")
   - **Situational:** drawn from the JD's responsibility list ("You're 6 weeks into a 3-month migration and the deadline shifts in by 4 weeks — what do you do?")

3. **5 questions to ask them.** Specific to this role/company. Drawn from:
   - The JD (gaps, ambiguities)
   - The company-researcher digest (red flags, growth stage)
   - The user's deal-breakers / nice-to-haves from `user-profile.json` (IR35, on-call expectations, team size)
   - Recruiter notes (anything still pending or worth confirming)

   Generic questions like "What's the company culture like?" are forbidden.

4. **Risk areas.** Gaps between CV and JD ("JD requires Kubernetes; your CV only mentions Docker — be ready to discuss the transition path or relevant equivalents"). Up to 5.

5. **Recent company signals.** If `company-researcher` returned reputation digest items or red flags, surface them as conversation starters or topics to navigate carefully.

### Output

Saved to `.job-scout/interview-prep/<job_id>.md`.

---

## Component 3: `/funnel-report`

### New skill

`skills/funnel-report/SKILL.md` — slash command. User-invocable. No subagent — the synthesis is bounded.

### Invocation

`/funnel-report` (no args). Default window: rolling 30/60/90 days.

### Data sources

| Source | What it provides |
|--------|------------------|
| `.job-scout/tracker.json` | Hot tracker — recent jobs at every stage |
| `.job-scout/archive/tracker-YYYY.json` (current year) | Aged `seen` jobs that rotated out |
| `.job-scout/recruiters/threads.json` | Recruiter pipeline — notes, last activity, lead tier |
| `.job-scout/cache/jd-keyword-corpus.json` | Trending keywords (frequency-delta) |

### Funnel stages

```
seen → scored → A-tier → approved → applied → recruiter replied → interview → offer
```

Each stage is computable from existing tracker fields:
- `seen`: any tracker entry with `status: "seen"`
- `scored`: any tracker entry with non-null `score`
- `A-tier`: tracker entries with `tier: "A"`
- `approved`: `status: "approved"`
- `applied`: `status: "applied"`
- `recruiter replied`: thread in `threads.json` with messages after the user's last drafted reply
- `interview`: tracker `notes` field (free-text — the user marks it manually)
- `offer`: same — manual marker

### Output sections

1. **30/60/90-day funnel table.** Counts at each stage, conversion rate between stages.

2. **Trend lines.** Week-over-week deltas for: seen count, A-tier ratio (A-tier / scored), applied count, recruiter reply rate.

3. **Recruiter pipeline summary.** Open hot/warm leads from `threads.json`: company, last activity date, known facts (from lead-memory notes), suggested next action ("Follow up — last contact 9 days ago").

4. **Top drop-off.** The stage with the largest conversion-rate drop, with a recommendation:
   - High `applied → recruiter replied` drop → "Cover letters may not be landing. Consider tightening the recruiter-gate angle."
   - High `A-tier → approved` drop → "You're seeing good matches but not approving them. Are deal-breakers misconfigured?"
   - High `seen → A-tier` drop → "Few A-tier matches. Check that the master keyword list reflects current targets."

5. **Trending keywords.** Top 10 corpus keywords by frequency-delta over the last 30 days vs the prior 30 days. Surfaces what's heating up in the user's market — actionable for CV/profile updates.

6. **Suggested next actions.** 3 prioritised actions:
   - Jobs to apply to (top 3 unapplied A-tier)
   - Recruiter threads to follow up on (top 3 by lead tier × days since last contact)
   - Profile sections to update (drawn from drop-off analysis)

### Output

Saved to `.job-scout/reports/<YYYY-MM-DD>-funnel.md`.

---

## Component 4: `/index-docs`

### New skill

`skills/index-docs/SKILL.md` — slash command. User-invocable.

### Purpose

Phase 1's `supporting-docs.md` reference defines bootstrap-time scanning. Phase 3 surfaces it as an explicit user command for:

- Re-scanning after the user adds new docs to the workspace
- Opting back in after declining at bootstrap
- Inspecting the current index without running another command first

### Behaviour

1. Bootstrap workspace (per `shared-references/workspace-layout.md`).
2. Load existing `.job-scout/cache/supporting-docs.json` (or treat as empty if missing).
3. Run the workspace scan defined in `shared-references/supporting-docs.md` Re-indexing section.
4. Compute the diff:
   - **New files** — extensions match, not in current index.
   - **Re-indexed files** — content hash changed since last index.
   - **Missing files** — were in index, file no longer at path.
5. Present the diff to the user with counts and the first 10 of each category.
6. Ask for confirmation. On approval, write the updated index. On decline, leave the index untouched but report what would have changed.

### Special interaction: opt-back-in

The supporting-docs reference says "if user declined indexing at bootstrap, the workspace remains opted-out: skip adding or updating entries." Running `/index-docs` overrides that opt-out for this and future sessions. The command displays a one-line confirmation: "Re-enabling supporting-docs indexing for this workspace."

### Output

The command returns a summary to the user (no file output unless the user requests `/index-docs --report`).

---

## Component 5: Daily-driver context line in `/check-job-notifications`

### Purpose

Make the most-used command's first output a one-line situational summary so the user knows what they're walking into.

### Implementation

Add Step 0a to `skills/check-job-notifications/SKILL.md`, between Step 0 (bootstrap) and Step 1 (load CV).

**Output format (when `tracker.json` has prior runs):**

```
📊 Last run [N] days ago. Tracker: [seen] seen, [A-tier] A-tier, [applied] applied.
   New since last run: [N] alerts.
```

**Output format (first run):**

```
🚀 First run. Setting up tracker.
```

The "new since last run" count is best-effort — it requires comparing the current notifications page to `tracker.last_run`. If the count can't be computed cheaply, omit that line.

### Cost

Single read of `tracker.stats`. Single comparison against current ISO timestamp. No browser interaction beyond what Step 1 already does.

---

## Component 6: Bootstrap nudge to index supporting docs

### Purpose

When `.job-scout/` is first created, if supporting docs are detected in the workspace, prompt the user to index them right away rather than waiting for a separate command.

### Implementation

Extend bootstrap step 4 in `shared-references/workspace-layout.md`. After all the standard files are written (schema-version, user-profile, tracker, supporting-docs.json stub), run a quick `Glob` for likely supporting-doc files at the workspace root: `*.pdf`, `*.docx`, `*.pptx`, `*.md`, `*.txt`. Filter out the CV (`cv.*`, `resume.*`, `curriculum.*`).

If 1+ files found:

```
📎 I noticed [N] files in your workspace that look like supporting materials
   (certs, talks, decks, recommendations). Indexing them now will make every 
   future CV rewrite, profile proposal, and cover letter sharper.

   Run /index-docs now? (Y/n)
```

If user accepts, dispatch `/index-docs` immediately. If declines, remember per session (the supporting-docs reference's opt-out behaviour applies).

### No edit needed if zero files found

If the glob returns zero supporting-doc files, the bootstrap proceeds silently. The user can run `/index-docs` later when they add docs.

---

## Data shapes introduced or changed in Phase 3

| File | Phase 3 change |
|------|----------------|
| `.job-scout/cover-letters/` | New directory. Per-letter markdown files keyed by `<job_id>-<angle>.md`. |
| `.job-scout/interview-prep/` | New directory. Per-job markdown files keyed by `<job_id>.md`. |
| `.job-scout/reports/<YYYY-MM-DD>-funnel.md` | New report type alongside existing `<YYYY-MM-DD>-new-jobs.md`. |
| `.job-scout/tracker.json` | No schema change — existing fields support funnel computation. |
| `.job-scout/cache/supporting-docs.json` | No schema change — `/index-docs` reads/writes the existing shape. |

## Files created or modified

| File | Change | Component |
|------|--------|-----------|
| `skills/cover-letter/SKILL.md` | New | 1 |
| `skills/cover-letter-writer/SKILL.md` | New (subagent) | 1 |
| `skills/interview-prep/SKILL.md` | New | 2 |
| `skills/funnel-report/SKILL.md` | New | 3 |
| `skills/index-docs/SKILL.md` | New | 4 |
| `skills/check-job-notifications/SKILL.md` | Modify (add Step 0a) | 5 |
| `skills/shared-references/workspace-layout.md` | Modify (extend bootstrap step 4 with supporting-docs nudge) | 6 |

## Rollout

- Single `main` branch, feature-by-feature merges — same pattern as Phases 1 and 2.
- Version bump to 0.6.0 on the final task.
- CHANGELOG entry summarising all components.
- ROADMAP Phase 3 checkboxes ticked per task. Once shipped, all 3 phases are complete; the roadmap shifts to a "completed" state with no Phase 4 unless a new design is initiated.

## What "done" looks like

Phase 3 ships when:

- All 6 Phase 3 Roadmap items are ticked.
- `CHANGELOG.md` has a 0.6.0 section.
- `plugin.json` reports `0.6.0`.
- A clean run of each new command on a sample workspace produces correct output (4 new commands × spot-check).
- `/check-job-notifications` opens with the context line.
- A fresh-workspace bootstrap shows the supporting-docs nudge when docs are present.
- `docs/ROADMAP.md` reflects all three phases as shipped.

## Open questions

1. **Should `/cover-letter` always present 3 angles, or let the user request just one?** **Working assumption:** always present 3 — the comparison helps the user pick. Token cost is acceptable since the subagent runs in parallel-internally (one prompt, three drafts).
2. **Should `/interview-prep` cache its output?** A re-run with the same tracker ID and unchanged inputs would produce the same packet. **Working assumption:** no caching in Phase 3 — interview prep is rare enough that fresh generation is fine. If volume grows, a simple `(job_id, cv_hash)` cache key can be added.
3. **`/funnel-report` archive read scope:** the report uses the current-year archive but not older years. Is that limit too tight? **Working assumption:** current year is right. Older archives are for `/funnel-report --window all` (a Phase 4+ extension if requested).

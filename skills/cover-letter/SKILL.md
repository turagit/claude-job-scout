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

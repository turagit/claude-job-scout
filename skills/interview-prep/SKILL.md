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

Follow `shared-references/workspace-layout.md` to ensure `.job-scout/` exists. Then follow `shared-references/render-orchestration.md` Step G (lifecycle cleanup) to archive expired report files and prune old archives — cheap directory scan; runs at the start of every Tier 1 command.

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
- **Company-researcher digest (optional):** if the orchestrator wants company context, dispatch `_company-researcher/SKILL.md` per `shared-references/subagent-protocol.md`. The dispatch payload must include `company_name` (from `tracker.jobs.<id>.company`), `job_id`, `source_blob` (the JD text), `cached_files` (matching supporting-docs paths — filter the index to docs whose filename or summary references this company), and `signals_requested` (default: `["size", "stage", "reputation", "red_flags"]`). This is optional — skip if the JD already provides sufficient company context.

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
- The _company-researcher digest (red flags, growth stage) — if obtained
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

If `_company-researcher` returned reputation digest items or red flags, surface them:

```
**Signal 1:** Company recently raised Series C ($120M) — likely scaling pressure.
   Conversation hook: "Congratulations on the Series C — how is the engineering org adapting to scale?"

**Signal 2:** Glassdoor mentions long hours during product launches.
   Worth checking: "How does the team handle launch-period intensity? What's the recovery cadence after?"
```

If no `_company-researcher` signals are available, this section is omitted.

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

## Step 5: Render

Construct a `data` payload as in `../shared-references/render-orchestration.md` Step A. View-specific fields:

- `title`: "Interview prep — {{role}}".
- `subtitle`: "{{company}} · prepared {{generated_at}}".
- `role`: full role title.
- `company`: company name.
- `url` *(optional)*: absolute LinkedIn job URL of the role being prepped — pulled from `tracker.jobs.<id>.url` when available. When present, the HTML template renders a "View posting ↗" link in the target-role banner; the markdown template wraps the role in a clickable `[role](url)`. Omit when not known.
- `filename`: `interview-prep-<role-slug>-<YYYY-MM-DD-HHMM>.html` where `<role-slug>` is `<tracker-id>-<4-char-disambiguator>`. The disambiguator is the first 4 hex characters of `sha1(role_title)` — keeps filenames distinct when re-running prep on the same tracker entry.
- `sections[]`: each is `{ id, heading, body, open_by_default }`. `id` is a short slug (e.g., `company-bg`, `tech-stack`, `hr-screen-questions`). `body` is HTML for the HTML view (use `| raw`) and markdown for the markdown view. `open_by_default` is `true` for the most-relevant section (typically the first); other folds start collapsed.

This is a time-series view — each invocation writes a new file. Lifecycle Step G (run during Step 0) archives interview-prep files older than 90 days into `.job-scout/reports/archive/` and deletes archive files older than 365 days.

Then follow `../shared-references/render-orchestration.md` end-to-end (Step G already ran in Step 0):

1. Step A — payload built above.
2. Steps B–F — read render config, dispatch `_visualizer`, open in Chrome (or fall back), handle errors.
3. Step E — print the summary line:

```
✓ Prep dossier for {{role}} at {{company}} — opened report in Chrome
```

(Or `…rendered as markdown above` when falling back.) If the `Agent` tool is unavailable, fall back to the pre-v0.7.0 markdown packet written in Step 4.

## State files

- **`.job-scout/interview-prep/`** — output directory. Per-job markdown files.
- **`.job-scout/tracker.json`** — read-only.
- **`.job-scout/recruiters/threads.json`** — read-only (for company-matched notes).
- **`.job-scout/user-profile.json`** — read-only.
- **`.job-scout/cache/supporting-docs.json`** — read-only.

## Reference Materials

- **`../shared-references/jd-keyword-extraction.md`** — keyword extraction (extraction step only)
- **`../shared-references/supporting-docs.md`** — supporting-docs consumer contract
- **`../shared-references/subagent-protocol.md`** — for optional _company-researcher dispatch
- **`../_company-researcher/SKILL.md`** — optional company context
- **`../shared-references/workspace-layout.md`** — bootstrap + state layout
- **`../_cv-optimizer/references/psychology-cheatsheet.md`** — informs SPAR narrative framing

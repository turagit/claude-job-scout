# Phase 2 — SEO / ATS Depth Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship v0.5.0 by delivering keyword intelligence (learned corpus, ATS simulator, density check), profile enrichment (supporting-doc citations, reverse-Boolean, Google snippet, banner/featured templates), and recruiter lead-memory.

**Architecture:** This plugin is a Claude Code plugin — the "code" is markdown skill files, markdown references, and per-project JSON state under `.job-scout/`. Validation is manual via shell (`jq`, `grep`, `wc`) and targeted reads.

**Tech Stack:** Markdown (CommonMark), JSON state files, Claude Agent tool for subagent dispatch, Claude Chrome extension for browser work.

**Design spec:** [`docs/superpowers/specs/2026-04-17-phase-2-seo-ats-depth-design.md`](../specs/2026-04-17-phase-2-seo-ats-depth-design.md)

**Roadmap:** [`docs/ROADMAP.md`](../../ROADMAP.md)

**Branching:** each task is one branch off `main` named `phase-2/task-NN-<short-slug>`. Controller merges directly to `main` after dual review (no PRs — `gh` CLI is unavailable).

**Merge order:** tasks are numbered to be merged **serially** in numerical order. Several tasks touch overlapping files; later tasks assume earlier merges have landed. Each task starts with `git checkout main && git pull`.

**Progress tracking:** after each task merges, tick the matching checkbox in `docs/ROADMAP.md`'s Phase 2 section.

---

## Task 1: JD keyword extraction reference + workspace-layout

**Files:**
- Create: `/Users/tura/git/claude-job-scout/skills/shared-references/jd-keyword-extraction.md`
- Modify: `/Users/tura/git/claude-job-scout/skills/shared-references/workspace-layout.md`

- [ ] **Step 1: Create branch**

```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-2/task-01-jd-keyword-extraction
```

- [ ] **Step 2: Write `jd-keyword-extraction.md`**

Create `/Users/tura/git/claude-job-scout/skills/shared-references/jd-keyword-extraction.md` with exactly:

===FILE_START===
# JD Keyword Extraction

Shared procedure for extracting keywords from job descriptions and merging them into the learned corpus. Every command that ingests JDs (`/match-jobs`, `/check-job-notifications`, `/job-search`) follows this procedure.

## When to run

After extracting job details (Step 4 in most commands) and before scoring. The extraction piggybacks on the JD text already in context — no additional LLM call is needed for the merge step.

## Extraction steps

1. Parse the JD text for **hard skills, tools, frameworks, certifications, methodologies, and domain terms**. Use `ats-keywords.md` as a seed vocabulary for recognition, but also discover terms not in the seed list (novel tools, niche frameworks, domain jargon).
2. For each extracted keyword, normalise to a canonical form: lowercase, collapse whitespace, preserve slashes and hyphens (e.g., `CI/CD`, `event-driven`). Include both acronym and spelled-out forms as separate entries (e.g., `aws` and `amazon web services`).
3. Tag `seniority_tags` from the job's experience-level field (e.g., "Senior" → `["senior"]`). Tag `role_tags` from the job's title (e.g., "Senior Data Engineer" → `["data-engineer"]`).
4. Load `.job-scout/cache/jd-keyword-corpus.json` (create if missing — see Shape below).
5. For each keyword:
   - **If it exists in the corpus:** increment `frequency`, update `last_seen`, append the job's ID to `source_jobs` (dedupe the array — no duplicate IDs).
   - **If it's new:** create the entry with `frequency: 1`, current timestamp for `first_seen` and `last_seen`, and `source_jobs: [<job_id>]`.
6. Increment `total_jds_ingested` by the number of JDs processed in this batch. Update `last_updated`.
7. Write the updated corpus back to `.job-scout/cache/jd-keyword-corpus.json`.

## Corpus file

**Location:** `.job-scout/cache/jd-keyword-corpus.json`

**Shape:**

```json
{
  "version": 1,
  "last_updated": "<ISO>",
  "total_jds_ingested": 0,
  "corpus": {
    "<keyword>": {
      "frequency": 5,
      "seniority_tags": ["senior", "lead"],
      "role_tags": ["data-engineer", "platform-engineer"],
      "first_seen": "<ISO>",
      "last_seen": "<ISO>",
      "source_jobs": ["job_id_1", "job_id_2"]
    }
  }
}
```

**Empty initial state:** `{ "version": 1, "last_updated": null, "total_jds_ingested": 0, "corpus": {} }`

## Consumers

- **cv-optimizer** (Phase 2 gap analysis): supplements the master keyword list with corpus terms the user's market actually demands.
- **ATS simulator**: uses corpus frequency to weight keyword-match scores — a keyword that appears in 80% of JDs in the user's market is more important than one that appears in 10%.
- **Density check**: uses corpus + master keyword list as the target keyword set.
- **Profile-optimizer** (keyword coverage score): compares profile keywords against corpus.

## Token cost

Negligible incremental cost. The JD text is already loaded for scoring. Extraction is a structured parse of text already in context. The corpus merge is a JSON read-merge-write with no additional LLM call.
===FILE_END===

- [ ] **Step 3: Add corpus to workspace-layout canonical layout**

In `/Users/tura/git/claude-job-scout/skills/shared-references/workspace-layout.md`, find (exact):
```
    supporting-docs.json    # index of non-CV workspace docs (see supporting-docs.md)
```
After that line, add:
```
    jd-keyword-corpus.json  # learned keyword model from ingested JDs (see jd-keyword-extraction.md)
```

- [ ] **Step 4: Verify**

```bash
cd /Users/tura/git/claude-job-scout && ls skills/shared-references/jd-keyword-extraction.md
```
Expected: file exists.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "jd-keyword-corpus" skills/shared-references/workspace-layout.md
```
Expected: at least `1`.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "jd-keyword-corpus" skills/shared-references/jd-keyword-extraction.md
```
Expected: at least `3`.

```bash
cd /Users/tura/git/claude-job-scout && git diff --stat
```
Expected: 2 files (1 new + 1 modified).

- [ ] **Step 5: Commit + push**

```bash
cd /Users/tura/git/claude-job-scout && git add skills/shared-references/jd-keyword-extraction.md skills/shared-references/workspace-layout.md && git commit -m "$(cat <<'EOF'
Add JD keyword extraction reference and corpus layout entry

New shared reference documenting the extraction procedure, corpus
shape, normalisation rules, and consumer list. Workspace-layout gains
jd-keyword-corpus.json in the cache directory listing.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)" && git push -u origin phase-2/task-01-jd-keyword-extraction
```

---

## Task 2: Wire corpus extraction into job-processing commands

**Files:**
- Modify: `/Users/tura/git/claude-job-scout/skills/match-jobs/SKILL.md`
- Modify: `/Users/tura/git/claude-job-scout/skills/check-job-notifications/SKILL.md`
- Modify: `/Users/tura/git/claude-job-scout/skills/job-search/SKILL.md`

- [ ] **Step 1: Create branch**

```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-2/task-02-corpus-wiring
```

- [ ] **Step 2: Add corpus extraction to `match-jobs/SKILL.md`**

Read the current file. Find the `## Step 4: Extract and score new jobs (parallel)` section. After the extraction paragraph ("For each *new* job, extract title, company...") and before the `**Scoring fan-out:**` paragraph, insert a corpus-extraction note.

Find (exact):
```
For each *new* job, extract title, company, location, salary, experience level, required/preferred skills, description, Easy Apply status, posting date, applicant count.

**Scoring fan-out:**
```

Replace with:
```
For each *new* job, extract title, company, location, salary, experience level, required/preferred skills, description, Easy Apply status, posting date, applicant count.

**Corpus enrichment:** after extraction, run the JD keyword extraction procedure from `../shared-references/jd-keyword-extraction.md` on each new job's description text. This merges discovered keywords into `.job-scout/cache/jd-keyword-corpus.json` — building the user's market-specific keyword model over time. No additional LLM call; extraction piggybacks on the JD text already in context.

**Scoring fan-out:**
```

- [ ] **Step 3: Add corpus extraction to `check-job-notifications/SKILL.md`**

Find the `## Step 4: Extract details for new jobs only` section. Append a corpus-extraction note at the end of Step 4's content, before `## Step 5: Filter`.

Find (exact):
```
## Step 4: Extract details for new jobs only

For each *new* job: open it and extract title, company, location (remote/hybrid/on-site + city), salary/rate, contract type, experience level, required skills, preferred skills, full description, Easy Apply status, posting date, applicant count, job URL.

## Step 5: Filter
```

Replace with:
```
## Step 4: Extract details for new jobs only

For each *new* job: open it and extract title, company, location (remote/hybrid/on-site + city), salary/rate, contract type, experience level, required skills, preferred skills, full description, Easy Apply status, posting date, applicant count, job URL.

**Corpus enrichment:** after extraction, run the JD keyword extraction procedure from `../shared-references/jd-keyword-extraction.md` on each new job's description. Merges keywords into `.job-scout/cache/jd-keyword-corpus.json`.

## Step 5: Filter
```

- [ ] **Step 4: Add corpus extraction to `job-search/SKILL.md`**

Find `## Step 3: Search LinkedIn` and its content. Append a corpus-extraction note after the extraction instructions and before `## Step 4: Score and Present`.

Find (exact):
```
Navigate to `https://www.linkedin.com/jobs/`. Enter target title, set location and filters (Experience Level, Remote, Date Posted — prioritize "Past Week"). Collect job IDs first and dedupe against `.job-scout/tracker.json` (see `shared-references/tracker-schema.md`) before opening any listing. Only extract details for new jobs: title, company, location, salary, requirements, description, Easy Apply status.

## Step 4: Score and Present
```

Replace with:
```
Navigate to `https://www.linkedin.com/jobs/`. Enter target title, set location and filters (Experience Level, Remote, Date Posted — prioritize "Past Week"). Collect job IDs first and dedupe against `.job-scout/tracker.json` (see `shared-references/tracker-schema.md`) before opening any listing. Only extract details for new jobs: title, company, location, salary, requirements, description, Easy Apply status.

**Corpus enrichment:** after extraction, run the JD keyword extraction procedure from `../shared-references/jd-keyword-extraction.md` on each new job's description. Merges keywords into `.job-scout/cache/jd-keyword-corpus.json`.

## Step 4: Score and Present
```

- [ ] **Step 5: Verify**

```bash
cd /Users/tura/git/claude-job-scout && grep -c "Corpus enrichment" skills/match-jobs/SKILL.md skills/check-job-notifications/SKILL.md skills/job-search/SKILL.md
```
Expected: `1` per file (3 total).

```bash
cd /Users/tura/git/claude-job-scout && grep -c "jd-keyword-extraction.md" skills/match-jobs/SKILL.md skills/check-job-notifications/SKILL.md skills/job-search/SKILL.md
```
Expected: `1` per file (3 total).

```bash
cd /Users/tura/git/claude-job-scout && git diff --stat
```
Expected: 3 files changed.

- [ ] **Step 6: Commit + push**

```bash
cd /Users/tura/git/claude-job-scout && git add skills/match-jobs/SKILL.md skills/check-job-notifications/SKILL.md skills/job-search/SKILL.md && git commit -m "$(cat <<'EOF'
Wire JD corpus extraction into all job-processing commands

/match-jobs, /check-job-notifications, and /job-search now run the
jd-keyword-extraction procedure after extracting job details. Each
ingested JD enriches .job-scout/cache/jd-keyword-corpus.json with
frequency-weighted, seniority-tagged, role-tagged keywords. No
additional LLM call — extraction piggybacks on the JD text already
in context.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)" && git push -u origin phase-2/task-02-corpus-wiring
```

---

## Task 3: ATS scan simulator + cv-optimizer integration

**Files:**
- Create: `/Users/tura/git/claude-job-scout/skills/cv-optimizer/references/ats-simulator.md`
- Modify: `/Users/tura/git/claude-job-scout/skills/cv-optimizer/SKILL.md` (orchestrator — phase table + reference list)

- [ ] **Step 1: Create branch**

```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-2/task-03-ats-simulator
```

- [ ] **Step 2: Write `ats-simulator.md`**

Create `/Users/tura/git/claude-job-scout/skills/cv-optimizer/references/ats-simulator.md` with exactly:

===FILE_START===
# ATS Scan Simulator

Loaded on demand by `cv-optimizer/SKILL.md` after Phase 2 gap analysis. Simulates how major ATS systems would parse and score the user's CV. Produces a concrete per-ATS score table rather than generic best-practice advice.

---

## Scoring components (0-100 per ATS)

| Component | Points | What it measures |
|-----------|--------|------------------|
| Parseability | 20 | Can the ATS extract text? Single column, no tables/images/text-boxes, text-selectable PDF or .docx |
| Section recognition | 20 | Standard headings found? ("Professional Experience", "Education", "Skills", "Certifications") |
| Keyword match | 40 | % of target keywords found in contextual positions (experience bullets weighted 2x vs skills-only section) |
| Contact extraction | 10 | Name, email, phone, LinkedIn URL each on a parseable plain-text line |
| Format compliance | 10 | Standard font (Arial/Calibri/Garamond), ≥10pt, ≥0.5in margins, consistent date format (MMM YYYY) |

## Per-ATS behaviour differences

### Workday

- Strictest on section headings. Rejects creative alternatives ("My Journey" instead of "Experience").
- Weights keyword frequency — terms appearing 2-3x across different sections score higher than 1x.
- Imports LinkedIn profile data via direct integration; CV keywords should match LinkedIn exactly.
- Date parsing is rigid: "Jan 2022 – Mar 2024" works, "2022-2024" doesn't.

### Greenhouse

- More lenient on headings but strict on format. Tables and multi-column layouts break parsing entirely.
- Imports LinkedIn Skills section as structured tags — exact phrasing matters ("Python" not "Python Programming Language").
- Strong preference for .docx over PDF. Scanned-image PDFs score 0 on parseability.
- Keyword matching is case-insensitive but exact-phrase — "CI/CD" matches, "continuous integration/continuous deployment" does not (include both forms).

### Lever

- Most modern parser. Handles some formatting variations but still trips on images, headers/footers, and embedded charts.
- Weights contextual keyword placement highest: a keyword in an experience bullet scores ~2x a keyword in a standalone skills list.
- Supports rich text formatting better than Workday/Greenhouse — bold/italic don't break parsing.
- Most tolerant of non-standard date formats.

## Keyword match scoring detail

The 40-point keyword-match component uses this weighting:

1. Load the target keyword set: master keyword list from `user-profile.json` + JD-specific terms (if a JD was provided) + top-20 corpus keywords from `.job-scout/cache/jd-keyword-corpus.json` (by frequency, filtered to the user's seniority + role tags).
2. For each target keyword, search the CV text:
   - **In an experience bullet:** 2 points per keyword (contextual usage, highest ATS weight).
   - **In a skills section:** 1 point per keyword (structured but less contextual).
   - **In the professional summary:** 1.5 points per keyword (visible and contextual).
   - **Not found:** 0 points.
3. Cap at 40 points total. Normalize: `min(40, sum_of_points / max_possible_points * 40)`.

## Output format

Present as a table:

```
ATS Simulation Results
┌──────────────┬───────┬──────────────┬─────────┬─────────┬────────┬────────┐
│ ATS          │ Total │ Parseability │ Section │ Keyword │Contact │ Format │
├──────────────┼───────┼──────────────┼─────────┼─────────┼────────┼────────┤
│ Workday      │ 91    │ 20/20        │ 18/20   │ 35/40   │ 10/10  │ 8/10   │
│ Greenhouse   │ 88    │ 20/20        │ 20/20   │ 30/40   │ 10/10  │ 8/10   │
│ Lever        │ 85    │ 18/20        │ 20/20   │ 29/40   │ 10/10  │ 8/10   │
└──────────────┴───────┴──────────────┴─────────┴─────────┴────────┴────────┘

Fix suggestions:
1. "My Journey" heading → "Professional Experience" (+4 pts Workday section)
2. Add "Kubernetes" to 2 experience bullets (+3 pts keyword match all ATS)
3. Remove table in Skills section → plain list (+2 pts Greenhouse parseability)
```

## After Phase 3 rewrite

Re-run the simulator on the optimized CV. Present a before/after comparison:

```
ATS Score Improvement
┌──────────┬──────────┬───────────┬────────┐
│ ATS      │ Original │ Optimized │ Change │
├──────────┼──────────┼───────────┼────────┤
│ Workday  │ 72       │ 91        │ +19    │
│ Greenhouse│ 68      │ 88        │ +20    │
│ Lever    │ 70       │ 85        │ +15    │
└──────────┴──────────┴───────────┴────────┘
```

## Subagent note

The simulation is rule-based and lightweight. Run all three ATS checks sequentially in-thread — no subagent dispatch needed. Total scoring is ~100 lines of structured evaluation, well within a single context.
===FILE_END===

- [ ] **Step 3: Update cv-optimizer orchestrator — add ATS simulator to phase table and reference list**

In `/Users/tura/git/claude-job-scout/skills/cv-optimizer/SKILL.md`, find (exact):
```
| 2 | Scoring & gap analysis | `references/phase-2-gap-analysis.md` | Always after Phase 1 |
```
Replace with:
```
| 2 | Scoring & gap analysis | `references/phase-2-gap-analysis.md` | Always after Phase 1 |
| 2a | ATS scan simulation | `references/ats-simulator.md` | Always after Phase 2 (supplementary robot-gate check) |
```

Also find (exact):
```
- **`references/phase-2-gap-analysis.md`** — Phase 2 content (lazy)
```
Replace with:
```
- **`references/phase-2-gap-analysis.md`** — Phase 2 content (lazy)
- **`references/ats-simulator.md`** — ATS scan simulation: Workday, Greenhouse, Lever (lazy, Phase 2a)
```

- [ ] **Step 4: Verify**

```bash
cd /Users/tura/git/claude-job-scout && ls skills/cv-optimizer/references/ats-simulator.md
```
Expected: exists.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "ats-simulator" skills/cv-optimizer/SKILL.md
```
Expected: at least `2` (phase table + reference list).

```bash
cd /Users/tura/git/claude-job-scout && grep -c "Workday" skills/cv-optimizer/references/ats-simulator.md
```
Expected: at least `3`.

```bash
cd /Users/tura/git/claude-job-scout && git diff --stat
```
Expected: 2 files (1 new + 1 modified).

- [ ] **Step 5: Commit + push**

```bash
cd /Users/tura/git/claude-job-scout && git add skills/cv-optimizer/references/ats-simulator.md skills/cv-optimizer/SKILL.md && git commit -m "$(cat <<'EOF'
Add ATS scan simulator reference + cv-optimizer integration

Simulates Workday, Greenhouse, and Lever parsing behaviour. Scores
each ATS 0-100 across 5 components (parseability, section recognition,
keyword match, contact extraction, format compliance). Produces a
concrete per-ATS score table and fix suggestions. Runs after Phase 2
gap analysis and re-runs after Phase 3 rewrite for before/after
comparison.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)" && git push -u origin phase-2/task-03-ats-simulator
```

---

## Task 4: Post-rewrite keyword-density check

**Files:**
- Modify: `/Users/tura/git/claude-job-scout/skills/cv-optimizer/references/phase-2-gap-analysis.md`

- [ ] **Step 1: Create branch**

```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-2/task-04-density-check
```

- [ ] **Step 2: Append density-check section to `phase-2-gap-analysis.md`**

Read the current file (26 lines). Append at the end (after the trailing `---`):

Find (exact — the trailing separator at end of file):
```
6. Flag any JD "hidden requirements" (e.g., security clearance implied by client type, visa requirements implied by location)

---
```

Replace with:
```
6. Flag any JD "hidden requirements" (e.g., security clearance implied by client type, visa requirements implied by location)

---

## Post-Rewrite Keyword-Density Validation

Runs between Phase 3 (optimized rewrite) and Phase 4 (output deliverables). After the optimized CV is produced, measure keyword density to catch stuffing and undershoot.

### Target keyword set

Combine three sources:
1. **Master keyword list** from `.job-scout/user-profile.json` (built by Phase 0 discovery + CV analysis).
2. **JD-specific keywords** extracted during the current analysis (if a target JD was provided).
3. **Top-20 corpus keywords** from `.job-scout/cache/jd-keyword-corpus.json` — ranked by `frequency`, filtered to the user's `seniority_tags` and `role_tags`. These represent what the user's actual market demands.

### Density rules

- **Target density per primary keyword:** 1-3% (occurrences / total word count × 100).
- **Stuffing flag (>3%):** "ATS stuffing risk — `[keyword]` appears [N] times in [M] words ([X]%). Reduce to 2-3 natural placements."
- **Undershoot flag (<0.5%) for JD-required keywords:** "Undershoot — `[keyword]` appears only [N] times. Add to at least 2 experience bullets."
- **Total unique keywords:** target 40-60 across the CV. Flag if below 30 or above 80.

### Output

Present as a density table in the Phase 4 deliverables:

```
Keyword Density Report (optimized CV — [M] total words)
┌─────────────────┬───────┬─────────┬────────┐
│ Keyword         │ Count │ Density │ Status │
├─────────────────┼───────┼─────────┼────────┤
│ Kubernetes      │ 4     │ 0.47%   │ ⚠ low  │
│ CI/CD           │ 3     │ 0.35%   │ ⚠ low  │
│ Python          │ 8     │ 0.94%   │ ✓      │
│ AWS             │ 12    │ 1.41%   │ ✓      │
│ microservices   │ 28    │ 3.29%   │ ⚠ high │
└─────────────────┴───────┴─────────┴────────┘

Total unique keywords: 47 (target: 40-60) ✓
```

### Before/after

If the density check flags issues AND the user approves auto-correction, re-run Phase 3 with targeted adjustments. Otherwise, surface the flags as advisory — the user edits manually. **Working assumption:** flag only, no auto-correction.
```

- [ ] **Step 3: Verify**

```bash
cd /Users/tura/git/claude-job-scout && grep -c "Density" skills/cv-optimizer/references/phase-2-gap-analysis.md
```
Expected: at least `3`.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "jd-keyword-corpus" skills/cv-optimizer/references/phase-2-gap-analysis.md
```
Expected: at least `1`.

```bash
cd /Users/tura/git/claude-job-scout && git diff --stat
```
Expected: 1 file changed.

- [ ] **Step 4: Commit + push**

```bash
cd /Users/tura/git/claude-job-scout && git add skills/cv-optimizer/references/phase-2-gap-analysis.md && git commit -m "$(cat <<'EOF'
Add post-rewrite keyword-density validation to Phase 2 gap analysis

Measures keyword density after the Phase 3 optimized rewrite. Flags
>3% per keyword as ATS stuffing risk, <0.5% for JD-required keywords
as undershoot. Uses master keyword list + JD-specific terms + top-20
corpus keywords as the target set. Flag-only — no auto-correction.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)" && git push -u origin phase-2/task-04-density-check
```

---

## Task 5: Banner + Featured concrete templates

**Files:**
- Create: `/Users/tura/git/claude-job-scout/skills/profile-optimizer/references/banner-featured-templates.md`
- Modify: `/Users/tura/git/claude-job-scout/skills/profile-optimizer/references/sections/featured.md`
- Modify: `/Users/tura/git/claude-job-scout/skills/profile-optimizer/references/sections/structured-fields.md`

- [ ] **Step 1: Create branch**

```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-2/task-05-banner-featured-templates
```

- [ ] **Step 2: Write `banner-featured-templates.md`**

Create `/Users/tura/git/claude-job-scout/skills/profile-optimizer/references/banner-featured-templates.md` with exactly:

===FILE_START===
# Banner + Featured Section Templates

Loaded on demand by `profile-optimizer/SKILL.md` when proposing banner images or Featured section content. Provides concrete, actionable templates rather than generic advice.

---

## Banner templates (3 options)

Choose the template that best matches the user's positioning based on their CV and career stage.

### Template 1 — Keyword Billboard

```
┌────────────────────────────────────────────────────────────┐
│                                                            │
│   [Role Title]  |  [Skill 1]  |  [Skill 2]  |  [Skill 3] │
│                                                            │
│   [One-line value statement or signature achievement]      │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Best for:** maximizing keyword visibility in a glance. Works for all roles. The skills chosen should match the top 3 keywords from the master keyword list.

**Example:** `Senior Data Engineer | Apache Spark | AWS | Real-Time Pipelines — Processing 2B+ events/day`

### Template 2 — Achievement Spotlight

```
┌────────────────────────────────────────────────────────────┐
│                                                            │
│            [Signature Metric]                              │
│            e.g. "£4.2B processed annually"                 │
│                                                            │
│            [Role Title] at [Company Type]                  │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Best for:** roles where one number tells the story (finance, ops, engineering scale). Triggers the anchoring effect from the psychology cheatsheet.

**Example:** `99.99% Uptime | Platform Engineer | FinTech & E-Commerce`

### Template 3 — Authority Signal

```
┌────────────────────────────────────────────────────────────┐
│                                                            │
│   Speaker at [Conference]  |  Author of [Publication]      │
│                                                            │
│   [Role Title]                                             │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Best for:** thought leaders, consultants, senior ICs building personal brand. Triggers the authority heuristic.

**Example:** `KubeCon Speaker | Author: "Scaling Event-Driven Systems" | Staff Engineer`

### Selection guidance

Match template to the user's strongest signal:
- Strong metrics (revenue, users, uptime, cost savings) → Template 2
- Strong credentials (talks, publications, certs) → Template 3
- General/balanced profile → Template 1 (safest default)

---

## Featured section templates (5-slot framework)

LinkedIn's Featured section supports 3-5 items displayed above the fold. Each slot should serve a distinct purpose.

| Slot | Content type | Source | Why it works |
|------|-------------|--------|--------------|
| 1 | Certification link | Credential verification page (Credly, AWS Verify, etc.) | Authority signal — one-click verification builds trust |
| 2 | Case study | Strongest CV achievement as a LinkedIn article or uploaded PDF | Depth behind the bullet — hiring managers can explore the full story |
| 3 | Talk/presentation | Conference slides (SlideShare/Speaker Deck), video link, or uploaded deck | Authority + expertise demonstration — rare differentiator |
| 4 | Project/portfolio | GitHub repo, product demo URL, portfolio page, or design samples | Tangible proof of work — especially important for technical roles |
| 5 | Recommendation highlight | Link to a key LinkedIn recommendation or testimonial screenshot | Social proof from a named authority figure |

### Mapping supporting docs to slots

Use the supporting-docs index (`.job-scout/cache/supporting-docs.json`) to recommend which slots to fill:

| Supporting doc type | Recommended slot |
|-------------------|-----------------|
| `cert` | Slot 1 — Certification link |
| `case_study` | Slot 2 — Case study |
| `talk` or `deck` | Slot 3 — Talk/presentation |
| `portfolio` or `publication` | Slot 4 — Project/portfolio |
| `recommendation` | Slot 5 — Recommendation highlight |

If the user has no supporting doc for a slot, suggest creating one:
- No cert? → "Consider adding your top certification to Credly for a verifiable link."
- No case study? → "Write a LinkedIn article about your strongest CV achievement — 500 words, focused on the business impact."
- No talk? → "Even an internal brown-bag deck uploaded as a PDF works here."

### Prioritization

If the user has more than 5 items, prioritize by:
1. Items backed by a supporting doc (verifiable > claimed)
2. Items relevant to the target role (from master keyword list overlap)
3. Items with the highest "authority signal" value (certs > recommendations > portfolio for most roles)
===FILE_END===

- [ ] **Step 3: Add cross-reference in `sections/featured.md`**

Read `/Users/tura/git/claude-job-scout/skills/profile-optimizer/references/sections/featured.md`. Append at the end:

```

### Templates

See `../banner-featured-templates.md` for the 5-slot Featured section framework and supporting-docs-to-slot mapping. Use the templates to propose specific Featured items backed by the user's indexed documents.
```

- [ ] **Step 4: Add cross-reference in `sections/structured-fields.md`**

Read `/Users/tura/git/claude-job-scout/skills/profile-optimizer/references/sections/structured-fields.md`. Append at the end:

```

### Banner templates

See `../banner-featured-templates.md` for 3 concrete banner templates (keyword billboard, achievement spotlight, authority signal). Choose based on the user's strongest signal from their CV.
```

- [ ] **Step 5: Verify**

```bash
cd /Users/tura/git/claude-job-scout && ls skills/profile-optimizer/references/banner-featured-templates.md
```
Expected: exists.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "banner-featured-templates" skills/profile-optimizer/references/sections/featured.md skills/profile-optimizer/references/sections/structured-fields.md
```
Expected: `1` per file.

```bash
cd /Users/tura/git/claude-job-scout && git diff --stat
```
Expected: 3 files (1 new + 2 modified).

- [ ] **Step 6: Commit + push**

```bash
cd /Users/tura/git/claude-job-scout && git add skills/profile-optimizer/references/banner-featured-templates.md skills/profile-optimizer/references/sections/featured.md skills/profile-optimizer/references/sections/structured-fields.md && git commit -m "$(cat <<'EOF'
Add banner + Featured section concrete templates

3 banner templates (keyword billboard, achievement spotlight, authority
signal) with selection guidance. 5-slot Featured framework with
supporting-docs-to-slot mapping. Cross-referenced from sections/
featured.md and sections/structured-fields.md.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)" && git push -u origin phase-2/task-05-banner-featured-templates
```

---

## Task 6: Supporting-doc-backed claims in profile-optimizer

**Files:**
- Modify: `/Users/tura/git/claude-job-scout/skills/profile-optimizer/references/sections/featured.md`
- Modify: `/Users/tura/git/claude-job-scout/skills/profile-optimizer/references/sections/about.md`
- Modify: `/Users/tura/git/claude-job-scout/skills/profile-optimizer/SKILL.md` (orchestrator Step 6)

- [ ] **Step 1: Create branch**

```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-2/task-06-supporting-doc-claims
```

- [ ] **Step 2: Add supporting-doc citation guidance to `sections/featured.md`**

Read the file. After the "### Templates" block added in Task 5 (or at the end if Task 5's content isn't present yet — it should be since tasks merge serially), append:

```

### Supporting-doc citations

When proposing Featured items, consult `.job-scout/cache/supporting-docs.json` (see `../../shared-references/supporting-docs.md` for the consumer contract). For each proposed item:

1. Check if the user's supporting-docs index contains a matching entry (by type: `cert` → Slot 1, `case_study` → Slot 2, etc.).
2. If a match exists, cite the source path in the proposal: "Feature your AWS SA Pro cert → source: `certs/aws-sa-pro.pdf`."
3. If no match exists but the slot is worth filling, suggest creating the asset (see template guidance above).

Add a **Supporting Doc** column to the proposal table:

```
| Current | Proposed | CV Source | Supporting Doc |
|---------|----------|-----------|----------------|
| (empty) | AWS SA Pro cert link | CV line 42 | certs/aws-sa-pro.pdf |
```
```

- [ ] **Step 3: Add supporting-doc citation guidance to `sections/about.md`**

Read the file. Append at the end:

```

### Supporting-doc citations

When weaving in achievements backed by the user's supporting documents, cite the source inline in the proposal:

- "Led platform migration for 50k users (documented in `case-studies/platform-migration-2024.pdf`)"
- "Presented at KubeCon 2025 on event-driven architectures (slides: `talks/kubecon-2025-eda.pdf`)"

Consult `.job-scout/cache/supporting-docs.json` for available documents. Only cite docs with `status: "ok"` — skip `"missing"` entries.
```

- [ ] **Step 4: Update profile-optimizer orchestrator Step 6**

In `/Users/tura/git/claude-job-scout/skills/profile-optimizer/SKILL.md`, find (exact):
```
6. **Generate section-by-section proposals** — ready-to-paste content derived from CV
```

Replace with:
```
6. **Generate section-by-section proposals** — ready-to-paste content derived from CV. For sections with supporting-doc coverage (Featured, About, Experience), consult `.job-scout/cache/supporting-docs.json` and cite source documents in the proposal table per `shared-references/supporting-docs.md` consumer contract.
```

- [ ] **Step 5: Verify**

```bash
cd /Users/tura/git/claude-job-scout && grep -c "supporting-docs.json" skills/profile-optimizer/references/sections/featured.md skills/profile-optimizer/references/sections/about.md skills/profile-optimizer/SKILL.md
```
Expected: at least `1` per file (3 total).

```bash
cd /Users/tura/git/claude-job-scout && git diff --stat
```
Expected: 3 files changed.

- [ ] **Step 6: Commit + push**

```bash
cd /Users/tura/git/claude-job-scout && git add skills/profile-optimizer/references/sections/featured.md skills/profile-optimizer/references/sections/about.md skills/profile-optimizer/SKILL.md && git commit -m "$(cat <<'EOF'
Add supporting-doc-backed claims to profile proposals

Featured and About section proposals now cite source documents from
the supporting-docs index. Adds a Supporting Doc column to proposal
tables and inline citations in About paragraph text. Orchestrator
Step 6 updated to consult the index per the consumer contract.
First consumer of the Phase 1 supporting-docs index.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)" && git push -u origin phase-2/task-06-supporting-doc-claims
```

---

## Task 7: Reverse-Boolean discoverability check

**Files:**
- Modify: `/Users/tura/git/claude-job-scout/skills/match-jobs/SKILL.md`
- Modify: `/Users/tura/git/claude-job-scout/skills/check-job-notifications/SKILL.md`

- [ ] **Step 1: Create branch**

```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-2/task-07-reverse-boolean
```

- [ ] **Step 2: Add reverse-Boolean to `match-jobs/SKILL.md`**

Read the file. Find `## Step 5: Present Results`. Before this heading, insert a new step:

Find (exact):
```
## Step 5: Present Results
```

Replace with:
```
## Step 4b: Reverse-Boolean discoverability check (A-tier only)

For each job scoring A-tier (85-100):
1. Extract from the JD: role title, top 3 required skills, location preference.
2. Construct the likely recruiter Boolean query using templates from `../shared-references/../profile-optimizer/references/recruiter-search-patterns.md`: `"<role>" AND ("<skill1>" OR "<skill2>") AND "<skill3>"`.
3. Load the user's cached LinkedIn profile from `.job-scout/cache/linkedin-profile.json`. Check for each Boolean term in: headline, current job title, skills list, about section, experience descriptions.
4. Classify: **Match** (all required terms found) or **Miss** (one or more terms absent).
5. Append to the A-tier match card:

```
🔍 Recruiter search simulation for: [Job Title] at [Company]
   Boolean: "<role>" AND ("<skill1>" OR "<skill2>") AND "<skill3>"
   Result: [MATCH | MISS — "<missing_keyword>" not found on your LinkedIn profile]
   Fix: Add "<missing_keyword>" to your LinkedIn Skills section and mention in your current role's bullets
```

Skip B/C-tier jobs — the user may not apply, so the discoverability check is not worth the analysis.

## Step 5: Present Results
```

- [ ] **Step 3: Add reverse-Boolean to `check-job-notifications/SKILL.md`**

Read the file. Find `## Step 7: Present results`. Before this heading, insert the same reverse-Boolean step:

Find (exact):
```
## Step 7: Present results
```

Replace with:
```
## Step 6b: Reverse-Boolean discoverability check (A-tier only)

For each job scoring A-tier (85-100):
1. Extract from the JD: role title, top 3 required skills, location preference.
2. Construct the likely recruiter Boolean query using templates from `../profile-optimizer/references/recruiter-search-patterns.md`: `"<role>" AND ("<skill1>" OR "<skill2>") AND "<skill3>"`.
3. Load the user's cached LinkedIn profile from `.job-scout/cache/linkedin-profile.json`. Check for each Boolean term in: headline, current job title, skills list, about section, experience descriptions.
4. Classify: **Match** or **Miss** with specific missing keywords.
5. Append to the A-tier match card in the report (same format as match-jobs Step 4b).

## Step 7: Present results
```

- [ ] **Step 4: Verify**

```bash
cd /Users/tura/git/claude-job-scout && grep -c "Reverse-Boolean" skills/match-jobs/SKILL.md skills/check-job-notifications/SKILL.md
```
Expected: `1` per file.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "recruiter-search-patterns" skills/match-jobs/SKILL.md skills/check-job-notifications/SKILL.md
```
Expected: at least `1` per file.

```bash
cd /Users/tura/git/claude-job-scout && git diff --stat
```
Expected: 2 files changed.

- [ ] **Step 5: Commit + push**

```bash
cd /Users/tura/git/claude-job-scout && git add skills/match-jobs/SKILL.md skills/check-job-notifications/SKILL.md && git commit -m "$(cat <<'EOF'
Add reverse-Boolean discoverability check for A-tier jobs

For each A-tier match, constructs the likely recruiter Boolean query
and verifies the user's LinkedIn profile would surface. Reports
match/miss with specific missing keywords and actionable fix
suggestions. Runs in both /match-jobs (Step 4b) and
/check-job-notifications (Step 6b). Skips B/C-tier.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)" && git push -u origin phase-2/task-07-reverse-boolean
```

---

## Task 8: Google snippet literal preview

**Files:**
- Modify: `/Users/tura/git/claude-job-scout/skills/profile-optimizer/SKILL.md` (orchestrator — add Step 9a)

- [ ] **Step 1: Create branch**

```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-2/task-08-google-snippet
```

- [ ] **Step 2: Add Step 9a to profile-optimizer orchestrator**

Read the file. Find (exact):
```
9. **Show alignment report** — keyword coverage, missing achievements, discrepancies
10. **Apply changes** via browser with user permission
```

Replace with:
```
9. **Show alignment report** — keyword coverage, missing achievements, discrepancies
9a. **Google snippet preview** — render the literal Google search result for the user's name:

    ```
    [Name] - [Headline]
    LinkedIn · [First ~160 characters of About section]
    ```

    Show two versions: **Current** (from cached profile) and **Proposed** (from this session's proposals). Check: does the snippet contain the target role title? The user's location? At least one quantified achievement? Does it truncate cleanly (not mid-word)? If the proposed snippet is weaker than the current, flag it.
10. **Apply changes** via browser with user permission
```

- [ ] **Step 3: Verify**

```bash
cd /Users/tura/git/claude-job-scout && grep -c "Google snippet preview" skills/profile-optimizer/SKILL.md
```
Expected: `1`.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "160 characters" skills/profile-optimizer/SKILL.md
```
Expected: `1`.

```bash
cd /Users/tura/git/claude-job-scout && git diff --stat
```
Expected: 1 file changed.

- [ ] **Step 4: Commit + push**

```bash
cd /Users/tura/git/claude-job-scout && git add skills/profile-optimizer/SKILL.md && git commit -m "$(cat <<'EOF'
Add Google snippet literal preview to profile-optimizer

New Step 9a renders the actual Google search result (Name + Headline +
first 160 chars of About) in current vs proposed form. Checks for
target role, location, quantified achievement, and clean truncation.
Flags if the proposed snippet is weaker than the current.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)" && git push -u origin phase-2/task-08-google-snippet
```

---

## Task 9: Recruiter lead-memory

**Files:**
- Modify: `/Users/tura/git/claude-job-scout/skills/recruiter-engagement/SKILL.md`
- Modify: `/Users/tura/git/claude-job-scout/skills/check-inbox/SKILL.md`

- [ ] **Step 1: Create branch**

```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-2/task-09-recruiter-lead-memory
```

- [ ] **Step 2: Update `recruiter-engagement/SKILL.md` Thread State schema**

Read the file. Find the `## Thread State` section with the JSON example. Expand the per-thread schema to include `notes`.

Find (exact):
```json
{
  "<thread_id>": {
    "recruiter_name": "...",
    "company": "...",
    "lead_tier": "hot | warm | cold",
    "last_seen_msg_id": "...",
    "last_drafted_reply": "...",
    "last_updated": "2026-04-08"
  }
}
```

Replace with:
```json
{
  "<thread_id>": {
    "recruiter_name": "...",
    "company": "...",
    "lead_tier": "hot | warm | cold",
    "last_seen_msg_id": "...",
    "last_drafted_reply": "...",
    "last_updated": "2026-04-08",
    "notes": [
      { "date": "2026-04-01", "note": "asked IR35 — confirmed outside" },
      { "date": "2026-04-05", "note": "rate range: £650-750/day" }
    ]
  }
}
```

- [ ] **Step 3: Add notes read/write rules to `recruiter-engagement/SKILL.md`**

After the JSON block and the existing paragraph about checking `last_seen_msg_id`, append:

Find (exact):
```
Before reading any thread's full history, check `last_seen_msg_id`. If the latest visible message id matches, skip the thread — there's nothing new. Only deep-read threads with new activity. After processing, update `last_seen_msg_id` and `lead_tier` per thread.
```

Replace with:
```
Before reading any thread's full history, check `last_seen_msg_id`. If the latest visible message id matches, skip the thread — there's nothing new. Only deep-read threads with new activity. After processing, update `last_seen_msg_id` and `lead_tier` per thread.

### Lead-memory notes

The `notes` array is an append-only log of facts established during the conversation. Notes persist across sessions so the skill never re-asks a question the recruiter already answered.

**Write trigger:** after each user-approved reply that contains a qualifying question or confirms a factual detail, append a note. Format: `{ "date": "<YYYY-MM-DD>", "note": "<topic> — <resolution or 'pending'>" }`. Examples: "asked IR35 — confirmed outside", "rate range: £650-750/day", "start date — pending, recruiter will confirm by Friday".

**Read trigger:** before drafting any reply:
1. Load `notes` for the thread.
2. Build a "known facts" summary from the latest note per topic.
3. Do not re-ask any question that has a resolved (non-"pending") note.
4. For "pending" notes, check if the recruiter's latest message resolves them. If so, update the note.

**Display:** surface the known-facts summary in the thread card presented to the user: "Known: IR35 outside, rate £650-750/day, available immediately."

Notes are never deleted. Contradictions are handled by reading the most recent note on a topic — it supersedes earlier entries.
```

- [ ] **Step 4: Update `check-inbox/SKILL.md` Step 3**

Find (exact):
```
## Step 3: Present Summary

Show leads grouped by category with: recruiter name, company, role mentioned, date received, and brief summary of why it was categorized that way. Recommend responding to Hot Leads first.
```

Replace with:
```
## Step 3: Present Summary

Show leads grouped by category with: recruiter name, company, role mentioned, date received, brief summary of why it was categorized that way, and **known facts** from lead-memory notes (if any — e.g., "Known: IR35 outside, rate £650-750/day"). Recommend responding to Hot Leads first.
```

- [ ] **Step 5: Verify**

```bash
cd /Users/tura/git/claude-job-scout && grep -c "notes" skills/recruiter-engagement/SKILL.md
```
Expected: at least `5`.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "known facts" skills/check-inbox/SKILL.md
```
Expected: at least `1`.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "Lead-memory" skills/recruiter-engagement/SKILL.md
```
Expected: `1`.

```bash
cd /Users/tura/git/claude-job-scout && git diff --stat
```
Expected: 2 files changed.

- [ ] **Step 6: Commit + push**

```bash
cd /Users/tura/git/claude-job-scout && git add skills/recruiter-engagement/SKILL.md skills/check-inbox/SKILL.md && git commit -m "$(cat <<'EOF'
Add recruiter lead-memory notes to thread state

threads.json per-thread schema gains a notes array — append-only log
of facts established during conversations (IR35 status, rate range,
start date, etc.). Before drafting any reply, the skill loads notes
and avoids re-asking resolved questions. check-inbox Step 3 now
displays known facts in the lead summary.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)" && git push -u origin phase-2/task-09-recruiter-lead-memory
```

---

## Task 10: Update ROADMAP Phase 2 checkboxes + release v0.5.0

**Files:**
- Modify: `/Users/tura/git/claude-job-scout/.claude-plugin/plugin.json`
- Modify: `/Users/tura/git/claude-job-scout/CHANGELOG.md`
- Modify: `/Users/tura/git/claude-job-scout/docs/ROADMAP.md`

- [ ] **Step 1: Create branch (merge LAST, after Tasks 1-9)**

```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-2/task-10-version-bump
```

- [ ] **Step 2: Bump plugin version**

Change `"version": "0.4.0"` to `"version": "0.5.0"` in `.claude-plugin/plugin.json`.

- [ ] **Step 3: Add 0.5.0 CHANGELOG section**

Insert before `## [0.4.0]` in CHANGELOG.md, using the actual merge date:

```markdown
## [0.5.0] — 2026-MM-DD

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
```

Update `2026-MM-DD` to the actual merge date.

- [ ] **Step 4: Update ROADMAP**

1. Phase 2 status: `In design` → `Shipped — v0.5.0`.
2. Phase 2 spec: already linked.
3. Phase 3 status: `Not started` → `In design`.
4. Current focus: `Phase 3 design spec.`
5. Add Phase 2 checkboxes (to be ticked): convert the existing bullet list under Phase 2 to checkbox format and tick all items.
6. Append log entry: `- **2026-MM-DD** — Phase 2 shipped as v0.5.0. Phase 3 (new user-facing commands) entering design.`

- [ ] **Step 5: Verify**

```bash
cd /Users/tura/git/claude-job-scout && jq -r .version .claude-plugin/plugin.json
```
Expected: `0.5.0`.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "^## \[0.5.0\]" CHANGELOG.md
```
Expected: `1`.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "Shipped — v0.5.0" docs/ROADMAP.md
```
Expected: `1`.

- [ ] **Step 6: Commit + push**

```bash
cd /Users/tura/git/claude-job-scout && git add .claude-plugin/plugin.json CHANGELOG.md docs/ROADMAP.md && git commit -m "$(cat <<'EOF'
Release v0.5.0 — Phase 2 complete

Bumps plugin version, adds CHANGELOG 0.5.0 section, and updates
ROADMAP to mark Phase 2 shipped and Phase 3 entering design.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)" && git push -u origin phase-2/task-10-version-bump
```

---

## Self-review

### Spec coverage

| Spec component | Task |
|----------------|------|
| 1. Learned JD keyword corpus | Tasks 1 + 2 |
| 2. ATS scan simulator | Task 3 |
| 3. Post-rewrite density check | Task 4 |
| 4. Supporting-doc-backed claims | Task 6 |
| 5. Reverse-Boolean discoverability | Task 7 |
| 6. Google snippet preview | Task 8 |
| 7. Banner + Featured templates | Task 5 |
| 8. Recruiter lead-memory | Task 9 |

All 8 spec components covered. Task 10 handles release.

### Placeholder scan

One deliberate placeholder: `2026-MM-DD` in Task 10's CHANGELOG — the merge date isn't known at plan-write time.

### Type consistency

- `jd-keyword-corpus.json` referenced consistently across Tasks 1, 2, 3, 4.
- `supporting-docs.json` referenced consistently in Tasks 5, 6.
- `linkedin-profile.json` referenced in Task 7 (reverse-Boolean).
- `threads.json` extended in Task 9.
- `recruiter-search-patterns.md` referenced in Task 7 (correct existing path).

## Execution handoff

**Plan complete and saved to `docs/superpowers/plans/2026-04-17-phase-2-seo-ats-depth.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration. Same proven pattern as Phase 1.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

**Which approach?**

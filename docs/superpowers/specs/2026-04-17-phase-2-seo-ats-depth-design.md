# Phase 2 — SEO / ATS Depth (v0.5.0)

**Date:** 2026-04-17
**Status:** In design — pending user review
**Target release:** v0.5.0

## Why this phase exists

Phase 1 laid the foundations: subagent protocol, progressive-disclosure skill splits, reconciled state layout, and the supporting-docs index. Phase 2 uses that infrastructure to make the plugin's CV and LinkedIn outputs genuinely competitive against ATS filters and recruiter search — not just "best-practice advice" but concrete, measurable simulation scores, learned keyword intelligence from the user's actual job market, and provenance-backed claims that hiring managers can verify.

## Goals

- Give the user a concrete "would this CV pass the ATS?" answer per target system, not just generic formatting advice.
- Build a keyword model from the user's own job market (every ingested JD enriches the corpus) so keyword recommendations improve over time.
- Close the loop between CV rewrite and keyword coverage with a post-rewrite density check that catches stuffing and undershoot.
- Make the plugin's profile proposals evidence-based by citing the user's own supporting documents (certs, talks, case studies).
- Let the user see exactly what a recruiter searching for their role would find — and what they'd miss.
- Show the literal Google snippet their name produces, so headline and About edits are tested against the real search surface.
- Give profile-optimizer concrete templates (not just advice) for banner images and Featured section slots.
- Make recruiter conversations stateful so the plugin never re-asks a question a recruiter already answered.

## Non-goals (explicitly deferred)

- **`/cover-letter`, `/interview-prep`, `/funnel-report`, `/index-docs` commands** — Phase 3.
- **WebFetch or external API access for `company-researcher`** — future consideration, not Phase 2.
- **Automated keyword extraction via ML/NLP** — the extraction is LLM-driven, not a separate ML pipeline.
- **Real-time ATS API integration** — the simulator mimics ATS behaviour from documented rules, it does not call any ATS API.

---

## Component 1: Learned JD Keyword Corpus

**Artefact:** `.job-scout/cache/jd-keyword-corpus.json`

**Purpose:** every JD the plugin ingests enriches a persistent keyword model. Over weeks of use, the corpus reflects the user's actual job market — frequency-weighted, seniority-tagged, role-tagged — rather than the static dictionary in `ats-keywords.md`.

### Shape

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

### Extraction procedure

**New shared reference:** `skills/shared-references/jd-keyword-extraction.md`.

Extraction runs inside the existing job-processing path of `/match-jobs`, `/check-job-notifications`, and `/job-search` — after Step 4 (extract job details) and before scoring. No additional LLM call: the keyword extraction piggybacks on the JD text already in context.

Steps:
1. Parse the JD text for hard skills, tools, frameworks, certifications, methodologies, and domain terms.
2. Use `ats-keywords.md` as a seed vocabulary for recognition, but also discover terms not in the seed list (novel tools, niche frameworks, domain jargon).
3. For each extracted keyword: if it exists in the corpus, increment `frequency`, update `last_seen`, append `source_jobs`; if new, create the entry.
4. Tag `seniority_tags` from the job's experience-level field (e.g., "Senior" → `["senior"]`). Tag `role_tags` from the job's title (e.g., "Data Engineer" → `["data-engineer"]`).
5. Write the updated corpus back to `.job-scout/cache/jd-keyword-corpus.json`.

### Consumers

- **cv-optimizer** (Phase 2 gap analysis): supplements the master keyword list with corpus terms the user's market actually demands.
- **ATS simulator** (Component 2): uses corpus frequency to weight keyword-match scores.
- **Density check** (Component 3): uses corpus + master keyword list as the target set.
- **Profile-optimizer** (keyword coverage score): compares profile keywords against corpus.

### Token cost

Negligible incremental cost. The JD text is already loaded for scoring. Extraction is a structured parse of text already in context. The corpus merge is a JSON read-merge-write with no LLM call.

---

## Component 2: ATS Scan Simulator

**Artefact:** `skills/cv-optimizer/references/ats-simulator.md`

**Purpose:** simulate how Workday, Greenhouse, and Lever would parse and score the user's CV. Output a concrete per-ATS score rather than generic best-practice advice.

### Scoring components (0-100 per ATS)

| Component | Points | What it measures |
|-----------|--------|------------------|
| Parseability | 20 | Can the ATS extract text? Single column, no tables/images/text-boxes, text-selectable PDF or .docx |
| Section recognition | 20 | Standard headings found? ("Professional Experience", "Education", "Skills", "Certifications") |
| Keyword match | 40 | % of target keywords found in contextual positions (experience bullets weighted higher than skills-only section) |
| Contact extraction | 10 | Name, email, phone, LinkedIn URL each on a parseable line |
| Format compliance | 10 | Standard font (Arial/Calibri/Garamond), ≥10pt, ≥0.5in margins, consistent date format (MMM YYYY) |

### Per-ATS behaviour differences

- **Workday:** strictest on section headings. Rejects creative alternatives ("My Journey" instead of "Experience"). Weights keyword frequency — terms appearing 2-3x score higher than 1x.
- **Greenhouse:** more lenient on headings but strict on format. Tables and multi-column layouts break parsing. Imports LinkedIn Skills section as structured tags — exact phrasing matters.
- **Lever:** most modern parser. Handles some formatting variations but still trips on images, headers/footers, and embedded charts. Weights contextual keyword placement (in bullets) higher than other ATS.

### Integration

Runs after cv-optimizer Phase 2 gap analysis, before Phase 3 rewrite. Presented alongside the existing seven-dimension scoring as a supplementary "robot gate" check.

**Output format:**

```
ATS Simulation Results
┌──────────────┬───────┬──────────────┬─────────┬─────────┬────────┬───────┐
│ ATS          │ Total │ Parseability │ Section │ Keyword │ Contact│ Format│
├──────────────┼───────┼──────────────┼─────────┼─────────┼────────┼───────┤
│ Workday      │ 91    │ 20/20        │ 18/20   │ 35/40   │ 10/10  │ 8/10  │
│ Greenhouse   │ 88    │ 20/20        │ 20/20   │ 30/40   │ 10/10  │ 8/10  │
│ Lever        │ 85    │ 18/20        │ 20/20   │ 29/40   │ 10/10  │ 8/10  │
└──────────────┴───────┴──────────────┴─────────┴─────────┴────────┴───────┘

Fix suggestions:
1. "My Journey" heading → "Professional Experience" (+4 pts Workday)
2. Add "Kubernetes" to 2 experience bullets (+3 pts keyword match all ATS)
3. Remove table in Skills section → plain list (+2 pts Greenhouse parseability)
```

### After Phase 3 rewrite

The simulator re-runs on the optimized CV and presents a before/after comparison: "Original: Workday 72 → Optimized: Workday 91."

---

## Component 3: Post-Rewrite Keyword-Density Check

**Purpose:** after cv-optimizer Phase 3 produces the optimized CV, verify keyword density is in the sweet spot — not stuffed, not thin.

### Rules

- **Target density per primary keyword:** 1-3% (occurrences / total word count × 100).
- **Stuffing flag:** >3% per keyword → "ATS stuffing risk — `[keyword]` appears [N] times in [M] words ([X]%). Reduce to 2-3 occurrences."
- **Undershoot flag:** <0.5% for any JD-required keyword → "Undershoot — `[keyword]` appears only [N] times. Add to at least 2 experience bullets."
- **Total unique keywords:** target 40-60 across the CV (from master keyword list + JD-specific + learned corpus).

### Integration

New validation subsection in `cv-optimizer/references/phase-2-gap-analysis.md` titled "Post-rewrite density validation." Runs between Phase 3 (rewrite) and Phase 4 (deliverables). The density report becomes part of Phase 4's output.

### Output

A density table:
```
Keyword Density Report (optimized CV)
┌─────────────────┬───────┬────────┬─────────┬────────┐
│ Keyword         │ Count │ Words  │ Density │ Status │
├─────────────────┼───────┼────────┼─────────┼────────┤
│ Kubernetes      │ 4     │ 850    │ 0.47%   │ ⚠ low  │
│ CI/CD           │ 3     │ 850    │ 0.35%   │ ⚠ low  │
│ Python          │ 8     │ 850    │ 0.94%   │ ✓      │
│ AWS             │ 12    │ 850    │ 1.41%   │ ✓      │
│ microservices   │ 28    │ 850    │ 3.29%   │ ⚠ high │
└─────────────────┴───────┴────────┴─────────┴────────┘
```

---

## Component 4: Supporting-Doc-Backed Claims

**Purpose:** make profile-optimizer proposals evidence-based by citing which indexed document backs each claim.

### How it works

Profile-optimizer reads `.job-scout/cache/supporting-docs.json` (built in Phase 1, Task 8). When generating proposals for sections that benefit from provenance:

- **Featured section proposals:** each proposed Featured item cites the source document path and type. Example: "Feature your AWS Solutions Architect Professional certification → source: `certs/aws-sa-pro.pdf` (type: cert)."
- **About paragraph proposals:** when weaving in achievements backed by supporting docs, cite the source inline. "Led platform migration for 50k users (documented in `case-studies/platform-migration-2024.pdf`)."
- **Experience bullet proposals:** if a bullet's claim maps to a supporting doc (e.g., a talk or publication), note the source.

### Integration

Update these profile-optimizer reference files:
- `references/sections/featured.md` — add a "Supporting docs" subsection instructing the skill to consult the index and cite sources.
- `references/sections/about.md` — add citation guidance.
- Orchestrator Step 6 — add a note: "For sections with supporting-doc coverage, cite the source document per `supporting-docs.md` consumer contract."

### Proposal table format

The existing proposal table (`Current | Proposed | CV Source`) gains a fourth column:

```
| Current | Proposed | CV Source | Supporting Doc |
|---------|----------|-----------|----------------|
| (empty) | AWS SA Pro cert link | CV line 42 | certs/aws-sa-pro.pdf |
| (empty) | Platform migration case study | CV bullet 3, role 1 | case-studies/migration-2024.pdf |
```

---

## Component 5: Reverse-Boolean Discoverability Check

**Purpose:** for each A-tier job match, verify the user's LinkedIn profile would actually surface in the recruiter's search.

### Procedure (per A-tier job)

1. Extract from the JD: role title, top 3 required skills, location preference, seniority level.
2. Construct the likely Boolean query using templates from `recruiter-search-patterns.md`: `"<role>" AND ("<skill1>" OR "<skill2>") AND "<skill3>" AND "<location>"`.
3. Check the user's cached LinkedIn profile (`linkedin-profile.json`) for each term. Check in: headline, current job title, skills list, about section, experience descriptions.
4. Classify: **Match** (all required terms found in searchable fields) or **Miss** (one or more terms absent).
5. For misses: identify the specific missing keyword(s) and the recommended placement ("Add 'Kubernetes' to your LinkedIn Skills section and one experience bullet").

### Integration

Appended to A-tier match cards in the reports produced by `/check-job-notifications` and `/match-jobs`. The check runs only for A-tier jobs (B/C-tier aren't worth the discoverability analysis — the user may not apply).

### Output format

```
🔍 Recruiter search simulation for: Senior Data Engineer at Acme Corp
   Boolean: "data engineer" AND ("Spark" OR "PySpark") AND "AWS" AND "remote"
   Result: MISS — "PySpark" not found on your LinkedIn profile
   Fix: Add "PySpark" to Skills section and mention in your current role's bullets
```

---

## Component 6: Google Snippet Literal Preview

**Purpose:** show the user the exact text Google displays when someone searches their name.

### What Google shows

Google indexes LinkedIn profiles and displays:
```
[Name] - [Headline]
LinkedIn · [First ~160 characters of About section]
```

### Implementation

Profile-optimizer renders this preview after proposing content changes (Step 7, after alignment report). Two previews shown:
1. **Current:** headline + About from the cached profile snapshot.
2. **Proposed:** headline + About from the proposed content.

The user sees both side-by-side and can judge whether the proposed version is stronger for search discoverability.

### Checks

- Does the snippet contain the target role title?
- Does it contain the user's location (for geo-targeted searches)?
- Does it truncate mid-word or mid-sentence? (If so, suggest rewriting the About opener to fit cleanly within ~160 chars.)
- Does it contain at least one quantified achievement?

### Integration

New output block in profile-optimizer Step 7. No new reference file needed — the logic is a rendering pass over already-proposed content. Add instructions to the orchestrator's Step 7 description.

---

## Component 7: Banner + Featured Concrete Templates

**Artefact:** `skills/profile-optimizer/references/banner-featured-templates.md`

**Purpose:** replace the current one-liner banner/Featured advice with concrete, actionable templates.

### Banner templates (3 options)

**Template 1 — Keyword Billboard:**
```
┌────────────────────────────────────────────────────────────┐
│                                                            │
│   [Role Title]  |  [Skill 1]  |  [Skill 2]  |  [Skill 3] │
│                                                            │
│   [One-line value statement or signature achievement]      │
│                                                            │
└────────────────────────────────────────────────────────────┘
```
Best for: maximizing keyword visibility in a glance. Works for all roles.

**Template 2 — Achievement Spotlight:**
```
┌────────────────────────────────────────────────────────────┐
│                                                            │
│            [Signature Metric]                              │
│            e.g. "£4.2B processed annually"                 │
│                                                            │
│            [Role Title] at [Company Type]                   │
│                                                            │
└────────────────────────────────────────────────────────────┘
```
Best for: roles where one number tells the story (finance, ops, engineering scale).

**Template 3 — Authority Signal:**
```
┌────────────────────────────────────────────────────────────┐
│                                                            │
│   Speaker at [Conference]  |  Author of [Publication]      │
│                                                            │
│   [Role Title]                                             │
│                                                            │
└────────────────────────────────────────────────────────────┘
```
Best for: thought leaders, consultants, senior ICs building personal brand.

### Featured section templates (5-slot framework)

| Slot | Content type | Source | Why it works |
|------|-------------|--------|-------------|
| 1 | Certification link | Credential verification page (e.g., Credly, AWS Verify) | Authority signal + one-click verification |
| 2 | Case study | Strongest CV achievement as a LinkedIn article or uploaded PDF | Depth behind the bullet — hiring managers can explore |
| 3 | Talk/presentation | Conference slides (SlideShare), video link, or uploaded deck | Authority + expertise demonstration |
| 4 | Project/portfolio | GitHub repo, product demo URL, portfolio page | Tangible proof of work |
| 5 | Recommendation highlight | Link to a key LinkedIn recommendation or testimonial screenshot | Social proof from a named authority |

### Selection guidance

The skill uses supporting-docs index types to recommend which slots to fill:
- `type: cert` → Slot 1
- `type: case_study` → Slot 2
- `type: talk` or `type: deck` → Slot 3
- `type: portfolio` or `type: publication` → Slot 4
- `type: recommendation` → Slot 5

### Integration

New reference file cross-referenced from `sections/featured.md` (slot proposals), `sections/structured-fields.md` (banner proposals), and the orchestrator's Step 6.

---

## Component 8: Recruiter Lead-Memory

**Purpose:** make recruiter conversations stateful across sessions.

### Schema change to `threads.json`

Each thread entry gains a `notes` array:

```json
{
  "<thread_id>": {
    "recruiter_name": "...",
    "company": "...",
    "lead_tier": "hot | warm | cold",
    "last_seen_msg_id": "...",
    "last_drafted_reply": "...",
    "last_updated": "2026-04-17",
    "notes": [
      { "date": "2026-04-01", "note": "asked IR35 — confirmed outside" },
      { "date": "2026-04-05", "note": "rate range: £650-750/day" },
      { "date": "2026-04-10", "note": "start date: immediate availability confirmed" }
    ]
  }
}
```

### Write rules

After each user-approved reply that contains a qualifying question or confirms a factual detail, the recruiter-engagement skill appends a note. The note captures the topic and the resolution (if known). Format: `"<topic> — <resolution or 'pending'>"`.

Notes are never deleted — they are an append-only log. Contradictions are handled by the skill reading the latest note on a topic: "IR35 confirmed outside (2026-04-01)" supersedes any earlier ambiguity.

### Read rules

Before drafting any reply to a recruiter thread:
1. Load `notes` for the thread.
2. Build a "known facts" summary from the notes.
3. Do not re-ask any question that has a resolved note.
4. Surface the known-facts summary in the thread card presented to the user: "Known: IR35 outside, rate £650-750/day, available immediately."

### Integration

- Update `recruiter-engagement/SKILL.md`: document the notes array, write trigger, read rules, known-facts summary construction.
- Update `check-inbox/SKILL.md`: Step 3 (Present Summary) gains a "Known facts" column per lead.

---

## Data shapes introduced or changed in Phase 2

| File | Phase 2 change |
|------|----------------|
| `.job-scout/cache/jd-keyword-corpus.json` | New file. Shape documented in Component 1. |
| `.job-scout/recruiters/threads.json` | Adds `notes` array per thread (Component 8). |
| `.job-scout/cache/supporting-docs.json` | No schema change — first consumer reads added (Component 4). |
| `.job-scout/cache/linkedin-profile.json` | No schema change — reverse-Boolean reads section content (Component 5). |

## Files created or modified

| File | Change type | Component |
|------|------------|-----------|
| `skills/shared-references/jd-keyword-extraction.md` | New | 1 |
| `skills/shared-references/workspace-layout.md` | Modify (add corpus to canonical layout) | 1 |
| `skills/cv-optimizer/references/ats-simulator.md` | New | 2 |
| `skills/cv-optimizer/SKILL.md` (orchestrator) | Modify (add ATS sim + density check integration) | 2, 3 |
| `skills/cv-optimizer/references/phase-2-gap-analysis.md` | Modify (add density-check subsection) | 3 |
| `skills/profile-optimizer/references/sections/featured.md` | Modify (add supporting-doc citation guidance) | 4 |
| `skills/profile-optimizer/references/sections/about.md` | Modify (add supporting-doc citation guidance) | 4 |
| `skills/profile-optimizer/SKILL.md` (orchestrator) | Modify (Steps 6, 7 — doc citations, Google snippet, reverse-Boolean hook) | 4, 5, 6 |
| `skills/profile-optimizer/references/banner-featured-templates.md` | New | 7 |
| `skills/profile-optimizer/references/sections/structured-fields.md` | Modify (cross-ref banner templates) | 7 |
| `skills/match-jobs/SKILL.md` | Modify (add corpus extraction + reverse-Boolean on A-tier) | 1, 5 |
| `skills/check-job-notifications/SKILL.md` | Modify (add corpus extraction + reverse-Boolean on A-tier) | 1, 5 |
| `skills/job-search/SKILL.md` | Modify (add corpus extraction) | 1 |
| `skills/recruiter-engagement/SKILL.md` | Modify (add notes schema, read/write rules) | 8 |
| `skills/check-inbox/SKILL.md` | Modify (add Known facts display) | 8 |

## Rollout

- Single `main` branch, feature-by-feature merges — same pattern as Phase 1.
- Version bump in `.claude-plugin/plugin.json` only on the final merge (0.4.0 → 0.5.0).
- CHANGELOG entry summarising all components.
- ROADMAP Phase 2 checkboxes ticked per task, Phase 3 flips to "In design" on final merge.

## What "done" looks like

Phase 2 ships when:
- All Phase 2 Roadmap checkboxes are ticked.
- `CHANGELOG.md` has a 0.5.0 section.
- `plugin.json` reports `0.5.0`.
- A clean run of `/analyze-cv` on a sample CV produces ATS simulation scores + density report.
- A clean run of `/optimize-profile` produces supporting-doc-backed proposals + Google snippet preview + banner/Featured templates.
- A clean run of `/check-job-notifications` populates the JD keyword corpus + shows reverse-Boolean on A-tier matches.
- A clean run of `/check-inbox` shows recruiter notes in thread summaries.
- `docs/ROADMAP.md` Phase 3 row flips to "In design."

## Open questions

1. **Should the ATS simulator be a subagent?** The simulation is rule-based and lightweight — running all three ATS checks sequentially in-thread is likely faster than dispatching 3 subagents. **Working assumption:** in-thread, no subagent overhead.
2. **Should the keyword corpus have a TTL?** Keywords from JDs older than 6 months may be stale. **Working assumption:** no TTL in Phase 2; the frequency counter naturally down-weights stale terms since they stop being reinforced. Phase 3's `/funnel-report` could add a "trending keywords" view.
3. **Should the density check auto-fix?** If a keyword is flagged as overstuffed, should the skill auto-edit the CV or just flag? **Working assumption:** flag only. The user approves all CV edits.

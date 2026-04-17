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

This file is a lightweight orchestrator. Full guidance for each profile section, activity/engagement advice, and the scoring rubric live in lazy-loaded reference files under `references/`. Load a reference only when its content is needed for the current step — this keeps the context window small on routine runs.

## CV Requirement

The CV is mandatory. If no CV is found in the workspace:
1. Ask the user to provide their CV (upload, paste, or point to a file path)
2. Do not proceed until the CV is loaded — it drives all content proposals

Once loaded, extract: role titles, seniority level, key skills (technical and domain), quantified achievements, industry/domain context, and career narrative.

**Master keyword list:** Reuse the list from `user-profile.json` → `master_keyword_list` (produced by `cv-optimizer`). If it doesn't exist, build it from the CV: every hard skill, tool, framework, methodology, certification, and industry term. This list is the single source of truth for all keyword placement across the profile.

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

## Cross-Platform Keyword Consistency

### Google Discoverability
- LinkedIn profiles rank high on Google for name searches
- Ensure headline + About first 3 lines work as a compelling Google snippet
- Include location and role in headline so Google queries like "John Smith data engineer London" return the profile

### Job Board Keyword Sync
- Extract exact phrasing from target job descriptions (not just generic terms)
- Recruiters search LinkedIn with the same terms they put in their own JDs
- Ensure exact-match phrases from target JDs appear on the profile, not just synonyms

### Recruiter Boolean Search Simulation
- Construct likely Boolean queries a recruiter would run for the user's target role based on `references/recruiter-search-patterns.md`
- Verify the profile would surface (all required keywords present, in searchable fields)
- Example: `"data engineer" AND "Spark" AND "AWS" AND "remote"` — would this profile match?

## Scoring framework

Load `references/scoring-framework.md` when computing scores. It covers per-section scoring, cross-cutting scores (keyword coverage, search appearance, 10-second test, CV alignment), and the weighted overall score.

## Profile vs CV Alignment

After proposing all content, generate an alignment report:
- Dates, titles, and companies must match exactly between CV and LinkedIn
- Every keyword on the master keyword list must appear somewhere on the LinkedIn profile
- Flag CV achievements not represented on LinkedIn
- Flag LinkedIn content that contradicts or isn't supported by the CV
- Tone shift is expected: CV formal/concise → LinkedIn conversational/first-person

## Optimization Process

1. **Load CV** — follow `shared-references/cv-loading.md`. Extract structured data (roles, skills, achievements, keywords). Reuse master keyword list from `user-profile.json` if available.
2. **Read current LinkedIn profile** via browser, score each section (1-10)
3. **Check structured fields** — location, industry, custom URL, photo, banner, Open to Work status
4. **Check activity & engagement** — SSI score, recent posting activity, creator mode status
5. **Run Boolean search simulation** — would a recruiter find this profile?
5a. **Optional: company enrichment** — if the user pastes in a specific job listing during this run, dispatch `company-researcher/SKILL.md` with the JD blob to get a size/stage/reputation digest. Use the digest to shape the Featured section and About-paragraph proposals.
6. **Generate section-by-section proposals** — ready-to-paste content derived from CV. For sections with supporting-doc coverage (Featured, About, Experience), consult `.job-scout/cache/supporting-docs.json` and cite source documents in the proposal table per `shared-references/supporting-docs.md` consumer contract.
7. **Calculate all scores** — section scores, cross-cutting scores, overall score
8. **Present before/after comparison** for each section with the CV source highlighted
9. **Show alignment report** — keyword coverage, missing achievements, discrepancies
9a. **Google snippet preview** — render the literal Google search result for the user's name:

    ```
    [Name] - [Headline]
    LinkedIn · [First ~160 characters of About section]
    ```

    Show two versions: **Current** (from cached profile) and **Proposed** (from this session's proposals). Check: does the snippet contain the target role title? The user's location? At least one quantified achievement? Does it truncate cleanly (not mid-word)? If the proposed snippet is weaker than the current, flag it.
10. **Apply changes** via browser with user permission — one section at a time. After each write, recompute `profile_hash` (SHA-256 over canonical JSON of headline, about, experience bullets, skills list, Open to Work config) and persist to `.job-scout/user-profile.json`.

## State & Caching

- **`.job-scout/user-profile.json`** — source of `master_keyword_list` (built by `cv-optimizer`) and `profile_hash` (built by this skill). Reuse `master_keyword_list` unless `cv_hash` changed; rebuild `profile_hash` on any content-changing profile edit (see bullet 2).
- **`profile_hash`** — after any write that changes `master_keyword_list` or the LinkedIn-facing content this skill proposes (headline, about, experience bullets, skills list, Open to Work config), compute a SHA-256 over the canonical JSON of those fields and persist to `.job-scout/user-profile.json` as `profile_hash`. Downstream skills (`job-matcher`) use it as part of the score-cache key, so a profile edit invalidates stale scores.
- **`.job-scout/cache/linkedin-profile.json`** — last-seen LinkedIn profile snapshot with per-section content hashes. Shape:

  ```json
  {
    "version": 1,
    "last_full_read": "<ISO>",
    "sections": {
      "headline":            { "content": "...", "hash": "<sha256>", "score": 8, "scored_at": "<ISO>" },
      "about":               { "content": "...", "hash": "<sha256>", "score": 7, "scored_at": "<ISO>" },
      "experience_0":        { "content": "...", "hash": "<sha256>", "score": 6, "scored_at": "<ISO>" },
      "skills":              { "content": [...], "hash": "<sha256>", "score": 5, "scored_at": "<ISO>" },
      "featured":            { "content": [...], "hash": "<sha256>", "score": 7, "scored_at": "<ISO>" },
      "education":           { "content": "...", "hash": "<sha256>", "score": 8, "scored_at": "<ISO>" },
      "certifications":      { "content": [...], "hash": "<sha256>", "score": 9, "scored_at": "<ISO>" },
      "recommendations":     { "content": [...], "hash": "<sha256>", "score": 6, "scored_at": "<ISO>" },
      "open_to_work":        { "content": "...", "hash": "<sha256>", "score": 7, "scored_at": "<ISO>" },
      "structured_fields":   { "content": "...", "hash": "<sha256>", "score": 8, "scored_at": "<ISO>" }
    }
  }
  ```

  Experience entries use zero-indexed keys (`experience_0`, `experience_1`, …). `structured_fields` is a single bucket covering location, industry, custom URL, photo, and banner. The `score` field (1–10) is the cached section score — when hashes match, the inner gate returns this value directly instead of re-scoring.

  **Two-tier reuse:**
  1. **Outer gate (cheap):** if `last_full_read < 7 days ago` and the user hasn't indicated edits, skip the browser read entirely and reuse all cached section scores.
  2. **Inner gate:** when the outer gate fails and a browser read runs, hash each section's freshly-read content and compare against the stored hash. Matching hashes → reuse the cached score for that section. Differing hashes → re-score only that section. Update each section's `content`, `hash`, and `scored_at` plus the top-level `last_full_read` after the read completes.

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

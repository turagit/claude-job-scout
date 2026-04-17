# ATS Scan Simulator

Loaded on demand by `_cv-optimizer/SKILL.md` after Phase 2 gap analysis. Simulates how major ATS systems would parse and score the user's CV. Produces a concrete per-ATS score table rather than generic best-practice advice.

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

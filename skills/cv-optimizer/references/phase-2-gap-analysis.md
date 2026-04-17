# Phase 2 — Scoring & Gap Analysis

Loaded on demand by `cv-optimizer/SKILL.md` after Phase 1 analysis completes. Takes the per-dimension scores, computes the weighted overall, grades, identifies top-5 improvements, and surfaces the strength spotlight.

---

1. **Score each dimension** (1–10) with specific evidence citations from the CV
2. **Calculate weighted overall score** out of 100
3. **Grade:** A (85–100), B (70–84), C (55–69), D (<55)
4. **Identify top 5 improvements** ranked by point-impact, formatted as:
   > "Rewrite 4 experience bullets using SPAR method → Content Impact 5→8 → **+7.5 weighted points**"
5. **Strength spotlight:** Call out the top 3 things the CV already does well (anchors confidence before asking for changes)

---

## ATS Keyword Strategy

When user provides a target job description:
1. Extract all hard skills, tools, certifications, and methodologies from the JD
2. Compare against current CV content
3. Categorize gaps: **must-add** (required skills the user has but CV doesn't mention), **should-add** (preferred skills), **cannot-add** (skills the user doesn't have — never fabricate)
4. Suggest natural placements within existing achievement bullets
5. Calculate match percentage before and after optimization
6. Flag any JD "hidden requirements" (e.g., security clearance implied by client type, visa requirements implied by location)

---

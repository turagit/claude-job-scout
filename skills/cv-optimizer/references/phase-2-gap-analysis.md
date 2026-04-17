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

---
name: cv-optimizer
description: >
  This skill should be used when the user asks to "analyze my CV", "improve my resume",
  "optimize my CV for ATS", "check my CV", "review my resume", "make my CV better",
  "tailor my CV", or needs guidance on CV formatting, keyword optimization,
  or ATS compatibility. Also triggers when preparing a CV for job applications.
version: 0.1.0
---

# CV Optimizer

Analyze, score, and improve CVs/resumes for maximum impact with both ATS and human recruiters.

## Analysis Framework

Evaluate across five dimensions (score 1-10 each):

### 1. ATS Compatibility (Weight: 25%)
- Standard section headings, no tables/columns/text boxes/images
- Clean formatting: standard fonts, consistent date formats
- Keywords from target job descriptions present naturally

### 2. Content Impact (Weight: 30%)
- PAR method: Problem -> Action -> Result with quantified metrics
- Strong action verbs (Led, Delivered, Architected, Optimized)
- No filler phrases ("responsible for", "duties included")

### 3. Keyword Optimization (Weight: 20%)
- Industry-standard terminology, not creative synonyms
- Both spelled-out and acronym forms included
- Keywords woven into experience bullets, not just skills lists
- Aim for 70%+ match against target job description

### 4. Structure & Readability (Weight: 15%)
- Reverse chronological, consistent formatting, 1-2 pages (3 for senior/academic)
- Clear visual hierarchy and balanced white space

### 5. Professional Positioning (Weight: 10%)
- Tailored professional summary (3-4 lines max)
- Complete contact info with LinkedIn URL
- No photos, DOB, marital status

## Improvement Process

1. Parse CV content
2. Score each dimension (1-10) with specific evidence
3. Calculate weighted overall score
4. Identify top 5 improvements ranked by impact
5. Provide before/after rewrites using PAR method
6. Generate optimized version preserving user's voice

**PAR pattern:** [Action Verb] + [What you did] + [Scope/Scale] + [Measurable Result]
- Weak: "Managed a team of developers"
- Strong: "Led 8 developers through platform migration, delivering 3 months early, reducing costs 40%"

## ATS Keyword Strategy

When user provides a target job description: extract hard skills/tools/certifications, compare against CV, identify missing keywords the user genuinely has, suggest natural placements (never keyword-stuff), calculate match percentage.

## Keyword Handoff to Profile Optimizer

After analysing a CV, produce a **master keyword list** containing every hard skill, tool, framework, methodology, certification, and industry term extracted from the CV and any target job descriptions. This list should be saved so that `profile-optimizer` can reuse it directly rather than re-extracting. Both the CV and LinkedIn profile must target the same keywords — if a keyword is on the CV, it must appear on LinkedIn, and vice versa.

## Freelance / Contractor CV Mode

When user is a freelancer/contractor, apply adjustments from `../shared-references/freelance-context.md`.

## Reference Materials

- **`references/ats-keywords.md`** — Common ATS keyword categories by industry
- **`references/action-verbs.md`** — Categorized action verbs for achievement types
- **`../shared-references/freelance-context.md`** — Freelance CV structure and evaluation

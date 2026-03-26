---
name: cv-optimizer
description: >
  This skill should be used when the user asks to "analyze my CV", "improve my resume",
  "optimize my CV for ATS", "check my CV", "review my resume", "make my CV better",
  "tailor my CV", or needs guidance on CV formatting, keyword optimization,
  or ATS compatibility. Also triggers when preparing a CV for job applications.
version: 0.2.0
---

# CV Optimizer

Analyze, score, and transform CVs into documents that pass ATS filters **and** compel human reviewers to shortlist the candidate — using evidence-based persuasion psychology throughout.

---

## Phase 0 — Discovery Interview (MANDATORY)

Before analysing anything, gather the context needed to get it right first time. Ask the user **all** of these in a single, structured prompt (group logically so it feels conversational, not interrogative):

### Identity & Career Context
1. **Target role(s):** What job title(s) are you pursuing? (e.g. "Senior Data Engineer", "Tech Lead")
2. **Target industries/sectors:** Any specific industries? (e.g. FinTech, HealthTech, Public Sector)
3. **Seniority level:** Junior / Mid / Senior / Lead / Principal / Executive
4. **Employment type:** Permanent / Freelance-Contract / Either
5. **Years of experience** (approximate total)

### Strengths & Differentiators
6. **Top 3 achievements you're most proud of** — the ones that made the biggest business impact (revenue, users, cost savings, speed, quality). Even rough numbers help ("about 30% faster", "saved roughly £200k").
7. **Unique selling points:** What makes you different from other candidates at your level? (rare skill combos, niche domain expertise, patents, publications, speaking engagements, open-source contributions)
8. **Soft-skill strengths:** e.g. stakeholder management, mentoring, cross-team leadership, client-facing communication
9. **Certifications or formal qualifications** worth highlighting

### Target & Constraints
10. **Do you have a specific job description** to tailor against? (paste or attach if yes)
11. **Any companies or sectors to avoid?**
12. **Location / remote preference** and any visa/work-authorization notes
13. **Anything you want to downplay or omit?** (career gaps, short stints, irrelevant early roles)
14. **Preferred CV length:** 1 page / 2 pages / no preference
15. **Tone preference:** Formal-corporate / Professional-modern / Technical-dense / Let me decide

### Freelance-Specific (only if applicable)
16. **Day-rate range** (optional, for positioning)
17. **IR35 preference** (UK only): Outside / Inside / Either
18. **Availability date**

> **Why up front?** Every piece of context here prevents a generic rewrite. The difference between a 70-score CV and a 92-score CV is almost always *context the optimizer didn't have*.

If the user declines to answer some questions, proceed with what's available but flag what you're assuming.

---

## Phase 1 — Deep Analysis

### Seven-Dimension Scoring (1–10 each, weighted)

#### 1. ATS Compatibility (20%)
- **Standard section headings** recognized by all major ATS (Workday, Greenhouse, Lever, iCIMS, Taleo): "Professional Experience", "Education", "Skills", "Certifications" — not creative alternatives
- **Clean formatting:** single-column layout, no tables/text boxes/images/headers-footers (ATS strips them), standard fonts (Arial, Calibri, Garamond), consistent date format (MMM YYYY)
- **File format:** .docx preferred by ATS; .pdf acceptable if text-selectable (never scanned image PDFs)
- **Contact block:** name, email, phone, LinkedIn URL, city/country — on separate plain-text lines
- **No ATS poison:** avoid special characters in headings, embedded charts, multi-column layouts, creative icons

#### 2. Content Impact — Achievement Density (25%)
- **SPAR method:** Situation → Problem → Action → Result (evolution of PAR — the Situation anchors the story, making the impact more credible)
- Every bullet should contain a **quantified result** or a **tangible business outcome**
- Strong action verbs from `references/action-verbs.md` — never repeat a verb within the same role
- Zero filler phrases: eliminate "responsible for", "duties included", "helped with", "involved in", "assisted with"
- **Recency weighting:** current/most recent role gets 4–6 bullets, previous 3–4, older 2–3 (mirrors how recruiters actually read)

#### 3. Keyword Optimization (15%)
- Extract **hard skills, tools, certifications, methodologies** from target JD (if provided)
- Include both spelled-out and acronym forms: "Continuous Integration/Continuous Deployment (CI/CD)"
- Keywords woven **into achievement bullets** — not dumped in a skills-only section (ATS + humans both weight contextual usage higher)
- Target **75%+ keyword match** against the specific JD; **60%+** against the general role category from `references/ats-keywords.md`
- Never keyword-stuff: each keyword must appear in a truthful context

#### 4. Structure & Visual Hierarchy (10%)
- Reverse chronological within each section
- **F-pattern optimized:** most important info in the left-most, top-most positions (matches eye-tracking research: recruiters scan in an F-shape spending 6–7 seconds on initial scan)
- Consistent bullet style, indentation, spacing
- Strategic use of **bold** for company names, role titles, and key metrics — guides the eye to high-value content during the 7-second scan
- Target length: 1 page (0–5 yrs), 2 pages (5–15 yrs), 3 pages (15+ or academic only)

#### 5. Professional Positioning & Narrative (10%)
- **Professional summary** (3–4 lines): functions as a value proposition, not a bio. Opens with strongest credential, names the target role, includes 1 signature achievement with a number
- Complete contact info with LinkedIn URL
- No photos, DOB, marital status, nationality (unless required by local convention)
- **Career narrative coherence:** progression should tell a logical story — if it doesn't, the summary must frame the thread

#### 6. Psychological Persuasion Design (NEW — 10%)
Evidence-based techniques from behavioral psychology applied to CV content:

- **Anchoring Effect:** Lead each role with the most impressive metric — it sets the reference point for everything that follows. If you "Grew revenue 340%", put it first; subsequent bullets inherit its halo.
- **Peak-End Rule:** The first bullet of your most recent role and the last line of your CV (often the education section or a closing skills block) are disproportionately remembered. Make them count.
- **Social Proof:** Named clients, Fortune-500 logos, user counts, team sizes, and recognizable brands all trigger trust heuristics. "Led migration for a FTSE-100 bank" beats "Led migration for a financial client."
- **Specificity Bias:** Specific numbers feel more credible than round ones. "Reduced latency by 37%" is more believable than "Reduced latency by about 40%." Use precise numbers wherever honestly possible.
- **Contrast Effect:** Place your strongest achievement immediately after the role title — the reader's baseline expectation for a bullet is low, so a strong number creates a positive surprise.
- **Loss Aversion Framing:** Frame achievements in terms of what would have been lost without you: "Prevented £2M revenue loss by identifying and resolving critical payment-processing bug within 4 hours" triggers loss-aversion more powerfully than "Saved £2M."
- **Authority Signals:** Certifications, publications, speaking engagements, "selected for", "appointed to", advisory roles — these trigger the authority heuristic. Place them where they'll be seen.
- **Scarcity & Exclusivity:** "One of 3 engineers selected for..." or "Invited to join founding team..." signals selectivity.

#### 7. Recruiter Experience & Readability (NEW — 10%)
Optimized for the human who reads *after* the ATS passes:

- **7-Second Scan Test:** Can a recruiter extract role, seniority, top 3 skills, and one impressive number within 7 seconds? If not, restructure.
- **Jargon calibration:** Match the terminology level to the likely first reviewer (HR screens need broader terms; hiring-manager screens can handle deep technical language). When in doubt, use both: "Implemented event-driven architecture (Kafka, SNS/SQS) to handle 50k events/sec."
- **White space discipline:** Cramming text reduces readability. If cutting content is needed to fit page count, cut the weakest bullets — don't shrink font or margins below 10pt/0.5in.
- **Consistent tense:** Past tense for all previous roles, present tense for current role only.
- **No orphan sections:** Every section should have at least 2 items. One-item sections look thin.

---

## Phase 2 — Scoring & Gap Analysis

1. **Score each dimension** (1–10) with specific evidence citations from the CV
2. **Calculate weighted overall score** out of 100
3. **Grade:** A (85–100), B (70–84), C (55–69), D (<55)
4. **Identify top 5 improvements** ranked by point-impact, formatted as:
   > "Rewrite 4 experience bullets using SPAR method → Content Impact 5→8 → **+7.5 weighted points**"
5. **Strength spotlight:** Call out the top 3 things the CV already does well (anchors confidence before asking for changes)

---

## Phase 3 — Optimized Rewrite

### Rewrite Rules
- **Preserve the user's voice and facts** — enhance, don't fabricate
- Apply SPAR method to every achievement bullet
- Integrate all Phase-0 context: user's stated achievements, USPs, soft skills, tone preference
- Front-load each bullet with the most impressive element (anchoring)
- Apply psychological persuasion techniques from Dimension 6
- Ensure every keyword from the JD gap analysis is placed in a natural context
- Bold key metrics and company names for scan-ability
- Respect the user's preferred page length

### SPAR Bullet Formula

```
[Action Verb] + [What you did] + [Context/Scale] + [Measurable Result or Business Outcome]
```

**Weak:** "Managed a team of developers"
**Better:** "Led 8 developers through platform migration, delivering 3 months early and reducing infrastructure costs 40%"
**Best (SPAR):** "Inherited a stalled platform migration blocked by cross-team dependencies (S); restructured the delivery plan and directly led 8 engineers through weekly sprint cycles (PA); delivered 3 months ahead of deadline, reducing infrastructure costs by 40% and eliminating £180k/year in legacy licensing (R)"

> For bullet brevity, the compressed form (Better) is usually right for CV bullets. The full SPAR narrative is useful for cover letters and interview prep — offer both when generating the optimized version.

### Professional Summary Template

```
[Seniority] [Role Title] with [X years] experience in [2-3 domain areas].
[Signature achievement with specific number].
[What you're looking for / what you bring to the target role].
```

Example: "Senior Platform Engineer with 12 years building high-availability systems across FinTech and e-commerce. Architected a real-time payments platform processing £4.2B annually for 3M+ users. Seeking hands-on technical leadership roles where I can combine system design expertise with cross-functional team building."

---

## Phase 4 — Output Deliverables

1. **Scored analysis** with per-dimension breakdown and evidence
2. **Top 5 improvements** with expected point impact
3. **Optimized CV** (full rewrite in the same format as input) saved with `-optimized` suffix
4. **Master keyword list** — every hard skill, tool, framework, methodology, certification, and industry term extracted. Saved for `profile-optimizer` reuse. Both CV and LinkedIn must target identical keywords.
5. **Before/after comparison** — show original vs. optimized for the 3 most impactful changes
6. **Interview ammunition** (bonus) — for each SPAR bullet, note the full story version the user can tell in interviews

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

## Freelance / Contractor CV Mode

When user is a freelancer/contractor, apply adjustments from `../shared-references/freelance-context.md`:
- Project-based layout preferred over employer-based
- Skills matrix at top for quick scanning
- Returning clients or extended contracts signal reliability (social proof + authority)
- Include availability date, day-rate range (optional), IR35 awareness

---

## Reference Materials

- **`references/ats-keywords.md`** — Common ATS keyword categories by industry
- **`references/action-verbs.md`** — Categorized action verbs for achievement types
- **`references/psychology-cheatsheet.md`** — Quick-reference for persuasion techniques applied to CV writing
- **`../shared-references/freelance-context.md`** — Freelance CV structure and evaluation

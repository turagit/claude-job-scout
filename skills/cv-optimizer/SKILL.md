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

Analyze, score, and improve CVs/resumes for maximum impact with both ATS (Applicant Tracking Systems) and human recruiters.

## Analysis Framework

When analyzing a CV, evaluate across these five dimensions and produce a score (1-10) for each:

### 1. ATS Compatibility (Weight: 25%)

- Standard section headings (Experience, Education, Skills, Summary)
- No tables, columns, text boxes, headers/footers, or images that ATS cannot parse
- Clean formatting: standard fonts, consistent date formats (MM/YYYY or Month YYYY)
- File format suitability (.docx preferred for ATS, .pdf acceptable)
- Keywords from target job descriptions present in natural context

### 2. Content Impact (Weight: 30%)

- PAR method used: Problem → Action → Result
- Quantified achievements with metrics (%, $, #, time saved)
- Strong action verbs leading each bullet (Led, Delivered, Architected, Optimized)
- Relevance to target role — remove or minimize irrelevant experience
- No generic filler phrases ("responsible for", "duties included", "team player")

### 3. Keyword Optimization (Weight: 20%)

- Industry-standard terminology present (not creative synonyms)
- Technical skills listed explicitly, not implied
- Both spelled-out terms and acronyms included (e.g., "Search Engine Optimization (SEO)")
- Keywords woven into experience bullets, not just a skills list
- Match rate against target job description keywords (aim for 70%+)

### 4. Structure & Readability (Weight: 15%)

- Reverse chronological order (most recent first)
- Consistent formatting throughout (bullet style, spacing, alignment)
- Appropriate length: 1-2 pages for most roles, up to 3 for senior/academic
- Clear visual hierarchy: name > section headers > job titles > bullets
- White space balanced — not cramped, not sparse

### 5. Professional Positioning (Weight: 10%)

- Professional summary tailored to target role (3-4 lines max)
- LinkedIn URL included and matches CV content
- Contact info complete: name, email, phone, location (city/country), LinkedIn
- No photos, date of birth, marital status, or other non-essential personal info
- Certifications and education properly positioned based on career stage

## Improvement Process

1. **Read the CV** — Parse all content from the uploaded file
2. **Score each dimension** — Rate 1-10 with specific evidence
3. **Calculate overall score** — Weighted average across all dimensions
4. **Identify top 5 improvements** — Ranked by impact on job search success
5. **Rewrite weak sections** — Provide before/after examples using PAR method
6. **Generate optimized version** — Create improved CV preserving the user's voice

## PAR Method Rewriting

Transform weak bullets into strong ones:

**Weak:** "Managed a team of developers"
**Strong:** "Led a cross-functional team of 8 developers through a platform migration, delivering 3 months ahead of schedule and reducing infrastructure costs by 40%"

**Pattern:** [Action Verb] + [What you did] + [Scope/Scale] + [Measurable Result]

## ATS Keyword Strategy

When the user provides a target job description:

1. Extract all hard skills, tools, technologies, and certifications mentioned
2. Compare against CV content
3. Identify missing keywords that the user genuinely possesses
4. Suggest natural placements within experience bullets (never keyword-stuff)
5. Calculate a match percentage

## Output Format

Present analysis as:

1. **Overall Score: X/10** with dimension breakdown
2. **Strengths** — What's working well (2-3 items)
3. **Critical Improvements** — Top 5 changes ranked by impact
4. **Rewritten Sections** — Before/after for each improvement
5. **Keyword Gap Report** — If a target job description was provided

## Freelance / Contractor CV Mode

When the user indicates they are a freelancer or contractor (check `user-profile.json`), adjust the analysis framework:

### Structure Differences

- **Project-based layout** is preferred over employer-based — each contract should be a distinct entry with: Client name, Role title, Duration (MM/YYYY – MM/YYYY), Key deliverables
- **Skills matrix** at the top is more valuable for freelancers — recruiters scan for tech stack quickly
- **Career timeline** should show continuous engagement — gaps between contracts are normal but long gaps (6+ months) should be addressed

### Freelance-Specific Evaluation Criteria

Replace the standard evaluation with:

1. **Client Diversity (replaces Professional Positioning for freelancers)**
   - Variety of clients and industries shows adaptability
   - Mix of company sizes (startup to enterprise) is a strength
   - Returning clients or extended contracts signal reliability

2. **Skills Breadth & Depth**
   - Core tech stack clearly identified and prominent
   - Complementary skills show versatility
   - Certifications strengthen contractor credibility

3. **Project Impact**
   - Each contract should demonstrate clear deliverables and outcomes
   - Use PAR method but frame around project goals, not company goals
   - Quantify where possible: "Reduced deployment time by 60%", "Migrated 500k user platform"

4. **Contractor Signals**
   - Mention of contract types (fixed-term, T&M, SOW) shows professionalism
   - Security clearances, if applicable
   - IR35 status awareness (UK)
   - Professional indemnity insurance (if relevant to industry)

### Freelance CV Improvements to Suggest

- Add a "Key Technologies" or "Tech Stack" section above experience
- Add availability status: "Available from [date]"
- Include day rate range (optional but increasingly common)
- List notable clients by name if permitted, industry if not

## Reference Materials

- **`references/ats-keywords.md`** — Common ATS keyword categories by industry
- **`references/action-verbs.md`** — Categorized action verbs for different achievement types

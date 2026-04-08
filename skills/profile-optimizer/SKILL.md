---
name: profile-optimizer
description: >
  This skill should be used when the user asks to "optimize my LinkedIn profile",
  "improve my LinkedIn", "make my profile stand out", "update my LinkedIn headline",
  "rewrite my LinkedIn summary", "LinkedIn SEO", "attract recruiters on LinkedIn",
  or needs guidance on making their LinkedIn profile more visible to recruiters
  and ATS systems. Also triggers when aligning a LinkedIn profile with a CV.
version: 0.3.0
---

# LinkedIn Profile Optimizer

Analyze and enhance LinkedIn profiles to maximize recruiter visibility and ATS compatibility. **The user's CV is the primary input** — every section proposal is derived from CV content.

## CV Requirement

The CV is mandatory. If no CV is found in the workspace:
1. Ask the user to provide their CV (upload, paste, or point to a file path)
2. Do not proceed until the CV is loaded — it drives all content proposals

Once loaded, extract: role titles, seniority level, key skills (technical and domain), quantified achievements, industry/domain context, and career narrative.

**Master keyword list:** Reuse the list from `user-profile.json` → `master_keyword_list` (produced by `cv-optimizer`). If it doesn't exist, build it from the CV: every hard skill, tool, framework, methodology, certification, and industry term. This list is the single source of truth for all keyword placement across the profile.

## CV-Driven Section Proposals

For each LinkedIn section, generate ready-to-paste content derived from the CV.

### 1. Headline (Critical — 220 characters)

Use CV data to propose 2-3 headline options:
- Extract the user's current/target role title from CV
- Pull top 3 searchable skills from CV skills and experience sections
- Include a value statement derived from the strongest CV achievement
- Apply formulas from `references/headline-formulas.md`
- Use industry-standard job titles that recruiters search for — see `references/recruiter-search-patterns.md` for common search terms by role
- Write the headline so it also works as a Google snippet (name + headline appears in Google results for name searches)

**Example derivation:** CV says "Led platform migration for 50k users, reducing costs 40%" → Headline option: `Senior Platform Engineer | Cloud Migration & Cost Optimisation | Delivered 40% Infrastructure Savings`

### 2. About / Summary (200-400 words)

Build from CV content in this structure:
- **Line 1-3 (visible hook):** Distill the CV's professional summary into a compelling opener — who you are, what you do, your signature achievement. These lines must stand alone since they show before "see more". Write these to also work as a Google search snippet.
- **Expertise paragraph:** Expand on CV skills and domain knowledge, rewritten in first-person conversational tone (CV is third-person/formal, LinkedIn is first-person/approachable)
- **Key achievements:** Take the 3-4 strongest quantified results from the CV and reframe as a narrative ("I led..." not "Led...")
- **What I'm looking for:** Derive from CV's target role, seniority, and work preferences (remote/contract/permanent)
- **Call to action:** "Drop me a message if..." or "Let's connect if you're looking for..."
- Weave CV keywords naturally throughout — primary keywords 2-3x, secondary 1-2x

### 3. Experience

For each role on the CV:
- **Job title:** Use the CV title if it's industry-standard and searchable. If the CV has a creative/internal title, propose a standard equivalent for LinkedIn (e.g., CV: "Engineering Lead" → LinkedIn: "Senior Software Engineer / Engineering Lead"). See `references/recruiter-search-patterns.md` for standard ↔ creative title mappings.
- **Company + dates:** Match CV exactly — flag any discrepancies
- **Bullets:** Take CV bullets and expand them using PAR method in conversational tone:
  - CV bullet → identify the Problem/context, Action taken, Result achieved
  - Rewrite with richer context than CV allows (LinkedIn has no page limit)
  - Ensure every bullet contains at least one searchable keyword from the master keyword list
  - Current role: 4-5 bullets (most detailed). Previous roles: 3-4 bullets. Older roles: 2-3 bullets
- **Rich media:** Suggest what to attach based on CV content (e.g., if CV mentions a project, suggest linking to it)

### 4. Skills & Endorsements

Build the skills list directly from the master keyword list:
- Extract every hard skill, tool, framework, methodology, and certification mentioned in CV
- Add industry-standard synonyms the CV may have missed (e.g., CV says "CI/CD" → also add "Jenkins", "GitHub Actions" if mentioned in experience context)
- Ensure exact-match phrasing that ATS systems import as structured tags (e.g., "Python" not "Python Programming Language") — many ATS (Greenhouse, Lever, Workday) import LinkedIn skills as structured tags, not free text
- Target 30-50 skills total
- Propose top 3 to pin: the 3 skills most relevant to the user's target role based on CV emphasis
- Mix: technical (from CV skills section), tools (from CV experience), methodologies (from CV), soft skills (inferred from leadership/collaboration achievements in CV)

### 5. Featured Section

Propose items based on CV content:
- Any portfolio links, publications, or projects mentioned in CV
- Suggest creating a case study from the CV's strongest achievement
- If CV mentions certifications, link to credential pages
- Target 3-5 featured items — these appear above the fold and drive engagement

### 6. Additional Sections

Derive from CV:
- **Certifications:** List all from CV, suggest adding credential URLs
- **Education:** Match CV exactly
- **Recommendations:** Suggest requesting recommendations from managers/clients named or implied in CV achievements
- **Volunteer/Projects:** Surface any from CV that aren't in the experience section

### 7. Open to Work Signal

Configure the private recruiter-only "Open to Work" signal (not the public green badge):
- **Job titles:** Set to 3-5 industry-standard titles derived from CV role titles — use exact terms recruiters search for (see `references/recruiter-search-patterns.md`)
- **Location:** Match the user's target search area from CV preferences
- **Work types:** Remote/on-site/hybrid based on CV and user preferences
- **Start date:** Based on user's availability
- See `references/open-to-work-config.md` for step-by-step setup

This is the single highest-impact discoverability setting — it places the profile directly into recruiter search results filtered by "Open to Work" candidates.

### 8. Structured Profile Fields

These fields act as recruiter search filters and ATS import fields:
- **Location:** Set to the broadest correct geographic value (e.g., "United Kingdom" not a small town, if targeting remote/national roles). Recruiters filter by location — too narrow means exclusion from searches.
- **Industry:** Must match the target role's industry, not necessarily the current employer's industry. This is a recruiter filter.
- **Custom URL:** Set to `/in/firstname-lastname` or similar clean slug. Default random URLs look unprofessional and rank lower in Google.
- **Profile photo:** Required for All-Star status. Professional headshot.
- **Banner image:** Use as a visual keyword billboard — role title, key skills, or professional tagline.
- **Name pronunciation / audio intro:** Profiles with these get a badge and extra visibility in search.

## Activity & Engagement Layer

Static profile content is necessary but not sufficient. The LinkedIn algorithm rewards active profiles:

### Social Selling Index (SSI)
- Check SSI score at `linkedin.com/sales/ssi` — target 70+
- SSI measures: establishing brand, finding the right people, engaging with insights, building relationships
- Higher SSI = higher search ranking and more profile views

### Content Strategy (Propose Based on CV)
- Suggest 2-3 post topics per week derived from CV expertise areas (e.g., CV shows "cloud migration" experience → suggest posting about migration lessons learned)
- Comments on industry posts with substantive replies (not "great post!") boost profile impressions significantly
- Engagement on others' content increases your own profile's visibility in their network

### Creator Mode Assessment
- Recommend enabling if user is targeting thought leadership or inbound recruiter interest
- Changes "Connect" → "Follow", adds hashtag topics to profile, surfaces posts to non-connections
- Hashtag topics should align with CV keywords (e.g., #CloudComputing, #DataEngineering)

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

## Scoring Framework

### Section Scores (1-10 each)
Score each section for content quality and completeness:
- Headline, About, Experience, Skills, Featured, Additional Sections, Open to Work, Structured Fields

### Cross-Cutting Scores
These measure discoverability factors that span multiple sections:

| Score | What it measures | How to calculate |
|-------|-----------------|------------------|
| **Keyword Coverage** | % of master keyword list found anywhere on profile | `(keywords_found / total_keywords) * 100` — target 90%+ |
| **Search Appearance Estimate** | Likelihood of appearing in recruiter searches | Based on: headline keywords ✓, skills count ≥30 ✓, All-Star complete ✓, Open to Work enabled ✓, SSI ≥70 ✓ |
| **Recruiter 10-Second Test** | Does the profile answer what a recruiter checks in <10 seconds | 5 checks: current role clear ✓, years of experience evident ✓, key skills visible ✓, location stated ✓, availability signal present ✓ |
| **CV Alignment** | Consistency between CV and LinkedIn | Dates match ✓, titles match ✓, companies match ✓, all CV keywords on LinkedIn ✓, no contradictions ✓ |

### Overall Score
Weighted aggregate: Section scores (60%) + Cross-cutting scores (40%). Present as X/100 with tier: A (85-100), B (70-84), C (55-69), D (<55).

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
6. **Generate section-by-section proposals** — ready-to-paste content derived from CV
7. **Calculate all scores** — section scores, cross-cutting scores, overall score
8. **Present before/after comparison** for each section with the CV source highlighted
9. **Show alignment report** — keyword coverage, missing achievements, discrepancies
10. **Apply changes** via browser with user permission — one section at a time

## State & Caching

- **`.job-scout/user-profile.json`** — source of `master_keyword_list` (built by `cv-optimizer`). Reuse it; rebuild only if `cv_hash` changed.
- **`.job-scout/cache/linkedin-profile.json`** — last-seen LinkedIn profile snapshot. If < 7 days old and the user hasn't reported edits, reuse it instead of re-reading every section via the browser. Re-evaluate only sections that changed.

## Reference Materials

- **`references/linkedin-seo.md`** — Algorithm factors, keyword strategy, and recruiter search behaviour
- **`references/headline-formulas.md`** — Headline templates by role
- **`references/recruiter-search-patterns.md`** — How recruiters search, Boolean queries, title mappings
- **`references/open-to-work-config.md`** — Open to Work setup guide
- **`../shared-references/workspace-layout.md`** — `.job-scout/` folder layout and bootstrap
- **`../shared-references/cv-loading.md`** — CV loading + caching procedure

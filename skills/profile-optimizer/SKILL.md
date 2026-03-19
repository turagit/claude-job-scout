---
name: profile-optimizer
description: >
  This skill should be used when the user asks to "optimize my LinkedIn profile",
  "improve my LinkedIn", "make my profile stand out", "update my LinkedIn headline",
  "rewrite my LinkedIn summary", "LinkedIn SEO", "attract recruiters on LinkedIn",
  or needs guidance on making their LinkedIn profile more visible to recruiters
  and ATS systems. Also triggers when aligning a LinkedIn profile with a CV.
version: 0.2.0
---

# LinkedIn Profile Optimizer

Analyze and enhance LinkedIn profiles to maximize recruiter visibility and ATS compatibility. **The user's CV is the primary input** — every section proposal is derived from CV content.

## CV Requirement

The CV is mandatory. If no CV is found in the workspace:
1. Ask the user to provide their CV (upload, paste, or point to a file path)
2. Do not proceed until the CV is loaded — it drives all content proposals

Once loaded, extract:
- **Role titles** and seniority level
- **Key skills** (technical and domain)
- **Quantified achievements** (metrics, percentages, revenue, scale)
- **Industry and domain** context
- **Career narrative** (progression, specialisation, transitions)

## CV-Driven Section Proposals

For each LinkedIn section, generate ready-to-paste content derived from the CV.

### 1. Headline (Critical — 220 characters)

Use CV data to propose 2-3 headline options:
- Extract the user's current/target role title from CV
- Pull top 3 searchable skills from CV skills and experience sections
- Include a value statement derived from the strongest CV achievement
- Apply formulas from `references/headline-formulas.md`

**Example derivation:** CV says "Led platform migration for 50k users, reducing costs 40%" → Headline option: `Senior Platform Engineer | Cloud Migration & Cost Optimisation | Delivered 40% Infrastructure Savings`

### 2. About / Summary (200-400 words)

Build from CV content in this structure:
- **Line 1-3 (visible hook):** Distill the CV's professional summary into a compelling opener — who you are, what you do, your signature achievement. These lines must stand alone since they show before "see more"
- **Expertise paragraph:** Expand on CV skills and domain knowledge, rewritten in first-person conversational tone (CV is third-person/formal, LinkedIn is first-person/approachable)
- **Key achievements:** Take the 3-4 strongest quantified results from the CV and reframe as a narrative ("I led..." not "Led...")
- **What I'm looking for:** Derive from CV's target role, seniority, and work preferences (remote/contract/permanent)
- **Call to action:** "Drop me a message if..." or "Let's connect if you're looking for..."
- Weave CV keywords naturally throughout — primary keywords 2-3x, secondary 1-2x

### 3. Experience

For each role on the CV:
- **Job title:** Use the CV title if it's industry-standard and searchable. If the CV has a creative/internal title, propose a standard equivalent for LinkedIn (e.g., CV: "Engineering Lead" → LinkedIn: "Senior Software Engineer / Engineering Lead")
- **Company + dates:** Match CV exactly — flag any discrepancies
- **Bullets:** Take CV bullets and expand them using PAR method in conversational tone:
  - CV bullet → identify the Problem/context, Action taken, Result achieved
  - Rewrite with richer context than CV allows (LinkedIn has no page limit)
  - Ensure every bullet contains at least one searchable keyword
  - Current role: 4-5 bullets (most detailed). Previous roles: 3-4 bullets. Older roles: 2-3 bullets
- **Rich media:** Suggest what to attach based on CV content (e.g., if CV mentions a project, suggest linking to it)

### 4. Skills & Endorsements

Build the skills list directly from CV:
- Extract every hard skill, tool, framework, methodology, and certification mentioned in CV
- Add industry-standard synonyms the CV may have missed (e.g., CV says "CI/CD" → also add "Jenkins", "GitHub Actions" if mentioned in experience context)
- Ensure exact-match phrasing that ATS systems import as structured tags (e.g., "Python" not "Python Programming Language")
- Target 30-50 skills total
- Propose top 3 to pin: the 3 skills most relevant to the user's target role based on CV emphasis
- Mix: technical (from CV skills section), tools (from CV experience), methodologies (from CV), soft skills (inferred from leadership/collaboration achievements in CV)

### 5. Featured Section

Propose items based on CV content:
- Any portfolio links, publications, or projects mentioned in CV
- Suggest creating a case study from the CV's strongest achievement
- If CV mentions certifications, link to credential pages
- Target 3-5 featured items

### 6. Additional Sections

Derive from CV:
- **Certifications:** List all from CV, suggest adding credential URLs
- **Education:** Match CV exactly
- **Recommendations:** Suggest requesting recommendations from managers/clients named or implied in CV achievements
- **Volunteer/Projects:** Surface any from CV that aren't in the experience section

## Profile vs CV Alignment

After proposing all content, generate an alignment report:
- Dates, titles, and companies must match exactly between CV and LinkedIn
- Every keyword on the CV must appear somewhere on the LinkedIn profile
- Flag CV achievements not represented on LinkedIn
- Flag LinkedIn content that contradicts or isn't supported by the CV
- Tone shift is expected: CV formal/concise → LinkedIn conversational/first-person

## Optimization Process

1. **Load CV** — read and extract all structured data (roles, skills, achievements, keywords)
2. **Read current LinkedIn profile** via browser, score each section (1-10)
3. **Generate section-by-section proposals** — ready-to-paste content derived from CV
4. **Present before/after comparison** for each section with the CV source highlighted
5. **Show alignment report** — keyword coverage, missing achievements, discrepancies
6. **Apply changes** via browser with user permission — one section at a time

## Reference Materials

- **`references/linkedin-seo.md`** — Algorithm factors and keyword strategy
- **`references/headline-formulas.md`** — Headline templates by role

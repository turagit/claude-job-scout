---
description: Analyze and improve your LinkedIn profile for recruiters and ATS
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

Optimize the user's LinkedIn profile for recruiter visibility and ATS, using their CV as the primary content source.

## Step 0: Bootstrap workspace

Follow `shared-references/workspace-layout.md` to ensure `.job-scout/` exists.

## Step 1: Load CV (Required)

Follow `shared-references/cv-loading.md` — **do not proceed without a CV**. Parse the CV and extract: role titles, skills, quantified achievements, career narrative, industry context, certifications, education. Reuse the `master_keyword_list` from `.job-scout/user-profile.json` (built by `cv-optimizer`); rebuild only if the CV's hash has changed.

## Step 2: Read LinkedIn Profile (with diff cache)

Check `.job-scout/cache/linkedin-profile.json`. If the snapshot is < 7 days old AND the user has not indicated they edited the profile since, reuse it instead of re-reading every section via the browser.

If a fresh read is needed, navigate to the user's LinkedIn profile and read all sections: headline, about, experience, education, skills, featured, certifications, recommendations. Also check: custom URL, location field, industry field, profile photo, banner image, Open to Work status, creator mode status. Write the result back to `.job-scout/cache/linkedin-profile.json` with a timestamp.

## Step 3: Check Activity & Engagement

Check SSI score at `linkedin.com/sales/ssi`. Note recent posting activity and engagement level. Flag if SSI < 70 or no activity in 30+ days.

## Step 4: Analyze and Score

Load the **profile-optimizer** skill.

**Section scores (1-10 each):** headline (keyword-rich, uses CV strengths?), about (hooks with CV achievements, keywords woven in?), experience (PAR method, matches CV, quantified?), skills (30+ from CV, top 3 pinned?), featured (CV projects showcased?), additional sections (certifications, education complete?), Open to Work (enabled with correct titles?), structured fields (location, industry, URL, photo correct?).

**Cross-cutting scores:**
- Keyword coverage: % of master keyword list found on profile (target 90%+)
- Search appearance estimate: headline keywords + skills ≥30 + All-Star + Open to Work + SSI ≥70
- Recruiter 10-second test: current role clear, years evident, key skills visible, location stated, availability signalled
- CV alignment: dates, titles, companies, keywords all consistent

Calculate overall score: section scores (60%) + cross-cutting scores (40%) → X/100 with tier (A/B/C/D).

## Step 5: Boolean Search Simulation

Using `references/recruiter-search-patterns.md`, construct 2-3 Boolean queries a recruiter would likely use for the user's target role. Check whether all required keywords exist in searchable profile fields. Flag any missing terms.

## Step 6: Generate CV-Driven Proposals

For every section scoring below 8, generate ready-to-paste content derived from the CV:
- **Headline:** 2-3 options using CV role title + top skills + strongest achievement. Use searchable titles from `references/recruiter-search-patterns.md`. Apply headline formulas.
- **About:** Full 200-400 word rewrite built from CV summary, achievements, and keywords. First-person conversational tone. Hook in first 3 lines (also works as Google snippet).
- **Experience:** For each CV role, rewrite bullets in PAR method with richer context. Expand current role most. Propose standard job titles if CV titles aren't searchable (include mapping rationale).
- **Skills:** Full list extracted from master keyword list with synonyms and ATS-exact phrasing. Both acronym and spelled-out forms. Propose top 3 to pin.
- **Featured:** Propose items from CV projects, publications, portfolio links.
- **Open to Work:** Propose configuration — 3-5 job titles (standard searchable terms from CV), location, work types, start date. See `references/open-to-work-config.md`.
- **Structured fields:** Propose location (broadest correct value), industry (matching target role), custom URL, banner image concept.
- **Activity:** Suggest 2-3 post topics per week based on CV expertise areas. Suggest creator mode if appropriate.

Present as a table per section: Current Content | Proposed Content | CV Source (which CV entry it's derived from).

## Step 7: Alignment Report

Show: keyword coverage (% of master keyword list found on LinkedIn), CV achievements missing from LinkedIn, any date/title/company mismatches, Boolean simulation results. List each gap with a specific fix.

## Step 8: Apply Changes

For each change user approves: navigate to section on LinkedIn, edit, update with approved text, save, confirm. **Always show exact content and get approval before editing.** After all changes, review full profile end-to-end, re-run scoring, and show updated scores vs original.

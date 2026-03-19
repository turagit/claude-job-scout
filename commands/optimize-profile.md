---
description: Analyze and improve your LinkedIn profile for recruiters and ATS
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

Optimize the user's LinkedIn profile for recruiter visibility and ATS, using their CV as the primary content source.

## Step 1: Load CV (Required)

Search the workspace for CV files (pdf, docx, md, txt). If multiple found, ask which to use. If none found, ask the user to provide their CV — **do not proceed without it**. Parse the CV and extract: role titles, skills, quantified achievements, career narrative, industry context, certifications, education.

## Step 2: Read LinkedIn Profile

Navigate to user's LinkedIn profile (ask for URL or find via LinkedIn menu). Read all sections: headline, about, experience, education, skills, featured, certifications, recommendations. Note completeness and All-Star status requirements.

## Step 3: Analyze and Score

Load the **profile-optimizer** skill. Score each section (1-10): headline (keyword-rich, uses CV strengths?), about (hooks with CV achievements, keywords woven in?), experience (PAR method, matches CV, quantified?), skills (30+ from CV, top 3 pinned?), completeness (All-Star status?), CV alignment (dates, titles, keywords all present?). Calculate overall score.

## Step 4: Generate CV-Driven Proposals

For every section scoring below 8, generate ready-to-paste content derived from the CV:
- **Headline:** 2-3 options using CV role title + top skills + strongest achievement. Apply headline formulas.
- **About:** Full 200-400 word rewrite built from CV summary, achievements, and keywords. First-person conversational tone. Hook in first 3 lines.
- **Experience:** For each CV role, rewrite bullets in PAR method with richer context than CV. Expand current role most. Propose standard job titles if CV titles aren't searchable.
- **Skills:** Full list extracted from CV with synonyms and ATS-friendly phrasing. Propose top 3 to pin.
- **Featured:** Propose items from CV projects, publications, portfolio links.
- **Additional:** Certifications from CV, recommendation requests based on CV roles.

Present as a table per section: Current Content | Proposed Content | CV Source (which CV entry it's derived from).

## Step 5: Alignment Report

Show: keyword coverage (% of CV keywords found on LinkedIn), CV achievements missing from LinkedIn, any date/title/company mismatches. List each gap with a fix.

## Step 6: Apply Changes

For each change user approves: navigate to section on LinkedIn, edit, update with approved text, save, confirm. **Always show exact content and get approval before editing.** After all changes, review full profile end-to-end and show updated scores.

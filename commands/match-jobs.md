---
description: Score and rank job listings against your CV and requirements
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

Analyze LinkedIn job listings and rank them against the user's CV and requirements.

## Step 1: Identify Source

Ask the user where to find jobs: job alerts (LinkedIn notifications), saved jobs, specific URL, or current search results.

## Step 2: Load Profile

Follow the shared CV-loading procedure in `shared-references/cv-loading.md`. Load the **job-matcher** skill.

## Step 3: Gather and Score

Navigate to appropriate LinkedIn page. For each listing, extract: title, company, location, salary, experience level, required/preferred skills, description, Easy Apply status, posting date, applicant count. Apply job-matcher scoring framework, filter out D-Tier.

Check `job-reports/tracker.json` first — skip applied/rejected jobs, note previously seen ones with old score.

## Step 4: Present Results

Show ranked markdown table (title, company, score, tier, Easy Apply, posted, applicants). For A-Tier and top B-Tier, provide detailed match cards with score breakdown, matched skills, gaps, and red flags.

Write newly scored jobs to tracker with status "seen".

## Next Steps

Ask which jobs to apply to (`/apply`), save, or discard. Suggest refining search if results are poor.

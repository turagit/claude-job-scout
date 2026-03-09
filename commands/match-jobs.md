---
description: Score and rank job listings against your CV and requirements
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

Analyze LinkedIn job listings (from alerts, search results, or saved jobs) and rank them against the user's CV and requirements.

## Step 1: Identify Source

Ask the user where to find jobs to analyze:
1. **Job Alerts** — Check LinkedIn notifications for new alert results
2. **Saved Jobs** — Review their saved/bookmarked jobs on LinkedIn
3. **Specific URL** — User provides a direct link to a job listing
4. **Current Search Results** — Analyze what's currently on screen

## Step 2: Load CV and Requirements

- Read the user's CV from the workspace
- Recall or ask for their requirements (target roles, location, salary, deal-breakers)
- Load the job-matcher skill for the scoring framework

## Step 3: Gather Job Listings

Using the browser, navigate to the appropriate LinkedIn page:
- **Alerts:** Go to LinkedIn notifications or job alert emails and open each listing
- **Saved Jobs:** Navigate to `https://www.linkedin.com/my-items/saved-jobs/`
- **Search Results:** Use current search results page

For each job listing:
1. Open the full job description
2. Extract: title, company, location, salary range (if shown), experience level, required skills, preferred skills, job description, Easy Apply availability, posting date, number of applicants
3. Move to next listing

## Step 4: Score and Rank

Apply the job-matcher skill scoring framework:
- Skills Match (30%)
- Experience Alignment (25%)
- Requirements Fit (25%)
- Growth & Culture (10%)
- Practical Factors (10%)

Filter out D-Tier matches immediately.

## Step 5: Present Results

Show a ranked summary table:

```
| Rank | Title | Company | Score | Tier | Easy Apply | Posted | Applicants |
```

For each A-Tier and top B-Tier job, provide a detailed match card:
- Score breakdown by dimension
- Matched skills vs. gaps
- Red flags (if any)
- Specific reasons this is a good/poor match

## Step 6: Recommend Next Steps

Ask the user to review the matches and decide:
- Which jobs to apply to → suggest /apply
- Which to save for later
- Which to discard
- Whether to refine search criteria based on what was found

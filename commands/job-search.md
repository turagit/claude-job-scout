---
description: Search LinkedIn for jobs matching your CV and requirements
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: [optional: job-title]
---

Run an interactive LinkedIn job search using the user's CV and requirements.

## Step 1: Gather Requirements

If no previous requirements are stored, ask the user about:
1. **Target roles** — Job titles and variations (e.g., "Software Engineer", "Backend Developer")
2. **Location** — Cities, countries, or "Remote"
3. **Salary range** — Minimum and ideal, currency
4. **Seniority level** — Junior, Mid, Senior, Lead, etc.
5. **Company preferences** — Size, industry, specific companies to target or avoid
6. **Deal-breakers** — Absolute non-negotiables
7. **Nice-to-haves** — Preferences that aren't deal-breakers

If an argument is provided ($1), use it as the primary job title to search for.

## Step 2: Load the CV

Check if the user has a CV available in the workspace. If not, ask them to provide one — the CV is essential for matching.

## Step 3: Search LinkedIn

Using the browser tools, navigate to LinkedIn Jobs and perform targeted searches:

1. Go to `https://www.linkedin.com/jobs/`
2. Enter the target job title in the search bar
3. Set location filters
4. Apply relevant filters (Experience Level, Remote, Date Posted — prioritize "Past Week")
5. For each promising result, open the job listing and read the full description

## Step 4: Analyze Results

Load the job-matcher skill. For each job listing found:
- Extract: title, company, location, salary (if shown), requirements, description
- Score against the CV and user requirements
- Assign a match tier (A/B/C/D)

## Step 5: Present Results

Present a ranked table of all jobs found:

```
| Rank | Title | Company | Score | Tier | Easy Apply | Key Match | Key Gap |
```

For A-Tier and top B-Tier matches, provide detailed analysis cards with:
- Full match breakdown by dimension
- Specific skills that match and gaps
- Recommendation (Apply / Consider / Skip)

## Step 6: Next Steps

Ask the user:
- Want to create alerts for these searches? (→ suggest /create-alerts)
- Ready to apply to any of these? (→ suggest /apply)
- Want to search for different terms?

Perform multiple searches if the user has several target roles.

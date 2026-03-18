---
description: Search LinkedIn for jobs matching your CV and requirements
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: [optional: job-title]
---

Run an interactive LinkedIn job search using the user's CV and requirements.

## Step 1: Load Profile & Requirements

Check `user-profile.json` — if exists, load and confirm with user. For any missing fields, ask: target roles, location, salary range, seniority, company preferences, deal-breakers, nice-to-haves. If argument provided ($1), use as primary search title. Save new info back to `user-profile.json` (merge, don't overwrite).

## Step 2: Load CV

Locate CV in workspace. If none found, ask user to provide one.

## Step 3: Search LinkedIn

Navigate to `https://www.linkedin.com/jobs/`. Enter target title, set location and filters (Experience Level, Remote, Date Posted — prioritize "Past Week"). Open each promising listing and extract: title, company, location, salary, requirements, description, Easy Apply status.

## Step 4: Score and Present

Load the **job-matcher** skill. Score each listing, assign tiers. Present ranked markdown table (title, company, score, tier, Easy Apply, key match, key gap). For A-Tier and top B-Tier, provide detailed analysis with score breakdown and matched skills vs gaps.

Perform multiple searches if user has several target roles. If profile is >30 days old, suggest `/analyze-cv`.

## Next Steps

Suggest `/create-alerts` for monitoring, `/apply` for approved jobs, or refining search terms.

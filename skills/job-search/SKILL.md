---
name: job-search
description: Search LinkedIn for jobs matching your CV and requirements
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: [optional: job-title]
disable-model-invocation: true
---

Run an interactive LinkedIn job search using the user's CV and requirements.

## Browser policy (read first)

All browser work in this command uses **the Claude Chrome extension exclusively**. Never request computer use. See `shared-references/browser-policy.md`.

## Step 0: Bootstrap workspace

Follow `shared-references/workspace-layout.md` to ensure `.job-scout/` exists.

## Step 1: Load Profile, CV & Requirements

Follow `shared-references/cv-loading.md`. If argument provided ($1), use as primary search title. For any missing requirement fields, ask: target roles, location, salary range, seniority, company preferences, deal-breakers, nice-to-haves. Save new info back to `.job-scout/user-profile.json` (merge, don't overwrite).

## Step 3: Search LinkedIn

Navigate to `https://www.linkedin.com/jobs/`. Enter target title, set location and filters (Experience Level, Remote, Date Posted — prioritize "Past Week"). Collect job IDs first and dedupe against `.job-scout/tracker.json` (see `shared-references/tracker-schema.md`) before opening any listing. Only extract details for new jobs: title, company, location, salary, requirements, description, Easy Apply status.

**Corpus enrichment:** after extraction, run the JD keyword extraction procedure from `../shared-references/jd-keyword-extraction.md` on each new job's description. Merges keywords into `.job-scout/cache/jd-keyword-corpus.json`.

## Step 4: Score and Present

Load the **_job-matcher** skill. Score each listing, assign tiers. Present ranked markdown table (title, company, score, tier, Easy Apply, key match, key gap). For A-Tier and top B-Tier, provide detailed analysis with score breakdown and matched skills vs gaps.

Perform multiple searches if user has several target roles. If profile is >30 days old, suggest `/analyze-cv`.

## Next Steps

Suggest `/create-alerts` for monitoring, `/apply` for approved jobs, or refining search terms.

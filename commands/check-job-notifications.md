---
description: Check LinkedIn notifications for new job alerts, analyze matches against CV and requirements, and report best opportunities
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

Check LinkedIn job alert notifications, analyze each opportunity against the user's CV and requirements, and produce a prioritized report of best matches — saved to file for future `/apply` use.

## Default Requirements (Always Active)

- **Work arrangement:** Fully remote only
- **Contract type:** Freelance / Contract
- **Salary transparency:** Prioritize listings that disclose salary or day rate; flag others with "Does not mention rate"

## Step 1: Load CV & Profile

Follow the shared CV-loading procedure in `shared-references/cv-loading.md`. If no profile exists yet, analyze the CV to extract skills, technologies, seniority, target roles, and domain expertise. Save to `user-profile.json` (create or merge) including `cv_path`, `cv_summary`, and `requirements` with defaults (`work_arrangement: "remote"`, `contract_type: "freelance"`). See user-profile-schema reference for schema.

## Step 2: Collect Jobs from LinkedIn

Navigate to `https://www.linkedin.com/notifications/`. Scan for job alert notifications (phrases like "new opportunities in", "new job alert", "jobs that match your"). Scroll 2-3 times to catch recent alerts.

For each alert, open every job listing and extract: job title, company, location (remote/hybrid/on-site + city), salary/rate (note presence or absence), contract type, experience level, required skills, preferred skills, full description, Easy Apply status, posting date, applicant count, job URL. Tag source as "Job Alert".

Then navigate to `https://www.linkedin.com/jobs/` and scan top 10-15 recommended jobs. Extract same fields for relevant ones. Tag source as "Recommendation".

## Step 3: Filter

Remove jobs that clearly violate default requirements:
- Non-remote (on-site/hybrid only) — discard. If ambiguous, keep and flag "Remote status unclear".
- Permanent-only with no contract option — discard. If ambiguous, keep and flag "Contract type unclear".

## Step 4: Score and Rank

Load the **job-matcher** skill. Apply the full scoring framework with freelance adjustments if applicable. Jobs that disclose compensation sort above same-tier jobs that don't.

Assign tiers: **A (85-100)** apply immediately, **B (70-84)** worth applying, **C (55-69)** consider if interesting, **D (<55)** discard.

## Step 5: Check Tracker for Duplicates

Load `job-reports/tracker.json` if it exists. For each job:
- Already applied or rejected by user → skip entirely
- Previously seen → include but note "Previously seen on [date]"
- New → process normally

## Step 6: Present Results

Show a clean markdown summary grouped by tier (A, B, C — omit D). Per job show: title, company, rate (or "Does not mention rate"), location, contract type, posting date, score, top 3 skill matches, notable gaps, and job URL. For A-Tier matches, add 2-3 sentences on why it's a strong match.

Include a summary line: jobs scanned, after filters, matches per tier, filtered out count.

## Step 7: Save Report

Save detailed markdown report to `job-reports/[YYYY-MM-DD]-new-jobs.md` with: header/stats, CV profile summary, full ranked list with score breakdowns, filtered-out jobs summary, and recommendations. Create `job-reports/` if needed. If today's report exists, append counter.

## Step 8: Update Tracker

Write all newly discovered jobs to `job-reports/tracker.json` with title, company, score, tier, first_seen, last_seen, and status "seen". Update existing entries if scores changed. Track cumulative stats (total scanned, applied, rejected, last run). Create the file if missing.

When user approves applications, update status to "approved". The `/apply` command will update to "applied" with date.

## Next Steps

After presenting results, ask which jobs to apply to (offer `/apply`), whether to refine alerts (`/create-alerts`), or check recruiter messages (`/check-inbox`).

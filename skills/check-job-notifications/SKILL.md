---
name: check-job-notifications
description: Check LinkedIn notifications for new job alerts, analyze matches against CV and requirements, and report best opportunities
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
disable-model-invocation: true
---

Check LinkedIn job alert notifications, analyze each opportunity against the user's CV and requirements, and produce a prioritized report of best matches — saved for future `/apply` use.

## Browser policy (read first)

All browser work in this command uses **the Claude Chrome extension exclusively**. Never request computer use. Never suggest Playwright, Selenium, or any other automation framework. See `shared-references/browser-policy.md` for the full policy. If the Chrome extension is not available in the current session, stop and report it — do not escalate to any other mechanism.

## Default Requirements (Always Active)

- **Work arrangement:** Fully remote only
- **Contract type:** Freelance / Contract
- **Salary transparency:** Prioritize listings that disclose salary or day rate; flag others with "Does not mention rate"

## Step 0: Bootstrap workspace

Follow `shared-references/workspace-layout.md` to ensure `.job-scout/` exists in the current workspace. All paths below are inside `.job-scout/`.

## Step 1: Load CV & Profile

Follow `shared-references/cv-loading.md`. If no profile exists, analyze the CV to extract skills, technologies, seniority, target roles, and domain expertise. Save to `.job-scout/user-profile.json` (create or merge) including `cv_path`, `cv_hash`, `cv_summary`, and `requirements` (defaults: `work_arrangement: "remote"`, `contract_type: "freelance"`).

## Step 2: Collect candidate job IDs (NO extraction yet)

Navigate to `https://www.linkedin.com/notifications/?filter=jobs_all`. Scroll 2-3 times to load recent alerts.

Identify **every unread job alert notification** (highlighted in blue). Do NOT stop after the first one.

For each unread alert: open the alert and collect the **job IDs and URLs** of every individual listing inside it. Tag source as "Job Alert". Do not extract full details yet.

## Step 3: Dedupe against tracker FIRST

Load `.job-scout/tracker.json` (see `shared-references/tracker-schema.md`). For each candidate job ID:

- **Already in tracker** (seen / approved / applied / rejected) → bump `last_seen`, do NOT re-extract, do NOT re-score. Skip.
- **New** → keep in the to-process list.

This is the primary token-saving step. Never extract a job you already know.

## Step 4: Extract details for new jobs only

For each *new* job: open it and extract title, company, location (remote/hybrid/on-site + city), salary/rate, contract type, experience level, required skills, preferred skills, full description, Easy Apply status, posting date, applicant count, job URL.

## Step 5: Filter

Drop jobs that violate default requirements:
- Non-remote (on-site/hybrid only) — discard. If ambiguous, keep and flag "Remote status unclear".
- Permanent-only with no contract option — discard. If ambiguous, keep and flag "Contract type unclear".

## Step 6: Score and rank

Load the **job-matcher** skill. Apply the scoring framework with freelance adjustments if applicable. Jobs that disclose compensation sort above same-tier jobs that don't. Cache each score in `.job-scout/cache/scores.json` keyed by `(job_id, cv_hash, profile_hash)`.

Tiers: **A (85-100)** apply immediately, **B (70-84)** worth applying, **C (55-69)** consider, **D (<55)** discard.

## Step 7: Present results

Markdown summary grouped by tier (A, B, C — omit D). Per job: title, company, rate (or "Does not mention rate"), location, contract type, posting date, score, top 3 skill matches, notable gaps, job URL. A-tier gets 2-3 sentences explaining the match. B/C tiers get a compact one-line table — do not write paragraph rationales for them.

Include a summary line: candidates collected, already known (skipped), newly extracted, after filters, matches per tier.

## Step 8: Save report

Write `.job-scout/reports/[YYYY-MM-DD]-new-jobs.md`: header/stats, profile summary, full ranked list with score breakdowns, filtered-out summary. If today's report exists, append counter.

## Step 9: Update tracker

Merge new jobs into `.job-scout/tracker.json` per the schema in `shared-references/tracker-schema.md`. Update `stats.last_run`. Never overwrite the whole file — read, merge, write.

When the user approves applications, update status to "approved". `/apply` will move it to "applied".

## Step 10: Offer "Top job picks for you" sweep

After saving, **ask the user**: "Done with notifications. Want me to continue and analyze/rank jobs from LinkedIn's 'Top job picks for you' feed at https://www.linkedin.com/jobs/, iterating through pages for any never-before-seen listings?"

If declined, skip to Next Steps.

If accepted:
1. Navigate to `https://www.linkedin.com/jobs/` and locate **"Top job picks for you"**.
2. Collect job IDs from each card. **Filter against `tracker.json` before extracting** (same dedupe rule as Step 3).
3. For each *new* job, extract details and tag source as "Top Picks".
4. Paginate via "Show more" / next page. Stop when (a) a page yields zero new jobs after dedupe, (b) you've covered 5 pages, or (c) the user says stop.
5. Run new jobs through Steps 5–9. Append to today's report under a **"Top Picks Sweep"** section rather than overwriting.
6. Present the new A/B/C matches.

## Next Steps

After presenting results, ask which jobs to apply to (offer `/apply`), whether to refine alerts (`/create-alerts`), or check recruiter messages (`/check-inbox`).

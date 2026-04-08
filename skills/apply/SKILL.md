---
name: apply
description: Apply to approved jobs via LinkedIn Easy Apply
allowed-tools: Read, Bash, Glob
disable-model-invocation: true
---

Apply to user-approved jobs on LinkedIn using Easy Apply.

## Browser policy (read first)

All browser work in this command uses **the Claude Chrome extension exclusively**. Never request computer use. Never install or suggest any other automation framework. See `shared-references/browser-policy.md`. Never enter SSN, bank details, or passwords into any form — hand off to the user.

## Rules

- **ONLY Easy Apply.** For external applications, inform user and open the page for them.
- **NEVER submit without explicit user confirmation.**
- **NEVER enter sensitive data** (SSN, bank details).

## Step 0: Bootstrap workspace

Follow `shared-references/workspace-layout.md` to ensure `.job-scout/` exists.

## Step 1: Confirm Applications

Present approved jobs list (title, company, score, tier, Easy Apply status). Ask user to confirm proceeding. Check `.job-scout/tracker.json` — warn about and skip already-applied or rejected jobs.

## Step 2: Prepare

Ensure user has: up-to-date CV, contact info on LinkedIn, answers for common Easy Apply questions (experience, visa, salary expectations).

## Step 3: Apply

For each approved job: navigate to listing, click Easy Apply, fill each form step (upload CV, basic fields from user-provided info). **Stop and ask** for any question you can't answer confidently. Show final summary and get explicit approval before submitting.

For non-Easy-Apply jobs: inform user, open external page, guide them if requested but let them handle sensitive fields and final submission.

## Step 4: Track and Report

Present summary table (title, company, status, notes). Update `.job-scout/tracker.json` — set status to "applied" with today's date for each successful application.

Suggest checking application status in a few days, running `/check-inbox` for responses.

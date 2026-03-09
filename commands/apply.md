---
description: Apply to approved jobs via LinkedIn Easy Apply
allowed-tools: Read, Bash, Glob
---

Apply to user-approved jobs on LinkedIn using Easy Apply. Only proceed with explicit user approval for each application.

## Important Rules

- **ONLY use Easy Apply.** If a job requires an external application, inform the user and offer to open the external site for them to complete manually, or offer to supervise and assist while they navigate the external site.
- **NEVER submit an application without explicit user confirmation.**
- **NEVER enter sensitive data** (SSN, bank details, etc.) into any form.

## Step 1: Confirm Applications

Present the list of jobs the user has approved for application. For each job, confirm:

- Job title and company
- Match score and tier
- Whether Easy Apply is available

Ask: "Shall I proceed with applying to these [N] jobs via Easy Apply?"

## Step 2: Prepare Application Materials

Check that the user has:

1. **An up-to-date CV** ready to upload (preferably the optimized version from /analyze-cv)
2. **Contact information** filled in on their LinkedIn profile
3. **Any standard answers** for common Easy Apply questions (e.g., years of experience, visa status, salary expectations)

Ask the user for any answers needed for application questions they want pre-filled.

## Step 3: Apply to Each Job

For each approved job:

1. Navigate to the job listing on LinkedIn using the browser
2. Click the "Easy Apply" button
3. Review each step of the application form:
   - Upload the CV if prompted
   - Fill in basic fields (phone, email) only if the user has provided them
   - For screening questions (years of experience, certifications, etc.), answer based on CV data or ask the user
   - **STOP and ask the user** for any question you cannot confidently answer
4. Review the final application summary
5. **Show the user what will be submitted and ask for final confirmation**
6. Click Submit only after user approval

## Step 4: Handle Non-Easy-Apply Jobs

If a job does not have Easy Apply:

1. Inform the user: "This job requires an external application on [company website]. I can open the page for you, or try to assist while you navigate — but external forms vary and may require your direct input."
2. If the user wants assistance, open the external page and guide them through it, but let the user handle sensitive fields and final submission.

## Step 5: Track and Report

After completing all applications, present a summary:

```
| Job Title | Company | Status | Notes |
|-----------|---------|--------|-------|
| Senior Dev | Acme Corp | Applied via Easy Apply | Submitted successfully |
| PM Lead | Beta Inc | Skipped — External application | Link shared with user |
```

Suggest the user:

- Check application status in a few days
- Run /check-inbox to watch for recruiter responses
- Continue searching with /job-search for more opportunities

## Job Tracker Integration

After each successful application:

1. Load `job-reports/tracker.json` (create if missing)
2. Update the job entry's status to `"applied"` and set `applied_date` to today
3. Save the tracker

Before starting applications:

- Check the tracker for any jobs the user has already applied to — warn them and skip duplicates
- If a job's status is `"rejected"`, skip it and inform the user

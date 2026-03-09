---
description: Check LinkedIn notifications for new job alerts, analyze matches against CV and requirements, and report best opportunities
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

Check LinkedIn job alert notifications, analyze each opportunity against the user's CV and requirements, and produce a prioritized report of best matches — saved to file for future `/apply` use.

## Default Requirements (Always Active)

These requirements are baked in and apply to every run unless the user explicitly overrides them:

- **Work arrangement:** Fully remote only
- **Contract type:** Freelance / Contract
- **Salary transparency:** Prioritize listings that disclose salary or day rate. Jobs that do not mention compensation are still scored normally but flagged with "⚠ Does not mention rate"

## Step 1: Locate and Analyze the CV

Search for the user's CV in the workspace. Check for common CV filenames and formats:

1. Search the project workspace folder and attached project files for files matching: `cv.*`, `CV.*`, `resume.*`, `Resume.*`, `curriculum.*` with extensions `.pdf`, `.docx`, `.doc`, `.txt`, `.md`
2. Also check for any file with "cv" or "resume" in the filename (case-insensitive)
3. If multiple candidates are found, ask the user which one to use
4. If **no CV is found**, stop and tell the user:

```
⚠ No CV found in workspace.

To add your CV, either:
  • Drag your CV file into this project's file panel (left sidebar)
  • Or place it in the project workspace folder
  
Supported formats: .pdf, .docx, .txt, .md

Once added, run /check-new-jobs again.
```

Once the CV is loaded:

- Extract all key information: skills, technologies, tools, frameworks, methodologies
- Identify the user's seniority level from experience history
- Determine target role titles and industry from career trajectory
- Note domain expertise and specializations
- Build a **dynamic profile** from the CV content — do NOT rely on hardcoded role titles; let the CV speak for itself
- Store this profile mentally for use throughout the matching process

## Step 2: Navigate to LinkedIn Notifications

Using the browser:

1. Navigate to `https://www.linkedin.com/notifications/`
2. Wait for the page to fully load
3. Scan notifications looking specifically for **job alert** notifications — these contain phrases like:
   - "new opportunities in"
   - "new job alert"
   - "jobs that match your"
   - "job alert:"
4. Identify and collect all job alert notification entries visible on the page
5. Scroll down to load more notifications if needed (at least 2-3 scrolls to catch recent alerts)

## Step 3: Process Job Alert Notifications

For each job alert notification found:

1. Click on the notification to open the alert results
2. For each job listing in the alert:
   - Open the full job description
   - Extract all available information:
     - **Job title**
     - **Company name**
     - **Location** (remote/hybrid/on-site + city/country)
     - **Salary or rate** (if shown — note presence or absence)
     - **Contract type** (freelance, contract, permanent, etc.)
     - **Experience level required**
     - **Required skills and technologies**
     - **Preferred/nice-to-have skills**
     - **Full job description text**
     - **Easy Apply availability**
     - **Posting date**
     - **Number of applicants** (if shown)
     - **Job URL** (copy the LinkedIn job listing URL)
   - Move to the next listing
3. Return to the notifications page and process the next alert
4. Continue until all job alert notifications have been processed

## Step 4: Check Recommended Jobs (Secondary Source)

After exhausting all job alert notifications:

1. Navigate to `https://www.linkedin.com/jobs/`
2. Look for the "Recommended for you" or "Jobs recommended for you" section
3. Scan the top 10-15 recommended jobs
4. For each that looks potentially relevant based on the CV profile built in Step 1:
   - Open and extract the same information as in Step 3
   - Tag these as source: "LinkedIn Recommendation" (vs "Job Alert" from Step 3)

## Step 5: Apply Filters

Before scoring, immediately filter out jobs that violate the default requirements:

1. **Remove non-remote jobs** — Discard any listing that is clearly on-site or hybrid-only with no remote option. If remote status is ambiguous, keep the job but flag it with "⚠ Remote status unclear"
2. **Remove permanent/full-time-only roles** — Discard any listing that is explicitly permanent employment with no freelance or contract option. If contract type is ambiguous, keep the job but flag it with "⚠ Contract type unclear — may be permanent"
3. Jobs that pass filters move to scoring

## Step 6: Score and Rank

Load the **job-matcher** skill. For each remaining job:

Apply the full scoring framework:

- **Skills Match (30%)** — Compare required and preferred skills against the CV profile
- **Experience Alignment (25%)** — Seniority, domain expertise, years of experience
- **Requirements Fit (25%)** — Remote status, contract type, rate alignment
- **Growth & Culture (10%)** — Career progression, tech stack alignment with trajectory
- **Practical Factors (10%)** — Easy Apply, posting freshness, competition level

### Salary Transparency Bonus

After calculating the base score, apply prioritization:

- Jobs that **disclose salary or day rate**: Sort these ABOVE same-tier jobs that don't
- Jobs that **do not disclose compensation**: Score normally but flag with `⚠ Does not mention rate`

### Tier Assignment

- **A-Tier (85-100):** Strong match — apply immediately
- **B-Tier (70-84):** Good match — worth applying
- **C-Tier (55-69):** Partial match — consider if interesting
- **D-Tier (below 55):** Weak match — discard (do not include in report)

## Step 7: Present Results in Conversation

Show the user a clear summary in the conversation:

```
═══════════════════════════════════════════════
  📋 NEW JOBS REPORT — [Today's Date]
  Source: LinkedIn Job Alerts + Recommendations
  Filters: Fully Remote | Freelance/Contract
  Jobs scanned: [N] | After filters: [N] | Matches: [N]
═══════════════════════════════════════════════

🅰️ A-TIER MATCHES (Apply Immediately)
──────────────────────────────────────

1. [Job Title] — [Company]
   💰 [Rate/Salary or "⚠ Does not mention rate"]
   📍 Remote | 📋 [Contract Type] | 📅 Posted [date]
   🎯 Score: [X]/100
   ✅ Key matches: [top 3 matched skills/experience areas]
   ⚠️ Gaps: [any notable gaps]
   🔗 [Job URL]

2. ...

🅱️ B-TIER MATCHES (Worth Applying)
─────────────────────────────────────

3. ...

🅲️ C-TIER MATCHES (Consider)
──────────────────────────────

4. ...

════════════════════════════════════
  SUMMARY
  A-Tier: [N] | B-Tier: [N] | C-Tier: [N]
  Filtered out: [N] (non-remote/permanent)
  Discarded: [N] (D-Tier)
════════════════════════════════════

📝 Full report saved to: [filename]
💡 To apply to any of these, tell me which ones you approve and I'll run /apply
```

For each A-Tier match, also provide a 2-3 sentence explanation of **why** it's a strong match based on the CV analysis.

## Step 8: Save Report to File

Save a detailed markdown report to the workspace as `job-reports/[YYYY-MM-DD]-new-jobs.md`:

The saved report should include:

1. **Header** with date, filter summary, and scan statistics
2. **CV Profile Summary** — Brief summary of what was extracted from the CV (target roles, key skills, seniority)
3. **Full ranked job list** with all extracted details per job:
   - Job title, company, location, rate/salary, contract type
   - Full match score breakdown by dimension
   - Matched skills vs gaps
   - Red flags (if any)
   - Job URL (clickable)
   - Source (Job Alert vs Recommendation)
4. **Filtered-out jobs** — Brief list of jobs that were removed by filters and why
5. **Recommendations** — Suggested next steps

If the `job-reports/` directory doesn't exist, create it.

If a report for today's date already exists, append a counter: `[YYYY-MM-DD]-new-jobs-2.md`

## Step 9: Recommend Next Steps

After presenting the report, ask the user:

1. **Which jobs would you like to apply to?** — "Tell me the numbers and I'll run /apply for each"
2. **Want to refine your alerts?** — If results were poor, suggest running /create-alerts with better criteria
3. **Want to check recruiter messages too?** — Suggest /check-inbox
4. **Want a deeper analysis on any specific listing?** — Offer to provide detailed match cards

## Error Handling

- If LinkedIn is not logged in, inform the user and stop
- If no job alert notifications are found, inform the user and proceed directly to Step 4 (recommended jobs)
- If no jobs at all match the filters, tell the user and suggest broadening search criteria
- If browser automation encounters issues on a specific listing, skip it and note in the report

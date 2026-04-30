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

Follow `shared-references/workspace-layout.md` to ensure `.job-scout/` exists in the current workspace. All paths below are inside `.job-scout/`. Then follow `shared-references/render-orchestration.md` Step G (lifecycle cleanup) to archive expired report files and prune old archives — cheap directory scan; runs at the start of every Tier 1 command.

## Step 0a: Daily-driver context line

Read `.job-scout/tracker.json`. Compute and display a one-line situational summary as the first user-visible output:

**If `tracker.stats.last_run` is set (prior runs exist):**

```
📊 Last run [N] days ago. Tracker: [seen] seen, [A-tier] A-tier, [applied] applied.
   New since last run: [M] alerts.
```

Where:
- `[N]` = days between today and `tracker.stats.last_run`.
- `[seen]` = count of tracker entries with `status: "seen"`.
- `[A-tier]` = count of tracker entries with `tier: "A"`.
- `[applied]` = `tracker.stats.applied`.
- `[M]` = best-effort count of new alerts on the notifications page since `last_run`. If this can't be computed cheaply at this point, omit the second line.

**If `tracker.stats.last_run` is null (first run):**

```
🚀 First run. Setting up tracker.
```

This step is read-only. Cost is one tracker.json read plus one timestamp diff. No browser interaction.

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

**Corpus enrichment:** after extraction, run the JD keyword extraction procedure from `../shared-references/jd-keyword-extraction.md` on each new job's description. Merges keywords into `.job-scout/cache/jd-keyword-corpus.json`.

## Step 5: Filter

Drop jobs that violate default requirements:
- Non-remote (on-site/hybrid only) — discard. If ambiguous, keep and flag "Remote status unclear".
- Permanent-only with no contract option — discard. If ambiguous, keep and flag "Contract type unclear".

## Step 6: Score and rank (parallel)

Apply the _job-matcher scoring framework with freelance adjustments if applicable. Jobs that disclose compensation sort above same-tier jobs that don't.

**Scoring fan-out:** batch the new jobs into groups of 5 and dispatch one subagent per batch per the contract in `../shared-references/subagent-protocol.md`:

```json
{
  "task": "score-job-batch",
  "inputs": {
    "jobs": [ /* extracted job blobs */ ],
    "user_profile": { "cv_summary": "...", "requirements": "...", "master_keyword_list": "..." },
    "cv_hash": "...",
    "profile_hash": "..."
  },
  "budget_lines": 200,
  "allowed_tools": ["Read"]
}
```

Each subagent loads the `_job-matcher` skill, returns `deltas: [{ job_id, score, tier, breakdown }, ...]`. Main thread merges all deltas into `.job-scout/cache/scores.json` keyed by `(job_id, cv_hash, profile_hash)`.

Tiers: **A (85-100)** apply immediately, **B (70-84)** worth applying, **C (55-69)** consider, **D (<55)** discard.

**Fallback:** if the `Agent` tool is unavailable in this session, fall back to sequential in-thread scoring. Log the fallback.

## Step 6b: Reverse-Boolean discoverability check (A-tier only)

For each job scoring A-tier (85-100):
1. Extract from the JD: role title, top 3 required skills, location preference.
2. Construct the likely recruiter Boolean query using templates from `../_profile-optimizer/references/recruiter-search-patterns.md`: `"<role>" AND ("<skill1>" OR "<skill2>") AND "<skill3>"`.
3. Load the user's cached LinkedIn profile from `.job-scout/cache/linkedin-profile.json`. Check for each Boolean term in: headline, current job title, skills list, about section, experience descriptions.
4. Classify: **Match** or **Miss** with specific missing keywords.
5. Append to the A-tier match card in the report (same format as match-jobs Step 4b).

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
2. Load `tracker.json` once and snapshot into memory — every subagent receives this snapshot.
3. For pages 1..5 (or until a stop condition fires): dispatch one subagent per page, each with `subagent_type: "general-purpose"` per `../shared-references/subagent-protocol.md`:

   ```json
   {
     "task": "top-picks-page",
     "inputs": {
       "page_number": 1,
       "tracker_snapshot_ids": ["..."],
       "source": "Top Picks"
     },
     "budget_lines": 200,
     "allowed_tools": ["Read"]
   }
   ```

   The subagent receives the page URL pattern in its prompt and extracts job blobs for any id not in `tracker_snapshot_ids`. It returns:

   ```json
   {
     "status": "ok",
     "deltas": [
       { "job_id": "...", "title": "...", "company": "...", "raw_blob": "...", "source": "Top Picks" }
     ]
   }
   ```

   Note: page-fetching in Phase 1 still happens via the main thread's Chrome extension (subagents do not have browser access). The main thread fetches the raw HTML or listing JSON for each page, then dispatches the subagent with that data in `inputs`. Subagents dedupe and parse only.

4. Collect all subagent deltas. Dedupe again against the live tracker (in case concurrent runs updated it).
5. Stop early if: any page's subagent returns zero new jobs, the user says stop, or the 5-page cap is hit.
6. Hand the collected new-job blobs to Step 6's scoring fan-out. Append to today's report under a **"Top Picks Sweep"** section rather than overwriting.
7. Present the new A/B/C matches.

**Fallback:** if the `Agent` tool is unavailable, fall back to the sequential in-thread loop (fetch → dedupe → extract → score) page by page.

## Step 11: Build results payload

Construct a `data` payload for the render layer. Tier classification uses the canonical `_job-matcher` thresholds: `score >= 85` → `"a"`, `70 <= score < 85` → `"b"`, `55 <= score < 70` → `"c"`. Notifications with `score < 55` are D-tier and must be pre-filtered before reaching the renderer. View-specific fields:

- `title`: "Today's notifications".
- `subtitle`: "{{N}} new · {{unread}} unread · A:{{a}} B:{{b}}".
- `filename`: "check-job-notifications-latest.html".
- `unread_count`: integer count of `seen: false` items.
- `results[]`: each item is `{ id, title, company, received_at, source, score, tier, seen, preview, url }`. The `preview` is the first 140 chars of the notification body. The `url` is an absolute LinkedIn job URL captured during extraction — optional: when present, the templates render a "View posting ↗" link in HTML and a clickable title in markdown; when omitted, the templates fall back to plain title text via `{% if note.url %}` guards.

## Step 12: Render

Follow `../shared-references/render-orchestration.md` end-to-end (Step G already ran in Step 0):

1. Step A — payload built in Step 11 above.
2. Steps B–F — read render config, dispatch `_visualizer`, open in Chrome (or fall back), handle errors.
3. Step E — print the summary line:

```
✓ {{N}} notifications — {{unread}} unread — opened report in Chrome
```

Fall back to pre-v0.7.0 markdown table if `Agent` tool is unavailable.

## Next Steps

After presenting results, ask which jobs to apply to (offer `/apply`), whether to refine alerts (`/create-alerts`), or check recruiter messages (`/check-inbox`).

---
name: check-job-notifications
description: Check LinkedIn notifications for new job alerts, analyse matches against CV and requirements, and report best opportunities
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
disable-model-invocation: true
---

Check LinkedIn job alert notifications, analyse each opportunity against the user's CV and requirements, and produce a prioritised report of the best matches — saved for future `/apply` use.

All filtering comes from the user's declared `requirements` and `deal_breakers[]` (set at `/analyze-cv` discovery) and is enforced uniformly by `_gate-engine`. This command carries no built-in defaults of its own.

## Browser policy (read first)

All browser work in this command uses **the Claude Chrome extension exclusively**. Never request computer use. Never suggest Playwright, Selenium, or any other automation framework. See `shared-references/browser-policy.md` for the full policy. If the Chrome extension is not available in the current session, stop and report it — do not escalate to any other mechanism.

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

Follow `shared-references/cv-loading.md`. If no profile exists, the user should be redirected to `/analyze-cv` for the full discovery interview (segment declaration, dealbreakers, voice, dimensions). This command must not fabricate defaults — `_gate-engine` and `_job-matcher` need user-declared `requirements` and `segment` to function correctly.

## Step 2: Collect candidate job IDs (NO extraction yet)

Navigate to `https://www.linkedin.com/notifications/?filter=jobs_all`. Scroll 2-3 times to load recent alerts.

Identify **every unread job alert notification** (highlighted in blue). Do NOT stop after the first one.

For each unread alert: open the alert and collect the **job IDs and URLs** of every individual listing inside it. Tag source as `"Job Alert"`. Do not extract full details yet.

## Step 2b: Sweep Top picks (v0.9.0+)

After notifications, navigate to `https://www.linkedin.com/jobs/collections/recommended/`. Scroll 1-2 times to load the first page of recommendations. Collect all visible job IDs and URLs. Tag source as `"Top Picks"`. Do not extract full details yet.

## Step 2c: Sweep Saved jobs (v0.9.0+)

Navigate to `https://www.linkedin.com/my-items/saved-jobs/`. Scroll until all saved entries are loaded (saved-jobs list is typically small — under 50). Collect all job IDs and URLs. Tag source as `"Saved"`. Do not extract full details yet.

## Step 3: Dedupe against tracker FIRST

Combine the candidate ID lists from Steps 2 (Job Alerts), 2b (Top Picks), and 2c (Saved). Each ID carries the source that surfaced it; if the same ID appears from multiple sources, preserve the source priority `Job Alert > Top Picks > Saved`.

Load `.job-scout/tracker.json` (see `shared-references/tracker-schema.md`). For each candidate job ID:

- **Already in tracker** (seen / approved / applied / rejected) → bump `last_seen`, do NOT re-extract, do NOT re-score. Skip.
- **New ID** → check the **repost fingerprint** per `../shared-references/linkedin-search.md` §5: `lower(company)|lower(title)|lower(location)` against non-rejected tracker entries (company/title/location are visible on the listing card — no extraction needed). On a match, treat as a repost: bump the existing entry's `last_seen`, append `repost id: <new_id> (<date>)` to its notes, and drop the candidate.
- **Genuinely new** → keep in the to-process list with the assigned source.

This is the primary token-saving step. Never extract a job you already know — across all three surfaces, by ID or by fingerprint.

## Step 4: Extract details for new jobs only

For each *new* job: open it and extract title, company, location (remote/hybrid/on-site + city), salary/rate, contract type, experience level, required skills, preferred skills, full description text, Easy Apply status, posting date, applicant count, job URL.

**JD persistence (required).** Immediately after extracting a job's full description text, persist it via the hybrid-storage contract in `../shared-references/jd-storage.md`:

```bash
mkdir -p .job-scout/jds
printf '%s\n' "$JD_TEXT" > ".job-scout/jds/$JOB_ID.txt.tmp"
mv ".job-scout/jds/$JOB_ID.txt.tmp" ".job-scout/jds/$JOB_ID.txt"
```

Set `jd_path: "jds/<job_id>.txt"` and `source` (one of `Job Alert | Top Picks | Saved`) on the tracker entry in the same atomic write. Skills that need the full JD downstream (`/cover-letter`, `/interview-prep`, `_job-matcher` evidence-quote extraction) read it from this path. The inline `description` field is removed from the canonical v2 tracker schema — do not write it.

**Corpus enrichment:** after extraction, run the JD keyword extraction procedure from `../shared-references/jd-keyword-extraction.md` on each new job's description. Merges keywords into `.job-scout/cache/jd-keyword-corpus.json`.

## Step 5: Gate + score new jobs (v0.8.0+)

Load `_job-matcher` (which transitively loads `_gate-engine`). For every newly extracted job from Step 4:

1. **`_gate-engine` runs first.** It evaluates the job against `user-profile.requirements` (work_arrangement, contract_type, seniority_floor, location, industries_to_avoid, companies_to_avoid, rate/salary floors, and the declared `deal_breakers[]`). If `gate_violations` is non-empty → set `tier: D`, `tier_reason: "gated: <kinds>"`, persist `gate_violations`, skip dimension scoring.
2. **If not gated** → the segment-aware rubric (per `user-profile.segment`) produces per-dimension tiers + evidence quotes. Persist `tier`, `dimensions`, `tier_reason`, `rubric_version: "v1"` to the tracker entry and the score cache.

Daily-driver display: top section shows A-tier with full dimension breakdown; B-tier with one-line dimension highlights; C/D summary counts collapsed. Gated jobs go to a collapsed "Filtered out" group below, each with a one-line "Gated: <kinds>" banner.

The default-requirements filter from previous versions is removed; the same conditions are now expressed as user-declared `deal_breakers[]` (set at `/analyze-cv` discovery) and enforced uniformly via `_gate-engine`.

## Step 5b: Similar-jobs expansion from A-tier hits (v0.9.0+)

After Step 5 scoring completes, iterate every job in this run that came out at `tier: "A"` (not gated). For each A-tier survivor:

1. The agent is already on (or can return to) that job's listing page. Scroll to the "Similar jobs" rail (LinkedIn typically shows 4-6 below the JD body).
2. Collect the IDs and URLs from that rail.
3. Filter against `tracker.json` to drop known IDs.
4. For each new ID, open the listing and run the full extract → JD persist → `_gate-engine` → score chain. Tag `source: "Similar"`. Also tag `notes` with `"expanded from: <seed_job_id>"` so the lineage is traceable.

Cap: at most 5 new similar-jobs per A-tier seed (LinkedIn's rail length). If a workspace's daily run produces 0 A-tier survivors, this step is a no-op.

The expansion fires gates the same way as primary jobs — a similar-job from a real A-tier hit can still be gated and end up in "Filtered out".

## Step 6: Parallel scoring fan-out

When Step 5 has more than ~5 new jobs to score, batch them into groups of 5 (the last batch may be smaller) and dispatch one subagent per batch per the contract in `../shared-references/subagent-protocol.md`:

```json
{
  "task": "score-job-batch",
  "inputs": {
    "jobs": [ /* extracted job blobs */ ],
    "user_profile": { "segment": "...", "cv_summary": "...", "requirements": "...", "dimensions": [], "master_keyword_list": "..." },
    "cv_hash": "...",
    "profile_hash": "...",
    "rubric_version": "v1"
  },
  "budget_lines": 200,
  "allowed_tools": ["Read"]
}
```

Each subagent loads `_job-matcher` (which loads `_gate-engine` first) and returns v1 deltas:

```json
{
  "status": "ok",
  "deltas": [
    { "job_id": "...", "tier": "A", "tier_reason": null,
      "dimensions": { "<dim_name>": {"tier": "A", "evidence": ["…"]} },
      "gate_violations": [],
      "rubric_version": "v1" }
  ]
}
```

The main thread merges all deltas into `.job-scout/cache/scores.json` keyed by `(job_id, cv_hash, profile_hash, rubric_version)` and persists each result to the tracker entry.

**Ordering preference:** within the same tier, jobs that disclose compensation sort above those that don't (flag the latter "Does not mention rate"); then by `posted_at` descending, with the freshness flag per `../shared-references/linkedin-search.md` §6.

**Fallback:** if the `Agent` tool is unavailable in this session, fall back to sequential in-thread scoring. Log the fallback.

## Step 6b: Reverse-Boolean discoverability check (A-tier only)

For each job the rubric tiers at A:
1. Extract from the JD: role title, top 3 required skills, location preference.
2. Construct the likely recruiter Boolean query using templates from `../_profile-optimizer/references/recruiter-search-patterns.md`: `"<role>" AND ("<skill1>" OR "<skill2>") AND "<skill3>"`.
3. Load the user's cached LinkedIn profile from `.job-scout/cache/linkedin-profile.json`. Check for each Boolean term in: headline, current job title, skills list, about section, experience descriptions.
4. Classify: **Match** or **Miss** with specific missing keywords.
5. Append to the A-tier match card in the report (same format as match-jobs Step 4b).

## Step 7: Present results

Markdown summary grouped by tier (A, B, C — gated jobs in a collapsed "Filtered out" group). Per job: title, company, rate (or "Does not mention rate"), location, contract type, posting date, tier, top 3 skill matches, notable gaps, job URL. A-tier gets the full dimension breakdown with evidence quotes. B-tier gets one line per dimension. C-tier gets a compact one-line table — no paragraph rationales.

Include a summary line: candidates collected, already known (skipped), newly extracted, after filters, matches per tier.

## Step 8: Save report

Write `.job-scout/reports/[YYYY-MM-DD]-new-jobs.md`: header/stats, profile summary, full ranked list with score breakdowns, filtered-out summary. If today's report exists, append counter.

## Step 9: Update tracker

Merge new jobs into `.job-scout/tracker.json` per the schema in `shared-references/tracker-schema.md`. Update `stats.last_run`. Never overwrite the whole file — read, merge, write.

When the user approves applications, update status to "approved". `/apply` will move it to "applied".

## Step 10: Offer "Top job picks for you" sweep

After saving, **ask the user**: "Done with notifications. Want me to continue and analyse/rank jobs from LinkedIn's 'Top job picks for you' feed at https://www.linkedin.com/jobs/, iterating through pages for any never-before-seen listings?"

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

Construct a `data` payload for the render layer. Tiers come straight from the `_job-matcher` v1 rubric — uppercase `A | B | C | D`, no aggregate score. Gated (D-tier) jobs appear only in the collapsed "Filtered out" group. View-specific fields:

- `title`: "Today's notifications".
- `subtitle`: "{{N}} new · {{unread}} unread · A:{{a}} B:{{b}} C:{{c}} · Filtered:{{gated}}".
- `filename`: "check-job-notifications-latest.html".
- `unread_count`: integer count of `seen: false` items.
- `tier_counts`: `{ a, b, c, d, total }`.
- `results[]`: each item is `{ id, title, company, location, received_at, posted_at, source, tier, tier_reason, dimensions, gate_violations, fresh, seen, preview, url }`. `dimensions` is the per-dimension `{tier, evidence[]}` map from the rubric. `fresh` per `../shared-references/linkedin-search.md` §6. The `preview` is the first 140 chars of the notification body. The `url` is an absolute LinkedIn job URL captured during extraction — optional: when present, the templates render a "View posting ↗" link in HTML and a clickable title in markdown; when omitted, the templates fall back to plain title text via `{% if note.url %}` guards.

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

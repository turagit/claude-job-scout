---
name: match-jobs
description: Score and rank job listings against your CV and requirements
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
disable-model-invocation: true
---

Analyze LinkedIn job listings and rank them against the user's CV and requirements.

## Browser policy (read first)

All browser work in this command uses **the Claude Chrome extension exclusively**. Never request computer use. See `shared-references/browser-policy.md`.

## Step 0: Bootstrap workspace

Follow `shared-references/workspace-layout.md` to ensure `.job-scout/` exists.

## Step 1: Identify Source

Ask the user where to find jobs: job alerts (LinkedIn notifications), saved jobs, specific URL, or current search results.

## Step 2: Load Profile

Follow `shared-references/cv-loading.md`. Load the **job-matcher** skill.

## Step 3: Collect IDs and dedupe FIRST

Navigate to the source page. Collect job IDs/URLs for every visible listing. Load `.job-scout/tracker.json` (see `shared-references/tracker-schema.md`). Drop any ID already in the tracker — bump `last_seen`, do not re-extract.

Also check `.job-scout/cache/scores.json` for cached `(job_id, cv_hash, profile_hash)` scores. Reuse cached scores; don't re-score unchanged jobs against an unchanged CV and profile.

## Step 4: Extract and score new jobs (parallel)

For each *new* job, extract title, company, location, salary, experience level, required/preferred skills, description, Easy Apply status, posting date, applicant count.

**Corpus enrichment:** after extraction, run the JD keyword extraction procedure from `../shared-references/jd-keyword-extraction.md` on each new job's description text. This merges discovered keywords into `.job-scout/cache/jd-keyword-corpus.json` — building the user's market-specific keyword model over time. No additional LLM call; extraction piggybacks on the JD text already in context.

**Scoring fan-out:** batch the new jobs into groups of 5 (the last batch may be smaller). For each batch, dispatch one subagent per the contract in `../shared-references/subagent-protocol.md`:

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

The subagent loads the `job-matcher` skill, scores each job, returns deltas:

```json
{
  "status": "ok",
  "deltas": [
    { "job_id": "...", "score": 87, "tier": "A", "breakdown": { /* per-dimension */ } }
  ]
}
```

Main thread collects all deltas, filters out D-Tier, and writes each score into `.job-scout/cache/scores.json` under the `(job_id, cv_hash, profile_hash)` key.

**Fallback:** if the `Agent` tool is unavailable in this session, fall back to sequential in-thread scoring using the same job-matcher framework. Log the fallback.

## Step 5: Present Results

Show ranked markdown table (title, company, score, tier, Easy Apply, posted, applicants). For A-Tier and top B-Tier, provide detailed match cards with score breakdown, matched skills, gaps, and red flags. Keep B/C tiers as compact rows — no paragraph rationales.

Merge newly scored jobs into `.job-scout/tracker.json` with status "seen".

## Next Steps

Ask which jobs to apply to (`/apply`), save, or discard. Suggest refining search if results are poor.

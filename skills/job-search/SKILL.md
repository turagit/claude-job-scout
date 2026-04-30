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

Follow `shared-references/workspace-layout.md` to ensure `.job-scout/` exists. Then follow `shared-references/render-orchestration.md` Step G (lifecycle cleanup) to archive expired report files and prune old archives — cheap directory scan; runs at the start of every Tier 1 command.

## Step 1: Load Profile, CV & Requirements

Follow `shared-references/cv-loading.md`. If argument provided ($1), use as primary search title. For any missing requirement fields, ask: target roles, location, salary range, seniority, company preferences, deal-breakers, nice-to-haves. Save new info back to `.job-scout/user-profile.json` (merge, don't overwrite).

## Step 3: Search LinkedIn

Navigate to `https://www.linkedin.com/jobs/`. Enter target title, set location and filters (Experience Level, Remote, Date Posted — prioritize "Past Week"). Collect job IDs first and dedupe against `.job-scout/tracker.json` (see `shared-references/tracker-schema.md`) before opening any listing. Only extract details for new jobs: title, company, location, salary, requirements, description, Easy Apply status.

**Corpus enrichment:** after extraction, run the JD keyword extraction procedure from `../shared-references/jd-keyword-extraction.md` on each new job's description. Merges keywords into `.job-scout/cache/jd-keyword-corpus.json`.

## Step 4: Score and Present

Load the **_job-matcher** skill. Score each listing, assign tiers. Present ranked markdown table (title, company, score, tier, Easy Apply, key match, key gap). For A-Tier and top B-Tier, provide detailed analysis with score breakdown and matched skills vs gaps.

Perform multiple searches if user has several target roles. If profile is >30 days old, suggest `/analyze-cv`.

## Step 5: Build results payload

Construct a `data` payload for the render layer. Tier classification uses the canonical `_job-matcher` thresholds: `score >= 85` → `"a"`, `70 <= score < 85` → `"b"`, `55 <= score < 70` → `"c"`. Jobs with `score < 55` are D-tier and must be pre-filtered before reaching the renderer.

```json
{
  "title": "Search results for `<query>`",
  "subtitle": "{{N}} surfaced · A:{{a}} B:{{b}} C:{{c}}",
  "generated_at": "<YYYY-MM-DD HH:MM>",
  "filename": "job-search-latest.html",
  "query": "<the original Boolean / keyword query string>",
  "tier_counts": { "a": <a_count>, "b": <b_count>, "c": <c_count>, "total": <total> },
  "results": [
    {
      "title": "<job title>",
      "company": "<company>",
      "location": "<location>",
      "salary": "<salary or empty string>",
      "posted_at": "<YYYY-MM-DD>",
      "applicants": "<applicant count or empty string>",
      "score": <integer>,
      "tier": "a | b | c",
      "url": "<absolute job URL on LinkedIn — optional; include when known>",
      "tags": ["<tag1>", "<tag2>"]
    }
  ]
}
```

Same shape as `match-jobs.results[]`, plus `applicants` when known. `tags` are drawn from matched skills/signals computed during scoring; limit to 5 per job.

The `url` is an absolute LinkedIn job URL captured during job extraction. It is optional: when present, the templates render a "View posting ↗" link in HTML and a clickable title in markdown; when omitted, the templates fall back to plain title text via `{% if job.url %}` guards.

Merge newly scored jobs into `.job-scout/tracker.json` with status "seen".

## Step 6: Render

Follow `../shared-references/render-orchestration.md` end-to-end (Step G already ran in Step 0):

1. Step A — payload built in Step 5 above.
2. Steps B–F — read render config, dispatch `_visualizer`, open in Chrome (or fall back), handle errors.
3. Step E — print the `job-search` summary line: `✓ {{N}} jobs surfaced — A:{{a}} B:{{b}} — opened report in Chrome` (or `…rendered as markdown above` when falling back).

If the `Agent` tool is unavailable, fall back to the pre-v0.7.0 markdown-table output.

## Next Steps

Suggest `/create-alerts` for monitoring, `/apply` for approved jobs, or refining search terms.

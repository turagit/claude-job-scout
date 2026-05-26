---
name: job-search
description: Search LinkedIn for jobs matching your CV and requirements
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: [optional: job-title — omit to fanout across all target_titles]
disable-model-invocation: true
---

Run a LinkedIn job search against the user's CV and requirements. Behaviour depends on the argument shape:

- **Zero-arg (`/job-search`)** — **adaptive multi-query fanout**. Iterates `user-profile.target_titles[]`, running each as its own query. For any title that yields fewer than 5 surfaced jobs after dedupe, agent LLM-generates 2-3 synonym variants and refires. All queries dedupe through `tracker.json`. Aim: discover the breadth of relevant openings without manual per-title invocation.
- **Single-arg (`/job-search <title>`)** — single query. Same as before — searches LinkedIn jobs for that exact title, no fanout, no synonym expansion.

## Browser policy (read first)

All browser work in this command uses **the Claude Chrome extension exclusively**. Never request computer use. See `shared-references/browser-policy.md`.

## Step 0: Bootstrap workspace

Follow `shared-references/workspace-layout.md` to ensure `.job-scout/` exists. Then follow `shared-references/render-orchestration.md` Step G (lifecycle cleanup) to archive expired report files and prune old archives — cheap directory scan; runs at the start of every Tier 1 command.

## Step 1: Load Profile, CV & Requirements

Follow `shared-references/cv-loading.md`. Read `user-profile.json` for `target_titles[]`, `segment`, `requirements`, `cv_summary`. If `target_titles` is empty, fall through to `cv_summary.target_roles` (legacy compat). If both are empty AND no argument is provided, ask the user to either pass a title arg or run `/analyze-cv` first.

If profile is >30 days old, suggest `/analyze-cv` and ask whether to proceed anyway.

## Step 2: Build the query plan

### Zero-arg invocation (multi-query fanout)

The query plan starts as one entry per `target_titles[]` element (or `cv_summary.target_roles` fallback). Each entry: `{ title: "<exact target>", source: "primary" }`.

### Single-arg invocation

The query plan is a single entry: `{ title: $1, source: "explicit" }`.

## Step 3: Search LinkedIn (per query in the plan)

For each query in the plan:

1. Navigate to `https://www.linkedin.com/jobs/`. Enter the query's title. Set location and filters from `requirements` (`location_preferences`, `work_arrangement`, `contract_type`, `seniority`). Date Posted: prioritise "Past Week".
2. Collect job IDs from the results page (scroll 1-2 times to load tail; do NOT page beyond page 1 for `/job-search` — `/deep-sweep` is for multi-page coverage).
3. Dedupe against `.job-scout/tracker.json` (see `shared-references/tracker-schema.md`). Drop any known ID; bump its `last_seen`.
4. **Adaptive synonym check:** count surfaced (post-dedupe NEW) IDs for this query. If `count < 5` AND the query came from `target_titles[]` (primary source, not explicit user input), proceed to Step 3b. Otherwise continue to Step 3c with the IDs in hand.

### Step 3b: Synonym expansion (adaptive only)

When a primary query yields fewer than 5 new IDs, generate variants:

```
Generate 2-3 synonym or adjacent-title variants for this LinkedIn job search.
The candidate's profile is:
- segment: {{user-profile.segment}}
- target_titles: {{user-profile.target_titles}}
- key_skills: {{user-profile.cv_summary.key_skills}}

The variant queries must be different enough to surface new postings, but close
enough to still match the candidate's profile. Vary by: seniority synonym (Lead↔Principal↔Senior),
function synonym (Platform↔Infrastructure↔SRE), or scope synonym (Engineer↔Architect↔Specialist).

Original query: "{{thin_title}}"

Return strict JSON: ["variant1", "variant2", "variant3"]
```

Append each variant as a NEW query plan entry with `source: "synonym"`, then return to Step 3 for that entry. Cap: at most 3 synonyms per primary title; do not synonym-expand a synonym.

### Step 3c: Extract details for new jobs

Open and extract: title, company, location, salary, requirements, full description text, Easy Apply status, posting date, applicant count, job URL.

**JD persistence (required).** Immediately after extracting a job's full description text, persist it per the hybrid-storage contract in `../shared-references/jd-storage.md` — write to `.job-scout/jds/<job_id>.txt`, set `jd_path` on the tracker entry. Skip inline `description` writes; the field is removed from the canonical v2 schema. Set `source: "Search"` on the tracker entry.

**Corpus enrichment:** after extraction, run the JD keyword extraction procedure from `../shared-references/jd-keyword-extraction.md` on each new job's description. Merges keywords into `.job-scout/cache/jd-keyword-corpus.json`.

## Step 4: Gate + score (v0.8.0+)

Load `_job-matcher` (which transitively loads `_gate-engine`). For each new job from this run:

1. `_gate-engine` runs first. If `gate_violations` is non-empty → set `tier: D`, `tier_reason: "gated: <kinds>"`, persist, skip dimension scoring.
2. Otherwise run the rubric. Matcher loads `user-profile.json.dimensions[]` if present, falls back to `../_job-matcher/references/dimensions-default.md`. Persist `tier`, `dimensions`, `tier_reason`, `rubric_version: "v1"`.

Across the entire fanout (all query plan entries), accumulate results into one combined set for the report. Display: A-tier first (full dimension breakdown), then B-tier (one-line per dimension), then C/D summary counts. Gated jobs go to a collapsed "Filtered out" group.

## Step 5: Build results payload

Construct a `data` payload for the render layer. Tier classification uses the canonical `_job-matcher` thresholds: `score >= 85` → `"a"`, `70 <= score < 85` → `"b"`, `55 <= score < 70` → `"c"`. Jobs with `score < 55` are D-tier and must be pre-filtered before reaching the renderer.

```json
{
  "title": "Search results — {{N_queries}} queries · {{N_results}} surfaced",
  "subtitle": "{{N_primary}} primary + {{N_synonym}} synonym · A:{{a}} B:{{b}} C:{{c}} · Filtered:{{gated}}",
  "generated_at": "<YYYY-MM-DD HH:MM>",
  "filename": "job-search-latest.html",
  "queries": ["<title1>", "<title2 (synonym of title1)>"],
  "tier_counts": { "a": <a_count>, "b": <b_count>, "c": <c_count>, "total": <total> },
  "results": [
    {
      "title": "<job title>",
      "company": "<company>",
      "location": "<location>",
      "salary": "<salary or empty string>",
      "posted_at": "<YYYY-MM-DD>",
      "applicants": "<applicant count or empty string>",
      "tier": "A | B | C | D",
      "tier_reason": "string|null",
      "dimensions": { "<dim_name>": {"tier": "A|B|C|D", "evidence": ["...", "..."]} },
      "gate_violations": [{"kind": "...", "detail": "..."}],
      "rubric_version": "v1",
      "source": "Search",
      "matched_query": "<which query in the plan surfaced this job>",
      "url": "<absolute job URL on LinkedIn — optional>",
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
3. Step E — print the `job-search` summary line: `✓ {{N_queries}} queries (incl. {{N_synonym}} synonym) — {{N_results}} surfaced — A:{{a}} B:{{b}} · Filtered:{{gated}} — opened report in Chrome` (or `…rendered as markdown above` when falling back).

If the `Agent` tool is unavailable, fall back to the pre-v0.7.0 markdown-table output.

## Next Steps

Suggest `/create-alerts` for monitoring, `/apply` for approved jobs, or refining search terms.

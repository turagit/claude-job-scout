---
name: job-search
description: Search LinkedIn for jobs matching your CV and requirements
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: [optional: job-title — omit to run the full query plan]
disable-model-invocation: true
version: 0.2.0
---

Run a LinkedIn job search against the user's CV and requirements. All searches follow the query grammar in `../shared-references/linkedin-search.md` — filter-addressed URLs, Boolean keyword queries, the learning loop, repost dedupe. Behaviour depends on the argument shape:

- **Zero-arg (`/job-search`)** — **full query plan v2**: Boolean title-cluster queries, skill-combination queries (when the keyword corpus is ripe), geo iteration across declared markets, and adaptive synonym rescue for thin queries. All queries dedupe through `tracker.json` by ID and by repost fingerprint. Aim: discover the breadth of relevant openings — including roles whose titles don't match `target_titles[]` — without manual per-title invocation.
- **Single-arg (`/job-search <title>`)** — single query, `family: "explicit"`. The title may itself be a Boolean expression; pass it through verbatim (encoded), with filters still URL-addressed from `requirements`.

## Browser policy (read first)

All browser work in this command uses **the Claude Chrome extension exclusively**. Never request computer use. See `../shared-references/browser-policy.md`.

## Step 0: Bootstrap workspace

Follow `../shared-references/workspace-layout.md` to ensure `.job-scout/` exists. Then follow `../shared-references/render-orchestration.md` Step G (lifecycle cleanup) to archive expired report files and prune old archives — cheap directory scan; runs at the start of every Tier 1 command.

## Step 1: Load profile, CV & requirements

Follow `../shared-references/cv-loading.md`. Read `user-profile.json` for `target_titles[]`, `query_clusters[]`, `segment`, `requirements`, `cv_summary`. If `target_titles` is empty, fall through to `cv_summary.target_roles` (legacy compatibility). If both are empty AND no argument is provided, ask the user to either pass a title argument or run `/analyze-cv` first.

If the profile is more than 30 days old, suggest `/analyze-cv` and ask whether to proceed anyway.

## Step 2: Build the query plan

Follow `../shared-references/linkedin-search.md` §3.

### Zero-arg invocation

1. **Title queries:** one Boolean query per `query_clusters[]` entry — `("Title A" OR "Title B") NOT (term1 OR term2)`. If `query_clusters[]` is absent, one plain query per `target_titles[]` entry.
2. **Skill queries:** if `.job-scout/cache/jd-keyword-corpus.json` has ≥10 source jobs, add 2–3 skill-pair queries per §3b (top co-occurring A/B-tier skills ∩ `cv_summary.key_skills`, with a context anchor).
3. **Geo iteration:** each query runs once per market in `requirements.location_preferences[]` (a single "worldwide remote" preference is one pass with `f_WT=2`).
4. **Ordering:** load `.job-scout/cache/query-stats.json` (treat missing as empty) and order per §3e — proven queries first, retired queries excluded, cold-start entries last.

### Single-arg invocation

One entry: `{ query: $1, family: "explicit" }`, in each declared market.

## Step 3: Run each query in the plan

For each entry:

1. **Construct the URL** per `linkedin-search.md` §1: `keywords` (URL-encoded Boolean query), `location`, `f_WT` from `work_arrangement`, `f_JT` from `contract_type`, `f_TPR=r604800` (Past Week), `sortBy=DD`. Never set `f_AL` unless the user explicitly asked for Easy Apply only. Navigate straight to it. On the first query of the run, glance at the active filter chips to confirm the parameters took; if one was ignored, set that filter via the UI for the rest of the run and note the drift in the summary.
2. Collect job IDs from the results page (scroll 1–2 times to load the tail; do NOT page beyond page 1 — `/deep-sweep` is the multi-page surface).
3. **Dedupe by ID** against `.job-scout/tracker.json` (see `../shared-references/canonical-schemas.md`). Drop known IDs; bump their `last_seen`.
4. **Dedupe by repost fingerprint** per `linkedin-search.md` §5 — `company|title|location` against non-rejected tracker entries. Matches are reposts: bump `last_seen`, append `repost id: <new_id> (<date>)` to the existing entry's notes, drop the candidate.
5. **Record query stats** per `linkedin-search.md` §4: candidates seen, new after dedupe (tier outcomes are added after Step 4 scoring).
6. **Adaptive synonym rescue:** if a `title`-family query yielded <5 new IDs, generate variants per Step 3b below and append them to the plan as `family: "synonym"`.

### Step 3b: Synonym expansion (adaptive only)

When a title query is thin, generate variants:

```
Generate 2-3 synonym or adjacent-title variants for this LinkedIn job search.
The candidate's profile is:
- segment: {{user-profile.segment}}
- target_titles: {{user-profile.target_titles}}
- key_skills: {{user-profile.cv_summary.key_skills}}

The variant queries must be different enough to surface new postings, but close
enough to still match the candidate's profile. Vary by: seniority synonym (Lead↔Principal↔Senior),
function synonym (Platform↔Infrastructure↔SRE), or scope synonym (Engineer↔Architect↔Specialist).
Express each variant as a quoted phrase or a small Boolean OR-group.

Original query: "{{thin_query}}"

Return strict JSON: ["variant1", "variant2", "variant3"]
```

Before firing a variant, check query-stats: skip variants already `retired`; run variants already `promoted` as part of their cluster instead. Cap: 3 synonyms per thin query; never expand a synonym.

### Step 3c: Extract details for new jobs

Open and extract: title, company, location, salary, requirements, full description text, Easy Apply status, posting date, applicant count, job URL.

**JD persistence (required).** Immediately after extracting a job's full description text, persist it per `../shared-references/jd-storage.md` — write to `.job-scout/jds/<job_id>.txt`, set `jd_path` on the tracker entry. Never write an inline `description` field (removed from the canonical v2 schema). Set `source: "Search"` on the tracker entry.

**Corpus enrichment:** run the JD keyword extraction procedure from `../shared-references/jd-keyword-extraction.md` on each new job's description. Merges keywords into `.job-scout/cache/jd-keyword-corpus.json` — which feeds the next run's skill queries.

## Step 4: Gate + score

Load `_job-matcher` (which transitively loads `_gate-engine`). For each new job from this run:

1. `_gate-engine` runs first. If `gate_violations` is non-empty → set `tier: "D"`, `tier_reason: "gated: <kinds>"`, persist, skip dimension scoring.
2. Otherwise run the rubric. The matcher loads `user-profile.json.dimensions[]` if present, falls back to `../_job-matcher/references/dimensions-default.md`. Persist `tier`, `dimensions`, `tier_reason`, `rubric_version: "v1"`.

After scoring, complete the query-stats write: add each new job's tier to its originating query's `new_tier_counts`, update `consecutive_zero_new`, apply retirement and promotion per `linkedin-search.md` §4.

Across the entire plan, accumulate results into one combined set. Display: A-tier first (full dimension breakdown), then B-tier (one line per dimension), then C/D summary counts. Gated jobs go to a collapsed "Filtered out" group.

## Step 5: Build results payload

Construct a `data` payload for the render layer. Tiers come straight from the `_job-matcher` v1 rubric — uppercase `A | B | C | D`, no aggregate score. D-tier (gated) entries appear only in the "Filtered out" group.

```json
{
  "title": "Search results — {{N_queries}} queries · {{N_results}} surfaced",
  "subtitle": "{{N_title}} title + {{N_skill}} skill + {{N_synonym}} synonym · A:{{a}} B:{{b}} C:{{c}} · Filtered:{{gated}} · Reposts skipped:{{reposts}}",
  "generated_at": "<YYYY-MM-DD HH:MM>",
  "filename": "job-search-latest.html",
  "queries": ["<query1>", "<query2 (skill)>", "<query3 (synonym of query1)>"],
  "tier_counts": { "a": <a_count>, "b": <b_count>, "c": <c_count>, "d": <gated_count>, "total": <total> },
  "results": [
    {
      "title": "<job title>",
      "company": "<company>",
      "location": "<location>",
      "salary": "<salary or empty string>",
      "posted_at": "<YYYY-MM-DD>",
      "applicants": "<applicant count or empty string>",
      "fresh": true,
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

Within each tier, order results by `posted_at` descending. Set `fresh: true` per `linkedin-search.md` §6 (A/B-tier, posted ≤48 h, low applicant count when known) — templates render the "⚡ apply early" chip. `tags` are drawn from matched skills/signals computed during scoring; limit to 5 per job. The `url` is optional; when present the templates render a "View posting ↗" link, otherwise plain text via `{% if job.url %}` guards.

Merge newly scored jobs into `.job-scout/tracker.json` with status `"seen"`.

## Step 6: Render

Follow `../shared-references/render-orchestration.md` end-to-end (Step G already ran in Step 0):

1. Step A — payload built in Step 5 above.
2. Steps B–F — read render config, dispatch `_visualizer`, open in Chrome (or fall back), handle errors.
3. Step E — print the `job-search` summary line: `✓ {{N_queries}} queries ({{N_skill}} skill, {{N_synonym}} synonym) — {{N_results}} surfaced, {{reposts}} reposts skipped — A:{{a}} B:{{b}} · Filtered:{{gated}} — opened report in Chrome` (or `…rendered as markdown above` when falling back). If any queries were retired this run, add one line: `Retired {{n}} dead quer{{y|ies}} from the plan (3 consecutive runs with nothing new).`

If the `Agent` tool is unavailable, fall back to a terminal markdown table: tier, title, company, location, posted date, matched query; dimension breakdowns for A-tier.

## Next Steps

Suggest `/create-alerts` (zero-arg derives alerts from this plan), `/deep-sweep` for the weekly multi-page pass, or `/apply` for approved jobs.

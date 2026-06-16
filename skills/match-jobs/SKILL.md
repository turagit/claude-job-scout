---
name: match-jobs
description: Score and rank job listings against your CV and requirements
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
disable-model-invocation: true
---

Analyse LinkedIn job listings and rank them against the user's CV and requirements.

## Browser policy (read first)

All browser work in this command uses **the Claude Chrome extension exclusively**. Never request computer use. See `shared-references/browser-policy.md`.

## Step 0: Bootstrap workspace

Follow `shared-references/workspace-layout.md` to ensure `.job-scout/` exists. Then follow `shared-references/render-orchestration.md` Step G (lifecycle cleanup) to archive expired report files and prune old archives — cheap directory scan; runs at the start of every Tier 1 command.

## Step 1: Identify Source

Ask the user where to find jobs: job alerts (LinkedIn notifications), saved jobs, specific URL, or current search results.

## Step 2: Load Profile

Follow `shared-references/cv-loading.md`. Load the **_job-matcher** skill.

## Step 3: Collect IDs and dedupe FIRST

Navigate to the source page. Collect job IDs/URLs for every visible listing. Load `.job-scout/tracker.json` (see `shared-references/tracker-schema.md`). Drop any ID already in the tracker — bump `last_seen`, do not re-extract.

Also apply the repost-fingerprint check from `../shared-references/linkedin-search.md` §5 — `lower(company)|lower(title)|lower(location)` against non-rejected tracker entries; matches bump `last_seen`, log `repost id: <new_id> (<date>)` in notes, and drop out of processing.

Then check `.job-scout/cache/scores.json` for cached `(job_id, cv_hash, profile_hash, rubric_version)` results. Reuse cached results; don't re-score unchanged jobs against an unchanged CV and profile.

## Step 4: Extract and score new jobs (parallel)

For each *new* job, extract title, company, location, salary, experience level, required/preferred skills, full description text, Easy Apply status, posting date, applicant count.

**JD persistence (required).** Immediately after extracting a job's full description text, persist it per the hybrid-storage contract in `../shared-references/jd-storage.md` — write to `.job-scout/jds/<job_id>.txt`, set `jd_path` on the tracker entry. The inline `description` field is removed from the canonical v2 tracker schema.

**Corpus enrichment:** after extraction, run the JD keyword extraction procedure from `../shared-references/jd-keyword-extraction.md` on each new job's description text. This merges discovered keywords into `.job-scout/cache/jd-keyword-corpus.json` — building the user's market-specific keyword model over time. No additional LLM call; extraction piggybacks on the JD text already in context.

**Gate + score (v0.8.0+):** load `_job-matcher` (which transitively loads `_gate-engine`). For each new or legacy-rubric job:

1. Run `_gate-engine` against `user-profile.requirements`. If `gate_violations` is non-empty → set `tier: D`, `tier_reason: "gated: <kinds>"`, persist `gate_violations` on the tracker entry, skip dimension scoring.
2. Otherwise run the rubric. The matcher loads `user-profile.json.dimensions[]` if present (the per-workspace rubric discovered at `/analyze-cv` time); otherwise falls back to the universal default at `../_job-matcher/references/dimensions-default.md`. Persist `tier`, `dimensions` (per-dimension tier + evidence quotes), `tier_reason`, `rubric_version: "v1"` to the tracker entry and the score cache.
3. Display: A-tier first (with full dimension breakdown), then B-tier (with one-line per dimension), then C/D summary counts (collapsed by default in the visual report).

Gated jobs do not appear in the daily top section of the report — they appear in a collapsed "Filtered out" group below, each with a one-line "Gated: <kinds>" banner.

**Scoring fan-out:** batch the new jobs into groups of 5 (the last batch may be smaller). For each batch, dispatch one subagent per the contract in `../shared-references/subagent-protocol.md`:

```json
{
  "task": "score-job-batch",
  "inputs": {
    "jobs": [ /* extracted job blobs */ ],
    "user_profile": { "segment": "...", "cv_summary": "...", "requirements": "...", "tone": "...", "master_keyword_list": "..." },
    "cv_hash": "...",
    "profile_hash": "...",
    "rubric_version": "v1"
  },
  "budget_lines": 200,
  "allowed_tools": ["Read"]
}
```

The subagent loads the `_job-matcher` skill (which loads `_gate-engine` first), scores each job, returns deltas:

```json
{
  "status": "ok",
  "deltas": [
    { "job_id": "...", "tier": "A", "tier_reason": null,
      "dimensions": { "Leadership scope": {"tier": "A", "evidence": ["…"]}, "…": {"…": "…"} },
      "gate_violations": [],
      "rubric_version": "v1" }
  ]
}
```

Main thread collects all deltas and writes each score into `.job-scout/cache/scores.json` under the `(job_id, cv_hash, profile_hash, rubric_version)` key.

**Fallback:** if the `Agent` tool is unavailable in this session, fall back to sequential in-thread scoring using the same _job-matcher framework. Log the fallback.

## Step 4b: Reverse-Boolean discoverability check (A-tier only)

For each job the rubric tiers at A:
1. Extract from the JD: role title, top 3 required skills, location preference.
2. Construct the likely recruiter Boolean query using templates from `../_profile-optimizer/references/recruiter-search-patterns.md`: `"<role>" AND ("<skill1>" OR "<skill2>") AND "<skill3>"`.
3. Load the user's cached LinkedIn profile from `.job-scout/cache/linkedin-profile.json`. Check for each Boolean term in: headline, current job title, skills list, about section, experience descriptions.
4. Classify: **Match** (all required terms found) or **Miss** (one or more terms absent).
5. Append to the A-tier match card:

```
🔍 Recruiter search simulation for: [Job Title] at [Company]
   Boolean: "<role>" AND ("<skill1>" OR "<skill2>") AND "<skill3>"
   Result: [MATCH | MISS — "<missing_keyword>" not found on your LinkedIn profile]
   Fix: Add "<missing_keyword>" to your LinkedIn Skills section and mention in your current role's bullets
```

Skip B/C-tier jobs — the user may not apply, so the discoverability check is not worth the analysis.

## Step 5: Build results payload

Construct a `data` payload for the render layer. Tiers come straight from the `_job-matcher` v1 rubric — uppercase `A | B | C | D`, no aggregate score. Gated (D-tier) jobs appear only in the collapsed "Filtered out" group.

```json
{
  "title": "{{N}} matches today",
  "subtitle": "A-tier: {{a_count}} · B-tier: {{b_count}} · Filtered: {{gated}}",
  "generated_at": "<YYYY-MM-DD HH:MM>",
  "filename": "match-jobs-latest.html",
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
      "competitiveness": "high | med | low — OPTIONAL; omit the key entirely when not yet derived (never null)",
      "competitiveness_evidence": "<short supporting note — OPTIONAL; omit when absent>",
      "confidence": "high | med | low — OPTIONAL; omit the key entirely when not yet derived (never null)",
      "match_explanation_tag": "all-fit | one-gap | multiple-gaps | overqualified | underqualified | trajectory-concern — OPTIONAL; omit when absent",
      "url": "<absolute job URL on LinkedIn — optional; include when known>",
      "tags": ["<tag1>", "<tag2>"],
      "rationale": "<one-paragraph rationale for A-tier and top B-tier; empty string otherwise>"
    }
  ]
}
```

**Within-tier ordering (Phase 12).** Within each tier, order results by `confidence` high → med → low (entries whose `confidence` is absent sort *after* any explicit value, treated as lowest), then by `posted_at` descending as the tie-breaker. This is the COMMAND's responsibility, applied here in the payload-build before dispatch — the template renders `results[]` in the order supplied (mirroring the existing tier-order contract; the template never re-sorts). The optional scoring fields (`competitiveness`, `competitiveness_evidence`, `confidence`, `match_explanation_tag`) are passed through verbatim from the tracker / score cache when present, and **omitted entirely when absent** — never written as `null` (see `../shared-references/canonical-schemas.md` § "Written lazily"). Set `fresh: true` per `../shared-references/linkedin-search.md` §6 — templates render the "⚡ apply early" chip. `tags` should be drawn from the matched skills / signals already computed during scoring. Limit to 5 tags per job.

The `url` is an absolute LinkedIn job URL captured during job extraction. It is optional: when present, the templates render a "View posting ↗" link in HTML and a clickable title in markdown; when omitted, the templates fall back to plain title text via `{% if job.url %}` guards.

Merge newly scored jobs into `.job-scout/tracker.json` with status "seen".

## Step 6: Render

Follow `../shared-references/render-orchestration.md` end-to-end (Step G already ran in Step 0):

1. Step A — payload built in Step 5 above.
2. Steps B–F — read render config, dispatch `_visualizer`, open in Chrome (or fall back), handle errors.
3. Step E — print the `match-jobs` summary line: `✓ {{N}} matches scored — A:{{a}} B:{{b}} C:{{c}} — opened report in Chrome` (or `…rendered as markdown above` when falling back).

If the `Agent` tool is unavailable, fall back to a terminal-only markdown render: print a table with tier, title, company, location, and posted_at; for A-tier jobs additionally print the dimension breakdown and rationale below the table. Skip URL links in the fallback (the orchestrator's render-orchestration.md isn't invoked, so no _visualizer markdown template is loaded).

## Next Steps

Ask which jobs to apply to (`/apply`), save, or discard. Suggest refining search if results are poor.

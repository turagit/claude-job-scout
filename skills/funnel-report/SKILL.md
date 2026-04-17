---
name: funnel-report
description: Show where the user stands across the job-search pipeline (30/60/90 day windows, drop-offs, trending keywords, suggested next actions)
allowed-tools: Read, Write, Bash, Glob, Grep
disable-model-invocation: true
---

Generate a pipeline analytics report showing the user's job-search funnel — counts at each stage, conversion rates, drop-offs, recruiter pipeline, trending keywords from the corpus, and 3 prioritised suggested next actions.

No subagent dispatch — synthesis is bounded and inputs are JSON state files.

## Step 0: Bootstrap workspace

Follow `shared-references/workspace-layout.md` to ensure `.job-scout/` exists.

## Step 1: Load data sources

| Source | What it provides |
|--------|------------------|
| `.job-scout/tracker.json` | Hot tracker — recent jobs at every stage |
| `.job-scout/archive/tracker-<current-year>.json` | Aged `seen` jobs that rotated out (current year only) |
| `.job-scout/recruiters/threads.json` | Recruiter pipeline — notes, last activity, lead tier |
| `.job-scout/cache/jd-keyword-corpus.json` | Trending keywords (frequency-delta calculation) |

If any of `archive/tracker-<year>.json`, `threads.json`, or `jd-keyword-corpus.json` are missing, treat them as empty and proceed (the report degrades gracefully).

## Step 2: Compute the funnel

Funnel stages, in order:

```
seen → scored → A-tier → approved → applied → recruiter replied → interview → offer
```

Computation:

- **seen:** count of all tracker entries (hot + current-year archive) where `status` is non-null.
- **scored:** count where `score` is non-null.
- **A-tier:** count where `tier == "A"`.
- **approved:** count where `status == "approved"`.
- **applied:** count where `status == "applied"`.
- **recruiter replied:** count of threads in `threads.json` with at least one message after the user's most recent `last_drafted_reply` for that thread (best-effort — if the message-after-reply detection is ambiguous, count threads where `last_seen_msg_id` differs from `last_drafted_reply` and `last_updated` is more recent than `last_drafted_reply`).
- **interview:** count of tracker entries where `notes` field contains "interview" (free-text — the user marks it manually).
- **offer:** count of tracker entries where `notes` field contains "offer".

Compute these counts for three windows: **30 days**, **60 days**, **90 days** — based on tracker entry `last_seen` field.

## Step 3: Compute conversion rates and trend lines

For each window, compute conversion rate between adjacent stages:

```
seen→scored: scored / seen
scored→A-tier: A-tier / scored
A-tier→approved: approved / A-tier
approved→applied: applied / approved
applied→recruiter-replied: replied / applied
```

For trend lines, compute week-over-week deltas (last 7 days vs prior 7 days) for: seen count, A-tier ratio, applied count, recruiter reply rate.

## Step 4: Identify the top drop-off

The stage with the largest conversion-rate drop in the 30-day window. Map to a recommendation:

| Top drop-off | Recommendation |
|-------------|----------------|
| `applied → recruiter replied` | "Cover letters may not be landing. Consider tightening the recruiter-gate angle (try `/cover-letter` with the latest A-tier job)." |
| `A-tier → approved` | "You're seeing good matches but not approving them. Are deal-breakers misconfigured? Re-check `user-profile.json.requirements`." |
| `seen → A-tier` | "Few A-tier matches. Check that the master keyword list reflects current targets — re-run `/analyze-cv`." |
| `approved → applied` | "Approved jobs piling up unapplied. Run `/apply` on the backlog." |
| `scored → A-tier` | "Your scoring threshold may be too strict, or the JDs you're seeing don't match your profile." |
| `seen → scored` | "Scoring failures — check that CV and profile hashes are stable. Re-run `/analyze-cv` if the CV changed." |

If no stage shows a clear drop (rates within 10% of each other), report "Pipeline is balanced — no significant drop-off."

## Step 5: Trending keywords

Read `.job-scout/cache/jd-keyword-corpus.json`. For each keyword:

1. Compute `frequency_last_30d` = sum of source_jobs whose tracker entry has `first_seen` within the last 30 days.
2. Compute `frequency_prior_30d` = sum of source_jobs whose tracker entry has `first_seen` between 30 and 60 days ago.
3. Compute `delta` = `frequency_last_30d` - `frequency_prior_30d`.
4. Sort by absolute `delta` descending.
5. Take the top 10. Filter to terms with `frequency_last_30d >= 3` (avoid one-off noise).

Report as: "Heating up: Kubernetes (+8), Rust (+5), MLOps (+3). Cooling: Hadoop (-4), jQuery (-2)."

## Step 6: Recruiter pipeline summary

From `.job-scout/recruiters/threads.json`, list open hot/warm leads:

- `lead_tier == "hot"` or `lead_tier == "warm"`
- AND `last_updated` within last 30 days

For each, show: company, last activity date (days ago), known facts (from `notes` array), suggested next action.

Suggested next action rules:
- Last contact 0-3 days ago: "Wait — recruiter likely responding."
- Last contact 4-7 days ago: "Awaiting response. Follow up in 2-3 days if no reply."
- Last contact 8-14 days ago: "Follow up now. Brief check-in is appropriate."
- Last contact 15+ days ago: "Likely cold. One last touch or move on."

## Step 7: Suggested next actions (top 3)

Synthesise from the analysis:

1. **Top job to apply to:** highest-scored A-tier job with `status: "approved"` not yet `"applied"`. Or, if no approved-not-applied: highest-scored A-tier with `status: "seen"` (suggest user reviews + approves).
2. **Top recruiter to follow up:** hottest lead with stalest contact (largest `(lead_tier_score) × (days_since_last_contact)`).
3. **Top profile improvement:** drawn from the top drop-off's recommendation. If no drop-off, suggest the top trending keyword from Step 5 ("Add `Rust` to your Skills section — it's heating up in your market").

## Step 8: Write the report

Save to `.job-scout/reports/<YYYY-MM-DD>-funnel.md`. Format:

```markdown
---
generated: <ISO timestamp>
window: rolling 30/60/90 days
---

# Funnel Report — <YYYY-MM-DD>

## Pipeline (30/60/90 days)

| Stage | 30d | 60d | 90d | 30d→60d Δ |
|-------|-----|-----|-----|-----------|
| seen | ... | ... | ... | ... |
| ... | ... | ... | ... | ... |

## Conversion Rates (30 day window)
[content]

## Trend Lines (week-over-week)
[content]

## Top Drop-Off
**[stage]** — [recommendation]

## Trending Keywords
[content]

## Recruiter Pipeline
[content]

## Suggested Next Actions
1. [content]
2. [content]
3. [content]
```

Confirm to the user with the file path. Suggest re-running weekly.

## State files

- **`.job-scout/reports/`** — output directory.
- **All data sources are read-only** here. The report does not modify state.

## Reference Materials

- **`../shared-references/tracker-schema.md`** — tracker.json shape (read), archive policy
- **`../shared-references/supporting-docs.md`** — not needed in Phase 3, but referenced for completeness
- **`../shared-references/workspace-layout.md`** — bootstrap + state layout
- **`../recruiter-engagement/SKILL.md`** — for `notes` array shape (read)

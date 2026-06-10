---
name: create-alerts
description: Create LinkedIn job alerts derived from your query plan, or manually
allowed-tools: Read, Bash
argument-hint: [optional: "manual" for the interactive flow]
disable-model-invocation: true
version: 0.2.0
---

Create job alerts on LinkedIn. Alerts are the one discovery surface that keeps working between sweeps — LinkedIn notifies the user of new matches, and `/check-job-notifications` harvests them. Zero-arg derives the alerts from the user's query plan; `manual` runs the interactive flow.

## Browser policy (read first)

All browser work in this command uses **the Claude Chrome extension exclusively**. Never request computer use. See `../shared-references/browser-policy.md`.

## Step 0: Bootstrap workspace

Follow `../shared-references/workspace-layout.md` to ensure `.job-scout/` exists.

## Step 1: Build the proposal (zero-arg)

Derive 3–5 proposed alerts from the same plan the search commands run (`../shared-references/linkedin-search.md`):

1. **One alert per query cluster** in `user-profile.json.query_clusters[]` — the Boolean OR-group as the keywords, filters from `requirements` via the URL grammar (`f_WT`, `f_JT`, location per market). If clusters are absent, one alert per `target_titles[]` entry (cap 5, broadest first).
2. **One skill-query alert** when `.job-scout/cache/query-stats.json` shows a `skill`-family query with standout yield (`total_new/runs` highest and ≥3 A/B-tier hits) — this is the alert that catches retitled roles.
3. **Frequency:** the broadest/best-yield alert Daily; the rest Weekly.

Present the proposal as a table — keywords, location, filters, frequency — and ask the user to approve, edit, or drop entries. Nothing is created without approval.

`/create-alerts manual`: ask what alerts to create — job title/keywords, location (city/country/Remote), frequency (Daily/Weekly), additional filters — and suggest basing them on previous `/job-search` runs.

## Step 2: Create alerts

For each approved alert: navigate to the filter-addressed search URL built per `linkedin-search.md` §1 (keywords + location + filters already applied — no UI clicking), then click "Set alert" / the "Get notified" toggle on the results page.

## Step 3: Verify

Navigate to the alerts management page and verify all new alerts appear with the right criteria. Present a summary: keywords, location, frequency.

Remind the user that `/check-job-notifications` is the harvest path for these alerts, and that re-running `/analyze-cv --rediscover` after a target change should be followed by refreshing alerts here.

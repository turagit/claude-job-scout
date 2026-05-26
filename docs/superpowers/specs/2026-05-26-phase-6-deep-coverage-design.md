# Phase 6 — Deep LinkedIn Coverage Design Spec

**Status:** Approved 2026-05-26 from the v0.8.0 follow-on conversation. Decisions inherited from the 2026-05-26 /grill-me session; this spec records the operational shape.

**Problem.** v0.8.0 nailed accuracy — hard gates collapsed 67% of false-positive contract-type noise on day-one usage in the freelance workspace — but the plugin still only reads from a single LinkedIn surface (notifications page) and runs one query at a time. The user's `target_titles[]` has 6 entries; only the first is ever searched. Top picks, Similar-jobs from A-tier hits, Saved jobs, and recruiter-message embedded job links never enter the tracker. Effective coverage is a small fraction of what LinkedIn actually surfaces.

**Goal.** Ship v0.9.0 with (a) adaptive multi-query fanout in `/job-search` that iterates all target_titles plus LLM-generated synonyms when a title is thin, (b) four new source surfaces in the daily driver, and (c) a new weekly `/deep-sweep` command that performs the full coverage × depth × recency cross-product.

## Decisions (inherited from grilling)

1. **Source coverage adds:** Top picks for you, Similar-jobs from A-tier hits, Recruiter-message embedded links, Saved jobs. Target-company pages explicitly deferred.
2. **Fanout level:** Adaptive — target_titles base, LLM synonyms only when a query yields <5 surfaced jobs. Not always-fan-out (too expensive), not conservative (too thin).
3. **Cadence:** Two modes. Daily-driver `/check-job-notifications` stays fast (≤5 min, fresh window, page 1). Weekly `/deep-sweep` is thorough (~15-20 min, Past Week, pages 1-3, all surfaces, similar-jobs expansion).
4. **Gate engine runs unchanged.** Phase 5's gates already filter every newly extracted job; deeper coverage means the gates filter more, not differently.
5. **Tracker dedupe is the unifying optimisation.** Every new source reads `tracker.json` first; only genuinely new IDs are extracted. Source attribution is preserved on first-extract via `source` field.

## Out of scope

- Target-company `/company/<slug>/jobs/` sweeps (user explicitly skipped during grilling — `companies_to_target` would need user maintenance and director-level roles rarely posted there anyway).
- Pagination depth beyond 3 pages per query (diminishing returns; LinkedIn ranks tail aggressively).
- Recency expansion to Past Month for daily driver (only `/deep-sweep` reaches further back).
- Scheduled / cron-driven invocation. `disable-model-invocation: true` is non-negotiable per CLAUDE.md hard rules; everything stays user-invoked.
- Token-cost optimisation. Acknowledged that `/deep-sweep` will burn meaningful tokens; user de-prioritised cost during the grilling.

## Decisions made within Phase 6 scope

### Source coverage

| Surface | Trigger | Where it appears |
|---|---|---|
| Notifications page | Always (existing) | `/check-job-notifications` Step 2 |
| Top picks (`/jobs/collections/recommended/`) | Always after notifications | `/check-job-notifications` Step 2b (new) |
| Similar-jobs from A-tier hits | After scoring, per A-tier survivor | `/check-job-notifications` Step 5b (new) |
| Saved jobs (`/jobs/saved/`) | Always | `/check-job-notifications` Step 2c (new) |
| Recruiter-message embedded links | Parse during `/check-inbox` run | `/check-inbox` Step 1b (new) |

All five sources feed the same `tracker.json` with appropriate `source` values from the canonical enum (`Job Alert | Top Picks | Search | Inbox | Saved | Similar`).

### Multi-query fanout

`/job-search` zero-arg invocation:
1. Read `user-profile.json.target_titles[]`. If empty, fall through to `cv_summary.target_roles` (legacy compat).
2. For each title, run the existing single-query search procedure.
3. Count surfaced (post-dedupe) IDs per title.
4. **Adaptive synonym expansion:** if a title yielded <5 IDs, agent calls the LLM with this prompt:

   ```
   Generate 2-3 synonym or adjacent-title variants for this job-search query
   on LinkedIn. The candidate's profile and CV summary are:
   - segment: {{user-profile.segment}}
   - target_titles: {{user-profile.target_titles}}
   - key_skills: {{user-profile.cv_summary.key_skills}}

   The variant queries must be different enough to surface new postings but
   close enough to still match the candidate's profile.

   Original query: "{{thin_title}}"

   Return strict JSON: ["variant1", "variant2", "variant3"]
   ```

5. Refire each variant. Cap at 3 variants per thin title.
6. Cross-title dedupe is handled by `tracker.json` — opening a job already in the tracker is a no-op (just bumps `last_seen`).

`/job-search <title>` with explicit arg retains current single-query behaviour.

### Similar-jobs expansion

After `_job-matcher` produces a tier for each newly extracted job in the run, for every A-tier survivor:

1. While the agent is still on that job's page, scroll to the "Similar jobs" rail.
2. Collect the IDs (typically 4-6 results).
3. Filter against `tracker.json` to drop known.
4. Open each new similar-job, extract, persist JD, run `_gate-engine`, score.
5. Tagged `source: "Similar"` in the tracker entry.

Cheap because the agent is already on the job's tab; one click expands.

### Saved jobs sweep

Navigate to `/jobs/saved/`. Scroll to load all entries. Collect IDs. Filter against tracker. For new IDs (the user saved them via LinkedIn UI but the plugin never processed them), open and run the full extract → JD persist → gate → score chain. Tagged `source: "Saved"`.

### Recruiter-message link parsing

During `/check-inbox` Step 1 (per-thread reading), look for embedded job-posting URLs (LinkedIn shortlinks, full `/jobs/view/<id>/` URLs, or inline-card thumbnails LinkedIn injects when a recruiter shares a role). Extract the canonical job ID from each. Filter against tracker. For new IDs, open and run the full chain. Tagged `source: "Inbox"`. Linked back to the originating thread via `thread.linked_job_ids[]` (Phase 8 reads this field — populated here in Phase 6).

### `/deep-sweep` command

New skill at `skills/deep-sweep/SKILL.md`. Frontmatter: `disable-model-invocation: true`.

```
Step 0: Bootstrap workspace + archive pass (same as Tier 1 commands).
Step 1: Load profile, CV, requirements (cv-loading.md).
Step 2: Adaptive multi-query fanout (6a) over target_titles[], Past Week filter, pages 1-3 per query.
Step 3: Visit Top picks, scroll all loaded, collect IDs.
Step 4: Visit Saved jobs, scroll all loaded, collect IDs.
Step 5: Dedupe ALL collected IDs against tracker.json.
Step 6: Extract details for new IDs, persist JDs.
Step 7: Gate + score with v1 rubric.
Step 8: For each A-tier in this run, follow Similar-jobs rail; ingest new IDs.
Step 9: Render via _visualizer with view='deep-sweep' (new template, mirror match-jobs.html.j2 layout).
```

Expected runtime: 15-20 min on a typical workspace. The user runs it weekly.

## Schema impact

No schema changes. The canonical `tracker.jobs.*.source` enum already includes `Top Picks`, `Saved`, `Similar`, `Inbox` (locked in Phase 5 schemas). Phase 6 just exercises them.

`thread.linked_job_ids[]` is already in canonical-schemas.md (locked Phase 5 for the recruiter rebuild in Phase 8). Phase 6 populates it from `/check-inbox` link parsing.

## Visualizer impact

Daily-driver and `/deep-sweep` reports gain a per-card `source` tag chip showing which surface the job came from. Minor template addition.

A new template `skills/_visualizer/templates/html/deep-sweep.html.j2` and `.md.j2` — same shape as `match-jobs.*.j2` but with extra subtitle-line stats (per-source breakdown).

## Out-of-band considerations

- **LinkedIn rate-limiting risk** grows with query volume. Mitigations: keep the daily driver at one notifications page + one Top picks page + Saved + similar-jobs-from-A-tier-only (bounded by tier-A count, typically ≤5). `/deep-sweep` adds the multi-query fanout but stays inside one workspace per run.
- **Browser session continuity**: every new sweep navigates the user's logged-in tab. The Chrome extension policy stays the gatekeeper; no other automation is permitted.
- **Token cost** of `/deep-sweep` is non-trivial (many queries, many scored jobs, many evidence-quote extractions). Acceptable given the user de-prioritised cost during grilling.

## Phase 7 hooks

The reject-with-reason chip UX (Phase 7) reads from the visual report. Adding the per-card `source` tag in Phase 6 prepares the card for Phase 7 chip additions — same template touched, same data shape extended.

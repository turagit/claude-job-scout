# LinkedIn Search — URL Grammar, Boolean Queries, Query Plan v2

> **Single source of truth for how this plugin searches LinkedIn jobs.** Every command that runs a job search (`/job-search`, `/deep-sweep`, `/create-alerts`, and any future discovery surface) builds its searches from this reference. The aims: maximum recall for relevant roles, deterministic reproducible queries, the fewest possible browser steps, and a learning loop so the plan improves with every run.

## 1. Filter-addressed URLs (use these, not the filter UI)

LinkedIn job-search filters are addressable directly in the URL. Constructing the URL is faster, cheaper in browser steps, and reproducible — clicking the filter UI is the fallback, not the default.

**Base form:**

```
https://www.linkedin.com/jobs/search/?keywords=<url-encoded query>&location=<url-encoded location>
```

**Parameters:**

| Param | Meaning | Values | Source |
|---|---|---|---|
| `keywords` | The Boolean query (§2) | URL-encoded string | query plan (§3) |
| `location` | Market to search | Free text: `United Kingdom`, `London`, `European Union`, `Portugal` … | `requirements.location_preferences[]` |
| `f_WT` | Workplace type | `1` on-site · `2` remote · `3` hybrid (comma-combinable: `2,3`) | `requirements.work_arrangement` |
| `f_TPR` | Posted within | `r86400` 24 h · `r604800` week · `r2592000` month | cadence: daily sweeps `r86400`–`r604800`; `/deep-sweep` `r604800` |
| `f_JT` | Job type | `F` full-time · `C` contract · `T` temporary · `P` part-time (comma-combinable) | `requirements.contract_type` (permanent → `F`; freelance → `C,T`) |
| `f_E` | Experience level | `1` intern … `4` mid-senior · `5` director · `6` executive (comma-combinable) | `requirements.seniority_floor` when cleanly mappable; otherwise omit — the gate engine is the enforcement point, not this filter |
| `f_AL` | Easy Apply only | `true` | **never set by default** — it hides most of the market; only on explicit user request |
| `sortBy` | Result order | `DD` date · `R` relevance | sweeps use `DD` (pagination depth then maps to recency); explicit single-title `/job-search <title>` may use `R` |
| `distance` | Radius (miles) for city locations | e.g. `25` | optional |

**Worked example** — remote-or-hybrid contract roles in the UK, posted this week, date-sorted:

```
https://www.linkedin.com/jobs/search/?keywords=%28%22Platform%20Engineer%22%20OR%20%22Infrastructure%20Engineer%22%29%20NOT%20intern&location=United%20Kingdom&f_WT=2%2C3&f_JT=C%2CT&f_TPR=r604800&sortBy=DD
```

**Drift fallback.** These parameters are stable but undocumented; LinkedIn may drift them. If a constructed URL ignores a filter (verify on the first query of a run by glancing at the active filter chips on the results page), fall back to setting that one filter through the UI for the rest of the run, and note the drift in the run summary so it can be reported.

## 2. Boolean queries in the `keywords` field

The keywords box supports `AND`, `OR`, `NOT`, quoted phrases, and parentheses. Operators must be UPPERCASE. Rules of craft:

- **Quote every multi-word phrase**: `"site reliability engineer"`, not three loose words.
- **One OR-group covers a whole synonym cluster** — `("SRE Manager" OR "Site Reliability Manager" OR "Platform Reliability Lead")` is one query where the old plan ran three.
- **`NOT` tails strip named noise**: `NOT (intern OR graduate OR unpaid)`. Build the tail from the user's declared exclusions (a `seniority_floor` above entry level implies `NOT (intern OR graduate OR junior)`; the user may add terms during `/analyze-cv`). Keep tails short — over-exclusion silently costs recall.
- **Depth limit**: at most ~2 levels of nesting and ~6 OR terms per group. LinkedIn truncates or mis-parses monster queries; two medium queries beat one giant one.
- **Skill queries pair skills with a context anchor**: `(Kubernetes AND Terraform) AND ("platform" OR "infrastructure")` — a bare skill pair surfaces every job that mentions the words; the anchor keeps it in-lane.

## 3. Query plan v2

A query plan is an ordered list of entries: `{ query, family, location, params }` where `family` is `title | skill | synonym | explicit`.

### 3a. Title queries (always)

One Boolean query per **title cluster**. Clusters live in `user-profile.json.query_clusters[]` (optional, additive):

```json
"query_clusters": [
  {
    "label": "platform-leadership",
    "titles": ["Platform Engineering Manager", "Head of Platform", "Infrastructure Engineering Manager"],
    "not_terms": ["intern", "graduate"]
  }
]
```

`/analyze-cv` discovery (Step 3d) proposes the clusters by grouping `target_titles[]` into true-synonym sets; the user approves or edits. Each cluster renders as `("Title A" OR "Title B" OR "Title C") NOT (term1 OR term2)`.

**Fallback:** when `query_clusters[]` is absent or empty, run one plain query per `target_titles[]` entry (pre-v0.10.0 behaviour). Never block on missing clusters.

### 3b. Skill queries (deep-sweep always; zero-arg /job-search when the corpus is ripe)

Skill queries catch the roles title queries can never see — right job, unexpected title. Build 2–3 per run:

1. Read `.job-scout/cache/jd-keyword-corpus.json`. Require ≥10 source jobs; below that the corpus is noise — skip this family.
2. Take the skills that co-occur most often in the JDs of this workspace's A/B-tier jobs, intersect with `cv_summary.key_skills` (only search for what the CV can evidence).
3. Form pairs of the top co-occurring skills and add a context anchor drawn from the segment or cluster labels: `(<skill1> AND <skill2>) AND (<anchor terms>)`.
4. Skip any pair already represented by a non-retired query in query-stats (§4).

### 3c. Geo iteration

When `requirements.location_preferences[]` names multiple markets (e.g. `["United Kingdom", "European Union"]`), each query in the plan runs once per market via the `location=` parameter. Fully-remote-only workspaces with a single "worldwide remote" preference use one pass with `f_WT=2`.

### 3d. Adaptive synonym rescue (unchanged from v0.9.0, plus memory)

When a title query yields <5 new (post-dedupe) IDs, LLM-generate 2–3 synonym variants (prompt in `job-search/SKILL.md`), run them as `family: "synonym"`. Cap 3 per thin query; never expand a synonym. **New:** record every variant in query-stats (§4); a variant that proves itself is promoted into its cluster rather than regenerated from scratch next run.

### 3e. Plan ordering

Run proven queries first: order by recency-weighted yield from query-stats (§4), cold-start entries last in declaration order. This way, a rate-limit interruption mid-run costs the least-proven queries, not the best ones.

## 4. Query performance memory — `.job-scout/cache/query-stats.json`

A cache (deletable at any time; absence = cold start). Shape:

```json
{
  "version": 1,
  "queries": {
    "<normalised query string>": {
      "family": "title | skill | synonym | explicit",
      "first_run": "YYYY-MM-DD",
      "last_run": "YYYY-MM-DD",
      "runs": 7,
      "total_candidates": 162,
      "total_new": 38,
      "new_tier_counts": { "A": 4, "B": 9, "C": 18, "D": 7 },
      "consecutive_zero_new": 0,
      "status": "active | retired | promoted",
      "cluster_label": "platform-leadership | null"
    }
  }
}
```

**Write trigger:** at the end of every sweep, for each executed query: bump `runs`, `last_run`, `total_candidates`, `total_new`; once scoring completes, add the new jobs' tiers to `new_tier_counts`; set `consecutive_zero_new` to 0 if the query produced new IDs, else increment.

**Retirement:** `consecutive_zero_new >= 3` → set `status: "retired"`. Retired queries leave the default plan; their slot goes to a fresh synonym variant. Mention retirements in the run summary (one line) so the user can revive by editing the file or re-running `/analyze-cv --rediscover`.

**Promotion:** a `synonym` query whose `new_tier_counts.A + new_tier_counts.B >= 3` → set `status: "promoted"` and propose appending its title to the originating cluster in `query_clusters[]` (user confirms; write via the `state-validators.md` atomic pattern). Promoted queries run every time without regeneration.

**Yield ordering metric (§3e):** `total_new / runs`, halved if `last_run` is more than 30 days old. No precision theatre — this only needs to sort a list of ~10 queries.

## 5. Repost fingerprint dedupe

LinkedIn re-lists the same role under fresh job IDs. ID dedupe alone re-extracts and re-scores these. So, in every sweep's dedupe step, *after* the ID filter:

1. For each surviving candidate, compute `fingerprint = lower(trim(company)) + "|" + lower(trim(title)) + "|" + lower(trim(location))`.
2. Build the comparison set from tracker entries that are not `rejected` (a rejected repost should stay invisible; a *changed* role re-listed under a new title forms a new fingerprint and passes).
3. On a fingerprint match: treat as a repost — bump the existing entry's `last_seen`, append `repost id: <new_id> (<YYYY-MM-DD>)` to its `notes`, and drop the candidate from the to-process list. No extraction, no scoring, no report card.
4. On no match: process normally.

Cost: string assembly over data already in memory. No schema change.

## 6. Freshness flag

Sweep report payloads already carry `posted_at` and (when shown) `applicants`. Two display rules, applied when building payloads:

- Within a tier, order results by `posted_at` descending (freshest first).
- An A- or B-tier job posted within the last 48 hours — and, when applicant count is known, with fewer than ~25 applicants — gets `"fresh": true` in its payload entry. Templates render an "⚡ apply early" chip. Early application is the cheapest response-rate lever there is; the report should make it impossible to miss.

## Consumers

- `job-search/SKILL.md` — full plan (title + skill + geo + synonym rescue), stats writes.
- `deep-sweep/SKILL.md` — full plan at deep settings (Past Week, pages 1–3), stats writes.
- `check-job-notifications/SKILL.md` — not a query surface, but applies §5 repost dedupe and §6 freshness to everything it ingests.
- `create-alerts/SKILL.md` — derives proposed alerts from clusters + top-performing queries.
- `analyze-cv/SKILL.md` — Step 3d cluster discovery writes `query_clusters[]`.

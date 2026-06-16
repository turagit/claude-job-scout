# Canonical Schemas (locked v2)

> **Authoritative reference for `.job-scout/` state writes.** Any skill that writes to `user-profile.json`, `tracker.json`, or `recruiters/threads.json` MUST conform to these schemas. Validation rules live in `state-validators.md`.

This reference replaces the older inline schemas in `tracker-schema.md` and `_job-matcher/references/user-profile-schema.md`. Those files now point here.

## `user-profile.json`

```json
{
  "schema_version": 2,
  "cv_path": "string",
  "cv_hash": "string|null",
  "cv_filename_on_linkedin": "string|null",
  "cv_uploaded_to_linkedin_at": "ISO8601|null",
  "cv_summary": {
    "key_skills": ["string"],
    "technologies": ["string"],
    "seniority": "string",
    "years_experience": "number",
    "target_roles": ["string"],
    "domain_expertise": ["string"],
    "industries": ["string"]
  },
  "target_titles": ["string"],
  "query_clusters": [
    {
      "label": "string — short kebab-case cluster label",
      "titles": ["string — true-synonym titles searched as one Boolean OR-group"],
      "not_terms": ["string — terms appended as a NOT tail"]
    }
  ],
  "preferred_length_pages": "number|null",
  "linkedin_profile_url": "string|null",
  "profile_hash": "string|null",
  "discovery_complete": "boolean",
  "segment": "string — free-text descriptor of the workspace's job-search lane (e.g. 'head pastry chef in Lisbon', 'construction site engineer — UK civils', 'mid-career switch to UX research', 'freelance backend contracts EU-remote', 'permanent leadership roles in enterprise IT')",
  "dimensions": [
    {
      "name": "string — dimension label",
      "criteria": {
        "A": "string — A-tier criterion",
        "B": "string — B-tier criterion",
        "C": "string — C-tier criterion",
        "D": "string — D-tier criterion"
      },
      "weight": "number — optional, defaults to 1.0; load-bearing dimensions can be tagged for the overall-tier derivation rule",
      "type": "load-bearing | modifying — optional; absent is treated as load-bearing"
    }
  ],
  "requirements": {
    "base_country": "string|null — the user's home/legal-work country; ONLY ever set by onboarding, never inferred. Default null.",
    "target_geography": "string|array|null — where the user wants roles (country, region, or 'remote'); default null",
    "work_arrangement": ["remote", "hybrid", "on-site"],
    "contract_type": ["permanent", "freelance"],
    "location_preferences": ["string"],
    "seniority_floor": "string|null",
    "min_day_rate": "number|null",
    "ideal_day_rate": "number|null",
    "rate_currency": "string|null",
    "salary_floor": "number|null",
    "salary_currency": "string|null",
    "deal_breakers": [
      {
        "kind": "work_arrangement | contract_type | seniority_floor | location | industry | company | rate_floor | salary_floor | custom",
        "values": ["string"],
        "free_text": "string|null",
        "source": "elicited | learned",
        "added_at": "ISO8601"
      }
    ],
    "nice_to_haves": ["string"],
    "companies_to_avoid": ["string"],
    "industries_to_avoid": ["string"],
    "companies_to_target": ["string"]
  },
  "tone": {
    "register": "string",
    "dialect": "british",
    "warmth": "string",
    "vocabulary_cues": ["string"],
    "exemplars": ["string"],
    "avoid": ["string"]
  },
  "master_keyword_list": ["string"],
  "ultramode": {
    "default": "boolean — when true, multi-source ultramode runs without re-prompting; default false",
    "api_keys": "object — maps a provider slug to an API key, e.g. { 'greenhouse': 'gh_live_abc123' }; default {}",
    "registry_built_at": "ISO8601|null — when sources.json was last (re)built; null until first discovery"
  },
  "last_updated": "ISO8601",
  "created_by": "string"
}
```

The `ultramode` block is additive and optional. Absent (or `default: false`, `api_keys: {}`, `registry_built_at: null`) means ultramode is off / cold-start — the plugin behaves exactly as in pre-Phase-11 LinkedIn-only mode. `requirements.base_country` is **only ever populated by onboarding, never inferred** from CV text, locale, or prior runs.

### Dimension `type` (deterministic-derivation enabler)

The optional `dimensions[].type` field tags each rubric dimension as either `load-bearing` (a must-clear core requirement, e.g. the headline skill or seniority) or `modifying` (a nice-to-have that nudges the tier but never sinks a match on its own, e.g. a bonus tooling familiarity). The field is **additive and back-compatible**: an entry without `type` is treated as `load-bearing`. Tagging makes the later confidence and `match_explanation_tag` derivation deterministic for *custom* per-workspace rubrics — the deriver can count gaps against load-bearing dimensions only, rather than guessing which dimensions are decisive. A worked `dimensions[]` example carrying real `type` values:

```json
"dimensions": [
  {
    "name": "core-language",
    "criteria": {
      "A": "expert in Python, 5+ years shipping production services",
      "B": "strong Python, 3+ years",
      "C": "working Python, 1-2 years",
      "D": "little or no Python"
    },
    "weight": 2.0,
    "type": "load-bearing"
  },
  {
    "name": "cloud-tooling",
    "criteria": {
      "A": "deep AWS plus Terraform in anger",
      "B": "solid AWS, some IaC",
      "C": "occasional cloud exposure",
      "D": "no cloud experience"
    },
    "weight": 1.0,
    "type": "modifying"
  }
]
```

## `tracker.json`

```json
{
  "schema_version": 2,
  "version": 2,
  "stats": {
    "total_seen": "number",
    "applied": "number",
    "rejected": "number",
    "last_run": "ISO8601|null",
    "last_search": "ISO8601|null",
    "last_archive_pass": "YYYY-MM-DD|null",
    "last_deep_sweep": "YYYY-MM-DD|null"
  },
  "jobs": {
    "4012345678": {
      "id": "string — the tracker key repeated verbatim (this map is keyed by job id)",
      "url": "string",
      "title": "string",
      "company": "string",
      "source": {
        "lane": "string — e.g. linkedin | ats | remote-board | aggregator | freelance",
        "provider": "string — slug, e.g. linkedin | greenhouse | remoteok",
        "board": "string — slug or LinkedIn surface, e.g. miro | Search | Top Picks"
      },
      "score": "number|null",
      "tier": "A | B | C | D | untiered",
      "tier_reason": "string|null",
      "dimensions": {
        "core-language": {
          "tier": "A | B | C | D",
          "evidence": ["string"]
        }
      },
      "gate_violations": [
        {"kind": "string", "detail": "string"}
      ],
      "rubric_version": "legacy | v1",
      "competitiveness": "high | med | low | null",
      "competitiveness_evidence": "string|null",
      "confidence": "high | med | low | null",
      "match_explanation_tag": "all-fit | one-gap | multiple-gaps | overqualified | underqualified | trajectory-concern | null",
      "status": "seen | approved | applied | rejected | skipped",
      "filtered_reason": "string|null",
      "reject_reason": "string|null",
      "rejected_at": "ISO8601|null",
      "approved_at": "ISO8601|null",
      "applied_at": "ISO8601|null",
      "first_seen": "YYYY-MM-DD",
      "last_seen": "YYYY-MM-DD",
      "jd_path": "string|null",
      "linked_thread_ids": ["string"],
      "notes": "string"
    }
  }
}
```

`jd_path` is a workspace-relative path to the full JD text under `.job-scout/jds/` named for the job id (for example `.job-scout/jds/4012345678.txt`). The inline `description` field used in v1 is removed — full JD text is hybrid-stored. See `jd-storage.md` (created in Task 5) for the contract.

`linked_thread_ids` is the reverse pointer of each thread's `linked_job_ids` (keyed by thread id) — added by `/check-inbox` Step 1b in v0.9.0 when it extracts a job from a recruiter message. Lets the visualiser show a "🔗 from recruiter" chip naming the recruiter on a job card, and (in Phase 8) lets the recruiter UI surface every job linked to a thread.

### Structured `source` (v3)

As of tracker `schema_version: 3`, `source` is a structured object `{lane, provider, board}`, not the old six-value LinkedIn string. This lets ultramode (Phase 11) record jobs sourced beyond LinkedIn while keeping one shape everywhere.

- `lane` — the broad acquisition channel, e.g. `linkedin`, `ats`, `remote-board`, `aggregator`, `freelance`.
- `provider` — the platform slug, e.g. `linkedin`, `greenhouse`, `remoteok`. Always a slug (see slug charset below).
- `board` — the specific board, company instance, or LinkedIn surface. For LinkedIn it is one of the legacy surface names (`Job Alert`, `Top Picks`, `Search`, `Inbox`, `Saved`, `Similar`); for external providers it is the board slug (e.g. `miro` for `greenhouse__miro`).

LinkedIn jobs map to a structured source whose `board` is the surface name, e.g. `{lane: "linkedin", provider: "linkedin", board: "Search"}`. **Every skill that reads `tracker.jobs[*].source` MUST call the `tracker_read_source(value)` shim in `state-validators.md`** — never read the field's shape directly, because a not-yet-upgraded entry may still hold a bare legacy string.

**Lazy upgrade.** Reads accept both shapes (the shim normalises). On the next write of any entry, the entry is rewritten with the structured shape, and the tracker file's `schema_version` bumps `2 → 3` on that first write. There is no destructive one-shot rewrite of every entry.

### Namespaced external IDs (collision-proof)

The tracker entry's `id` field is the single canonical identifier for a job. **Tracker keys, `cache/scores.json` keys, and the per-job JD text file under `jds/` (named for the id) all use this `id` verbatim.** Readers MUST NOT infer the ID format from context — LinkedIn IDs are bare numeric strings (e.g. `4012345678`), external IDs are namespaced (below). Always treat `id` as an opaque string.

- **Slug charset.** Provider and board slugs are normalised at discovery to `[a-z0-9-]`: lowercase the value, replace every `[^a-z0-9-]` run with `-`, compress repeated `-`, then trim leading/trailing `-`. **No underscores inside a slug.**
- **External ID format.** Three segments — provider slug, then board slug, then the external id — joined by `__` (double underscore), the only segment separator. Because slugs never contain `_`, the three segments are always unambiguous and collision-free. Example: `greenhouse__miro__4012345`.
- **LinkedIn IDs stay bare numeric** — no namespace prefix, for back-compatibility with existing trackers and score caches.
- **Uniqueness is per-source, not global.** An `id` is unique *within its source*; the same role surfaced by two different sources is two entries with two IDs. Treating those as the same job is a fingerprint/dedupe concern (handled elsewhere), not an ID concern.

## `recruiters/threads.json`

```json
{
  "schema_version": 2,
  "last_scanned": "ISO8601|null",
  "scan_source": "string",
  "stats": {
    "total_threads_scanned": "number",
    "hot": "number",
    "warm": "number",
    "cold": "number",
    "non_lead": "number"
  },
  "threads": {
    "2-abc123def456": {
      "recruiter_name": "string",
      "participant_title": "string|null",
      "company": "string|null",
      "lead_tier": "hot | warm | cold | non-lead",
      "lead_tier_detail": "string|null",
      "last_seen_msg_id": "string|null",
      "last_drafted_reply": "string|null",
      "last_updated": "ISO8601|null",
      "last_message_date": "YYYY-MM-DD|null",
      "thread_url_path": "string|null",
      "linked_job_ids": ["string"],
      "notes": [
        {"date": "YYYY-MM-DD", "note": "string"}
      ]
    }
  }
}
```

## `cache/scores.json` (score cache)

The per-workspace score cache. The operational read/write/invalidation flow lives in `_job-matcher/SKILL.md`; this section is the canonical shape for the **cache key** and the **cache value object**, so the scoring additions below stay in one authoritative place.

**The cache key stays the four-part form and is NOT changed by these additions.** A key is the string `job_id:cv_hash:profile_hash:v1` — the `job_id`, the `cv_hash`, the `profile_hash`, and the literal rubric tag `v1`. `rubric_version` stays `v1`; the scoring fields added below are **additive value-object fields and do not touch the key**. Adding them does **not** bump `rubric_version` and does **not** invalidate any existing cached entry.

```json
{
  "4012345678:a1b2c3:d4e5f6:v1": {
    "tier": "A",
    "tier_reason": "string|null",
    "dimensions": { "core-language": { "tier": "A", "evidence": ["10 years Python"] } },
    "gate_violations": [],
    "rubric_version": "v1",
    "competitiveness": "high",
    "competitiveness_evidence": "string|null",
    "confidence": "high",
    "match_explanation_tag": "all-fit",
    "scored_at": "2026-06-16T09:00:00Z"
  }
}
```

The four scoring fields — `competitiveness` (`high`/`med`/`low` or null), `competitiveness_evidence` (string or null), `confidence` (`high`/`med`/`low` or null), and `match_explanation_tag` (`all-fit`/`one-gap`/`multiple-gaps`/`overqualified`/`underqualified`/`trajectory-concern` or null) — appear on **both** the tracker job entry and this cache value object.

**Written lazily, omitted (never null) when absent.** They are populated on the **next scoring** of an entry, not backfilled. For an entry not yet rescored, each key is **omitted entirely from the object — never written as `null`**. An absent key and a key holding `null` are therefore distinguishable: absent means "not yet derived", explicit `null` means "derived and genuinely not applicable".

**Reader contract — every reader and template MUST treat these four keys as optionally-absent.** Never assume presence. In Jinja, read defensively, e.g. `{{ job.confidence or '' }}` and `{{ job.match_explanation_tag or '' }}`. In Python, use `job.get('confidence')` / `job.get('competitiveness')` and tolerate `None`. A missing key MUST render as a neutral/empty state, never as an error or a stray literal. The same contract applies whether the fields are read off the tracker entry or off the cache value object.

The tracker file `schema_version` is **NOT** bumped for these additions (it stays at v3 / lazily-upgraded v3): the fields are optional and additive, matching the non-bumping rule in § When to bump `schema_version`.

## `sources.json` (ultramode source registry)

`.job-scout/sources.json` is the single per-workspace registry of verified job sources, written by ultramode discovery (Phase 11). One registry holds sources of mixed types, so there is **no top-level `lane`** field. Instead each source carries a `category` (its broad source type — which maps to the tracker entry's `source.lane` when a job is sourced) and an `access_lane` (its technical polling method). The file is regenerable and deletable: its absence triggers first-run discovery.

```json
{
  "schema_version": 1,
  "base_country": "string|null — copied from user-profile requirements.base_country at build time",
  "target_geography": "string|array|null — copied from requirements.target_geography at build time",
  "priority_order": ["string — source names in the order the engine should poll them"],
  "backbone": ["string — names of the always-on universal aggregator backbone sources"],
  "sources": [
    {
      "name": "string — human-readable source name",
      "url": "string — homepage or board URL",
      "category": "ats-provider | remote-board | aggregator | national-board | freelance-marketplace | community",
      "access_lane": "api | rss | html | extension",
      "endpoint": "string — the URL ultramode fetches: the JSON API (api), the feed (rss), or the listing/search page (html). MUST be non-empty for api, rss and html; may be empty for extension (the dispatcher navigates `url` in the browser). `url` is the human-facing homepage.",
      "needs_key": "boolean — true if an API key is required (looked up in user-profile ultramode.api_keys)",
      "needs_slug": "boolean — true if a per-board slug must be supplied to query",
      "priority": "number — lower polls first",
      "poll_method": "string — short note on how to poll (e.g. 'GET endpoint, paginate', 'fetch RSS', 'extension browse')",
      "notes": "string — free-text caveats, rate limits, coverage notes",
      "verified_at": "ISO8601|null — when this source was last verified reachable"
    }
  ]
}
```

A worked example with four real sources lives in `sources-schema-example.json` alongside this reference.

## `cache/capability-graph.json` (CV capability graph)

The derived map of what the user's CV can credibly speak to, used by discovery and categorisation to reach beyond literal keyword overlap. It is a **regenerable, deletable cache keyed by `cv_hash`** — if the CV changes the hash changes and the graph is rebuilt; deleting the file simply forces a rebuild on next use. The envelope:

- `stated` — capabilities the CV names outright (the literal skills and tools on the page).
- `latent` — capabilities strongly implied by the stated ones but not named (e.g. someone who ran on-call rotations for a payments platform latently knows incident response).
- `adjacent` — neighbouring capabilities a short hop away that the user could credibly grow into or that recruiters would read across to.

```json
{
  "schema_version": 1,
  "cv_hash": "a1b2c3d4e5f6",
  "built_at": "2026-06-16T09:00:00Z",
  "stated": ["python", "postgresql", "aws lambda", "terraform"],
  "latent": ["incident response", "infrastructure as code", "cost optimisation"],
  "adjacent": ["kubernetes", "platform engineering", "data engineering"]
}
```

## `cache/jargon-normalizer.json` (jargon recall layer)

A **persistent** alias dictionary that maps a canonical term to the surface forms hiring teams actually write. It powers jargon recall — matching a CV's "site reliability engineer" against a JD that only ever says "SRE", and vice versa. Unlike the capability graph this file is **not keyed by `cv_hash`**: it accretes across runs and workspaces' worth of learning. `aliases` maps a canonical term **string** to a **list of alias strings**.

```json
{
  "schema_version": 1,
  "updated_at": "2026-06-16T09:00:00Z",
  "aliases": {
    "sre": ["site reliability engineer", "reliability engineer"],
    "ml engineer": ["machine learning engineer", "applied scientist"],
    "k8s": ["kubernetes", "container orchestration"]
  }
}
```

Both caches are **regenerable and deletable** — they hold no source-of-truth state. The capability graph rebuilds from the CV; the jargon normaliser rebuilds (more slowly) from observed JD and CV vocabulary. Their absence is a cache miss, never an error.

## Canonical enums (single source of truth)

| Field | Allowed values |
|---|---|
| `tracker.jobs.*.status` | `seen`, `approved`, `applied`, `rejected`, `skipped` |
| `tracker.jobs.*.tier` | `A`, `B`, `C`, `D`, `untiered` |
| `tracker.jobs.*.rubric_version` | `legacy`, `v1` |
| `tracker.jobs.*.source.board` (LinkedIn lane only) | `Job Alert`, `Top Picks`, `Search`, `Inbox`, `Saved`, `Similar` |
| `threads.*.lead_tier` | `hot`, `warm`, `cold`, `non-lead` |
| `user-profile.requirements.deal_breakers[].kind` | `work_arrangement`, `contract_type`, `seniority_floor`, `location`, `industry`, `company`, `rate_floor`, `salary_floor`, `custom` |
| `user-profile.segment` | free-text string (any descriptor the user chooses at `/analyze-cv` discovery) |
| `sources.sources[].category` | `ats-provider`, `remote-board`, `aggregator`, `national-board`, `freelance-marketplace`, `community` |
| `sources.sources[].access_lane` | `api`, `rss`, `html`, `extension` |
| `query-stats.json` query `family` | `title`, `skill`, `synonym`, `explicit`, `capability` |
| `tracker.jobs.*.competitiveness` / `scores.*.competitiveness` | `high`, `med`, `low`, or absent/null |
| `tracker.jobs.*.confidence` / `scores.*.confidence` | `high`, `med`, `low`, or absent/null |
| `tracker.jobs.*.match_explanation_tag` / `scores.*.match_explanation_tag` | `all-fit`, `one-gap`, `multiple-gaps`, `overqualified`, `underqualified`, `trajectory-concern`, or absent/null |
| `user-profile.dimensions[].type` | `load-bearing`, `modifying`, or absent (treated as `load-bearing`) |

The `query-stats.json` `family` enum gains `capability` here (Phase 12): a query family that searches on a CV capability — stated, latent, or adjacent — drawn from `cache/capability-graph.json`. The four scoring fields and `dimensions[].type` are listed for completeness; they are optional/additive and validated only when present.

## Status transition rules

- `seen → approved → applied` (forward only)
- `seen → rejected` (forward only)
- `seen → skipped` (forward only — for explicit user "not now")
- Never downgrade. Never set a status field to a value outside the enum above.

## When to bump `schema_version`

Bump when a field is renamed, removed, or its type changes. Adding optional fields without a rename is a non-bumping change. A migration script must exist for every bump and live in the plan that introduced the change.

**Tracker `schema_version: 2 → 3` (Phase 11).** Triggered by the structured-`source` change (the field's type changes from string to object). Per the lazy-upgrade rule in § Structured `source` (v3), the bump happens on the **first write** of any entry after the upgrade — reads tolerate both shapes via `tracker_read_source(value)` until then. The `user-profile.json` additions (`requirements.base_country`, `requirements.target_geography`, `ultramode`) are all optional and do **not** bump its `schema_version`.

# Ultramode Sources (taxonomy, lanes, backbone, resolvers)

> **Central reference for multi-source ultramode (Phase 11).** Source categories and access lanes are universal; the concrete providers that fill them are discovered and verified per workspace and cached in `.job-scout/sources.json`. This file defines the taxonomy, the access-lane ingestion methods, the always-on universal backbone, the ATS slug resolver, and the cross-source dedupe + canonical-preference rules.
>
> Companion references: `canonical-schemas.md` (the `sources.json` schema, structured `source`, namespaced IDs), `browser-policy.md` (the `WebFetch` carve-out and the extension-lane rule), `linkedin-search.md` (the repost fingerprint reused below).

## Source taxonomy (six categories)

Every verified source is classified into exactly one **category** (its broad source type). The category maps onto the tracker entry's `source.lane` when a job is sourced. These six values are the canonical `sources.sources[].category` enum (see `canonical-schemas.md`):

| Category | What it is | Typical canonical priority |
|---|---|---|
| `ats-provider` | An applicant-tracking system serving one employer's own board (Greenhouse, Lever, Ashby, Workable, Recruitee, Personio, SmartRecruiters, Workday). Direct-to-employer. | Highest — this is the employer's own listing. |
| `remote-board` | A remote-first job board with whole-board feeds (RemoteOK, Remotive, Himalayas, Working Nomads, We Work Remotely). | Mid. |
| `aggregator` | A multi-employer, multi-country search index (Adzuna, Arbeitnow, Jooble-class indexes). Occupation-agnostic. | Lower — usually a re-list of a role hosted elsewhere. |
| `national-board` | A country- or vertical-specific board (e.g. a national public-sector board, an EU member-state board). Resolved by `base_country`. | Mid. |
| `freelance-marketplace` | A contract/gig marketplace (Upwork, Malt, Freelancer-class). Mostly login-walled. | Lowest. |
| `community` | A curated community feed (Hacker News "Who is hiring", Slack/Discord job channels, niche newsletters). Mostly login-walled. | Mid. |

## Access lanes (four lanes, each with an ingestion method)

Independently of category, each source carries an **access lane** — its technical polling method (the canonical `sources.sources[].access_lane` enum). One category can appear in several lanes (e.g. an aggregator may be `api` or `html`). The ingestion method per lane:

| Lane | Ingestion method |
|---|---|
| `api` | Read-only HTTP `GET` the documented JSON endpoint, then **parse the JSON**. Paginate as the endpoint dictates. Uses the `WebFetch` carve-out (see `browser-policy.md`). |
| `rss` | Read-only HTTP `GET` the feed URL, then **parse the XML** (one `<item>`/`<entry>` per posting). Dedupe by item GUID before extracting. Uses the `WebFetch` carve-out. |
| `html` | Read-only HTTP `GET` the source's `endpoint` (its listing/search page; `url` is the homepage), then **apply a client-side full-text filter** over title + tags + body. **Never trust the source's documented `category=` / `search=` query parameters** — verified discovery found free-feed server-side filters return identical, unfiltered results for every term (Decision 9). Filter client-side or you ingest noise. Uses the `WebFetch` carve-out. |
| `extension` | A logged-in browser sweep via the Claude Chrome extension, following **dedupe-before-extract** (load the tracker, collect candidate IDs, filter against it, open only new ones — Hard Rule #2). This is the **only** lane that touches the user's logged-in session. **Login-walled sources** (most freelance marketplaces, Slack/Discord communities, some national boards and consumer aggregators) use the **extension lane** — never credentialed HTTP scraping. The extension lane is load-bearing, not a fallback. |

### Why `html` filters client-side (Decision 9)

Verified discovery against live data showed the `html` lane dominates (~68% of verified sources), and that documented server-side filters are unreliable: Remotive's `search`/`category` params returned identical unfiltered results for every term, and RemoteOK's tag filter was loose. So every `html`-lane (and loose-`api`-lane) source records its real `poll_method` and ultramode **filters client-side over full text** — never relying on a `category=` or `search=` URL parameter to do the narrowing.

## Universal Backbone

The backbone is a small, curated, **occupation-agnostic, multi-country** set of sources that ships with the plugin and is always available, so even rare lanes (non-tech occupations, thin geographies) get coverage before any per-workspace niche discovery runs. National-board entries are resolved at build time by the workspace's `requirements.base_country` (the `{country}` placeholder in `endpoint`/`url` is filled then; if `base_country` is null the national-board entries are skipped, not guessed).

Task 3 (`_source-discovery`) ingests the JSON array below **verbatim** as the seed backbone, normalises slugs, fills `{country}` placeholders from `base_country`, then merges in per-workspace discovered sources. Each entry carries at least `{name, url, category, access_lane, endpoint, needs_key}`; `needs_key` is marked correctly per provider (keyless feeds are `false`; keyed APIs such as Adzuna are `true` and look their key up in `user-profile.json` `ultramode.api_keys`).

```json
[
  {
    "name": "RemoteOK",
    "url": "https://remoteok.com",
    "category": "remote-board",
    "access_lane": "api",
    "endpoint": "https://remoteok.com/api",
    "needs_key": false,
    "needs_slug": false,
    "poll_method": "GET the JSON feed; the first array element is a legal/metadata notice — skip it; filter the rest client-side by full text and posted date. Set a descriptive User-Agent.",
    "notes": "Whole-board remote feed, keyless. Remote-only — best for remote target geographies."
  },
  {
    "name": "Remotive",
    "url": "https://remotive.com",
    "category": "remote-board",
    "access_lane": "api",
    "endpoint": "https://remotive.com/api/remote-jobs",
    "needs_key": false,
    "needs_slug": false,
    "poll_method": "GET the JSON feed; iterate the jobs array. Do NOT pass search=/category= params — they return identical unfiltered results (Decision 9). Filter client-side over full text.",
    "notes": "Keyless remote-board JSON. Server-side filters unreliable — client-side filter mandatory."
  },
  {
    "name": "Arbeitnow",
    "url": "https://www.arbeitnow.com",
    "category": "aggregator",
    "access_lane": "api",
    "endpoint": "https://www.arbeitnow.com/api/job-board-api",
    "needs_key": false,
    "needs_slug": false,
    "poll_method": "GET the JSON feed; paginate via the returned links.next URL; filter client-side over full text and posted date.",
    "notes": "Keyless multi-country aggregator (EU-leaning). Part of the always-on backbone."
  },
  {
    "name": "Himalayas",
    "url": "https://himalayas.app",
    "category": "remote-board",
    "access_lane": "api",
    "endpoint": "https://himalayas.app/jobs/api",
    "needs_key": false,
    "needs_slug": false,
    "poll_method": "GET the JSON feed; iterate the jobs array; filter client-side over full text.",
    "notes": "Keyless remote-board JSON feed."
  },
  {
    "name": "Working Nomads",
    "url": "https://www.workingnomads.com",
    "category": "remote-board",
    "access_lane": "api",
    "endpoint": "https://www.workingnomads.com/api/exposed_jobs/",
    "needs_key": false,
    "needs_slug": false,
    "poll_method": "GET the JSON feed; iterate the jobs array; filter client-side over full text.",
    "notes": "Keyless remote-board JSON feed."
  },
  {
    "name": "Jobicy",
    "url": "https://jobicy.com",
    "category": "remote-board",
    "access_lane": "api",
    "endpoint": "https://jobicy.com/api/v2/remote-jobs?count=50",
    "needs_key": false,
    "needs_slug": false,
    "poll_method": "GET the keyless v2 JSON feed (add &geo=<region>&tag=<occupation> to narrow); or the RSS at https://jobicy.com/feed/job_feed which DOES honour job_types=contract,freelance + search_region. Filter client-side over full text; most jobType values are Full-Time so contract filtering happens at sweep time. Rate ~1/hour.",
    "notes": "Keyless remote-board JSON+RSS. Occupation-agnostic; verified live 2026-06-16."
  },
  {
    "name": "We Work Remotely",
    "url": "https://weworkremotely.com",
    "category": "remote-board",
    "access_lane": "rss",
    "endpoint": "https://weworkremotely.com/remote-jobs.rss",
    "needs_key": false,
    "needs_slug": false,
    "poll_method": "GET the RSS feed; one <item> per posting; dedupe by item GUID before extracting; filter client-side over title + body.",
    "notes": "Keyless RSS. Category-specific feeds exist but the all-jobs feed plus client-side filter is the robust default."
  },
  {
    "name": "Hacker News Who is Hiring",
    "url": "https://news.ycombinator.com",
    "category": "community",
    "access_lane": "api",
    "endpoint": "https://hn.algolia.com/api/v1/search_by_date?tags=comment,story_{whoishiring_id}&hitsPerPage=200",
    "needs_key": false,
    "needs_slug": false,
    "poll_method": "Resolve the current month's 'Ask HN: Who is hiring?' story id, then GET the Algolia comments endpoint; each top-level comment is one posting; filter client-side over full text.",
    "notes": "Keyless via the HN Algolia search API. Community lane; monthly thread."
  },
  {
    "name": "Adzuna",
    "url": "https://www.adzuna.com",
    "category": "aggregator",
    "access_lane": "api",
    "endpoint": "https://api.adzuna.com/v1/api/jobs/{country}/search/1?results_per_page=50&app_id={app_id}&app_key={app_key}",
    "needs_key": true,
    "needs_slug": false,
    "poll_method": "GET the country search endpoint ({country} led by base_country, e.g. 'gb', 'pt', 'nl'); supply app_id/app_key from ultramode.api_keys; paginate via the trailing page number in the path.",
    "notes": "Occupation-agnostic multi-country aggregator. Keyed — free tier needs an app_id/app_key pair. Country code in the path is resolved from base_country."
  },
  {
    "name": "Jooble",
    "url": "https://jooble.org",
    "category": "aggregator",
    "access_lane": "api",
    "endpoint": "https://{country}.jooble.org/api/{api_key}",
    "needs_key": true,
    "needs_slug": false,
    "poll_method": "POST a JSON body {keywords, location} to the keyed endpoint; {country} subdomain led by base_country; paginate via the page field.",
    "notes": "Keyed multi-country aggregator. Backbone fallback for thin geographies; key looked up in ultramode.api_keys."
  },
  {
    "name": "EURES (EU national board)",
    "url": "https://eures.europa.eu",
    "category": "national-board",
    "access_lane": "html",
    "endpoint": "https://europa.eu/eures/portal/jv-se/search?lang=en&app=2.18&country={country}",
    "needs_key": false,
    "needs_slug": false,
    "poll_method": "GET the search page for {country} from base_country; apply a client-side full-text filter over the rendered listings — do NOT trust the page's own search/category params (Decision 9).",
    "notes": "EU-wide national/public board, resolved by base_country. html lane: client-side filter mandatory. Skipped when base_country is null."
  }
]
```

## Curated lane seed (provenance-from-file, re-probed on use)

The Universal Backbone above is occupation-agnostic. The **curated lane seed** is the opposite: a small set of **lane-tagged**, version-controlled, already-verified sources that bootstrap the two categories a cold first-run cannot otherwise reach — `ats-provider` (no backbone entry; the ATS axis resolves *companies*, and `companies_to_target[]` is empty on a fresh workspace) and `freelance-marketplace` (no backbone entry; almost all login-walled). Full provenance for every entry lives in `../../docs/superpowers/specs/2026-06-16-phase-13-verified-sources-research.json` (each was probed live 2026-06-15/16).

**The never-fabricate invariant is preserved — read this before using the seed.** A seed is a **candidate, not an admission**. It is re-probed live (the ATS seed via `resolve_ats` below; the marketplace/feed seed via the §2 gates in `discovery-protocol.md`) **before** it enters a workspace `sources.json`, and it is written only with a fresh probe-time `verified_at`. A version-controlled, periodically-reverified seed list is **provenance-from-file — exactly like the Universal Backbone — and is NOT a violation of the Hard invariant.** What the invariant forbids is admitting a source the model *recalled* but did not probe; a seed that fails its live re-probe is **skipped or extension-routed, never written**.

**Genericity (CLAUDE.md hard rule).** Each seed carries `lane_tags`. A workspace resolves only the seeds whose `lane_tags` intersect its lane (from `segment` / `target_titles` / `cv_keywords`). The seed below covers the **Linux / platform / SRE / DevOps / IAM** lane; for any other lane (a doctor, a lawyer, a chef) the seed simply does not apply and discovery falls back to the live enumeration axes — chiefly the professional-body and web-search axes (`discovery-protocol.md` §1). The framework supports adding further lane seeds the same way (version-controlled + re-probed); it is not tech-only by design, only tech-seeded today.

### ATS seed — keyless company boards (bootstrap the watchlist when `companies_to_target` is empty)

Resolved through `resolve_ats` (below): the baked `slug` is the most-specific candidate, but the resolver still probes it live (`200 + jobs>0 + identity-check`) before admission. `freelance_friendly` is `false` across the ATS lane (employer boards are permanent-heavy); the value is **lane coverage**, and `contract_type` filtering happens at **sweep time**, not at admission.

| company | provider | slug | lane_tags | verified_at |
|---|---|---|---|---|
| Canonical | greenhouse | `canonical` | linux, platform, sre, remote | 2026-06-16 |
| Grafana Labs | greenhouse | `grafanalabs` | platform, sre, observability, remote | 2026-06-16 |
| GitLab | greenhouse | `gitlab` | platform, sre, infra, remote | 2026-06-16 |
| N26 | greenhouse | `n26` | iam, idm, sre, fintech | 2026-06-16 |
| Datadog | greenhouse | `datadog` | platform, sre, observability | 2026-06-16 |
| Adyen | greenhouse | `adyen` | platform, sre, infra, fintech, nl | 2026-06-16 |
| Elastic | greenhouse | `elastic` | platform, infra, observability, remote | 2026-06-16 |
| Catawiki | greenhouse | `catawiki` | platform, infra, nl | 2026-06-16 |
| Trivago | greenhouse | `trivago` | devops, infra, dach | 2026-06-16 |
| Vercel | greenhouse | `vercel` | platform, infra, remote | 2026-06-16 |
| Mollie | ashby | `mollie` | platform, infra, nl | 2026-06-16 |
| Bitvavo | ashby | `bitvavo` | platform, infra, nl | 2026-06-16 |
| Recharge | ashby | `recharge` | infra, data | 2026-06-16 |
| Wise | smartrecruiters | `Wise` | platform, infra, fintech, uk | 2026-06-16 |

**Identity check (defeat slug collisions).** A `200 + jobs>0` is not enough — a generic slug can resolve to the wrong employer (e.g. greenhouse `bird`). On a hit, verify the board's identity: the company name in a posting's `company`/`location`/`absolute_url` host plausibly matches the seed company. Only then cache and admit; otherwise treat as a miss and continue.

### Freelance-marketplace beachhead (applies when `contract_type` includes `freelance`)

`extension` where login-walled (retained, never dropped — see the Gate A login-wall rule in `discovery-protocol.md` §2), `html` where the listings are publicly readable. Each is re-probed before admission.

| name | url | access_lane | needs_key | lane_tags | verified_at |
|---|---|---|---|---|---|
| Malt | https://www.malt.com/ | extension | false | freelance, eu, devops, sre | 2026-06-16 |
| YunoJuno | https://www.yunojuno.com/ | extension | false | freelance, uk, eu | 2026-06-16 |
| Worksome | https://www.worksome.com/ | extension | false | freelance, uk, eu, nordics | 2026-06-16 |
| Braintrust | https://www.usebraintrust.com/jobs | html | false | freelance, infra, devops | 2026-06-16 |
| hackajob | https://hackajob.com/talent/devops-jobs | html | false | freelance, uk, eu, sre, platform | 2026-06-16 |
| IT-Contracts.nl | https://www.it-contracts.nl/ | html | false | freelance, nl, zzp, devops | 2026-06-16 |
| freelance.nl | https://www.freelance.nl/ | extension | false | freelance, nl, zzp, devops, linux | 2026-06-16 |
| Freep.nl | https://www.freep.nl/ | extension | false | freelance, nl, zzp, iam, devops | 2026-06-16 |
| freelancermap | https://www.freelancermap.com/it-projects.html | html | false | freelance, eu, infra, ci | 2026-06-16 |
| Toptal | https://www.toptal.com/ | extension | false | freelance, global, devops | 2026-06-16 |
| Lemon.io | https://lemon.io/ | extension | false | freelance, eu, devops | 2026-06-16 |

### Lane-specific keyless-feed seed (tech lanes)

Keyless feeds too niche to be occupation-agnostic backbone, but high-signal for this lane. Added as discovery candidates (still §2-probed):

| name | category | access_lane | endpoint | lane_tags |
|---|---|---|---|---|
| JustJoin.it | national-board | api | `https://api.justjoin.it/v2/user-panel/offers/by-cursor?orderBy=DESC&sortBy=published&perPage=100` | devops, sre, eu, b2b-contract |
| Landing.jobs | national-board | api | `https://landing.jobs/api/v1/jobs?type=remote` | platform, sre, eu, contractor |
| kube.careers | community | html | `https://kube.careers/remote-kubernetes-jobs` | kubernetes, sre, platform |
| Arc.dev | remote-board | html | `https://arc.dev/remote-jobs/devops` | devops, sre, freelance |
| web3.career | aggregator | html | `https://web3.career/devops-jobs` | devops, sre, web3 |

## ATS slug resolver (probe-and-cache)

ATS providers (Greenhouse, Lever, Ashby, Workable, Recruitee, Personio, SmartRecruiters, Workday) are **keyless but per-company** — each query needs a board **slug** identifying one employer. The watchlist of companies auto-seeds from the tracker's A/B-tier employers plus `requirements.companies_to_target[]` plus manual additions **plus the lane-matching entries of the § Curated lane seed → ATS seed** (so a cold first-run with an empty `companies_to_target` still resolves a real ATS lane instead of leaving the category dark). For each company we must resolve `company → {provider, board}` by probing the keyless endpoints, then **cache the result** in `.job-scout/cache/ats-slugs.json`. On a miss, fall back to the extension lane (browse the company's careers page in the logged-in browser). A curated-seed entry already names its `provider`/`slug`, so the resolver probes that pair **first** (still live, still identity-checked) before deriving candidates.

### Real keyless endpoint patterns (probe URLs)

`<slug>` is the candidate board slug; a 200 with a non-empty job array means a hit.

| Provider | Probe URL pattern | Hit signal |
|---|---|---|
| `greenhouse` | `https://boards-api.greenhouse.io/v1/boards/<slug>/jobs` | 200 + JSON `jobs[]` non-empty |
| `lever` | `https://api.lever.co/v0/postings/<slug>?mode=json` | 200 + JSON array non-empty |
| `ashby` | `https://api.ashbyhq.com/posting-api/job-board/<slug>` | 200 + JSON `jobs[]` non-empty |
| `workable` | `https://apply.workable.com/api/v3/accounts/<slug>/jobs` | 200 + JSON `results[]` non-empty |
| `recruitee` | `https://<slug>.recruitee.com/api/offers` | 200 + JSON `offers[]` non-empty |
| `personio` | `https://<slug>.jobs.personio.de/xml` | 200 + XML `<position>` non-empty |
| `smartrecruiters` | `https://api.smartrecruiters.com/v1/companies/<slug>/postings` | 200 + JSON `content[]` non-empty |
| `workday` | `https://<slug>.wd1.myworkdayjobs.com/wday/cxs/<slug>/<tenant>/jobs` | 200 + JSON `jobPostings[]` non-empty (tenant guessed; extension fallback if unknown) |

### Slug candidate derivation

From a company display name, derive an ordered list of candidate slugs (charset `[a-z0-9-]`, no underscores; see `canonical-schemas.md`):

```
function slugify(s):
    s = lowercase(s)
    s = replace every run of [^a-z0-9-] with "-"
    s = compress repeated "-" into a single "-"
    s = trim leading/trailing "-"
    return s

function candidate_slugs(company_name):
    base = slugify(company_name)                       # "Miro Inc." -> "miro-inc"
    candidates = ordered, de-duplicated:
        base                                           # "miro-inc"
        base with trailing "-inc"/"-ltd"/"-gmbh"/"-bv"/
              "-llc"/"-corp"/"-co"/"-group" stripped   # "miro"
        slugify(first whitespace token of company)     # "miro"
        base with all "-" removed                      # "miroinc"
    return candidates                                   # most-specific first
```

### Probe-and-cache algorithm

```
CACHE = ".job-scout/cache/ats-slugs.json"   # { "<company-lower>": {provider, board, verified_at} | {miss:true, checked_at} }

function resolve_ats(company_name):
    key = lowercase(company_name)
    cache = load_json(CACHE) or {}

    # 1. Cache hit (positive) — return immediately
    if cache[key] exists and not cache[key].miss:
        return { provider: cache[key].provider, board: cache[key].board }

    # 2. Recent negative cache — skip re-probing for a cooldown window
    if cache[key] exists and cache[key].miss and age(cache[key].checked_at) < 30 days:
        return EXTENSION_FALLBACK            # caller browses careers page via extension

    # 3. Probe each provider with each candidate slug, most-specific slug first.
    #    Provider order follows canonical preference / market share.
    PROVIDERS = [greenhouse, lever, ashby, workable, recruitee,
                 personio, smartrecruiters, workday]
    #    A curated-seed company supplies its own (provider, slug) — probe that FIRST.
    probe_list = seed_pair_first(company_name, candidate_slugs(company_name), PROVIDERS)
    for (provider, slug) in probe_list:
        url = probe_url(provider, slug)                # table above
        resp = WebFetch(url)                            # read-only HTTP GET, carve-out
        if resp.status == 200 and hit_signal(provider, resp):
            if not identity_ok(company_name, resp):     # defeat slug collisions (e.g. greenhouse 'bird')
                continue                                # wrong employer — keep probing, do not admit
            cache[key] = { provider: provider, board: slug,
                           verified_at: now_iso() }
            save_json(CACHE, cache)
            return { provider: provider, board: slug }

    # 4. Miss — record a negative entry (cooldown) and fall back to the extension.
    cache[key] = { miss: true, checked_at: now_iso() }
    save_json(CACHE, cache)
    return EXTENSION_FALLBACK
```

Notes for the implementer: probe most-specific slug first to avoid a generic slug matching the wrong employer; stop at the first hit (do not enumerate all providers once one matches); honour each provider's rate limits and set a descriptive User-Agent; the negative-cache cooldown (30 days) keeps repeat sweeps cheap without permanently writing off a company that later adopts an ATS. **`seed_pair_first(company, slugs, providers)`** yields the curated seed's own `(provider, slug)` ahead of the derived `(slug × provider)` grid when the company is in the § Curated lane seed → ATS seed, else just the grid. **`identity_ok(company, resp)`** confirms a `200 + jobs>0` board actually belongs to the intended employer (company name appears in a posting's `company`/`location`/`absolute_url` host) — a hit that fails the identity check is **not** admitted; the resolver keeps probing. This is what keeps a baked seed slug honest: the slug is a candidate, the live probe + identity check is the admission.

## Adaptive priority order (Decision 5)

`sources.json` carries a `priority_order[]` — the order the engine polls sources in (lower polls first; see `canonical-schemas.md` § `sources.json`). Discovery (Task 3, `_source-discovery`) writes a **static default** at build time, ordered by canonical preference (`ats-provider` first, then remote/national board, then aggregator, then community, then `freelance-marketplace` last). That default is right for a permanent job hunt — but **wrong** for a freelance + remote one, where an employer's own ATS is the *least* likely place a contract gig surfaces.

So `priority_order` is **not hardcoded**: ultramode **derives** it from the workspace's `requirements` each run, reading three fields (`canonical-schemas.md` § `user-profile.json` `requirements`):

- **`contract_type`** — `["freelance"]`, `["permanent"]`, or both.
- **`work_arrangement`** — whether `"remote"` is present.
- **`location_preferences`** — used as a tie-breaker (a remote-board source that covers the user's geography polls ahead of one that does not).

### Derivation rule

```
function derive_priority_order(requirements, sources):
    freelance = "freelance" in requirements.contract_type
    permanent = "permanent" in requirements.contract_type
    remote    = "remote" in requirements.work_arrangement

    if freelance and remote and not permanent:
        # Freelance + remote: contract gigs surface on remote boards,
        # contract-capable aggregators and freelance marketplaces first;
        # an employer ATS is the LEAST likely place a gig appears, so it
        # drops to second band and is contract-filtered when swept.
        bands = [
            [remote-board sources covering location_preferences],
            [remote-board sources (other), aggregator sources (contract-capable)],
            [freelance-marketplace sources],
            [ats-provider sources],         # ATS contract-filtered — lower priority for freelance+remote
            [community, national-board sources],
        ]
    elif permanent and not freelance:
        # Permanent: the employer's own ATS is the highest-signal,
        # direct-to-employer listing — ATS-first.
        bands = [
            [ats-provider sources],          # ATS-first
            [remote-board sources, national-board sources],
            [aggregator sources],
            [community sources],
            [freelance-marketplace sources], # last
        ]
    else:
        # Mixed (both contract_type values, or remote unset): keep the
        # canonical-preference static default discovery already wrote.
        bands = canonical_preference_default(sources)

    # Flatten bands in order; within a band keep discovery's existing
    # `priority` as the stable tie-break. Result is the source NAMES in
    # poll order — written back to sources.json priority_order[].
    return [s.name for band in bands for s in stable_sort(band, key=priority)]
```

The two named orderings, stated explicitly:

- **Freelance + remote** → remote-board + contract-capable aggregator + freelance-marketplace **first**; ATS **second** (contract-filtered when swept). Not ATS-first.
- **Permanent** → **ATS-first** (direct-to-employer), then boards, then aggregators, freelance-marketplace last.

**Where it runs.** The sweep dispatcher (`/ultramode`, Task 7) calls `derive_priority_order` against the workspace `requirements` and the registry's `sources[]` at the start of a run, **before** fanning out `_source-sweep` dispatches, and uses the result as the fan-out order. `_source-sweep` consumes the order it is dispatched in (one source per dispatch — it never re-derives the order itself). This reference is the spec the command reads; **deriving the order is a reference-level rule, not a per-command edit** — no command file hardcodes either ordering.

## Cross-source dedupe + canonical preference (Decision 6)

The same role often surfaces on several sources. Ultramode reuses the existing repost fingerprint from `linkedin-search.md` and extends it **across** sources.

### Fingerprint

```
fingerprint = lower(company) | "|" | lower(title) | "|" | normalise_location(location)
```

**Location normalisation rule** (applied before fingerprinting, so trivial location wording differences collapse to one key):

```
function normalise_location(loc):
    loc = lowercase(trim(loc))
    if loc matches /remote|anywhere|distributed|work from home|wfh/:
        return "remote"
    drop a leading postcode/ZIP token
    drop common country suffixes after the last comma when a city is present
        (e.g. "Lisbon, Portugal" -> "lisbon"; "London, UK" -> "london")
    collapse internal whitespace to single spaces
    strip accents (é -> e) and any [^a-z0-9 ] characters
    return the result
```

Two postings with the same fingerprint are treated as **one job seen on multiple sources**, not two jobs (consistent with the per-source-unique ID rule in `canonical-schemas.md` — the IDs differ; the fingerprint unifies them).

### Canonical selection

On a fingerprint collision, choose the **canonical "apply here" entry** by direct-to-employer preference:

```
ATS  >  LinkedIn  >  aggregator  >  marketplace
```

(`ats-provider` category wins; then the LinkedIn lane; then `aggregator`/`remote-board`/`national-board`/`community`; then `freelance-marketplace` last.) The canonical entry's URL is the row's "apply at source" link. All other hits are **retained** on the canonical entry as `also_seen_on[]` (one entry per other source — the loser's structured `source` object `{lane, provider, board}`, the same shape the `ultramode` view's `source_chip()` macro renders), surfaced in the unified view as "also seen on N sources."

### Where canonical selection runs — dispatcher merge time (cross-source step)

The preference order above is applied **across** sources, but **one `_source-sweep` only ever sees one source** — it cannot know that the same fingerprint will also arrive from a different sweep. So **a single sweep never picks the canonical winner or writes `also_seen_on[]`.** Per `_source-sweep`'s Stage 2, a sweep only drops a candidate whose fingerprint is already in `known_fingerprints[]` (i.e. already in the tracker); it does **not** see another sweep's still-in-flight deltas. The cross-source winner is chosen one level up, by the **dispatcher** (`/ultramode`, Task 7), at **merge time**, when it folds the per-source deltas into the single in-memory tracker (the serial, single-writer merge in `_source-sweep` § Tracker coordination).

The merge-time algorithm, run once per incoming delta as the dispatcher reconciles fan-in:

```
function merge_delta_into_tracker(delta, tracker):
    fp = delta.fingerprint
    existing = tracker.find_by_fingerprint(fp)     # already-merged entry, if any

    if existing is None:
        tracker.add(delta)                          # first sighting → it is canonical (for now)
        return

    # Fingerprint collision across sources → pick the canonical winner by the
    # ATS > LinkedIn > aggregator > marketplace preference (the table above).
    # Do NOT redefine that order here — apply it.
    winner, loser = order_by_canonical_preference(existing, delta)

    # The winner is the canonical "apply here" entry; the loser becomes a
    # sighting recorded on the winner's also_seen_on[].
    if winner is delta:                             # the new delta outranks the merged entry
        delta.also_seen_on = existing.also_seen_on + [ sighting(existing) ]
        tracker.replace(existing.id, with=delta)    # swap canonical, carry sightings forward
    else:                                           # the merged entry stays canonical
        winner.also_seen_on.append(sighting(loser))

    # sighting(x) = x.source   # the loser's structured {lane, provider, board}; source_chip() renders the label
```

Two consequences make this single-writer-safe: (1) because the dispatcher merges deltas **serially** (no two sweeps write at once), every collision is resolved deterministically against the already-merged entry; (2) because the loser is **retained** as an `also_seen_on[]` sighting and never re-fetched (its JD was already filtered out, or is simply dropped), the merge costs no extra token spend. `_source-sweep` is the producer of the per-source deltas; **this merge-time selection is the consumer that turns N same-fingerprint deltas into one canonical entry + `also_seen_on[]`.**

A runnable fixture proving this rule — three same-fingerprint jobs from `ats`, `linkedin`, `aggregator` lanes resolving to the `ats` canonical with the other two on `also_seen_on[]` — lives at `examples/ultramode-dedupe-example.json` alongside this reference.

### ATS-backed JD enrichment

When an **aggregator** (or any non-ATS source) wins a collision whose canonical resolves to an **employer ATS**, fetch the **full JD from the ATS** (its `api`-lane JSON carries the complete description) rather than scoring on the aggregator's truncated text. This prevents scoring being starved by short aggregator snippets. The ATS JD is what gets stored under `jds/<id>.txt` for the canonical entry.

## Key handling (D7) — keyless-first, never in a browser form

Most of the taxonomy is **keyless**: every ATS-lane probe (Greenhouse, Lever, Ashby, …), every keyless backbone feed (RemoteOK, Remotive, Arbeitnow, Himalayas, Working Nomads, We Work Remotely, HN Who-is-hiring), and the `html`/`rss` lanes all run with **zero API keys**. **Keyless-first is the rule: ultramode runs a full sweep on a fresh workspace with no keys at all.** Only a few keyed aggregators (`needs_key: true` — Adzuna, Jooble) require a token.

Where keys live and how they flow:

- **Storage.** Keys live in `user-profile.json` under `ultramode.api_keys` — a `{ "<provider-slug>": "<token>" }` map (canonical-schemas § `user-profile.json` `ultramode`). This is **gitignored workspace state**; keys are never committed, never written to `config.json`, never written to `sources.json` (the registry only marks `needs_key: true`).
- **Entry.** Keys are added/removed **only** via `/config ultramode key <provider> <token>` / `--remove` (the candidate pastes the token into the terminal). **A key is NEVER entered into a browser form** — ultramode does not type tokens into any web page the Chrome extension is driving (Hard Rule on sensitive data: SSN, bank details, passwords, and API keys never go into a browser form).
- **Lookup.** The dispatcher (`/ultramode`, Task 7) reads `ultramode.api_keys` and passes **only** the key a given `needs_key` source requires into that source's `_source-sweep` envelope (`api_keys`), looked up by provider slug. Keys are never logged or echoed back to the candidate.
- **Prompt + graceful skip.** When discovery flags a keyed aggregator that **materially** helps the lane, the dispatcher prompts **inline** with the signup link, once. If the candidate declines, or the key is simply absent from `ultramode.api_keys`, the dispatcher **gracefully skips** that source — never blocks the run — and records `Skipped <provider> (no API key)` in the report so the candidate sees what was not searched and can add the key later via `/config`.
- **`ultramode.default`.** The `/config ultramode default <true|false>` toggle (default `false`) controls whether ultramode runs without re-prompting; it lives in the same `ultramode` block.

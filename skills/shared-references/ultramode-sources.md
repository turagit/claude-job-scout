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
| `html` | Read-only HTTP `GET` the listing page, then **apply a client-side full-text filter** over title + tags + body. **Never trust the source's documented `category=` / `search=` query parameters** — verified discovery found free-feed server-side filters return identical, unfiltered results for every term (Decision 9). Filter client-side or you ingest noise. Uses the `WebFetch` carve-out. |
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

## ATS slug resolver (probe-and-cache)

ATS providers (Greenhouse, Lever, Ashby, Workable, Recruitee, Personio, SmartRecruiters, Workday) are **keyless but per-company** — each query needs a board **slug** identifying one employer. The watchlist of companies auto-seeds from the tracker's A/B-tier employers plus `requirements.companies_to_target[]` plus manual additions. For each company we must resolve `company → {provider, board}` by probing the keyless endpoints, then **cache the result** in `.job-scout/cache/ats-slugs.json`. On a miss, fall back to the extension lane (browse the company's careers page in the logged-in browser).

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
    for slug in candidate_slugs(company_name):
        for provider in PROVIDERS:
            url = probe_url(provider, slug)            # table above
            resp = WebFetch(url)                        # read-only HTTP GET, carve-out
            if resp.status == 200 and hit_signal(provider, resp):
                cache[key] = { provider: provider, board: slug,
                               verified_at: now_iso() }
                save_json(CACHE, cache)
                return { provider: provider, board: slug }

    # 4. Miss — record a negative entry (cooldown) and fall back to the extension.
    cache[key] = { miss: true, checked_at: now_iso() }
    save_json(CACHE, cache)
    return EXTENSION_FALLBACK
```

Notes for the implementer (Task 4): probe most-specific slug first to avoid a generic slug matching the wrong employer; stop at the first hit (do not enumerate all providers once one matches); honour each provider's rate limits and set a descriptive User-Agent; the negative-cache cooldown (30 days) keeps repeat sweeps cheap without permanently writing off a company that later adopts an ATS.

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

(`ats-provider` category wins; then the LinkedIn lane; then `aggregator`/`remote-board`/`national-board`/`community`; then `freelance-marketplace` last.) The canonical entry's URL is the row's "apply at source" link. All other hits are **retained** on the canonical entry as `also_seen_on[]` (one entry per other source — name + url + lane), surfaced in the unified view as "also seen on N sources."

### ATS-backed JD enrichment

When an **aggregator** (or any non-ATS source) wins a collision whose canonical resolves to an **employer ATS**, fetch the **full JD from the ATS** (its `api`-lane JSON carries the complete description) rather than scoring on the aggregator's truncated text. This prevents scoring being starved by short aggregator snippets. The ATS JD is what gets stored under `jds/<id>.txt` for the canonical entry.

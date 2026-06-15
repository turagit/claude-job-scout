---
name: _source-sweep
description: >
  [Internal subagent — dispatched only by /ultramode (the multi-source sweep
  orchestrator), one dispatch per source; not user-invocable]
  Internal subagent skill. Sweeps ONE verified `sources.json` source for a
  workspace: collects candidate IDs/fingerprints first, dedupes them against the
  tracker snapshot the dispatcher passed in (and the cross-source fingerprint
  rule), fetches the full JD only for genuinely-new roles, persists each new JD
  to `jds/<namespaced-id>.txt`, sets the structured `source` + namespaced id on
  the new entry, and returns delta-only new roles for the dispatcher to score and
  merge. Honours the source's access lane (api / rss / html / extension) and
  poll method. Never re-fetches a known role. Not user-invocable.
version: 0.1.0
---

# Source Sweep (Subagent)

Sweep **one** verified job source — an entry from `.job-scout/sources.json` — and return only the **genuinely-new** roles, JD-fetched and tracker-ready, for the dispatcher to score and persist. The big win this skill exists to protect is **dedupe-before-extract** (Hard Rule #2): collect candidate identifiers first, filter them against the tracker the dispatcher already loaded, and fetch a JD only for what survives. Fetching JDs for roles already in the tracker is the single largest avoidable token cost in multi-source ultramode — this skill is built so that cost never happens.

**This skill is dispatched only by other skills, via the `Agent` tool, per `../shared-references/subagent-protocol.md`.** It is not user-invocable. **One sweep dispatch handles exactly one source** — the dispatching command (`/ultramode`, Task 7) fans out one `_source-sweep` per entry in `sources.json`, in parallel, then merges the returned deltas serially.

## Tracker coordination (read this before anything else)

The dispatching command owns the tracker; this subagent never writes it. The contract:

1. **The command loads `.job-scout/tracker.json` ONCE**, at the start of the whole multi-source run, before any sweep is dispatched.
2. From that single read it derives the **candidate-fingerprint set** — every non-`rejected` tracker entry's `id`, plus its cross-source fingerprint (`lower(company)|lower(title)|normalise_location(location)`, per `../shared-references/ultramode-sources.md` § Cross-source dedupe) — and passes that set **into every sweep's input envelope** (`known_ids[]`, `known_fingerprints[]`).
3. **Each sweep returns delta-only new roles.** A subagent never re-emits a role already represented by `known_ids` / `known_fingerprints`, and never re-emits unchanged fields of anything (per the subagent protocol's delta-return rule).
4. **The command merges the deltas serially** — one sweep's deltas at a time — into the in-memory tracker, then writes the tracker once at the end (atomic-rename, `../shared-references/state-validators.md`). **There are no concurrent tracker writes.** Two sweeps that surface the same fingerprint are reconciled at merge time by the dispatcher — it picks the canonical winner by cross-source preference and records the loser on `also_seen_on[]` (the merge-time algorithm in `../shared-references/ultramode-sources.md` § Where canonical selection runs — dispatcher merge time), not by the subagents racing to write. A single sweep cannot do this: it only sees its own source, never another sweep's in-flight deltas.

This is why the subagent's `allowed_tools` grants `Write` (for JD blobs only) but the subagent has no access to `tracker.json`: state coordination is single-writer by construction.

## Input shape

The dispatcher passes a single JSON envelope (per `subagent-protocol.md`) describing exactly one source plus the tracker snapshot:

```json
{
  "task": "sweep-source",
  "inputs": {
    "source": {
      "name": "RemoteOK",
      "url": "https://remoteok.com",
      "category": "remote-board",
      "access_lane": "api",
      "endpoint": "https://remoteok.com/api",
      "needs_key": false,
      "needs_slug": false,
      "poll_method": "GET the JSON feed; skip element 0 (legal notice); filter client-side over full text and posted date. Set a descriptive User-Agent.",
      "notes": "Whole-board remote feed, keyless."
    },
    "lane_keywords": ["devops", "sre", "platform engineer", "kubernetes", "terraform", "site reliability"],
    "not_terms": ["intern", "graduate", "unpaid"],
    "freshness_window_days": 7,
    "known_ids": ["4012345678", "greenhouse__miro__4012345"],
    "known_fingerprints": ["miro|platform engineer|remote", "acme|sre|lisbon"],
    "ats_watchlist": [
      { "company": "Miro", "tier": "A" },
      { "company": "Acme Robotics", "tier": "target" }
    ],
    "api_keys": { "adzuna": "app_id:app_key" }
  },
  "budget_lines": 200,
  "allowed_tools": ["Read", "Grep", "Write", "WebFetch"]
}
```

- `source` is **one** `sources.json` entry verbatim (its `access_lane` and `poll_method` drive everything below).
- `lane_keywords[]` + `not_terms[]` are the workspace lane's relevance terms (derived from `segment` / `target_titles` / `master_keyword_list`), used for the **client-side full-text filter** on `html`/feed lanes.
- `known_ids[]` + `known_fingerprints[]` are the tracker snapshot the command loaded once (see § Tracker coordination). They are the dedupe set — **read-only** here.
- `ats_watchlist[]` is supplied **only for `ats-provider` sources** (the seed companies; see § ATS watchlist).
- `api_keys` carries any key this source's `needs_key` requires (looked up by the dispatcher from `user-profile.json` `ultramode.api_keys`); absent/empty for keyless sources.
- `allowed_tools` is exactly `["Read", "Grep", "Write", "WebFetch"]`: `WebFetch` for the read-only public `GET` (the carve-out in `../shared-references/browser-policy.md`), `Write` **only** for JD blobs under `jds/`, `Read`/`Grep` to load the ATS-slug cache and reference material. **No tracker write tool** — the dispatcher is the single writer.

## Output shape (delta-return)

A single JSON envelope. `deltas` carry **only genuinely-new** roles — already tracker-ready (structured `source`, namespaced `id`, `jd_path` pointing at the blob this subagent wrote):

```json
{
  "status": "ok",
  "deltas": [
    {
      "id": "remoteok__remoteok__998877",
      "url": "https://remoteok.com/remote-jobs/998877",
      "title": "Senior Platform Engineer",
      "company": "Globex",
      "location": "Remote",
      "source": { "lane": "remote-board", "provider": "remoteok", "board": "remoteok" },
      "jd_path": "jds/remoteok__remoteok__998877.txt",
      "posted_at": "2026-06-14",
      "fingerprint": "globex|senior platform engineer|remote",
      "tags": ["kubernetes", "terraform", "aws"]
    }
  ],
  "errors": [
    { "code": "source_unreachable", "message": "RemoteOK /api returned 503; no candidates collected this sweep." }
  ],
  "continuation_cursor": null
}
```

- Every delta entry is a **new** role only. A role whose `id` is in `known_ids`, or whose `fingerprint` is in `known_fingerprints`, is **never** in `deltas` (it was filtered before any JD fetch). No prose outside the JSON envelope; no re-emission of input data.
- `id` is the **namespaced external id** `<provider>__<board>__<externalid>` (LinkedIn IDs stay bare, but this subagent never sweeps LinkedIn — that is the extension/`/job-search` surface). `jd_path` is `jds/<namespaced-id>.txt`, the blob this subagent already wrote.
- `source` is the structured `{lane, provider, board}` object (canonical-schemas § Structured `source`): `lane` = the source's `category`, `provider`/`board` = its slugs.
- `status: "partial"` + a `continuation_cursor` when the source's pagination cannot be drained within `budget_lines`; the dispatcher re-dispatches with the cursor.
- Scoring is **not** done here — the dispatcher hands `deltas` to `_job-matcher`/`_gate-engine` after fan-in (§ Score). The subagent returns metadata + `jd_path` only.

## Engine — dedupe BEFORE extract (Hard Rule #2, non-negotiable ordering)

The same four-stage shape `linkedin-search.md` uses for LinkedIn, applied to one external source. **The ordering is load-bearing: collect identifiers first, dedupe, and only then fetch any JD. A JD fetch must never precede the dedupe filter.**

### Stage 1 — collect candidate IDs / fingerprints FIRST (no JD fetch yet)

Poll the source by its `access_lane` and read only the **list-level** fields needed to identify and fingerprint each candidate — id, title, company, location, posted date, tags, and the listing URL. **Do not fetch any per-role JD page in this stage.** Per lane:

- **`api`** — read-only `WebFetch` `GET` of `endpoint`; parse the JSON; iterate the listing array per `poll_method` (e.g. skip RemoteOK's element-0 legal notice; paginate Arbeitnow via `links.next`; supply `api_keys` when `needs_key`). Each array element is one candidate; its id, title, company, location, tags come straight from the JSON.
- **`rss`** — read-only `WebFetch` `GET` of the feed; parse the XML; **dedupe by item GUID** as you read (one `<item>`/`<entry>` per posting); the GUID is the candidate's external id.
- **`html`** — read-only `WebFetch` `GET` of the listing page; parse the rendered listings into candidates (title + tags + the listing URL + any inline snippet). The **client-side full-text filter** (§ Client-side filter) runs here, on this list-level text, before extraction.
- **`extension`** — login-walled source: per Hard Rule #1 + `browser-policy.md`, this lane is a logged-in Chrome-extension sweep and **does not run inside this subagent** (subagents get no browser tools). For an `extension`-lane source the subagent returns `status: "ok"` with empty `deltas` and an `errors[]` note (`code: "extension_lane_deferred"`) so the dispatcher runs that source on the main thread via the extension, following dedupe-before-extract there.

Compute each candidate's cross-source `fingerprint = lower(company)|lower(title)|normalise_location(location)` (the rule in `../shared-references/ultramode-sources.md` § Cross-source dedupe; `normalise_location` collapses remote synonyms and trims country suffixes). Build a candidate list of `{external_id, namespaced_id, title, company, location, posted_at, tags, url, fingerprint}` — **identifiers only, still no JD text.**

### Stage 2 — filter candidates BEFORE any extract

Drop every candidate that is already known, against the snapshot the dispatcher passed in. This filter runs **before** Stage 3's JD fetch — that ordering is the whole point of the skill:

1. **By namespaced id:** drop any candidate whose `namespaced_id` (`<provider>__<board>__<externalid>`) is in `known_ids[]`.
2. **By cross-source fingerprint:** drop any surviving candidate whose `fingerprint` is in `known_fingerprints[]` — this is the same role already seen on LinkedIn or another source (Decision 6). It is **not** re-fetched or re-scored; the dispatcher records the additional sighting as an `also_seen_on[]` hit on the canonical entry at **merge time** — this sweep never picks the canonical winner itself, because it only sees one source (see `../shared-references/ultramode-sources.md` § Where canonical selection runs — dispatcher merge time; worked fixture in `examples/ultramode-dedupe-example.json`).
3. **Within this sweep:** if two candidates from this same source share a fingerprint, keep the first and drop the rest.

Only the candidates that survive both filters are "genuinely new". Everything dropped here never reaches a JD fetch.

### Stage 3 — extract: fetch the JD ONLY for genuinely-new roles

For each surviving (genuinely-new) candidate only:

- **`api`/`rss`** — the JD usually rides in the same feed payload (the `description`/`content` field). Use it. Only when the feed carries a truncated snippet do an extra read-only `WebFetch` of the role's own detail URL for the full text. **ATS-backed enrichment:** when this source is a non-ATS aggregator/board whose role resolves to an employer ATS, prefer the ATS's full JD over the aggregator's truncated text (Decision 6, § Cross-source dedupe) — fuller text means the scorer is not starved.
- **`html`** — read-only `WebFetch` the role's detail page for the full description.

### Stage 4 — persist the JD blob + build the tracker-ready delta

For each genuinely-new role, write the JD blob, then emit the delta entry:

1. **Write `jds/<namespaced-id>.txt`** via the `write_jd()` contract in `../shared-references/jd-storage.md` (temp-file + atomic `mv`; `<provider>__<board>__<externalid>.txt`). This is the only `Write` this subagent performs.
2. Build the delta entry with the **namespaced `id`**, the structured **`source: {lane: <category>, provider: <slug>, board: <slug>}`**, `jd_path: "jds/<namespaced-id>.txt"`, the list-level metadata, the `fingerprint`, and up to 5 `tags`. No `tier`/`dimensions` — scoring is the dispatcher's downstream step.

Return all delta entries in one envelope. The dispatcher merges them serially into the single in-memory tracker and writes once.

## Client-side filter (Decision 9) — `html` and feed lanes

For `html` sources, and for any `api`/`rss` feed whose server-side filters are unreliable, **filter to lane relevance client-side over the full text** — title + tags + description/snippet concatenated, matched against `lane_keywords[]` (a role is in-lane if it hits any lane keyword) with `not_terms[]` excluded. **Do NOT rely on the source's documented `category=` / `search=` query parameters** — verified discovery found those free-feed server-side filters return identical, unfiltered results for every term (RemoteOK's tag filter is loose; Remotive's `search`/`category` are no-ops). Trusting them ingests noise; client-side full-text filtering is the only robust narrowing. Also drop candidates outside `freshness_window_days` by posted date. This filter runs in **Stage 1** (on list-level text), so out-of-lane roles never reach a JD fetch.

## ATS watchlist auto-seed (Decision 9) + cold-start — `ats-provider` sources

`ats-provider` sources are keyless but **per-company**: each query needs one employer's board slug. The dispatcher builds the **watchlist** and passes it in `ats_watchlist[]`; this subagent resolves each company to a board and sweeps it.

### Building the watchlist (the dispatcher does this; documented here for the contract)

The watchlist auto-seeds from three sources, unioned and de-duplicated case-insensitively:

1. **The tracker's A/B-tier employers** — every distinct `company` on a non-`rejected` tracker entry whose `tier` is `A` or `B`. These are the employers this workspace already rates highly; their own boards are the highest-signal ATS lane.
2. **`requirements.companies_to_target[]`** — the user's explicitly named target employers (from `user-profile.json`).
3. **Manual additions** — any companies the user added to the watchlist directly.

### Cold-start

With **fewer than 1 A/B-tier employer** in the tracker (a fresh workspace that has not yet run LinkedIn sweeps), there is nothing to harvest from tier history. In that case **seed the watchlist from `requirements.companies_to_target[]` only**, and note in `errors[]` (`code: "ats_watchlist_coldstart"`) that the watchlist will **enrich automatically after LinkedIn sweeps populate the tracker** with tiered employers. Do not block, and never fabricate target companies to pad an empty watchlist.

### Resolving each watchlist company to a board

For each `ats_watchlist[]` company, call the **probe-and-cache `resolve_ats`** routine in `../shared-references/ultramode-sources.md` § ATS slug resolver:

- Derive candidate slugs (most-specific first), probe the keyless provider endpoints (Greenhouse, Lever, Ashby, Workable, Recruitee, Personio, SmartRecruiters, Workday) via read-only `WebFetch`, stop at the first hit, and **cache** the `company → {provider, board}` result in `.job-scout/cache/ats-slugs.json` (positive hits cached; misses negative-cached with a 30-day cooldown). Honour the cooldown — do not re-probe a recently-missed company.
- On a hit, the resolved board's listing endpoint is swept exactly like an `api`-lane source (Stages 1–4 above), with `provider`/`board` from the resolver. The ATS JSON carries the full JD, so Stage 3 uses it directly (no separate detail fetch).
- On a miss (`resolve_ats` returns the extension fallback), this subagent **cannot** browse the careers page (no browser tools); it records an `errors[]` entry (`code: "ats_unresolved"`, naming the company) so the dispatcher can queue an extension-lane sweep on the main thread. It does not guess a slug.

`resolve_ats`'s slug cache is the only state besides JD blobs this subagent writes — and it is a cache (`cache/ats-slugs.json`), not canonical tracker state.

## Score (done by the dispatcher after fan-in)

This subagent **does not score**. After fan-in, the dispatcher hands the genuinely-new roles to the existing scorer, unchanged:

- `_gate-engine` runs first on each new role (against `requirements.deal_breakers[]` etc.); a non-empty `gate_violations` forces `tier: D` and skips dimension scoring.
- otherwise `_job-matcher` runs the v1 rubric, reading the JD from the `jd_path` this subagent wrote.
- Scoring is **batched per `subagent-protocol.md`** (batches of ≤5 by similarity), exactly as `/job-search` Step 4 and `/match-jobs` do — the multi-source roles join the same scoring fan-out, no special path. The scorer's contract is untouched by this skill.

## Budget

`budget_lines: 200`. If a source's pagination cannot be fully drained within budget, return `status: "partial"` with the genuinely-new roles collected so far in `deltas`, the pagination position in `continuation_cursor`, and let the dispatcher re-dispatch with the cursor. A partial sweep still obeys dedupe-before-extract — everything it returns was filtered before its JD was fetched.

## Not user-invocable

This skill has no `allowed-tools` frontmatter for the slash-command surface and must never be wired into a slash command. The dispatching `/ultramode` command always loads it via the `Agent` tool with a self-contained prompt, one dispatch per source.

## Reference materials

- `../shared-references/subagent-protocol.md` — the universal subagent I/O contract (envelope, delta-return, budget) this skill conforms to.
- `../shared-references/ultramode-sources.md` — access lanes + per-lane ingestion, the `resolve_ats` probe-and-cache resolver, the cross-source dedupe fingerprint + canonical preference (Decisions 6 & 9).
- `../shared-references/canonical-schemas.md` — structured `source: {lane, provider, board}`, the `<provider>__<board>__<externalid>` namespaced id format, the slug charset, the `category`/`access_lane` enums.
- `../shared-references/linkedin-search.md` — the existing dedupe-before-extract flow (§5 repost fingerprint) this skill mirrors for external sources.
- `../shared-references/jd-storage.md` — the `write_jd()` contract for `jds/<id>.txt` blobs.
- `../shared-references/browser-policy.md` — the read-only `WebFetch` carve-out and the login-walled → extension-lane rule.
- `../_job-matcher/SKILL.md` + `../_gate-engine/SKILL.md` — the scorer the dispatcher hands new roles to (unchanged by this skill).

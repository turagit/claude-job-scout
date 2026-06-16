---
name: ultramode
description: Sweep every verified job source for your workspace in one pass — discover the source registry, dedupe across sources, gate, score, and render a unified ranking
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: [optional: sources | onboarding — omit to run the multi-source sweep]
disable-model-invocation: true
version: 0.1.0
---

Multi-source ultramode (Phase 11). One pass that sweeps **every verified source** in this workspace's registry — ATS boards, remote boards, aggregators, national boards, freelance marketplaces, communities — dedupes the same role across them, gates and scores the genuinely-new roles through the existing rubric, and renders **one unified, source-agnostic ranking** alongside the LinkedIn surface. This command is the **dispatcher**: it loads the tracker once, derives the poll order, fans out the per-source sweep subagents, runs the extension lane on the main thread, performs the cross-source canonical merge, persists state, and renders via `_visualizer`.

LinkedIn remains the `/job-search` / `/deep-sweep` surface. Ultramode adds the **rest** of the market on top — keyless-first, with optional keyed aggregators when the candidate opts in.

## Browser policy (read first)

All logged-in browser work in this command uses **the Claude Chrome extension exclusively** (the `extension`-lane sweeps in Step 4). Never request computer use; never suggest Playwright, Selenium, or any other automation framework. The read-only public `WebFetch` `GET` of `api`/`rss`/`html` endpoints is the documented carve-out and happens **inside the dispatched `_source-sweep` subagents**, never as logged-in scraping. See `../shared-references/browser-policy.md`.

## Invocation forms

The user types one of:

```
/ultramode                          — run the multi-source sweep (first run triggers onboarding)
/ultramode sources                  — re-run source discovery / rebuild the registry
/ultramode sources add <url|name>   — add a source you already use to the registry
/ultramode onboarding               — re-run the first-run lane interview from scratch
```

- **Bare `/ultramode`** — the sweep flow (Step 4). If `.job-scout/sources.json` is absent, first-run onboarding (Step 3) runs automatically, then the sweep proceeds.
- **`/ultramode sources`** — re-dispatch `_source-discovery` and overwrite the registry (Step 3, discovery sub-step only — it reuses the already-known lane answers from `requirements`, re-asking only for genuine gaps). Does not run the sweep unless the user then runs bare `/ultramode`.
- **`/ultramode sources add <url|name>`** — add a board or site the candidate already uses or trusts, at any time. The source is probed and access-lane-classified (login-walled → `extension` lane, never dropped), appended to `.job-scout/sources.json`, and joins subsequent sweeps driven by the existing keyword corpus — no re-specifying queries. Does not run the sweep on its own.
- **`/ultramode onboarding`** — re-run the **whole** lane interview (Step 3 in full, including the explicit `base_country` question), then rebuild the registry.

## Step 0: Bootstrap workspace

Follow `../shared-references/workspace-layout.md` to ensure `.job-scout/` exists. Then follow `../shared-references/render-orchestration.md` Step G (lifecycle cleanup) to archive expired report files and prune old archives — cheap directory scan; runs at the start of every Tier 1 command.

## Step 1: Load profile, CV corpus & requirements

Follow `../shared-references/cv-loading.md`. Read `user-profile.json` for `segment`, `target_titles[]`, `query_clusters[]`, `requirements`, `cv_summary`, `master_keyword_list`, `ultramode` (the `{default, api_keys, registry_built_at}` block — treat an absent block as `{default: false, api_keys: {}, registry_built_at: null}`).

The **CV corpus** is the lane's relevance vocabulary, reused (never re-derived) across the whole run:

- `cv_summary.key_skills` and `cv_summary` — the candidate's skills and seniority.
- `target_titles[]` and `query_clusters[]` — the lane's title vocabulary (mirrors `/job-search` Step 1).
- `master_keyword_list` — the workspace keyword model built by `_cv-optimizer`.
- `.job-scout/cache/jd-keyword-corpus.json` (the **jd-keyword-corpus**) — the market-specific keyword model built up by prior sweeps; treat a missing file as empty.

From these, build the **lane relevance terms** passed to every sweep: `lane_keywords[]` = union of `cv_summary.key_skills`, the title tokens from `target_titles[]`/`query_clusters[]`, the top co-occurring skills in the jd-keyword-corpus, and `master_keyword_list`; `not_terms[]` = the workspace's exclusion terms (seniority/scope mismatches from `requirements.deal_breakers[]`). This is the same corpus `/job-search` and `/match-jobs` already read — ultramode reuses it rather than parsing the CV again.

If `target_titles` and `cv_summary.target_roles` are both empty, stop and ask the user to run `/analyze-cv` first — ultramode needs a declared lane to filter sources against.

## Step 2: Branch on invocation form

- **Registry present AND bare `/ultramode`** → skip to Step 4 (sweep flow).
- **Registry absent (any form), OR `/ultramode onboarding`** → Step 3 (full onboarding), then Step 4 for bare/onboarding forms.
- **`/ultramode sources`** → Step 3 discovery sub-step only (rebuild registry; do not sweep).

## Step 3: First-run onboarding (build the source registry)

Runs when `.job-scout/sources.json` is absent, on `/ultramode onboarding`, or (discovery sub-step only) on `/ultramode sources`. This is the **lane interview** that produces the discovery input envelope.

### Step 3a: Establish `base_country` — explicit question, read back to confirm

`base_country` is the workspace's home/legal-work country. It anchors the national-board backbone entries and the aggregator country codes (Adzuna `{country}`, Jooble `{country}` subdomain).

**Ask the candidate their `base_country` explicitly, then read the answer back to confirm it. NEVER infer `base_country`.** Do not infer it from the email handle, not from the CV text, not from the browser locale, not from `requirements.location_preferences`, not from any prior run. It is set **only** by this explicit question + confirmation. (This mirrors the canonical-schemas rule: `requirements.base_country` is *only ever populated by onboarding, never inferred*.)

```
Which country are you based in / legally able to work in? This anchors the
national job boards and country-specific aggregators I search.

  Country: ___
```

Read the answer back to confirm before continuing — e.g. `Got it — base_country = "Portugal". Is that right? (Y/n)`. Only on confirmation, set `requirements.base_country` on `user-profile.json` (merge, do not overwrite unrelated keys). If the candidate declines to give a country, leave `base_country` as `null` — discovery then skips the national-board backbone entries rather than guessing (per `ultramode-sources.md` § Universal Backbone). Never substitute a guessed value for a declined answer.

### Step 3b: Fill the rest of the lane from `requirements` — ask only for gaps

Read `requirements` for `target_geography`, `work_arrangement`, `contract_type`, and the field descriptor (`segment` / `target_titles`). For each that is already set, use it. **Ask only for the genuine gaps** (read-first, ask-second):

- `target_geography` — where the candidate wants roles (country, region, or "remote").
- `work_arrangement` — `remote` / `hybrid` / `on-site` (any subset).
- `contract_type` — `permanent` / `freelance` (either or both).
- field — derived from `segment` / `target_titles`; confirm rather than re-ask if already declared.

### Step 3c: Ask for trusted sources

Ask: **"Which job sources do you already use or trust?"** — boards, niche communities, a company careers page, a Slack/Discord jobs channel. Collect them as `user_sources[] = [{name, url}]`. These are always probed, classified, and retained by discovery (login-walled ones land in the `extension` lane; see `_source-discovery` § User sources). An empty answer is fine — the backbone still applies.

### Step 3c-bis: Seed target companies (so the ATS lane is not dark on first run)

The ATS lane is per-company: a fresh workspace with an empty `requirements.companies_to_target[]` and no A/B-tier employers yet has **nothing to resolve**, so the highest-signal direct-to-employer category stays dark on first run. To avoid that, seed it now:

- **Ask** (optional): *"Name 2–5 companies you'd love to work for / contract with — I'll watch their own job boards directly."* Collect into `requirements.companies_to_target[]` (merge, do not overwrite).
- **And/or derive** candidates from the CV corpus already loaded in Step 1 — the employer names in `cv_summary` work history and any companies named in `target_titles`/`segment` — and offer them for the user to confirm before adding.
- An empty answer is fine: discovery still bootstraps the ATS lane from the **lane-matching `## Curated lane seed → ATS seed`** (`../shared-references/ultramode-sources.md`), so the category is no longer guaranteed empty. User-named companies simply add to it.

This list is passed to discovery (Step 3d) and feeds the sweep-time ATS watchlist (`_source-sweep` § ATS watchlist).

### Step 3d: Dispatch `_source-discovery`

Build the discovery input envelope from the CV corpus (Step 1) and the lane answers above, and dispatch `_source-discovery` via the `Agent` tool per `../shared-references/subagent-protocol.md`:

```json
{
  "task": "discover-sources",
  "inputs": {
    "base_country": "<from Step 3a — confirmed value, or null>",
    "target_geography": "<requirements.target_geography>",
    "work_arrangement": ["<requirements.work_arrangement>"],
    "contract_type": ["<requirements.contract_type>"],
    "field": "<segment / target_titles descriptor>",
    "cv_keywords": ["<from cv_summary.key_skills + master_keyword_list>"],
    "companies_to_target": ["<from Step 3c-bis — confirmed/derived companies, or []>"],
    "user_sources": [ { "name": "...", "url": "..." } ]
  },
  "budget_lines": 800,
  "allowed_tools": ["Read", "Grep", "WebFetch", "WebSearch"]
}
```

Discovery is a **multi-round web loop**, not a single scoring batch — dispatch it with a budget well above the 200 default (`budget_lines: 800`). The subagent enumerates (seeded with the lane-matching curated seed), live-probes, adversarially verifies, loops until the completeness critic is dry, resolves the curated lane seed + merges the universal backbone, and returns a verified `sources_fragment` delta (it writes nothing — the dispatcher writes the file).

**The dispatch is mandatory and the loop runs to `ok`:**
- **You MUST call the `Agent` tool here.** Persisting a registry (Step 3e) without a parsed `_source-discovery` delta is a defect — see the Step 3e gate. (Only the documented `Agent`-unavailable fallback in `subagent-protocol.md` exempts this, and that fallback runs the same enumerate→probe→verify loop in-thread and is logged.)
- If it returns `status: "partial"` with a `continuation_cursor`, **re-dispatch with the cursor until `status: "ok"`** — never persist a `partial`.
- If it returns `status: "ok"` with an **empty confirmed-set after a single round**, or an `errors[]` carrying `tool_unavailable`, treat the probe lane as suspect: **re-probe (retry the dispatch, or run the probes on the main thread via the `WebFetch` carve-out) before persisting** — do not accept a clean-but-empty `ok` as a genuinely dry lane. Parse the delta only once it is a real, non-suspect `ok`.

### Step 3e: Gate, present for approval & persist

**Persistence is gated on a real discovery result. Do NOT skip these gates — they are what stops a silent backbone-only registry (the Phase 13 failure).**

**Gate 1 — parsed-delta gate (you must have actually run discovery).** If you did **not** call the `Agent` tool in Step 3d and parse a real `_source-discovery` delta envelope (or run the documented in-thread fallback), **you have NOT completed Step 3 — do not write `sources.json`.** Step 3e is not self-sufficient: resolving the backbone from the reference is **not** a substitute for discovery. Log the dispatch (and any fallback) in the run output so its presence is auditable.

**Gate 2 — count invariant.** Build the merged registry, then assert before writing:

```
len(sources) == len(resolved backbone bodies) + len(fragment.sources) + len(retained user_sources)
```

A mismatch means the discovered fragment was dropped or mis-merged — **fail loudly, do not write.** This catches a fragment silently lost at merge time.

**Gate 3 — known-rich-lane acceptance.** Count the **non-backbone** discovered sources and break them down by `category`. Apply the lane-conditional threshold:

- **If `requirements.contract_type` includes `freelance`:** require **≥ 1 `freelance-marketplace` AND ≥ 1 `ats-provider`** among the discovered/seed sources (the two structurally-dark categories), plus **≥ 5 non-backbone sources total**.
- **Otherwise (tech / professional / EU-remote lanes):** require **≥ 5 non-backbone sources total.**
- **A genuinely thin niche lane** (the critic asked and `errors[]` legitimately carries `lane_dry` for the missing categories, with no `tool_unavailable`/`probe_failed`) may fall below threshold — but only **after** the dispatcher has confirmed discovery actually ran the loop (Gate 1 + a non-suspect `ok`).

On a **below-threshold** result: do **not** silently write. **Warn**, show the shortfall + `errors[]` (which dry lanes, and whether any were `probe_failed`/`tool_unavailable` rather than truly `lane_dry`), and **offer an immediate `/ultramode sources` re-dispatch**. Write a below-threshold registry **only on explicit user acknowledgement**, and record `discovered_below_threshold` in the run output so the thin result is visible, never invisible.

**Present for approval (transparent table).** Show a short table per source — name, category, access lane, `needs_key` / `needs_slug` — **headed by the discovered-source count and the per-category breakdown** (e.g. `Discovered: 23 non-backbone — ats-provider:9 · freelance-marketplace:6 · national-board:3 · remote-board:3 · community:2`) so a zero- or thin-discovered union is visible **before** write. Note inline which sources are **keyless** vs **keyed** (key handling is Step 5), and surface any `errors[]` (dry lanes, unconfirmed user sources, probe failures).

**On approval, persist:**

1. Resolve the backbone bodies from `../shared-references/ultramode-sources.md` § Universal Backbone (the subagent named them in `backbone[]`), fill `{country}` from the confirmed `base_country` (skip national-board entries when `base_country` is null), and union with the verified discovered/seed/user fragment. (The curated lane seed was already re-probed by discovery — its hits arrive inside the fragment with their own `verified_at`, not re-resolved here.)
2. Re-assert the Gate 2 count invariant on the final object, then write the merged registry to **`.job-scout/sources.json`** (write to `sources.json.tmp`, then `mv` it over `sources.json` — the atomic-rename recipe in `../shared-references/state-validators.md`), conforming to the `sources.json` schema in `../shared-references/canonical-schemas.md` (`base_country`/`target_geography` copied in, `priority_order[]`, `backbone[]`, `sources[]`). Every `sources[]` entry carries a non-null `verified_at`.
3. Set `user-profile.json` `ultramode.registry_built_at` to the build timestamp (merge, do not overwrite) — **only after a successful write that passed all three gates.** Never stamp `registry_built_at` for a run that did not actually persist a gated registry.

The build is re-runnable any time via `/ultramode sources`; deleting `sources.json` triggers a fresh onboarding on the next run.

## Step 4: Sweep flow (the multi-source pass)

### Step 4a: Load the registry & derive the poll order

Load `.job-scout/sources.json`. Derive the poll order by applying `derive_priority_order(requirements, sources)` from `../shared-references/ultramode-sources.md` § Adaptive priority order (Decision 5) against this workspace's `requirements` — freelance+remote demotes ATS below remote-boards/marketplaces; permanent is ATS-first; mixed keeps discovery's canonical-preference default. **This ordering is a reference-level rule — read it from `ultramode-sources.md`; do not hardcode either ordering here.** The result is the source NAMES in fan-out order.

### Step 4b: Load the tracker ONCE & derive the fingerprint set

**Load `.job-scout/tracker.json` exactly once**, here, before any sweep is dispatched (Hard Rule #2; the single-writer contract in `_source-sweep` § Tracker coordination). From that one read derive the **candidate-fingerprint set** passed into every sweep:

- `known_ids[]` — every non-`rejected` entry's `id`.
- `known_fingerprints[]` — each non-`rejected` entry's cross-source fingerprint `lower(company)|lower(title)|normalise_location(location)` (the rule in `../shared-references/ultramode-sources.md` § Cross-source dedupe).

Also build, from this same read, the **ATS watchlist** for `ats-provider` sources — the **four-source union** (case-insensitive) the contract in `_source-sweep` § ATS watchlist defines: (1) the tracker's distinct A/B-tier employers + (2) `requirements.companies_to_target[]` + (3) **the lane-matching entries of the `## Curated lane seed → ATS seed`** (`../shared-references/ultramode-sources.md` — only seeds whose `lane_tags` intersect this workspace's lane) + (4) any manual additions. **Cold-start** (fewer than 1 A/B-tier employer) seeds from `companies_to_target[]` **plus the lane-matching curated ATS seed**, emitting `ats_watchlist_coldstart` — so the ATS lane is non-empty on a fresh workspace (the central cold-start fix; never `companies_to_target[]` alone). Each watchlist company is still resolved live via `resolve_ats` (with its identity check) before it is swept.

### Step 4c: Fan out one `_source-sweep` per source

For each source in poll order, dispatch one `_source-sweep` via the `Agent` tool per `../shared-references/subagent-protocol.md`, passing that one source verbatim plus the fingerprint snapshot:

```json
{
  "task": "sweep-source",
  "inputs": {
    "source": { /* one sources.json entry verbatim */ },
    "lane_keywords": ["<from Step 1 corpus>"],
    "not_terms": ["<from requirements.deal_breakers>"],
    "freshness_window_days": 7,
    "known_ids": ["<the snapshot from Step 4b>"],
    "known_fingerprints": ["<the snapshot from Step 4b>"],
    "ats_watchlist": [ { "company": "Miro", "tier": "A" } ],
    "api_keys": { "<provider>": "<token from ultramode.api_keys>" }
  },
  "budget_lines": 200,
  "allowed_tools": ["Read", "Grep", "Write", "WebFetch"]
}
```

- `ats_watchlist[]` is supplied **only for `ats-provider` sources**.
- `api_keys` carries only the key this source's `needs_key` requires, looked up from `user-profile.json` `ultramode.api_keys` (Step 5). Omit/empty for keyless sources; if a needed key is absent, gracefully skip the source (Step 5).
- The independent `api`/`rss`/`html` sweeps can be dispatched in **parallel** (per `subagent-protocol.md`). They never write the tracker — they dedupe-before-extract against the snapshot, write only JD blobs, and return delta-only genuinely-new roles. If a sweep returns `status: "partial"` with a `continuation_cursor`, re-dispatch with the cursor.
- **Fallback:** if the `Agent` tool is unavailable, run the sweeps sequentially in-thread on the same dedupe-before-extract framework, and log the fallback (per `subagent-protocol.md`).

### Step 4d: Extension lane — run on the MAIN THREAD

Subagents have no browser tools, so **`extension`-lane sources cannot be swept inside a subagent**. The dispatched `_source-sweep` returns `status: "ok"` with empty `deltas` and an `errors[]` note (`code: "extension_lane_deferred"`, or `ats_unresolved` for an ATS company whose slug did not resolve). For every such deferred source, the dispatcher sweeps it **on the main thread** via the Claude Chrome extension, following dedupe-before-extract in the logged-in session: load the same fingerprint snapshot, collect candidate IDs on the listing page, drop everything already in `known_ids`/`known_fingerprints`, open only the genuinely-new roles, persist each JD to `jds/<namespaced-id>.txt`, and produce the same delta shape as a subagent sweep. This is the only browser work in the command (Hard Rule #1).

### Step 4e: Merge deltas serially — canonical selection + `also_seen_on[]`

Merge the per-source deltas (from the subagent sweeps **and** the main-thread extension sweeps) into the single in-memory tracker **serially — one source's deltas at a time, no concurrent writes**. For each incoming delta apply the merge-time algorithm `merge_delta_into_tracker(delta, tracker)` from `../shared-references/ultramode-sources.md` § Where canonical selection runs — dispatcher merge time:

- A delta whose fingerprint is **new** is added as canonical (first sighting).
- A delta whose fingerprint **collides** with an already-merged entry resolves to one canonical "apply here" winner by the `ATS > LinkedIn > aggregator > marketplace` preference; the loser is recorded as a **sighting on the winner's `also_seen_on[]`** (`{lane, provider, board}` — the loser's structured `source`, rendered by the view's `source_chip()` macro), never re-fetched or re-scored. This is why the dispatcher — not the subagent — picks the canonical winner: only the dispatcher sees deltas from all sources at merge time (a single sweep sees only its own source).
- **ATS-backed JD enrichment:** when a non-ATS source wins a collision whose role resolves to an employer ATS, prefer the ATS's full JD for scoring (per § ATS-backed JD enrichment) so the scorer is not starved by truncated aggregator text.

Because the merge is serial and the loser is retained (not dropped, not re-fetched), this is single-writer-safe and costs no extra tokens.

### Step 4f: Gate + score the genuinely-new roles (unchanged scorer)

The accumulated genuinely-new roles join the **existing** scoring path, unchanged — exactly as `/job-search` Step 4 and `/match-jobs` Step 4 do:

1. `_gate-engine` runs first on each new role against `requirements` (`deal_breakers[]` etc.). Non-empty `gate_violations` → set `tier: "D"`, `tier_reason: "gated: <kinds>"`, persist the violations, skip dimension scoring.
2. Otherwise `_job-matcher` runs the v1 rubric, reading the JD from each role's `jd_path`. It loads `user-profile.json.dimensions[]` if present, else `../_job-matcher/references/dimensions-default.md`. Persist `tier`, `dimensions`, `tier_reason`, `rubric_version: "v1"`.

Scoring is **batched per `../shared-references/subagent-protocol.md`** (batches of ≤5 by similarity), the same fan-out `/match-jobs` uses — multi-source roles take no special path. Write each score into `.job-scout/cache/scores.json` under the `(job_id, cv_hash, profile_hash, rubric_version)` key. Then merge the scored roles into `.job-scout/tracker.json` with status `"seen"` and **write the tracker once** (atomic-rename per `../shared-references/state-validators.md`). The structured `source: {lane, provider, board}` and namespaced ids the sweeps produced are carried through.

### Step 4g: Build the unified results payload

Build the `data` payload for the `ultramode` view per `../shared-references/render-orchestration.md` § "The `ultramode` view". It mirrors `match-jobs` — same tier pills, per-dimension table, "⚡ apply early" chip, "Filtered out" gated group — plus source-aware fields:

```json
{
  "title": "Ultramode — {{N_sources}} sources · {{N_new}} new roles",
  "subtitle": "A:{{a}} B:{{b}} C:{{c}} · Filtered:{{gated}} · deduped across sources",
  "generated_at": "<YYYY-MM-DD HH:MM>",
  "filename": "ultramode-<YYYY-MM-DD>.html",
  "tier_counts": { "a": <a>, "b": <b>, "c": <c>, "d": <gated>, "total": <total> },
  "source_breakdown": { "<source label>": <count> },
  "results": [
    {
      "title": "<job title>", "company": "<company>", "location": "<location>",
      "salary": "<salary or empty>", "posted_at": "<YYYY-MM-DD>",
      "applicants": "<count or empty>", "fresh": true,
      "tier": "A | B | C | D", "tier_reason": "string|null",
      "dimensions": { "<dim>": {"tier": "A|B|C|D", "evidence": ["..."]} },
      "gate_violations": [{"kind": "...", "detail": "..."}],
      "rubric_version": "v1", "rationale": "<A-tier / top-B only>",
      "competitiveness": "high | med | low — OPTIONAL; omit when not yet derived (never null)",
      "competitiveness_evidence": "<short supporting note — OPTIONAL; omit when absent>",
      "confidence": "high | med | low — OPTIONAL; omit when not yet derived (never null)",
      "match_explanation_tag": "all-fit | one-gap | multiple-gaps | overqualified | underqualified | trajectory-concern — OPTIONAL; omit when absent",
      "url": "<canonical apply-at-source URL>",
      "source": { "lane": "...", "provider": "...", "board": "..." },
      "also_seen_on": [ { "lane": "...", "provider": "...", "board": "..." } ],
      "tags": ["<tag1>", "<tag2>"]
    }
  ]
}
```

- **Source is a chip, not a grouping axis** — the list is **one unified, source-agnostic ranking**, never bucketed by source. `url` is the canonical "apply at source" link; mirrors go on `also_seen_on[]` ("also seen on N sources").
- **Ordering is the dispatcher's responsibility:** pre-sort `results[]` to tier A → B → C, gated (D-tier) entries last. **Within-tier (Phase 12):** order by `confidence` high → med → low (absent `confidence` sorts after any explicit value, treated as lowest), then `posted_at` descending (freshest-first) as the tie-breaker. The COMMAND applies this here in the payload-build; the template does not re-sort. The four optional scoring fields (`competitiveness`, `competitiveness_evidence`, `confidence`, `match_explanation_tag`) pass through verbatim from the tracker / score cache when present and are **omitted entirely when absent** — never `null` (see `../shared-references/canonical-schemas.md` § "Written lazily").
- `source_breakdown` is an optional name→count strip (e.g. `Greenhouse · Miro`). Include any `Skipped <provider> (no API key)` line from Step 5 in the subtitle or a notes strip so the candidate sees what was not searched.

### Step 4h: Render via `_visualizer` (never inline)

Follow `../shared-references/render-orchestration.md` end-to-end (Step G already ran in Step 0), with `view: "ultramode"`:

1. Step A — payload built in Step 4g.
2. Steps B–F — read render config, dispatch `_visualizer` through the `Agent` tool, open in Chrome (or fall back), handle errors. **Inline HTML production is forbidden (Hard Rule #8)** — the `ultramode` template/theming/asset embedding live in `_visualizer`.
3. Step E — print the `ultramode` summary line: `✓ Ultramode — {{N_sources}} sources · {{N_new}} new jobs — A:{{a}} B:{{b}} C:{{c}} · Filtered:{{gated}} — opened report in Chrome` (or `…rendered as markdown above` when falling back). Append any `Skipped <provider> (no API key)` notes on a following line.

If the `Agent` tool is unavailable, fall back to a terminal markdown table (tier, title, company, location, posted_at, source chip; dimension breakdowns + rationale for A-tier), per the same fallback `/match-jobs` uses.

## Step 5: Key handling (keyless-first) + `/config`

**Keyless-first is the rule: ultramode runs with zero API keys.** Every backbone source except the keyed aggregators (Adzuna, Jooble) is keyless, and so is every ATS lane — a fresh workspace gets full coverage with no keys at all.

When discovery flags a **keyed** aggregator that *materially* helps this lane (e.g. Adzuna for a country/occupation the keyless feeds cover thinly), prompt the candidate **inline** with the signup link, once, at the point the source would be swept:

```
<provider> needs a free API key to search (it covers <what it adds for this lane>).
Get one at <signup link>, then add it with:  /config ultramode key <provider> <token>
Skip for now? (Y/n)
```

- **Never enter an API key into a browser form.** Keys are handled only via `/config` and stored in `user-profile.json` `ultramode.api_keys` (gitignored workspace state). The candidate pastes the token into the terminal, never into any web page the extension is driving (Hard Rule on sensitive data).
- **Gracefully skip if declined or absent.** If the candidate declines, or the key is simply not present in `ultramode.api_keys`, **skip that source** — do not block the run. Record `Skipped <provider> (no API key)` and surface it in the report (Step 4g/4h) so the candidate knows what was not searched and can add the key later.

Keys live in `ultramode.api_keys` as a `{ "<provider>": "<token>" }` map. The dispatcher reads them in Step 4c (looking up only the key a `needs_key` source requires) and never logs or echoes a token back.

`/config` is extended (this task) to add/remove a provider key and to toggle `ultramode.default`. See `../config/SKILL.md`:

- `/config ultramode key <provider> <token>` — add/replace a key.
- `/config ultramode key <provider> --remove` — remove a key.
- `/config ultramode default <true|false>` — toggle the run-without-prompting default (default `false`).

When `ultramode.default` is `true`, a Tier 1 LinkedIn command may offer to also run the ultramode sweep without re-prompting; when `false` (the default), ultramode runs only on explicit `/ultramode`.

## Next Steps

Suggest `/apply` for approved new roles, `/match-jobs` to re-score against an updated CV, or `/ultramode sources` to rebuild the registry when the lane changes (new geography, new contract type).

## Reference materials

- `../shared-references/ultramode-sources.md` — taxonomy, access lanes, the universal backbone, `derive_priority_order()`, the cross-source fingerprint + `merge_delta_into_tracker()` canonical selection, key-handling note.
- `../shared-references/canonical-schemas.md` — the `sources.json` schema, the `ultramode` profile block (`default`/`api_keys`/`registry_built_at`), `requirements.base_country`/`target_geography`, the structured `source` + namespaced id.
- `../shared-references/render-orchestration.md` — the `ultramode` view and the render lifecycle (Steps A–G).
- `../shared-references/subagent-protocol.md` — the dispatch / delta-return / budget contract for `_source-discovery`, `_source-sweep`, the scorer, and `_visualizer`.
- `../shared-references/cv-loading.md` — the CV corpus this command reuses (never re-parses).
- `../_source-discovery/SKILL.md` — the discovery subagent (Step 3d).
- `../_source-sweep/SKILL.md` — the per-source sweep subagent (Step 4c), tracker coordination, the `extension_lane_deferred` contract.
- `../_job-matcher/SKILL.md` + `../_gate-engine/SKILL.md` — the unchanged scorer (Step 4f).
- `../config/SKILL.md` — key add/remove and `ultramode.default` toggle (Step 5).
- `../shared-references/browser-policy.md` — the Chrome-extension-only rule and the read-only `WebFetch` carve-out.

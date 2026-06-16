---
name: _source-discovery
description: >
  [Internal subagent — dispatched only by /ultramode (and /ultramode sources), not user-invocable]
  Internal subagent skill. Builds the verified per-workspace source registry
  `.job-scout/sources.json` by enumerating candidate job sources along independent
  axes, live-probing and adversarially verifying each one, looping until a
  completeness critic finds no more gaps, then merging the always-on universal
  backbone. Returns a verified `sources.json` fragment as a delta. Never invents
  or includes unverified sources. Not user-invocable.
version: 0.1.0
---

# Source Discovery (Subagent)

Build the per-workspace **verified** source registry written to `.job-scout/sources.json`. The engine discovers concrete job sources for one workspace lane, **probes every candidate live before it is allowed into the registry**, and merges the always-on universal backbone. The dispatching command (`/ultramode`, Task 7) fans this out, parses the returned delta, and writes the file.

**This skill is dispatched only by other skills, via the `Agent` tool, per `../shared-references/subagent-protocol.md`.** It is not user-invocable. One discovery dispatch builds the whole registry for a workspace.

## Hard invariant — nothing unverified enters the registry

**This is the load-bearing rule of the whole skill. Read it before anything else.**

- **Nothing enters `sources.json` unverified.** A candidate source is admitted only after a live probe confirms it is reachable AND carries roles for this workspace's lane (see the verification rubric in `references/discovery-protocol.md`).
- **The synthesis step uses ONLY confirmed candidates.** When assembling the output fragment, the engine reads exclusively from the confirmed-set the verification loop produced. It MUST NOT invent, guess, hallucinate, or "fill in" plausible-looking sources, endpoints, slugs, or `verified_at` timestamps.
- **An empty confirmed-set yields an empty `sources[]` (plus the backbone) — never a fabricated one.** A synthesis step handed an empty confirmed-set will, if not explicitly forbidden, produce convincing but fictional entries. That is the single most damaging failure mode for this skill. If discovery confirms nothing for a lane, the correct output is the universal backbone alone, with `errors[]` naming the dry lanes — **not** a manufactured list.
- **Provenance, not memory.** Every `sources[]` entry's `endpoint`, `needs_key`, `needs_slug`, `access_lane`, and `verified_at` come from what the probe actually observed, never from the model's prior knowledge of "how that provider usually works".
- **A curated lane seed is provenance-from-file, NOT fabrication — but it is still a candidate, not an admission.** The `## Curated lane seed` in `../shared-references/ultramode-sources.md` (ATS companies, freelance marketplaces, lane-specific feeds) and the Universal Backbone are version-controlled, verified source lists. Resolving a seed is allowed and encouraged — but **each seed is re-probed live** (ATS via `resolve_ats` with its identity check; marketplace/feed via the §2 gates) and admitted only with a **fresh probe-time `verified_at`**. A seed that fails its live re-probe is **skipped or extension-routed, never written**. Reading a seed from the file is not the violation; writing one you did not re-probe is.
- **An empty or below-threshold confirmed-set is a LOUD, AUDITABLE signal — never a silent swallow.** It MUST populate `errors[]` enumerating **every dry lane by name** plus the round count and probe-attempt count. Distinguish the three empty-shaped outcomes so the dispatcher can tell them apart: a lane probed-and-confirmed-nothing is `lane_dry`; a candidate whose probe failed outright (timeout / `ECONNREFUSED` / blanket `403`) is `probe_failed`; **N consecutive outright tool failures is `tool_unavailable`** (the probe lane itself is dead — the dispatcher must retry on the main thread, not accept a clean dry `ok`). A `status: "ok"` with an empty `sources[]` and an empty `errors[]` is itself a defect — never emit it.

If you are ever unsure whether a source was truly probed, treat it as unverified and drop it (recording `probe_failed`/`lane_unconfirmed` so the gap is visible, not invisible).

## Input shape

The dispatcher passes a single JSON envelope (per `subagent-protocol.md`). `field` is a **single workspace-derived value** (one discovery dispatch per workspace — not one dispatch per lane):

```json
{
  "task": "discover-sources",
  "inputs": {
    "base_country": "Portugal",
    "target_geography": ["Portugal", "remote-EU"],
    "work_arrangement": ["remote", "hybrid"],
    "contract_type": ["permanent", "freelance"],
    "field": "backend software engineering",
    "cv_keywords": ["python", "django", "postgres", "aws"],
    "companies_to_target": ["Acme Robotics", "Globex"],
    "user_sources": [
      { "name": "Landing.jobs", "url": "https://landing.jobs" },
      { "name": "Our Slack #jobs", "url": "https://acme.slack.com" }
    ]
  },
  "budget_lines": 800,
  "allowed_tools": ["Read", "Grep", "WebFetch", "WebSearch"]
}
```

- `field` is the workspace's single job-search lane descriptor (derived from `user-profile.json` `segment` / `target_titles`). The engine expands it into occupation synonyms internally; it does not expect one dispatch per occupation.
- `companies_to_target[]` are the user's named target employers (from onboarding Step 3c-bis / `requirements.companies_to_target[]`, possibly empty). They are the **ATS-company enumeration source** for §1's category axis — unioned with the lane-matching curated ATS seed and resolved via `resolve_ats` — so a user who names employers gets their boards discovered on the very first run rather than waiting for the sweep-time watchlist.
- `budget_lines` is the multi-round web-loop budget (well above the 200 single-batch default — the dispatcher passes ~800; see § Budget).
- `user_sources[]` are the user's own named sources. They are always probed, always classified, and **always retained** (see § User sources).
- `allowed_tools` is exactly `["Read", "Grep", "WebFetch", "WebSearch"]` — web enumeration (`WebSearch`) plus live read-only probing of public endpoints (`WebFetch`, the carve-out in `../shared-references/browser-policy.md`), plus `Read`/`Grep` to ingest the backbone reference. No write tools: the dispatcher writes the file after fan-in.

## Output shape (delta-return)

A single JSON envelope. The `deltas` carry the verified `sources.json` **fragment** — a partial `sources.json` object the dispatcher merges with the backbone-resolved registry and writes:

```json
{
  "status": "ok",
  "deltas": [
    {
      "sources_fragment": {
        "priority_order": ["Greenhouse (Miro)", "RemoteOK", "Landing.jobs", "Adzuna"],
        "backbone": ["Adzuna", "Jooble", "..."],
        "sources": [
          {
            "name": "Landing.jobs",
            "url": "https://landing.jobs",
            "category": "national-board",
            "access_lane": "html",
            "endpoint": "",
            "needs_key": false,
            "needs_slug": false,
            "priority": 3,
            "poll_method": "GET the listings page; client-side full-text filter (Decision 9)",
            "notes": "User-supplied. Portugal-leaning tech board. Probed live 2026-06-15.",
            "verified_at": "2026-06-15T00:00:00Z"
          }
        ]
      }
    }
  ],
  "errors": [
    { "code": "lane_dry", "message": "No verified freelance-marketplace source carried <field> roles for <geography>; backbone-only for that lane." }
  ],
  "continuation_cursor": null
}
```

- Each `sources[]` entry conforms **exactly** to the `sources.json` schema in `../shared-references/canonical-schemas.md` — same field names, the same `category` enum (`ats-provider | remote-board | aggregator | national-board | freelance-marketplace | community`) and `access_lane` enum (`api | rss | html | extension`). `endpoint` is non-empty when `access_lane` is `api` or `rss`.
- `verified_at` is the probe time — present only because a live probe happened. A `null` or absent `verified_at` means the entry should not be in the fragment at all.
- `deltas` carry **only** the discovered/user fragment. The backbone JSON is read by the dispatcher (or by this engine from the reference) and is named in `backbone[]`; the engine does not re-emit the backbone's full bodies as discovered sources.
- `status: "partial"` + `continuation_cursor` if the loop hits `budget_lines` mid-discovery; the dispatcher re-dispatches with the cursor.
- No prose outside the JSON envelope.

## Engine (overview)

Full enumeration axes, the live-probe/verify rubric, the loop-until-dry critic mechanics, and backbone ingestion live in `references/discovery-protocol.md`. The loop in brief:

1. **Enumerate** candidates along independent axes — category, region/country (led by `base_country`), occupation + synonyms (expanded from `field` + `cv_keywords`), professional bodies for the occupation, and a live `WebSearch` of "best job boards for `<field>` in `<geography>`". Enumeration is allowed to be wide and speculative — this is the only stage that may name a source it has not yet confirmed.
2. **Live-probe + adversarially verify** each candidate **before inclusion**: is it live (read-only `WebFetch`)? does it actually carry roles for this lane (not an empty board, not a parked domain, not a paywalled stub)? Then classify its access lane, resolve its real `endpoint`, and set `needs_key` / `needs_slug` from what the probe shows. A candidate that fails any check is dropped, not downgraded.
3. **Loop until dry.** A completeness critic inspects the confirmed-set, **names the gaps** (a category with zero confirmed sources, a geography uncovered, an occupation synonym unsearched), and seeds another enumeration round targeting exactly those gaps. The loop ends when a round adds no new confirmed sources and the critic reports no actionable gaps.
4. **Resolve the curated lane seed, then merge the universal backbone.** First, for the lane-matching entries of the `## Curated lane seed` in `../shared-references/ultramode-sources.md` (ATS companies via `resolve_ats` + identity check; freelance marketplaces and lane feeds via the §2 gates), re-probe each live and admit the hits to `confirmed` with a fresh `verified_at` — this is how the structurally-dark `ats-provider` and `freelance-marketplace` categories get a real first-run lane (the seed is a candidate, the live re-probe is the admission). Then read the `## Universal Backbone` JSON array verbatim, normalise slugs, fill `{country}` placeholders from `base_country` (skip national-board entries when `base_country` is null — never guess), and union it with the confirmed discovered+seed set. Backbone names are listed in `backbone[]`.
5. **Synthesise from confirmed candidates ONLY** (see the Hard invariant above) into the `sources_fragment`, assign `priority` / `priority_order` by canonical preference (ATS > remote/national board > aggregator > marketplace), and return as a delta.

## User sources

`user_sources[]` are first-class:

- **Always probed and classified** through the same rubric — live check, access-lane classification, endpoint resolution.
- **Always retained**, even on a thin or login-walled result. A user source that sits behind a login is classified into the **`extension` lane** (`access_lane: "extension"`, empty `endpoint`, `poll_method` noting the logged-in sweep) — it is **never dropped** for being login-walled, because the extension lane is load-bearing, not a fallback (see `../shared-references/ultramode-sources.md`).
- A user source the probe cannot even reach is still retained, with a note and a `lane_unconfirmed` entry in `errors[]`, so the user sees their source was carried but could not be auto-polled — the engine does not silently discard user intent.

## Persistence (done by the dispatcher after fan-in)

This subagent has no write tools. The dispatching `/ultramode` command, after parsing the delta:

1. Writes the merged registry to **`.job-scout/sources.json`** (atomic-rename, per `../shared-references/state-validators.md`), conforming to the Task 1 schema.
2. Sets `user-profile.json` `ultramode.registry_built_at` to the build timestamp.

The build is **re-runnable** via `/ultramode sources`, which re-dispatches this subagent and overwrites the registry. Deleting `.job-scout/sources.json` triggers a fresh first-run discovery on the next ultramode run.

## Budget

Discovery is a **multi-round web loop** (a `WebSearch` per axis, a `WebFetch` per candidate, full-text Gate B checks, plus the curated-seed re-probes), so the dispatcher passes a budget **well above** the single-scoring-batch default of 200 (`ultramode/SKILL.md` Step 3d). If the enumerate→verify→critic loop still cannot complete within budget, return `status: "partial"` with the confirmed-set so far in `sources_fragment`, the critic's outstanding gaps in `errors[]`, and a `continuation_cursor` the dispatcher passes back to continue the loop. **Never round a budget-truncated run down to `status: "ok"` with an empty confirmed-set** — that is the failure the silent-swallow guard exists to catch; emit `partial` + cursor (or `tool_unavailable` if the probe lane is dead) so the dispatcher loops or retries rather than persisting a backbone-only registry. A partial result still obeys the Hard invariant — everything in it is verified.

## Not user-invocable

This skill has no `allowed-tools` frontmatter for the slash-command surface and must never be wired into a slash command. The dispatching `/ultramode` command always loads it via the `Agent` tool with a self-contained prompt.

## Reference materials

- `references/discovery-protocol.md` — the enumeration axes, the live-probe/verify rubric, the loop-until-dry/critic mechanics, and backbone ingestion in full.
- `../shared-references/subagent-protocol.md` — the universal subagent I/O contract this skill conforms to.
- `../shared-references/ultramode-sources.md` — taxonomy, access lanes, the `## Universal Backbone` JSON merged in step 4, the ATS slug resolver.
- `../shared-references/canonical-schemas.md` — the `sources.json` schema the output fragment must satisfy, plus the slug charset and the `category`/`access_lane` enums.
- `../shared-references/browser-policy.md` — the read-only `WebFetch` carve-out and the login-walled → extension-lane rule.
- `../shared-references/sources-schema-example.json` — a worked four-source example of a valid `sources.json`.

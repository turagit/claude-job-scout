---
name: sources
description: Manage where the job hunt looks — list the verified source registry, add a board or company, rebuild via discovery, or re-run the first-run lane interview
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: [list | add <url|name> | scope [eu-nl|eu-broad] | retire <name> | rebuild | onboarding — omit for list]
disable-model-invocation: true
version: 0.2.0
---

Where the hunt looks. `/ultramode` is *go look*; `/sources` is *where*. It owns `.job-scout/sources.json` — the per-workspace, CV-derived, **verified** source registry built by `_source-discovery` — and the first-run lane interview that seeds it.

## Browser policy (read first)

Discovery probes are read-only public `WebFetch` `GET`s (the documented carve-out); any logged-in verification uses **the Claude Chrome extension exclusively**. Never request computer use; never suggest Playwright, Selenium, or any other framework. See `../shared-references/browser-policy.md`.

## Invocation forms

```
/sources                      — list the registry (default)
/sources add <url|name>       — add a board you trust, or a company (resolved to its ATS board)
/sources scope                — show the source scope (eu-nl default; eu-broad adds global marketplaces)
/sources scope <eu-nl|eu-broad> — set it (offers a rebuild; scope matters at rebuild time)
/sources retire <name>        — retire a source permanently (tombstone — rebuilds never re-admit it)
/sources rebuild              — re-run discovery and rebuild the registry through the Phase 13 gates
/sources onboarding           — re-run the whole first-run lane interview, then rebuild
```

`/ultramode sources …` and `/ultramode onboarding` are deprecated spellings that point here.

## Step 0: Bootstrap

Follow `../shared-references/workspace-layout.md` to ensure `.job-scout/` exists. If `sources.json` is absent and the form is `list` or `add`, say so and offer `/sources onboarding` — nothing to list or add into yet.

If `sources.json` exists with `schema_version < 2`, run `python3 $SCRIPTS/migrate_sources.py .job-scout/sources.json` before anything else (idempotent; adds `auth_state` + lifecycle lists — Phase 16). `$SCRIPTS` = `../_ultra-engine/scripts` resolved from this skill.

## `/sources` — list

Read `.job-scout/sources.json` and print a terminal table (no `_visualizer` — this is a Tier-2 utility view):

```
Registry: {{N}} sources · built {{ultramode.registry_built_at (from user-profile.json)}} · base {{base_country}} · geography {{target_geography}}
{{category}}: {{n}} · … (one line, all six categories + linkedin)

| name | category | lane | needs_key | last swept |
|---|---|---|---|---|
…
```

Order: `priority_order[]` first, the rest alphabetically. After the table, one status line: how many sources the newest run dir's scorecard actually swept (`ls -1dr .job-scout/cache/run/*/ | head -1` → `scorecard.json` → count of `.sources` keys), so "registered" vs "recently swept" is visible at a glance. Close with: `Add: /sources add <url|name> · Rebuild: /sources rebuild`.

## `/sources scope` — the catalogue scope (Phase 16)

Read: `python3 $SCRIPTS/catalog.py config-read .job-scout/user-profile.json` → print
`Scope: {{source_scope}} (refresh: {{source_refresh}})` plus one line explaining the other value
(`eu-nl` = EU/NL/BENELUX packs; `eu-broad` adds the opt-in global marketplaces — Upwork, Freelancer,
FlexJobs, Contra — and global remote boards). Reading NEVER writes the default.

Set (`/sources scope eu-broad`): validate the value (only `eu-nl`/`eu-broad`; anything else → show
allowed values, stop). Write with exactly this recipe (unknown keys must survive — test-pinned):

    jq '.ultramode.source_scope = "<value>"' .job-scout/user-profile.json > .job-scout/user-profile.json.tmp \
      && jq -e . .job-scout/user-profile.json.tmp >/dev/null && mv .job-scout/user-profile.json.tmp .job-scout/user-profile.json

Then OFFER (never force) a rebuild: `Scope set to <value>. It takes effect at the next rebuild — run /sources rebuild now? (y/N)`.

## `/sources add <url|name>` — admit one source

The candidate names a board they use or trust, or a company they want watched:

1. **URL given** → probe it live (read-only GET). Classify per `../_source-discovery/references/discovery-protocol.md` Gates A–C as amended by Phase 13: a recognised login wall routes to `access_lane: "extension"` and is RETAINED; admit on occupation (never on today's contract mix); a dead/parked domain is refused with the probe evidence.
2. **Company name given** → resolve its ATS board via the `resolve_ats` probe-and-cache flow (`../shared-references/ultramode-sources.md` § ATS slug resolver), identity-check included. On a hit, admit the board as an `ats-provider` source; also merge the company into `requirements.companies_to_target[]` (so a registry rebuild keeps watching it). On a miss, say which providers were probed and keep the company in `companies_to_target[]` for the next rebuild.
3. Build the entry per the `sources.json` schema (`../shared-references/canonical-schemas.md`), `verified_at` = today, and append via the atomic-rename recipe (`../shared-references/state-validators.md`). Confirm with the entry's name, category, and lane. The source joins the next sweep automatically — no re-specifying queries.

## `/sources retire <name>` — permanent retirement (Phase 16)

Confirm first (`Retire <name>? Rebuilds will never re-admit it. (y/N)`), then:
`python3 $SCRIPTS/registry_lifecycle.py retire --registry .job-scout/sources.json --name "<name>"`.
Show the returned identity key. Absence from a future catalogue is NOT retirement — only this
tombstone is; to undo, remove the key from `retired_identities` by hand and `/sources add` the URL.

## `/sources onboarding` — the first-run lane interview

This is the interview that used to live in `/ultramode` Step 3. Run it in full, then continue into § Rebuild below.

### base_country — explicit question, read back to confirm

`base_country` anchors the national-board backbone and aggregator country codes. **Ask explicitly, read the answer back, NEVER infer** — not from the email handle, the CV, the locale, or any prior run (canonical-schemas: *only ever populated by onboarding*):

```
Which country are you based in / legally able to work in? This anchors the
national job boards and country-specific aggregators I search.

  Country: ___
```

Confirm (`Got it — base_country = "<X>". Is that right? (Y/n)`), then set `requirements.base_country` (merge). A declined answer stays `null` — discovery skips the national-board backbone rather than guessing.

### The rest of the lane — read first, ask only for gaps

From `requirements`: `target_geography`, `work_arrangement`, `contract_type`, and the field descriptor (`segment`/`target_titles`). Ask only for what is genuinely unset.

### Trusted sources

**"Which job sources do you already use or trust?"** → `user_sources[] = [{name, url}]`. Always probed, classified, and retained by discovery (login walls land in the extension lane). Empty is fine.

### Target companies (so the ATS lane is never dark)

Ask (optional): *"Name 2–5 companies you'd love to work for / contract with — I'll watch their own job boards directly."* → merge into `requirements.companies_to_target[]`; also offer employer names derived from the CV corpus for confirmation. Empty is fine — the lane-matching curated seed still applies.

## `/sources rebuild` — dispatch discovery and persist through the gates

Runs after onboarding, or standalone (reusing the already-known lane answers; re-ask only genuine gaps).

1. **Build the discovery input envelope** from the CV corpus (`../shared-references/cv-loading.md`; `cv_summary.key_skills`, `target_titles[]`/`query_clusters[]`, `master_keyword_list`, the jd-keyword-corpus) and the lane answers: `base_country`, `target_geography`, `work_arrangement`, `contract_type`, field, `cv_keywords[]`, `companies_to_target[]` — **the dynamic ATS watchlist union (tracker A/B-tier employers + `companies_to_target[]` + the lane-matching curated seed + manual additions, per `../_source-sweep/SKILL.md` § ATS watchlist) is folded in here, at registry-build time** — and `user_sources[]`.
2. **Dispatch `_source-discovery`** via the `Agent` tool per `../shared-references/subagent-protocol.md`, `budget_lines: 800`, `allowed_tools: ["Read", "Grep", "WebFetch", "WebSearch"]`. **The dispatch is mandatory and loops to `ok`:** never persist a `partial` (re-dispatch with the `continuation_cursor`); treat a clean-but-empty single-round `ok` or `tool_unavailable` as suspect — re-probe before persisting.

3. **Gate and persist — the Phase 13 gates, verbatim:**
   - **Gate 1 (parsed-delta):** no parsed `_source-discovery` delta ⇒ you have NOT run discovery — do not write `sources.json`. Log the dispatch so its presence is auditable.
   - **Gate 2 (count invariant):** assert `len(sources) == len(resolved backbone) + len(fragment.sources) + len(retained user_sources) (+1 when the ensured LinkedIn entry is present)` before writing; mismatch ⇒ fail loudly.
   - **Gate 3 (lane-conditional acceptance):** freelance lanes require ≥1 `freelance-marketplace` AND ≥1 `ats-provider` plus ≥5 non-backbone total; other lanes ≥5 non-backbone. Below threshold ⇒ warn, show the shortfall + `errors[]`, offer an immediate re-dispatch, write only on explicit acknowledgement with `discovered_below_threshold` recorded.
   - **Present the approval table** (name, category, lane, keys) headed by the discovered-source count and per-category breakdown, then persist atomically: resolve the backbone (fill `{country}` from the confirmed `base_country`), union the verified fragment, **ensure the LinkedIn registry entry exists** (per ../ultramode/SKILL.md Step 3 — add it if absent), re-assert Gate 2 (which now accounts for the +1), write `sources.json.tmp` → `mv`. Stamp ultramode.registry_built_at only after a gated write (unchanged) — the Phase 16 staleness nag reads it.

4. **Catalogue admission (Phase 16, D5) — runs after the gated persist, so the registry file exists and is never clobbered.** Candidate precedence is `user sources → EU/NL catalogue → lane seed → universal backbone → live discoveries`; the step-3 write has already persisted every non-catalogue band, and this step merges the packaged catalogue on top without removing anything:
   1. `scope=$(python3 $SCRIPTS/catalog.py config-read .job-scout/user-profile.json | jq -r .source_scope)`
   2. `python3 $SCRIPTS/catalog.py select ../shared-references/source-catalogue.json --scope $scope` → the candidate list.
   3. **Probe every candidate live — packaged entries are hypotheses, never auto-admitted (never-fabricate):** api/rss/html lanes get a read-only `WebFetch` GET of `endpoint` (Gate B: postings visible); a recognised access/login wall flips the candidate to `access_lane: "extension"` with `endpoint: ""` and is RETAINED (verification completes in the logged-in sweep). A dead/parked candidate is dropped and recorded in the run notes with its probe evidence.
   4. Project each survivor: `python3 $SCRIPTS/project.py --candidate <one>.json --priority <next free> --verified-at <probe ISO8601>` (catalogue-only fields are stripped here; leaks are rejected again at merge).
   5. Merge atomically: `python3 $SCRIPTS/registry_lifecycle.py merge --registry .job-scout/sources.json --candidates <projected-array>.json --catalogue ../shared-references/source-catalogue.json --expect-sha256 $(shasum -a 256 .job-scout/sources.json | cut -d' ' -f1)`. Exit 3 = the registry changed underneath — re-read and retry once. Report the printed counts verbatim (`retained/added/updated/tombstoned_skipped/total`).
   Gate 2 (step 3) governs the pre-catalogue write with its own formula, unchanged; after this merge the closing invariant is `len(sources) == merge.total` exactly as printed by `registry_lifecycle.py` — the script IS the count assertion, and a mismatch inside it fails loudly before any write. Retired identities stay out (tombstones); user sources and every step-3 entry are retained by construction.

## Not a sweep

`/sources` never sweeps. When the registry changes, suggest `/ultramode` (full market) or `/ultramode source <name>` (just the new one).

## Reference materials

- `../ultramode/SKILL.md` — the sweep this registry feeds.
- `../_source-discovery/SKILL.md` + `references/discovery-protocol.md` — the discovery subagent and its admission gates.
- `../shared-references/ultramode-sources.md` — taxonomy, backbone, curated lane seed, `resolve_ats`.
- `../shared-references/canonical-schemas.md` — the `sources.json` schema.
- `../shared-references/subagent-protocol.md`, `state-validators.md`, `browser-policy.md`.

# Phase 11 — Ultramode: Multi-Source Discovery & Sweep Design Spec (v0.11.0)

**Status:** Drafted 2026-06-15. Design decisions locked in this session's `/grill-me` (every decision below is a user-approved branch); validated end-to-end against live data before drafting. Awaiting approval to execute.

> Numbering note: Phases 8 (triage feedback UX), 9 (recruiter rebuild + `/config tone`), 10 (nurture commands) remain **deferred, not cancelled**. Ultramode takes the next free slot (Phase 11) rather than renumbering them, but it is the **current execution priority** and is expected to ship ahead of 8–10. Target release `v0.11.0`.

**Problem.** The plugin automates the LinkedIn pipeline end-to-end, but LinkedIn is one market surface. For many candidates the highest-signal roles live elsewhere: on employer ATS boards (often posted there *before or instead of* LinkedIn), on occupation- and geography-specific boards, on remote-native feeds, in freelance marketplaces, and in community channels. A candidate searching only LinkedIn is structurally blind to a large fraction of the roles they could actually land. The plugin has no mechanism to reach any non-LinkedIn source, no abstraction for heterogeneous job sources, and a tracker `source` enum that is six LinkedIn-only values.

The opportunity is asymmetric by lane: a Netherlands-based remote freelance SRE and a Netherlands-based hospital doctor want almost entirely **different** source sets. So the feature cannot ship a hardcoded source list — it must *derive* the right sources per candidate from their CV and a short onboarding, then sweep them with the keyword model the plugin already holds.

**Goal.** Ship `v0.11.0` with an opt-in **ultramode** that, when activated, widens sourcing beyond LinkedIn into a per-workspace, CV-derived, **verified** set of external sources; sweeps them with the existing query corpus; and folds every job — regardless of source — into the *same* tracker, scoring, and render pipeline, presented as one unified, tier-ranked report with a direct link per role. The LinkedIn core ships **unchanged**; ultramode is additive and defaults **off**.

---

## Decisions

1. **Access — HTTP-fetch primary, Chrome-extension lane for the rest.** Structured public endpoints (ATS JSON, aggregator APIs, RSS/JSON feeds) are read over read-only `WebFetch`; the Chrome extension is reserved for opening/applying and for login-walled sources (most freelance marketplaces, Slack/Discord communities, some consumer aggregators). `browser-policy.md` gains an explicit **carve-out**: `WebFetch` is a plain read-only HTTP GET, **not** browser automation — Hard Rule #1 ("Chrome extension exclusively") continues to govern all *in-browser* work; it does not prohibit fetching public HTTP. No new browser-automation framework is introduced; the extension remains the only mechanism that touches the user's logged-in session.

2. **Activation — `/ultramode` command + config default toggle; ships OFF.** A new user-invoked slash command `/ultramode` (carries `disable-model-invocation: true`, Hard Rule #4) runs the external sweep and renders its own report. A `.job-scout/config.json` flag `ultramode.default` (default `false`), togglable via `/config`, makes the existing sweeps (`/job-search`, `/deep-sweep`) widen automatically when set. Default-off preserves "keep the plugin as-is"; turning it on is a choice the user owns. Sub-commands: `/ultramode` (sweep), `/ultramode sources` (re-run discovery / edit registry), `/ultramode onboarding` (re-run the lane interview).

3. **The engine is generic; the registry is derived and verified per workspace.** Source *categories* and *access lanes* are universal; the concrete providers that fill them are lane-specific and discovered per workspace, cached as `.job-scout/sources.json`. First `/ultramode` runs **verified discovery** (Decision 4 wires its inputs):
   - **Enumerate** along independent axes (by category · by region/country · by occupation + synonyms · by professional bodies · by live web-search "best boards for X in Y").
   - **Live-probe + adversarially verify** every candidate before it enters the registry — confirm it is live and carries roles for this lane, classify its **access lane** (`api | rss | html | extension`), record the concrete endpoint/URL pattern, `needs_key`, `needs_slug`; drop anything dead, irrelevant, or unreachable.
   - **Loop-until-dry**: keep enumerating until fresh strategies surface nothing new; a completeness critic names gaps and seeds another round.
   - A small **universal aggregator backbone** is always available so even rare lanes get coverage out of the box.
   - Exhaustiveness and accuracy here are **non-negotiable** — this registry is the foundation every future sweep depends on. Nothing enters `sources.json` on the model's word alone.

4. **First-run onboarding — derive from CV, ask only for gaps, confirm what can't be inferred.** Discovery reads occupation/seniority/skills/geography from the CV (`cv_summary`, `target_titles[]`, `query_clusters[]`, `master_keyword_list[]`, `jd-keyword-corpus.json`) and **asks the candidate** for what's missing or unsafe to infer:
   - **`base_country`** — asked **explicitly, always confirmed out loud**, never inferred (e.g. not from an email handle). It is a new first-class profile field distinct from target geography; it drives national-board selection, work-eligibility signal, timezone fit, and freelance/tax context.
   - **`target_geography`**, **`work_arrangement`**, **`contract_type`**, **field/occupation** — read from `requirements` where present, asked otherwise.
   - User-supplied sources are **first-class**: onboarding asks "which boards/sites do you already use?" and `/ultramode sources add <url|name>` works anytime; each is probed and access-lane-classified (login-walled → extension lane, not dropped) and joins the sweep driven by the existing keyword corpus — no re-specifying queries.

5. **Source priority is adaptive, not hardcoded.** Ultramode orders sources from `requirements` (`contract_type` · `work_arrangement` · `location_preferences`): a freelance + remote lane leads with remote-native feeds + contract-capable aggregators + freelance marketplaces, ATS as a contract-filtered secondary; a permanent lane leads with ATS. One engine; the order is data, not code.

6. **Source taxonomy + cross-source dedupe.** Six universal categories — `ats-provider · remote-board · aggregator · eu-national-board (national/vertical) · freelance-marketplace · community` — each tagged with an access lane. The existing repost fingerprint `lower(company)|lower(title)|lower(location)` (with light location normalisation) dedupes **across** sources. On a collision, the canonical "apply here" entry is chosen **direct-to-employer first**: employer ATS > LinkedIn > aggregator > marketplace; the others are retained as "also seen on N sources." When an aggregator surfaces a role whose canonical is an employer ATS, ultramode fetches the **full JD from the ATS** so scoring is not starved by truncated aggregator text.

7. **Keys — keyless-first, keyed opt-in.** Ultramode works immediately with zero keys (ATS boards · niche/remote feeds · HN · any keyless aggregator). When discovery finds a keyed aggregator that materially improves *this* lane's coverage, it prompts inline ("Adzuna covers NL roles well — add a free key?") with the signup link and **gracefully skips** if declined. Keys live in gitignored workspace config (`config.json` → `ultramode.api_keys`), **never** entered into a browser form (Hard Rule on sensitive data preserved).

8. **Results view — one unified, source-agnostic, tier-ranked report (reuses `_visualizer` untouched).** Every job from every source appears in a single list, **source shown only as a chip**, never the organising axis. Ranked by **tier A→B→C, freshest-first within tier** (no new scalar score — the engine is unchanged; "max score" = max tier). Each row carries a **direct link to the canonical (direct-to-employer) listing** and "also seen on N." Gated/dealbreaker jobs collapse into the existing "Filtered out" group. Rendered through `_visualizer` per Hard Rule #8 — British English, tier pills, per-dimension breakdown, "⚡ apply early" freshness chips, the existing toolbar. **Scoring, gating, and rendering are reused as-is** — `_job-matcher`/`_gate-engine`/`_visualizer` already accept source-agnostic job blobs; ultramode adds a source chip, the "also seen on N" line, and an "apply at source" CTA, nothing more.

9. **Real-world findings baked into the design** (from this session's live discovery and sweep — see *Validation* below):
   - **HTML is the dominant access reality (~68% of verified sources), not clean APIs.** "HTTP-first" largely resolves to *HTML fetch*, and the robust keyless-JSON-API set is a minority backbone (RemoteOK, Remotive, Himalayas, Arbeitnow, Working Nomads, HN Algolia, WeWorkRemotely RSS + the keyless ATS endpoints). Consequence: the **extension lane is load-bearing, not a fallback** — it does the high-value freelance/community/national-board work. The spec treats the keyless-API backbone as the *efficient core* and the extension lane as a *first-class ingestion mode*.
   - **Free-feed server-side filters are unreliable.** Remotive's `search`/`category` params returned identical unfiltered results for every term; RemoteOK's tag filter was loose. Ultramode **must filter client-side over full text** (title + tags + description) and must not trust documented `category=`/`search=` parameters. Each source records its real `poll_method`.
   - **ATS providers need a company watchlist.** Greenhouse/Lever/Ashby/Workable/Recruitee/Personio/SmartRecruiters/Workday are keyless but per-company (need a board slug). The watchlist **auto-seeds from the tracker's A/B-tier employers** (the companies whose LinkedIn jobs already scored well) plus `requirements.companies_to_target[]`, plus manual add — resolving company→ATS-slug by probe-and-cache.

10. **Out of scope (v0.11.0):** cross-source *persistent alerts/monitoring* (ultramode is pull-on-invoke; scheduled/standing watches are a later phase); Workday-style per-tenant ATS resolution beyond best-effort; FX conversion for rate gates; auto-apply on external sources (apply stays user-driven, in-browser); any browser-automation framework beyond the Chrome extension; deep entity-resolution of near-duplicate community channels.

## Schema impact

Additive; a per-file `schema_version` bump, no destructive migration.

- **Tracker `source`** — today a six-value LinkedIn enum (`Job Alert | Top Picks | Search | Inbox | Saved | Similar`). Replace with a **structured object** `source: { lane, provider, board }` (e.g. `{lane:"ats", provider:"greenhouse", board:"miro"}`; LinkedIn surfaces map to `{lane:"linkedin", provider:"linkedin", board:"<surface>"}`). Readers gain a back-compat shim that lifts the legacy string into `{lane:"linkedin", provider:"linkedin", board:<string>}`. Bumps the tracker file `schema_version` (v2 → v3).
- **External job IDs** — namespaced and filesystem-safe: `<provider>__<board>__<externalid>` (e.g. `greenhouse__miro__4012345`), so tracker keys, score-cache keys, and `jds/<id>.txt` paths never collide across sources.
- **`.job-scout/sources.json`** — new per-workspace registry (the verified discovery output): `{ lane, base_country, target_geography, priority_order, backbone[], sources[] }`; each source carries `{name, url, category, access_lane, endpoint, needs_key, needs_slug, priority, poll_method, notes}`. Regenerable; deletable (absence triggers first-run discovery).
- **`user-profile.json`** — additive: `requirements.base_country` (string, **elicited**), `requirements.target_geography` (string|array), and an `ultramode` block (`{ default: bool, api_keys: {<provider>: "<token>"}, registry_built_at }`). All optional; absent → ultramode off / cold-start.
- **Universal aggregator backbone** ships as a small curated default list in a shared reference (occupation-agnostic, multi-country), so non-tech lanes have coverage before any niche discovery.

## New components

- `skills/ultramode/SKILL.md` — the user command (sweep · `sources` · `onboarding`), `disable-model-invocation: true`.
- `skills/_source-discovery/SKILL.md` — internal: the verified fan-out / live-probe / loop-til-dry engine that builds `sources.json` (dispatched via `Agent`, per the subagent protocol).
- `skills/_source-sweep/SKILL.md` — internal: per-source candidate-collection → **dedupe-before-extract** (Hard Rule #2) → JD fetch → hand to `_job-matcher`; one subagent per source via the protocol; honours per-source `poll_method` and access lane.
- `skills/shared-references/ultramode-sources.md` — source taxonomy, access-lane definitions, the universal backbone list, ATS slug-resolution (probe-and-cache), client-side-filter rule, cross-source dedupe + canonical preference.
- `skills/shared-references/browser-policy.md` — the `WebFetch` carve-out (Decision 1).
- `skills/shared-references/canonical-schemas.md` — structured `source`, namespaced IDs, `sources.json`, profile additions.
- `_visualizer` — new `ultramode` view (or `match-jobs` variant): source chip, "also seen on N," apply-at-source CTA. Templating lives in `_visualizer` per Hard Rule #8.

## Workstream map

| # | Workstream | Touches |
|---|---|---|
| W1 | Access lane + browser-policy carve-out; universal backbone | `browser-policy.md`, `ultramode-sources.md` (new) |
| W2 | Verified discovery engine (`_source-discovery`) + `sources.json` | new internal skill; `canonical-schemas.md` |
| W3 | First-run onboarding (`base_country` explicit) + `/ultramode` command + `/config` toggle | `ultramode` (new), `config`, `analyze-cv` (read-through of CV corpus) |
| W4 | Per-source sweep (`_source-sweep`): dedupe-before-extract, client-side filter, ATS watchlist auto-seed | new internal skill; `linkedin-search.md` (fingerprint reuse) |
| W5 | Schema: structured `source`, namespaced IDs, profile additions, back-compat shim | `canonical-schemas.md`, tracker/profile readers across skills |
| W6 | Adaptive priority + cross-source dedupe + canonical direct-to-employer | `ultramode-sources.md`, `_source-sweep` |
| W7 | Results view (unified, tier-ranked, source chip, direct link) | `_visualizer` templates + `render-orchestration.md` |
| W8 | Keyless-first / keyed opt-in key handling | `config`, `ultramode-sources.md` |

## Validation (already performed this session)

The design was proven before drafting, not after:
- **Verified discovery** was run twice (two-pass, uncapped) for a real lane (NL-based · EU-remote · freelance · Linux/Platform/SRE), producing **174 verified unique sources** from 217 enumerated → 103+ live-probed, each access-lane-classified. Breakdown: ~68% `html`, ~25% `api` (16 keyless incl. ATS, 15 keyed), the rest `rss`/`extension`. This is the worked reference for `sources.json` and the source of Decision 9's findings.
- **The results report** was built end-to-end from **live** data — 39 real infra roles pulled from three keyless sources (WeWorkRemotely, RemoteOK, Arbeitnow), unified, tier-ranked (A→B→C, freshest-first), with real direct links, source chips, a working sort/filter toolbar, and a "Filtered out" group gated on the location dealbreaker — rendered in the exact `_visualizer` theme. It confirmed the view reuses the render layer with only the source chip + alternates added.
- Both artifacts are workspace-scoped (not committed; `.job-scout/` is gitignored).

## Verification (for execution)

No automated suite (per CLAUDE.md). Checks: `jq`-validate a generated `sources.json` against the schema (every source has a valid `access_lane` and `category`, `endpoint` present for `api`/`rss`); `grep` zero-hit sweep confirming the legacy string `source` enum is fully shimmed (no reader assumes a bare string); `python3`+`jinja2` render of the ultramode view against sample payloads (multi-source, gated, empty, "also seen on N"); a live keyless-API smoke (RemoteOK/Remotive/Arbeitnow GET returns parseable JSON, client-side filter yields infra roles); namespaced-ID round-trip (`jds/<provider>__<board>__<id>.txt` writes and reads back); British-English `grep -i` sweep over new user-facing strings; full read-through of each new SKILL.md for subagent-protocol and Hard-Rule conformance.

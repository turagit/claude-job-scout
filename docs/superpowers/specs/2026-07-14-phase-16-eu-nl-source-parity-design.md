# Phase 16 — EU/NL source parity (the Codex handoff port)

**Status:** approved — every decision below was resolved one-by-one in the 2026-07-14 grill session; this document is the record
**Date:** 2026-07-14
**Predecessors:** Phase 14 (deterministic engine spine) · Phase 15 (the ultramode merge)
**Provenance:** the sibling Codex implementation's handoff document — `codex-job-scout` @ `ce72837b` (plugin `0.15.0+codex.20260714074903`), local clone at `../codex-job-scout` — covering its EU/NL source-catalogue release and its first real Ultramode run (2026-07-14), plus an in-session audit of *this* repo confirming which handoff gaps already don't apply here. The Codex repo is a **reference implementation**: contracts and test cases are stolen from it; code is not transplanted.

## 1. Problem

The Codex sibling shipped a versioned EU/NL source catalogue with a hardened admission lifecycle, and its first live run surfaced seven gaps. This plugin — 15 phases deep, with a shipped `_ultra-engine` spine that already covers most of the handoff's orchestration invariants (snapshot-before-fanout, delta envelopes, namespaced IDs, fetch-then-gate, rotation, scorecard, always-render, checkpoints) — lacks the parts that matter for *where we look*:

1. **No packaged source catalogue.** Discovery bootstraps from the lane seed + backbone; there is no versioned, evidence-stamped candidate catalogue for the EU/NL/BENELUX market, and no scope control (`eu-nl` vs `eu-broad`).
2. **No lifecycle hardening.** `sources.json` has no identity aliases, no retirement tombstones, no host-identity normalisation, no projection boundary between catalogue-only fields and the frozen registry schema — so a future catalogue refresh could silently drop user sources or duplicate identities on URL spelling differences.
3. **Auth state is not first-class.** Login-walls live in prose `notes`; the sweep planner cannot distinguish `public / auth-required / signed-in / session-expired` without re-reading free text.
4. **No exhaustive extension-lane mode.** Bare `/ultramode` sweeps *all* public lanes every run (already better than Codex's LinkedIn+4), but the Chrome lane is rotation-only (4/run) with no way to demand "every extension source, now, resumably".
5. **The report auto-open is the same known-broken mechanism** the Codex run hit: `render-orchestration.md` Step E navigates the Chrome extension to `file://<path>`, which browser URL policy rejects.
6. **The BENELUX hole.** The user's highest-value hunting ground (NL + BE + LUX brokers and boards) is exactly the pack the Codex catalogue left empty (`eu-national`: 0 entries), and nothing in the sweep prioritises BENELUX sources.

Audited as **already closed here, no work needed**: handoff gap 5 (scorecard accounting — Phase 15's Step 4f mandates unconditional `jd-fetch.json`/`merge.json` bookkeeping and names the 2026-07-03 defect) and gap 6 (profile freshness — `cv-loading.md` warns at ≥30 days and continues, non-blocking). One residual hardening for gap 5 ships in this phase (D13).

## 2. Decisions locked (the grill record)

| # | Decision |
|---|---|
| D1 | **Phase 16 extension, not a rebuild.** Incremental v0.16.0 on the existing plugin; existing `_ultra-engine` spine, skill topology, and `.job-scout/` workspaces stay backward-compatible. Codex repo is reference-only. |
| D2 | **Re-derived catalogue, bounded.** Start from the 21 Codex candidates; independently re-probe each (sessionless HTTP, fresh `evidence_checked_at`); drop failures; gap-fill. Our own catalogue JSON, Claude-side `catalogue_version: 1`, committed to `skills/shared-references/`; the research record to `docs/superpowers/specs/`. |
| D3 | **BENELUX pack replaces Codex's empty `eu-national`.** Deliberate research hunt for NL/BE/LUX boards and freelance brokers/intermediaries (deep-research harness, multi-angle); capped at ~5 survivors, contract-weighted. |
| D4 | **BENELUX is priority-weighted in the sweep itself.** The adaptive poll-order derivation and the extension-lane rotation weighting rank BENELUX-tagged sources above generic EU/global ones — as a scoring rule in the scripts, not prose. LinkedIn remains always-on and outside rotation. |
| D5 | **Packaged candidates are hypotheses, never auto-admitted.** Admission only via live `/sources rebuild` under the never-fabricate invariant; candidates whose sessionless probe hits an access wall are tagged extension-lane and verified in the user's real browser at rebuild time. |
| D6 | **`auth_state` becomes first-class in `sources.json`**: `public \| auth-required \| signed-in \| session-expired`, plus `auth_state_observed_at` (ISO 8601). It is an *observation with a timestamp*, never a guarantee — the sweep treats it as a hint and still handles `login_required` envelopes gracefully. Schema-version bump + migration (existing entries default from category/notes heuristics) + compat tests. Credentials live exclusively in Chrome; the plugin never sees, stores, or logs them. |
| D7 | **Config contract parity with Codex, verbatim semantics**: `source_scope: "eu-nl"` (default) `\| "eu-broad"`; `source_refresh: "manual"` (only accepted value); missing `source_scope` *reads* as `eu-nl` without being written; unknown config keys are preserved on every write. |
| D8 | **`/sources scope` owns the scope surface.** No-arg shows current; `/sources scope eu-broad` validates, writes, then *offers* (never forces) a rebuild — scope only matters at rebuild time. `/tune` stays vocabulary + gates. |
| D9 | **Global marketplaces stay opt-in behind `eu-broad`** (Contra, Upwork, Freelancer, FlexJobs). On default `eu-nl` they are never admitted — deliberate, given the BENELUX-first, €750/day positioning. |
| D10 | **Manual refresh only**, plus a staleness nag in the ultramode preamble (">90 days since last `/sources rebuild`"). No scheduled automation — standing browser automation collides with hard rule 4. The `source_refresh` key exists and validates so the contract is future-proof. |
| D11 | **Lifecycle invariants land as `_ultra-engine` scripts** (hard rule 9), tested in `tests/run.sh`: catalogue validate/select; projection with catalogue-only field stripping (`lane_tags`, `auth_required`, `evidence_url`, `evidence_checked_at` never reach the registry; final validation rejects leaks); host-identity normalisation (identity = normalised homepage domain + category; endpoint URLs excluded); `identity_aliases` for domain/category migrations; `retired_identities` tombstones (absence from a later catalogue is **not** retirement); user-added sources retained unless explicitly retired; atomic + conflict-aware snapshot/refresh/registry replacement; exact-count invariants (no silently dropped fragment); single `category: linkedin` entry guaranteed. |
| D12 | **`/ultramode super`** — new scope: every enabled extension-lane source (bare already covers all public lanes), deterministic order, per-source checkpoints riding the existing 48h resume machinery; a login-blocked source records its `login_required` envelope and the run moves on. |
| D13 | **Five-way honest accounting in every mode**: attempted / completed / login-blocked / failed / rotated-out, in scorecard and report. Plus the gap-5 hardening: `scorecard.sh` emits an explicit disclosure when `jd-fetch.json` or `merge.json` is absent instead of silently defaulting zeros — script-enforced honesty over prose-enforced. |
| D14 | **Report delivery replaces `file://` Chrome navigation** with harness file delivery (report rendered into the user's panel); OS-opener (`open`/`xdg-open`) fallback where that tool is absent; the existing markdown ask-and-fallback stays for render failures. The extension is never asked to navigate to a local file again. |
| D15 | **Every job carries its direct canonical apply link** — in the terminal summary *and* the report cards. Non-negotiable output rule. |
| D16 | **Login handoff flow**: sweep hits wall → zero-count `login_required` envelope → report names the source, tab left open → the *user* signs in directly in Chrome → `/ultramode source <name>` reruns just that source on the reused session → `auth_state` transitions to `signed-in` with a fresh `observed_at`. The plugin does not claim stored-login support until this is proven live (D18). |
| D17 | **Live acceptance targets: freelance.nl and Malt.** freelance.nl = fresh proof squarely in the NL lane (untouched by the Codex run); Malt = regression check (one of Codex's two observed `login_required` blocks). |
| D18 | **Release gate.** Spec → plan (writing-plans) → TDD task-by-task → independent code review → live acceptance (§5) → v0.16.0 with ROADMAP + CHANGELOG. Until acceptance item 2 passes, docs must not claim stored-login support. |

## 3. Workstreams

### WS-A — Catalogue research + artifact (D2, D3)
Build-time, before any code: re-probe the 21 Codex candidates sessionlessly (exists? serves EU/NL lane-relevant contract roles? login-wall status?); run the BENELUX deep-research hunt (NL brokers/intermediaries beyond Striive/freelance.nl/Nationale Vacaturebank; BE boards and broker platforms — ICTjob.be-class, ProUnity/Connecting-Expertise-class; LUX — jobs.lu/Moovijob-class). Output: `docs/superpowers/specs/2026-07-14-phase-16-source-catalogue-research.json` (evidence trail) and `skills/shared-references/source-catalogue.json` (`catalogue_version: 1`; packs: `eu-core`, `nl-core`, `eu-contract`, `benelux`, and the `eu-broad`-only `authenticated-marketplaces` + `eu-compatible-global`). Every entry carries `evidence_url` + fresh `evidence_checked_at` (catalogue-only fields). The three Codex-failed candidates (DevITJobs NL, Computer Futures NL, Hays NL) are re-probed like everything else — their Codex admission failure was a live outcome, not a catalogue verdict.

### WS-B — Lifecycle scripts (D5, D11)
New `_ultra-engine` scripts (bash + jq; python3 stdlib where bash strains, per the Phase 14 convention), each with contract docs in `_ultra-engine/SKILL.md` and tests in `tests/run.sh`:
- **`catalog.py`** — `validate <catalogue>` (schema, exact pack membership, no duplicate identities post-normalisation) and `select <catalogue> --scope <eu-nl|eu-broad>` (deterministic candidate emission; `eu-broad` ⊇ `eu-nl`).
- **`project.py`** — catalogue candidate → frozen registry-entry shape; strips catalogue-only fields; refuses a projection with null `verified_at`; maps `lane_tags`/probe outcome into `access_lane` + initial `auth_state`.
- **`identity.sh`** — host normalisation (scheme/`www.`/trailing-dot/case) + identity key minting (`domain|category`); the single executable implementation dispatcher and tests both call.
- **`registry_lifecycle.py`** — the atomic rebuild boundary: merges selected candidates into the live registry honouring precedence (`user sources → catalogue → lane seed → universal backbone → live discoveries`), `identity_aliases`, `retired_identities`, user-source retention, exact-count invariants, single-linkedin guarantee; conflict-aware temp-file + validate + rename, same pattern as `merge_tracker.py`.
- `/sources rebuild` (skill prose) orchestrates: select → probe every candidate live (never-fabricate) → project survivors → `registry_lifecycle` merge. `/sources retire <name>` writes a tombstone.

### WS-C — Schema migration: auth state (D6)
Additive `auth_state` + `auth_state_observed_at` on every registry entry; `.job-scout/schema-version` bump with a migration that defaults existing entries (`category: linkedin` → `auth-required`; notes matching login/signup heuristics → `auth-required`; else `public`); compat tests prove a pre-Phase-16 workspace loads, migrates once, and round-trips. Sweep-time transitions: successful read of an `auth-required` source → `signed-in`; a previously `signed-in`/`public` source hitting a login wall → `session-expired` (+ `login_required` envelope either way).

### WS-D — Config + scope surface (D7, D8, D9, D10)
`source_scope`/`source_refresh` in `user-profile.json` with the parity semantics (default-without-write; unknown-key preservation — tested); `/sources scope [value]`; the `eu-broad` marketplaces admitted only under that scope; the ultramode preamble staleness nag.

### WS-E — `/ultramode super` + accounting (D4, D12, D13)
`super` joins the scope grammar (`bare | linkedin | external | source <name> | super`): rotation pick is replaced by *all* extension-lane sources in deterministic order (BENELUX weight, then staleness, then name); each source checkpoints as `sweep-<slug>` so an interrupted super run resumes. `rotation.sh pick` gains the BENELUX priority weighting (bare runs too). `scorecard.sh` gains the five-way accounting block (computed from rotation.json + per-sweep envelopes + checkpoint presence) and the missing-artifact disclosures. The report's scorecard section renders all five counts in every mode.

### WS-F — Report delivery + links (D14, D15)
`render-orchestration.md` Step E rewritten: harness file delivery first, OS opener fallback, markdown fallback retained; the `file://` navigate call deleted. Payload + `_visualizer` + terminal-summary contracts audited so every job line/card carries the canonical apply URL (and `also_seen_on[]` alternates in the report).

### WS-G — Login handoff (D16, D17)
The `login_required` path made explicit in the ultramode + `/sources` prose: envelope → named source in report + terminal ("sign in to <source> in the open tab, then run `/ultramode source <name>`") → rerun transitions `auth_state`. No credential entry, no account creation by the model — the flow pauses and hands the user the browser.

### WS-H — Docs
README, QUICKSTART, COMMANDS, TROUBLESHOOTING: scope control, `super`, the login handoff, the BENELUX story. CHANGELOG v0.16.0; ROADMAP Phase 16 row. Stored-login claim gated on acceptance (D18).

## 4. Contract-test map (the handoff's mandated list → our suite)

All in `skills/_ultra-engine/tests/run.sh` unless noted: exact `eu-nl`/`eu-broad` pack selection · default-without-write config semantics · unknown-config-key preservation · catalogue schema validation · host-identity normalisation · aliases + tombstones (absence ≠ retirement) · user-source retention · atomic refresh/snapshot conflict handling · catalogue-only field stripping (projection + final-validation leak rejection) · exact registry-count invariants · `login_required` zero-count envelope shape (validator fixture) · auth_state transitions incl. signed-in reuse without secret access · super-vs-bare five-way accounting · scorecard missing-artifact disclosure · schema migration round-trip (compat fixture of a pre-Phase-16 workspace) · deterministic payload/report output (existing golden pattern extended).

## 5. Acceptance (hard gates, live workspace)

1. **Rebuild under the new catalogue** on CVFREELANCER: BENELUX-tagged sources visibly outrank generic EU/global in the derived poll order; registry passes final validation; user sources and LinkedIn entry intact; counts reconcile exactly.
2. **Login handoff proven on freelance.nl AND Malt**: first sweep records `login_required`; the user signs in directly in Chrome; `/ultramode source <name>` succeeds on the reused session; `auth_state` transitions observed in `sources.json`. Only after this passes may docs claim stored-login support.
3. **One clean `/ultramode super` run**: all extension sources attempted in deterministic order; login-blocked sources skipped-and-recorded; five-way accounting in the scorecard reconciles with the checkpoint artifacts by `jq` spot-check; report delivered via harness file delivery with a direct apply link on every card and summary line.
4. `bash skills/_ultra-engine/tests/run.sh` ends `ALL PASS`; a pre-Phase-16 workspace fixture migrates cleanly.

## 6. Implementation-level calls baked in (flag at plan review if you disagree)

1. Catalogue file is named **`source-catalogue.json`** (scope-agnostic — it contains both scopes); Codex's `eu-nl-` prefix is not copied.
2. Pack names: `eu-core`, `nl-core`, `eu-contract`, `benelux`, `authenticated-marketplaces`, `eu-compatible-global`. `benelux` is capped at ~5; the empty-pack pattern is not carried over.
3. Rotation default stays **N=4** on bare runs; `super` is the exhaustive path. BENELUX weighting applies to both.
4. `auth_state` transitions are written only from *observed* sweep outcomes — never inferred from elapsed time.
5. Config keys live in `user-profile.json` beside `render` and `ultramode.api_keys`; no new config file.
6. The five-way accounting is computed by `scorecard.sh` from artifacts, never hand-assembled by the dispatcher.
7. British English throughout user-facing copy, per hard rule 7 (`catalogue`, not `catalog`, in prose; script filenames may abbreviate).

## 7. Out of scope / parked

- Scheduled/automatic source refresh (explicitly deferred; `source_refresh` accepts only `manual`).
- Non-BENELUX national packs (DE/FR/Nordics) — later catalogue versions.
- The feedback/learning loop (roadmap Phase C) — unchanged.
- Porting Codex's Python `core/` or CLI shape — reference-only by D1.
- Windows portability beyond the existing bash+jq assumption.

# Phase 14 + 15 — Deterministic engine spine & the ultramode merge (one verb for the whole market)

**Status:** approved — every decision below was resolved one-by-one in the 2026-07-02 grill session; this document is the record
**Date:** 2026-07-02
**Predecessors:** Phase 11 (ultramode multi-source) · Phase 12 (discovery & categorisation foundations) · Phase 13 (discovery hardening)
**Provenance:** live-run audit of the `CVFREELANCER` workspace, 2026-07-02 — `/ultramode` and `/deep-sweep` both run for real, state files audited in-session (`sources.json`, `tracker.json`, `query-stats.json`, `reports/`, `jds/`)

## 1. Problem

Two problems, one root.

**Topology:** two commands split one job. `/deep-sweep` owns LinkedIn; `/ultramode` owns everything else; they are bridged by an opt-in toggle (`ultramode.default`) that the primary user has already turned on — proving the merged experience *is* the product. Meanwhile "where do we look" (registry management) and "go look" (the sweep) share one verb, and vocabulary tuning has no verb at all.

**Fidelity:** the 2026-07-02 run — the first with a fully healthy post-Phase-13 registry (42 sources, all six categories populated) — showed the failure class has moved downstream: **execution drift**. The dispatcher paraphrased the prose contracts at run time. Audit evidence:

1. **0 of 64 external roles had a JD persisted** (`with_jd: 0`); scoring ran on ≤350-char excerpts. Direct casualty: **14 roles gated `work_arrangement (remote not confirmed)`** — killed for *missing* data, not confirmed violations. Several kills were annotated "STRONG IAM+SRE near-miss" by the scorer itself.
2. **The dispatcher improvised its own subagent prompts** instead of loading the `_source-sweep` contract: silent result caps (20–25/cluster; Greenhouse returned exactly 25 = cap hit), ad-hoc IDs (`himalayas-devops-alma`) instead of namespaced `<provider>__<board>__<externalid>`, prose `source` strings (`"ultramode 2026-07-02 [Greenhouse]"`) instead of the structured `{lane, provider, board}`, and no structured `gate_violations[]` persisted (only prose `tier_reason`).
3. **Economics inverted:** 25 of 64 fetches were permanent ATS roles that can never pass this lane's freelance-only gate — filtered at the most expensive stage (scoring) instead of the cheapest (sweep).
4. **The extension lane never ran:** 9 login-walled marketplaces (Malt, Toptal, Worksome, YunoJuno, Lemon.io, freelance.nl…) — for a freelance lane, the crown jewels — produced zero entries. **No report was rendered** (no `ultramode-*.html` exists for the run; tracker was written 11:17, newest report file 08:15).
5. Net yield of the entire external pass: **3 C-tiers, 0 A/B** — while the registry itself was healthy. Phase 13 fixed discovery; execution is now the bottleneck.

**Root cause:** prose contracts degrade under context pressure, and this is strike three — Phase 11 shipped prose, Phase 13 tightened prose with gates and bold MUSTs, and the very next run drifted in five *new* ways. Mechanical work (state, schemas, merges, budgets, ordering) needs determinism; the model should spend its judgement only where judgement is the job (relevance, gating messy text, scoring, prose).

## 2. Decisions locked (the grill record)

| # | Decision |
|---|---|
| D1 | **Sweep-time drop of explicit violations.** A role whose title/body *states* a hard-gate violation (permanent/loondienst, onsite, hybrid) is dropped inside the sweep, before any fetch or scoring. The workspace's gate semantics are passed into the sweep as data. |
| D2 | **Fetch-then-gate for unconfirmed data.** A role failing a gate only on *missing* evidence ("remote not confirmed", no rate shown) gets its full JD fetched first, then is gated on real text. Never gate on absence when presence is one GET away. |
| D3 | **Near-miss rail.** Strong-fit roles that genuinely fail exactly one gate are surfaced in a collapsed "Near-misses — would you bend?" report section instead of being buried in D-tier. |
| D4 | **Gate reads `values[]` as the allowed set — no hard-coded contract taxonomy.** Detachering/secondment counts as freelance for this user (`values: ["freelance","detachering"]`, CVFREELANCER updated 2026-07-02). Plugin-level rule: `_gate-engine` treats `deal_breakers[].values` + `free_text` as the source of truth and never applies its own idea of what "freelance" includes. |
| D5 | **Deterministic scripted spine, delivered as skills.** Mechanical work moves into version-controlled scripts shipped inside an internal engine skill (`_ultra-engine`), each script's contract documented in its SKILL.md. bash + `jq` (python3 stdlib allowed where bash+jq strain); zero installs; the plugin model (skills all the way down) is preserved. |
| D6 | **Topology: `/ultramode` is the flagship.** Bare `/ultramode` = weekly full-market scan (LinkedIn + every registry source), one unified ranked report. Scopes: `/ultramode linkedin`, `/ultramode external`, `/ultramode source <name>`. New small `/sources` command (list / add / rebuild / lane interview) absorbs `/ultramode sources*` + `onboarding`. `/deep-sweep` becomes a one-release deprecation alias. The `ultramode.default` toggle retires (config migration: ignored with a note). `/check-job-notifications` (daily driver) and `/job-search` (surgical) unchanged. |
| D7 | **Checkpointed stages + always-render.** Every stage persists its artifact as it completes; an interrupted run is detected and resumed, not restarted; the report renders at the end of whatever completed. A partial report always beats none. |
| D8 | **Extension-lane rotation.** Login-walled sources are swept ~4/run, staleness-ordered, so each is hit at least fortnightly at weekly cadence. `/ultramode source <name>` forces any specific one now. |
| D9 | **JD-fetch budget, disclosed.** Soft cap ~75 full-JD fetches/run; overflow goes to a persisted deferred queue served first next run; the cap and carry-over are stated in the report. Caps are fine; silent caps are the defect. |
| D10 | **Wall-clock envelope: 30–45 min** for the full weekly pass. |
| D11 | **`/tune` = vocabulary + gates.** No-arg shows the full hunting vocabulary (titles, clusters, capability-graph status, jargon aliases, exclusions) *and* the hard gates; subcommands add/remove titles/keywords/exclusions and adjust gates (e.g. rate floor) without re-running the CV interview. One vocabulary model feeds both LinkedIn and external lanes. Target companies stay with `/sources add` (a *where*, not a *what*). |
| D12 | **Per-run scorecard.** Every run ends with (and embeds in the report) an honest accounting: sources swept / skipped / rotated-out, candidates seen, new-after-dedupe, gated with per-reason counts, near-misses, JD fetches used vs deferred, A/B/C yield, per-stage timings. |
| D13 | **Feedback loop deferred** to its own phase (reject-reason re-weighting etc.) — except **`/bend <id>` ships now** with the rail: one-shot re-score of a near-miss as if its failed gate were relaxed, recorded on the entry (`bent: true` + note). `/bend` does not modify `deal_breakers` — learning from bends belongs to the feedback phase. |
| D14 | **Sequencing: engine before face.** Phase 14 (v0.14.0) = engine correctness, topology untouched. Phase 15 (v0.15.0) = the merge + new surfaces. **Publish gate:** two consecutive clean weekly runs on both live workspaces (CVFREELANCER freelance lane + CVDIRECTOR permanent lane), then a publish-readiness pass. |

## 3. Phase 14 design — engine correctness (v0.14.0)

Command names and roles do not change in this phase. Everything below makes the *existing* commands stop lying.

### WS-A — the `_ultra-engine` spine
*New internal skill: `skills/_ultra-engine/` — SKILL.md documents each script's I/O contract; scripts live in `skills/_ultra-engine/scripts/`.*

Deterministic scripts (bash + jq; python3 stdlib where noted):

- **`snapshot`** — build `cache/ultramode-snapshot.json` (known IDs + fingerprints) from the tracker in one pass. Blesses the pattern today's run improvised, as the documented contract (subagents read the file; the envelope carries its path, not 1,300 fingerprints).
- **`fingerprint`** — the canonical cross-source fingerprint + `normalise_location`, as the single executable implementation both dispatcher and tests call.
- **`namespace-id`** — `<provider>__<board>__<externalid>` with deterministic slug fallback when a source exposes no stable ID.
- **`merge-tracker`** (python3) — serial, schema-validating, atomic tracker merge: enforces structured `source`, namespaced IDs, `gate_violations[]` shape, canonical-winner selection + `also_seen_on[]`; **rejects a malformed delta loudly instead of absorbing it**. Existing entries are never rewritten (IDs are immutable forever); legacy prose `source` strings are parsed to structured on read via the existing shim, new writes are structured-only.
- **`validate-delta`** — pre-merge validation of every sweep return against the delta schema.
- **`checkpoint`** — stage artifacts under `cache/run/<date>/`; detects a partial run for resume (D7).
- **`rotation`** — staleness-ordered pick of N extension-lane sources; bookkeeps `last_swept_at` per source in `sources.json` (additive field) (D8).
- **`jd-queue`** — the deferred-fetch queue with budget accounting (D9).
- **`scorecard`** — assembles the run scorecard from checkpoints (D12); the render payload embeds it.
- **`payload`** — deterministic assembly of the render payload (tier ordering, within-tier confidence sort, near-miss section, disclosure lines) so ordering rules stop living in prose.

**Prompt templates, not improvised prompts:** `_source-sweep` gains verbatim per-lane prompt templates (`api` / `rss` / `html`) in its references; the dispatcher fills declared variables (source entry, snapshot path, lane keywords, gate semantics, caps) and changes nothing else. Caps are parameters and always disclosed in the return envelope.

### WS-B — pipeline order (D1, D2, D9)
1. Sweep applies occupation filter + **explicit-violation drop** (gate semantics passed in as data — allowed contract values incl. detachering, remote requirement) and returns per-source counts including drops.
2. **Fetch-then-gate stage:** candidates failing gates only on missing evidence enter the JD-fetch queue (budgeted); gate runs on full text. Scoring requires `jd_path` — the matcher refuses to score an external role without a persisted JD (or records exactly why in the scorecard).

### WS-C — near-miss rail + `/bend` (D3, D13)
- `gate_violations[]` restored as structured data (kind + detail), `tier_reason` stays the human string.
- Near-miss rule (precise, in `_gate-engine` reference): **exactly one** gate kind failed AND dimension evidence is A/B-grade. Entry gains `near_miss: true`.
- `_visualizer`: collapsed "Near-misses — would you bend?" section listing the failed gate per role + the `/bend <id>` affordance.
- New tiny command skill **`/bend <id>`** (`disable-model-invocation: true`): re-gates + re-scores that one role with the named gate relaxed, updates the entry (`bent: true`, audit note), re-renders or prints the delta.

### WS-D — extension lane runs, render always runs (D7, D8)
- Main-thread extension sweep is a checkpointed stage with the rotation applied; each source's delta checkpoints before the next opens.
- Render is unconditional at pipeline end — whatever stages completed, a report ships, marked partial where partial.

### WS-E — migration / back-compat
- Tracker: no ID rewrites; `source` normalisation on read; additive fields only (`near_miss`, `bent`, `gate_violations[]` re-population happens lazily as entries are touched).
- `sources.json`: additive `last_swept_at`.
- Profile: none in Phase 14.

### Phase 14 acceptance (hard gates)
- A full `/ultramode` run on CVFREELANCER where: every scored external entry has `jd_path`; zero prose `source` strings written; all new external IDs namespaced; ≥3 login-walled marketplaces actually swept; the scorecard's counts reconcile with `tracker.json` by `jq` spot-check; any truncation is disclosed; detachering roles at/above the rate floor pass the gate; the near-miss rail renders.
- **Kill-test:** interrupt the run mid-scoring → re-invoke → run resumes from checkpoints and still renders a report.
- **The spine has a real test suite** (the repo's first): script-level tests for fingerprint/namespace/merge/rotation/queue runnable via one entry point (`skills/_ultra-engine/tests/run.sh`), documented in CLAUDE.md's testing section.

## 4. Phase 15 design — the merge (v0.15.0)

### WS-F — `/ultramode` flagship + scopes (D6)
- Bare `/ultramode` = LinkedIn query plan + external registry sweep in one checkpointed pipeline, one unified report (near-miss rail, scorecard, disclosure lines). LinkedIn becomes a registry source entry (`{lane: "extension", provider: "linkedin"}`) whose adapter is the existing query plan — canonical preference (`ATS > LinkedIn > aggregator > marketplace`) already knows where it ranks.
- `/ultramode linkedin` ≈ today's deep-sweep; `/ultramode external` = external only (no Chrome needed); `/ultramode source <name>` = one source now (bypasses rotation).

### WS-G — `/sources` (D6)
- `list` (registry + per-source last-swept/yield), `add <url|name>` (probe, classify, admit — company names resolve via ATS resolver), `rebuild` (re-discovery through the Phase 13 gates), first-run lane interview when no registry exists.

### WS-H — `/tune` (D11)
- No-arg display of vocabulary + gates; `add/remove title`, `add/remove keyword`, `exclude <term>`, gate adjustments (`rate-floor`, contract values, arrangement).
- **Cache-invalidation contract (spine):** vocabulary/gate edits update `profile_hash` semantics correctly so stale cached scores/gates re-evaluate lazily — fixing the class of staleness found when the detachering rule was hand-applied (already-gated roles stayed wrongly D-tier).

### WS-I — retirement + docs
- `/deep-sweep` → deprecation alias (prints pointer, runs the merged pass) for one release, then removal.
- `ultramode.default` retired; config migration ignores it with a one-time note.
- README / QUICKSTART / command docs rewritten around: `/analyze-cv` → `/sources` → `/ultramode` weekly → `/check-job-notifications` daily → `/tune` between runs.

### Phase 15 acceptance (hard gates)
- Bare `/ultramode` completes LinkedIn + external ≤45 min with checkpoints on a live workspace; `/ultramode linkedin` reproduces old deep-sweep behaviour; `/sources list|add|rebuild` round-trip; `/tune add title` shows up in the next run's plan; `/deep-sweep` prints the deprecation pointer and still works; a **fresh scratch workspace** goes interview → registry → sweep → report end-to-end.
- **Publish gate (D14):** two consecutive clean weekly runs on CVFREELANCER *and* CVDIRECTOR, then publish-readiness (README, marketplace listing, cold-start walkthrough).

## 5. Implementation-level calls baked in (flag at plan review if you disagree)

1. **IDs are immutable forever** — dedupe anchors on them; only the `source` field normalises (on read).
2. **Prompt templates** live in `skills/_source-sweep/references/`, loaded verbatim; the dispatcher fills declared variables only.
3. **python3 (stdlib only)** allowed for merge/validation; everything else bash + `jq`. No installs, no network in scripts except where the script *is* the fetcher.
4. Rotation default **N=4**; JD-fetch cap default **75** — both parameters, not prose.
5. Near-miss requires **exactly one** failed gate kind; two failed gates is honest D-tier.
6. `/bend` never edits `deal_breakers` — bend-pattern learning is the feedback phase's job.
7. The engine skill is named **`_ultra-engine`** (internal, `_`-prefixed per house convention).

## 6. Out of scope / parked

- The full feedback/learning loop (reject-reason re-weighting, approved-corpus boost — roadmap "Phase C").
- Continuous x-ray source discovery (search-engine `site:` sweeps feeding `/sources rebuild`).
- Cross-lane pointers between workspaces ("this permanent role fits your CVDIRECTOR lane").
- Keyed-aggregator expansion (Adzuna/Jooble stay opt-in as shipped).
- Windows portability beyond documenting the bash+jq assumption.

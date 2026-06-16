# Phase 13 — Ultramode discovery hardening (sources that actually surface)

**Status:** proposed (awaiting approval)
**Date:** 2026-06-16
**Predecessors:** Phase 11 (ultramode multi-source) · Phase 12 (discovery & categorisation foundations)
**Provenance:** `2026-06-16-phase-13-verified-sources-research.json` (58 live-verified sources, this lane, 2026-06-15/16)

## 1. Problem

`/ultramode` first-run discovery is supposed to build a large, lane-specific, **verified** source registry. In the live `CVFREELANCER` workspace (freelance / Linux-Platform-SRE-DevOps / NL base / EU-UK remote) it produced a **backbone-only registry: 10 sources, 0 discovered, 2 of them keyed-and-skipped → 8 swept.** Every role found was permanent-FTE and gated out (the user is freelance-only), so the run surfaced nothing.

This violates the original, user-declared non-negotiable: *first-run discovery must collect the maximum sources possible.*

**The "170 sources" the user remembers never existed in any workspace** — they were a design-time research artifact from Phase 11 spec validation, never shipped as a seed and never written to `sources.json`. The plugin ships a **10-entry universal backbone** + a live discovery engine meant to rebuild the big list per workspace. The engine returned nothing beyond the backbone.

### Market proof (the bug is not "the lane is dry")

A parallel adversarial verification pass found **58 real, currently-reachable, lane-relevant sources** for this exact lane, every one individually probed live — vs the **0** the engine persisted:

| category | verified | highlights |
|---|---|---|
| ATS company boards (keyless) | 14 | Canonical (41 remote Linux roles), Grafana Labs, GitLab, N26 (IAM/IDM!), Wise, Adyen, Mollie |
| freelance marketplaces | ~16 | Malt, YunoJuno, Worksome, Braintrust ($140-190/hr infra), hackajob, IT-Contracts.nl, freelance.nl |
| NL/EU national boards | ~12 | JustJoin.it (keyless JSON, b2b filter), Landing.jobs (keyless JSON, Contractor filter) |
| remote boards | 5 | Jobicy (keyless API+RSS, contract param), Arc.dev, WWR DevOps RSS |
| community/aggregator | ~11 | HN Algolia, kube.careers, web3.career |

The two categories the engine returned at **literally zero** — `ats-provider` and `freelance-marketplace` — are exactly the two with **no backbone seed** and the two most blocked by the over-strict admission gates. That is the fingerprint of a structural blind spot + an unenforced dispatch, not a thin market.

## 2. Root cause (ranked, from static analysis + the live pass)

1. **No dispatch enforcement (primary, high confidence).** `/ultramode` Step 3e is fully self-sufficient: it re-resolves the 10 backbone bodies straight from `ultramode-sources.md` using only `base_country`, "unions" a discovered fragment that may never have been produced, writes a valid 10-entry `sources.json`, and stamps `registry_built_at` **unconditionally**. Nothing asserts the `_source-discovery` Agent call happened or that its delta was parsed. An interactive run that does the interview + resolves the backbone + writes the file satisfies every literal instruction while silently skipping the expensive, invisible discovery fan-out.
2. **ATS lane structurally dark (high).** The backbone has **zero `ats-provider` entries**; the ATS axis resolves *companies*, not generic providers; on a cold tracker the watchlist seeds from `companies_to_target[]` **only**, which is empty on a fresh workspace. So the highest-value category cannot appear on first run regardless of probe success — yet the live pass resolved 14 keyless boards from cold guesses alone.
3. **Silent-failure swallow (high).** The hard "empty confirmed-set → backbone-only, never fabricate" invariant is correct anti-hallucination policy but doubles as a total failure swallow: never-dispatched, dead probe tools, over-strict gates, and a genuinely thin lane all render as the *identical* 10-entry registry with the timestamp set. The dispatcher cannot tell "ran and thin" from "never ran." There is no `errors[]`-on-empty rule and no loud-warning-on-zero-discovered rule.
4. **No freelance-marketplace seed + Gate A drops login walls (high).** Backbone has zero marketplace entries; marketplaces are login-walled; **Gate A drops a non-2xx/empty body before the login-walled→extension rule can fire**, so 403/Cloudflare-blocked marketplaces (Malt, Toptal, Proxify) are dropped rather than retained into the extension lane. For a freelance-only user this empties the single most important category.
5. **Over-strict admission, Gate B conflation (med).** Gates A+B+C are all-or-nothing, total-drop, multiplicative. Gate B conflates "serves the occupation" with "has freelance roles *right now*" — so structurally-valid boards get dropped because today's listings skew permanent. Contract-type filtering belongs at **sweep time** (where `derive_priority_order` already plans to contract-filter), not at discovery-time source admission.
6. **`probe_failed` indistinguishable from `lane_dry` (med).** If WebFetch/WebSearch fail inside the subagent (403/ECONNREFUSED), Gate A drops 100% and the engine returns a clean-but-empty `status: ok` — accepted as a complete dry discovery. No `tool_unavailable`/`probe_failed` code exists; the only re-dispatch trigger is `status: partial`. *(Note: the Phase-13 investigation's own workflow subagents successfully ran WebFetch/WebSearch and verified 58 sources, so web tools DO work in subagents here — this is a lower-likelihood contributor than 1–4, but the missing signal must still be added.)*
7. **`budget_lines: 200` truncation (low).** A multi-round web loop shares the single-scoring-batch default; can bite mid-round-1 with `confirmed` still empty.

## 3. Design — three workstreams

**Guiding principle, preserved throughout:** *nothing enters `sources.json` unverified.* Every relaxation below is on the **enforcement, retention, and admission-criteria** side. Curated seeds are **candidates that are still live-probed before admission** — provenance-from-file (exactly like the existing backbone), not fabrication.

### Workstream A — Dispatch enforcement & auditable failure
*Files: `skills/ultramode/SKILL.md`, `skills/_source-discovery/SKILL.md`*

- **A1 — Parsed-delta gate.** Rewrite Step 3e to **refuse to persist** unless it has parsed a real `_source-discovery` delta envelope from an actual Agent-tool call. Add an explicit gate line: *"If you did not call the Agent tool in Step 3d, you have NOT completed Step 3 — do not write `sources.json`."* Log the dispatch (and any documented `Agent`-unavailable fallback) in the run output so its absence is visible.
- **A2 — Count invariant.** Before the atomic rename, assert `len(sources) == len(backbone) + len(fragment.sources) + len(user_sources)`. Fail loudly on mismatch (catches a fragment silently dropped at merge).
- **A3 — Known-rich-lane acceptance gate.** After merge, for a lane that *should* be rich (tech / freelance / EU-remote), assert the registry holds **≥ N verified non-backbone sources**, lane-conditioned (see §4 decision 1). Below threshold → **do not silently write**: warn, populate `errors[]` naming every dry lane, show the shortfall in the approval table, and **offer an immediate `/ultramode sources` re-dispatch**; only write a below-threshold registry on explicit user acknowledgement.
- **A4 — Approval-table transparency.** Echo the **discovered-source count + per-category breakdown** in the Step 3e approval table, so a zero-discovered union is visible *before* write (today it is invisible).
- **A5 — Mandatory loop-until-ok + raised budget.** Raise `_source-discovery` `budget_lines` well above the 200 single-batch default (it is a multi-round web loop). Make the dispatcher's continuation loop mandatory: never persist on `status: partial`, always re-dispatch the `continuation_cursor`, and treat a `status: ok` whose confirmed-set is empty after a single round as **suspect → re-probe before persist.**
- **A6 — Mandatory `errors[]`-on-empty.** Strengthen the hard invariant in `_source-discovery`: an empty/below-threshold confirmed-set **MUST** emit a populated `errors[]` enumerating every dry lane by name + round count + probe-attempt count. Converts the silent swallow into an auditable, retryable signal.

### Workstream B — Seed the structurally-dark lanes
*Files: `skills/shared-references/ultramode-sources.md`, `skills/ultramode/SKILL.md`*

- **B1 — Curated ATS watchlist seed.** Add a baked, version-controlled `## Curated lane seed` map of `{company → {provider, slug, lane_tags, verified_at}}` (seed set from the research artifact: Canonical, Grafana Labs, GitLab, N26, Wise, Datadog, Adyen, Mollie, …). On first run with empty `companies_to_target`, the ATS axis runs a **slug-resolution pass over this seed**: fan out across the 8 keyless ATS providers in the resolver table, keep the provider returning `200 + jobs>0 + identity-check` (verify job-URL host / company-name to defeat slug collisions like greenhouse `bird`), cache to `cache/ats-slugs.json`. **Each seed is re-probed live — the baked slug is a candidate, not an admission.** Treat empty `companies_to_target` as a **named critic gap**, not a silent skip.
- **B2 — Freelance-marketplace beachhead.** Add a curated freelance-marketplace seed (Malt, YunoJuno, Worksome, hackajob, Braintrust, IT-Contracts.nl, freelance.nl, …), classified `extension` where login-walled and `html` where public, applied for any workspace whose `contract_type` includes `freelance`. The backbone currently has **zero** marketplace entries.
- **B3 — Keyless-feed enrichment.** Add the newly-verified keyless feeds to the backbone (occupation-agnostic: Jobicy api+rss) and to a **lane-specific discovery seed** for tech lanes (JustJoin.it api, Landing.jobs api, WWR category RSS, kube.careers, Arc.dev, web3.career). Refine the existing Remotive/WWR/Himalayas poll_methods with the verified category/contract query params + RSS endpoints captured in the research artifact.
- **B4 — Onboarding target companies.** Add a Step 3c-bis: optionally ask the candidate for **2–5 target companies** (and/or derive candidates from the CV's employer history / `target_titles`) → write to `requirements.companies_to_target[]`, so the ATS resolver has a non-empty seed on the very first run instead of waiting for LinkedIn sweeps to populate tiered employers. Low-friction, optional.
- **B5 — Never-fabricate carve-out clause.** Add an explicit clause to the `_source-discovery` hard invariant: *a curated, version-controlled, re-probed-on-use seed list is provenance-from-file (like the backbone), NOT fabrication.* Prevents implementers reading B1–B3 as an invariant violation; the live re-probe is what keeps it honest.

### Workstream C — Honest probing & sane admission
*Files: `skills/_source-discovery/references/discovery-protocol.md`, `skills/_source-discovery/SKILL.md`*

- **C1 — Login-wall ≠ dead host.** Amend Gate A so a `401/403`/Cloudflare-style challenge, or a known-marketplace host returning a login/anti-bot page, is **routed to the extension lane and retained** (`access_lane: extension`, empty `endpoint`), exactly like user sources. Only a true non-2xx on an *unrecognised/parked* domain drops. Recovers the Toptal/Proxify/Malt class.
- **C2 — Split admission from contract-type.** Relax Gate B to admit a board that is **live AND serves the occupation** (field/synonyms), decoupled from whether today's postings carry freelance roles. Move `contract_type` filtering to **sweep time**. Replace all-or-nothing total-drop with: drop only on dead/off-occupation; **retain on-occupation-but-permanent-today with a note.**
- **C3 — `probe_failed` / `tool_unavailable` code.** Require the subagent to emit `tool_unavailable`/`probe_failed` (not `lane_dry`) when N consecutive WebFetch/WebSearch calls fail outright. The dispatcher treats `probe_failed` as a **hard error to surface/retry on the main thread** — never a clean backbone-only `ok`. Lets the dispatcher tell a dead probe lane from a dry one.

## 4. Decisions baked in (flag at approval if you disagree)

1. **Acceptance threshold (A3):** lane-conditional, **not** a flat count. Recommend: a known-rich lane must yield **≥ 5** verified non-backbone sources; **and when `contract_type` includes `freelance`, require ≥ 1 `freelance-marketplace` AND ≥ 1 `ats-provider` present.** (A flat N≥5 could be satisfied by remote-boards alone while the two dark categories stay empty — the exact failure we are fixing.)
2. **Below-threshold UX (A3):** warn + populate `errors[]` + offer immediate re-dispatch + **require explicit acknowledgement** before writing a thin registry. Do not hard-block (a genuinely thin niche lane must still be able to proceed), but never write thin *silently*.
3. **Probing stays in the subagent**, not moved to the main thread (the investigation proved web tools work in subagents), **plus** the C3 `probe_failed` signal and a main-thread retry fallback for the dead-probe case.
4. **Seed maintenance:** seeds carry `verified_at`; they are **re-probed live at resolution time**, so staleness self-heals (a migrated ATS or changed anti-bot posture simply fails the live probe and is skipped/extension-routed). No background refresh job in this phase.

## 5. Acceptance criteria

**Hard gates (automated/spot-checkable):**
- For the `CVFREELANCER`-shaped fixture lane, first-run discovery yields **≥ 5 verified non-backbone sources, including ≥ 1 `ats-provider` and ≥ 1 `freelance-marketplace`**, OR fails loudly with `errors[]` naming every dry lane + an offer to re-dispatch.
- Count invariant `len(sources) == backbone + fragment.sources + user_sources` asserted before write.
- **Never-fabricate preserved:** every admitted source (incl. every curated seed) carries a `verified_at` from a live probe at resolution time; no unprobed entry reaches `sources.json`. (Spot-check: no seed appears in a workspace registry without a fresh `verified_at`.)
- A simulated dead-probe run emits `probe_failed`, not a clean backbone-only `ok`.
- No XML/angle-bracket tokens in any SKILL `description` (the standing Phase-11 regression guard).
- **Back-compat:** an existing backbone-only `sources.json` still loads; re-running `/ultramode sources` upgrades it; no migration required.
- **Scorer untouched:** no `rubric_version` bump, score-cache key unchanged, no re-score storm (this phase touches discovery/registry only, never the matcher).

**Soft gates (interactive):**
- The Step 3e approval table shows the discovered-source count + per-category breakdown.
- A re-run in `CVFREELANCER` surfaces ATS boards (Canonical/Grafana/GitLab/N26…) and freelance marketplaces, and the sweep produces freelance/contract roles that clear the gate.

## 6. Non-goals

- No change to the scorer, tier rubric, gate engine, or score-cache key.
- No new browser-automation framework; the Chrome-extension-only rule and the read-only `WebFetch` carve-out are unchanged.
- No background/scheduled seed-refresh job (self-healing via live re-probe is sufficient for this phase).
- Not committing any `.job-scout/` workspace state.

## 7. Rollout

- SemVer **minor**: v0.13.0 (user-visible: richer first-run discovery + the new onboarding company question + the acceptance gate).
- `CHANGELOG.md` section; `docs/ROADMAP.md` Phase 13 entry.
- Build via subagent-driven-development (per-task spec + quality review, final coherence review), matching Phases 11–12.

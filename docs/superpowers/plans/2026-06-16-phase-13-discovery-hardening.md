# Phase 13 — Discovery hardening — implementation plan

Spec: `../specs/2026-06-16-phase-13-discovery-hardening-design.md`
Provenance: `../specs/2026-06-16-phase-13-verified-sources-research.json`
Method: manual execution (tightly-coupled markdown), then adversarial review workflow. Target: **v0.13.0**.

Files touched: `skills/shared-references/ultramode-sources.md`, `skills/shared-references/canonical-schemas.md`, `skills/_source-discovery/SKILL.md`, `skills/_source-discovery/references/discovery-protocol.md`, `skills/ultramode/SKILL.md`, `skills/_source-sweep/SKILL.md`, `CHANGELOG.md`, `docs/ROADMAP.md`, `.claude-plugin/plugin.json`.

---

## Task 1 — Curated lane seed + backbone enrichment (`ultramode-sources.md`)  [B1, B2, B3, B5]
Add a new `## Curated lane seed (provenance-from-file, re-probed on use)` section after the Universal Backbone:
- **ATS seed** — the 14 verified `{company, provider, slug, lane_tags, verified_at}` entries from the research artifact + the 5 keyless endpoint patterns. State the first-run resolution rule (fan out 7 providers, keep `200 + jobs>0 + identity-check`, cache to `cache/ats-slugs.json`).
- **Freelance-marketplace beachhead** — the verified set, `extension` where login-walled / `html` where public; applies when `contract_type` includes `freelance`.
- **Keyless-feed enrichment** — Jobicy (api+rss) as a backbone addition; JustJoin.it/Landing.jobs/kube.careers/Arc.dev/web3.career as a lane-specific tech seed. Refine Remotive/WWR/Himalayas poll_methods with verified params.
- **B5 carve-out clause**: curated, version-controlled, re-probed-on-use seeds are provenance-from-file (like the backbone), NOT fabrication.
**Verify:** `grep -n "Curated lane seed" ultramode-sources.md`; the 14 ATS slugs + 5 endpoint patterns present; carve-out clause present; no angle-bracket tokens leak into any SKILL description.

## Task 2 — Schema additions (`canonical-schemas.md`)  [A2, A6, B1, C3]
- Curated-seed entry shape (`company/provider/slug/lane_tags/verified_at`; marketplace `name/url/access_lane/needs_key/verified_at`).
- New `errors[]` codes: `probe_failed`, `tool_unavailable` (distinct from `lane_dry`), `ats_watchlist_coldstart` (already exists — confirm), `discovered_below_threshold`.
- Note the count invariant (`len(sources) == backbone + fragment.sources + user_sources`) and that every admitted source carries a probe-time `verified_at`.
**Verify:** `grep -n "probe_failed\|tool_unavailable\|below_threshold" canonical-schemas.md`; shapes additive (no rename of existing fields); `rubric_version`/score-cache text untouched.

## Task 3 — Discovery subagent contract (`_source-discovery/SKILL.md`)  [A6, C3, B5, A5]
- A6: empty/below-threshold confirmed-set MUST emit populated `errors[]` naming every dry lane + round/probe counts.
- C3: emit `probe_failed`/`tool_unavailable` (not `lane_dry`) on N consecutive outright tool failures.
- B5: add the never-fabricate carve-out clause (seeds are provenance-from-file, still re-probed).
- A5: note budget raised + multi-round loop; ATS/marketplace seed resolution is part of the engine.
**Verify:** `grep` for the new codes + carve-out; Hard-invariant section still forbids unprobed admission; no angle-brackets in description.

## Task 4 — Verification gates (`discovery-protocol.md`)  [C1, C2, B1]
- C1: Gate A — recognised login-wall / 401-403 / known-marketplace host → route to `extension` lane and RETAIN (not drop); only non-2xx on unrecognised/parked domains drops.
- C2: Gate B — admit on live + on-occupation; decouple from contract-type (moved to sweep time); replace total-drop with retain-on-occupation-permanent-today-with-note.
- B1: document the ATS-seed slug-resolution pass with the identity check (defeat slug collisions).
**Verify:** `grep` Gate A/B retention language; the "dropped, not downgraded" absolutism is replaced; identity-check present.

## Task 5 — Dispatcher enforcement + onboarding (`ultramode/SKILL.md`)  [A1, A2, A3, A4, A5, B4]
- A1: Step 3e refuses to persist without a parsed `_source-discovery` delta; explicit "if you didn't call the Agent tool, Step 3 is not done" gate; log the dispatch.
- A2: assert count invariant before atomic rename.
- A3: known-rich-lane acceptance gate, lane-conditional (freelance ⇒ ≥1 marketplace AND ≥1 ATS; else ≥5 non-backbone); below-threshold → warn + `errors[]` + offer re-dispatch + require ack.
- A4: approval table echoes discovered count + per-category breakdown.
- A5: raise `budget_lines`; mandatory loop-until-ok; never persist on `partial`; empty-after-one-round → re-probe.
- B4: Step 3c-bis — optionally collect 2–5 target companies (or derive from CV employer history) → `requirements.companies_to_target[]`.
**Verify:** `grep` for the gate lines + count invariant + 3c-bis; Step 3e no longer self-sufficient; no angle-brackets in description.

## Task 6 — Sweep-time contract filtering (`_source-sweep/SKILL.md`)  [C2, B1]
- Receive contract-type filtering that discovery no longer applies: the sweep's client-side filter + gate engine handle `contract_type` at role level.
- ATS watchlist cold-start: integrate the curated ATS seed when `companies_to_target` is empty.
**Verify:** `grep` contract-filter-at-sweep language; ATS seed referenced; scorer path unchanged.

## Task 7 — Version + docs  [rollout]
- `.claude-plugin/plugin.json` → `0.13.0`.
- `CHANGELOG.md` → `## [0.13.0]` Keep-a-Changelog section.
- `docs/ROADMAP.md` → Phase 13 entry (status, what shipped).
**Verify:** `jq -r .version .claude-plugin/plugin.json` == `0.13.0`; CHANGELOG + ROADMAP updated.

---

## Final gates (review workflow + spot-checks)
- Adversarial review: spec-compliance per file · cross-file coherence (shape/cross-ref consistency) · never-fabricate-invariant audit · no-angle-bracket scanner across all SKILL descriptions.
- `jq . docs/superpowers/specs/2026-06-16-phase-13-verified-sources-research.json` valid.
- No `rubric_version` bump anywhere; score-cache key unchanged.
- Plugin still loads (no "validation failed"): every SKILL `description` free of `<...>` tokens.

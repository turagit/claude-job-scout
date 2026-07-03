# Phase 15 — The Ultramode Merge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `/ultramode` the single flagship full-market verb (LinkedIn joins the source registry), land `/sources` and `/tune`, retire `/deep-sweep` to a deprecation alias and kill the `ultramode.default` toggle.

**Architecture:** LinkedIn becomes a registry source entry whose adapter is the existing query plan (`references/linkedin-adapter.md`, produced from `/deep-sweep`'s dying body); the Phase-14 engine pipeline is untouched — the adapter just feeds it the same validated delta envelopes as every other source. Registry management moves to a new `/sources` command; vocabulary/gate tuning to a new `/tune` command backed by a tiny new engine script (`profile_hash.sh`) so edits invalidate cached scores deterministically.

**Tech Stack:** Markdown command skills + one bash/jq engine script; no new dependencies. Spec: `docs/superpowers/specs/2026-07-02-phase-14-15-engine-spine-and-merge-design.md` §4 (WS-F/G/H/I), decisions D6/D11/D14.

## Global Constraints

- **British English** in all user-facing copy; identifiers exempt (CLAUDE.md hard rule 7). Every user-invocable command carries `disable-model-invocation: true` (hard rule 4).
- **The Phase-14 engine is load-bearing and frozen this phase** — no edits to existing `skills/_ultra-engine/scripts/*` (one NEW script is added); mechanical ops stay script calls (hard rule 9). `bash skills/_ultra-engine/tests/run.sh` must end `ALL PASS` after every task.
- **Additive schema only:** the registry may gain a `linkedin`-category entry; `requirements.exclusion_terms[]` is new-optional; `ultramode.default` is retired READ-side (never written, ignored when present — no migration rewrite of user files).
- **The daily driver (`/check-job-notifications`) and `/job-search`'s LinkedIn mechanics are untouched** except the one Step-7 widening removal named in Task 6.
- **`/ultramode linkedin` must reproduce the old `/deep-sweep` behaviour** (query plan v2, Past Week pages 1–3, Top picks + Saved, similar-jobs expansion, query-stats writes) — spec §4 acceptance.
- Commit messages: `Phase 15 Task N: <summary>`, ending with the footer:
```
Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01CuUKc5Ax8CPosmz74aieAY
```
- Repo path contains spaces — quote it in every shell command. macOS bash 3.2; `jq`, `python3`, `shasum` available.

## File Structure (locked)

```
skills/_ultra-engine/scripts/profile_hash.sh     # NEW (Task 1)
skills/_ultra-engine/tests/test_profile_hash.sh  # NEW (Task 1)
skills/sources/SKILL.md                          # NEW (Task 2) — registry management verb
skills/ultramode/SKILL.md                        # MODIFIED (Task 3) — flagship + scopes
skills/ultramode/references/linkedin-adapter.md  # NEW (Task 4) — LinkedIn as a source
skills/tune/SKILL.md                             # NEW (Task 5) — vocabulary + gates verb
skills/deep-sweep/SKILL.md                       # REPLACED BODY (Task 6) — deprecation alias
skills/job-search/SKILL.md                       # MODIFIED (Task 6) — Step 7 widening removed
skills/config/SKILL.md                           # MODIFIED (Task 6) — default-toggle retired
skills/shared-references/canonical-schemas.md    # MODIFIED (Tasks 3/5) — additive notes
README.md, QUICKSTART.md, CHANGELOG.md,
.claude-plugin/plugin.json, docs/ROADMAP.md,
docs/TEST-PLAN-v0.15.md                          # Task 7 — docs + release
```

---

### Task 1: `profile_hash.sh` — the canonical scoring-input hash

**Files:**
- Create: `skills/_ultra-engine/scripts/profile_hash.sh`
- Test: `skills/_ultra-engine/tests/test_profile_hash.sh`

**Interfaces:**
- Produces: `bash profile_hash.sh <user-profile.json>` → prints 16 lowercase hex chars to stdout — sha256 of the `jq -S` canonical form of the scoring-relevant subset `{target_titles, query_clusters, master_keyword_list, requirements, dimensions}`. Deterministic: same subset → same hash regardless of key order or unrelated fields. Consumed by `/tune` (Task 5) and documented as the recipe `/analyze-cv`/`_profile-optimizer` should adopt.

- [ ] **Step 1: Write the failing test**

`skills/_ultra-engine/tests/test_profile_hash.sh`:
```bash
#!/bin/bash
. "$(dirname "$0")/helpers.sh"
PH="$(dirname "$0")/../scripts/profile_hash.sh"
t=$(mktemp -d)
cat > "$t/a.json" <<'EOF'
{"target_titles": ["SRE"], "requirements": {"contract_type": ["freelance"]}, "cv_hash": "zzz", "tone": {"dialect": "british"}}
EOF
cat > "$t/b.json" <<'EOF'
{"requirements": {"contract_type": ["freelance"]}, "target_titles": ["SRE"], "cv_hash": "DIFFERENT", "last_updated": "2026-07-03"}
EOF
cat > "$t/c.json" <<'EOF'
{"target_titles": ["SRE", "Platform Engineer"], "requirements": {"contract_type": ["freelance"]}}
EOF
ha=$(bash "$PH" "$t/a.json"); hb=$(bash "$PH" "$t/b.json"); hc=$(bash "$PH" "$t/c.json")
assert_eq "$ha" "$hb" "unrelated fields and key order do not change the hash"
[ "$ha" != "$hc" ]; _report $? "scoring-relevant change changes the hash (a=$ha c=$hc)"
case "$ha" in ????????????????) _report 0 "16 hex chars";; *) _report 1 "16 hex chars: got '$ha'";; esac
finish
```

- [ ] **Step 2: Run to verify it fails** — `bash skills/_ultra-engine/tests/test_profile_hash.sh` → FAILs (script missing).

- [ ] **Step 3: Implement**

`skills/_ultra-engine/scripts/profile_hash.sh`:
```bash
#!/bin/bash
# Usage: profile_hash.sh <user-profile.json>
# Prints the canonical 16-hex profile hash: sha256 over the jq -S canonical
# form of the SCORING-RELEVANT subset only. Any writer that changes one of
# these fields recomputes profile_hash with this script — cached scores keyed
# on the old hash then re-evaluate lazily. Unrelated fields never shift it.
set -eu
jq -S '{target_titles: (.target_titles // []), query_clusters: (.query_clusters // null),
        master_keyword_list: (.master_keyword_list // []), requirements: (.requirements // {}),
        dimensions: (.dimensions // [])}' "$1" | shasum -a 256 | cut -c1-16
```

- [ ] **Step 4: Run to verify it passes** — test → `checks=3 fails=0`; `bash skills/_ultra-engine/tests/run.sh` → `ALL PASS`.

- [ ] **Step 5: Document + commit** — add one row to the script table in `skills/_ultra-engine/SKILL.md` (after the `payload` row, same format): `| profile_hash | \`bash $SCRIPTS/profile_hash.sh <user-profile.json>\` | Canonical 16-hex hash of the scoring-relevant profile subset; every writer that edits titles/clusters/keywords/requirements/dimensions MUST recompute it (D11 cache invalidation). |`

```bash
git add skills/_ultra-engine
git commit -m "Phase 15 Task 1: profile_hash.sh — canonical scoring-input hash"
```

---

### Task 2: `/sources` — the registry-management verb

**Files:**
- Create: `skills/sources/SKILL.md`

**Interfaces:**
- Consumes: the existing onboarding/discovery machinery text in `skills/ultramode/SKILL.md` Steps 3–3e (this task COPIES and adapts it — Task 3 then shrinks ultramode's Step 3 to a reference; do not delete anything from ultramode here).
- Produces: `/sources` (list) · `/sources add <url|name>` · `/sources rebuild` · `/sources onboarding`. Task 3's ultramode references `../sources/SKILL.md`'s onboarding and rebuild sections (headed `## /sources onboarding — …` and `## /sources rebuild — …`).

- [ ] **Step 1: Write `skills/sources/SKILL.md`** (full content):

````markdown
---
name: sources
description: Manage where the job hunt looks — list the verified source registry, add a board or company, rebuild via discovery, or re-run the first-run lane interview
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: [list | add <url|name> | rebuild | onboarding — omit for list]
disable-model-invocation: true
version: 0.1.0
---

Where the hunt looks. `/ultramode` is *go look*; `/sources` is *where*. It owns `.job-scout/sources.json` — the per-workspace, CV-derived, **verified** source registry built by `_source-discovery` — and the first-run lane interview that seeds it.

## Browser policy (read first)

Discovery probes are read-only public `WebFetch` `GET`s (the documented carve-out); any logged-in verification uses **the Claude Chrome extension exclusively**. Never request computer use; never suggest Playwright, Selenium, or any other framework. See `../shared-references/browser-policy.md`.

## Invocation forms

```
/sources                      — list the registry (default)
/sources add <url|name>       — add a board you trust, or a company (resolved to its ATS board)
/sources rebuild              — re-run discovery and rebuild the registry through the Phase 13 gates
/sources onboarding           — re-run the whole first-run lane interview, then rebuild
```

`/ultramode sources …` and `/ultramode onboarding` are deprecated spellings that point here.

## Step 0: Bootstrap

Follow `../shared-references/workspace-layout.md` to ensure `.job-scout/` exists. If `sources.json` is absent and the form is `list` or `add`, say so and offer `/sources onboarding` — nothing to list or add into yet.

## `/sources` — list

Read `.job-scout/sources.json` and print a terminal table (no `_visualizer` — this is a Tier-2 utility view):

```
Registry: {{N}} sources · built {{built_at}} · base {{base_country}} · geography {{target_geography}}
{{category}}: {{n}} · … (one line, all six categories + linkedin)

| name | category | lane | needs_key | last swept |
|---|---|---|---|---|
…
```

Order: `priority_order[]` first, the rest alphabetically. After the table, one status line: how many sources the newest run dir's scorecard actually swept (`ls -1dr .job-scout/cache/run/*/ | head -1` → `scorecard.json` → count of `.sources` keys), so "registered" vs "recently swept" is visible at a glance. Close with: `Add: /sources add <url|name> · Rebuild: /sources rebuild`.

## `/sources add <url|name>` — admit one source

The candidate names a board they use or trust, or a company they want watched:

1. **URL given** → probe it live (read-only GET). Classify per `../_source-discovery/references/discovery-protocol.md` Gates A–C as amended by Phase 13: a recognised login wall routes to `access_lane: "extension"` and is RETAINED; admit on occupation (never on today's contract mix); a dead/parked domain is refused with the probe evidence.
2. **Company name given** → resolve its ATS board via the `resolve_ats` probe-and-cache flow (`../shared-references/ultramode-sources.md` § ATS slug resolver), identity-check included. On a hit, admit the board as an `ats-provider` source; also merge the company into `requirements.companies_to_target[]` (so a registry rebuild keeps watching it). On a miss, say which providers were probed and keep the company in `companies_to_target[]` for the next rebuild.
3. Build the entry per the `sources.json` schema (`../shared-references/canonical-schemas.md`), `verified_at` = today, and append via the atomic-rename recipe (`../shared-references/state-validators.md`). Confirm with the entry's name, category, and lane. The source joins the next sweep automatically — no re-specifying queries.

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
   - **Gate 2 (count invariant):** assert `len(sources) == len(resolved backbone) + len(fragment.sources) + len(retained user_sources)` before writing; mismatch ⇒ fail loudly.
   - **Gate 3 (lane-conditional acceptance):** freelance lanes require ≥1 `freelance-marketplace` AND ≥1 `ats-provider` plus ≥5 non-backbone total; other lanes ≥5 non-backbone. Below threshold ⇒ warn, show the shortfall + `errors[]`, offer an immediate re-dispatch, write only on explicit acknowledgement with `discovered_below_threshold` recorded.
   - **Present the approval table** (name, category, lane, keys) headed by the discovered-source count and per-category breakdown, then persist atomically: resolve the backbone (fill `{country}` from the confirmed `base_country`), union the verified fragment, **ensure the LinkedIn registry entry exists** (Task 3's § LinkedIn entry — add it if absent), re-assert Gate 2, write `sources.json.tmp` → `mv`. Stamp `ultramode.registry_built_at` only after a gated write.

## Not a sweep

`/sources` never sweeps. When the registry changes, suggest `/ultramode` (full market) or `/ultramode source <name>` (just the new one).

## Reference materials

- `../ultramode/SKILL.md` — the sweep this registry feeds.
- `../_source-discovery/SKILL.md` + `references/discovery-protocol.md` — the discovery subagent and its admission gates.
- `../shared-references/ultramode-sources.md` — taxonomy, backbone, curated lane seed, `resolve_ats`.
- `../shared-references/canonical-schemas.md` — the `sources.json` schema.
- `../shared-references/subagent-protocol.md`, `state-validators.md`, `browser-policy.md`.
````

- [ ] **Step 2: Verify** — `grep -n "disable-model-invocation: true" skills/sources/SKILL.md` → hit; `grep -c "Gate " skills/sources/SKILL.md` ≥ 3; `bash skills/_ultra-engine/tests/run.sh` → `ALL PASS`.

- [ ] **Step 3: Commit** — `git add skills/sources && git commit -m "Phase 15 Task 2: /sources — registry management verb"`

---

### Task 3: `/ultramode` — flagship + scopes

**Files:**
- Modify: `skills/ultramode/SKILL.md` (intro, Invocation forms, Steps 1–3, Step 4a/4b/4d additions; Step 4c/4e–4h untouched)
- Modify: `skills/shared-references/canonical-schemas.md` (two additive notes)

**Interfaces:**
- Consumes: `/sources` section names (Task 2); `references/linkedin-adapter.md` (Task 4 — written next, referenced by exact path here).
- Produces: the scope grammar (`bare | linkedin | external | source <name>`) Task 6's alias and Task 7's docs rely on; the LinkedIn registry entry JSON below (also used by `/sources rebuild`).

- [ ] **Step 1: Replace the intro paragraph and Invocation forms section** of `skills/ultramode/SKILL.md` (everything from the line after the frontmatter down to, but not including, `## Browser policy`) with:

````markdown
**The flagship sweep.** One pass over the WHOLE market: LinkedIn (via `references/linkedin-adapter.md` — the richest surface, always swept) plus every verified source in this workspace's registry — ATS boards, remote boards, aggregators, national boards, freelance marketplaces, communities. Dedupe across sources, gate and score the genuinely-new roles, render one unified, source-agnostic ranking with the near-miss rail and the run scorecard. This command is the **dispatcher**: registry + rotation + snapshot, per-source sweeps through the `_ultra-engine` scripts, serial canonical merge, fetch-then-gate, scoring, always-render.

## Invocation forms

```
/ultramode                    — full market: LinkedIn + every registry source (the weekly run)
/ultramode linkedin           — LinkedIn only (what /deep-sweep used to be)
/ultramode external           — external sources only (keyless lanes need no browser)
/ultramode source <name>      — exactly one registry source, now (bypasses the rotation)
```

Registry management lives in **`/sources`** (list · add · rebuild · onboarding). The deprecated spellings still work but redirect: `/ultramode sources …` → print `Registry management moved to /sources — running it for you.` and follow `../sources/SKILL.md`; `/ultramode onboarding` → same, § onboarding. The old `ultramode.default` config toggle is retired (v0.15.0): the full market IS the default; scopes replace the toggle, and a `default` key still present in `user-profile.json` is ignored.
````

- [ ] **Step 2: Replace Step 1's ultramode-block sentence.** In `## Step 1: Load profile, CV corpus & requirements`, the read list names `ultramode` (the `{default, api_keys, registry_built_at}` block). Replace that clause with: `` `ultramode.api_keys` (provider tokens for keyed sources — Step 5) and `ultramode.registry_built_at`; a legacy `ultramode.default` key is IGNORED (retired v0.15.0, never written) ``. Also append to the lane-corpus paragraph's `not_terms[]` sentence: `` plus `requirements.exclusion_terms[]` (the `/tune` exclusion list; treat absent as empty) ``.

- [ ] **Step 3: Replace Step 2 (branch) and Step 3 (onboarding) wholesale** — everything from `## Step 2: Branch on invocation form` down to (not including) `## Step 4:` — with:

````markdown
## Step 2: Branch on invocation form

- **Registry present** → Step 4, with the scope: bare = LinkedIn + all external; `linkedin` = the adapter only; `external` = registry sources only; `source <name>` = that one source only.
- **Registry absent** → run the first-run flow in `../sources/SKILL.md` (§ onboarding then § rebuild) — announce it (`No source registry yet — running the /sources interview first.`), then continue into Step 4 with the requested scope. (`/ultramode linkedin` works without a registry: the adapter needs none — but still suggest `/sources onboarding` for the full market.)
- **Deprecated forms** (`sources …`, `onboarding`) → redirect per Invocation forms; do not sweep.

## Step 3: The LinkedIn registry entry (ensure-once)

Before the first sweep of a run, ensure `sources.json` carries the LinkedIn entry; if absent (pre-v0.15 registry), append it via the atomic-rename recipe and say so (`Registry upgraded: LinkedIn added as a source.`):

```json
{
  "name": "LinkedIn",
  "url": "https://www.linkedin.com/jobs/",
  "category": "linkedin",
  "access_lane": "extension",
  "endpoint": null,
  "needs_key": false,
  "needs_slug": false,
  "poll_method": "The LinkedIn adapter — references/linkedin-adapter.md: query plan v2 (linkedin-search.md §3), Past Week pages 1-3, Top picks + Saved surfaces, post-scoring similar-jobs expansion, query-stats writes.",
  "notes": "The richest surface. Always swept on bare /ultramode — never rotation-governed.",
  "verified_at": "<today>"
}
```
````

- [ ] **Step 4: Scope-gate Step 4 and slot the adapter in.** Three surgical edits inside the existing `## Step 4: Sweep flow (the multi-source pass)`:
  1. In **Step 4b**, after the rotation-pick sentence, add: `Scopes: `linkedin` skips the rotation pick and every non-LinkedIn source (write `{"picked": [], "rotated_out": []}`); `external` proceeds as written but skips the adapter in 4d; `source <name>` replaces both the poll order and the rotation with exactly that one source (an extension-lane pick of one; still \`rotation.sh mark\` it when swept).`
  2. In **Step 4d**, before the rotation-subset sentence, add: `First — unless the scope is `external` or `source <name>` (non-LinkedIn) — sweep **LinkedIn** on the main thread per `references/linkedin-adapter.md`: it produces the same validated envelope (checkpoint stage `sweep-linkedin`) as every other source, and it is never rotation-governed. Then the rotation subset:`
  3. In **Step 4f**, after sub-step 2, add a third sub-step: `3. **Similar-jobs expansion (LinkedIn scope only):** for each THIS-RUN LinkedIn role scored `tier: "A"`, collect up to 5 IDs from its listing page's "Similar jobs" rail (extension, dedupe-before-extract against the snapshot), produce ONE supplemental envelope (stage `sweep-linkedin-similar`, `source.board: "Similar"`), validate → merge → gate + score that batch the same way. One round only — expansion roles never seed further expansion (the old /deep-sweep Step 8 cap, unchanged).`

- [ ] **Step 5: canonical-schemas additive notes.** In `skills/shared-references/canonical-schemas.md`: (a) in the `sources.json` section, after the category sentence, add: `Phase 15: the registry may carry ONE \`category: "linkedin"\` entry (the LinkedIn adapter — always swept, never rotation-governed; maps to \`source.lane: "linkedin"\`); it is ensured automatically by \`/ultramode\` and \`/sources rebuild\`.` (b) In the `ultramode` profile-block description, change the `default` line to: `` `default` — RETIRED v0.15.0: never written, ignored on read (scopes replaced it; see `/ultramode` Invocation forms) ``.

- [ ] **Step 6: Verify** — `grep -n "linkedin-adapter" skills/ultramode/SKILL.md` → ≥2 hits; `grep -n "sources/SKILL.md" skills/ultramode/SKILL.md` → ≥1; `grep -cn "ultramode.default" skills/ultramode/SKILL.md` → only the retirement mentions (no live reads); `bash skills/_ultra-engine/tests/run.sh` → `ALL PASS`.

- [ ] **Step 7: Commit** — `git add skills/ultramode skills/shared-references/canonical-schemas.md && git commit -m "Phase 15 Task 3: /ultramode flagship — scopes, /sources redirect, LinkedIn registry entry"`

---

### Task 4: the LinkedIn adapter reference

**Files:**
- Create: `skills/ultramode/references/linkedin-adapter.md`

**Interfaces:**
- Consumes: `../shared-references/linkedin-search.md` (query grammar §1, plan v2 §3, query-stats §4, repost dedupe §5, freshness §6), the Phase-14 envelope contract (`validate_delta.py` shape), `namespace/id` rules (LinkedIn ids stay bare numeric).
- Produces: the adapter contract `/ultramode` Step 4d dispatches; Task 6's alias points here via /ultramode.

- [ ] **Step 1: Write `skills/ultramode/references/linkedin-adapter.md`** (full content):

````markdown
# The LinkedIn adapter — LinkedIn as a registry source

LinkedIn is one source in the registry (`category: "linkedin"`), swept on the MAIN THREAD via the Claude Chrome extension (Hard Rule #1) by the dispatcher during `/ultramode` Step 4d. It produces exactly the envelope every other source produces — the engine neither knows nor cares that this one is special. What used to be `/deep-sweep`'s body lives here.

## Inputs (from the dispatcher)

The Step 4b snapshot path, the Step 1 lane corpus (`query_clusters[]`/`target_titles[]`, `lane_keywords[]`, `not_terms[]` incl. `requirements.exclusion_terms[]`), `requirements` (for the GATE_BLOCK semantics and filter-addressed URLs), and `.job-scout/cache/query-stats.json`.

## The sweep (query plan v2 — reference, do not duplicate)

1. **Build the plan** per `../../shared-references/linkedin-search.md` §3, exactly as `/job-search` Step 2's zero-arg branch: Boolean title-cluster queries (per-title fallback), 2–3 skill-combination queries when the corpus is ripe, the `capability` family per §3f (≤3, cache-miss ⇒ skip), geo iteration across `location_preferences[]`, ordering from query-stats (proven first, retired excluded).
2. **Run every query** filter-addressed per §1: encoded Boolean `keywords`, `f_TPR=r604800` (Past Week), `f_WT`/`f_JT` from requirements, `sortBy=DD`; pages 1–3, collect IDs per page. Confirm filter chips on the run's first query; on drift fall back to the UI for that filter and record it in the envelope's `errors[]`.
3. **Dedupe before extract** (Hard Rule #2): drop every ID in the snapshot's `known_ids`; drop repost fingerprints per §5 (a repost match bumps nothing here — record it in `counts.scanned` only). **Adaptive synonym rescue** per `/job-search` Step 3b: a `family: "title"` query yielding <5 new gets 2–3 synonym variants (max 3, never expand a synonym).
4. **Sweep the extra surfaces:** Top picks (`/jobs/collections/recommended/`, 2–3 scrolls) and Saved (`/my-items/saved-jobs/`, all), tagging `source.board` accordingly. Surface priority on duplicate sightings: `Top Picks > Saved > Search`.
5. **Extract each genuinely-new role** (open the listing): title, company, location, salary, posted_at, applicant count, URL, full JD text → `jds/<id>.txt` per `../../shared-references/jd-storage.md`; run JD keyword extraction per `../../shared-references/jd-keyword-extraction.md`. Apply the GATE_BLOCK drop-on-explicit rule (stated permanent/onsite/hybrid ⇒ count in `counts.dropped_explicit_violation`, do not extract); record honest `signals` for the rest.
6. **Write query-stats** per §4: per-query candidates/new counts now; after the dispatcher's Step 4f scoring, complete the tier-count writes, retirement (3 consecutive zero-new), and synonym promotion — the adapter owns both halves of the §4 lifecycle.

## The envelope

Same shape as every sweep (validated by `validate_delta.py` before merge): `status`, `counts` (`scanned` = every ID seen incl. known/reposts; `matched` = lane-relevant AND genuinely-new; `dropped_explicit_violation`; `returned`; `capped` — cap 60 for this source, disclosed), `deltas[]` with **bare numeric LinkedIn ids** (never namespaced — back-compat with the whole tracker), `url`, title/company/location, `source: {"lane": "linkedin", "provider": "linkedin", "board": "Search" | "Top Picks" | "Saved" | "Similar"}`, `fingerprint` via `bash <SCRIPTS>/fingerprint.sh`, `posted_at`, `jd_path`, `signals`, `tags`. Checkpoint stage: `sweep-linkedin`.

## Post-scoring similar-jobs expansion

Owned by `/ultramode` Step 4f.3 (one supplemental envelope, stage `sweep-linkedin-similar`, `board: "Similar"`, ≤5 per A-tier seed, one round only).

## Failure modes

Rate-limited mid-run → stop this source, emit the partial envelope with an `errors[]` entry naming the in-flight query, and let the run continue (the scorecard discloses it; the next run's snapshot dedupe makes the retry cheap). Not logged in → `errors[]` `{"code": "login_required", "message": "LinkedIn session not active — log in and re-run /ultramode linkedin"}`, zero counts, never prompt for credentials.
````

- [ ] **Step 2: Verify** — `grep -n "sweep-linkedin" skills/ultramode/references/linkedin-adapter.md` → hits; `grep -n "bare numeric" skills/ultramode/references/linkedin-adapter.md` → hit; suite `ALL PASS`.

- [ ] **Step 3: Commit** — `git add skills/ultramode/references && git commit -m "Phase 15 Task 4: LinkedIn adapter — the deep-sweep body as a registry source"`

---

### Task 5: `/tune` — vocabulary + gates

**Files:**
- Create: `skills/tune/SKILL.md`
- Modify: `skills/shared-references/canonical-schemas.md` (one additive note)

**Interfaces:**
- Consumes: `profile_hash.sh` (Task 1, exact CLI); the single-entry atomic recipe (`state-validators.md` § Single-entry atomic update) for tracker-adjacent writes; `deal_breakers[]` shapes (canonical-schemas).
- Produces: `requirements.exclusion_terms[]` (new-optional; Task 3 already wired it into ultramode's `not_terms`); the `/tune` grammar Task 7's docs cite.

- [ ] **Step 1: Write `skills/tune/SKILL.md`** (full content):

````markdown
---
name: tune
description: Show and adjust what the hunt looks for — target titles, keywords, exclusions, and the hard gates (rate floor, contract types, arrangement) — without re-running the full CV interview
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: [add title|keyword <v> | remove title|keyword <v> | exclude <term> | unexclude <term> | gate rate-floor <n> | gate contract <v,..> | gate arrangement <v,..> — omit to show]
disable-model-invocation: true
version: 0.1.0
---

What the hunt looks for. `/sources` is *where*; `/tune` is *what*. Every edit writes `user-profile.json` atomically (merge, never overwrite unrelated keys), recomputes `profile_hash` via the engine script, and tells you what changed — so cached scores re-evaluate lazily on the next run instead of going silently stale (the 2026-07-02 detachering lesson).

## `/tune` — show the hunting vocabulary (default)

Read `user-profile.json` and the caches, then print one screen:

```
Hunting with:
  Titles ({{n}}):        {{target_titles, comma-separated}}
  Clusters:              {{query_clusters | "none — searches run one plain query per title"}}
  Keywords ({{n}}):      {{master_keyword_list, first 15}}…
  Exclusions ({{n}}):    {{requirements.exclusion_terms | "none"}}
  Capability graph:      {{built <date> for current CV | STALE (cv changed) | not built — run /analyze-cv}}
  Jargon aliases:        {{n entries | not built}}

Hard gates (deal-breakers):
  Arrangement:           {{work_arrangement values}}
  Contract:              {{contract_type values}}
  Location:              {{location values}}
  Rate floor:            {{rate_floor value + currency | "none"}}

profile_hash: {{current}} · Changes here re-score lazily on the next run.
Edit: /tune add title "…" · /tune exclude "…" · /tune gate rate-floor 800 · full grammar in the hint.
```

Capability-graph staleness: compare `capability-graph.json`'s stored `cv_hash` with the profile's; missing file ⇒ "not built".

## Edits — shared mechanics (every subcommand)

1. Read `user-profile.json`; apply the change **in memory** (merge semantics — preserve every unrelated key).
2. Write back atomically: `user-profile.json.tmp` → `jq -e .` → `mv` (`../shared-references/state-validators.md`).
3. Recompute the hash: `old=$(profile_hash)`, write, `new=$(bash <SCRIPTS>/profile_hash.sh .job-scout/user-profile.json)`, set `profile_hash` to the new value (one more atomic write, or fold into the same write by computing on the in-memory object written to a temp file first).
4. Confirm in one line, British English: `Added title "Linux Engineer" · profile_hash {{old}} → {{new}} · takes effect next run.`
5. Never touch `cv_hash`, `dimensions` content, the tone block, or the score cache itself.

## `add title "<t>"` / `remove title "<t>"`

Merge into / remove from `target_titles[]` (case-insensitive dedupe). If `query_clusters[]` exists, propose where the title belongs: an existing cluster (true synonyms only) or a new cluster — apply on confirmation; without clusters, note the plan falls back to one plain query per title. On remove: also remove it from any cluster (an emptied cluster is deleted). Note when relevant: `The capability graph is CV-derived and unchanged — re-run /analyze-cv if your lane genuinely shifted.`

## `add keyword <k>` / `remove keyword <k>`

Merge into / remove from `master_keyword_list[]`. These feed the external lanes' `lane_keywords[]` and the skill-combination query family — recall-only, they never drop anything.

## `exclude "<term>"` / `unexclude "<term>"`

Merge into / remove from `requirements.exclusion_terms[]` (new-optional, additive). Exclusions join `not_terms[]` everywhere: the LinkedIn Boolean NOT-tail and every sweep's `{{NOT_TERMS}}`. Warn on overlap: if the term appears in `master_keyword_list` or a cluster title, say so and require confirmation.

## `gate rate-floor <n>` / `gate contract <v1[,v2…]>` / `gate arrangement <v1[,v2…]>`

Edit the matching `deal_breakers[]` entry's `values[]` (create the entry if absent, `source: "elicited"`, `added_at` now):

- `rate-floor <n>` → `deal_breakers[kind=="rate_floor"].values = ["<n>"]` AND `requirements.min_day_rate = <n>` (keep them in step); append ` (updated <YYYY-MM-DD> via /tune)` to its `free_text`.
- `contract <values>` → `deal_breakers[kind=="contract_type"].values` = the given list, validated against `permanent | freelance | detachering | contract` (anything else: ask). Remind: values are the ALLOWED set (gate-as-data, `_gate-engine` § Gate semantics).
- `arrangement <values>` → same for `kind=="work_arrangement"`, values from `remote | hybrid | on-site`.

After a gate edit, additionally note: `Near-misses gated on the old rule stay in the rail — /bend <id> re-scores one, or the next run re-gates new roles under the new rule.`

## Never

Never edit the CV, fabricate skills into `master_keyword_list` the CV cannot support (warn if a keyword looks like a credential claim), or write anything outside `user-profile.json`.

## Reference materials

- `../shared-references/canonical-schemas.md` — `deal_breakers[]`, `exclusion_terms[]`, the profile fields.
- `../_ultra-engine/SKILL.md` — `profile_hash.sh` contract.
- `../shared-references/state-validators.md` — atomic writes.
- `../analyze-cv/SKILL.md` — the full interview (clusters, dimensions, capability graph) when the lane genuinely changes.
````

- [ ] **Step 2: canonical-schemas note.** In the `requirements` schema block of `skills/shared-references/canonical-schemas.md`, after the `companies_to_target` line, add: `"exclusion_terms": ["string — /tune-managed NOT-terms; unioned into every query plan's not_terms and every sweep's {{NOT_TERMS}}; optional, default []"],` — and in the prose after the block: `Phase 15: \`requirements.exclusion_terms[]\` is additive-optional; \`profile_hash\` is canonically computed by \`_ultra-engine/scripts/profile_hash.sh\` over `{target_titles, query_clusters, master_keyword_list, requirements, dimensions}` — every writer that edits those fields recomputes it.`

- [ ] **Step 3: Verify** — `grep -n "profile_hash.sh" skills/tune/SKILL.md` → hit; `grep -n "exclusion_terms" skills/shared-references/canonical-schemas.md` → ≥2 hits; suite `ALL PASS`.

- [ ] **Step 4: Commit** — `git add skills/tune skills/shared-references/canonical-schemas.md && git commit -m "Phase 15 Task 5: /tune — vocabulary + gates with deterministic hash invalidation"`

---

### Task 6: retirements — `/deep-sweep` alias, `/job-search` widening, `/config` toggle

**Files:**
- Modify: `skills/deep-sweep/SKILL.md` (body replaced; frontmatter description updated)
- Modify: `skills/job-search/SKILL.md` (Step 7 replaced)
- Modify: `skills/config/SKILL.md` (Step 6 replaced; Step 1 grammar line updated)

- [ ] **Step 1: `skills/deep-sweep/SKILL.md`** — replace the ENTIRE file with:

````markdown
---
name: deep-sweep
description: DEPRECATED alias for /ultramode — the weekly thorough sweep is now the full-market flagship (LinkedIn + every registry source)
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
disable-model-invocation: true
version: 1.0.0
---

**`/deep-sweep` retired in v0.15.0 — it became `/ultramode`.** The weekly thorough sweep now covers the whole market in one pass: the LinkedIn query plan you know (unchanged, via `../ultramode/references/linkedin-adapter.md`) plus every verified source in your registry, one unified ranking, the near-miss rail, the run scorecard.

On invocation:

1. Print exactly:

```
/deep-sweep is now /ultramode (v0.15.0) — running the full-market sweep.
  LinkedIn only (the old behaviour):  /ultramode linkedin
  This alias is removed in the next minor release.
```

2. Then follow `../ultramode/SKILL.md` end-to-end with the **bare** scope. Do not duplicate any of its behaviour here.
````

- [ ] **Step 2: `skills/job-search/SKILL.md`** — replace the whole `## Step 7: Widen to ultramode when opted in (default off)` section (heading through its final paragraph, ending before the next `##` heading) with:

````markdown
## Step 7: The wider market

`/job-search` is LinkedIn-only by design — the surgical search. For the whole market (LinkedIn + every registry source, deduped, one ranking) run `/ultramode`; manage where it looks with `/sources`. The old `ultramode.default` widening toggle is retired (v0.15.0).
````

- [ ] **Step 3: `skills/config/SKILL.md`** — (a) in Step 1's grammar block, change the line `/config ultramode default <true|false>` to `/config ultramode default   (RETIRED v0.15.0 — prints a notice)`; (b) replace the whole `## Step 6: Toggle the ultramode default …` section body with:

````markdown
## Step 6: `/config ultramode default` — retired (v0.15.0)

The toggle is gone: `/ultramode` always sweeps the full market, and the scopes replaced the switch (`/ultramode linkedin`, `/ultramode external`, `/ultramode source <name>`). On any `/config ultramode default …` invocation print exactly:

```
`ultramode.default` was retired in v0.15.0 — /ultramode always sweeps the full market.
Scopes replace the toggle: /ultramode linkedin · /ultramode external · /ultramode source <name>
```

Write nothing. A `default` key still present in `user-profile.json` is harmless — every reader ignores it.
````

- [ ] **Step 4: Verify** — `grep -rn "ultramode.default" skills/ | grep -v "RETIRED\|retired\|ignored\|IGNORED"` → no live-behaviour hits; `grep -n "deep-sweep" skills/deep-sweep/SKILL.md | head -3` shows the alias copy; `wc -l skills/deep-sweep/SKILL.md` → under 30; suite `ALL PASS`.

- [ ] **Step 5: Commit** — `git add skills/deep-sweep skills/job-search skills/config && git commit -m "Phase 15 Task 6: retire /deep-sweep to alias, remove widening step, retire default toggle"`

---

### Task 7: docs + release v0.15.0

**Files:**
- Modify: `README.md`, `QUICKSTART.md`, `CHANGELOG.md`, `.claude-plugin/plugin.json`, `docs/ROADMAP.md`
- Create: `docs/TEST-PLAN-v0.15.md`

- [ ] **Step 1: `README.md`.** In `## Commands`: `/ultramode` moves to the top described as `the weekly full-market sweep — LinkedIn + every verified source, one ranking, near-miss rail, run scorecard (scopes: linkedin · external · source <name>)`; add `/sources` (`manage where it looks: list · add <url|name> · rebuild · onboarding`), `/tune` (`show and adjust titles, keywords, exclusions, and hard gates — no full re-interview`), `/bend` if absent; mark `/deep-sweep` `(deprecated alias → /ultramode)`. In the `### Ultramode` section heading and intro, drop the word "opt-in" and state the merge: `As of v0.15.0 ultramode IS the flagship: LinkedIn is one source in the registry, swept by the same engine.` In `## Getting Started`, the command order becomes: `/analyze-cv` → `/sources onboarding` → `/ultramode` → daily `/check-job-notifications` → `/tune` between runs → `/bend <id>` from the near-miss rail. In `### Daily workflow`, replace any `/deep-sweep` mention with `/ultramode` (weekly) and add `/tune` for between-runs adjustments.

- [ ] **Step 2: `QUICKSTART.md`.** In `## Step 3 — Run these commands, in order`, the sequence becomes `/analyze-cv`, `/sources onboarding` (say: builds your verified source registry — answer the country question honestly, it is never guessed), `/ultramode` (say: 30–45 min, walk away; the report opens itself; near-misses appear in their own rail with `/bend` hints). Replace any `/deep-sweep` or `/ultramode sources` mentions accordingly. Keep the file's existing voice.

- [ ] **Step 3: `CHANGELOG.md`** — new top section:

````markdown
## [0.15.0] — <today's date>

### Changed
- **`/ultramode` is the flagship.** Bare `/ultramode` sweeps the WHOLE market — LinkedIn (now a registry source, swept by the same engine through `references/linkedin-adapter.md`) plus every verified external source — into one deduped, unified ranking. Scopes: `/ultramode linkedin` (the old `/deep-sweep`), `/ultramode external`, `/ultramode source <name>`.
- **`/deep-sweep` is a deprecation alias** (prints a pointer, runs the full-market sweep; removed next minor release). `/job-search`'s widening step and the `ultramode.default` toggle are retired — scopes replace the switch; a leftover `default` key is ignored.

### Added
- **`/sources`** — registry management gets its own verb: `list` (registry + last-swept view), `add <url|name>` (probe/classify/admit a board, or resolve a company to its ATS board), `rebuild` (discovery through the Phase 13 gates, now folding the dynamic ATS watchlist in at build time), `onboarding` (the lane interview).
- **`/tune`** — see and adjust the hunting vocabulary (titles, keywords, exclusions) and the hard gates (rate floor, contract types, arrangement) without the full CV interview. Every edit recomputes `profile_hash` via the new engine script, so cached scores re-evaluate lazily instead of going stale.
- **`profile_hash.sh`** — canonical 16-hex hash of the scoring-relevant profile subset, with tests; `requirements.exclusion_terms[]` (additive) feeds every query plan's NOT-terms.
````

- [ ] **Step 4: `.claude-plugin/plugin.json`** — `version` → `0.15.0`; in `description`, replace `opt-in multi-source ultramode discovery beyond LinkedIn` with `one flagship full-market sweep (LinkedIn + a verified multi-source registry)`.

- [ ] **Step 5: `docs/ROADMAP.md`** — tick every Phase 15 checkbox (`- [ ]` → `- [x]` in the `## Phase 15` section); update the status-table row 15 to `Shipped — v0.15.0 (fresh-workspace smoke + publish gate pending)`; add a Log entry dated today: Phase 15 shipped as v0.15.0 — one-paragraph summary naming the flagship merge, `/sources`, `/tune`, the alias, the toggle retirement, and that the publish gate (two clean weekly runs on both workspaces) now runs.

- [ ] **Step 6: `docs/TEST-PLAN-v0.15.md`** (full content):

````markdown
# Live acceptance — v0.15.0 (The ultramode merge)

Two halves: a **fresh-workspace end-to-end** (proves a stranger's first run works) and the **publish gate** (two consecutive clean weekly runs on both live workspaces). `slash` = Claude Code from the workspace; `$` = shell there.

## A · Fresh-workspace end-to-end (~1 h)

```bash
mkdir -p ~/job-hunt-fresh && cd ~/job-hunt-fresh && cp /path/to/your-cv.pdf .
```
Update the plugin to v0.15.0, reload, then in order:

1. `/analyze-cv` — the interview (segment, deal-breakers, dimensions, clusters, capability graph).
2. `/ultramode` — with NO registry it must announce the `/sources` interview first, run it (country question asked explicitly and read back — never guessed), build the registry through the gates (approval table with discovered counts), THEN sweep the full market and open one unified report with the scorecard.
   - `$ jq '.sources | length' .job-scout/sources.json` → ≥ 12; `$ jq '[.sources[] | select(.category=="linkedin")] | length'` → 1.
3. `/tune` — shows titles/keywords/gates; `/tune add title "Site Reliability Engineer"` → confirm line with `profile_hash old → new`; `/tune` again shows it.
4. `/deep-sweep` — prints the deprecation pointer, then runs the full-market sweep.
5. `/config ultramode default true` — prints the retirement notice, writes nothing.

**Pass:** every step behaves as written; the report renders; no stage improvises.

## B · Publish gate (weeks 1–2)

On **CVFREELANCER** and **CVDIRECTOR**, once per week for two weeks:

```slash
/ultramode
```

After each run (workspace shell; `TODAY` = run date):

```bash
$ RD=$(ls -1dr .job-scout/cache/run/*/ | head -1)
$ jq '.stages.render' "$RD/manifest.json"                      # "done"
$ jq '.sources | keys | length' "$RD/scorecard.json"           # ≥ 15 sources swept (incl. "linkedin")
$ jq '.sources.linkedin' "$RD/scorecard.json"                  # LinkedIn counts present
$ jq -r '.disclosures[]' "$RD/scorecard.json"                  # every cap/skip named
$ jq --arg t "$TODAY" '[.jobs[] | select(.first_seen==$t and (.source|type)=="object" and .jd_path==null and (.tier=="A" or .tier=="B" or .tier=="C" or .near_miss==true))] | length' .job-scout/tracker.json   # 0
```

**Clean run** = render done, LinkedIn + externals in one scorecard, gates hold, runtime ≤ 45 min. Four clean runs (2 workspaces × 2 weeks) ⇒ the publish gate passes; the plugin goes to marketplace-readiness (Phase 16 opens with the WebFetch-cap fetch-runner investigation).

## C · Report back

Per run: the summary line, the disclosure list, runtime, and any gate failure with its output.
````

- [ ] **Step 7: Verify** — `jq -r .version .claude-plugin/plugin.json` → `0.15.0`; `grep -c "deep-sweep" README.md QUICKSTART.md` shows only deprecation-context mentions; ROADMAP Phase 15 has zero unticked boxes; suite `ALL PASS`.

- [ ] **Step 8: Commit** — `git add -A && git commit -m "Phase 15 Task 7: release v0.15.0 docs — flagship story, /sources + /tune, deprecations, publish-gate test plan"`

---

### Task 8: integration consistency sweep

**Files:** none created — verification + at most small pointer fixes discovered by the greps (each fix named in the report).

- [ ] **Step 1: Run the sweep** (repo root; every command's expectation stated):

```bash
# 1. No live ultramode.default behaviour anywhere (retirement mentions only):
grep -rn "ultramode.default" skills/ README.md QUICKSTART.md | grep -viE "retired|ignored|was retired"     # expect: empty
# 2. Every /ultramode sources|onboarding mention is a deprecation/redirect context:
grep -rn "/ultramode sources\|/ultramode onboarding" skills/ README.md QUICKSTART.md | grep -viE "deprecat|redirect|moved"   # expect: empty
# 3. No skill still instructs running /deep-sweep as a real command (alias + docs-deprecation mentions exempt):
grep -rln "deep-sweep" skills/ | grep -v "skills/deep-sweep"                                               # inspect each hit: must be historical/deprecation context
# 4. The adapter is referenced from ultramode and nowhere contradicts it:
grep -rn "linkedin-adapter" skills/                                                                        # expect: ultramode SKILL + the reference itself
# 5. Envelope vocabulary intact:
grep -c "sweep-linkedin" skills/ultramode/SKILL.md skills/ultramode/references/linkedin-adapter.md          # ≥1 each
# 6. Suite + render:
bash skills/_ultra-engine/tests/run.sh                                                                      # ALL PASS
```
Also re-run the Task 16 (Phase 14) render-verify one-liner → `render ok:` twice.

- [ ] **Step 2: Fix anything the sweep catches** (small pointer edits only — anything structural goes back to the controller), re-run the failing grep, then commit: `git add -A && git commit -m "Phase 15 Task 8: integration consistency sweep"` (or report "sweep clean, nothing to commit").

---

## Self-review (run before handoff)

- **Spec coverage:** WS-F → Tasks 3+4 (flagship, scopes, LinkedIn entry, adapter); WS-G → Task 2 (+ Task 3's redirects); WS-H → Tasks 1+5 (`profile_hash.sh`, `/tune`, exclusion_terms, invalidation); WS-I → Tasks 6+7 (alias, widening removal, toggle retirement, docs, release). Spec §4 acceptance: bare-run ≤45 min + fresh-workspace end-to-end + `/ultramode linkedin` ≈ old deep-sweep + `/sources` round-trip + `/tune` round-trip + alias behaviour → all in TEST-PLAN-v0.15 (Task 7); publish gate = D14.
- **Placeholder scan:** the only `{{…}}` tokens are display-template placeholders inside `/sources` list and `/tune` show screens (deliberate output templates) and the Task 13 template-placeholder mentions quoted in the adapter — none are plan-authoring gaps.
- **Type consistency:** scope names (`linkedin | external | source <name>`) identical in Tasks 3/6/7; stage names `sweep-linkedin`/`sweep-linkedin-similar` identical in Tasks 3/4; `exclusion_terms` path identical in Tasks 3/5; `profile_hash.sh` CLI identical in Tasks 1/5; `/sources` section names (§ onboarding, § Rebuild) match between Tasks 2/3.

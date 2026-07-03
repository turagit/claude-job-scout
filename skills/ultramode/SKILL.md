---
name: ultramode
description: Sweep every verified job source for your workspace in one pass — discover the source registry, dedupe across sources, gate, score, and render a unified ranking
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: [linkedin | external | source <name> — omit for the full-market sweep]
disable-model-invocation: true
version: 0.2.0
---

**The flagship sweep.** One pass over the WHOLE market: LinkedIn (via `references/linkedin-adapter.md` — the richest surface, always swept) plus every verified source in this workspace's registry — ATS boards, remote boards, aggregators, national boards, freelance marketplaces, communities. Dedupe across sources, gate and score the genuinely-new roles, render one unified, source-agnostic ranking with the near-miss rail and the run scorecard. This command is the **dispatcher**: registry + rotation + snapshot, per-source sweeps through the `_ultra-engine` scripts, serial canonical merge, fetch-then-gate, scoring, always-render.

## Browser policy (read first)

All logged-in browser work in this command uses **the Claude Chrome extension exclusively** (the `extension`-lane sweeps in Step 4). Never request computer use; never suggest Playwright, Selenium, or any other automation framework. The read-only public `WebFetch` `GET` of `api`/`rss`/`html` endpoints is the documented carve-out and happens **inside the dispatched `_source-sweep` subagents**, never as logged-in scraping. See `../shared-references/browser-policy.md`.

## Invocation forms

```
/ultramode                    — full market: LinkedIn + every registry source (the weekly run)
/ultramode linkedin           — LinkedIn only (what /deep-sweep used to be)
/ultramode external           — external sources only (keyless lanes need no browser)
/ultramode source <name>      — exactly one registry source, now (bypasses the rotation)
```

Registry management lives in **`/sources`** (list · add · rebuild · onboarding). The deprecated spellings still work but redirect: `/ultramode sources …` → print `Registry management moved to /sources — running it for you.` and follow `../sources/SKILL.md`; `/ultramode onboarding` → same, § onboarding. The old `ultramode.default` config toggle is retired (v0.15.0): the full market IS the default; scopes replace the toggle, and a `default` key still present in `user-profile.json` is ignored.

## Step 0: Bootstrap workspace

Follow `../shared-references/workspace-layout.md` to ensure `.job-scout/` exists. Then follow `../shared-references/render-orchestration.md` Step G (lifecycle cleanup) to archive expired report files and prune old archives — cheap directory scan; runs at the start of every Tier 1 command.

## Step 1: Load profile, CV corpus & requirements

Follow `../shared-references/cv-loading.md`. Read `user-profile.json` for `segment`, `target_titles[]`, `query_clusters[]`, `requirements`, `cv_summary`, `master_keyword_list`, `ultramode.api_keys` (provider tokens for keyed sources — Step 5) and `ultramode.registry_built_at`; a legacy `ultramode.default` key is IGNORED (retired v0.15.0, never written).

The **CV corpus** is the lane's relevance vocabulary, reused (never re-derived) across the whole run:

- `cv_summary.key_skills` and `cv_summary` — the candidate's skills and seniority.
- `target_titles[]` and `query_clusters[]` — the lane's title vocabulary (mirrors `/job-search` Step 1).
- `master_keyword_list` — the workspace keyword model built by `_cv-optimizer`.
- `.job-scout/cache/jd-keyword-corpus.json` (the **jd-keyword-corpus**) — the market-specific keyword model built up by prior sweeps; treat a missing file as empty.

From these, build the **lane relevance terms** passed to every sweep: `lane_keywords[]` = union of `cv_summary.key_skills`, the title tokens from `target_titles[]`/`query_clusters[]`, the top co-occurring skills in the jd-keyword-corpus, and `master_keyword_list`; `not_terms[]` = the workspace's exclusion terms (seniority/scope mismatches from `requirements.deal_breakers[]`) plus `requirements.exclusion_terms[]` (the `/tune` exclusion list; treat absent as empty). This is the same corpus `/job-search` and `/match-jobs` already read — ultramode reuses it rather than parsing the CV again.

If `target_titles` and `cv_summary.target_roles` are both empty, stop and ask the user to run `/analyze-cv` first — ultramode needs a declared lane to filter sources against.

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

If `sources.json` is absent under the `linkedin` scope, skip this ensure-once and Step 4b's registry load entirely — the adapter needs no registry; the entry is added when `/sources` first builds one.

## Step 4: Sweep flow (the multi-source pass)

Resolve `SCRIPTS` = `../_ultra-engine/scripts` (this plugin's engine — see `../_ultra-engine/SKILL.md` for every contract) and `WS` = `.job-scout`. Mechanical work below is script calls; composing them from memory is a defect (CLAUDE.md hard rule #9).

### Step 4a: Resume or start a run
`rd=$(bash $SCRIPTS/checkpoint.sh find-incomplete $WS)`. If non-empty and its manifest `started_at` is within 48h, announce **resuming** and skip every stage whose checkpoint says `done`. Otherwise `rd=$(bash $SCRIPTS/checkpoint.sh init $WS $(date +%F-%H%M))`. Set `TODAY` = the run id's date component (`TODAY=$(basename "$rd" | cut -c1-10)` — so a resumed run keeps its original date); every `date +%F` in Steps 4e–4g uses `$TODAY`.

### Step 4b: Registry, rotation, snapshot
Load `sources.json`; derive poll order per `ultramode-sources.md` § Adaptive priority order. Pick this run's extension-lane subset: `bash $SCRIPTS/rotation.sh pick $WS/sources.json 4`; write `{picked, rotated_out}` (rotated_out = extension sources not picked) to `$rd/rotation.json`. Scopes: `linkedin` skips the rotation pick and every non-LinkedIn source (write `{"picked": [], "rotated_out": []}`); `external` proceeds as written but skips the adapter in 4d; `source <name>` replaces both the poll order and the rotation with exactly that one source (an extension-lane pick of one; still `rotation.sh mark` it when swept). Build the snapshot: `bash $SCRIPTS/snapshot.sh $WS/tracker.json $WS/cache/ultramode-snapshot.json`, then `bash $SCRIPTS/checkpoint.sh save $rd snapshot $WS/cache/ultramode-snapshot.json`. ATS coverage in the sweep is the registry's `ats-provider` sources themselves; the dynamic watchlist union (tracker A/B-tier employers + `companies_to_target[]` + curated seed + manual additions, per `../_source-sweep/SKILL.md` § ATS watchlist) is applied when the registry is (re)built — Phase 15's `/sources` command (§ rebuild) owns refreshing it. This weekly sweep pass reads the registry as-is.

### Step 4c: Fan out subagent sweeps (api/rss/html lanes)
For each non-extension source in poll order: load the template matching its `access_lane` from `../_source-sweep/references/prompt-<lane>.md`, substitute ONLY the placeholders (all ten, nothing else: {{SOURCE_JSON}} = the registry entry verbatim · {{SNAPSHOT_PATH}} = $WS/cache/ultramode-snapshot.json · {{WS_DIR}} = .job-scout · {{SCRIPTS}} = the resolved ../_ultra-engine/scripts path · {{LANE_KEYWORDS}} / {{NOT_TERMS}} = the Step 1 lane corpus · {{GATE_BLOCK}} = the drop-on-explicit-violation rules built from requirements.deal_breakers values[]/free_text as data · {{FRESHNESS_DAYS}} = 7 · {{CAP}} = 40 · {{API_KEY_LINE}} = for a needs_key source, the token line looked up from ultramode.api_keys per Step 5, else an empty line — and if a needed key is ABSENT, do not dispatch that source at all), and dispatch via the Agent tool per `subagent-protocol.md` (parallel across sources is fine — they never write the tracker). Save each return: write it to a temp file, `python3 $SCRIPTS/validate_delta.py --ws $WS <file>`; on failure re-dispatch that source once with the validator's stderr appended under a "## Previous attempt was rejected because" line. **On a source's second validation failure, or an absent API key (the ABSENT case above), the failure must still reach the scorecard:** write a minimal valid envelope in its place — `{"status": "ok", "counts": {"scanned": 0, "matched": 0, "dropped_explicit_violation": 0, "returned": 0, "capped": false}, "deltas": [], "errors": [{"code": "<sweep_failed|no_api_key>", "message": "<detail — e.g. Skipped <provider> (no API key)>"}], "continuation_cursor": null}` and checkpoint IT as `sweep-<slug>` exactly as a successful sweep would be, so the scorecard's disclosures surface it. On success: `bash $SCRIPTS/checkpoint.sh save $rd sweep-<name-slug> <file>`.

### Step 4d: Extension lane — main thread, rotation subset only
First — unless the scope is `external` or `source <name>` (non-LinkedIn) — sweep **LinkedIn** on the main thread per `references/linkedin-adapter.md`: it produces the same validated envelope (checkpoint stage `sweep-linkedin`) as every other source, and it is never rotation-governed. Then the rotation subset: For each `rotation.json .picked` source: sweep it in the logged-in session via the Chrome extension (dedupe-before-extract against the snapshot; collect candidate ids on the listing page; open only new ones; write each full JD to `jds/<namespaced-id>.txt` minted with `bash $SCRIPTS/namespace_id.sh`; build the SAME envelope shape including `counts` + `signals`). Validate + checkpoint exactly as 4c, then `bash $SCRIPTS/rotation.sh mark $WS/sources.json <name> $(date +%F)`. A source that cannot be swept (login expired, layout dead) records an `errors[]` envelope — never silence.

### Step 4e: Merge (all-or-nothing, serial, atomic)
`python3 $SCRIPTS/merge_tracker.py --ws $WS --tracker $WS/tracker.json --today $TODAY $rd/sweep-*.json` — save its stdout to `$rd/merge.json` and `bash $SCRIPTS/checkpoint.sh save $rd merge $rd/merge.json`. On non-zero exit: STOP the pipeline, show the validator output, append `{"stage": "merge", "message": "<first line of stderr>"}` to `$rd/pipeline-errors.json` (create it as `{"errors": []}` first if absent), and still proceed to Steps 4g–4h with whatever previous stages completed (always-render).

### Step 4f: Fetch-then-gate (D2), then gate + score
1. Queue: every merged entry from this run with `jd_path: null` → `bash $SCRIPTS/jd_queue.sh push $WS/cache/jd-queue.json <entries>` (an entry whose JD is already on disk but carries an `unknown` load-bearing `signals` value is NOT queued — it goes straight to gate + score in 4f.2, since the gate reads the full JD text; re-fetching a JD that already exists on disk is the exact economics inversion this phase fixes). Pop the budget: `bash $SCRIPTS/jd_queue.sh pop $WS/cache/jd-queue.json 75` — and CHECK its exit status: on non-zero exit the rewrite failed and nothing was dequeued, so discard the printed output and skip the fetch stage this run (fetches are idempotent, so a rare double-serve is harmless — but never treat failed-pop output as consumed). For each popped entry fetch the full JD (WebFetch for public urls; the extension for login-walled sources), write `jds/<id>.txt`, set `jd_path` on the entry via the atomic single-entry recipe (state-validators.md). Re-push any popped entry whose fetch failed back onto the queue before writing jd-fetch.json — a failed fetch defers, never strands. **This sub-step's bookkeeping is unconditional:** the queue push and the `jd-fetch.json` write happen even when you fetch nothing — a run that skips fetching (empty queue, failed pop, or every candidate's endpoint already proved dead in-sweep) still writes `{"budget": 75, "used": 0, "deferred": <real queue count>}` and appends one line to `$rd/pipeline-errors.json` (`{"stage": "jd-fetch", "message": "<why the stage fetched nothing>"}`) so the scorecard discloses it — zeros with a non-empty candidate list and no explanation are the 2026-07-03 bookkeeping defect. Write `$rd/jd-fetch.json`; checkpoint `jd-fetch`.
2. Gate + score every this-run entry **with a jd_path**, batched ≤5 per `subagent-protocol.md`: `_gate-engine` first (violations as structured data; single-kind failures continue to the rubric per its § near-miss), `_job-matcher` rubric second (refuses jd-missing). Persist per entry atomically: `tier`, `tier_reason`, `gate_violations[]`, `dimensions`, `rubric_version: "v1"`, and when applicable `near_miss` + `near_miss_would_be_tier`; scores into `cache/scores.json` under the usual key. Checkpoint `scoring` when the batch set completes. For LinkedIn-sourced roles, then complete the query-stats second half (tier counts, retirement, synonym promotion) per `references/linkedin-adapter.md` § The sweep, item 6.
3. **Similar-jobs expansion (LinkedIn scope only):** for each THIS-RUN LinkedIn role scored `tier: "A"`, collect up to 5 IDs from its listing page's "Similar jobs" rail (extension, dedupe-before-extract against the snapshot), produce ONE supplemental envelope (stage `sweep-linkedin-similar`, `source.board: "Similar"`), validate → merge → gate + score that batch the same way. One round only — expansion roles never seed further expansion (the old /deep-sweep Step 8 cap, unchanged).

### Step 4g: Scorecard + payload
`bash $SCRIPTS/scorecard.sh $rd $WS/tracker.json $TODAY` then `bash $SCRIPTS/payload.sh $WS/tracker.json $rd $TODAY <n-sources-swept> > $rd/payload.json`; checkpoint both. The payload is the render input verbatim — do not hand-assemble or re-sort it.

### Step 4h: Render — ALWAYS
Follow `render-orchestration.md` with `view: "ultramode"` and `$rd/payload.json` (Hard Rule #8 — via `_visualizer`, never inline). This step runs even when 4c–4f partially failed: the report states what completed and the scorecard's disclosures name what didn't. `bash $SCRIPTS/checkpoint.sh save $rd render` only after the report file exists. Summary line: `✓ Ultramode — {{N_sources}} sources · {{N_new}} new roles — A:{{a}} B:{{b}} C:{{c}} · Filtered:{{gated}} · Near-misses:{{nm}} — opened report in Chrome`, followed by every scorecard disclosure line.

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

`/config` is extended (this task) to add/remove a provider key. See `../config/SKILL.md`:

- `/config ultramode key <provider> <token>` — add/replace a key.
- `/config ultramode key <provider> --remove` — remove a key.

## Next Steps

Suggest `/apply` for approved new roles, `/match-jobs` to re-score against an updated CV, or `/sources rebuild` to rebuild the registry when the lane changes (new geography, new contract type).

## Reference materials

- `../shared-references/ultramode-sources.md` — taxonomy, access lanes, the universal backbone, `derive_priority_order()`, the cross-source fingerprint + `merge_delta_into_tracker()` canonical selection, key-handling note.
- `../shared-references/canonical-schemas.md` — the `sources.json` schema, the `ultramode` profile block (`api_keys`/`registry_built_at`; `default` retired v0.15.0), `requirements.base_country`/`target_geography`, the structured `source` + namespaced id.
- `../shared-references/render-orchestration.md` — the `ultramode` view and the render lifecycle (Steps A–G).
- `../shared-references/subagent-protocol.md` — the dispatch / delta-return / budget contract for `_source-discovery`, `_source-sweep`, the scorer, and `_visualizer`.
- `../shared-references/cv-loading.md` — the CV corpus this command reuses (never re-parses).
- `../_source-discovery/SKILL.md` — the discovery subagent (dispatched by /sources rebuild).
- `../_source-sweep/SKILL.md` — the per-source sweep subagent (Step 4c), its prompt templates, and the ATS watchlist definition; the extension lane runs on the main thread per Step 4d's rotation subset.
- `../_job-matcher/SKILL.md` + `../_gate-engine/SKILL.md` — the unchanged scorer (Step 4f).
- `../config/SKILL.md` — key add/remove (Step 5); the default toggle is retired.
- `../shared-references/browser-policy.md` — the Chrome-extension-only rule and the read-only `WebFetch` carve-out.

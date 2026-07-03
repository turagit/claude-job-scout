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

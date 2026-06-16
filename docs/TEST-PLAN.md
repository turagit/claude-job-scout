# Manual test plan — v0.11.0 (Ultramode) + v0.12.0 (Discovery & Categorisation)

A hands-on walkthrough to exercise the v0.11.0 + v0.12.0 features end-to-end and confirm they behave. This is the **interactive soft-gate smoke** deferred from the Phase 11/12 builds (the automated hard gates already pass in CI-equivalent checks). It drives a *real* job search — real CV, real LinkedIn session — so results are live.

**Legend:** `slash` = type into Claude Code, run from the workspace; `$` = shell, run in the workspace terminal (or in Claude Code with a leading `!`). State lives in `.job-scout/` in the workspace.

---

## 0 · Setup

```bash
mkdir -p ~/job-hunt-test && cd ~/job-hunt-test
cp /path/to/your-cv.pdf .            # PDF / DOCX / DOC / TXT / MD
# optional: drop a couple of supporting docs (cert/talk/diploma) in the same folder
```

- Update the plugin to **v0.12.0** (pull/reinstall from `turagit/claude-job-scout`) and reload Claude Code.
- Have the **Claude Chrome extension** installed and be **logged into LinkedIn** for LinkedIn surfaces. Ultramode keyless sources (RemoteOK / Remotive / Arbeitnow / ATS boards) work over `WebFetch` without it.
- Run Claude Code from `~/job-hunt-test`.

## 1 · Regression — the plugin loads (the validation bug)

In Claude Code, type `/` and confirm the plugin's commands list with **no "Plugin validation failed"** error. (The Phase-11 `_source-sweep` description XML-tag bug is fixed in v0.12.0.)

```bash
$ git -C <plugin-repo> show origin/main:.claude-plugin/plugin.json | jq -r .version   # expect 0.12.0
```

## 2 · Phase 12 — discovery & categorisation

**2a · Profile + the capability graph**

```slash
/analyze-cv
```

Expect: the discovery interview, then proposals for **dimensions**, **search clusters**, and — new in v0.12.0 — a **capability graph** (*stated · latent · adjacent* capabilities, each adjacency with a one-line `domain_bridge` justification) you approve/trim.

```bash
$ jq '.requirements.base_country, [.dimensions[]|{name,type}]' .job-scout/user-profile.json
$ jq '{stated, latent, adjacent}' .job-scout/cache/capability-graph.json   # adjacent = objects w/ domain_bridge
```
**Pass:** a `capability-graph.json` exists, keyed by your CV; `adjacent` entries are objects carrying `domain_bridge`.

**2b · Search — capability queries + the new badges**

```slash
/job-search
```
(or `/job-search "Platform Engineer"`). Expect: the plan includes **`capability` queries** (catching reworded roles), and the report shows, on A/B-tier cards, **competitiveness · confidence · explanation-tag** chips, with the **highest-confidence matches first within each tier**.

```bash
# capability queries actually ran (cap ≤3, ride the query-stats loop):
$ jq 'to_entries | map(select(.value.family=="capability")) | .[].key' .job-scout/cache/query-stats.json
# the parallel scoring fields on A/B jobs (tier rubric untouched):
$ jq '[.jobs[] | select(.tier=="A" or .tier=="B") | {title,tier,competitiveness,confidence,match_explanation_tag}]' .job-scout/tracker.json
```
**Pass:** ≤3 `capability`-family queries appear; A/B jobs carry `competitiveness`/`confidence`/`match_explanation_tag`; the report renders the badges, sorted by confidence within tier.

**2c · Explicit scoring**

```slash
/match-jobs
```
**Pass:** same badges + within-tier confidence sort; the standouts rise to the top of their tier.

## 3 · Phase 11 — ultramode (sources beyond LinkedIn)

```slash
/ultramode
```
Expect (first run = onboarding): it **asks your base country explicitly and reads it back** (never guesses), asks target geography / arrangement / contract / field, builds a **verified `sources.json`**, presents it for approval, sweeps, and renders **one unified, source-agnostic, tier-ranked report** with an **apply-at-source** link per role + the same competitiveness/confidence badges.

```bash
$ jq '{base_country, target_geography, n_sources:(.sources|length)}' .job-scout/sources.json
$ jq '[.sources[]|{name,category,access_lane,needs_key}] | .[0:12]' .job-scout/sources.json
```

```slash
/ultramode sources add https://boards.greenhouse.io/<a-company>
/ultramode sources
/config ultramode default on
/job-search
```
**Pass:** base country was asked and confirmed; `sources.json` holds a verified, access-lane-classified registry; with `ultramode.default on`, `/job-search` widens to external sources; `off` leaves the LinkedIn core unchanged.

## 4 · Whole-state check

```bash
$ ls -1 .job-scout/cache
$ jq '.aliases|keys|length'                         .job-scout/cache/jargon-normalizer.json
$ jq '[.[]|.family]|group_by(.)|map({(.[0]):length})' .job-scout/cache/query-stats.json
$ jq '[.jobs[].rubric_version]|unique'              .job-scout/tracker.json   # expect ["v1"] (+ maybe "legacy")
$ ls -1 .job-scout/reports
```

## 5 · Acceptance criteria

**Automated hard gates (already green; re-checkable in the plugin repo):**
- `rubric_version` stays `v1`; the score-cache key is unchanged (no re-score storm).
- The deterministic confidence/tag decision table passes its cases; every tag is exercised.
- Reports render with **and** without the new fields (back-compat, no null leak).
- The capability family + jargon map are recall-only (never drop a job); cap ≤3 across all three sweep surfaces.
- No XML-tag tokens in any SKILL `description` (the Phase-11 regression guard).
- `competitiveness` never feeds the tier/dimensions/gates.

**Interactive soft gates (this walkthrough):**
- `/analyze-cv` proposed and let you approve a capability graph (with `domain_bridge`).
- `/ultramode` asked your base country explicitly and confirmed it.
- `capability`-family queries appear in `query-stats.json`; a deliberately-noisy one retires after 3 empty runs.
- A/B cards show competitiveness/confidence badges, sorted high→med→low within tier.
- Pre-existing tracked jobs (no new fields) still render cleanly.

## Notes & caveats

- This drives your **real** job search (real CV, real LinkedIn session). Treat results as live.
- LinkedIn surfaces need the Chrome extension + an active LinkedIn login; ultramode's keyless sources do not.
- Nothing is applied or sent without your explicit approval.
- If a step misbehaves, capture the exact command + what you saw and file it; the per-feature design lives in `docs/superpowers/specs/` (Phase 11, Phase 12).

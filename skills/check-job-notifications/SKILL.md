---
name: check-job-notifications
description: Walk every LinkedIn job alert to its real end, plus Top Picks and Saved, dedupe against the tracker, read only new descriptions, gate and score them, and deliver the report and phone digest — unattended
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent
disable-model-invocation: true
version: 1.0.0
---

The daily driver. Every mechanical step is one engine script call with a fixed contract; you sequence them, drive the browser, and make exactly two judgement calls (the drift check when a script asks, and nothing else — gating and scoring run in pinned subagents). Never improvise a step, a selector, a cap, or a prompt. Nothing here waits on a human; this runs unattended.

## Constants

```
PLUGIN   = this plugin's root (the directory containing skills/ and agents/)
SCRIPTS  = $PLUGIN/skills/_ultra-engine/scripts
WS       = <workspace>/.job-scout            (absolute)
TODAY    = date +%F ;  RUN_ID = date +%F-%H%M
BUDGET   = jq -r '.jd_budget_per_run // 150' $WS/config.json
VALVE    = 10 ;  FP_DAYS = 45
```

## Browser adapter (D2) — built-in pane first, Chrome extension fallback

| Action | Built-in browser pane | Chrome extension |
|---|---|---|
| navigate | `mcp__Claude_Browser__navigate {url}` | `mcp__claude-in-chrome__navigate {url}` |
| run page script (returns the script's last expression) | `mcp__Claude_Browser__javascript_tool {action:"javascript_exec", text}` | `mcp__claude-in-chrome__javascript_tool {action:"javascript_exec", text}` |
| read page text | `mcp__Claude_Browser__get_page_text` | `mcp__claude-in-chrome__get_page_text` |
| click a card (by ref from `find`) | `mcp__Claude_Browser__find` + `computer left_click` | `mcp__claude-in-chrome__find` + `computer left_click` |

Pick the pane if its `tabs_context` call succeeds; otherwise the extension; otherwise STOP with `no_scrape` reason `browser unavailable`. Page scripts are the files under `$SCRIPTS/page/` pasted **verbatim** into the run-page-script tool. Forbidden: screenshots for discovery, any LinkedIn internal or undocumented API, any other automation. A login wall → STOP `no_scrape` reason `linkedin login required`.

## Step 0 — Preflight (no browser yet)

1. `[ -f $WS/user-profile.json ] && jq -e '.discovery_complete == true and (.requirements|type=="object")' $WS/user-profile.json` else STOP `no_scrape` reason `profile missing or incomplete — run /analyze-cv`. A missing `$WS` is the same stop (`workspace missing`).
2. Follow `../shared-references/render-orchestration.md` Step G (report lifecycle cleanup).
3. `rd=$(bash $SCRIPTS/checkpoint.sh init $WS $RUN_ID)`; `python3 $SCRIPTS/alerts_ledger.py prune --ledger $WS/alerts.json --today $TODAY`.
4. `bash $SCRIPTS/snapshot.sh $WS/tracker.json $WS/cache/ultramode-snapshot.json`; `bash $SCRIPTS/checkpoint.sh save $rd snapshot $WS/cache/ultramode-snapshot.json`. Build the 45-day fingerprint set once: `jq -c -L $SCRIPTS/lib --arg cut $(date -v-${FP_DAYS}d +%F 2>/dev/null || date -d "-${FP_DAYS} days" +%F) 'include "fingerprint"; [.jobs[] | select((.status//"seen")!="rejected" and (.last_seen//"0000") >= $cut) | fp((.company//""); (.title//""); (.location//""))] | unique' $WS/tracker.json > $rd/fp-45d.json`.
5. Choose the browser surface (adapter table). Any STOP here → jump to Step 8 with `run_status=no_scrape`.

## Step 1 — Drain yesterday's queue first (D8)

`n=$(bash $SCRIPTS/jd_queue.sh count $WS/cache/jd-queue.json)`; if `n > 0`: `bash $SCRIPTS/jd_queue.sh pop $WS/cache/jd-queue.json $BUDGET > $rd/queue-pop.json` (on non-zero exit treat as empty). For each popped entry run **Step 4's JD read** and collect its delta into `$rd/sweep-queue.json` (envelope shape in Step 5, `source.board` = the entry's `board`). `used` starts at the number read here.

## Step 2 — Parse the notifications page

Navigate to `https://www.linkedin.com/notifications/?filter=jobs_all`; run `page/notifications.js`; save the returned JSON to `$rd/notifications-dump.json`. Then:

```
python3 $SCRIPTS/alerts_parse.py < $rd/notifications-dump.json > $rd/alerts.json
python3 $SCRIPTS/alerts_ledger.py plan --ledger $WS/alerts.json --alerts $rd/alerts.json --today $TODAY > $rd/walk-plan.json
```

If the dump has `exhausted: false`, record `{"stage":"notifications","message":"Load more not exhausted after 25 clicks"}` in `$rd/pipeline-errors.json` and continue. Zero alerts with `exhausted: true` is a valid quiet day.

## Step 3 — Walk every alert in `walk-plan.json` (D5, D6, D7)

For each `{alert_key, resume_page}` (extract that alert's record from `$rd/alerts.json` into `$rd/alert-<key>.json`):

1. `python3 $SCRIPTS/alerts_ledger.py start --ledger $WS/alerts.json --alert-json $rd/alert-<key>.json --today $TODAY --run-id $RUN_ID`.
2. `page = resume_page`. Loop:
   a. Navigate to `<results_url>&start=$(( (page-1)*25 ))`; run `page/results.js`; save to `$rd/page-<key>-<page>.json`.
   b. `python3 $SCRIPTS/cards_parse.py --surface alert < $rd/page-<key>-<page>.json > $rd/cards-<key>-<page>.json`. Exit 3 (`extractor_mismatch`) → append `{"stage":"walk","message":"extractor_mismatch <key> page <page>"}` to `$rd/pipeline-errors.json`, leave the alert `partial`, and move to the next alert — never continue on an empty read.
   c. Dedupe the cards **before the divider** (the leaf element reading `We found more results related to your search…`; `before_divider: true`): known = id in snapshot `known_ids`; repost = not known and `bash $SCRIPTS/fingerprint.sh "<company>" "<title>" "<location>"` is in `$rd/fp-45d.json` (append `{id, matched_id: <the tracker id with that fingerprint via jq>, alert_key, title, company, location}` to `$rd/reposts.json`); new = the rest → append `{card…, alert_key}` to `$rd/new-cards.json` (skip ids already there from an earlier alert; first alert wins). Cards with `parse_warning: true` are still processed like any other card; their count is disclosed via `pipeline-errors.json`, not dropped.
   d. `python3 $SCRIPTS/alerts_ledger.py page --ledger $WS/alerts.json --key <key> --page <page> --cards-seen <cards> --before-divider <n> --known <k> --reposts <r> --new <new>`.
   e. `python3 $SCRIPTS/walk_stop.py --alert $rd/alert-<key>.json --page $rd/cards-<key>-<page>.json --page-no <page> --valve $VALVE > $rd/stop-<key>-<page>.json`. If `needs_model_check` is true, answer ONE question yourself from the card titles in `undecided_ids`: "Do any of these titles plausibly match the alert keywords `<keywords>`?" and re-run with `--model-says-match true|false`. Record your answer in `$rd/pipeline-errors.json` as `{"stage":"walk","message":"model drift check <key> page <page>: <true|false>"}` (it is a disclosure, not an error).
   f. `stop: true` → `python3 $SCRIPTS/alerts_ledger.py complete --ledger $WS/alerts.json --key <key> --reason <reason>`; break. Else `page += 1`.
3. `bash $SCRIPTS/checkpoint.sh save $rd walk-<key>`.

## Step 4 — Read descriptions for new cards, within budget (D7, D8)

Order: queue drain (done), then alert cards in `$rd/new-cards.json` order, then Top Picks, then Saved. For each card while `used < BUDGET`:

1. Navigate to `https://www.linkedin.com/jobs/search-results/?currentJobId=<id>` (alerts) or `https://www.linkedin.com/jobs/view/<id>/` (Top Picks / Saved / Similar); read page text; take everything from `About the job` to the end of the description block. If the text has an expander (`…more` / `Show more`), `find` it, click it, re-read.
2. `mkdir -p $WS/jds; printf '%s\n' "<text>" > $WS/jds/<id>.txt.tmp && mv $WS/jds/<id>.txt.tmp $WS/jds/<id>.txt`. `used += 1`.
3. Emit the delta (Step 5 shape) with `jd_path: "jds/<id>.txt"`.

Cards left when the budget is exhausted: write them to `$rd/queued.json` and `bash $SCRIPTS/jd_queue.sh push $WS/cache/jd-queue.json $rd/queued.json` (entries `{id, title, company, location, url, board, alert_key}`). Always write `$rd/jd-fetch.json` = `{"budget": BUDGET, "used": used, "deferred": <queue count after push>}` and `bash $SCRIPTS/checkpoint.sh save $rd jd-fetch $rd/jd-fetch.json`, even when nothing was read.

## Step 5 — Envelopes, validation, merge (all-or-nothing)

Group deltas into envelopes: one per alert (`$rd/sweep-alert-<key>.json`), plus `sweep-queue`, `sweep-toppicks`, `sweep-saved`. Envelope:

```json
{"status":"ok","counts":{"scanned":<cards seen>,"matched":<new>,"dropped_explicit_violation":0,"returned":<deltas>,"capped":false},
 "deltas":[{"id":"4460908564","url":"https://www.linkedin.com/jobs/view/4460908564/","title":"…","company":"…","location":"Germany (Remote)",
            "source":{"lane":"linkedin","provider":"linkedin","board":"Job Alert"},"fingerprint":"<fingerprint.sh output>",
            "posted_at":"<YYYY-MM-DD from posted_ago, else empty>","jd_path":"jds/4460908564.txt","signals":{"remote":"remote"},
            "matched_query":"linux engineer Contract Remote","alert_key":"<key>","tags":[]}],
 "errors":[],"continuation_cursor":null}
```

`board` ∈ `Job Alert | Top Picks | Saved | Similar`; `signals.remote` from the card's `workplace` (`unknown` when absent). Deltas whose JD was queued carry `jd_path: null`. Then:

```
for f in $rd/sweep-*.json; do python3 $SCRIPTS/validate_delta.py --ws $WS $f || { echo "REFUSED $f"; exit 1; }; done
python3 $SCRIPTS/merge_tracker.py --ws $WS --tracker $WS/tracker.json --today $TODAY $rd/sweep-*.json > $rd/merge.json
bash $SCRIPTS/checkpoint.sh save $rd merge $rd/merge.json
```

A merge failure: append `{"stage":"merge","message":"<first stderr line>"}` to `$rd/pipeline-errors.json` and continue to Step 8 (always render). Then set `matched_query` and `alert_key` on each merged entry with the single-entry atomic recipe in `../shared-references/state-validators.md`.

## Step 6 — Top Picks and Saved (after every alert is complete or partial)

Top Picks: navigate `https://www.linkedin.com/jobs/collections/recommended/`; run `page/toppicks.js`; `cards_parse.py --surface toppicks`; dedupe as Step 3c; Step 4 within budget; envelope `sweep-toppicks` (`board: "Top Picks"`). Saved: navigate `https://www.linkedin.com/jobs-tracker/`; run `page/saved.js`; `cards_parse.py --surface saved` (`note: "saved_empty"` is a clean zero); same path; `board: "Saved"`. Both merge in Step 5's second pass (`merge_tracker.py` again with only the new envelopes).

## Step 7 — Gate, then score (D14)

Batch this run's merged entries that have a `jd_path` into groups of 5. For each batch dispatch `Agent` with `subagent_type: "gate-batch"` and the envelope from `../shared-references/subagent-protocol.md`:

```json
{"task":"gate-batch","inputs":{"plugin_root":"$PLUGIN","workspace":"$WS","jobs":[{"id":"…","title":"…","company":"…","location":"…","workplace":"remote","salary_text":"…","jd_path":"jds/….txt"}],
 "requirements":<user-profile.requirements>,"profile_hash":"<bash $SCRIPTS/profile_hash.sh $WS/user-profile.json>","cv_hash":"<user-profile.cv_hash>","rubric_version":"v1"},
 "budget_lines":200,"allowed_tools":["Read"]}
```

Persist each delta atomically (`gate_violations`, `signals`; `tier: "D"`, `tier_reason: "gated: <kinds>"` when gated with ≥2 kinds). Jobs with zero violations, and jobs with exactly one violated kind (flag `near_miss_candidate: true`), go to `subagent_type: "score-batch"` in batches of 5 with the same envelope plus `"dimensions": <user-profile.dimensions>`, `"segment"`, `"cv_summary"`. Persist `tier`, `tier_reason`, `dimensions`, `rubric_version`, and the optional fields when present; near-miss candidates keep `tier: "D"` and gain `near_miss` + `near_miss_would_be_tier` when the rubric says A/B. Write the score cache entry keyed `(id, cv_hash, profile_hash, rubric_version)`. `bash $SCRIPTS/checkpoint.sh save $rd scoring`.

**Similar jobs (one round):** for each this-run entry now at `tier: "A"`, navigate to its `url`, read page text, collect up to 5 ids from the "Similar jobs" rail via `find`/page text (`/jobs/view/<id>/` links), dedupe against the snapshot, Step 4 within budget, envelope `sweep-linkedin-similar` (`board: "Similar"`, `notes: "expanded from: <seed id>"`), validate → merge → gate → score exactly as above. Expansion roles never seed further expansion.

## Step 8 — Scorecard, payload, render, digest — ALWAYS

```
python3 $SCRIPTS/coverage.py --ledger $WS/alerts.json --run-id $RUN_ID --reposts $rd/reposts.json --out $rd/coverage.json
bash $SCRIPTS/scorecard.sh $rd $WS/tracker.json $TODAY > $rd/scorecard.json
bash $SCRIPTS/payload_notifications.sh $WS/tracker.json $rd $TODAY <fresh|no_scrape> ["<reason>"] > $rd/payload.json
```

Render per `../shared-references/render-orchestration.md` Steps B–F with `view: "check-job-notifications"` and `$rd/payload.json` (Hard Rule 8). Then:

```
python3 $SCRIPTS/digest.py --payload $rd/payload.json --profile $WS/user-profile.json --out $WS/reports/check-job-notifications-$TODAY-digest.txt --last-success "$(jq -r '.stats.last_run // "unknown"' $WS/tracker.json)"
bash $SCRIPTS/checkpoint.sh save $rd render
```

A `no_scrape` run performs only this step (no tracker writes) and still writes the digest.

## Step 9 — Print

1. `✓ {{alerts}} alerts walked · {{cards}} cards · {{new}} new — A:{{a}} B:{{b}} C:{{c}} · Filtered:{{d}} · Queued:{{queued}} — report delivered` (or `✓ No fresh scrape — {{reason}} — digest written`).
2. One line per A/B/C role: `{{tier}} · {{title}} — {{company}} → {{url}}`.
3. `Digest: $WS/reports/check-job-notifications-$TODAY-digest.txt` and every `pipeline-errors.json` message as a disclosure line.
4. Next steps as text, never a question: `/apply <id>` for approved roles, `/bend <id>` for near misses, `/ultramode` for the wider market.

## Failure table (all disclosed, none silent)

| Condition | Action |
|---|---|
| Workspace or profile missing | STOP `no_scrape`; digest + report say why |
| No browser surface / login wall | STOP `no_scrape`; no tracker writes |
| `extractor_mismatch` on a page | Alert stays `partial`; disclosed; next alert |
| Validator refuses an envelope | Fix nothing by hand; disclose; the envelope is excluded from the merge |
| Merge fails | Disclose; still render with whatever completed |
| Budget exhausted | Queue the rest; report "Queued for tomorrow" |

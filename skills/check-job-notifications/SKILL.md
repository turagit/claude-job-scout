---
name: check-job-notifications
description: Walk every LinkedIn job alert to its real end, plus Top Picks and Saved, dedupe against the tracker, read only new descriptions, gate and score them, and deliver the report and phone digest — unattended
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent
disable-model-invocation: true
version: 1.2.0
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

1. `[ -d $WS ]` else this is a terminal stop, not a `no_scrape` one: print `✗ No fresh scrape — workspace missing at <path> — nothing written` and stop the command entirely — there is no `$rd` yet, so nothing is written and no digest is produced.
2. `rd=$(bash $SCRIPTS/checkpoint.sh init $WS $RUN_ID)`; `python3 $SCRIPTS/alerts_ledger.py prune --ledger $WS/alerts.json --today $TODAY`. Initialise this run's working files: `[ -f $rd/pipeline-errors.json ] || echo '{"errors": []}' > $rd/pipeline-errors.json`; `echo '[]' > $rd/reposts.json`; `echo '[]' > $rd/new-cards.json`; `echo '[]' > $rd/queued.json`. Every disclosure below uses one idiom — `jq --argjson e '<obj>' '.errors += [$e]' $rd/pipeline-errors.json > $rd/pipeline-errors.json.tmp && mv $rd/pipeline-errors.json.tmp $rd/pipeline-errors.json` — and the same shape with `. += [$e]` (no `.errors` wrapper) appends to `reposts.json`, `new-cards.json`, `queued.json`.
3. `[ -f $WS/user-profile.json ] && jq -e '.discovery_complete == true and (.requirements|type=="object")' $WS/user-profile.json` else STOP `no_scrape` reason `profile missing or incomplete — run /analyze-cv` and jump to Step 8 (`$rd` already exists, so the digest and report still get written).
4. Follow `../shared-references/render-orchestration.md` Step G (report lifecycle cleanup).
5. `bash $SCRIPTS/snapshot.sh $WS/tracker.json $WS/cache/ultramode-snapshot.json`; `bash $SCRIPTS/checkpoint.sh save $rd snapshot $WS/cache/ultramode-snapshot.json`. Build the 45-day fingerprint set: `jq -c -L $SCRIPTS/lib --arg cut $(date -v-${FP_DAYS}d +%F 2>/dev/null || date -d "-${FP_DAYS} days" +%F) 'include "fingerprint"; [.jobs[] | select((.status//"seen")!="rejected" and (.last_seen//"0000") >= $cut) | fp((.company//""); (.title//""); (.location//""))] | unique' $WS/tracker.json > $rd/fp-45d.json`. Build the fingerprint→id map once: `jq -c -L $SCRIPTS/lib 'include "fingerprint"; [.jobs[]|select((.status//"seen")!="rejected")|{(fp((.company//"");(.title//"");(.location//""))): .id}] | add // {}' $WS/tracker.json > $rd/fp-map.json`.
6. Choose the browser surface (adapter table). Any STOP here → jump to Step 8 with `run_status=no_scrape` (`$rd` already exists).
7. `ALLOWED_WT=$(jq -c '[(.requirements.deal_breakers[]? | select(.kind=="work_arrangement") | .values[]?)] | map(ascii_downcase | if .=="on-site" then "onsite" else . end) | unique' $WS/user-profile.json)` — the declared work-arrangement allow-list, lower-cased, `on-site`/`onsite` folded together. Example: a profile with `values: ["remote"]` → `ALLOWED_WT = ["remote"]`; a profile with no `work_arrangement` deal-breaker entry at all → `ALLOWED_WT = []`. **`ALLOWED_WT == []` disables the Step 3c/6 card drop entirely** — every card proceeds straight to dedupe; an empty allow-list means "nothing declared", never "nothing allowed".

## Step 1 — Drain yesterday's queue first (D8)

`DRAIN_CAP=$(( BUDGET / 3 ))` (integer division; 50 at the default 150 — this keeps at least two thirds of `BUDGET` free for the alert walk itself). `n=$(bash $SCRIPTS/jd_queue.sh count $WS/cache/jd-queue.json notifications)`; if `n > 0`: `bash $SCRIPTS/jd_queue.sh pop $WS/cache/jd-queue.json $DRAIN_CAP notifications > $rd/queue-pop.json` (on non-zero exit treat as empty; the `notifications` origin means this only ever pops this command's own queued entries — ultramode's leftover queue is never drained here). For each popped entry run **Step 4's JD read** (its failure clause re-pushes and discloses — never silently drops) and collect the resulting delta into `$rd/sweep-queue.json` (envelope shape in Step 5, `source.board` = the entry's `board`). `used` starts at the number of successful reads here. If `n > DRAIN_CAP` (entries still remain after the pop), disclose `{"stage":"queue","message":"drained <popped> of <n> queued (cap BUDGET/3)"}`.

## Step 2 — Parse the notifications page

Navigate to `https://www.linkedin.com/notifications/?filter=jobs_all`; run `page/notifications.js`; save the returned JSON to `$rd/notifications-dump.json`. Then:

```
python3 $SCRIPTS/alerts_parse.py < $rd/notifications-dump.json > $rd/alerts.json
python3 $SCRIPTS/alerts_ledger.py plan --ledger $WS/alerts.json --alerts $rd/alerts.json --today $TODAY > $rd/walk-plan.json
```

If the dump has `exhausted: false`, disclose `{"stage":"notifications","message":"Load more not exhausted after 25 clicks"}` and continue. When `alerts.json`'s `dropped_unparseable > 0`, disclose `{"stage":"notifications","message":"<n> alert links could not be parsed — LinkedIn link format may have changed"}`. When the dump's own `alerts[]` had ≥1 entry but `alerts.json`'s `alerts` is empty, that is `extractor_mismatch` for the notifications page: disclose `{"stage":"notifications","message":"extractor_mismatch notifications page"}` and STOP the alert walk for this run (skip Step 3 entirely), continuing to Step 6 onward. Zero alerts with `exhausted: true` and a raw dump with no alert links at all is a valid quiet day.

## Step 3 — Walk every alert in `walk-plan.json`'s `.walk[]` (D5, D6, D7)

For each `{alert_key, resume_page}` (extract that alert's record from `$rd/alerts.json` into `$rd/alert-<key>.json`):

1. `python3 $SCRIPTS/alerts_ledger.py start --ledger $WS/alerts.json --alert-json $rd/alert-<key>.json --today $TODAY --run-id $RUN_ID`.
2. `page = resume_page`. Loop:
   a. Navigate to `<results_url>&start=$(( (page-1)*25 ))`; run `page/results.js`; save to `$rd/page-<key>-<page>.json`.
   b. `python3 $SCRIPTS/cards_parse.py --surface alert --today $TODAY < $rd/page-<key>-<page>.json > $rd/cards-<key>-<page>.json`. Exit 3 (`extractor_mismatch`) → disclose `{"stage":"walk","message":"extractor_mismatch <key> page <page>"}`, leave the alert `partial`, and move to the next alert — never continue on an empty read. Exit 0 with `zero_cards: true` → disclose `{"stage":"walk","message":"zero cards on <key> page <page> (claimed: <claimed_results>)"}`, leave the alert `partial`, and move to the next alert — never run `walk_stop.py` on it. `low_confidence > 0` → disclose `{"stage":"walk","message":"<n> low-confidence cards on <key> page <page>"}`.
   c. First, when `ALLOWED_WT` (Step 0) is non-empty — an empty `ALLOWED_WT` disables this drop entirely, every card proceeds straight to dedupe — drop explicit workplace violations, card by card, before any dedupe and before any JD read: a card whose `workplace` is not `"unknown"` and not a member of `ALLOWED_WT` is dropped now — append `{id, title, company, location, workplace, alert_key}` to `$rd/dropped-cards.json`, count it as this page's `--dropped`; `unknown` workplace is never dropped. Then dedupe the remaining cards **before the divider** (the leaf element reading `We found more results related to your search…`; `before_divider: true`): known = id in snapshot `known_ids`; repost = not known and `fp=$(bash $SCRIPTS/fingerprint.sh "<company>" "<title>" "<location>")` is a member of `$rd/fp-45d.json` (the 45-day fingerprint set from Step 0) — use `$rd/fp-map.json` only to resolve `matched_id: <fp-map.json[$fp]>` for disclosure, never to decide repost-ness — append `{id, matched_id, alert_key, title, company, location}` to `$rd/reposts.json`; new = the rest → append `{card…, alert_key}` to `$rd/new-cards.json` (skip ids already there from an earlier alert; first alert wins). Cards with `parse_warning: true` are still processed like any other card, never dropped.
   d. `python3 $SCRIPTS/alerts_ledger.py page --ledger $WS/alerts.json --key <key> --page <page> --cards-seen <cards> --before-divider <n> --known <k> --reposts <r> --new <new> --dropped <d>`.
   e. `python3 $SCRIPTS/walk_stop.py --alert $rd/alert-<key>.json --page $rd/cards-<key>-<page>.json --page-no <page> --valve $VALVE > $rd/stop-<key>-<page>.json`. If `needs_model_check` is true, answer ONE question yourself from the card titles in `undecided_ids`: "Do any of these titles plausibly match the alert keywords `<keywords>`?" and re-run with `--model-says-match true|false`. Disclose your answer as `{"stage":"walk","message":"model drift check <key> page <page>: <true|false>"}` (a disclosure, not an error).
   f. `stop: true` → `python3 $SCRIPTS/alerts_ledger.py complete --ledger $WS/alerts.json --key <key> --reason <reason>`; break. Else `page += 1`.
3. `bash $SCRIPTS/checkpoint.sh save $rd walk-<key>`.

## Step 4 — Read descriptions for new cards, within budget (D7, D8)

Order: queue drain (done), then alert cards in `$rd/new-cards.json` order, then Top Picks, then Saved. For each card while `used < BUDGET`:

1. Navigate to `https://www.linkedin.com/jobs/search-results/?currentJobId=<id>` (alerts) or `https://www.linkedin.com/jobs/view/<id>/` (Top Picks / Saved / Similar); read page text; take everything from `About the job` to the end of the description block. If the text has an expander (`…more` / `Show more`), `find` it, click it, re-read.
2. Page didn't load, or no `About the job` block found: set `attempts` = (entry's `attempts` or 0) + 1. If `attempts < 3`, re-push `{id, title, company, location, url, board, alert_key, attempts}` onto the queue now (`bash $SCRIPTS/jd_queue.sh push $WS/cache/jd-queue.json <one-entry-array-file> notifications`) and disclose `{"stage":"jd-read","message":"JD read failed (attempt <attempts>), re-queued: <id>"}`; if `attempts` reaches 3, do NOT re-push — append the entry to `$rd/dead-links.json` and disclose `{"stage":"jd-read","message":"dropped after 3 failed reads (listing gone): <id>"}`. Either way move to the next card — this card does not count against `used` and gets no delta this run.
3. `mkdir -p $WS/jds; printf '%s\n' "<text>" > $WS/jds/<id>.txt.tmp && mv $WS/jds/<id>.txt.tmp $WS/jds/<id>.txt`. `used += 1`.
4. Emit the delta (Step 5 shape) with `jd_path: "jds/<id>.txt"`.

Cards left when the budget is exhausted also get a delta (Step 5 shape) with `jd_path: null`, so `returned == matched` and `capped: false` stay truthful — the queue drain owns fetching their JD next run. Write them to `$rd/queued.json` too and `bash $SCRIPTS/jd_queue.sh push $WS/cache/jd-queue.json $rd/queued.json notifications` (entries `{id, title, company, location, url, board, alert_key}`). Always write `$rd/jd-fetch.json` = `{"budget": BUDGET, "used": used, "deferred": <queue count after push>}` and `bash $SCRIPTS/checkpoint.sh save $rd jd-fetch $rd/jd-fetch.json`, even when nothing was read.

## Step 5 — Envelopes, validation, merge (all-or-nothing)

Group deltas into envelopes: one per alert (`$rd/sweep-alert-<key>.json`), plus `sweep-queue`, `sweep-toppicks`, `sweep-saved`. Envelope:

```json
{"status":"ok","counts":{"scanned":<cards seen>,"matched":<new + dropped>,"dropped_explicit_violation":0,"returned":<deltas>,"capped":false},
 "deltas":[{"id":"4460908564","url":"https://www.linkedin.com/jobs/view/4460908564/","title":"…","company":"…","location":"Germany (Remote)",
            "source":{"lane":"linkedin","provider":"linkedin","board":"Job Alert"},"fingerprint":"<fingerprint.sh output>",
            "posted_at":"<the card's own posted_at, from cards_parse.py --today>","jd_path":"jds/4460908564.txt","signals":{"remote":"remote"},
            "matched_query":"linux engineer Contract Remote","alert_key":"<key>","tags":[]}],
 "errors":[],"continuation_cursor":null}
```

`board` ∈ `Job Alert | Top Picks | Saved | Similar`; `signals.remote` from the card's `workplace` (`unknown` when absent). Deltas whose JD was queued (Step 4) carry `jd_path: null`. `counts.dropped_explicit_violation` = the count of `$rd/dropped-cards.json` entries with this envelope's `alert_key` (Step 3c/6). `counts.matched` = new + dropped — the pre-drop genuinely-new count, not just the survivors — so `validate_delta.py`'s cap check (`returned == matched` when uncapped) isn't fooled into double-subtracting the drop. Then:

```
survivors=""
for f in $rd/sweep-*.json; do
  if python3 $SCRIPTS/validate_delta.py --ws $WS "$f" 2>$rd/validate-err.txt; then
    survivors="$survivors $f"
  else
    mv "$f" "$rd/refused-$(basename "$f")"
  fi
done
python3 $SCRIPTS/merge_tracker.py --ws $WS --tracker $WS/tracker.json --today $TODAY $survivors > $rd/merge-1.json
bash $SCRIPTS/checkpoint.sh save $rd merge-1 $rd/merge-1.json
bash $SCRIPTS/snapshot.sh $WS/tracker.json $WS/cache/ultramode-snapshot.json
```

A validator refusal never gets fixed by hand: `mv` the refused envelope to `$rd/refused-<name>.json`, disclose `{"stage":"validate","message":"refused <name>: <first stderr line>"}`, and merge only the survivors — by their explicit filenames (`$survivors` above), never a re-globbed `$rd/sweep-*.json` (a refusal must never silently re-enter the merge). A merge failure: write `$rd/merge-1.json` as `{"merged":0,"collisions_also_seen":0,"url_upgrades":0,"skipped_known":0}` (the neutral element for Step 7's sum), disclose `{"stage":"merge","message":"<first stderr line>"}`, and continue to Step 8 (always render). Then set `matched_query` and `alert_key` on each merged entry with the single-entry atomic recipe in `../shared-references/state-validators.md`.

## Step 6 — Top Picks and Saved (after every alert is complete or partial)

Top Picks: navigate `https://www.linkedin.com/jobs/collections/recommended/`; run `page/toppicks.js`; `cards_parse.py --surface toppicks --today $TODAY`; drop explicit workplace violations first exactly as Step 3c (same guard: only when `ALLOWED_WT` is non-empty; `$rd/dropped-cards.json`, `unknown` never dropped — `alert_key` = `"Top Picks"`); dedupe the rest as Step 3c (fp-map for `matched_id`); Step 4 within budget; envelope `sweep-toppicks` (`board: "Top Picks"`, `counts.dropped_explicit_violation` = this surface's dropped count, `counts.matched` = new + dropped as in Step 5). Saved: navigate `https://www.linkedin.com/jobs-tracker/`; run `page/saved.js`; `cards_parse.py --surface saved --today $TODAY` (`note: "saved_empty"` is a clean zero); same drop-then-dedupe path (`alert_key` = `"Saved"`); `board: "Saved"`. Merge this pass with Step 5's validate-then-merge recipe, naming `$rd/sweep-toppicks.json $rd/sweep-saved.json` explicitly (never a `sweep-*` glob) → `$rd/merge-2.json` (same zero-fill on failure), then rebuild the snapshot again so Step 7's similar-jobs expansion dedupes against fresh ids.

## Step 7 — Gate, then score (D14)

Batch this run's merged entries that have a `jd_path` into groups of 5, plus every tracker entry with a `jd_path`, `tier: "untiered"`, and `first_seen` within the last 7 days (a prior run's subagent failure, retried here). Skip any job whose `cache/scores.json` key `(id, cv_hash, profile_hash, rubric_version)` already exists. For each batch dispatch `Agent` with `subagent_type: "gate-batch"` and the envelope from `../shared-references/subagent-protocol.md`:

```json
{"task":"gate-batch","inputs":{"plugin_root":"$PLUGIN","workspace":"$WS","jobs":[{"id":"…","title":"…","company":"…","location":"…","workplace":"remote","salary_text":"…","jd_path":"jds/….txt"}],
 "requirements":<user-profile.requirements>,"profile_hash":"<bash $SCRIPTS/profile_hash.sh $WS/user-profile.json>","cv_hash":"<user-profile.cv_hash>","rubric_version":"v1"},
 "budget_lines":200,"allowed_tools":["Read"]}
```

`Agent` unavailable → run the batch sequentially in-thread per `subagent-protocol.md`'s fallback. A batch returning `status: "error"` or an unparsable body → disclose `{"stage":"gate"|"score","message":"<batch ids>: <reason>"}` and leave those entries `tier: "untiered"` (retried next run via the selection above) — never guess a tier.

Persist each gate delta atomically — `gate_violations` and `signals` (including `rate`, the JD-disclosed compensation figure verbatim, e.g. `"€800/day"`, or `"unknown"`) are persisted verbatim onto the tracker entry; `tier: "D"`, `tier_reason: "gated: <kinds>"` when gated with ≥2 kinds. Jobs with zero violations, and jobs with exactly one violated kind (flag `near_miss_candidate: true`), go to `subagent_type: "score-batch"` in batches of 5 with the same envelope plus `"dimensions"`, `"segment"`, `"cv_summary"` (all three read from `user-profile.json`). Persist `tier`, `tier_reason`, `dimensions`, `rubric_version`, and the optional fields when present; near-miss candidates keep `tier: "D"` and gain `near_miss` + `near_miss_would_be_tier` when the rubric says A/B. Write the score cache entry (`cache/scores.json`, keyed `(id, cv_hash, profile_hash, rubric_version)`). `bash $SCRIPTS/checkpoint.sh save $rd scoring`.

**Similar jobs (one round):** for each this-run entry now at `tier: "A"`, navigate to its `url`, read page text, collect up to 5 ids from the "Similar jobs" rail via `find`/page text (`/jobs/view/<id>/` links), dedupe against the rebuilt snapshot. For each new id: navigate to `https://www.linkedin.com/jobs/view/<id>/`, read page text — title = the first heading line, company and location = the next two lines of the header block — then read the JD as in Step 4, fingerprint via `fingerprint.sh`. Step 4 within budget; envelope `sweep-linkedin-similar` (`board: "Similar"`); validate → merge, naming `$rd/sweep-linkedin-similar.json` explicitly (`$rd/merge-3.json`, same zero-fill and refused-envelope handling as Step 5 on failure, rebuild snapshot) → gate → score exactly as above. `merge_tracker.py` writes `notes: ""`, so after this merge set `notes: "expanded from: <seed id>"` together with `matched_query`/`alert_key` in the single-entry atomic recipe. Expansion roles never seed further expansion.

Before Step 8: `jq -s '{merged:(map(.merged//0)|add),collisions_also_seen:(map(.collisions_also_seen//0)|add),url_upgrades:(map(.url_upgrades//0)|add),skipped_known:(map(.skipped_known//0)|add)}' $rd/merge-*.json > $rd/merge.json`. Re-write `$rd/jd-fetch.json` = `{"budget": BUDGET, "used": <final used>, "deferred": <final queue count>}` (`deferred` from `bash $SCRIPTS/jd_queue.sh count $WS/cache/jd-queue.json notifications`), so the Top Picks, Saved, and Similar reads from Steps 6–7 are counted, not just the alert walk's.

## Step 8 — Scorecard, payload, render, digest — ALWAYS

```
python3 $SCRIPTS/coverage.py --ledger $WS/alerts.json --run-id $RUN_ID --reposts $rd/reposts.json --out $rd/coverage.json
bash $SCRIPTS/scorecard.sh $rd $WS/tracker.json $TODAY > $rd/scorecard.json
bash $SCRIPTS/payload_notifications.sh $WS/tracker.json $rd $TODAY <fresh|no_scrape> ["<reason>"] > $rd/payload.json
```

Render per `../shared-references/render-orchestration.md` Steps B–F with `view: "check-job-notifications"` and `$rd/payload.json` (Hard Rule 8), with these overrides: an absent or `ask` `render` key is treated as `always`; a Step F render error takes the markdown branch without prompting. Nothing in this command waits on a human. Then:

```
python3 $SCRIPTS/digest.py --payload $rd/payload.json --profile $WS/user-profile.json --out $WS/reports/check-job-notifications-$TODAY-digest.txt --last-success "$(jq -r '.stats.last_run // "unknown"' $WS/tracker.json)" --workspace-name "$(basename "$(dirname "$WS")")"
bash $SCRIPTS/checkpoint.sh save $rd render
```

A `no_scrape` run performs only this step (no tracker writes) and still writes the digest.

## Step 9 — Print

1. `✓ {{alerts}} alerts walked · {{cards}} cards · {{new}} new — A:{{a}} B:{{b}} C:{{c}} · Filtered:{{d}} · Queued:{{queued}} — report delivered` (or `✓ No fresh scrape — {{reason}} — digest written`).
2. One line per A/B/C role: `{{tier}} · {{title}} — {{company}} → {{url}}`.
3. `Digest: $WS/reports/check-job-notifications-$TODAY-digest.txt` and every `$rd/pipeline-errors.json` `.errors[]` message as a disclosure line.
4. Next steps as text, never a question: `/apply <id>` for approved roles, `/bend <id>` for near misses, `/ultramode` for the wider market.

## Failure table (all disclosed, none silent)

| Condition | Action |
|---|---|
| Workspace missing | Terminal stop before `$rd` exists — print and stop; nothing written, no digest |
| Profile missing or incomplete | STOP `no_scrape`; digest + report say why |
| No browser surface / login wall | STOP `no_scrape`; no tracker writes |
| `extractor_mismatch` on a page | Alert stays `partial`; disclosed; next alert |
| JD read fails 3 times (expired listing) | Dropped from the queue; listed in `$rd/dead-links.json`; disclosed |
| Card's `workplace` is explicit and outside `ALLOWED_WT` | Dropped before the JD read; counted `--dropped`; `unknown` never dropped |
| Yesterday's queue has more than `DRAIN_CAP` entries | Only `DRAIN_CAP` popped this run; disclosed; the rest wait for tomorrow |
| Zero cards parsed on an alert page (`zero_cards: true`) | Alert stays `partial`; disclosed; next alert — never run `walk_stop.py` |
| Validator refuses an envelope | Fix nothing by hand; `mv` to `$rd/refused-<name>.json`; disclose; merged only by explicit surviving filenames |
| Merge fails | Disclose; zero-filled counters; still render with whatever completed |
| A JD read fails (no page / no `About the job`) | Re-push to the queue; disclose; not counted against budget |
| A gate-batch/score-batch errors or returns unparsable output | Disclose; entry stays `untiered`; retried next run |
| `Agent` tool unavailable | Disclose; gate/score run sequentially in-thread |
| Budget exhausted | Queue the rest; report "Queued for tomorrow" |
| An alert link parses but `f_TPR`/`keywords` is bad or missing | Counted in `dropped_unparseable`; disclosed once with a count |
| Alert links present but `alerts` parses empty | Treated as `extractor_mismatch` for the notifications page; disclosed; alert walk stopped for this run |

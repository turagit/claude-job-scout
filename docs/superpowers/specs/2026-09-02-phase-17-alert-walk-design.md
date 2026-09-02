# Phase 17 — The alert walk: deterministic LinkedIn job-alert discovery for the daily driver

**Status:** approved — every decision below was resolved one-by-one in the 2026-09-02 grill session; this document is the record
**Date:** 2026-09-02
**Predecessors:** Phase 14 (deterministic engine spine) · Phase 15 (the ultramode merge) · Phase 16 (EU/NL source parity)
**Evidence:** [`2026-09-02-phase-17-alert-walk-linkedin-dom-evidence.md`](2026-09-02-phase-17-alert-walk-linkedin-dom-evidence.md) — the live-page observations every contract here is built on. Read it before touching an extractor.

## 1. Problem

`/check-job-notifications` is the daily driver: it runs every night from a Cowork scheduled task in the CVFREELANCER workspace and ad hoc during the day. It is losing real opportunities, and its own reports hide the loss.

1. **It reads the preview, not the alert.** Each alert's "View jobs" link carries a six-ID `originToLandingJobPostings` parameter. The 2026-09-01 "exhaustive" pass and the 2026-09-02 nightly both took that list as authoritative. The first alert walked on 2026-09-02 held **24 exact matches; the tracker knew 10**. The nightly report for the same morning claimed 68 collected, 64 known, 4 new.
2. **Its stop rule is prose and wrong.** "Identify every unread alert (highlighted in blue)" — no read/unread marker exists in the DOM. "Scroll 2–3 times" — the results list is paginated, 25 per page, exact matches end at a divider that may sit on page 1 or page 3.
3. **It is the only discovery command off the engine spine.** `/ultramode` gets snapshot, delta validation, atomic merge, checkpoints, the queue and the scorecard from `_ultra-engine`. The daily driver hand-rolls dedupe and tracker writes in prose, and the live tracker shows the result: 200+ free-text `source` values, a non-canonical `gated` status, bare-string gate violations, mixed date formats, ad-hoc fields. None of the mandated validators ran.
4. **It is interactive in an unattended slot.** Three prompts (create workspace, continue to a second Top Picks sweep, which jobs to apply to) stall a scheduled run. The task prompt compensates by restating gates and a no-browser fallback that re-ranks the whole tracker.
5. **Its Saved-jobs URL is dead.** `/my-items/saved-jobs/` now redirects to the Job tracker page.
6. **The command file is 256 lines of version notes and legacy fallbacks** — token cost on every run and ambiguity for a smaller runner model.

## 2. Decisions locked (the grill record)

| # | Decision |
|---|---|
| D1 | **Script extraction, not screenshots.** The notifications page, every alert results page, Top Picks and the Job-tracker Saved tab are read through in-page scripts and page-text reads. Screenshots are never used for discovery. The extraction scripts are engine artefacts with fixtures and tests; they use only the stable anchors named in the evidence file. |
| D2 | **Two Anthropic-operated browser surfaces, ordered.** The built-in browser pane is primary; the Chrome extension is the fallback when the pane is absent or broken. Both are documented in `browser-policy.md`; everything else stays forbidden. The command carries one adapter table mapping *navigate / run page script / read page text* to each surface's tool names. |
| D3 | **Internal endpoints are off-limits.** Voyager and any other LinkedIn internal API are named as forbidden in the command and the browser policy. Descriptions come from the rendered pane only. |
| D4 | **Alert identity** = `keywords` + `geoId` + `f_TPR` epoch from the link, plus every other query parameter carried verbatim for re-opening. Same keywords with a newer epoch is a new alert. |
| D5 | **Page-walk stop rules, in order:** (1) the divider `We found more results related to your search that may not be exact matches…` — stop, the cards before it are the alert; (2) **drift** — a whole page (never mid-page) on which no card matches the alert's intent: no card carries the alert's workplace qualifier when the keywords name one (`Remote`/`Hybrid`/`On-site`), and no card title shares a meaningful term with the keywords when they do not; the script decides the qualifier case, the model decides the title case only when the script cannot; (3) the **10-page valve** (250 cards). If the divider has not appeared and the page is not drifted, follow `Next`. Every stop reason is recorded per alert (`divider` / `drift` / `valve` / `no_next`). Recorded-reason precedence when several apply on the same page: divider, then valve, then no_next, then drift — the stop decision is identical, only the coverage label differs. |
| D6 | **Alert ledger** at `.job-scout/alerts.json` (schema in §4). Completed alerts are never re-walked; `partial` alerts resume from `last_page + 1`; records older than 30 days are pruned on load. The notifications list is exhausted (`Load more` until it disappears) before walking. |
| D7 | **Dedupe.** ID dedupe against the snapshot is absolute. Repost-fingerprint dedupe matches only tracker entries with `last_seen` within 45 days and status not `rejected`; every fingerprint drop is disclosed with both IDs and the card text in a collapsed "Treated as reposts" group. **No gating on card text** — every genuinely new job gets its JD read, then gated on JD text. Amended 2026-09-02 (user ruling): a card whose visible workplace type is explicit and outside the allowed work_arrangement set is dropped before the JD read, counted and disclosed; `unknown` is never dropped. |
| D8 | **JD budget** 150 per run (`config.json` `jd_budget_per_run`, default 150). Overflow goes to the existing `jd_queue.sh` queue with the card record; the queue is drained first on the next run, before any new alert is walked; queued roles are listed in the report as "queued for tomorrow". Nothing is discarded. |
| D9 | **Surfaces and order:** alerts (all, fully) → Top Picks page 1 → Job-tracker Saved tab → similar-jobs from A-tier hits (≤5 per seed, one round). The interactive second Top Picks sweep (old Step 10) is removed. Alerts always complete before optional surfaces start. Surface priority on duplicate sightings: `Job Alert > Top Picks > Saved > Similar`. |
| D10 | **Unattended by design.** No prompts in either mode. Missing workspace, missing/incomplete profile, or no browser surface ⇒ hard stop with a one-line reason in the digest and a `no_scrape` status; never a re-rank of existing jobs. Next steps are printed, never asked. |
| D11 | **Outputs:** the HTML report via `_visualizer` (unchanged pipeline, extended payload), a **plain-text phone digest** `.job-scout/reports/check-job-notifications-<date>-digest.txt` produced by an engine script (order and 7,500-char trim rule in §4), and the per-run scorecard with a **per-alert coverage table**. A page that claims results but yields zero parsed cards is a loud `extractor_mismatch` failure, never a quiet empty. |
| D12 | **Engine placement.** New scripts (§3) under `_ultra-engine`, contracts in its `SKILL.md`, tests in `tests/run.sh`. Reuse of `snapshot.sh`, `fingerprint.sh`, `validate_delta.py`, `merge_tracker.py`, `jd_queue.sh`, `checkpoint.sh`, `scorecard.sh`, `payload.sh`, `profile_hash.sh`. The command never re-implements a mechanical step in prose. |
| D13 | **Command rewritten from scratch**, lean, one script call per mechanical step, written for an unattended Sonnet-class main thread. Judgement steps name their subagent and its pinned model. |
| D14 | **Model split (plugin-shipped `agents/`):** `gate-batch` pinned `sonnet` (deal-breaker checks on JD text, batches of 5); `score-batch` pinned `opus` (rubric + evidence for ungated survivors only, batches of 5); `_visualizer` stays on the session model. The main thread runs on the session model — a Cowork setting, not a plugin setting. Subagents receive only their batch's card records + JD paths + profile hash. |
| D15 | **One-shot tracker migration** to the canonical schema (source → structured, `gated` → `seen`+`D`, gate violations → `{kind, detail}`, dates → `YYYY-MM-DD` for `first_seen`/`last_seen`, ad-hoc fields dropped, unknown `stats` keys kept), backup first, entry count asserted equal, run on both live workspaces. Tests on a fixture cut from the real tracker. |
| D16 | **Scheduled task rewritten** to a few lines: run the command in the workspace; create the calendar event from the digest file; print the headline lines. Gates are never restated. A `no_scrape` digest produces the short honest event. |
| D17 | **Deferred (named follow-on):** wiring the shared card extractor into `ultramode/references/linkedin-adapter.md` and `/job-search`. `/ultramode` remains the occasional all-sources sweep; LinkedIn alerts are the daily source. |
| D18 | **Release gate.** Spec → plan → TDD task-by-task → independent review → live acceptance (§6) → v0.17.0 with ROADMAP + CHANGELOG. |

## 3. Engine scripts (new)

All bash+jq or python3-stdlib, atomic writes, non-zero exit on violation, machine-readable stdout.

| Script | Call | Contract |
|---|---|---|
| `alerts_parse.py` | `python3 $SCRIPTS/alerts_parse.py < links.json` | Input: the JSON array the notifications page script returns (`[{href, age_text}]`). Output: deduped alert records `{alert_key, keywords, geo_id, since_epoch, since_iso, params, preview_ids[], qualifiers[]}` (`qualifiers` = workplace words found in keywords). Rejects hrefs without `alertAction=viewjobs`; dedupes the doubled anchors. |
| `cards_parse.py` | `python3 $SCRIPTS/cards_parse.py --surface alert\|toppicks\|saved < page.json` | Input: the page script's dump `{claimed_results, cards:[{id, text}], divider_index, has_next, page}`. Output: card records `{id, title, company, location, workplace, salary_text, posted_ago, viewed, promoted, easy_apply, before_divider}` + `{divider_seen, cards_before_divider, has_next}`. Exit 3 with `extractor_mismatch` when `claimed_results > 0` and zero cards parsed. |
| `walk_stop.py` | `python3 $SCRIPTS/walk_stop.py --alert <alert.json> --page <cards.json> --page-no N --valve 10` | Applies D5 deterministically: returns `{stop: true\|false, reason: divider\|drift\|valve\|no_next\|null, needs_model_check: bool, undecided_ids[]}`. `needs_model_check` is true only when the alert has no workplace qualifier and the term-overlap rule cannot decide; the command then asks the model the single yes/no question "does any of these titles match the alert intent?" and re-runs with `--model-says-match true\|false`. |
| `alerts_ledger.py` | `... load\|start\|page\|complete\|prune --ledger $WS/alerts.json …` | The D6 ledger: `load` prints alerts to walk given parsed alerts (skips `complete`, returns resume page for `partial`), `start`/`page`/`complete` write progress atomically, `prune` drops records older than 30 days. |
| `page_script.js` (reference asset) | shipped under `_ultra-engine/scripts/page/` — `notifications.js`, `results.js`, `toppicks.js`, `saved.js` | The exact in-page scripts the command runs verbatim through the adapter. Each returns one JSON string. No other page script may be improvised. Each scrolls its list to the bottom before reading and reads until the count stabilises. |
| `digest.py` | `python3 $SCRIPTS/digest.py --payload <payload.json> --scorecard <scorecard.json> --out <digest.txt>` | The D11 phone digest: run-status line; A/B/C one line each (title, company, rate or "rate not disclosed", location, bare URL; A first with key evidence); near-miss section; `FILTERED OUT (n)` numbered; queued-for-tomorrow; reposts count; gates in force; the styled-report pointer. Plain text, bare URLs, 7,500-char trim keeping the most relevant lines and ending with `…and N more — see the styled report`. |
| `migrate_tracker_v3.py` | `python3 $SCRIPTS/migrate_tracker_v3.py --tracker $WS/tracker.json [--dry-run]` | D15. Backup to `.backup/tracker.json.<UTC>.pre-phase17.json`; normalise; assert `len(jobs)` equal; write atomically; print a change summary by category. |
| `coverage.py` | folded into `scorecard.sh` via a new `alerts.json` stage file | Per-alert row: `alert_key, keywords, pages_walked, stop_reason, cards_seen, before_divider, known, reposts, new, jd_read, queued`. Totals line. A `no_scrape` run emits the reason instead of rows. |

Existing scripts reused unchanged: `snapshot.sh`, `fingerprint.sh`, `validate_delta.py`, `merge_tracker.py`, `jd_queue.sh`, `checkpoint.sh`, `scorecard.sh` (extended), `payload.sh` (extended for the notifications view), `profile_hash.sh`.

## 4. Schemas

### `alerts.json` (new, workspace)

```json
{
  "schema_version": 1,
  "alerts": {
    "<alert_key>": {
      "keywords": "linux engineer Contract Remote",
      "geo_id": "91000000",
      "since_epoch": 1788218797,
      "since": "2026-08-31T23:26:37Z",
      "params": "keywords=…&f_TPR=a1788218797-&geoId=91000000&origin=…",
      "first_seen": "2026-09-02",
      "status": "partial | complete",
      "last_page": 2,
      "stop_reason": "divider | drift | valve | no_next | null",
      "cards_seen": 49, "before_divider": 24, "known": 10, "reposts": 1, "new": 13,
      "run_id": "2026-09-02-0310"
    }
  }
}
```

`alert_key` = `sha1(keywords + "|" + geo_id + "|" + since_epoch)[:16]`.

### Card record (script output, never persisted as-is)

`{id, surface, title, company, location, workplace: remote|hybrid|onsite|unknown, salary_text|null, posted_ago|null, viewed, promoted, easy_apply, before_divider, alert_key|null}`.

### Tracker entry additions (additive, no `schema_version` bump)

`source` = `{lane: "linkedin", provider: "linkedin", board: "Job Alert" | "Top Picks" | "Saved" | "Similar"}`; `matched_query` = the alert keywords (attribution only); `alert_key`; `signals.remote` from the card's workplace (`unknown` when absent). The daily driver writes the structured `source` from now on (closes the ROADMAP's deferred item).

### Sweep envelope

The alert walk emits **one envelope per alert** (`stage: sweep-alert-<alert_key>`) plus one each for `sweep-toppicks`, `sweep-saved`, `sweep-linkedin-similar`, all validated by `validate_delta.py` and merged by `merge_tracker.py`. `counts` = `{scanned, before_divider, known, reposts, matched, returned, queued, capped}`; `deltas[]` carry bare numeric ids, card fields, `jd_path` (or null when queued), `source`, `fingerprint` via `fingerprint.sh`.

### Payload additions (`check-job-notifications` view)

`coverage[]` (the per-alert table), `queued[]`, `reposts[]` (collapsed), `run_status: fresh | no_scrape`, `no_scrape_reason|null`, `budget: {limit, used, queued}`.

## 5. The command (shape of the rewrite)

```
0  Preflight (scripts): workspace + profile present, else STOP(no_scrape). Pick browser surface (pane → extension), else STOP(no_scrape). checkpoint init. alerts_ledger prune. snapshot.
1  Drain queue: jd_queue pop ≤ budget → read JDs (card click + pane text) → envelope.
2  Notifications: navigate → run notifications.js (exhausts Load more) → alerts_parse → alerts_ledger load.
3  For each alert to walk: navigate params (+start) → results.js → cards_parse → dedupe (snapshot ids, fingerprint 45d) → walk_stop → ledger page → next page or complete.
4  For each new card (all alerts, then Top Picks, then Saved): budget check → click card → pane text → jds/<id>.txt → delta; over budget → jd_queue push.
5  validate_delta → merge_tracker (serial).
6  gate-batch subagents (sonnet, 5/batch) → score-batch subagents (opus, 5/batch, ungated only) → score cache → tracker field updates (atomic jq recipe).
7  Similar-jobs from A-tier (one round) → steps 4–6 for that envelope.
8  scorecard (with coverage) → payload → _visualizer → digest.py → checkpoint save.
9  Print: summary line, coverage totals, one line per A/B/C role with URL, "queued N", next-step commands.
```

Every step names its script call and the exact JSON it expects back. No step contains an "if the tool is unavailable, improvise" clause; unavailability is a disclosed stop.

## 6. Live acceptance (user-run, freelance workspace)

1. `tests/run.sh` → `ALL PASS` including fixtures cut from the 2026-09-02 pages and the tracker-migration fixture.
2. Migration on both workspaces: backup present, entry count unchanged, validators pass.
3. One nightly-equivalent run: the coverage table lists every alert on the page with a stop reason; for two alerts, a manual count of cards before the divider equals `before_divider`; `known + reposts + new = before_divider` per alert.
4. The before-number: on the `linux engineer Contract Remote` alert of 2026-08-31T23:26Z (or its successor), zero exact matches absent from the tracker after the run.
5. Digest file present, under 7,500 chars, bare URLs only; calendar event created from it by the rewritten task.
6. One deliberate no-browser run produces a `no_scrape` digest and no tracker writes.

## 7. Out of scope

Gmail application reconciliation (lives in the task prompt or a later phase); `/ultramode` and `/job-search` extractor wiring (D17); any change to the rubric, dimensions or score-cache key; LinkedIn "Applied/In Progress" tabs of the Job tracker page.

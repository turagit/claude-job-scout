# Phase 17 — The alert walk Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `/check-job-notifications` walk every LinkedIn job alert to its real end (the "We found more results…" divider), through scripted extraction with a per-alert coverage ledger, on the `_ultra-engine` spine, unattended, with a phone digest — so no exact-match role is silently skipped.

**Architecture:** In-page scripts (shipped verbatim) dump alerts and cards as JSON; python/bash engine scripts parse, decide stop rules, keep the alert ledger, build coverage/scorecard/payload/digest, and migrate the drifted live tracker. The command file becomes a thin sequencer of those scripts plus two pinned-model subagents (gate on Sonnet, score on Opus). Nothing mechanical lives in prose.

**Tech Stack:** bash 3.2 + jq, python3 stdlib, in-page JavaScript run through the built-in browser pane (primary) or the Chrome extension (fallback), Jinja2 templates rendered by `_visualizer`, unittest + bash test harness in `skills/_ultra-engine/tests/run.sh`.

**Spec:** `docs/superpowers/specs/2026-09-02-phase-17-alert-walk-design.md` (decisions D1–D18) and its evidence file `docs/superpowers/specs/2026-09-02-phase-17-alert-walk-linkedin-dom-evidence.md` (the only source of DOM anchors).

## Global Constraints

- British English in all user-facing copy (`skills/shared-references/voice-profile.md`); identifiers exempt.
- Every slash command keeps `disable-model-invocation: true`.
- Browser work: built-in browser pane first, Chrome extension fallback; nothing else. Voyager/internal endpoints forbidden (D2, D3).
- Mechanical operations are `_ultra-engine` script calls (CLAUDE.md hard rule 9). Scripts: bash 3.2-compatible or python3 stdlib only; atomic writes (`.tmp` + `mv`/`os.replace`); non-zero exit on violation; machine-readable stdout.
- Every new script lands with a test in the same commit; `bash skills/_ultra-engine/tests/run.sh` must print `ALL PASS` before every commit that touches `skills/_ultra-engine/`.
- DOM anchors used by page scripts are ONLY those listed in the evidence file §1–§4.
- Tracker enums: `status ∈ {seen, approved, applied, rejected, skipped}`, `tier ∈ {A,B,C,D,untiered}`, `rubric_version ∈ {legacy, v1}`, `source.board (linkedin) ∈ {Job Alert, Top Picks, Search, Inbox, Saved, Similar}`, `deal_breakers[].kind ∈ {work_arrangement, contract_type, seniority_floor, location, industry, company, rate_floor, salary_floor, custom}`.
- JD budget default 150 per run (`config.json` key `jd_budget_per_run`); fingerprint window 45 days; ledger prune 30 days; page valve 10.
- Plugin version bumps to `0.17.0` only in the release task. Work on branch `phase-17/build`. Commit messages: `Phase 17 Task N: <what>` + the `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>` trailer.
- Never commit a `.job-scout/` folder or any file from the live workspaces except sanitised fixtures written by hand in this plan.

---

## File map

| Path | Responsibility |
|---|---|
| `skills/_ultra-engine/scripts/page/notifications.js` | In-page script: exhaust "Load more", return every alert link + age text. |
| `skills/_ultra-engine/scripts/page/results.js` | In-page script: one alert results page → cards (id + innerText), divider index, pagination, claimed result count. |
| `skills/_ultra-engine/scripts/page/toppicks.js` | In-page script: Top Picks page 1 (old markup) → cards. |
| `skills/_ultra-engine/scripts/page/saved.js` | In-page script: Job-tracker Saved tab → cards or `saved_count: 0`. |
| `skills/_ultra-engine/scripts/alerts_parse.py` | notifications.js output → alert records (key, params, qualifiers, preview ids). |
| `skills/_ultra-engine/scripts/cards_parse.py` | results/toppicks/saved output → card records; `extractor_mismatch` loud failure. |
| `skills/_ultra-engine/scripts/walk_stop.py` | D5 stop rules for one page: divider / drift / valve / no_next / continue. |
| `skills/_ultra-engine/scripts/alerts_ledger.py` | `.job-scout/alerts.json`: plan / start / page / complete / prune. |
| `skills/_ultra-engine/scripts/coverage.py` | Ledger + run id → `coverage.json` (per-alert table + totals). |
| `skills/_ultra-engine/scripts/scorecard.sh` (modify) | Embed `coverage.json` when present. |
| `skills/_ultra-engine/scripts/payload_notifications.sh` | The `check-job-notifications` render payload (results, coverage, queued, reposts, budget, run_status). |
| `skills/_ultra-engine/scripts/digest.py` | Plain-text phone digest, 7,500-char trim, `no_scrape` variant. |
| `skills/_ultra-engine/scripts/migrate_tracker_v3.py` | One-shot canonicalisation of a drifted tracker (D15). |
| `skills/_ultra-engine/tests/test_*.{py,sh}` + `tests/fixtures/p17-*.json` | Tests and hand-written fixtures per script. |
| `agents/gate-batch.md`, `agents/score-batch.md` | Plugin-shipped subagents pinned to `sonnet` / `opus`. |
| `skills/check-job-notifications/SKILL.md` | Rewritten command (thin sequencer). |
| `skills/shared-references/browser-policy.md` | Two surfaces, ordered; internal endpoints forbidden. |
| `skills/shared-references/canonical-schemas.md`, `workspace-layout.md` | `alerts.json` schema, tracker additions, `jd_budget_per_run`. |
| `skills/_visualizer/templates/{html,markdown}/check-job-notifications.*.j2`, `skills/_visualizer/SKILL.md`, `skills/shared-references/render-orchestration.md` | Coverage table, queued, reposts, run-status banner; summary line. |
| `docs/scheduled-tasks/freelancer-daily-scan.md` | The rewritten Cowork task prompt. |
| `docs/ROADMAP.md`, `CHANGELOG.md`, `README.md`, `QUICKSTART.md`, `.claude-plugin/plugin.json` | Release. |

Shared interface used by every page script and parser — **the page dump**:

```json
{ "surface": "alert | toppicks | saved | notifications",
  "url": "<location.href>",
  "claimed_results": "99+ results" | null,
  "page": 1,
  "cards": [ { "id": "4460908564", "text": "<innerText of the outermost card element>" } ],
  "divider_index": 24 | null,
  "has_next": true,
  "saved_count": null | 0 }
```

Shared interface produced by `cards_parse.py` — **the card record**:

```json
{ "id": "4460908564", "surface": "alert", "title": "Platform Engineer (Remote)", "company": "Hire Feed",
  "location": "Germany (Remote)", "workplace": "remote", "salary_text": "$40/hr - $100/hr",
  "posted_ago": "5 hours ago", "viewed": false, "promoted": true, "easy_apply": false,
  "early_applicant": true, "before_divider": true }
```

---

### Task 0: Branch and baseline

**Files:** none changed.

- [ ] **Step 1: Create the branch from `main`**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout" && git checkout -b phase-17/build main
```

- [ ] **Step 2: Confirm the baseline suite passes**

Run: `bash skills/_ultra-engine/tests/run.sh | tail -1`
Expected: `ALL PASS`

---

### Task 1: `alerts_parse.py` — notifications dump → alert records

**Files:**
- Create: `skills/_ultra-engine/scripts/alerts_parse.py`
- Create: `skills/_ultra-engine/tests/fixtures/p17-notifications-dump.json`
- Test: `skills/_ultra-engine/tests/test_alerts_parse.py`

**Interfaces:**
- Consumes: the `notifications` page dump `{"surface":"notifications","alerts":[{"href":..,"age_text":..}],"load_more_clicks":n,"exhausted":bool}` (Task 5 produces it).
- Produces: stdout JSON `{"alerts":[AlertRecord], "dropped_duplicates": n}` where `AlertRecord = {alert_key, keywords, geo_id, since_epoch, since, params, results_url, preview_ids[], qualifiers[], age_text}`. `alert_key = sha1(f"{keywords}|{geo_id}|{since_epoch}").hexdigest()[:16]`. `params` is the original query string minus `currentJobId` and `originToLandingJobPostings`. `results_url = "https://www.linkedin.com/jobs/search-results/?" + params`. `qualifiers ⊆ {"remote","hybrid","onsite"}` derived from the keywords (case-insensitive: `remote`→remote, `hybrid`→hybrid, `on-site`/`onsite`/`on site`→onsite).

- [ ] **Step 1: Write the fixture**

`skills/_ultra-engine/tests/fixtures/p17-notifications-dump.json`:

```json
{"surface":"notifications","url":"https://www.linkedin.com/notifications/?filter=jobs_all","load_more_clicks":2,"exhausted":true,
 "alerts":[
  {"href":"https://www.linkedin.com/jobs/search-results/?keywords=linux+engineer+Contract+Remote&f_TPR=a1788218797-&geoId=91000000&origin=SEMANTIC_SEARCH_JOB_ALERT_IN_APP_NOTIFICATION&alertAction=viewjobs&currentJobId=4461737101&originToLandingJobPostings=4461737101,4461723921,4461789493,4461758173,4454761864,4461780431","age_text":"43m"},
  {"href":"https://www.linkedin.com/jobs/search-results/?keywords=linux+engineer+Contract+Remote&f_TPR=a1788218797-&geoId=91000000&origin=SEMANTIC_SEARCH_JOB_ALERT_IN_APP_NOTIFICATION&alertAction=viewjobs&currentJobId=4461737101&originToLandingJobPostings=4461737101,4461723921,4461789493,4461758173,4454761864,4461780431","age_text":"43m"},
  {"href":"https://www.linkedin.com/jobs/search-results/?keywords=linux+security+engineer&f_TPR=a1788197083-&f_SAL=f_SA_id_226001%3A274001&geoId=91000000&origin=SEMANTIC_SEARCH_JOB_ALERT_IN_APP_NOTIFICATION&alertAction=viewjobs&currentJobId=4461781661&originToLandingJobPostings=4461781661","age_text":"13h"},
  {"href":"https://www.linkedin.com/jobs/search-results/?keywords=linux+engineer+Contract+Remote&f_TPR=a1788136516-&geoId=91000000&origin=SEMANTIC_SEARCH_JOB_ALERT_IN_APP_NOTIFICATION&alertAction=viewjobs&currentJobId=4459287833&originToLandingJobPostings=4459287833,4459521700,4461741721,4461743064","age_text":"1d"},
  {"href":"https://www.linkedin.com/feed/","age_text":""}
 ]}
```

- [ ] **Step 2: Write the failing test**

`skills/_ultra-engine/tests/test_alerts_parse.py`:

```python
import json, os, subprocess, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "scripts", "alerts_parse.py")
FIX = os.path.join(HERE, "fixtures", "p17-notifications-dump.json")

def run(payload):
    return subprocess.run(["python3", SCRIPT], input=json.dumps(payload), capture_output=True, text=True)

class T(unittest.TestCase):
    def setUp(self):
        self.dump = json.load(open(FIX))
        p = run(self.dump); self.assertEqual(p.returncode, 0, p.stderr)
        self.out = json.loads(p.stdout)

    def test_dedupes_doubled_anchor_and_drops_non_alert(self):
        self.assertEqual(len(self.out["alerts"]), 3)
        self.assertEqual(self.out["dropped_duplicates"], 1)

    def test_same_keywords_newer_epoch_is_a_distinct_alert(self):
        keys = {a["alert_key"] for a in self.out["alerts"] if a["keywords"] == "linux engineer Contract Remote"}
        self.assertEqual(len(keys), 2)

    def test_fields(self):
        a = self.out["alerts"][0]
        self.assertEqual(a["keywords"], "linux engineer Contract Remote")
        self.assertEqual(a["geo_id"], "91000000")
        self.assertEqual(a["since_epoch"], 1788218797)
        self.assertEqual(a["since"], "2026-08-31T23:26:37Z")
        self.assertEqual(a["preview_ids"], ["4461737101","4461723921","4461789493","4461758173","4454761864","4461780431"])
        self.assertEqual(a["qualifiers"], ["remote"])
        self.assertEqual(len(a["alert_key"]), 16)
        self.assertNotIn("currentJobId", a["params"]); self.assertNotIn("originToLandingJobPostings", a["params"])
        self.assertIn("alertAction=viewjobs", a["params"])
        self.assertTrue(a["results_url"].startswith("https://www.linkedin.com/jobs/search-results/?"))

    def test_salary_param_kept_and_no_qualifier(self):
        a = [x for x in self.out["alerts"] if x["keywords"] == "linux security engineer"][0]
        self.assertIn("f_SAL=", a["params"]); self.assertEqual(a["qualifiers"], [])

    def test_deterministic_key(self):
        again = json.loads(run(self.dump).stdout)
        self.assertEqual([a["alert_key"] for a in again["alerts"]], [a["alert_key"] for a in self.out["alerts"]])

    def test_bad_input_is_clean_error(self):
        p = run({"surface": "notifications"})
        self.assertEqual(p.returncode, 1); self.assertNotIn("Traceback", p.stderr)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `cd skills/_ultra-engine/tests && python3 -m unittest test_alerts_parse -v`
Expected: FAIL (script missing → returncode 2 / FileNotFoundError assertions fail).

- [ ] **Step 4: Write the script**

`skills/_ultra-engine/scripts/alerts_parse.py`:

```python
#!/usr/bin/env python3
"""notifications.js dump -> alert records. stdlib only. Usage: alerts_parse.py < dump.json
Exit 0 with {"alerts": [...], "dropped_duplicates": n}; exit 1 with one stderr line on bad input."""
import hashlib, json, re, sys
from datetime import datetime, timezone
from urllib.parse import urlsplit, parse_qsl, urlencode

DROP = {"currentJobId", "originToLandingJobPostings"}
BASE = "https://www.linkedin.com/jobs/search-results/?"

def qualifiers(keywords):
    k = keywords.lower(); q = []
    if re.search(r"\bremote\b", k): q.append("remote")
    if re.search(r"\bhybrid\b", k): q.append("hybrid")
    if re.search(r"\bon[- ]?site\b", k): q.append("onsite")
    return q

def parse_one(href, age_text):
    u = urlsplit(href)
    pairs = parse_qsl(u.query, keep_blank_values=True)
    q = dict(pairs)
    if q.get("alertAction") != "viewjobs" or "keywords" not in q or "f_TPR" not in q:
        return None
    m = re.match(r"^a(\d+)-?$", q["f_TPR"])
    if not m:
        return None
    epoch = int(m.group(1))
    keywords = q["keywords"]; geo = q.get("geoId", "")
    params = urlencode([(k, v) for k, v in pairs if k not in DROP])
    preview = [i for i in q.get("originToLandingJobPostings", "").split(",") if i]
    return {
        "alert_key": hashlib.sha1(f"{keywords}|{geo}|{epoch}".encode()).hexdigest()[:16],
        "keywords": keywords, "geo_id": geo, "since_epoch": epoch,
        "since": datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "params": params, "results_url": BASE + params,
        "preview_ids": preview, "qualifiers": qualifiers(keywords), "age_text": age_text or "",
    }

def main():
    try:
        dump = json.load(sys.stdin)
        links = dump["alerts"]
        assert isinstance(links, list)
    except Exception as e:
        print(f"alerts_parse: bad input ({e})", file=sys.stderr); sys.exit(1)
    seen, out, dups = set(), [], 0
    for item in links:
        rec = parse_one(str(item.get("href", "")), item.get("age_text"))
        if rec is None:
            continue
        if rec["alert_key"] in seen:
            dups += 1; continue
        seen.add(rec["alert_key"]); out.append(rec)
    print(json.dumps({"alerts": out, "dropped_duplicates": dups}, ensure_ascii=False))

if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `cd skills/_ultra-engine/tests && python3 -m unittest test_alerts_parse -v`
Expected: 6 tests OK.

- [ ] **Step 6: Run the whole suite, then commit**

```bash
bash skills/_ultra-engine/tests/run.sh | tail -1   # ALL PASS
git add skills/_ultra-engine/scripts/alerts_parse.py skills/_ultra-engine/tests/test_alerts_parse.py skills/_ultra-engine/tests/fixtures/p17-notifications-dump.json
git commit -m "Phase 17 Task 1: alerts_parse.py — alert records from the notifications dump

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---
### Task 2: `cards_parse.py` — page dump → card records, with the loud `extractor_mismatch`

**Files:**
- Create: `skills/_ultra-engine/scripts/cards_parse.py`
- Create: `skills/_ultra-engine/tests/fixtures/p17-results-page1.json`, `p17-results-page2.json`, `p17-results-drift.json`, `p17-toppicks-page1.json`, `p17-saved-empty.json`, `p17-results-mismatch.json`
- Test: `skills/_ultra-engine/tests/test_cards_parse.py`

**Interfaces:**
- Consumes: a page dump (File map § shared interface) on stdin; `--surface alert|toppicks|saved`.
- Produces: stdout JSON `{"surface", "page", "claimed_results", "cards": [CardRecord], "divider_seen": bool, "cards_before_divider": int, "has_next": bool, "note": null|"saved_empty"}`. Exit 3 + stderr `extractor_mismatch: page claims <n> results, parsed 0 cards` when `claimed_results` parses to a number > 0 and no cards were parsed. Exit 1 on malformed input. Card `id` must match `^\d{6,}$`; others are dropped and counted in `dropped_bad_id`.

- [ ] **Step 1: Write the fixtures**

`p17-results-page1.json` (five cards; index 4 sits after the divider):

```json
{"surface":"alert","url":"https://www.linkedin.com/jobs/search-results/?currentJobId=4461737101&keywords=linux%20engineer%20Contract%20Remote&geoId=91000000&f_TPR=a1788218797-","claimed_results":"99+ results","page":1,"divider_index":4,"has_next":true,"saved_count":null,
 "cards":[
  {"id":"4461737101","text":"Selected, Platform Engineer (Remote)\nPlatform Engineer (Remote)\n\nHire Feed\n\nFrance (Remote)\n\n$40/hr - $100/hr\n\nViewed\n\n · \n\nBe an early applicant\n\n · \n\nPosted 19 hours ago\n19 hours ago"},
  {"id":"4460927420","text":"DevOps Engineer (Infrastructure)\nDevOps Engineer (Infrastructure)\n\nHire Feed\n\nGermany (Remote)\n\n$20/hr - $70/hr\n\nBe an early applicant\n\n · \n\nPosted 4 hours ago\n4 hours ago\n\n · \n\nPromoted"},
  {"id":"4459517621","text":"Staff Engineer - DevOps (Verified job)\nStaff Engineer - DevOps \n\nHard Rock Digital\n\nGdańsk (Remote)\n\nBe an early applicant\n\n · \n\nPosted 16 hours ago\n16 hours ago"},
  {"id":"4460933633","text":"DevOps Engineer \n\nNLB Services\n\nDublin (Hybrid)\n\nBe an early applicant\n\n · \n\nPosted 16 hours ago\n16 hours ago\n\n · \n\nEasy Apply\n\n · \n\nPromoted"},
  {"id":"4461709378","text":"Freelancer (Senior) DevOps Engineer (m/w/d)\nFreelancer (Senior) DevOps Engineer (m/w/d)\n\niVentureGroup\n\nHamburg, Germany (Hybrid)\n\nBe an early applicant\n\n · \n\nPosted 21 hours ago\n21 hours ago\n\n · \n\nPromoted"}
 ]}
```

`p17-results-page2.json`:

```json
{"surface":"alert","url":"https://www.linkedin.com/jobs/search-results/?keywords=linux%20engineer%20Contract%20Remote&start=25&geoId=91000000&f_TPR=a1788218797-","claimed_results":"99+ results","page":2,"divider_index":null,"has_next":true,"saved_count":null,
 "cards":[
  {"id":"4461569949","text":"Infrastructure Engineer (m/w/d)\nInfrastructure Engineer (m/w/d)\n\nComputer Futures\n\nMunich (Remote)\n\nBe an early applicant\n\n · \n\nPosted 6 hours ago\n6 hours ago"},
  {"id":"4460622080","text":"Linux Expert\n\nEngenious\n\nPoland (Remote)\n\nActively reviewing applicants\n\nBe an early applicant\n\n · \n\nPosted 18 hours ago\n18 hours ago\n\n · \n\nEasy Apply"},
  {"id":"4459287833","text":"System Engineer \n\nTenth Revolution Group\n\nMilan (Hybrid)\n\n5,000 EUR/month - 6,000 EUR/month\n\nActively reviewing applicants\n\n · \n\nPosted 18 hours ago\n18 hours ago"}
 ]}
```

`p17-results-drift.json` (no divider, nothing remote):

```json
{"surface":"alert","url":"https://www.linkedin.com/jobs/search-results/?keywords=linux%20engineer%20Contract%20Remote&start=50","claimed_results":"99+ results","page":3,"divider_index":null,"has_next":true,"saved_count":null,
 "cards":[
  {"id":"4461782151","text":"Unix System Administrator \n\nHays\n\nMadrid (Hybrid)\n\nBe an early applicant\n\n · \n\nPosted 11 hours ago\n11 hours ago"},
  {"id":"4267795780","text":"Administrateur Système CDD (H/F) \n\nClaranet France\n\nIlle-et-Vilaine (Hybrid)\n\nBe an early applicant\n\n · \n\nPosted 21 hours ago\n21 hours ago"},
  {"id":"4462017910","text":"ingénieur informatique Systèmes & Réseaux (h/f) / Freelance\n\nFree-Work\n\nNancy (On-site)\n\n350 EUR/day - 500 EUR/day\n\nBe an early applicant\n\n · \n\nPosted 4 hours ago\n4 hours ago"}
 ]}
```

`p17-toppicks-page1.json`:

```json
{"surface":"toppicks","url":"https://www.linkedin.com/jobs/collections/recommended/","claimed_results":null,"page":1,"divider_index":null,"has_next":true,"saved_count":null,
 "cards":[
  {"id":"4428875133","text":"DevOps Specialist\nNewton Energy Solutions\nDelft, South Holland, Netherlands (On-site)\nViewed\nPromoted"},
  {"id":"4401921503","text":"Cloud-architect (Azure)\nIT Infra Talents\nThe Randstad, Netherlands\n2 days ago\nEasy Apply"},
  {"id":"not-an-id","text":"junk"}
 ]}
```

`p17-saved-empty.json`:

```json
{"surface":"saved","url":"https://www.linkedin.com/jobs-tracker/","claimed_results":null,"page":1,"divider_index":null,"has_next":false,"saved_count":0,"cards":[]}
```

`p17-results-mismatch.json`:

```json
{"surface":"alert","url":"https://www.linkedin.com/jobs/search-results/?keywords=x","claimed_results":"42 results","page":1,"divider_index":null,"has_next":false,"saved_count":null,"cards":[]}
```

- [ ] **Step 2: Write the failing test**

`skills/_ultra-engine/tests/test_cards_parse.py`:

```python
import json, os, subprocess, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "scripts", "cards_parse.py")
def fix(n): return json.load(open(os.path.join(HERE, "fixtures", n)))
def run(payload, surface):
    return subprocess.run(["python3", SCRIPT, "--surface", surface], input=json.dumps(payload), capture_output=True, text=True)

class T(unittest.TestCase):
    def test_page1_records(self):
        p = run(fix("p17-results-page1.json"), "alert"); self.assertEqual(p.returncode, 0, p.stderr)
        o = json.loads(p.stdout)
        self.assertTrue(o["divider_seen"]); self.assertEqual(o["cards_before_divider"], 4); self.assertTrue(o["has_next"])
        c = {x["id"]: x for x in o["cards"]}
        self.assertEqual(len(c), 5)
        a = c["4461737101"]
        self.assertEqual(a["title"], "Platform Engineer (Remote)"); self.assertEqual(a["company"], "Hire Feed")
        self.assertEqual(a["location"], "France (Remote)"); self.assertEqual(a["workplace"], "remote")
        self.assertEqual(a["salary_text"], "$40/hr - $100/hr"); self.assertEqual(a["posted_ago"], "19 hours ago")
        self.assertTrue(a["viewed"]); self.assertFalse(a["promoted"]); self.assertTrue(a["before_divider"])
        v = c["4459517621"]
        self.assertEqual(v["title"], "Staff Engineer - DevOps"); self.assertEqual(v["company"], "Hard Rock Digital")
        h = c["4460933633"]
        self.assertEqual(h["workplace"], "hybrid"); self.assertTrue(h["easy_apply"]); self.assertTrue(h["promoted"]); self.assertIsNone(h["salary_text"])
        self.assertFalse(c["4461709378"]["before_divider"])

    def test_page2_no_divider(self):
        o = json.loads(run(fix("p17-results-page2.json"), "alert").stdout)
        self.assertFalse(o["divider_seen"]); self.assertEqual(o["cards_before_divider"], 3)
        self.assertEqual(o["cards"][2]["salary_text"], "5,000 EUR/month - 6,000 EUR/month")
        self.assertTrue(all(x["before_divider"] for x in o["cards"]))

    def test_toppicks_old_markup_and_bad_id_dropped(self):
        o = json.loads(run(fix("p17-toppicks-page1.json"), "toppicks").stdout)
        self.assertEqual([x["id"] for x in o["cards"]], ["4428875133", "4401921503"])
        self.assertEqual(o["dropped_bad_id"], 1)
        self.assertEqual(o["cards"][0]["workplace"], "onsite"); self.assertTrue(o["cards"][0]["viewed"])
        self.assertEqual(o["cards"][1]["workplace"], "unknown"); self.assertEqual(o["cards"][1]["posted_ago"], "2 days ago")

    def test_saved_empty_is_ok_with_note(self):
        p = run(fix("p17-saved-empty.json"), "saved"); self.assertEqual(p.returncode, 0)
        o = json.loads(p.stdout); self.assertEqual(o["cards"], []); self.assertEqual(o["note"], "saved_empty")

    def test_mismatch_is_loud(self):
        p = run(fix("p17-results-mismatch.json"), "alert")
        self.assertEqual(p.returncode, 3); self.assertIn("extractor_mismatch", p.stderr)

    def test_bad_input(self):
        p = subprocess.run(["python3", SCRIPT, "--surface", "alert"], input="{", capture_output=True, text=True)
        self.assertEqual(p.returncode, 1); self.assertNotIn("Traceback", p.stderr)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `cd skills/_ultra-engine/tests && python3 -m unittest test_cards_parse -v`
Expected: FAIL (script missing).

- [ ] **Step 4: Write the script**

`skills/_ultra-engine/scripts/cards_parse.py`:

```python
#!/usr/bin/env python3
"""Page dump -> card records. stdlib only.
Usage: cards_parse.py --surface alert|toppicks|saved < dump.json
Exit 0: {"surface","page","claimed_results","cards":[...],"divider_seen","cards_before_divider","has_next","note","dropped_bad_id"}
Exit 3: extractor_mismatch (page claims results, zero cards parsed). Exit 1: bad input."""
import argparse, json, re, sys

ID_RE = re.compile(r"^\d{6,}$")
SAL_RE = re.compile(r"(\$|€|£|\bEUR\b|\bUSD\b|\bGBP\b|\bCHF\b|\bPLN\b).*(/hr|/hour|/day|/month|/yr|/year)|(/hr|/day|/month)\b", re.I)
POSTED_RE = re.compile(r"^Posted\s+(.+)$", re.I)
AGO_RE = re.compile(r"^\d+\s+(second|minute|hour|day|week|month)s?\s+ago$", re.I)
FLAGS = {"viewed": "Viewed", "promoted": "Promoted", "easy_apply": "Easy Apply",
         "early_applicant": "Be an early applicant", "reviewing": "Actively reviewing applicants"}
NOISE = {"·", "Verified job"}

def workplace(location):
    m = re.search(r"\((Remote|Hybrid|On-site)\)\s*$", location or "", re.I)
    if not m: return "unknown"
    return {"remote": "remote", "hybrid": "hybrid", "on-site": "onsite"}[m.group(1).lower()]

def parse_text(text):
    lines = [l.strip() for l in (text or "").split("\n")]
    lines = [l for l in lines if l and l not in NOISE]
    if not lines: return None
    title = lines[0]
    if title.startswith("Selected, "): title = title[len("Selected, "):]
    title = re.sub(r"\s*\(Verified job\)\s*$", "", title).strip()
    rest = lines[1:]
    if rest and re.sub(r"\s*\(Verified job\)\s*$", "", rest[0]).strip() == title: rest = rest[1:]  # aria twin
    rec = {"title": title, "company": None, "location": None, "workplace": "unknown", "salary_text": None,
           "posted_ago": None, "viewed": False, "promoted": False, "easy_apply": False, "early_applicant": False}
    body = []
    for l in rest:
        hit = False
        for k, label in FLAGS.items():
            if l == label:
                if k != "reviewing": rec[k] = True
                hit = True; break
        if hit: continue
        m = POSTED_RE.match(l)
        if m: rec["posted_ago"] = m.group(1).strip(); continue
        if AGO_RE.match(l):
            if rec["posted_ago"] is None: rec["posted_ago"] = l
            continue
        if SAL_RE.search(l) and rec["salary_text"] is None: rec["salary_text"] = l; continue
        body.append(l)
    if body: rec["company"] = body[0]
    if len(body) > 1: rec["location"] = body[1]
    rec["workplace"] = workplace(rec["location"])
    return rec

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--surface", required=True, choices=["alert", "toppicks", "saved"])
    a = ap.parse_args()
    try:
        dump = json.load(sys.stdin); cards_in = dump.get("cards"); assert isinstance(cards_in, list)
    except Exception as e:
        print(f"cards_parse: bad input ({e})", file=sys.stderr); sys.exit(1)
    div = dump.get("divider_index"); divider_seen = isinstance(div, int)
    out, bad, seen = [], 0, set()
    for i, c in enumerate(cards_in):
        cid = str(c.get("id", ""))
        if not ID_RE.match(cid): bad += 1; continue
        if cid in seen: continue
        rec = parse_text(c.get("text", ""))
        if rec is None: bad += 1; continue
        seen.add(cid)
        rec.update({"id": cid, "surface": a.surface, "before_divider": (not divider_seen) or i < div})
        out.append(rec)
    claimed = dump.get("claimed_results"); claimed_n = 0
    if isinstance(claimed, str):
        m = re.match(r"^\s*([\d,]+)", claimed); claimed_n = int(m.group(1).replace(",", "")) if m else 0
    note = None
    if a.surface == "saved" and not out and (dump.get("saved_count") == 0): note = "saved_empty"
    if not out and claimed_n > 0:
        print(f"extractor_mismatch: page claims {claimed_n} results, parsed 0 cards ({dump.get('url','')})", file=sys.stderr); sys.exit(3)
    print(json.dumps({"surface": a.surface, "page": dump.get("page", 1), "claimed_results": claimed, "cards": out,
                      "divider_seen": divider_seen, "cards_before_divider": sum(1 for r in out if r["before_divider"]),
                      "has_next": bool(dump.get("has_next")), "note": note, "dropped_bad_id": bad}, ensure_ascii=False))

if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `cd skills/_ultra-engine/tests && python3 -m unittest test_cards_parse -v`
Expected: 6 tests OK. If `test_page1_records` fails on `posted_ago`, check the aria twin handling: the `Posted N hours ago` line must win over the bare `N hours ago` line.

- [ ] **Step 6: Suite + commit**

```bash
bash skills/_ultra-engine/tests/run.sh | tail -1   # ALL PASS
git add skills/_ultra-engine/scripts/cards_parse.py skills/_ultra-engine/tests/test_cards_parse.py skills/_ultra-engine/tests/fixtures/p17-*.json
git commit -m "Phase 17 Task 2: cards_parse.py — card records from page dumps, loud extractor_mismatch

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---
### Task 3: `walk_stop.py` — the D5 stop rules for one page

**Files:**
- Create: `skills/_ultra-engine/scripts/walk_stop.py`
- Test: `skills/_ultra-engine/tests/test_walk_stop.py` (reuses Task 2 fixtures through `cards_parse.py`)

**Interfaces:**
- Consumes: `--alert <alert.json>` (one AlertRecord from Task 1), `--page <parsed.json>` (Task 2 output), `--page-no N`, `--valve 10`, optional `--model-says-match true|false`.
- Produces: stdout JSON `{"stop": bool, "reason": "divider"|"drift"|"valve"|"no_next"|null, "needs_model_check": bool, "undecided_ids": [..], "matched_ids": [..]}`. Rule order: divider → valve → no_next → drift. Drift with qualifiers: no card whose `workplace` is in the alert's qualifiers ⇒ drift. Drift without qualifiers: meaningful keyword terms (≥3 chars, not in the stop list `{and, or, not, the, contract, remote, hybrid, onsite, on-site, freelance, job, jobs}`) matched as prefixes against card titles (so `engineer` matches `engineering`); zero title matches ⇒ `needs_model_check: true` with every id undecided unless `--model-says-match` was given, in which case `true` ⇒ continue, `false` ⇒ drift. Never stops mid-page.

- [ ] **Step 1: Write the failing test**

`skills/_ultra-engine/tests/test_walk_stop.py`:

```python
import json, os, subprocess, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.join(HERE, "..", "scripts")
def parsed(fixture):
    d = json.load(open(os.path.join(HERE, "fixtures", fixture)))
    p = subprocess.run(["python3", os.path.join(S, "cards_parse.py"), "--surface", "alert"], input=json.dumps(d), capture_output=True, text=True)
    return json.loads(p.stdout)
def tmpjson(obj):
    f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False); json.dump(obj, f); f.close(); return f.name
def stop(alert, page, page_no, extra=()):
    p = subprocess.run(["python3", os.path.join(S, "walk_stop.py"), "--alert", tmpjson(alert), "--page", tmpjson(page),
                        "--page-no", str(page_no), "--valve", "10", *extra], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    return json.loads(p.stdout)
REMOTE = {"alert_key": "k1", "keywords": "linux engineer Contract Remote", "qualifiers": ["remote"]}
NOQUAL = {"alert_key": "k2", "keywords": "ipa kerberos", "qualifiers": []}

class T(unittest.TestCase):
    def test_divider_stops(self):
        r = stop(REMOTE, parsed("p17-results-page1.json"), 1)
        self.assertEqual((r["stop"], r["reason"]), (True, "divider"))
    def test_no_divider_remote_present_continues(self):
        r = stop(REMOTE, parsed("p17-results-page2.json"), 2)
        self.assertEqual((r["stop"], r["reason"]), (False, None)); self.assertFalse(r["needs_model_check"])
    def test_whole_page_without_qualifier_is_drift(self):
        r = stop(REMOTE, parsed("p17-results-drift.json"), 3)
        self.assertEqual((r["stop"], r["reason"]), (True, "drift"))
    def test_valve(self):
        r = stop(REMOTE, parsed("p17-results-page2.json"), 10)
        self.assertEqual((r["stop"], r["reason"]), (True, "valve"))
    def test_no_next(self):
        pg = parsed("p17-results-page2.json"); pg["has_next"] = False
        r = stop(REMOTE, pg, 2); self.assertEqual((r["stop"], r["reason"]), (True, "no_next"))
    def test_no_qualifier_term_overlap_continues(self):
        alert = {"alert_key": "k3", "keywords": "devops engineer", "qualifiers": []}
        r = stop(alert, parsed("p17-results-page2.json"), 2)  # "Infrastructure Engineer" matches 'engineer'
        self.assertFalse(r["stop"]); self.assertFalse(r["needs_model_check"]); self.assertIn("4461569949", r["matched_ids"])
    def test_no_qualifier_no_overlap_asks_model(self):
        r = stop(NOQUAL, parsed("p17-results-drift.json"), 3)
        self.assertFalse(r["stop"]); self.assertTrue(r["needs_model_check"]); self.assertEqual(len(r["undecided_ids"]), 3)
    def test_model_verdicts(self):
        self.assertFalse(stop(NOQUAL, parsed("p17-results-drift.json"), 3, ("--model-says-match", "true"))["stop"])
        r = stop(NOQUAL, parsed("p17-results-drift.json"), 3, ("--model-says-match", "false"))
        self.assertEqual((r["stop"], r["reason"]), (True, "drift"))
    def test_divider_beats_everything(self):
        pg = parsed("p17-results-page1.json"); pg["has_next"] = False
        self.assertEqual(stop(REMOTE, pg, 10)["reason"], "divider")

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd skills/_ultra-engine/tests && python3 -m unittest test_walk_stop -v`
Expected: FAIL (script missing).

- [ ] **Step 3: Write the script**

`skills/_ultra-engine/scripts/walk_stop.py`:

```python
#!/usr/bin/env python3
"""D5 stop rules for one alert results page. stdlib only.
Usage: walk_stop.py --alert alert.json --page parsed.json --page-no N [--valve 10] [--model-says-match true|false]
Order: divider -> valve -> no_next -> drift. Never mid-page."""
import argparse, json, re, sys

STOP = {"and", "or", "not", "the", "contract", "remote", "hybrid", "onsite", "on-site", "freelance", "job", "jobs"}

def terms(keywords):
    return [t for t in re.findall(r"[a-z0-9][a-z0-9+#.-]{2,}", keywords.lower()) if t not in STOP]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--alert", required=True); ap.add_argument("--page", required=True)
    ap.add_argument("--page-no", type=int, required=True); ap.add_argument("--valve", type=int, default=10)
    ap.add_argument("--model-says-match", choices=["true", "false"])
    a = ap.parse_args()
    try:
        alert = json.load(open(a.alert)); page = json.load(open(a.page)); cards = page["cards"]
    except Exception as e:
        print(f"walk_stop: bad input ({e})", file=sys.stderr); sys.exit(1)
    out = {"stop": False, "reason": None, "needs_model_check": False, "undecided_ids": [], "matched_ids": []}
    def done(reason): out.update({"stop": True, "reason": reason}); print(json.dumps(out)); sys.exit(0)
    if page.get("divider_seen"): done("divider")
    if a.page_no >= a.valve: done("valve")
    if not page.get("has_next"): done("no_next")
    quals = set(alert.get("qualifiers") or [])
    if quals:
        out["matched_ids"] = [c["id"] for c in cards if c.get("workplace") in quals]
        if not out["matched_ids"]: done("drift")
        print(json.dumps(out)); return
    ts = terms(alert.get("keywords", ""))
    for c in cards:
        title = (c.get("title") or "").lower()
        if any(re.search(r"\b" + re.escape(t), title) for t in ts): out["matched_ids"].append(c["id"])
    if out["matched_ids"]:
        print(json.dumps(out)); return
    if a.model_says_match == "true":
        print(json.dumps(out)); return
    if a.model_says_match == "false": done("drift")
    out["needs_model_check"] = True; out["undecided_ids"] = [c["id"] for c in cards]
    print(json.dumps(out))

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd skills/_ultra-engine/tests && python3 -m unittest test_walk_stop -v`
Expected: 9 tests OK.

- [ ] **Step 5: Suite + commit**

```bash
bash skills/_ultra-engine/tests/run.sh | tail -1   # ALL PASS
git add skills/_ultra-engine/scripts/walk_stop.py skills/_ultra-engine/tests/test_walk_stop.py
git commit -m "Phase 17 Task 3: walk_stop.py — divider / drift / valve / no_next stop rules

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---
### Task 4: `alerts_ledger.py` — the alert ledger (`.job-scout/alerts.json`)

**Files:**
- Create: `skills/_ultra-engine/scripts/alerts_ledger.py`
- Test: `skills/_ultra-engine/tests/test_alerts_ledger.py`

**Interfaces:**
- Consumes: AlertRecords from Task 1 (`--alerts parsed.json` is the full `alerts_parse.py` output).
- Produces / commands (all write atomically, all print JSON):
  - `plan --ledger L --alerts A --today YYYY-MM-DD` → `{"walk":[{"alert_key","resume_page","status":"new"|"partial"}], "skipped_complete": n}` (read-only).
  - `start --ledger L --alert-json <one AlertRecord file> --today D --run-id R` → upserts a `partial` record (no-op on an existing record except `run_id` update); prints the record.
  - `page --ledger L --key K --page N --cards-seen n --before-divider n --known n --reposts n --new n` → adds the counts, sets `last_page = N`; prints the record.
  - `complete --ledger L --key K --reason divider|drift|valve|no_next` → `status: complete`, `stop_reason`; prints the record.
  - `prune --ledger L --today D [--days 30]` → drops records whose `first_seen` is older than `days`; prints `{"pruned": n, "kept": n}`.
- Ledger file shape: `{"schema_version": 1, "alerts": {<alert_key>: {keywords, geo_id, since_epoch, since, params, first_seen, status, last_page, stop_reason, cards_seen, before_divider, known, reposts, new, run_id}}}`. A missing file is an empty ledger.

- [ ] **Step 1: Write the failing test**

`skills/_ultra-engine/tests/test_alerts_ledger.py`:

```python
import json, os, subprocess, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.join(HERE, "..", "scripts")
def sh(*args):
    p = subprocess.run(["python3", os.path.join(S, "alerts_ledger.py"), *map(str, args)], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    return json.loads(p.stdout)
def tmpjson(obj):
    f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False); json.dump(obj, f); f.close(); return f.name
A1 = {"alert_key": "aaaa000000000001", "keywords": "linux engineer Contract Remote", "geo_id": "91000000", "since_epoch": 1788218797,
      "since": "2026-08-31T23:26:37Z", "params": "keywords=linux+engineer&f_TPR=a1788218797-", "results_url": "https://x/?a", "preview_ids": [], "qualifiers": ["remote"], "age_text": "43m"}
A2 = dict(A1, alert_key="aaaa000000000002", keywords="ipa kerberos", qualifiers=[], since_epoch=1788171457)

class T(unittest.TestCase):
    def setUp(self):
        self.L = os.path.join(tempfile.mkdtemp(), "alerts.json")
        self.parsed = tmpjson({"alerts": [A1, A2], "dropped_duplicates": 0})
    def test_plan_on_missing_ledger_walks_everything_from_page_1(self):
        r = sh("plan", "--ledger", self.L, "--alerts", self.parsed, "--today", "2026-09-02")
        self.assertEqual([(w["alert_key"], w["resume_page"], w["status"]) for w in r["walk"]],
                         [("aaaa000000000001", 1, "new"), ("aaaa000000000002", 1, "new")])
        self.assertFalse(os.path.exists(self.L))  # plan is read-only
    def test_start_page_complete_lifecycle(self):
        rec = sh("start", "--ledger", self.L, "--alert-json", tmpjson(A1), "--today", "2026-09-02", "--run-id", "2026-09-02-0310")
        self.assertEqual((rec["status"], rec["last_page"], rec["first_seen"]), ("partial", 0, "2026-09-02"))
        rec = sh("page", "--ledger", self.L, "--key", A1["alert_key"], "--page", 1, "--cards-seen", 25, "--before-divider", 24, "--known", 10, "--reposts", 1, "--new", 13)
        rec = sh("page", "--ledger", self.L, "--key", A1["alert_key"], "--page", 2, "--cards-seen", 25, "--before-divider", 25, "--known", 20, "--reposts", 0, "--new", 5)
        self.assertEqual((rec["last_page"], rec["cards_seen"], rec["known"], rec["new"]), (2, 50, 30, 18))
        r = sh("plan", "--ledger", self.L, "--alerts", self.parsed, "--today", "2026-09-02")
        self.assertEqual([(w["alert_key"], w["resume_page"], w["status"]) for w in r["walk"]][0], (A1["alert_key"], 3, "partial"))
        rec = sh("complete", "--ledger", self.L, "--key", A1["alert_key"], "--reason", "divider")
        self.assertEqual((rec["status"], rec["stop_reason"]), ("complete", "divider"))
        r = sh("plan", "--ledger", self.L, "--alerts", self.parsed, "--today", "2026-09-02")
        self.assertEqual([w["alert_key"] for w in r["walk"]], [A2["alert_key"]]); self.assertEqual(r["skipped_complete"], 1)
    def test_start_is_idempotent(self):
        sh("start", "--ledger", self.L, "--alert-json", tmpjson(A1), "--today", "2026-09-02", "--run-id", "r1")
        sh("page", "--ledger", self.L, "--key", A1["alert_key"], "--page", 1, "--cards-seen", 5, "--before-divider", 5, "--known", 1, "--reposts", 0, "--new", 4)
        rec = sh("start", "--ledger", self.L, "--alert-json", tmpjson(A1), "--today", "2026-09-03", "--run-id", "r2")
        self.assertEqual((rec["last_page"], rec["first_seen"], rec["run_id"]), (1, "2026-09-02", "r2"))
    def test_prune(self):
        sh("start", "--ledger", self.L, "--alert-json", tmpjson(A1), "--today", "2026-07-01", "--run-id", "r0")
        sh("start", "--ledger", self.L, "--alert-json", tmpjson(A2), "--today", "2026-09-01", "--run-id", "r1")
        r = sh("prune", "--ledger", self.L, "--today", "2026-09-02"); self.assertEqual((r["pruned"], r["kept"]), (1, 1))
        self.assertNotIn(A1["alert_key"], json.load(open(self.L))["alerts"])
    def test_bad_reason_rejected(self):
        sh("start", "--ledger", self.L, "--alert-json", tmpjson(A1), "--today", "2026-09-02", "--run-id", "r")
        p = subprocess.run(["python3", os.path.join(S, "alerts_ledger.py"), "complete", "--ledger", self.L, "--key", A1["alert_key"], "--reason", "tired"], capture_output=True, text=True)
        self.assertNotEqual(p.returncode, 0)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd skills/_ultra-engine/tests && python3 -m unittest test_alerts_ledger -v`
Expected: FAIL (script missing).

- [ ] **Step 3: Write the script**

`skills/_ultra-engine/scripts/alerts_ledger.py`:

```python
#!/usr/bin/env python3
"""The alert ledger (.job-scout/alerts.json). stdlib only, atomic writes.
Commands: plan | start | page | complete | prune  (see plan Task 4 for arguments)."""
import argparse, json, os, sys, tempfile
from datetime import date

REASONS = ("divider", "drift", "valve", "no_next")
COUNTS = ("cards_seen", "before_divider", "known", "reposts", "new")

def load(path):
    if not os.path.isfile(path): return {"schema_version": 1, "alerts": {}}
    with open(path) as fh: return json.load(fh)

def save(path, ledger):
    d = os.path.dirname(os.path.abspath(path)); os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    with os.fdopen(fd, "w") as fh: json.dump(ledger, fh, indent=1, ensure_ascii=False)
    os.replace(tmp, path)

def rec_of(alert, today, run_id):
    return {"keywords": alert["keywords"], "geo_id": alert.get("geo_id", ""), "since_epoch": alert["since_epoch"],
            "since": alert.get("since"), "params": alert.get("params", ""), "first_seen": today, "status": "partial",
            "last_page": 0, "stop_reason": None, "cards_seen": 0, "before_divider": 0, "known": 0, "reposts": 0, "new": 0,
            "run_id": run_id}

def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan"); p.add_argument("--ledger", required=True); p.add_argument("--alerts", required=True); p.add_argument("--today", required=True)
    s = sub.add_parser("start"); s.add_argument("--ledger", required=True); s.add_argument("--alert-json", required=True); s.add_argument("--today", required=True); s.add_argument("--run-id", required=True)
    g = sub.add_parser("page"); g.add_argument("--ledger", required=True); g.add_argument("--key", required=True); g.add_argument("--page", type=int, required=True)
    for c in COUNTS: g.add_argument("--" + c.replace("_", "-"), type=int, required=True)
    c = sub.add_parser("complete"); c.add_argument("--ledger", required=True); c.add_argument("--key", required=True); c.add_argument("--reason", required=True, choices=REASONS)
    r = sub.add_parser("prune"); r.add_argument("--ledger", required=True); r.add_argument("--today", required=True); r.add_argument("--days", type=int, default=30)
    a = ap.parse_args()
    L = load(a.ledger); al = L["alerts"]
    if a.cmd == "plan":
        parsed = json.load(open(a.alerts))["alerts"]; walk, skipped = [], 0
        for x in parsed:
            k = x["alert_key"]; cur = al.get(k)
            if cur is None: walk.append({"alert_key": k, "resume_page": 1, "status": "new"})
            elif cur["status"] == "complete": skipped += 1
            else: walk.append({"alert_key": k, "resume_page": int(cur.get("last_page", 0)) + 1, "status": "partial"})
        print(json.dumps({"walk": walk, "skipped_complete": skipped})); return
    if a.cmd == "start":
        x = json.load(open(a.alert_json)); k = x["alert_key"]
        if k not in al: al[k] = rec_of(x, a.today, a.run_id)
        else: al[k]["run_id"] = a.run_id
        save(a.ledger, L); print(json.dumps(al[k])); return
    if a.cmd in ("page", "complete"):
        if a.key not in al: print(f"alerts_ledger: unknown key {a.key}", file=sys.stderr); sys.exit(1)
        rec = al[a.key]
        if a.cmd == "page":
            for cnt in COUNTS: rec[cnt] = int(rec.get(cnt, 0)) + int(getattr(a, cnt))
            rec["last_page"] = a.page
        else:
            rec["status"] = "complete"; rec["stop_reason"] = a.reason
        save(a.ledger, L); print(json.dumps(rec)); return
    if a.cmd == "prune":
        today = date.fromisoformat(a.today); keep, pruned = {}, 0
        for k, rec in al.items():
            if (today - date.fromisoformat(rec.get("first_seen", a.today))).days > a.days: pruned += 1
            else: keep[k] = rec
        L["alerts"] = keep; save(a.ledger, L); print(json.dumps({"pruned": pruned, "kept": len(keep)}))

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd skills/_ultra-engine/tests && python3 -m unittest test_alerts_ledger -v`
Expected: 5 tests OK.

- [ ] **Step 5: Suite + commit**

```bash
bash skills/_ultra-engine/tests/run.sh | tail -1   # ALL PASS
git add skills/_ultra-engine/scripts/alerts_ledger.py skills/_ultra-engine/tests/test_alerts_ledger.py
git commit -m "Phase 17 Task 4: alerts_ledger.py — plan/start/page/complete/prune for alerts.json

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---
### Task 5: The four in-page scripts (shipped verbatim) + anchor guard test

**Files:**
- Create: `skills/_ultra-engine/scripts/page/notifications.js`, `results.js`, `toppicks.js`, `saved.js`
- Test: `skills/_ultra-engine/tests/test_page_scripts.sh`

**Interfaces:**
- Each file is the exact text the command pastes into the browser surface's page-script tool. Each ends with a `JSON.stringify(out)` expression whose value is the page dump (File map § shared interface). They use top-level `await` (both surfaces support it).
- `notifications.js` → `{"surface":"notifications","url","load_more_clicks","exhausted","alerts":[{"href","age_text"}]}`.
- `results.js` → an `alert` dump with `claimed_results`, `divider_index`, `has_next`, `page` (read from `aria-current="true"`), `cards` (outermost `componentkey` cards only).
- `toppicks.js` → a `toppicks` dump from `li[data-occludable-job-id]` after scrolling until the count stops growing.
- `saved.js` → a `saved` dump; `saved_count` parsed from the `Saved · N` tab label; cards from either selector set.

- [ ] **Step 1: Write the anchor guard test (fails until the files exist)**

`skills/_ultra-engine/tests/test_page_scripts.sh`:

```bash
#!/bin/bash
. "$(dirname "$0")/helpers.sh"
P="$(dirname "$0")/../scripts/page"
req() { grep -qF -- "$2" "$P/$1"; _report $? "$1 carries anchor: $2"; }
for f in notifications.js results.js toppicks.js saved.js; do
  [ -s "$P/$f" ]; _report $? "$f exists and is non-empty"
  grep -q 'JSON.stringify(out)' "$P/$f"; _report $? "$f returns JSON.stringify(out)"
  grep -q '"surface"' "$P/$f" || grep -q 'surface:' "$P/$f"; _report $? "$f sets surface"
  ! grep -qi 'voyager' "$P/$f"; _report $? "$f never mentions voyager"
done
req notifications.js 'alertAction=viewjobs'
req notifications.js 'Load more'
req results.js 'job-card-component-ref-'
req results.js 'We found more results related to your search'
req results.js 'pagination-controls-next-button-visible'
req results.js 'aria-current'
req toppicks.js 'data-occludable-job-id'
req toppicks.js 'data-job-id'
req saved.js 'jobs-tracker'
req saved.js 'Saved'
if command -v node >/dev/null 2>&1; then
  for f in notifications.js results.js toppicks.js saved.js; do
    node -e "new Function('return (async()=>{' + require('fs').readFileSync('$P/$f','utf8') + '})()')" 2>/dev/null
    _report $? "$f parses as JS (node available)"
  done
fi
finish
```

- [ ] **Step 2: Run it to verify it fails**

Run: `bash skills/_ultra-engine/tests/test_page_scripts.sh`
Expected: `fails>0`, exit 1.

- [ ] **Step 3: Write `notifications.js`**

```javascript
// notifications.js — run on https://www.linkedin.com/notifications/?filter=jobs_all
// Exhausts "Load more", returns every job-alert link. Anchors: evidence §1 only.
const sleep = ms => new Promise(r => setTimeout(r, ms));
const loadMore = () => [...document.querySelectorAll('button')].find(b => b.innerText.trim() === 'Load more');
let clicks = 0;
for (let i = 0; i < 25; i++) { const b = loadMore(); if (!b) break; b.click(); clicks++; await sleep(1500); }
window.scrollTo(0, document.body.scrollHeight); await sleep(800);
const seen = new Set(); const alerts = [];
for (const a of document.querySelectorAll('a[href*="alertAction=viewjobs"]')) {
  if (seen.has(a.href)) continue; seen.add(a.href);
  let n = a, age = '';
  for (let i = 0; i < 6 && n; i++) {
    n = n.parentElement; if (!n) break;
    const t = (n.innerText || '').split('\n').map(s => s.trim()).find(s => /^\d+\s?(m|h|d|w|min|mins|hr|hrs|hour|hours|day|days|week|weeks)$/.test(s));
    if (t) { age = t; break; }
  }
  alerts.push({ href: a.href, age_text: age });
}
const out = { surface: 'notifications', url: location.href, load_more_clicks: clicks, exhausted: !loadMore(), alerts };
JSON.stringify(out)
```

- [ ] **Step 4: Write `results.js`**

```javascript
// results.js — run on an alert results page (https://www.linkedin.com/jobs/search-results/?…)
// Returns the page dump for cards_parse.py --surface alert. Anchors: evidence §2 only.
const sleep = ms => new Promise(r => setTimeout(r, ms));
const isScroller = e => { const s = getComputedStyle(e); return /(auto|scroll)/.test(s.overflowY) && e.scrollHeight > e.clientHeight + 100; };
let pane = null;
for (const c of document.querySelectorAll('[componentkey^="job-card-component-ref-"]')) {
  let n = c.parentElement; while (n && !isScroller(n)) n = n.parentElement; if (n) { pane = n; break; }
}
if (pane) { for (let i = 0; i < 6; i++) { pane.scrollTop = pane.scrollHeight; await sleep(500); } pane.scrollTop = 0; await sleep(300); }
const all = [...document.querySelectorAll('[componentkey^="job-card-component-ref-"]')];
const outer = all.filter(c => !(c.parentElement && c.parentElement.closest('[componentkey^="job-card-component-ref-"]')));
const divider = [...document.querySelectorAll('p,span,div')].find(e => e.children.length === 0 && /^We found more results related to your search/.test(e.textContent.trim()));
let dividerIndex = null;
if (divider) { dividerIndex = 0; for (const c of outer) { if (c.compareDocumentPosition(divider) & Node.DOCUMENT_POSITION_FOLLOWING) dividerIndex++; } }
const cards = outer.map(c => ({ id: c.getAttribute('componentkey').replace('job-card-component-ref-', ''), text: c.innerText }));
const claimedEl = [...document.querySelectorAll('p,span,div,h1,h2')].find(e => e.children.length === 0 && /^\d[\d,]*\+?\s+results?$/.test(e.textContent.trim()));
const active = document.querySelector('[data-testid="pagination-controls-list"] button[aria-current="true"]');
const page = active ? parseInt(active.innerText.trim(), 10) || 1 : 1;
const hasNext = !!document.querySelector('button[data-testid="pagination-controls-next-button-visible"]');
const out = { surface: 'alert', url: location.href, claimed_results: claimedEl ? claimedEl.textContent.trim() : null, page,
              cards, divider_index: dividerIndex, has_next: hasNext, saved_count: null };
JSON.stringify(out)
```

- [ ] **Step 5: Write `toppicks.js`**

```javascript
// toppicks.js — run on https://www.linkedin.com/jobs/collections/recommended/
// Old (Ember) markup: occludable cards must be scrolled into existence. Anchors: evidence §3 only.
const sleep = ms => new Promise(r => setTimeout(r, ms));
const isScroller = e => { const s = getComputedStyle(e); return /(auto|scroll)/.test(s.overflowY) && e.scrollHeight > e.clientHeight + 100; };
const count = () => document.querySelectorAll('li[data-occludable-job-id]').length;
let pane = null; const first = document.querySelector('li[data-occludable-job-id]');
if (first) { let n = first.parentElement; while (n && !isScroller(n)) n = n.parentElement; pane = n; }
let last = -1;
for (let i = 0; i < 12 && count() !== last; i++) { last = count(); if (pane) pane.scrollTop = pane.scrollHeight; else window.scrollTo(0, document.body.scrollHeight); await sleep(700); }
if (pane) { pane.scrollTop = 0; await sleep(300); }
const cards = [...document.querySelectorAll('li[data-occludable-job-id]')].map(li => {
  const inner = li.querySelector('[data-job-id]');
  return { id: li.getAttribute('data-occludable-job-id') || (inner && inner.getAttribute('data-job-id')) || '', text: li.innerText };
});
const active = document.querySelector('button[aria-label^="Page"][aria-current="true"]');
const page = active ? parseInt(active.innerText.trim(), 10) || 1 : 1;
const hasNext = [...document.querySelectorAll('button[aria-label^="Page"]')].some(b => parseInt(b.innerText.trim(), 10) > page);
const out = { surface: 'toppicks', url: location.href, claimed_results: null, page, cards, divider_index: null, has_next: hasNext, saved_count: null };
JSON.stringify(out)
```

- [ ] **Step 6: Write `saved.js`**

```javascript
// saved.js — run on https://www.linkedin.com/jobs-tracker/ (the redirect target of /my-items/saved-jobs/)
// Reads the Saved tab count; extracts cards through either known selector set. Anchors: evidence §4.
const sleep = ms => new Promise(r => setTimeout(r, ms));
await sleep(1500);
const savedTab = [...document.querySelectorAll('button,a,[role=tab],span')].find(e => /^Saved\s*·\s*\d+$/.test((e.innerText || e.textContent || '').trim()));
let savedCount = null;
if (savedTab) { savedCount = parseInt((savedTab.innerText || savedTab.textContent).replace(/\D/g, ''), 10); if (savedTab.click && savedTab.getAttribute('aria-selected') !== 'true') { savedTab.click(); await sleep(1500); } }
for (let i = 0; i < 6; i++) { window.scrollTo(0, document.body.scrollHeight); await sleep(600); }
const seen = new Set(); const cards = [];
for (const e of document.querySelectorAll('[componentkey^="job-card-component-ref-"], li[data-occludable-job-id], [data-job-id]')) {
  const id = (e.getAttribute('componentkey') || '').replace('job-card-component-ref-', '') || e.getAttribute('data-occludable-job-id') || e.getAttribute('data-job-id') || '';
  if (!/^\d{6,}$/.test(id) || seen.has(id)) continue; seen.add(id);
  const host = e.closest('li') || e; cards.push({ id, text: host.innerText });
}
if (!cards.length) { for (const a of document.querySelectorAll('a[href*="/jobs/view/"]')) { const m = a.href.match(/\/jobs\/view\/(\d+)/); if (m && !seen.has(m[1])) { seen.add(m[1]); const host = a.closest('li') || a.parentElement; cards.push({ id: m[1], text: host ? host.innerText : a.innerText }); } } }
const out = { surface: 'saved', url: location.href, claimed_results: null, page: 1, cards, divider_index: null, has_next: false, saved_count: savedCount };
JSON.stringify(out)
```

- [ ] **Step 7: Run the guard test; it must pass**

Run: `bash skills/_ultra-engine/tests/test_page_scripts.sh`
Expected: every check `ok`, `fails=0`.

- [ ] **Step 8: Live smoke of `results.js` and `notifications.js` (read-only, built-in browser)**

Open the notifications page in the built-in browser pane, run `notifications.js` through its page-script tool, and check the returned JSON has `exhausted: true` and every `href` contains `alertAction=viewjobs`. Open the first alert's `results_url` (from `alerts_parse.py`) and run `results.js`; pipe the output through `python3 skills/_ultra-engine/scripts/cards_parse.py --surface alert` and confirm `cards_before_divider` equals a manual count of cards above the divider. Record both counts in the commit message.

- [ ] **Step 9: Suite + commit**

```bash
bash skills/_ultra-engine/tests/run.sh | tail -1   # ALL PASS
git add skills/_ultra-engine/scripts/page skills/_ultra-engine/tests/test_page_scripts.sh
git commit -m "Phase 17 Task 5: in-page scripts (notifications/results/toppicks/saved) + anchor guard (live smoke: N alerts, M cards before divider)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---
### Task 6: `coverage.py` + scorecard embedding

**Files:**
- Create: `skills/_ultra-engine/scripts/coverage.py`
- Modify: `skills/_ultra-engine/scripts/scorecard.sh` (embed `coverage.json`; add `budget` from `jd-fetch.json`)
- Test: `skills/_ultra-engine/tests/test_coverage.py`; extend `skills/_ultra-engine/tests/test_scorecard.sh`

**Interfaces:**
- Consumes: the ledger (Task 4) and `--run-id`; optional `--reposts <reposts.json>` (Task 12 writes `$rd/reposts.json` as `[{"id","matched_id","alert_key","title","company","location"}]`).
- Produces: `coverage.json` = `{"rows":[{alert_key, keywords, since, pages_walked, stop_reason, status, cards_seen, before_divider, known, reposts, new}], "totals":{alerts, complete, partial, cards_seen, before_divider, known, reposts, new}, "reposts_disclosed": n}`. Rows are the ledger records whose `run_id == --run-id`, ordered by `since` descending. `scorecard.json` gains `coverage` (this object, or `{"rows":[],"totals":{}}` when absent) and `budget: {limit, used, queued}` (from `jd-fetch.json` `{budget, used, deferred}` → `limit=budget, queued=deferred`).

- [ ] **Step 1: Write the failing test**

`skills/_ultra-engine/tests/test_coverage.py`:

```python
import json, os, subprocess, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); S = os.path.join(HERE, "..", "scripts")
LEDGER = {"schema_version": 1, "alerts": {
  "k1": {"keywords": "linux engineer Contract Remote", "since": "2026-08-31T23:26:37Z", "first_seen": "2026-09-02", "status": "complete", "last_page": 2, "stop_reason": "divider", "cards_seen": 49, "before_divider": 24, "known": 10, "reposts": 1, "new": 13, "run_id": "r1"},
  "k2": {"keywords": "ipa kerberos", "since": "2026-08-31T10:17:37Z", "first_seen": "2026-09-02", "status": "partial", "last_page": 1, "stop_reason": None, "cards_seen": 25, "before_divider": 25, "known": 20, "reposts": 0, "new": 5, "run_id": "r1"},
  "k0": {"keywords": "old", "since": "2026-08-30T10:00:00Z", "first_seen": "2026-08-31", "status": "complete", "last_page": 1, "stop_reason": "no_next", "cards_seen": 3, "before_divider": 3, "known": 3, "reposts": 0, "new": 0, "run_id": "r0"}}}
class T(unittest.TestCase):
    def test_rows_and_totals(self):
        d = tempfile.mkdtemp(); L = os.path.join(d, "alerts.json"); json.dump(LEDGER, open(L, "w"))
        R = os.path.join(d, "reposts.json"); json.dump([{"id": "1", "matched_id": "2", "alert_key": "k1"}], open(R, "w"))
        out = os.path.join(d, "coverage.json")
        p = subprocess.run(["python3", os.path.join(S, "coverage.py"), "--ledger", L, "--run-id", "r1", "--reposts", R, "--out", out], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr); c = json.load(open(out))
        self.assertEqual([r["alert_key"] for r in c["rows"]], ["k1", "k2"])
        self.assertEqual(c["rows"][0]["pages_walked"], 2)
        self.assertEqual(c["totals"], {"alerts": 2, "complete": 1, "partial": 1, "cards_seen": 74, "before_divider": 49, "known": 30, "reposts": 1, "new": 18})
        self.assertEqual(c["reposts_disclosed"], 1)
    def test_missing_ledger_gives_empty(self):
        d = tempfile.mkdtemp(); out = os.path.join(d, "coverage.json")
        p = subprocess.run(["python3", os.path.join(S, "coverage.py"), "--ledger", os.path.join(d, "none.json"), "--run-id", "r1", "--out", out], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0); self.assertEqual(json.load(open(out))["rows"], [])
if __name__ == "__main__":
    unittest.main()
```

Append to `skills/_ultra-engine/tests/test_scorecard.sh` (before its `finish` line):

```bash
# Phase 17: coverage + budget embedding
rd17=$(mktemp -d); printf '{"rows":[{"alert_key":"k1"}],"totals":{"alerts":1},"reposts_disclosed":0}' > "$rd17/coverage.json"
printf '{"budget":150,"used":12,"deferred":3}' > "$rd17/jd-fetch.json"
sc17=$(bash "$SC" "$rd17" "$(dirname "$0")/fixtures/tracker-mini.json" 2026-09-02)
assert_eq "1" "$(echo "$sc17" | jq '.coverage.rows|length')" "coverage embedded"
assert_json_eq '{"limit":150,"used":12,"queued":3}' "$(echo "$sc17" | jq -c '.budget')" "budget embedded"
rd18=$(mktemp -d)
assert_eq "0" "$(bash "$SC" "$rd18" "$(dirname "$0")/fixtures/tracker-mini.json" 2026-09-02 | jq '.coverage.rows|length')" "absent coverage is empty rows"
```

(`$SC` is the scorecard path variable already defined at the top of that test file; if it is named differently there, use that name.)

- [ ] **Step 2: Run both to verify they fail**

Run: `cd skills/_ultra-engine/tests && python3 -m unittest test_coverage -v; bash test_scorecard.sh | tail -3`
Expected: coverage tests FAIL (script missing); scorecard shows `FAIL: coverage embedded`.

- [ ] **Step 3: Write `coverage.py`**

```python
#!/usr/bin/env python3
"""Per-alert coverage table for one run. stdlib only.
Usage: coverage.py --ledger alerts.json --run-id R --out coverage.json [--reposts reposts.json]"""
import argparse, json, os

KEYS = ("cards_seen", "before_divider", "known", "reposts", "new")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger", required=True); ap.add_argument("--run-id", required=True)
    ap.add_argument("--out", required=True); ap.add_argument("--reposts")
    a = ap.parse_args()
    alerts = json.load(open(a.ledger))["alerts"] if os.path.isfile(a.ledger) else {}
    rows = []
    for k, r in alerts.items():
        if r.get("run_id") != a.run_id: continue
        rows.append({"alert_key": k, "keywords": r.get("keywords"), "since": r.get("since"),
                     "pages_walked": int(r.get("last_page", 0)), "stop_reason": r.get("stop_reason"), "status": r.get("status"),
                     **{x: int(r.get(x, 0)) for x in KEYS}})
    rows.sort(key=lambda r: r["since"] or "", reverse=True)
    totals = {"alerts": len(rows), "complete": sum(1 for r in rows if r["status"] == "complete"),
              "partial": sum(1 for r in rows if r["status"] == "partial"), **{x: sum(r[x] for r in rows) for x in KEYS}}
    reposts = json.load(open(a.reposts)) if a.reposts and os.path.isfile(a.reposts) else []
    tmp = a.out + ".tmp"
    with open(tmp, "w") as fh: json.dump({"rows": rows, "totals": totals, "reposts_disclosed": len(reposts)}, fh, indent=1)
    os.replace(tmp, a.out)
    print(json.dumps(totals))

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Extend `scorecard.sh`**

In `skills/_ultra-engine/scripts/scorecard.sh`, after the line `pipe='{"errors": []}'; [ -f "$rd/pipeline-errors.json" ] && pipe=$(cat "$rd/pipeline-errors.json")` add:

```bash
cov='{"rows": [], "totals": {}, "reposts_disclosed": 0}'; [ -f "$rd/coverage.json" ] && cov=$(cat "$rd/coverage.json")
```

Add `--argjson cov "$cov"` to the final `jq -n` argument list, and inside the output object add two keys right after `jd_fetch: $jdf, rotation: $rot,`:

```
     coverage: $cov,
     budget: {limit: ($jdf.budget // 0), used: ($jdf.used // 0), queued: ($jdf.deferred // 0)},
```

- [ ] **Step 5: Run both tests to verify they pass**

Run: `cd skills/_ultra-engine/tests && python3 -m unittest test_coverage -v && bash test_scorecard.sh | tail -1`
Expected: OK and `fails=0`.

- [ ] **Step 6: Suite + commit**

```bash
bash skills/_ultra-engine/tests/run.sh | tail -1   # ALL PASS
git add skills/_ultra-engine/scripts/coverage.py skills/_ultra-engine/scripts/scorecard.sh skills/_ultra-engine/tests/test_coverage.py skills/_ultra-engine/tests/test_scorecard.sh
git commit -m "Phase 17 Task 6: coverage.py per-alert table; scorecard embeds coverage + budget

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---
### Task 7: `payload_notifications.sh` — the render payload for the daily driver

**Files:**
- Create: `skills/_ultra-engine/scripts/payload_notifications.sh`
- Create: `skills/_ultra-engine/tests/fixtures/p17-tracker-run.json`
- Test: `skills/_ultra-engine/tests/test_payload_notifications.sh`

**Interfaces:**
- Call: `bash $SCRIPTS/payload_notifications.sh <tracker.json> <run-dir> <today> <run_status> [<no_scrape_reason>]` where `run_status ∈ fresh|no_scrape`.
- Reads from `<run-dir>`: `scorecard.json` (Task 6 shape), optional `reposts.json`, optional `queued.json` (`[{id,title,company,location,url,alert_key}]`).
- Produces stdout JSON for `_visualizer` view `check-job-notifications`: `{title, subtitle, generated_at, filename, unread_count, tier_counts:{a,b,c,d,total}, results:[…], near_misses:[…], coverage, queued:[…], reposts:[…], budget, run_status, no_scrape_reason, scorecard}`. `results[]` = tracker entries with `first_seen == today`, each `{id, title, company, location, received_at: first_seen, posted_at, source: <board string>, tier, tier_reason, dimensions, gate_violations, fresh, seen: false, preview: "", url, competitiveness?, confidence?, match_explanation_tag?}` sorted tier A→B→C→D(untiered last), confidence high→med→low(absent last), compensation-disclosing (`salary_text` or `signals.rate` present) before non-disclosing, then `posted_at` desc. `fresh` = tier A/B and `posted_at` within 2 days of today. `source` is emitted as the **board string** so the existing template's `{{ note.source }}` keeps rendering (legacy strings pass through). Optional scoring fields are omitted when null.

- [ ] **Step 1: Write the fixture**

`skills/_ultra-engine/tests/fixtures/p17-tracker-run.json`:

```json
{"schema_version":3,"stats":{"total_seen":4},"jobs":{
 "1001":{"id":"1001","url":"https://www.linkedin.com/jobs/view/1001/","title":"Lead Platform Engineer","company":"Acme","location":"Amsterdam (Remote)","source":{"lane":"linkedin","provider":"linkedin","board":"Job Alert"},"tier":"A","tier_reason":null,"dimensions":{"core":{"tier":"A","evidence":["kubernetes"]}},"gate_violations":[],"rubric_version":"v1","confidence":"high","status":"seen","first_seen":"2026-09-02","last_seen":"2026-09-02","posted_at":"2026-09-02","jd_path":"jds/1001.txt","signals":{"remote":"remote","rate":"€800/day"},"notes":""},
 "1002":{"id":"1002","url":"https://www.linkedin.com/jobs/view/1002/","title":"SRE","company":"Beta","location":"Berlin (Remote)","source":{"lane":"linkedin","provider":"linkedin","board":"Top Picks"},"tier":"B","tier_reason":null,"dimensions":{},"gate_violations":[],"rubric_version":"v1","status":"seen","first_seen":"2026-09-02","last_seen":"2026-09-02","posted_at":"2026-08-25","jd_path":"jds/1002.txt","notes":""},
 "1003":{"id":"1003","url":"https://www.linkedin.com/jobs/view/1003/","title":"Cloud Architect","company":"Gamma","location":"Utrecht (Hybrid)","source":"Job Alert","tier":"D","tier_reason":"gated: work_arrangement","dimensions":{},"gate_violations":[{"kind":"work_arrangement","detail":"hybrid stated"}],"rubric_version":"v1","status":"seen","first_seen":"2026-09-02","last_seen":"2026-09-02","posted_at":"2026-09-01","jd_path":"jds/1003.txt","near_miss":true,"near_miss_would_be_tier":"B","notes":""},
 "0999":{"id":"0999","url":"https://www.linkedin.com/jobs/view/0999/","title":"Old","company":"Delta","location":"Paris","source":"Search","tier":"C","status":"seen","first_seen":"2026-08-20","last_seen":"2026-09-02","rubric_version":"legacy","notes":""}}}
```

- [ ] **Step 2: Write the failing test**

`skills/_ultra-engine/tests/test_payload_notifications.sh`:

```bash
#!/bin/bash
. "$(dirname "$0")/helpers.sh"
P="$(dirname "$0")/../scripts/payload_notifications.sh"; T="$(dirname "$0")/fixtures/p17-tracker-run.json"
rd=$(mktemp -d)
printf '{"date":"2026-09-02","coverage":{"rows":[{"alert_key":"k1","keywords":"x","pages_walked":2,"stop_reason":"divider","status":"complete","cards_seen":49,"before_divider":24,"known":10,"reposts":1,"new":13}],"totals":{"alerts":1,"complete":1,"partial":0,"cards_seen":49,"before_divider":24,"known":10,"reposts":1,"new":13},"reposts_disclosed":1},"budget":{"limit":150,"used":13,"queued":0},"disclosures":[]}' > "$rd/scorecard.json"
printf '[{"id":"1777","matched_id":"1001","alert_key":"k1","title":"Lead Platform Engineer","company":"Acme","location":"Amsterdam (Remote)"}]' > "$rd/reposts.json"
printf '[{"id":"1888","title":"Queued role","company":"Eps","location":"Remote","url":"https://www.linkedin.com/jobs/view/1888/","alert_key":"k1"}]' > "$rd/queued.json"
out=$(bash "$P" "$T" "$rd" 2026-09-02 fresh)
assert_eq "check-job-notifications-2026-09-02.html" "$(echo "$out" | jq -r .filename)" "filename"
assert_eq "1001 1002 1003" "$(echo "$out" | jq -r '[.results[].id]|join(" ")')" "today only, tier order, D last"
assert_json_eq '{"a":1,"b":1,"c":0,"d":1,"total":3}' "$(echo "$out" | jq -c .tier_counts)" "tier counts"
assert_eq "Job Alert" "$(echo "$out" | jq -r '.results[0].source')" "structured source rendered as board string"
assert_eq "Job Alert" "$(echo "$out" | jq -r '.results[2].source')" "legacy string source passes through"
assert_eq "true" "$(echo "$out" | jq -r '.results[0].fresh')" "A-tier posted today is fresh"
assert_eq "false" "$(echo "$out" | jq -r '.results[1].fresh')" "B-tier 8 days old is not fresh"
assert_eq "null" "$(echo "$out" | jq -r '.results[1].confidence // "null"')" "absent optional field omitted"
assert_eq "1" "$(echo "$out" | jq '.near_misses|length')" "near-miss rail"
assert_eq "1" "$(echo "$out" | jq '.coverage.rows|length')" "coverage passed through"
assert_eq "1888" "$(echo "$out" | jq -r '.queued[0].id')" "queued passed through"
assert_eq "1777" "$(echo "$out" | jq -r '.reposts[0].id')" "reposts passed through"
assert_eq "fresh" "$(echo "$out" | jq -r .run_status)" "run status"
ns=$(bash "$P" "$T" "$rd" 2026-09-02 no_scrape "browser unavailable")
assert_eq "browser unavailable" "$(echo "$ns" | jq -r .no_scrape_reason)" "no_scrape reason"
assert_eq "0" "$(echo "$ns" | jq '.results|length')" "no_scrape renders no new results"
finish
```

- [ ] **Step 3: Run it to verify it fails**

Run: `bash skills/_ultra-engine/tests/test_payload_notifications.sh`
Expected: fails (script missing).

- [ ] **Step 4: Write the script**

`skills/_ultra-engine/scripts/payload_notifications.sh`:

```bash
#!/bin/bash
# Usage: payload_notifications.sh <tracker.json> <run-dir> <today> <fresh|no_scrape> [<no_scrape_reason>]
# The check-job-notifications render payload. Ordering lives here, never in the template or prose.
set -eu
tracker="$1"; rd="$2"; today="$3"; status="$4"; reason="${5-}"
sc='{}'; [ -f "$rd/scorecard.json" ] && sc=$(cat "$rd/scorecard.json")
rep='[]'; [ -f "$rd/reposts.json" ] && rep=$(cat "$rd/reposts.json")
que='[]'; [ -f "$rd/queued.json" ] && que=$(cat "$rd/queued.json")
jq -n --arg today "$today" --arg status "$status" --arg reason "$reason" \
      --argjson sc "$sc" --argjson rep "$rep" --argjson que "$que" --slurpfile t "$tracker" '
  def tier_rank: {"A": 0, "B": 1, "C": 2, "D": 3, "untiered": 4}[.tier // "untiered"] // 4;
  def conf_rank: {"high": 0, "med": 1, "low": 2}[.confidence // "absent"] // 3;
  def comp_rank: if ((.salary_text // "") != "" or ((.signals // {}).rate // "") != "") then 0 else 1 end;
  def date_num: ((.posted_at // "") | if . == "" then "0000-00-00" else . end) | gsub("-"; "") | tonumber;
  def board: if (.source | type) == "object" then (.source.board // "Job Alert") else ((.source // "Job Alert") | tostring) end;
  def days_old: (($today | strptime("%Y-%m-%d") | mktime) - ((.posted_at // "1970-01-01") | strptime("%Y-%m-%d") | mktime)) / 86400;
  def opt(k): if (.[k] // null) == null then {} else {(k): .[k]} end;
  def card: {id: .id, title: .title, company: .company, location: (.location // ""), received_at: .first_seen,
             posted_at: (.posted_at // ""), source: board, tier: (.tier // "untiered"), tier_reason: (.tier_reason // null),
             dimensions: (.dimensions // {}), gate_violations: (.gate_violations // []),
             fresh: ((.tier == "A" or .tier == "B") and (.posted_at // "") != "" and days_old <= 2),
             seen: false, preview: "", url: (.url // "")}
            + opt("competitiveness") + opt("competitiveness_evidence") + opt("confidence") + opt("match_explanation_tag");
  ([ $t[0].jobs | to_entries[] | .value | select(.first_seen == $today) ]
     | if $status == "no_scrape" then [] else . end) as $new
  | [ $new[] | select(.near_miss == true) ] as $nm
  | [ $new[] | select(.near_miss != true) ] | sort_by([tier_rank, conf_rank, comp_rank, (0 - date_num)]) as $sorted
  | ([ $new[] | (.tier // "untiered") ] | group_by(.) | map({(.[0]): length}) | add // {}) as $tc
  | { title: "Today'"'"'s notifications",
      subtitle: ("\($new | length) new · A:\($tc.A // 0) B:\($tc.B // 0) C:\($tc.C // 0) · Filtered:\($tc.D // 0) · alerts walked: \($sc.coverage.totals.alerts // 0)"),
      generated_at: $today, filename: "check-job-notifications-\($today).html",
      unread_count: ($new | length),
      tier_counts: {a: ($tc.A // 0), b: ($tc.B // 0), c: ($tc.C // 0), d: ($tc.D // 0), total: ($new | length)},
      results: [ $sorted[] | card ],
      near_misses: [ $nm[] | card + {would_be_tier: (.near_miss_would_be_tier // "B"),
                                     failed_gate: (((.gate_violations // [])[0]) // {"kind": "unknown", "detail": ""}),
                                     bend_hint: "/bend \(.id)"} ],
      coverage: ($sc.coverage // {"rows": [], "totals": {}, "reposts_disclosed": 0}),
      queued: $que, reposts: $rep,
      budget: ($sc.budget // {"limit": 0, "used": 0, "queued": 0}),
      run_status: $status, no_scrape_reason: (if $status == "no_scrape" then $reason else null end),
      scorecard: $sc }
'
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `bash skills/_ultra-engine/tests/test_payload_notifications.sh`
Expected: `fails=0`. (macOS jq: `strptime`/`mktime` are available in jq ≥1.6; if `days_old` errors on an empty `posted_at`, the guard `(.posted_at // "") != ""` short-circuits before it is evaluated — keep that order.)

- [ ] **Step 6: Suite + commit**

```bash
bash skills/_ultra-engine/tests/run.sh | tail -1   # ALL PASS
git add skills/_ultra-engine/scripts/payload_notifications.sh skills/_ultra-engine/tests/test_payload_notifications.sh skills/_ultra-engine/tests/fixtures/p17-tracker-run.json
git commit -m "Phase 17 Task 7: payload_notifications.sh — ordered render payload with coverage, queued, reposts, run_status

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---
### Task 8: `digest.py` — the plain-text phone digest

**Files:**
- Create: `skills/_ultra-engine/scripts/digest.py`
- Test: `skills/_ultra-engine/tests/test_digest.py` (uses Task 7's script + fixture to produce a payload)

**Interfaces:**
- Call: `python3 $SCRIPTS/digest.py --payload payload.json --profile user-profile.json --out digest.txt [--max-chars 7500] [--last-success YYYY-MM-DD]`.
- Produces the digest file and prints `{"chars": n, "trimmed": bool}`. Content order (D11): (1) status line; (2) `A/B/C MATCHES` one line per job `A · <title> — <company> · <rate or "rate not disclosed"> · <location> · <url>` (A lines append ` · <first evidence quote>` when present); (3) `NEAR MISSES` (`would be <tier>; failed <kind>: <detail>; /bend <id>`); (4) `FILTERED OUT (n)` numbered lines with gate kinds; (5) `QUEUED FOR TOMORROW (n)`; (6) `REPOSTS SKIPPED: n`; (7) `Alerts walked: a (complete c, partial p) · cards a · new n`; (8) `Gates: <kind=value(s)>…` from `requirements.deal_breakers[]`; (9) `Styled report: iCloud Drive → CoWork → <workspace name> → .job-scout/reports/`. Bare URLs only; no markdown. When `run_status == no_scrape`: line 1 is `NO FRESH SCRAPE — <reason>. Last successful run: <last-success or unknown>.`, then sections 8–9 only. Trim rule: if the text exceeds `--max-chars`, drop lines from the end of section 4 (then 5) until it fits, ending that section with `…and N more — see the styled report`.

- [ ] **Step 1: Write the failing test**

`skills/_ultra-engine/tests/test_digest.py`:

```python
import json, os, subprocess, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); S = os.path.join(HERE, "..", "scripts")
PROFILE = {"requirements": {"deal_breakers": [{"kind": "work_arrangement", "values": ["remote"]}, {"kind": "contract_type", "values": ["freelance", "detachering"]}, {"kind": "rate_floor", "values": ["650"], "free_text": "EUR/day"}]}}

def payload(rd, status="fresh", reason=""):
    p = subprocess.run(["bash", os.path.join(S, "payload_notifications.sh"), os.path.join(HERE, "fixtures", "p17-tracker-run.json"), rd, "2026-09-02", status, reason], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr; return json.loads(p.stdout)

class T(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        json.dump({"coverage": {"rows": [], "totals": {"alerts": 3, "complete": 2, "partial": 1, "cards_seen": 70, "new": 9}, "reposts_disclosed": 2}, "budget": {"limit": 150, "used": 9, "queued": 1}}, open(os.path.join(self.d, "scorecard.json"), "w"))
        json.dump([{"id": "1888", "title": "Queued role", "company": "Eps", "location": "Remote", "url": "https://www.linkedin.com/jobs/view/1888/"}], open(os.path.join(self.d, "queued.json"), "w"))
        self.prof = os.path.join(self.d, "profile.json"); json.dump(PROFILE, open(self.prof, "w"))
    def run_digest(self, pl, extra=()):
        pf = os.path.join(self.d, "payload.json"); json.dump(pl, open(pf, "w")); out = os.path.join(self.d, "digest.txt")
        p = subprocess.run(["python3", os.path.join(S, "digest.py"), "--payload", pf, "--profile", self.prof, "--out", out, *extra], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr); return open(out).read(), json.loads(p.stdout)
    def test_fresh_digest_order_and_content(self):
        txt, meta = self.run_digest(payload(self.d))
        lines = txt.split("\n")
        self.assertTrue(lines[0].startswith("Fresh scrape 2026-09-02"))
        self.assertLess(txt.index("A/B/C MATCHES"), txt.index("NEAR MISSES")); self.assertLess(txt.index("NEAR MISSES"), txt.index("FILTERED OUT"))
        self.assertLess(txt.index("FILTERED OUT"), txt.index("QUEUED FOR TOMORROW")); self.assertLess(txt.index("QUEUED FOR TOMORROW"), txt.index("Gates:"))
        self.assertIn("A · Lead Platform Engineer — Acme · €800/day · Amsterdam (Remote) · https://www.linkedin.com/jobs/view/1001/ · kubernetes", txt)
        self.assertIn("B · SRE — Beta · rate not disclosed · Berlin (Remote) · https://www.linkedin.com/jobs/view/1002/", txt)
        self.assertIn("would be B; failed work_arrangement: hybrid stated; /bend 1003", txt)
        self.assertIn("REPOSTS SKIPPED: 2", txt); self.assertIn("Alerts walked: 3 (complete 2, partial 1)", txt)
        self.assertIn("Gates: work_arrangement=remote; contract_type=freelance, detachering; rate_floor=650 (EUR/day)", txt)
        self.assertIn("Styled report: iCloud Drive", txt); self.assertNotIn("](", txt); self.assertNotIn("**", txt)
        self.assertFalse(meta["trimmed"])
    def test_no_scrape_digest(self):
        txt, _ = self.run_digest(payload(self.d, "no_scrape", "browser unavailable"), ("--last-success", "2026-09-01"))
        self.assertTrue(txt.startswith("NO FRESH SCRAPE — browser unavailable. Last successful run: 2026-09-01."))
        self.assertNotIn("A/B/C MATCHES", txt); self.assertIn("Gates:", txt)
    def test_trim(self):
        pl = payload(self.d)
        pl["results"] += [dict(pl["results"][2], id=str(5000 + i), title="Filtered role %d" % i) for i in range(200)]
        txt, meta = self.run_digest(pl, ("--max-chars", "3000"))
        self.assertLessEqual(len(txt), 3000); self.assertTrue(meta["trimmed"]); self.assertIn("more — see the styled report", txt)
        self.assertIn("A/B/C MATCHES", txt); self.assertIn("Gates:", txt)
if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to verify it fails**

Run: `cd skills/_ultra-engine/tests && python3 -m unittest test_digest -v`
Expected: FAIL (script missing).

- [ ] **Step 3: Write the script**

`skills/_ultra-engine/scripts/digest.py`:

```python
#!/usr/bin/env python3
"""Plain-text phone digest from the notifications payload. stdlib only.
Usage: digest.py --payload payload.json --profile user-profile.json --out digest.txt [--max-chars 7500] [--last-success DATE]"""
import argparse, json, os, re

def rate_of(j):
    r = (j.get("signals") or {}).get("rate") or j.get("salary_text") or j.get("salary") or ""
    return r if r else "rate not disclosed"

def job_line(prefix, j, evidence=False):
    line = f"{prefix} · {j.get('title','')} — {j.get('company','')} · {rate_of(j)} · {j.get('location','')} · {j.get('url','')}"
    if evidence:
        for dim in (j.get("dimensions") or {}).values():
            ev = dim.get("evidence") or []
            if ev: return line + " · " + str(ev[0])
    return line

def gates_line(profile):
    parts = []
    for db in ((profile.get("requirements") or {}).get("deal_breakers") or []):
        vals = ", ".join(str(v) for v in (db.get("values") or []))
        ft = db.get("free_text")
        s = f"{db.get('kind')}={vals}" if vals else f"{db.get('kind')}"
        if ft: s += f" ({ft})"
        parts.append(s)
    return "Gates: " + "; ".join(parts) if parts else "Gates: none declared"

def build(pl, profile, last_success, ws_name):
    cov = (pl.get("coverage") or {}).get("totals") or {}
    tail = [gates_line(profile), f"Styled report: iCloud Drive → CoWork → {ws_name} → .job-scout/reports/"]
    if pl.get("run_status") == "no_scrape":
        head = [f"NO FRESH SCRAPE — {pl.get('no_scrape_reason') or 'reason not recorded'}. Last successful run: {last_success or 'unknown'}."]
        return head, [], [], [], tail
    tc = pl.get("tier_counts") or {}
    head = [f"Fresh scrape {pl.get('generated_at','')} · alerts walked {cov.get('alerts',0)} · cards {cov.get('cards_seen',0)} · new {tc.get('total',0)} · A:{tc.get('a',0)} B:{tc.get('b',0)} C:{tc.get('c',0)} · filtered {tc.get('d',0)} · queued {len(pl.get('queued') or [])}"]
    res = pl.get("results") or []
    matches = ["", "A/B/C MATCHES"] + [job_line(j["tier"], j, evidence=(j["tier"] == "A")) for j in res if j.get("tier") in ("A", "B", "C") and not j.get("gate_violations")]
    if len(matches) == 2: matches.append("none cleared the gates today")
    nm = pl.get("near_misses") or []
    near = ["", "NEAR MISSES"] + [job_line(j.get("would_be_tier", "B"), j) + f" · would be {j.get('would_be_tier','B')}; failed {(j.get('failed_gate') or {}).get('kind','?')}: {(j.get('failed_gate') or {}).get('detail','')}; {j.get('bend_hint','')}" for j in nm] if nm else []
    filt = [j for j in res if j.get("gate_violations")]
    filtered = ["", f"FILTERED OUT ({len(filt)})"] + [f"{i}. {j.get('title','')} — {j.get('company','')} · {j.get('location','')} · " + ", ".join(v.get("kind", "?") for v in j["gate_violations"]) + f" · {j.get('url','')}" for i, j in enumerate(filt, 1)]
    q = pl.get("queued") or []
    queued = ["", f"QUEUED FOR TOMORROW ({len(q)})"] + [f"- {j.get('title','')} — {j.get('company','')} · {j.get('location','')} · {j.get('url','')}" for j in q]
    rest = ["", f"REPOSTS SKIPPED: {(pl.get('coverage') or {}).get('reposts_disclosed', 0)}",
            f"Alerts walked: {cov.get('alerts',0)} (complete {cov.get('complete',0)}, partial {cov.get('partial',0)}) · cards {cov.get('cards_seen',0)} · new {cov.get('new',0)}", ""]
    return head + matches + near, filtered, queued, rest, tail

def render(head, filtered, queued, rest, tail): return "\n".join(head + filtered + queued + rest + tail) + "\n"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--payload", required=True); ap.add_argument("--profile", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--max-chars", type=int, default=7500); ap.add_argument("--last-success"); ap.add_argument("--workspace-name", default="CVFREELANCER")
    a = ap.parse_args()
    pl = json.load(open(a.payload)); profile = json.load(open(a.profile)) if os.path.isfile(a.profile) else {}
    head, filtered, queued, rest, tail = build(pl, profile, a.last_success, a.workspace_name)
    trimmed = False
    for section in (filtered, queued):  # D11: drop from the end of FILTERED OUT first, then QUEUED
        if len(render(head, filtered, queued, rest, tail)) <= a.max_chars: break
        dropped = 0
        while len(section) > 2 and len(render(head, filtered, queued, rest, tail)) > a.max_chars:
            section.pop(); dropped += 1
        if dropped:
            section.append(f"…and {dropped} more — see the styled report"); trimmed = True
    text = render(head, filtered, queued, rest, tail)
    if len(text) > a.max_chars:  # last resort: hard cut on a line boundary, keep the tail
        body = "\n".join(head)[: a.max_chars - len("\n".join(tail)) - 60]
        text = body + "\n…truncated — see the styled report\n" + "\n".join(tail) + "\n"; trimmed = True
    text = re.sub(r"\n{3,}", "\n\n", text)
    tmp = a.out + ".tmp"
    with open(tmp, "w") as fh: fh.write(text)
    os.replace(tmp, a.out)
    print(json.dumps({"chars": len(text), "trimmed": trimmed}))

if __name__ == "__main__":
    main()
```

The `…and N more` line states the number of lines removed from that section. The hard-cut branch only engages when even an emptied FILTERED OUT and QUEUED section cannot fit (hundreds of A/B/C lines), and it always keeps the gates line and the report pointer.

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd skills/_ultra-engine/tests && python3 -m unittest test_digest -v`
Expected: 3 tests OK. If `test_trim` fails on the length bound, the hard-cut branch is not engaging; check that `render()` output is measured after every pop.

- [ ] **Step 5: Suite + commit**

```bash
bash skills/_ultra-engine/tests/run.sh | tail -1   # ALL PASS
git add skills/_ultra-engine/scripts/digest.py skills/_ultra-engine/tests/test_digest.py
git commit -m "Phase 17 Task 8: digest.py — plain-text phone digest with 7,500-char trim and no_scrape variant

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---
### Task 9: `migrate_tracker_v3.py` — one-shot canonicalisation of a drifted tracker (D15)

**Files:**
- Create: `skills/_ultra-engine/scripts/migrate_tracker_v3.py`
- Create: `skills/_ultra-engine/tests/fixtures/p17-tracker-drifted.json`
- Test: `skills/_ultra-engine/tests/test_migrate_tracker_v3.py`

**Interfaces:**
- Call: `python3 $SCRIPTS/migrate_tracker_v3.py --tracker <tracker.json> [--sources <sources.json>] [--dry-run]`.
- Behaviour: backup to `<dir>/.backup/tracker.json.<UTC stamp>.pre-phase17.json` (skipped on `--dry-run`); normalise every entry; assert entry count unchanged; write atomically; print a JSON summary `{"entries", "changed", "by_rule": {...}, "backup": path|null, "dry_run": bool}`. Rules, applied per entry:
  1. `id` set to the map key.
  2. `source` string → `{lane:"linkedin", provider:"linkedin", board: B}` where B is the first match in order: contains `top pick`/`top_picks`/`recommend` → `Top Picks`; `saved` → `Saved`; `similar` → `Similar`; `inbox`/`recruiter` → `Inbox`; `alert`/`notification` → `Job Alert`; else `Search`. Namespaced ids (`provider__board__ext`) with a string source → `{lane: <category of the sources.json entry whose name/provider matches provider, else "aggregator">, provider, board}` from the id parts. Object source lacking `lane`/`provider`/`board` (e.g. `{type, surface}`) → mapped the same way from `surface`/`type` text. Objects already carrying all three keys are untouched. The original string is appended to `notes` as `source(legacy): <text>` when it carried more than the board word.
  3. `status` outside the enum → `seen`; `gated` additionally forces `tier: "D"` when tier is missing/`untiered`. The old value is appended to `notes` as `status(legacy): <old>`.
  4. `gate_violations` strings → `{kind: <s if s in the deal-breaker kind enum else "custom">, detail: s}`; objects missing `kind` → `kind: "custom"`.
  5. `first_seen`/`last_seen` ISO datetimes → the date part; missing `last_seen` → `first_seen`; missing `first_seen` → `last_seen` or today.
  6. `tier` missing/invalid → `untiered`; `rubric_version` missing/invalid → `legacy`.
  7. Ad-hoc fields `employment_type`, `rate_disclosed` removed; non-null values appended to `notes` as `employment_type: X`.
  8. `notes` non-string → `""` before appends.
- `stats` keys are preserved verbatim; `schema_version` set to 3.

- [ ] **Step 1: Write the fixture**

`skills/_ultra-engine/tests/fixtures/p17-tracker-drifted.json`:

```json
{"schema_version":2,"stats":{"total_seen":6,"last_run":"2026-09-02","last_ultramode":"2026-08-28","closed_applications":7},"jobs":{
 "4401921503":{"company":"IT Infra Talents","employment_type":"FULL_TIME","first_seen":"2026-09-02T06:00:00Z","gate_violations":["contract_type","skills_mismatch"],"location":"The Randstad, Netherlands","rate_disclosed":null,"source":{"surface":"top_picks","type":"linkedin"},"status":"gated","tier":"D","tier_reason":"consultancy model","title":"Cloud-architect (Azure)","url":"https://www.linkedin.com/jobs/view/4401921503/"},
 "4461737101":{"id":"4461737101","title":"Platform Engineer (Remote)","company":"Hire Feed","location":"France (Remote)","source":"Job Alert (gap lanes: ansible / SRE / platform engineer)","tier":"D","status":"seen","first_seen":"2026-09-01T21:30:00Z","last_seen":"2026-09-01T21:30:00Z","rubric_version":"v1","gate_violations":[{"kind":"rate_floor","detail":"$40-100/hr"}],"notes":"","url":"https://www.linkedin.com/jobs/view/4461737101/"},
 "4459517621":{"id":"4459517621","title":"Staff Engineer","company":"Hard Rock Digital","location":"Gdańsk (Remote)","source":"Ultramode LinkedIn sweep 2026-08-18","status":"seen","first_seen":"2026-08-18","last_seen":"2026-08-18","notes":null,"url":"https://www.linkedin.com/jobs/view/4459517621/"},
 "greenhouse__miro__4012345":{"id":"greenhouse__miro__4012345","title":"SRE","company":"Miro","location":"Amsterdam","source":"greenhouse","tier":"B","status":"approved","first_seen":"2026-07-02","last_seen":"2026-07-02","rubric_version":"v1","notes":"","url":"https://boards.greenhouse.io/miro/jobs/4012345"},
 "4400000001":{"id":"4400000001","title":"Good entry","company":"Ok Co","location":"Berlin (Remote)","source":{"lane":"linkedin","provider":"linkedin","board":"Search"},"tier":"A","status":"applied","first_seen":"2026-08-01","last_seen":"2026-08-02","rubric_version":"v1","gate_violations":[],"notes":"fine","url":"https://www.linkedin.com/jobs/view/4400000001/"},
 "4400000002":{"id":"4400000002","title":"Inbox lead","company":"Rec Co","location":"Remote","source":"check-inbox 2026-07-12 (recruiter link)","tier":"C","status":"skipped","first_seen":"2026-07-12","notes":"","url":"https://www.linkedin.com/jobs/view/4400000002/"}}}
```

- [ ] **Step 2: Write the failing test**

`skills/_ultra-engine/tests/test_migrate_tracker_v3.py`:

```python
import json, os, shutil, subprocess, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); S = os.path.join(HERE, "..", "scripts")
KINDS = {"work_arrangement","contract_type","seniority_floor","location","industry","company","rate_floor","salary_floor","custom"}
class T(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); self.t = os.path.join(self.d, "tracker.json")
        shutil.copy(os.path.join(HERE, "fixtures", "p17-tracker-drifted.json"), self.t)
        json.dump({"schema_version": 2, "sources": [{"name": "Greenhouse", "provider": "greenhouse", "category": "ats-provider"}]}, open(os.path.join(self.d, "sources.json"), "w"))
    def run_it(self, *extra):
        p = subprocess.run(["python3", os.path.join(S, "migrate_tracker_v3.py"), "--tracker", self.t, "--sources", os.path.join(self.d, "sources.json"), *extra], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr); return json.loads(p.stdout)
    def test_dry_run_changes_nothing(self):
        before = open(self.t).read(); s = self.run_it("--dry-run")
        self.assertEqual(open(self.t).read(), before); self.assertTrue(s["dry_run"]); self.assertIsNone(s["backup"]); self.assertGreater(s["changed"], 0)
    def test_migration(self):
        s = self.run_it(); t = json.load(open(self.t)); j = t["jobs"]
        self.assertEqual(s["entries"], 6); self.assertEqual(len(j), 6); self.assertTrue(os.path.isfile(s["backup"]))
        self.assertEqual(t["schema_version"], 3); self.assertEqual(t["stats"]["closed_applications"], 7)
        a = j["4401921503"]
        self.assertEqual(a["id"], "4401921503"); self.assertEqual(a["source"], {"lane": "linkedin", "provider": "linkedin", "board": "Top Picks"})
        self.assertEqual((a["status"], a["tier"]), ("seen", "D")); self.assertEqual(a["first_seen"], "2026-09-02"); self.assertEqual(a["last_seen"], "2026-09-02")
        self.assertEqual(a["gate_violations"], [{"kind": "contract_type", "detail": "contract_type"}, {"kind": "custom", "detail": "skills_mismatch"}])
        self.assertNotIn("employment_type", a); self.assertNotIn("rate_disclosed", a); self.assertIn("employment_type: FULL_TIME", a["notes"]); self.assertIn("status(legacy): gated", a["notes"])
        self.assertEqual(a["rubric_version"], "legacy")
        b = j["4461737101"]; self.assertEqual(b["source"]["board"], "Job Alert"); self.assertIn("source(legacy): Job Alert (gap lanes", b["notes"]); self.assertEqual(b["first_seen"], "2026-09-01")
        c = j["4459517621"]; self.assertEqual(c["source"]["board"], "Search"); self.assertEqual(c["tier"], "untiered"); self.assertEqual(c["notes"], "source(legacy): Ultramode LinkedIn sweep 2026-08-18")
        g = j["greenhouse__miro__4012345"]; self.assertEqual(g["source"], {"lane": "ats-provider", "provider": "greenhouse", "board": "miro"})
        ok = j["4400000001"]; self.assertEqual(ok["source"]["board"], "Search"); self.assertEqual(ok["notes"], "fine")
        self.assertEqual(j["4400000002"]["source"]["board"], "Inbox"); self.assertEqual(j["4400000002"]["last_seen"], "2026-07-12")
        for e in j.values():
            self.assertIn(e["status"], {"seen","approved","applied","rejected","skipped"}); self.assertIn(e["tier"], {"A","B","C","D","untiered"})
            for v in e.get("gate_violations", []): self.assertIn(v["kind"], KINDS)
    def test_idempotent(self):
        self.run_it(); once = open(self.t).read(); s = self.run_it(); self.assertEqual(s["changed"], 0); self.assertEqual(open(self.t).read(), once)
    def test_validator_passes_after(self):
        self.run_it()
        chk = subprocess.run(["jq", "-e", '[.jobs[] | select(.status as $s | ["seen","approved","applied","rejected","skipped"] | index($s) | not)] | length == 0', self.t], capture_output=True)
        self.assertEqual(chk.returncode, 0)
if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run it to verify it fails**

Run: `cd skills/_ultra-engine/tests && python3 -m unittest test_migrate_tracker_v3 -v`
Expected: FAIL (script missing).

- [ ] **Step 4: Write the script**

`skills/_ultra-engine/scripts/migrate_tracker_v3.py`:

```python
#!/usr/bin/env python3
"""One-shot canonicalisation of a drifted tracker.json (Phase 17, D15). stdlib only.
Usage: migrate_tracker_v3.py --tracker tracker.json [--sources sources.json] [--dry-run]"""
import argparse, json, os, re, sys, tempfile
from datetime import datetime, timezone

STATUSES = {"seen", "approved", "applied", "rejected", "skipped"}
TIERS = {"A", "B", "C", "D", "untiered"}
KINDS = {"work_arrangement", "contract_type", "seniority_floor", "location", "industry", "company", "rate_floor", "salary_floor", "custom"}
BOARD_RULES = [(r"top.?pick|recommend", "Top Picks"), (r"saved", "Saved"), (r"similar", "Similar"),
               (r"inbox|recruiter", "Inbox"), (r"alert|notification", "Job Alert")]

def board_of(text):
    t = (text or "").lower()
    for rx, b in BOARD_RULES:
        if re.search(rx, t): return b
    return "Search"

def note(e, s):
    n = e.get("notes"); n = n if isinstance(n, str) else ""
    e["notes"] = (n + ("; " if n else "") + s) if s not in n else n

def date_only(v, fallback):
    if isinstance(v, str) and re.match(r"^\d{4}-\d{2}-\d{2}", v): return v[:10]
    return fallback

def lane_for(provider, sources):
    for s in sources:
        if (s.get("provider") or s.get("name", "")).lower() == provider.lower(): return s.get("category") or "aggregator"
    return "aggregator"

def fix(key, e, sources, today, by):
    orig = json.dumps(e, sort_keys=True)
    if e.get("id") != key: e["id"] = key; by["id"] += 1
    src = e.get("source")
    if not (isinstance(src, dict) and all(isinstance(src.get(k), str) and src.get(k) for k in ("lane", "provider", "board"))):
        text = src if isinstance(src, str) else " ".join(str(v) for v in (src or {}).values()) if isinstance(src, dict) else ""
        parts = key.split("__")
        if len(parts) == 3 and not key.isdigit():
            e["source"] = {"lane": lane_for(parts[0], sources), "provider": parts[0], "board": parts[1]}
        else:
            b = board_of(text); e["source"] = {"lane": "linkedin", "provider": "linkedin", "board": b}
            if isinstance(src, str) and src.strip().lower() != b.lower(): note(e, f"source(legacy): {src.strip()}")
        by["source"] += 1
    st = e.get("status")
    if st not in STATUSES:
        note(e, f"status(legacy): {st}")
        if st == "gated" and e.get("tier") in (None, "untiered"): e["tier"] = "D"
        e["status"] = "seen"; by["status"] += 1
    if e.get("tier") not in TIERS: e["tier"] = "untiered"; by["tier"] += 1
    if e.get("rubric_version") not in ("legacy", "v1"): e["rubric_version"] = "legacy"; by["rubric_version"] += 1
    gv = e.get("gate_violations")
    if isinstance(gv, list):
        new = []
        for v in gv:
            if isinstance(v, str): new.append({"kind": v if v in KINDS else "custom", "detail": v})
            elif isinstance(v, dict): new.append({"kind": v.get("kind") if v.get("kind") in KINDS else "custom", "detail": str(v.get("detail", ""))})
        if new != gv: e["gate_violations"] = new; by["gate_violations"] += 1
    fs, ls = e.get("first_seen"), e.get("last_seen")
    nfs = date_only(fs, date_only(ls, today)); nls = date_only(ls, nfs)
    if (nfs, nls) != (fs, ls): e["first_seen"], e["last_seen"] = nfs, nls; by["dates"] += 1
    for f in ("employment_type", "rate_disclosed"):
        if f in e:
            if e[f] not in (None, ""): note(e, f"{f}: {e[f]}")
            del e[f]; by["adhoc_fields"] += 1
    if not isinstance(e.get("notes"), str): e["notes"] = ""
    return json.dumps(e, sort_keys=True) != orig

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--tracker", required=True); ap.add_argument("--sources"); ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    t = json.load(open(a.tracker)); jobs = t.get("jobs")
    if not isinstance(jobs, dict): print("migrate: .jobs is not an object", file=sys.stderr); sys.exit(1)
    sources = json.load(open(a.sources)).get("sources", []) if a.sources and os.path.isfile(a.sources) else []
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    by = {k: 0 for k in ("id", "source", "status", "tier", "rubric_version", "gate_violations", "dates", "adhoc_fields")}
    n_before = len(jobs); changed = sum(1 for k, e in jobs.items() if isinstance(e, dict) and fix(k, e, sources, today, by))
    if len(jobs) != n_before: print("migrate: entry count changed — aborting", file=sys.stderr); sys.exit(2)
    t["schema_version"] = 3
    backup = None
    if not a.dry_run:
        d = os.path.dirname(os.path.abspath(a.tracker)); os.makedirs(os.path.join(d, ".backup"), exist_ok=True)
        backup = os.path.join(d, ".backup", f"tracker.json.{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.pre-phase17.json")
        with open(a.tracker) as src, open(backup, "w") as dst: dst.write(src.read())
        fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
        with os.fdopen(fd, "w") as fh: json.dump(t, fh, indent=1, ensure_ascii=False)
        os.replace(tmp, a.tracker)
    print(json.dumps({"entries": n_before, "changed": changed, "by_rule": by, "backup": backup, "dry_run": a.dry_run}))

if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `cd skills/_ultra-engine/tests && python3 -m unittest test_migrate_tracker_v3 -v`
Expected: 4 tests OK.

- [ ] **Step 6: Suite + commit**

```bash
bash skills/_ultra-engine/tests/run.sh | tail -1   # ALL PASS
git add skills/_ultra-engine/scripts/migrate_tracker_v3.py skills/_ultra-engine/tests/test_migrate_tracker_v3.py skills/_ultra-engine/tests/fixtures/p17-tracker-drifted.json
git commit -m "Phase 17 Task 9: migrate_tracker_v3.py — canonicalise drifted trackers with backup and count assertion

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---
### Task 10: Plugin-shipped subagents pinned to models (D14)

**Files:**
- Create: `agents/gate-batch.md`, `agents/score-batch.md`
- Test: `skills/_ultra-engine/tests/test_agents_frontmatter.sh`

**Interfaces:**
- The command (Task 12) dispatches `Agent` with `subagent_type: "gate-batch"` / `"score-batch"` and the JSON envelope from `shared-references/subagent-protocol.md`. Input `inputs`: `{ "jobs": [{ "id", "title", "company", "location", "workplace", "salary_text", "jd_path" }], "workspace": "<abs path>", "requirements": <user-profile.requirements>, "profile_hash", "cv_hash", "rubric_version": "v1" }` (score-batch adds `"dimensions": <user-profile.dimensions[]>`, `"segment"`, `"cv_summary"`). Output deltas: gate → `{ "job_id", "gated": bool, "gate_violations": [{kind, detail}], "signals": {"contract","remote"} }`; score → `{ "job_id", "tier", "tier_reason", "dimensions": {...}, "near_miss"?, "near_miss_would_be_tier"?, "competitiveness"?, "confidence"?, "match_explanation_tag"? }`.

- [ ] **Step 1: Write the guard test**

`skills/_ultra-engine/tests/test_agents_frontmatter.sh`:

```bash
#!/bin/bash
. "$(dirname "$0")/helpers.sh"
A="$(dirname "$0")/../../../agents"
fm() { sed -n '/^---$/,/^---$/p' "$A/$1" | grep -E "^$2:" | head -1 | sed 's/^[^:]*: *//'; }
assert_eq "gate-batch" "$(fm gate-batch.md name)" "gate-batch name"
assert_eq "sonnet" "$(fm gate-batch.md model)" "gate-batch pinned to sonnet"
assert_eq "score-batch" "$(fm score-batch.md name)" "score-batch name"
assert_eq "opus" "$(fm score-batch.md model)" "score-batch pinned to opus"
for f in gate-batch.md score-batch.md; do
  grep -q '^tools: Read' "$A/$f"; _report $? "$f read-only tools"
  grep -q 'subagent-protocol.md' "$A/$f"; _report $? "$f cites the protocol"
  grep -q '"deltas"' "$A/$f"; _report $? "$f documents the delta shape"
  ! grep -qi 'voyager\|navigate\|screenshot' "$A/$f"; _report $? "$f never touches a browser"
done
grep -q '_gate-engine' "$A/gate-batch.md"; _report $? "gate-batch loads _gate-engine"
grep -q '_job-matcher' "$A/score-batch.md"; _report $? "score-batch loads _job-matcher"
finish
```

- [ ] **Step 2: Run it to verify it fails**

Run: `bash skills/_ultra-engine/tests/test_agents_frontmatter.sh` → fails (files missing).

- [ ] **Step 3: Write `agents/gate-batch.md`**

```markdown
---
name: gate-batch
description: Gate a batch of at most 5 newly discovered jobs against the workspace's declared deal_breakers using each job's full description text. Dispatched by /check-job-notifications only. Returns structured deltas, never prose.
model: sonnet
tools: Read
---

You are the gate stage of the daily job scan. You receive one JSON envelope (see `skills/shared-references/subagent-protocol.md`) and return one JSON object. No prose before or after the JSON.

## What to do

1. Read `skills/_gate-engine/SKILL.md` and `skills/_gate-engine/references/gate-rules.md` from the plugin root given in `inputs.plugin_root`.
2. For every job in `inputs.jobs`, read its description from `<inputs.workspace>/<jd_path>`. If the file is missing or empty, return that job with `"gated": false`, `"gate_violations": []`, and add `{ "code": "jd_missing", "message": "<job_id>" }` to `errors` — never guess a gate from card text alone.
3. Evaluate the gates in the engine's order against `inputs.requirements` (`deal_breakers[].values` is the allowed set; `free_text` refines it). A gate fails only on text that states or clearly implies the violation. "Not stated" is never a violation.
4. Derive `signals`: `contract` ∈ `freelance | permanent | detachering | contract | unknown`, `remote` ∈ `remote | hybrid | onsite | unknown`, from explicit JD statements; else `unknown`.

## Output (strict)

```json
{ "status": "ok",
  "deltas": [ { "job_id": "4461737101", "gated": true,
                "gate_violations": [ { "kind": "rate_floor", "detail": "USD 40–100/hour, below the EUR 650/day floor" } ],
                "signals": { "contract": "contract", "remote": "remote" } } ],
  "errors": [], "continuation_cursor": null }
```

Rules: one delta per input job, in input order; `kind` only from the deal-breaker enum; `detail` quotes or closely paraphrases the JD evidence in at most 140 characters; British English. Stay within `budget_lines`.
```

- [ ] **Step 4: Write `agents/score-batch.md`**

```markdown
---
name: score-batch
description: Score a batch of at most 5 ungated jobs with the workspace's v1 dimension rubric, returning tier, per-dimension evidence, and the optional Phase 12 fields. Dispatched by /check-job-notifications only. Returns structured deltas, never prose.
model: opus
tools: Read
---

You are the scoring stage of the daily job scan. You receive one JSON envelope (see `skills/shared-references/subagent-protocol.md`) and return one JSON object. No prose before or after the JSON.

## What to do

1. Read `skills/_job-matcher/SKILL.md` and, if `inputs.dimensions` is empty, `skills/_job-matcher/references/dimensions-default.md` from `inputs.plugin_root`.
2. For every job in `inputs.jobs`, read its description from `<inputs.workspace>/<jd_path>`. A missing file is an error entry `{ "code": "jd_missing", "message": "<job_id>" }` and no delta for that job.
3. Apply the rubric per dimension using `inputs.dimensions` (or the defaults), `inputs.segment`, and `inputs.cv_summary`. Each dimension gets a tier and one or two short evidence quotes from the JD.
4. If the envelope marks a job `"near_miss_candidate": true` (exactly one gate kind failed upstream), still score it fully and set `near_miss: true` with `near_miss_would_be_tier` when the rubric result is A or B; its `tier` stays `"D"`.
5. Derive the optional fields when the evidence supports them: `competitiveness` (`high|med|low`) with a one-line `competitiveness_evidence`, `confidence` (`high|med|low`), `match_explanation_tag` (`all-fit|one-gap|multiple-gaps|overqualified|underqualified|trajectory-concern`). Omit any you cannot support — never emit null.

## Output (strict)

```json
{ "status": "ok",
  "deltas": [ { "job_id": "4461737101", "tier": "B", "tier_reason": null,
                "dimensions": { "platform-depth": { "tier": "A", "evidence": ["design and maintain scalable infrastructure"] } },
                "rubric_version": "v1", "confidence": "med", "match_explanation_tag": "one-gap" } ],
  "errors": [], "continuation_cursor": null }
```

Rules: one delta per scored job; tiers uppercase `A|B|C|D`; evidence quotes ≤ 120 characters each, verbatim from the JD; British English in `tier_reason`. Stay within `budget_lines`.
```

- [ ] **Step 5: Run the guard test; it must pass**

Run: `bash skills/_ultra-engine/tests/test_agents_frontmatter.sh` → `fails=0`.

- [ ] **Step 6: Suite + commit**

```bash
bash skills/_ultra-engine/tests/run.sh | tail -1   # ALL PASS
git add agents skills/_ultra-engine/tests/test_agents_frontmatter.sh
git commit -m "Phase 17 Task 10: gate-batch (sonnet) and score-batch (opus) plugin agents

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---
### Task 11: Templates, visualizer contract, and the summary line

**Files:**
- Modify: `skills/_visualizer/templates/html/check-job-notifications.html.j2`
- Modify: `skills/_visualizer/templates/markdown/check-job-notifications.md.j2`
- Modify: `skills/_visualizer/SKILL.md` (add a `check-job-notifications` additive-fields section after the `ultramode` one at line 34)
- Modify: `skills/shared-references/render-orchestration.md` (summary-line row for `check-job-notifications`)
- Test: `skills/_ultra-engine/tests/test_templates_notifications.py` (renders both templates with Jinja2 against the Task 7 payload; skips cleanly if Jinja2 is not installed)

**Interfaces:**
- Consumes: the Task 7 payload (`coverage`, `queued`, `reposts`, `budget`, `run_status`, `no_scrape_reason`, `near_misses`).
- Produces: templates that render every new section and never error when a field is absent.

- [ ] **Step 1: Write the failing test**

`skills/_ultra-engine/tests/test_templates_notifications.py`:

```python
import json, os, subprocess, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); S = os.path.join(HERE, "..", "scripts")
TPL = os.path.join(HERE, "..", "..", "_visualizer", "templates")
try:
    import jinja2
except ImportError:
    jinja2 = None

def payload(status="fresh", reason=""):
    rd = tempfile.mkdtemp()
    json.dump({"coverage": {"rows": [{"alert_key": "k1", "keywords": "linux engineer Contract Remote", "since": "2026-08-31T23:26:37Z", "pages_walked": 2, "stop_reason": "divider", "status": "complete", "cards_seen": 49, "before_divider": 24, "known": 10, "reposts": 1, "new": 13}], "totals": {"alerts": 1, "complete": 1, "partial": 0, "cards_seen": 49, "before_divider": 24, "known": 10, "reposts": 1, "new": 13}, "reposts_disclosed": 1}, "budget": {"limit": 150, "used": 13, "queued": 1}, "disclosures": []}, open(os.path.join(rd, "scorecard.json"), "w"))
    json.dump([{"id": "1777", "matched_id": "1001", "alert_key": "k1", "title": "Lead Platform Engineer", "company": "Acme", "location": "Amsterdam (Remote)"}], open(os.path.join(rd, "reposts.json"), "w"))
    json.dump([{"id": "1888", "title": "Queued role", "company": "Eps", "location": "Remote", "url": "https://www.linkedin.com/jobs/view/1888/"}], open(os.path.join(rd, "queued.json"), "w"))
    p = subprocess.run(["bash", os.path.join(S, "payload_notifications.sh"), os.path.join(HERE, "fixtures", "p17-tracker-run.json"), rd, "2026-09-02", status, reason], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr; return json.loads(p.stdout)

@unittest.skipIf(jinja2 is None, "jinja2 not installed — template render test skipped")
class T(unittest.TestCase):
    def render(self, fmt, data):
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.join(TPL, fmt)), autoescape=False)
        return env.get_template("check-job-notifications.%s.j2" % ("html" if fmt == "html" else "md")).render(data=data)
    def test_html_sections(self):
        h = self.render("html", payload())
        for s in ("Alert coverage", "linux engineer Contract Remote", "divider", "Queued for tomorrow", "Queued role", "Treated as reposts", "1777", "Would you bend", "/bend 1003", "View posting"):
            self.assertIn(s, h)
        self.assertNotIn("no fresh scrape", h.lower())
    def test_html_no_scrape_banner(self):
        h = self.render("html", payload("no_scrape", "browser unavailable"))
        self.assertIn("No fresh scrape", h); self.assertIn("browser unavailable", h)
    def test_markdown_sections(self):
        m = self.render("markdown", payload())
        for s in ("### Alert coverage", "| linux engineer Contract Remote |", "### Queued for tomorrow", "### Treated as reposts", "### Near misses", "/bend 1003"):
            self.assertIn(s, m)
    def test_missing_optional_fields_do_not_error(self):
        d = payload(); d.pop("coverage"); d.pop("queued"); d.pop("reposts"); d.pop("near_misses"); d.pop("budget")
        self.render("html", d); self.render("markdown", d)
if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it (fails on missing sections; if Jinja2 is missing, install it for the test run: `python3 -m pip install --user jinja2`)**

Run: `cd skills/_ultra-engine/tests && python3 -m unittest test_templates_notifications -v`
Expected: FAIL on `Alert coverage`.

- [ ] **Step 3: Edit the HTML template**

In `skills/_visualizer/templates/html/check-job-notifications.html.j2`:

(a) Extend the schema comment (lines 1–10) with optional keys: `coverage`, `queued`, `reposts`, `near_misses`, `budget`, `run_status`, `no_scrape_reason`.

(b) Insert immediately after the `</header>` line (line 17):

```jinja
{% if data.run_status == 'no_scrape' %}
<div class="gated-banner" style="background:var(--surface-muted,#f5f5f5);border-left:3px solid var(--danger,#c0392b);padding:10px 14px;border-radius:4px;margin:12px 0">
  <strong>No fresh scrape</strong> — {{ data.no_scrape_reason or 'reason not recorded' }}. The tracker was not modified; below is an empty run.
</div>
{% endif %}
{% if data.coverage and data.coverage.rows %}
<details open style="margin:12px 0"><summary><strong>Alert coverage</strong> — {{ data.coverage.totals.alerts }} alerts walked · {{ data.coverage.totals.cards_seen }} cards · {{ data.coverage.totals.new }} new{% if data.budget %} · JD budget {{ data.budget.used }}/{{ data.budget.limit }}{% if data.budget.queued %} · {{ data.budget.queued }} queued{% endif %}{% endif %}</summary>
<table class="dim-table" style="width:100%;margin-top:8px;font-size:13px;border-collapse:collapse">
  <tr><th style="text-align:left;padding:4px 8px">Alert</th><th style="padding:4px 8px">Pages</th><th style="padding:4px 8px">Stop</th><th style="padding:4px 8px">Cards</th><th style="padding:4px 8px">Exact</th><th style="padding:4px 8px">Known</th><th style="padding:4px 8px">Reposts</th><th style="padding:4px 8px">New</th></tr>
  {% for r in data.coverage.rows %}
  <tr class="dim-row"><td style="padding:4px 8px">{{ r.keywords }}<div style="font-size:11px;color:var(--text-muted)">since {{ r.since }}{% if r.status != 'complete' %} · <strong>partial</strong>{% endif %}</div></td><td style="text-align:center">{{ r.pages_walked }}</td><td style="text-align:center">{{ r.stop_reason or '—' }}</td><td style="text-align:center">{{ r.cards_seen }}</td><td style="text-align:center">{{ r.before_divider }}</td><td style="text-align:center">{{ r.known }}</td><td style="text-align:center">{{ r.reposts }}</td><td style="text-align:center"><strong>{{ r.new }}</strong></td></tr>
  {% endfor %}
</table></details>
{% endif %}
```

(c) Insert immediately before the `{% else %}` on line 69 (i.e. after `</section>`):

```jinja
{% endif %}
{% if data.near_misses %}
<details style="margin:12px 0"><summary><strong>Would you bend?</strong> — {{ data.near_misses|length }} near miss{% if data.near_misses|length != 1 %}es{% endif %}</summary>
<ul>{% for j in data.near_misses %}<li><strong>{{ j.title }}</strong> · {{ j.company }} · {{ j.location }} — would be <strong>{{ j.would_be_tier }}</strong>; failed <strong>{{ j.failed_gate.kind }}</strong>{% if j.failed_gate.detail %} ({{ j.failed_gate.detail }}){% endif %} · <code>{{ j.bend_hint }}</code>{% if j.url %} · <a href="{{ j.url }}" target="_blank" rel="noopener noreferrer">View posting ↗</a>{% endif %}</li>{% endfor %}</ul></details>
{% endif %}
{% if data.queued %}
<details style="margin:12px 0"><summary><strong>Queued for tomorrow</strong> — {{ data.queued|length }} role{% if data.queued|length != 1 %}s{% endif %} over the JD budget</summary>
<ul>{% for j in data.queued %}<li>{{ j.title }} · {{ j.company }} · {{ j.location }}{% if j.url %} · <a href="{{ j.url }}" target="_blank" rel="noopener noreferrer">View posting ↗</a>{% endif %}</li>{% endfor %}</ul></details>
{% endif %}
{% if data.reposts %}
<details style="margin:12px 0"><summary><strong>Treated as reposts</strong> — {{ data.reposts|length }} skipped by fingerprint (both IDs shown; open one if it looks wrong)</summary>
<ul>{% for r in data.reposts %}<li>{{ r.title }} · {{ r.company }} · {{ r.location }} — new id <code>{{ r.id }}</code> matched tracked <code>{{ r.matched_id }}</code></li>{% endfor %}</ul></details>
{% endif %}
{% if data.results %}
```

This keeps the original `{% if data.results %} … {% else %} … {% endif %}` frame intact: the first inserted `{% endif %}` closes the results frame early, the new sections render regardless of results, and the re-opened `{% if data.results %}` immediately precedes the original `{% else %}` so the empty-state still shows when there are no results.

- [ ] **Step 4: Edit the markdown template**

In `skills/_visualizer/templates/markdown/check-job-notifications.md.j2`, insert after the `**Unread:** …` line:

```jinja
{% if data.run_status == 'no_scrape' %}
> ⚠️ **No fresh scrape** — {{ data.no_scrape_reason or 'reason not recorded' }}. The tracker was not modified.
{% endif %}
{% if data.coverage and data.coverage.rows %}
### Alert coverage

{{ data.coverage.totals.alerts }} alerts walked · {{ data.coverage.totals.cards_seen }} cards · {{ data.coverage.totals.new }} new{% if data.budget %} · JD budget {{ data.budget.used }}/{{ data.budget.limit }}{% endif %}

| Alert | Pages | Stop | Cards | Exact | Known | Reposts | New |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
{% for r in data.coverage.rows %}| {{ r.keywords }}{% if r.status != 'complete' %} _(partial)_{% endif %} | {{ r.pages_walked }} | {{ r.stop_reason or '—' }} | {{ r.cards_seen }} | {{ r.before_divider }} | {{ r.known }} | {{ r.reposts }} | **{{ r.new }}** |
{% endfor %}
{% endif %}
```

and append before the final `{% else %}` (the empty-state branch):

```jinja
{% if data.near_misses %}
### Near misses

{% for j in data.near_misses %}- **{{ j.title }}** · {{ j.company }} · {{ j.location }} — would be **{{ j.would_be_tier }}**; failed **{{ j.failed_gate.kind }}**{% if j.failed_gate.detail %} ({{ j.failed_gate.detail }}){% endif %} · `{{ j.bend_hint }}`{% if j.url %} · {{ j.url }}{% endif %}
{% endfor %}
{% endif %}
{% if data.queued %}
### Queued for tomorrow

{% for j in data.queued %}- {{ j.title }} · {{ j.company }} · {{ j.location }}{% if j.url %} · {{ j.url }}{% endif %}
{% endfor %}
{% endif %}
{% if data.reposts %}
### Treated as reposts

{% for r in data.reposts %}- {{ r.title }} · {{ r.company }} · {{ r.location }} — new `{{ r.id }}` matched `{{ r.matched_id }}`
{% endfor %}
{% endif %}
```

- [ ] **Step 5: Document the additive fields**

In `skills/_visualizer/SKILL.md`, after the `### \`ultramode\` payload — additive fields (Phase 14)` section, add:

```markdown
### `check-job-notifications` payload — additive fields (Phase 17)

Produced by `_ultra-engine/scripts/payload_notifications.sh`; templates render each only when present:

- `run_status: "fresh" | "no_scrape"` and `no_scrape_reason` — a `no_scrape` run renders a banner, no results, and still the coverage/gates context.
- `coverage: { rows: [{alert_key, keywords, since, pages_walked, stop_reason, status, cards_seen, before_divider, known, reposts, new}], totals: {…}, reposts_disclosed }` — the per-alert table ("Alert coverage").
- `queued: [{id, title, company, location, url}]` — roles over the JD budget, deferred to the next run.
- `reposts: [{id, matched_id, alert_key, title, company, location}]` — fingerprint drops, disclosed with both ids.
- `near_misses: [...]` — same shape as the `ultramode` rail (`would_be_tier`, `failed_gate`, `bend_hint`).
- `budget: {limit, used, queued}`.
- `results[].source` is the LinkedIn **board string** (`Job Alert | Top Picks | Saved | Similar`), not the structured object — the daily-driver template interpolates it directly.
```

In `skills/shared-references/render-orchestration.md` § Step E table, replace the `check-job-notifications` row with:

```
| `check-job-notifications` | `✓ {{alerts}} alerts walked · {{cards}} cards · {{new}} new — A:{{a}} B:{{b}} C:{{c}} · Filtered:{{d}} · Queued:{{queued}} — report delivered` (or `✓ No fresh scrape — {{reason}} — digest written`) |
```

- [ ] **Step 6: Run the template test; it must pass**

Run: `cd skills/_ultra-engine/tests && python3 -m unittest test_templates_notifications -v`
Expected: 4 tests OK (or `skipped` when Jinja2 is absent — in that case install it and re-run; do not commit on a skip).

- [ ] **Step 7: Suite + commit**

```bash
bash skills/_ultra-engine/tests/run.sh | tail -1   # ALL PASS
git add skills/_visualizer/templates/html/check-job-notifications.html.j2 skills/_visualizer/templates/markdown/check-job-notifications.md.j2 skills/_visualizer/SKILL.md skills/shared-references/render-orchestration.md skills/_ultra-engine/tests/test_templates_notifications.py
git commit -m "Phase 17 Task 11: notifications templates — coverage table, queued, reposts, near-miss rail, no_scrape banner

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---
### Task 12: The command rewrite + browser policy + schema docs + engine contract table

**Files:**
- Rewrite: `skills/check-job-notifications/SKILL.md` (from scratch)
- Modify: `skills/shared-references/browser-policy.md` (two surfaces, ordered; internal endpoints forbidden)
- Modify: `skills/shared-references/canonical-schemas.md` (new `## alerts.json` section; tracker additions `matched_query`, `alert_key`; `config.json` `jd_budget_per_run`)
- Modify: `skills/shared-references/workspace-layout.md` (add `alerts.json` and the digest to the canonical layout)
- Modify: `skills/_ultra-engine/SKILL.md` (table rows for every Phase 17 script)
- Test: `skills/_ultra-engine/tests/test_command_contract.sh`

**Interfaces:**
- Consumes every script from Tasks 1–9 and the agents from Task 10 with the exact calls shown below.
- Produces `$rd/reposts.json` (`[{id, matched_id, alert_key, title, company, location}]`), `$rd/queued.json` (`[{id, title, company, location, url, alert_key}]`), `$rd/sweep-alert-<key>.json`, `$rd/sweep-toppicks.json`, `$rd/sweep-saved.json`, `$rd/sweep-linkedin-similar.json`, `$rd/jd-fetch.json`, `$rd/coverage.json`, `$rd/scorecard.json`, `$rd/payload.json`, the HTML report, and the digest file.

- [ ] **Step 1: Write the contract guard test**

`skills/_ultra-engine/tests/test_command_contract.sh`:

```bash
#!/bin/bash
. "$(dirname "$0")/helpers.sh"
C="$(dirname "$0")/../../check-job-notifications/SKILL.md"
must() { grep -qF -- "$1" "$C"; _report $? "command cites: $1"; }
never() { ! grep -qiF -- "$1" "$C"; _report $? "command never says: $1"; }
grep -q '^disable-model-invocation: true' "$C"; _report $? "disable-model-invocation"
for s in page/notifications.js page/results.js page/toppicks.js page/saved.js alerts_parse.py cards_parse.py walk_stop.py alerts_ledger.py snapshot.sh fingerprint.sh validate_delta.py merge_tracker.py jd_queue.sh checkpoint.sh coverage.py scorecard.sh payload_notifications.sh digest.py; do must "$s"; done
must 'subagent_type: "gate-batch"'; must 'subagent_type: "score-batch"'
must 'jd_budget_per_run'; must 'We found more results'; must 'no_scrape'
never 'voyager'; never 'highlighted in blue'; never 'Scroll 2-3'; never 'Want me to'; never 'ask the user'; never 'my-items/saved-jobs'
[ "$(wc -l < "$C")" -le 230 ]; _report $? "command file stays lean (<=230 lines)"
finish
```

- [ ] **Step 2: Run it to verify it fails** — `bash skills/_ultra-engine/tests/test_command_contract.sh` → fails.

- [ ] **Step 3: Write the new `skills/check-job-notifications/SKILL.md`**

````markdown
---
name: check-job-notifications
description: Walk every LinkedIn job alert to its real end, plus Top Picks and Saved, dedupe against the tracker, read only new descriptions, gate and score them, and deliver the report and phone digest — unattended
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent
disable-model-invocation: true
version: 1.0.0
---

The daily driver. Every mechanical step is one engine script call with a fixed contract; you sequence them, drive the browser, and make exactly two judgement calls (the drift check when a script asks, and nothing else — gating and scoring run in pinned subagents). Never improvise a step, a selector, a cap, or a prompt. Never ask the user anything; this runs unattended.

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

Pick the pane if its `tabs_context` call succeeds; otherwise the extension; otherwise STOP with `no_scrape` reason `browser unavailable`. Page scripts are the files under `$SCRIPTS/page/` pasted **verbatim** into the run-page-script tool. Forbidden: screenshots for discovery, any LinkedIn internal API (Voyager or otherwise), any other automation. A login wall → STOP `no_scrape` reason `linkedin login required`.

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
   c. Dedupe the cards **before the divider** (`before_divider: true`): known = id in snapshot `known_ids`; repost = not known and `bash $SCRIPTS/fingerprint.sh "<company>" "<title>" "<location>"` is in `$rd/fp-45d.json` (append `{id, matched_id: <the tracker id with that fingerprint via jq>, alert_key, title, company, location}` to `$rd/reposts.json`); new = the rest → append `{card…, alert_key}` to `$rd/new-cards.json` (skip ids already there from an earlier alert; first alert wins).
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
````

- [ ] **Step 4: Browser policy edits**

In `skills/shared-references/browser-policy.md`: replace the opening paragraph and Hard rule 1–2 wording so the sanctioned surfaces are "the built-in Claude browser pane (primary) and the Claude Chrome extension (fallback), both Anthropic-operated, both driving the user's own logged-in session". Keep the forbidden list verbatim. Add a new hard rule 4:

```markdown
4. **Never call LinkedIn's internal APIs.** Voyager and any other undocumented endpoint are forbidden even from inside the page context. Job descriptions are read from the rendered page only. Calling internal endpoints at volume from the user's account is the pattern that triggers automated-activity restrictions, and a restricted account ends the job search.
```

Also add to "If a command says 'navigate to X'": *use whichever of the two surfaces the command selected in its adapter step.*

- [ ] **Step 5: Schema and layout docs**

`skills/shared-references/canonical-schemas.md` — add before `## Canonical enums`:

```markdown
## `alerts.json` (alert ledger — Phase 17)

```json
{ "schema_version": 1,
  "alerts": { "<alert_key>": { "keywords": "string", "geo_id": "string", "since_epoch": 1788218797, "since": "ISO8601",
    "params": "string — the alert link's query string minus currentJobId/originToLandingJobPostings",
    "first_seen": "YYYY-MM-DD", "status": "partial | complete", "last_page": 0,
    "stop_reason": "divider | drift | valve | no_next | null",
    "cards_seen": 0, "before_divider": 0, "known": 0, "reposts": 0, "new": 0, "run_id": "string" } } }
```

`alert_key = sha1("<keywords>|<geo_id>|<since_epoch>")[:16]`. Written only by `_ultra-engine/scripts/alerts_ledger.py`. Records older than 30 days are pruned on every run.

**Tracker additions (Phase 17, additive, no bump):** `matched_query` (the alert keywords that surfaced the role), `alert_key`. The daily driver writes the structured `source` (`board ∈ Job Alert | Top Picks | Saved | Similar`).

**`config.json` additions:** `jd_budget_per_run` (integer, default 150) — the per-run cap on job-description reads; overflow is queued to `cache/jd-queue.json`.
```

`skills/shared-references/workspace-layout.md` — add to the canonical layout tree: `alerts.json           # Phase 17 alert ledger — see canonical-schemas.md` and under `reports/`: `check-job-notifications-YYYY-MM-DD-digest.txt   # plain-text phone digest (digest.py)`. Bump the migration note: no workspace version bump (all additive).

- [ ] **Step 6: Engine contract table**

Append to the table in `skills/_ultra-engine/SKILL.md`:

```
| alerts_parse | `python3 $SCRIPTS/alerts_parse.py < notifications-dump.json` | Alert records (key, params, qualifiers, preview ids) from the notifications page dump; dedupes the doubled anchors. |
| cards_parse | `python3 $SCRIPTS/cards_parse.py --surface alert\|toppicks\|saved < page-dump.json` | Card records from a page dump; exit 3 `extractor_mismatch` when a page claims results but yields no cards. |
| walk_stop | `python3 $SCRIPTS/walk_stop.py --alert a.json --page cards.json --page-no N [--valve 10] [--model-says-match true\|false]` | D5 stop rules: divider → valve → no_next → drift (whole page only). |
| alerts_ledger | `python3 $SCRIPTS/alerts_ledger.py plan\|start\|page\|complete\|prune …` | `$WS/alerts.json`: which alerts were walked, how far, why they stopped; resume for partials. |
| coverage | `python3 $SCRIPTS/coverage.py --ledger $WS/alerts.json --run-id R --out $rd/coverage.json [--reposts $rd/reposts.json]` | Per-alert coverage table; `scorecard.sh` embeds it. |
| payload_notifications | `bash $SCRIPTS/payload_notifications.sh $WS/tracker.json $rd <today> fresh\|no_scrape [reason]` | The `check-job-notifications` render payload (ordering, coverage, queued, reposts, near-miss rail, run status). |
| digest | `python3 $SCRIPTS/digest.py --payload $rd/payload.json --profile $WS/user-profile.json --out <digest.txt> [--max-chars 7500] [--last-success DATE]` | Plain-text phone digest with the D11 order and trim rule. |
| migrate_tracker_v3 | `python3 $SCRIPTS/migrate_tracker_v3.py --tracker $WS/tracker.json [--sources $WS/sources.json] [--dry-run]` | One-shot canonicalisation of a drifted tracker; backup first; entry count asserted. |
| page scripts | `$SCRIPTS/page/{notifications,results,toppicks,saved}.js` | The exact in-page scripts pasted into the browser surface; anchors from the Phase 17 evidence file only. |
```

- [ ] **Step 7: Run the contract test and the suite; commit**

```bash
bash skills/_ultra-engine/tests/test_command_contract.sh | tail -1   # fails=0
bash skills/_ultra-engine/tests/run.sh | tail -1                     # ALL PASS
git add skills/check-job-notifications/SKILL.md skills/shared-references/browser-policy.md skills/shared-references/canonical-schemas.md skills/shared-references/workspace-layout.md skills/_ultra-engine/SKILL.md skills/_ultra-engine/tests/test_command_contract.sh
git commit -m "Phase 17 Task 12: check-job-notifications rewritten on the engine spine; two-surface browser policy; alerts.json schema

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

- [ ] **Step 8: Live dry walk (read-only, one alert)**

With the built-in browser pane, execute Steps 2–3 by hand for ONE alert against a scratch copy of the workspace (`cp -R "$WS" /tmp/ws-scratch`), with `WS` pointed at the copy. Confirm: `alerts.json` gains one `complete` record with `stop_reason: divider`, `coverage.json` shows `known + reposts + new == before_divider`, and `reposts.json` names both ids for any fingerprint drop. Note the numbers in the ROADMAP log at Task 15.

---
### Task 13: The rewritten Cowork scheduled task (D16)

**Files:**
- Create: `docs/scheduled-tasks/freelancer-daily-scan.md`

**Interfaces:**
- Consumes: the digest file written by the command (Task 12) at `.job-scout/reports/check-job-notifications-<date>-digest.txt` and the command's printed summary.
- Produces: the text the user pastes into the Cowork scheduled task. No gates, no process description.

- [ ] **Step 1: Write the document**

`docs/scheduled-tasks/freelancer-daily-scan.md`:

````markdown
# Scheduled task — Freelancer daily job scan

Paste the block below as the task's instructions. It replaces the 2026-08-31 version, which restated the gates and described a re-ranking fallback; both now live in the plugin (`user-profile.json` holds the gates; the command writes a `no_scrape` digest when the browser is unavailable).

Schedule: nightly, 03:10 Europe/Amsterdam. Folder: `~/CoWork/CVFREELANCER`. Model for the task session: Sonnet is sufficient (the command sequences scripts; gating and scoring run in pinned subagents).

```
Freelancer daily job scan

1. In the CVFREELANCER folder, run the linkedin-job-hunter `/check-job-notifications` command. Do not add instructions about how the scan works, which gates apply, or what to do if the browser is missing — the command handles all of that and never asks questions.

2. When it finishes, read the digest file it names in its summary: `.job-scout/reports/check-job-notifications-<today>-digest.txt`. If the summary reports a `no_scrape` status, the digest already says so — use it as-is.

3. Create one Google Calendar event on my primary calendar (create_event):
   - summary: the digest's first line, shortened to at most 80 characters, prefixed "Freelancer scan <today> — ".
   - description: the digest file's full text, verbatim. Plain text, bare URLs, no formatting added.
   - startTime: 5 minutes after now; endTime: 20 minutes after now; timeZone: "Europe/Amsterdam".
   - overrideReminders: [ { "method": "popup", "minutes": 0 } ]. No attendees.

4. Print inline: the command's summary line and its per-role direct-link lines. Do not open the report in a browser.
```

## Why this shape

- One process description exists, in the plugin. The task prompt never restates it, so nothing can drift.
- A missing browser produces a short, honest event ("NO FRESH SCRAPE — …") and no tracker writes, instead of a costly re-rank of yesterday's jobs.
- The digest's size and order are produced by `digest.py` under test, not improvised per night.
````

- [ ] **Step 2: Commit**

```bash
git add docs/scheduled-tasks/freelancer-daily-scan.md
git commit -m "Phase 17 Task 13: rewritten nightly scheduled-task prompt (digest-driven, no restated gates)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 14: Migrate the live trackers (D15) — dry-run, then live, both workspaces

**Files:** none in the repo. Touches `~/Library/Mobile Documents/com~apple~CloudDocs/CoWork/CVFREELANCER/.job-scout/tracker.json` and the CVDIRECTOR workspace's tracker (ask the user for its path if it is not at `~/Library/Mobile Documents/com~apple~CloudDocs/CoWork/CVDIRECTOR/.job-scout/`).

- [ ] **Step 1: Dry-run on the freelance workspace and record the summary**

```bash
WS="$HOME/Library/Mobile Documents/com~apple~CloudDocs/CoWork/CVFREELANCER/.job-scout"
python3 skills/_ultra-engine/scripts/migrate_tracker_v3.py --tracker "$WS/tracker.json" --sources "$WS/sources.json" --dry-run
```

Expected: `"entries": 4049` (or the current count), `"dry_run": true`, a non-zero `changed`, and no change to the file's mtime.

- [ ] **Step 2: Live run, then assert**

```bash
WS="$HOME/Library/Mobile Documents/com~apple~CloudDocs/CoWork/CVFREELANCER/.job-scout"
before=$(jq '.jobs|length' "$WS/tracker.json")
python3 skills/_ultra-engine/scripts/migrate_tracker_v3.py --tracker "$WS/tracker.json" --sources "$WS/sources.json"
after=$(jq '.jobs|length' "$WS/tracker.json"); echo "before=$before after=$after"
jq -r '[.jobs[] | .source | type] | group_by(.) | map("\(.[0]) \(length)") | join(", ")' "$WS/tracker.json"    # expect: object N only
jq -r '[.jobs[] | .status] | unique | join(",")' "$WS/tracker.json"                                             # expect: canonical statuses only
jq -r '[.jobs[] | .first_seen | test("T")] | any' "$WS/tracker.json"                                            # expect: false
ls "$WS/.backup/" | grep pre-phase17
```

Expected: `before == after`; only `object` sources; only canonical statuses; `false`; one backup file.

- [ ] **Step 3: Repeat Steps 1–2 for the CVDIRECTOR workspace**

Same commands with `WS` pointing at that workspace. If the folder does not exist, record "CVDIRECTOR not present on this machine" in the ROADMAP log (Task 15) instead of skipping silently.

- [ ] **Step 4: Remove the stale engine copy from the workspace**

```bash
WS="$HOME/Library/Mobile Documents/com~apple~CloudDocs/CoWork/CVFREELANCER/.job-scout"
[ -d "$WS/engine-scripts" ] && mv "$WS/engine-scripts" "$WS/.backup/engine-scripts.2026-07-15.stale"
```

Then remove the `engine-scripts/` row from `~/Library/Mobile Documents/com~apple~CloudDocs/CoWork/CVFREELANCER/README.md`'s "What is where" table (it is not a repo file; edit in place).

- [ ] **Step 5: Record the outcome**

No commit for this task. Paste the three summaries (dry-run, live freelance, live director) into the Task 15 ROADMAP log entry.

---
### Task 15: Release v0.17.0 — version, CHANGELOG, ROADMAP, README, QUICKSTART

**Files:**
- Modify: `.claude-plugin/plugin.json` (version `0.17.0`)
- Modify: `CHANGELOG.md` (new top section)
- Modify: `docs/ROADMAP.md` (status table row, "Current focus" paragraph, Phase 17 section, Log entry)
- Modify: `README.md`, `QUICKSTART.md` (daily-driver description; built-in browser wording)

- [ ] **Step 1: Bump the version**

In `.claude-plugin/plugin.json` change `"version": "0.16.0"` to `"version": "0.17.0"`.

- [ ] **Step 2: CHANGELOG section (insert above `## [0.16.0]`)**

```markdown
## [0.17.0] — <release date>

### Added
- **The alert walk** — `/check-job-notifications` now parses every job alert from the notifications page in one read and walks each alert's results pages until LinkedIn's "We found more results…" divider (or a whole drifted page, or a 10-page valve), so every exact-match listing is seen. A single alert on 2026-09-02 held 24 exact matches of which the old command saw 10.
- **Alert ledger** (`.job-scout/alerts.json`) — which alerts were walked, how far, and why they stopped; partial walks resume; completed alerts are never re-walked.
- **Per-alert coverage table** in the report and scorecard: cards seen, exact matches, known, reposts, new, pages, stop reason.
- **Phone digest** (`reports/check-job-notifications-<date>-digest.txt`) — plain text, bare URLs, trimmed to 7,500 characters, produced by `digest.py`; the nightly calendar event is built from it.
- **JD budget with carry-over** — 150 descriptions per run (`config.json` `jd_budget_per_run`); overflow is queued and listed as "Queued for tomorrow", never dropped.
- **Pinned-model subagents** — `gate-batch` (Sonnet) and `score-batch` (Opus) shipped under `agents/`.
- **Engine scripts**: `alerts_parse.py`, `cards_parse.py`, `walk_stop.py`, `alerts_ledger.py`, `coverage.py`, `payload_notifications.sh`, `digest.py`, `migrate_tracker_v3.py`, and the four in-page scripts under `scripts/page/`, all under `tests/run.sh`.

### Changed
- **Browser surfaces**: the built-in browser pane is primary, the Chrome extension is the fallback; discovery reads pages through in-page scripts, never screenshots. Internal LinkedIn endpoints (Voyager) are explicitly forbidden.
- `/check-job-notifications` is **unattended by design** — no prompts in any mode; a missing workspace, profile, or browser is a disclosed `no_scrape` stop with a digest, never a re-rank of old jobs.
- Fingerprint (repost) dedupe now matches only entries seen in the last 45 days and every drop is disclosed with both ids.
- Saved jobs are read from LinkedIn's Job tracker page (the old `/my-items/saved-jobs/` URL redirects there). The interactive second Top Picks sweep is removed.
- The daily driver writes the structured `source` object (closing the long-deferred item).

### Fixed
- The daily driver treated each alert's six-id link preview as the alert's full contents — the root cause of silently skipped roles.
- Live trackers canonicalised by `migrate_tracker_v3.py` (free-text sources, `gated` status, string gate violations, mixed date formats).
```

- [ ] **Step 3: ROADMAP**

Add a row to the status table:

```
| **17. The alert walk — deterministic job-alert discovery** | v0.17.0 | Built — live acceptance pending | [`specs/2026-09-02-phase-17-alert-walk-design.md`](superpowers/specs/2026-09-02-phase-17-alert-walk-design.md) | [`plans/2026-09-02-phase-17-alert-walk.md`](superpowers/plans/2026-09-02-phase-17-alert-walk.md) |
```

Prepend to the **Current focus** paragraph: `**Phase 17 (The alert walk, v0.17.0) is built — live acceptance pending** (spec §6: suite ALL PASS, both trackers migrated, one nightly-equivalent run with a coverage table that matches a manual count on two alerts, zero exact matches missing on the measured alert, digest + calendar event, one deliberate no-browser run). ` Add a `## Phase 17 — v0.17.0: The alert walk` section listing Tasks 1–15 as checkboxes, and a Log entry dated with the release date that records: the before-number (10 of 24 on the `linux engineer Contract Remote` alert of 2026-08-31T23:26Z), the migration summaries from Task 14, and that the `/ultramode` + `/job-search` extractor wiring is the named follow-on (D17). Remove the sentence about the daily driver's structured-source conversion being deferred.

- [ ] **Step 4: README and QUICKSTART**

In both files, wherever `/check-job-notifications` is described, state: it walks every alert to the divider, keeps an alert ledger and a coverage table, writes a phone digest, runs unattended, and uses the built-in browser pane first with the Chrome extension as fallback. Replace any sentence that says the Chrome extension is the only browser surface with the two-surface wording. Add the `jd_budget_per_run` config key to the config table in README.

- [ ] **Step 5: Verify docs and commit**

```bash
grep -n '"version"' .claude-plugin/plugin.json          # 0.17.0
grep -n '0.17.0' CHANGELOG.md docs/ROADMAP.md | head
bash skills/_ultra-engine/tests/run.sh | tail -1        # ALL PASS
git add .claude-plugin/plugin.json CHANGELOG.md docs/ROADMAP.md README.md QUICKSTART.md
git commit -m "Phase 17 Task 15: docs + release v0.17.0 (live acceptance pending)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

- [ ] **Step 6: Hand over for live acceptance (user-run, spec §6)**

Do not merge to `main` until the six acceptance items in the spec pass on the CVFREELANCER workspace. Record results in the ROADMAP log, then merge with `git checkout main && git merge --no-ff phase-17/build` and tag `v0.17.0`.

---

## Self-review

**Spec coverage.** D1 → Tasks 2, 5. D2/D3 → Task 12 (browser policy + adapter). D4 → Task 1. D5 → Task 3 (+ the model-check hook in Task 12 Step 3). D6 → Task 4. D7 → Task 12 Step 3 (45-day window computed in the snapshot filter; reposts.json). D8 → Task 12 Step 4 (jd_queue push/pop; `jd_budget_per_run`). D9 → Task 12 Steps 3–7. D10 → Task 12 Step 0 + failure table. D11 → Tasks 6, 7, 8, 11. D12 → Tasks 1–9 + engine SKILL.md rows in Task 12. D13 → Task 12. D14 → Task 10. D15 → Tasks 9, 14. D16 → Task 13. D17 → recorded in Task 15 ROADMAP text. D18 → Task 15 Step 6. Spec §3 `coverage.py` folded into scorecard → Task 6. Spec §4 schemas → Task 12 Step 5 (canonical-schemas + workspace-layout). Spec §6 acceptance → Task 15 Step 6.

**Type consistency.** `alert_key` (16 hex) flows Task 1 → 4 → 6 → 12; card record keys (`id, title, company, location, workplace, salary_text, posted_ago, viewed, promoted, easy_apply, early_applicant, before_divider`) flow Task 2 → 3 → 12; page dump keys (`surface, url, claimed_results, page, cards, divider_index, has_next, saved_count`) flow Task 5 → 2; `reposts.json` entries `{id, matched_id, alert_key, title, company, location}` flow Task 12 → 6 → 7 → 11; `queued.json` entries `{id, title, company, location, url, alert_key}` flow Task 12 → 7 → 8 → 11; scorecard `coverage`/`budget` keys flow Task 6 → 7 → 8. Subagent names `gate-batch`/`score-batch` and their delta shapes match between Task 10 and Task 12.

**Placeholders.** None remain: every code step is complete; the only user-supplied values are the release date and the CVDIRECTOR path, both marked explicitly.

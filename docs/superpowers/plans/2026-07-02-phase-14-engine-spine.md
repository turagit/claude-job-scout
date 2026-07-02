# Phase 14 — Deterministic Engine Spine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move every mechanical operation of the ultramode pipeline (snapshots, fingerprints, IDs, delta validation, tracker merges, rotation, JD budgeting, checkpoints, scorecard, payload assembly) into version-controlled, tested scripts inside a new internal `_ultra-engine` skill, so the model spends judgement only where judgement is the job.

**Architecture:** A new `skills/_ultra-engine/` skill ships `scripts/` (bash + jq, python3 stdlib for merge/validation) with a self-contained test suite. `_source-sweep` gains verbatim prompt templates. `/ultramode`'s Step 4 is rewritten to *drive* the scripts instead of describing behaviour in prose. `_gate-engine`/`_job-matcher` gain the near-miss rule and the jd_path requirement; `_visualizer` gains the near-miss rail + scorecard strip; a tiny `/bend` command lands. Command topology does not change in this phase.

**Tech Stack:** bash (macOS 3.2-compatible: no associative arrays, no `${var,,}`), `jq` (already a hard dependency of this repo's validators), python3 stdlib only. No new installs.

## Global Constraints

- Spec: `docs/superpowers/specs/2026-07-02-phase-14-15-engine-spine-and-merge-design.md` — decisions D1–D14 govern; implementation calls §5 apply verbatim.
- **IDs are immutable forever.** No script or skill ever rewrites an existing tracker entry's `id`. External IDs: `<provider>__<board>__<externalid>`, slugs `[a-z0-9-]` (no underscores), `__` the only separator. LinkedIn IDs stay bare numeric. (canonical-schemas.md § Namespaced external IDs)
- **Structured `source` on every new write:** `{lane, provider, board}`. Legacy string sources are parsed on read only (shim), never written. Tracker `schema_version` bumps 2→3 on first structured write (lazy upgrade — no destructive rewrite).
- **Atomic writes everywhere:** write `<file>.tmp`, validate with `jq -e`, `mv` over the original (state-validators.md). On validation failure: leave state untouched, print the violating field, never best-effort save.
- **All state lives under `.job-scout/`** in the *workspace* (never in the plugin repo; `.gitignore` already covers it). Scripts take the workspace dir explicitly; default `${JOB_SCOUT_DIR:-.job-scout}`.
- **No silent caps:** every truncation, skip, or budget hit must appear in the return envelope / scorecard.
- **British English** in all user-facing copy; identifiers exempt. New user-invocable command (`/bend`) carries `disable-model-invocation: true`.
- **No browser-automation frameworks**; nothing here touches the browser — that stays in the command skills via the Chrome extension.
- Commit messages: `Phase 14 Task N: <summary>`, ending with the Co-Authored-By/Claude-Session footer the harness mandates.
- Run all tests from the repo root with: `bash skills/_ultra-engine/tests/run.sh` — expected final line `ALL PASS`.

## File Structure (locked)

```
skills/_ultra-engine/
  SKILL.md                      # internal skill; documents every script contract (Task 12)
  scripts/
    lib/fingerprint.jq          # THE fingerprint + location normalisation (single implementation)
    fingerprint.sh              # CLI wrapper over lib/fingerprint.jq
    namespace_id.sh             # provider/board/external-id -> namespaced id (+ deterministic URL fallback)
    snapshot.sh                 # tracker.json -> cache/ultramode-snapshot.json
    validate_delta.py           # sweep-envelope validator (pre-merge)
    merge_tracker.py            # serial, schema-validating, atomic tracker merge + canonical selection
    rotation.sh                 # staleness-ordered extension-lane pick + last_swept_at bookkeeping
    jd_queue.sh                 # deferred JD-fetch queue with budget accounting
    checkpoint.sh               # run-dir stage manifest: init/save/done/find-incomplete
    scorecard.sh                # run-dir checkpoints -> scorecard.json
    payload.sh                  # tracker + run-dir -> render payload (ordering, near-miss rail, disclosures)
  tests/
    run.sh                      # the runner (bash tests + python unittest)
    helpers.sh                  # assert helpers
    fixtures/                   # mini tracker/deltas/sources fixtures (created per task)
    test_fingerprint.sh  test_namespace_id.sh  test_snapshot.sh  test_rotation.sh
    test_jd_queue.sh  test_checkpoint.sh  test_scorecard.sh  test_payload.sh
    test_validate_delta.py  test_merge_tracker.py
skills/_source-sweep/references/
  prompt-api.md  prompt-rss.md  prompt-html.md   # verbatim templates (Task 13)
skills/bend/SKILL.md            # /bend command (Task 17)
```

Modified: `skills/_source-sweep/SKILL.md`, `skills/ultramode/SKILL.md`, `skills/_gate-engine/SKILL.md` (+ its gate-rules reference), `skills/_job-matcher/SKILL.md`, `skills/_visualizer/SKILL.md` + `templates/html/ultramode.html.j2` + `templates/markdown/ultramode.md.j2` + `references/component-library.md`, `skills/shared-references/canonical-schemas.md` (additive fields), `CLAUDE.md`, `.claude-plugin/plugin.json`, `CHANGELOG.md`, `README.md`, `docs/ROADMAP.md`.

---

### Task 1: `_ultra-engine` skeleton + test harness

**Files:**
- Create: `skills/_ultra-engine/SKILL.md` (stub — full contracts land in Task 12)
- Create: `skills/_ultra-engine/tests/run.sh`, `skills/_ultra-engine/tests/helpers.sh`

**Interfaces:**
- Produces: `run.sh` (runs every `tests/test_*.sh` + `python3 -m unittest discover`), `helpers.sh` exporting `assert_eq`, `assert_ok`, `assert_fail`, `assert_json_eq`, and `fail_count` bookkeeping. All later tasks rely on these exact names.

- [ ] **Step 1: Write the harness and a self-test**

`skills/_ultra-engine/tests/helpers.sh`:
```bash
#!/bin/bash
# Test helpers for _ultra-engine. Source me. bash-3.2 compatible.
FAILS=0; CHECKS=0
_report() { CHECKS=$((CHECKS+1)); if [ "$1" -ne 0 ]; then FAILS=$((FAILS+1)); echo "  FAIL: $2"; else echo "  ok: $2"; fi; }
assert_eq()  { [ "$1" = "$2" ]; _report $? "${3:-expected [$1] got [$2]} (want='$1' got='$2')"; }
assert_ok()  { "$@" >/dev/null 2>&1; _report $? "exit0: $*"; }
assert_fail(){ "$@" >/dev/null 2>&1; [ $? -ne 0 ]; _report $? "nonzero-exit: $*"; }
assert_json_eq() {
  local want got
  want=$(printf '%s' "$1" | jq -Se . 2>/dev/null) || { _report 1 "${3:-json}: want side unparseable"; return; }
  got=$(printf '%s' "$2" | jq -Se . 2>/dev/null) || { _report 1 "${3:-json}: got side unparseable"; return; }
  [ "$want" = "$got" ]; _report $? "${3:-json mismatch}"
}
finish() { echo "checks=$CHECKS fails=$FAILS"; [ "$FAILS" -eq 0 ]; }
```

`skills/_ultra-engine/tests/run.sh`:
```bash
#!/bin/bash
# Runs the whole _ultra-engine suite. Usage: bash skills/_ultra-engine/tests/run.sh
set -u
cd "$(dirname "$0")" || exit 1
command -v jq >/dev/null || { echo "jq is required"; exit 1; }
command -v python3 >/dev/null || { echo "python3 is required"; exit 1; }
total_fail=0
for t in test_*.sh; do
  [ -e "$t" ] || continue
  echo "== $t"
  bash "$t" || total_fail=$((total_fail+1))
done
if ls test_*.py >/dev/null 2>&1; then
  echo "== python unittests"
  python3 -m unittest discover -s . -p 'test_*.py' -v 2>&1 | tail -3
  python3 -m unittest discover -s . -p 'test_*.py' >/dev/null 2>&1 || total_fail=$((total_fail+1))
fi
[ "$total_fail" -eq 0 ] && echo "ALL PASS" || { echo "SUITES FAILED: $total_fail"; exit 1; }
```

`skills/_ultra-engine/SKILL.md` (stub):
```markdown
---
name: _ultra-engine
description: Internal deterministic engine for the ultramode pipeline — scripts for snapshots, fingerprints, IDs, delta validation, tracker merges, rotation, JD budgeting, checkpoints, scorecard, and payload assembly. Loaded by orchestrator skills; never user-invoked.
allowed-tools: Read, Bash, Grep, Glob
disable-model-invocation: true
version: 0.1.0
---

Scripts live in `scripts/`; every contract is documented here (Phase 14 Task 12 fills this file). Tests: `bash tests/run.sh` → `ALL PASS`.
```

- [ ] **Step 2: Run the suite — expect green (zero suites)**

Run: `bash skills/_ultra-engine/tests/run.sh`
Expected: `ALL PASS` (no test files yet — the harness itself must run).

- [ ] **Step 3: Commit**

```bash
git add skills/_ultra-engine
git commit -m "Phase 14 Task 1: _ultra-engine skeleton + test harness"
```

---

### Task 2: fingerprint (single implementation)

**Files:**
- Create: `skills/_ultra-engine/scripts/lib/fingerprint.jq`, `skills/_ultra-engine/scripts/fingerprint.sh`
- Test: `skills/_ultra-engine/tests/test_fingerprint.sh`

**Interfaces:**
- Produces: jq functions `norm_loc` and `fp($company; $title; $location)` (import path `lib`, module name `fingerprint`); CLI `fingerprint.sh <company> <title> <location>` printing the fingerprint to stdout. Format: `lower(company)|lower(title)|normalise_location(location)`; normalise_location = lowercase → strip the words area/region/greater/metropolitan → strip punctuation → collapse whitespace → trim. Consumed by Tasks 4, 5, 6.

- [ ] **Step 1: Write the failing test**

`skills/_ultra-engine/tests/test_fingerprint.sh`:
```bash
#!/bin/bash
. "$(dirname "$0")/helpers.sh"
FP="$(dirname "$0")/../scripts/fingerprint.sh"
assert_eq "acme gmbh|senior platform engineer|berlin" "$(bash "$FP" "Acme GmbH" "Senior Platform Engineer" "Berlin")" "basic"
assert_eq "acme|sre|amsterdam" "$(bash "$FP" "ACME" "SRE" "Greater Amsterdam Area")" "strips greater/area"
assert_eq "n26|iam engineer|berlin metropolitan" "$(bash "$FP" "N26" "IAM  Engineer" "Berlin, Metropolitan-Region!")" "punctuation + collapse; keeps non-listed words"
assert_eq "globex|devops|" "$(bash "$FP" "Globex" "DevOps" "")" "empty location"
finish
```
Note the third case: `metropolitan` is a listed strip-word — expected is `berlin metropolitan`? No — listed words are stripped, so expected must be `n26|iam engineer|berlin`. Use exactly:
```bash
assert_eq "n26|iam engineer|berlin" "$(bash "$FP" "N26" "IAM  Engineer" "Berlin, Metropolitan-Region!")" "punctuation + collapse + strip-words"
```

- [ ] **Step 2: Run to verify it fails**

Run: `bash skills/_ultra-engine/tests/test_fingerprint.sh`
Expected: FAIL lines (script not found → empty output).

- [ ] **Step 3: Implement**

`skills/_ultra-engine/scripts/lib/fingerprint.jq`:
```jq
# THE canonical cross-source fingerprint. Single implementation — every
# consumer (snapshot, validator, merge) calls these, never re-derives.
def squeeze: gsub("\\s+"; " ") | sub("^ "; "") | sub(" $"; "");
def norm_loc:
  ascii_downcase
  | gsub("[^a-z0-9 ]"; " ")
  | gsub("\\b(area|region|greater|metropolitan)\\b"; " ")
  | squeeze;
def fp($c; $t; $l):
  ($c | ascii_downcase | squeeze) + "|" + ($t | ascii_downcase | squeeze) + "|" + ($l | norm_loc);
```

`skills/_ultra-engine/scripts/fingerprint.sh`:
```bash
#!/bin/bash
# Usage: fingerprint.sh <company> <title> <location>   -> prints fingerprint
set -u
d="$(cd "$(dirname "$0")" && pwd)"
jq -nr -L "$d/lib" --arg c "${1-}" --arg t "${2-}" --arg l "${3-}" 'include "fingerprint"; fp($c; $t; $l)'
```

- [ ] **Step 4: Run to verify it passes**

Run: `bash skills/_ultra-engine/tests/test_fingerprint.sh` → `checks=4 fails=0`. Then `bash skills/_ultra-engine/tests/run.sh` → `ALL PASS`.

- [ ] **Step 5: Commit**

```bash
git add skills/_ultra-engine
git commit -m "Phase 14 Task 2: canonical fingerprint lib + CLI"
```

---

### Task 3: namespace_id

**Files:**
- Create: `skills/_ultra-engine/scripts/namespace_id.sh`
- Test: `skills/_ultra-engine/tests/test_namespace_id.sh`

**Interfaces:**
- Produces: `namespace_id.sh <provider> <board> <external_id>` → `provider__board__externalid`; `namespace_id.sh --from-url <provider> <board> <url>` → deterministic fallback id (12 hex chars of sha256 of the normalised URL: lowercase, strip trailing `/`, strip query+fragment). Slugs normalised to `[a-z0-9-]` (underscores in the raw external id are preserved — only *slugs* forbid `_`). Consumed by Task 13 templates and Task 15.

- [ ] **Step 1: Write the failing test**

`skills/_ultra-engine/tests/test_namespace_id.sh`:
```bash
#!/bin/bash
. "$(dirname "$0")/helpers.sh"
NS="$(dirname "$0")/../scripts/namespace_id.sh"
assert_eq "greenhouse__miro__4012345" "$(bash "$NS" Greenhouse MIRO 4012345)" "slugifies provider+board"
assert_eq "it-contracts-nl__it-contracts-nl__abc-9" "$(bash "$NS" "IT-Contracts.nl" "IT-Contracts.nl" "abc-9")" "dots to dashes"
a=$(bash "$NS" --from-url remoteok remoteok "https://remoteok.com/remote-jobs/998877?ref=x")
b=$(bash "$NS" --from-url remoteok remoteok "https://remoteok.com/remote-jobs/998877/")
assert_eq "$a" "$b" "url fallback deterministic across query/trailing-slash"
case "$a" in remoteok__remoteok__????????????) _report 0 "fallback shape";; *) _report 1 "fallback shape: $a";; esac
finish
```

- [ ] **Step 2: Run to verify it fails** — `bash skills/_ultra-engine/tests/test_namespace_id.sh` → FAILs.

- [ ] **Step 3: Implement**

`skills/_ultra-engine/scripts/namespace_id.sh`:
```bash
#!/bin/bash
# Usage: namespace_id.sh <provider> <board> <external_id>
#        namespace_id.sh --from-url <provider> <board> <url>
set -u
slug() { printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9-]+/-/g; s/-+/-/g; s/^-+//; s/-+$//'; }
if [ "${1-}" = "--from-url" ]; then
  p=$(slug "$2"); b=$(slug "$3")
  u=$(printf '%s' "$4" | tr '[:upper:]' '[:lower:]' | sed -E 's/[?#].*$//; s:/+$::')
  h=$(printf '%s' "$u" | shasum -a 256 | cut -c1-12)
  printf '%s__%s__%s\n' "$p" "$b" "$h"
else
  p=$(slug "$1"); b=$(slug "$2")
  e=$(printf '%s' "$3" | sed -E 's/[[:space:]]+//g')
  printf '%s__%s__%s\n' "$p" "$b" "$e"
fi
```

- [ ] **Step 4: Run to verify it passes** — test file → `fails=0`; `run.sh` → `ALL PASS`.

- [ ] **Step 5: Commit** — `git add skills/_ultra-engine && git commit -m "Phase 14 Task 3: namespace_id script"`

---

### Task 4: snapshot

**Files:**
- Create: `skills/_ultra-engine/scripts/snapshot.sh`
- Test: `skills/_ultra-engine/tests/test_snapshot.sh`, fixture `skills/_ultra-engine/tests/fixtures/tracker-mini.json`

**Interfaces:**
- Produces: `snapshot.sh <tracker.json> <out.json>` → writes `{generated_at, known_ids: [...], known_fingerprints: [...]}` from every non-`rejected` entry; fingerprints via `lib/fingerprint.jq`. Consumed by the ultramode dispatcher (Task 15) and the sweep templates (Task 13) which pass the snapshot *path* to subagents (blessing the pattern the 2026-07-02 run improvised).

- [ ] **Step 1: Fixture + failing test**

`skills/_ultra-engine/tests/fixtures/tracker-mini.json`:
```json
{
  "schema_version": 3, "version": 2,
  "stats": {"total_seen": 3, "applied": 0, "rejected": 1, "last_run": null, "last_search": null, "last_archive_pass": null, "last_deep_sweep": null},
  "jobs": {
    "4001": {"id": "4001", "url": "https://l/4001", "title": "Senior SRE", "company": "Acme", "location": "Amsterdam", "source": {"lane": "linkedin", "provider": "linkedin", "board": "Search"}, "tier": "B", "status": "seen", "first_seen": "2026-06-01", "last_seen": "2026-06-28", "jd_path": null, "notes": ""},
    "4002": {"id": "4002", "url": "https://l/4002", "title": "DevOps Engineer", "company": "Globex", "location": "Greater Berlin Area", "source": "ultramode 2026-06-16 [Search]", "tier": "C", "status": "rejected", "first_seen": "2026-06-01", "last_seen": "2026-06-01", "jd_path": null, "notes": ""},
    "greenhouse__miro__7": {"id": "greenhouse__miro__7", "url": "https://g/7", "title": "Platform Engineer", "company": "Miro", "location": "Remote", "source": {"lane": "ats", "provider": "greenhouse", "board": "miro"}, "tier": "A", "status": "seen", "first_seen": "2026-06-10", "last_seen": "2026-06-28", "jd_path": "jds/greenhouse__miro__7.txt", "notes": ""}
  }
}
```

`skills/_ultra-engine/tests/test_snapshot.sh`:
```bash
#!/bin/bash
. "$(dirname "$0")/helpers.sh"
S="$(dirname "$0")/../scripts/snapshot.sh"; FX="$(dirname "$0")/fixtures/tracker-mini.json"
out=$(mktemp); bash "$S" "$FX" "$out"
assert_eq "2" "$(jq '.known_ids|length' "$out")" "rejected excluded from ids"
assert_eq "true" "$(jq '.known_ids|index("4001") != null' "$out")" "linkedin id present"
assert_eq "true" "$(jq '.known_fingerprints|index("acme|senior sre|amsterdam") != null' "$out")" "fingerprint computed"
assert_eq "true" "$(jq '.known_fingerprints|index("miro|platform engineer|remote") != null' "$out")" "external fingerprint"
assert_ok jq -e '.generated_at|length > 0' "$out"
rm -f "$out"; finish
```

- [ ] **Step 2: Run to verify it fails.**

- [ ] **Step 3: Implement**

`skills/_ultra-engine/scripts/snapshot.sh`:
```bash
#!/bin/bash
# Usage: snapshot.sh <tracker.json> <out.json>
# Builds the dedupe snapshot every sweep reads: non-rejected ids + fingerprints.
set -eu
d="$(cd "$(dirname "$0")" && pwd)"
tracker="$1"; out="$2"
jq -L "$d/lib" --arg now "$(date -u +%FT%TZ)" '
  include "fingerprint";
  [ .jobs | to_entries[] | .value | select((.status // "seen") != "rejected") ] as $live
  | { generated_at: $now,
      known_ids: [ $live[].id ],
      known_fingerprints: [ $live[] | fp((.company // ""); (.title // ""); (.location // "")) ] | unique }
' "$tracker" > "$out.tmp" && jq -e . "$out.tmp" >/dev/null && mv "$out.tmp" "$out"
```

- [ ] **Step 4: Run to verify it passes** — test + `run.sh` → `ALL PASS`.

- [ ] **Step 5: Commit** — `git add skills/_ultra-engine && git commit -m "Phase 14 Task 4: snapshot script"`

---

### Task 5: validate_delta.py

**Files:**
- Create: `skills/_ultra-engine/scripts/validate_delta.py`
- Test: `skills/_ultra-engine/tests/test_validate_delta.py`, fixture `skills/_ultra-engine/tests/fixtures/delta-good.json`

**Interfaces:**
- Produces: `python3 validate_delta.py --ws <workspace> <delta.json>` — exit 0 valid / exit 1 with one violation per stderr line. Validates the Phase 14 envelope: `{status, deltas[], errors[], counts, continuation_cursor}` where `counts = {scanned, matched, dropped_explicit_violation, returned, capped}` (the **no-silent-caps disclosure** — `capped: true` whenever `returned < matched - dropped_explicit_violation`). Each delta entry requires: `id` (external-namespaced or bare-numeric), `url`, `title`, `company`, `location` (may be "" ), structured `source` object with non-empty `lane`/`provider`/`board`, `fingerprint` containing exactly 2 `|`, `posted_at` (`YYYY-MM-DD` or ""), and `jd_path` which must exist under `--ws` when non-null. Consumed by Task 6 (merge refuses unvalidated input) and Task 15.

- [ ] **Step 1: Fixture + failing test**

`skills/_ultra-engine/tests/fixtures/delta-good.json`:
```json
{
  "status": "ok",
  "counts": {"scanned": 40, "matched": 6, "dropped_explicit_violation": 3, "returned": 2, "capped": true},
  "deltas": [
    {"id": "remotive__remotive__555", "url": "https://r/555", "title": "Platform Engineer", "company": "Initech", "location": "Remote", "source": {"lane": "remote-board", "provider": "remotive", "board": "remotive"}, "fingerprint": "initech|platform engineer|remote", "posted_at": "2026-07-01", "jd_path": "jds/remotive__remotive__555.txt", "tags": ["kubernetes"]}
  ],
  "errors": [], "continuation_cursor": null
}
```

`skills/_ultra-engine/tests/test_validate_delta.py`:
```python
import json, os, subprocess, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "scripts", "validate_delta.py")

def run(ws, payload):
    f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    json.dump(payload, f); f.close()
    p = subprocess.run(["python3", SCRIPT, "--ws", ws, f.name], capture_output=True, text=True)
    os.unlink(f.name); return p

class T(unittest.TestCase):
    def setUp(self):
        self.ws = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.ws, "jds"))
        with open(os.path.join(HERE, "fixtures", "delta-good.json")) as fh:
            self.good = json.load(fh)
        open(os.path.join(self.ws, "jds", "remotive__remotive__555.txt"), "w").write("full jd text")

    def test_good_passes(self):
        self.assertEqual(run(self.ws, self.good).returncode, 0)

    def test_prose_source_rejected(self):
        bad = json.loads(json.dumps(self.good)); bad["deltas"][0]["source"] = "ultramode [Remotive]"
        p = run(self.ws, bad); self.assertEqual(p.returncode, 1); self.assertIn("source", p.stderr)

    def test_missing_jd_file_rejected(self):
        bad = json.loads(json.dumps(self.good)); bad["deltas"][0]["jd_path"] = "jds/nope.txt"
        self.assertEqual(run(self.ws, bad).returncode, 1)

    def test_bad_id_rejected(self):
        bad = json.loads(json.dumps(self.good)); bad["deltas"][0]["id"] = "himalayas-devops-alma"
        p = run(self.ws, bad); self.assertEqual(p.returncode, 1); self.assertIn("id", p.stderr)

    def test_undisclosed_cap_rejected(self):
        bad = json.loads(json.dumps(self.good)); bad["counts"]["capped"] = False  # 2 < 6-3 ⇒ must be true
        self.assertEqual(run(self.ws, bad).returncode, 1)

    def test_missing_counts_rejected(self):
        bad = json.loads(json.dumps(self.good)); del bad["counts"]
        self.assertEqual(run(self.ws, bad).returncode, 1)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run to verify it fails** — `python3 -m unittest skills/_ultra-engine/tests/test_validate_delta.py` fails (script missing). *(Run from `skills/_ultra-engine/tests/`: `python3 -m unittest test_validate_delta -v`.)*

- [ ] **Step 3: Implement**

`skills/_ultra-engine/scripts/validate_delta.py`:
```python
#!/usr/bin/env python3
"""Validate a _source-sweep return envelope before merge. stdlib only.
Usage: validate_delta.py --ws <workspace-dir> <delta.json>
Exit 0 = valid. Exit 1 = invalid, one violation per stderr line."""
import argparse, json, os, re, sys

ID_RE = re.compile(r"^([0-9]+|[a-z0-9-]+__[a-z0-9-]+__[^_\s]\S*)$")
DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})?$")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ws", required=True)
    ap.add_argument("delta")
    a = ap.parse_args()
    errs = []
    try:
        env = json.load(open(a.delta))
    except Exception as e:
        print(f"envelope: unparseable JSON ({e})", file=sys.stderr); sys.exit(1)

    if env.get("status") not in ("ok", "partial"):
        errs.append("envelope.status: must be ok|partial")
    c = env.get("counts")
    if not isinstance(c, dict):
        errs.append("envelope.counts: required object {scanned,matched,dropped_explicit_violation,returned,capped}")
    else:
        for k in ("scanned", "matched", "dropped_explicit_violation", "returned"):
            if not isinstance(c.get(k), int): errs.append(f"counts.{k}: required int")
        if isinstance(c.get("returned"), int) and isinstance(c.get("matched"), int) \
           and isinstance(c.get("dropped_explicit_violation"), int):
            truncated = c["returned"] < (c["matched"] - c["dropped_explicit_violation"])
            if truncated and c.get("capped") is not True:
                errs.append("counts.capped: truncation occurred but capped is not true (silent cap)")
    if not isinstance(env.get("errors"), list):
        errs.append("envelope.errors: required list")

    for i, d in enumerate(env.get("deltas") or []):
        p = f"deltas[{i}]"
        for k in ("id", "url", "title", "company"):
            if not isinstance(d.get(k), str) or not d.get(k):
                errs.append(f"{p}.{k}: required non-empty string")
        if not isinstance(d.get("location", ""), str):
            errs.append(f"{p}.location: must be string")
        if isinstance(d.get("id"), str) and not ID_RE.match(d["id"]):
            errs.append(f"{p}.id: not bare-numeric or provider__board__externalid: {d['id']!r}")
        s = d.get("source")
        if not (isinstance(s, dict) and all(isinstance(s.get(k), str) and s.get(k) for k in ("lane", "provider", "board"))):
            errs.append(f"{p}.source: required structured object {{lane,provider,board}} — prose strings are the Phase-14 defect")
        fp = d.get("fingerprint", "")
        if not (isinstance(fp, str) and fp.count("|") == 2):
            errs.append(f"{p}.fingerprint: required 'company|title|location' form")
        if not DATE_RE.match(d.get("posted_at", "") or ""):
            errs.append(f"{p}.posted_at: YYYY-MM-DD or empty")
        jd = d.get("jd_path")
        if jd is not None:
            if not isinstance(jd, str) or not jd:
                errs.append(f"{p}.jd_path: string or null")
            else:
                rel = jd[len(".job-scout/"):] if jd.startswith(".job-scout/") else jd
                if not os.path.isfile(os.path.join(a.ws, rel)):
                    errs.append(f"{p}.jd_path: file not found under workspace: {jd}")
    if errs:
        for e in errs: print(e, file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run to verify it passes** — from `skills/_ultra-engine/tests/`: `python3 -m unittest test_validate_delta -v` → all pass; `bash run.sh` → `ALL PASS`.

- [ ] **Step 5: Commit** — `git add skills/_ultra-engine && git commit -m "Phase 14 Task 5: delta validator (structured source, namespaced ids, disclosed caps, jd existence)"`

---

### Task 6: merge_tracker.py (the heart)

**Files:**
- Create: `skills/_ultra-engine/scripts/merge_tracker.py`
- Test: `skills/_ultra-engine/tests/test_merge_tracker.py` (reuses `fixtures/tracker-mini.json`, `fixtures/delta-good.json`)

**Interfaces:**
- Consumes: `validate_delta.py` (invoked per delta file before merging; a failing delta aborts the whole merge, tracker untouched), `lib/fingerprint.jq` via `jq -L` subprocess (fingerprint recomputation — never a second implementation).
- Produces: `python3 merge_tracker.py --ws <workspace> --tracker <tracker.json> --today YYYY-MM-DD delta1.json [delta2.json ...]` — serial merge in argument order; atomic write; stdout = one-line JSON summary `{"merged": n, "collisions_also_seen": n, "url_upgrades": n, "skipped_known": n}`. Rules:
  - entry template: id/url/title/company/location/source(structured)/tier `"untiered"`/tier_reason null/status `"seen"`/first_seen=last_seen=today/jd_path/tags/notes `""` — scoring fields land later (omit, never null, per canonical "written lazily").
  - skip any delta whose id ∈ tracker or fingerprint ∈ live tracker fingerprints **but** record the sighting: append delta's `source` to the existing entry's `also_seen_on[]` (dedupe by lane+provider+board triple; never append its own source), bump `last_seen`.
  - within-run fingerprint collision: canonical rank `{ats:0, ats-provider:0, linkedin:1, national-board:2, remote-board:2, community:2, aggregator:3, freelance-marketplace:4, freelance:4, other:5}` on `source.lane`; winner is the entry, loser → winner's `also_seen_on[]`.
  - **canonical URL upgrade:** when an incoming delta collides with an *existing incumbent* and the incoming ranks strictly better (e.g. ATS vs aggregator), keep the incumbent entry (IDs immutable) but set its `url` to the incoming apply-URL, set its `jd_path` to the incoming one when the incumbent's is null, append a note `canonical upgraded to <provider> (<date>)`, and count it in `url_upgrades`.
  - existing entries: only `also_seen_on`, `last_seen`, `url`, `jd_path`(null→value), `notes` may change. `schema_version` set to 3. `stats.total_seen = len(jobs)`; `stats.last_run = today`.
  - atomic: write `.tmp`, re-validate (status/tier enums, keys == entry ids, every non-null jd_path file exists), `mv`.

- [ ] **Step 1: Write the failing tests**

`skills/_ultra-engine/tests/test_merge_tracker.py`:
```python
import json, os, shutil, subprocess, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "scripts", "merge_tracker.py")
FX = os.path.join(HERE, "fixtures")

def delta(entries, counts=None):
    n = len(entries)
    return {"status": "ok", "counts": counts or {"scanned": n, "matched": n, "dropped_explicit_violation": 0, "returned": n, "capped": False},
            "deltas": entries, "errors": [], "continuation_cursor": None}

def entry(i, company="Initech", title="Platform Engineer", loc="Remote", lane="remote-board", prov="remotive", board="remotive", jd=True):
    return {"id": i, "url": f"https://x/{i}", "title": title, "company": company, "location": loc,
            "source": {"lane": lane, "provider": prov, "board": board},
            "fingerprint": f"{company.lower()}|{title.lower()}|{loc.lower()}",
            "posted_at": "2026-07-01", "jd_path": f"jds/{i}.txt" if jd else None, "tags": []}

class T(unittest.TestCase):
    def setUp(self):
        self.ws = tempfile.mkdtemp(); os.makedirs(os.path.join(self.ws, "jds"))
        self.tracker = os.path.join(self.ws, "tracker.json")
        shutil.copy(os.path.join(FX, "tracker-mini.json"), self.tracker)
        self.jd("greenhouse__miro__7")  # fixture entry carries a jd_path — final validation checks the file exists

    def jd(self, i): open(os.path.join(self.ws, "jds", f"{i}.txt"), "w").write("jd")

    def run_merge(self, *deltas):
        paths = []
        for k, d in enumerate(deltas):
            p = os.path.join(self.ws, f"d{k}.json"); json.dump(d, open(p, "w")); paths.append(p)
        return subprocess.run(["python3", SCRIPT, "--ws", self.ws, "--tracker", self.tracker,
                               "--today", "2026-07-02"] + paths, capture_output=True, text=True)

    def load(self): return json.load(open(self.tracker))

    def test_new_role_merges_with_lazy_fields(self):
        e = entry("remotive__remotive__9"); self.jd(e["id"])
        p = self.run_merge(delta([e])); self.assertEqual(p.returncode, 0, p.stderr)
        t = self.load(); j = t["jobs"]["remotive__remotive__9"]
        self.assertEqual(j["status"], "seen"); self.assertEqual(j["tier"], "untiered")
        self.assertEqual(j["first_seen"], "2026-07-02")
        self.assertNotIn("competitiveness", j)          # written lazily — omitted, never null
        self.assertEqual(t["schema_version"], 3)
        self.assertEqual(t["stats"]["total_seen"], len(t["jobs"]))

    def test_known_fingerprint_records_sighting_not_duplicate(self):
        e = entry("jobicy__jobicy__1", company="Miro", title="Platform Engineer", loc="Remote",
                  lane="remote-board", prov="jobicy", board="jobicy"); self.jd(e["id"])
        p = self.run_merge(delta([e])); self.assertEqual(p.returncode, 0, p.stderr)
        t = self.load()
        self.assertNotIn("jobicy__jobicy__1", t["jobs"])
        seen = t["jobs"]["greenhouse__miro__7"]["also_seen_on"]
        self.assertIn({"lane": "remote-board", "provider": "jobicy", "board": "jobicy"}, seen)
        self.assertEqual(t["jobs"]["greenhouse__miro__7"]["last_seen"], "2026-07-02")

    def test_within_run_collision_ats_wins(self):
        a = entry("aggro__board__1", company="Vandelay", lane="aggregator", prov="aggro", board="board")
        g = entry("greenhouse__vandelay__2", company="Vandelay", lane="ats", prov="greenhouse", board="vandelay")
        self.jd(a["id"]); self.jd(g["id"])
        p = self.run_merge(delta([a]), delta([g])); self.assertEqual(p.returncode, 0, p.stderr)
        t = self.load()
        self.assertIn("greenhouse__vandelay__2", t["jobs"]); self.assertNotIn("aggro__board__1", t["jobs"])
        self.assertIn({"lane": "aggregator", "provider": "aggro", "board": "board"},
                      t["jobs"]["greenhouse__vandelay__2"]["also_seen_on"])

    def test_url_upgrade_on_existing_incumbent(self):
        # incumbent 4001 (linkedin, rank 1) vs incoming ATS (rank 0) same fingerprint
        e = entry("greenhouse__acme__5", company="Acme", title="Senior SRE", loc="Amsterdam",
                  lane="ats", prov="greenhouse", board="acme"); self.jd(e["id"])
        p = self.run_merge(delta([e])); self.assertEqual(p.returncode, 0, p.stderr)
        t = self.load(); j = t["jobs"]["4001"]
        self.assertEqual(j["url"], "https://x/greenhouse__acme__5")
        self.assertIn("canonical upgraded to greenhouse", j["notes"])
        self.assertNotIn("greenhouse__acme__5", t["jobs"])

    def test_invalid_delta_aborts_untouched(self):
        e = entry("x__y__1"); e["source"] = "prose string"; self.jd("x__y__1")
        before = open(self.tracker).read()
        p = self.run_merge(delta([e]))
        self.assertEqual(p.returncode, 1)
        self.assertEqual(before, open(self.tracker).read())

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run to verify it fails** — from `tests/`: `python3 -m unittest test_merge_tracker -v` → errors (script missing).

- [ ] **Step 3: Implement**

`skills/_ultra-engine/scripts/merge_tracker.py`:
```python
#!/usr/bin/env python3
"""Serial, schema-validating, atomic tracker merge. stdlib only.
Usage: merge_tracker.py --ws WS --tracker TRACKER --today YYYY-MM-DD delta.json [...]
Deltas merge in argument order (serial by construction). Any invalid delta
aborts the whole merge with the tracker untouched. Exit 0 on success with a
one-line JSON summary on stdout."""
import argparse, json, os, subprocess, sys, tempfile

RANK = {"ats": 0, "ats-provider": 0, "linkedin": 1, "national-board": 2, "remote-board": 2,
        "community": 2, "aggregator": 3, "freelance-marketplace": 4, "freelance": 4}
STATUSES = {"seen", "approved", "applied", "rejected", "skipped"}
TIERS = {"A", "B", "C", "D", "untiered"}
HERE = os.path.dirname(os.path.abspath(__file__))

def rank(source): return RANK.get((source or {}).get("lane", ""), 5)

def fp_of(company, title, location):
    out = subprocess.run(["jq", "-nr", "-L", os.path.join(HERE, "lib"),
                          "--arg", "c", company or "", "--arg", "t", title or "", "--arg", "l", location or "",
                          'include "fingerprint"; fp($c; $t; $l)'],
                         capture_output=True, text=True, check=True)
    return out.stdout.strip()

def read_source(v):
    """The tracker_read_source shim: tolerate legacy prose strings on read.
    Every legacy string in live trackers is a LinkedIn surface (or a pre-Phase-14
    prose write) — rank it as linkedin so an aggregator can never 'upgrade' it."""
    if isinstance(v, dict): return v
    return {"lane": "linkedin", "provider": "linkedin", "board": str(v)[:60]}

def sighting(entry, src):
    tri = {k: src[k] for k in ("lane", "provider", "board")}
    own = {k: read_source(entry.get("source"))[k] for k in ("lane", "provider", "board")}
    seen = entry.setdefault("also_seen_on", [])
    if tri != own and tri not in seen: seen.append(tri)

def validate_final(t, ws):
    errs = []
    for k, j in t["jobs"].items():
        if j.get("id") != k: errs.append(f"jobs[{k}].id mismatch")
        if j.get("status") not in STATUSES: errs.append(f"jobs[{k}].status {j.get('status')!r}")
        if j.get("tier") not in TIERS: errs.append(f"jobs[{k}].tier {j.get('tier')!r}")
        jd = j.get("jd_path")
        if jd:
            rel = jd[len(".job-scout/"):] if jd.startswith(".job-scout/") else jd
            if not os.path.isfile(os.path.join(ws, rel)): errs.append(f"jobs[{k}].jd_path missing file {jd}")
    return errs

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ws", required=True); ap.add_argument("--tracker", required=True)
    ap.add_argument("--today", required=True); ap.add_argument("deltas", nargs="+")
    a = ap.parse_args()

    for d in a.deltas:  # gate: refuse unvalidated input, all-or-nothing
        v = subprocess.run(["python3", os.path.join(HERE, "validate_delta.py"), "--ws", a.ws, d],
                           capture_output=True, text=True)
        if v.returncode != 0:
            sys.stderr.write(f"REFUSED {d}:\n{v.stderr}"); sys.exit(1)

    t = json.load(open(a.tracker))
    jobs = t["jobs"]
    live_fp = {}
    for k, j in jobs.items():
        if (j.get("status") or "seen") != "rejected":
            live_fp.setdefault(fp_of(j.get("company"), j.get("title"), j.get("location")), k)

    merged = seen_known = upgrades = collisions = 0
    merged_this_run = set()

    def new_entry(e):
        j = {"id": e["id"], "url": e["url"], "title": e["title"], "company": e["company"],
             "location": e.get("location", ""), "source": e["source"],
             "tier": "untiered", "tier_reason": None, "status": "seen",
             "first_seen": a.today, "last_seen": a.today,
             "jd_path": e.get("jd_path"), "tags": e.get("tags") or [], "notes": ""}
        if e.get("posted_at"): j["posted_at"] = e["posted_at"]
        if e.get("signals"): j["signals"] = e["signals"]
        return j

    for d in a.deltas:
        env = json.load(open(d))
        for e in env.get("deltas") or []:
            fp = e["fingerprint"]
            if e["id"] in jobs:  # known id: sighting only
                sighting(jobs[e["id"]], e["source"]); jobs[e["id"]]["last_seen"] = a.today
                seen_known += 1; continue
            if fp in live_fp:  # fingerprint collision
                inc_id = live_fp[fp]; inc = jobs[inc_id]
                better = rank(e["source"]) < rank(read_source(inc.get("source")))
                if better and inc_id in merged_this_run:
                    # both arrived this run: the better-ranked one BECOMES the entry,
                    # the earlier one is recorded as a sighting on it
                    j = new_entry(e)
                    j["also_seen_on"] = inc.get("also_seen_on") or []
                    sighting(j, read_source(inc.get("source")))
                    del jobs[inc_id]; merged_this_run.discard(inc_id)
                    jobs[e["id"]] = j; merged_this_run.add(e["id"]); live_fp[fp] = e["id"]
                elif better:
                    # pre-existing incumbent: ids are immutable — upgrade the apply URL only
                    inc["url"] = e["url"]
                    if not inc.get("jd_path") and e.get("jd_path"): inc["jd_path"] = e["jd_path"]
                    note = f"canonical upgraded to {e['source']['provider']} ({a.today})"
                    inc["notes"] = ((inc.get("notes") or "") + ("; " if inc.get("notes") else "") + note)
                    upgrades += 1
                    sighting(inc, e["source"]); inc["last_seen"] = a.today
                else:
                    sighting(inc, e["source"]); inc["last_seen"] = a.today
                collisions += 1; continue
            jobs[e["id"]] = new_entry(e)  # genuinely new
            live_fp[fp] = e["id"]; merged_this_run.add(e["id"]); merged += 1

    t["schema_version"] = 3
    t.setdefault("stats", {})["total_seen"] = len(jobs)
    t["stats"]["last_run"] = a.today

    errs = validate_final(t, a.ws)
    if errs:
        sys.stderr.write("MERGE ABORTED (validation):\n" + "\n".join(errs) + "\n"); sys.exit(1)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(a.tracker)), suffix=".tmp")
    with os.fdopen(fd, "w") as fh: json.dump(t, fh, indent=1, ensure_ascii=False)
    os.replace(tmp, a.tracker)
    print(json.dumps({"merged": merged, "collisions_also_seen": collisions,
                      "url_upgrades": upgrades, "skipped_known": seen_known}))

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run to verify it passes** — `python3 -m unittest test_merge_tracker -v` → 5 pass; `bash run.sh` → `ALL PASS`.

- [ ] **Step 5: Commit** — `git add skills/_ultra-engine && git commit -m "Phase 14 Task 6: atomic schema-validating tracker merge with canonical selection"`

---

### Task 7: rotation

**Files:**
- Create: `skills/_ultra-engine/scripts/rotation.sh`
- Test: `skills/_ultra-engine/tests/test_rotation.sh`, fixture `skills/_ultra-engine/tests/fixtures/sources-mini.json`

**Interfaces:**
- Consumes: `sources.json` (canonical schema; entries gain additive `last_swept_at: "YYYY-MM-DD"|absent`).
- Produces: `rotation.sh pick <sources.json> <N>` → newline-separated names of the N stalest `access_lane=="extension"` sources (absent `last_swept_at` sorts first = never swept); `rotation.sh mark <sources.json> <name> <YYYY-MM-DD>` → atomically stamps that source's `last_swept_at`. Consumed by Task 15 (dispatcher) — default N=4 (spec §5.4).

- [ ] **Step 1: Fixture + failing test**

`skills/_ultra-engine/tests/fixtures/sources-mini.json`:
```json
{"schema_version": 1, "base_country": "Netherlands", "target_geography": "EU", "priority_order": [], "backbone": [],
 "sources": [
  {"name": "Malt", "url": "https://malt.com", "category": "freelance-marketplace", "access_lane": "extension", "needs_key": false, "last_swept_at": "2026-06-20"},
  {"name": "Toptal", "url": "https://toptal.com", "category": "freelance-marketplace", "access_lane": "extension", "needs_key": false},
  {"name": "freelance.nl", "url": "https://freelance.nl", "category": "freelance-marketplace", "access_lane": "extension", "needs_key": false, "last_swept_at": "2026-06-01"},
  {"name": "Worksome", "url": "https://worksome.com", "category": "freelance-marketplace", "access_lane": "extension", "needs_key": false, "last_swept_at": "2026-06-25"},
  {"name": "RemoteOK", "url": "https://remoteok.com", "category": "remote-board", "access_lane": "api", "needs_key": false}
 ]}
```

`skills/_ultra-engine/tests/test_rotation.sh`:
```bash
#!/bin/bash
. "$(dirname "$0")/helpers.sh"
R="$(dirname "$0")/../scripts/rotation.sh"; FX="$(dirname "$0")/fixtures/sources-mini.json"
tmp=$(mktemp); cp "$FX" "$tmp"
picks=$(bash "$R" pick "$tmp" 3)
assert_eq "Toptal
freelance.nl
Malt" "$picks" "never-swept first, then stalest; api lane excluded"
bash "$R" mark "$tmp" "Toptal" "2026-07-02"
assert_eq "2026-07-02" "$(jq -r '.sources[]|select(.name=="Toptal").last_swept_at' "$tmp")" "mark stamps"
picks2=$(bash "$R" pick "$tmp" 1)
assert_eq "freelance.nl" "$picks2" "marked source rotates to back"
rm -f "$tmp"; finish
```

- [ ] **Step 2: Run to verify it fails.**

- [ ] **Step 3: Implement**

`skills/_ultra-engine/scripts/rotation.sh`:
```bash
#!/bin/bash
# Usage: rotation.sh pick <sources.json> <N>
#        rotation.sh mark <sources.json> <name> <YYYY-MM-DD>
set -eu
cmd="$1"; f="$2"
case "$cmd" in
  pick)
    n="$3"
    jq -r --argjson n "$n" '
      [ .sources[] | select(.access_lane == "extension") ]
      | sort_by(.last_swept_at // "0000-00-00")
      | .[:$n][].name' "$f"
    ;;
  mark)
    name="$3"; day="$4"
    jq --arg name "$name" --arg day "$day" '
      .sources |= map(if .name == $name then . + {last_swept_at: $day} else . end)' "$f" > "$f.tmp" \
      && jq -e . "$f.tmp" >/dev/null && mv "$f.tmp" "$f"
    ;;
  *) echo "usage: rotation.sh pick <sources.json> <N> | mark <sources.json> <name> <date>" >&2; exit 2;;
esac
```

- [ ] **Step 4: Run to verify it passes** — test + `run.sh` → `ALL PASS`.

- [ ] **Step 5: Commit** — `git add skills/_ultra-engine && git commit -m "Phase 14 Task 7: extension-lane rotation"`

---

### Task 8: jd_queue

**Files:**
- Create: `skills/_ultra-engine/scripts/jd_queue.sh`
- Test: `skills/_ultra-engine/tests/test_jd_queue.sh`

**Interfaces:**
- Produces: FIFO queue at `<queue.json>` (`{"queue": [entry...]}`; entry = the full delta-entry object that still needs its JD fetched).
  - `jd_queue.sh push <queue.json> <entries.json>` — append a JSON array of entries, deduped by `.id` against what's queued.
  - `jd_queue.sh pop <queue.json> <N>` — print the first N as a JSON array AND rewrite the queue without them (atomic).
  - `jd_queue.sh count <queue.json>` — print queue length (0 for missing file).
  Consumed by Task 15 (fetch-then-gate stage; budget default 75 per spec §5.4 — deferred queue served first next run).

- [ ] **Step 1: Write the failing test**

`skills/_ultra-engine/tests/test_jd_queue.sh`:
```bash
#!/bin/bash
. "$(dirname "$0")/helpers.sh"
Q="$(dirname "$0")/../scripts/jd_queue.sh"
q=$(mktemp -d)/queue.json
assert_eq "0" "$(bash "$Q" count "$q")" "missing file counts 0"
echo '[{"id":"a__b__1","title":"X"},{"id":"a__b__2","title":"Y"}]' > /tmp/e1.$$
bash "$Q" push "$q" /tmp/e1.$$
assert_eq "2" "$(bash "$Q" count "$q")" "push 2"
echo '[{"id":"a__b__2","title":"Y-dup"},{"id":"a__b__3","title":"Z"}]' > /tmp/e2.$$
bash "$Q" push "$q" /tmp/e2.$$
assert_eq "3" "$(bash "$Q" count "$q")" "dedupe by id on push"
popped=$(bash "$Q" pop "$q" 2)
assert_eq "a__b__1 a__b__2" "$(echo "$popped" | jq -r 'map(.id)|join(" ")')" "FIFO order"
assert_eq "1" "$(bash "$Q" count "$q")" "popped removed"
rm -f /tmp/e1.$$ /tmp/e2.$$; finish
```

- [ ] **Step 2: Run to verify it fails.**

- [ ] **Step 3: Implement**

`skills/_ultra-engine/scripts/jd_queue.sh`:
```bash
#!/bin/bash
# Deferred JD-fetch queue. See test for the contract.
set -eu
cmd="$1"; q="$2"
ensure() { [ -f "$q" ] || { mkdir -p "$(dirname "$q")"; echo '{"queue": []}' > "$q"; }; }
case "$cmd" in
  count) [ -f "$q" ] && jq '.queue|length' "$q" || echo 0;;
  push)
    ensure; add="$3"
    jq --slurpfile new "$add" '
      (.queue | map(.id)) as $have
      | .queue += ($new[0] | map(select(.id as $i | $have | index($i) | not)))' "$q" > "$q.tmp" \
      && jq -e . "$q.tmp" >/dev/null && mv "$q.tmp" "$q"
    ;;
  pop)
    ensure; n="$3"
    jq --argjson n "$n" '.queue[:$n]' "$q"
    jq --argjson n "$n" '.queue |= .[$n:]' "$q" > "$q.tmp" && jq -e . "$q.tmp" >/dev/null && mv "$q.tmp" "$q"
    ;;
  *) echo "usage: jd_queue.sh count|push|pop <queue.json> [entries.json|N]" >&2; exit 2;;
esac
```

- [ ] **Step 4: Run to verify it passes** — test + `run.sh` → `ALL PASS`.

- [ ] **Step 5: Commit** — `git add skills/_ultra-engine && git commit -m "Phase 14 Task 8: deferred JD-fetch queue"`

---

### Task 9: checkpoint

**Files:**
- Create: `skills/_ultra-engine/scripts/checkpoint.sh`
- Test: `skills/_ultra-engine/tests/test_checkpoint.sh`

**Interfaces:**
- Produces: run dirs under `<ws>/cache/run/<run-id>/` with `manifest.json` (`{run_id, started_at, stages: {<name>: "done"|"failed"}}`).
  - `checkpoint.sh init <ws> <run-id>` → creates dir + manifest, prints the run dir path.
  - `checkpoint.sh save <run-dir> <stage> [artifact-file]` → copies artifact into the run dir as `<stage>.json` (if given) and marks `stages.<stage> = "done"` (atomic manifest write).
  - `checkpoint.sh stage <run-dir> <stage>` → prints `done`/`failed`/`absent`.
  - `checkpoint.sh find-incomplete <ws>` → prints the newest run dir whose manifest lacks `stages.render == "done"`, else nothing (exit 0 either way). Consumed by Task 15 (resume + always-render) and Task 10.

- [ ] **Step 1: Write the failing test**

`skills/_ultra-engine/tests/test_checkpoint.sh`:
```bash
#!/bin/bash
. "$(dirname "$0")/helpers.sh"
C="$(dirname "$0")/../scripts/checkpoint.sh"
ws=$(mktemp -d)
rd=$(bash "$C" init "$ws" 2026-07-02-1000)
assert_eq "$ws/cache/run/2026-07-02-1000" "$rd" "init prints run dir"
assert_eq "absent" "$(bash "$C" stage "$rd" snapshot)" "absent stage"
echo '{"known_ids": []}' > /tmp/snap.$$
bash "$C" save "$rd" snapshot /tmp/snap.$$
assert_eq "done" "$(bash "$C" stage "$rd" snapshot)" "saved stage"
assert_ok test -f "$rd/snapshot.json"
assert_eq "$rd" "$(bash "$C" find-incomplete "$ws")" "incomplete found (no render)"
bash "$C" save "$rd" render
assert_eq "" "$(bash "$C" find-incomplete "$ws")" "complete run not offered"
rm -f /tmp/snap.$$; finish
```

- [ ] **Step 2: Run to verify it fails.**

- [ ] **Step 3: Implement**

`skills/_ultra-engine/scripts/checkpoint.sh`:
```bash
#!/bin/bash
# Run-stage checkpoints. See test for the contract.
set -eu
cmd="$1"
case "$cmd" in
  init)
    ws="$2"; id="$3"; rd="$ws/cache/run/$id"; mkdir -p "$rd"
    [ -f "$rd/manifest.json" ] || printf '{"run_id": "%s", "started_at": "%s", "stages": {}}\n' \
      "$id" "$(date -u +%FT%TZ)" > "$rd/manifest.json"
    echo "$rd";;
  save)
    rd="$2"; stage="$3"; art="${4-}"
    if [ -n "$art" ]; then cp "$art" "$rd/$stage.json"; fi
    jq --arg s "$stage" '.stages[$s] = "done"' "$rd/manifest.json" > "$rd/manifest.json.tmp" \
      && mv "$rd/manifest.json.tmp" "$rd/manifest.json";;
  stage)
    rd="$2"; stage="$3"
    jq -r --arg s "$stage" '.stages[$s] // "absent"' "$rd/manifest.json";;
  find-incomplete)
    ws="$2"
    for d in $(ls -1dr "$ws"/cache/run/*/ 2>/dev/null); do
      d="${d%/}"
      [ -f "$d/manifest.json" ] || continue
      if [ "$(jq -r '.stages.render // "absent"' "$d/manifest.json")" != "done" ]; then echo "$d"; break; fi
    done;;
  *) echo "usage: checkpoint.sh init|save|stage|find-incomplete ..." >&2; exit 2;;
esac
```

- [ ] **Step 4: Run to verify it passes** — test + `run.sh` → `ALL PASS`.

- [ ] **Step 5: Commit** — `git add skills/_ultra-engine && git commit -m "Phase 14 Task 9: run checkpoints + resume detection"`

---

### Task 10: scorecard

**Files:**
- Create: `skills/_ultra-engine/scripts/scorecard.sh`
- Test: `skills/_ultra-engine/tests/test_scorecard.sh` (reuses `fixtures/tracker-mini.json`, `fixtures/delta-good.json`)

**Interfaces:**
- Consumes: a run dir containing `sweep-<slug>.json` envelopes (validated shape from Task 5), optional `merge.json` (Task 6 stdout summary), optional `jd-fetch.json` (`{"budget": 75, "used": n, "deferred": n}`), optional `rotation.json` (`{"picked": [...], "rotated_out": [...]}`).
- Produces: `scorecard.sh <run-dir> <tracker.json> <today>` → writes `<run-dir>/scorecard.json` and prints it:

```json
{
  "date": "YYYY-MM-DD",
  "sources": {"<slug>": {"scanned": 0, "matched": 0, "dropped_explicit_violation": 0, "returned": 0, "capped": false, "errors": 0}},
  "dedupe": {"merged": 0, "collisions_also_seen": 0, "url_upgrades": 0, "skipped_known": 0},
  "jd_fetch": {"budget": 0, "used": 0, "deferred": 0},
  "rotation": {"picked": [], "rotated_out": []},
  "gating": {"gated": 0, "by_kind": {}, "near_miss": 0},
  "tiers": {"A": 0, "B": 0, "C": 0, "D": 0, "untiered": 0},
  "disclosures": ["<one line per cap/skip/deferral — never silent>"]
}
```
`gating`/`tiers` are computed over tracker entries with `first_seen == today`. Disclosure lines are generated for: every `capped: true` source, every source with `errors[]`, a non-empty deferred queue, and every `rotated_out` name. Consumed by Task 11 (payload embeds it) and Task 15.

- [ ] **Step 1: Write the failing test**

`skills/_ultra-engine/tests/test_scorecard.sh`:
```bash
#!/bin/bash
. "$(dirname "$0")/helpers.sh"
SC="$(dirname "$0")/../scripts/scorecard.sh"; FXD="$(dirname "$0")/fixtures"
rd=$(mktemp -d)
cp "$FXD/delta-good.json" "$rd/sweep-remotive.json"
echo '{"merged": 1, "collisions_also_seen": 0, "url_upgrades": 0, "skipped_known": 2}' > "$rd/merge.json"
echo '{"budget": 75, "used": 3, "deferred": 2}' > "$rd/jd-fetch.json"
echo '{"picked": ["Malt"], "rotated_out": ["Toptal", "Worksome"]}' > "$rd/rotation.json"
bash "$SC" "$rd" "$FXD/tracker-mini.json" "2026-06-01" > /dev/null
assert_ok test -f "$rd/scorecard.json"
assert_eq "6" "$(jq '.sources["remotive"].matched' "$rd/scorecard.json")" "source counts lifted"
assert_eq "1" "$(jq '.dedupe.merged' "$rd/scorecard.json")" "merge summary lifted"
assert_eq "2" "$(jq '.jd_fetch.deferred' "$rd/scorecard.json")" "jd fetch lifted"
assert_eq "1" "$(jq '.tiers.B' "$rd/scorecard.json")" "tiers over first_seen==today"
assert_eq "true" "$(jq '[.disclosures[]|select(test("capped"))]|length > 0' "$rd/scorecard.json")" "cap disclosed"
assert_eq "true" "$(jq '[.disclosures[]|select(test("Toptal"))]|length > 0' "$rd/scorecard.json")" "rotation disclosed"
finish
```

- [ ] **Step 2: Run to verify it fails.**

- [ ] **Step 3: Implement**

`skills/_ultra-engine/scripts/scorecard.sh`:
```bash
#!/bin/bash
# Usage: scorecard.sh <run-dir> <tracker.json> <today>
set -eu
rd="$1"; tracker="$2"; today="$3"
sweeps="[]"
for f in "$rd"/sweep-*.json; do
  [ -e "$f" ] || continue
  n=$(basename "$f" .json); n=${n#sweep-}
  sweeps=$(jq -n --argjson acc "$sweeps" --arg n "$n" --slurpfile e "$f" \
    '$acc + [{key: $n, value: {scanned: ($e[0].counts.scanned // 0), matched: ($e[0].counts.matched // 0),
      dropped_explicit_violation: ($e[0].counts.dropped_explicit_violation // 0),
      returned: ($e[0].counts.returned // 0), capped: ($e[0].counts.capped // false),
      errors: ($e[0].errors | length)}}]')
done
merge='{}'; [ -f "$rd/merge.json" ] && merge=$(cat "$rd/merge.json")
jdf='{"budget": 0, "used": 0, "deferred": 0}'; [ -f "$rd/jd-fetch.json" ] && jdf=$(cat "$rd/jd-fetch.json")
rot='{"picked": [], "rotated_out": []}'; [ -f "$rd/rotation.json" ] && rot=$(cat "$rd/rotation.json")
jq -n --arg today "$today" --argjson sweeps "$sweeps" --argjson merge "$merge" \
      --argjson jdf "$jdf" --argjson rot "$rot" --slurpfile t "$tracker" '
  [ $t[0].jobs | to_entries[] | .value | select(.first_seen == $today) ] as $new
  | {date: $today,
     sources: ($sweeps | from_entries),
     dedupe: {merged: ($merge.merged // 0), collisions_also_seen: ($merge.collisions_also_seen // 0),
              url_upgrades: ($merge.url_upgrades // 0), skipped_known: ($merge.skipped_known // 0)},
     jd_fetch: $jdf, rotation: $rot,
     gating: {gated: ([ $new[] | select(.tier == "D") ] | length),
              by_kind: ([ $new[] | (.gate_violations // [])[] | .kind ] | group_by(.) | map({(.[0]): length}) | add // {}),
              near_miss: ([ $new[] | select(.near_miss == true) ] | length)},
     tiers: ([ $new[] | .tier // "untiered" ] | group_by(.) | map({(.[0]): length}) | add // {}
             | {A: (.A // 0), B: (.B // 0), C: (.C // 0), D: (.D // 0), untiered: (.untiered // 0)}),
     disclosures:
       ( [ $sweeps[] | select(.value.capped) | "\(.key): results capped — \(.value.returned) of \(.value.matched - .value.dropped_explicit_violation) lane matches returned" ]
       + [ $sweeps[] | select(.value.errors > 0) | "\(.key): \(.value.errors) sweep error(s) — see envelope" ]
       + (if ($jdf.deferred // 0) > 0 then ["JD fetches: \($jdf.used) of budget \($jdf.budget) used — \($jdf.deferred) deferred to next run"] else [] end)
       + [ $rot.rotated_out[]? | "rotated out this run: \(.) (swept on its next rotation slot)" ] ) }
' > "$rd/scorecard.json.tmp" && jq -e . "$rd/scorecard.json.tmp" >/dev/null && mv "$rd/scorecard.json.tmp" "$rd/scorecard.json"
cat "$rd/scorecard.json"
```

- [ ] **Step 4: Run to verify it passes** — test + `run.sh` → `ALL PASS`.

- [ ] **Step 5: Commit** — `git add skills/_ultra-engine && git commit -m "Phase 14 Task 10: per-run scorecard assembly"`

---

### Task 11: payload

**Files:**
- Create: `skills/_ultra-engine/scripts/payload.sh`
- Test: `skills/_ultra-engine/tests/test_payload.sh`, fixture `skills/_ultra-engine/tests/fixtures/tracker-payload.json`

**Interfaces:**
- Consumes: tracker + a run dir whose `scorecard.json` exists (Task 10).
- Produces: `payload.sh <tracker.json> <run-dir> <today> <n_sources>` → prints the `ultramode` render payload:
  - `results[]` = entries with `first_seen == today` **excluding** near-miss entries, ordered: tier A→B→C→D(gated last); within tier `confidence` high→med→low→absent; then `posted_at` desc.
  - `near_misses[]` = entries with `near_miss == true`, each carrying `would_be_tier`, the single failed gate kind + detail, and the `/bend <id>` hint.
  - `scorecard` = embedded verbatim from the run dir; `title`/`subtitle`/`filename`/`generated_at`/`tier_counts`/`source_breakdown` as in the existing ultramode view (source label = `provider` or `provider · board` when they differ; legacy prose sources label as their string).
  - Phase-12 optional fields pass through only when present (omit-when-absent — jq naturally omits absent keys; the script must never inject nulls).

- [ ] **Step 1: Fixture + failing test**

`skills/_ultra-engine/tests/fixtures/tracker-payload.json`:
```json
{"schema_version": 3, "version": 2,
 "stats": {"total_seen": 5, "applied": 0, "rejected": 0, "last_run": "2026-07-02", "last_search": null, "last_archive_pass": null, "last_deep_sweep": null},
 "jobs": {
  "a__a__1": {"id": "a__a__1", "url": "u1", "title": "Platform Engineer", "company": "One", "location": "Remote", "source": {"lane": "ats", "provider": "greenhouse", "board": "one"}, "tier": "B", "confidence": "low", "status": "seen", "first_seen": "2026-07-02", "last_seen": "2026-07-02", "posted_at": "2026-07-01", "jd_path": "jds/a__a__1.txt", "notes": ""},
  "a__a__2": {"id": "a__a__2", "url": "u2", "title": "SRE", "company": "Two", "location": "Remote", "source": {"lane": "remote-board", "provider": "jobicy", "board": "jobicy"}, "tier": "B", "confidence": "high", "status": "seen", "first_seen": "2026-07-02", "last_seen": "2026-07-02", "posted_at": "2026-06-28", "jd_path": "jds/a__a__2.txt", "notes": ""},
  "a__a__3": {"id": "a__a__3", "url": "u3", "title": "Linux Engineer", "company": "Three", "location": "Berlin", "source": {"lane": "aggregator", "provider": "arbeitnow", "board": "arbeitnow"}, "tier": "A", "status": "seen", "first_seen": "2026-07-02", "last_seen": "2026-07-02", "posted_at": "2026-07-02", "jd_path": "jds/a__a__3.txt", "notes": ""},
  "a__a__4": {"id": "a__a__4", "url": "u4", "title": "IAM Engineer", "company": "Four", "location": "Remote", "source": {"lane": "ats", "provider": "greenhouse", "board": "four"}, "tier": "D", "tier_reason": "gated: contract_type (permanent)", "gate_violations": [{"kind": "contract_type", "detail": "permanent"}], "near_miss": true, "near_miss_would_be_tier": "A", "status": "seen", "first_seen": "2026-07-02", "last_seen": "2026-07-02", "posted_at": "2026-07-01", "jd_path": "jds/a__a__4.txt", "notes": ""},
  "a__a__5": {"id": "a__a__5", "url": "u5", "title": "Helpdesk", "company": "Five", "location": "Onsite", "source": {"lane": "aggregator", "provider": "arbeitnow", "board": "arbeitnow"}, "tier": "D", "tier_reason": "gated: work_arrangement,contract_type", "gate_violations": [{"kind": "work_arrangement", "detail": "onsite"}, {"kind": "contract_type", "detail": "permanent"}], "status": "seen", "first_seen": "2026-07-02", "last_seen": "2026-07-02", "posted_at": "2026-06-30", "jd_path": "jds/a__a__5.txt", "notes": ""}
 }}
```

`skills/_ultra-engine/tests/test_payload.sh`:
```bash
#!/bin/bash
. "$(dirname "$0")/helpers.sh"
P="$(dirname "$0")/../scripts/payload.sh"; FXD="$(dirname "$0")/fixtures"
rd=$(mktemp -d); echo '{"date": "2026-07-02", "disclosures": []}' > "$rd/scorecard.json"
out=$(bash "$P" "$FXD/tracker-payload.json" "$rd" "2026-07-02" 12)
assert_eq "a__a__3 a__a__2 a__a__1 a__a__5" "$(echo "$out" | jq -r '[.results[].id]|join(" ")')" \
  "A first; within B high-conf before low; two-gate D last; near-miss excluded from results"
assert_eq "a__a__4" "$(echo "$out" | jq -r '.near_misses[0].id')" "near-miss lifted to rail"
assert_eq "A" "$(echo "$out" | jq -r '.near_misses[0].would_be_tier')" "would-be tier carried"
assert_eq "1" "$(echo "$out" | jq '.tier_counts.a')" "tier counts"
assert_eq "false" "$(echo "$out" | jq '.results[0]|has("confidence")')" "omit-when-absent (no null injection)"
assert_eq "ultramode-2026-07-02.html" "$(echo "$out" | jq -r '.filename')" "filename"
assert_eq "2026-07-02" "$(echo "$out" | jq -r '.scorecard.date')" "scorecard embedded"
finish
```

- [ ] **Step 2: Run to verify it fails.**

- [ ] **Step 3: Implement**

`skills/_ultra-engine/scripts/payload.sh`:
```bash
#!/bin/bash
# Usage: payload.sh <tracker.json> <run-dir> <today> <n_sources>
set -eu
tracker="$1"; rd="$2"; today="$3"; nsrc="$4"
jq -n --arg today "$today" --argjson nsrc "$nsrc" \
      --slurpfile t "$tracker" --slurpfile sc "$rd/scorecard.json" '
  def tier_rank: {"A": 0, "B": 1, "C": 2, "D": 3, "untiered": 4}[.tier // "untiered"] // 4;
  def conf_rank: if has("confidence") then ({"high": 0, "med": 1, "low": 2}[.confidence] // 3) else 3 end;
  def date_num: (.posted_at // "0000-00-00") | gsub("-"; "") | tonumber;
  def src_label: if (.source | type) == "object"
      then (if .source.provider == .source.board then .source.provider else "\(.source.provider) · \(.source.board)" end)
      else (.source | tostring) end;
  [ $t[0].jobs | to_entries[] | .value | select(.first_seen == $today) ] as $new
  | [ $new[] | select(.near_miss == true) ] as $nm
  | [ $new[] | select(.near_miss != true) ] | sort_by([tier_rank, conf_rank, (0 - date_num)]) as $results
  | ([ $new[] | .tier ] | group_by(.) | map({(.[0]): length}) | add // {}) as $tc
  | { title: "Ultramode — \($nsrc) sources · \($new | length) new roles",
      subtitle: "A:\($tc.A // 0) B:\($tc.B // 0) C:\($tc.C // 0) · Filtered:\($tc.D // 0) · deduped across sources",
      generated_at: $today, filename: "ultramode-\($today).html",
      tier_counts: {a: ($tc.A // 0), b: ($tc.B // 0), c: ($tc.C // 0), d: ($tc.D // 0), total: ($new | length)},
      source_breakdown: ([ $results[] | src_label ] | group_by(.) | map({(.[0]): length}) | add // {}),
      scorecard: $sc[0],
      results: $results,
      near_misses: [ $nm[] | . + {
        would_be_tier: (.near_miss_would_be_tier // "B"),
        failed_gate: ((.gate_violations // [{"kind": "unknown", "detail": ""}])[0]),
        bend_hint: "/bend \(.id)" } ] }
'
```

- [ ] **Step 4: Run to verify it passes** — test + `run.sh` → `ALL PASS`.

- [ ] **Step 5: Commit** — `git add skills/_ultra-engine && git commit -m "Phase 14 Task 11: deterministic render payload (ordering, near-miss rail, disclosures)"`

---

### Task 12: `_ultra-engine/SKILL.md` contracts + CLAUDE.md

**Files:**
- Modify: `skills/_ultra-engine/SKILL.md` (replace stub body), `CLAUDE.md`

**Interfaces:**
- Produces: the engine's documented contract, referenced by Tasks 13–17. CLAUDE.md gains hard rule #9 and a real Testing section.

- [ ] **Step 1: Write the full SKILL.md body** (keep the Task-1 frontmatter; replace the body):

```markdown
The deterministic spine of the ultramode pipeline (Phase 14, spec 2026-07-02). Orchestrator skills MUST call these scripts for every mechanical operation — hand-rolled snapshots, merges, ID minting, ordering, or budget accounting are defects, not style choices. Scripts print machine-readable output, exit non-zero on any violation, and never write state non-atomically.

Resolve `SCRIPTS` as this skill's own `scripts/` directory (e.g. `skills/_ultra-engine/scripts` relative to the plugin root). `WS` is the workspace's `.job-scout` directory.

| Script | Call | Contract |
|---|---|---|
| snapshot | `bash $SCRIPTS/snapshot.sh $WS/tracker.json $WS/cache/ultramode-snapshot.json` | Non-rejected ids + canonical fingerprints; subagents read the FILE (pass its path, never inline the lists). |
| fingerprint | `bash $SCRIPTS/fingerprint.sh <company> <title> <location>` | THE fingerprint. Never re-derive in prose or a second implementation. |
| namespace_id | `bash $SCRIPTS/namespace_id.sh <provider> <board> <ext-id>` (or `--from-url <provider> <board> <url>`) | Collision-proof external ids; slugs `[a-z0-9-]`. |
| validate_delta | `python3 $SCRIPTS/validate_delta.py --ws $WS <delta.json>` | Rejects prose sources, malformed ids, undisclosed caps, missing JD blobs. Run on EVERY sweep return before merge. |
| merge_tracker | `python3 $SCRIPTS/merge_tracker.py --ws $WS --tracker $WS/tracker.json --today <YYYY-MM-DD> <delta...>` | Serial merge, canonical selection + `also_seen_on`, URL upgrade, atomic write. All-or-nothing: any invalid delta aborts untouched. |
| rotation | `bash $SCRIPTS/rotation.sh pick <sources.json> 4` / `mark <sources.json> <name> <date>` | Staleness-ordered extension-lane rotation (D8). |
| jd_queue | `bash $SCRIPTS/jd_queue.sh push|pop|count $WS/cache/jd-queue.json ...` | Deferred JD-fetch queue; budget default 75 (D9). |
| checkpoint | `bash $SCRIPTS/checkpoint.sh init|save|stage|find-incomplete ...` | Run-dir stage manifest under `$WS/cache/run/<id>/`; `find-incomplete` powers resume (D7). |
| scorecard | `bash $SCRIPTS/scorecard.sh <run-dir> $WS/tracker.json <today>` | The per-run accounting incl. `disclosures[]` (D12). |
| payload | `bash $SCRIPTS/payload.sh $WS/tracker.json <run-dir> <today> <n-sources>` | The ultramode render payload: ordering, near-miss rail, scorecard embed. |

Single-entry tracker field updates (a score landing, a bend) use the atomic jq recipe in `../shared-references/state-validators.md`; multi-entry writes go through `merge_tracker.py` only.

Tests: `bash skills/_ultra-engine/tests/run.sh` → `ALL PASS`. Any contract change lands with a test change in the same commit.
```

- [ ] **Step 2: CLAUDE.md edits** — two changes:

(1) Append to the Hard rules list:
```markdown
9. **Mechanical pipeline operations go through `_ultra-engine` scripts.** Snapshots, fingerprints, external-ID minting, delta validation, tracker merges, extension-lane rotation, JD-fetch budgeting, checkpoints, scorecards, and render-payload assembly are script calls (see `skills/_ultra-engine/SKILL.md`), never re-implemented in prose or improvised at run time. The model's jobs in the sweep pipeline are relevance triage, gating judgement on JD text, scoring, and report prose — nothing mechanical.
```

(2) Replace the Testing / validation section body ("No automated test suite exists. …") with:
```markdown
The deterministic spine has a real test suite: `bash skills/_ultra-engine/tests/run.sh` (bash + python3 unittest; expected final line `ALL PASS`). Run it before any commit that touches `skills/_ultra-engine/`. Everything else (skill prose, templates, live sweeps) is validated manually: spot-checks via shell (`jq`, `grep`, `wc`) and end-to-end runs of the affected slash command in a scratch workspace. Each implementation task in `docs/superpowers/plans/` names the specific verification step.
```

- [ ] **Step 3: Verify** — `bash skills/_ultra-engine/tests/run.sh` → `ALL PASS`; `grep -c "ultra-engine" CLAUDE.md` ≥ 2.

- [ ] **Step 4: Commit** — `git add skills/_ultra-engine/SKILL.md CLAUDE.md && git commit -m "Phase 14 Task 12: engine contracts + hard rule 9 + testing section"`

---

### Task 13: `_source-sweep` verbatim prompt templates

**Files:**
- Create: `skills/_source-sweep/references/prompt-api.md`, `prompt-rss.md`, `prompt-html.md`
- Modify: `skills/_source-sweep/SKILL.md`

**Interfaces:**
- Consumes: snapshot path (Task 4), namespaced-ID rule (Task 3), envelope shape (Task 5).
- Produces: three templates whose **only** variable parts are these placeholders (dispatcher fills them, changes nothing else): `{{SOURCE_JSON}}`, `{{SNAPSHOT_PATH}}`, `{{WS_DIR}}`, `{{SCRIPTS}}` (the `_ultra-engine/scripts` dir, so subagents mint ids with `namespace_id.sh`), `{{LANE_KEYWORDS}}`, `{{NOT_TERMS}}`, `{{GATE_BLOCK}}`, `{{FRESHNESS_DAYS}}`, `{{CAP}}`, `{{API_KEY_LINE}}`. Consumed by Task 15.

- [ ] **Step 1: Write `prompt-api.md`** (full text):

````markdown
# Verbatim sweep prompt — `api` lane

> Dispatcher contract: load this file, substitute ONLY the `{{...}}` placeholders, send as the subagent prompt. Do not paraphrase, reorder, or drop sections — the 2026-07-02 audit traced five defects to improvised prompts.

---
You are a `_source-sweep` subagent for a job-hunter plugin. Sweep exactly ONE source for GENUINELY-NEW roles, dedupe against the known-set, and return ONLY the JSON envelope below. No prose outside the JSON.

## Source (verbatim registry entry)
{{SOURCE_JSON}}
{{API_KEY_LINE}}

## Dedup snapshot — READ THIS FILE FIRST
Read `{{SNAPSHOT_PATH}}`: `known_ids[]` + `known_fingerprints[]`. A role is ALREADY KNOWN when its id is in known_ids OR its fingerprint `lower(company)|lower(title)|normalise_location(location)` is in known_fingerprints (normalise_location = lowercase, strip the words area/region/greater/metropolitan, strip punctuation, collapse spaces). Known roles are dropped BUT counted (they cost no fetch).

## Lane relevance (occupation-level — keep if title/body plausibly matches ANY)
{{LANE_KEYWORDS}}
Exclude when the title contains: {{NOT_TERMS}}

## Hard-gate pre-filter (drop ONLY on explicit violations)
{{GATE_BLOCK}}
Count every such drop in `counts.dropped_explicit_violation`. When the posting does NOT state the signal, KEEP the role and record the uncertainty in `signals` — downstream fetches the full JD before gating (never gate on absence here).

## Freshness
Prefer roles posted within the last {{FRESHNESS_DAYS}} days when a date is present; no date → include with `posted_at: ""`.

## Fetch & parse
GET the source's `endpoint` (read-only public HTTP — the documented WebFetch carve-out). Parse the JSON as its `poll_method` describes. Paginate as the endpoint dictates. One retry on failure, then record the failure in `errors[]` and stop.

## Per-role duties (for each kept, genuinely-new role)
1. Mint the id: `bash {{SCRIPTS}}/namespace_id.sh <provider> <board> <external-id>` (or `--from-url` when no stable id exists).
2. Write the FULL description text to `{{WS_DIR}}/jds/<id>.txt` (UTF-8, whatever the source returned; if the list endpoint carries no description, fetch the role's detail URL once; if that fails set `jd_path: null` and record `signals` honestly).
3. Compute the fingerprint exactly as the snapshot rule above.

## Return EXACTLY this envelope (JSON only; cap {{CAP}} newest — when you truncate, `capped` MUST be true)
{
  "status": "ok",
  "counts": {"scanned": 0, "matched": 0, "dropped_explicit_violation": 0, "returned": 0, "capped": false},
  "deltas": [
    {"id": "<provider__board__externalid>", "url": "<apply url>", "title": "", "company": "", "location": "",
     "source": {"lane": "<this source's category>", "provider": "<slug>", "board": "<slug>"},
     "fingerprint": "<company|title|location>", "posted_at": "YYYY-MM-DD or ",
     "jd_path": "jds/<id>.txt or null",
     "signals": {"contract": "freelance|permanent|detachering|unknown", "remote": "remote|hybrid|onsite|unknown", "rate": "<figure or unknown>"},
     "tags": []}
  ],
  "errors": [{"code": "", "message": ""}],
  "continuation_cursor": null
}
````

- [ ] **Step 2: Write `prompt-rss.md` and `prompt-html.md`** — identical text except the `## Fetch & parse` section:

`prompt-rss.md` fetch section:
```markdown
## Fetch & parse
GET the feed URL (read-only public HTTP — the WebFetch carve-out). Parse the XML: one `<item>`/`<entry>` per posting; dedupe by item GUID before anything else. One retry on failure, then record in `errors[]` and stop.
```

`prompt-html.md` fetch section:
```markdown
## Fetch & parse
GET the source's `endpoint` (its listing/search page). Parse the listing HTML into role cards. **Never trust the source's `category=`/`search=` query parameters** — free-feed server-side filters are unreliable (Decision 9); apply the lane filter client-side over title + tags + visible body text. If the page is JS-only or empty, record `{"code": "js_only", ...}` in `errors[]` and stop (one retry max).
```

- [ ] **Step 3: Wire into `_source-sweep/SKILL.md`** — add directly under the "## Input shape" heading:

```markdown
## Prompt templates (dispatcher contract — Phase 14)

The dispatcher builds this subagent's prompt from the verbatim template matching the source's `access_lane` — `references/prompt-api.md`, `references/prompt-rss.md`, or `references/prompt-html.md` — substituting ONLY the `{{...}}` placeholders (`{{GATE_BLOCK}}` is built from `requirements.deal_breakers` as data: the allowed `values[]` per kind plus the drop-on-explicit-violation rule; `{{CAP}}` defaults to 40). Composing a sweep prompt from memory is a defect: the 2026-07-02 audit traced missing JD persistence, ad-hoc IDs, prose sources, and silent caps to exactly that. The `extension` lane has no template — it never runs in a subagent (§ extension_lane_deferred).
```

- [ ] **Step 4: Verify** — `ls skills/_source-sweep/references/prompt-*.md` → 3 files; `grep -c '{{SNAPSHOT_PATH}}' skills/_source-sweep/references/prompt-api.md` → ≥1; `grep -n "Prompt templates" skills/_source-sweep/SKILL.md` → hit.

- [ ] **Step 5: Commit** — `git add skills/_source-sweep && git commit -m "Phase 14 Task 13: verbatim sweep prompt templates (api/rss/html)"`

---

### Task 14: gate semantics (D1/D4), near-miss rule (D3), jd_path requirement

**Files:**
- Modify: `skills/_gate-engine/SKILL.md`, `skills/_job-matcher/SKILL.md`

- [ ] **Step 1: `_gate-engine/SKILL.md`** — add a section (after its evaluation rules):

```markdown
## Gate semantics are data, not taxonomy (Phase 14, D4)

The gate reads each `deal_breakers[]` entry's `values[]` as the workspace's **allowed set** (for `contract_type`/`work_arrangement`/`location`) or threshold (`rate_floor`/`salary_floor`), refined by its `free_text`. Never apply a built-in idea of what a term includes: if `values` is `["freelance", "detachering"]`, a detachering/secondment role passes the contract gate (this exact case was mis-gated on 2026-07-02). Unknown evidence is NOT a violation — a gate may only fail on text that states or clearly implies the violation; "not stated" is handled upstream by fetch-then-gate (D2), and by the time this engine runs, every role carries its full JD.

## Structured violations + the near-miss flag (Phase 14, D3)

- Always persist `gate_violations[]` as `[{kind, detail}]` — `kind` from the deal-breaker enum, `detail` a short quote/paraphrase of the violating evidence. `tier_reason` remains the human-readable summary; it never replaces the structured field.
- When **exactly one distinct `kind`** fails and every other gate passes, do NOT stop at `tier: "D"`: hand the role to `_job-matcher` for a full rubric pass anyway. If the rubric result (ignoring the gate) is A or B, set `near_miss: true` and `near_miss_would_be_tier: "A"|"B"` on the entry. Tier stays `"D"` (a gate is a gate — the rail, not the ranking, is where near-misses surface). Two or more failed kinds is honest D-tier: no rubric pass, no flag.
```

- [ ] **Step 2: `_job-matcher/SKILL.md`** — add to its scoring contract:

```markdown
## JD required (Phase 14)

Scoring reads the JD from `jd_path`. **Refuse to score an entry whose `jd_path` is null or whose file is missing** — return it as `{id, skipped: "jd_missing"}` so the dispatcher records it in the scorecard's disclosures. Scoring from a listing excerpt is the 2026-07-02 defect ("remote not confirmed" gates on absent data) and is never acceptable.

## Near-miss rubric pass (Phase 14, D3)

When dispatched for a single-gate-failure role (`_gate-engine` § near-miss), run the rubric exactly as normal and return the would-be tier and dimensions. The dispatcher persists `near_miss`/`near_miss_would_be_tier` alongside the D tier; dimension evidence renders in the near-miss rail.
```

- [ ] **Step 3: Verify** — `grep -n "detachering" skills/_gate-engine/SKILL.md` → hit; `grep -n "jd_missing" skills/_job-matcher/SKILL.md` → hit.

- [ ] **Step 4: Commit** — `git add skills/_gate-engine skills/_job-matcher && git commit -m "Phase 14 Task 14: gate-as-data, structured violations, near-miss rule, jd_path requirement"`

---

### Task 15: rewrite `/ultramode` Step 4 to drive the engine

**Files:**
- Modify: `skills/ultramode/SKILL.md` (replace the bodies of Steps 4a–4h; Steps 0–3 and 5 unchanged)

**Interfaces:**
- Consumes: every script from Tasks 2–11 by the exact calls in `_ultra-engine/SKILL.md`; templates from Task 13; gate/matcher rules from Task 14.

- [ ] **Step 1: Replace the Step 4 section** with (verbatim, keeping the existing "## Step 4: Sweep flow" heading):

```markdown
Resolve `SCRIPTS` = `../_ultra-engine/scripts` (this plugin's engine — see `../_ultra-engine/SKILL.md` for every contract) and `WS` = `.job-scout`. Mechanical work below is script calls; composing them from memory is a defect (CLAUDE.md hard rule #9).

### Step 4a: Resume or start a run
`rd=$(bash $SCRIPTS/checkpoint.sh find-incomplete $WS)`. If non-empty and its manifest `started_at` is within 48h, announce **resuming** and skip every stage whose checkpoint says `done`. Otherwise `rd=$(bash $SCRIPTS/checkpoint.sh init $WS $(date +%F-%H%M))`.

### Step 4b: Registry, rotation, snapshot
Load `sources.json`; derive poll order per `ultramode-sources.md` § Adaptive priority order. Pick this run's extension-lane subset: `bash $SCRIPTS/rotation.sh pick $WS/sources.json 4`; write `{picked, rotated_out}` (rotated_out = extension sources not picked) to `$rd/rotation.json`. Build the snapshot: `bash $SCRIPTS/snapshot.sh $WS/tracker.json $WS/cache/ultramode-snapshot.json`, then `checkpoint.sh save $rd snapshot $WS/cache/ultramode-snapshot.json`. The ATS watchlist derives exactly as before (four-source union, cold-start rule).

### Step 4c: Fan out subagent sweeps (api/rss/html lanes)
For each non-extension source in poll order: load the template matching its `access_lane` from `../_source-sweep/references/prompt-<lane>.md`, substitute ONLY the placeholders ({{SOURCE_JSON}} = the registry entry verbatim; {{SNAPSHOT_PATH}} = the snapshot file; {{GATE_BLOCK}} = the drop-on-explicit-violation rules built from `requirements.deal_breakers` values[]/free_text as data; {{CAP}} = 40), and dispatch via the Agent tool per `subagent-protocol.md` (parallel across sources is fine — they never write the tracker). Save each return: write it to a temp file, `python3 $SCRIPTS/validate_delta.py --ws $WS <file>`; on failure re-dispatch that source once with the validator's stderr appended under a "## Previous attempt was rejected because" line; on second failure record the source as failed in `errors` and move on. On success: `checkpoint.sh save $rd sweep-<name-slug> <file>`.

### Step 4d: Extension lane — main thread, rotation subset only
For each `rotation.json .picked` source: sweep it in the logged-in session via the Chrome extension (dedupe-before-extract against the snapshot; collect candidate ids on the listing page; open only new ones; write each full JD to `jds/<namespaced-id>.txt` minted with `namespace_id.sh`; build the SAME envelope shape including `counts` + `signals`). Validate + checkpoint exactly as 4c, then `bash $SCRIPTS/rotation.sh mark $WS/sources.json <name> $(date +%F)`. A source that cannot be swept (login expired, layout dead) records an `errors[]` envelope — never silence.

### Step 4e: Merge (all-or-nothing, serial, atomic)
`python3 $SCRIPTS/merge_tracker.py --ws $WS --tracker $WS/tracker.json --today $(date +%F) $rd/sweep-*.json` — save its stdout to `$rd/merge.json` and `checkpoint.sh save $rd merge $rd/merge.json`. On non-zero exit: STOP the pipeline, show the validator output, and still proceed to Steps 4g–4h with whatever previous stages completed (always-render).

### Step 4f: Fetch-then-gate (D2), then gate + score
1. Queue: every merged entry from this run with `jd_path: null` OR any load-bearing `signals` value `unknown` (contract/remote/rate when a matching deal-breaker exists) → `jd_queue.sh push $WS/cache/jd-queue.json <entries>`. Pop the budget: `jd_queue.sh pop $WS/cache/jd-queue.json 75`. For each popped entry fetch the full JD (WebFetch for public urls; the extension for login-walled sources), write `jds/<id>.txt`, set `jd_path` on the entry via the atomic single-entry recipe (state-validators.md). Write `{"budget": 75, "used": <n>, "deferred": $(jd_queue.sh count ...)}` to `$rd/jd-fetch.json`; checkpoint `jd-fetch`.
2. Gate + score every this-run entry **with a jd_path**, batched ≤5 per `subagent-protocol.md`: `_gate-engine` first (violations as structured data; single-kind failures continue to the rubric per its § near-miss), `_job-matcher` rubric second (refuses jd-missing). Persist per entry atomically: `tier`, `tier_reason`, `gate_violations[]`, `dimensions`, `rubric_version: "v1"`, and when applicable `near_miss` + `near_miss_would_be_tier`; scores into `cache/scores.json` under the usual key. Checkpoint `scoring` when the batch set completes.

### Step 4g: Scorecard + payload
`bash $SCRIPTS/scorecard.sh $rd $WS/tracker.json $(date +%F)` then `bash $SCRIPTS/payload.sh $WS/tracker.json $rd $(date +%F) <n-sources-swept> > $rd/payload.json`; checkpoint both. The payload is the render input verbatim — do not hand-assemble or re-sort it.

### Step 4h: Render — ALWAYS
Follow `render-orchestration.md` with `view: "ultramode"` and `$rd/payload.json` (Hard Rule #8 — via `_visualizer`, never inline). This step runs even when 4c–4f partially failed: the report states what completed and the scorecard's disclosures name what didn't. `checkpoint.sh save $rd render` only after the report file exists. Summary line: `✓ Ultramode — {{N_sources}} sources · {{N_new}} new roles — A:{{a}} B:{{b}} C:{{c}} · Filtered:{{gated}} · Near-misses:{{nm}} — opened report in Chrome`, followed by every scorecard disclosure line.
```

- [ ] **Step 2: Verify** — `grep -c 'SCRIPTS/' skills/ultramode/SKILL.md` ≥ 8; `grep -n "always" skills/ultramode/SKILL.md | grep -i render` → hit; Steps 0–3 and 5 untouched (`git diff` shows changes confined to Step 4).

- [ ] **Step 3: Commit** — `git add skills/ultramode && git commit -m "Phase 14 Task 15: /ultramode Step 4 drives the engine (checkpoints, rotation, fetch-then-gate, always-render)"`

---

### Task 16: `_visualizer` — near-miss rail + scorecard strip

**Files:**
- Modify: `skills/_visualizer/templates/html/ultramode.html.j2`, `skills/_visualizer/templates/markdown/ultramode.md.j2`, `skills/_visualizer/SKILL.md` (payload schema), `skills/_visualizer/references/component-library.md`
- Test: render-verify with `skills/_ultra-engine/tests/fixtures/` payload (one-off command, not a suite file)

- [ ] **Step 1: Add the near-miss rail block** to `ultramode.html.j2`, inserted immediately AFTER the existing gated/"Filtered out" group block (locate it by searching the template for the gated-group marker; the inserted block is self-contained):

```jinja2
{% if near_misses %}
<details class="near-miss-rail">
  <summary>Near-misses — would you bend? ({{ near_misses|length }})</summary>
  {% for j in near_misses %}
  <div class="card near-miss">
    <div class="card-head">
      <span class="tier-pill tier-d">D</span>
      <span class="would-be">would be {{ j.would_be_tier }}</span>
      <strong>{{ j.title }}</strong> @ {{ j.company }} · {{ j.location }}
    </div>
    <div class="gate-line">Fails one gate: <code>{{ j.failed_gate.kind }}</code> — {{ j.failed_gate.detail }}</div>
    <div class="bend-hint">Bend it: <code>{{ j.bend_hint }}</code> · <a href="{{ j.url }}">view role</a></div>
  </div>
  {% endfor %}
</details>
{% endif %}
{% if scorecard %}
<details class="scorecard"><summary>Run scorecard</summary>
  <ul>
  {% for d in scorecard.disclosures %}<li>{{ d }}</li>{% endfor %}
  {% if not scorecard.disclosures %}<li>Nothing capped, skipped, or deferred this run.</li>{% endif %}
  </ul>
</details>
{% endif %}
```

And the markdown twin in `ultramode.md.j2` (same position):

```jinja2
{% if near_misses %}
## Near-misses — would you bend? ({{ near_misses|length }})
{% for j in near_misses %}
- **{{ j.title }}** @ {{ j.company }} ({{ j.location }}) — would be **{{ j.would_be_tier }}**; fails `{{ j.failed_gate.kind }}`: {{ j.failed_gate.detail }} → `{{ j.bend_hint }}`
{% endfor %}
{% endif %}
{% if scorecard and scorecard.disclosures %}
## Run scorecard
{% for d in scorecard.disclosures %}- {{ d }}
{% endfor %}
{% endif %}
```

- [ ] **Step 2: Document** — add `near_misses[]` (id/title/company/location/url/would_be_tier/failed_gate{kind,detail}/bend_hint) and `scorecard` (embedded object; templates read `.disclosures[]`) to the ultramode payload schema in `skills/_visualizer/SKILL.md`, and a "Near-miss rail" + "Scorecard strip" entry (the two blocks above) in `references/component-library.md`. British English throughout.

- [ ] **Step 3: Render-verify** (the repo's established Jinja2 check):

```bash
cd skills/_visualizer && python3 - <<'EOF'
import json, pathlib
from jinja2 import Environment, FileSystemLoader
payload = {"title": "T", "subtitle": "s", "generated_at": "2026-07-02", "tier_counts": {"a": 1, "b": 0, "c": 0, "d": 1, "total": 2},
  "source_breakdown": {"greenhouse": 1}, "results": [], "scorecard": {"date": "2026-07-02", "disclosures": ["sweep-x: results capped — 2 of 3 lane matches returned"]},
  "near_misses": [{"id": "a__b__4", "title": "IAM Engineer", "company": "Four", "location": "Remote", "url": "u4",
                   "would_be_tier": "A", "failed_gate": {"kind": "contract_type", "detail": "permanent"}, "bend_hint": "/bend a__b__4"}]}
env = Environment(loader=FileSystemLoader("templates"))
for t in ("html/ultramode.html.j2", "markdown/ultramode.md.j2"):
    out = env.get_template(t).render(**payload)
    assert "would you bend" in out.lower() and "/bend a__b__4" in out and "capped" in out, t
    print("render ok:", t)
EOF
```
Expected: `render ok:` twice.

- [ ] **Step 4: Commit** — `git add skills/_visualizer && git commit -m "Phase 14 Task 16: near-miss rail + scorecard strip in ultramode view"`

---

### Task 17: `/bend` command + schema doc

**Files:**
- Create: `skills/bend/SKILL.md`
- Modify: `skills/shared-references/canonical-schemas.md` (additive fields note)

- [ ] **Step 1: Write `skills/bend/SKILL.md`** (full content):

```markdown
---
name: bend
description: Re-score a near-miss role as if its single failed gate were relaxed — the "would you bend?" action from the ultramode report
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: <tracker-id>
disable-model-invocation: true
version: 0.1.0
---

Bend exactly one near-miss. `/bend <tracker-id>` takes a role the gates filtered but the rubric loved (`near_miss: true` in `tracker.json`) and re-evaluates it with its single failed gate relaxed, so you can judge it on merit. Bending never changes your deal-breakers — it is a one-shot exception, recorded on the entry. (Learning from repeated bends is a later phase.)

## Steps

1. Load `.job-scout/tracker.json`; find the entry by id. Not found → say so and stop. Found but `near_miss` is not `true` → explain that `/bend` only applies to near-misses (point at the report's rail) and stop.
2. Read the failed gate: `gate_violations[0].kind` (near-misses have exactly one distinct kind by definition — `_gate-engine` § near-miss).
3. Re-run the evaluation with that kind excluded: `_gate-engine` over the remaining deal-breakers (must still pass), then `_job-matcher` on `jd_path` (it refuses a missing JD — if the JD is missing, fetch it first via WebFetch or the extension per the source's lane, persist to `jds/<id>.txt`, set `jd_path`).
4. Update the entry atomically (single-entry recipe in `../shared-references/state-validators.md`): `tier` = the rubric tier, `tier_reason` = `"bent: <kind> relaxed on <YYYY-MM-DD> — was gated: <detail>"`, `bent: true`, keep `gate_violations[]` and `near_miss` untouched. Write the score into `cache/scores.json` under the usual key.
5. Report one line before/after in British English: `Bent <id>: D (gated: contract_type) → A. Apply link: <url>` and suggest `/apply <id>` or `/cover-letter <id>` as next steps.
```

- [ ] **Step 2: canonical-schemas.md** — in the tracker-entry section, after the Phase-12 "written lazily" note, add:

```markdown
**Phase 14 additive entry fields (written lazily, omitted when absent — never null):** `posted_at` (`YYYY-MM-DD`, from the source when known), `also_seen_on[]` (`[{lane, provider, board}]` — sightings of the same fingerprint on other sources; the entry's own `source` never appears here), `near_miss` (`true` only when exactly one gate kind failed and the rubric's would-be tier is A/B), `near_miss_would_be_tier` (`"A"|"B"`), `bent` (`true` after `/bend` relaxed the failed gate one-off), `signals` (`{contract, remote, rate}` as swept, `unknown` marking what fetch-then-gate must resolve). `sources.json` entries gain `last_swept_at` (`YYYY-MM-DD`, rotation bookkeeping).
```

- [ ] **Step 3: Verify** — `grep -n "disable-model-invocation: true" skills/bend/SKILL.md` → hit; `grep -n "last_swept_at" skills/shared-references/canonical-schemas.md` → hit.

- [ ] **Step 4: Commit** — `git add skills/bend skills/shared-references/canonical-schemas.md && git commit -m "Phase 14 Task 17: /bend command + additive schema fields"`

---

### Task 18: release v0.14.0 + live acceptance

**Files:**
- Modify: `.claude-plugin/plugin.json` (version → `0.14.0`), `CHANGELOG.md`, `README.md`, `docs/ROADMAP.md`

- [ ] **Step 1: Full test suite green** — `bash skills/_ultra-engine/tests/run.sh` → `ALL PASS`.

- [ ] **Step 2: CHANGELOG.md** — new section at top:

```markdown
## [0.14.0] — 2026-07-02

### Added
- **Deterministic engine spine (`_ultra-engine`)** — scripts for snapshots, fingerprints, namespaced IDs, delta validation, atomic tracker merges with canonical selection + `also_seen_on`, extension-lane rotation, JD-fetch budgeting, run checkpoints, per-run scorecard, and render-payload assembly — plus the repo's first automated test suite (`skills/_ultra-engine/tests/run.sh`).
- **Near-miss rail + `/bend`** — strong-fit roles failing exactly one hard gate surface in a collapsed "would you bend?" report section; `/bend <id>` re-scores one with that gate relaxed.
- **Per-run scorecard** — sources swept/skipped/rotated, dedupe accounting, JD-fetch budget use, gating by reason, tier yield, and explicit disclosure lines (no silent caps, ever).

### Changed
- `/ultramode` Step 4 now drives the engine: checkpointed stages with resume, marketplace rotation (4/run, staleness-ordered), sweep-time drop of explicit gate violations, fetch-then-gate for unconfirmed data (budget 75/run, deferred queue), scoring refuses roles without a persisted JD, and the report **always renders** — partial runs included.
- `_source-sweep` prompts are verbatim templates (api/rss/html); improvised dispatch prompts are a named defect.
- `_gate-engine` reads `deal_breakers[].values` as the allowed set (detachering-as-freelance honoured) and always persists structured `gate_violations[]`.

### Fixed
- The five 2026-07-02 audit defects: zero JD persistence, silent result caps, ad-hoc external IDs, prose `source` strings, and the never-rendered report/extension lane.
```

- [ ] **Step 3: README.md** — in the ultramode section, add one short paragraph: near-miss rail + `/bend`, the always-rendered report with a scorecard, and marketplace rotation ("every login-walled marketplace at least fortnightly"). British English.

- [ ] **Step 4: ROADMAP.md** — tick every Phase 14 checkbox; append to the Log: `- **<date>** — Phase 14 shipped as v0.14.0. <one-line summary>. Live acceptance: <result of Step 6>.`

- [ ] **Step 5: Commit + tag**

```bash
git add .claude-plugin/plugin.json CHANGELOG.md README.md docs/ROADMAP.md
git commit -m "Phase 14 Task 18: release v0.14.0"
git tag v0.14.0
```

- [ ] **Step 6: Live acceptance (user-run, CVFREELANCER)** — the spec §3 hard gates, in order:
1. `/ultramode` full run → every scored external entry has `jd_path` (`jq '[.jobs[]|select(.first_seen=="<today>" and .tier != "untiered" and .jd_path == null)]|length' → 0`); zero prose `source` strings among today's entries; all new external ids match `__`-namespacing; ≥3 login-walled marketplaces swept (scorecard `rotation.picked`); scorecard counts reconcile with the tracker; every truncation appears in `disclosures[]`; detachering roles at/above €750/day pass the gate; the near-miss rail renders.
2. **Kill-test:** start `/ultramode`, interrupt during scoring, re-invoke → resumes from checkpoints, report still renders.
3. `/bend <id>` on one near-miss → tier updates, `bent: true`, one-line before/after.
Record results in the ROADMAP log line (Step 4 placeholder).

---

## Self-review (run before handoff)

- **Spec coverage:** D1 → Task 13 GATE_BLOCK + Task 15 4c; D2 → Tasks 8/15-4f; D3 → Tasks 14/11/16; D4 → Task 14; D5 → Tasks 1–12; D7 → Tasks 9/15-4a/4h; D8 → Tasks 7/15-4b/4d; D9 → Tasks 8/10/15-4f; D12 → Tasks 10/16; D13 → Task 17. D6/D10/D11/D14 are Phase 15 / process-level (no Phase 14 task — correct).
- **Placeholder scan:** the only `{{...}}` tokens are the *deliberate* template placeholders (Task 13) and summary-line variables quoted from the existing SKILL convention.
- **Type consistency:** envelope `counts` keys identical in Tasks 5/10/13; `signals` shape identical in Tasks 13/15/17; run-dir artifact names (`sweep-<slug>.json`, `merge.json`, `jd-fetch.json`, `rotation.json`, `scorecard.json`, `payload.json`) identical in Tasks 9/10/11/15; script CLIs match `_ultra-engine/SKILL.md` (Task 12) everywhere.


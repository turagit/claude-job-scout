# Phase 16 — EU/NL Source Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Port the Codex sibling's EU/NL source catalogue, registry lifecycle hardening, first-class auth state, exhaustive sweep mode, and report-delivery fix into this plugin as v0.16.0, per the approved spec `docs/superpowers/specs/2026-07-14-phase-16-eu-nl-source-parity-design.md` (D1–D18).

**Architecture:** All mechanical operations land as new `_ultra-engine` scripts with tests (hard rule 9): catalogue validate/select, host-identity normalisation, projection, migration, atomic lifecycle merge, auth-state updates. Orchestration changes are prose edits to `sources/SKILL.md`, `ultramode/SKILL.md`, and `render-orchestration.md`. The catalogue itself is a committed artifact produced by a bounded research pass (re-probe the 21 Codex candidates + a BENELUX hunt).

**Tech Stack:** bash 3.2 + jq, python3 stdlib only (Phase 14 convention). Tests via `skills/_ultra-engine/tests/run.sh` (bash suites + python unittest auto-discovery). No installs, no new dependencies.

## Global Constraints

- British English in all user-facing copy (`catalogue` in prose); identifiers/JSON keys exempt (hard rule 7).
- Scripts print machine-readable output, exit non-zero on violation, never write state non-atomically (atomic = write `.tmp`, validate, `mv`/`os.replace`).
- Every script contract change lands with its test change in the same commit; each new script gets a row in `skills/_ultra-engine/SKILL.md`'s table in the same commit.
- Config contract parity (D7): `source_scope: "eu-nl"|"eu-broad"` (default `eu-nl`), `source_refresh: "manual"` only; missing keys read as defaults **without writing**; unknown config keys preserved on write. Keys live at `user-profile.json` `.ultramode.source_scope` / `.ultramode.source_refresh`.
- Catalogue-only fields — exactly `lane_tags`, `auth_required`, `evidence_url`, `evidence_checked_at` — never reach `sources.json` (D11).
- `auth_state` enum: `public | auth-required | signed-in | session-expired`; transitions written only from observed sweep outcomes (spec §6.4).
- LinkedIn: at most one `category: "linkedin"` entry, never catalogue-admitted, never rotated (existing invariant).
- BENELUX priority packs are exactly `benelux` and `nl-core` (D4).
- The plugin never sees, stores, or logs credentials; sign-in happens in the user's Chrome (D6/D16).
- Run `bash skills/_ultra-engine/tests/run.sh` before every commit touching `skills/_ultra-engine/` (CLAUDE.md); expected final line `ALL PASS`.
- Repo root for all paths below: the plugin repo root. `SCRIPTS` = `skills/_ultra-engine/scripts`, `TESTS` = `skills/_ultra-engine/tests`.

**One deliberate deviation from the spec's §3 WS-B naming (flag in review):** host normalisation ships as `SCRIPTS/lib/identity.py` (importable by `catalog.py`/`project.py`/`registry_lifecycle.py` **and** runnable as a CLI), not a separate `identity.sh` — one executable implementation instead of a bash/python drift pair, following the `lib/fingerprint.jq` precedent.

---

### Task 1: `lib/identity.py` — host normalisation + identity keys

**Files:**
- Create: `skills/_ultra-engine/scripts/lib/identity.py`
- Test: `skills/_ultra-engine/tests/test_identity.py`
- Modify: `skills/_ultra-engine/SKILL.md` (add table row)

**Interfaces:**
- Produces: `norm_host(url: str) -> str` (lowercased registrable host: scheme, `www.`, path/query/fragment, port, userinfo, trailing dot stripped) and `identity_key(url: str, category: str) -> str` returning `"<host>|<category>"`. CLI: `python3 $SCRIPTS/lib/identity.py normalise <url>` and `python3 $SCRIPTS/lib/identity.py key <url> <category>`. Tasks 2, 4, 5 import these.

- [ ] **Step 1: Write the failing test**

```python
# skills/_ultra-engine/tests/test_identity.py
import os, subprocess, sys, unittest

SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "scripts")
sys.path.insert(0, os.path.join(SCRIPTS, "lib"))
from identity import norm_host, identity_key  # noqa: E402


class TestNormHost(unittest.TestCase):
    def test_spelling_variants_collapse(self):
        for u in ("https://WWW.Example.com/jobs?x=1",
                  "http://example.com./",
                  "example.com",
                  "https://user@example.com:443/board#top"):
            self.assertEqual("example.com", norm_host(u), u)

    def test_subdomain_is_significant(self):
        self.assertEqual("jobs.example.com", norm_host("https://jobs.example.com/"))

    def test_identity_key(self):
        self.assertEqual("malt.nl|freelance-marketplace",
                         identity_key("https://www.Malt.nl/", "freelance-marketplace"))

    def test_cli(self):
        out = subprocess.run(
            ["python3", os.path.join(SCRIPTS, "lib", "identity.py"),
             "key", "https://www.jobs.lu/en/", "national-board"],
            capture_output=True, text=True)
        self.assertEqual(0, out.returncode)
        self.assertEqual("jobs.lu|national-board", out.stdout.strip())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd skills/_ultra-engine/tests && python3 -m unittest test_identity -v`
Expected: FAIL/ERROR with `ModuleNotFoundError: No module named 'identity'`

- [ ] **Step 3: Write the implementation**

```python
#!/usr/bin/env python3
# skills/_ultra-engine/scripts/lib/identity.py
"""THE host-identity normalisation. Never re-derive elsewhere (spec D11).

Identity = normalised homepage host + category. Mutable endpoint URLs are
deliberately excluded from identity.
"""
import re
import sys


def norm_host(url):
    h = url.strip().lower()
    h = re.sub(r'^[a-z][a-z0-9+.-]*://', '', h)      # scheme
    h = h.split('/', 1)[0].split('?', 1)[0].split('#', 1)[0]
    h = h.rsplit('@', 1)[-1]                          # userinfo
    h = h.split(':', 1)[0]                            # port
    if h.startswith('www.'):
        h = h[4:]
    return h.rstrip('.')


def identity_key(url, category):
    return "%s|%s" % (norm_host(url), category)


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "normalise":
        print(norm_host(sys.argv[2]))
    elif len(sys.argv) >= 4 and sys.argv[1] == "key":
        print(identity_key(sys.argv[2], sys.argv[3]))
    else:
        print("usage: identity.py normalise <url> | key <url> <category>",
              file=sys.stderr)
        sys.exit(2)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd skills/_ultra-engine/tests && python3 -m unittest test_identity -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Add the SKILL.md table row**

In `skills/_ultra-engine/SKILL.md`, add to the script table (after the `profile_hash` row):

```markdown
| identity | `python3 $SCRIPTS/lib/identity.py normalise <url>` / `key <url> <category>` | THE host-identity normalisation (`domain\|category`); catalogue/lifecycle scripts import it — never re-derive. |
```

- [ ] **Step 6: Run the whole suite, then commit**

Run: `bash skills/_ultra-engine/tests/run.sh`
Expected: `ALL PASS`

```bash
git add skills/_ultra-engine/scripts/lib/identity.py skills/_ultra-engine/tests/test_identity.py skills/_ultra-engine/SKILL.md
git commit -m "Phase 16 Task 1: host-identity normalisation (lib/identity.py)"
```

---

### Task 2: `catalog.py` — catalogue validate / select / config-read

**Files:**
- Create: `skills/_ultra-engine/scripts/catalog.py`
- Test: `skills/_ultra-engine/tests/test_catalog.py`
- Create: `skills/_ultra-engine/tests/fixtures/catalogue-mini.json`
- Modify: `skills/_ultra-engine/SKILL.md` (add table row)

**Interfaces:**
- Consumes: `identity_key` from Task 1.
- Produces:
  - `python3 $SCRIPTS/catalog.py validate <catalogue.json>` → exit 0 + `ok`, or exit 2 with one error per line on stderr.
  - `python3 $SCRIPTS/catalog.py select <catalogue.json> --scope <eu-nl|eu-broad>` → JSON array of candidate objects on stdout, each annotated with `"pack": "<pack-id>"`, ordered by pack `priority` then in-pack order. `eu-broad` is a strict superset of `eu-nl`.
  - `python3 $SCRIPTS/catalog.py config-read <user-profile.json>` → `{"source_scope": "...", "source_refresh": "..."}` with defaults applied **without writing**; exit 2 on invalid stored values.
- Catalogue file contract (parity with Codex, `catalog_version` reset to 1 for our derivation): top-level `{catalog_version, default_scope, identity_aliases[], retired_identities[], packs[]}`; pack `{id, priority, scopes[], countries[], sources[]}`; candidate source = registry-entry fields minus `priority`/`verified_at`, plus catalogue-only `lane_tags[]` (optional), `auth_required`, `evidence_url`, `evidence_checked_at` (required).

- [ ] **Step 1: Write the fixture**

```json
{
  "catalog_version": 1,
  "default_scope": "eu-nl",
  "identity_aliases": [],
  "retired_identities": ["deadboard.example|remote-board"],
  "packs": [
    {
      "id": "eu-core", "priority": 1, "scopes": ["eu-nl", "eu-broad"], "countries": ["*"],
      "sources": [
        {
          "name": "EU Remote Jobs", "url": "https://euremotejobs.com/", "category": "remote-board",
          "access_lane": "html", "endpoint": "https://euremotejobs.com/",
          "needs_key": false, "needs_slug": false,
          "poll_method": "GET the public board; filter EU/EMEA technical roles client-side.",
          "notes": "EU-time-zone board.",
          "auth_required": false,
          "evidence_url": "https://euremotejobs.com/", "evidence_checked_at": "2026-07-14T09:00:00Z"
        }
      ]
    },
    {
      "id": "benelux", "priority": 2, "scopes": ["eu-nl", "eu-broad"], "countries": ["NL", "BE", "LU"],
      "sources": [
        {
          "name": "Jobs.lu", "url": "https://www.jobs.lu/", "category": "national-board",
          "access_lane": "html", "endpoint": "https://www.jobs.lu/en/it-jobs",
          "needs_key": false, "needs_slug": false,
          "poll_method": "GET the IT listing pages; filter client-side.",
          "notes": "Luxembourg national board.",
          "auth_required": false,
          "evidence_url": "https://www.jobs.lu/", "evidence_checked_at": "2026-07-14T09:00:00Z"
        }
      ]
    },
    {
      "id": "authenticated-marketplaces", "priority": 3, "scopes": ["eu-broad"], "countries": ["*"],
      "sources": [
        {
          "name": "Upwork", "url": "https://www.upwork.com/", "category": "freelance-marketplace",
          "access_lane": "extension", "endpoint": "",
          "needs_key": false, "needs_slug": false,
          "poll_method": "extension browse of saved searches (logged in).",
          "notes": "Global marketplace; login required to search.",
          "auth_required": true,
          "evidence_url": "https://www.upwork.com/", "evidence_checked_at": "2026-07-14T09:00:00Z"
        }
      ]
    }
  ]
}
```

Save as `skills/_ultra-engine/tests/fixtures/catalogue-mini.json`.

- [ ] **Step 2: Write the failing test**

```python
# skills/_ultra-engine/tests/test_catalog.py
import copy, json, os, subprocess, tempfile, unittest

HERE = os.path.dirname(__file__)
SCRIPT = os.path.join(HERE, "..", "scripts", "catalog.py")
FIXTURE = os.path.join(HERE, "fixtures", "catalogue-mini.json")


def run(*args):
    return subprocess.run(["python3", SCRIPT] + list(args),
                          capture_output=True, text=True)


def tmp_json(data):
    f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    json.dump(data, f)
    f.close()
    return f.name


class TestValidate(unittest.TestCase):
    def test_fixture_is_valid(self):
        r = run("validate", FIXTURE)
        self.assertEqual(0, r.returncode, r.stderr)
        self.assertEqual("ok", r.stdout.strip())

    def test_duplicate_identity_across_packs_rejected(self):
        cat = json.load(open(FIXTURE))
        dupe = copy.deepcopy(cat["packs"][0]["sources"][0])
        dupe["name"] = "EU Remote Jobs (again)"
        dupe["url"] = "http://WWW.euremotejobs.com"     # spelling variant, same identity
        cat["packs"][1]["sources"].append(dupe)
        r = run("validate", tmp_json(cat))
        self.assertEqual(2, r.returncode)
        self.assertIn("duplicate identity", r.stderr)

    def test_bad_scope_rejected(self):
        cat = json.load(open(FIXTURE))
        cat["packs"][0]["scopes"] = ["global"]
        r = run("validate", tmp_json(cat))
        self.assertEqual(2, r.returncode)

    def test_linkedin_candidate_rejected(self):
        cat = json.load(open(FIXTURE))
        cat["packs"][0]["sources"][0]["category"] = "linkedin"
        r = run("validate", tmp_json(cat))
        self.assertEqual(2, r.returncode)
        self.assertIn("linkedin", r.stderr)

    def test_missing_evidence_rejected(self):
        cat = json.load(open(FIXTURE))
        del cat["packs"][0]["sources"][0]["evidence_checked_at"]
        r = run("validate", tmp_json(cat))
        self.assertEqual(2, r.returncode)


class TestSelect(unittest.TestCase):
    def test_eu_nl_excludes_broad_only_packs(self):
        r = run("select", FIXTURE, "--scope", "eu-nl")
        self.assertEqual(0, r.returncode, r.stderr)
        names = [c["name"] for c in json.loads(r.stdout)]
        self.assertEqual(["EU Remote Jobs", "Jobs.lu"], names)

    def test_eu_broad_is_superset_and_ordered(self):
        r = run("select", FIXTURE, "--scope", "eu-broad")
        got = json.loads(r.stdout)
        self.assertEqual(["EU Remote Jobs", "Jobs.lu", "Upwork"],
                         [c["name"] for c in got])
        self.assertEqual(["eu-core", "benelux", "authenticated-marketplaces"],
                         [c["pack"] for c in got])

    def test_invalid_scope_rejected(self):
        r = run("select", FIXTURE, "--scope", "everywhere")
        self.assertEqual(2, r.returncode)


class TestConfigRead(unittest.TestCase):
    def test_defaults_without_write(self):
        p = tmp_json({"schema_version": 2, "x_custom": {"a": 1}})
        before = open(p, "rb").read()
        r = run("config-read", p)
        self.assertEqual(0, r.returncode, r.stderr)
        self.assertEqual({"source_scope": "eu-nl", "source_refresh": "manual"},
                         json.loads(r.stdout))
        self.assertEqual(before, open(p, "rb").read())  # read never writes

    def test_stored_values_returned(self):
        p = tmp_json({"ultramode": {"source_scope": "eu-broad"}})
        self.assertEqual("eu-broad", json.loads(run("config-read", p).stdout)["source_scope"])

    def test_invalid_values_rejected(self):
        self.assertEqual(2, run("config-read", tmp_json(
            {"ultramode": {"source_scope": "global"}})).returncode)
        self.assertEqual(2, run("config-read", tmp_json(
            {"ultramode": {"source_refresh": "weekly"}})).returncode)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd skills/_ultra-engine/tests && python3 -m unittest test_catalog -v`
Expected: every test ERRORs (script missing → returncode 2 with python "No such file" on stderr — the validate/select success cases fail).

- [ ] **Step 4: Write the implementation**

```python
#!/usr/bin/env python3
# skills/_ultra-engine/scripts/catalog.py
"""Source-catalogue validate/select + scope config-read. See test_catalog.py."""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
from identity import identity_key  # noqa: E402

SCOPES = ("eu-nl", "eu-broad")
REFRESH = ("manual",)
CATEGORIES = ("ats-provider", "remote-board", "aggregator", "national-board",
              "freelance-marketplace", "community")
LANES = ("api", "rss", "html", "extension")
SOURCE_REQUIRED = ("name", "url", "category", "access_lane", "endpoint",
                   "needs_key", "needs_slug", "poll_method", "notes",
                   "auth_required", "evidence_url", "evidence_checked_at")


def fail(errs):
    for e in errs:
        print(e, file=sys.stderr)
    sys.exit(2)


def validate(cat):
    errs = []
    if not isinstance(cat.get("catalog_version"), int) or cat["catalog_version"] < 1:
        errs.append("catalog_version must be an int >= 1")
    if cat.get("default_scope") not in SCOPES:
        errs.append("default_scope must be one of %s" % (SCOPES,))
    for k in ("identity_aliases", "retired_identities", "packs"):
        if not isinstance(cat.get(k), list):
            errs.append("%s must be a list" % k)
            cat[k] = []
    pack_ids, seen = set(), {}
    for p in cat["packs"]:
        pid = p.get("id") or "?"
        if pid in pack_ids:
            errs.append("duplicate pack id: %s" % pid)
        pack_ids.add(pid)
        if not isinstance(p.get("priority"), int):
            errs.append("%s: priority must be an int" % pid)
        scopes = p.get("scopes") or []
        if not scopes or not set(scopes) <= set(SCOPES):
            errs.append("%s: scopes must be a non-empty subset of %s" % (pid, (SCOPES,)))
        if not isinstance(p.get("countries"), list):
            errs.append("%s: countries must be a list" % pid)
        for s in p.get("sources") or []:
            label = "%s/%s" % (pid, s.get("name", "?"))
            missing = [k for k in SOURCE_REQUIRED if k not in s]
            if missing:
                errs.append("%s: missing fields %s" % (label, missing))
                continue
            if s["category"] == "linkedin":
                errs.append("%s: linkedin is never a catalogue candidate" % label)
                continue
            if s["category"] not in CATEGORIES:
                errs.append("%s: bad category %r" % (label, s["category"]))
            if s["access_lane"] not in LANES:
                errs.append("%s: bad access_lane %r" % (label, s["access_lane"]))
            if s["access_lane"] in ("api", "rss", "html") and not s["endpoint"]:
                errs.append("%s: endpoint required for lane %s" % (label, s["access_lane"]))
            if "priority" in s or "verified_at" in s:
                errs.append("%s: priority/verified_at are registry fields, not catalogue fields" % label)
            key = identity_key(s["url"], s["category"])
            if key in seen:
                errs.append("duplicate identity %s (%s vs %s)" % (key, seen[key], label))
            seen[key] = label
    return errs


def select(cat, scope):
    out = []
    for p in sorted(cat["packs"], key=lambda p: p["priority"]):
        if scope in p["scopes"]:
            for s in p["sources"]:
                c = dict(s)
                c["pack"] = p["id"]
                out.append(c)
    return out


def config_read(profile):
    um = profile.get("ultramode") or {}
    scope = um.get("source_scope", "eu-nl")
    refresh = um.get("source_refresh", "manual")
    errs = []
    if scope not in SCOPES:
        errs.append("invalid ultramode.source_scope: %r (allowed: %s)" % (scope, (SCOPES,)))
    if refresh not in REFRESH:
        errs.append("invalid ultramode.source_refresh: %r (allowed: %s)" % (refresh, (REFRESH,)))
    if errs:
        fail(errs)
    return {"source_scope": scope, "source_refresh": refresh}


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate")
    v.add_argument("catalogue")
    s = sub.add_parser("select")
    s.add_argument("catalogue")
    s.add_argument("--scope", required=True)
    c = sub.add_parser("config-read")
    c.add_argument("profile")
    a = ap.parse_args()

    if a.cmd == "validate":
        errs = validate(json.load(open(a.catalogue)))
        if errs:
            fail(errs)
        print("ok")
    elif a.cmd == "select":
        if a.scope not in SCOPES:
            fail(["invalid scope: %r (allowed: %s)" % (a.scope, (SCOPES,))])
        cat = json.load(open(a.catalogue))
        errs = validate(cat)
        if errs:
            fail(errs)
        json.dump(select(cat, a.scope), sys.stdout, indent=2)
        print()
    elif a.cmd == "config-read":
        json.dump(config_read(json.load(open(a.profile))), sys.stdout)
        print()


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd skills/_ultra-engine/tests && python3 -m unittest test_catalog -v`
Expected: PASS (11 tests)

- [ ] **Step 6: Add the SKILL.md table row**

```markdown
| catalog | `python3 $SCRIPTS/catalog.py validate <catalogue>` / `select <catalogue> --scope <eu-nl\|eu-broad>` / `config-read $WS/user-profile.json` | Packaged-catalogue schema validation; deterministic scope selection (candidates annotated with `pack`); effective scope/refresh config with defaults, read-only (D7). |
```

- [ ] **Step 7: Run the whole suite, then commit**

Run: `bash skills/_ultra-engine/tests/run.sh` → `ALL PASS`

```bash
git add skills/_ultra-engine/scripts/catalog.py skills/_ultra-engine/tests/test_catalog.py skills/_ultra-engine/tests/fixtures/catalogue-mini.json skills/_ultra-engine/SKILL.md
git commit -m "Phase 16 Task 2: catalogue validate/select + config-read (catalog.py)"
```

---

### Task 3: config write recipe — unknown-key preservation test

**Files:**
- Test: `skills/_ultra-engine/tests/test_config_scope.sh`

**Interfaces:**
- Consumes: `catalog.py config-read` (Task 2).
- Produces: the **documented write recipe** that Task 9's `/sources scope` prose uses verbatim: `jq '.ultramode.source_scope = "<value>"' user-profile.json > user-profile.json.tmp && jq -e . user-profile.json.tmp >/dev/null && mv user-profile.json.tmp user-profile.json`. This task pins its semantics with a test so prose and reality cannot drift.

- [ ] **Step 1: Write the failing test**

```bash
#!/bin/bash
# skills/_ultra-engine/tests/test_config_scope.sh
. "$(dirname "$0")/helpers.sh"
C="$(dirname "$0")/../scripts/catalog.py"
tmp=$(mktemp)
cat > "$tmp" <<'EOF'
{"schema_version": 2, "x_custom": {"keep": true}, "ultramode": {"api_keys": {"adzuna": "k"}}}
EOF

# The documented /sources scope write recipe (verbatim from sources/SKILL.md § scope):
jq '.ultramode.source_scope = "eu-broad"' "$tmp" > "$tmp.tmp" && jq -e . "$tmp.tmp" >/dev/null && mv "$tmp.tmp" "$tmp"

assert_eq "eu-broad" "$(python3 "$C" config-read "$tmp" | jq -r .source_scope)" "write recipe sets scope"
assert_eq "true" "$(jq -r '.x_custom.keep' "$tmp")" "unknown top-level keys preserved"
assert_eq "k" "$(jq -r '.ultramode.api_keys.adzuna' "$tmp")" "sibling ultramode keys preserved"
assert_eq "manual" "$(python3 "$C" config-read "$tmp" | jq -r .source_refresh)" "refresh still defaults"
rm -f "$tmp"; finish
```

- [ ] **Step 2: Run test to verify it currently passes end-to-end**

Run: `bash skills/_ultra-engine/tests/test_config_scope.sh`
Expected: `checks=4 fails=0` (this test pins existing jq behaviour + Task 2's reader — it must pass immediately; if it fails, the recipe or reader is wrong and must be fixed before proceeding).

- [ ] **Step 3: Run the whole suite, then commit**

Run: `bash skills/_ultra-engine/tests/run.sh` → `ALL PASS`

```bash
git add skills/_ultra-engine/tests/test_config_scope.sh
git commit -m "Phase 16 Task 3: pin the scope write recipe (unknown-key preservation)"
```

---

### Task 4: `sources.json` v2 — migration + auth-state scripts + schema docs

**Files:**
- Create: `skills/_ultra-engine/scripts/migrate_sources.py`
- Create: `skills/_ultra-engine/scripts/auth_state.sh`
- Test: `skills/_ultra-engine/tests/test_migrate_sources.py`
- Test: `skills/_ultra-engine/tests/test_auth_state.sh`
- Create: `skills/_ultra-engine/tests/fixtures/sources-v1-compat.json`
- Modify: `skills/shared-references/canonical-schemas.md` (§ `sources.json`)
- Modify: `skills/_ultra-engine/SKILL.md` (two table rows)

**Interfaces:**
- Produces:
  - `python3 $SCRIPTS/migrate_sources.py <sources.json>` — v1→v2 in place (atomic): sets `schema_version: 2`, adds top-level `identity_aliases: []` + `retired_identities: []` if absent, gives every entry an `auth_state` (default heuristics below). Idempotent; prints `{"migrated": bool, "schema_version": 2, "sources": N}`.
  - `bash $SCRIPTS/auth_state.sh set <sources.json> <name> <state> <ISO8601>` — validates the enum + source name, atomically writes `auth_state` + `auth_state_observed_at`. `bash $SCRIPTS/auth_state.sh get <sources.json> <name>` prints the state.
- Default heuristics (spec §3 WS-C): `category == "linkedin"` → `auth-required`; `access_lane == "extension"` AND `notes`+`poll_method` match `/login|sign[ -]?in|sign[ -]?up|account|credential/i` → `auth-required`; else `public`. `auth_state_observed_at` is **omitted** until the first real observation (Phase 14 "omitted when absent — never null" convention).
- Tasks 5, 9, 10 require `schema_version >= 2`.

- [ ] **Step 1: Write the v1 compat fixture** (shape of a real pre-Phase-16 registry)

```json
{
  "schema_version": 1,
  "base_country": "Netherlands",
  "target_geography": ["Netherlands", "remote-EU"],
  "priority_order": ["Malt", "RemoteOK"],
  "backbone": ["Adzuna"],
  "sources": [
    {"name": "LinkedIn", "url": "https://www.linkedin.com", "category": "linkedin",
     "access_lane": "extension", "endpoint": "", "needs_key": false, "needs_slug": false,
     "priority": 1, "poll_method": "adapter", "notes": "The richest surface.",
     "verified_at": "2026-07-01T00:00:00Z"},
    {"name": "Malt", "url": "https://www.malt.nl", "category": "freelance-marketplace",
     "access_lane": "extension", "endpoint": "", "needs_key": false, "needs_slug": false,
     "priority": 2, "poll_method": "extension browse", "notes": "Login required to search projects.",
     "verified_at": "2026-07-01T00:00:00Z", "last_swept_at": "2026-07-01"},
    {"name": "RemoteOK", "url": "https://remoteok.com", "category": "remote-board",
     "access_lane": "api", "endpoint": "https://remoteok.com/api", "needs_key": false,
     "needs_slug": false, "priority": 3, "poll_method": "GET the JSON feed",
     "notes": "Whole-board remote feed.", "verified_at": "2026-07-01T00:00:00Z"}
  ]
}
```

Save as `skills/_ultra-engine/tests/fixtures/sources-v1-compat.json`.

- [ ] **Step 2: Write the failing migration test**

```python
# skills/_ultra-engine/tests/test_migrate_sources.py
import json, os, shutil, subprocess, tempfile, unittest

HERE = os.path.dirname(__file__)
SCRIPT = os.path.join(HERE, "..", "scripts", "migrate_sources.py")
FIXTURE = os.path.join(HERE, "fixtures", "sources-v1-compat.json")


def run(path):
    return subprocess.run(["python3", SCRIPT, path], capture_output=True, text=True)


class TestMigrate(unittest.TestCase):
    def setUp(self):
        self.path = tempfile.mktemp(suffix=".json")
        shutil.copy(FIXTURE, self.path)

    def tearDown(self):
        os.unlink(self.path)

    def test_v1_round_trip(self):
        r = run(self.path)
        self.assertEqual(0, r.returncode, r.stderr)
        d = json.load(open(self.path))
        self.assertEqual(2, d["schema_version"])
        self.assertEqual([], d["identity_aliases"])
        self.assertEqual([], d["retired_identities"])
        by = {s["name"]: s for s in d["sources"]}
        self.assertEqual("auth-required", by["LinkedIn"]["auth_state"])   # linkedin heuristic
        self.assertEqual("auth-required", by["Malt"]["auth_state"])       # login-wall notes heuristic
        self.assertEqual("public", by["RemoteOK"]["auth_state"])          # everything else
        for s in d["sources"]:
            self.assertNotIn("auth_state_observed_at", s)                 # omitted until observed
        # untouched fields survive
        self.assertEqual("2026-07-01", by["Malt"]["last_swept_at"])
        self.assertEqual(["Malt", "RemoteOK"], d["priority_order"])

    def test_idempotent(self):
        run(self.path)
        before = open(self.path).read()
        r = run(self.path)
        self.assertEqual(0, r.returncode)
        self.assertFalse(json.loads(r.stdout)["migrated"])
        self.assertEqual(before, open(self.path).read())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run to verify it fails** — `cd skills/_ultra-engine/tests && python3 -m unittest test_migrate_sources -v` → ERROR (script missing).

- [ ] **Step 4: Write `migrate_sources.py`**

```python
#!/usr/bin/env python3
# skills/_ultra-engine/scripts/migrate_sources.py
"""sources.json v1 -> v2 (Phase 16): auth_state + lifecycle lists. Idempotent, atomic."""
import json
import os
import re
import sys

LOGIN_RE = re.compile(r"login|sign[ -]?in|sign[ -]?up|account|credential", re.I)


def default_state(s):
    if s.get("category") == "linkedin":
        return "auth-required"
    blob = "%s %s" % (s.get("notes", ""), s.get("poll_method", ""))
    if s.get("access_lane") == "extension" and LOGIN_RE.search(blob):
        return "auth-required"
    return "public"


def main():
    path = sys.argv[1]
    d = json.load(open(path))
    if d.get("schema_version", 1) >= 2:
        print(json.dumps({"migrated": False, "schema_version": d["schema_version"],
                          "sources": len(d.get("sources", []))}))
        return
    d["schema_version"] = 2
    d.setdefault("identity_aliases", [])
    d.setdefault("retired_identities", [])
    for s in d.get("sources", []):
        s.setdefault("auth_state", default_state(s))
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(d, f, indent=2)
        f.write("\n")
    json.load(open(tmp))
    os.replace(tmp, path)
    print(json.dumps({"migrated": True, "schema_version": 2,
                      "sources": len(d["sources"])}))


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run to verify migration tests pass** — `python3 -m unittest test_migrate_sources -v` → PASS (2 tests).

- [ ] **Step 6: Write the failing auth_state test**

```bash
#!/bin/bash
# skills/_ultra-engine/tests/test_auth_state.sh
. "$(dirname "$0")/helpers.sh"
A="$(dirname "$0")/../scripts/auth_state.sh"
M="$(dirname "$0")/../scripts/migrate_sources.py"
FX="$(dirname "$0")/fixtures/sources-v1-compat.json"
tmp=$(mktemp); cp "$FX" "$tmp"; python3 "$M" "$tmp" >/dev/null

assert_eq "auth-required" "$(bash "$A" get "$tmp" "Malt")" "get reads state"
assert_ok bash "$A" set "$tmp" "Malt" "signed-in" "2026-07-14T10:00:00Z"
assert_eq "signed-in" "$(bash "$A" get "$tmp" "Malt")" "set transitions state"
assert_eq "2026-07-14T10:00:00Z" "$(jq -r '.sources[]|select(.name=="Malt").auth_state_observed_at' "$tmp")" "observed_at stamped"
assert_fail bash "$A" set "$tmp" "Malt" "logged-in" "2026-07-14T10:00:00Z"   # bad enum
assert_fail bash "$A" set "$tmp" "Nope" "signed-in" "2026-07-14T10:00:00Z"   # unknown source
assert_eq "signed-in" "$(bash "$A" get "$tmp" "Malt")" "failed set leaves state untouched"
rm -f "$tmp"; finish
```

- [ ] **Step 7: Run to verify it fails** — `bash skills/_ultra-engine/tests/test_auth_state.sh` → FAILs (script missing).

- [ ] **Step 8: Write `auth_state.sh`**

```bash
#!/bin/bash
# Usage: auth_state.sh set <sources.json> <name> <state> <ISO8601>
#        auth_state.sh get <sources.json> <name>
# States are observations from sweep outcomes, never inferred from elapsed time (spec §6.4).
set -eu
cmd="$1"; f="$2"; name="$3"
case "$cmd" in
  set)
    state="$4"; at="$5"
    case "$state" in public|auth-required|signed-in|session-expired) ;;
      *) echo "invalid auth_state: $state (allowed: public|auth-required|signed-in|session-expired)" >&2; exit 2;;
    esac
    jq -e --arg n "$name" '.sources[] | select(.name==$n)' "$f" >/dev/null \
      || { echo "unknown source: $name" >&2; exit 2; }
    jq --arg n "$name" --arg s "$state" --arg at "$at" '
      .sources |= map(if .name==$n then . + {auth_state: $s, auth_state_observed_at: $at} else . end)' "$f" > "$f.tmp" \
      && jq -e . "$f.tmp" >/dev/null && mv "$f.tmp" "$f"
    ;;
  get)
    jq -r --arg n "$name" '.sources[] | select(.name==$n) | .auth_state // "public"' "$f"
    ;;
  *) echo "usage: auth_state.sh set <sources.json> <name> <state> <ISO8601> | get <sources.json> <name>" >&2; exit 2;;
esac
```

- [ ] **Step 9: Run to verify it passes** — `bash skills/_ultra-engine/tests/test_auth_state.sh` → `checks=7 fails=0`.

- [ ] **Step 10: Update `canonical-schemas.md` § `sources.json`**

In the `sources.json` JSON block: change `"schema_version": 1` → `"schema_version": 2`; after `"backbone"` add:

```json
  "identity_aliases": ["array — [{from, to}] identity-key redirects ('domain|category' strings) for domain/category migrations; default []"],
  "retired_identities": ["array — identity keys ('domain|category') intentionally retired via /sources retire; a retired identity is never re-admitted by a rebuild. Absence from a catalogue is NOT retirement — only a tombstone here is (Phase 16)."],
```

And in the per-source entry, after `"verified_at"` add:

```json
      "auth_state": "public | auth-required | signed-in | session-expired — non-secret session observation (Phase 16). NEVER a credential store; sign-in lives in the user's Chrome profile. Written from observed sweep outcomes only.",
      "auth_state_observed_at": "ISO8601 — when auth_state was last observed. Omitted until the first observation; never null.",
      "pack": "string — provenance: the catalogue pack that admitted this entry (e.g. 'benelux', 'nl-core'). Omitted for non-catalogue sources. Packs 'benelux' and 'nl-core' get rotation/poll priority (Phase 16 D4)."
```

After the JSON block, append one paragraph:

```markdown
**Phase 16 (schema_version 2):** migration is `python3 $SCRIPTS/migrate_sources.py $WS/sources.json` — run by `/sources` and `/ultramode` on load whenever `schema_version < 2` (idempotent; defaults `auth_state` from category/notes heuristics). The four catalogue-only candidate fields (`lane_tags`, `auth_required`, `evidence_url`, `evidence_checked_at`) must never appear in this file; `registry_lifecycle.py` rejects them at merge time.
```

- [ ] **Step 11: Add the two SKILL.md table rows**

```markdown
| migrate_sources | `python3 $SCRIPTS/migrate_sources.py $WS/sources.json` | sources.json v1→v2 (auth_state + lifecycle lists), idempotent, atomic. Orchestrators run it on load when `schema_version < 2`. |
| auth_state | `bash $SCRIPTS/auth_state.sh set $WS/sources.json <name> <state> <ISO>` / `get <name>` | Observed auth-state transitions (`public\|auth-required\|signed-in\|session-expired`) + timestamp; never inferred, never secret-bearing. |
```

- [ ] **Step 12: Run the whole suite, then commit**

Run: `bash skills/_ultra-engine/tests/run.sh` → `ALL PASS`

```bash
git add skills/_ultra-engine/scripts/migrate_sources.py skills/_ultra-engine/scripts/auth_state.sh skills/_ultra-engine/tests/test_migrate_sources.py skills/_ultra-engine/tests/test_auth_state.sh skills/_ultra-engine/tests/fixtures/sources-v1-compat.json skills/shared-references/canonical-schemas.md skills/_ultra-engine/SKILL.md
git commit -m "Phase 16 Task 4: sources.json v2 — auth_state migration + transition script"
```

---

### Task 5: `project.py` — candidate → registry-entry projection

**Files:**
- Create: `skills/_ultra-engine/scripts/project.py`
- Test: `skills/_ultra-engine/tests/test_project.py`
- Modify: `skills/_ultra-engine/SKILL.md` (add table row)

**Interfaces:**
- Consumes: a single candidate object (as emitted by `catalog.py select`, possibly with `access_lane` flipped to `extension` by the live probe) on a file or stdin.
- Produces: `python3 $SCRIPTS/project.py --candidate <file|-> --priority N --verified-at <ISO8601>` → one registry-entry JSON object on stdout: catalogue-only fields stripped; `priority` + `verified_at` set; `auth_state` = `"auth-required"` if candidate `auth_required` is true else `"public"`; `pack` passed through. Exit 2 on: missing/malformed `verified_at`, unknown candidate fields, empty endpoint on an api/rss/html lane, `category: linkedin`. Task 6 consumes arrays of these entries.

- [ ] **Step 1: Write the failing test**

```python
# skills/_ultra-engine/tests/test_project.py
import json, os, subprocess, tempfile, unittest

HERE = os.path.dirname(__file__)
SCRIPT = os.path.join(HERE, "..", "scripts", "project.py")

CAND = {
    "name": "Jobs.lu", "url": "https://www.jobs.lu/", "category": "national-board",
    "access_lane": "html", "endpoint": "https://www.jobs.lu/en/it-jobs",
    "needs_key": False, "needs_slug": False,
    "poll_method": "GET the IT listing pages; filter client-side.",
    "notes": "Luxembourg national board.", "pack": "benelux",
    "lane_tags": ["*"], "auth_required": False,
    "evidence_url": "https://www.jobs.lu/", "evidence_checked_at": "2026-07-14T09:00:00Z",
}


def run(cand, *extra):
    f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    json.dump(cand, f)
    f.close()
    args = ["python3", SCRIPT, "--candidate", f.name,
            "--priority", "7", "--verified-at", "2026-07-14T12:00:00Z"] + list(extra)
    return subprocess.run(args, capture_output=True, text=True)


class TestProject(unittest.TestCase):
    def test_projection_strips_catalogue_fields(self):
        r = run(CAND)
        self.assertEqual(0, r.returncode, r.stderr)
        e = json.loads(r.stdout)
        for k in ("lane_tags", "auth_required", "evidence_url", "evidence_checked_at"):
            self.assertNotIn(k, e)
        self.assertEqual(7, e["priority"])
        self.assertEqual("2026-07-14T12:00:00Z", e["verified_at"])
        self.assertEqual("public", e["auth_state"])
        self.assertEqual("benelux", e["pack"])
        self.assertNotIn("auth_state_observed_at", e)

    def test_auth_required_maps_to_state(self):
        c = dict(CAND, auth_required=True, access_lane="extension", endpoint="")
        e = json.loads(run(c).stdout)
        self.assertEqual("auth-required", e["auth_state"])

    def test_bad_verified_at_rejected(self):
        f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        json.dump(CAND, f); f.close()
        r = subprocess.run(["python3", SCRIPT, "--candidate", f.name,
                            "--priority", "7", "--verified-at", "yesterday"],
                           capture_output=True, text=True)
        self.assertEqual(2, r.returncode)

    def test_unknown_field_rejected(self):
        self.assertEqual(2, run(dict(CAND, surprise=1)).returncode)

    def test_empty_endpoint_on_html_rejected(self):
        self.assertEqual(2, run(dict(CAND, endpoint="")).returncode)

    def test_linkedin_rejected(self):
        self.assertEqual(2, run(dict(CAND, category="linkedin")).returncode)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run to verify it fails** — `python3 -m unittest test_project -v` → ERRORs.

- [ ] **Step 3: Write the implementation**

```python
#!/usr/bin/env python3
# skills/_ultra-engine/scripts/project.py
"""Catalogue candidate -> frozen registry entry. The projection boundary (D11)."""
import argparse
import json
import re
import sys

ALLOWED = ("name", "url", "category", "access_lane", "endpoint", "needs_key",
           "needs_slug", "poll_method", "notes", "pack")
CATALOGUE_ONLY = ("lane_tags", "auth_required", "evidence_url", "evidence_checked_at")
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$")


def die(msg):
    print(msg, file=sys.stderr)
    sys.exit(2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--priority", type=int, required=True)
    ap.add_argument("--verified-at", dest="verified_at", required=True)
    a = ap.parse_args()

    if not ISO.match(a.verified_at):
        die("verified_at must be ISO8601 (a live probe timestamp — the admission proof)")
    src = sys.stdin if a.candidate == "-" else open(a.candidate)
    c = json.load(src)

    unknown = set(c) - set(ALLOWED) - set(CATALOGUE_ONLY)
    if unknown:
        die("unknown candidate fields: %s" % sorted(unknown))
    if c.get("category") == "linkedin":
        die("linkedin entries are ensured by the dispatcher, never projected")
    if c.get("access_lane") in ("api", "rss", "html") and not c.get("endpoint"):
        die("endpoint required for access_lane %s" % c.get("access_lane"))

    entry = {k: c[k] for k in ALLOWED if k in c}
    entry["priority"] = a.priority
    entry["verified_at"] = a.verified_at
    entry["auth_state"] = "auth-required" if c.get("auth_required") else "public"
    json.dump(entry, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run to verify it passes** — `python3 -m unittest test_project -v` → PASS (6 tests).

- [ ] **Step 5: Add the SKILL.md table row**

```markdown
| project | `python3 $SCRIPTS/project.py --candidate <file\|-> --priority N --verified-at <ISO>` | Catalogue candidate → registry entry: strips catalogue-only fields, requires a probe-time `verified_at`, maps `auth_required` → initial `auth_state`. The projection boundary (D11). |
```

- [ ] **Step 6: Run the whole suite, then commit**

```bash
bash skills/_ultra-engine/tests/run.sh   # ALL PASS
git add skills/_ultra-engine/scripts/project.py skills/_ultra-engine/tests/test_project.py skills/_ultra-engine/SKILL.md
git commit -m "Phase 16 Task 5: projection boundary (project.py)"
```

---

### Task 6: `registry_lifecycle.py` — atomic merge + retire

**Files:**
- Create: `skills/_ultra-engine/scripts/registry_lifecycle.py`
- Test: `skills/_ultra-engine/tests/test_registry_lifecycle.py`
- Modify: `skills/_ultra-engine/SKILL.md` (add table row)

**Interfaces:**
- Consumes: `identity_key` (Task 1); a v2 registry (Task 4); an array of projected entries (Task 5); optionally the catalogue (Task 2 shape) for packaged aliases/tombstones.
- Produces:
  - `python3 $SCRIPTS/registry_lifecycle.py merge --registry <sources.json> --candidates <entries.json> [--catalogue <catalogue.json>] [--expect-sha256 <hex>]` — merges candidates into the registry: identity dedupe (via aliases), tombstone skip, user-source retention (existing entries never removed by a merge), update-in-place for known identities (fields `endpoint`, `poll_method`, `notes`, `verified_at`, `pack`, `priority`; observed `auth_state`/`auth_state_observed_at`/`last_swept_at` preserved), single-linkedin guarantee, exact-count invariant, catalogue-only leak rejection, conflict check, atomic write. Prints `{"retained": N, "added": N, "updated": N, "tombstoned_skipped": N, "total": N}` where `total == retained + added` always.
  - `python3 $SCRIPTS/registry_lifecycle.py retire --registry <sources.json> --name <name>` — removes the entry, appends its identity key to `retired_identities`, scrubs `priority_order`/`backbone` mentions. Prints `{"retired": name, "identity": key, "total": N}`.
  - Exit codes: 2 = validation error; 3 = conflict (`--expect-sha256` mismatch: registry changed since read).

- [ ] **Step 1: Write the failing test**

```python
# skills/_ultra-engine/tests/test_registry_lifecycle.py
import hashlib, json, os, shutil, subprocess, tempfile, unittest

HERE = os.path.dirname(__file__)
SCRIPT = os.path.join(HERE, "..", "scripts", "registry_lifecycle.py")
MIGRATE = os.path.join(HERE, "..", "scripts", "migrate_sources.py")
FIXTURE = os.path.join(HERE, "fixtures", "sources-v1-compat.json")

NEW = {"name": "Jobs.lu", "url": "https://www.jobs.lu/", "category": "national-board",
       "access_lane": "html", "endpoint": "https://www.jobs.lu/en/it-jobs",
       "needs_key": False, "needs_slug": False, "poll_method": "GET listing pages",
       "notes": "Luxembourg national board.", "pack": "benelux", "priority": 7,
       "verified_at": "2026-07-14T12:00:00Z", "auth_state": "public"}


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def run(*args):
    return subprocess.run(["python3", SCRIPT] + list(args), capture_output=True, text=True)


def tmp_json(data):
    f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    json.dump(data, f)
    f.close()
    return f.name


class TestLifecycle(unittest.TestCase):
    def setUp(self):
        self.reg = tempfile.mktemp(suffix=".json")
        shutil.copy(FIXTURE, self.reg)
        subprocess.run(["python3", MIGRATE, self.reg], capture_output=True)

    def tearDown(self):
        os.unlink(self.reg)

    def test_merge_adds_and_retains(self):
        r = run("merge", "--registry", self.reg, "--candidates", tmp_json([NEW]))
        self.assertEqual(0, r.returncode, r.stderr)
        c = json.loads(r.stdout)
        self.assertEqual({"retained": 3, "added": 1, "updated": 0,
                          "tombstoned_skipped": 0, "total": 4}, c)
        d = json.load(open(self.reg))
        self.assertEqual(4, len(d["sources"]))          # user sources retained
        self.assertIn("Jobs.lu", [s["name"] for s in d["sources"]])

    def test_known_identity_updates_and_preserves_observations(self):
        upd = dict(NEW, name="Malt (EU)", url="http://WWW.malt.nl/",  # same identity, new spelling
                   category="freelance-marketplace", access_lane="extension", endpoint="",
                   notes="refreshed", pack="eu-contract", priority=2,
                   auth_state="auth-required")
        r = run("merge", "--registry", self.reg, "--candidates", tmp_json([upd]))
        c = json.loads(r.stdout)
        self.assertEqual((3, 0, 1), (c["retained"], c["added"], c["updated"]), r.stderr)
        malt = [s for s in json.load(open(self.reg))["sources"]
                if s["url"] == "https://www.malt.nl"][0]
        self.assertEqual("refreshed", malt["notes"])            # updated field
        self.assertEqual("Malt", malt["name"])                  # existing name kept
        self.assertEqual("2026-07-01", malt["last_swept_at"])   # observation preserved
        self.assertEqual("auth-required", malt["auth_state"])   # observed state not overwritten

    def test_tombstone_blocks_admission(self):
        d = json.load(open(self.reg))
        d["retired_identities"] = ["jobs.lu|national-board"]
        json.dump(d, open(self.reg, "w"))
        c = json.loads(run("merge", "--registry", self.reg,
                           "--candidates", tmp_json([NEW])).stdout)
        self.assertEqual((0, 1), (c["added"], c["tombstoned_skipped"]))

    def test_alias_redirects_identity(self):
        cat = {"catalog_version": 1, "default_scope": "eu-nl", "packs": [],
               "identity_aliases": [{"from": "jobs.lu|national-board",
                                     "to": "malt.nl|freelance-marketplace"}],
               "retired_identities": []}
        c = json.loads(run("merge", "--registry", self.reg,
                           "--candidates", tmp_json([NEW]),
                           "--catalogue", tmp_json(cat)).stdout)
        self.assertEqual((0, 1), (c["added"], c["updated"]))  # lands on Malt, no new entry

    def test_leaked_catalogue_field_rejected(self):
        r = run("merge", "--registry", self.reg,
                "--candidates", tmp_json([dict(NEW, auth_required=False)]))
        self.assertEqual(2, r.returncode)
        self.assertIn("catalogue-only", r.stderr)

    def test_missing_verified_at_rejected(self):
        bad = dict(NEW); del bad["verified_at"]
        self.assertEqual(2, run("merge", "--registry", self.reg,
                                "--candidates", tmp_json([bad])).returncode)

    def test_second_linkedin_rejected(self):
        li = dict(NEW, name="LinkedIn 2", url="https://linkedin.example", category="linkedin",
                  access_lane="extension", endpoint="")
        self.assertEqual(2, run("merge", "--registry", self.reg,
                                "--candidates", tmp_json([li])).returncode)

    def test_conflict_detected(self):
        r = run("merge", "--registry", self.reg, "--candidates", tmp_json([NEW]),
                "--expect-sha256", "0" * 64)
        self.assertEqual(3, r.returncode)
        r2 = run("merge", "--registry", self.reg, "--candidates", tmp_json([NEW]),
                 "--expect-sha256", sha(self.reg))
        self.assertEqual(0, r2.returncode, r2.stderr)

    def test_retire_writes_tombstone(self):
        run("merge", "--registry", self.reg, "--candidates", tmp_json([NEW]))
        r = run("retire", "--registry", self.reg, "--name", "Jobs.lu")
        self.assertEqual(0, r.returncode, r.stderr)
        d = json.load(open(self.reg))
        self.assertNotIn("Jobs.lu", [s["name"] for s in d["sources"]])
        self.assertIn("jobs.lu|national-board", d["retired_identities"])
        # and a rebuild cannot re-admit it
        c = json.loads(run("merge", "--registry", self.reg,
                           "--candidates", tmp_json([NEW])).stdout)
        self.assertEqual(1, c["tombstoned_skipped"])

    def test_v1_registry_refused(self):
        raw = tempfile.mktemp(suffix=".json")
        shutil.copy(FIXTURE, raw)
        r = run("merge", "--registry", raw, "--candidates", tmp_json([NEW]))
        self.assertEqual(2, r.returncode)
        self.assertIn("migrate", r.stderr)
        os.unlink(raw)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run to verify it fails** — `python3 -m unittest test_registry_lifecycle -v` → ERRORs.

- [ ] **Step 3: Write the implementation**

```python
#!/usr/bin/env python3
# skills/_ultra-engine/scripts/registry_lifecycle.py
"""Atomic sources.json lifecycle: catalogue-admission merge + retirement.

Invariants (spec D11): user sources retained; absence from a catalogue is not
retirement; tombstones block re-admission; aliases redirect identities; exact
counts; single linkedin entry; catalogue-only fields never persisted; atomic,
conflict-aware writes.
"""
import argparse
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
from identity import identity_key  # noqa: E402

CATALOGUE_ONLY = ("lane_tags", "auth_required", "evidence_url", "evidence_checked_at")
UPDATE_FIELDS = ("endpoint", "poll_method", "notes", "verified_at", "pack", "priority")


def die(msg, code=2):
    print(msg, file=sys.stderr)
    sys.exit(code)


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def write_atomic(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    json.load(open(tmp))
    os.replace(tmp, path)


def load_registry(path):
    reg = json.load(open(path))
    if reg.get("schema_version", 1) < 2:
        die("sources.json is schema_version %s — run migrate_sources.py first"
            % reg.get("schema_version", 1))
    return reg


def build_aliases(reg, cat):
    m = {}
    for a in (reg.get("identity_aliases") or []) + ((cat or {}).get("identity_aliases") or []):
        m[a["from"]] = a["to"]
    return m


def resolve(key, aliases):
    seen = set()
    while key in aliases and key not in seen:
        seen.add(key)
        key = aliases[key]
    return key


def merge(a):
    reg = load_registry(a.registry)
    if a.expect_sha256 and sha256(a.registry) != a.expect_sha256:
        die("registry changed since read — re-read and retry", 3)
    cands = json.load(open(a.candidates))
    cat = json.load(open(a.catalogue)) if a.catalogue else None
    aliases = build_aliases(reg, cat)
    retired = set(reg.get("retired_identities") or []) \
        | set((cat or {}).get("retired_identities") or [])

    existing = {}
    for s in reg["sources"]:
        k = resolve(identity_key(s["url"], s["category"]), aliases)
        if k in existing:
            die("duplicate identity already in registry: %s" % k)
        existing[k] = s

    retained = len(reg["sources"])
    added = updated = tomb = 0
    for c in cands:
        leak = set(CATALOGUE_ONLY) & set(c)
        if leak:
            die("catalogue-only fields leaked into candidate %r: %s"
                % (c.get("name", "?"), sorted(leak)))
        if not c.get("verified_at"):
            die("candidate %r has no verified_at — not admissible (never-fabricate)"
                % c.get("name", "?"))
        if c.get("category") == "linkedin":
            die("linkedin entries are ensured by the dispatcher, never catalogue-admitted")
        key = resolve(identity_key(c["url"], c["category"]), aliases)
        if key in retired:
            tomb += 1
            continue
        if key in existing:
            e = existing[key]
            for f in UPDATE_FIELDS:
                if f in c:
                    e[f] = c[f]
            e.setdefault("auth_state", c.get("auth_state", "public"))
            updated += 1
        else:
            existing[key] = c
            added += 1

    out = list(existing.values())
    if sum(1 for s in out if s.get("category") == "linkedin") > 1:
        die("more than one category: linkedin entry")
    if len(out) != retained + added:
        die("exact-count invariant broken: %d != %d retained + %d added"
            % (len(out), retained, added))
    reg["sources"] = out
    write_atomic(a.registry, reg)
    print(json.dumps({"retained": retained, "added": added, "updated": updated,
                      "tombstoned_skipped": tomb, "total": len(out)}))


def retire(a):
    reg = load_registry(a.registry)
    hits = [s for s in reg["sources"] if s["name"] == a.name]
    if not hits:
        die("unknown source: %s" % a.name)
    key = identity_key(hits[0]["url"], hits[0]["category"])
    reg["sources"] = [s for s in reg["sources"] if s["name"] != a.name]
    reg.setdefault("retired_identities", [])
    if key not in reg["retired_identities"]:
        reg["retired_identities"].append(key)
    reg["priority_order"] = [n for n in reg.get("priority_order", []) if n != a.name]
    reg["backbone"] = [n for n in reg.get("backbone", []) if n != a.name]
    write_atomic(a.registry, reg)
    print(json.dumps({"retired": a.name, "identity": key, "total": len(reg["sources"])}))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("merge")
    m.add_argument("--registry", required=True)
    m.add_argument("--candidates", required=True)
    m.add_argument("--catalogue")
    m.add_argument("--expect-sha256", dest="expect_sha256")
    r = sub.add_parser("retire")
    r.add_argument("--registry", required=True)
    r.add_argument("--name", required=True)
    a = ap.parse_args()
    merge(a) if a.cmd == "merge" else retire(a)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run to verify it passes** — `python3 -m unittest test_registry_lifecycle -v` → PASS (10 tests).

- [ ] **Step 5: Add the SKILL.md table row**

```markdown
| registry_lifecycle | `python3 $SCRIPTS/registry_lifecycle.py merge --registry $WS/sources.json --candidates <entries.json> [--catalogue <cat>] [--expect-sha256 <hex>]` / `retire --registry $WS/sources.json --name <name>` | Atomic lifecycle boundary: identity dedupe via aliases, tombstone skip, user-source retention, exact counts, single-linkedin, catalogue-leak rejection, conflict-aware write (exit 3). Retirement = tombstone, never mere absence. |
```

- [ ] **Step 6: Run the whole suite, then commit**

```bash
bash skills/_ultra-engine/tests/run.sh   # ALL PASS
git add skills/_ultra-engine/scripts/registry_lifecycle.py skills/_ultra-engine/tests/test_registry_lifecycle.py skills/_ultra-engine/SKILL.md
git commit -m "Phase 16 Task 6: registry lifecycle merge + retire (atomic, conflict-aware)"
```

---

### Task 7: `rotation.sh` — BENELUX weighting + `pick-all`

**Files:**
- Modify: `skills/_ultra-engine/scripts/rotation.sh`
- Modify: `skills/_ultra-engine/tests/test_rotation.sh`
- Modify: `skills/_ultra-engine/tests/fixtures/sources-mini.json` (add `pack` to one entry)
- Modify: `skills/_ultra-engine/SKILL.md` (update rotation row)

**Interfaces:**
- Consumes: v2 registry entries with optional `pack` (Task 4/6).
- Produces: `rotation.sh pick <sources.json> <N>` — deterministic order now `(BENELUX-priority, last_swept_at, name)` where BENELUX-priority = 0 when `pack` ∈ {`benelux`, `nl-core`} else 1. New: `rotation.sh pick-all <sources.json>` — every extension-lane non-linkedin source in the same order (the `/ultramode super` worklist). `mark` unchanged. Task 11's prose calls `pick-all`.

- [ ] **Step 1: Extend the fixture and write the failing test**

In `skills/_ultra-engine/tests/fixtures/sources-mini.json`, add `"pack": "benelux"` to the `freelance.nl` entry (leave the others without `pack`).

Append to `skills/_ultra-engine/tests/test_rotation.sh` before `finish`:

```bash
# Phase 16: BENELUX pack weighting + pick-all
tmp2=$(mktemp); cp "$FX" "$tmp2"
picks3=$(bash "$R" pick "$tmp2" 2)
assert_eq "freelance.nl
Toptal" "$picks3" "benelux-pack source outranks equally-stale generic ones"
all=$(bash "$R" pick-all "$tmp2")
assert_eq "$(jq -r '[.sources[]|select(.access_lane=="extension" and .category!="linkedin")]|length' "$tmp2")" \
          "$(printf '%s\n' "$all" | grep -c .)" "pick-all returns every extension-lane non-linkedin source"
assert_eq "freelance.nl" "$(printf '%s\n' "$all" | head -1)" "pick-all leads with benelux"
assert_eq "" "$(printf '%s\n' "$all" | grep -x "LinkedIn" || true)" "pick-all excludes linkedin"
rm -f "$tmp2"
```

Note: the existing first assertion (`Toptal / freelance.nl / Malt`) will now expect `freelance.nl / Toptal / Malt` — update that expected string in the same edit, since freelance.nl now carries a priority pack.

- [ ] **Step 2: Run to verify it fails** — `bash skills/_ultra-engine/tests/test_rotation.sh` → FAILs on the new assertions (`pick-all` unknown command; weighting absent).

- [ ] **Step 3: Implement**

Replace `rotation.sh`'s `pick` case and add `pick-all`:

```bash
#!/bin/bash
# Usage: rotation.sh pick <sources.json> <N>
#        rotation.sh pick-all <sources.json>
#        rotation.sh mark <sources.json> <name> <YYYY-MM-DD>
# Order: BENELUX packs (benelux, nl-core) first, then stalest-first, then name (D4).
set -eu
cmd="$1"; f="$2"
ORDER='[ .sources[] | select(.access_lane == "extension" and (.category // "") != "linkedin") ]
  | sort_by([(if ((.pack // "") == "benelux" or (.pack // "") == "nl-core") then 0 else 1 end),
             (.last_swept_at // "0000-00-00"), .name])'
case "$cmd" in
  pick)
    n="$3"
    jq -r --argjson n "$n" "$ORDER | .[:\$n][].name" "$f"
    ;;
  pick-all)
    jq -r "$ORDER | .[].name" "$f"
    ;;
  mark)
    name="$3"; day="$4"
    jq --arg name "$name" --arg day "$day" '
      .sources |= map(if .name == $name then . + {last_swept_at: $day} else . end)' "$f" > "$f.tmp" \
      && jq -e . "$f.tmp" >/dev/null && mv "$f.tmp" "$f"
    ;;
  *) echo "usage: rotation.sh pick <sources.json> <N> | pick-all <sources.json> | mark <sources.json> <name> <date>" >&2; exit 2;;
esac
```

- [ ] **Step 4: Run to verify it passes** — `bash skills/_ultra-engine/tests/test_rotation.sh` → `fails=0`.

- [ ] **Step 5: Update the SKILL.md rotation row**

```markdown
| rotation | `bash $SCRIPTS/rotation.sh pick <sources.json> 4` / `pick-all <sources.json>` / `mark <sources.json> <name> <date>` | Extension-lane order: BENELUX packs (`benelux`, `nl-core`) first, then stalest, then name (D4/D8). `pick` = rotation subset; `pick-all` = the `/ultramode super` worklist. |
```

- [ ] **Step 6: Run the whole suite, then commit**

```bash
bash skills/_ultra-engine/tests/run.sh   # ALL PASS
git add skills/_ultra-engine/scripts/rotation.sh skills/_ultra-engine/tests/test_rotation.sh skills/_ultra-engine/tests/fixtures/sources-mini.json skills/_ultra-engine/SKILL.md
git commit -m "Phase 16 Task 7: BENELUX rotation weighting + pick-all (super worklist)"
```

---

### Task 8: `scorecard.sh` — five-way accounting + missing-artifact disclosures; `login_required` envelope

**Files:**
- Modify: `skills/_ultra-engine/scripts/scorecard.sh`
- Modify: `skills/_ultra-engine/tests/test_scorecard.sh`
- Modify: `skills/shared-references/canonical-schemas.md` (§ `errors[]` codes — add `login_required`)

**Interfaces:**
- Consumes: run-dir artifacts (`sweep-*.json`, `rotation.json`, `merge.json`, `jd-fetch.json`) as today; sweep envelopes may now carry `errors[].code == "login_required"` (a zero-count envelope: `{"status":"ok","counts":{"scanned":0,...,"returned":0,"capped":false},"deltas":[],"errors":[{"code":"login_required","message":"<source> needs sign-in — sign in in the open Chrome tab, then run /ultramode source <name>"}],"continuation_cursor":null}`); `rotation.json` may carry `"mode": "bare"|"super"|"linkedin"|"external"|"source"`.
- Produces: `scorecard.json` gains
  - `"accounting": {"mode": "<mode>", "attempted": N, "completed": N, "login_blocked": N, "failed": N, "rotated_out": N}` where: attempted = number of sweep envelopes; login_blocked = envelopes with a `login_required` error code; failed = envelopes with ≥1 error code other than `login_required` and `returned == 0`; completed = attempted − login_blocked − failed; rotated_out = `rotation.json .rotated_out | length`.
  - Disclosure lines `"jd-fetch.json artifact missing — JD accounting incomplete"` / `"merge.json artifact missing — dedupe accounting incomplete"` whenever those files are absent (D13 hardening — silent zero defaults retired).
- Task 11's report prose renders `accounting` in every mode.

- [ ] **Step 1: Write the failing test additions**

Append to `skills/_ultra-engine/tests/test_scorecard.sh` before `finish` (reuse the file's existing run-dir scaffolding pattern — it already builds a temp run dir with sweep fixtures; follow the same style):

```bash
# Phase 16: five-way accounting + missing-artifact disclosures
rd2=$(mktemp -d)
cat > "$rd2/sweep-ok.json" <<'EOF'
{"status":"ok","counts":{"scanned":10,"matched":3,"dropped_explicit_violation":1,"returned":2,"capped":false},"deltas":[],"errors":[],"continuation_cursor":null}
EOF
cat > "$rd2/sweep-blocked.json" <<'EOF'
{"status":"ok","counts":{"scanned":0,"matched":0,"dropped_explicit_violation":0,"returned":0,"capped":false},"deltas":[],"errors":[{"code":"login_required","message":"Malt needs sign-in — sign in in the open Chrome tab, then run /ultramode source Malt"}],"continuation_cursor":null}
EOF
cat > "$rd2/sweep-dead.json" <<'EOF'
{"status":"ok","counts":{"scanned":0,"matched":0,"dropped_explicit_violation":0,"returned":0,"capped":false},"deltas":[],"errors":[{"code":"sweep_failed","message":"layout dead"}],"continuation_cursor":null}
EOF
echo '{"picked":["Malt"],"rotated_out":["Toptal","YunoJuno"],"mode":"super"}' > "$rd2/rotation.json"
echo '{"jobs":{}}' > "$rd2/tracker-empty.json"
out2=$(bash "$S" "$rd2" "$rd2/tracker-empty.json" 2026-07-14)
assert_eq "super" "$(printf '%s' "$out2" | jq -r .accounting.mode)" "mode from rotation.json"
assert_eq "3" "$(printf '%s' "$out2" | jq -r .accounting.attempted)" "attempted counts envelopes"
assert_eq "1" "$(printf '%s' "$out2" | jq -r .accounting.completed)" "completed excludes blocked+failed"
assert_eq "1" "$(printf '%s' "$out2" | jq -r .accounting.login_blocked)" "login_required counted"
assert_eq "1" "$(printf '%s' "$out2" | jq -r .accounting.failed)" "failure counted"
assert_eq "2" "$(printf '%s' "$out2" | jq -r .accounting.rotated_out)" "rotated_out from rotation.json"
assert_eq "1" "$(printf '%s' "$out2" | jq '[.disclosures[]|select(test("jd-fetch.json artifact missing"))]|length')" "missing jd-fetch disclosed"
assert_eq "1" "$(printf '%s' "$out2" | jq '[.disclosures[]|select(test("merge.json artifact missing"))]|length')" "missing merge disclosed"
rm -rf "$rd2"
```

(`$S` = the scorecard script variable already defined at the top of the test file; if it is named differently there, match the existing name.)

- [ ] **Step 2: Run to verify it fails** — `bash skills/_ultra-engine/tests/test_scorecard.sh` → new assertions FAIL (no `accounting` key).

- [ ] **Step 3: Implement in `scorecard.sh`**

Three edits:

(a) In the sweeps loop, capture error codes — extend the per-envelope value object with `codes`:

```bash
      errors: ($e[0].errors | length),
      codes: ([ $e[0].errors[]? | (.code // "error") ]),
      messages: ([ $e[0].errors[]? | (.message // "error") ])}}]')
```

(b) After the `pipe=` line, add artifact-presence flags:

```bash
jdf_missing=false; [ -f "$rd/jd-fetch.json" ] || jdf_missing=true
merge_missing=false; [ -f "$rd/merge.json" ] || merge_missing=true
```

and pass them into the final jq: `--argjson jdf_missing "$jdf_missing" --argjson merge_missing "$merge_missing"`.

(c) In the final jq program, after the `rotation: $rot,` line add:

```
     accounting:
       ( [ $sweeps[] ] as $sw
       | ([ $sw[] | select(.value.codes | index("login_required")) ] | length) as $blocked
       | ([ $sw[] | select((.value.codes | length) > 0
                           and (.value.codes | index("login_required") | not)
                           and .value.returned == 0) ] | length) as $failed
       | {mode: ($rot.mode // "bare"),
          attempted: ($sw | length),
          completed: (($sw | length) - $blocked - $failed),
          login_blocked: $blocked,
          failed: $failed,
          rotated_out: ($rot.rotated_out | length)} ),
```

and extend `disclosures` with:

```
       + (if $jdf_missing then ["jd-fetch.json artifact missing — JD accounting incomplete"] else [] end)
       + (if $merge_missing then ["merge.json artifact missing — dedupe accounting incomplete"] else [] end)
```

- [ ] **Step 4: Run to verify it passes** — `bash skills/_ultra-engine/tests/test_scorecard.sh` → `fails=0` (pre-existing assertions must still pass — the fixtures for those runs will now also emit `accounting`; that is additive and breaks nothing).

- [ ] **Step 5: Document the `login_required` code**

In `skills/shared-references/canonical-schemas.md`, find the `errors[]` codes list (≈ line 380, "the transient diagnostics channel") and add:

```markdown
- `login_required` — an extension-lane source needs the user to sign in in Chrome. The envelope is a valid zero-count return (`scanned: 0`, `returned: 0`), never a fabrication; the message names the source and the rerun command (`/ultramode source <name>`). The dispatcher records the observation via `auth_state.sh set <name> <auth-required|session-expired> <now>`.
```

- [ ] **Step 6: Run the whole suite, then commit**

```bash
bash skills/_ultra-engine/tests/run.sh   # ALL PASS
git add skills/_ultra-engine/scripts/scorecard.sh skills/_ultra-engine/tests/test_scorecard.sh skills/shared-references/canonical-schemas.md
git commit -m "Phase 16 Task 8: five-way sweep accounting + artifact-missing disclosures"
```

---

### Task 9: The catalogue artifact — re-probe research + BENELUX hunt (WS-A)

**Files:**
- Create: `docs/superpowers/specs/2026-07-14-phase-16-source-catalogue-research.json`
- Create: `skills/shared-references/source-catalogue.json`

**Interfaces:**
- Consumes: `catalog.py validate` (Task 2); the Codex catalogue at `../codex-job-scout/plugins/codex-job-scout/references/shared/eu-nl-source-catalogue.json` as the candidate hypothesis list (21 candidates).
- Produces: the packaged catalogue every later task reads: `skills/shared-references/source-catalogue.json`, `catalog_version: 1`, `default_scope: "eu-nl"`, packs `eu-core`/`nl-core`/`eu-contract`/`benelux` (scopes `["eu-nl","eu-broad"]`) + `authenticated-marketplaces`/`eu-compatible-global` (scopes `["eu-broad"]`).

**This is a judgement task (research), not blind mechanics — run it in the main session, not a context-free subagent.** Probes are read-only public `WebFetch` GETs (the browser-policy carve-out).

- [ ] **Step 1: Extract the 21 Codex candidates as the worklist**

```bash
jq '[.packs[] | .id as $p | .sources[] | {pack: $p, name, url, category, access_lane, endpoint, auth_required}]' \
  "../codex-job-scout/plugins/codex-job-scout/references/shared/eu-nl-source-catalogue.json"
```

- [ ] **Step 2: Re-probe each of the 21 sessionlessly** (WebFetch on `evidence_url`/`endpoint`). Record per candidate, in a working notes file: reachable? currently listing EU/NL-relevant technical roles (lane: Linux/Platform/SRE/DevOps, contract-friendly)? login wall? If a probe hits an access wall but the site is corroborated real (RED Global-class), flip `access_lane` to `extension` and keep it — verification completes in the user's Chrome at rebuild (D5). Drop only candidates that are dead, parked, or demonstrably occupation-irrelevant. Every surviving candidate gets fresh `evidence_url` + `evidence_checked_at` (probe timestamp) + `auth_required` (observed) + `notes` (one line, British English).

- [ ] **Step 3: BENELUX hunt via the deep-research skill** — invoke `deep-research` with: *"Job boards and freelance broker/intermediary platforms for senior Linux/Platform/SRE/DevOps contract work in the BENELUX (Netherlands, Belgium, Luxembourg): NL freelance brokers/detacheringsbureaus beyond Striive and freelance.nl (e.g. Circle8/HeadFirst-class), Belgian IT boards and broker platforms (ICTjob.be-class, ProUnity/Connecting-Expertise-class public boards), Luxembourg boards (jobs.lu/Moovijob-class). For each: URL, whether searching requires an account, whether contract/freelance roles appear, evidence of current technical listings."* Probe each finding sessionlessly like Step 2. Admit at most **5** survivors into the `benelux` pack, contract-weighted (a broker with live freelance Linux/SRE listings beats a generic national board).

- [ ] **Step 4: Author the two artifacts.** Research JSON (`docs/superpowers/specs/2026-07-14-phase-16-source-catalogue-research.json`): one record per candidate probed (all 21 + every BENELUX finding), with `{name, url, pack, probe_outcome: "admitted"|"dropped"|"extension-routed", evidence_url, evidence_checked_at, auth_required, notes}` — the audit trail for every inclusion AND exclusion. Catalogue (`skills/shared-references/source-catalogue.json`): survivors only, in the Task 2 contract shape. Existing NL sources already in live registries (Striive, Nationale Vacaturebank etc.) stay in their Codex packs (`nl-core`) — the lifecycle merge dedupes against live registries by identity, so overlap is safe.

- [ ] **Step 5: Validate**

Run: `python3 skills/_ultra-engine/scripts/catalog.py validate skills/shared-references/source-catalogue.json`
Expected: `ok` (exit 0). Also `python3 skills/_ultra-engine/scripts/catalog.py select skills/shared-references/source-catalogue.json --scope eu-nl | jq length` — a number ≥ 10 (sanity: the eu-nl candidate pool survived).

- [ ] **Step 6: Commit**

```bash
git add docs/superpowers/specs/2026-07-14-phase-16-source-catalogue-research.json skills/shared-references/source-catalogue.json
git commit -m "Phase 16 Task 9: packaged source catalogue v1 — re-probed EU/NL candidates + BENELUX pack"
```

---

### Task 10: `/sources` prose — scope, catalogue-aware rebuild, retire, migration-on-load

**Files:**
- Modify: `skills/sources/SKILL.md`
- Modify: `skills/shared-references/ultramode-sources.md` (new § The packaged catalogue)

**Interfaces:**
- Consumes: `catalog.py` (Task 2), write recipe (Task 3), `migrate_sources.py` (Task 4), `project.py` (Task 5), `registry_lifecycle.py` (Task 6), the catalogue artifact (Task 9).
- Produces: the user-facing surface Tasks 11–12 reference: `/sources scope [eu-nl|eu-broad]`, `/sources retire <name>`, and the rebuilt § rebuild flow.

- [ ] **Step 1: Update the frontmatter + invocation forms** in `skills/sources/SKILL.md`: `argument-hint: [list | add <url|name> | scope [eu-nl|eu-broad] | retire <name> | rebuild | onboarding — omit for list]`, and add to the invocation block:

```
/sources scope                — show the source scope (eu-nl default; eu-broad adds global marketplaces)
/sources scope <eu-nl|eu-broad> — set it (offers a rebuild; scope matters at rebuild time)
/sources retire <name>        — retire a source permanently (tombstone — rebuilds never re-admit it)
```

- [ ] **Step 2: Add the migration-on-load rule** to Step 0 (Bootstrap):

```markdown
If `sources.json` exists with `schema_version < 2`, run `python3 $SCRIPTS/migrate_sources.py .job-scout/sources.json` before anything else (idempotent; adds `auth_state` + lifecycle lists — Phase 16). `$SCRIPTS` = `../_ultra-engine/scripts` resolved from this skill.
```

- [ ] **Step 3: Add the § scope section** after § list:

```markdown
## `/sources scope` — the catalogue scope (Phase 16)

Read: `python3 $SCRIPTS/catalog.py config-read .job-scout/user-profile.json` → print
`Scope: {{source_scope}} (refresh: {{source_refresh}})` plus one line explaining the other value
(`eu-nl` = EU/NL/BENELUX packs; `eu-broad` adds the opt-in global marketplaces — Upwork, Freelancer,
FlexJobs, Contra — and global remote boards). Reading NEVER writes the default.

Set (`/sources scope eu-broad`): validate the value (only `eu-nl`/`eu-broad`; anything else → show
allowed values, stop). Write with exactly this recipe (unknown keys must survive — test-pinned):

    jq '.ultramode.source_scope = "<value>"' .job-scout/user-profile.json > .job-scout/user-profile.json.tmp \
      && jq -e . .job-scout/user-profile.json.tmp >/dev/null && mv .job-scout/user-profile.json.tmp .job-scout/user-profile.json

Then OFFER (never force) a rebuild: `Scope set to <value>. It takes effect at the next rebuild — run /sources rebuild now? (y/N)`.
```

- [ ] **Step 4: Add the § retire section** after § add:

```markdown
## `/sources retire <name>` — permanent retirement (Phase 16)

Confirm first (`Retire <name>? Rebuilds will never re-admit it. (y/N)`), then:
`python3 $SCRIPTS/registry_lifecycle.py retire --registry .job-scout/sources.json --name "<name>"`.
Show the returned identity key. Absence from a future catalogue is NOT retirement — only this
tombstone is; to undo, remove the key from `retired_identities` by hand and `/sources add` the URL.
```

- [ ] **Step 5: Extend § rebuild with the catalogue stage.** Insert between the existing step 2 (dispatch `_source-discovery`) and step 3 (gates), as a new step:

```markdown
2-bis. **Catalogue admission (Phase 16, D5).** After discovery returns, admit the packaged catalogue for this workspace's scope — candidate precedence is `user sources → EU/NL catalogue → lane seed → universal backbone → live discoveries`:
   1. `scope=$(python3 $SCRIPTS/catalog.py config-read .job-scout/user-profile.json | jq -r .source_scope)`
   2. `python3 $SCRIPTS/catalog.py select <plugin>/skills/shared-references/source-catalogue.json --scope $scope` → the candidate list.
   3. **Probe every candidate live — packaged entries are hypotheses, never auto-admitted (never-fabricate):** api/rss/html lanes get a read-only `WebFetch` GET of `endpoint` (Gate B: postings visible); a recognised access/login wall flips the candidate to `access_lane: "extension"` with `endpoint: ""` and is RETAINED (verification completes in the logged-in sweep). A dead/parked candidate is dropped and recorded in the run notes with its probe evidence.
   4. Project each survivor: `python3 $SCRIPTS/project.py --candidate <one>.json --priority <next free> --verified-at <probe ISO8601>` (catalogue-only fields are stripped here; leaks are rejected again at merge).
   5. Merge atomically: `python3 $SCRIPTS/registry_lifecycle.py merge --registry .job-scout/sources.json --candidates <projected-array>.json --catalogue <plugin>/skills/shared-references/source-catalogue.json --expect-sha256 $(shasum -a 256 .job-scout/sources.json | cut -d' ' -f1)`. Exit 3 = the registry changed underneath — re-read and retry once. Report the printed counts verbatim (`retained/added/updated/tombstoned_skipped/total`).
   Gate 2's count invariant now reads: `len(sources) == merge.total` as printed by `registry_lifecycle.py` — the script IS the count assertion; a mismatch inside it fails loudly before any write.
```

And in the § rebuild closing paragraph add: `Stamp ultramode.registry_built_at only after a gated write (unchanged) — the Phase 16 staleness nag reads it.`

- [ ] **Step 6: Add § The packaged catalogue to `ultramode-sources.md`** (new section after § Curated lane seed):

```markdown
## The packaged catalogue (Phase 16)

`shared-references/source-catalogue.json` ships versioned, evidence-stamped candidate packs for the EU/NL/BENELUX market (`catalog_version` 1; provenance: `docs/superpowers/specs/2026-07-14-phase-16-source-catalogue-research.json`). Packs: `eu-core`, `nl-core`, `benelux`, `eu-contract` (scopes `eu-nl` + `eu-broad`); `authenticated-marketplaces`, `eu-compatible-global` (`eu-broad` only — global marketplaces are a deliberate opt-in). Candidates are **selection hypotheses**: admission happens only in `/sources rebuild` after a live probe (`sources/SKILL.md` § rebuild 2-bis), and the four catalogue-only fields (`lane_tags`, `auth_required`, `evidence_url`, `evidence_checked_at`) never reach `sources.json`. Entries admitted from the `benelux`/`nl-core` packs carry `pack` provenance and get rotation + poll-order priority (D4): the BENELUX broker/board lane is this user population's highest-value hunting ground after LinkedIn. Retirement is tombstone-only (`/sources retire`); a candidate's absence from a later catalogue version never removes a live source.
```

- [ ] **Step 7: Verify + commit.** Verification is manual (prose): `grep -n "scope\|retire\|2-bis\|catalog.py\|registry_lifecycle" skills/sources/SKILL.md` shows every new hook; `bash skills/_ultra-engine/tests/run.sh` still `ALL PASS` (no script changes).

```bash
git add skills/sources/SKILL.md skills/shared-references/ultramode-sources.md
git commit -m "Phase 16 Task 10: /sources scope + retire + catalogue-aware rebuild"
```

---

### Task 11: `/ultramode` prose — `super` scope, login handoff, auth-state transitions, staleness nag

**Files:**
- Modify: `skills/ultramode/SKILL.md`

**Interfaces:**
- Consumes: `rotation.sh pick-all` (Task 7), `auth_state.sh` (Task 4), `login_required` envelope + `accounting` (Task 8), `migrate_sources.py` (Task 4).
- Produces: the `super` scope and handoff copy Task 13 documents.

- [ ] **Step 1: Scope grammar.** In the invocation-forms block add `\n/ultramode super              — every enabled source, no rotation (all extension-lane sources; resumable)`; in Step 4's scope enumeration (line ≈48) add: `super` = LinkedIn + all external + **all** extension-lane sources.

- [ ] **Step 2: Migration-on-load.** In the step that loads `sources.json` (Step 4b), first line: `If sources.json has schema_version < 2, run python3 $SCRIPTS/migrate_sources.py $WS/sources.json first (idempotent — Phase 16).`

- [ ] **Step 3: Rotation pick by scope.** In Step 4b, replace the single pick call with: bare → `bash $SCRIPTS/rotation.sh pick $WS/sources.json 4` (unchanged); `super` → `bash $SCRIPTS/rotation.sh pick-all $WS/sources.json` and `rotated_out: []`. Write `{picked, rotated_out, mode}` to `$rd/rotation.json` where `mode` ∈ `bare|linkedin|external|source|super` (Task 8's scorecard reads it). BENELUX weighting is inside the script — never re-order in prose.

- [ ] **Step 4: Login handoff + auth-state transitions.** In Step 4d (extension lane), after the "A source that cannot be swept…" sentence, replace/extend with:

```markdown
**Login walls (Phase 16, D16):** when a source presents a sign-in wall, produce the zero-count
`login_required` envelope (`errors[0] = {code: "login_required", message: "<name> needs sign-in —
sign in in the open Chrome tab, then run /ultramode source <name>"}`), leave that tab open for the
user, record the observation — `bash $SCRIPTS/auth_state.sh set $WS/sources.json "<name>"
<auth-required|session-expired> "$(date -u +%FT%TZ)"` (`session-expired` when the entry's previous
`auth_state` was `signed-in` or `public`, else `auth-required`) — and move on to the next source;
a blocked source never stalls the run. Conversely, a successful sweep of an `auth-required`/
`session-expired` source records `signed-in` the same way, and NEVER touches credentials: the user
signs in themselves in Chrome; the plugin only reuses the session. `auth_state` is a hint —
a `signed-in` source can still hit a wall (sessions expire outside our sight); handle it via this
same path, never treat the stored state as a guarantee.
```

In `super` mode add: `Sweep the pick-all worklist in its printed order; checkpoint each source (stage sweep-<slug>) before opening the next, so an interrupted super run resumes from the last completed source (the 48h resume window applies unchanged). rotation.sh mark each source after sweeping it, exactly as in bare mode — a super sweep IS a sweep, and last_swept_at must reflect reality so the next bare rotation stays honest.`

- [ ] **Step 5: Staleness nag (D10).** In Step 4b after loading the registry: `If ultramode.registry_built_at is older than 90 days, print one line — "Registry last rebuilt {{date}} (>90 days) — consider /sources rebuild." — and continue (never block a read-only sweep).`

- [ ] **Step 6: Report + summary accounting.** In Step 4g (scorecard + payload), note that `scorecard.json.accounting` must reach the render payload; in the terminal-summary step, require the five-way line: `Sources: {{attempted}} attempted · {{completed} completed · {{login_blocked}} login-blocked · {{failed}} failed · {{rotated_out}} rotated out ({{mode}} mode)` plus, when `login_blocked > 0`, one line per blocked source with its rerun command.

- [ ] **Step 7: Verify + commit.** `grep -n "super\|login_required\|auth_state\|90 days\|pick-all" skills/ultramode/SKILL.md` shows each hook; suite still `ALL PASS`.

```bash
git add skills/ultramode/SKILL.md
git commit -m "Phase 16 Task 11: /ultramode super + login handoff + auth-state transitions"
```

---

### Task 12: Report delivery — replace `file://` navigation; direct links everywhere

**Files:**
- Modify: `skills/shared-references/render-orchestration.md` (Step D html-success path; Step E; Step F copy)
- Modify: `skills/ultramode/SKILL.md` (terminal summary: per-role links)

**Interfaces:**
- Consumes: the visualizer's written HTML `path` (unchanged).
- Produces: the delivery contract (D14) + link rule (D15) all Tier 1 commands follow.

- [ ] **Step 1: Rewrite Step D "Success, format=html"** in `render-orchestration.md`:

```markdown
### Success, format=html

Subagent returned `status: "ok"` with a `path` delta.

1. **Deliver the file to the user through the harness's file-delivery tool** (e.g. `SendUserFile`
   with `display: "render"`), so the report renders in the user's panel. Never ask the browser
   extension to navigate to a local `file://` URL — browser URL policy rejects local navigation
   (Phase 16, D14).
2. **If no file-delivery tool exists in this harness**, open via the OS instead:
   `open "<path>"` (macOS) / `xdg-open "<path>"` (Linux) via Bash.
3. **If both are unavailable or fail**, fall through to Step F: ask-and-fallback.
4. On success, print the terminal summary (Step E) and return.
```

Also update Step F's prompt copy: `⚠ Couldn't open in Chrome (<reason>).` → `⚠ Couldn't deliver the report (<reason>).`

- [ ] **Step 2: Direct links in Step E.** Replace the Step E table's trailing clauses `— opened report in Chrome` with `— report delivered` (all rows), and append after the table:

```markdown
**Direct links are mandatory (Phase 16, D15):** whatever the render mode, the terminal summary
ends with one line per surfaced A/B/C role: `{{tier}} · {{title}} — {{company}} → {{canonical url}}`
(the canonical apply-at-source URL — the same link the report card carries). A user must never
need to open the HTML to reach a job.
```

- [ ] **Step 3: Ultramode summary wiring.** In `skills/ultramode/SKILL.md`'s final step (terminal summary after render), require the per-role link lines from the merged tracker entries of this run (`url` field of each A/B/C entry), matching Step E's format.

- [ ] **Step 4: Verify + commit.** `grep -n "file://" skills/shared-references/render-orchestration.md` → only the prohibition sentence remains (no instruction to navigate). Suite `ALL PASS`.

```bash
git add skills/shared-references/render-orchestration.md skills/ultramode/SKILL.md
git commit -m "Phase 16 Task 12: harness file delivery replaces file:// navigation; direct links mandatory"
```

---

### Task 13: Docs + release — README/QUICKSTART/COMMANDS/TROUBLESHOOTING, CHANGELOG, version bump

**Files:**
- Modify: `README.md`, `QUICKSTART.md` (if present at root — check `ls`), `docs/COMMANDS.md` (check actual path: `git ls-files | grep -i command`), `docs/TROUBLESHOOTING.md` (same check; create nothing new — edit what exists)
- Modify: `CHANGELOG.md`, `.claude-plugin/plugin.json`, `docs/ROADMAP.md`

**Interfaces:** none produced — this is the release surface.

- [ ] **Step 1: Docs sweep.** In each existing doc that describes `/sources` or `/ultramode`: add `scope`/`retire` forms, the `super` scope, the login-handoff behaviour ("if a source says login required: sign in in the open tab, rerun `/ultramode source <name>`"), and the BENELUX story (one sentence: the catalogue ships EU/NL/BENELUX packs; BENELUX sources are priority-swept). **Stored-login claim is forbidden until acceptance passes (D18)** — write "reuses your existing Chrome session where one exists" and nothing stronger.

- [ ] **Step 2: CHANGELOG.** New `## [0.16.0] — 2026-07-XX` section (Keep a Changelog): Added — packaged EU/NL/BENELUX source catalogue + `/sources scope|retire`, `auth_state` in sources.json (v2, auto-migrated), `/ultramode super`, five-way sweep accounting, per-role direct links in every summary; Changed — report delivery via harness file panel (no more `file://`), BENELUX-weighted rotation; Fixed — scorecard silently defaulting to zeros when stage artifacts are missing.

- [ ] **Step 3: Version bump.** `.claude-plugin/plugin.json` `"version": "0.15.0"` → `"0.16.0"`. Tick completed WS checkboxes in `docs/ROADMAP.md` Phase 16 section.

- [ ] **Step 4: Full verify + commit.**

```bash
bash skills/_ultra-engine/tests/run.sh   # ALL PASS
git add -A && git commit -m "Phase 16 Task 13: docs + release v0.16.0"
```

---

### Task 14: Live acceptance (user-run, gates the release — spec §5)

**Files:** none (live workspaces). Do not mark Phase 16 shipped, and do not claim stored-login support anywhere, until all four pass.

- [ ] **Gate 1 — rebuild:** `/sources rebuild` on CVFREELANCER. Verify: BENELUX-tagged sources outrank generic ones in the derived poll order (`jq '.priority_order[:8]' sources.json` — spot-check); `registry_lifecycle` counts printed and reconciled; LinkedIn entry + user sources intact; `schema_version: 2` with `auth_state` on every entry.
- [ ] **Gate 2 — login handoff on freelance.nl AND Malt:** first sweep records `login_required` (zero-count envelope, tab left open, `auth_state` → `auth-required`/`session-expired`); the user signs in directly in Chrome; `/ultramode source <name>` succeeds on the reused session and `auth_state` → `signed-in` with `auth_state_observed_at` stamped. Only after both sources pass may docs claim stored-login support.
- [ ] **Gate 3 — one clean `/ultramode super`:** all extension sources attempted in `pick-all` order; blocked sources skipped-and-recorded; `scorecard.json.accounting` reconciles with the run dir's `sweep-*.json` by `jq` spot-check; report delivered via the harness panel; every A/B/C role carries its direct link in the terminal summary.
- [ ] **Gate 4 — suite + compat:** `bash skills/_ultra-engine/tests/run.sh` → `ALL PASS` on `main`; a copy of a real pre-Phase-16 `sources.json` migrates cleanly via `migrate_sources.py` (idempotence re-run included).

---

## Self-review (performed at plan-writing time)

**Spec coverage:** D1 (framing) → whole plan; D2/D3 → Task 9; D4 → Tasks 7, 10, 11; D5 → Tasks 9, 10; D6 → Tasks 4, 11; D7 → Tasks 2, 3, 10; D8 → Task 10; D9 → Tasks 2, 9, 10; D10 → Tasks 2, 11; D11 → Tasks 1, 2, 5, 6; D12 → Tasks 7, 8, 11; D13 → Task 8; D14 → Task 12; D15 → Task 12; D16 → Tasks 4, 8, 11; D17/D18 → Tasks 13, 14. Contract-test map (spec §4): pack selection → test_catalog; default-without-write + unknown-key preservation → test_catalog + test_config_scope; catalogue schema → test_catalog; host normalisation → test_identity; aliases/tombstones/retention/atomic-conflict/leak-stripping/exact-counts → test_registry_lifecycle; login_required envelope → test_scorecard fixture; auth-state transitions → test_auth_state; super-vs-bare accounting → test_scorecard; artifact-missing disclosure → test_scorecard; migration round-trip → test_migrate_sources; deterministic report → existing payload/scorecard golden pattern (extended in Task 8).

**Known deviation:** `identity.sh` delivered as `lib/identity.py` (single implementation) — flagged in Global Constraints.

**Type consistency:** identity keys are `"<host>|<category>"` strings everywhere (Tasks 1, 2, 6); candidates carry `pack` from `select` (Task 2) through `project` (Task 5) into the registry (Tasks 6, 7); `auth_state` enum spelled identically in Tasks 4, 5, 8, 11; `accounting` field names identical in Tasks 8, 11, 12.

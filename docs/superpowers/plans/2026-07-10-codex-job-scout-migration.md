# Codex Job Scout Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a self-contained, installable Codex marketplace plugin that preserves all 18 Claude Job Scout command contracts and interoperates with existing `.job-scout/` workspaces.

**Architecture:** Freeze the Claude `v0.15.0` behaviour as compatibility fixtures, replace the Bash/`jq` spine and model-driven renderer with a Python 3.11 standard-library core, then place thin Codex skills over capability adapters for Chrome, web, confirmations, optional subagents, and report opening. Only the deterministic core writes canonical state.

**Tech Stack:** Codex plugin and marketplace manifests, Markdown skills, `agents/openai.yaml`, Python 3.11+ standard library, `unittest`, HTML/CSS/JavaScript assets, GitHub Actions.

## Global Constraints

- Treat `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout` as read-only for the entire implementation.
- Perform every write, test artifact, commit, installation document, and generated file inside `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/codex-job-scout` or an OS temporary directory.
- Preserve `.job-scout/` filenames, schema versions, enums, IDs, fingerprints, hashes, cache keys, transitions, ordering, unknown fields, and checkpoint semantics.
- Do not evolve the shared state schema unless the user explicitly authorizes it in a coding session.
- Require Python 3.11+ at runtime; use no runtime `pip`, Node, Bash, `jq`, or platform-specific utility dependency.
- Require the official Codex Chrome plugin for logged-in browser commands.
- Use no Anthropic/OpenAI API key, SDK, or usage-billed LLM API call.
- Keep sequential execution complete; multi-agent work is optional acceleration only.
- Never let subagents or browser adapters write canonical `.job-scout/` state.
- Never use computer use, an external browser framework, credential scraping, or credentialed HTTP scraping.
- Stop application, message, alert, and profile mutations at an explicit confirmation boundary.
- Expose exactly 18 user skills; internal playbooks are references or Python modules, not discoverable skills.
- Use British English for user-facing copy unless the workspace tone contract overrides it.
- Keep the target repository's only inherited remote named `claude-upstream`; do not push to it.
- Commit after every task with the exact intent-focused commit shown in that task.

## Target File Map

### Marketplace root

- `.agents/plugins/marketplace.json` — local/Git marketplace entry for `codex-job-scout`.
- `README.md` — marketplace installation and repository overview.
- `compatibility/SOURCE_COMMIT` — immutable source baseline `f5e25ce5a5fb9f9b91b527e9decae7842369d96b`.
- `compatibility/command-contract.json` — machine-readable 18-command public contract.
- `compatibility/fixtures/` — copied and captured legacy inputs/outputs.
- `compatibility/test_contract.py` — public-surface and provenance checks.
- `tools/check_source_read_only.py` — compares the source worktree status with the recorded baseline.
- `tools/audit_plugin.py` — checks skill count, metadata, links, forbidden runtime terms, and LLM API dependencies.
- `.github/workflows/test.yml` — Python 3.11/3.12 matrix on macOS, Linux, and Windows.

### Plugin root: `plugins/codex-job-scout/`

- `.codex-plugin/plugin.json` — Codex plugin manifest, version `0.15.0+codex.1`.
- `AGENTS.md` — contributor invariants and verification commands.
- `README.md` — installed-plugin usage and command map.
- `QUICKSTART.md` — first workspace workflow.
- `skills/{analyze-cv,apply,bend,check-inbox,check-job-notifications,config,cover-letter,create-alerts,deep-sweep,funnel-report,index-docs,interview-prep,job-search,match-jobs,optimize-profile,sources,tune,ultramode}/SKILL.md` — the 18 thin user orchestrators.
- `skills/{analyze-cv,apply,bend,check-inbox,check-job-notifications,config,cover-letter,create-alerts,deep-sweep,funnel-report,index-docs,interview-prep,job-search,match-jobs,optimize-profile,sources,tune,ultramode}/agents/openai.yaml` — explicit-only invocation and UI metadata.
- `references/shared/` — shared schemas and domain procedures.
- `references/internal/` — ten model capability playbooks formerly exposed as underscore skills.
- `references/adapters/` — Chrome, web, subagent, confirmation, and report-opening contracts.
- `assets/` — report CSS, JavaScript, and golden-view inputs.
- `core/job_scout/` — platform-neutral deterministic package.
- `core/tests/` — standard-library unit, golden, and round-trip tests.
- `scripts/job_scout.py` — stable executable wrapper used by skills.

### Python module ownership

- `result.py` — `Result` and `JobScoutError` wire types.
- `preflight.py` — interpreter, workspace, state-version, and permission checks.
- `json_store.py` — canonical JSON, atomic replacement, backups, and quarantine.
- `identity.py` — fingerprints, namespaced IDs, and profile hashes.
- `schemas.py` — canonical state and delta validation without destructive normalization.
- `snapshot.py` — known-ID and fingerprint snapshot creation.
- `queue.py` — FIFO JD queue with deduplication.
- `rotation.py` — extension-lane selection and sweep stamps.
- `checkpoint.py` — resumable run manifests and stage artifacts.
- `locking.py` — exclusive lock, heartbeat, stale detection, and conflict quarantine.
- `delta.py` — source-envelope validation.
- `merge.py` — deterministic, atomic tracker merge.
- `scorecard.py` — run accounting and disclosures.
- `payload.py` — final tier/near-miss ordering and render payloads.
- `render/` — escaped HTML and Markdown view rendering.
- `cli.py` — stable subcommands over the modules above.

---

### Task 1: Freeze Source Provenance and the Public Command Contract

**Files:**
- Create: `compatibility/SOURCE_COMMIT`
- Create: `compatibility/command-contract.json`
- Create: `compatibility/test_contract.py`
- Create: `tools/check_source_read_only.py`
- Create: `compatibility/source-status.json`

**Interfaces:**
- Consumes: read-only source commit `f5e25ce5a5fb9f9b91b527e9decae7842369d96b` and the current source worktree status.
- Produces: `command-contract.json` with keys `source_commit`, `source_version`, and `commands`; `check_source_read_only.py --source SOURCE_REPOSITORY --baseline BASELINE_JSON` exits 0 only when no project-caused source change exists.

- [ ] **Step 1: Write the failing provenance and command-inventory test**

```python
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ContractTest(unittest.TestCase):
    def test_source_and_commands_are_frozen(self) -> None:
        self.assertEqual(
            (ROOT / "compatibility/SOURCE_COMMIT").read_text().strip(),
            "f5e25ce5a5fb9f9b91b527e9decae7842369d96b",
        )
        contract = json.loads(
            (ROOT / "compatibility/command-contract.json").read_text()
        )
        self.assertEqual(contract["source_version"], "0.15.0")
        self.assertEqual(
            [item["name"] for item in contract["commands"]],
            [
                "analyze-cv", "apply", "bend", "check-inbox",
                "check-job-notifications", "config", "cover-letter",
                "create-alerts", "deep-sweep", "funnel-report", "index-docs",
                "interview-prep", "job-search", "match-jobs",
                "optimize-profile", "sources", "tune", "ultramode",
            ],
        )
        self.assertTrue(all(item["implicit_invocation"] is False for item in contract["commands"]))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test and verify the contract files are absent**

Run: `python -m unittest compatibility.test_contract -v`  
Expected: `ERROR` or `FAIL` because `SOURCE_COMMIT` and `command-contract.json` do not exist.

- [ ] **Step 3: Add the immutable source and command contract**

Write `SOURCE_COMMIT` as exactly
`f5e25ce5a5fb9f9b91b527e9decae7842369d96b` plus a newline. Write
`command-contract.json` with the exact ordered names above and these argument
values: `analyze-cv: "[cv-file-path]"`, `apply: null`, `bend:
"tracker-id"`, `check-inbox: null`, `check-job-notifications: null`,
`config: null`, `cover-letter: "[tracker-id | linkedin-url]"`,
`create-alerts: "[optional: manual]"`, `deep-sweep: null`, `funnel-report:
null`, `index-docs: null`, `interview-prep: "[tracker-id]"`, `job-search:
"[optional: job-title]"`, `match-jobs: null`, `optimize-profile: null`,
`sources: "[list | add URL_OR_NAME | rebuild | onboarding]"`, `tune: "[add |
remove | exclude | unexclude | gate]"`, and `ultramode: "[linkedin | external
| source NAME]"`. Every entry contains `implicit_invocation: false` and its
complete source description. Record `deep-sweep` with `alias_of: "ultramode"`;
every other entry has `alias_of: null`.

Implement `check_source_read_only.py` with this stable interface:

```python
def status_lines(source: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "status", "--short"], cwd=source, text=True,
        capture_output=True, check=True,
    )
    return sorted(line for line in completed.stdout.splitlines() if line)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    args = parser.parse_args()
    expected = json.loads(args.baseline.read_text())["status_lines"]
    actual = status_lines(args.source)
    if actual != expected:
        print(json.dumps({"expected": expected, "actual": actual}, indent=2))
        return 1
    return 0
```

Record the already-present source lines `?? .agents/` and `?? skills-lock.json`
in `compatibility/source-status.json`; this records pre-existing state rather
than claiming the source is clean.

- [ ] **Step 4: Run the contract and source-read-only checks**

Run: `python -m unittest compatibility.test_contract -v`  
Expected: `OK`.

Run: `bash ../claude-job-scout/skills/_ultra-engine/tests/run.sh`  
Expected: final line `ALL PASS`; the source suite writes only to OS temporary
directories.

Run:

```bash
python tools/check_source_read_only.py \
  --source '../claude-job-scout' \
  --baseline compatibility/source-status.json
```

Expected: exit 0 and no output.

- [ ] **Step 5: Commit the compatibility boundary**

```bash
git add compatibility tools/check_source_read_only.py
git commit -m "test: freeze Claude compatibility contract"
```

### Task 2: Create the Self-Contained Marketplace and Plugin Shell

**Files:**
- Create: `.agents/plugins/marketplace.json`
- Create: `plugins/codex-job-scout/.codex-plugin/plugin.json`
- Create: `plugins/codex-job-scout/README.md`
- Create: `tools/test_plugin_layout.py`
- Modify: `README.md`
- Move: `QUICKSTART.md` to `plugins/codex-job-scout/QUICKSTART.md`

**Interfaces:**
- Consumes: plugin name `codex-job-scout` and source version `0.15.0`.
- Produces: marketplace `codex-job-scout`, plugin version `0.15.0+codex.1`, and a plugin root that validates before skills are added.

- [ ] **Step 1: Write the failing marketplace-layout test**

```python
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PluginLayoutTest(unittest.TestCase):
    def test_marketplace_points_to_matching_plugin(self) -> None:
        market = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text())
        self.assertEqual(market["name"], "codex-job-scout")
        self.assertEqual(len(market["plugins"]), 1)
        entry = market["plugins"][0]
        self.assertEqual(entry["name"], "codex-job-scout")
        self.assertEqual(entry["source"]["path"], "./plugins/codex-job-scout")
        manifest = json.loads(
            (ROOT / "plugins/codex-job-scout/.codex-plugin/plugin.json").read_text()
        )
        self.assertEqual(manifest["name"], entry["name"])
        self.assertEqual(manifest["version"], "0.15.0+codex.1")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the layout test and verify it fails**

Run: `python -m unittest tools.test_plugin_layout -v`  
Expected: `ERROR` because the marketplace and Codex manifest do not exist.

- [ ] **Step 3: Add exact marketplace and manifest data**

Use this marketplace entry:

```json
{
  "name": "codex-job-scout",
  "interface": { "displayName": "Codex Job Scout" },
  "plugins": [
    {
      "name": "codex-job-scout",
      "source": { "source": "local", "path": "./plugins/codex-job-scout" },
      "policy": { "installation": "AVAILABLE", "authentication": "ON_INSTALL" },
      "category": "Productivity"
    }
  ]
}
```

Use this exact initial manifest; Task 12 adds the `skills` path after the valid
skill tree exists:

```json
{
  "name": "codex-job-scout",
  "version": "0.15.0+codex.1",
  "description": "Cross-platform job-search automation with shared local state, multi-source discovery, CV optimisation, matching, recruiter workflows, and protected browser actions.",
  "author": { "name": "BSF" },
  "keywords": ["linkedin", "job-search", "cv", "career", "recruiter", "easy-apply", "remote"],
  "interface": {
    "displayName": "Codex Job Scout",
    "shortDescription": "Find, rank, track, and act on job opportunities",
    "longDescription": "A cross-platform Codex port of LinkedIn Job Hunter. It analyses CVs, searches LinkedIn and verified public sources, deduplicates and ranks roles, prepares applications and recruiter replies, and stores interoperable state under .job-scout.",
    "developerName": "BSF",
    "category": "Productivity",
    "capabilities": ["Interactive", "Read", "Write"],
    "defaultPrompt": [
      "Run my full-market job sweep.",
      "Analyse my CV and job-search requirements.",
      "Show the strongest jobs found so far."
    ],
    "brandColor": "#0F766E"
  }
}
```

Replace the marketplace-root README with installation architecture and link to
the plugin README. Move the existing quick-start file into the plugin root so
history follows the user documentation; its content is ported in Task 16.

- [ ] **Step 4: Run layout validation**

Run: `python -m unittest tools.test_plugin_layout -v`  
Expected: `OK`.

Run: `python -m json.tool .agents/plugins/marketplace.json >/dev/null`  
Expected: exit 0.

Run: `python -m json.tool plugins/codex-job-scout/.codex-plugin/plugin.json >/dev/null`  
Expected: exit 0.

- [ ] **Step 5: Commit the installable shell**

```bash
git add .agents README.md plugins tools/test_plugin_layout.py
git commit -m "feat: scaffold Codex marketplace plugin"
```

### Task 3: Add the Python Core Result, Preflight, and CLI Boundary

**Files:**
- Create: `plugins/codex-job-scout/core/job_scout/__init__.py`
- Create: `plugins/codex-job-scout/core/job_scout/result.py`
- Create: `plugins/codex-job-scout/core/job_scout/preflight.py`
- Create: `plugins/codex-job-scout/core/job_scout/cli.py`
- Create: `plugins/codex-job-scout/scripts/job_scout.py`
- Create: `plugins/codex-job-scout/core/tests/test_preflight.py`
- Create: `plugins/codex-job-scout/core/tests/test_cli.py`

**Interfaces:**
- Produces: `Result[T].to_dict()`, `JobScoutError(code, message, details)`, `check_runtime(workspace: Path) -> Result[dict[str, object]]`, and `cli.main(argv: Sequence[str] | None) -> int`.

- [ ] **Step 1: Write failing result and preflight tests**

```python
import tempfile
import unittest
from pathlib import Path

from job_scout.preflight import check_runtime
from job_scout.result import Result


class PreflightTest(unittest.TestCase):
    def test_writable_workspace_returns_structured_success(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            result = check_runtime(Path(raw))
        self.assertIsInstance(result, Result)
        self.assertTrue(result.ok)
        self.assertGreaterEqual(result.value["python"], [3, 11])

    def test_missing_workspace_returns_stable_error(self) -> None:
        result = check_runtime(Path("/definitely/missing/job-scout-workspace"))
        self.assertFalse(result.ok)
        self.assertEqual(result.error.code, "workspace_missing")
```

- [ ] **Step 2: Run the tests and verify imports fail**

Run from `plugins/codex-job-scout/core`:

`python -m unittest discover -s tests -p 'test_preflight.py' -v`  
Expected: `ERROR` with `ModuleNotFoundError: job_scout` or missing modules.

- [ ] **Step 3: Implement the minimal stable wire types and preflight**

Use frozen dataclasses:

```python
@dataclass(frozen=True)
class JobScoutError:
    code: str
    message: str
    details: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class Result(Generic[T]):
    value: T | None = None
    error: JobScoutError | None = None

    @property
    def ok(self) -> bool:
        return self.error is None

    def to_dict(self) -> dict[str, object]:
        if self.ok:
            return {"ok": True, "value": self.value}
        return {"ok": False, "error": asdict(self.error)}
```

`check_runtime` verifies Python 3.11+, workspace existence/directory status, and
writability via a temporary file created and removed inside the workspace. The
CLI initially exposes `preflight --workspace PATH`, writes one JSON object to
stdout, diagnostics to stderr, and exits 0 on success or 2 on structured error.
The wrapper resolves its parent plugin directory, inserts its sibling `core`
directory into `sys.path`, and delegates to
`job_scout.cli.main`.

- [ ] **Step 4: Run core and CLI tests**

Run: `python -m unittest discover -s plugins/codex-job-scout/core/tests -v`  
Expected: all tests pass.

Run: `python plugins/codex-job-scout/scripts/job_scout.py preflight --workspace .`  
Expected: JSON with `"ok": true` and exit 0.

- [ ] **Step 5: Commit the core boundary**

```bash
git add plugins/codex-job-scout/core plugins/codex-job-scout/scripts
git commit -m "feat: add cross-platform core CLI"
```

### Task 4: Implement Canonical JSON, Atomic Writes, and State Validation

**Files:**
- Create: `plugins/codex-job-scout/core/job_scout/json_store.py`
- Create: `plugins/codex-job-scout/core/job_scout/schemas.py`
- Create: `plugins/codex-job-scout/core/tests/test_json_store.py`
- Create: `plugins/codex-job-scout/core/tests/test_schemas.py`
- Create: `compatibility/fixtures/state/legacy-tracker.json`
- Create: `compatibility/fixtures/state/legacy-profile.json`

**Interfaces:**
- Produces: `canonical_bytes(value: object) -> bytes`, `load_json(path: Path) -> object`, `atomic_write_json(path: Path, value: object, validator: Callable[[object], None]) -> None`, `quarantine(path: Path, reason: str) -> Path`, `validate_tracker`, `validate_profile`, and `validate_threads`.

- [ ] **Step 1: Write failing canonicalization and round-trip tests**

```python
class JsonStoreTest(unittest.TestCase):
    def test_canonical_bytes_are_sorted_compact_utf8(self) -> None:
        self.assertEqual(
            canonical_bytes({"z": "Malmö", "a": [1, None]}),
            b'{"a":[1,null],"z":"MalmÃ¶"}',
        )

    def test_atomic_round_trip_preserves_unknown_fields(self) -> None:
        value = {"schema_version": 3, "jobs": {}, "future_field": {"x": 1}}
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "tracker.json"
            atomic_write_json(path, value, validate_tracker)
            self.assertEqual(load_json(path), value)
```

- [ ] **Step 2: Run tests and verify missing modules fail**

Run: `python -m unittest discover -s plugins/codex-job-scout/core/tests -p 'test_json_store.py' -v`  
Expected: `ERROR` because `json_store` is absent.

- [ ] **Step 3: Implement canonical and atomic storage**

Canonical JSON uses:

```python
json.dumps(
    value, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
    allow_nan=False,
).encode("utf-8")
```

Atomic writes create a named temporary file in `path.parent`, write canonical
bytes plus a final newline only when the incumbent contract includes one,
flush, `os.fsync`, reload and validate, then call `os.replace`. On failure,
unlink the temporary file and leave the destination unchanged. Validators
check the exact enums and required structures from
`skills/shared-references/canonical-schemas.md` without removing unknown keys.
`quarantine` moves a corrupt/conflict copy under `.job-scout/quarantine/` with a
UTC timestamp and writes a sibling `.reason.txt` diagnostic.

- [ ] **Step 4: Run storage, schema, and legacy fixture tests**

Run: `python -m unittest discover -s plugins/codex-job-scout/core/tests -p 'test_json_store.py' -v`  
Expected: `OK`.

Run: `python -m unittest discover -s plugins/codex-job-scout/core/tests -p 'test_schemas.py' -v`  
Expected: `OK`, including invalid status/tier/rubric rejection and unknown-field preservation.

- [ ] **Step 5: Commit trusted state I/O**

```bash
git add compatibility/fixtures/state plugins/codex-job-scout/core
git commit -m "feat: add atomic state validation"
```

### Task 5: Port Identity and Hashing with Golden Parity

**Files:**
- Create: `plugins/codex-job-scout/core/job_scout/identity.py`
- Create: `plugins/codex-job-scout/core/tests/test_identity.py`
- Copy: source identity fixtures into `compatibility/fixtures/identity/`
- Modify: `plugins/codex-job-scout/core/job_scout/cli.py`

**Interfaces:**
- Produces: `fingerprint(company: str, title: str, location: str) -> str`, `namespace_id(provider: str, board: str, external_id: str | None, url: str | None) -> str`, and `profile_hash(profile: Mapping[str, object]) -> str`.

- [ ] **Step 1: Write failing golden tests**

```python
class IdentityTest(unittest.TestCase):
    def test_fingerprint_matches_v015(self) -> None:
        self.assertEqual(
            fingerprint("Acme GmbH", "Senior Platform Engineer", "Berlin"),
            "acme gmbh|senior platform engineer|berlin",
        )
        self.assertEqual(
            fingerprint("Malmö AB", "Senior SRE", "Zürich"),
            "malmo ab|senior sre|zurich",
        )

    def test_url_namespace_is_query_independent(self) -> None:
        left = namespace_id("remoteok", "remoteok", None, "https://remoteok.com/jobs/9?ref=x")
        right = namespace_id("remoteok", "remoteok", None, "https://remoteok.com/jobs/9/")
        self.assertEqual(left, right)

    def test_profile_hash_matches_fixture(self) -> None:
        fixture = (
            Path(__file__).resolve().parents[4]
            / "compatibility/fixtures/identity/profile-a.json"
        )
        profile = json.loads(fixture.read_text())
        self.assertEqual(profile_hash(profile), "4f0e1fd17e97bd54")
```

- [ ] **Step 2: Run and verify the missing implementation fails**

Run: `python -m unittest discover -s plugins/codex-job-scout/core/tests -p 'test_identity.py' -v`  
Expected: `ERROR` importing `job_scout.identity`.

- [ ] **Step 3: Implement exact legacy normalization**

Use Unicode NFKD decomposition, remove combining marks, lowercase, replace
punctuation with spaces, collapse whitespace, and apply the existing location
stop-word rules from `fingerprint.jq`. URL fallback removes the query, fragment,
and trailing slash before taking the first 12 SHA-256 hex characters.
`profile_hash` selects only the incumbent fields, canonicalizes with sorted
keys in the same shape as `profile_hash.sh`, and returns 16 SHA-256 hex
characters. Add CLI subcommands `fingerprint`, `namespace-id`, and
`profile-hash` with JSON output.

- [ ] **Step 4: Run identity tests and compare every legacy case**

Run: `python -m unittest discover -s plugins/codex-job-scout/core/tests -p 'test_identity.py' -v`  
Expected: all source `test_fingerprint.sh`, `test_namespace_id.sh`, and
`test_profile_hash.sh` cases pass in Python.

- [ ] **Step 5: Commit identity parity**

```bash
git add compatibility/fixtures/identity plugins/codex-job-scout/core
git commit -m "feat: port job identity and hashes"
```

### Task 6: Port Snapshots, JD Queues, and Source Rotation

**Files:**
- Create: `plugins/codex-job-scout/core/job_scout/snapshot.py`
- Create: `plugins/codex-job-scout/core/job_scout/queue.py`
- Create: `plugins/codex-job-scout/core/job_scout/rotation.py`
- Create: `plugins/codex-job-scout/core/tests/test_snapshot.py`
- Create: `plugins/codex-job-scout/core/tests/test_queue.py`
- Create: `plugins/codex-job-scout/core/tests/test_rotation.py`
- Copy: `skills/_ultra-engine/tests/fixtures/sources-mini.json` and `skills/_ultra-engine/tests/fixtures/tracker-mini.json` to `compatibility/fixtures/engine/`
- Modify: `plugins/codex-job-scout/core/job_scout/cli.py`

**Interfaces:**
- Produces: `build_snapshot(tracker, generated_at)`, `JDQueue.push/pop/count`, `pick_sources(registry, limit)`, and `mark_swept(registry, name, day)`.

- [ ] **Step 1: Write failing fixture tests**

Write `unittest` cases that assert: rejected jobs are excluded from known IDs;
incumbent fingerprints are included; queue push deduplicates by ID; pop is FIFO
and removes only returned entries; never-swept extension sources sort before
stalest swept sources; API lanes and `category: linkedin` never enter rotation;
and `mark_swept` changes only the named source.

- [ ] **Step 2: Run the three test modules and verify missing implementations**

Run from `plugins/codex-job-scout/core`:

```bash
python -m unittest discover -s tests -p 'test_snapshot.py' -v
python -m unittest discover -s tests -p 'test_queue.py' -v
python -m unittest discover -s tests -p 'test_rotation.py' -v
```

Expected: import errors for the three missing modules.

- [ ] **Step 3: Implement pure transformations and atomic persistence**

Keep transformations pure: input mappings are deep-copied and returned rather
than mutated. `JDQueue` accepts a path and delegates every write to
`atomic_write_json`. Rotation sorting uses `(never_swept_first,
last_swept_at_or_empty, casefolded_name)` and returns names only. Add CLI groups
`snapshot`, `queue`, and `rotation` matching the source script arguments while
emitting structured JSON.

- [ ] **Step 4: Run the engine-slice tests**

Run: `python -m unittest discover -s plugins/codex-job-scout/core/tests -p 'test_snapshot.py' -v`  
Expected: `OK`.

Run: `python -m unittest discover -s plugins/codex-job-scout/core/tests -p 'test_queue.py' -v`  
Expected: `OK`.

Run: `python -m unittest discover -s plugins/codex-job-scout/core/tests -p 'test_rotation.py' -v`  
Expected: `OK`.

- [ ] **Step 5: Commit the discovery mechanics**

```bash
git add compatibility/fixtures/engine plugins/codex-job-scout/core
git commit -m "feat: port snapshot queue and rotation"
```

### Task 7: Port Checkpoints and Add Simple Workspace Locking

**Files:**
- Create: `plugins/codex-job-scout/core/job_scout/checkpoint.py`
- Create: `plugins/codex-job-scout/core/job_scout/locking.py`
- Create: `plugins/codex-job-scout/core/tests/test_checkpoint.py`
- Create: `plugins/codex-job-scout/core/tests/test_locking.py`
- Modify: `plugins/codex-job-scout/core/job_scout/cli.py`

**Interfaces:**
- Produces: `CheckpointStore.init/stage/save/find_incomplete`; `WorkspaceLock.acquire`, `heartbeat`, `release`, and context-manager methods; `LockHeldError` includes the incumbent metadata.

- [ ] **Step 1: Write failing checkpoint and lock tests**

```python
class LockTest(unittest.TestCase):
    def test_second_writer_is_rejected_and_release_allows_next(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            workspace = Path(raw)
            first = WorkspaceLock(workspace, command="ultramode")
            first.acquire()
            with self.assertRaises(LockHeldError):
                WorkspaceLock(workspace, command="tune").acquire()
            first.release()
            WorkspaceLock(workspace, command="tune").acquire().release()

    def test_six_hour_lock_is_removed_as_stale(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            workspace = Path(raw)
            state_dir = workspace / ".job-scout"
            state_dir.mkdir()
            (state_dir / ".job-scout.lock").write_text(json.dumps({
                "version": 1,
                "owner_token": "old",
                "host": "other",
                "pid": 999,
                "platform": "test",
                "command": "ultramode",
                "started_at": "2026-07-10T00:00:00Z",
                "heartbeat_at": "2026-07-10T00:00:00Z",
            }))
            lock = WorkspaceLock(
                workspace,
                command="config",
                clock=lambda: datetime.fromisoformat(
                    "2026-07-10T07:00:00+00:00"
                ),
            )
            lock.acquire()
            self.assertEqual(lock.metadata["command"], "config")
            lock.release()
```

Checkpoint tests reproduce all nine incumbent shell assertions, including a
workspace path containing spaces and idempotent saves.

- [ ] **Step 2: Run tests and verify missing modules**

Run: `python -m unittest discover -s plugins/codex-job-scout/core/tests -p 'test_checkpoint.py' -v`  
Expected: import error.

Run: `python -m unittest discover -s plugins/codex-job-scout/core/tests -p 'test_locking.py' -v`  
Expected: import error.

- [ ] **Step 3: Implement checkpoint and lock semantics**

Acquire with `os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)`.
Metadata is JSON containing `version: 1`, hostname, PID, `platform.system()`,
command, `started_at`, and `heartbeat_at`. Same-host PID liveness uses `os.kill(pid,
0)` where supported and treats permission errors as alive. Other-host locks are
stale only when heartbeat age exceeds six hours. Before acquisition, quarantine
files matching `.job-scout.lock*conflict*`. Release removes the lock only when
its random owner token still matches. Checkpoints preserve the source manifest
and stage-artifact behavior and use atomic JSON/file replacement.

- [ ] **Step 4: Run checkpoint and lock tests**

Run: `python -m unittest discover -s plugins/codex-job-scout/core/tests -p 'test_checkpoint.py' -v`  
Expected: `OK`.

Run: `python -m unittest discover -s plugins/codex-job-scout/core/tests -p 'test_locking.py' -v`  
Expected: `OK` on the current OS with liveness calls mocked for portability.

- [ ] **Step 5: Commit resilience primitives**

```bash
git add plugins/codex-job-scout/core
git commit -m "feat: add checkpoints and workspace locks"
```

### Task 8: Port Delta Validation and Atomic Tracker Merge

**Files:**
- Create: `plugins/codex-job-scout/core/job_scout/delta.py`
- Create: `plugins/codex-job-scout/core/job_scout/merge.py`
- Create: `plugins/codex-job-scout/core/tests/test_delta.py`
- Create: `plugins/codex-job-scout/core/tests/test_merge.py`
- Copy: `skills/_ultra-engine/tests/fixtures/delta-good.json`, `tracker-mini.json`, and `tracker-payload.json` to `compatibility/fixtures/merge/`
- Modify: `plugins/codex-job-scout/core/job_scout/cli.py`

**Interfaces:**
- Produces: `validate_delta(envelope, workspace) -> None`, `merge_deltas(tracker, envelopes, today) -> MergeResult`, and `merge_tracker_file(workspace, tracker_path, delta_paths, today) -> MergeResult`.

- [ ] **Step 1: Write failing validator and merge parity tests**

Cover valid envelopes, missing counts, invalid IDs, paths escaping `.job-scout`,
duplicate delta IDs, incumbent ID/key mismatch repair, rejected-entry handling,
same-role cross-source merge, canonical URL preference, `also_seen_on`, null
preservation, and all-or-nothing failure.

Use this atomicity assertion:

```python
before = tracker_path.read_bytes()
with self.assertRaises(DeltaValidationError):
    merge_tracker_file(workspace, tracker_path, [bad_delta], "2026-07-10")
self.assertEqual(tracker_path.read_bytes(), before)
```

- [ ] **Step 2: Run tests and verify missing modules**

Run: `python -m unittest discover -s plugins/codex-job-scout/core/tests -p 'test_delta.py' -v`  
Expected: import error.

Run: `python -m unittest discover -s plugins/codex-job-scout/core/tests -p 'test_merge.py' -v`  
Expected: import error.

- [ ] **Step 3: Implement validation-first deterministic merge**

Validate every envelope before copying the tracker. Index incumbents by exact ID
and `identity.fingerprint`. Apply envelopes in source-name then delta-ID order.
Use the canonical-source preference from `ultramode-sources.md`; add mirrors to
`also_seen_on` without duplicates; preserve incumbent unknown keys; set only the
fields owned by the merge contract. Validate the full candidate tracker and
atomically replace once. Return counts matching the incumbent merger stdout.
Expose `validate-delta` and `merge-tracker` CLI subcommands.

- [ ] **Step 4: Run validator, merger, and full core tests**

Run: `python -m unittest discover -s plugins/codex-job-scout/core/tests -p 'test_delta.py' -v`  
Expected: `OK`.

Run: `python -m unittest discover -s plugins/codex-job-scout/core/tests -p 'test_merge.py' -v`  
Expected: all 18 incumbent Python merger cases and new atomicity cases pass.

- [ ] **Step 5: Commit canonical merge parity**

```bash
git add compatibility/fixtures/merge plugins/codex-job-scout/core
git commit -m "feat: port validated tracker merge"
```

### Task 9: Port Scorecards and Render Payload Ordering

**Files:**
- Create: `plugins/codex-job-scout/core/job_scout/scorecard.py`
- Create: `plugins/codex-job-scout/core/job_scout/payload.py`
- Create: `plugins/codex-job-scout/core/tests/test_scorecard.py`
- Create: `plugins/codex-job-scout/core/tests/test_payload.py`
- Copy: `skills/_ultra-engine/tests/fixtures/sources-mini.json`, `tracker-mini.json`, and `tracker-payload.json` to `compatibility/fixtures/reports/`
- Modify: `plugins/codex-job-scout/core/job_scout/cli.py`

**Interfaces:**
- Produces: `build_scorecard(run_dir, tracker, today) -> dict`, `build_ultramode_payload(tracker, scorecard, today, source_count) -> dict`, and generic per-view payload builders.

- [ ] **Step 1: Write failing scorecard and ordering tests**

Reproduce the 11 incumbent scorecard assertions and 10 payload assertions.
Assert tier order A/B/C/D, confidence ordering where applicable, posted date
ordering, two-gate D last, single-gate A/B near misses excluded from results,
missing optional signals omitted rather than set to null, null tiers counted,
and scorecard disclosures embedded.

- [ ] **Step 2: Run and verify missing implementations**

Run: `python -m unittest discover -s plugins/codex-job-scout/core/tests -p 'test_scorecard.py' -v`  
Expected: import error.

Run: `python -m unittest discover -s plugins/codex-job-scout/core/tests -p 'test_payload.py' -v`  
Expected: import error.

- [ ] **Step 3: Implement pure scorecard and payload builders**

Read all completed `sweep-*.json` stages, `merge.json`, `jd-fetch.json`,
`rotation.json`, and `pipeline-errors.json`; disclose caps, rotated-out sources,
source errors, pipeline errors, and deferred JD work using incumbent wording.
Payload builders never mutate or sort the tracker in place. Use explicit enum
rank maps and UTC-safe date parsing. Add `scorecard` and `payload` CLI groups.

- [ ] **Step 4: Run report-data and full core suites**

Run: `python -m unittest discover -s plugins/codex-job-scout/core/tests -p 'test_scorecard.py' -v`  
Expected: `OK`.

Run: `python -m unittest discover -s plugins/codex-job-scout/core/tests -p 'test_payload.py' -v`  
Expected: `OK`.

Run: `python -m unittest discover -s plugins/codex-job-scout/core/tests -v`  
Expected: all core tests pass.

- [ ] **Step 5: Commit report-data parity**

```bash
git add compatibility/fixtures/reports plugins/codex-job-scout/core
git commit -m "feat: port scorecards and payloads"
```

### Task 10: Replace Model Rendering with Deterministic Renderers

**Files:**
- Create: `plugins/codex-job-scout/core/job_scout/render/__init__.py`
- Create: `plugins/codex-job-scout/core/job_scout/render/html.py`
- Create: `plugins/codex-job-scout/core/job_scout/render/markdown.py`
- Create: `plugins/codex-job-scout/core/job_scout/render/views.py`
- Create: `plugins/codex-job-scout/core/tests/test_render_html.py`
- Create: `plugins/codex-job-scout/core/tests/test_render_markdown.py`
- Move: `skills/_visualizer/assets/theme.css` to `plugins/codex-job-scout/assets/theme.css`
- Move: `skills/_visualizer/assets/interactive.js` to `plugins/codex-job-scout/assets/interactive.js`
- Copy: `match-jobs-pre-phase-a.json`, `match-jobs-with-tags.json`, `ultramode-also-seen.json`, `ultramode-empty.json`, `ultramode-gated.json`, and `ultramode-multi-source.json` from the current visualizer examples into `compatibility/fixtures/render-inputs/`; create explicit minimal input JSON for each remaining view
- Create: `compatibility/fixtures/render-golden/`
- Modify: `plugins/codex-job-scout/core/job_scout/cli.py`

**Interfaces:**
- Produces: `render_html(view, data, css, javascript) -> str`, `render_markdown(view, data) -> str`, and `render_report(view, format, data, output_dir) -> RenderResult`.

- [ ] **Step 1: Write failing escape, view, and atomic-output tests**

```python
class HtmlRenderTest(unittest.TestCase):
    def test_job_content_is_escaped_and_assets_are_embedded(self) -> None:
        body = render_html(
            "match-jobs",
            {"title": "<script>x</script>", "subtitle": "s", "generated_at": "now",
             "filename": "match-jobs-latest.html", "results": [],
             "tier_counts": {"a": 0, "b": 0, "c": 0, "d": 0, "total": 0}},
            css=".x{}",
            javascript="console.log('x')",
        )
        self.assertNotIn("<script>x</script>", body)
        self.assertIn("&lt;script&gt;x&lt;/script&gt;", body)
        self.assertIn("console.log('x')", body)
```

Add golden subtests for `match-jobs`, `job-search`,
`check-job-notifications`, `funnel-report`, `check-inbox`, `interview-prep`, and
`ultramode`, in both HTML and Markdown, plus empty/gated/near-miss/partial cases.

- [ ] **Step 2: Run render tests and verify missing package**

Run: `python -m unittest discover -s plugins/codex-job-scout/core/tests -p 'test_render_*.py' -v`  
Expected: import error for `job_scout.render`.

- [ ] **Step 3: Implement escaped component functions and view registry**

Use `html.escape(value, quote=True)` for every external value. Define focused
component functions for hero, toolbar, source chip, tier pill, dimension table,
job card, gated group, near-miss rail, scorecard strip, metrics, thread card,
and interview section. `views.py` maps the seven view names to complete HTML and
Markdown composition functions. Only CSS, JavaScript, and fixed structural
markup are trusted raw strings. `render_report` validates the payload, writes
HTML atomically, and returns Markdown in memory. Add CLI command:

`render --view VIEW --format html|markdown --input PAYLOAD --output-dir DIR`.

- [ ] **Step 4: Run render, JavaScript, and full core tests**

Run: `python -m unittest discover -s plugins/codex-job-scout/core/tests -p 'test_render_*.py' -v`  
Expected: `OK` and every golden file matches.

Run: `node --check plugins/codex-job-scout/assets/interactive.js` when Node is available; otherwise run the existing JavaScript syntax check in CI's optional tooling job.  
Expected: exit 0 when run.

Run: `python -m unittest discover -s plugins/codex-job-scout/core/tests -v`  
Expected: all tests pass.

- [ ] **Step 5: Commit deterministic reports**

```bash
git add compatibility/fixtures/render-inputs compatibility/fixtures/render-golden \
  plugins/codex-job-scout/assets plugins/codex-job-scout/core
git commit -m "feat: add deterministic report rendering"
```

### Task 11: Relocate Shared and Internal Capability References

**Files:**
- Move: `skills/shared-references/*` to `plugins/codex-job-scout/references/shared/`
- Move: `_company-researcher`, `_cover-letter-writer`, `_cv-optimizer`, `_cv-section-rewriter`, `_gate-engine`, `_job-matcher`, `_profile-optimizer`, `_recruiter-engagement`, `_source-discovery`, and `_source-sweep` playbooks and references to `plugins/codex-job-scout/references/internal/`
- Delete after parity: legacy `_ultra-engine` shell scripts and `_visualizer` model renderer
- Create: `tools/test_reference_layout.py`
- Create: `plugins/codex-job-scout/references/internal/INDEX.md`

**Interfaces:**
- Consumes: the source skill/reference corpus already present in the target clone.
- Produces: a reference tree in which every link resolves relative to the referring file and no direct child of plugin `skills/` lacks `SKILL.md`.

- [ ] **Step 1: Write the failing layout/link audit**

Implement a standard-library test that scans Markdown links and backtick paths,
resolves local paths, and reports missing targets. Assert the plugin `skills/`
directory, once created, contains only the 18 names from
`command-contract.json`. Assert no internal reference starts with YAML skill
frontmatter.

- [ ] **Step 2: Run the audit against the unported layout**

Run: `python -m unittest tools.test_reference_layout -v`  
Expected: failure because references still live under the source `skills/`
layout and the plugin reference tree is absent.

- [ ] **Step 3: Move capability material and update exact path families**

Move these model playbooks under `references/internal/`: company researcher,
cover-letter writer, CV optimizer, CV-section rewriter, gate engine, job
matcher, profile optimizer, recruiter engagement, source discovery, and source
sweep. Replace their skill frontmatter with an index entry containing purpose,
consumers, required inputs, and output envelope. Point all mechanical
`_ultra-engine` calls to `scripts/job_scout.py` CLI commands. Point all
visualizer calls to `render` CLI. From command skills, update shared links to
`../../references/shared/` followed by the exact referenced filename; use
relative sibling paths inside the reference tree.

- [ ] **Step 4: Run link, core, and source-read-only checks**

Run: `python -m unittest tools.test_reference_layout -v`  
Expected: `OK`.

Run: `python -m unittest discover -s plugins/codex-job-scout/core/tests -v`  
Expected: all tests pass after removal of legacy runtime scripts.

Run: `python tools/check_source_read_only.py --source ../claude-job-scout --baseline compatibility/source-status.json`  
Expected: exit 0.

- [ ] **Step 5: Commit the private capability boundary**

```bash
git add plugins/codex-job-scout/references plugins/codex-job-scout/core \
  plugins/codex-job-scout/scripts tools/test_reference_layout.py
git commit -m "refactor: make internal capabilities private"
```

### Task 12: Define Codex Adapter Contracts and Generate Explicit Skill Metadata

**Files:**
- Create: `plugins/codex-job-scout/references/adapters/chrome.md`
- Create: `plugins/codex-job-scout/references/adapters/web.md`
- Create: `plugins/codex-job-scout/references/adapters/subagents.md`
- Create: `plugins/codex-job-scout/references/adapters/confirmations.md`
- Create: `plugins/codex-job-scout/references/adapters/reports.md`
- Create: `tools/generate_skill_metadata.py`
- Create: `tools/test_adapter_contracts.py`
- Create: `agents/openai.yaml` under each of `analyze-cv`, `apply`, `bend`, `check-inbox`, `check-job-notifications`, `config`, `cover-letter`, `create-alerts`, `deep-sweep`, `funnel-report`, `index-docs`, `interview-prep`, `job-search`, `match-jobs`, `optimize-profile`, `sources`, `tune`, and `ultramode`
- Modify: `plugins/codex-job-scout/.codex-plugin/plugin.json`

**Interfaces:**
- Produces: five host-capability contracts; generated `openai.yaml` with `allow_implicit_invocation: false`; manifest `skills: "./skills/"`.

- [ ] **Step 1: Write failing adapter-policy tests**

The test must assert: Chrome contract names `chrome:control-chrome`; logged-in
work has no fallback; web is public/sessionless GET only; subagents are
optional, delta-only, and cannot browse/write state; confirmation contract
contains final-submit/send/save boundaries; reports preserve files on open
failure; every user skill metadata policy is false; and no internal skill
directory exists.

- [ ] **Step 2: Run the policy tests and verify missing adapters**

Run: `python -m unittest tools.test_adapter_contracts -v`  
Expected: failure listing the five missing adapter references and metadata.

- [ ] **Step 3: Write exact adapter rules and metadata generator**

The generator reads `compatibility/command-contract.json`, creates one skill
directory per command, and uses this complete formatter:

```python
def render_openai_yaml(command: dict[str, object]) -> str:
    name = str(command["name"])
    display_name = name.replace("-", " ").title()
    description = str(command["description"]).replace("\n", " ").strip()[:120]
    safe_description = description.replace('"', "'")
    return (
        "interface:\n"
        f'  display_name: "{display_name}"\n'
        f'  short_description: "{safe_description}"\n'
        f'  default_prompt: "Run $codex-job-scout:{name} and follow its workflow."\n'
        "policy:\n"
        "  allow_implicit_invocation: false\n"
    )
```

Use `yaml`-free deterministic text generation. Reject unknown commands and an
existing non-generated metadata file. The Chrome reference requires reading
the installed Chrome skill before browser work. The subagent reference maps the
legacy envelope to Codex spawn/follow-up semantics and caps workers at available
slots. Add `"skills": "./skills/"` to the manifest only after the generated
tree passes.

- [ ] **Step 4: Generate and validate adapter metadata**

Run: `python tools/generate_skill_metadata.py`  
Expected: `generated metadata for 18 skills`.

Run: `python -m unittest tools.test_adapter_contracts -v`  
Expected: `OK`.

Run: `python -m unittest tools.test_plugin_layout -v`  
Expected: `OK` with the skills path present.

- [ ] **Step 5: Commit Codex capability policies**

```bash
git add compatibility plugins/codex-job-scout tools
git commit -m "feat: add Codex adapter policies"
```

### Task 13: Port Local-State and Analysis Commands

**Files:**
- Create/modify: skill bodies for `analyze-cv`, `config`, `tune`, `index-docs`, `funnel-report`, `cover-letter`, and `interview-prep`
- Create: `tools/test_local_command_contracts.py`
- Modify: relevant internal and shared references

**Interfaces:**
- Consumes: core CLI, shared references, internal capability playbooks, render adapter, and confirmation adapter.
- Produces: seven explicit-only Codex skills with incumbent argument forms and state effects.

- [ ] **Step 1: Write failing command-contract tests**

For each command, parse `SKILL.md` frontmatter and assert it contains only
`name` and `description`. Assert exact leaf name, required argument forms from
`command-contract.json`, workspace bootstrap, lock use before writes, Python CLI
calls for mechanical operations, preserved output path, and no Claude tool
names or `.claude-plugin` path.

- [ ] **Step 2: Run and verify the seven skill bodies are absent**

Run: `python -m unittest tools.test_local_command_contracts -v`  
Expected: failure listing seven missing `SKILL.md` files.

- [ ] **Step 3: Port the seven orchestrators**

Move the incumbent bodies into their generated skill directories and make these
mechanical substitutions:

- replace `disable-model-invocation`, `allowed-tools`, `argument-hint`, and
  per-skill `version` frontmatter with name/description only;
- replace workspace writes and validation recipes with named
  `scripts/job_scout.py` commands;
- replace internal skill loading with explicit reads under
  `references/internal/`;
- replace shared paths with `../../references/shared/`;
- replace visualizer dispatch with deterministic `render` CLI plus reports
  adapter;
- add lock acquire/release around every possible write path;
- preserve all user questions, scoring logic, filenames, and British English.

Keep tracker-ID/URL handling for `cover-letter` and the exact `interview-prep`
missing-JD behavior. Do not add browser access to commands that do not already
need it.

- [ ] **Step 4: Run local command, reference, and core tests**

Run: `python -m unittest tools.test_local_command_contracts tools.test_reference_layout -v`  
Expected: `OK`.

Run: `python -m unittest discover -s plugins/codex-job-scout/core/tests -v`  
Expected: all tests pass.

- [ ] **Step 5: Commit the first command slice**

```bash
git add plugins/codex-job-scout/skills plugins/codex-job-scout/references tools
git commit -m "feat: port local job scout commands"
```

### Task 14: Port Discovery and Read-Only Browser Commands

**Files:**
- Create/modify: skill bodies for `bend`, `check-job-notifications`, `job-search`, `match-jobs`, `optimize-profile`, `sources`, `ultramode`, and `deep-sweep`
- Create: `tools/test_discovery_command_contracts.py`
- Modify: LinkedIn, browser, source, subagent, and render references

**Interfaces:**
- Consumes: Chrome/web/subagent adapters, core snapshot/delta/merge/scorecard/payload/render CLI, internal gate/matcher/source playbooks.
- Produces: eight discovery commands with identical dedupe-before-extract, scopes, gates, ranking, redirects, and partial-run disclosures.

- [ ] **Step 1: Write failing discovery contract tests**

Assert every browser skill requires the Chrome adapter before claiming Chrome is
unavailable; every listing flow snapshots/deduplicates before opening JDs;
public web lanes are sessionless; subagent absence explicitly selects sequential
execution; `ultramode` retains all four scopes, checkpoint/resume, validated
delta fan-in, serial merge, fetch-then-gate, similar-jobs cap, scorecard, and
always-render; `deep-sweep` prints the incumbent retirement notice and delegates
to bare `ultramode`.

- [ ] **Step 2: Run and verify the eight bodies are absent**

Run: `python -m unittest tools.test_discovery_command_contracts -v`  
Expected: failure listing eight missing or unported skill bodies.

- [ ] **Step 3: Port discovery commands and the flagship pipeline**

For every command, replace frontmatter with `name` and `description` only;
replace workspace writes, validation, snapshots, queues, rotation, checkpoints,
delta validation, merges, scorecards, payloads, and rendering with named
`scripts/job_scout.py` CLI subcommands; replace internal skill loading with
explicit reads under `references/internal/`; replace shared paths with
`../../references/shared/`; and acquire/release the workspace lock around every
possible state write. Rewrite every `Agent tool` instruction to the subagent
adapter, every `WebFetch` instruction to the web adapter, and every `Claude
Chrome extension` instruction to the Chrome adapter. Keep browser activity on
the main thread. Preserve registry rules, optional third-party keys, source
rotation, JD budget 75, batches of at most five, one similar-jobs expansion
round, stage names, artifact paths, always-render, and scorecard wording.

- [ ] **Step 4: Run discovery, adapter, reference, and core suites**

Run:

```bash
python -m unittest \
  tools.test_discovery_command_contracts \
  tools.test_adapter_contracts \
  tools.test_reference_layout -v
```

Expected: `OK`.

Run: `python -m unittest discover -s plugins/codex-job-scout/core/tests -v`  
Expected: all tests pass.

- [ ] **Step 5: Commit discovery parity**

```bash
git add plugins/codex-job-scout/skills plugins/codex-job-scout/references tools
git commit -m "feat: port discovery and ultramode commands"
```

### Task 15: Port External-Mutation and Inbox Commands

**Files:**
- Create/modify: skill bodies for `apply`, `check-inbox`, and `create-alerts`
- Create: `tools/test_mutation_command_contracts.py`
- Modify: recruiter, browser, confirmation, and state references

**Interfaces:**
- Consumes: Chrome and confirmation adapters, core state/lock CLI, recruiter playbook.
- Produces: three commands that preserve current capabilities while stopping at explicit external mutation boundaries.

- [ ] **Step 1: Write failing mutation-safety tests**

Assert `apply` never submits without approval and never enters sensitive data;
external forms hand off; `check-inbox` never sends without approval and keeps
thread/job linkage; `create-alerts` previews 3–5 derived alerts or the manual
criteria and confirms before creation. Assert all three acquire the lock before
local state writes, release in cleanup, and use only the Chrome adapter for
logged-in work.

- [ ] **Step 2: Run and verify the final three bodies are absent**

Run: `python -m unittest tools.test_mutation_command_contracts -v`  
Expected: failure listing three missing or unported bodies.

- [ ] **Step 3: Port mutation workflows with centralized confirmation language**

For each command, replace frontmatter with `name` and `description` only;
replace workspace writes and validation with named `scripts/job_scout.py` CLI
subcommands; replace internal skill loading with explicit reads under
`references/internal/`; replace shared paths with
`../../references/shared/`; replace Claude browser language with the Chrome
adapter; acquire/release the workspace lock around every local write; and
reference the shared confirmation contract at the exact final submit, send, or
create step. Preserve Easy Apply field rules, external handoff, recruiter
qualification and drafting, job-link extraction, alert derivation,
tracker/thread state effects, and explicit user control. Do not add test-only or
dry-run behavior to the production command contract.

- [ ] **Step 4: Run every command and reference contract test**

Run: `python -m unittest discover -s tools -p 'test_*contracts.py' -v`  
Expected: all 18 command contracts and adapter contracts pass.

Run: `python -m unittest tools.test_reference_layout tools.test_plugin_layout -v`  
Expected: `OK`.

- [ ] **Step 5: Commit the complete command surface**

```bash
git add plugins/codex-job-scout/skills plugins/codex-job-scout/references tools
git commit -m "feat: port protected browser mutations"
```

### Task 16: Add Documentation, Audits, and Cross-Platform CI

**Files:**
- Create: `plugins/codex-job-scout/AGENTS.md`
- Modify: `README.md`
- Modify: `plugins/codex-job-scout/README.md`
- Modify: `plugins/codex-job-scout/QUICKSTART.md`
- Create: `plugins/codex-job-scout/docs/COMMANDS.md`
- Create: `plugins/codex-job-scout/docs/INSTALL.md`
- Create: `plugins/codex-job-scout/docs/TROUBLESHOOTING.md`
- Create: `tools/audit_plugin.py`
- Create: `tools/test_audit.py`
- Create: `.github/workflows/test.yml`
- Remove: `.claude-plugin/`, `.claude/`, and `CLAUDE.md` from the target repository

**Interfaces:**
- Produces: complete install/update/uninstall/command-map documentation, one-command audit, and OS test matrix.

- [ ] **Step 1: Write failing audit tests**

Audit rules must assert: exactly 18 skill directories; all local links resolve;
manifest and folder names match; every `openai.yaml` disables implicit
invocation; no plugin-runtime file contains `.claude-plugin`, `Claude Chrome
extension`, `Agent tool`, `WebFetch`, `disable-model-invocation`, `allowed-tools`,
or `mcp__claude`; no Python import outside the standard library allowlist; no
Anthropic/OpenAI API-key environment names; no shell runtime file remains; and
no MCP/app manifest exists.

- [ ] **Step 2: Run the audit and verify legacy artifacts fail it**

Run: `python -m unittest tools.test_audit -v`  
Expected: failure listing the target's remaining Claude runtime artifacts and
missing documentation.

- [ ] **Step 3: Port docs, remove runtime artifacts, and add CI**

Document exact local and Git marketplace installation, Chrome prerequisite,
Python detection on macOS/Linux/Windows, new-thread requirement, cachebuster
updates, uninstall, lock recovery, no-LLM-API boundary, and the one-to-one
Claude `/command` to Codex `$codex-job-scout:command` table.

`AGENTS.md` repeats source read-only, schema freeze, atomic writes, confirmation,
British English, and verification commands. CI uses `actions/setup-python` with
3.11 and 3.12 on `ubuntu-latest`, `macos-latest`, and `windows-latest`, then runs:

```text
python -m unittest compatibility.test_contract -v
python -m unittest discover -s plugins/codex-job-scout/core/tests -v
python -m unittest discover -s tools -p "test_*.py" -v
python tools/audit_plugin.py
```

Remove only target runtime artifacts; preserve Git history and approved
historical design documents.

- [ ] **Step 4: Run all tests and the audit**

Run: `python -m unittest compatibility.test_contract -v`  
Expected: `OK`.

Run: `python -m unittest discover -s plugins/codex-job-scout/core/tests -v`  
Expected: all tests pass.

Run: `python -m unittest discover -s tools -p 'test_*.py' -v`  
Expected: all tests pass.

Run: `python tools/audit_plugin.py`  
Expected: `PASS: 18 skills, 0 broken links, 0 forbidden runtime dependencies`.

- [ ] **Step 5: Commit distribution documentation and CI**

```bash
git add -A
git commit -m "docs: complete Codex distribution and CI"
```

### Task 17: Validate, Install, Smoke-Test, and Publish the Compatibility Handoff

**Files:**
- Create: `compatibility/REPORT.md`
- Create: `compatibility/CLAUDE-HANDOFF-PROMPT.md`
- Create: `docs/ACCEPTANCE-CHECKLIST.md`
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: complete marketplace/plugin, core tests, command audits, source baseline, installed Chrome plugin.
- Produces: validated local installation, evidence report, manual live-action checklist, and ready-to-paste Claude prompt.

- [ ] **Step 1: Write the final acceptance checklist before running it**

The checklist contains exact pass/fail rows for marketplace validation, plugin
validation, 18-skill discovery, Python preflight, existing-state round trip,
empty workspace bootstrap, one local analysis command, one read-only LinkedIn
command, sequential ultramode fixture run, optional multi-agent equivalence,
HTML/Markdown open behavior, and confirmation stops for apply/message/alert.

- [ ] **Step 2: Run complete fresh verification**

Run:

```bash
python -m unittest compatibility.test_contract -v
python -m unittest discover -s plugins/codex-job-scout/core/tests -v
python -m unittest discover -s tools -p 'test_*.py' -v
python tools/audit_plugin.py
python tools/check_source_read_only.py \
  --source ../claude-job-scout \
  --baseline compatibility/source-status.json
```

Expected: every command exits 0; no source status difference.

- [ ] **Step 3: Validate with the official plugin validator**

Run from the installed `plugin-creator` skill directory, using an isolated
development environment if its `yaml` dependency is not already available:

```bash
python scripts/validate_plugin.py \
  '/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/codex-job-scout/plugins/codex-job-scout'
```

Expected: validator success with no manifest, skill, asset, or reference error.
Any temporary validator dependency belongs in an OS temporary directory, not
the project or runtime package.

- [ ] **Step 4: Install through the actual marketplace flow**

Run:

```bash
codex plugin marketplace add \
  '/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/codex-job-scout'
codex plugin add codex-job-scout@codex-job-scout
codex plugin list
```

Expected: marketplace add succeeds, plugin is `installed, enabled`, version is
`0.15.0+codex.1` or the current cachebuster derivative, and its path resolves to
the new repository/cache rather than `claude-job-scout`.

- [ ] **Step 5: Smoke-test in a new Codex thread**

Use a temporary fixture workspace, not this repository. Confirm all 18 skills
are discoverable. Run Python preflight, `$codex-job-scout:config`, a fixture
`$codex-job-scout:match-jobs`, and sequential `$codex-job-scout:ultramode
external`. When the user's Chrome session is available, run one read-only
LinkedIn collection flow. Exercise `apply`, `check-inbox`, and `create-alerts`
only until their final confirmation, then decline.

Expected: every acceptance row is recorded as PASS or as an explicit manual
follow-up; no external mutation occurs.

- [ ] **Step 6: Write compatibility evidence and Claude handoff prompt**

`REPORT.md` records source commit, target commit, test commands/counts,
cross-platform CI status, install output, command inventory, state/hash parity,
browser checks, and any bounded manual gaps.

`CLAUDE-HANDOFF-PROMPT.md` instructs Claude to work only in
`claude-job-scout`, read this compatibility report, add the same simple lock
contract and stale cleanup without changing schemas, update Claude-side docs,
run the incumbent deterministic suite, and report exact diffs. It must not ask
Claude to port Codex metadata or Python internals unless compatibility findings
show a source-side defect.

Add a `0.15.0+codex.1` changelog entry describing the Codex port without
rewriting historical Claude entries.

- [ ] **Step 7: Commit final acceptance evidence**

```bash
git add compatibility docs/ACCEPTANCE-CHECKLIST.md CHANGELOG.md
git commit -m "test: verify installable Codex job scout"
```

- [ ] **Step 8: Confirm final repository and source states**

Run: `git status --short`  
Expected in `codex-job-scout`: no output.

Run: `git log --oneline --decorate -18`  
Expected: the design commit plus one focused commit for each completed task.

Run:

```bash
python tools/check_source_read_only.py \
  --source ../claude-job-scout \
  --baseline compatibility/source-status.json
```

Expected: exit 0 and no output.

## Final Review Gate

Before declaring completion, use `superpowers:verification-before-completion`,
rerun Task 17 Step 2 from a clean target worktree, inspect `git diff` and
`git status`, and verify the installed plugin points to `codex-job-scout`.

# Codex Job Scout Migration Design

**Status:** Approved 10 July 2026  
**Source baseline:** `claude-job-scout` commit `f5e25ce`, tag `v0.15.0`  
**Target:** sibling repository `codex-job-scout`  
**Selected approach:** compatibility-first refactor

## 1. Purpose

Create an installable Codex plugin that preserves the functionality and command
contracts of the existing Claude `linkedin-job-hunter` plugin while establishing
a platform-neutral, deterministic core.

Users must be able to switch between the Claude and Codex plugins in the same
job-search workspace without losing findings or invalidating tracking,
deduplication, caches, or trust guarantees.

The source `claude-job-scout` repository is consultation-only throughout this
project. All generated files, commits, tests, and implementation work occur in
the sibling `codex-job-scout` repository.

## 2. Goals

1. Preserve all 18 user-facing command names, arguments, defaults, redirects,
   safety boundaries, and material outputs.
2. Keep existing `.job-scout/` workspaces interoperable between Claude and
   Codex without an independent Codex schema evolution.
3. Preserve canonical IDs, fingerprints, hashes, cache keys, tracker state,
   merge rules, ordering, and deduplication.
4. Replace the Unix-specific Bash/`jq` spine with a cross-platform Python 3.11+
   standard-library core.
5. Replace model-interpreted report rendering with deterministic HTML and
   Markdown rendering.
6. Use Codex-native plugin packaging, explicit skill invocation, Chrome control,
   optional subagents, and marketplace installation.
7. Require no Anthropic or OpenAI API keys, SDKs, or usage-billed LLM API calls.
8. Prove compatibility through fixtures, automated tests, real plugin
   installation, and safe browser smoke tests.

## 3. Non-goals

- Do not modify `claude-job-scout` during this project.
- Do not redesign the `.job-scout/` domain schemas.
- Do not introduce a hosted service, database, distributed lock, or LLM API.
- Do not vendor or reproduce the proprietary Codex Chrome plugin.
- Do not use computer use, Playwright/Selenium/Puppeteer servers, or credential
  scraping.
- Do not submit real applications, messages, profile edits, or alerts during
  automated acceptance testing.
- Do not make simultaneous cross-device use safe. One active device per
  workspace remains the supported model.

## 4. Approaches considered

### 4.1 Direct compatibility port

Copy the repository and replace Claude-specific metadata and tool names. This
is fast but retains Unix-only scripts, model-driven rendering, mixed platform
concerns, and weak compatibility evidence. Rejected.

### 4.2 Compatibility-first refactor

Freeze existing behaviour as fixtures, port the deterministic layer to Python,
isolate Codex adapters, then migrate the skills. This provides meaningful
refactoring while constraining behavioural drift. Selected.

### 4.3 Ground-up redesign

Replace the skill-driven system with a new application and thin skill wrappers.
This risks losing subtle behaviour embedded in the existing skills and
references, and makes state compatibility harder to prove. Rejected.

## 5. Repository and plugin structure

The repository is both a self-contained marketplace and the home of the plugin:

```text
codex-job-scout/
├── .agents/plugins/marketplace.json
├── README.md
├── compatibility/
│   ├── SOURCE_COMMIT
│   ├── command-contract.json
│   └── fixtures/
├── docs/
└── plugins/
    └── codex-job-scout/
        ├── .codex-plugin/plugin.json
        ├── AGENTS.md
        ├── skills/
        │   ├── analyze-cv/
        │   ├── apply/
        │   └── ...all 18 user skills...
        ├── core/
        │   ├── job_scout/
        │   └── tests/
        ├── references/
        │   ├── internal/
        │   └── shared/
        └── assets/
```

The plugin folder and manifest name are both `codex-job-scout`. The first Codex
version is `0.15.0+codex.1`, aligning the functional baseline with Claude
release `0.15.0`.

The repository preserves the source Git history. The inherited source remote is
named `claude-upstream`; no writable Codex remote is configured by this project.

## 6. Component boundaries

### 6.1 User skills

Thin Codex orchestrators retain the existing leaf command names and argument
forms. Codex exposes them through namespaced invocation, for example:

```text
$codex-job-scout:ultramode
$codex-job-scout:apply <tracker-id>
$codex-job-scout:tune add title <value>
```

Every user-facing skill includes `agents/openai.yaml` with:

```yaml
policy:
  allow_implicit_invocation: false
```

This is the Codex-native replacement for Claude's
`disable-model-invocation: true`.

### 6.2 Internal capabilities

Claude's 12 underscore-prefixed internal skills become capability playbooks
under `references/internal/` or deterministic core modules, according to their
responsibility. They are loaded explicitly by user orchestrators or embedded in
self-contained subagent prompts. They are not Codex skills, cannot be invoked
from the skill picker, and do not expand the 18-command public surface.

### 6.3 Platform-neutral core

`core/job_scout/` owns deterministic operations:

- state loading and validation;
- canonical JSON and hashing;
- job/source fingerprinting and namespaced IDs;
- snapshots, queues, rotation, checkpoints, and scorecards;
- delta validation and tracker merges;
- gate/scoring payload persistence;
- report payload construction and ordering;
- report retention and deterministic rendering;
- workspace locking and stale-lock recovery.

The core uses Python 3.11+ and the standard library only. It does not import
Codex APIs or know about Claude/Codex skill names.

### 6.4 Codex adapters

Adapters isolate capabilities whose invocation differs by host:

- official Chrome control for logged-in sites;
- native web access for public HTTP/RSS/ATS sources;
- optional subagent dispatch and fan-in;
- user confirmations;
- local report opening;
- conversation-facing progress and error messages.

Adapters return the same structured envelopes consumed by the deterministic
core. Canonical state writes never occur inside an adapter or subagent.

### 6.5 Shared references and assets

Shared references move out of `skills/` so Codex does not interpret a
reference-only directory as a malformed skill. Skills link to root reference
files using paths relative to their own directories.

Existing report styling and client-side interactions are retained as bundled
assets.

## 7. Command compatibility

The following leaf commands remain:

1. `analyze-cv`
2. `apply`
3. `bend`
4. `check-inbox`
5. `check-job-notifications`
6. `config`
7. `cover-letter`
8. `create-alerts`
9. `deep-sweep`
10. `funnel-report`
11. `index-docs`
12. `interview-prep`
13. `job-search`
14. `match-jobs`
15. `optimize-profile`
16. `sources`
17. `tune`
18. `ultramode`

`deep-sweep` remains the deprecated alias for bare `ultramode`. Existing
argument hints, zero-argument defaults, subcommands, redirects, report names,
and next-step guidance are preserved. Documentation provides a one-to-one map
from Claude `/command` syntax to Codex `$codex-job-scout:command` syntax.

## 8. Shared `.job-scout/` state contract

`.job-scout/` remains the sole workspace source of truth. The Codex plugin
preserves:

- existing filenames and directory layout;
- schema versions and enum values;
- tracker status transitions;
- full-JD blob paths;
- source identities and cross-source fingerprints;
- CV/profile/rubric cache keys;
- archive and retention rules;
- existing checkpoint/resume semantics;
- fields unknown to the Codex implementation.

The Codex plugin does not introduce an independent state migration. A future
schema change requires explicit user authorization in a coding session and a
coordinated compatibility decision for both plugins.

Canonical hashes and identifiers must match the current shell/`jq` outputs
exactly. Golden fixtures cover whitespace, key ordering, absent/null values,
Unicode normalization, URLs, and legacy state.

All replacement writes use a temporary file in the destination directory,
validation, flush, and `os.replace`. Invalid or interrupted work leaves the
previous valid state untouched. Corrupt or conflicting files are quarantined
with diagnostics rather than silently discarded.

## 9. Workspace locking

Commands that may write create `.job-scout/.job-scout.lock` using exclusive
creation. The lock contains:

- format version;
- hostname and process ID;
- platform;
- command;
- start and heartbeat timestamps.

Behaviour:

1. An active lock stops a second writer with a clear message.
2. A same-host lock whose process is dead is stale immediately.
3. A lock with no heartbeat for six hours is stale and removed automatically.
4. Lock release occurs in a `finally` path.
5. iCloud conflict copies are quarantined and reported.

The existing Claude plugin does not yet honour this lock. Therefore normal
sequential switching is supported, while simultaneous Claude/Codex mutation is
documented as unsupported until the Claude side receives the matching change.
The final project includes a ready-to-paste prompt for that follow-up.

## 10. Browser, web, and API boundaries

Logged-in LinkedIn and other login-walled work uses the official
`chrome:control-chrome` capability and the user's existing Chrome session. The
Codex Chrome plugin is an installation prerequisite.

Public sessionless sources use Codex-native web access for read-only HTTP GETs.
Existing optional third-party job-board keys remain supported, but the plugin
introduces no Anthropic/OpenAI API key, SDK, or usage-billed LLM API path. Claude
and Codex reasoning runs through the user's normal product subscriptions.

If a capability is unavailable, the affected command or source stops or skips
according to the existing contract and discloses what did not run. It never
silently changes browser mechanisms.

Forbidden behaviour remains:

- computer use;
- external browser-automation frameworks or servers;
- credential, cookie, or session-token extraction;
- entering passwords, bank details, national identifiers, or similar sensitive
  values;
- credentialed HTTP scraping of login-walled sources.

## 11. Parallel execution

Sequential execution is normative and must be functionally complete. When
Codex multi-agent tools are present, independent scoring, discovery, source
sweeps, research, drafting, and rendering preparation may run concurrently
within available worker slots.

Workers receive self-contained JSON inputs and return structured deltas. They
do not perform logged-in browser work or canonical writes. Fan-in validates all
results and merges them in deterministic source/job order, independent of
completion order. Missing multi-agent capability changes performance only.

## 12. Mutation confirmations

Explicit skill invocation authorizes navigation and read-only collection, not
irreversible external changes.

- Easy Apply stops before final submission.
- Recruiter responses remain drafts until explicit send approval.
- Alert creation and profile edits show a complete preview before saving.
- External applications remain human handoffs.
- Sensitive fields are never entered.
- Batch approval is allowed only after every included action is reviewable.

These rules are centralized in one adapter reference and tested as command
contracts.

## 13. Deterministic rendering

The model-driven `_visualizer` is replaced with Python standard-library
renderers. They preserve the current views, filenames, report lifecycle,
Modern Cards styling, and client-side interactions.

Requirements:

- escape job/user content by default;
- allow raw output only for bundled trusted assets;
- render HTML and Markdown without a model or third-party package;
- cover every view with golden fixtures;
- cover empty results, gated jobs, near misses, partial runs, and scorecard
  disclosures;
- write reports atomically under `.job-scout/reports/`.

The Chrome adapter attempts to open an HTML report. If opening fails, the
command returns a clickable absolute path; the generated report is never lost.

## 14. Error handling and recovery

The Python core emits structured results and stable error codes, with
diagnostics on stderr. State validation, delta validation, and write validation
fail before canonical replacement.

Per-source failures do not erase successful results. `ultramode` preserves its
always-render rule and discloses failed, skipped, capped, rotated, and deferred
work. Missing Python, Chrome, permissions, unsupported state, and lock
contention each receive targeted remediation guidance.

No error path silently enables computer use, installs a browser framework,
uses an LLM API, or submits an external action.

## 15. Installation and updates

The repository carries its own marketplace definition. Installation is:

```text
codex plugin marketplace add <path-or-git-url-to-codex-job-scout>
codex plugin add codex-job-scout@codex-job-scout
```

Preflight verifies:

- Python 3.11 or later;
- official Chrome plugin availability for browser commands;
- workspace writability;
- supported `.job-scout/` state version.

Local development updates use the Codex cachebuster/reinstall workflow. A new
thread is required after installation or reinstall so Codex loads the current
skills and tools.

No MCP server or app connector is added.

## 16. Migration sequence

1. Preserve source history in the sibling repository and record the source
   baseline.
2. Capture current command and deterministic behaviour as compatibility
   fixtures.
3. Restructure the target as a marketplace-backed Codex plugin.
4. Port deterministic operations to Python through red/green fixture parity.
5. Add locking and deterministic rendering.
6. Add Codex Chrome, web, subagent, confirmation, and report-opening adapters.
7. Port user skills and internal capability playbooks, then remove Claude-only
   metadata and tool language.
8. Update user, contributor, install, update, troubleshooting, and command-map
   documentation.
9. Validate, install, and smoke-test the real plugin.

Each stage must leave the target testable. The source repository remains
read-only.

## 17. Verification

### 17.1 Automated tests

- Unit tests for every operation formerly implemented in Bash/`jq`.
- Golden compatibility tests for hashes, IDs, fingerprints, snapshots,
  rotation, queues, validation, merges, scorecards, payloads, and reports.
- State round-trip tests, including preservation of unknown fields.
- Lock acquisition, contention, process-death, heartbeat, timeout, and cleanup
  tests.
- Renderer security and output fixtures for every report view.
- Command inventory, argument, redirect, and explicit-invocation contract
  tests.
- Reference-link and forbidden-Claude-runtime-term audits.
- No-LLM-API dependency audits.

### 17.2 Platform and packaging tests

- GitHub Actions matrix for macOS, Linux, and Windows with Python 3.11+.
- Codex marketplace and plugin validation.
- Real local marketplace addition and plugin installation.
- Discovery of all 18 namespaced user skills in a new thread.

### 17.3 Browser acceptance

- Representative read-only LinkedIn flows when the user's Chrome session is
  available.
- Mutation workflows tested only through the final confirmation boundary.
- Manual checklist for live submission/send/save actions.

## 18. Acceptance criteria

The migration is complete when:

1. `codex-job-scout` installs through its marketplace and validates as a Codex
   plugin.
2. All 18 user commands are discoverable with preserved arguments and
   behaviour.
3. Existing `.job-scout/` fixtures round-trip without schema or identity drift.
4. The cross-platform Python core passes on macOS, Linux, and Windows.
5. Deterministic HTML and Markdown reports pass golden and safety tests.
6. Sequential execution is complete; multi-agent execution produces equivalent
   merged results.
7. Browser mutation boundaries require explicit confirmation.
8. No Anthropic/OpenAI API dependency or unsupported browser fallback exists.
9. Real local installation and safe smoke tests pass.
10. The source `claude-job-scout` worktree shows no project-caused changes.

## 19. Deliverables

- Working sibling `codex-job-scout` marketplace repository.
- Approved design and detailed implementation plan, committed in the target.
- Cross-platform Python core and deterministic renderer.
- Ported Codex skills and adapters.
- Compatibility fixtures, automated tests, and CI matrix.
- Install, update, uninstall, command-map, troubleshooting, and contributor
  documentation.
- Compatibility report tied to source commit `f5e25ce`.
- Manual live-action acceptance checklist.
- Ready-to-paste Claude prompt for matching lock awareness and any other
  compatibility changes discovered during the port.
- Final evidence that the source repository remained unchanged.

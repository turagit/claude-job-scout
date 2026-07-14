---
name: _ultra-engine
description: Internal deterministic engine for the ultramode pipeline — scripts for snapshots, fingerprints, IDs, delta validation, tracker merges, rotation, JD budgeting, checkpoints, scorecard, and payload assembly. Loaded by orchestrator skills; never user-invoked.
allowed-tools: Read, Bash, Grep, Glob
disable-model-invocation: true
version: 0.1.0
---

The deterministic spine of the ultramode pipeline (Phase 14, spec 2026-07-02). Orchestrator skills MUST call these scripts for every mechanical operation — hand-rolled snapshots, merges, ID minting, ordering, or budget accounting are defects, not style choices. Scripts print machine-readable output, exit non-zero on any violation, and never write state non-atomically.

Resolve `SCRIPTS` as this skill's own `scripts/` directory (e.g. `skills/_ultra-engine/scripts` relative to the plugin root). `WS` is the workspace's `.job-scout` directory.

| Script | Call | Contract |
|---|---|---|
| snapshot | `bash $SCRIPTS/snapshot.sh $WS/tracker.json $WS/cache/ultramode-snapshot.json` | Non-rejected ids + canonical fingerprints; subagents read the FILE (pass its path, never inline the lists). |
| fingerprint | `bash $SCRIPTS/fingerprint.sh <company> <title> <location>` | THE fingerprint. Never re-derive in prose or a second implementation. |
| namespace_id | `bash $SCRIPTS/namespace_id.sh <provider> <board> <ext-id>` (or `--from-url <provider> <board> <url>`) | Collision-proof external ids; slugs `[a-z0-9-]`. |
| validate_delta | `python3 $SCRIPTS/validate_delta.py --ws $WS <delta.json>` | Rejects prose sources, malformed ids, undisclosed caps, missing JD blobs. Run on EVERY sweep return before merge. |
| merge_tracker | `python3 $SCRIPTS/merge_tracker.py --ws $WS --tracker $WS/tracker.json --today <YYYY-MM-DD> <delta...>` | Serial merge, canonical selection + `also_seen_on`, URL upgrade, atomic write. All-or-nothing: any invalid delta aborts untouched. |
| migrate_sources | `python3 $SCRIPTS/migrate_sources.py $WS/sources.json` | sources.json v1→v2 (auth_state + lifecycle lists), idempotent, atomic. Orchestrators run it on load when `schema_version < 2`. |
| auth_state | `bash $SCRIPTS/auth_state.sh set $WS/sources.json <name> <state> <ISO>` / `get <name>` | Observed auth-state transitions (`public\|auth-required\|signed-in\|session-expired`) + timestamp; never inferred, never secret-bearing. |
| rotation | `bash $SCRIPTS/rotation.sh pick <sources.json> 4` / `mark <sources.json> <name> <date>` | Staleness-ordered extension-lane rotation (D8). |
| jd_queue | `bash $SCRIPTS/jd_queue.sh push|pop|count $WS/cache/jd-queue.json ...` | Deferred JD-fetch queue; budget default 75 (D9). |
| checkpoint | `bash $SCRIPTS/checkpoint.sh init|save|stage|find-incomplete ...` | Run-dir stage manifest under `$WS/cache/run/<id>/`; `find-incomplete` powers resume (D7). |
| scorecard | `bash $SCRIPTS/scorecard.sh <run-dir> $WS/tracker.json <today>` | The per-run accounting incl. `disclosures[]` (D12). |
| payload | `bash $SCRIPTS/payload.sh $WS/tracker.json <run-dir> <today> <n-sources>` | The ultramode render payload: ordering, near-miss rail, scorecard embed. |
| profile_hash | `bash $SCRIPTS/profile_hash.sh <user-profile.json>` | Canonical 16-hex hash of the scoring-relevant profile subset; every writer that edits titles/clusters/keywords/requirements/dimensions MUST recompute it (D11 cache invalidation). |
| identity | `python3 $SCRIPTS/lib/identity.py normalise <url>` / `key <url> <category>` | THE host-identity normalisation (`domain\|category`); catalogue/lifecycle scripts import it — never re-derive. |
| catalog | `python3 $SCRIPTS/catalog.py validate <catalogue>` / `select <catalogue> --scope <eu-nl\|eu-broad>` / `config-read $WS/user-profile.json` | Packaged-catalogue schema validation; deterministic scope selection (candidates annotated with `pack`); effective scope/refresh config with defaults, read-only (D7). |
| project | `python3 $SCRIPTS/project.py --candidate <file\|-> --priority N --verified-at <ISO>` | Catalogue candidate → registry entry: strips catalogue-only fields, requires a probe-time `verified_at`, maps `auth_required` → initial `auth_state`. The projection boundary (D11). |
| registry_lifecycle | `python3 $SCRIPTS/registry_lifecycle.py merge --registry $WS/sources.json --candidates <entries.json> [--catalogue <cat>] [--expect-sha256 <hex>]` / `retire --registry $WS/sources.json --name <name>` | Atomic lifecycle boundary: identity dedupe via aliases, tombstone skip, user-source retention, exact counts, single-linkedin, catalogue-leak rejection, conflict-aware write (exit 3). Retirement = tombstone, never mere absence. |

Single-entry tracker field updates (a score landing, a bend) use the atomic jq recipe in `../shared-references/state-validators.md`; multi-entry writes go through `merge_tracker.py` only.

Tests: `bash skills/_ultra-engine/tests/run.sh` → `ALL PASS`. Any contract change lands with a test change in the same commit.

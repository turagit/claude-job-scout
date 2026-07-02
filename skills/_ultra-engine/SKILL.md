---
name: _ultra-engine
description: Internal deterministic engine for the ultramode pipeline — scripts for snapshots, fingerprints, IDs, delta validation, tracker merges, rotation, JD budgeting, checkpoints, scorecard, and payload assembly. Loaded by orchestrator skills; never user-invoked.
allowed-tools: Read, Bash, Grep, Glob
disable-model-invocation: true
version: 0.1.0
---

Scripts live in `scripts/`; every contract is documented here (Phase 14 Task 12 fills this file). Tests: `bash tests/run.sh` → `ALL PASS`.

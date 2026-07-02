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

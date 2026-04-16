# Subagent Protocol

The single contract every skill in this plugin follows when dispatching subagents via the `Agent` tool. Parallel scoring, parallel pagination, company research, CV section rewrites, cover-letter drafting, and any future fan-out pattern all obey this protocol.

## Why this exists

Parallelism only pays off when the main thread does not re-absorb the subagent's full context. The delta-return and strict output schema in this protocol are what keep a 20-subagent fan-out from blowing the main conversation window.

## Dispatch

- Use the `Agent` tool. Every spawn names a `subagent_type`. Phase 1 uses `general-purpose` only; named repo-local subagents may be introduced in later phases.
- The prompt body is **self-contained** — the subagent has no access to the main conversation's context.
- If the `Agent` tool is not available in the current environment, every dispatching skill must fall back to sequential in-thread execution. Detect at dispatch time, not at skill-load time.

## Input shape

The prompt body carries a single JSON envelope:

```json
{
  "task": "<short string identifying the task type, e.g. 'score-job', 'rewrite-cv-role'>",
  "inputs": { /* task-specific fields */ },
  "budget_lines": 200,
  "allowed_tools": ["Read", "Grep", "Glob"]
}
```

The subagent must ignore anything not inside `inputs`. The main thread is responsible for passing all required data — the subagent cannot ask follow-up questions.

## Output shape

The subagent returns a single JSON object:

```json
{
  "status": "ok | partial | error",
  "deltas": [ /* array of change records, task-specific */ ],
  "errors": [ /* array of { code, message }; empty [] on success */ ],
  "continuation_cursor": null
}
```

- `deltas` contain **only changes** against the provided inputs. Re-emitting unchanged fields is forbidden.
- `status: "partial"` signals the subagent hit its budget; `continuation_cursor` is an opaque string the dispatcher may pass back in a follow-up call.
- `status: "error"` carries a populated `errors` array. The main thread decides retry / fallback / user-surface — the subagent never prompts the user.

No prose, no commentary, no repeating input data in the response. The main thread parses the JSON and merges.

## Budget

- `budget_lines` is a hard cap on the response body. Default 200.
- Subagents that cannot fit within budget return `status: "partial"` with a continuation cursor.
- Budgets are set by the dispatcher. Subagents do not negotiate.

**Continuing a partial result:** the dispatcher may re-dispatch with the same `task` and `inputs`, adding a top-level `continuation_cursor` field alongside `task`. Each continuation must itself respect the declared `budget_lines`. A cursor-bearing dispatch that returns `status: "ok"` indicates the work is complete; `status: "partial"` with a new cursor indicates more work remains.

## Allowed tools

- The dispatcher lists exactly the tools the subagent may use.
- Phase 1 default is read-only: `["Read", "Grep", "Glob"]`.
- Write access (`Write`, `Edit`) is granted only when the task is explicitly a content-production task and the dispatcher knows where the output goes.
- Browser tools are never granted to subagents in Phase 1 — all browser work stays on the main thread (see `browser-policy.md`).

## Idempotency

Re-dispatching the same `(task, inputs)` must produce the same deltas. Re-dispatching the same `(task, inputs, continuation_cursor)` must produce the same remaining deltas. State writes happen only in the main thread after fan-in, so repeated dispatches are safe.

## Fan-in merge

The dispatcher is responsible for:
1. Parsing each subagent's JSON response.
2. Validating `status`.
3. Merging `deltas` into canonical state (`scores.json`, `tracker.json`, etc.) with the existing merge rules.
4. Collecting any `errors` into a single summary for the user (or for retry logic).
5. Never letting partial/errored subagents block successful ones.

## Example: parallel job scoring

Main thread has 23 new jobs to score. It batches into 5 subagents of 5 jobs each (last subagent gets 3).

Dispatch payload (per subagent):
```json
{
  "task": "score-job-batch",
  "inputs": {
    "jobs": [ { "id": "...", "title": "...", "description": "...", ... } ],
    "user_profile": { /* cv_summary, requirements, master_keyword_list */ },
    "cv_hash": "...",
    "profile_hash": "..."
  },
  "budget_lines": 200,
  "allowed_tools": ["Read"]
}
```

Expected response:
```json
{
  "status": "ok",
  "deltas": [
    { "job_id": "123", "score": 87, "tier": "A", "breakdown": { /* per-dimension */ } },
    { "job_id": "124", "score": 61, "tier": "C", "breakdown": { /* ... */ } }
  ],
  "errors": []
}
```

Main thread merges all `deltas` into `.job-scout/cache/scores.json` and `.job-scout/tracker.json`.

Note: the dispatcher narrowed `allowed_tools` from the default `["Read", "Grep", "Glob"]` to just `["Read"]` — scoring needs only file reads, so the narrower grant keeps the subagent's tool surface minimal.

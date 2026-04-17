---
name: company-researcher
description: >
  Internal subagent skill. Dispatched by profile-optimizer, /match-jobs,
  /check-job-notifications, and (in later phases) cover-letter-writer
  when a job listing carries a company name worth enriching. Returns a
  short, structured digest — never prose. Not user-invocable.
version: 0.1.0
---

# Company Researcher (Subagent)

Produce a short structured digest about a company so the dispatching skill can make better recommendations without pulling company-research noise into the main conversation.

**This skill is dispatched only by other skills, via the `Agent` tool, per `../shared-references/subagent-protocol.md`.** It is not user-invocable.

## Input shape

```json
{
  "task": "research-company",
  "inputs": {
    "company_name": "Acme Corp",
    "job_id": "123456789",
    "source_blob": "<full job description text if available>",
    "cached_files": ["<optional paths to user-indexed docs mentioning this company>"],
    "signals_requested": ["size", "stage", "reputation", "red_flags"]
  },
  "budget_lines": 60,
  "allowed_tools": ["Read", "Grep", "Glob"]
}
```

## Output shape

```json
{
  "status": "ok",
  "deltas": [
    {
      "company_name": "Acme Corp",
      "size": "50-200 employees | unknown",
      "stage": "Series B | growth-stage | public | unknown",
      "reputation_digest": "<one short line — factual signals only, no speculation>",
      "red_flags": ["<flag 1>", "<flag 2>"]
    }
  ],
  "errors": []
}
```

**Output rules:**

- Each field is either a concrete value or `null`. Never speculate. If a signal can't be determined from the inputs, return `null`.
- `reputation_digest` is at most one sentence and cites the signal type ("from source_blob", "from user's cached recommendation file at path/to/file.pdf").
- `red_flags` is empty `[]` if none apply. Valid flags include: undisclosed company name, agency with no end client named, pattern-matching scam indicators from `../recruiter-engagement/references/response-templates.md`, pay-to-apply references.
- No prose outside the JSON envelope.

## Sources

Phase 1 sources only:
- The `source_blob` passed in the prompt (the JD text, if available).
- Files at paths named in `cached_files` (passed in by the dispatcher from `.job-scout/cache/supporting-docs.json`).

Phase 1 does **not** grant this subagent `WebFetch` or browser access. Any signal that can't be derived from the two sources above is `null`. Future phases may extend sources under explicit user consent.

## Budget

`budget_lines: 60`. If the subagent can't fit within 60 lines, return `status: "partial"` with the highest-signal fields populated and the rest `null`.

## Not user-invocable

This skill has no `allowed-tools` frontmatter for the slash-command surface and should never be wired into a slash command. The dispatching skill always loads it via `Agent` with a self-contained prompt.

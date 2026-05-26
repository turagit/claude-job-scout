---
name: _gate-engine
description: >
  [Internal — loaded by _job-matcher and the orchestrators of /match-jobs and /check-job-notifications] Evaluates a job listing against the user's declared deal_breakers in user-profile.json. Returns a list of gate_violations and an overall gated flag. Any non-empty violation list forces the job to tier D with no further scoring. This is the primary false-positive defence in v0.8.0.
version: 0.1.0
---

# Gate Engine

Hard-gate jobs against declared dealbreakers before any scoring happens.

## Why this skill exists

Pre-v0.8.0, the matcher computed a weighted score over Skills, Experience, Requirements, Growth, and Practical. The Requirements dimension was 25% — meaning a job that violated work_arrangement, contract type, or seniority floor could still score 75 from the other four dimensions and land in B-tier. The fix is structural: dealbreaker violations are not partial-credit factors; they are gates.

## Inputs

- The user-profile.json `requirements` block (esp. `deal_breakers[]`, `work_arrangement`, `contract_type`, `companies_to_avoid`, `industries_to_avoid`, `seniority_floor`, `min_day_rate`, `salary_floor`, `rate_currency`, `salary_currency`, `location_preferences`).
- The extracted job listing: title, company, location, work_arrangement, contract_type, seniority, industry, day_rate (if disclosed), salary (if disclosed), JD text.

## Output

```json
{
  "gated": true | false,
  "gate_violations": [
    {"kind": "work_arrangement|contract_type|seniority_floor|location|industry|company|rate_floor|salary_floor|custom",
     "detail": "<one-line human readable reason>"}
  ]
}
```

## Evaluation order

See `references/gate-rules.md` for the full rules table. Evaluate in this order (cheap → expensive):

1. **company** — fail-fast if `job.company` is in `requirements.companies_to_avoid` (case-insensitive substring match).
2. **work_arrangement** — fail if `job.work_arrangement` is not in `requirements.work_arrangement`.
3. **contract_type** — fail if `job.contract_type` not in `requirements.contract_type`.
4. **location** — fail if `job.location` is not covered by `requirements.location_preferences` (preference may be country, region, or "worldwide remote").
5. **seniority_floor** — fail if `job.seniority` < `requirements.seniority_floor`. Seniority ordering: Junior < Mid < Senior < Lead < Manager < Senior Manager < Director < Senior Director < VP < SVP < C-level. For director-perm segment, default floor is `Director`. For freelance, the floor is whatever the user declared (often "Senior" or "Lead").
6. **industry** — fail if `job.industry` (parsed from JD) is in `requirements.industries_to_avoid`.
7. **rate_floor / salary_floor** — fail if `job.day_rate < requirements.min_day_rate` (with currency check) OR `job.salary < requirements.salary_floor`. If the listing doesn't disclose, do NOT gate (flag for follow-up in the report card instead).
8. **custom deal_breakers** — for each `deal_breaker` of kind `custom`, evaluate the `free_text` rule via an LLM call against the JD text. Costly; runs last.

If any check fails, append the violation and continue evaluating remaining checks — the user benefits from seeing the full list of reasons, not just the first one.

## Behaviour

- If `gate_violations` is non-empty, the consumer (`_job-matcher`) sets `tier: D`, `tier_reason: "gated: <kinds>"`, `gate_violations: [...]`, and skips dimension scoring.
- If `gate_violations` is empty, the consumer proceeds with dimension scoring.

## Caching

Gate results are part of the score cache (see `_job-matcher` SKILL.md § Score Caching Contract). Same key (`job_id × cv_hash × profile_hash × rubric_version`). Profile changes invalidate via `profile_hash` bump (`/analyze-cv` recomputes the hash when `requirements` changes).

## Reference Materials

- `references/gate-rules.md` — full rules table, seniority ordering, location-match logic, currency handling.

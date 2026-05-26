# Gate Rules

The operational table the `_gate-engine` skill consults at evaluation time.

## Seniority ordering

```
junior < mid < senior < lead < manager < senior manager < director < senior director < vp < svp < c-level
```

Comparison is case-insensitive substring against the parsed `seniority` field on the job listing. A JD that reads "Director / Head of Platform" satisfies a `director` floor.

If the JD's seniority is ambiguous (no clear level keyword), do NOT gate — flag the listing for manual review in the report card via `tier_reason: "seniority unclear"`.

## Location match

The `requirements.location_preferences` array may contain country codes, region names (`EU`, `UK`, `EEA`, `worldwide remote`), or city names. Match logic:

1. If `job.work_arrangement` is `remote` AND any of the preferences is `worldwide remote` or `remote` → pass.
2. If preference is a country/region and `job.location` mentions that country/region (case-insensitive) → pass.
3. If preference is a city and `job.location` mentions that city → pass.
4. Otherwise → fail.

## Currency for rate/salary gates

If currencies differ between `requirements.rate_currency` (e.g. GBP) and `job.day_rate_currency` (e.g. EUR), the gate engine SHOULD convert using a daily-cached FX rate. **Phase 5 simplification:** if currencies differ, do NOT gate; flag the listing for manual review and surface in the report card. (Phase 6 candidate to add FX.)

## Custom deal-breakers (LLM prompt)

```
You are checking whether a job listing violates a user-declared dealbreaker.

Dealbreaker rule (free text): {{deal_breaker.free_text}}

Job listing:
- Title: {{job.title}}
- Company: {{job.company}}
- Location: {{job.location}}
- JD text: {{job.jd_text[:2000]}}

Reply with strict JSON: {"violates": true|false, "detail": "<one-line reason>"}.
```

Phase 5 limits the count of `custom` dealbreakers per evaluation to 3 (cap declared in `/analyze-cv` elicitation — the open free-text prompt collects at most 3 entries). Each `custom` rule is one extra LLM call per scored job; the cap keeps batch scoring tractable.

## Dealbreaker source provenance

Every `deal_breakers[]` entry carries `source: "elicited"` (declared by the user at `/analyze-cv` discovery) or `source: "learned"` (promoted from a reject-reason pattern in a future phase). The gate engine treats both identically at evaluation time — provenance affects only the UX that introduced the rule.

## Forward references

- Phase 6 will add Top-Picks, Similar-jobs, and recruiter-link surfaces — the gate engine is unchanged; it runs on every newly extracted job regardless of source.
- Phase 7 will add the reject-with-reason chip UX in the visual report. The chip's "wrong location / wrong seniority / wrong contract / wrong company / wrong industry / overqualified" reasons map 1:1 to gate `kind` values, which is intentional: a reject-pattern of "wrong company × 3 against Acme Corp" naturally promotes to a `kind: company` dealbreaker entry.

# Canonical Schemas (locked v2)

> **Authoritative reference for `.job-scout/` state writes.** Any skill that writes to `user-profile.json`, `tracker.json`, or `recruiters/threads.json` MUST conform to these schemas. Validation rules live in `state-validators.md`.

This reference replaces the older inline schemas in `tracker-schema.md` and `_job-matcher/references/user-profile-schema.md`. Those files now point here.

## `user-profile.json`

```json
{
  "schema_version": 2,
  "cv_path": "string",
  "cv_hash": "string|null",
  "cv_filename_on_linkedin": "string|null",
  "cv_uploaded_to_linkedin_at": "ISO8601|null",
  "cv_summary": {
    "key_skills": ["string"],
    "technologies": ["string"],
    "seniority": "string",
    "years_experience": "number",
    "target_roles": ["string"],
    "domain_expertise": ["string"],
    "industries": ["string"]
  },
  "target_titles": ["string"],
  "preferred_length_pages": "number|null",
  "linkedin_profile_url": "string|null",
  "profile_hash": "string|null",
  "discovery_complete": "boolean",
  "segment": "string — free-text descriptor of the workspace's job-search lane (e.g. 'head pastry chef in Lisbon', 'construction site engineer — UK civils', 'mid-career switch to UX research', 'freelance backend contracts EU-remote', 'permanent leadership roles in enterprise IT')",
  "dimensions": [
    {
      "name": "string — dimension label",
      "criteria": {
        "A": "string — A-tier criterion",
        "B": "string — B-tier criterion",
        "C": "string — C-tier criterion",
        "D": "string — D-tier criterion"
      },
      "weight": "number — optional, defaults to 1.0; load-bearing dimensions can be tagged for the overall-tier derivation rule"
    }
  ],
  "requirements": {
    "work_arrangement": ["remote", "hybrid", "on-site"],
    "contract_type": ["permanent", "freelance"],
    "location_preferences": ["string"],
    "seniority_floor": "string|null",
    "min_day_rate": "number|null",
    "ideal_day_rate": "number|null",
    "rate_currency": "string|null",
    "salary_floor": "number|null",
    "salary_currency": "string|null",
    "deal_breakers": [
      {
        "kind": "work_arrangement | contract_type | seniority_floor | location | industry | company | rate_floor | salary_floor | custom",
        "values": ["string"],
        "free_text": "string|null",
        "source": "elicited | learned",
        "added_at": "ISO8601"
      }
    ],
    "nice_to_haves": ["string"],
    "companies_to_avoid": ["string"],
    "industries_to_avoid": ["string"],
    "companies_to_target": ["string"]
  },
  "tone": {
    "register": "string",
    "dialect": "british",
    "warmth": "string",
    "vocabulary_cues": ["string"],
    "exemplars": ["string"],
    "avoid": ["string"]
  },
  "master_keyword_list": ["string"],
  "last_updated": "ISO8601",
  "created_by": "string"
}
```

## `tracker.json`

```json
{
  "schema_version": 2,
  "version": 2,
  "stats": {
    "total_seen": "number",
    "applied": "number",
    "rejected": "number",
    "last_run": "ISO8601|null",
    "last_search": "ISO8601|null",
    "last_archive_pass": "YYYY-MM-DD|null"
  },
  "jobs": {
    "<job_id>": {
      "id": "string",
      "url": "string",
      "title": "string",
      "company": "string",
      "source": "Job Alert | Top Picks | Search | Inbox | Saved | Similar",
      "score": "number|null",
      "tier": "A | B | C | D | untiered",
      "tier_reason": "string|null",
      "dimensions": {
        "<dimension_name>": {
          "tier": "A | B | C | D",
          "evidence": ["string"]
        }
      },
      "gate_violations": [
        {"kind": "string", "detail": "string"}
      ],
      "rubric_version": "legacy | v1",
      "status": "seen | approved | applied | rejected | skipped",
      "filtered_reason": "string|null",
      "reject_reason": "string|null",
      "rejected_at": "ISO8601|null",
      "approved_at": "ISO8601|null",
      "applied_at": "ISO8601|null",
      "first_seen": "YYYY-MM-DD",
      "last_seen": "YYYY-MM-DD",
      "jd_path": "string|null",
      "notes": "string"
    }
  }
}
```

`jd_path` is a workspace-relative path to the full JD text under `.job-scout/jds/<job_id>.txt`. The inline `description` field used in v1 is removed — full JD text is hybrid-stored. See `jd-storage.md` (created in Task 5) for the contract.

## `recruiters/threads.json`

```json
{
  "schema_version": 2,
  "last_scanned": "ISO8601|null",
  "scan_source": "string",
  "stats": {
    "total_threads_scanned": "number",
    "hot": "number",
    "warm": "number",
    "cold": "number",
    "non_lead": "number"
  },
  "threads": {
    "<thread_id>": {
      "recruiter_name": "string",
      "participant_title": "string|null",
      "company": "string|null",
      "lead_tier": "hot | warm | cold | non-lead",
      "lead_tier_detail": "string|null",
      "last_seen_msg_id": "string|null",
      "last_drafted_reply": "string|null",
      "last_updated": "ISO8601|null",
      "last_message_date": "YYYY-MM-DD|null",
      "thread_url_path": "string|null",
      "linked_job_ids": ["string"],
      "notes": [
        {"date": "YYYY-MM-DD", "note": "string"}
      ]
    }
  }
}
```

## Canonical enums (single source of truth)

| Field | Allowed values |
|---|---|
| `tracker.jobs.*.status` | `seen`, `approved`, `applied`, `rejected`, `skipped` |
| `tracker.jobs.*.tier` | `A`, `B`, `C`, `D`, `untiered` |
| `tracker.jobs.*.rubric_version` | `legacy`, `v1` |
| `tracker.jobs.*.source` | `Job Alert`, `Top Picks`, `Search`, `Inbox`, `Saved`, `Similar` |
| `threads.*.lead_tier` | `hot`, `warm`, `cold`, `non-lead` |
| `user-profile.requirements.deal_breakers[].kind` | `work_arrangement`, `contract_type`, `seniority_floor`, `location`, `industry`, `company`, `rate_floor`, `salary_floor`, `custom` |
| `user-profile.segment` | free-text string (any descriptor the user chooses at `/analyze-cv` discovery) |

## Status transition rules

- `seen → approved → applied` (forward only)
- `seen → rejected` (forward only)
- `seen → skipped` (forward only — for explicit user "not now")
- Never downgrade. Never set a status field to a value outside the enum above.

## When to bump `schema_version`

Bump from 2 to 3 when a field is renamed, removed, or its type changes. Adding optional fields without a rename is a non-bumping change. A migration script must exist for every bump and live in the plan that introduced the change.

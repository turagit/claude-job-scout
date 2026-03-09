# User Profile Schema

All commands in this plugin read from and write to a shared `user-profile.json` file in the workspace root. This avoids re-asking the user for the same information across sessions.

## File Location

`./user-profile.json` (workspace root)

## Schema

```json
{
  "cv_path": "path/to/cv.pdf",
  "cv_summary": {
    "key_skills": ["skill1", "skill2"],
    "technologies": ["tech1", "tech2"],
    "seniority": "Senior",
    "years_experience": 10,
    "target_roles": ["Role A", "Role B"],
    "domain_expertise": ["Domain 1", "Domain 2"],
    "industries": ["Industry 1"]
  },
  "requirements": {
    "work_arrangement": "remote",
    "contract_type": "freelance",
    "target_roles": ["Role A", "Role B"],
    "min_day_rate": null,
    "ideal_day_rate": null,
    "rate_currency": "GBP",
    "location_preferences": ["UK", "EU"],
    "seniority": "Senior",
    "deal_breakers": [],
    "nice_to_haves": [],
    "companies_to_avoid": [],
    "companies_to_target": []
  },
  "linkedin_profile_url": null,
  "last_updated": "2026-03-09T15:00:00Z",
  "created_by": "check-new-jobs"
}
```

## Field Descriptions

### `cv_path`

Path to the user's CV file relative to workspace root. Set by `/analyze-cv` or `/check-new-jobs`.

### `cv_summary`

Extracted profile from CV analysis. Built dynamically from CV content — never hardcoded. Updated whenever the CV is re-analyzed.

### `requirements`

User's job search preferences. Defaults to `remote` + `freelance` if not specified. Commands should read these first and only ask the user for fields that are missing or `null`.

### `last_updated`

ISO 8601 timestamp. Commands should check this — if older than 30 days, suggest the user re-run `/analyze-cv` to refresh.

## Command Responsibilities

| Command | Reads | Writes |
|---------|-------|--------|
| `/analyze-cv` | — | `cv_path`, `cv_summary` |
| `/check-new-jobs` | All fields | `cv_path`, `cv_summary` (if not set) |
| `/job-search` | `requirements`, `cv_summary` | `requirements` (fills in missing fields from conversation) |
| `/match-jobs` | `requirements`, `cv_summary` | — |
| `/create-alerts` | `requirements` | — |
| `/apply` | `cv_path`, `requirements` | — |
| `/check-inbox` | `cv_summary`, `requirements` | — |
| `/optimize-profile` | `cv_path`, `cv_summary` | `linkedin_profile_url` |

## Behavior Rules

1. **Read first, ask second** — Always check `user-profile.json` before asking the user for any information it might contain
2. **Merge, don't overwrite** — When updating, merge new fields with existing data rather than replacing the entire file
3. **Create if missing** — If the file doesn't exist, create it with whatever fields are available
4. **Inform the user** — When reading from the profile, briefly confirm: "Using your saved preferences (remote, freelance). Want to change anything?"

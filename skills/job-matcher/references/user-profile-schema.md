# User Profile Schema

All commands share `./user-profile.json` in workspace root to avoid re-asking for information.

```json
{
  "cv_path": "path/to/cv.pdf",
  "cv_summary": {
    "key_skills": [], "technologies": [], "seniority": "Senior",
    "years_experience": 10, "target_roles": [], "domain_expertise": [], "industries": []
  },
  "requirements": {
    "work_arrangement": "remote", "contract_type": "freelance",
    "target_roles": [], "min_day_rate": null, "ideal_day_rate": null,
    "rate_currency": "GBP", "location_preferences": [],
    "seniority": "Senior", "deal_breakers": [], "nice_to_haves": [],
    "companies_to_avoid": [], "companies_to_target": []
  },
  "linkedin_profile_url": null,
  "last_updated": "ISO8601",
  "created_by": "command-name"
}
```

## Rules

1. **Read first, ask second** — check profile before asking for info it might contain
2. **Merge, don't overwrite** — update fields without replacing the file
3. **Create if missing** — with whatever fields are available
4. **Confirm with user** — "Using saved preferences (remote, freelance). Want to change?"
5. **Stale check** — if `last_updated` >30 days, suggest re-running `/analyze-cv`

## Command Access

| Command | Reads | Writes |
|---------|-------|--------|
| `/analyze-cv` | — | cv_path, cv_summary |
| `/check-job-notifications` | All | cv_path, cv_summary (if missing) |
| `/job-search` | requirements, cv_summary | requirements (fills gaps) |
| `/match-jobs` | requirements, cv_summary | — |
| `/apply` | cv_path, requirements | — |
| `/check-inbox` | cv_summary, requirements | — |
| `/optimize-profile` | cv_path, cv_summary | linkedin_profile_url |
| `/create-alerts` | requirements | — |

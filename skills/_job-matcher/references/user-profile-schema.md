# User Profile (per-workspace)

> **Schema definition:** see [`../../shared-references/canonical-schemas.md`](../../shared-references/canonical-schemas.md). The JSON shape lives there and is locked.

This file documents read/write access and operational rules. Every workspace has its own `user-profile.json` at the root of `.job-scout/`.

## Rules

1. **Read first, ask second.** Check the profile before asking for info it might contain.
2. **Merge, don't overwrite.** Update fields without replacing the file. Writes go through `validate_profile` (see `state-validators.md`).
3. **Create if missing.** On first bootstrap, write a canonical v2 stub via `/analyze-cv`.
4. **Confirm with user.** "Using saved preferences (remote, freelance, Director). Want to change?"
5. **Stale check.** If `last_updated` >30 days, suggest re-running `/analyze-cv`.
6. **Segment is required.** The matcher uses it to load the right dimension set. `/analyze-cv` declares it at init time and writes it.

## Command access

| Command | Reads | Writes |
|---|---|---|
| `/analyze-cv` | All | cv_path, cv_summary, cv_hash, target_titles, segment, tone, requirements.deal_breakers, discovery_complete |
| `/check-job-notifications` | All | last_updated (if missing fields filled) |
| `/job-search` | requirements, target_titles, segment | requirements (fills gaps) |
| `/match-jobs` | All | — |
| `/apply` | cv_path, requirements | — |
| `/check-inbox` | tone, cv_summary, requirements | — |
| `/optimize-profile` | cv_path, cv_summary, tone | linkedin_profile_url, profile_hash |
| `/create-alerts` | requirements, target_titles | — |
| `/cover-letter` | All (esp. tone, cv_summary) | — |
| `/interview-prep` | All | — |

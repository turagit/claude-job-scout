# CV Loading & Profile Check — Shared Procedure

All commands that need the user's CV or profile should follow this procedure rather than implementing their own.

## Step 0: Ensure workspace folder exists

Before anything else, follow `workspace-layout.md` to ensure `.job-scout/` exists in the current workspace. All paths below are relative to that folder.

## Step 1: Check `.job-scout/user-profile.json`

- **If found and `last_updated` < 30 days:** Load it. Briefly confirm with user: "Using your saved profile (Senior, remote, freelance). Still accurate?"
- **If found but `last_updated` ≥ 30 days:** Load it but warn: "Your profile is over 30 days old — consider re-running `/analyze-cv` to refresh."
- **If not found:** Proceed to Step 2, then create it.

## Step 2: Locate CV File

Search workspace for CV files using these patterns (in order):
1. `cv_path` from `user-profile.json` (if profile exists)
2. Files matching: `cv.*`, `resume.*`, `curriculum.*` with extensions `.pdf`, `.docx`, `.doc`, `.txt`, `.md`
3. Any PDF/DOCX in the workspace root that looks like a CV

- **If one found:** Use it. Compute its content hash and store as `cv_hash` in `user-profile.json`.
- **If multiple found:** Ask user which to use.
- **If none found:** Ask user to provide their CV. Stop if the calling command requires a CV.

## Step 3: Reuse cached parse

If `.job-scout/cache/cv-<hash>.json` exists for the current CV's hash, load it directly — do **not** re-parse the CV file. The cache contains parsed text, extracted skills, and the master keyword list.

If no cache exists, parse the CV once, write the cache, then proceed.

## Step 4: Master Keyword List

Reuse `master_keyword_list` from `user-profile.json` (populated by `_cv-optimizer`). Do not re-extract keywords unless the CV's hash has changed.

## Rules

- **Read first, ask second** — always check what's already saved before prompting.
- **Merge, don't overwrite** — update fields in `user-profile.json` without replacing unrelated data.
- **Hash before parsing** — never re-parse an unchanged CV.
- **Create if missing** — with whatever fields are available.

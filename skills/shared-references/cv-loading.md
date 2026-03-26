# CV Loading & Profile Check — Shared Procedure

All commands that need the user's CV or profile should follow this procedure rather than implementing their own.

## Step 1: Check user-profile.json

Look for `user-profile.json` in the workspace root.

- **If found and `last_updated` < 30 days:** Load it. Briefly confirm with user: "Using your saved profile (Senior, remote, freelance). Still accurate?"
- **If found but `last_updated` ≥ 30 days:** Load it but warn: "Your profile is over 30 days old — consider re-running `/analyze-cv` to refresh."
- **If not found:** Proceed to Step 2, then create it.

## Step 2: Locate CV File

Search workspace for CV files using these patterns (in order):
1. `cv_path` from `user-profile.json` (if profile exists)
2. Files matching: `cv.*`, `resume.*`, `curriculum.*` with extensions `.pdf`, `.docx`, `.doc`, `.txt`, `.md`
3. Any PDF/DOCX in the workspace root that looks like a CV

- **If one found:** Use it.
- **If multiple found:** Ask user which to use.
- **If none found:** Ask user to provide their CV. Stop if the calling command requires a CV.

## Step 3: Load Master Keyword List

If `cv-optimizer` has previously run and saved a `master_keyword_list` in `user-profile.json`, reuse it. Do not re-extract keywords unless the CV has changed.

## Rules

- **Read first, ask second** — always check what's already saved before prompting
- **Merge, don't overwrite** — update fields in `user-profile.json` without replacing unrelated data
- **Create if missing** — with whatever fields are available

# Workspace Layout — `.job-scout/`

Every command in this plugin reads and writes state inside a single per-project folder named `.job-scout/`, located at the root of whatever workspace the user invoked the plugin from. This keeps state scoped to the project (so a freelance-search workspace and a permanent-role workspace don't pollute each other) and gives every skill one canonical place to look.

## Canonical layout

```
.job-scout/
  user-profile.json     # CV-derived facts, requirements, master keyword list, cv_path, cv_hash, discovery_complete
  tracker.json          # every job ever seen — see tracker-schema.md
  reports/              # YYYY-MM-DD-*.md run reports (notifications sweeps, match runs, CV analyses)
  cache/
    cv-<hash>.json          # parsed CV text + extracted keywords, keyed by file content hash
    cv-analysis-<hash>.json # full cv-optimizer scoring output, keyed by content hash
    scores.json             # job scores keyed by (job_id, cv_hash, profile_hash)
    linkedin-profile.json   # last-seen snapshot of the user's LinkedIn profile
  recruiters/
    threads.json        # per-thread state: last_seen_msg_id, lead_tier, last_drafted_reply
```

The folder is intentionally hidden (`.` prefix) so it doesn't clutter the user's project view, and the name is fixed so commands can find it without configuration.

## Bootstrap procedure (run on first invocation of any command)

Before doing any real work, every command must ensure `.job-scout/` exists in the current workspace. The procedure:

1. **Check** for `.job-scout/` at the workspace root (the directory the plugin was invoked from — not the plugin install path).
2. **If it exists:** proceed. Do not re-prompt.
3. **If it does not exist:** ask the user *once*, in plain language:

   > "I don't see a `.job-scout/` folder in this project yet. This is where I'll keep your CV profile, the list of jobs I've already shown you, cached scores, and run reports — all scoped to *this* project so different job searches stay separate. Want me to create it now?"

4. **On approval:** create the folder and the `reports/`, `cache/`, and `recruiters/` subfolders. Write a stub `user-profile.json` with `{ "created": "<ISO date>", "discovery_complete": false }` and an empty `tracker.json` with `{ "version": 1, "jobs": {}, "stats": { "total_seen": 0, "applied": 0, "rejected": 0 } }`.
5. **On decline:** tell the user the command needs a state folder to work properly and offer to fall back to the workspace root for this run only (legacy mode). Do not nag again in the same session.

## Why per-project (not per-user)

A user running the plugin from `~/projects/freelance-search/` and from `~/projects/perm-roles/` is doing two different searches with different CVs, requirements, and tracked jobs. A global folder would mix them. The `.job-scout/` folder lives next to the project so each workspace gets its own clean state.

If the user *wants* a global default, they can symlink `.job-scout/` to a shared location — that's their call, not ours.

## Migration from legacy paths

Earlier versions wrote `user-profile.json` and `job-reports/` directly to the workspace root. On bootstrap, if those legacy files are found:

1. Offer to move them into `.job-scout/` (preserving content).
2. If the user declines, keep reading from the legacy paths but write all new state into `.job-scout/`.

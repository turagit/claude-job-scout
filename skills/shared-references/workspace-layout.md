# Workspace Layout — `.job-scout/`

Every command in this plugin reads and writes state inside a single per-project folder named `.job-scout/`, located at the root of whatever workspace the user invoked the plugin from. This keeps state scoped to the project (so a freelance-search workspace and a permanent-role workspace don't pollute each other) and gives every skill one canonical place to look.

## Canonical layout

```
.job-scout/
  schema-version        # JSON: { "version": 1, "upgraded_at": "<ISO>" } — bumped by migration runner
  user-profile.json     # CV-derived facts, requirements, master keyword list, cv_path, cv_hash, discovery_complete
  tracker.json          # every job ever seen — see tracker-schema.md
  reports/              # YYYY-MM-DD-*.md run reports (notifications sweeps, match runs, CV analyses)
  archive/              # tracker-YYYY.json — aged seen-status jobs rotated out of tracker.json
  cache/
    cv-<hash>.json          # parsed CV text + extracted keywords, keyed by file content hash
    cv-analysis-<hash>.json # full cv-optimizer scoring output, keyed by content hash
    scores.json             # job scores keyed by (job_id, cv_hash, profile_hash)
    linkedin-profile.json   # last-seen snapshot of the user's LinkedIn profile
    supporting-docs.json    # index of non-CV workspace docs (see supporting-docs.md)
    jd-keyword-corpus.json  # learned keyword model from ingested JDs (see jd-keyword-extraction.md)
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

4. **On approval:** create the folder and the `reports/`, `cache/`, `recruiters/`, and `archive/` subfolders. Write:
   - `schema-version` with `{ "version": 1, "upgraded_at": "<ISO>" }`.
   - A stub `user-profile.json` with `{ "created": "<ISO date>", "discovery_complete": false }`.
   - An empty `tracker.json` with `{ "version": 1, "jobs": {}, "stats": { "total_seen": 0, "applied": 0, "rejected": 0 }, "last_archive_pass": null }`.
   - An empty `cache/supporting-docs.json` with `{ "version": 1, "last_scanned": null, "docs": {} }`.

   Then run the supporting-docs scan described in `supporting-docs.md` — the user is prompted once per workspace; the scan itself runs silently on subsequent commands. Does not block the command that triggered the bootstrap.
5. **On decline:** tell the user the command needs a state folder to work properly and offer to fall back to the workspace root for this run only (legacy mode). Do not nag again in the same session.

## Why per-project (not per-user)

A user running the plugin from `~/projects/freelance-search/` and from `~/projects/perm-roles/` is doing two different searches with different CVs, requirements, and tracked jobs. A global folder would mix them. The `.job-scout/` folder lives next to the project so each workspace gets its own clean state.

If the user *wants* a global default, they can symlink `.job-scout/` to a shared location — that's their call, not ours.

## Migration from legacy paths

Earlier versions wrote `user-profile.json` and `job-reports/` directly to the workspace root. On bootstrap, if those legacy files are found:

1. Offer to move them into `.job-scout/` (preserving content).
2. If the user declines, keep reading from the legacy paths but write all new state into `.job-scout/`.

## Schema version and migration

`.job-scout/schema-version` records the current schema version of the workspace. Every command, on entry, reads this file and runs the migration runner before doing real work.

On a freshly bootstrapped workspace (folder just created by step 4 above), no migration pass is needed — bootstrap writes `schema-version` directly at `version: 1`.

### Migration runner shape

```
current = read(.job-scout/schema-version).version
target  = SCHEMA_VERSION  # canonical value documented in this file; currently 1
if current < target:
  for v in range(current, target):
    apply_migration(v -> v+1)
  write(.job-scout/schema-version, { version: target, upgraded_at: <ISO> })
```

### First-run behaviour on an already-existing `.job-scout/`

If `.job-scout/` exists but `schema-version` is missing, treat the workspace as pre-schema-versioning: write `schema-version` with `{ "version": 1, "upgraded_at": "<ISO>" }` and continue. Do not re-run any migrations.

On the specific v0.3.0 → v0.4.0 upgrade, two additional one-time actions are performed alongside the `schema-version` write (mechanics live in the owning references, not here):
- **Clear `.job-scout/cache/scores.json`** — the cache key shape expanded to include `profile_hash`, so pre-upgrade entries cannot match post-upgrade lookups. See `job-matcher/SKILL.md`.
- **Run one tracker archive pass** — aged `status: seen` entries rotate to `.job-scout/archive/tracker-YYYY.json`. See `tracker-schema.md`.

Inform the user about the upgrade actions in a single message, not interactively.

### Adding a new migration

1. Bump the canonical `SCHEMA_VERSION` constant (documented here, not in code — the plugin is a set of markdown skills).
2. Add a subsection below this one describing `v<N> → v<N+1>`: what fields change, how to transform data in place, any files that are renamed or moved.
3. Update every skill that reads the affected files to use the new shape.

No migrations exist in Phase 1. The scaffolding is in place for Phase 2+.

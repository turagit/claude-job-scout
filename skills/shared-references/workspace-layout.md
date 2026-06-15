# Workspace Layout — `.job-scout/`

Every command in this plugin reads and writes state inside a single per-project folder named `.job-scout/`, located at the root of whatever workspace the user invoked the plugin from. This keeps state scoped to the project (so a freelance-search workspace and a permanent-role workspace don't pollute each other) and gives every skill one canonical place to look.

## Canonical layout

```
.job-scout/
  schema-version        # JSON: { "version": 3, "upgraded_at": "<ISO>" } — workspace-level version, bumped by migration runner
  user-profile.json     # canonical v2 — see canonical-schemas.md (segment, requirements, tone, deal_breakers, ultramode)
  tracker.json          # canonical v2/v3 — see canonical-schemas.md (status/tier enums, dimensions, rubric_version, structured source)
  sources.json          # ultramode source registry (Phase 11) — see canonical-schemas.md; absent until ultramode discovery runs
  jds/                  # per-job JD blobs — see jd-storage.md
    <job_id>.txt
  reports/              # YYYY-MM-DD-*.md and HTML run reports (notifications sweeps, match runs, CV analyses)
  archive/              # tracker-YYYY.json — aged seen-status jobs rotated out of tracker.json
  cache/
    cv-<hash>.json          # parsed CV text + extracted keywords, keyed by file content hash
    cv-analysis-<hash>.json # full _cv-optimizer scoring output, keyed by content hash
    scores.json             # job scores keyed by (job_id, cv_hash, profile_hash, rubric_version)
    linkedin-profile.json   # last-seen snapshot of the user's LinkedIn profile
    supporting-docs.json    # index of non-CV workspace docs (see supporting-docs.md)
    jd-keyword-corpus.json  # learned keyword model from ingested JDs (see jd-keyword-extraction.md)
    query-stats.json        # per-query yield memory for the search plan (see linkedin-search.md §4)
  recruiters/
    threads.json        # canonical v2 — see canonical-schemas.md (lead_tier enum, notes[], last_seen_msg_id)
  cover-letters/        # per-job generated cover letters
  .backup/              # atomic-write backups, retained ≥30 days
    <filename>.<ISO8601>.json
```

> **Two version axes.** The `.job-scout/schema-version` file tracks the *workspace* version. Each state file (`user-profile.json`, `tracker.json`, `threads.json`) carries its own per-file `schema_version`. These are orthogonal: the workspace bumps when the *layout* changes (new directories, new files); per-file versions bump when the *file shape* changes. Phase 5 bumps both: workspace v2 → v3 (adds `jds/` and `.backup/`); per-file shapes → 2 (canonical contracts in `canonical-schemas.md`). Phase 11 bumps the workspace v3 → v4 (ultramode foundations; adds the optional `sources.json` registry and `user-profile` `ultramode` block) and lazily bumps the tracker file shape 2 → 3 (structured `source`).

The folder is intentionally hidden (`.` prefix) so it doesn't clutter the user's project view, and the name is fixed so commands can find it without configuration.

## Bootstrap procedure (run on first invocation of any command)

Before doing any real work, every command must ensure `.job-scout/` exists in the current workspace. The procedure:

1. **Check** for `.job-scout/` at the workspace root (the directory the plugin was invoked from — not the plugin install path).
2. **If it exists:** proceed. Do not re-prompt.
3. **If it does not exist:** ask the user *once*, in plain language:

   > "I don't see a `.job-scout/` folder in this project yet. This is where I'll keep your CV profile, the list of jobs I've already shown you, cached scores, and run reports — all scoped to *this* project so different job searches stay separate. Want me to create it now?"

   Based on the user's answer, take exactly one of the two branches below:

4. **[Branch A — user said Yes]** Create the folder and the `reports/`, `cache/`, `recruiters/`, and `archive/` subfolders. Write:
   - `schema-version` with `{ "version": 1, "upgraded_at": "<ISO>" }`.
   - A stub `user-profile.json` with `{ "created": "<ISO date>", "discovery_complete": false }`.
   - An empty `tracker.json` with `{ "version": 1, "jobs": {}, "stats": { "total_seen": 0, "applied": 0, "rejected": 0 }, "last_archive_pass": null }`.
   - An empty `cache/supporting-docs.json` with `{ "version": 1, "last_scanned": null, "docs": {} }`.

   Then run the supporting-docs scan described in `supporting-docs.md` — the user is prompted once per workspace; the scan itself runs silently on subsequent commands. Does not block the command that triggered the bootstrap.

   Then run the supporting-docs nudge: quick `Glob` for likely supporting-doc files at the workspace root (`*.pdf`, `*.docx`, `*.pptx`, `*.md`, `*.txt`). Filter out the CV (matches `cv.*`, `resume.*`, `curriculum.*`) and anything inside `.job-scout/`, `.git/`, or dotted directories. If 1+ files found, prompt the user:

   > "📎 I noticed [N] files in your workspace that look like supporting materials (certs, talks, decks, recommendations). Indexing them now will make every future CV rewrite, profile proposal, and cover letter sharper. Run `/index-docs` now? (Y/n)"

   On Y: dispatch `/index-docs` immediately. On n: remember per session (the supporting-docs reference's opt-out behaviour applies). If zero files found, proceed silently — the user can run `/index-docs` later when they add docs.

5. **[Branch B — user said No]** Tell the user the command needs a state folder to work properly and offer to fall back to the workspace root for this run only (legacy mode). Do not nag again in the same session.

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
target  = SCHEMA_VERSION  # canonical value documented in this file; currently 4 (1→2 in v0.7.0, 2→3 in v0.8.0, 3→4 in the Phase 11 ultramode release)
if current < target:
  for v in range(current, target):
    apply_migration(v -> v+1)
  write(.job-scout/schema-version, { version: target, upgraded_at: <ISO> })
```

### First-run behaviour on an already-existing `.job-scout/`

If `.job-scout/` exists but `schema-version` is missing, treat the workspace as pre-schema-versioning: write `schema-version` with `{ "version": 1, "upgraded_at": "<ISO>" }` and continue. Do not re-run any migrations.

On the specific v0.3.0 → v0.4.0 upgrade, two additional one-time actions are performed alongside the `schema-version` write (mechanics live in the owning references, not here):
- **Clear `.job-scout/cache/scores.json`** — the cache key shape expanded to include `profile_hash`, so pre-upgrade entries cannot match post-upgrade lookups. See `_job-matcher/SKILL.md`.
- **Run one tracker archive pass** — aged `status: seen` entries rotate to `.job-scout/archive/tracker-YYYY.json`. See `tracker-schema.md`.

Inform the user about the upgrade actions in a single message, not interactively.

### Adding a new migration

1. Bump the canonical `SCHEMA_VERSION` constant (documented here, not in code — the plugin is a set of markdown skills).
2. Add a subsection below this one describing `v<N> → v<N+1>`: what fields change, how to transform data in place, any files that are renamed or moved.
3. Update every skill that reads the affected files to use the new shape.

First migration (`v1 → v2`) ships with the v0.7.0 release; see below.

### v1 → v2 (visual render layer; ships with plugin v0.7.0)

Applies when the migration runner reads `version: 1` from `.job-scout/schema-version` and the canonical `SCHEMA_VERSION` is `2`.

1. **Add config keys for retention** (idempotent — only adds missing keys, preserves existing values):
   - If `.job-scout/config.json` does not exist, create it with `{}`.
   - If the file is missing the key `render_retention_days`, add it with value `90`.
   - If the file is missing the key `render_archive_days`, add it with value `365`.
   - **Do not** add the `render` key. Its absence is the signal that the first-run prompt (see `render-orchestration.md` Step B1) has not yet fired; the prompt sets the key on first user answer.

2. **Create reports directories** (idempotent):
   - Create `.job-scout/reports/` if missing.
   - Create `.job-scout/reports/archive/` if missing.

3. **Bump schema version**:
   - The runner writes `{ "version": 2, "upgraded_at": "<ISO>" }` to `.job-scout/schema-version` after every per-version migration in the loop completes (per the runner shape above). This step is documented here for completeness; the runner handles the actual write.

This migration is safe to run repeatedly: every per-step write is itself idempotent, and the runner's `current < target` guard prevents re-execution once `version: 2` lands.

### v2 → v3 (foundations + accuracy core; ships with plugin v0.8.0)

Applies when the migration runner reads `version: 2` from `.job-scout/schema-version` and the canonical `SCHEMA_VERSION` is `3`. The data-side migrations are described in detail in `docs/superpowers/plans/2026-05-26-phase-0-1-foundations-and-accuracy.md` Tasks 8–11; this section documents the workspace-level changes.

1. **Add new directories** (idempotent):
   - Create `.job-scout/jds/` for hybrid JD blob storage. See `jd-storage.md`.
   - Create `.job-scout/.backup/` for atomic-write backups.

2. **Lock canonical per-file schemas**. The three state files (`user-profile.json`, `tracker.json`, `recruiters/threads.json`) now declare their own `schema_version: 2` at the top. See `canonical-schemas.md`. All writes go through `state-validators.md` enum checks.

3. **Migrate live state**:
   - `tracker.json` — normalise non-canonical statuses/tiers; backfill `first_seen`; tag every entry `rubric_version: legacy`; remove inline `description` (move to `jds/<id>.txt` lazily on next access).
   - `user-profile.json` — add `segment`, unify `requirements` shape, add empty `deal_breakers[]`, add `tone` block.
   - `recruiters/threads.json` — normalise `lead_tier` enum, rename `participant` → `recruiter_name`, add spec fields (`last_seen_msg_id`, `last_drafted_reply`, `notes[]`, `linked_job_ids[]`).

4. **Bump schema version**:
   - The runner writes `{ "version": 3, "upgraded_at": "<ISO>" }` to `.job-scout/schema-version`.

This migration is performed once per workspace by the one-shot scripts in the v0.8.0 release plan. After it runs, subsequent commands read v3 and proceed normally.

### v3 → v4 (ultramode multi-source foundations; ships with Phase 11)

Applies when the migration runner reads `version: 3` from `.job-scout/schema-version` and the canonical `SCHEMA_VERSION` is `4`. This is the additive, back-compatible foundation for ultramode (sourcing jobs beyond LinkedIn). It introduces no destructive rewrites — every step below is additive or lazy. The per-file changes it enables are detailed in `canonical-schemas.md`.

1. **`user-profile.json` additions** (idempotent — only adds missing keys, preserves existing values):
   - Add `requirements.base_country` with value `null`. It is **only ever populated by onboarding (the `/ultramode` first-run flow), never inferred** — not from the CV, not from email locale, not from prior runs. The migration leaves it `null`; onboarding sets it.
   - Add `requirements.target_geography` with value `null`.
   - Add the top-level `ultramode` block `{ "default": false, "api_keys": {}, "registry_built_at": null }`.
   - These are optional additive fields, so the file's own `schema_version` does **not** bump.

2. **Tracker `source` lazy upgrade** (no migration-time work):
   - The tracker's `source` field changes from a bare LinkedIn string to a structured `{lane, provider, board}` object. This is handled **lazily**, not in the migration pass: reads tolerate both shapes via `tracker_read_source(value)` (see `state-validators.md`), and the next write of any entry rewrites it structured and bumps the tracker file `schema_version` `2 → 3`. The migration pass does **not** rewrite tracker entries.

3. **Score-cache migration** (`cache/scores.json` — non-destructive):
   - LinkedIn entries keep their bare numeric keys unchanged — existing cached scores remain valid.
   - External (namespaced-ID) entries have no pre-existing cache entries, so they simply score fresh on first encounter; a cache miss is acceptable and expected.
   - There is **no destructive rewrite** of `scores.json`. The cache is keyed on the tracker entry's `id` verbatim (numeric for LinkedIn, `<provider>__<board>__<externalid>` for external — see `canonical-schemas.md` § Namespaced external IDs).

4. **`sources.json`** is **not** created by this migration. Its absence is the signal that ultramode discovery has not yet run; the first `/ultramode` invocation builds it. A v3-workspace upgraded to v4 therefore has no `sources.json` and prompts onboarding on first `/ultramode`.

5. **Bump schema version**:
   - The runner writes `{ "version": 4, "upgraded_at": "<ISO>" }` to `.job-scout/schema-version`.

This migration is safe to run repeatedly: each per-step write is idempotent, and the runner's `current < target` guard prevents re-execution once `version: 4` lands.

## Template macro contract: `source_chip(source)`

Tracker entries now carry a structured `source` object (`{lane, provider, board}`), so user-facing templates can no longer interpolate `{{ job.source }}` directly — that would render an object, not a label. A shared macro `source_chip(source)` owns the structured-to-string rendering in one place.

- **Where it lives:** defined as a Jinja macro in `base.html.j2` and `base.md.j2` (the shared template bases), so every Tier 1 template inherits it. Implementation lands in a later task (Task 6); this section documents the contract only.
- **Input:** a structured `source` object, or — for back-compatibility during the lazy upgrade — a bare legacy string.
- **Output:** a short human-readable chip string. For LinkedIn (`lane == "linkedin"`) it renders the `board` surface alone (e.g. `Search`, `Top Picks`) to preserve today's appearance. For external sources it renders a provider/board label (e.g. `Greenhouse · Miro`). A bare legacy string renders verbatim.
- **Migration note:** existing templates currently interpolate `{{ job.source }}` / `{{ note.source }}` directly (in `deep-sweep`, `check-job-notifications`, both html and markdown variants). Those call sites MUST be migrated to `{{ source_chip(job.source) }}` in Task 6. They are **not** edited in this task — only catalogued here.

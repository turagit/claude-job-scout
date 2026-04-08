# Changelog

All notable changes to the LinkedIn Job Hunter plugin are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project aims to follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] — 2026-04-08

Major refactor focused on persistent per-project state, token efficiency, and migrating to the modern plugin format.

### Added

- **Per-project `.job-scout/` workspace.** Every command now bootstraps a hidden, per-project state folder on first invocation (with user consent), containing `user-profile.json`, `tracker.json`, `reports/`, `cache/`, and `recruiters/`. Different projects get cleanly separated state, so a freelance-search workspace and a permanent-role workspace never mix.
- **`shared-references/workspace-layout.md`** — canonical folder layout plus the bootstrap procedure every command runs.
- **`shared-references/tracker-schema.md`** — single authoritative schema for `tracker.json`, documenting the dedupe-before-extract pattern.
- **Content-hash CV caching** in `cv-optimizer` / `/analyze-cv`: parsed CVs and full analysis outputs are cached by content hash. Re-analyzing an unchanged CV returns instantly and skips the Phase 0 discovery interview when `discovery_complete` is already set.
- **Score caching contract** in `job-matcher`: scores are cached by `(job_id, cv_hash)` in `.job-scout/cache/scores.json`. Unchanged jobs scored against an unchanged CV are never re-scored.
- **LinkedIn profile snapshot cache** in `profile-optimizer`: last-seen profile stored in `.job-scout/cache/linkedin-profile.json` and reused for up to 7 days, with only changed sections re-evaluated on subsequent runs.
- **Per-thread recruiter state** in `recruiter-engagement`: `.job-scout/recruiters/threads.json` records `last_seen_msg_id` per thread so unchanged conversations are skipped on subsequent `/check-inbox` runs.
- **"Top job picks for you" sweep** as Step 10 of `/check-job-notifications`: after the notifications report is saved, the command now asks whether to continue analyzing LinkedIn's recommendations feed. It paginates and dedupes against the tracker, only extracting never-before-seen listings.
- **CHANGELOG.md** (this file).
- **`shared-references/browser-policy.md`** — explicit, hard rule that the plugin uses the Claude Chrome extension exclusively for all browser work. Computer use is forbidden. Every browser-touching command now opens with a "Browser policy" section pointing at this file, so the model never escalates a "navigate to LinkedIn" instruction into a computer-use request. README now carries a transparency callout telling users that any computer-use prompt during plugin execution is a bug, not expected behavior.

### Changed

- **Migrated from legacy `commands/` layout to `skills/<name>/SKILL.md`.** Each of the 8 slash commands moved into its own skill directory with modern frontmatter. Silences the "uses the legacy commands/ format" install warning. All 8 commands have `disable-model-invocation: true`, preserving slash-only invocation — the model will never auto-fire browser automation, applications, or recruiter replies.
- **Dedupe-before-extract.** `/check-job-notifications`, `/match-jobs`, and `/job-search` now collect job IDs first and filter against `tracker.json` *before* opening any listing. Previously these commands extracted every job fully and then deduped, paying the full extraction cost for every already-known job. This is the single biggest token-saving change in the release.
- **`shared-references/cv-loading.md`** updated to hash CVs, reuse cached parses, and always operate out of `.job-scout/` rather than loose workspace-root files.
- **Report presentation:** B/C-tier jobs now render as compact rows instead of paragraph rationales — full prose is reserved for A-tier matches.
- **SKILL.md files** for `cv-optimizer`, `job-matcher`, `profile-optimizer`, and `recruiter-engagement` now document their caching contracts and point at the new shared references.
- **`.claude-plugin/plugin.json`** version bumped from 0.2.0 to 0.3.0.

### Migration notes

- On first run in an existing project, the plugin auto-detects legacy `user-profile.json` or `job-reports/` at the workspace root and offers a one-time migration into `.job-scout/`.
- No action required for fresh installs — the bootstrap prompt handles first-time setup.
- If you want `.job-scout/` to stay out of source control, add it to your project's `.gitignore`.

---

## [0.2.0] — Earlier releases

Historical releases preceding the 0.3.0 refactor. These evolved the plugin from the initial MCP prototype into the LinkedIn Job Hunter form:

- CV optimizer with SPAR method, seven-dimension scoring, and persuasion-psychology rewrites.
- Profile optimizer that consumes the CV to drive section proposals and Boolean search simulation.
- Job matcher with freelance/contract adjustments and rate normalization.
- Recruiter engagement skill with lead qualification and response templates.
- `/check-job-notifications` daily driver command.
- Initial loose `job-reports/tracker.json` and workspace-root `user-profile.json` (superseded by `.job-scout/` in 0.3.0).
- Legacy `commands/*.md` layout (migrated to `skills/*/SKILL.md` in 0.3.0).

## [0.1.0] — Initial release

Initial release of the LinkedIn Job Hunter plugin for Claude Cowork. Basic CV and LinkedIn tools, early command set.

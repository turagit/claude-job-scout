# CLAUDE.md

Guidance for Claude (or any agent) working inside the `linkedin-job-hunter` plugin repo. If you're resuming cold, read this first, then `docs/ROADMAP.md`.

## Goal

Automate the end-to-end LinkedIn job-seeking pipeline (CV → profile → search → apply → recruiter) inside the user's own logged-in browser via the Claude Chrome extension, with per-project state, aggressive caching, and subagent-parallelism for scorable units of work.

## Hard rules (non-negotiable)

1. **Browser work uses the Claude Chrome extension exclusively.** Never request "computer use". Never install or suggest Playwright, Selenium, Puppeteer, headless Chrome, or any MCP browser server other than the official Chrome extension. See `skills/shared-references/browser-policy.md`.
2. **Dedupe before extract.** Every command that touches LinkedIn listings loads `.job-scout/tracker.json` first, collects candidate IDs, filters against the tracker, then opens only new ones. This is the largest token saver in the plugin.
3. **`.job-scout/` is the single source of truth for per-project state.** CV profile, tracker, caches, reports, recruiter threads. Never write state to the workspace root or anywhere else.
4. **Every slash command carries `disable-model-invocation: true`.** Commands are user-invoked only — the model must never auto-fire browser automation, applications, or recruiter replies.
5. **Subagent dispatch follows `skills/shared-references/subagent-protocol.md`.** If you spawn a subagent for any reason, use the I/O contract, token budget, and delta-return rule defined there. No ad-hoc subagent shapes.

## File layout

- `skills/<name>/SKILL.md` — each slash command and each model-auto-loaded skill.
- `skills/<name>/references/` — lazy-loaded reference material for that skill.
- `skills/shared-references/` — references used by more than one skill (browser policy, workspace layout, tracker schema, CV loading, subagent protocol, freelance context).
- `.claude-plugin/plugin.json` — plugin manifest and canonical plugin version.
- `docs/ROADMAP.md` — phase status, resume trail.
- `docs/superpowers/specs/` — design specs (immutable once approved).
- `docs/superpowers/plans/` — step-by-step implementation plans.
- `CHANGELOG.md` — user-visible release notes.
- `README.md` — end-user-facing docs.

## Never do

- Install or suggest any browser-automation framework besides the Chrome extension.
- Commit a `.job-scout/` folder into this repo (`.gitignore` covers it).
- Skip the subagent protocol when dispatching subagents.
- Add a per-skill `version:` bump without matching the plugin version policy below.
- Fabricate user achievements, credentials, or metrics in any CV/profile/cover-letter output.
- Enter sensitive data (SSN, bank details, passwords) into any browser form.

## Testing / validation

No automated test suite exists. Validation is manual: spot-checks via shell (`jq`, `grep`, `wc`) and end-to-end runs of the affected slash command in a scratch workspace. Each implementation task in `docs/superpowers/plans/` names the specific verification step.

## Versioning policy

- `.claude-plugin/plugin.json` carries the canonical plugin version. Bump on every user-visible release (SemVer minor for feature releases, patch for fixes).
- Per-skill `version:` frontmatter is informational. Bump it when that skill's contract or output shape changes — not on every edit.
- `CHANGELOG.md` gets one section per plugin version, following Keep a Changelog.

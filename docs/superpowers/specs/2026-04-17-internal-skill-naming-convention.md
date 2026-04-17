# Internal Skill Naming Convention (v0.6.1)

**Date:** 2026-04-17
**Status:** In design — pending execution
**Target release:** v0.6.1 (patch — non-breaking maintenance)

## Why

The plugin's `skills/` directory mixes three categories of `SKILL.md` files in a flat layout:

1. **User-invokable slash commands** (12) — the entry points users are meant to type.
2. **Capability engines** (4) — loaded by orchestrator slash commands (e.g., `cv-optimizer` is loaded by `/analyze-cv`).
3. **Internal subagents** (3) — dispatched only via the `Agent` tool from other skills.

The Claude Code skills menu lists all three categories as peers. User-invokable commands and their internal capability engines end up looking like duplicates (e.g., `analyze-cv` next to `cv-optimizer`). Users have to read descriptions or documentation to know which to pick.

## Convention

**Rule:** skills not intended for direct user invocation are prefixed with an underscore (`_`). Slash-command skills have no prefix.

The underscore follows the near-universal programming convention for "private/internal." It's the lightest-weight signal that works without explanation, and alphabetical sorting groups all underscore-prefixed skills together in the menu.

## Scope

### Renamed (7 skills)

| Current name | New name | Category | Loaded/dispatched by |
|--------------|----------|----------|----------------------|
| `cv-optimizer` | `_cv-optimizer` | Capability | `/analyze-cv` |
| `profile-optimizer` | `_profile-optimizer` | Capability | `/optimize-profile` |
| `job-matcher` | `_job-matcher` | Capability | `/match-jobs`, `/check-job-notifications` |
| `recruiter-engagement` | `_recruiter-engagement` | Capability | `/check-inbox` |
| `company-researcher` | `_company-researcher` | Subagent | `_profile-optimizer`, `/interview-prep` |
| `cv-section-rewriter` | `_cv-section-rewriter` | Subagent | `_cv-optimizer` (Phase 3 rewrite) |
| `cover-letter-writer` | `_cover-letter-writer` | Subagent | `/cover-letter` |

### Unchanged (12 user-invokable slash commands)

`analyze-cv`, `apply`, `check-inbox`, `check-job-notifications`, `cover-letter`, `create-alerts`, `funnel-report`, `index-docs`, `interview-prep`, `job-search`, `match-jobs`, `optimize-profile`.

### Non-goals

- **No slash command renames.** `/analyze-cv`, `/cover-letter`, etc. remain identical — this is a non-breaking change for end users.
- **No behavioural changes.** `disable-model-invocation`, allowed-tools, dispatch shapes — all preserved.
- **No architectural changes.** The three-category pattern (user-invokable / auto-loaded / subagent) stays intact; only the naming visual-signal changes.
- **No directory-structure overhaul.** Stays flat; just renamed. Considered nesting under `skills/_internal/` — rejected because it may break Claude Code's skill discovery depending on harness implementation, and flat-with-prefix is sufficient.

## Changes to supporting content

**Frontmatter `name:` field** of each renamed skill — updated to match new directory name.

**Description prefixes** — 7 frontmatter `description:` fields gain a category marker:
- Capability engines: `"[Internal — loaded by /<parent-command>] ..."`
- Subagents: `"[Internal subagent — dispatched only by <parent>, not user-invocable] ..."`

This provides a second clarity layer: even if a user misses the `_` prefix in the menu, the first bracket in the description names the parent and the role explicitly.

**Cross-references** — every file that references a renamed skill by path or by name must be updated. This includes:
- Every orchestrator's `Reference Materials` section listing the capability/subagent
- Every skill that dispatches a subagent by path (e.g., `cover-letter/SKILL.md` → `_cover-letter-writer/SKILL.md`)
- Every reference file inside a renamed skill (now under `_<name>/references/`) whose relative paths in its own content refer to its own directory — those are relative and don't change because the file moves with the directory
- CLAUDE.md, ROADMAP.md, CHANGELOG — mentions of renamed skills

**CLAUDE.md** — new subsection under "Hard rules" codifying the convention so future contributors follow it.

## Release

**v0.6.1** — patch release (non-breaking maintenance). No user-invokable command behaviour changes. CHANGELOG entry describes it as a clarity/hygiene improvement.

Decision: do **not** start an "Unreleased" CHANGELOG section now — the convention change is a discrete release and users benefit from a clear version marker showing when the rename happened.

## What "done" looks like

- All 7 directories renamed; `git mv` preserves history.
- 7 `name:` frontmatter fields updated to match new directory names.
- 7 `description:` fields prefixed with `[Internal …]` marker.
- All cross-references in sibling skills and references updated.
- CLAUDE.md documents the convention in the "Hard rules" section.
- `grep -rn '\bcv-optimizer\b\|\bprofile-optimizer\b\|\bjob-matcher\b\|\brecruiter-engagement\b\|\bcompany-researcher\b\|\bcv-section-rewriter\b\|\bcover-letter-writer\b' skills/ docs/` returns zero matches for the old names (except within CHANGELOG historical entries for v0.4.0–v0.6.0, which should remain unchanged as historical record).
- `plugin.json` reports `0.6.1`.
- `git status` is clean on `main`.

## Open questions

1. **Should CHANGELOG historical entries be preserved with old names?** Yes — they document what shipped at v0.4.0, v0.5.0, v0.6.0 when those names were current. Only forward-looking docs use new names.
2. **Should `allowed-tools` frontmatter be removed from capability engines?** Capability engines don't need slash-command tools (they're loaded, not invoked). Current files inherit `allowed-tools` from their historical slash-command shape. **Working assumption:** leave as-is this release. If the tools list is wrong, it's a behaviour change requiring separate analysis.

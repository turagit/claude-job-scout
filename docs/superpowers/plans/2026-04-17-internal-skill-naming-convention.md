# Internal Skill Naming Convention Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Rename 7 internal skills with `_` prefix to distinguish them from user-invokable slash commands in the skills menu. Ship as v0.6.1 patch release.

**Architecture:** Rename-only maintenance PR. All changes are a single atomic commit per task — renaming a skill without updating its references leaves the repo in a broken intermediate state, so renames and cross-reference updates ship together.

**Design spec:** [`docs/superpowers/specs/2026-04-17-internal-skill-naming-convention.md`](../specs/2026-04-17-internal-skill-naming-convention.md)

**Branching:** 2 tasks, 2 branches, 2 serial merges to `main`.

---

## Task 1: Atomic rename + cross-reference update

Single coherent commit. Rename all 7 skill directories, update frontmatter `name:` fields, prefix descriptions, and fix every cross-reference in the repo. Cannot be split without breaking the repo.

**Files renamed (`git mv`):**
- `skills/cv-optimizer/` → `skills/_cv-optimizer/`
- `skills/profile-optimizer/` → `skills/_profile-optimizer/`
- `skills/job-matcher/` → `skills/_job-matcher/`
- `skills/recruiter-engagement/` → `skills/_recruiter-engagement/`
- `skills/company-researcher/` → `skills/_company-researcher/`
- `skills/cv-section-rewriter/` → `skills/_cv-section-rewriter/`
- `skills/cover-letter-writer/` → `skills/_cover-letter-writer/`

**Files modified (frontmatter + description):**
- `skills/_cv-optimizer/SKILL.md` — `name: _cv-optimizer`, description prefix `[Internal — loaded by /analyze-cv]`
- `skills/_profile-optimizer/SKILL.md` — `name: _profile-optimizer`, description prefix `[Internal — loaded by /optimize-profile]`
- `skills/_job-matcher/SKILL.md` — `name: _job-matcher`, description prefix `[Internal — loaded by /match-jobs and /check-job-notifications]`
- `skills/_recruiter-engagement/SKILL.md` — `name: _recruiter-engagement`, description prefix `[Internal — loaded by /check-inbox]`
- `skills/_company-researcher/SKILL.md` — `name: _company-researcher`, description prefix `[Internal subagent — dispatched only by /interview-prep and _profile-optimizer, not user-invocable]`
- `skills/_cv-section-rewriter/SKILL.md` — `name: _cv-section-rewriter`, description prefix `[Internal subagent — dispatched only by _cv-optimizer, not user-invocable]`
- `skills/_cover-letter-writer/SKILL.md` — `name: _cover-letter-writer`, description prefix `[Internal subagent — dispatched only by /cover-letter, not user-invocable]`

**Cross-reference updates across sibling skills (estimate ~15 files):**

Any `SKILL.md` or `references/*.md` that names one of the 7 renamed skills by path or by name must be updated. The audit pattern below finds them all.

### Steps

- [ ] **Step 1: Create branch**

```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b v0.6.1/task-01-internal-skill-rename
```

- [ ] **Step 2: Audit — list everything that will be touched**

Run each of these and save the output — use it to plan Step 3 edits. Verify nothing unexpected appears.

```bash
cd /Users/tura/git/claude-job-scout && grep -rln "cv-optimizer\|profile-optimizer\|job-matcher\|recruiter-engagement\|company-researcher\|cv-section-rewriter\|cover-letter-writer" skills/ docs/ README.md CLAUDE.md CHANGELOG.md 2>/dev/null | sort -u
```

Expected: a union of files that reference any of the 7 old names. Each one needs inspection.

```bash
cd /Users/tura/git/claude-job-scout && ls skills/
```

Expected: see the 7 old directory names alongside the user-invokable ones. Confirm you have the correct list.

- [ ] **Step 3: Rename directories with `git mv` (preserves history)**

```bash
cd /Users/tura/git/claude-job-scout && \
git mv skills/cv-optimizer skills/_cv-optimizer && \
git mv skills/profile-optimizer skills/_profile-optimizer && \
git mv skills/job-matcher skills/_job-matcher && \
git mv skills/recruiter-engagement skills/_recruiter-engagement && \
git mv skills/company-researcher skills/_company-researcher && \
git mv skills/cv-section-rewriter skills/_cv-section-rewriter && \
git mv skills/cover-letter-writer skills/_cover-letter-writer
```

Verify:
```bash
cd /Users/tura/git/claude-job-scout && ls skills/ | grep "^_" | wc -l
```
Expected: `7`.

- [ ] **Step 4: Update `name:` frontmatter in each renamed skill**

For each of the 7 renamed skills, open the SKILL.md and update the `name:` field to match the new directory name. Exact edits:

**`skills/_cv-optimizer/SKILL.md`** — find `name: cv-optimizer` → replace with `name: _cv-optimizer`.
**`skills/_profile-optimizer/SKILL.md`** — find `name: profile-optimizer` → replace with `name: _profile-optimizer`.
**`skills/_job-matcher/SKILL.md`** — find `name: job-matcher` → replace with `name: _job-matcher`.
**`skills/_recruiter-engagement/SKILL.md`** — find `name: recruiter-engagement` → replace with `name: _recruiter-engagement`.
**`skills/_company-researcher/SKILL.md`** — find `name: company-researcher` → replace with `name: _company-researcher`.
**`skills/_cv-section-rewriter/SKILL.md`** — find `name: cv-section-rewriter` → replace with `name: _cv-section-rewriter`.
**`skills/_cover-letter-writer/SKILL.md`** — find `name: cover-letter-writer` → replace with `name: _cover-letter-writer`.

Verify:
```bash
cd /Users/tura/git/claude-job-scout && grep -l "^name: _" skills/_*/SKILL.md | wc -l
```
Expected: `7`.

- [ ] **Step 5: Prefix the 7 descriptions with a category marker**

For each renamed skill, prepend the category marker to the `description:` value. The original description text follows immediately after. Exact edits:

**`skills/_cv-optimizer/SKILL.md`** — the `description:` field is multi-line (starts with `>`). Prepend `[Internal — loaded by /analyze-cv] ` to the first content line of the description. For example, find:
```
description: >
  This skill should be used when the user asks to "analyze my CV", ...
```
Replace with:
```
description: >
  [Internal — loaded by /analyze-cv] This skill should be used when the user asks to "analyze my CV", ...
```

Apply the analogous prefix to the other 6 renamed skills. The exact prefix per skill (matches the spec):

- `_cv-optimizer`: `[Internal — loaded by /analyze-cv]`
- `_profile-optimizer`: `[Internal — loaded by /optimize-profile]`
- `_job-matcher`: `[Internal — loaded by /match-jobs and /check-job-notifications]`
- `_recruiter-engagement`: `[Internal — loaded by /check-inbox]`
- `_company-researcher`: `[Internal subagent — dispatched only by /interview-prep and _profile-optimizer, not user-invocable]`
- `_cv-section-rewriter`: `[Internal subagent — dispatched only by _cv-optimizer, not user-invocable]`
- `_cover-letter-writer`: `[Internal subagent — dispatched only by /cover-letter, not user-invocable]`

Verify:
```bash
cd /Users/tura/git/claude-job-scout && grep -c "\[Internal" skills/_*/SKILL.md
```
Expected: `7` total.

- [ ] **Step 6: Update cross-references in sibling skills**

For each sibling (non-renamed) SKILL.md and reference file, replace every occurrence of the 7 old names with the new `_`-prefixed names.

**Scope of replacement:** the exact string `cv-optimizer` → `_cv-optimizer`, `profile-optimizer` → `_profile-optimizer`, etc. — but ONLY when the old name is being used as a skill reference (path or name). Do NOT replace occurrences inside CHANGELOG historical entries (those are the frozen record of what shipped at each prior version).

**Known sibling files to update (from Step 2 audit):**
- `skills/analyze-cv/SKILL.md` — references `cv-optimizer` (load the skill)
- `skills/match-jobs/SKILL.md` — references `job-matcher`
- `skills/check-job-notifications/SKILL.md` — references `job-matcher`
- `skills/optimize-profile/SKILL.md` — references `profile-optimizer`
- `skills/check-inbox/SKILL.md` — references `recruiter-engagement`
- `skills/cover-letter/SKILL.md` — references `cover-letter-writer`
- `skills/interview-prep/SKILL.md` — references `company-researcher`, `cv-optimizer` (for psychology-cheatsheet path)
- `skills/funnel-report/SKILL.md` — references `recruiter-engagement` (for notes schema)
- Reference files inside renamed skills that point to sibling subagents (e.g., `_cv-optimizer/SKILL.md` references `cv-section-rewriter` in its Parallel Rewrite section — must become `_cv-section-rewriter`)
- `skills/_cv-section-rewriter/SKILL.md` — references `cv-optimizer/references/phase-3-optimized-rewrite.md` — must become `_cv-optimizer/references/phase-3-optimized-rewrite.md`

The complete list comes from the Step 2 audit. Use find-and-replace per file, verifying each edit in context.

**Do NOT touch:**
- `CHANGELOG.md` — historical sections for 0.4.0, 0.5.0, 0.6.0 keep old names (they documented what shipped at those versions)
- `docs/superpowers/specs/2026-04-16-*.md` — phase specs are immutable historical design docs
- `docs/superpowers/plans/2026-04-16-*.md` and `2026-04-17-phase-*.md` — implementation plans are historical records
- `docs/ROADMAP.md` checkbox descriptions — these summarise completed work; old names are fine

Verify:
```bash
cd /Users/tura/git/claude-job-scout && grep -rln "\b\(cv-optimizer\|profile-optimizer\|job-matcher\|recruiter-engagement\|company-researcher\|cv-section-rewriter\|cover-letter-writer\)\b" skills/
```
Expected: zero output (all skill-internal references updated).

```bash
cd /Users/tura/git/claude-job-scout && grep -rln "_cv-optimizer\|_profile-optimizer\|_job-matcher\|_recruiter-engagement\|_company-researcher\|_cv-section-rewriter\|_cover-letter-writer" skills/
```
Expected: non-zero — new names present throughout skills/.

- [ ] **Step 7: Audit pass — confirm no broken references**

```bash
cd /Users/tura/git/claude-job-scout && for f in skills/*/SKILL.md skills/*/references/**/*.md; do [ -f "$f" ] || continue; grep -oE "\`[^\`]*\.md\`|\`\.\./[^\`]*\`" "$f" 2>/dev/null; done | sort -u > /tmp/refs.txt && while IFS= read -r line; do clean=$(echo "$line" | tr -d '\`'); full="skills/$(echo "$clean" | sed 's|^\.\./||; s|\./||')"; if [[ "$clean" == *.md ]] && [ ! -f "$full" ] && [ ! -f "$clean" ]; then echo "MISSING: $clean"; fi; done < /tmp/refs.txt
```

This is a best-effort dead-link check. Expected: minimal or zero MISSING lines. Report anything unexpected.

- [ ] **Step 8: Commit + push**

```bash
cd /Users/tura/git/claude-job-scout && git add -A && git commit -m "$(cat <<'EOF'
Prefix 7 internal skills with _ for menu clarity

Renames capability engines (cv-optimizer, profile-optimizer, job-matcher,
recruiter-engagement) and subagents (company-researcher, cv-section-rewriter,
cover-letter-writer) to underscore-prefixed names. The _ signals "not for
direct user invocation" in the skills menu — follows the universal
programming convention for internal/private.

User-invokable slash commands (12) are unchanged. This is a non-breaking
maintenance change: no slash command renames, no behavioural changes.

Each renamed skill:
- Directory renamed via git mv (preserves history)
- Frontmatter name: field updated to match new directory
- description: prefixed with [Internal — ...] marker naming the parent
  command/skill that loads or dispatches it

All cross-references across sibling skills and reference files updated
to use new names. Historical records (CHANGELOG 0.4.0–0.6.0, phase
specs, phase plans) keep old names — they document what shipped at
those versions.

Ships as v0.6.1.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)" && git push -u origin v0.6.1/task-01-internal-skill-rename
```

## Task 2: CLAUDE.md convention + v0.6.1 release

**Files:**
- Modify: `CLAUDE.md` (document the convention under Hard rules)
- Modify: `.claude-plugin/plugin.json` (version 0.6.0 → 0.6.1)
- Modify: `CHANGELOG.md` (add [0.6.1] section above [0.6.0])
- Modify: `docs/ROADMAP.md` (log entry)

### Steps

- [ ] **Step 1: Create branch (merge AFTER Task 1)**

```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b v0.6.1/task-02-release
```

- [ ] **Step 2: Document convention in CLAUDE.md**

Find the current "Hard rules" section. Append a new rule (preserve numbering — whatever the last existing rule number is, add one):

```
N. **Skills prefixed with `_` are internal.** User-invokable slash commands have no prefix (`analyze-cv`, `cover-letter`, etc.). Skills starting with `_` (`_cv-optimizer`, `_cover-letter-writer`, etc.) are capability engines loaded by orchestrators or subagents dispatched via the `Agent` tool — never invoke them directly as slash commands. When creating new skills, follow this convention: `_` prefix if the skill is loaded by another skill or dispatched via `Agent`; no prefix if the user types it as a slash command.
```

- [ ] **Step 3: Bump plugin version**

In `.claude-plugin/plugin.json`: find `"version": "0.6.0"` → replace with `"version": "0.6.1"`.

- [ ] **Step 4: Add 0.6.1 CHANGELOG section**

Insert above `## [0.6.0] — 2026-04-17`:

```markdown
## [0.6.1] — 2026-04-17

Maintenance release. No user-invokable command changes.

### Changed

- **Internal skills now prefixed with `_`** — the 7 skills that are not user-invokable (4 capability engines: `cv-optimizer`, `profile-optimizer`, `job-matcher`, `recruiter-engagement`; 3 internal subagents: `company-researcher`, `cv-section-rewriter`, `cover-letter-writer`) are renamed to `_cv-optimizer`, `_profile-optimizer`, etc. The underscore follows the universal programming convention for "private/internal" and visually distinguishes them from the 12 user-invokable slash commands in the skills menu. All cross-references updated. Historical records (prior CHANGELOG entries, phase specs, phase plans) preserve old names as they documented what shipped at those versions.
- **Skill descriptions** for renamed skills gain an `[Internal — …]` or `[Internal subagent — …]` prefix naming the parent command or skill that loads/dispatches them.
- **`CLAUDE.md`** documents the naming convention so future contributors follow it.
- **`.claude-plugin/plugin.json`** version bumped from 0.6.0 to 0.6.1.

### Migration notes

- **Non-breaking for end users.** All 12 user-invokable slash commands (`/analyze-cv`, `/cover-letter`, `/check-job-notifications`, etc.) keep their names and behaviour.
- **Non-breaking for plugin developers** unless they imported the renamed skills by name or path in custom extensions — in which case update to the new `_`-prefixed names.

---

```

- [ ] **Step 5: Update ROADMAP log**

Append to the log section:

```
- **2026-04-17** — v0.6.1 maintenance release. Renamed 7 internal skills with `_` prefix for menu clarity.
```

- [ ] **Step 6: Verify**

```bash
cd /Users/tura/git/claude-job-scout && jq -r .version .claude-plugin/plugin.json
```
Expected: `0.6.1`.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "^## \[0.6.1\]" CHANGELOG.md
```
Expected: `1`.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "Skills prefixed with" CLAUDE.md
```
Expected: `1`.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "v0.6.1 maintenance release" docs/ROADMAP.md
```
Expected: `1`.

```bash
cd /Users/tura/git/claude-job-scout && git diff --stat
```
Expected: 4 files changed.

- [ ] **Step 7: Commit + push**

```bash
cd /Users/tura/git/claude-job-scout && git add -A && git commit -m "$(cat <<'EOF'
Release v0.6.1 — internal skill naming convention

Bumps plugin version, adds CHANGELOG 0.6.1 section, documents the
_-prefix convention in CLAUDE.md, appends ROADMAP log entry.
Non-breaking maintenance release.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)" && git push -u origin v0.6.1/task-02-release
```

- [ ] **Step 8: After merge — tag v0.6.1**

Once the release branch merges to main:
```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git tag -a v0.6.1 -m "v0.6.1 — internal skill naming convention (maintenance)" && git push origin v0.6.1
```

---

## Self-review

**Spec coverage:** all 7 renames, frontmatter updates, description prefixes, cross-reference updates, CLAUDE.md convention, version bump, CHANGELOG, ROADMAP — all covered across the two tasks.

**Placeholder scan:** none.

**Type consistency:** the 7 new names are used identically across all references in the plan (e.g., `_cv-optimizer` not `_cv_optimizer` or `cv-optimizer_`).

## Execution handoff

**Plan complete. Two execution options:**

**1. Subagent-Driven (recommended)** — same pipeline as Phases 1–3.

**2. Inline Execution** — same session, batch with checkpoints.

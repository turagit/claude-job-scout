# Phase 4 — Visual Render Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship v0.7.0 by adding a visual render layer that turns Tier 1 command output into self-contained HTML reports auto-opened in the user's Chrome via the existing extension, with a styled-markdown fallback when HTML rendering or Chrome opening fails.

**Architecture:** This plugin is a Claude Code plugin — the "code" is markdown skill files, markdown references, and per-project JSON state under `.job-scout/`. Validation is manual via shell (`jq`, `grep`, `wc`) and end-to-end runs in a scratch workspace. A new internal `_visualizer` subagent is dispatched via the `Agent` tool per the existing subagent protocol; it loads templates, embeds data as JSON, and writes self-contained HTML to `.job-scout/reports/`. Each Tier 1 command gains a final "render" step that calls a shared orchestration procedure documented in `shared-references/render-orchestration.md`.

**Tech Stack:** Markdown (CommonMark) skill files, Jinja2-shaped templates with a narrow expression surface, vanilla CSS + ~3 KB vanilla JS (no frameworks, no build step), JSON state, Claude `Agent` tool for subagent dispatch, Claude Chrome extension for browser-open.

**Design spec:** [`docs/superpowers/specs/2026-04-29-visual-render-layer-design.md`](../specs/2026-04-29-visual-render-layer-design.md)

**Roadmap:** [`docs/ROADMAP.md`](../../ROADMAP.md)

**Branching:** each task is one branch off `main` named `phase-4/task-NN-<short-slug>`. Controller merges directly to `main` after dual review (no PRs — `gh` CLI is unavailable in this environment).

**Merge order:** tasks are numbered to be merged **serially** in numerical order. Foundational tasks (1–9) must land before any Tier 1 command is wired (10+). Tasks 12–16 (the remaining five views) may be developed in parallel branches but must merge in numerical order to keep ROADMAP ticks coherent.

**Progress tracking:** after each task merges, tick the matching checkbox in `docs/ROADMAP.md`'s new Phase 4 section (added in Task 18).

---

## Task 1: `_visualizer` skill skeleton + reference files

**Files:**
- Create: `/Users/tura/git/claude-job-scout/skills/_visualizer/SKILL.md` (placeholder; full content in Task 5)
- Create: `/Users/tura/git/claude-job-scout/skills/_visualizer/references/rendering-protocol.md`
- Create: `/Users/tura/git/claude-job-scout/skills/_visualizer/references/theme-tokens.md`
- Create: `/Users/tura/git/claude-job-scout/skills/_visualizer/references/component-library.md`

- [ ] **Step 1: Create branch + dirs**

```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-4/task-01-visualizer-skeleton && mkdir -p skills/_visualizer/references skills/_visualizer/templates/html skills/_visualizer/templates/markdown skills/_visualizer/assets
```

- [ ] **Step 2: Write placeholder `_visualizer/SKILL.md`**

Create `/Users/tura/git/claude-job-scout/skills/_visualizer/SKILL.md` with exactly this content:

===FILE_START===
---
name: _visualizer
description: >
  [Internal subagent — dispatched only by Tier 1 user-facing commands, not user-invocable] Renders structured command output as a self-contained HTML report (Modern Cards aesthetic) or styled markdown. Writes the result to `.job-scout/reports/` and returns the path. Loaded via the `Agent` tool per `../shared-references/subagent-protocol.md`.
version: 0.1.0
---

# Visualizer (Subagent) — Skeleton

This file is a placeholder created in Task 1 of the v0.7.0 plan. The full subagent contract — input schema, output contract, templating engine, file-write logic, schema check, error returns — is filled in by Task 5.

Until Task 5 lands, this skill is not dispatchable.
===FILE_END===

- [ ] **Step 3: Write `references/rendering-protocol.md`**

Create `/Users/tura/git/claude-job-scout/skills/_visualizer/references/rendering-protocol.md` with exactly this content:

===FILE_START===
# Rendering Protocol

The contract every Tier 1 command follows when dispatching `_visualizer` via the `Agent` tool. Layered on top of `../../shared-references/subagent-protocol.md` (the universal subagent contract); this file specialises that contract for rendering.

## Dispatch envelope

The dispatcher passes a single JSON envelope as the prompt body:

```json
{
  "task": "render-report",
  "inputs": {
    "view": "match-jobs | job-search | check-job-notifications | funnel-report | check-inbox | interview-prep",
    "format": "html | markdown | plain",
    "data": { /* view-specific payload — see component-library.md */ },
    "output_dir": "/abs/path/to/.job-scout/reports"
  },
  "budget_lines": 800,
  "allowed_tools": ["Read", "Write"]
}
```

`budget_lines: 800` is set high because rendered HTML can run 30–50 KB. Subagents that need more must return `status: "partial"` per the universal protocol.

`allowed_tools` is exactly `["Read", "Write"]` — `Read` to load templates and assets, `Write` to emit the final file. Nothing else.

## Successful response (delta-return)

```json
{
  "status": "ok",
  "deltas": [
    {
      "path": "/abs/path/to/.job-scout/reports/match-jobs-latest.html",
      "format": "html",
      "bytes": 38421
    }
  ],
  "errors": [],
  "continuation_cursor": null
}
```

Exactly one delta per dispatch. The path is the file the subagent just wrote (HTML) or the markdown body it produced (when `format: "markdown"`). For `markdown` and `plain`, no file is written — the dispatcher prints the body in-conversation; the subagent returns the rendered string in a special `body` field instead of `path`:

```json
{
  "status": "ok",
  "deltas": [
    {
      "path": null,
      "format": "markdown",
      "bytes": 1842,
      "body": "## Match report — 4 results...\n..."
    }
  ],
  "errors": [],
  "continuation_cursor": null
}
```

## Error responses

```json
{
  "status": "error",
  "deltas": [],
  "errors": [
    { "code": "schema_mismatch | budget_exceeded | template_missing | io_error", "message": "<one-line>" }
  ],
  "continuation_cursor": null
}
```

Error codes:
- `schema_mismatch` — required keys missing in `inputs.data` for the given `view`.
- `budget_exceeded` — output exceeded `budget_lines`. Subagent should never return partial HTML; it returns this error and lets the dispatcher fall through to markdown.
- `template_missing` — no template file at `templates/<format>/<view>.<ext>.j2`.
- `io_error` — `Write` failed (disk full, path not writable, etc.).

## Templating engine — supported syntax

`_visualizer` interprets a narrow Jinja-shaped surface:

- `{{ <dot.path> }}` — value substitution; HTML-escaped by default in `.html.j2` templates, raw in `.md.j2`.
- `{{ <dot.path> | raw }}` — raw substitution (no escape) in HTML templates.
- `{{ <dot.path> | json }}` — JSON-stringified substitution (used for the embedded data slot).
- `{% for item in <dot.path> %} ... {% endfor %}` — iteration. Inside the loop, `item` is the iterating variable.
- `{% if <dot.path> %} ... {% endif %}` — conditional rendering. Truthy on non-empty / non-zero / non-null.
- `{% if <dot.path> %} ... {% else %} ... {% endif %}` — with `else` branch.

Anything beyond this is out of scope. Filters other than `raw` and `json` are not supported. There are no macros, no includes, no inheritance — composition happens by the dispatcher passing a complete data shape.

`<dot.path>` resolves left-to-right: `data.jobs[0].score` resolves `data` → `data.jobs` → `data.jobs[0]` → `data.jobs[0].score`. Bracket notation supports integer indices only. Missing keys at any depth resolve to empty string (HTML) or empty value (markdown), never to `undefined` or an error.

## Schema check (per view)

Each view's HTML and markdown templates begin with a 5-line frontmatter comment listing the required keys in `inputs.data`. The subagent reads this frontmatter, validates the input data, and returns `schema_mismatch` if any required key is missing.

Frontmatter shape (in `.html.j2` files; identical in `.md.j2`):

```html
{# schema:
   required:
     - data.view_title
     - data.results[].score
     - data.results[].title
#}
```

The subagent parses this comment block by string match — no full Jinja parser needed.

## File-write rules (HTML format only)

- Path: `<output_dir>/<filename>` where `filename` is dispatcher-supplied via `inputs.data.filename` (the dispatcher decides snapshot-vs-timestamped naming).
- Atomic write: write to `<filename>.tmp`, then rename. Avoids half-written files if the subagent dies mid-write.
- Inline assets: `theme.css` and `interactive.js` are read from `../assets/` and embedded as `<style>` and `<script>` blocks in the final HTML. No external `<link>` or `<script src>`.
- Embedded data: `inputs.data` is serialized as a `<script type="application/json" id="report-data">` block so the interactive JS can read it without re-parsing the DOM.

## File-write rules (markdown / plain format)

No file is written. Subagent returns the rendered body in the `body` field. Dispatcher prints it directly in the conversation.
===FILE_END===

- [ ] **Step 4: Write `references/theme-tokens.md`**

Create `/Users/tura/git/claude-job-scout/skills/_visualizer/references/theme-tokens.md` with exactly this content:

===FILE_START===
# Theme Tokens — Modern Cards

Single source of truth for visual design across all rendered HTML reports. Every per-view template uses these tokens via `var(--name)` — no view defines its own colors, fonts, or spacing.

The full token set is implemented as CSS custom properties in `../assets/theme.css`. This file is the conceptual reference; `theme.css` is the implementation.

## Color tokens

| Token | Value | Use |
|-------|-------|-----|
| `--bg-page` | linear-gradient(180deg, #fff 0%, #f5f3ff 100%) | Page background |
| `--bg-card` | #ffffff | Card surfaces |
| `--surface-soft` | #f5f3ff | Subtle inner surfaces (chip backgrounds, hover states) |
| `--accent-from` | #7c3aed (violet 600) | Primary gradient start, A-tier pill, link color |
| `--accent-to` | #ec4899 (pink 500) | Primary gradient end |
| `--accent-warn` | #fbbf24 (amber 400) | B-tier pill background |
| `--accent-warn-fg` | #78350f (amber 900) | B-tier pill text |
| `--accent-mute` | #9ca3af (gray 400) | C-tier text, muted accents |
| `--text-strong` | #1f1f2e | Body text, titles |
| `--text-muted` | #6b7280 | Secondary text, metadata lines |
| `--ring-soft` | rgba(124, 58, 237, 0.10) | Card borders, divider lines |
| `--shadow-card` | 0 1px 3px rgba(0,0,0,.04), 0 8px 24px rgba(124,58,237,.08) | Card shadow |

## Geometry tokens

| Token | Value | Use |
|-------|-------|-----|
| `--radius-card` | 12px | Card corners, fold containers |
| `--radius-pill` | 999px | Score pills, tag chips, toolbar buttons |

## Typography tokens

| Token | Value | Use |
|-------|-------|-----|
| `--font-sans` | 'Inter', -apple-system, system-ui, sans-serif | Body text, titles |
| `--font-mono` | 'JetBrains Mono', 'SF Mono', monospace | Score values, metric numbers, timestamps |

## Tier-color mapping

A score's tier is derived in the dispatcher (orchestrator) and passed in `inputs.data` as a `tier` string. Templates render the score pill with a class derived from the tier:

| Tier | Score range | Pill class | Pill background |
|------|-------------|------------|-----------------|
| A | ≥ 80 | `score-pill tier-a` | violet→pink gradient |
| B | 60–79 | `score-pill tier-b` | amber |
| C | < 60 | `score-pill tier-c` | gray |

Templates never compute the tier themselves — they trust the dispatcher's `tier` field.

## Print mode

`@media print` rules in `theme.css`:
- Page background → white.
- Hover effects removed.
- Toolbar and copy buttons hidden.
- Folds forced open.
- Cards get a 1 px solid border instead of shadow.
- `page-break-inside: avoid` on cards and folds.
===FILE_END===

- [ ] **Step 5: Write `references/component-library.md`**

Create `/Users/tura/git/claude-job-scout/skills/_visualizer/references/component-library.md` with exactly this content:

===FILE_START===
# Component Library

The HTML class primitives that templates compose. Every primitive is implemented in `../assets/theme.css`. Templates use class names; they do not redefine styles.

## `.report-header`

The hero block at the top of every HTML report. Composed of:

```html
<header class="report-header">
  <div class="icon">★</div>
  <div>
    <h1>{{ data.title }}</h1>
    <div class="subtitle">{{ data.subtitle }}</div>
  </div>
</header>
```

The `★` icon is rendered with the violet→pink gradient. Templates may swap the glyph (e.g., 📬 for inbox); the gradient is preserved by `theme.css`.

## `.job-card` / `.thread-card` / `.event-card`

Three names for the same card primitive — semantic differentiation only. All three share the visual treatment.

```html
<article class="job-card" data-tier="a" data-sort_score="87" data-sort_date="2026-04-29">
  <div class="header">
    <div class="title">Senior Backend Engineer</div>
    <div class="score-pill tier-a">87</div>
  </div>
  <div class="meta">Stripe · Remote · €180–220k</div>
  <div>
    <span class="tag-chip">Go</span>
    <span class="tag-chip">Payments</span>
    <span class="tag-chip accent">Senior IC</span>
  </div>
</article>
```

`data-tier` and `data-sort_*` attributes are read by `interactive.js` for filter/sort. The dispatcher emits them; templates iterate.

## `.score-pill`

Three-variant pill: `tier-a` (gradient), `tier-b` (amber), `tier-c` (gray). Always wraps a numeric score.

## `.tag-chip` / `.tag-chip.accent`

Small pill chip for keywords, skills, signals. Default is violet on `--surface-soft`; `.accent` flips to pink-on-pink for variety.

## `.metric-block`

Used in `funnel-report` for big-number stats:

```html
<div class="metric-block">
  <div class="label">Applications sent</div>
  <div class="value">12</div>
  <div class="delta up">+3 vs last week</div>
</div>
```

`.delta.up` is green; `.delta.down` is red. Templates pass `up` or `down` based on sign.

## `.timeline-item`

Used in `check-inbox` and `interview-prep` for chronological lists. Renders a left-rail dot:

```html
<div class="timeline-item">
  <div class="meta">2026-04-28 · Sarah from Stripe</div>
  <div>"Saw your profile and wanted to chat about a Senior Backend role..."</div>
</div>
```

## `.fold`

Collapsible section with a chevron. Used in `interview-prep` and inside long thread cards.

```html
<div class="fold">
  <div class="fold-header">
    <span>Company background</span>
    <span class="chevron">›</span>
  </div>
  <div class="fold-body">
    <p>Stripe is a payments infrastructure company...</p>
  </div>
</div>
```

JS toggles `.open` on the outer `.fold`. Print stylesheet forces all folds open.

## `.empty-state`

Used when a command produces zero results.

```html
<div class="empty-state">
  <div class="icon">🌱</div>
  <div class="title">No new matches today.</div>
  <div class="hint">Try refining your search filters or running again later.</div>
</div>
```

## `.toolbar`

Horizontal row of sort/filter buttons. Always sits immediately above a list of `.job-card`s (etc.) — `interactive.js` finds the list as `nextElementSibling`.

```html
<div class="toolbar">
  <button data-sort="score" class="active">Score ↓</button>
  <button data-sort="date">Date ↓</button>
  <button data-sort="company">Company A–Z</button>
  <span style="flex:1"></span>
  <button data-filter="all" class="active">All</button>
  <button data-filter="a">A-tier</button>
  <button data-filter="b">B-tier</button>
</div>
```

## `.copy-btn`

Small button that copies a sibling element's text to clipboard. Used in `interview-prep` for prep paragraphs and in any view for cover-letter-shaped output (Tier 2 work; reserved primitive).

```html
<button class="copy-btn" data-copy-target="prep-1">Copy</button>
<div id="prep-1">...prep content...</div>
```

JS handles the click, swaps the label to "Copied!" for 1.5 s.

## Footer

Every report ends with:

```html
<footer>
  Generated 2026-04-29 14:30 · linkedin-job-hunter v0.7.0
</footer>
```

Templates fill the timestamp from `data.generated_at` (always provided by the dispatcher).
===FILE_END===

- [ ] **Step 6: Verify**

```bash
cd /Users/tura/git/claude-job-scout && ls skills/_visualizer/ skills/_visualizer/references/ skills/_visualizer/templates/ skills/_visualizer/templates/html/ skills/_visualizer/templates/markdown/ skills/_visualizer/assets/ 2>&1
```
Expected: all directories exist; `_visualizer/` contains `SKILL.md`; `references/` contains 3 `.md` files; `templates/`, `templates/html/`, `templates/markdown/`, and `assets/` are empty.

```bash
cd /Users/tura/git/claude-job-scout && wc -l skills/_visualizer/SKILL.md skills/_visualizer/references/*.md
```
Expected: SKILL.md ~10 lines (placeholder); rendering-protocol.md ~85 lines; theme-tokens.md ~55 lines; component-library.md ~110 lines.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "schema_mismatch\|budget_exceeded\|template_missing\|io_error" skills/_visualizer/references/rendering-protocol.md
```
Expected: at least `4`.

```bash
cd /Users/tura/git/claude-job-scout && git status -s
```
Expected: 4 new files under `skills/_visualizer/`.

- [ ] **Step 7: Commit + push**

```bash
cd /Users/tura/git/claude-job-scout && git add skills/_visualizer/ && git commit -m "$(cat <<'EOF'
Scaffold _visualizer skill skeleton + reference files

Adds the directory structure for the v0.7.0 visualizer subagent
plus three reference documents: rendering-protocol (subagent
contract, templating engine surface, error codes), theme-tokens
(Modern Cards color/geometry/type tokens), and component-library
(HTML class primitives templates compose). The SKILL.md itself is
a placeholder; full contract is written in Task 5.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)" && git push -u origin phase-4/task-01-visualizer-skeleton
```

---

## Task 2: theme.css asset

**Files:**
- Create: `/Users/tura/git/claude-job-scout/skills/_visualizer/assets/theme.css`

- [ ] **Step 1: Create branch**

```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-4/task-02-theme-css
```

- [ ] **Step 2: Write `theme.css`**

Create `/Users/tura/git/claude-job-scout/skills/_visualizer/assets/theme.css` with exactly this content:

===FILE_START===
:root {
  --bg-page: linear-gradient(180deg, #ffffff 0%, #f5f3ff 100%);
  --bg-card: #ffffff;
  --surface-soft: #f5f3ff;
  --accent-from: #7c3aed;
  --accent-to: #ec4899;
  --accent-warn: #fbbf24;
  --accent-warn-fg: #78350f;
  --accent-mute: #9ca3af;
  --text-strong: #1f1f2e;
  --text-muted: #6b7280;
  --ring-soft: rgba(124, 58, 237, 0.10);
  --shadow-card: 0 1px 3px rgba(0, 0, 0, .04), 0 8px 24px rgba(124, 58, 237, .08);
  --radius-card: 12px;
  --radius-pill: 999px;
  --font-sans: 'Inter', -apple-system, system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', 'SF Mono', monospace;
}

* { box-sizing: border-box; }

body {
  font-family: var(--font-sans);
  background: var(--bg-page);
  margin: 0;
  padding: 32px 24px;
  color: var(--text-strong);
  min-height: 100vh;
}

main {
  max-width: 880px;
  margin: 0 auto;
}

.report-header {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 24px;
}

.report-header .icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--accent-from), var(--accent-to));
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 700;
  font-size: 18px;
  flex-shrink: 0;
}

.report-header h1 {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.01em;
}

.report-header .subtitle {
  color: var(--text-muted);
  font-size: 13px;
  margin-top: 2px;
}

.toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
  align-items: center;
}

.toolbar button {
  background: var(--bg-card);
  border: 1px solid var(--ring-soft);
  border-radius: var(--radius-pill);
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
  cursor: pointer;
  font-family: inherit;
  transition: all 0.15s ease;
}

.toolbar button:hover {
  border-color: var(--accent-from);
  color: var(--accent-from);
}

.toolbar button.active {
  background: var(--accent-from);
  color: white;
  border-color: var(--accent-from);
}

.job-card,
.thread-card,
.event-card {
  background: var(--bg-card);
  border: 1px solid var(--ring-soft);
  border-radius: var(--radius-card);
  padding: 14px 18px;
  margin-bottom: 10px;
  box-shadow: var(--shadow-card);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.job-card:hover,
.thread-card:hover,
.event-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, .04), 0 12px 32px rgba(124, 58, 237, .12);
}

.job-card .header,
.thread-card .header,
.event-card .header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 6px;
}

.job-card .title,
.thread-card .title,
.event-card .title {
  font-weight: 700;
  font-size: 15px;
  color: var(--text-strong);
}

.job-card .meta,
.thread-card .meta,
.event-card .meta {
  color: var(--text-muted);
  font-size: 12px;
  margin-bottom: 10px;
}

.score-pill {
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: var(--radius-pill);
  flex-shrink: 0;
  white-space: nowrap;
}

.score-pill.tier-a {
  background: linear-gradient(135deg, var(--accent-from), var(--accent-to));
  color: white;
}

.score-pill.tier-b {
  background: var(--accent-warn);
  color: var(--accent-warn-fg);
}

.score-pill.tier-c {
  background: #e5e7eb;
  color: #4b5563;
}

.tag-chip {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  background: var(--surface-soft);
  color: var(--accent-from);
  padding: 2px 8px;
  border-radius: var(--radius-pill);
  margin-right: 4px;
  margin-bottom: 4px;
}

.tag-chip.accent {
  background: #fdf2f8;
  color: var(--accent-to);
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 10px;
  margin-bottom: 18px;
}

.metric-block {
  background: var(--bg-card);
  border: 1px solid var(--ring-soft);
  border-radius: var(--radius-card);
  padding: 14px 16px;
  box-shadow: var(--shadow-card);
}

.metric-block .label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--text-muted);
}

.metric-block .value {
  font-family: var(--font-mono);
  font-size: 24px;
  font-weight: 700;
  color: var(--text-strong);
  margin-top: 4px;
}

.metric-block .delta {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
  margin-top: 4px;
}

.metric-block .delta.up { color: #10b981; }
.metric-block .delta.down { color: #ef4444; }
.metric-block .delta.flat { color: var(--accent-mute); }

.timeline {
  border-left: 2px solid var(--ring-soft);
  margin-left: 12px;
  padding-left: 0;
}

.timeline-item {
  padding: 10px 0 10px 18px;
  margin-left: 0;
  position: relative;
}

.timeline-item::before {
  content: '';
  position: absolute;
  left: -7px;
  top: 16px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--accent-from);
  box-shadow: 0 0 0 3px var(--bg-card);
}

.timeline-item .meta {
  color: var(--text-muted);
  font-size: 12px;
  margin-bottom: 4px;
}

.fold {
  background: var(--bg-card);
  border: 1px solid var(--ring-soft);
  border-radius: var(--radius-card);
  margin-bottom: 8px;
  overflow: hidden;
  box-shadow: var(--shadow-card);
}

.fold .fold-header {
  padding: 12px 16px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  user-select: none;
  font-size: 14px;
}

.fold .fold-header:hover {
  background: var(--surface-soft);
}

.fold .chevron {
  transition: transform 0.2s ease;
  color: var(--accent-from);
  font-size: 18px;
  line-height: 1;
}

.fold.open .chevron {
  transform: rotate(90deg);
}

.fold .fold-body {
  display: none;
  padding: 0 16px 16px;
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-strong);
}

.fold.open .fold-body {
  display: block;
}

.empty-state {
  text-align: center;
  padding: 48px 24px;
  color: var(--text-muted);
}

.empty-state .icon {
  font-size: 32px;
  margin-bottom: 12px;
  opacity: 0.5;
}

.empty-state .title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-strong);
}

.empty-state .hint {
  font-size: 13px;
  margin-top: 6px;
}

.copy-btn {
  background: transparent;
  border: 1px solid var(--ring-soft);
  border-radius: 6px;
  padding: 4px 10px;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
  cursor: pointer;
  font-family: inherit;
  transition: all 0.15s ease;
}

.copy-btn:hover {
  border-color: var(--accent-from);
  color: var(--accent-from);
}

.copy-btn.copied {
  background: var(--accent-from);
  color: white;
  border-color: var(--accent-from);
}

footer {
  margin-top: 32px;
  text-align: center;
  font-size: 11px;
  color: var(--text-muted);
}

@media print {
  body {
    background: white;
    padding: 16px;
  }
  .toolbar, .copy-btn {
    display: none !important;
  }
  .job-card, .thread-card, .event-card, .fold, .metric-block {
    box-shadow: none !important;
    border: 1px solid #e5e7eb !important;
    page-break-inside: avoid;
  }
  .fold {
    page-break-inside: avoid;
  }
  .fold .fold-body {
    display: block !important;
  }
  .fold .chevron {
    display: none;
  }
  .report-header .icon {
    background: #7c3aed !important;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
  .score-pill.tier-a {
    background: #7c3aed !important;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
}
===FILE_END===

- [ ] **Step 3: Verify**

```bash
cd /Users/tura/git/claude-job-scout && wc -l skills/_visualizer/assets/theme.css
```
Expected: ~290 lines.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "^[[:space:]]*--" skills/_visualizer/assets/theme.css
```
Expected: at least `15` (token lines under `:root`).

```bash
cd /Users/tura/git/claude-job-scout && grep -c "@media print" skills/_visualizer/assets/theme.css
```
Expected: `1`.

```bash
cd /Users/tura/git/claude-job-scout && grep -cE "\.(score-pill|tag-chip|job-card|thread-card|event-card|metric-block|timeline-item|fold|empty-state|copy-btn|toolbar|report-header)" skills/_visualizer/assets/theme.css
```
Expected: at least `30`.

- [ ] **Step 4: Commit + push**

```bash
cd /Users/tura/git/claude-job-scout && git add skills/_visualizer/assets/theme.css && git commit -m "$(cat <<'EOF'
Add theme.css for Modern Cards aesthetic

Implements the full token set documented in
references/theme-tokens.md plus all component primitives from
references/component-library.md. Single CSS file inlined into
every rendered HTML report. Includes a print stylesheet that
removes hover effects, hides toolbars, and forces all folds
open for clean PDF output.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)" && git push -u origin phase-4/task-02-theme-css
```

---

## Task 3: interactive.js asset

**Files:**
- Create: `/Users/tura/git/claude-job-scout/skills/_visualizer/assets/interactive.js`

- [ ] **Step 1: Create branch**

```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-4/task-03-interactive-js
```

- [ ] **Step 2: Write `interactive.js`**

Create `/Users/tura/git/claude-job-scout/skills/_visualizer/assets/interactive.js` with exactly this content:

===FILE_START===
(function () {
  'use strict';

  // Sort handlers
  document.querySelectorAll('.toolbar [data-sort]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var key = btn.dataset.sort;
      var toolbar = btn.closest('.toolbar');
      var list = toolbar && toolbar.nextElementSibling;
      if (!list) return;
      var items = Array.prototype.slice.call(list.children).filter(function (el) {
        return el.dataset && (el.dataset.sortScore !== undefined || el.dataset['sort_' + key] !== undefined);
      });
      items.sort(function (a, b) {
        var av = a.dataset['sort_' + key] || '';
        var bv = b.dataset['sort_' + key] || '';
        if (key === 'score') {
          return (parseInt(bv, 10) || 0) - (parseInt(av, 10) || 0);
        }
        if (key === 'date') {
          return (new Date(bv)).getTime() - (new Date(av)).getTime();
        }
        return av.localeCompare(bv);
      });
      items.forEach(function (item) { list.appendChild(item); });
      toolbar.querySelectorAll('[data-sort]').forEach(function (b) { b.classList.remove('active'); });
      btn.classList.add('active');
    });
  });

  // Filter handlers (tier-based and unread-based)
  document.querySelectorAll('.toolbar [data-filter]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var filter = btn.dataset.filter;
      var attr = btn.dataset.filterAttr || 'tier';
      var toolbar = btn.closest('.toolbar');
      var list = toolbar && toolbar.nextElementSibling;
      if (!list) return;
      list.querySelectorAll('[data-' + attr + ']').forEach(function (item) {
        if (filter === 'all' || item.dataset[attr] === filter) {
          item.style.display = '';
        } else {
          item.style.display = 'none';
        }
      });
      toolbar.querySelectorAll('[data-filter][data-filter-attr="' + attr + '"], [data-filter]:not([data-filter-attr])').forEach(function (b) {
        if ((b.dataset.filterAttr || 'tier') === attr) b.classList.remove('active');
      });
      btn.classList.add('active');
    });
  });

  // Fold expand/collapse
  document.querySelectorAll('.fold .fold-header').forEach(function (header) {
    header.addEventListener('click', function () {
      header.parentElement.classList.toggle('open');
    });
  });

  // Mark-as-read (visual only — does not persist)
  document.querySelectorAll('[data-mark-read]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var targetId = btn.dataset.markRead;
      var target = document.getElementById(targetId);
      if (!target) return;
      target.classList.toggle('read');
      target.style.opacity = target.classList.contains('read') ? '0.55' : '';
    });
  });

  // Copy-to-clipboard
  document.querySelectorAll('.copy-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var targetId = btn.dataset.copyTarget;
      var target = document.getElementById(targetId);
      if (!target || !navigator.clipboard) return;
      var text = target.innerText || target.textContent || '';
      navigator.clipboard.writeText(text.trim()).then(function () {
        var orig = btn.textContent;
        btn.classList.add('copied');
        btn.textContent = 'Copied!';
        setTimeout(function () {
          btn.classList.remove('copied');
          btn.textContent = orig;
        }, 1500);
      }).catch(function () {
        btn.textContent = 'Copy failed';
        setTimeout(function () { btn.textContent = 'Copy'; }, 1500);
      });
    });
  });

  // Expose embedded data for any inline view-specific scripts
  var dataEl = document.getElementById('report-data');
  if (dataEl) {
    try {
      window.__REPORT_DATA__ = JSON.parse(dataEl.textContent);
    } catch (e) {
      window.__REPORT_DATA__ = null;
    }
  }
})();
===FILE_END===

- [ ] **Step 3: Verify**

```bash
cd /Users/tura/git/claude-job-scout && wc -l skills/_visualizer/assets/interactive.js
```
Expected: roughly 90 lines.

```bash
cd /Users/tura/git/claude-job-scout && node --check skills/_visualizer/assets/interactive.js && echo OK
```
Expected: `OK` (syntax-valid JS).

```bash
cd /Users/tura/git/claude-job-scout && grep -cE "data-(sort|filter|mark-read|copy-target)" skills/_visualizer/assets/interactive.js
```
Expected: at least `4`.

- [ ] **Step 4: Commit + push**

```bash
cd /Users/tura/git/claude-job-scout && git add skills/_visualizer/assets/interactive.js && git commit -m "$(cat <<'EOF'
Add interactive.js for report sort/filter/fold/copy

Vanilla JS, ~90 lines, IIFE-wrapped. Implements:
- Sort lists by score / date / company-name
- Filter lists by tier or unread status
- Fold expand/collapse via .fold-header click
- Mark-as-read visual toggle
- Copy-to-clipboard with 1.5s success indicator
- Exposes embedded JSON data as window.__REPORT_DATA__

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)" && git push -u origin phase-4/task-03-interactive-js
```

---

## Task 4: Base templates (HTML + markdown)

**Files:**
- Create: `/Users/tura/git/claude-job-scout/skills/_visualizer/templates/base.html.j2`
- Create: `/Users/tura/git/claude-job-scout/skills/_visualizer/templates/base.md.j2`

- [ ] **Step 1: Create branch**

```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-4/task-04-base-templates
```

- [ ] **Step 2: Write `base.html.j2`**

Create `/Users/tura/git/claude-job-scout/skills/_visualizer/templates/base.html.j2` with exactly this content:

===FILE_START===
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ data.title }} — linkedin-job-hunter</title>
<style>
{{ assets.theme_css | raw }}
</style>
</head>
<body>
<main>
{{ view_body | raw }}
<footer>Generated {{ data.generated_at }} · linkedin-job-hunter v{{ plugin_version }}</footer>
</main>
<script type="application/json" id="report-data">
{{ data | json }}
</script>
<script>
{{ assets.interactive_js | raw }}
</script>
</body>
</html>
===FILE_END===

- [ ] **Step 3: Write `base.md.j2`**

Create `/Users/tura/git/claude-job-scout/skills/_visualizer/templates/base.md.j2` with exactly this content:

===FILE_START===
{{ view_body | raw }}

---
_Generated {{ data.generated_at }} · linkedin-job-hunter v{{ plugin_version }}_
===FILE_END===

- [ ] **Step 4: Verify**

```bash
cd /Users/tura/git/claude-job-scout && cat skills/_visualizer/templates/base.html.j2 | head -3
```
Expected: starts with `<!DOCTYPE html>`.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "view_body" skills/_visualizer/templates/base.html.j2 skills/_visualizer/templates/base.md.j2
```
Expected: `2` (one match in each file).

```bash
cd /Users/tura/git/claude-job-scout && grep -c "report-data" skills/_visualizer/templates/base.html.j2
```
Expected: `1`.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "assets.theme_css\|assets.interactive_js" skills/_visualizer/templates/base.html.j2
```
Expected: `2`.

- [ ] **Step 5: Commit + push**

```bash
cd /Users/tura/git/claude-job-scout && git add skills/_visualizer/templates/base.html.j2 skills/_visualizer/templates/base.md.j2 && git commit -m "$(cat <<'EOF'
Add base.html.j2 and base.md.j2 frame templates

Both base templates wrap a {{ view_body }} placeholder filled by
the per-view template. The HTML base inlines theme.css and
interactive.js, embeds the rendered data as <script
type="application/json" id="report-data">, and renders a footer
with timestamp + plugin version. The markdown base appends a
trailing italic generation line.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)" && git push -u origin phase-4/task-04-base-templates
```

---

## Task 5: `_visualizer/SKILL.md` — full subagent contract

**Files:**
- Modify: `/Users/tura/git/claude-job-scout/skills/_visualizer/SKILL.md` (replace placeholder content)

- [ ] **Step 1: Create branch**

```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-4/task-05-visualizer-contract
```

- [ ] **Step 2: Replace `_visualizer/SKILL.md`**

Overwrite `/Users/tura/git/claude-job-scout/skills/_visualizer/SKILL.md` with exactly this content:

===FILE_START===
---
name: _visualizer
description: >
  [Internal subagent — dispatched only by Tier 1 user-facing commands, not user-invocable] Renders structured command output as a self-contained HTML report (Modern Cards aesthetic) or styled markdown. Writes the result to `.job-scout/reports/` and returns the path. Loaded via the `Agent` tool per `../shared-references/subagent-protocol.md`.
version: 1.0.0
---

# Visualizer (Subagent)

Render a structured command-output payload as either a self-contained HTML report or a styled-markdown body. The dispatching skill is one of the six Tier 1 user-facing commands (`match-jobs`, `job-search`, `check-job-notifications`, `funnel-report`, `check-inbox`, `interview-prep`); future Tier 2 work will add `analyze-cv`, `cover-letter`, and `optimize-profile`.

**This skill is dispatched only by other skills, via the `Agent` tool, per `../shared-references/subagent-protocol.md`.** It is not user-invocable.

## Input shape

The dispatcher passes a single JSON envelope as the prompt body:

```json
{
  "task": "render-report",
  "inputs": {
    "view": "match-jobs | job-search | check-job-notifications | funnel-report | check-inbox | interview-prep",
    "format": "html | markdown | plain",
    "data": { /* view-specific payload */ },
    "output_dir": "/abs/path/to/.job-scout/reports"
  },
  "budget_lines": 800,
  "allowed_tools": ["Read", "Write"]
}
```

The full contract — including the `data` shape per view — is in `references/rendering-protocol.md`.

## Output shape

```json
{
  "status": "ok | error",
  "deltas": [
    {
      "path": "/abs/path/to/file.html | null",
      "format": "html | markdown | plain",
      "bytes": 38421,
      "body": "<for markdown/plain only — the rendered string>"
    }
  ],
  "errors": [],
  "continuation_cursor": null
}
```

Exactly one delta per dispatch.

## Procedure

### Step 1: Validate inputs

Verify all four required keys are present in `inputs`: `view`, `format`, `data`, `output_dir`. If any is missing, return:

```json
{
  "status": "error",
  "deltas": [],
  "errors": [{ "code": "schema_mismatch", "message": "missing input: <key>" }],
  "continuation_cursor": null
}
```

`view` must be one of the six allowed values. `format` must be one of `html`, `markdown`, `plain`.

### Step 2: Resolve template path

For `format: "html"`:
- Template: `templates/html/<view>.html.j2`
- Base: `templates/base.html.j2`

For `format: "markdown"`:
- Template: `templates/markdown/<view>.md.j2`
- Base: `templates/base.md.j2`

For `format: "plain"`:
- No template. Subagent emits a flattened text dump of `inputs.data` as JSON-formatted text with 2-space indentation. Skip to Step 6.

If the view template file does not exist, return:

```json
{
  "status": "error",
  "deltas": [],
  "errors": [{ "code": "template_missing", "message": "no template at templates/<format>/<view>.<ext>.j2" }],
  "continuation_cursor": null
}
```

### Step 3: Run the schema check

Read the template file. Locate the schema-frontmatter block at the top:

```
{# schema:
   required:
     - data.foo
     - data.bar[].baz
#}
```

Parse the dotted paths under `required:`. For each path, walk `inputs.data` and verify the key exists at every level. Bracket suffix `[]` means the path requires a non-empty array at that segment.

If any required key is missing, return:

```json
{
  "status": "error",
  "deltas": [],
  "errors": [{ "code": "schema_mismatch", "message": "missing: <dotted.path>" }],
  "continuation_cursor": null
}
```

### Step 4: Render the view body

Expand the view template against `inputs.data` using the supported syntax surface from `references/rendering-protocol.md`:

- `{{ <dot.path> }}` — value substitution; HTML-escaped in `.html.j2`, raw in `.md.j2`.
- `{{ <dot.path> | raw }}` — substitution without escape (HTML only).
- `{{ <dot.path> | json }}` — JSON-stringified substitution.
- `{% for x in <dot.path> %} ... {% endfor %}` — iteration.
- `{% if <dot.path> %} ... {% endif %}` — conditional. Optional `{% else %}` branch.

Path resolution: dot-separated segments resolve left-to-right against `data`. Bracket-indexing (`data.results[0].score`) supports integer indices only. Missing keys at any depth resolve to empty string in `.html.j2`, empty string in `.md.j2` (templates use `{% if %}` to handle absence).

The result is the `view_body` string.

### Step 5: Render the base wrapper

For `format: "html"`:

1. Read `templates/base.html.j2`.
2. Read `assets/theme.css` and `assets/interactive.js`.
3. Build the substitution context:
   ```json
   {
     "view_body": "<rendered HTML from Step 4>",
     "data": <inputs.data>,
     "assets": {
       "theme_css": "<contents of assets/theme.css>",
       "interactive_js": "<contents of assets/interactive.js>"
     },
     "plugin_version": "<read from .claude-plugin/plugin.json>"
   }
   ```
4. Expand `base.html.j2` against this context using the same engine as Step 4.

For `format: "markdown"`:

1. Read `templates/base.md.j2`.
2. Build context with `view_body`, `data`, `plugin_version`. (No `assets`.)
3. Expand `base.md.j2`.

The result is the `final_body` string.

### Step 6: Write or return

For `format: "html"`:

1. Compose path: `<inputs.output_dir>/<inputs.data.filename>` (the dispatcher provides the filename — see render-orchestration.md).
2. Atomic write: write to `<path>.tmp`, then rename to `<path>`. If write fails, return:
   ```json
   { "status": "error", "deltas": [], "errors": [{ "code": "io_error", "message": "<reason>" }], "continuation_cursor": null }
   ```
3. Return:
   ```json
   {
     "status": "ok",
     "deltas": [{ "path": "<path>", "format": "html", "bytes": <byte count> }],
     "errors": [],
     "continuation_cursor": null
   }
   ```

For `format: "markdown"` or `"plain"`:

Return the body in `delta.body` instead of writing a file:

```json
{
  "status": "ok",
  "deltas": [{ "path": null, "format": "markdown", "bytes": <byte count>, "body": "<final_body>" }],
  "errors": [],
  "continuation_cursor": null
}
```

### Step 7: Budget check

If at any point during Steps 4–6 the rendered output exceeds `budget_lines * 100` characters (a rough char-per-line estimate), abort and return:

```json
{ "status": "error", "deltas": [], "errors": [{ "code": "budget_exceeded", "message": "output > budget_lines" }], "continuation_cursor": null }
```

The dispatcher's fallback chain handles the error.

## Reference Materials

- **`references/rendering-protocol.md`** — full subagent contract, templating engine surface, error codes.
- **`references/theme-tokens.md`** — Modern Cards color/geometry/type tokens.
- **`references/component-library.md`** — HTML class primitives templates compose.
- **`../shared-references/subagent-protocol.md`** — universal subagent dispatch rules (idempotency, fan-in merge, allowed tools).

## Not user-invocable

This skill has no user-facing slash command. It is dispatched only via the `Agent` tool by the six Tier 1 commands. The dispatching skill always passes a self-contained JSON envelope.
===FILE_END===

- [ ] **Step 3: Verify**

```bash
cd /Users/tura/git/claude-job-scout && wc -l skills/_visualizer/SKILL.md
```
Expected: roughly 145–165 lines.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "version: 1.0.0" skills/_visualizer/SKILL.md
```
Expected: `1`.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "render-report\|schema_mismatch\|template_missing\|budget_exceeded\|io_error" skills/_visualizer/SKILL.md
```
Expected: at least `5`.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "Not user-invocable" skills/_visualizer/SKILL.md
```
Expected: `1`.

- [ ] **Step 4: Commit + push**

```bash
cd /Users/tura/git/claude-job-scout && git add skills/_visualizer/SKILL.md && git commit -m "$(cat <<'EOF'
Fill in _visualizer subagent contract

Replaces the Task 1 placeholder with the full procedure: input
validation, template-path resolution, schema check via {# schema:
#} frontmatter, view-body rendering, base-wrapper rendering with
inlined assets, atomic file write for HTML or in-band body return
for markdown, and budget enforcement. Bumps version to 1.0.0
because the contract is now stable.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)" && git push -u origin phase-4/task-05-visualizer-contract
```

---

## Task 6: `match-jobs` templates (HTML + markdown)

**Files:**
- Create: `/Users/tura/git/claude-job-scout/skills/_visualizer/templates/html/match-jobs.html.j2`
- Create: `/Users/tura/git/claude-job-scout/skills/_visualizer/templates/markdown/match-jobs.md.j2`

- [ ] **Step 1: Create branch**

```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-4/task-06-match-jobs-templates
```

- [ ] **Step 2: Write `html/match-jobs.html.j2`**

Create `/Users/tura/git/claude-job-scout/skills/_visualizer/templates/html/match-jobs.html.j2` with exactly this content:

===FILE_START===
{# schema:
   required:
     - data.title
     - data.subtitle
     - data.generated_at
     - data.filename
     - data.tier_counts
     - data.results
#}
<header class="report-header">
  <div class="icon">★</div>
  <div>
    <h1>{{ data.title }}</h1>
    <div class="subtitle">{{ data.subtitle }}</div>
  </div>
</header>

{% if data.results %}
<div class="toolbar">
  <button data-sort="score" class="active">Score ↓</button>
  <button data-sort="date">Date ↓</button>
  <button data-sort="company">Company A–Z</button>
  <span style="flex:1"></span>
  <button data-filter="all" data-filter-attr="tier" class="active">All ({{ data.tier_counts.total }})</button>
  <button data-filter="a" data-filter-attr="tier">A-tier ({{ data.tier_counts.a }})</button>
  <button data-filter="b" data-filter-attr="tier">B-tier ({{ data.tier_counts.b }})</button>
  <button data-filter="c" data-filter-attr="tier">C-tier ({{ data.tier_counts.c }})</button>
</div>

<section>
{% for job in data.results %}
  <article class="job-card" data-tier="{{ job.tier }}" data-sort_score="{{ job.score }}" data-sort_date="{{ job.posted_at }}" data-sort_company="{{ job.company }}">
    <div class="header">
      <div class="title">{{ job.title }}</div>
      <div class="score-pill tier-{{ job.tier }}">{{ job.score }}</div>
    </div>
    <div class="meta">{{ job.company }} · {{ job.location }}{% if job.salary %} · {{ job.salary }}{% endif %}{% if job.posted_at %} · {{ job.posted_at }}{% endif %}</div>
    {% if job.tags %}
    <div>
      {% for tag in job.tags %}<span class="tag-chip">{{ tag }}</span>{% endfor %}
    </div>
    {% endif %}
    {% if job.rationale %}
    <div style="font-size:13px;color:var(--text-strong);margin-top:8px;line-height:1.5">{{ job.rationale }}</div>
    {% endif %}
  </article>
{% endfor %}
</section>
{% else %}
<div class="empty-state">
  <div class="icon">🌱</div>
  <div class="title">No matching jobs found.</div>
  <div class="hint">Try refining your search filters or running again later.</div>
</div>
{% endif %}
===FILE_END===

- [ ] **Step 3: Write `markdown/match-jobs.md.j2`**

Create `/Users/tura/git/claude-job-scout/skills/_visualizer/templates/markdown/match-jobs.md.j2` with exactly this content:

===FILE_START===
{# schema:
   required:
     - data.title
     - data.subtitle
     - data.generated_at
     - data.tier_counts
     - data.results
#}
## {{ data.title }}

_{{ data.subtitle }}_

{% if data.results %}
| Tier | Score | Title | Company | Location | Salary |
|------|------:|-------|---------|----------|--------|
{% for job in data.results %}| {% if job.tier %}{% if job.tier == "a" %}🟢 A{% endif %}{% if job.tier == "b" %}🟡 B{% endif %}{% if job.tier == "c" %}⚪ C{% endif %}{% endif %} | **{{ job.score }}** | {{ job.title }} | {{ job.company }} | {{ job.location }} | {% if job.salary %}{{ job.salary }}{% endif %} |
{% endfor %}

**Tier counts:** A: {{ data.tier_counts.a }} · B: {{ data.tier_counts.b }} · C: {{ data.tier_counts.c }} · Total: {{ data.tier_counts.total }}

{% for job in data.results %}{% if job.rationale %}
### {% if job.tier == "a" %}🟢{% endif %}{% if job.tier == "b" %}🟡{% endif %}{% if job.tier == "c" %}⚪{% endif %} {{ job.title }} · {{ job.company }} ({{ job.score }})

{{ job.rationale }}
{% endif %}{% endfor %}

{% else %}
🌱 **No matching jobs found.** Try refining your search filters or running again later.
{% endif %}
===FILE_END===

- [ ] **Step 4: Verify**

```bash
cd /Users/tura/git/claude-job-scout && wc -l skills/_visualizer/templates/html/match-jobs.html.j2 skills/_visualizer/templates/markdown/match-jobs.md.j2
```
Expected: HTML ~38 lines; markdown ~22 lines.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "{# schema:" skills/_visualizer/templates/html/match-jobs.html.j2 skills/_visualizer/templates/markdown/match-jobs.md.j2
```
Expected: `2` (one match per file).

```bash
cd /Users/tura/git/claude-job-scout && grep -c "score-pill\|tag-chip\|job-card" skills/_visualizer/templates/html/match-jobs.html.j2
```
Expected: at least `4`.

- [ ] **Step 5: Commit + push**

```bash
cd /Users/tura/git/claude-job-scout && git add skills/_visualizer/templates/html/match-jobs.html.j2 skills/_visualizer/templates/markdown/match-jobs.md.j2 && git commit -m "$(cat <<'EOF'
Add match-jobs HTML and markdown templates

HTML template renders a sortable/filterable list of .job-card
items with score pills, tag chips, and optional per-job
rationales. Toolbar exposes sort by score/date/company and
filter by tier. Markdown template renders a sortable table
plus per-A/B-tier rationale sections, using emoji as tier
indicators (🟢/🟡/⚪).

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)" && git push -u origin phase-4/task-06-match-jobs-templates
```

---

## Task 7: `render-orchestration.md` shared reference

**Files:**
- Create: `/Users/tura/git/claude-job-scout/skills/shared-references/render-orchestration.md`

- [ ] **Step 1: Create branch**

```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-4/task-07-render-orchestration
```

- [ ] **Step 2: Write `render-orchestration.md`**

Create `/Users/tura/git/claude-job-scout/skills/shared-references/render-orchestration.md` with exactly this content:

===FILE_START===
# Render Orchestration

The procedure every Tier 1 user-facing command follows after computing its output, when the user has opted in to HTML rendering. Centralised here because all six Tier 1 commands implement the identical lifecycle: build a payload → consult `render` config → maybe dispatch `_visualizer` → maybe open in Chrome → handle failure → print terminal summary.

## When to invoke

At the **end** of a Tier 1 command, after the command has computed its results and would otherwise print the terminal output. The procedure replaces (or augments, depending on render mode) that final print.

## Step A: Build the data payload

The dispatching skill builds a `data` object whose shape matches the requirements declared in `_visualizer/templates/html/<view>.html.j2`'s `{# schema: #}` frontmatter. Every payload includes these universal fields, plus view-specific fields:

```json
{
  "title": "<short hero title — see per-view rules below>",
  "subtitle": "<one-line subtitle>",
  "generated_at": "2026-04-29 14:30",
  "filename": "<view>-latest.html | <view>-2026-04-29-1430.html",
  "tier_counts": { "a": 0, "b": 0, "c": 0, "total": 0 },
  "results": [ /* view-specific items */ ]
}
```

### Filename rules

| View | Filename pattern |
|------|------------------|
| `match-jobs` | `match-jobs-latest.html` |
| `job-search` | `job-search-latest.html` |
| `check-job-notifications` | `check-job-notifications-latest.html` |
| `check-inbox` | `check-inbox-latest.html` |
| `funnel-report` | `funnel-report-<YYYY-MM-DD-HHMM>.html` |
| `interview-prep` | `interview-prep-<role-slug>-<YYYY-MM-DD-HHMM>.html` |

For `interview-prep`: `<role-slug>` is `<tracker-id>-<4-char-disambiguator>`. The disambiguator is the first 4 characters of the SHA-1 hash of the input role title — keeps filenames distinct even when re-running prep on the same tracker entry.

### Tier classification (used by views with scored items)

The dispatcher classifies before passing to `_visualizer`:
- `score >= 80` → `"a"`
- `60 <= score < 80` → `"b"`
- `score < 60` → `"c"`

## Step B: Read the render config

Load `.job-scout/config.json`. Treat a missing file as an empty object.

- If the `render` key is **absent**, run **Step B1: First-run prompt** below.
- If `render: "always"`, set `mode = "html"` and continue to Step C.
- If `render: "never"`, set `mode = "markdown"` and continue to Step C.
- If `render: "ask"`, run **Step B2: Per-invocation prompt** below.

### Step B1: First-run prompt

The user has never set a render preference. Print exactly this prompt to the conversation and wait for input:

```
How should command output be displayed?

  always  — Render as a styled HTML report and auto-open in Chrome.
            Best experience. Higher token cost per command (≈ <measured>
            extra tokens per render for the visualizer subagent).
  never   — Show output as styled markdown directly in this window.
            Lower token cost. No browser hop.
  ask     — Decide per-command at the end of each run.

Choice [always]: 
```

The `<measured>` placeholder is replaced by the canonical figure from `docs/superpowers/specs/2026-04-29-visual-render-layer-design.md` Section 7's "Token cost reference" subsection (filled by Task 11 of the implementation plan).

Map the user's response:
- empty / "always" / "a" → `"always"`
- "never" / "n" → `"never"`
- "ask" → `"ask"`
- anything else → re-prompt once; on second invalid input, default to `"always"` and warn.

Write the chosen value to `.job-scout/config.json` under the `render` key. If the file did not exist, create it with `{}` first then write the key. Preserve any other keys (e.g., `render_retention_days`, `render_archive_days`).

Use the chosen value to set `mode` for this run (e.g., `"always"` → `mode = "html"`).

### Step B2: Per-invocation prompt

User has `render: "ask"` set. After the command's core work is done, print:

```
Render this report as HTML in Chrome? (y/N)
  y = styled HTML in Chrome (≈ <measured> extra tokens)
  N = styled markdown in this window
```

Map: `y` / `Y` → `mode = "html"`; anything else → `mode = "markdown"`.

## Step C: Dispatch `_visualizer`

If `mode = "html"`:

```
Dispatch _visualizer with envelope:
{
  "task": "render-report",
  "inputs": {
    "view": "<view>",
    "format": "html",
    "data": <payload from Step A>,
    "output_dir": "<absolute path to .job-scout/reports>"
  },
  "budget_lines": 800,
  "allowed_tools": ["Read", "Write"]
}
```

If `mode = "markdown"`: same envelope, `format: "markdown"`.

The dispatch follows `subagent-protocol.md`. Parse the JSON response.

## Step D: Handle the response

### Success, format=html

Subagent returned `status: "ok"` with a `path` delta.

1. Call the Chrome extension's "navigate to URL" tool with `file://<path>`.
2. **If Chrome opens successfully**, print the terminal summary (Step E) and return.
3. **If Chrome fails to open**, fall through to Step F: ask-and-fallback.

### Success, format=markdown

Subagent returned `status: "ok"` with a `body` delta. Print `body` directly to the conversation (it is already formatted as Markdown). Then print the terminal summary (Step E) and return.

### Error from subagent

Subagent returned `status: "error"`. Fall through to Step F: ask-and-fallback.

## Step E: Terminal summary

A 2–3 line summary printed even when HTML rendering succeeds. Format depends on view:

| View | Summary line |
|------|--------------|
| `match-jobs` | `✓ {{N}} matches scored — A:{{a}} B:{{b}} C:{{c}} — opened report in Chrome` (or `…rendered as markdown above`) |
| `job-search` | `✓ {{N}} jobs surfaced — A:{{a}} B:{{b}} — opened report in Chrome` |
| `check-job-notifications` | `✓ {{N}} notifications — {{unread}} unread — opened report in Chrome` |
| `funnel-report` | `✓ Pipeline snapshot for week of {{date}} — opened report in Chrome` |
| `check-inbox` | `✓ {{N}} threads — {{unread}} unread — opened report in Chrome` |
| `interview-prep` | `✓ Prep dossier for {{role}} at {{company}} — opened report in Chrome` |

When falling back to markdown, replace the trailing clause with `— rendered above`.

## Step F: Ask-and-fallback

The HTML render or open failed. Print exactly this prompt:

```
⚠ Couldn't open in Chrome (<reason>).
Show output here as text instead? (Y/n)
```

Where `<reason>` is the subagent's `errors[0].message` if available, otherwise `extension unavailable`.

Map response:
- empty / `Y` / `y` → re-dispatch `_visualizer` with `format: "markdown"` and same `data`. Print the returned `body`. Append `(HTML written to <path> if you'd like to open it manually)` if a path was successfully written before the open failed.
- `n` / `N` → print `Open manually: <path>` if a path was successfully written. If no path was written, print `Render failed; no file produced.` Then return.

If the markdown re-dispatch itself fails, dispatch one more time with `format: "plain"` and print the resulting body. The plain path is the last-resort safety net and never fails (worst case is a JSON dump).

Append the original error to `.job-scout/cache/visualizer-errors.log` as a single line:

```
2026-04-29T14:30:01Z view=match-jobs format=html error=schema_mismatch detail="missing: data.results[].score"
```

Trim that file to the last 50 lines after each append.

## Step G: Lifecycle cleanup (run once at the start of each Tier 1 command)

Before doing any work, clean up old reports. This is cheap (a directory scan) and keeps disk usage bounded.

1. Read `.job-scout/config.json`. Use `render_retention_days` (default 90) and `render_archive_days` (default 365).
2. List files in `.job-scout/reports/` matching `<view>-<timestamp>.html` for time-series views (`funnel-report`, `interview-prep`).
3. Any such file with mtime older than `render_retention_days` ago: move to `.job-scout/reports/archive/`.
4. List files in `.job-scout/reports/archive/`. Any with mtime older than `render_archive_days` ago: delete.
5. Snapshot views (`-latest.html`) are never archived or deleted by this cleanup; they are overwritten by each run.

If `.job-scout/reports/archive/` does not exist, create it before step 3.

## Fallback when the `Agent` tool is unavailable

If the dispatching session does not have access to the `Agent` tool (per `subagent-protocol.md`'s "fall back to sequential in-thread execution" clause), the command does not invoke this orchestration. Instead it falls back to its pre-v0.7.0 terminal-only output. Log the fallback once per session.

## Reference Materials

- **`subagent-protocol.md`** — universal subagent dispatch rules.
- **`workspace-layout.md`** — `.job-scout/` directory layout including `reports/` and `config.json`.
- **`browser-policy.md`** — the Chrome extension is the only browser path; never request computer use.
- **`../_visualizer/SKILL.md`** — subagent contract.
- **`../_visualizer/references/rendering-protocol.md`** — full rendering protocol.
===FILE_END===

- [ ] **Step 3: Verify**

```bash
cd /Users/tura/git/claude-job-scout && wc -l skills/shared-references/render-orchestration.md
```
Expected: roughly 175–195 lines.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "Step [A-G]:" skills/shared-references/render-orchestration.md
```
Expected: at least `7` (Steps A–G).

```bash
cd /Users/tura/git/claude-job-scout && grep -c "render-report\|render: \"always\"\|render: \"never\"\|render: \"ask\"" skills/shared-references/render-orchestration.md
```
Expected: at least `4`.

- [ ] **Step 4: Commit + push**

```bash
cd /Users/tura/git/claude-job-scout && git add skills/shared-references/render-orchestration.md && git commit -m "$(cat <<'EOF'
Add render-orchestration shared reference

Centralises the procedure every Tier 1 command follows when
emitting output: build payload, read render config, fire
first-run or per-invocation prompt as appropriate, dispatch
_visualizer, open in Chrome, handle failure (ask-and-fallback
chain), print terminal summary, run lifecycle cleanup. Each
Tier 1 SKILL.md will reference this file in its render step
rather than duplicating the procedure.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)" && git push -u origin phase-4/task-07-render-orchestration
```

---

## Task 8: Schema migration 0.6 → 0.7

**Files:**
- Modify: `/Users/tura/git/claude-job-scout/skills/shared-references/workspace-layout.md`

- [ ] **Step 1: Create branch**

```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-4/task-08-schema-migration
```

- [ ] **Step 2: Read current migration section**

```bash
cd /Users/tura/git/claude-job-scout && grep -n "schema-version\|migration" skills/shared-references/workspace-layout.md | head -20
```

Find the existing migration runner section. The Phase 1 migration scaffolding is in this file. Identify the location where new migrations are appended (typically a section heading like "## Migrations" or a list of version transitions).

- [ ] **Step 3: Append the 0.6 → 0.7 migration**

Find the migrations list / section in `workspace-layout.md` and append a new subsection at the end of the migration list (before any closing "Reference Materials" section if one exists). The exact append text is:

```markdown

### 0.6 → 0.7 (visual render layer)

Triggered when `.job-scout/schema-version` reads `0.6` and the running plugin is v0.7.0 or later.

1. **Add config keys for retention** (idempotent — only adds missing keys, preserves existing values):
   - If `.job-scout/config.json` does not exist, create it with `{}`.
   - If the file is missing the key `render_retention_days`, add it with value `90`.
   - If the file is missing the key `render_archive_days`, add it with value `365`.
   - **Do not** add the `render` key. Its absence is the signal that the first-run prompt (see `render-orchestration.md` Step B1) has not yet fired; the prompt sets the key on first user answer.

2. **Create reports directories** (idempotent):
   - Create `.job-scout/reports/` if missing.
   - Create `.job-scout/reports/archive/` if missing.

3. **Bump schema version**:
   - Write `0.7` to `.job-scout/schema-version`.

This migration is safe to run repeatedly — every step is idempotent.
```

- [ ] **Step 4: Verify**

```bash
cd /Users/tura/git/claude-job-scout && grep -c "0.6 → 0.7" skills/shared-references/workspace-layout.md
```
Expected: `1`.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "render_retention_days\|render_archive_days" skills/shared-references/workspace-layout.md
```
Expected: at least `2`.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "Do not\*\* add the \`render\` key" skills/shared-references/workspace-layout.md
```
Expected: `1`.

```bash
cd /Users/tura/git/claude-job-scout && git diff --stat
```
Expected: 1 file changed.

- [ ] **Step 5: Commit + push**

```bash
cd /Users/tura/git/claude-job-scout && git add skills/shared-references/workspace-layout.md && git commit -m "$(cat <<'EOF'
Add 0.6 → 0.7 schema migration

Extends the Phase 1 migration scaffolding with the v0.7.0
transition: adds render_retention_days (90) and render_archive_days
(365) to config.json if missing, creates .job-scout/reports/ and
.job-scout/reports/archive/, bumps schema-version to 0.7.
Deliberately does not add the `render` key — its absence is the
signal that the first-run prompt should fire.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)" && git push -u origin phase-4/task-08-schema-migration
```

---

## Task 9: `/config` slash command

**Files:**
- Create: `/Users/tura/git/claude-job-scout/skills/config/SKILL.md`

- [ ] **Step 1: Create branch + dir**

```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-4/task-09-config-command && mkdir -p skills/config
```

- [ ] **Step 2: Write `config/SKILL.md`**

Create `/Users/tura/git/claude-job-scout/skills/config/SKILL.md` with exactly this content:

===FILE_START===
---
name: config
description: View or change per-workspace plugin settings under .job-scout/config.json
allowed-tools: Read, Write, Edit, Bash
disable-model-invocation: true
version: 0.1.0
---

View or change per-workspace plugin settings stored in `.job-scout/config.json`. v0.7.0 exposes a single user-facing setting via this command: `render` (controls how Tier 1 command output is displayed).

## Step 0: Bootstrap workspace

Follow `shared-references/workspace-layout.md` to ensure `.job-scout/` exists.

## Step 1: Parse the invocation

The user types one of these forms:

```
/config
/config render
/config render <always|never|ask>
```

- `/config` (no args) — show all current settings.
- `/config render` — show the current value of `render`.
- `/config render <value>` — set `render` to the given value.

## Step 2: Show current settings (no-arg invocation)

Read `.job-scout/config.json` (treat missing as `{}`). Print:

```
Current settings (.job-scout/config.json):

  render               = <value or "(unset — first-run prompt will fire on next Tier 1 command)">
  render_retention_days = <value, default 90>
  render_archive_days  = <value, default 365>
```

Then exit.

## Step 3: Show the render value (`/config render`)

Read `.job-scout/config.json`. If `render` is set, print:

```
render = "<value>"
```

If unset, print:

```
render is not set. The first-run prompt will fire on the next Tier 1 command.
Set explicitly with: /config render <always|never|ask>
```

Then exit.

## Step 4: Set the render value (`/config render <value>`)

Validate that `<value>` is one of: `always`, `never`, `ask`. If not, print:

```
Invalid value. Allowed: always, never, ask.
```

and exit without modifying the file.

If valid:
1. Read `.job-scout/config.json` (treat missing as `{}`).
2. Set `render: "<value>"`.
3. Write back. Preserve any other keys.
4. Confirm:

```
Set render = "<value>"
```

## Step 5: Validate the file is well-formed JSON after write

Re-read `.job-scout/config.json` and parse. If parsing fails, restore from backup or report the failure path and exit non-zero.

## Reference Materials

- **`shared-references/workspace-layout.md`** — `.job-scout/` layout and bootstrap procedure.
- **`shared-references/render-orchestration.md`** — describes how the `render` key is consumed by Tier 1 commands.
===FILE_END===

- [ ] **Step 3: Verify**

```bash
cd /Users/tura/git/claude-job-scout && wc -l skills/config/SKILL.md
```
Expected: roughly 70–85 lines.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "disable-model-invocation: true" skills/config/SKILL.md
```
Expected: `1`.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "always\|never\|ask" skills/config/SKILL.md
```
Expected: at least `4`.

- [ ] **Step 4: Commit + push**

```bash
cd /Users/tura/git/claude-job-scout && git add skills/config/ && git commit -m "$(cat <<'EOF'
Add /config slash command

User-facing helper for viewing and changing per-workspace
settings in .job-scout/config.json. v0.7.0 only exposes the
render key (always|never|ask). Carries disable-model-invocation
per the plugin's hard rule for slash commands. Future config
keys can be added without changing the dispatch shape.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)" && git push -u origin phase-4/task-09-config-command
```

---

## Task 10: Wire `/match-jobs` to the render orchestration

**Files:**
- Modify: `/Users/tura/git/claude-job-scout/skills/match-jobs/SKILL.md`

- [ ] **Step 1: Create branch**

```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-4/task-10-wire-match-jobs
```

- [ ] **Step 2: Read current `match-jobs/SKILL.md`**

```bash
cd /Users/tura/git/claude-job-scout && cat skills/match-jobs/SKILL.md
```

Note that the file currently ends with a `## Next Steps` section after `## Step 5: Present Results`. The render step is inserted between Step 5 and `## Next Steps` as a new `## Step 6: Render`.

- [ ] **Step 3: Insert render step**

Edit `skills/match-jobs/SKILL.md`. Find this exact block (around the bottom of Step 5):

```
## Step 5: Present Results

Show ranked markdown table (title, company, score, tier, Easy Apply, posted, applicants). For A-Tier and top B-Tier, provide detailed match cards with score breakdown, matched skills, gaps, and red flags. Keep B/C tiers as compact rows — no paragraph rationales.

Merge newly scored jobs into `.job-scout/tracker.json` with status "seen".

## Next Steps
```

Replace with:

```
## Step 5: Build results payload

Construct a `data` payload for the render layer. Tier classification: `score >= 80` → `"a"`, `60 <= score < 80` → `"b"`, `score < 60` → `"c"`.

```json
{
  "title": "{{N}} matches today",
  "subtitle": "Top score: {{top_score}} · A-tier: {{a_count}} · B-tier: {{b_count}}",
  "generated_at": "<YYYY-MM-DD HH:MM>",
  "filename": "match-jobs-latest.html",
  "tier_counts": { "a": <a_count>, "b": <b_count>, "c": <c_count>, "total": <total> },
  "results": [
    {
      "title": "<job title>",
      "company": "<company>",
      "location": "<location>",
      "salary": "<salary or empty string>",
      "posted_at": "<YYYY-MM-DD>",
      "score": <integer>,
      "tier": "a | b | c",
      "tags": ["<tag1>", "<tag2>"],
      "rationale": "<one-paragraph rationale for A-tier and top B-tier; empty string otherwise>"
    }
  ]
}
```

`tags` should be drawn from the matched skills / signals already computed during scoring. Limit to 5 tags per job.

Merge newly scored jobs into `.job-scout/tracker.json` with status "seen".

## Step 6: Render

Follow `../shared-references/render-orchestration.md` end-to-end:

1. Step G first — clean up old reports under `.job-scout/reports/`.
2. Step A — payload built in Step 5 above.
3. Steps B–F — read render config, dispatch `_visualizer`, open in Chrome (or fall back), handle errors.
4. Step E — print the `match-jobs` summary line.

If the `Agent` tool is unavailable, fall back to the pre-v0.7.0 markdown table output described in the original Step 5.

## Next Steps
```

- [ ] **Step 4: Bump skill version**

Find this line in the frontmatter of `skills/match-jobs/SKILL.md`:

```
---
name: match-jobs
description: Score and rank job listings against your CV and requirements
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
disable-model-invocation: true
---
```

Add a `version: 0.2.0` line to the frontmatter:

```
---
name: match-jobs
description: Score and rank job listings against your CV and requirements
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
disable-model-invocation: true
version: 0.2.0
---
```

(If the file already has a `version:` field, change it to `0.2.0`.)

- [ ] **Step 5: Verify**

```bash
cd /Users/tura/git/claude-job-scout && grep -c "## Step 6: Render" skills/match-jobs/SKILL.md
```
Expected: `1`.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "render-orchestration.md" skills/match-jobs/SKILL.md
```
Expected: `1`.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "version: 0.2.0" skills/match-jobs/SKILL.md
```
Expected: `1`.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "match-jobs-latest.html" skills/match-jobs/SKILL.md
```
Expected: `1`.

- [ ] **Step 6: Commit + push**

```bash
cd /Users/tura/git/claude-job-scout && git add skills/match-jobs/SKILL.md && git commit -m "$(cat <<'EOF'
Wire /match-jobs to the visual render layer

Adds Step 5 (build results payload) and Step 6 (render via
shared-references/render-orchestration.md). Tier classification
moves into the orchestrator. Falls back to the pre-v0.7.0
markdown-table output if the Agent tool is unavailable. Bumps
skill version to 0.2.0 because the contract now produces an
HTML report in addition to terminal output.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)" && git push -u origin phase-4/task-10-wire-match-jobs
```

---

## Task 11: End-to-end smoke + token measurement (`/match-jobs` slice)

**Files:**
- Modify: `/Users/tura/git/claude-job-scout/docs/superpowers/specs/2026-04-29-visual-render-layer-design.md`

- [ ] **Step 1: Create branch**

```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-4/task-11-smoke-and-measure
```

- [ ] **Step 2: Set up a scratch workspace**

```bash
mkdir -p /tmp/job-scout-smoke && cd /tmp/job-scout-smoke && rm -rf .job-scout && mkdir -p .job-scout/cache && echo '0.6' > .job-scout/schema-version && cat > .job-scout/cv.json <<'EOF'
{ "summary": "Senior backend engineer with 10 years of payments and Go experience.", "skills": ["Go", "Postgres", "Kafka", "Stripe API", "Kubernetes"], "cv_hash": "smoketest-cv" }
EOF
cat > .job-scout/cache/seed-jobs.json <<'EOF'
{ "jobs": [
  { "id": "J1", "title": "Senior Backend Engineer", "company": "Stripe", "location": "Remote", "salary": "€180k-220k", "posted_at": "2026-04-28", "description": "Go, Payments, Stripe API, Postgres", "easy_apply": false },
  { "id": "J2", "title": "Staff Software Engineer", "company": "Linear", "location": "Remote", "salary": "", "posted_at": "2026-04-27", "description": "TypeScript, Postgres, distributed systems", "easy_apply": true },
  { "id": "J3", "title": "Engineering Manager", "company": "Notion", "location": "SF or remote", "salary": "$240k-280k", "posted_at": "2026-04-26", "description": "Lead a team of 6, hiring, mentorship", "easy_apply": false },
  { "id": "J4", "title": "Backend Lead", "company": "Vercel", "location": "Remote", "salary": "", "posted_at": "2026-04-25", "description": "Go, Kubernetes, edge computing", "easy_apply": true }
] }
EOF
```

- [ ] **Step 3: Run `/match-jobs` against the seed data**

Open a Claude Code session in `/tmp/job-scout-smoke`. Trigger the v0.7.0 plugin's `/match-jobs` command pointed at `.job-scout/cache/seed-jobs.json` as the input source. (The exact mechanism depends on how `/match-jobs` discovers seed inputs — load the existing skill and follow its prompts.)

Expected behaviour:
1. Schema migration runs first (0.6 → 0.7); creates `.job-scout/reports/` and `.job-scout/reports/archive/`.
2. First-run prompt fires asking how to display output.
3. Choose `always`. The orchestrator writes `render: "always"` to `.job-scout/config.json`.
4. `_visualizer` is dispatched with `format: "html"`.
5. `.job-scout/reports/match-jobs-latest.html` is written.
6. Chrome opens the file (or fallback fires).
7. Terminal prints the summary line.

- [ ] **Step 4: Shell-level verification**

```bash
cd /tmp/job-scout-smoke && test -s .job-scout/reports/match-jobs-latest.html && echo OK
```
Expected: `OK`.

```bash
cd /tmp/job-scout-smoke && ! grep -E '<link[^>]+href|<script[^>]+src' .job-scout/reports/match-jobs-latest.html && echo OK
```
Expected: `OK` (file is self-contained — no external links).

```bash
cd /tmp/job-scout-smoke && sed -n '/<script type="application\/json"/,/<\/script>/p' .job-scout/reports/match-jobs-latest.html | sed '1d;$d' | jq -e .
```
Expected: valid JSON output (the embedded `report-data` block).

```bash
cd /tmp/job-scout-smoke && grep -c "Generated 20" .job-scout/reports/match-jobs-latest.html
```
Expected: `1`.

```bash
cd /tmp/job-scout-smoke && cat .job-scout/config.json | jq -r '.render'
```
Expected: `always`.

```bash
cd /tmp/job-scout-smoke && cat .job-scout/schema-version
```
Expected: `0.7`.

- [ ] **Step 5: Visual verification (manual)**

Open `.job-scout/reports/match-jobs-latest.html` in Chrome. Confirm:
- Hero header reads "4 matches today" (or similar).
- A-tier jobs have violet-pink gradient pills; B-tier are amber; C-tier are gray.
- Sort buttons (Score / Date / Company) reorder the cards.
- Filter buttons (All / A / B / C) hide / show cards.
- Hover state lifts cards slightly.
- Footer shows generation timestamp + plugin version.

If anything fails: the issue is in Tasks 2–6 (`theme.css`, `interactive.js`, base templates, or the `match-jobs` template). Fix on a follow-up branch before continuing.

- [ ] **Step 6: Capture token measurements**

The subagent protocol's response includes input + output token counts (a metadata field on every `Agent` dispatch). Capture both for this run.

For typical 4-job payload (the seed data):
- Input tokens: `<INPUT_SMALL>`
- Output tokens: `<OUTPUT_SMALL>`

For a larger 50-job payload (synthesise by replicating the seed jobs 12 times with disambiguating IDs):
- Input tokens: `<INPUT_LARGE>`
- Output tokens: `<OUTPUT_LARGE>`

Compute the range. Round to nearest 100. Example outcome: "≈ 1.5–3.2k extra tokens per render".

- [ ] **Step 7: Update the spec with measurements**

Edit `docs/superpowers/specs/2026-04-29-visual-render-layer-design.md`. Find this exact passage in Section 2 (twice — once in the first-run prompt, once in the ask-mode prompt):

```
            Best experience. Higher token cost per command (≈ <measured>
            extra tokens per render for the visualizer subagent).
```

Replace `<measured>` with the rounded range from Step 6 (e.g., `1.5–3.2k`).

Find the second occurrence:

```
  y = styled HTML in Chrome (≈ <measured> extra tokens)
```

Replace `<measured>` similarly.

Then add a new subsection at the end of Section 7, before Section 8:

```markdown

### Token cost reference (measured 2026-MM-DD)

Captured during plan task 11 against:

| Payload size | Input tokens | Output tokens | Total |
|--------------|--------------|---------------|-------|
| 4 jobs (typical match-jobs run) | <X> | <Y> | <X+Y> |
| 50 jobs (large match-jobs run) | <X> | <Y> | <X+Y> |

Rounded range used in user-facing prompts: **≈ <range>k extra tokens per render**. Update this subsection after any major template revision that materially changes payload size.
```

Fill in the two `match-jobs` rows from the measurements captured in Step 6. The `funnel-report` row will be appended by Task 15 once that view is wired and runnable.

- [ ] **Step 8: Update render-orchestration.md placeholder**

Edit `skills/shared-references/render-orchestration.md`. Find these two passages:

```
            Best experience. Higher token cost per command (≈ <measured>
            extra tokens per render for the visualizer subagent).
```

```
  y = styled HTML in Chrome (≈ <measured> extra tokens)
```

Replace `<measured>` in both with the rounded range from Step 6. Note the comment in the file already says the placeholder is replaced with the canonical figure from the spec; this step propagates that figure.

- [ ] **Step 9: Verify**

```bash
cd /Users/tura/git/claude-job-scout && grep -c "<measured>" docs/superpowers/specs/2026-04-29-visual-render-layer-design.md skills/shared-references/render-orchestration.md
```
Expected: `0` (all placeholders replaced).

```bash
cd /Users/tura/git/claude-job-scout && grep -c "Token cost reference" docs/superpowers/specs/2026-04-29-visual-render-layer-design.md
```
Expected: `1`.

```bash
cd /Users/tura/git/claude-job-scout && git diff --stat
```
Expected: 2 files changed.

- [ ] **Step 10: Commit + push**

```bash
cd /Users/tura/git/claude-job-scout && git add docs/superpowers/specs/2026-04-29-visual-render-layer-design.md skills/shared-references/render-orchestration.md && git commit -m "$(cat <<'EOF'
Replace token-cost placeholders with measured values

Ran /match-jobs end-to-end against a 4-job and a 50-job payload
in a scratch workspace. Captured input + output token counts
from the subagent dispatch metadata. Replaced ≈ <measured>
placeholders in both Section 2 prompts and the
render-orchestration reference. Added Section 7 "Token cost
reference" subsection with the measured table.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)" && git push -u origin phase-4/task-11-smoke-and-measure
```

---

## Task 12: `/job-search` templates + wiring

**Files:**
- Create: `/Users/tura/git/claude-job-scout/skills/_visualizer/templates/html/job-search.html.j2`
- Create: `/Users/tura/git/claude-job-scout/skills/_visualizer/templates/markdown/job-search.md.j2`
- Modify: `/Users/tura/git/claude-job-scout/skills/job-search/SKILL.md`

- [ ] **Step 1: Create branch**

```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-4/task-12-wire-job-search
```

- [ ] **Step 2: Write `html/job-search.html.j2`**

Create `/Users/tura/git/claude-job-scout/skills/_visualizer/templates/html/job-search.html.j2` with exactly this content:

===FILE_START===
{# schema:
   required:
     - data.title
     - data.subtitle
     - data.generated_at
     - data.filename
     - data.tier_counts
     - data.results
     - data.query
#}
<header class="report-header">
  <div class="icon">🔍</div>
  <div>
    <h1>{{ data.title }}</h1>
    <div class="subtitle">{{ data.subtitle }}</div>
  </div>
</header>

{% if data.query %}
<div style="background:var(--surface-soft);padding:10px 14px;border-radius:var(--radius-card);margin-bottom:18px;font-size:13px;color:var(--text-strong)">
  <strong>Query:</strong> <span style="font-family:var(--font-mono)">{{ data.query }}</span>
</div>
{% endif %}

{% if data.results %}
<div class="toolbar">
  <button data-sort="date" class="active">Recency ↓</button>
  <button data-sort="score">Score ↓</button>
  <button data-sort="company">Company A–Z</button>
  <span style="flex:1"></span>
  <button data-filter="all" data-filter-attr="tier" class="active">All ({{ data.tier_counts.total }})</button>
  <button data-filter="a" data-filter-attr="tier">A-tier ({{ data.tier_counts.a }})</button>
  <button data-filter="b" data-filter-attr="tier">B-tier ({{ data.tier_counts.b }})</button>
</div>

<section>
{% for job in data.results %}
  <article class="job-card" data-tier="{{ job.tier }}" data-sort_score="{{ job.score }}" data-sort_date="{{ job.posted_at }}" data-sort_company="{{ job.company }}">
    <div class="header">
      <div class="title">{{ job.title }}</div>
      <div class="score-pill tier-{{ job.tier }}">{{ job.score }}</div>
    </div>
    <div class="meta">{{ job.company }} · {{ job.location }}{% if job.salary %} · {{ job.salary }}{% endif %} · posted {{ job.posted_at }}{% if job.applicants %} · {{ job.applicants }} applicants{% endif %}</div>
    {% if job.tags %}
    <div>
      {% for tag in job.tags %}<span class="tag-chip">{{ tag }}</span>{% endfor %}
    </div>
    {% endif %}
  </article>
{% endfor %}
</section>
{% else %}
<div class="empty-state">
  <div class="icon">🔍</div>
  <div class="title">No jobs found for this query.</div>
  <div class="hint">Try widening your search terms or checking back later.</div>
</div>
{% endif %}
===FILE_END===

- [ ] **Step 3: Write `markdown/job-search.md.j2`**

Create `/Users/tura/git/claude-job-scout/skills/_visualizer/templates/markdown/job-search.md.j2` with exactly this content:

===FILE_START===
{# schema:
   required:
     - data.title
     - data.subtitle
     - data.generated_at
     - data.tier_counts
     - data.results
     - data.query
#}
## 🔍 {{ data.title }}

_{{ data.subtitle }}_

{% if data.query %}**Query:** `{{ data.query }}`{% endif %}

{% if data.results %}
| Tier | Score | Title | Company | Posted |
|------|------:|-------|---------|--------|
{% for job in data.results %}| {% if job.tier == "a" %}🟢{% endif %}{% if job.tier == "b" %}🟡{% endif %}{% if job.tier == "c" %}⚪{% endif %} | **{{ job.score }}** | {{ job.title }} | {{ job.company }} | {{ job.posted_at }} |
{% endfor %}

**Tiers:** A: {{ data.tier_counts.a }} · B: {{ data.tier_counts.b }} · Total: {{ data.tier_counts.total }}
{% else %}
🔍 **No jobs found for this query.** Try widening your search terms.
{% endif %}
===FILE_END===

- [ ] **Step 4: Modify `skills/job-search/SKILL.md` — add render step**

Read the current file:

```bash
cd /Users/tura/git/claude-job-scout && cat skills/job-search/SKILL.md
```

Identify the final user-output step (typically presents the search results as a markdown table). Insert a new `## Step N: Render` section immediately after that step (and before any `## Next Steps` block), with this content:

```
## Step N: Render

Construct a `data` payload as in `../shared-references/render-orchestration.md` Step A. View-specific fields:

- `title`: "Search results for `<query>`" (or "Search results · {{N}} jobs").
- `subtitle`: "{{N}} surfaced · A:{{a}} B:{{b}}".
- `query`: the original Boolean / keyword query string.
- `filename`: "job-search-latest.html".
- `results[]`: same shape as `match-jobs.results[]`, but `applicants` is added when known. Tier classification: same as match-jobs.

Then follow `render-orchestration.md` Steps B–G end-to-end. The summary line for this view (Step E):

```
✓ {{N}} jobs surfaced — A:{{a}} B:{{b}} — opened report in Chrome
```

If the `Agent` tool is unavailable, fall back to the pre-v0.7.0 markdown-table output.
```

(Replace `## Step N: Render` with the actual next step number — read the file first to find the next step number; commonly Step 5 or Step 6.)

Bump the skill's frontmatter `version:` to `0.2.0` (add the line if not present).

- [ ] **Step 5: Verify**

```bash
cd /Users/tura/git/claude-job-scout && wc -l skills/_visualizer/templates/html/job-search.html.j2 skills/_visualizer/templates/markdown/job-search.md.j2
```
Expected: HTML ~38 lines; markdown ~17 lines.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "## Step.*Render" skills/job-search/SKILL.md
```
Expected: `1`.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "render-orchestration.md" skills/job-search/SKILL.md
```
Expected: `1`.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "version: 0.2.0" skills/job-search/SKILL.md
```
Expected: `1`.

- [ ] **Step 6: Commit + push**

```bash
cd /Users/tura/git/claude-job-scout && git add skills/_visualizer/templates/html/job-search.html.j2 skills/_visualizer/templates/markdown/job-search.md.j2 skills/job-search/SKILL.md && git commit -m "$(cat <<'EOF'
Wire /job-search to the visual render layer

Adds HTML + markdown templates for job-search and inserts a
render step into the job-search skill. Templates highlight the
query string at the top, support sort by recency/score/company,
filter by tier. Bumps skill version to 0.2.0.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)" && git push -u origin phase-4/task-12-wire-job-search
```

---

## Task 13: `/check-job-notifications` templates + wiring

**Files:**
- Create: `/Users/tura/git/claude-job-scout/skills/_visualizer/templates/html/check-job-notifications.html.j2`
- Create: `/Users/tura/git/claude-job-scout/skills/_visualizer/templates/markdown/check-job-notifications.md.j2`
- Modify: `/Users/tura/git/claude-job-scout/skills/check-job-notifications/SKILL.md`

- [ ] **Step 1: Create branch**

```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-4/task-13-wire-notifications
```

- [ ] **Step 2: Write `html/check-job-notifications.html.j2`**

Create `/Users/tura/git/claude-job-scout/skills/_visualizer/templates/html/check-job-notifications.html.j2` with exactly this content:

===FILE_START===
{# schema:
   required:
     - data.title
     - data.subtitle
     - data.generated_at
     - data.filename
     - data.tier_counts
     - data.results
     - data.unread_count
#}
<header class="report-header">
  <div class="icon">🔔</div>
  <div>
    <h1>{{ data.title }}</h1>
    <div class="subtitle">{{ data.subtitle }}</div>
  </div>
</header>

{% if data.results %}
<div class="toolbar">
  <button data-sort="date" class="active">Latest ↓</button>
  <button data-sort="score">Score ↓</button>
  <span style="flex:1"></span>
  <button data-filter="all" data-filter-attr="seen" class="active">All ({{ data.tier_counts.total }})</button>
  <button data-filter="false" data-filter-attr="seen">Unread ({{ data.unread_count }})</button>
  <button data-filter="a" data-filter-attr="tier">A-tier ({{ data.tier_counts.a }})</button>
  <button data-filter="b" data-filter-attr="tier">B-tier ({{ data.tier_counts.b }})</button>
</div>

<section>
{% for note in data.results %}
  <article id="note-{{ note.id }}" class="event-card" data-tier="{{ note.tier }}" data-seen="{% if note.seen %}true{% else %}false{% endif %}" data-sort_score="{{ note.score }}" data-sort_date="{{ note.received_at }}">
    <div class="header">
      <div class="title">{{ note.title }}</div>
      <div class="score-pill tier-{{ note.tier }}">{{ note.score }}</div>
    </div>
    <div class="meta">{{ note.company }} · {{ note.received_at }}{% if note.source %} · {{ note.source }}{% endif %}</div>
    {% if note.preview %}<div style="font-size:13px;color:var(--text-muted);margin-top:6px">{{ note.preview }}</div>{% endif %}
    <div style="margin-top:8px"><button class="copy-btn" data-mark-read="note-{{ note.id }}">{% if note.seen %}Mark unread{% else %}Mark read{% endif %}</button></div>
  </article>
{% endfor %}
</section>
{% else %}
<div class="empty-state">
  <div class="icon">🔕</div>
  <div class="title">No notifications today.</div>
  <div class="hint">Make sure your LinkedIn alerts are still active.</div>
</div>
{% endif %}
===FILE_END===

- [ ] **Step 3: Write `markdown/check-job-notifications.md.j2`**

Create `/Users/tura/git/claude-job-scout/skills/_visualizer/templates/markdown/check-job-notifications.md.j2` with exactly this content:

===FILE_START===
{# schema:
   required:
     - data.title
     - data.subtitle
     - data.generated_at
     - data.tier_counts
     - data.results
     - data.unread_count
#}
## 🔔 {{ data.title }}

_{{ data.subtitle }}_

**Unread:** {{ data.unread_count }} of {{ data.tier_counts.total }}

{% if data.results %}
| Status | Tier | Score | Title | Company | Received |
|:------:|:----:|------:|-------|---------|----------|
{% for note in data.results %}| {% if note.seen %}✓{% else %}●{% endif %} | {% if note.tier == "a" %}🟢{% endif %}{% if note.tier == "b" %}🟡{% endif %}{% if note.tier == "c" %}⚪{% endif %} | **{{ note.score }}** | {{ note.title }} | {{ note.company }} | {{ note.received_at }} |
{% endfor %}
{% else %}
🔕 **No notifications today.** Make sure your LinkedIn alerts are still active.
{% endif %}
===FILE_END===

- [ ] **Step 4: Modify `skills/check-job-notifications/SKILL.md` — add render step**

Read the current file:

```bash
cd /Users/tura/git/claude-job-scout && cat skills/check-job-notifications/SKILL.md
```

Identify the final user-output step. Insert a new `## Step N: Render` section after it (before any `## Next Steps`):

```
## Step N: Render

Construct a `data` payload as in `../shared-references/render-orchestration.md` Step A. View-specific fields:

- `title`: "Today's notifications".
- `subtitle`: "{{N}} new · {{unread}} unread · A:{{a}} B:{{b}}".
- `filename`: "check-job-notifications-latest.html".
- `unread_count`: integer count of `seen: false` items.
- `results[]`: each item is `{ id, title, company, received_at, source, score, tier, seen, preview }`. The `preview` is the first 140 chars of the notification body.

Then follow `render-orchestration.md` Steps B–G end-to-end. Summary line:

```
✓ {{N}} notifications — {{unread}} unread — opened report in Chrome
```

Fall back to pre-v0.7.0 markdown table if `Agent` tool is unavailable.
```

Bump the skill's frontmatter `version:` to `0.2.0`.

- [ ] **Step 5: Verify**

```bash
cd /Users/tura/git/claude-job-scout && wc -l skills/_visualizer/templates/html/check-job-notifications.html.j2 skills/_visualizer/templates/markdown/check-job-notifications.md.j2
```
Expected: HTML ~36 lines; markdown ~18 lines.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "## Step.*Render" skills/check-job-notifications/SKILL.md
```
Expected: `1`.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "version: 0.2.0" skills/check-job-notifications/SKILL.md
```
Expected: `1`.

- [ ] **Step 6: Commit + push**

```bash
cd /Users/tura/git/claude-job-scout && git add skills/_visualizer/templates/html/check-job-notifications.html.j2 skills/_visualizer/templates/markdown/check-job-notifications.md.j2 skills/check-job-notifications/SKILL.md && git commit -m "$(cat <<'EOF'
Wire /check-job-notifications to the visual render layer

HTML template renders each notification as an .event-card with
mark-read toggle and a tier pill. Filter buttons cover unread
status and tier. Markdown template renders a status-prefixed
table. Bumps skill version to 0.2.0.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)" && git push -u origin phase-4/task-13-wire-notifications
```

---

## Task 14: `/check-inbox` templates + wiring

**Files:**
- Create: `/Users/tura/git/claude-job-scout/skills/_visualizer/templates/html/check-inbox.html.j2`
- Create: `/Users/tura/git/claude-job-scout/skills/_visualizer/templates/markdown/check-inbox.md.j2`
- Modify: `/Users/tura/git/claude-job-scout/skills/check-inbox/SKILL.md`

- [ ] **Step 1: Create branch**

```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-4/task-14-wire-inbox
```

- [ ] **Step 2: Write `html/check-inbox.html.j2`**

Create `/Users/tura/git/claude-job-scout/skills/_visualizer/templates/html/check-inbox.html.j2` with exactly this content:

===FILE_START===
{# schema:
   required:
     - data.title
     - data.subtitle
     - data.generated_at
     - data.filename
     - data.results
     - data.unread_count
     - data.thread_count
#}
<header class="report-header">
  <div class="icon">📬</div>
  <div>
    <h1>{{ data.title }}</h1>
    <div class="subtitle">{{ data.subtitle }}</div>
  </div>
</header>

{% if data.results %}
<div class="toolbar">
  <button data-sort="date" class="active">Latest ↓</button>
  <button data-sort="company">Company A–Z</button>
  <span style="flex:1"></span>
  <button data-filter="all" data-filter-attr="seen" class="active">All ({{ data.thread_count }})</button>
  <button data-filter="false" data-filter-attr="seen">Unread ({{ data.unread_count }})</button>
</div>

<section>
{% for thread in data.results %}
  <article id="thread-{{ thread.id }}" class="thread-card" data-seen="{% if thread.unread %}false{% else %}true{% endif %}" data-sort_date="{{ thread.last_message_at }}" data-sort_company="{{ thread.company }}">
    <div class="header">
      <div class="title">{{ thread.recruiter_name }}{% if thread.company %} · {{ thread.company }}{% endif %}{% if thread.unread %} <span class="tag-chip accent">unread</span>{% endif %}</div>
      <div style="font-size:11px;color:var(--text-muted);font-family:var(--font-mono)">{{ thread.last_message_at }}</div>
    </div>
    <div class="meta">{{ thread.message_count }} message{% if thread.message_count %}{% endif %} · last from {{ thread.last_message_from }}</div>
    {% if thread.lead_tier %}<div><span class="tag-chip">Lead tier: {{ thread.lead_tier }}</span></div>{% endif %}
    <div class="fold" style="margin-top:10px">
      <div class="fold-header">
        <span>Conversation ({{ thread.message_count }} message{% if thread.message_count %}{% endif %})</span>
        <span class="chevron">›</span>
      </div>
      <div class="fold-body">
        <div class="timeline">
        {% for msg in thread.messages %}
          <div class="timeline-item">
            <div class="meta">{{ msg.sent_at }} · {{ msg.from }}</div>
            <div>{{ msg.body }}</div>
          </div>
        {% endfor %}
        </div>
      </div>
    </div>
  </article>
{% endfor %}
</section>
{% else %}
<div class="empty-state">
  <div class="icon">📭</div>
  <div class="title">Inbox is quiet.</div>
  <div class="hint">No active recruiter threads right now.</div>
</div>
{% endif %}
===FILE_END===

- [ ] **Step 3: Write `markdown/check-inbox.md.j2`**

Create `/Users/tura/git/claude-job-scout/skills/_visualizer/templates/markdown/check-inbox.md.j2` with exactly this content:

===FILE_START===
{# schema:
   required:
     - data.title
     - data.subtitle
     - data.generated_at
     - data.results
     - data.unread_count
     - data.thread_count
#}
## 📬 {{ data.title }}

_{{ data.subtitle }}_

**Unread:** {{ data.unread_count }} of {{ data.thread_count }} threads

{% if data.results %}
{% for thread in data.results %}
### {% if thread.unread %}● {% endif %}{{ thread.recruiter_name }}{% if thread.company %} · {{ thread.company }}{% endif %}

_{{ thread.message_count }} messages · last {{ thread.last_message_at }} from {{ thread.last_message_from }}_{% if thread.lead_tier %} · **Lead tier: {{ thread.lead_tier }}**{% endif %}

{% for msg in thread.messages %}- **{{ msg.sent_at }} · {{ msg.from }}:** {{ msg.body }}
{% endfor %}
{% endfor %}
{% else %}
📭 **Inbox is quiet.** No active recruiter threads right now.
{% endif %}
===FILE_END===

- [ ] **Step 4: Modify `skills/check-inbox/SKILL.md` — add render step**

Read the current file:

```bash
cd /Users/tura/git/claude-job-scout && cat skills/check-inbox/SKILL.md
```

Identify the final user-output step. Insert a new `## Step N: Render` section after it:

```
## Step N: Render

Construct a `data` payload as in `../shared-references/render-orchestration.md` Step A. View-specific fields:

- `title`: "Recruiter inbox".
- `subtitle`: "{{N}} threads · {{unread}} unread".
- `filename`: "check-inbox-latest.html".
- `thread_count`: integer.
- `unread_count`: integer.
- `results[]`: each is `{ id, recruiter_name, company, message_count, last_message_at, last_message_from, unread, lead_tier, messages[] }`. `messages[]` is `[{ sent_at, from, body }]` chronological. `lead_tier` per `_recruiter-engagement` taxonomy.

Then follow `render-orchestration.md` Steps B–G. Summary line:

```
✓ {{N}} threads — {{unread}} unread — opened report in Chrome
```

Fall back to pre-v0.7.0 inline output if `Agent` tool is unavailable.
```

Bump skill `version:` to `0.2.0`.

- [ ] **Step 5: Verify**

```bash
cd /Users/tura/git/claude-job-scout && wc -l skills/_visualizer/templates/html/check-inbox.html.j2 skills/_visualizer/templates/markdown/check-inbox.md.j2
```
Expected: HTML ~50 lines; markdown ~17 lines.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "## Step.*Render\|render-orchestration.md\|version: 0.2.0" skills/check-inbox/SKILL.md
```
Expected: at least `3`.

- [ ] **Step 6: Commit + push**

```bash
cd /Users/tura/git/claude-job-scout && git add skills/_visualizer/templates/html/check-inbox.html.j2 skills/_visualizer/templates/markdown/check-inbox.md.j2 skills/check-inbox/SKILL.md && git commit -m "$(cat <<'EOF'
Wire /check-inbox to the visual render layer

HTML template renders each thread as a .thread-card with an
expand/collapse fold containing a chronological timeline of
messages. Unread filter and recency sort. Markdown template
shows threads as headed sections with bulleted messages.
Bumps skill version to 0.2.0.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)" && git push -u origin phase-4/task-14-wire-inbox
```

---

## Task 15: `/funnel-report` templates + wiring (time-series naming)

**Files:**
- Create: `/Users/tura/git/claude-job-scout/skills/_visualizer/templates/html/funnel-report.html.j2`
- Create: `/Users/tura/git/claude-job-scout/skills/_visualizer/templates/markdown/funnel-report.md.j2`
- Modify: `/Users/tura/git/claude-job-scout/skills/funnel-report/SKILL.md`

- [ ] **Step 1: Create branch**

```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-4/task-15-wire-funnel
```

- [ ] **Step 2: Write `html/funnel-report.html.j2`**

Create `/Users/tura/git/claude-job-scout/skills/_visualizer/templates/html/funnel-report.html.j2` with exactly this content:

===FILE_START===
{# schema:
   required:
     - data.title
     - data.subtitle
     - data.generated_at
     - data.filename
     - data.metrics
     - data.stages
#}
<header class="report-header">
  <div class="icon">📊</div>
  <div>
    <h1>{{ data.title }}</h1>
    <div class="subtitle">{{ data.subtitle }}</div>
  </div>
</header>

<div class="metrics-grid">
{% for m in data.metrics %}
  <div class="metric-block">
    <div class="label">{{ m.label }}</div>
    <div class="value">{{ m.value }}</div>
    {% if m.delta_text %}<div class="delta {{ m.delta_dir }}">{{ m.delta_text }}</div>{% endif %}
  </div>
{% endfor %}
</div>

<section>
<h2 style="font-size:14px;text-transform:uppercase;letter-spacing:1.5px;color:var(--text-muted);margin:24px 0 12px;font-weight:600">Pipeline by stage</h2>
{% for stage in data.stages %}
  <article class="job-card" data-tier="a">
    <div class="header">
      <div class="title">{{ stage.name }}</div>
      <div class="score-pill tier-a">{{ stage.count }}</div>
    </div>
    {% if stage.companies %}
    <div class="meta">{{ stage.companies | raw }}</div>
    {% endif %}
    {% if stage.note %}<div style="font-size:13px;color:var(--text-strong);margin-top:6px">{{ stage.note }}</div>{% endif %}
  </article>
{% endfor %}
</section>
===FILE_END===

- [ ] **Step 3: Write `markdown/funnel-report.md.j2`**

Create `/Users/tura/git/claude-job-scout/skills/_visualizer/templates/markdown/funnel-report.md.j2` with exactly this content:

===FILE_START===
{# schema:
   required:
     - data.title
     - data.subtitle
     - data.generated_at
     - data.metrics
     - data.stages
#}
## 📊 {{ data.title }}

_{{ data.subtitle }}_

### Metrics

| Metric | Value | Delta |
|--------|------:|-------|
{% for m in data.metrics %}| {{ m.label }} | **{{ m.value }}** | {% if m.delta_text %}{{ m.delta_text }}{% endif %} |
{% endfor %}

### Pipeline by stage

{% for stage in data.stages %}- **{{ stage.name }}** — {{ stage.count }}{% if stage.companies %} ({{ stage.companies | raw }}){% endif %}{% if stage.note %}: {{ stage.note }}{% endif %}
{% endfor %}
===FILE_END===

- [ ] **Step 4: Modify `skills/funnel-report/SKILL.md` — add render step**

Read the current file:

```bash
cd /Users/tura/git/claude-job-scout && cat skills/funnel-report/SKILL.md
```

Identify the final user-output step. Insert a new `## Step N: Render` section after it:

```
## Step N: Render

Construct a `data` payload as in `../shared-references/render-orchestration.md` Step A. View-specific fields:

- `title`: "Pipeline · week of {{date}}".
- `subtitle`: short health summary, e.g. "12 sent · 3 interviews · 1 offer".
- `filename`: `funnel-report-{{YYYY-MM-DD-HHMM}}.html` (time-series — not -latest).
- `metrics[]`: each is `{ label, value, delta_text, delta_dir }`. `delta_dir` is `"up" | "down" | "flat"`. `delta_text` is the friendly text, e.g. "+3 vs last week".
- `stages[]`: each is `{ name, count, companies, note }`. `companies` may include inline emoji or short HTML chips for the HTML view (use `| raw` filter).

Then follow `render-orchestration.md` Steps B–G. Summary line:

```
✓ Pipeline snapshot for week of {{date}} — opened report in Chrome
```

Fall back to pre-v0.7.0 markdown summary if `Agent` tool is unavailable. Note: filename is time-series, so each invocation writes a new file. Lifecycle Step G archives files older than 90 days into `.job-scout/reports/archive/`.
```

Bump skill `version:` to `0.2.0`.

- [ ] **Step 5: Verify**

```bash
cd /Users/tura/git/claude-job-scout && wc -l skills/_visualizer/templates/html/funnel-report.html.j2 skills/_visualizer/templates/markdown/funnel-report.md.j2
```
Expected: HTML ~32 lines; markdown ~20 lines.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "funnel-report-{{YYYY" skills/funnel-report/SKILL.md
```
Expected: `1`.

- [ ] **Step 6: Append the funnel-report token row to the spec**

Now that `/funnel-report` is wired, run it once against seed data in `/tmp/job-scout-smoke` (or `/tmp/job-scout-final`) and capture the subagent's input + output token counts for that one render. Then edit `docs/superpowers/specs/2026-04-29-visual-render-layer-design.md` and append a new row to the "Token cost reference" table (added by Task 11), directly after the second `match-jobs` row:

```
| funnel-report (typical week's data) | <X> | <Y> | <X+Y> |
```

If the new row's total falls outside the rounded range used in the prompt copy (`≈ <range>k extra tokens per render`), update both the prompt copy in the spec (Section 2 — two locations) and in `skills/shared-references/render-orchestration.md` (also two locations). If it falls within the existing range, no other changes needed.

- [ ] **Step 7: Commit + push**

```bash
cd /Users/tura/git/claude-job-scout && git add skills/_visualizer/templates/html/funnel-report.html.j2 skills/_visualizer/templates/markdown/funnel-report.md.j2 skills/funnel-report/SKILL.md docs/superpowers/specs/2026-04-29-visual-render-layer-design.md skills/shared-references/render-orchestration.md && git commit -m "$(cat <<'EOF'
Wire /funnel-report to the visual render layer

HTML template renders a metrics grid (responsive .metric-block
auto-fit) plus a stage-by-stage breakdown using .job-card
primitives. Markdown template uses tables for metrics and a
bullet list for stages. Filename is time-series (not -latest);
lifecycle cleanup archives old reports after 90 days. Appends
the funnel-report row to the spec's token-cost reference table.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)" && git push -u origin phase-4/task-15-wire-funnel
```

---

## Task 16: `/interview-prep` templates + wiring (slugged naming, folds, copy)

**Files:**
- Create: `/Users/tura/git/claude-job-scout/skills/_visualizer/templates/html/interview-prep.html.j2`
- Create: `/Users/tura/git/claude-job-scout/skills/_visualizer/templates/markdown/interview-prep.md.j2`
- Modify: `/Users/tura/git/claude-job-scout/skills/interview-prep/SKILL.md`

- [ ] **Step 1: Create branch**

```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-4/task-16-wire-interview
```

- [ ] **Step 2: Write `html/interview-prep.html.j2`**

Create `/Users/tura/git/claude-job-scout/skills/_visualizer/templates/html/interview-prep.html.j2` with exactly this content:

===FILE_START===
{# schema:
   required:
     - data.title
     - data.subtitle
     - data.generated_at
     - data.filename
     - data.role
     - data.company
     - data.sections
#}
<header class="report-header">
  <div class="icon">🎯</div>
  <div>
    <h1>{{ data.title }}</h1>
    <div class="subtitle">{{ data.subtitle }}</div>
  </div>
</header>

<div style="background:var(--surface-soft);padding:14px 18px;border-radius:var(--radius-card);margin-bottom:18px">
  <div style="font-size:11px;text-transform:uppercase;letter-spacing:1.5px;color:var(--text-muted);margin-bottom:4px">Target role</div>
  <div style="font-size:16px;font-weight:700;color:var(--text-strong)">{{ data.role }}</div>
  <div style="font-size:13px;color:var(--text-muted);margin-top:2px">{{ data.company }}</div>
</div>

<section>
{% for section in data.sections %}
  <div class="fold {% if section.open_by_default %}open{% endif %}">
    <div class="fold-header">
      <span>{{ section.heading }}</span>
      <span class="chevron">›</span>
    </div>
    <div class="fold-body">
      <div style="display:flex;justify-content:flex-end;margin-bottom:8px">
        <button class="copy-btn" data-copy-target="prep-{{ section.id }}">Copy</button>
      </div>
      <div id="prep-{{ section.id }}">
        {{ section.body | raw }}
      </div>
    </div>
  </div>
{% endfor %}
</section>
===FILE_END===

- [ ] **Step 3: Write `markdown/interview-prep.md.j2`**

Create `/Users/tura/git/claude-job-scout/skills/_visualizer/templates/markdown/interview-prep.md.j2` with exactly this content:

===FILE_START===
{# schema:
   required:
     - data.title
     - data.subtitle
     - data.generated_at
     - data.role
     - data.company
     - data.sections
#}
## 🎯 {{ data.title }}

_{{ data.subtitle }}_

**Target role:** {{ data.role }} · {{ data.company }}

{% for section in data.sections %}
### {{ section.heading }}

{{ section.body | raw }}

{% endfor %}
===FILE_END===

- [ ] **Step 4: Modify `skills/interview-prep/SKILL.md` — add render step**

Read the current file:

```bash
cd /Users/tura/git/claude-job-scout && cat skills/interview-prep/SKILL.md
```

Identify the final user-output step. Insert a new `## Step N: Render` section after it:

```
## Step N: Render

Construct a `data` payload as in `../shared-references/render-orchestration.md` Step A. View-specific fields:

- `title`: "Interview prep — {{role}}".
- `subtitle`: "{{company}} · prepared {{generated_at}}".
- `role`: full role title.
- `company`: company name.
- `filename`: `interview-prep-<role-slug>-<YYYY-MM-DD-HHMM>.html` where `<role-slug>` is `<tracker-id>-<4-char-disambiguator>`. The disambiguator is the first 4 hex characters of `sha1(role_title)`.
- `sections[]`: each is `{ id, heading, body, open_by_default }`. `id` is a short slug (e.g., `company-bg`, `tech-stack`, `hr-screen-questions`). `body` is HTML for the HTML view (use `| raw`) and markdown for the markdown view. `open_by_default` is true for the most-relevant section (typically the first); other folds start collapsed.

Then follow `render-orchestration.md` Steps B–G. Summary line:

```
✓ Prep dossier for {{role}} at {{company}} — opened report in Chrome
```

Fall back to pre-v0.7.0 markdown sections if `Agent` tool is unavailable.
```

Bump skill `version:` to `0.2.0`.

- [ ] **Step 5: Verify**

```bash
cd /Users/tura/git/claude-job-scout && wc -l skills/_visualizer/templates/html/interview-prep.html.j2 skills/_visualizer/templates/markdown/interview-prep.md.j2
```
Expected: HTML ~32 lines; markdown ~14 lines.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "sha1\|disambiguator" skills/interview-prep/SKILL.md
```
Expected: at least `1`.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "version: 0.2.0" skills/interview-prep/SKILL.md
```
Expected: `1`.

- [ ] **Step 6: Commit + push**

```bash
cd /Users/tura/git/claude-job-scout && git add skills/_visualizer/templates/html/interview-prep.html.j2 skills/_visualizer/templates/markdown/interview-prep.md.j2 skills/interview-prep/SKILL.md && git commit -m "$(cat <<'EOF'
Wire /interview-prep to the visual render layer

HTML template renders sections as collapsible folds, each with
a Copy button that pulls the section body to clipboard. The
first section opens by default; others start collapsed. Filename
is slugged + timestamped; the disambiguator is sha1(role_title)
truncated to 4 hex chars so re-running prep on the same tracker
entry produces distinct files. Bumps skill version to 0.2.0.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)" && git push -u origin phase-4/task-16-wire-interview
```

---

## Task 17: CLAUDE.md hard rule + `.gitignore` update

**Files:**
- Modify: `/Users/tura/git/claude-job-scout/CLAUDE.md`
- Modify: `/Users/tura/git/claude-job-scout/.gitignore`

- [ ] **Step 1: Create branch**

```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-4/task-17-claudemd-gitignore
```

- [ ] **Step 2: Add `.superpowers/` to `.gitignore`**

Find this exact line in `.gitignore`:

```
.job-scout/
```

Add a new line directly below it:

```
.superpowers/
```

- [ ] **Step 3: Add the hard rule to CLAUDE.md**

Find the "## Hard rules (non-negotiable)" section in `CLAUDE.md`. Identify the last numbered rule (currently rule 6 about `_` prefix). Insert a new rule 7 immediately after rule 6 and before the next section heading:

```
7. **Tier 1 user-facing commands render via `_visualizer`, never inline.** Any skill that produces user-facing output for `/job-search`, `/match-jobs`, `/check-job-notifications`, `/funnel-report`, `/check-inbox`, or `/interview-prep` dispatches the `_visualizer` subagent through the `Agent` tool, following `skills/shared-references/render-orchestration.md`. Inline HTML production from these orchestrators is forbidden — the templating, theming, and asset embedding live in one place by design.
```

- [ ] **Step 4: Verify**

```bash
cd /Users/tura/git/claude-job-scout && grep -c "^\.superpowers/" .gitignore
```
Expected: `1`.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "render via \`_visualizer\`" CLAUDE.md
```
Expected: `1`.

```bash
cd /Users/tura/git/claude-job-scout && grep -E "^[0-9]+\. " CLAUDE.md | wc -l
```
Expected: at least `7`.

```bash
cd /Users/tura/git/claude-job-scout && git status -s
```
Expected: 2 modified files.

- [ ] **Step 5: Commit + push**

```bash
cd /Users/tura/git/claude-job-scout && git add CLAUDE.md .gitignore && git commit -m "$(cat <<'EOF'
Add hard rule for _visualizer dispatch + gitignore .superpowers/

Adds rule 7 to CLAUDE.md: Tier 1 commands must dispatch
_visualizer rather than producing HTML inline. Centralises
templating/theming concerns in one skill. Also adds
.superpowers/ to gitignore so brainstorming sessions don't
pollute the working tree.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)" && git push -u origin phase-4/task-17-claudemd-gitignore
```

---

## Task 18: Release prep — versioning, ROADMAP, CHANGELOG, README

**Files:**
- Modify: `/Users/tura/git/claude-job-scout/.claude-plugin/plugin.json`
- Modify: `/Users/tura/git/claude-job-scout/docs/ROADMAP.md`
- Modify: `/Users/tura/git/claude-job-scout/CHANGELOG.md`
- Modify: `/Users/tura/git/claude-job-scout/README.md`

- [ ] **Step 1: Create branch**

```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-4/task-18-release-prep
```

- [ ] **Step 2: Bump `.claude-plugin/plugin.json`**

Read the file:

```bash
cd /Users/tura/git/claude-job-scout && cat .claude-plugin/plugin.json
```

Find the `"version"` field. Change its value from `"0.6.1"` (or whatever the current value is — confirm by reading) to `"0.7.0"`.

- [ ] **Step 3: Update ROADMAP.md**

Find this row in the "Status at a glance" table at the top of `docs/ROADMAP.md`:

```
| 3. New user-facing commands | v0.6.0 | Shipped — v0.6.0 | [`specs/2026-04-17-phase-3-user-facing-commands-design.md`](superpowers/specs/2026-04-17-phase-3-user-facing-commands-design.md) | [`plans/2026-04-17-phase-3-user-facing-commands.md`](superpowers/plans/2026-04-17-phase-3-user-facing-commands.md) |
```

Add a new row directly below:

```
| **4. Visual render layer** | v0.7.0 | In progress | [`specs/2026-04-29-visual-render-layer-design.md`](superpowers/specs/2026-04-29-visual-render-layer-design.md) | [`plans/2026-04-29-visual-render-layer.md`](superpowers/plans/2026-04-29-visual-render-layer.md) |
```

Then find the "Current focus:" line below the table and replace it with:

```
**Current focus:** Phase 4 (visual render layer) executing toward v0.7.0.
```

Then find the section "## Phase 3 — v0.6.0: New user-facing commands" with its checkbox list. After that section's last checkbox, add a new section with checkboxes for every plan task:

```markdown

## Phase 4 — v0.7.0: Visual render layer

Adds a beautified HTML report layer for the six Tier 1 user-facing commands. Reports render via the `_visualizer` subagent (Modern Cards aesthetic, light JS interactivity), auto-open in Chrome via the existing extension, and fall back to styled markdown when HTML rendering or browser-open fails.

- [ ] **Task 1: `_visualizer` skill skeleton + reference files**
- [ ] **Task 2: theme.css asset**
- [ ] **Task 3: interactive.js asset**
- [ ] **Task 4: base.html.j2 + base.md.j2 frame templates**
- [ ] **Task 5: `_visualizer/SKILL.md` full subagent contract**
- [ ] **Task 6: `match-jobs` HTML + markdown templates**
- [ ] **Task 7: `render-orchestration.md` shared reference**
- [ ] **Task 8: Schema migration 0.6 → 0.7**
- [ ] **Task 9: `/config` slash command**
- [ ] **Task 10: Wire `/match-jobs` to render orchestration**
- [ ] **Task 11: End-to-end smoke + token measurement**
- [ ] **Task 12: Wire `/job-search`**
- [ ] **Task 13: Wire `/check-job-notifications`**
- [ ] **Task 14: Wire `/check-inbox`**
- [ ] **Task 15: Wire `/funnel-report`**
- [ ] **Task 16: Wire `/interview-prep`**
- [ ] **Task 17: CLAUDE.md hard rule + `.gitignore` update**
- [ ] **Task 18: Release prep — versioning, ROADMAP, CHANGELOG, README**
- [ ] **Task 19: Final 6-command end-to-end smoke**
```

Then find the `## Log` section and append:

```
- **2026-04-29** — Phase 4 (visual render layer) entering execution. Spec + plan committed; v0.7.0 target.
```

- [ ] **Step 4: Update CHANGELOG.md**

Find the most recent version section in `CHANGELOG.md` (currently v0.6.1). Insert a new section above it:

```markdown
## [0.7.0] — 2026-04-29 (in progress)

### Added

- Visual render layer for Tier 1 user-facing commands. `/match-jobs`, `/job-search`, `/check-job-notifications`, `/funnel-report`, `/check-inbox`, and `/interview-prep` now produce a Modern Cards–styled HTML report that auto-opens in Chrome via the existing extension.
- New `_visualizer` subagent (`skills/_visualizer/`) — dispatches via the `Agent` tool, returns a delta-only response per the existing subagent protocol. Templates, theme tokens, and asset bundle live in a single skill.
- New `/config` slash command for viewing and changing per-workspace settings (`.job-scout/config.json`).
- New shared reference `skills/shared-references/render-orchestration.md` documenting the procedure every Tier 1 command follows: build payload → consult render config → dispatch → open in Chrome → handle failure → terminal summary → lifecycle cleanup.
- First-run prompt: on first Tier 1 invocation after upgrade, the user picks `always`, `never`, or `ask` for HTML rendering. The choice is stored in `.job-scout/config.json` and can be changed via `/config render <mode>`.
- Markdown fallback: when HTML rendering or Chrome-open fails, the user is asked whether to show output as styled markdown in the conversation window.
- Schema migration 0.6 → 0.7: adds retention config keys and creates `.job-scout/reports/` and `.job-scout/reports/archive/`.
- `.superpowers/` is now gitignored.

### Changed

- Each of the six Tier 1 SKILL.md files gains a final "render" step that calls into the shared orchestration. Bumps each skill's `version:` frontmatter to `0.2.0`.
- CLAUDE.md gains a new hard rule (#7): Tier 1 commands must dispatch `_visualizer` rather than rendering HTML inline.

### Out of scope (deferred to v0.8.0+)

- Tier 2 commands (`/analyze-cv`, `/cover-letter`, `/optimize-profile`).
- Dark mode.
- Cross-report comparison views.
- Print/PDF stylesheet polish.
- Embedded charts in `/funnel-report`.
```

- [ ] **Step 5: Update README.md**

Find a sensible insertion point in `README.md` — typically a "Features" or "How it works" section. Add a new subsection (place at the end of the Features list or as a new top-level section):

```markdown

### Visual reports (v0.7.0+)

Six Tier 1 commands — `/match-jobs`, `/job-search`, `/check-job-notifications`, `/funnel-report`, `/check-inbox`, `/interview-prep` — now render their output as a self-contained HTML report (Modern Cards aesthetic, light interactivity) that auto-opens in your Chrome via the existing Claude Chrome extension.

Reports are saved under `.job-scout/reports/`. Snapshot views (match-jobs, job-search, check-job-notifications, check-inbox) write `<view>-latest.html`, overwriting on each run. Time-series views (funnel-report, interview-prep) write timestamped files; old files auto-archive after 90 days.

On the first Tier 1 invocation after upgrade, you pick how output is displayed:

- `always` — render HTML and auto-open in Chrome (best experience; higher token cost).
- `never` — render styled markdown directly in the conversation window (lower token cost).
- `ask` — choose per-run.

Change later with `/config render <mode>`. When HTML rendering or Chrome-open fails, the plugin asks if you want the markdown view instead — output is never lost.
```

- [ ] **Step 6: Verify**

```bash
cd /Users/tura/git/claude-job-scout && grep -c '"version": "0.7.0"' .claude-plugin/plugin.json
```
Expected: `1`.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "Phase 4 — v0.7.0\|Phase 4 (visual render layer)" docs/ROADMAP.md
```
Expected: at least `2`.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "## \[0.7.0\]" CHANGELOG.md
```
Expected: `1`.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "Visual reports\|render HTML and auto-open" README.md
```
Expected: at least `1`.

```bash
cd /Users/tura/git/claude-job-scout && git diff --stat
```
Expected: 4 files changed.

- [ ] **Step 7: Commit + push**

```bash
cd /Users/tura/git/claude-job-scout && git add .claude-plugin/plugin.json docs/ROADMAP.md CHANGELOG.md README.md && git commit -m "$(cat <<'EOF'
Release prep for v0.7.0 — visual render layer

Bumps plugin.json to 0.7.0. Adds Phase 4 entry to ROADMAP with
the full task checklist. Inserts v0.7.0 section in CHANGELOG
following Keep a Changelog conventions. Adds a "Visual reports"
section to README explaining the render mode options and
fallback behaviour.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)" && git push -u origin phase-4/task-18-release-prep
```

---

## Task 19: Final 6-command end-to-end smoke

**Files:**
- No code changes. Manual verification across all six Tier 1 commands.

- [ ] **Step 1: Create branch (for any docs corrections)**

```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git checkout -b phase-4/task-19-final-smoke
```

- [ ] **Step 2: Set up scratch workspace with seed data**

```bash
mkdir -p /tmp/job-scout-final && cd /tmp/job-scout-final && rm -rf .job-scout && mkdir -p .job-scout/cache .job-scout/threads && echo '0.6' > .job-scout/schema-version
```

Seed CV:
```bash
cd /tmp/job-scout-final && cat > .job-scout/cv.json <<'EOF'
{ "summary": "Senior backend engineer with 10 years of payments experience.", "skills": ["Go", "Postgres", "Kafka", "Stripe API", "Kubernetes"], "cv_hash": "smoketest-cv" }
EOF
```

Seed jobs (4 plus a 50-job replication for token-cost re-check):
```bash
cd /tmp/job-scout-final && cat > .job-scout/cache/seed-jobs.json <<'EOF'
{ "jobs": [
  { "id": "J1", "title": "Senior Backend Engineer", "company": "Stripe", "location": "Remote", "salary": "€180k-220k", "posted_at": "2026-04-28", "description": "Go, Payments, Stripe API, Postgres", "easy_apply": false },
  { "id": "J2", "title": "Staff Software Engineer", "company": "Linear", "location": "Remote", "salary": "", "posted_at": "2026-04-27", "description": "TypeScript, Postgres, distributed systems", "easy_apply": true },
  { "id": "J3", "title": "Engineering Manager", "company": "Notion", "location": "SF or remote", "salary": "$240k-280k", "posted_at": "2026-04-26", "description": "Lead a team of 6, hiring, mentorship", "easy_apply": false },
  { "id": "J4", "title": "Backend Lead", "company": "Vercel", "location": "Remote", "salary": "", "posted_at": "2026-04-25", "description": "Go, Kubernetes, edge computing", "easy_apply": true }
] }
EOF
```

Seed threads (for `/check-inbox`):
```bash
cd /tmp/job-scout-final && cat > .job-scout/threads/T1.json <<'EOF'
{ "id": "T1", "recruiter_name": "Sarah Chen", "company": "Stripe", "unread": true, "last_message_at": "2026-04-28", "last_message_from": "Sarah", "lead_tier": "warm", "messages": [ { "sent_at": "2026-04-25", "from": "Sarah", "body": "Saw your profile — would you be open to chatting about a Senior Backend role?" }, { "sent_at": "2026-04-28", "from": "Sarah", "body": "Following up — happy to share the JD." } ] }
EOF
```

- [ ] **Step 3: Run each Tier 1 command and verify**

For each of the six commands, run it against the scratch workspace and verify the corresponding HTML report renders correctly. Use this checklist per command:

For `/match-jobs`:
1. Run the command pointing at `.job-scout/cache/seed-jobs.json`.
2. ` test -s .job-scout/reports/match-jobs-latest.html` → OK.
3. Open in Chrome. Verify: 4 cards, A/B/C tiers visible, sort + filter buttons work, hover lifts cards.
4. Verify the embedded `report-data` JSON parses with `jq`.

For `/job-search`:
1. Run with a query like `"Senior Go engineer remote"` (against the same seed jobs).
2. `test -s .job-scout/reports/job-search-latest.html` → OK.
3. Open in Chrome. Verify the query string banner is visible at top.

For `/check-job-notifications`:
1. Trigger against synthetic notification data (or LinkedIn directly if convenient).
2. `test -s .job-scout/reports/check-job-notifications-latest.html` → OK.
3. Verify mark-read button toggles card opacity.

For `/check-inbox`:
1. Run against `.job-scout/threads/T1.json`.
2. `test -s .job-scout/reports/check-inbox-latest.html` → OK.
3. Click the fold header — the message timeline expands.

For `/funnel-report`:
1. Run with seeded application history (use `.job-scout/tracker.json` if available, else synthesise).
2. `ls .job-scout/reports/funnel-report-*.html | head -1` shows a timestamped file.
3. Open in Chrome. Verify metrics-grid auto-fits and `delta.up` / `delta.down` colors are correct.

For `/interview-prep`:
1. Run with `tracker-id=J1`.
2. `ls .job-scout/reports/interview-prep-J1-*.html` shows a slugged + timestamped file.
3. Open in Chrome. Verify folds collapse/expand. Click a Copy button — verify clipboard contains the section text.

- [ ] **Step 4: Run the fallback path**

Trigger a render failure on `/match-jobs`:
```bash
cd /Users/tura/git/claude-job-scout && mv skills/_visualizer/templates/html/match-jobs.html.j2 skills/_visualizer/templates/html/match-jobs.html.j2.bak
```

Run `/match-jobs` again. Expect:
1. `_visualizer` returns `template_missing`.
2. The orchestrator prompts "Show output here as text instead? (Y/n)".
3. Answering `Y` produces the markdown view inline.
4. `.job-scout/cache/visualizer-errors.log` contains a single line for this error.

Restore:
```bash
cd /Users/tura/git/claude-job-scout && mv skills/_visualizer/templates/html/match-jobs.html.j2.bak skills/_visualizer/templates/html/match-jobs.html.j2
```

- [ ] **Step 5: Run the lifecycle path**

Touch a fake old `funnel-report`:
```bash
cd /tmp/job-scout-final && touch -t 202512290900 .job-scout/reports/funnel-report-2025-12-29-0900.html
```

Run any Tier 1 command. Verify:
```bash
cd /tmp/job-scout-final && ls .job-scout/reports/archive/funnel-report-2025-12-29-0900.html
```
Expected: file exists in archive (moved by lifecycle cleanup).

Touch a year-old archive entry:
```bash
cd /tmp/job-scout-final && touch -t 202412290900 .job-scout/reports/archive/funnel-report-2024-12-29-0900.html 2>/dev/null || true
```

Run another Tier 1 command. Verify:
```bash
cd /tmp/job-scout-final && test ! -e .job-scout/reports/archive/funnel-report-2024-12-29-0900.html && echo OK
```
Expected: `OK` (file deleted by archive cleanup).

- [ ] **Step 6: Tick all ROADMAP checkboxes**

Now that all 19 tasks have been verified end-to-end, update `docs/ROADMAP.md` to mark every Phase 4 task complete:

For every line matching `- [ ] **Task N: ...**` under the "## Phase 4 — v0.7.0: Visual render layer" section, change `- [ ]` to `- [x]`.

Also update the row in the "Status at a glance" table at the top:

Find:
```
| **4. Visual render layer** | v0.7.0 | In progress | [`specs/2026-04-29-visual-render-layer-design.md`](superpowers/specs/2026-04-29-visual-render-layer-design.md) | [`plans/2026-04-29-visual-render-layer.md`](superpowers/plans/2026-04-29-visual-render-layer.md) |
```

Replace with:
```
| **4. Visual render layer** | v0.7.0 | Shipped — v0.7.0 | [`specs/2026-04-29-visual-render-layer-design.md`](superpowers/specs/2026-04-29-visual-render-layer-design.md) | [`plans/2026-04-29-visual-render-layer.md`](superpowers/plans/2026-04-29-visual-render-layer.md) |
```

Find the "Current focus:" line and replace with:
```
**Current focus:** All four phases complete. Plugin is at v0.7.0. Future phases (Tier 2 visual coverage, dark mode, charts) gated on user need.
```

Update the CHANGELOG: change `## [0.7.0] — 2026-04-29 (in progress)` to `## [0.7.0] — 2026-04-29` (drop the "in progress" suffix).

Append to ROADMAP `## Log`:

```
- **2026-04-29** — Phase 4 shipped as v0.7.0. Six Tier 1 commands now render Modern-Cards HTML reports auto-opened in Chrome with markdown fallback.
```

- [ ] **Step 7: Verify**

```bash
cd /Users/tura/git/claude-job-scout && grep -c "Shipped — v0.7.0" docs/ROADMAP.md
```
Expected: `1`.

```bash
cd /Users/tura/git/claude-job-scout && grep -c "\\- \\[x\\] \\*\\*Task" docs/ROADMAP.md
```
Expected: at least `19` more than before this task started (one per Phase 4 task).

```bash
cd /Users/tura/git/claude-job-scout && grep -c "## \[0.7.0\] — 2026-04-29$" CHANGELOG.md
```
Expected: `1`.

```bash
cd /Users/tura/git/claude-job-scout && git status -s
```
Expected: 1–2 modified files (ROADMAP.md and possibly CHANGELOG.md).

- [ ] **Step 8: Commit + push + tag**

```bash
cd /Users/tura/git/claude-job-scout && git add docs/ROADMAP.md CHANGELOG.md && git commit -m "$(cat <<'EOF'
Release v0.7.0 — Visual render layer

Final smoke confirmed all six Tier 1 commands render correctly
across HTML, markdown, and fallback paths. Lifecycle cleanup
verified on funnel-report rotation (90d) and archive deletion
(365d). All 19 Phase 4 tasks ticked. Plugin moves to v0.7.0
status: shipped.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)" && git push -u origin phase-4/task-19-final-smoke
```

After merge to main, tag the release:

```bash
cd /Users/tura/git/claude-job-scout && git checkout main && git pull && git tag -a v0.7.0 -m "Release v0.7.0 — Visual render layer" && git push origin v0.7.0
```

---

## Plan summary

19 tasks, branched off `main` and merged serially. Each task is independently verifiable via shell spot-checks plus (where appropriate) end-to-end runs in a scratch workspace at `/tmp/job-scout-*`.

**Foundational tasks (1–9):** must land before any Tier 1 wiring.

**Vertical-slice validation (10–11):** wires `/match-jobs` first, smoke-tests it, captures token measurements, and propagates the measured range into the spec and the orchestration reference. This is the gate before the remaining five views are wired.

**Per-view wiring tasks (12–16):** can be developed in parallel branches but must merge in numerical order. Each follows the same shape: HTML template + markdown template + insert "Render" step into the existing SKILL.md + bump skill version.

**Release tasks (17–19):** CLAUDE.md hard rule, gitignore, plugin.json + ROADMAP + CHANGELOG + README, final 6-command end-to-end smoke + ROADMAP ticks + git tag.

**Total estimated effort:** 12–16 hours of focused work (foundations 5–7h, per-view wiring 4–5h, release prep + smoke 3–4h). Execution may be subagent-driven for parallelism on tasks 12–16.

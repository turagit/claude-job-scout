# Visual Render Layer — Design Spec

**Date:** 2026-04-29
**Target release:** v0.7.0 ("Phase 4 — Visual render layer")
**Author:** brainstormed with Claude (`/superpowers:brainstorming`)
**Status:** Approved design, pending plan

---

## 1. Goal & Scope

### Goal

Tier 1 user-facing commands no longer present their results as raw terminal markdown. Each one produces a beautified, self-contained HTML report (Modern Cards aesthetic, light interactivity) that auto-opens in the user's logged-in Chrome via the existing Claude Chrome extension. The terminal still receives a 2–3 line summary so the conversation flow is preserved.

This is a presentation layer added on top of existing commands — it does not change what those commands compute, only how their results are displayed.

### In scope (v0.7.0)

Six Tier 1 commands gain HTML rendering:

- `/job-search`
- `/match-jobs`
- `/check-job-notifications`
- `/funnel-report`
- `/check-inbox`
- `/interview-prep`

Plus the supporting infrastructure:

- A new internal skill `_visualizer` (subagent dispatched via `Agent`).
- Templates, theme tokens, and a small interactive-JS asset bundle.
- A `render` config key in `.job-scout/config.json` with first-run prompt.
- A 0.6 → 0.7 schema migration.
- A small `/config` helper command for changing `render` mode without editing the file.

### Out of scope (v0.7.0)

- Tier 2 commands (`/analyze-cv`, `/cover-letter`, `/optimize-profile`) — bundled in a v0.8.0 follow-up if v0.7.0 is well-received.
- Tier 3 admin commands (`/apply`, `/create-alerts`, `/index-docs`) — stay terminal-only permanently.
- Dark mode — light theme only for v0.7.0.
- Cross-report search/comparison ("diff today vs yesterday").

---

## 2. User-facing surface

### First-run config prompt

The first time a Tier 1 command is invoked after the v0.7.0 upgrade, the orchestrator detects that `.job-scout/config.json` is missing a `render` key and prompts once:

```
How should command output be displayed?

  always  — Render as a styled HTML report and auto-open in Chrome.
            Best experience. Adds modest token overhead per command
            (the visualizer subagent inlines templates + assets).
  never   — Show output as styled markdown directly in this window.
            Lower token cost. No browser hop.
  ask     — Decide per-command at the end of each run.

Choice [always]: _
```

The user's response writes the chosen value to `.job-scout/config.json` under the `render` key. The prompt is shown only on this first invocation; afterwards the user changes their preference via `/config render <mode>` or by editing the file.

The token-overhead description is intentionally qualitative in v0.7.0. A measured range will replace it in a follow-up patch once a real-world `_visualizer` dispatch has been observed (see Section 7).

### Per-invocation behaviour

| `render` value | Behaviour at end of each Tier 1 command |
|----------------|------------------------------------------|
| `always`       | Render HTML, open in Chrome. Print summary line in terminal. |
| `never`        | Render styled markdown via `_visualizer`, print in terminal. No HTML written. |
| `ask`          | At end of command, prompt the user (see below). |

The `ask`-mode prompt:

```
Render this report as HTML in Chrome? (y/N)
  y = styled HTML in Chrome (adds modest token overhead)
  N = styled markdown in this window
```

### Terminal summary (always printed)

Even when HTML rendering fires, the orchestrator prints a short 2–3 line summary to the conversation. Example for `/match-jobs`:

```
✓ 4 matches scored — A:2 B:2 — opened report in Chrome
```

The HTML is the deep view; the terminal line is the receipt. This keeps the conversation legible when scrolling back through history without having to reopen browser tabs.

### Chrome-open mechanic

After writing the HTML, the orchestrator calls the Chrome extension's existing "navigate to URL" capability with `file://<absolute-path-to-report>`. If `file://` is blocked by the browser or the extension fails to open the file, the orchestrator falls through to the fallback chain in Section 6 — there is no alternative open-mechanic in v0.7.0.

### `/config` command

A small new user-facing command:

```
/config render <always|never|ask>
```

Writes the chosen value into `.job-scout/config.json`. No other config key is exposed via this command in v0.7.0 — it exists solely so the user can flip render mode without editing JSON. Per the plugin's hard rules, this command carries `disable-model-invocation: true`.

---

## 3. Architecture

### Data flow

```
┌──────────────────────────────────┐
│ Tier 1 command (orchestrator)    │   e.g. /match-jobs
│ 1. Performs its core work        │
│ 2. Builds structured payload     │   { view, data }
│ 3. Reads config.render            │
│ 4. If render → dispatch ─────────┐│
│ 5. Open returned path in Chrome  ││
│ 6. Print terminal summary        ││
└──────────────────────────────────┘│
                                    ▼
                ┌──────────────────────────────────┐
                │ _visualizer subagent             │
                │  - Loads template for { view }   │
                │  - Loads theme tokens + assets   │
                │  - Embeds data as JSON           │
                │  - Inlines CSS + interactive JS  │
                │  - Writes file to .job-scout/    │
                │    reports/                      │
                │  - Returns delta:                │
                │      { path, format, bytes }     │
                └──────────────────────────────────┘
```

### Why a subagent (not inline)

This decision tracks the existing subagent protocol (`shared-references/subagent-protocol.md`) and the precedent set by `_company-researcher` and `_cv-section-rewriter`. Specifically:

- **Token isolation.** Verbose HTML (≈ 30–50 KB per report) never enters the orchestrator's reasoning context. The subagent reads the data in, writes the file, and returns only `{ path, format, bytes }` — a delta-return well under 100 tokens.
- **Single owner of templates and theme.** Template strings and theme tokens live in one skill, not duplicated across six command orchestrators.
- **Clean failure surface.** A subagent that fails returns a typed error; the orchestrator can fall through to the markdown path without entangling rendering logic into command code.

Rendering is not parallelised — one report per command, one subagent per command run. Parallelism is not the value here; isolation is.

### File layout

```
skills/_visualizer/
  SKILL.md                            # subagent contract; entry point
  references/
    rendering-protocol.md             # input JSON schema, output contract,
                                      # token budget, supported formats
    theme-tokens.md                   # color/spacing/type tokens
    component-library.md              # cards, chips, score-pills, headers,
                                      # timeline-items, fold, metric-block
  templates/
    base.html.j2                      # frame: doctype, head, theme link,
                                      # JS bootstrap, JSON data slot
    base.md.j2                        # markdown frame
    html/
      match-jobs.html.j2
      job-search.html.j2
      check-job-notifications.html.j2
      funnel-report.html.j2
      check-inbox.html.j2
      interview-prep.html.j2
    markdown/
      match-jobs.md.j2
      job-search.md.j2
      check-job-notifications.md.j2
      funnel-report.md.j2
      check-inbox.md.j2
      interview-prep.md.j2
  assets/
    theme.css                         # inlined into every HTML report
    interactive.js                    # ~3 KB sort/filter/expand/copy

docs/superpowers/specs/
  2026-04-29-visual-render-layer-design.md   # this file

skills/<each Tier 1 skill>/SKILL.md          # gains "Step N: render" section
.job-scout/                                  # new files (gitignored)
  reports/
  config.json                                # gains `render` key
```

### Templating engine

Jinja2-style placeholders interpreted by `_visualizer` itself via deterministic string substitution. Each template file is human-readable HTML or Markdown with `{{ data.foo }}` and `{% for x in data.list %}` constructs. The subagent expands these against the input data and returns the resulting file path.

There is no Python runtime, no external Jinja library, no build step. The engine is the subagent's own loop: load template, walk the AST of the syntax it supports, write the result. The supported syntax surface is intentionally narrow:

- `{{ <dot.path> }}` — value substitution with HTML-escaping by default
- `{{ <dot.path> | raw }}` — substitution without escaping
- `{% for item in <dot.path> %} … {% endfor %}` — iteration
- `{% if <dot.path> %} … {% endif %}` — conditional rendering (truthy on non-empty / non-zero)

Anything more complex (filters, macros, includes) is out of scope. If a template needs more, the data shape changes upstream — not the engine.

### Asset embedding

`theme.css` and `interactive.js` are inlined into every HTML report. No `<link>` tags, no `<script src>`. Each report is a single self-contained file that:

- Survives moving, archiving, or emailing.
- Is immune to later theme changes (a 6-month-old report still looks like itself).
- Has zero runtime network dependencies.

The price is per-report bloat (~10 KB CSS + ~3 KB JS, gzip-friendly inside the file). At v0.7.0 expected report counts (single-digit per day), this is negligible.

### Subagent contract

Input (passed via `Agent` tool):

```json
{
  "view": "match-jobs",
  "format": "html",
  "data": { ... },
  "output_dir": "/abs/path/to/.job-scout/reports"
}
```

Allowed `view` values: `match-jobs`, `job-search`, `check-job-notifications`, `funnel-report`, `check-inbox`, `interview-prep`.
Allowed `format` values: `html`, `markdown`, `plain`.

Successful return (delta-return rule applies):

```json
{
  "ok": true,
  "path": "/abs/path/to/.job-scout/reports/match-jobs-latest.html",
  "format": "html",
  "bytes": 38421
}
```

Error return:

```json
{
  "ok": false,
  "error": "schema_mismatch" | "budget_exceeded" | "template_missing" | "io_error",
  "detail": "<one-line>",
  "path": null
}
```

Token budget: input + output capped per the existing subagent protocol. Budget for `_visualizer` set during plan task 1 once a real render is measured.

### Touched files in existing skills

Each of the six Tier 1 SKILL.md files gains a final "Step N: render" section that reads the `render` config, dispatches `_visualizer`, opens the returned path, and prints the terminal summary. The pre-render steps in those skills are unchanged. CLAUDE.md gets a one-line addition under "Hard rules" reminding agents to dispatch via `_visualizer` rather than rendering inline.

---

## 4. Visual system (Modern Cards)

### Personality

The chosen direction is "Modern Cards" — Stripe / Linear-marketing aesthetic. Soft gradients, pill-shaped score chips, tag chips, generous card surfaces, gentle shadows. The reports should feel like a polished SaaS dashboard, not a printed document or a developer dashboard.

### Theme tokens

Single source of truth in `assets/theme.css`, inlined per render:

```css
:root {
  --bg-page:        linear-gradient(180deg, #ffffff 0%, #f5f3ff 100%);
  --bg-card:        #ffffff;
  --surface-soft:   #f5f3ff;
  --accent-from:    #7c3aed;        /* violet 600 */
  --accent-to:      #ec4899;        /* pink 500 */
  --accent-warn:    #fbbf24;        /* amber 400, B-tier */
  --accent-warn-fg: #78350f;        /* amber 900 */
  --accent-mute:    #9ca3af;        /* gray 400, C-tier */
  --text-strong:    #1f1f2e;
  --text-muted:     #6b7280;
  --ring-soft:      rgba(124, 58, 237, 0.10);
  --shadow-card:    0 1px 3px rgba(0, 0, 0, .04),
                    0 8px 24px rgba(124, 58, 237, .08);
  --radius-card:    12px;
  --radius-pill:    999px;
  --font-sans:      'Inter', -apple-system, system-ui, sans-serif;
  --font-mono:      'JetBrains Mono', 'SF Mono', monospace;
}
```

### Component library

Every template composes from the same set of HTML class primitives, defined in `assets/theme.css`:

- `.report-header` — gradient star icon, title, subtitle line ("4 roles · 2 strong fits").
- `.job-card` / `.thread-card` / `.event-card` — base card with hover-lift, accent-ring, rounded-12 corners.
- `.score-pill` — gradient background for A-tier (≥ 80), amber for B-tier (60–79), gray for C-tier (< 60).
- `.tag-chip` — soft purple/pink pill chips for keywords, stack, signals.
- `.metric-block` — used in `funnel-report` for big-number stats with delta arrows.
- `.timeline-item` — chronological lists in `check-inbox` and `interview-prep`.
- `.fold` — collapsible section with chevron, JS-backed expand/collapse.
- `.empty-state` — empty-data hero used when a command produced zero results.

### Per-view template responsibilities

| View | Hero | Body | Interactive bits |
|------|------|------|------------------|
| `match-jobs` | "N matches · A:x B:y" header | `.job-card` list, sorted by score | sort by score / date / company; filter by tier |
| `job-search` | Query echo + result count | `.job-card` list, by recency | filter by tier / saved |
| `check-job-notifications` | Notification feed timestamp | `.event-card` chronological | mark-as-read; filter unseen |
| `funnel-report` | "Pipeline · this week" | `.metric-block` grid + stage breakdown | hover tooltips on stage bars |
| `check-inbox` | "N threads · M unread" | `.thread-card` per recruiter | expand thread; filter unread |
| `interview-prep` | Role + company hero | sectioned `.fold` blocks per prep area | expand / collapse; copy-to-clipboard |

### Print stylesheet

A small `@media print` block in `theme.css` removes hover effects, switches the page background to white, and sets sensible page-break rules. Reports save cleanly to PDF if the user prints them; this is in scope because it's a CSS-only addition.

### Markdown templates

Markdown templates produce styled, terminal-friendly Markdown. They use:

- `#`, `##`, `###` headings.
- Tables for list views (sorted; tier in a column).
- Emoji as score indicators (🟢 A, 🟡 B, ⚪ C) — survives ANSI-light terminals; meaningful at a glance.
- Bullet hierarchy for `interview-prep` sections.
- A trailing `_Generated YYYY-MM-DD HH:MM_` line on every markdown report.

Markdown reports render directly inside the Claude Code conversation window via Markdown rendering — no file is written.

---

## 5. Lifecycle, files, and config

### Report locations

```
.job-scout/
  reports/
    match-jobs-latest.html
    job-search-latest.html
    check-job-notifications-latest.html
    check-inbox-latest.html
    funnel-report-2026-04-29-1430.html        # timestamped
    funnel-report-2026-04-28-0915.html
    interview-prep-stripe-senior-be-2026-04-29-1430.html
    archive/
      funnel-report-2026-01-29-1100.html      # auto-rotated when > 90 days
```

### Naming rules

- **Snapshot views** (`match-jobs`, `job-search`, `check-job-notifications`, `check-inbox`): filename is `<view>-latest.html`. Overwritten on each run. One file per view, ever.
- **Time-series views** (`funnel-report`, `interview-prep`): filename is `<view>-<YYYY-MM-DD-HHMM>.html`. `interview-prep` adds a `-<role-slug>` segment because each invocation targets a different role (slug derived from `tracker-id` plus a 4-character disambiguating suffix).

### Retention

- Snapshot views: no retention policy. One file per view; always-current.
- Time-series views: a file in `.job-scout/reports/` older than `render_retention_days` (default 90) moves to `.job-scout/reports/archive/`. A file in `archive/` older than `render_archive_days` (default 365) is deleted.
- Cleanup runs lazily at the start of each Tier 1 command — a cheap directory scan, no separate cron.

### Config schema

`.job-scout/config.json`:

```json
{
  "render": "always",
  "render_retention_days": 90,
  "render_archive_days": 365
}
```

Only `render` is exposed via the first-run prompt and `/config render <mode>`. The retention numbers are documented but not surfaced in UI; power users edit the file directly.

### State versioning

A 0.6 → 0.7 entry is added to `.job-scout/schema-version`'s migration runner (the existing scaffolding from Phase 1). The migration:

1. Adds `render_retention_days: 90` and `render_archive_days: 365` if missing.
2. Creates `.job-scout/reports/` and `.job-scout/reports/archive/` if they don't exist.
3. Bumps the schema version file's content from `0.6` to `0.7`.

The migration deliberately does **not** write the `render` key. Its absence is the signal that the first-run prompt (Section 2) has not yet fired; the prompt sets the key on first user answer. This keeps the first-run UX out of the migration runner's responsibilities.

Migration is idempotent (running it twice is a no-op).

### Repository hygiene

`.gitignore` already covers `.job-scout/`. The brainstorming-related `.superpowers/` directory is added to `.gitignore` as part of v0.7.0 (small chore; covers the visual-companion sessions used to design this spec).

---

## 6. Error handling & fallback

### The fallback chain when `render: "always"`

1. Orchestrator dispatches `_visualizer` with `format: "html"`.
2. **Render OK + Chrome opens** → terminal summary printed; done.
3. **Render fails** OR **Chrome can't open the file** → orchestrator prompts the user:
   ```
   ⚠ Couldn't open in Chrome (<reason>).
   Show output here as text instead? (Y/n)
   ```
4. **User answers `Y` (or hits Enter)** → orchestrator re-dispatches `_visualizer` with `format: "markdown"`. The rich markdown renders inside the conversation window. If an HTML file was successfully written but couldn't be opened, the path is preserved and printed so the user can open it manually later.
5. **User answers `n`** → orchestrator prints the absolute path of the written HTML (if any) plus a one-line "Open manually." hint, and returns. No further rendering.
6. **Markdown render itself fails** → orchestrator dispatches `_visualizer` once more with `format: "plain"` (a flattened structured text dump that is the last-resort safety net) and prints the result. This path never blocks the user.

The fallback prompt is intentionally not warned about token cost: this path goes from expensive (HTML) to cheap (markdown). Warning about cost when de-escalating cost would be confusing.

### `render: "never"` mode

`never` mode uses the same markdown path — `_visualizer` dispatched with `format: "markdown"`. It is no longer "today's terminal output"; it is the same styled markdown that the fallback path produces. Users who pick `never` for token reasons still receive a polished view, just inline rather than in Chrome.

### Empty data

When a command finds nothing (`/match-jobs` returns zero jobs, `/check-inbox` is empty), the renderer still produces a report. HTML reports show an `.empty-state` hero ("No new matches today.") with a one-line hint. Markdown reports show a heading plus a friendly empty line. Consistency over conditional rendering — the user always knows the command ran successfully.

### Subagent budget exceeded

Per the existing `subagent-protocol.md` rules, `_visualizer` enforces its own input + output token budget. If exceeded it returns:

```json
{ "ok": false, "error": "budget_exceeded", "detail": "...", "path": null }
```

Orchestrator falls through to the fallback chain (step 3 above). In practice the templates are small enough (<5 KB each) and the data payloads bounded enough that this should never trigger; the contract is explicit so a runaway data shape (e.g., a `match-jobs` payload with 5,000 jobs) fails predictably.

### Schema mismatch

Each template begins with a 5-line schema check (required keys present, types match). Failure returns:

```json
{ "ok": false, "error": "schema_mismatch", "detail": "missing: data.jobs[].score", "path": null }
```

Orchestrator falls through to the fallback chain. The diagnostic is appended to `.job-scout/cache/visualizer-errors.log`, which is auto-pruned to the last 50 lines. This file is the iteration surface for tightening templates against real data over time.

### Stale reports

No staleness detection in v0.7.0. If a user opens `match-jobs-latest.html` from yesterday, that's their yesterday — not a bug. The header includes a "generated YYYY-MM-DD HH:MM" line so every report is self-dating.

---

## 7. Testing & validation

No automated test suite (per CLAUDE.md). Validation is manual end-to-end runs in a scratch workspace, plus shell spot-checks. Each plan task names its specific verification step.

### Per-view smoke test (six total — one per Tier 1 command)

1. Run the command in a scratch `.job-scout/` workspace seeded with realistic data.
2. Verify HTML written to the expected path; confirm it opens in Chrome via the extension.
3. Verify Modern Cards aesthetic — score pills correct (A vs B vs C), no broken styles, fonts loaded.
4. Click each interactive element (sort, filter, fold, copy) and verify behaviour.
5. Re-run with `render: "never"`; verify markdown rendered in-window.
6. Force a failure (e.g., delete a template mid-run); verify the fallback prompt fires and `Y` delivers markdown.

### Shell spot-checks (post-render, per command)

```bash
# File exists and is non-empty
test -s .job-scout/reports/match-jobs-latest.html

# Self-contained — no external <link href> or <script src>
! grep -E '<link[^>]+href|<script[^>]+src' .job-scout/reports/match-jobs-latest.html

# Embedded JSON parses
sed -n '/<script type="application\/json"/,/<\/script>/p' \
    .job-scout/reports/match-jobs-latest.html | \
  sed '1d;$d' | jq -e .

# Header timestamp present
grep -q 'generated 20[0-9][0-9]-[01][0-9]-[0-3][0-9]' \
    .job-scout/reports/match-jobs-latest.html
```

### Token-cost measurement (deferred)

Originally this section gated the prompt-copy placeholder behind a measured range from a real `/match-jobs` and `/funnel-report` dispatch. The v0.7.0 release ships without that measurement: the prompt copy now reads "Adds modest token overhead per command" (qualitative) instead of a numeric range. Rationale:

- The end-to-end smoke (Task 19 in the implementation plan) was deferred from the v0.7.0 cut. Without a real dispatch, fabricating a numeric range would be misleading.
- The plugin is markdown-skill-only (no compiled engine), so first real-world use *is* the smoke. Measurements captured then become the v0.7.1 patch.

To collect the measurement post-v0.7.0:

1. Run `/match-jobs` with `render: "always"` against a realistic payload (≥10 jobs).
2. Capture the `_visualizer` subagent's input + output token counts from the dispatch metadata.
3. Repeat for `/funnel-report`.
4. Open a v0.7.1 patch branch; add a "Token cost reference" subsection here with the measured table; replace the qualitative "modest token overhead" wording in Section 2 (two places) and `skills/shared-references/render-orchestration.md` (two places) with the range (e.g., "≈ 1.5–3.2k extra tokens per render").

### Lifecycle / retention test

1. Touch a fake `funnel-report-2025-12-29-1100.html` (>90 days old).
2. Run any Tier 1 command.
3. Verify the old file moved into `archive/`.
4. Touch one in `archive/` dated 2024-12 (>365 days). Run again. Verify it's deleted.

### Fallback chain end-to-end

1. With the Chrome extension *not* connected: run `/match-jobs`. Verify the fallback prompt fires; `Y` delivers styled markdown in-window; the HTML file path is still printed.
2. With a corrupted template: run `/match-jobs`. Verify the diagnostic landed in `visualizer-errors.log` and the fallback markdown still rendered.
3. With `render: "never"`: run `/match-jobs`. Verify markdown-only path runs cleanly with no HTML file written.

---

## 8. Out of scope & future work

### Deferred to v0.8.0 (or later)

- **Tier 2 commands** — `/analyze-cv`, `/cover-letter`, `/optimize-profile` get the same `_visualizer` treatment. Templates only; the subagent infrastructure already exists by then. Estimated 1–2 days of work.
- **Dark mode.** Theme tokens are already abstracted in `assets/theme.css`; adding a dark variant is a CSS-only PR. Probably ships with Tier 2.
- **Cross-report comparison views.** "Show me funnel-report week-over-week," or "diff today's match-jobs vs yesterday's." Useful but a real feature, not a polish pass — separate spec.
- **Print/PDF stylesheet polish.** v0.7.0 ships a basic `@media print` block. A real "looks great as PDF" pass — page breaks, headers/footers, palette adjustments — is its own spec.
- **Embedded charts in `funnel-report`.** v0.7.0 uses `.metric-block` with bar-style HTML/CSS. If users ask for proper line/bar charts of pipeline health over time, an inline SVG chart helper would be added to `_visualizer/assets/`. Not in scope.

### Explicitly not on the roadmap

- **Localhost static server.** If `file://` blocking is real for some users, the markdown fallback handles it. We will not ship a long-running local process to work around browser permission policies.
- **Editing reports in-browser.** Reports are read-only artifacts.
- **Sharing / exporting via email or Slack.** Reports are local files; users can attach or print as they like.
- **Cross-project report aggregation.** The plugin is per-project by design.
- **A full SPA.** Reports stay single static HTML files.

### Versioning impact

- `.claude-plugin/plugin.json` bumps to `0.7.0` (semver minor; new feature surface).
- Each of the six Tier 1 SKILL.md files gets a `version:` frontmatter bump. Their contracts change because they now produce HTML in addition to / instead of terminal markdown.
- A new `_visualizer/SKILL.md` ships at version `1.0.0`.
- `.job-scout/schema-version` migrates from `0.6` to `0.7` (idempotent migration described in Section 5).
- `CHANGELOG.md` gets a v0.7.0 section under Keep a Changelog conventions.
- `docs/ROADMAP.md` gets a new entry: "Phase 4 — v0.7.0: Visual render layer" and a status row in the table at the top.

---

## 9. Open questions to settle during the implementation plan

These do not block design approval; they are notes for the plan-writing skill.

- **Exact slug rule for `interview-prep` filenames** — current proposal is `tracker-id` plus a 4-character disambiguator. The plan task that builds `interview-prep` rendering verifies this against real tracker-id shapes.
- **Template syntax engine — implementation choice.** The narrow Jinja-style surface described in Section 3 is the contract; the plan task for `_visualizer` decides whether to implement it as a small parser or to lean on a tiny dependency. Either way, the supported syntax surface does not grow.
- **Token budget for `_visualizer`.** Set during plan task 1 once a real render is measured. Recorded in `subagent-protocol.md` alongside the existing budgets.

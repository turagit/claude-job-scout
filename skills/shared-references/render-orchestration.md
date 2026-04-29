# Render Orchestration

The procedure every Tier 1 user-facing command follows after computing its output, when the user has opted in to HTML rendering. Centralised here because all six Tier 1 commands implement the identical lifecycle: build a payload → consult `render` config → maybe dispatch `_visualizer` → maybe open in Chrome → handle failure → print terminal summary.

## When to invoke

At the **end** of a Tier 1 command, after the command has computed its results and would otherwise print the terminal output. The procedure replaces (or augments, depending on render mode) that final print.

## Step A: Build the data payload

The dispatching skill builds a `data` object whose shape matches the requirements declared in `_visualizer/templates/html/<view>.html.j2`'s `{# schema: #}` frontmatter. The schema frontmatter is authoritative for each view's required keys.

Universal fields (every view):

```json
{
  "title": "<short hero title — see per-view rules below>",
  "subtitle": "<one-line subtitle>",
  "generated_at": "2026-04-29 14:30",
  "filename": "<view>-latest.html | <view>-2026-04-29-1430.html",
  "results": [ /* view-specific items, may be empty */ ]
}
```

Per-view extensions (only when the view's schema requires them):

- `tier_counts: { a, b, c, total }` — for views that bucket scored items: `match-jobs`, `job-search`, `check-job-notifications`. Populate all four keys (use `0` when none) so toolbar buttons render `(0)` rather than blank.
- `unread_count` — for `check-job-notifications` and `check-inbox`.
- `thread_count` — for `check-inbox`.
- `metrics`, `stages` — for `funnel-report`.
- `role`, `company`, `sections` — for `interview-prep`.
- `query` — for `job-search`.

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

The dispatcher uses the canonical scoring tiers from `_job-matcher` and passes the tier value directly to `_visualizer`:
- `score >= 85` → `"a"`
- `70 <= score < 85` → `"b"`
- `55 <= score < 70` → `"c"`

D-tier jobs (`score < 55`) are pre-filtered by `match-jobs` and `check-job-notifications` before reaching the renderer (per `_job-matcher`'s scoring framework); the visualizer never sees them. Templates render only `tier-a` / `tier-b` / `tier-c` pill variants.

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

The HTML render or open failed.

**`budget_exceeded` short-circuit:** if the visualizer returned `errors[0].code == "budget_exceeded"`, skip the prompt and re-dispatch with `format: "markdown"` directly. Print a one-line note `⚠ Report exceeded HTML budget; rendering as markdown.` before the markdown body. The user is not asked because there is no Chrome-open path to fall back from — the rendering itself is what failed.

For all other error codes (`schema_mismatch`, `template_missing`, `io_error`, or extension-unavailable), prompt the user as below.

Print exactly this prompt:

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

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

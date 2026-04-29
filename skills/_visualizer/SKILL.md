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

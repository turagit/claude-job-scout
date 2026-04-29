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

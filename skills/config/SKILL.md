---
name: config
description: View or change per-workspace plugin settings under .job-scout/config.json
allowed-tools: Read, Write, Edit, Bash
disable-model-invocation: true
---

View or change per-workspace plugin settings. Render settings live in `.job-scout/config.json`; ultramode settings (`api_keys`, `default`) live in `user-profile.json` under the `ultramode` block. This command exposes:

- `render` — how Tier 1 command output is displayed (in `config.json`).
- `ultramode key <provider> <token>` / `ultramode key <provider> --remove` — add / remove a provider API key (in `user-profile.json` `ultramode.api_keys`).
- `ultramode default <true|false>` — toggle whether ultramode runs without re-prompting (in `user-profile.json` `ultramode.default`).

## Step 0: Bootstrap workspace

Follow `shared-references/workspace-layout.md` to ensure `.job-scout/` exists.

## Step 1: Parse the invocation

The user types one of these forms:

```
/config
/config render
/config render <always|never|ask>
/config ultramode key <provider> <token>
/config ultramode key <provider> --remove
/config ultramode default <true|false>
```

- `/config` (no args) — show all current settings (render + ultramode).
- `/config render` — show the current value of `render`.
- `/config render <value>` — set `render` to the given value.
- `/config ultramode key <provider> <token>` — add or replace an ultramode provider key.
- `/config ultramode key <provider> --remove` — remove an ultramode provider key.
- `/config ultramode default <true|false>` — toggle `ultramode.default`.

## Step 2: Show current settings (no-arg invocation)

Read `.job-scout/config.json` (treat missing as `{}`) and `user-profile.json` (treat missing `ultramode` block as `{default: false, api_keys: {}, registry_built_at: null}`). Print:

```
Current settings (.job-scout/config.json):

  render               = <value or "(unset — first-run prompt will fire on next Tier 1 command)">
  render_retention_days = <value, default 90>
  render_archive_days  = <value, default 365>

Ultramode (user-profile.json → ultramode):

  ultramode.default    = <true|false, default false>
  ultramode.api_keys   = <comma-separated provider slugs that have a key, or "(none)"> 
  ultramode.registry_built_at = <ISO timestamp or "(not built — run /ultramode)">
```

**Never print key values** — list only which providers have a key set (the slug), never the token itself.

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
2. Set `render: "<value>"` on the in-memory object.
3. Write the entire updated object back via the `Write` tool (not `Edit`), preserving any other keys (e.g., `render_retention_days`, `render_archive_days`).
4. Confirm:

```
Set render = "<value>"
```

## Step 5: Add / remove an ultramode provider key (`/config ultramode key …`)

Ultramode API keys live in `user-profile.json` under `ultramode.api_keys` (a `{ "<provider>": "<token>" }` map) — **gitignored workspace state, never `config.json`, and never entered into a browser form.** The candidate pastes the token into the terminal here; ultramode looks it up at sweep time. See `../ultramode/SKILL.md` Step 5.

### `/config ultramode key <provider> <token>` — add or replace

1. Validate `<provider>` is a non-empty slug (`[a-z0-9-]+`, lowercased) and `<token>` is non-empty. If not, print `Usage: /config ultramode key <provider> <token>` and exit without writing.
2. Read `user-profile.json` (treat a missing `ultramode` block as `{default: false, api_keys: {}, registry_built_at: null}`).
3. Set `ultramode.api_keys["<provider>"] = "<token>"` on the in-memory object (merge — preserve every other key in `user-profile.json` and every other provider key).
4. Write the entire updated `user-profile.json` back via the `Write` tool (not `Edit`).
5. Confirm **without echoing the token**:

```
Set ultramode key for "<provider>" (token hidden). Stored in user-profile.json (gitignored).
```

### `/config ultramode key <provider> --remove` — remove

1. Read `user-profile.json`. If `ultramode.api_keys["<provider>"]` is absent, print `No key set for "<provider>".` and exit.
2. Delete that provider's entry from `ultramode.api_keys` (preserve all other keys), write the whole object back via `Write`.
3. Confirm: `Removed ultramode key for "<provider>".`

## Step 6: Toggle the ultramode default (`/config ultramode default <true|false>`)

Controls whether ultramode runs without re-prompting (default `false` — ultramode runs only on explicit `/ultramode`).

1. Validate `<value>` is `true` or `false`. If not, print `Invalid value. Allowed: true, false.` and exit without writing.
2. Read `user-profile.json` (treat a missing `ultramode` block as the default above).
3. Set `ultramode.default = <boolean>` (merge — preserve `api_keys`, `registry_built_at`, and every other key).
4. Write the whole object back via `Write`. Confirm: `Set ultramode.default = <value>`.

## Step 7: Validate the file is well-formed JSON after write

Re-read the file just written (`.job-scout/config.json` for render changes, `user-profile.json` for ultramode changes) and parse. If parsing fails, the in-memory object (which we know is well-formed because we just constructed it) is the recovery source: re-write it to disk via `Write` and re-parse. If that still fails, print the failure path and exit non-zero. The user can then inspect the file manually.

## Reference Materials

- **`shared-references/workspace-layout.md`** — `.job-scout/` layout and bootstrap procedure.
- **`shared-references/render-orchestration.md`** — describes how the `render` key is consumed by Tier 1 commands.
- **`shared-references/canonical-schemas.md`** — the `ultramode` block (`default`/`api_keys`/`registry_built_at`) in `user-profile.json`.
- **`../ultramode/SKILL.md`** — how `ultramode.api_keys` and `ultramode.default` are consumed; the keyless-first / never-in-a-browser-form key-handling rule.

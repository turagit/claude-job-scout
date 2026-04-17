---
name: index-docs
description: Re-scan workspace for supporting documents and rebuild the supporting-docs index
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
disable-model-invocation: true
---

Explicitly (re)scan the workspace for supporting documents and rebuild `.job-scout/cache/supporting-docs.json`. Phase 1's bootstrap auto-runs this scan once on workspace creation; this command is for users who add documents mid-session, want to re-scan after edits, or declined the bootstrap prompt and want to opt back in.

## Step 0: Bootstrap workspace

Follow `../shared-references/workspace-layout.md` to ensure `.job-scout/` exists in the current workspace.

## Step 1: Load existing index

Read `.job-scout/cache/supporting-docs.json`. If missing or empty, treat the current state as `{ "version": 1, "last_scanned": null, "docs": {} }` and proceed.

## Step 2: Run the workspace scan

Follow the scan procedure from `../shared-references/supporting-docs.md` — the "When the index is built" and "Re-indexing" sections describe the file extensions, exclusion list, classification heuristics, and hash logic. Do not duplicate that procedure here; load the reference and follow it.

## Step 3: Compute the diff

Compare the freshly-scanned state to the existing index. Categorise each entry:

- **New files** — extension matches the scan list, path not in current index.
- **Re-indexed files** — path in current index, content hash differs from stored hash (file edited since last scan).
- **Missing files** — path in current index, file no longer at path. Mark with `status: "missing"` (do not delete the entry).
- **Unchanged files** — hash matches; nothing to do.

## Step 4: Present the diff

Show the user a summary:

```
📎 Supporting-docs index update

  New files (N):
    - certs/aws-sa-pro-2026.pdf
    - talks/kubecon-2026-eda.pdf
    ... (showing first 10 of N)

  Re-indexed (N):
    - case-studies/migration-2024.pdf  (content changed)
    ... (showing first 10 of N)

  Missing (N):
    - portfolio/old-deck.pdf  (file moved or deleted)
    ... (showing first 10 of N)

  Unchanged: N

Apply changes? (Y/n)
```

If all four categories are empty, report "No changes detected" and exit.

## Step 5: Apply on approval

On approval:
1. For each new file: classify (filename heuristic + content inspection for first 5 inconclusive), generate a 200-word summary, compute SHA-256, add to the index.
2. For each re-indexed file: re-classify, re-summarise, update the hash.
3. For each missing file: set `status: "missing"` on the existing entry.
4. Update `last_scanned` to the current ISO timestamp.
5. Write the updated index back to `.job-scout/cache/supporting-docs.json`.
6. Report final counts.

On decline: leave the index untouched but report what would have changed.

## Special interaction: opt-back-in

If the user previously declined indexing at bootstrap (the supporting-docs reference's opt-out behaviour), running this command overrides that opt-out for this and future sessions. Display a single-line confirmation when this happens:

> "Re-enabling supporting-docs indexing for this workspace."

## Reference Materials

- **`../shared-references/supporting-docs.md`** — canonical scan procedure, classification heuristics, file shape
- **`../shared-references/workspace-layout.md`** — `.job-scout/` layout and bootstrap

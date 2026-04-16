# Supporting-Docs Index

The user's CV is the primary input, but the README asks users to bring everything that tells their professional story: certifications, talks, decks, case studies, recommendations, publications, portfolio files. This reference documents the shared index of those documents.

## Purpose

`.job-scout/cache/supporting-docs.json` lets downstream skills (`profile-optimizer` in Phase 1; `cover-letter-writer`, ATS simulator, and `/index-docs` in later phases) read a small summary of each document instead of re-parsing the originals. Docs are keyed by path and validated by content hash.

## File location

`.job-scout/cache/supporting-docs.json`

## Shape

```json
{
  "version": 1,
  "last_scanned": "2026-04-16T10:00:00Z",
  "docs": {
    "<workspace-relative-path>": {
      "type": "cert | talk | deck | recommendation | case_study | publication | portfolio | other",
      "hash": "<sha256>",
      "extracted_keywords": [],
      "summary_200w": "...",
      "last_indexed": "2026-04-16T10:00:00Z"
    }
  }
}
```

## Type taxonomy

- **cert** — certifications, diplomas, language tests, transcripts
- **talk** — conference slides, brown-bag decks, webinar recordings (linked), transcripts
- **deck** — architecture diagrams, design docs, RFCs, whiteboard exports
- **recommendation** — testimonials, client feedback, LinkedIn recommendations, screenshots of kind words
- **case_study** — post-mortems, project retrospectives, launch reports
- **publication** — papers, blog posts, patents, package pages
- **portfolio** — product screenshots, portfolio PDFs, media mentions
- **other** — catch-all; ask the user to re-categorise on next interactive pass

## When the index is built

On workspace bootstrap (first command invocation in a new workspace), after the `.job-scout/` folder is created, scan the workspace root (not `.job-scout/` itself) for files matching common supporting-doc extensions: `.pdf`, `.docx`, `.doc`, `.pptx`, `.key`, `.png`, `.jpg`, `.md`, `.txt`.

Exclude:
- The CV file itself (identified by the `cv.*`, `resume.*`, `curriculum.*` pattern or the path stored in `user-profile.json`).
- Anything inside `.job-scout/`, `.git/`, `node_modules/`, or any dotted directory.

Ask the user **once**:

> "I noticed these files in your workspace alongside the CV: [list first 10, summarise the rest]. They look like supporting materials — certificates, talks, case studies — that make every rewrite sharper. Want me to index them now? This is cached; I only re-read if a file's contents change."

On approval: read each file, classify by filename heuristics (e.g., `cert*.pdf` → `cert`, `*talk*.pdf` → `talk`, `*recommendation*` → `recommendation`), fall back to content inspection for the first N files where heuristics are inconclusive, and write the index. Generate a 200-word summary per doc. Compute SHA-256 over each file's bytes.

On decline: write an empty `docs: {}` with `last_scanned` set and do not prompt again in the same session.

## Re-indexing

On every command entry, re-scan the workspace:

1. Compare the file list against `docs` in the index.
2. For new files: classify, summarise, add to index.
3. For existing files: hash the content. If hash differs from stored hash, re-classify and re-summarise. Otherwise reuse.
4. For missing files: mark the entry with `"status": "missing"` but do not delete — the user may have moved the file temporarily.

Re-scans should be non-blocking: if a downstream skill needs the index immediately and the scan hasn't finished, the skill proceeds with whatever is already in the index and logs a warning.

## Consumer contract

Any skill reading `supporting-docs.json` must:

- Read the index, not the source files, for keyword and summary data.
- Cite the `path` when a claim on a CV or LinkedIn section derives from a specific doc (Phase 2 introduces this explicitly in `profile-optimizer` for the Featured section).
- Treat `type: "other"` as "ask the user before acting on this."

## Phase-1 scope

Phase 1 establishes the index and the workspace-scan/prompt behaviour. No consumer skill in Phase 1 is required to read it; the first consumer lands in Phase 2. Building the data now avoids backfilling later.

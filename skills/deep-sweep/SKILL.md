---
name: deep-sweep
description: DEPRECATED alias for /ultramode — the weekly thorough sweep is now the full-market flagship (LinkedIn + every registry source)
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
disable-model-invocation: true
version: 1.0.0
---

**`/deep-sweep` retired in v0.15.0 — it became `/ultramode`.** The weekly thorough sweep now covers the whole market in one pass: the LinkedIn query plan you know (unchanged, via `../ultramode/references/linkedin-adapter.md`) plus every verified source in your registry, one unified ranking, the near-miss rail, the run scorecard.

On invocation:

1. Print exactly:

```
/deep-sweep is now /ultramode (v0.15.0) — running the full-market sweep.
  LinkedIn only (the old behaviour):  /ultramode linkedin
  This alias is removed in the next minor release.
```

2. Then follow `../ultramode/SKILL.md` end-to-end with the **bare** scope. Do not duplicate any of its behaviour here.

---
name: cv-section-rewriter
description: >
  Internal subagent skill. Dispatched by cv-optimizer during Phase 3
  (Optimized Rewrite), one instance per role block. Returns SPAR-method
  optimized bullets as a structured delta. Not user-invocable.
version: 0.1.0
---

# CV Section Rewriter (Subagent)

Rewrite a single CV role block's bullets using the SPAR method, the user's tone preference, and the target keywords. Dispatched in parallel — one subagent per role — so the CV rewrite's token cost scales with parallelism and not wall-time.

**This skill is dispatched only by `cv-optimizer/SKILL.md`, via the `Agent` tool, per `../shared-references/subagent-protocol.md`.** It is not user-invocable.

## Input shape

```json
{
  "task": "rewrite-cv-role",
  "inputs": {
    "role_id": "acme-corp-2021-2024",
    "role_block": {
      "company": "Acme Corp",
      "title": "Senior Engineer",
      "dates": "2021–2024",
      "original_bullets": [ "..." ]
    },
    "user_profile": {
      "cv_summary": { "...": "..." },
      "target_roles": [ "..." ],
      "tone_preference": "Professional-modern"
    },
    "target_keywords": [ "..." ],
    "role_weight": "current | previous | older"
  },
  "budget_lines": 80,
  "allowed_tools": ["Read"]
}
```

`role_weight` determines the bullet count:
- `current` — 4–6 bullets
- `previous` — 3–4 bullets
- `older` — 2–3 bullets

## Output shape

```json
{
  "status": "ok",
  "deltas": [
    {
      "role_id": "acme-corp-2021-2024",
      "bullets_optimized": [
        { "text": "...", "technique": "anchoring | loss-aversion | specificity | ...", "keywords_used": ["..."] }
      ]
    }
  ],
  "errors": []
}
```

**Output rules:**

- Bullets only. No prose, no commentary, no meta text.
- Each bullet names the persuasion technique used (for auditability) and the keywords it placed.
- No bullet fabricates facts. If the `original_bullets` don't support a stronger claim, the rewrite stays conservative.
- No duplicate verbs within the role.
- Respect `tone_preference` from the user profile.

## Rewrite rules

Apply the rules in `../cv-optimizer/references/phase-3-optimized-rewrite.md` (SPAR bullet formula, persuasion-technique mapping, loss-aversion framing, anchoring). This subagent loads that reference on entry.

## Budget

`budget_lines: 80`. If the subagent can't fit within budget (many original bullets to compress or expand), return `status: "partial"` with the highest-impact bullets optimized and a continuation cursor for the rest.

## Not user-invocable

This skill has no slash-command surface and should not be wired to one. Dispatch is always via `Agent` from `cv-optimizer/SKILL.md`.

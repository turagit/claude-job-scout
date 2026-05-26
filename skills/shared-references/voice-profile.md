# Voice Profile

> **Single source of truth for the user's voice across every user-voiced draft.** The `tone` block in each workspace's `user-profile.json` carries the operational payload; this file explains what consumers do with it.

## Why this exists

Before this phase, `response-templates.md` carried structural instructions ("Thank them, ask qualifying questions") but no voice. Generic templates produce flat copy. The user's stated voice — **British, sophisticated, charming, classy (not over the top), likable, friendly, positive** — is now codified as data in `user-profile.json.tone`, consumed by every skill that drafts text in the user's name.

## Tone block shape

See [`canonical-schemas.md`](canonical-schemas.md) for the JSON shape. Fields:

| Field | Purpose |
|---|---|
| `register` | High-level descriptor of the formality and pacing. "considered, restrained, dry-witted". |
| `dialect` | `british` for this user — controls spelling (organise, programme), idiom, rhythm. |
| `warmth` | Where on the cold↔effusive axis to sit. "personable but never sycophantic; gracious not effusive". |
| `vocabulary_cues` | Concrete words and turns of phrase to favour — used as prompt anchors. |
| `exemplars` | Two to six full-sentence samples in the voice. Used as few-shot anchors at draft time. |
| `avoid` | Negative examples — phrases, registers, or spellings that break the voice. |

## Consumer skills (must read tone block at draft time)

- `_recruiter-engagement` — recruiter replies, follow-ups, warm-stale revivals.
- `_cover-letter-writer` — every cover letter.
- `_profile-optimizer` — LinkedIn About, Headline, Experience bullets.
- `_cv-optimizer` / `_cv-section-rewriter` — every bullet rewrite.
- `interview-prep` (orchestrator) — SPAR narratives, "questions to ask" lists.
- Any future user-voiced surface.

## Read pattern

```
1. Load .job-scout/user-profile.json.
2. Extract the `tone` block. If absent, fall back to a hard-coded neutral profile and warn.
3. Pass the tone block into the LLM prompt as a system-level constraint, with `vocabulary_cues` and `exemplars` as few-shot anchors and `avoid` as explicit negatives.
```

## Write pattern

The tone block is set once at `/analyze-cv` time and rarely changes. Updates go through `validate_profile`. A `/config tone` command (not in Phase 5; Phase 8 candidate) will let the user revise.

## Operational examples

A recruiter reply drafter should, at draft time, prepend to the LLM prompt:

```
You are drafting a reply on behalf of the user. The user's voice is:
- Register: {{tone.register}}
- Dialect: {{tone.dialect}}
- Warmth: {{tone.warmth}}
- Favour these words and phrasings: {{tone.vocabulary_cues | join: ", "}}
- Avoid: {{tone.avoid | join: ", "}}

Examples in the user's voice:
{% for ex in tone.exemplars %}
- "{{ex}}"
{% endfor %}

Draft the reply in this voice.
```

## Cross-workspace policy

Both workspaces carry the same tone block by default (the user's voice doesn't change between CVDIRECTOR and CVFREELANCER). Override per workspace is possible — just edit `user-profile.json.tone` in that workspace. The migration in Task 16 writes the same payload to both.

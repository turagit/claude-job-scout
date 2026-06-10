# Voice Profile

> **Single source of truth for the user's voice across every user-voiced draft.** The `tone` block in each workspace's `user-profile.json` carries the operational payload; this file explains what consumers do with it.

## Why this exists

Before this phase, `response-templates.md` carried structural instructions ("Thank them, ask qualifying questions") but no voice. Generic templates produce flat copy. Each user has a distinct voice (formality, register, dialect, vocabulary, things they would never say). Codifying that voice as structured data in `user-profile.json.tone` means every skill that drafts text in the user's name reads from one place — recruiter replies, follow-ups, cover letters, profile copy, CV bullet rewrites, interview-prep talking points all share the same voice anchors.

## Tone block shape

See [`canonical-schemas.md`](canonical-schemas.md) for the JSON shape. Fields:

| Field | Purpose |
|---|---|
| `register` | High-level descriptor of the formality and pacing. "considered, restrained, dry-witted". |
| `dialect` | English variant (`british`, `american`, `australian`, etc.) — controls spelling, idiom, rhythm. |
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
2. Extract the `tone` block. If absent, fall back to the British default below and warn.
3. Pass the tone block into the LLM prompt as a system-level constraint, with `vocabulary_cues` and `exemplars` as few-shot anchors and `avoid` as explicit negatives.
```

## British English is the plugin default

Unless `tone.dialect` explicitly says otherwise, **every user-voiced draft and every piece of user-facing plugin copy is British English** — spelling, idiom, rhythm, and date format (`10 June 2026`, never `06/10/2026`). This applies to recruiter replies, follow-ups, cover letters, profile copy, CV bullets, interview narratives, report copy, and conversational summaries.

**Americanisms to avoid (non-exhaustive):**

| Avoid | Prefer |
|---|---|
| -ize/-yze/-or spellings (optimize, analyze, color, behavior) | -ise/-yse/-our (optimise, analyse, colour, behaviour) |
| resume / résumé (in prose) | CV |
| reach out / touch base / circle back | get in touch / follow up / come back to |
| gotten | got |
| "I'm excited to..." as a reflex opener | "I'd be glad to…", "I'd welcome…" — enthusiasm shown through specificity, not exclamation |
| MM/DD dates, US-default `$` | `D Month YYYY`; currency from `requirements.rate_currency` / `salary_currency` |
| normalcy, oftentimes, off of | normality, often, off |

Identifiers are exempt: command names (`/analyze-cv`, `/optimize-profile`), directory and file names, JSON keys, CSS classes, and code stay exactly as they are — they are API surface, not prose.

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

A user with multiple workspaces typically wants the same voice across all of them — the user's voice doesn't change because they're searching different jobs. By default, a tone block configured in one workspace can be copied into others. Override per workspace is possible — just edit `user-profile.json.tone` in that workspace.

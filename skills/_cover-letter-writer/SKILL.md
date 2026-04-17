---
name: _cover-letter-writer
description: >
  [Internal subagent — dispatched only by /cover-letter, not user-invocable] Internal subagent skill. Dispatched by /cover-letter to draft three
  angle options (hiring-manager / recruiter-gate / culture-match) for
  a single job. Returns drafts as structured deltas. Not user-invocable.
version: 0.1.0
---

# Cover Letter Writer (Subagent)

Draft three cover-letter angle options for a single job. Each draft is ~250-350 words, structured as **hook → 2-3 evidence paragraphs (CV achievements + supporting-doc citations) → close with a specific ask**.

**This skill is dispatched only by `cover-letter/SKILL.md`, via the `Agent` tool, per `../shared-references/subagent-protocol.md`.** It is not user-invocable.

## Input shape

```json
{
  "task": "draft-cover-letter",
  "inputs": {
    "job": {
      "title": "Senior Data Engineer",
      "company": "Acme Corp",
      "jd_blob": "<full JD text>",
      "source": "tracker | url"
    },
    "user_profile": {
      "cv_summary": { "key_skills": [], "technologies": [], "top_achievements": [], "..." : "..." },
      "target_roles": ["..."],
      "tone_preference": "Formal-corporate | Professional-modern | Technical-dense | Let me decide"
    },
    "supporting_docs_index": {
      "paths": ["certs/aws-sa-pro.pdf", "case-studies/migration-2024.pdf", "..."],
      "types": ["cert", "case_study", "..."]
    },
    "target_keywords": ["..."],
    "linkedin_voice_sample": "<first 500 chars of About>"
  },
  "budget_lines": 200,
  "allowed_tools": ["Read"]
}
```

## Output shape

```json
{
  "status": "ok",
  "deltas": [
    {
      "angle": "hiring-manager",
      "draft": "<full markdown body of the cover letter, ~250-350 words>",
      "opening_two_sentences": "<for the orchestrator's preview>",
      "supporting_docs_cited": ["certs/aws-sa-pro.pdf"],
      "keywords_placed": ["Kubernetes", "AWS"]
    },
    {
      "angle": "recruiter-gate",
      "draft": "...",
      "opening_two_sentences": "...",
      "supporting_docs_cited": [],
      "keywords_placed": ["Python", "Spark", "AWS", "Kafka"]
    },
    {
      "angle": "culture-match",
      "draft": "...",
      "opening_two_sentences": "...",
      "supporting_docs_cited": ["case-studies/migration-2024.pdf"],
      "keywords_placed": ["Python"]
    }
  ],
  "errors": []
}
```

## The three angles

### Hiring-manager pitch

**Lead with:** the candidate's strongest CV achievement, framed against the JD. Treats the reader as a hiring manager who will read directly (not screened by a recruiter).

**Opening pattern:** "[Quantified achievement] — that's the kind of result your [JD-derived initiative] needs. I'm [Name], a [role] with [X years] in [domain]..."

**Best for:** roles where the hiring manager will read directly; established companies with low recruiter intermediation.

### Recruiter-gate

**Lead with:** keyword-dense opening that mirrors the JD's language. Optimised for ATS + recruiter screening, not the hiring manager.

**Opening pattern:** "I'm applying for the [exact JD title] role. As a [JD seniority] [JD role title] with experience in [JD-required-skill 1], [skill 2], and [skill 3]..."

**Best for:** larger companies with ATS + recruiter screening before any human review.

### Culture-match

**Lead with:** shared values / mission, references the company's own messaging (drawn from JD framing). Frames the candidate as someone who'd thrive in this specific company's environment.

**Opening pattern:** "Your team's commitment to [company value from JD] resonates with how I've approached my work in [domain]. As a [role]..."

**Best for:** mission-driven companies, public-benefit orgs, scale-ups with strong culture brand.

## Drafting rules (apply to all three angles)

- **Length:** 250-350 words. Anything longer is too much; anything shorter is too thin.
- **Structure:** hook (2-3 sentences) → 2-3 evidence paragraphs → close with a specific ask (interview, call, time slot).
- **Evidence paragraphs cite supporting docs.** When a claim maps to a doc in `supporting_docs_index`, cite the path inline: "(documented in `case-studies/migration-2024.pdf`)" or "(verifiable: `certs/aws-sa-pro.pdf`)". Track citations in the `supporting_docs_cited` array of the delta.
- **Keyword placement.** Place 3-5 target keywords from `target_keywords` naturally — not as a list. Track placements in the `keywords_placed` array.
- **Tone respects `tone_preference`.** Default to Professional-modern if unset.
- **Voice continuity.** The `linkedin_voice_sample` shows the user's About-section voice — match that register so the cover letter doesn't read as written by a different person.
- **No fabrication.** Every claim must be supportable from the CV summary or supporting docs. If a JD asks for a skill the user doesn't have, do not claim it.
- **No generic openers.** "I am writing to apply for..." is forbidden. Lead with substance.

## Budget

`budget_lines: 200`. Three drafts × ~50 lines each = ~150 lines, well within budget. If the subagent can't fit, return `status: "partial"` with the highest-priority drafts (always include `hiring-manager` if any are emitted).

## Not user-invocable

This skill has no slash-command surface. Dispatch is always via `Agent` from `cover-letter/SKILL.md`.

# Default Dimensions (universal bootstrap)

> **This is the default rubric used by `_job-matcher` when a workspace has not yet declared its own dimensions.** Each workspace can override by writing a `dimensions[]` array to `user-profile.json` (typically populated by `/analyze-cv` discovery against the user's specific CV, target_titles, segment, and requirements).

Five dimensions. Each scored A/B/C/D with evidence quotes pulled from the JD. The overall tier is derived from the dimension tiers per the rule at the bottom. **The criteria below are abstract**: they reason about the candidate's own `cv_summary`, `target_titles`, `requirements`, and the JD text. They make no assumptions about industry, role family, seniority, or tooling — they are equally valid for a baker, a construction engineer, a sales director, or a platform engineer.

## Dimensions

### 1. Skills & technical fit

Does the JD's required skill set have demonstrable evidence in the candidate's CV — directly named or strongly adjacent?

- **A:** Every required skill in the JD has direct or strong-adjacent evidence in the CV. CV shows depth (multi-year, multiple projects), not just exposure.
- **B:** Most required skills covered; one or two need a transferable-skill argument.
- **C:** Half or fewer required skills covered; meaningful gaps would need bridging.
- **D:** Core required skills absent; the CV-to-JD mismatch is structural.

Evidence to quote: pair each required-skill from the JD with the CV bullet, project, or section that demonstrates it. Operate on `cv_summary.key_skills`, `cv_summary.technologies`, and the JD's stated requirements — never against a hardcoded skill list.

### 2. Role shape match

Does the role's level, scope, and function match the candidate's `target_titles` and stated `seniority` / `seniority_floor`?

- **A:** Title and scope sit squarely within the candidate's declared `target_titles`. Seniority signal in the JD matches the candidate's level. Functional remit is one the candidate has done before.
- **B:** Title or scope is adjacent to declared targets (same family, slightly different angle). Seniority within ±1 level. Functional remit is mostly aligned.
- **C:** Title is at the right level but the functional remit is meaningfully different. Or scope is unclear in the JD.
- **D:** Title or scope is mismatched (e.g. asking a senior leader for IC work, or asking an IC for a function the candidate hasn't done).

Evidence: title, "function" or "remit" sentence, team-size or scope language in the JD.

### 3. Domain & context

Does the company's industry, sector, stage, and methodology overlap with the candidate's experience and stated preferences (including `industries_to_avoid` and `cv_summary.industries`)?

- **A:** Industry or sector directly matches the candidate's prior experience or `cv_summary.industries`. Company context (stage, ownership, methodology) suits the candidate's profile.
- **B:** Industry is adjacent or transferable (same regulatory regime, similar customer shape, comparable scale).
- **C:** Industry is new but the role is portable; some ramp-up required.
- **D:** Industry is hostile to the candidate's profile (e.g. asking for deep regulated-finance experience from someone with none, or asking a corporate operator for early-stage chaos).

Evidence: company About section, sector keywords, "we are…" lines in the JD.

### 4. Engagement fit

Does the practical shape of the role — work arrangement, contract type, duration, hours, geography, commercial terms — work for the candidate, given that hard dealbreakers have already been caught by `_gate-engine`? This dimension scores the *soft* commercial and practical fit *after* gates pass.

- **A:** All practical attributes (arrangement, contract type, duration, hours, location, rate/salary if disclosed) sit comfortably within the candidate's preferences. No friction.
- **B:** Practical attributes mostly fit; one or two are borderline (e.g. hybrid-2-days when fully-remote was preferred, or rate disclosed at the low end of the range).
- **C:** Practical attributes pass gates but require negotiation (rate gap, start-date gap, duration ambiguity).
- **D:** Practical attributes are technically allowed by the gates but uncomfortable enough to make the role unappealing in practice.

Evidence: work arrangement chip, contract-type line, duration/hours line, rate/salary line, location line.

### 5. Trajectory fit

How well does this opportunity advance the candidate's stated goals — visibility, growth, brand, learning, network, repeat-work potential, reputational upside?

- **A:** Strong forward-looking signal. The role would clearly advance the candidate's stated goals (career step, brand exposure, named end-client for freelance, learning a target technology, etc.).
- **B:** Reasonable trajectory fit. Some clear upside; nothing that would advance the candidate dramatically but also nothing that would stall them.
- **C:** Neutral trajectory. The role is a lateral move — pays the bills, doesn't move the needle on goals.
- **D:** Negative trajectory. The role would represent a step back, or comes with reputational / context-switch costs the candidate would regret.

Evidence: company brand signals, engineering culture indicators, named end client (for freelance), explicit growth path language, repeat-work hints.

## Overall tier derivation

| Dimension tiers | Overall tier |
|---|---|
| All A or one B (rest A) | **A** |
| Majority B, no C/D | **B** |
| Any C, no D | **C** |
| Any D in {Skills & technical fit, Role shape match, Engagement fit} | **D** |
| Any D in {Domain & context, Trajectory fit} but rest ≥ B | **C** |

The first three dimensions are *load-bearing*: a D in any of them produces an overall D. The last two are *modifying*: a D in either reduces the overall tier by one notch but does not auto-fail the job.

Hard gates are applied earlier in `_gate-engine`; any gated job is D before dimensions are computed.

## How workspaces customise

The default rubric above is the bootstrap. Each workspace can override by writing a `dimensions[]` array to `user-profile.json` — the per-workspace dimension set discovered by `/analyze-cv` based on the user's specific CV, target_titles, segment, and requirements. Examples:

- A construction-engineer workspace might rename dimension 1 to "Trades & tooling competence" and reweight.
- A baker workspace might replace dimension 5 with "Production volume & shift pattern".
- A sales-leadership workspace might split dimension 2 into "Quota responsibility" and "Team scope".

When `user-profile.json.dimensions[]` is non-empty, `_job-matcher` loads it; otherwise it falls back to this default.

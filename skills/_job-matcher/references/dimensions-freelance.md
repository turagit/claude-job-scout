# Dimensions — freelance

For `segment: freelance` workspaces.

## Dimensions

### 1. Skills (semantic)

Not keyword bingo. Evaluate whether the JD's required technologies have demonstrable evidence in the CV — same skill, called by a different name counts (e.g. JD says "GitOps tooling", CV mentions ArgoCD + FluxCD → A).

- **A:** Every required skill in the JD has direct or strong-adjacent evidence on the CV. CV shows depth (multi-year, multiple projects), not just exposure.
- **B:** Most required skills covered; one or two require transferable-skill argument.
- **C:** Half or fewer required skills covered; gaps would need bridging on the job.
- **D:** Core required skills absent; CV-to-JD mismatch.

Evidence: pair each required-skill from JD with the CV bullet / project that demonstrates it.

### 2. Engagement shape

Does the contract's shape (duration, hours, start date) suit the candidate?

- **A:** Duration 3–9 months, full-time hours, start date within candidate's stated availability window, named extension potential.
- **B:** Duration acceptable (e.g. 12+ months for an open-ended engagement, or 1–3 months for a clear sprint), full-time or part-time matching candidate preference.
- **C:** Duration ambiguous in JD; start date outside candidate's window by a few weeks; hours unclear.
- **D:** Sub-month gigs, "as-needed" hours, indefinite open-ended ICs.

Evidence: "duration", "start date", "hours per week" lines in JD.

### 3. Commercial fit

Does the rate (when disclosed) and terms (IR35 status, currency) work?

- **A:** Rate disclosed, at or above `min_day_rate`, IR35 outside (UK) or equivalent jurisdiction terms favourable, currency matches `rate_currency`.
- **B:** Rate disclosed and acceptable, IR35 status not stated but client type implies outside; or rate slightly below ideal but within negotiating range.
- **C:** Rate not disclosed (typical of agencies), but client/agency reputable and worth a qualification call.
- **D:** Rate disclosed and below floor (hard gate — should be caught by `_gate-engine`); IR35 inside without uplift; currency conversion at-loss.

Evidence: rate line, IR35 line, "via [agency]" or "end client" line.

### 4. Stack & methodology

Does the JD's tech stack and ways of working align with how the candidate wants to operate?

- **A:** Stack heavily overlaps CV's preferred technologies (Linux, Ansible, Terraform, Kubernetes, RHEL, FreeIPA, etc.). Methodology: GitOps, IaC, SRE practices, mature CI/CD — words the candidate uses.
- **B:** Stack overlaps in core areas (some Linux, some IaC) with extension into adjacent tech (e.g. Pulumi instead of Terraform). Methodology is sound.
- **C:** Stack partially overlaps; substantial unfamiliar components require ramp-up.
- **D:** Stack is largely unfamiliar (e.g. Windows-heavy, low-code platforms, .NET-only); methodology is anti-pattern (manual deploys, ticket-based ops).

Evidence: "Tech stack", "we use" lines in JD.

### 5. Client signals

Is this end-client direct, a reputable agency, or a body-shop pretending? Does the client likely lead to repeat work or a strong reference?

- **A:** Named end-client (not via undisclosed agency), brand has visible engineering culture / blog / open-source / talks. Reputational upside.
- **B:** Agency named, agency has track record of placing senior infrastructure people; end client identified.
- **C:** Agency, end client undisclosed, generic "exciting opportunity" copy.
- **D:** Anonymous agency, end client refused on contact, copy reads like mass outreach, sub-contractor pyramid signs.

Evidence: agency name, "end client" line, candidate-side reputation lookup.

## Overall tier derivation

| Dimension tiers | Overall tier |
|---|---|
| All A or one B (rest A) | **A** |
| Majority B, no C/D | **B** |
| Any C, no D | **C** |
| Any D in {Skills, Commercial fit, Stack & methodology} | **D** |
| Any D in {Engagement shape, Client signals} but rest ≥ B | **C** |

(Hard gates applied earlier in `_gate-engine`; gated jobs are D before dimensions are computed.)

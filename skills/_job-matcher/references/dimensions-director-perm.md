# Dimensions — director-perm

For `segment: director-perm` workspaces. Each scored job receives an A/B/C/D tier per dimension plus evidence quotes pulled from the JD. The overall tier is derived from the dimension tiers per the rule at the bottom.

## Dimensions

### 1. Leadership scope

Does the role's organisational scope match the candidate's prior scope?

- **A:** JD explicitly names: directly managing managers, P&L responsibility, org of 30+ engineers/staff, or named board-adjacent role (CTO/CIO/CPO/Head of X with department-level scope).
- **B:** JD names: managing 10–30 directly or through team leads, multi-team responsibility, no P&L but clear strategic remit.
- **C:** JD names: managing 5–10, single team, ambiguous on scope, or "Lead" title without scope clarity.
- **D:** JD names: IC, dotted-line management only, or a manager-of-1.

Evidence to quote: explicit team size, "managing X engineers", "owning P&L", "reporting to CTO/CEO".

### 2. Domain

Does the job's industry/sector overlap with the candidate's experience and stated preferences?

- **A:** Aerospace, space, scientific computing, large-scale R&D infrastructure (direct fit to user's ESA/ESTEC background); or top-tier financial services / regulated industries where the user has explicit experience.
- **B:** Adjacent regulated industries (govtech, energy, biotech, defence-adjacent enterprise IT), or large-enterprise IT where infrastructure scale is meaningful.
- **C:** General enterprise IT, financial services without explicit regulatory complexity, mid-market SaaS.
- **D:** Early-stage startups asking director-level for IC work; consumer web; consulting bodyshops.

Evidence: company description, sector keywords in JD.

### 3. Function

Does the functional flavour of the role match the candidate's track record?

- **A:** IT Director / Head of IT Services / Service Delivery Director / Head of Infrastructure / Head of Enterprise Architecture — directly listed in `target_titles`.
- **B:** Adjacent function: Head of Platform, Head of Technology Operations, IT Operations Director — close but not exact match to declared targets.
- **C:** Title is director-level but functional remit is different (Head of Product, Head of Engineering with no infra remit).
- **D:** Functional remit is mismatched (e.g. Head of Sales Engineering for an infra candidate).

Evidence: title, "function" or "remit" line in JD.

### 4. Track-record alignment

Does the JD's stated experience profile align with the candidate's track record?

- **A:** JD names experience the candidate has explicitly: ESA / aerospace / scientific computing background; ITIL/ITSM at scale; vendor & contract management; multi-decade IT.
- **B:** JD names experience adjacent: large-scale ITSM, multi-vendor environments, regulated procurement, 15+ years IT, prior director-level role.
- **C:** JD's experience profile is generic ("10+ years in IT leadership") with no specifics that align uniquely.
- **D:** JD asks for experience the candidate lacks (e.g. heavy SaaS product engineering background, US-only regulatory experience).

Evidence: "Requirements" or "About you" section quotes.

### 5. Cultural signals

How does the company present itself — founder-led, PE-owned, public, government, scientific institution? Does that match the candidate's preference profile?

- **A:** Scientific / research institutions; founder-led mature companies; PE-backed with multi-year hold; firms that mention "considered" or "long-horizon" decision-making.
- **B:** Mid-stage growth companies with seasoned management; public companies with stable senior teams.
- **C:** PE roll-ups, fast-growth startups with first director hire, consultancies.
- **D:** Pre-Series-A startups asking for director-level work; heavily process-heavy firms; companies with explicit "fast-paced" / "wear many hats" language at director level.

Evidence: company About section, JD tone, "we are a team that…" lines.

## Overall tier derivation

| Dimension tiers | Overall tier |
|---|---|
| All A or one B (rest A) | **A** |
| Majority B, no C/D | **B** |
| Any C, no D | **C** |
| Any D in {Leadership scope, Function, Track-record} | **D** |
| Any D in {Domain, Cultural signals} but rest ≥ B | **C** |

(Hard gates are applied earlier in `_gate-engine`; any gated job is D before dimensions are computed.)

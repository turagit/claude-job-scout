---
name: job-matcher
description: >
  This skill should be used when the user asks to "match jobs to my CV", "score these jobs",
  "rank job listings", "find best matches", "analyze job alerts", "which jobs should I apply to",
  "compare jobs against my profile", or needs to evaluate job listings against their
  CV and stated requirements. Also triggers during job alert analysis workflows.
version: 0.1.0
---

# Job Matcher

Score, rank, and filter job listings against a user's CV and stated requirements to surface the best opportunities.

## Matching Framework

Evaluate each job listing across these dimensions:

### 1. Skills Match (Weight: 30%)
- Count required/preferred skills from listing that appear in CV
- Identify transferable skills (e.g., "React" satisfies "frontend framework")
- Flag critical missing skills that would be dealbreakers
- Calculate: `(matched_required / total_required) * 100`

### 2. Experience Alignment (Weight: 25%)
- Years of experience match (within +/-2 years acceptable)
- Industry and domain knowledge overlap
- Seniority level alignment
- Management/IC track alignment

### 3. Requirements Fit (Weight: 25%)
- Location match (remote, hybrid, on-site)
- Salary/rate alignment (if disclosed)
- Contract type match (permanent, contract, freelance)
- Work authorization / visa requirements

### 4. Growth & Culture (Weight: 10%)
- Career progression opportunity
- Technology stack alignment with career goals
- Company size/sector preference match

### 5. Practical Factors (Weight: 10%)
- Easy Apply preferred
- Posting freshness (>30 days = stale)
- Number of applicants (lower = better odds)

## Scoring System

- **Match Score: X/100** — weighted aggregate
- **A-Tier (85-100):** Strong match — apply immediately
- **B-Tier (70-84):** Good match — worth applying
- **C-Tier (55-69):** Partial match — apply if interested
- **D-Tier (below 55):** Weak match — skip

## Batch Analysis

When analyzing multiple listings: quick-filter D-Tier and deal-breaker violations first, deep-score the rest, rank by score within tiers, provide detailed analysis for A-Tier and top B-Tier.

## Freelance / Contract Adjustments

When user's profile indicates freelance/contract work, apply adjustments from `../shared-references/freelance-context.md`.

## Reference Materials

- **`references/matching-weights.md`** — Weight customization by industry and career stage
- **`references/user-profile-schema.md`** — Shared user profile schema
- **`../shared-references/freelance-context.md`** — Freelance scoring, rate normalization, IR35 rules

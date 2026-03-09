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
- Count required skills from the listing that appear in the user's CV
- Count preferred/nice-to-have skills present
- Identify transferable skills that satisfy requirements (e.g., "React" satisfies "frontend framework")
- Flag critical missing skills that would be dealbreakers
- Calculate: `(matched_required / total_required) * 100`

### 2. Experience Alignment (Weight: 25%)
- Years of experience match (within ±2 years is acceptable)
- Industry relevance — same industry scores higher
- Seniority level alignment (don't match Senior roles to Junior CVs or vice versa)
- Domain knowledge overlap (e.g., fintech experience for fintech role)
- Management/IC track alignment

### 3. Requirements Fit (Weight: 25%)
- Location match (remote, hybrid, on-site + city/country)
- Salary range alignment (if disclosed)
- Work authorization / visa requirements
- Travel requirements within user's tolerance
- Contract type match (permanent, contract, freelance)

### 4. Growth & Culture (Weight: 10%)
- Career progression opportunity
- Company size preference match
- Industry sector interest
- Technology stack alignment with career goals
- Learning opportunities

### 5. Practical Factors (Weight: 10%)
- Application method (Easy Apply preferred)
- Posting freshness (newer = better, >30 days = stale)
- Company reputation signals
- Number of applicants (lower competition = better odds)
- Recruiter responsiveness signals

## Scoring System

For each job, produce:
- **Match Score: X/100** — weighted aggregate
- **Match Tier:**
  - **A-Tier (85-100):** Strong match — apply immediately
  - **B-Tier (70-84):** Good match — worth applying
  - **C-Tier (55-69):** Partial match — apply if interested in the company
  - **D-Tier (below 55):** Weak match — skip unless compelling reason

## Requirements Gathering

Before matching, collect user requirements through conversation:

1. **Target roles** — Job titles, variations, related titles
2. **Location** — Cities, countries, remote preference, hybrid tolerance
3. **Salary** — Minimum acceptable, ideal range, currency
4. **Seniority** — Junior, Mid, Senior, Lead, Principal, Director, VP
5. **Company preferences** — Size, industry, specific companies to target or avoid
6. **Deal-breakers** — Absolute requirements (e.g., must be remote, must sponsor visa)
7. **Nice-to-haves** — Preferences that aren't deal-breakers

Store these requirements for use across all matching operations.

## Batch Analysis Process

When analyzing multiple job listings (e.g., from job alerts):

1. **Gather listings** — Read all job listings from LinkedIn alerts or search results
2. **Quick filter** — Immediately discard D-Tier matches and deal-breaker violations
3. **Deep analysis** — Score remaining jobs across all dimensions
4. **Rank results** — Sort by match score within tiers
5. **Present summary table:**

```
| Rank | Job Title | Company | Score | Tier | Key Match | Key Gap |
|------|-----------|---------|-------|------|-----------|---------|
| 1    | ...       | ...     | 92    | A    | ...       | ...     |
```

6. **Detailed cards** — For A-Tier and top B-Tier, provide detailed analysis
7. **Recommendation** — Suggest which to apply to and in what order

## Red Flags to Surface

Always flag these regardless of match score:
- Job posted >45 days ago with no updates
- Vague job descriptions with no specific requirements
- Salary significantly below market rate
- Company with recent layoffs or poor Glassdoor ratings (if known)
- Duplicate postings from same company (may indicate high turnover)
- Requirements that seem unrealistic for the level/compensation

## Reference Materials

- **`references/matching-weights.md`** — Detailed weight customization by industry and career stage

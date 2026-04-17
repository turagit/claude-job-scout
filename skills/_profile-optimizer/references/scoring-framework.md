# Scoring Framework

Loaded on demand by `_profile-optimizer/SKILL.md` when computing scores.

---

### Section Scores (1-10 each)
Score each section for content quality and completeness:
- Headline, About, Experience, Skills, Featured, Additional Sections, Open to Work, Structured Fields

### Cross-Cutting Scores
These measure discoverability factors that span multiple sections:

| Score | What it measures | How to calculate |
|-------|-----------------|------------------|
| **Keyword Coverage** | % of master keyword list found anywhere on profile | `(keywords_found / total_keywords) * 100` — target 90%+ |
| **Search Appearance Estimate** | Likelihood of appearing in recruiter searches | Based on: headline keywords ✓, skills count ≥30 ✓, All-Star complete ✓, Open to Work enabled ✓, SSI ≥70 ✓ |
| **Recruiter 10-Second Test** | Does the profile answer what a recruiter checks in <10 seconds | 5 checks: current role clear ✓, years of experience evident ✓, key skills visible ✓, location stated ✓, availability signal present ✓ |
| **CV Alignment** | Consistency between CV and LinkedIn | Dates match ✓, titles match ✓, companies match ✓, all CV keywords on LinkedIn ✓, no contradictions ✓ |

### Overall Score
Weighted aggregate: Section scores (60%) + Cross-cutting scores (40%). Present as X/100 with tier: A (85-100), B (70-84), C (55-69), D (<55).

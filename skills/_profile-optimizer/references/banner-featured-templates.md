# Banner + Featured Section Templates

Loaded on demand by `_profile-optimizer/SKILL.md` when proposing banner images or Featured section content. Provides concrete, actionable templates rather than generic advice.

---

## Banner templates (3 options)

Choose the template that best matches the user's positioning based on their CV and career stage.

### Template 1 — Keyword Billboard

```
┌────────────────────────────────────────────────────────────┐
│                                                            │
│   [Role Title]  |  [Skill 1]  |  [Skill 2]  |  [Skill 3] │
│                                                            │
│   [One-line value statement or signature achievement]      │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Best for:** maximizing keyword visibility in a glance. Works for all roles. The skills chosen should match the top 3 keywords from the master keyword list.

**Example:** `Senior Data Engineer | Apache Spark | AWS | Real-Time Pipelines — Processing 2B+ events/day`

### Template 2 — Achievement Spotlight

```
┌────────────────────────────────────────────────────────────┐
│                                                            │
│            [Signature Metric]                              │
│            e.g. "£4.2B processed annually"                 │
│                                                            │
│            [Role Title] at [Company Type]                  │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Best for:** roles where one number tells the story (finance, ops, engineering scale). Triggers the anchoring effect from the psychology cheatsheet.

**Example:** `99.99% Uptime | Platform Engineer | FinTech & E-Commerce`

### Template 3 — Authority Signal

```
┌────────────────────────────────────────────────────────────┐
│                                                            │
│   Speaker at [Conference]  |  Author of [Publication]      │
│                                                            │
│   [Role Title]                                             │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Best for:** thought leaders, consultants, senior ICs building personal brand. Triggers the authority heuristic.

**Example:** `KubeCon Speaker | Author: "Scaling Event-Driven Systems" | Staff Engineer`

### Selection guidance

Match template to the user's strongest signal:
- Strong metrics (revenue, users, uptime, cost savings) → Template 2
- Strong credentials (talks, publications, certs) → Template 3
- General/balanced profile → Template 1 (safest default)

---

## Featured section templates (5-slot framework)

LinkedIn's Featured section supports 3-5 items displayed above the fold. Each slot should serve a distinct purpose.

| Slot | Content type | Source | Why it works |
|------|-------------|--------|--------------|
| 1 | Certification link | Credential verification page (Credly, AWS Verify, etc.) | Authority signal — one-click verification builds trust |
| 2 | Case study | Strongest CV achievement as a LinkedIn article or uploaded PDF | Depth behind the bullet — hiring managers can explore the full story |
| 3 | Talk/presentation | Conference slides (SlideShare/Speaker Deck), video link, or uploaded deck | Authority + expertise demonstration — rare differentiator |
| 4 | Project/portfolio | GitHub repo, product demo URL, portfolio page, or design samples | Tangible proof of work — especially important for technical roles |
| 5 | Recommendation highlight | Link to a key LinkedIn recommendation or testimonial screenshot | Social proof from a named authority figure |

### Mapping supporting docs to slots

Use the supporting-docs index (`.job-scout/cache/supporting-docs.json`) to recommend which slots to fill:

| Supporting doc type | Recommended slot |
|-------------------|-----------------|
| `cert` | Slot 1 — Certification link |
| `case_study` | Slot 2 — Case study |
| `talk` or `deck` | Slot 3 — Talk/presentation |
| `portfolio` or `publication` | Slot 4 — Project/portfolio |
| `recommendation` | Slot 5 — Recommendation highlight |

If the user has no supporting doc for a slot, suggest creating one:
- No cert? → "Consider adding your top certification to Credly for a verifiable link."
- No case study? → "Write a LinkedIn article about your strongest CV achievement — 500 words, focused on the business impact."
- No talk? → "Even an internal brown-bag deck uploaded as a PDF works here."

### Prioritization

If the user has more than 5 items, prioritize by:
1. Items backed by a supporting doc (verifiable > claimed)
2. Items relevant to the target role (from master keyword list overlap)
3. Items with the highest "authority signal" value (certs > recommendations > portfolio for most roles)

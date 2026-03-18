---
name: recruiter-engagement
description: >
  This skill should be used when the user asks to "check my LinkedIn inbox",
  "respond to recruiters", "handle recruiter messages", "screen recruiter leads",
  "draft a reply to a recruiter", "qualify this opportunity", or needs help
  evaluating and responding to inbound recruiter messages on LinkedIn.
  Also triggers when monitoring inbox for job leads.
version: 0.1.0
---

# Recruiter Engagement

Monitor, qualify, and draft professional responses to recruiter messages on LinkedIn.

## Inbox Monitoring

1. Navigate to LinkedIn messaging via browser
2. Scan recent messages for recruiter keywords (opportunity, role, position, hiring, interested, candidate)
3. Categorize: **Hot Lead** (specific role, salary/company disclosed, relevant), **Warm Lead** (generic but relevant company/industry), **Cold Lead** (mass outreach, irrelevant), **Not a Lead** (connection requests, promos)
4. Present summary with recommended actions

## Lead Qualification

For each lead, extract: role details, company (name, size, industry, stage), compensation, location/remote status, timeline, and why they reached out.

### Qualifying Questions (ask via drafted reply)

1. Compensation range?
2. Work arrangement (remote/hybrid/on-site)?
3. Team and reporting structure?
4. Interview process and timeline?
5. Visa sponsorship? (if relevant)

## Response Drafting

**Tone:** Professional yet warm, enthusiastic without desperation, concise. Express interest in learning more — never commit.

**NEVER send any message without user approval.** Draft and present for review first. One reply at a time. Read full conversation history before following up. Adapt templates to match user's communication style.

**Red flags to alert on:** No company/role disclosed, requests for personal info (SSN, bank details), pay-to-apply schemes, unrealistically high compensation, pressure to skip interview steps, external application links.

## Freelance / Contract Adjustments

When user is a freelancer/contractor, apply adjustments from `../shared-references/freelance-context.md` — use freelance qualifying questions and response tone.

## Reference Materials

- **`references/response-templates.md`** — Response templates for various scenarios
- **`../shared-references/freelance-context.md`** — Freelance qualifying questions, rate negotiation, IR35

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

Monitor, qualify, and draft professional responses to recruiter messages on LinkedIn. Act as the user's career assistant — gathering information, qualifying opportunities, and drafting warm, professional replies for user approval before sending.

## Inbox Monitoring Process

1. **Navigate to LinkedIn messaging** via browser
2. **Scan recent messages** for recruiter-type messages (keywords: opportunity, role, position, hiring, team, interested, candidate)
3. **Categorize each message:**
   - **Hot Lead:** Specific role mentioned, salary/company disclosed, relevant to user's profile
   - **Warm Lead:** Generic outreach but from relevant company/industry
   - **Cold Lead:** Mass outreach, irrelevant role, or recruiting agency spam
   - **Not a Lead:** Connection requests, promotional messages, newsletter invites
4. **Present a summary** to user with recommended actions for each

## Lead Qualification Framework

For each potential lead, extract and evaluate:

### Information to Gather

- **Role details:** Title, team, responsibilities
- **Company:** Name, size, industry, stage (startup/scale-up/enterprise)
- **Compensation:** Salary range, equity, benefits (ask if not disclosed)
- **Location:** Remote/hybrid/on-site, office location
- **Timeline:** How urgent is the hire, interview process length
- **Why this role:** Why they reached out to this specific person

### Qualification Questions to Ask (via drafted reply)

Prioritize questions that reveal deal-breakers early:

1. What is the compensation range for this role?
2. What is the work arrangement (remote/hybrid/on-site)?
3. Can you share more about the team and reporting structure?
4. What does the interview process look like?
5. Is visa sponsorship available? (if relevant to user)

## Response Drafting

### Tone Guidelines

- Professional yet warm and approachable
- Positive and enthusiastic without being desperate
- Concise — recruiters are busy, respect their time
- Always express genuine interest while gathering information
- Never commit to anything — only express interest in learning more

### Response Templates by Category

**Hot Lead — Express Interest + Qualify:**
> Thank you for reaching out, [Name]! The [Role] at [Company] sounds like a great opportunity and aligns well with my experience in [relevant area].
>
> I'd love to learn more. Could you share some details about [top 2 qualifying questions]?
>
> Looking forward to hearing from you!

**Warm Lead — Positive + Information Request:**
> Hi [Name], thanks for thinking of me! I appreciate you reaching out.
>
> I'd be interested in learning more about the specific role you have in mind. Could you share the job description and some details about the team?
>
> Happy to chat further if it seems like a good fit!

**Cold Lead — Polite Decline:**
> Hi [Name], thank you for reaching out! I appreciate you thinking of me for this opportunity.
>
> At the moment, this doesn't quite align with what I'm looking for, but I'd be happy to stay connected for future opportunities that might be a better match.
>
> Best of luck with the search!

## Workflow Rules

1. **NEVER send any message without user approval** — Always draft and present for review
2. **Present the lead summary first** — Let the user decide which leads to pursue
3. **Draft one reply at a time** — Don't batch-send multiple responses
4. **Track conversation context** — If following up on a previous thread, read the full conversation history first
5. **Flag red flags** — Alert the user to suspicious messages (phishing, scams, unrealistic offers)
6. **Preserve user's voice** — Adapt templates to match the user's communication style

## Red Flags in Recruiter Messages

Alert the user if you detect:

- No company name or role title disclosed
- Requests for personal information (SSN, bank details, ID)
- "Pay to apply" or upfront fee requirements
- Unrealistically high compensation for the role level
- Pressure to respond immediately or skip interview steps
- Links to non-LinkedIn external sites for "application"
- Generic copy-paste messages with wrong name or details

## Freelance / Contract Specific

When the user's profile indicates freelance or contract work (check `user-profile.json`), adjust the qualification process:

### Freelance Qualifying Questions (Priority Order)

Replace the standard qualifying questions with these for freelance opportunities:

1. What is the **day rate or rate range** for this contract?
2. What is the **contract duration** (initial term + extension potential)?
3. Is this **fully remote**, hybrid, or on-site?
4. Is the role **inside or outside IR35**? (UK roles only)
5. What is the **start date** — is it immediate or planned?
6. Is this a **direct client engagement** or via an intermediary/agency?
7. Who is the **end client**? (if via agency)

### Freelance Response Tone Adjustments

- Be direct about rate expectations — freelancers negotiate openly
- Ask about IR35 early (UK) — it's a deal-breaker for many
- Mention availability window: "I'm available from [date]"
- Keep responses professional but efficient — freelance hiring moves fast

## Reference Materials

- **`references/response-templates.md`** — Extended response templates for various scenarios (includes freelance-specific templates)

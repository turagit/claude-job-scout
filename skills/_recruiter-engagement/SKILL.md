---
name: _recruiter-engagement
description: >
  [Internal — loaded by /check-inbox] This skill should be used when the user asks to "check my LinkedIn inbox",
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

**Permanent roles:**
1. Compensation range?
2. Work arrangement (remote/hybrid/on-site)?
3. Team and reporting structure?
4. Interview process and timeline?
5. Visa sponsorship? (if relevant)

**Freelance/contract roles:** Use the qualifying questions from `../shared-references/freelance-context.md` (day rate, duration, remote, IR35, start date, client vs agency, end client).

## Response Drafting

**Tone:** Professional yet warm, enthusiastic without desperation, concise. Express interest in learning more — never commit.

**NEVER send any message without user approval.** Draft and present for review first. One reply at a time. Read full conversation history before following up. Adapt templates to match user's communication style.

**Red flags to alert on:** No company/role disclosed, requests for personal info (SSN, bank details), pay-to-apply schemes, unrealistically high compensation, pressure to skip interview steps, external application links.

## Freelance / Contract Adjustments

When user is a freelancer/contractor, apply adjustments from `../shared-references/freelance-context.md` — use freelance qualifying questions and response tone.

## Thread State

Per-thread state lives in `.job-scout/recruiters/threads.json`:

```json
{
  "<thread_id>": {
    "recruiter_name": "...",
    "company": "...",
    "lead_tier": "hot | warm | cold",
    "last_seen_msg_id": "...",
    "last_drafted_reply": "...",
    "last_updated": "2026-04-08",
    "notes": [
      { "date": "2026-04-01", "note": "asked IR35 — confirmed outside" },
      { "date": "2026-04-05", "note": "rate range: £650-750/day" }
    ]
  }
}
```

Before reading any thread's full history, check `last_seen_msg_id`. If the latest visible message id matches, skip the thread — there's nothing new. Only deep-read threads with new activity — this avoids re-reading unchanged conversations on every run. After processing, update `last_seen_msg_id` and `lead_tier` per thread.

### Lead-memory notes

The `notes` array is an append-only log of facts established during the conversation. Notes persist across sessions so the skill never re-asks a question the recruiter already answered.

**Write trigger:** after each user-approved reply that contains a qualifying question or confirms a factual detail, append a note. Format: `{ "date": "<YYYY-MM-DD>", "note": "<topic> — <resolution or 'pending'>" }`. Examples: "asked IR35 — confirmed outside", "rate range: £650-750/day", "start date — pending, recruiter will confirm by Friday".

**Read trigger:** before drafting any reply:
1. Load `notes` for the thread.
2. Build a "known facts" summary from the latest note per topic.
3. Do not re-ask any question that has a resolved (non-"pending") note.
4. For "pending" notes, check if the recruiter's latest message resolves them. If so, update the note.

**Display:** surface the known-facts summary in the thread card presented to the user: "Known: IR35 outside, rate £650-750/day, available immediately."

Notes are never deleted. Contradictions are handled by reading the most recent note on a topic — it supersedes earlier entries.

## Reference Materials

- **`references/response-templates.md`** — Response templates for various scenarios
- **`../shared-references/freelance-context.md`** — Freelance qualifying questions, rate negotiation, IR35
- **`../shared-references/workspace-layout.md`** — `.job-scout/` folder layout and bootstrap

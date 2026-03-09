---
description: Monitor LinkedIn inbox for recruiter messages and leads
allowed-tools: Read, Write, Bash, Glob
---

Scan the LinkedIn inbox for recruiter messages, qualify leads, and draft professional responses for user approval.

## Important Rules

- **NEVER send any message without explicit user approval.**
- **Draft all replies first** and present them to the user for review.
- **Always be positive, professional, and warm** in tone.

## Step 1: Navigate to Inbox

Using the browser:
1. Navigate to `https://www.linkedin.com/messaging/`
2. Scan the most recent messages (focus on unread first, then recent)

## Step 2: Identify Recruiter Messages

Look for messages that indicate recruitment outreach:
- Keywords: opportunity, role, position, hiring, team, interested, candidate, recruiting, talent
- Messages from people with "Recruiter", "Talent Acquisition", "Sourcer", "HR", or "Headhunter" in their title
- Messages that mention specific companies or job openings

Skip: connection requests, promotional messages, newsletter invites, social messages from contacts.

## Step 3: Categorize Leads

Load the recruiter-engagement skill. For each recruiter message, classify:

- **Hot Lead** — Specific role mentioned, relevant company/industry, salary or details shared
- **Warm Lead** — Generic outreach but from a relevant company or recruiter
- **Cold Lead** — Mass outreach, irrelevant role, recruiting agency spam
- **Red Flag** — Suspicious messages (phishing, scam signals, requests for personal info)

## Step 4: Present Summary

Show the user a lead summary:

```
INBOX SCAN RESULTS
==================
Hot Leads (2):
  1. [Recruiter Name] from [Company] — [Role mentioned] — Received [date]
  2. ...

Warm Leads (3):
  1. ...

Cold Leads (1):
  1. ...

Red Flags (0): None detected

Recommended: Respond to Hot Leads first, then Warm Leads.
```

For each Hot and Warm lead, include a brief summary of the message content and why it was categorized that way.

## Step 5: Draft Responses

For each lead the user wants to respond to:

1. Read the full conversation thread (not just the latest message)
2. Cross-reference the opportunity against the user's CV and requirements
3. Draft a response using the recruiter-engagement skill templates, adapted to:
   - The specific opportunity mentioned
   - The user's relevant experience
   - Key qualifying questions to ask
4. Present the draft to the user with context:
   - "Here's my suggested reply to [Name] about the [Role] at [Company]:"
   - [Draft message]
   - "Shall I send this, or would you like to adjust it?"

## Step 6: Send (With Approval Only)

Only after the user explicitly approves each message:
1. Navigate to the conversation in LinkedIn messaging
2. Type the approved message
3. Confirm with the user one final time before hitting Send
4. Confirm the message was sent

## Step 7: Follow-Up Tracking

After processing the inbox, suggest:
- Setting a reminder to check inbox again in 2-3 days
- Following up on unanswered messages after 5-7 days
- Running /match-jobs if any roles mentioned look promising

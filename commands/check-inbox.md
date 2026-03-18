---
description: Monitor LinkedIn inbox for recruiter messages and leads
allowed-tools: Read, Write, Bash, Glob
---

Scan LinkedIn inbox for recruiter messages, qualify leads, and draft responses for user approval.

## Rules

- **NEVER send any message without explicit user approval.**
- Draft all replies first for user review.

## Step 1: Scan Inbox

Navigate to `https://www.linkedin.com/messaging/`. Scan recent messages (unread first). Identify recruiter outreach by keywords (opportunity, role, position, hiring, candidate) and titles (Recruiter, Talent Acquisition, Sourcer, HR).

## Step 2: Categorize

Load the **recruiter-engagement** skill. Classify each message: Hot Lead (specific role, relevant, details shared), Warm Lead (generic but relevant company), Cold Lead (mass outreach, irrelevant), Red Flag (suspicious/scam signals).

## Step 3: Present Summary

Show leads grouped by category with: recruiter name, company, role mentioned, date received, and brief summary of why it was categorized that way. Recommend responding to Hot Leads first.

## Step 4: Draft and Send Responses

For each lead the user wants to respond to: read full conversation thread, cross-reference against CV/requirements, draft response using recruiter-engagement templates adapted to the specific opportunity. Present draft with context and ask for approval. Only send after explicit user confirmation — navigate to conversation, type message, confirm once more before sending.

## Next Steps

Suggest `/check-new-jobs` for latest alerts, following up on unanswered messages after 5-7 days.

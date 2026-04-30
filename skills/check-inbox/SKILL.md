---
name: check-inbox
description: Monitor LinkedIn inbox for recruiter messages and leads
allowed-tools: Read, Write, Bash, Glob
disable-model-invocation: true
---

Scan LinkedIn inbox for recruiter messages, qualify leads, and draft responses for user approval.

## Browser policy (read first)

All browser work in this command uses **the Claude Chrome extension exclusively**. Never request computer use. Never suggest any other automation framework. See `shared-references/browser-policy.md`.

## Rules

- **NEVER send any message without explicit user approval.**
- Draft all replies first for user review.

## Step 0: Bootstrap workspace

Follow `shared-references/workspace-layout.md` to ensure `.job-scout/` exists. Recruiter thread state lives in `.job-scout/recruiters/threads.json`. Then follow `shared-references/render-orchestration.md` Step G (lifecycle cleanup) to archive expired report files and prune old archives — cheap directory scan; runs at the start of every Tier 1 command.

## Step 1: Scan Inbox

Navigate to `https://www.linkedin.com/messaging/`. Scan recent messages (unread first). Identify recruiter outreach by keywords (opportunity, role, position, hiring, candidate) and titles (Recruiter, Talent Acquisition, Sourcer, HR).

**Dedupe via thread state:** load `.job-scout/recruiters/threads.json`. For each thread, check `last_seen_msg_id`. If the latest message is the same as the stored value, skip the thread — nothing new to read. Only deep-read threads with new activity. After processing, update `last_seen_msg_id` and `lead_tier` per thread.

## Step 2: Categorize

Load the **_recruiter-engagement** skill. Classify each message: Hot Lead (specific role, relevant, details shared), Warm Lead (generic but relevant company), Cold Lead (mass outreach, irrelevant), Red Flag (suspicious/scam signals).

## Step 3: Present Summary

Show leads grouped by category with: recruiter name, company, role mentioned, date received, brief summary of why it was categorized that way, and **known facts** from lead-memory notes (if any — e.g., "Known: IR35 outside, rate £650-750/day"). Recommend responding to Hot Leads first.

## Step 4: Draft and Send Responses

For each lead the user wants to respond to: read full conversation thread, cross-reference against CV/requirements, draft response using _recruiter-engagement templates adapted to the specific opportunity. Present draft with context and ask for approval. Only send after explicit user confirmation — navigate to conversation, type message, confirm once more before sending.

## Step 5: Build results payload

Construct a `data` payload as in `../shared-references/render-orchestration.md` Step A. View-specific fields:

- `title`: "Recruiter inbox".
- `subtitle`: "{{N}} threads · {{unread}} unread".
- `filename`: "check-inbox-latest.html".
- `thread_count`: integer.
- `unread_count`: integer count of `unread: true` threads.
- `results[]`: each item is `{ id, recruiter_name, company, message_count, last_message_at, last_message_from, unread, lead_tier, url, messages[] }`. `messages[]` is `[{ sent_at, from, body }]` chronological. `lead_tier` per `_recruiter-engagement` taxonomy (warm/cold/lukewarm). `url` is the absolute LinkedIn conversation URL or — when the thread is about a specific role — the job posting URL; it is optional. When present, the templates render a "View on LinkedIn ↗" link in HTML and a clickable thread heading in markdown; when omitted, the templates fall back to plain text via `{% if thread.url %}` guards.

## Step 6: Render

Follow `../shared-references/render-orchestration.md` end-to-end (Step G already ran in Step 0):

1. Step A — payload built in Step 5 above.
2. Steps B–F — read render config, dispatch `_visualizer`, open in Chrome (or fall back), handle errors.
3. Step E — print the summary line:

```
✓ {{N}} threads — {{unread}} unread — opened report in Chrome
```

Fall back to pre-v0.7.0 inline output if `Agent` tool is unavailable.

## Next Steps

Suggest `/check-job-notifications` for latest alerts, following up on unanswered messages after 5-7 days.

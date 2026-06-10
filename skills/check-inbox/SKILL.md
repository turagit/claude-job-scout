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

## Step 1b: Parse embedded job links (v0.9.0+)

While reading each thread with new activity, scan every message body for embedded job-posting URLs. LinkedIn surfaces three shapes:

1. Full canonical URLs: `https://www.linkedin.com/jobs/view/<id>/` or `https://www.linkedin.com/jobs/view/<id>?...`
2. Shortlinks: `linkedin.com/jobs/view/<id>` (no scheme) or wrapped tracking-redirect URLs (`lnkd.in/...` — follow once to resolve to the canonical form).
3. Inline job cards: LinkedIn injects rich cards when a recruiter shares a role. The card carries the job ID as a data attribute on the rendered element.

For each unique job ID extracted from a thread:

1. Filter against `.job-scout/tracker.json`. If known, just record the linkage (see step 3 below) and skip extraction.
2. If new: open the listing, extract details, persist JD to `.job-scout/jds/<id>.txt`, set `jd_path` on the tracker entry, set `source: "Inbox"`, and tag `notes` with `"from recruiter thread: <thread_id>"`.
3. Run `_gate-engine` and `_job-matcher` on the new job (same chain as `/check-job-notifications` Step 5).
4. **Record bidirectional linkage:** add the job ID to `thread.linked_job_ids[]` on the recruiter thread, and add the thread ID to `tracker.jobs[<id>].linked_thread_ids[]` (canonical schema reserves both fields). This wiring lights up cross-navigation in Phase 8's recruiter UX.

After this step, the inbox scan has populated the tracker with recruiter-sourced jobs the rest of the plugin would otherwise never see.

## Step 2: Categorize

Load the **_recruiter-engagement** skill. Classify each thread into the canonical `lead_tier` enum (`../shared-references/canonical-schemas.md`): `hot` (specific role, relevant, details shared), `warm` (generic but relevant company/industry), `cold` (mass outreach, irrelevant), `non-lead` (connection requests, promotions). Scam or red-flag signals (no company disclosed, requests for personal data, pay-to-apply, pressure tactics) are not a tier — record them in `lead_tier_detail` (e.g. `"red flag: pay-to-apply scheme"`) and surface them prominently in the summary.

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
- `results[]`: each item is `{ id, recruiter_name, company, message_count, last_message_at, last_message_from, unread, lead_tier, lead_tier_detail, linked_jobs, url, messages[] }`. `messages[]` is `[{ sent_at, from, body }]` chronological. `lead_tier` per the canonical enum (`hot | warm | cold | non-lead`); `lead_tier_detail` carries red-flag notes when present. `linked_jobs` is `[{ id, title, tier }]` resolved from `thread.linked_job_ids[]` against the tracker — lets the report show which scored jobs came from this thread. `url` is the absolute LinkedIn conversation URL or — when the thread is about a specific role — the job posting URL; it is optional. When present, the templates render a "View on LinkedIn ↗" link in HTML and a clickable thread heading in markdown; when omitted, the templates fall back to plain text via `{% if thread.url %}` guards.

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

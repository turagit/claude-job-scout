# Scheduled task — Freelancer daily job scan

Paste the block below as the task's instructions. It replaces the 2026-08-31 version, which restated the gates and described a re-ranking fallback; both now live in the plugin (`user-profile.json` holds the gates; the command writes a `no_scrape` digest when the browser is unavailable).

Schedule: nightly, 03:10 Europe/Amsterdam. Folder: `~/CoWork/CVFREELANCER`. Model for the task session: Sonnet is sufficient (the command sequences scripts; gating and scoring run in pinned subagents).

```
Freelancer daily job scan

1. In the CVFREELANCER folder, run the linkedin-job-hunter `/check-job-notifications` command. Do not add instructions about how the scan works, which gates apply, or what to do if the browser is missing — the command handles all of that and never asks questions.

2. When it finishes, read the digest file it names in its summary: `.job-scout/reports/check-job-notifications-<today>-digest.txt`. If the summary reports a `no_scrape` status, the digest already says so — use it as-is.

3. Create one Google Calendar event on my primary calendar (create_event):
   - summary: the digest's first line, shortened to at most 80 characters, prefixed "Freelancer scan <today> — ".
   - description: the digest file's full text, verbatim. Plain text, bare URLs, no formatting added.
   - startTime: 5 minutes after now; endTime: 20 minutes after now; timeZone: "Europe/Amsterdam".
   - overrideReminders: [ { "method": "popup", "minutes": 0 } ]. No attendees.

4. Print inline: the command's summary line and its per-role direct-link lines. Do not open the report in a browser.
```

## Why this shape

- One process description exists, in the plugin. The task prompt never restates it, so nothing can drift.
- A missing browser produces a short, honest event ("NO FRESH SCRAPE — …") and no tracker writes, instead of a costly re-rank of yesterday's jobs.
- The digest's size and order are produced by `digest.py` under test, not improvised per night.

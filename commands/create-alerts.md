---
description: Create LinkedIn job alerts matching your search criteria
allowed-tools: Read, Bash
---

Create job alerts on LinkedIn for matching positions.

## Step 1: Gather Criteria

Ask what alerts to create: job title/keywords, location (city/country/Remote), frequency (Daily/Weekly), additional filters (experience level, company size, Easy Apply). If user ran `/job-search` previously, suggest alerts based on those parameters.

## Step 2: Create Alerts

For each alert: navigate to `https://www.linkedin.com/jobs/`, enter keywords, set location, apply filters, click "Set alert" / "Get notified" toggle.

## Step 3: Verify

Navigate to alerts management page and verify all new alerts appear. Present summary: alert title, location, frequency.

Suggest creating 3-5 alerts covering title variations (broad + specific), setting highest-priority to Daily, and using `/check-new-jobs` regularly to score new listings.

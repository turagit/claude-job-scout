---
description: Create LinkedIn job alerts matching your search criteria
allowed-tools: Read, Bash
---

Create job alerts on LinkedIn so the user receives notifications for matching positions.

## Step 1: Confirm Search Criteria

Ask the user what alerts they want to create. Gather for each alert:
1. **Job title / keywords** to search for
2. **Location** (city, country, or Remote)
3. **Frequency** — Daily or Weekly notifications
4. **Additional filters** — Experience level, company size, Easy Apply only, etc.

If the user previously ran /job-search, suggest creating alerts based on those same search parameters.

## Step 2: Create Alerts on LinkedIn

For each alert the user wants:

1. Navigate to `https://www.linkedin.com/jobs/` using the browser
2. Enter the job title/keywords in the search field
3. Set the location
4. Apply any additional filters (Experience Level, Date Posted, Remote, Easy Apply)
5. Look for and click the "Set alert" or "Get notified" toggle/button on the search results page
6. Confirm the alert was created by verifying the toggle state or confirmation message

## Step 3: Verify and Report

After creating all alerts:
1. Navigate to `https://www.linkedin.com/jobs/preferences/` or the alerts management page
2. Verify all new alerts appear in the list
3. Present a summary to the user:

```
Alert created: [Job Title] in [Location] — [Frequency]
```

## Step 4: Recommend

Suggest:
- Creating 3-5 alerts covering different job title variations
- Using both broad terms ("Software Engineer") and specific ones ("React Developer")
- Setting at least one alert to Daily for highest-priority searches
- Checking alerts regularly with /match-jobs to score new listings

Remind the user they can run /match-jobs whenever they receive alert notifications to quickly score the new listings.

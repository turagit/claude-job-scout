# Phase 17 — LinkedIn DOM evidence (captured 2026-09-02, built-in browser pane, logged-in session)

Read-only observations that the Phase 17 extractor contracts and test fixtures are built from. Everything here was read from the live pages on 2026-09-02 between 07:00 and 09:30 UTC. Class names on the new-style pages are obfuscated and rotate; **only the attributes and text patterns listed as "stable anchors" may be used by the extractor.**

## 1. Notifications page — `https://www.linkedin.com/notifications/?filter=jobs_all`

- Ten alert cards render initially; a `<button>` whose trimmed text is `Load more` appends more. After two clicks the button disappeared and the list was exhausted at **14 alerts spanning ~1.5 days** (oldest "1d"). The surface holds roughly two days of alerts.
- No read/unread marker exists in the DOM: no class containing `unread`/`new`, no `data-*` attributes, no background-colour difference up the ancestor chain. **"Unread, highlighted in blue" is not a usable rule.**
- Each alert card has **two `<a>` elements with the same href** (the title and the "View jobs" button), so anchors must be deduplicated by href.
- **Stable anchor:** `a[href*="alertAction=viewjobs"]`. The href is the alert's identity and preview:

```
https://www.linkedin.com/jobs/search-results/?keywords=linux+engineer+Contract+Remote
  &f_TPR=a1788218797-            # "posted after" epoch seconds, trailing dash
  &geoId=91000000                # European Union
  &origin=SEMANTIC_SEARCH_JOB_ALERT_IN_APP_NOTIFICATION
  &alertAction=viewjobs
  &currentJobId=4461737101
  &originToLandingJobPostings=4461737101,4461723921,4461789493,4461758173,4454761864,4461780431
```

- `originToLandingJobPostings` carries **at most six IDs**. It is a preview, not the alert's contents. The alert above resolved to 24 exact matches on its results page.
- Some alerts add `f_SAL=...` (salary filter) — pass every query parameter through verbatim when re-opening.
- The relative age ("43m", "11h", "1d") is a bare text node near the link; it is informational only. The epoch in `f_TPR` is the authoritative timestamp.
- Distinct alerts observed: 12 saved searches, e.g. `linux engineer Contract Remote`, `"identity management" linux Remote`, `platform engineer Contract Remote`, `ansible Contract Remote`, `linux security engineer`, `"red hat" identity Remote`, `identity management Remote`, `ipa kerberos`, `site reliability engineer Contract Remote`, `lead platform engineer Contract Remote`, `linux administrator Contract Remote`, `redhat idm`. The same keywords appear twice with different epochs (e.g. `linux engineer Contract Remote` at 2026-08-31T00:35 and 2026-08-31T23:26) — those are **two alerts**.

## 2. Alert results page — `https://www.linkedin.com/jobs/search-results/?…`

New-style (non-Ember) markup. 25 cards per page. Pagination `1 2 3 Next`; `&start=25` opens page 2.

- **Stable anchor for a card:** `[componentkey^="job-card-component-ref-<jobId>"]`. Two nested elements carry the same key (outer `div[role=button]` and an inner div) — select the **outermost** (one whose parent has no such ancestor) or dedupe by ID. 25 outer cards ⇒ 50 raw matches.
- Card text (innerText, in order): title (rendered twice: visible + `aria-hidden` twin), company, location with workplace type in brackets — `Germany (Remote)`, `Dublin (Hybrid)`, `Nancy (On-site)`, `Rotterdam` (none) — optional salary line (`$40/hr - $100/hr`, `350 EUR/day - 500 EUR/day`, `5,000 EUR/month - 6,000 EUR/month`), then footer tokens separated by ` · `: `Viewed` | `Be an early applicant` | `Actively reviewing applicants` | `Posted N hours ago` (+ aria twin `N hours ago`) | `Easy Apply` | `Promoted`. Also `(Verified job)` may be appended to the title's aria text.
- **Divider — stable anchor:** a leaf element whose text is exactly `We found more results related to your search that may not be exact matches, but could still be a great fit.` It appears **once**, between the last exact match and the first loose match (page 1: 24 cards before, 1 after). Pages after the divider carry no divider (page 2: 25 cards, none) — everything there is loose-match territory.
- **Result count:** a leaf `<p>` matching `/^\d[\d,]*\+? results?$/` (e.g. `99+ results`). Used only as the "page claims results but zero cards parsed" loud-failure check.
- **Pagination — stable anchors:** `[data-testid="pagination-controls-list"] button[aria-label="Page N"]` with `aria-current="true"` on the active page; `button[data-testid="pagination-controls-next-button-visible"]` when a next page exists (the hidden variant's testid ends `-hidden`).
- **Description pane:** clicking a card (or opening `…&currentJobId=<id>`) loads the JD into the right pane; the page text after the list contains the full JD under `About the job`. The URL updates to `currentJobId=<id>`. A `Show more`/`more` control may truncate the JD; the pane text read must expand it or read the full node.
- The card list lives in a scrollable pane (overflow-y auto) — lazy rendering was **not** observed (all 25 cards present without scrolling), but the extractor scrolls the pane to the bottom once before reading as insurance.

## 3. Top Picks — `https://www.linkedin.com/jobs/collections/recommended/`

Old-style Ember markup. 24–31 cards on page 1, pagination `Page 1..4` via `button[aria-label="Page N"]`.

- **Stable anchors:** `li[data-occludable-job-id]` (outer) / `div[data-job-id]` (inner); title link `a.job-card-container__link[href^="/jobs/view/<id>/"]` with `aria-label="<title>"`; company in `.artdeco-entity-lockup__subtitle`; location in `.job-card-container__metadata-wrapper li`; footer `job-card-container__footer-item` (`Viewed`, `Promoted`, `Easy Apply`, posted-ago).
- Cards are occludable (lazy): the list must be scrolled to the bottom before reading, and re-read until the count stops growing.
- **Pagination active page:** `button[aria-label="Page N"][aria-current="page"]` (carries `aria-current="page"`, not `"true"`); the button class includes `jobs-search-pagination__indicator`.

## 4. Saved jobs — `https://www.linkedin.com/my-items/saved-jobs/`

**Redirects to `https://www.linkedin.com/jobs-tracker/`** ("Job tracker") with a tab group. **Stable anchors:** `div[role="radio"][aria-checked="true"]` on the active tab; sibling radios carry `aria-checked="false"`. The Saved tab contains a `<label>` child with text matching `/^Saved\s*·\s*\d+$/` (e.g. `Saved · 0`); parse the count from that text. Other tabs: `In Progress · 4`, `Applied · 35`, `Interview · 0`, `Archived`. **Verified live 2026-09-02:** page requires ~2.5 seconds for tabs to render after load; tab click requires ~1.5 seconds more for card content to render. The Saved tab was empty for this account (`Saved · 0`, "No jobs here"). **Card selectors:** `[componentkey^="job-card-component-ref-"]` (new-style), `li[data-occludable-job-id]` (Ember-style), or `[data-job-id]` fallback.

## 5. Measured miss rate (the before-number)

Alert `linux engineer Contract Remote` @ 2026-08-31T23:26Z, page 1: 24 exact matches. Live tracker (CVFREELANCER, 4,049 entries, last_run 2026-09-02): **10 known, 14 never seen.** Today's report claimed "68 collected · 64 known · 4 new" across all ten alerts because it read only the six-ID preview per alert.

## 6. Live-state drift observed (input to the migration task)

- `source`: 3,524 string entries with 200+ distinct free-text values (`"Job Alert (gap lanes: ansible / SRE / platform engineer)"`, `"Ultramode LinkedIn sweep 2026-08-18"`, …); 525 structured objects, some with a non-canonical shape `{"surface": "top_picks", "type": "linkedin"}`.
- `status`: non-canonical `"gated"` present on 2026-09-02 entries.
- `gate_violations`: bare strings (`["contract_type","skills_mismatch"]`) instead of `[{kind, detail}]`; `skills_mismatch` is not a deal-breaker kind.
- `first_seen`: 2,216 date-only, 1,833 ISO datetime.
- Ad-hoc fields present: `employment_type`, `rate_disclosed`.
- `stats` carries undocumented keys (`last_deep_sweep`, `last_ultramode`, `last_inbox_scan`, `last_job_search`, `last_search`, `closed_applications`) — keep them (additive, harmless).
- A July copy of the engine scripts lives at `.job-scout/engine-scripts/` in the workspace (stale duplicate).

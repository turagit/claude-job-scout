# Browser Interaction Policy

Every command in this plugin that touches LinkedIn (or any other website) does so **exclusively through the Claude Chrome extension** running in the user's own logged-in browser. This is the only sanctioned browser mechanism for the plugin.

## Hard rules

1. **Never request, suggest, or enable "computer use."** Computer use takes control of the user's entire screen/mouse/keyboard and is strictly out of scope for this plugin. The Chrome extension is sufficient for every task the plugin performs, and asking for computer use makes users (rightly) nervous about intent. If the Chrome extension tools appear unavailable in the current session, **stop and tell the user** — do not offer computer use as a fallback.

2. **Never install, suggest, or enable any other browser-automation framework** (Playwright, Selenium, Puppeteer, headless Chrome, MCP browser servers other than the official Claude Chrome extension, etc.). The user has a logged-in LinkedIn session in their personal browser — the Chrome extension is how we use it.

3. **Never send sensitive data through the browser automation.** No SSN, no bank details, no passwords, no session tokens. If a LinkedIn form asks for any of these, stop and hand off to the user.

## Read-only `WebFetch` carve-out (ultramode public sources)

Phase 11 ultramode reads structured **public** job sources — ATS JSON boards, aggregator/feed APIs, RSS feeds — over read-only `WebFetch`. This is a plain HTTP `GET` of a public URL: **no logged-in session, no cookies, no automation framework, no rendered browser.** It is therefore **not browser automation and not a violation of Hard Rule #1.**

To be precise about what this carve-out does and does not change:

- **Hard Rule #1 still governs all *in-browser* work.** The Claude Chrome extension remains the **only** mechanism that touches the user's logged-in session — opening listings, applying, recruiter replies, and any sweep of a logged-in surface. The carve-out adds a separate, sessionless read path for public HTTP; it does not relax the in-browser rule one inch.
- **`WebFetch` here means: public HTTP `GET` → parse JSON/XML/HTML.** No credentials, no session tokens, no form submission, no clicking. If a source needs a login to read it, it is **not** eligible for this lane.
- **The forbidden list is unchanged and still explicit.** No Playwright, no Selenium, no Puppeteer, no headless Chrome, no computer use, no MCP browser server other than the official Claude Chrome extension. The carve-out introduces **no** new browser-automation framework — it is the plugin's existing `WebFetch` capability, used read-only.
- **Login-walled sources use the extension lane, never credentialed HTTP scraping.** Most freelance marketplaces, Slack/Discord communities, and some national boards/consumer aggregators sit behind a login. These are read through the Chrome extension in the user's own browser (with dedupe-before-extract), **never** by sending the user's credentials or session cookies through `WebFetch`. Per-source lane classification lives in `ultramode-sources.md`.

In short: public, sessionless HTTP reads are permitted via `WebFetch`; anything touching the user's logged-in session stays inside the Chrome extension, and every other automation framework stays forbidden.

## Why this matters

The plugin's trust model is: "Claude is my helper inside the browser I already use." The moment that boundary is crossed — computer use, external automation, or moving secrets around — the trust model breaks and users are right to panic. Keeping every browser interaction inside the Chrome extension means:

- The user can see exactly what's happening in their own browser window.
- Nothing runs outside the tab the extension is operating on.
- Stopping the plugin is as simple as closing the tab or disabling the extension.
- The plugin cannot reach anything on the user's machine outside that browser.

## If a command says "navigate to X"

Read it as: "use the Claude Chrome extension to navigate the user's existing browser tab to X." Nothing more. If the Chrome extension's navigation tool is not available in the current session, report that to the user and stop — do not escalate to any other mechanism.

## For the user (transparency)

This plugin only uses the Claude Chrome extension for browser work. If you ever see a prompt asking you to enable "computer use" or install any other browser-automation tool while running a command from this plugin, **something is wrong** — either the session is missing the Chrome extension, or an instruction is being misread. Please report it as a bug rather than approving it.

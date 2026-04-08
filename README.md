# LinkedIn Job Hunter

An all-in-one LinkedIn job search automation plugin for Claude Code / Cowork. Analyzes your CV, searches for matching jobs, optimizes your LinkedIn profile, manages recruiter conversations, and applies to jobs — all from one place.

## What It Does

This plugin turns Claude into your personal job search assistant on LinkedIn. It handles the pipeline from CV optimization to application submission, so you can focus on preparing for interviews instead of scrolling job boards.

- **CV Analysis & Improvement** — ATS compatibility scoring, keyword gap analysis, persuasion-psychology-aware rewrites.
- **Smart Job Search** — searches LinkedIn, scores every listing against your CV and stated requirements, ranks by fit.
- **Job Alerts** — creates LinkedIn job alerts so nothing slips through.
- **Daily Notification Sweep** — scans your unread job-alert notifications, scores new listings, and writes a ranked report.
- **Easy Apply** — handles LinkedIn Easy Apply for jobs you approve. Hands off external applications to you.
- **Inbox Monitoring** — scans recruiter messages, qualifies leads (hot/warm/cold), drafts replies for your approval.
- **Profile Optimization** — rewrites your headline, summary, experience, and skills for recruiter and ATS visibility.

## Commands

All commands are user-invoked slash commands. The model will **not** auto-trigger them — browser automation, applications, and recruiter replies only happen when *you* ask.

| Command | Description |
|---------|-------------|
| `/check-job-notifications` | **Daily driver** — check notifications, score new listings, save a ranked report |
| `/analyze-cv` | Analyze and optimize your CV for ATS and recruiters |
| `/job-search` | Search LinkedIn for jobs matching your CV and requirements |
| `/create-alerts` | Create LinkedIn job alerts matching your search criteria |
| `/match-jobs` | Score and rank job listings against your CV and requirements |
| `/apply` | Apply to approved jobs via LinkedIn Easy Apply |
| `/check-inbox` | Monitor LinkedIn inbox for recruiter messages and leads |
| `/optimize-profile` | Analyze and improve your LinkedIn profile |

## Skills

These are model-auto-loaded playbooks used by the commands above. You don't invoke them directly.

| Skill | Purpose |
|-------|---------|
| `cv-optimizer` | ATS analysis, keyword optimization, SPAR-method rewrites |
| `job-matcher` | Job scoring framework, requirement matching, batch ranking |
| `profile-optimizer` | LinkedIn SEO, headline formulas, section-by-section optimization |
| `recruiter-engagement` | Lead qualification, response drafting, conversation management |

---

## The `.job-scout/` workspace (important)

Starting in v0.3.0, every command reads and writes state inside a hidden, **per-project** folder called `.job-scout/`, located at the root of whatever project you invoke the plugin from.

### Why per-project

If you run the plugin from `~/projects/freelance-search/` and from `~/projects/perm-roles/`, you are doing two different searches — different CV, different requirements, different tracked jobs. A global folder would mix them. Per-project state keeps them cleanly separated. If you *want* a single shared home, you can symlink `.job-scout/` to a shared location — that's your call.

### What goes inside (full transparency)

```
.job-scout/
  user-profile.json       # CV-derived facts: skills, seniority, target roles, requirements,
                          #   master keyword list, cv_hash, discovery_complete flag
  tracker.json            # every job ever seen: id, url, title, company, score, tier,
                          #   status (seen/approved/applied/rejected), first_seen, last_seen
  reports/                # dated markdown reports from each run (YYYY-MM-DD-new-jobs.md etc.)
  cache/
    cv-<hash>.json            # parsed CV text + extracted keywords, keyed by CV content hash
    cv-analysis-<hash>.json   # full CV scoring output, keyed by content hash
    scores.json               # job scores keyed by (job_id, cv_hash)
    linkedin-profile.json     # last-seen snapshot of your LinkedIn profile (for diffing)
  recruiters/
    threads.json            # per-thread state: last_seen_msg_id, lead_tier, last_drafted_reply
```

**What is NOT stored:** no passwords, no session tokens, no LinkedIn cookies, no messages sent, no personal data beyond what's already in your CV and public LinkedIn profile.

**Why this is safe:**

1. It lives only on your machine, inside your own project directory. Nothing is uploaded anywhere.
2. The `.` prefix makes it hidden and keeps it out of everyday file listings.
3. Everything in it is either (a) a direct derivation of your CV and public LinkedIn data, or (b) a log of what the plugin has shown you — no secrets.
4. You can inspect, edit, or delete any file in `.job-scout/` at any time. Deleting it is a clean reset.
5. Add `.job-scout/` to your project's `.gitignore` if you don't want state committed to source control (recommended for most workflows).

### Why the plugin wants this folder (the token-saving story)

Without persistent state, every command would re-parse your CV, re-score every job, re-read every recruiter thread, and re-ask you the same profile questions on every run. That is slow and expensive. With `.job-scout/`:

- Your CV is parsed **once per content hash** — edit your CV and it re-parses; otherwise it's instant.
- Jobs you've already been shown are **never re-extracted** (the tracker is consulted *before* opening any listing).
- Job scores are cached per `(job_id, cv_hash)` — unchanged jobs against an unchanged CV are never re-scored.
- LinkedIn profile snapshots are cached for 7 days so re-runs don't re-read every section from scratch.
- Recruiter threads with no new messages are skipped on subsequent `/check-inbox` runs.

The practical effect: the second, third, and tenth runs of `/check-job-notifications` are dramatically cheaper than the first.

### First-run bootstrap

The first time you run any command in a new project, the plugin will ask:

> "I don't see a `.job-scout/` folder in this project yet. This is where I'll keep your CV profile, the list of jobs I've already shown you, cached scores, and run reports — all scoped to *this* project so different job searches stay separate. Want me to create it now?"

**Say yes.** The plugin will create the folder, write a stub `user-profile.json` and an empty `tracker.json`, and proceed. If you decline, the plugin will fall back to legacy behavior (writing loose files at your workspace root) for that session only, and will not nag you again in the same session.

---

## Installation

Clone this repo and install as a plugin:

```bash
git clone https://github.com/turagit/claude-job-scout.git
```

In Claude Desktop / Claude Code, go to Settings → Plugins → "Install from folder" and select the cloned directory. Claude detects `.claude-plugin/plugin.json` and installs all 8 slash commands and 4 skills automatically.

## Requirements

- **Claude Code or Claude Desktop** with Cowork / browser automation enabled
- **LinkedIn account** — you must be logged in to LinkedIn in your browser
- **Your CV** — place it anywhere in the project workspace; the plugin will find it by name (`cv.*`, `resume.*`, `curriculum.*`) or ask you to point to it

## Getting Started

1. Install the plugin (above).
2. `cd` into the project folder you want to run your job search from (create a new one if you like — e.g. `~/projects/freelance-search/`).
3. Drop your CV into that folder.
4. Log into LinkedIn in your browser.
5. Run `/analyze-cv` — bootstraps `.job-scout/`, runs the one-time discovery interview, and saves your profile.
6. Run `/optimize-profile` to align your LinkedIn profile with your CV.
7. Run `/job-search` or `/create-alerts` to start finding jobs.

### Daily workflow (once set up)

1. `/check-job-notifications` — scans unread alerts, scores new jobs, writes a ranked report. Offers to continue into LinkedIn's "Top job picks for you" feed for a deeper sweep.
2. Review the matches and tell Claude which ones to apply to.
3. Optionally run `/check-inbox` for recruiter messages.

## Privacy & Safety

- Claude never sends messages or submits applications without your explicit approval.
- Claude never enters sensitive personal data (SSN, bank details, passwords).
- All recruiter responses are drafted and shown to you before sending.
- External job applications are handed off to you for completion.
- Your CV data and all `.job-scout/` state stays local. Nothing is shared with any external service.
- `disable-model-invocation: true` is set on every command, so the model will never auto-fire browser automation or applications — only *you* can invoke them.

## Author

Built by BSF

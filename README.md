# LinkedIn Job Hunter

An all-in-one LinkedIn job search automation plugin for Claude Cowork. Analyzes your CV, searches for matching jobs, optimizes your LinkedIn profile, manages recruiter conversations, and applies to jobs — all from one place.

## What It Does

This plugin turns Claude into your personal job search assistant on LinkedIn. It handles the entire pipeline from CV optimization to application submission, so you can focus on preparing for interviews instead of endlessly scrolling job boards.

**CV Analysis & Improvement** — Upload your CV and get a detailed ATS compatibility score, keyword gap analysis, and a rewritten version optimized for your target roles.

**Smart Job Search** — Tell Claude what you're looking for and it searches LinkedIn, scores every listing against your CV and requirements, and surfaces the best matches ranked by fit.

**Job Alerts** — Create LinkedIn job alerts based on your search criteria so you never miss a new posting.

**Job Matching** — When new jobs appear in your alerts or saved jobs, Claude scores and ranks them so you instantly know which ones are worth your time.

**Easy Apply** — For jobs you approve, Claude handles the LinkedIn Easy Apply process. For external applications, it opens the page and guides you through.

**Inbox Monitoring** — Claude scans your LinkedIn inbox for recruiter messages, qualifies each lead (hot, warm, cold), and drafts professional responses for your approval before sending anything.

**Profile Optimization** — Claude reads your LinkedIn profile, compares it against your CV, and rewrites your headline, summary, experience, and skills to maximize visibility to recruiters and ATS systems.

## Commands

| Command | Description |
|---------|-------------|
| `/analyze-cv` | Analyze and optimize your CV for ATS and recruiters |
| `/job-search` | Search LinkedIn for jobs matching your CV and requirements |
| `/create-alerts` | Create LinkedIn job alerts matching your search criteria |
| `/match-jobs` | Score and rank job listings against your CV and requirements |
| `/apply` | Apply to approved jobs via LinkedIn Easy Apply |
| `/check-inbox` | Monitor LinkedIn inbox for recruiter messages and leads |
| `/optimize-profile` | Analyze and improve your LinkedIn profile |

## Skills

| Skill | Purpose |
|-------|---------|
| cv-optimizer | ATS analysis, keyword optimization, PAR method rewrites |
| job-matcher | Job scoring framework, requirement matching, batch ranking |
| profile-optimizer | LinkedIn SEO, headline formulas, section-by-section optimization |
| recruiter-engagement | Lead qualification, response drafting, conversation management |

## Installation

Clone this repo and install the plugin from the resulting folder. You have two options:

**Option A — Install the .plugin file directly:**
Download the `linkedin-job-hunter.plugin` file from the [Releases](https://github.com/turagit/claude-job-scout/releases) page (or from the repo root if provided). In Claude Desktop, go to Settings → Plugins and drag the `.plugin` file into the window, or click "Install plugin" and select the file. Claude will show you a preview of the plugin contents — click Accept to install.

**Option B — Install from a cloned repo:**
```bash
git clone https://github.com/turagit/claude-job-scout.git
```
Then open Claude Desktop, go to Settings → Plugins → "Install from folder", and select the cloned `claude-job-scout` directory. Claude will detect the `.claude-plugin/plugin.json` manifest and install everything automatically. You can also simply drag the folder into the Claude Desktop Plugins settings panel.

After installation, the 7 slash commands (`/analyze-cv`, `/job-search`, `/create-alerts`, `/match-jobs`, `/apply`, `/check-inbox`, `/optimize-profile`) and all 4 skills will be available in every Cowork session.

## Requirements

- **Claude Desktop** with Cowork mode and browser automation (Claude in Chrome) enabled
- **LinkedIn account** — you must be logged in to LinkedIn in your browser
- **Your CV** — upload it or have it in your workspace folder for best results

## Getting Started

1. Install the plugin (see Installation above)
2. Log in to LinkedIn in your browser
3. Start with `/analyze-cv` to optimize your CV
4. Run `/optimize-profile` to align your LinkedIn profile
5. Use `/job-search` to find matching jobs
6. Create alerts with `/create-alerts` for ongoing monitoring
7. Score new listings with `/match-jobs`
8. Apply to the best matches with `/apply`
9. Monitor recruiter outreach with `/check-inbox`

## Privacy & Safety

- Claude never sends messages or submits applications without your explicit approval
- Claude never enters sensitive personal data (SSN, bank details, passwords)
- All recruiter responses are drafted and shown to you before sending
- External job applications are handed off to you for completion
- Your CV data stays local — it is not shared with any external service

## Author

Built by BSF

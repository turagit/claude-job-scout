# LinkedIn Job Hunter

An all-in-one LinkedIn job search automation plugin for Claude Code / Cowork. Analyses your CV, runs crafted Boolean discovery sweeps for matching jobs, optimises your LinkedIn profile, manages recruiter conversations, and applies to jobs — all from one place.

> **New here? Start with the [Quick Start guide](QUICKSTART.md)** — workspace setup, where to put your CV and supporting documents (certificates, talks, diplomas), and the commands to run in order.

## What It Does

This plugin turns Claude into your personal job search assistant on LinkedIn. It handles the pipeline from CV optimisation to application submission, so you can focus on preparing for interviews instead of scrolling job boards.

- **CV Analysis & Improvement** — ATS compatibility scoring, keyword gap analysis, persuasion-psychology-aware rewrites.
- **Deep Job Discovery** — Boolean title-cluster and skill-combination queries, filter-addressed search URLs, geo iteration, and a learning loop that remembers which queries actually produce good jobs. Catches roles whose titles don't match your list.
- **Smart Matching** — hard gates on your declared dealbreakers, then per-dimension scoring with evidence quotes from the JD, ranked by tier and freshness.
- **Job Alerts** — derives LinkedIn alerts from your query plan so nothing slips through while you're away.
- **Daily Notification Sweep** — scans your unread job-alert notifications, scores new listings, and writes a ranked report.
- **Easy Apply** — handles LinkedIn Easy Apply for jobs you approve. Hands off external applications to you.
- **Inbox Monitoring** — scans recruiter messages, qualifies leads (hot/warm/cold), drafts replies for your approval.
- **Profile Optimisation** — rewrites your headline, summary, experience, and skills for recruiter and ATS visibility.

## Commands

All commands are user-invoked slash commands. The model will **not** auto-trigger them — browser automation, applications, and recruiter replies only happen when *you* ask.

| Command | Description |
|---------|-------------|
| `/check-job-notifications` | **Daily driver** — check notifications + Top picks + Saved jobs, expand similar-jobs from A-tier hits, score new listings, save a ranked report |
| `/deep-sweep` | **Weekly thorough scan** — full Boolean query plan (title clusters + skill queries + synonyms), all source surfaces, Past Week, pages 1-3, similar-jobs expansion. Run once a week |
| `/ultramode` | **Opt-in multi-source sweep** beyond LinkedIn (off by default) — builds a verified per-workspace source registry from your CV, sweeps it, and returns one unified tier-ranked report with a direct apply-at-source link per role. `sources`: edit the registry; `onboarding`: re-run the lane interview |
| `/analyze-cv` | Analyse and optimise your CV for ATS and recruiters; discover per-workspace dealbreakers, voice, scoring dimensions, and Boolean query clusters |
| `/job-search` | Zero-arg: the full query plan — Boolean title clusters, skill-combination queries, geo iteration, synonym rescue, repost dedupe. Single-arg: search that title only |
| `/create-alerts` | Zero-arg: derive 3-5 LinkedIn alerts from your query plan. `manual`: dictate criteria yourself |
| `/match-jobs` | Score and rank job listings against your CV and requirements |
| `/apply` | Apply to approved jobs via LinkedIn Easy Apply |
| `/check-inbox` | Monitor LinkedIn inbox for recruiter messages and leads |
| `/optimize-profile` | Analyse and improve your LinkedIn profile |
| `/cover-letter` | Generate a tailored cover letter (3 angle options) for a specific job |
| `/interview-prep` | Generate an interview-prep packet (SPAR narratives, predicted questions, questions to ask) for a specific job |
| `/funnel-report` | Pipeline analytics: 30/60/90-day funnel, drop-offs, trending keywords, suggested next actions |
| `/index-docs` | Re-scan workspace for supporting documents and rebuild the index |

## Skills

These are model-auto-loaded playbooks used by the commands above. You don't invoke them directly.

| Skill | Purpose |
|-------|---------|
| `_cv-optimizer` | ATS analysis, keyword optimisation, SPAR-method rewrites |
| `_job-matcher` | Hard-gated, segment-aware, per-dimension scoring with evidence quotes |
| `_gate-engine` | Hard-gate evaluator — runs before scoring; auto-D-tiers any job that violates a declared dealbreaker |
| `_profile-optimizer` | LinkedIn SEO, headline formulas, section-by-section optimisation |
| `_recruiter-engagement` | Lead qualification, response drafting, conversation management |

---

### Sharper matching & wider recall (v0.12.0)

The hardest part of a job search isn't scrolling — it's surfacing the roles you'd be a *great* fit for, especially when they're written in words you'd never have searched for. This release tackles both ends of that problem.

**Wider recall — catches great-fit roles written in different words.** `/analyze-cv` now derives a **capability graph** from your CV — the functional and adjacent capabilities behind your stated skills, not just the tool names — and shows it to you for approval before it's used. Paired with a conservative **jargon and alias map** (high-confidence title and skill synonyms, grown from the job descriptions your sweeps already read), it feeds a new line of **capability queries** into your existing search plan. These find well-matched roles that were retitled, jargon-rebranded, or described at the function level ("scale, availability, observability") rather than the tool level ("Kubernetes") — the kind your title and skill searches quietly miss. The queries run on `/job-search`, `/deep-sweep`, and ultramode, are capped at a few per run, and ride the same learning loop as every other query: the ones that keep finding A/B-tier jobs graduate into your clusters, the ones that don't retire on their own.

**Sharper ranking — shows where you're a genuine standout, best matches first.** A flat A/B/C list doesn't tell you where you're exceptional versus merely qualified. Now each A/B-tier match carries a **competitiveness** badge (are you a standout for this role?), a **confidence** badge (how sure is the match?), and a short **explanation tag** (`all-fit`, `one-gap`, `overqualified`, and so on). Reports sort **within each tier by confidence then recency**, so the bulletproof standout matches rise to the top of their tier instead of being buried.

It's all additive: your existing tiers, scores, and cached results are untouched, and there's nothing to migrate.

---

### Ultramode — sourcing beyond LinkedIn (v0.11.0+)

LinkedIn is one market surface. Many of the roles you could actually land are posted elsewhere first — on employer ATS boards, on occupation- and geography-specific boards, on remote-native feeds, in freelance marketplaces, and in community channels. **Ultramode** is an opt-in sweep that widens your sourcing into those places and folds everything it finds into the same tracker, scoring, and report you already use.

**It is off by default.** The LinkedIn pipeline is unchanged — turning ultramode on is a choice you own.

**How to use it:**

- `/ultramode` — runs the external sweep and renders its own report.
- `/ultramode sources` — re-runs source discovery or lets you edit the registry (and `/ultramode sources add <url|name>` adds a board you already use).
- `/ultramode onboarding` — re-runs the lane interview.

**The first run** reads what it can from your CV and keyword corpus, then asks you for what it cannot safely infer — your **base country** (asked explicitly and always confirmed out loud, never guessed from an email handle), your target geography, work arrangement, contract type, and field. From that it builds a **verified** per-workspace source registry (`.job-scout/sources.json`): it enumerates candidate sources widely, live-probes and adversarially verifies every one before it counts, and keeps going until fresh strategies turn up nothing new. Nothing enters the registry on the model's word alone.

**The source categories** it covers are universal — employer ATS providers, remote-native boards, aggregators, national and vertical boards, freelance marketplaces, and community channels — but the concrete sources that fill them are derived for *your* lane. A small universal backbone is always available so even rare occupations have coverage out of the box.

**Keyless-first.** Ultramode works immediately with zero API keys (ATS boards, niche and remote feeds, and any keyless aggregator). If discovery finds a keyed aggregator that would materially improve coverage for your lane, it asks inline with the signup link and gracefully skips if you decline. Any keys you add live in your gitignored workspace config and are never entered into a browser form.

**The results** come back as one unified, tier-ranked report — every job from every source in a single list, ranked A→B→C and freshest-first, with the **source shown only as a chip**, never as the organising axis. Each role carries a direct **apply-at-source** link to the canonical, direct-to-employer listing (employer ATS is preferred over LinkedIn, aggregators, and marketplaces), plus an "also seen on N sources" line. Dealbreaker-gated jobs collapse into the same "Filtered out" group as everywhere else.

Set `/config ultramode.default on` to have your existing `/job-search` and `/deep-sweep` sweeps widen to the external registry automatically.

---

### The discovery engine (v0.10.0+)

Every LinkedIn search the plugin runs follows `skills/shared-references/linkedin-search.md`:

- **Filter-addressed URLs** — workplace type, contract type, recency, and sort order are set in the URL itself, not clicked through the filter UI. Deterministic, reproducible, faster.
- **Boolean title clusters** — `/analyze-cv` groups your target titles into synonym clusters; one query like `("Head of Platform" OR "Platform Engineering Manager") NOT (intern OR graduate)` covers what used to take three searches.
- **Skill-combination queries** — built from the keyword corpus your sweeps accumulate, these find well-matched roles whose titles you'd never have guessed.
- **A learning loop** — every query's yield is recorded in `query-stats.json`. Proven queries run first, dead queries retire after three empty runs, and synonym variants that keep producing A/B-tier jobs get promoted into your clusters.
- **Repost dedupe** — re-listed jobs (same company, title, and location under a fresh ID) are recognised and skipped instead of being re-extracted and re-scored.
- **Freshness flags** — A/B-tier jobs posted within 48 hours carry an "⚡ apply early" chip; applying early is the cheapest way to raise your response rate.

### Visual reports (v0.7.0+)

Six Tier 1 commands — `/match-jobs`, `/job-search`, `/check-job-notifications`, `/funnel-report`, `/check-inbox`, `/interview-prep` — now render their output as a self-contained HTML report (Modern Cards aesthetic, light interactivity) that auto-opens in your Chrome via the existing Claude Chrome extension.

Reports are saved under `.job-scout/reports/`. Snapshot views (match-jobs, job-search, check-job-notifications, check-inbox) write `<view>-latest.html`, overwriting on each run. Time-series views (funnel-report, interview-prep) write timestamped files; old files auto-archive after 90 days.

On the first Tier 1 invocation after upgrade, you pick how output is displayed:

- `always` — render HTML and auto-open in Chrome (best experience; higher token cost).
- `never` — render styled markdown directly in the conversation window (lower token cost).
- `ask` — choose per-run.

Change later with `/config render <mode>`. When HTML rendering or Chrome-open fails, the plugin asks if you want the markdown view instead — output is never lost.

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
    scores.json               # job results keyed by (job_id, cv_hash, profile_hash, rubric_version)
    query-stats.json          # per-query yield memory — powers the learning loop
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
- Job results are cached per `(job_id, cv_hash, profile_hash, rubric_version)` — unchanged jobs against an unchanged CV and profile are never re-scored, and reposts of known jobs are recognised by fingerprint and skipped entirely.
- LinkedIn profile snapshots are cached for 7 days so re-runs don't re-read every section from scratch.
- Recruiter threads with no new messages are skipped on subsequent `/check-inbox` runs.

The practical effect: the second, third, and tenth runs of `/check-job-notifications` are dramatically cheaper than the first.

### First-run bootstrap

The first time you run any command in a new project, the plugin will ask:

> "I don't see a `.job-scout/` folder in this project yet. This is where I'll keep your CV profile, the list of jobs I've already shown you, cached scores, and run reports — all scoped to *this* project so different job searches stay separate. Want me to create it now?"

**Say yes.** The plugin will create the folder, write a stub `user-profile.json` and an empty `tracker.json`, and proceed. If you decline, the plugin will fall back to legacy behaviour (writing loose files at your workspace root) for that session only, and will not nag you again in the same session.

---

## Installation

Clone this repo and install as a plugin:

```bash
git clone https://github.com/turagit/claude-job-scout.git
```

In Claude Desktop / Claude Code, go to Settings → Plugins → "Install from folder" and select the cloned directory. Claude detects `.claude-plugin/plugin.json` and installs all the slash commands and internal skills automatically.

## Requirements

- **Claude Code or Claude Desktop**
- **The Claude Chrome extension** — this is the *only* browser mechanism the plugin uses. See the box below.
- **LinkedIn account** — you must be logged in to LinkedIn in your browser
- **Your CV** — place it anywhere in the project workspace; the plugin will find it by name (`cv.*`, `resume.*`, `curriculum.*`) or ask you to point to it

> **The plugin does NOT use "computer use."**
> Every browser interaction goes through the Claude Chrome extension running in your own logged-in browser tab. The plugin never takes control of your screen, mouse, or keyboard, and it will never ask you to enable computer use. If you ever see a prompt asking to enable computer use while running a command from this plugin, **something is wrong** — decline it and report it as a bug. The full policy lives at `skills/shared-references/browser-policy.md`.

## Getting Started

1. Install the plugin (above).
2. `cd` into the project folder you want to run your job search from (create a new one if you like — e.g. `~/projects/freelance-search/`).
3. **Drop your CV into that folder — and everything that tells your professional story alongside it.** The more context Claude has, the sharper every rewrite, score, and recruiter reply becomes. Consider adding:
   - **Certifications & diplomas** — AWS, Azure, GCP, PMP, CFA, university transcripts, language certificates. Claude will surface them in the right places and match them against JD "must-have" keywords you'd otherwise miss.
   - **Talks, presentations & decks** — conference slides, internal brown-bags, webinars. These are authority signals Claude can weave into your headline, About section, and interview ammunition.
   - **Architectural diagrams & design docs** — system designs, RFCs, whiteboard photos, Miro exports. They're proof-of-depth that turns "Led platform migration" into a story a hiring manager can actually picture.
   - **Case studies & write-ups** — post-mortems, project retrospectives, launch reports, anything with a measurable outcome you're proud of.
   - **Publications, patents & open-source** — papers, blog posts, GitHub profile URL, package names you maintain. All three are rare trust-triggers most CVs leave on the table.
   - **Testimonials, recommendations & client feedback** — screenshots of kind words from managers or clients. These become the seed for LinkedIn recommendation requests and About-section social proof.
   - **Awards, selections & "one of N chosen" moments** — scholarships, accelerators, hackathon wins, "top 3%" rankings. Scarcity signals punch above their weight on both CV and profile.
   - **Anything else that tells your story** — portfolio PDFs, product screenshots, media mentions, podcast appearances. If it would make you proud to show a hiring manager, put it in the folder.

   File format doesn't matter much — PDF, DOCX, PNG, Markdown, plain text all work. Claude will index what it can read and ask you about the rest. Nothing leaves your machine; see the [`.job-scout/` section](#the-job-scout-workspace-important) for the full data-handling story.
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

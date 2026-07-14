# Quick Start — LinkedIn Job Hunter

A five-minute setup to go from "plugin installed" to your first ranked list of matching jobs. You run everything as slash commands inside Claude Code, in a folder of your choosing. The plugin keeps all its state in a single `.job-scout/` folder it creates there — so each job search lives in its own workspace.

## Before you begin

- **Claude Code** with the `linkedin-job-hunter` plugin installed.
- **The Claude Chrome extension**, signed in to **your own LinkedIn account** in that browser. This is how the plugin works *inside the browser you already use* — it never takes over your screen or asks for your password. (`/ultramode`'s external sources read public job APIs directly and need no extension; LinkedIn itself still goes through it.)
- **Your CV** as a file (PDF, DOCX, DOC, TXT, or Markdown).
- Optionally, **supporting documents** — diplomas, certificates, conference talks, architecture decks, recommendations, case studies, portfolio pieces.

Nothing is ever submitted or sent on your behalf without you approving it first.

---

## Step 1 — Make a workspace

One folder per job hunt. Open a terminal:

```bash
mkdir ~/job-hunt
cd ~/job-hunt
```

Run Claude Code from inside `~/job-hunt`. The first command you run will offer to create the `.job-scout/` state folder here — say yes. **You never edit `.job-scout/` by hand; the plugin owns it.**

## Step 2 — Add your CV (and your supporting documents)

Copy your files into the **workspace root** (`~/job-hunt`), *not* into `.job-scout/`:

```bash
cp ~/Documents/my-cv.pdf        ~/job-hunt/cv.pdf
cp ~/Documents/aws-cert.pdf     ~/job-hunt/
cp ~/Documents/kubecon-talk.pptx ~/job-hunt/
cp ~/Documents/diploma.pdf      ~/job-hunt/
```

- **CV:** name it `cv.*`, `resume.*`, or `curriculum.*` so it's found automatically. If it's named something else, `/analyze-cv` will simply ask which file is your CV.
- **Supporting documents:** drop any of `.pdf .docx .doc .pptx .key .png .jpg .md .txt` in the same folder. The plugin will offer to index them on first run; the index makes your **cover letters and interview prep sharper** (it can cite your real certificates, talks, and case studies instead of generic claims). You can always (re)scan later with `/index-docs`.

## Step 3 — Run these commands, in order

Type each as a slash command in Claude Code. The plugin asks questions where it needs you — answer them; it proposes things — approve or edit them.

1. **`/analyze-cv`** — the required first step. It creates `.job-scout/`, runs a one-time **discovery interview** (your target roles, must-haves and dealbreakers, tone), reads your CV, and proposes:
   - your **scoring dimensions** (how jobs get graded A/B/C/D),
   - your **search clusters** (the title/keyword groups it will search), and
   - your **capability graph** — the latent and adjacent skills your CV credibly speaks to, so it can find great-fit roles written in *different words*.
   Review and approve each. *(If you added supporting documents, it'll also offer to index them — say yes, or run `/index-docs` whenever you add more.)*

2. **`/sources onboarding`** — builds your verified source registry. Answer the country question honestly; it is never guessed. Covers LinkedIn plus employer ATS boards, remote-job feeds, aggregators, national boards, freelance marketplaces, and community channels, all live-verified before anything is added. The registry draws from a packaged **EU/NL/BENELUX source catalogue**, with BENELUX sources swept first as the highest-value hunting ground for an NL-based, EU-remote search. `/sources scope` shows and changes how wide it casts (`eu-nl` default, or `eu-broad` to opt in global marketplaces); `/sources retire <name>` permanently drops a source you never want swept again.

3. **`/ultramode`** — the full-market sweep. 30–45 minutes, walk away — the report is delivered via the harness file panel when it's done (falling back to your OS's default file opener if that's unavailable). Near-misses (strong-fit roles that failed just one hard gate) appear in their own rail with `/bend` hints. *(First time any report is shown, the plugin asks once whether you prefer rich HTML reports opened in your browser or plain text — that's `/config render`.)* Run `/ultramode super` for the exhaustive scope — every source, no rotation held back — with a five-way accounting (attempted/completed/login-blocked/failed/rotated-out) in the summary. If a source needs sign-in, the plugin reuses your existing Chrome session where one exists; if it hits a login wall it skips that source without stalling the run and tells you to sign in yourself in the open tab, then rerun `/ultramode source <name>`.

Once your first report is in, `/optimize-profile` aligns your LinkedIn profile with your CV, and `/job-search <title>` or `/match-jobs` score anything specific you want to check by hand.

Then settle into a rhythm:

- **Daily:** **`/check-job-notifications`** — your driver. Scans new LinkedIn alerts + recommendations, scores the new roles, writes a fresh ranked report.
- **Weekly:** **`/ultramode`** — the full-market sweep again: LinkedIn plus every verified source, deduped into one ranking.
- **Between sweeps:** **`/tune`** — show and adjust titles, keywords, exclusions, and hard gates, without a full re-interview.
- **Per role you like:** **`/cover-letter <job>`** (three tailored angles, citing your supporting docs) and **`/interview-prep <tracker-id>`** (SPAR stories, likely questions, questions to ask).
- **To apply:** **`/apply`** — walks you through LinkedIn Easy Apply on the jobs *you* approved. Never auto-submits.
- **Recruiters:** **`/check-inbox`** — triages LinkedIn messages into hot/warm/cold leads and drafts replies for your approval.
- **Alerts that work while you sleep:** **`/create-alerts`** — proposes LinkedIn job alerts from your search plan.
- **See how you're doing:** **`/funnel-report`** — your 30/60/90-day pipeline, drop-offs, trending keywords, and suggested next moves.

Anytime: **`/config`** to change settings (report style, optional API keys).

---

## What to expect

- **Everything stays local**, in `.job-scout/` in this workspace — your profile, the jobs it tracks, the JDs, the reports. Nothing is uploaded anywhere; the folder is git-ignored.
- **You're always in control.** Commands are user-invoked; applications and recruiter replies are drafted for your approval, never sent automatically.
- **It learns your lane.** The more it sees (and the jobs you approve or reject), the sharper the searches and rankings get.
- **British English**, by default, in everything it writes for you.

### The first 15 minutes, condensed

```text
1. mkdir ~/job-hunt && cd ~/job-hunt          # a workspace
2. copy your CV + certificates/talks in       # into ~/job-hunt (not .job-scout/)
3. /analyze-cv          → approve the proposals  # profile + capability graph
4. /sources onboarding  → answer the country Q   # verified source registry
5. /ultramode           → walk away, ~30-45 min  # LinkedIn + every source, one report
…then /check-job-notifications daily, /tune between sweeps.
```

For the full feature reference, see the [README](README.md).

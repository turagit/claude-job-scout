---
name: analyze-cv
description: Analyse and optimise your CV for ATS and recruiters
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: [cv-file-path]
disable-model-invocation: true
---

Analyse and improve the user's CV using the **_cv-optimizer** skill.

## Step 0: Bootstrap workspace

Follow `shared-references/workspace-layout.md` to ensure `.job-scout/` exists in the current workspace. All state below lives inside it.

## Step 1: Load CV

If argument provided, read file at @$1. Otherwise, follow `shared-references/cv-loading.md` to locate the CV, hash it, and load any existing profile.

**Cache check:** if `.job-scout/cache/cv-analysis-<hash>.json` exists for the current CV's hash AND the user is not requesting a fresh run, return the cached analysis directly. Re-analysing an unchanged CV against an unchanged profile burns tokens for no new information.

## Step 2: Discovery Interview (MANDATORY — DO NOT SKIP)

Run the **Phase 0 Discovery Interview** from the _cv-optimizer skill. Ask all questions in a single structured message grouped by category (Identity & Career Context, Strengths & Differentiators, Target & Constraints). This is critical — the quality of the optimisation depends entirely on having this context upfront.

If the user has an existing `user-profile.json`, pre-fill what you can and confirm: "I have these details saved — are they still accurate?" Only ask for missing or potentially stale information.

If the user provides a target job description, extract it and use it for keyword gap analysis.

**Do NOT proceed to analysis until the user has responded to the discovery questions.** A generic analysis without context produces generic results.

## Step 3a: Discovery interview — segment, dealbreakers, voice (v0.8.0)

Skip this step if `user-profile.json.discovery_complete == true` AND the user did not pass `--rediscover`.

Otherwise conduct the hybrid discovery interview. Four blocks, asked in sequence:

### Segment declaration

"In one short sentence, describe what kind of role you're hunting for in this workspace. This is just a free-text label so we both remember what this lane is for, and it helps tailor the matching rubric. Examples: 'head pastry chef in Lisbon', 'construction site engineer — UK civils', 'mid-career switch to UX research', 'freelance backend contracts EU-remote', 'permanent leadership roles in enterprise IT'."

Write the user's exact response to `user-profile.json.segment`. The matcher uses it both as a prompt anchor and as input to the dimensions discovery (Step 3c below).

### Dealbreaker checklist (menu, 7 categories)

Walk this checklist. For each item, ask the user to confirm whether it's a HARD GATE for them. A hard gate auto-rejects any listing that violates it — see `../_gate-engine/SKILL.md`.

| # | Question | If yes, write to |
|---|---|---|
| 1 | "Are there work arrangements you absolutely won't consider? (e.g. 'must be remote', 'no fully on-site'.)" | `requirements.work_arrangement` (whitelist) and `requirements.deal_breakers[]` with `kind: work_arrangement` |
| 2 | "Is contract type a hard rule? (perm-only, freelance-only, or both fine?)" | `requirements.contract_type` (whitelist) and `requirements.deal_breakers[]` with `kind: contract_type` |
| 3 | "Is there a seniority level below which a listing should be auto-rejected?" | `requirements.seniority_floor` and `requirements.deal_breakers[]` with `kind: seniority_floor` |
| 4 | "Geographies you won't entertain? (e.g. 'must be EU-based', 'no US-based on-site', 'no relocation required'.)" | `requirements.location_preferences` and `requirements.deal_breakers[]` with `kind: location` |
| 5 | "Industries you don't want to be approached for? (e.g. gambling, defence, crypto, MLM.)" | `requirements.industries_to_avoid` and `requirements.deal_breakers[]` with `kind: industry` |
| 6 | "Specific companies to avoid?" | `requirements.companies_to_avoid` and `requirements.deal_breakers[]` with `kind: company` |
| 7 | "Minimum day rate or salary floor below which a listing should auto-reject?" | `requirements.min_day_rate` / `requirements.salary_floor` and `requirements.deal_breakers[]` with `kind: rate_floor` or `salary_floor` |

For every `deal_breaker` entry, set `source: "elicited"` and `added_at: <now ISO8601>`.

### Open free-text follow-up

"Anything else that should auto-reject a listing for you? Up to three. Free text — I'll evaluate each against new JDs."

For each non-empty answer, append a `deal_breakers[]` entry with `kind: "custom"`, `free_text: "<the answer>"`, `source: "elicited"`. Cap at 3 entries — each `custom` rule is one extra LLM call per scored job.

### Tone confirmation

Read the existing `user-profile.json.tone` block. Echo a one-line summary:

> "Voice on drafts is set to: {{tone.dialect}}, {{tone.register}}, {{tone.warmth}}. Want to change it?"

If yes, walk a brief elicitation (register, dialect, warmth, vocabulary cues, exemplars, avoid). If no, do nothing — keep the current tone. If the tone block is empty (new workspace), run a fresh elicitation.

### Step 3c: Dimensions discovery

Generate the 5-dimension rubric this workspace will use for job scoring. Read the universal bootstrap at `../_job-matcher/references/dimensions-default.md` and ADAPT it to this workspace by:

1. Considering `cv_summary.key_skills`, `cv_summary.target_roles` or `target_titles`, `cv_summary.industries`, `segment` (the free-text description from Step 3a above), and `requirements`.
2. For each of the 5 universal dimensions (Skills & technical fit / Role shape match / Domain & context / Engagement fit / Trajectory fit), rewrite the A/B/C/D criteria so they reference what would actually appear in JDs for THIS user's lane. Example transformations:
   - For a pastry chef workspace, "Skills & technical fit" criterion-A might be rephrased to: "Every named technique (lamination, sugar work, plated desserts, etc.) the JD requires is demonstrably evidenced on the CV; CV shows multi-year depth in the chosen specialism."
   - For a construction-engineer workspace, "Domain & context" criterion-A might be rephrased to: "Sector matches candidate's track record (civils, residential, commercial, infrastructure); regulatory regime (UK Building Regs, Eurocodes, AS/NZS) aligns."
3. Present the proposed 5 dimensions to the user as a structured block. Ask: "Does this look right, or do you want to edit any of the dimensions or their criteria?"
4. On approval, write the array to `user-profile.json.dimensions[]` per the shape in `../shared-references/canonical-schemas.md`. On revision, update accordingly.

The matcher reads `user-profile.json.dimensions[]` at scoring time. If the array is empty or absent, the matcher falls back to the universal default — never blocks scoring.

A user can re-run dimensions discovery later by editing `dimensions[]` directly, or by re-running `/analyze-cv --rediscover`.

### Step 3d: Query-cluster discovery (v0.10.0)

Generate the Boolean search clusters that `/job-search` and `/deep-sweep` will run, per `../shared-references/linkedin-search.md` §3a:

1. Group `target_titles[]` into clusters of true synonyms — titles a recruiter would use interchangeably for the same role. Titles that represent genuinely different roles get their own cluster.
2. For each cluster, propose 1–2 additional synonym titles the user didn't list but the market uses (drawn from the segment and `cv_summary`).
3. Ask one follow-up: "Any words that should always be excluded from search results? (e.g. intern, graduate, unpaid — I'll add them as NOT terms.)" A declared `seniority_floor` above entry level pre-fills `["intern", "graduate"]` for confirmation.
4. Present the proposed clusters — label, titles, NOT terms — and ask the user to approve or edit.
5. On approval, write `query_clusters[]` to `user-profile.json` per the shape in `../shared-references/canonical-schemas.md`.

Workspaces without `query_clusters[]` are never blocked — the search commands fall back to one plain query per title.

### Persist + mark discovery complete

After the interview, write all changes to `user-profile.json` via the atomic-write pattern in `../shared-references/state-validators.md` (using `validate_profile`). Set `discovery_complete: true` and `last_updated: <now>`.

## Step 3: Analyse

Load the **_cv-optimizer** skill. Score all seven dimensions (1–10 each, weighted). Present:

1. **Overall score** with letter grade (A/B/C/D) and per-dimension breakdown with evidence
2. **Strength spotlight** — top 3 things the CV already does well (lead with positives)
3. **Top 5 improvements** ranked by weighted point impact, with before/after previews
4. **Keyword gap report** (if JD provided): match percentage, must-add keywords, suggested placements
5. **7-second scan test result** — can a recruiter extract role, seniority, top skills, and one number in 7 seconds?
6. **Psychology audit** — which persuasion techniques are already working, which are missing

Be encouraging — highlight strengths before improvements. Frame improvements as opportunities, not failures.

## Step 4: Generate Improved CV

If user wants a rewrite:
- Create optimised version applying all SPAR rewrites, keyword placements, psychological persuasion techniques, and structural improvements
- Preserve the user's voice, facts, and tone preference (from discovery interview)
- Save with "-optimized" suffix
- Provide a **change summary** listing every modification made and why
- Show **before/after comparison** for the 3 most impactful changes
- Provide **interview ammunition** — full SPAR narratives for top achievements the user can use in interviews

## Step 5: Update Profile & Cache

Save to `.job-scout/user-profile.json` (create/merge): cv_path, cv_hash, cv_summary (key_skills, technologies, seniority, years_experience, target_roles, domain_expertise, industries, top_achievements), last_updated, master_keyword_list, discovery_complete: true. See user-profile-schema reference for full schema.

Also write the full analysis output to `.job-scout/cache/cv-analysis-<hash>.json` so subsequent runs on the same CV return instantly.

Save the master keyword list so that `/optimize-profile` can reuse it for LinkedIn alignment.

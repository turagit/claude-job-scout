---
description: Analyze and optimize your CV for ATS and recruiters
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: [cv-file-path]
---

Analyze and improve the user's CV using the **cv-optimizer** skill.

## Step 0: Bootstrap workspace

Follow `shared-references/workspace-layout.md` to ensure `.job-scout/` exists in the current workspace. All state below lives inside it.

## Step 1: Load CV

If argument provided, read file at @$1. Otherwise, follow `shared-references/cv-loading.md` to locate the CV, hash it, and load any existing profile.

**Cache check:** if `.job-scout/cache/cv-analysis-<hash>.json` exists for the current CV's hash AND the user is not requesting a fresh run, return the cached analysis directly. Re-analyzing an unchanged CV against an unchanged profile burns tokens for no new information.

## Step 2: Discovery Interview (MANDATORY — DO NOT SKIP)

Run the **Phase 0 Discovery Interview** from the cv-optimizer skill. Ask all questions in a single structured message grouped by category (Identity & Career Context, Strengths & Differentiators, Target & Constraints). This is critical — the quality of the optimization depends entirely on having this context upfront.

If the user has an existing `user-profile.json`, pre-fill what you can and confirm: "I have these details saved — are they still accurate?" Only ask for missing or potentially stale information.

If the user provides a target job description, extract it and use it for keyword gap analysis.

**Do NOT proceed to analysis until the user has responded to the discovery questions.** A generic analysis without context produces generic results.

## Step 3: Analyze

Load the **cv-optimizer** skill. Score all seven dimensions (1–10 each, weighted). Present:

1. **Overall score** with letter grade (A/B/C/D) and per-dimension breakdown with evidence
2. **Strength spotlight** — top 3 things the CV already does well (lead with positives)
3. **Top 5 improvements** ranked by weighted point impact, with before/after previews
4. **Keyword gap report** (if JD provided): match percentage, must-add keywords, suggested placements
5. **7-second scan test result** — can a recruiter extract role, seniority, top skills, and one number in 7 seconds?
6. **Psychology audit** — which persuasion techniques are already working, which are missing

Be encouraging — highlight strengths before improvements. Frame improvements as opportunities, not failures.

## Step 4: Generate Improved CV

If user wants a rewrite:
- Create optimized version applying all SPAR rewrites, keyword placements, psychological persuasion techniques, and structural improvements
- Preserve the user's voice, facts, and tone preference (from discovery interview)
- Save with "-optimized" suffix
- Provide a **change summary** listing every modification made and why
- Show **before/after comparison** for the 3 most impactful changes
- Provide **interview ammunition** — full SPAR narratives for top achievements the user can use in interviews

## Step 5: Update Profile & Cache

Save to `.job-scout/user-profile.json` (create/merge): cv_path, cv_hash, cv_summary (key_skills, technologies, seniority, years_experience, target_roles, domain_expertise, industries, top_achievements), last_updated, master_keyword_list, discovery_complete: true. See user-profile-schema reference for full schema.

Also write the full analysis output to `.job-scout/cache/cv-analysis-<hash>.json` so subsequent runs on the same CV return instantly.

Save the master keyword list so that `/optimize-profile` can reuse it for LinkedIn alignment.

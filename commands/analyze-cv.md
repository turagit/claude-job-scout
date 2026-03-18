---
description: Analyze and optimize your CV for ATS and recruiters
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: [cv-file-path]
---

Analyze and improve the user's CV using the **cv-optimizer** skill.

## Step 1: Load CV

If argument provided, read file at @$1. Otherwise, locate CV in workspace or ask user. Support .pdf, .docx, .txt, .md.

## Step 2: Target Role (Optional)

Ask what role(s) they're targeting and whether they have a specific job description to optimize against. Proceed with general analysis if skipped.

## Step 3: Analyze

Load the **cv-optimizer** skill. Score all five dimensions (1-10 each, weighted). Present: overall score with breakdown, top 3 strengths, top 5 improvements ranked by impact, before/after rewrites using PAR method, keyword gap report (if JD provided).

Be encouraging — highlight strengths before improvements.

## Step 4: Generate Improved CV

If user wants a rewrite: create improved version preserving voice and facts, save with "-optimized" suffix, summarize all changes.

## Step 5: Update Profile

Save to `user-profile.json` (create/merge): cv_path, cv_summary (key_skills, technologies, seniority, years_experience, target_roles, domain_expertise), last_updated. See user-profile-schema reference for full schema.

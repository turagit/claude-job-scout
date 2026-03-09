---
description: Analyze and optimize your CV for ATS and recruiters
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: [cv-file-path]
---

Analyze and improve the user's CV using the cv-optimizer skill.

## Step 1: Load the CV

If an argument is provided, read the file at @$1. Otherwise, ask the user to upload or point to their CV file. Support .pdf, .docx, .txt, and .md formats. Use appropriate tools to extract text content from the file.

## Step 2: Ask for Target Role (Optional)

Ask the user:

- What role(s) are you targeting? (job title, industry)
- Do you have a specific job description you want to optimize for? If so, ask them to share it.

If they skip this, proceed with a general analysis.

## Step 3: Analyze

Load and follow the cv-optimizer skill. Evaluate the CV across all five dimensions:

1. ATS Compatibility
2. Content Impact
3. Keyword Optimization
4. Structure & Readability
5. Professional Positioning

Score each dimension 1-10 and calculate the weighted overall score.

## Step 4: Present Findings

Present:

1. Overall score with dimension breakdown
2. Top 3 strengths
3. Top 5 improvements ranked by impact
4. Before/after rewrites for weak sections using the PAR method
5. Keyword gap report (if a target job description was provided)

## Step 5: Generate Improved CV

Ask the user if they want a fully rewritten version. If yes:

- Create an improved version preserving their voice and factual content
- Save it alongside the original with "-optimized" appended to the filename
- Present a summary of all changes made

Always be encouraging — highlight what's already strong before diving into improvements.

## Step 6: Update User Profile

Save the analysis results to `user-profile.json` in the workspace root (create if it doesn't exist, merge if it does):

- `cv_path` — Path to the CV file that was analyzed
- `cv_summary.key_skills` — Top skills extracted from the CV
- `cv_summary.technologies` — Technologies, tools, and frameworks found
- `cv_summary.seniority` — Estimated seniority level
- `cv_summary.years_experience` — Total years of experience
- `cv_summary.target_roles` — Inferred target roles from career trajectory
- `cv_summary.domain_expertise` — Domain specializations identified
- `last_updated` — Current timestamp

See the user-profile-schema reference in the job-matcher skill for the full schema.

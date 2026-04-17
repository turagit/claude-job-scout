# JD Keyword Extraction

Shared procedure for extracting keywords from job descriptions and merging them into the learned corpus. Every command that ingests JDs (`/match-jobs`, `/check-job-notifications`, `/job-search`) follows this procedure.

## When to run

After extracting job details (Step 4 in most commands) and before scoring. The extraction piggybacks on the JD text already in context — no additional LLM call is needed for the merge step.

## Extraction steps

1. Parse the JD text for **hard skills, tools, frameworks, certifications, methodologies, and domain terms**. Use `ats-keywords.md` as a seed vocabulary for recognition, but also discover terms not in the seed list (novel tools, niche frameworks, domain jargon).
2. For each extracted keyword, normalise to a canonical form: lowercase, collapse whitespace, preserve slashes and hyphens (e.g., `CI/CD`, `event-driven`). Include both acronym and spelled-out forms as separate entries (e.g., `aws` and `amazon web services`).
3. Tag `seniority_tags` from the job's experience-level field (e.g., "Senior" → `["senior"]`). Tag `role_tags` from the job's title (e.g., "Senior Data Engineer" → `["data-engineer"]`).
4. Load `.job-scout/cache/jd-keyword-corpus.json` (create if missing — see Shape below).
5. For each keyword:
   - **If it exists in the corpus:** increment `frequency`, update `last_seen`, append the job's ID to `source_jobs` (dedupe the array — no duplicate IDs).
   - **If it's new:** create the entry with `frequency: 1`, current timestamp for `first_seen` and `last_seen`, and `source_jobs: [<job_id>]`.
6. Increment `total_jds_ingested` by the number of JDs processed in this batch. Update `last_updated`.
7. Write the updated corpus back to `.job-scout/cache/jd-keyword-corpus.json`.

## Corpus file

**Location:** `.job-scout/cache/jd-keyword-corpus.json`

**Shape:**

```json
{
  "version": 1,
  "last_updated": "<ISO>",
  "total_jds_ingested": 0,
  "corpus": {
    "<keyword>": {
      "frequency": 5,
      "seniority_tags": ["senior", "lead"],
      "role_tags": ["data-engineer", "platform-engineer"],
      "first_seen": "<ISO>",
      "last_seen": "<ISO>",
      "source_jobs": ["job_id_1", "job_id_2"]
    }
  }
}
```

**Empty initial state:** `{ "version": 1, "last_updated": null, "total_jds_ingested": 0, "corpus": {} }`

## Consumers

- **_cv-optimizer** (Phase 2 gap analysis): supplements the master keyword list with corpus terms the user's market actually demands.
- **ATS simulator**: uses corpus frequency to weight keyword-match scores — a keyword that appears in 80% of JDs in the user's market is more important than one that appears in 10%.
- **Density check**: uses corpus + master keyword list as the target keyword set.
- **_profile-optimizer** (keyword coverage score): compares profile keywords against corpus.

## Token cost

Negligible incremental cost. The JD text is already loaded for scoring. Extraction is a structured parse of text already in context. The corpus merge is a JSON read-merge-write with no additional LLM call.

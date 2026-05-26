# Phase 5 — Foundations + Accuracy Core Design Spec

**Status:** Approved 2026-05-26 from /grill-me session.

**Problem.** Live workspace state has drifted from spec on every axis: two different tracker schemas across workspaces, seven different status values vs the spec's five, eight different tier values vs the spec's four, zero JD blobs persisted (contract says they must be), empty score and CV caches, 770 jobs of which 24–29% are untiered, zero rejections ever logged, zero hot leads. Match-score false positives dominate user pain because (a) no hard gates enforce dealbreakers, (b) Skills uses keyword bingo on noisy JDs, (c) the score is a single number with no evidence trail.

**Goal.** Ship v0.8.0 with (a) one canonical schema enforced at write time, (b) both workspaces migrated in place, (c) the silently-broken contracts (JD blob persistence, score cache, CV cache, archive pass) actually wired, (d) a hard-gate step before scoring, (e) a segment-aware rubric (director-perm vs freelance) producing per-dimension tiers with evidence quotes — no hidden weighted average.

**Out of scope for this phase.** Coverage adds (Top picks, Similar-jobs, recruiter-link parsing, Saved jobs) — Phase 6. Reject UX in the visual report — Phase 7. Recruiter rebuild — Phase 8. Nurture commands — Phase 9. Outbound recruiter sourcing — Phase 10+.

## Decisions (from the 2026-05-26 grilling session)

1. **Workspaces are independent.** CVDIRECTOR and CVFREELANCER are separately maintained with different CVs, tones, requirements. Fix the schema drift; keep them logically separate.

2. **False positives dominate; fix is hard gates.** Any dealbreaker violation auto-D-tiers the job and skips further scoring. No partial-credit aggregation can rescue a gated job.

3. **Dealbreakers are per-user, elicited at `/analyze-cv` via hybrid menu + free text.** Fixed checklist asks each of: work arrangement, contract type, seniority floor, geography, industries to avoid, companies to avoid, rate/salary floor. Then one open prompt: "anything else that should auto-reject a listing?" Captures generic 80% and personal idiosyncratic gates.

4. **Reject-with-reason → suggest-after-pattern.** Captured at the visual report (Phase 7). Phase 5 only adds the data fields (`reject_reason`, `rejected_at`) and reads them on display; the chip UX ships in Phase 7. No silent auto-promotion ever.

5. **Score shape: per-dimension breakdown + overall tier, no single number.** Each dimension carries A/B/C/D + evidence quotes. Overall tier derived from dimension tiers via fixed rule.

6. **Rubric dimensions are segment-specific.** Workspace declares `segment` at init. Director-perm set: Leadership scope / Domain / Function / Track-record / Cultural signals. Freelance set: Skills (semantic) / Engagement shape / Commercial fit / Stack & methodology / Client signals.

7. **Migrate in place.** Preserve all 770 job IDs (dedupe set worth keeping). Normalize non-canonical statuses and tiers via explicit map. Drop the 7 entries with `status: null` or `version: null` corruption. Backfill `first_seen` from `last_seen` where null.

8. **Voice applies everywhere user-voiced, both workspaces.** British, sophisticated, charming, classy (not over the top), likable, friendly, positive. Codified as a structured tone block in `user-profile.json`. Consumed by recruiter replies, follow-ups, cover letters, profile copy, interview-prep talking points, CV bullet rewrites. Saved to user memory.

## Canonical schemas (locked in this phase)

### user-profile.json (per workspace)

```json
{
  "schema_version": 2,
  "cv_path": "string",
  "cv_hash": "string|null",
  "cv_filename_on_linkedin": "string|null",
  "cv_uploaded_to_linkedin_at": "ISO8601|null",
  "cv_summary": {
    "key_skills": ["string"],
    "technologies": ["string"],
    "seniority": "string",
    "years_experience": "number",
    "target_roles": ["string"],
    "domain_expertise": ["string"],
    "industries": ["string"]
  },
  "target_titles": ["string"],
  "preferred_length_pages": "number|null",
  "linkedin_profile_url": "string|null",
  "profile_hash": "string|null",
  "discovery_complete": "boolean",
  "segment": "director-perm | freelance",
  "requirements": {
    "work_arrangement": ["remote", "hybrid", "on-site"],
    "contract_type": ["permanent", "freelance"],
    "location_preferences": ["string"],
    "seniority_floor": "string|null",
    "min_day_rate": "number|null",
    "ideal_day_rate": "number|null",
    "rate_currency": "string|null",
    "salary_floor": "number|null",
    "salary_currency": "string|null",
    "deal_breakers": [
      {
        "kind": "work_arrangement | contract_type | seniority_floor | location | industry | company | rate_floor | salary_floor | custom",
        "values": ["string"],
        "free_text": "string|null",
        "source": "elicited | learned",
        "added_at": "ISO8601"
      }
    ],
    "nice_to_haves": ["string"],
    "companies_to_avoid": ["string"],
    "industries_to_avoid": ["string"],
    "companies_to_target": ["string"]
  },
  "tone": {
    "register": "string",
    "dialect": "british",
    "warmth": "string",
    "vocabulary_cues": ["string"],
    "exemplars": ["string"],
    "avoid": ["string"]
  },
  "master_keyword_list": ["string"],
  "last_updated": "ISO8601",
  "created_by": "string"
}
```

### tracker.json (per workspace)

```json
{
  "schema_version": 2,
  "version": 2,
  "stats": {
    "total_seen": "number",
    "applied": "number",
    "rejected": "number",
    "last_run": "ISO8601|null",
    "last_search": "ISO8601|null",
    "last_archive_pass": "YYYY-MM-DD|null"
  },
  "jobs": {
    "<job_id>": {
      "id": "string",
      "url": "string",
      "title": "string",
      "company": "string",
      "source": "Job Alert | Top Picks | Search | Inbox | Saved | Similar",
      "score": "number|null",
      "tier": "A | B | C | D | untiered",
      "tier_reason": "string|null",
      "dimensions": {
        "<dimension_name>": {
          "tier": "A | B | C | D",
          "evidence": ["string"]
        }
      },
      "gate_violations": [
        {"kind": "string", "detail": "string"}
      ],
      "rubric_version": "legacy | v1",
      "status": "seen | approved | applied | rejected | skipped",
      "filtered_reason": "string|null",
      "reject_reason": "string|null",
      "rejected_at": "ISO8601|null",
      "approved_at": "ISO8601|null",
      "applied_at": "ISO8601|null",
      "first_seen": "YYYY-MM-DD",
      "last_seen": "YYYY-MM-DD",
      "jd_path": "string|null",
      "notes": "string"
    }
  }
}
```

`description` (full JD blob) is no longer stored inline — it lives in `.job-scout/jds/<job_id>.txt`. `jd_path` is the relative pointer; null when the JD has not yet been extracted.

### recruiters/threads.json (per workspace)

The threads schema is locked in this phase but its full rebuild ships in Phase 8. Phase 5 only normalises lead_tier enums and adds the spec fields where missing — keeps inbox functional without re-architecting it.

```json
{
  "schema_version": 2,
  "last_scanned": "ISO8601|null",
  "scan_source": "string",
  "stats": {
    "total_threads_scanned": "number",
    "hot": "number",
    "warm": "number",
    "cold": "number",
    "non_lead": "number"
  },
  "threads": {
    "<thread_id>": {
      "recruiter_name": "string",
      "participant_title": "string|null",
      "company": "string|null",
      "lead_tier": "hot | warm | cold | non-lead",
      "lead_tier_detail": "string|null",
      "last_seen_msg_id": "string|null",
      "last_drafted_reply": "string|null",
      "last_updated": "ISO8601|null",
      "last_message_date": "YYYY-MM-DD|null",
      "thread_url_path": "string|null",
      "linked_job_ids": ["string"],
      "notes": [
        {"date": "YYYY-MM-DD", "note": "string"}
      ]
    }
  }
}
```

### Canonical enums

| Field | Allowed values |
|---|---|
| `tracker.jobs.*.status` | `seen`, `approved`, `applied`, `rejected`, `skipped` |
| `tracker.jobs.*.tier` | `A`, `B`, `C`, `D`, `untiered` |
| `tracker.jobs.*.rubric_version` | `legacy`, `v1` |
| `tracker.jobs.*.source` | `Job Alert`, `Top Picks`, `Search`, `Inbox`, `Saved`, `Similar` |
| `threads.*.lead_tier` | `hot`, `warm`, `cold`, `non-lead` |
| `user-profile.requirements.deal_breakers[].kind` | `work_arrangement`, `contract_type`, `seniority_floor`, `location`, `industry`, `company`, `rate_floor`, `salary_floor`, `custom` |
| `user-profile.segment` | `director-perm`, `freelance` |

### Status migration map (legacy → canonical)

| Legacy value (observed in live state) | Canonical mapping |
|---|---|
| `filtered_out` | `status: seen` + `filtered_reason: <reason or "legacy">` |
| `seen_filtered_out` | `status: seen` + `filtered_reason: "legacy"` |
| `seen_duplicate` | `status: skipped` + `filtered_reason: "duplicate"` |
| `seen_noted` | `status: seen` + `notes: <copy of prior notes or "legacy_seen_noted">` |
| `new` | `status: seen` (no scoring yet — Phase 1 rescores via lazy path) |
| `null` | **drop entry** (corruption) |

### Tier migration map (legacy → canonical)

| Legacy value | Canonical mapping |
|---|---|
| `A_upgraded` | `tier: A` + `notes: "legacy A_upgraded"` |
| `DEFERRED` | `tier: untiered` + `rubric_version: legacy` (forces rescore on first view) |
| `FILTERED` | `tier: D` + `tier_reason: "legacy filter"` |
| `untiered` (already), missing, `null` | `tier: untiered` |
| `A`, `B`, `C`, `D` | unchanged (also tagged `rubric_version: legacy`) |

### Lead tier migration map (legacy → canonical)

| Legacy value | Canonical mapping |
|---|---|
| `non-lead`, `non-lead (system promo)`, `non-lead-for-Tura`, `non-lead (side-gig, stale)` | `lead_tier: non-lead` + `lead_tier_detail: <legacy string>` |
| `warm-stale` | `lead_tier: warm` + `lead_tier_detail: "stale"` |
| `stale` | `lead_tier: cold` + `lead_tier_detail: "stale"` |
| `cold` | unchanged |
| `hot` (none observed but valid) | unchanged |

## Voice profile (tone block content)

The `tone` block populated by Task 16 carries this payload in both workspaces:

```json
{
  "register": "considered, restrained, dry-witted",
  "dialect": "british",
  "warmth": "personable but never sycophantic; gracious not effusive",
  "vocabulary_cues": [
    "organise", "programme", "behaviour", "favour",
    "happy to", "delighted to", "do let me know",
    "rather", "quite", "indeed",
    "have a think", "circle back", "in due course"
  ],
  "exemplars": [
    "Thank you for reaching out — the role sounds intriguing, and I'd be glad to learn more.",
    "Happy to share more detail once I've had a closer look at the JD.",
    "I'm afraid this one isn't quite a fit for me at the moment, but do keep me in mind for future briefs.",
    "Just circling back on this — let me know if it'd be useful to compare notes in the next week or so."
  ],
  "avoid": [
    "super excited",
    "I am writing to express my interest",
    "cheerio", "old chap",
    "American spellings (organize, color, etc.)",
    "exclamation points beyond one per message",
    "stacked buzzwords",
    "self-deprecation that undermines authority"
  ]
}
```

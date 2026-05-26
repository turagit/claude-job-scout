# Phase 5 (v0.8.0) — Foundations + Accuracy Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship v0.8.0 by (a) locking canonical schemas, migrating both live workspaces in place, enforcing previously silent contracts (JD blob persistence, score/CV caches, archive pass) and codifying the user's voice profile; then (b) replacing the keyword-bingo scoring rubric with a segment-aware, hard-gated, per-dimension-with-evidence rubric so A/B-tier false positives drop to near-zero.

**Architecture:** This plugin is a Claude Code plugin — the "code" is markdown skill files, markdown references, and per-project JSON state under `.job-scout/`. Validation is manual via shell (`jq`, `grep`, `wc`) and end-to-end runs against the user's live workspaces (CVDIRECTOR and CVFREELANCER). Browser work uses the Claude Chrome extension exclusively. State writes go through a single canonical-schema reference; a new `_gate-engine` runs before any scoring; the rewritten `_job-matcher` loads a segment-specific dimension set declared per workspace.

**Tech Stack:** Markdown (CommonMark) skill files, JSON state, `jq` for state manipulation, bash for verification, the existing `_visualizer` Jinja-shaped templates.

**Design spec:** [`docs/superpowers/specs/2026-05-26-phase-0-1-foundations-and-accuracy-design.md`](../specs/2026-05-26-phase-0-1-foundations-and-accuracy-design.md) — co-authored from the 2026-05-26 grilling session with the user. Decisions locked: hybrid dealbreaker elicitation, per-segment rubric dimensions, reject-with-reason feedback (Phase 6), British/sophisticated/charming voice everywhere user-voiced, migrate-in-place over nuke.

**Roadmap:** [`docs/ROADMAP.md`](../../ROADMAP.md) — this is Phase 5; Phases 6 (coverage + cadence), 7 (triage feedback + reject UX), 8 (recruiter reader + tone propagation), 9 (nurture) follow.

**Production host caution.** The user's memory flags this Mac as production. Every task that mutates state under `~/Library/Mobile Documents/com~apple~CloudDocs/CoWork/CVDIRECTOR/.job-scout/` or `.../CVFREELANCER/.job-scout/` MUST: (a) back up the affected file to `.job-scout/.backup/<filename>.<timestamp>.json` first, (b) write to a `.tmp` sibling then atomic-rename, (c) require explicit user approval before executing (do not run silently in subagent mode). Migration tasks 8–11 are gated by an approval step.

**Branching:** each task is one branch off `main` named `phase-5/task-NN-<short-slug>`. Controller merges directly to `main` after dual review (no PRs — `gh` CLI is unavailable in this environment).

**Merge order:** tasks are numbered to merge **serially**. Schema reference tasks (1–7) land before migration runs (8–11). Migration tasks land before persistence/cache wiring (12–15). Phase 0 verification (18) gates everything in Phase 1.

**Progress tracking:** after each task merges, tick the matching checkbox in `docs/ROADMAP.md`'s new Phase 5 section (added in Task 32).

**Canonical absolute paths used throughout this plan:**

- Repo: `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout`
- Live workspace A (director, perm): `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/CoWork/CVDIRECTOR`
- Live workspace B (freelance): `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/CoWork/CVFREELANCER`

The repo path contains spaces; **always quote it** in shell commands (`cd "/Users/tura/..."`).

---

# Phase 0 — Foundations (Tasks 1–18)

## Task 1: Design spec + plan stub

**Files:**
- Create: `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout/docs/superpowers/specs/2026-05-26-phase-0-1-foundations-and-accuracy-design.md`

- [ ] **Step 1: Create branch**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout" && git checkout main && git pull --rebase && git checkout -b phase-5/task-01-design-spec
```

- [ ] **Step 2: Write the design spec capturing the grilling-session outcome**

Create the file with exactly this content:

===FILE_START===
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
===FILE_END===

- [ ] **Step 3: Verify file exists and is valid markdown**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
wc -l docs/superpowers/specs/2026-05-26-phase-0-1-foundations-and-accuracy-design.md
grep -c "^## " docs/superpowers/specs/2026-05-26-phase-0-1-foundations-and-accuracy-design.md
```

Expected: file is 100–200 lines; section count ≥ 4.

- [ ] **Step 4: Commit**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
git add docs/superpowers/specs/2026-05-26-phase-0-1-foundations-and-accuracy-design.md
git commit -m "Phase 5 design spec — foundations + accuracy core"
git checkout main && git merge --no-ff phase-5/task-01-design-spec -m "Merge phase-5/task-01-design-spec"
```

---

## Task 2: Canonical schemas reference

**Files:**
- Create: `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout/skills/shared-references/canonical-schemas.md`

- [ ] **Step 1: Branch**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout" && git checkout main && git pull --rebase && git checkout -b phase-5/task-02-canonical-schemas
```

- [ ] **Step 2: Write the schemas reference**

Create the file. The full content lives in the design spec (Task 1); this file is the operational reference loaded by skills that write state. Use exactly this content (copy the canonical schemas + enum tables from the design spec):

===FILE_START===
# Canonical Schemas (locked v2)

> **Authoritative reference for `.job-scout/` state writes.** Any skill that writes to `user-profile.json`, `tracker.json`, or `recruiters/threads.json` MUST conform to these schemas. Validation rules live in `state-validators.md`.

This reference replaces the older inline schemas in `tracker-schema.md` and `_job-matcher/references/user-profile-schema.md`. Those files now point here.

## `user-profile.json`

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

## `tracker.json`

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

`jd_path` is a workspace-relative path to the full JD text under `.job-scout/jds/<job_id>.txt`. The inline `description` field used in v1 is removed — full JD text is hybrid-stored. See `jd-storage.md` (created in Task 5) for the contract.

## `recruiters/threads.json`

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

## Canonical enums (single source of truth)

| Field | Allowed values |
|---|---|
| `tracker.jobs.*.status` | `seen`, `approved`, `applied`, `rejected`, `skipped` |
| `tracker.jobs.*.tier` | `A`, `B`, `C`, `D`, `untiered` |
| `tracker.jobs.*.rubric_version` | `legacy`, `v1` |
| `tracker.jobs.*.source` | `Job Alert`, `Top Picks`, `Search`, `Inbox`, `Saved`, `Similar` |
| `threads.*.lead_tier` | `hot`, `warm`, `cold`, `non-lead` |
| `user-profile.requirements.deal_breakers[].kind` | `work_arrangement`, `contract_type`, `seniority_floor`, `location`, `industry`, `company`, `rate_floor`, `salary_floor`, `custom` |
| `user-profile.segment` | `director-perm`, `freelance` |

## Status transition rules

- `seen → approved → applied` (forward only)
- `seen → rejected` (forward only)
- `seen → skipped` (forward only — for explicit user "not now")
- Never downgrade. Never set a status field to a value outside the enum above.

## When to bump `schema_version`

Bump from 2 to 3 when a field is renamed, removed, or its type changes. Adding optional fields without a rename is a non-bumping change. A migration script must exist for every bump and live in the plan that introduced the change.
===FILE_END===

- [ ] **Step 3: Verify**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
wc -l skills/shared-references/canonical-schemas.md
grep -c "^## " skills/shared-references/canonical-schemas.md
```

Expected: ≥120 lines; ≥6 sections.

- [ ] **Step 4: Commit**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
git add skills/shared-references/canonical-schemas.md
git commit -m "Add canonical-schemas.md — locked v2 state contracts"
git checkout main && git merge --no-ff phase-5/task-02-canonical-schemas -m "Merge phase-5/task-02-canonical-schemas"
```

---

## Task 3: State validators reference

**Files:**
- Create: `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout/skills/shared-references/state-validators.md`

- [ ] **Step 1: Branch**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout" && git checkout main && git pull --rebase && git checkout -b phase-5/task-03-state-validators
```

- [ ] **Step 2: Write the validators reference**

Create the file with this exact content:

===FILE_START===
# State Validators

> **Mandatory pre-write check.** Every skill that writes to `.job-scout/` state files MUST run the validation routine in this reference before persisting. Enum violations are rejected; the write is aborted and the user is told which field failed.

## Why

Live state has historically drifted from spec because writes happened without enforcement. Director's tracker carries `tier: A_upgraded`, `tier: DEFERRED`, `tier: FILTERED`; Freelancer's tracker carries `status: seen_noted`, `status: seen_duplicate`. None of these are spec values; downstream consumers (`_visualizer`, `_job-matcher`) silently mis-handle them. Validators close that loop.

## Validation routine (every state write)

1. **Load the canonical enum table from `canonical-schemas.md`.**
2. **For every field listed in the enum table:** if the value being written is not in the allowed set, raise a `SCHEMA_VIOLATION` error and abort the write.
3. **Required fields:** verify every field marked required in `canonical-schemas.md` is present. Missing required fields raise `SCHEMA_VIOLATION`.
4. **Type checks:** strings stay strings, arrays stay arrays, numbers stay numbers, ISO8601 fields match `^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}Z?)?$`.
5. **Status transition check:** if updating an existing job, the new status must be a legal successor of the current status per `canonical-schemas.md` § Status transition rules.

## Standard validation procedure (operational)

Skills must implement this as a pre-write step. The exact mechanism in this codebase is a `jq` check followed by an atomic file-rename pattern.

### Validate a single tracker.json change before persisting

```bash
# Given $TRACKER (path to tracker.json) and $NEW (path to candidate new state)
# Returns 0 if valid, non-zero with stderr message if not.

validate_tracker() {
  local f="$1"

  # 1. Enum check — status
  local bad_status
  bad_status=$(jq -r '.jobs | to_entries | map(select(.value.status as $s |
    ["seen","approved","applied","rejected","skipped"] | index($s) | not)) |
    map(.key + ":" + (.value.status // "null")) | join(",")' "$f")
  if [ -n "$bad_status" ]; then
    echo "SCHEMA_VIOLATION: status $bad_status" >&2; return 2
  fi

  # 2. Enum check — tier
  local bad_tier
  bad_tier=$(jq -r '.jobs | to_entries | map(select(.value.tier as $t |
    ["A","B","C","D","untiered"] | index($t) | not)) |
    map(.key + ":" + (.value.tier // "null")) | join(",")' "$f")
  if [ -n "$bad_tier" ]; then
    echo "SCHEMA_VIOLATION: tier $bad_tier" >&2; return 2
  fi

  # 3. Enum check — rubric_version
  local bad_rv
  bad_rv=$(jq -r '.jobs | to_entries | map(select(.value.rubric_version as $r |
    ["legacy","v1"] | index($r) | not)) |
    map(.key + ":" + (.value.rubric_version // "null")) | join(",")' "$f")
  if [ -n "$bad_rv" ]; then
    echo "SCHEMA_VIOLATION: rubric_version $bad_rv" >&2; return 2
  fi

  # 4. schema_version present and == 2
  local sv
  sv=$(jq -r '.schema_version // "missing"' "$f")
  if [ "$sv" != "2" ]; then
    echo "SCHEMA_VIOLATION: schema_version is $sv, expected 2" >&2; return 2
  fi

  return 0
}
```

### Validate a user-profile.json change

```bash
validate_profile() {
  local f="$1"

  # segment must be one of two
  local seg
  seg=$(jq -r '.segment // "missing"' "$f")
  case "$seg" in
    director-perm|freelance) : ;;
    *) echo "SCHEMA_VIOLATION: segment is $seg" >&2; return 2 ;;
  esac

  # deal_breakers[].kind must be valid
  local bad_dk
  bad_dk=$(jq -r '.requirements.deal_breakers // [] | map(select(.kind as $k |
    ["work_arrangement","contract_type","seniority_floor","location","industry","company","rate_floor","salary_floor","custom"] | index($k) | not)) |
    map(.kind // "null") | join(",")' "$f")
  if [ -n "$bad_dk" ]; then
    echo "SCHEMA_VIOLATION: deal_breakers[].kind $bad_dk" >&2; return 2
  fi

  # tone block presence (warn-only — populated by Task 16)
  local tone_present
  tone_present=$(jq -r 'has("tone")' "$f")
  if [ "$tone_present" != "true" ]; then
    echo "WARN: tone block missing" >&2
  fi

  return 0
}
```

### Validate a threads.json change

```bash
validate_threads() {
  local f="$1"

  local bad_lt
  bad_lt=$(jq -r '.threads | to_entries | map(select(.value.lead_tier as $t |
    ["hot","warm","cold","non-lead"] | index($t) | not)) |
    map(.key + ":" + (.value.lead_tier // "null")) | join(",")' "$f")
  if [ -n "$bad_lt" ]; then
    echo "SCHEMA_VIOLATION: lead_tier $bad_lt" >&2; return 2
  fi

  return 0
}
```

## Atomic write pattern

Every state write follows this pattern:

```bash
write_state_file() {
  local target="$1"     # e.g. .job-scout/tracker.json
  local new_content="$2"   # path to candidate file
  local validator="$3"     # function name (validate_tracker etc.)

  # 1. Validate
  "$validator" "$new_content" || return $?

  # 2. Back up the current state
  local stamp; stamp=$(date -u +%Y%m%dT%H%M%SZ)
  local backup_dir
  backup_dir="$(dirname "$target")/.backup"
  mkdir -p "$backup_dir"
  if [ -f "$target" ]; then
    cp "$target" "$backup_dir/$(basename "$target").$stamp.json"
  fi

  # 3. Atomic rename
  mv "$new_content" "$target"
}
```

## When to skip validators

Never. The only exceptions are:

1. **Migration scripts** (Tasks 8–11 of this plan) — they convert non-canonical state TO canonical, so the input side is by definition non-canonical. They run the validator on the OUTPUT side only.
2. **Read-only reports** — no write, no validation. The validator is write-side only.

## Error surface

When a skill aborts a write due to `SCHEMA_VIOLATION`, it must:

1. Print the violating field and value to the user.
2. Leave the on-disk state unchanged (atomic-rename guarantees this).
3. Suggest the user file an issue with the offending payload, or — if the cause is obvious — fix the upstream skill that produced the bad payload.

Never silently fall back to a default value or "best effort" save.
===FILE_END===

- [ ] **Step 3: Verify**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
wc -l skills/shared-references/state-validators.md
bash -n <(grep -A40 'validate_tracker()' skills/shared-references/state-validators.md | sed '/^```/d')
```

Expected: ≥150 lines; bash syntax check passes.

- [ ] **Step 4: Commit**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
git add skills/shared-references/state-validators.md
git commit -m "Add state-validators.md — pre-write enum + transition checks"
git checkout main && git merge --no-ff phase-5/task-03-state-validators -m "Merge phase-5/task-03-state-validators"
```

---

## Task 4: JD storage reference

**Files:**
- Create: `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout/skills/shared-references/jd-storage.md`

- [ ] **Step 1: Branch**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout" && git checkout main && git pull --rebase && git checkout -b phase-5/task-04-jd-storage
```

- [ ] **Step 2: Write the JD storage reference**

Create the file with this exact content:

===FILE_START===
# JD Storage (hybrid)

> **The full JD text lives outside `tracker.json`.** Metadata stays in the tracker entry; the JD blob lives at `.job-scout/jds/<job_id>.txt`. The tracker entry's `jd_path` is the pointer.

## Why hybrid

`tracker.json` is read on every dedupe pass — every command that touches LinkedIn listings loads it. JD blobs are large (~3–8KB each). 770 jobs × 5KB = ~4MB of JD text loaded on every dedupe read if stored inline. Move blobs out: dedupe stays cheap, JD reads are lazy per-job.

The v1 contract (in the old `tracker-schema.md`) said "description is written once, by the first ingestion skill that fully extracts the job." Live state shows zero of 770 jobs have a description stored — the inline-write contract silently failed. The hybrid layout enforces the write because the absence of a sibling file is visible at a glance.

## File layout

```
.job-scout/
  jds/
    <job_id>.txt        # plain-text JD blob. UTF-8. Whatever LinkedIn rendered.
    <job_id>.meta.json  # optional companion: extracted-at, applicant-count snapshot, posting-date
```

## Write contract

Any ingestion skill that has the full JD in hand MUST write it before persisting the tracker entry:

```bash
write_jd() {
  local ws=".job-scout"   # workspace .job-scout/ root
  local jid="$1"          # job id
  local jd_text="$2"      # the full JD text

  mkdir -p "$ws/jds"
  printf '%s\n' "$jd_text" > "$ws/jds/$jid.txt.tmp"
  mv "$ws/jds/$jid.txt.tmp" "$ws/jds/$jid.txt"
  echo "jds/$jid.txt"   # caller writes this string to tracker.jobs[$jid].jd_path
}
```

The tracker entry must then have `jd_path: "jds/<job_id>.txt"` set in the same atomic write.

## Read contract

Skills that need the full JD (`/cover-letter`, `/interview-prep`, `_job-matcher` evidence-quote extraction) MUST:

1. Read `tracker.jobs[jid].jd_path`.
2. If non-null, read the file at `<workspace>/.job-scout/<jd_path>`.
3. If null (legacy entry), the skill must trigger fresh extraction via the Chrome extension and backfill — same as the v1 contract said for missing descriptions.

## Migration of existing entries

All 770 existing entries have `description: <empty or absent>`. They are tagged `jd_path: null` by the migration. On next interaction with each job, the consuming skill fetches the JD and backfills `jd_path`. There is no batch backfill — the cost is paid lazily on access.

## Retention

JDs are never deleted by the plugin. The user may prune `.job-scout/jds/` manually; the only consequence is that downstream commands re-extract on demand.
===FILE_END===

- [ ] **Step 3: Verify**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
wc -l skills/shared-references/jd-storage.md
grep -c "^## " skills/shared-references/jd-storage.md
```

Expected: ≥40 lines; ≥4 sections.

- [ ] **Step 4: Commit**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
git add skills/shared-references/jd-storage.md
git commit -m "Add jd-storage.md — hybrid JD blob layout"
git checkout main && git merge --no-ff phase-5/task-04-jd-storage -m "Merge phase-5/task-04-jd-storage"
```

---

## Task 5: Update workspace-layout.md

**Files:**
- Modify: `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout/skills/shared-references/workspace-layout.md`

- [ ] **Step 1: Branch**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout" && git checkout main && git pull --rebase && git checkout -b phase-5/task-05-workspace-layout
```

- [ ] **Step 2: Read the current file**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
cat skills/shared-references/workspace-layout.md
```

- [ ] **Step 3: Replace the "What goes inside" tree to add `jds/` and `.backup/`, and append a "Schema version" section**

Replace the existing `.job-scout/` layout block (whichever lines render the tree) with this new version. Add the schema-version section at the end of the file.

New tree:

```
.job-scout/
  schema-version         # plain text: "2"
  user-profile.json      # canonical v2 (see canonical-schemas.md)
  tracker.json           # canonical v2
  jds/                   # per-job JD blobs (see jd-storage.md)
    <job_id>.txt
  reports/               # rendered reports (snapshot + time-series; see render-orchestration.md)
  cache/
    cv-<hash>.json
    cv-analysis-<hash>.json
    scores.json
    linkedin-profile.json
    jd-keyword-corpus.json
  recruiters/
    threads.json         # canonical v2
  archive/
    tracker-YYYY.json    # rotated `seen` entries (60d)
  cover-letters/         # per-job generated cover letters
  .backup/               # atomic-write backups, retained ≥30 days
    <filename>.<ISO8601>.json
```

New trailing section to append:

===FILE_START===

## Schema version

`.job-scout/schema-version` is a one-line plain text file holding the current schema version (today: `2`). On every command's Step 0, the bootstrap routine reads this file:

- File missing or content not `2` → run the migration routine (see migration plans in `docs/superpowers/plans/`) before proceeding.
- File present and current → proceed.

Bump the schema-version when any canonical schema in `canonical-schemas.md` makes a backwards-incompatible change.
===FILE_END===

- [ ] **Step 4: Verify**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
grep -q "jds/" skills/shared-references/workspace-layout.md && grep -q ".backup/" skills/shared-references/workspace-layout.md && grep -q "schema-version" skills/shared-references/workspace-layout.md
echo $?
```

Expected: `0`.

- [ ] **Step 5: Commit**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
git add skills/shared-references/workspace-layout.md
git commit -m "Update workspace-layout.md — jds/, .backup/, schema-version"
git checkout main && git merge --no-ff phase-5/task-05-workspace-layout -m "Merge phase-5/task-05-workspace-layout"
```

---

## Task 6: Point old schema docs at the new canonical reference

**Files:**
- Modify: `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout/skills/shared-references/tracker-schema.md`
- Modify: `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout/skills/_job-matcher/references/user-profile-schema.md`

- [ ] **Step 1: Branch**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout" && git checkout main && git pull --rebase && git checkout -b phase-5/task-06-schema-pointers
```

- [ ] **Step 2: Replace `tracker-schema.md` content**

Overwrite the file with this content (keeps it short — operational rules only; canonical shape lives in `canonical-schemas.md`):

===FILE_START===
# `tracker.json` Operational Rules

> **Schema definition:** see [`canonical-schemas.md`](canonical-schemas.md). This file documents read/write rules, dedupe contract, and archival policy. The JSON shape is canonical and locked there.

The single source of truth for "have I seen this job before?". Lives at `.job-scout/tracker.json`. Every command that reads or scores jobs MUST consult this file *before* extracting job details — that is the primary token-saving mechanism in the plugin.

## Rules

- **Key by job id**, not URL — LinkedIn URLs sometimes carry tracking params. Strip to the canonical `/jobs/view/<id>/` form.
- **Dedupe before extraction.** When sweeping a listing page, collect every job id first, then drop any id already in `tracker.json`. Only open and extract details for the survivors.
- **`status` transitions are one-way** — see `canonical-schemas.md` § Status transition rules.
- **`last_seen` updates every time** the job appears in any sweep. `first_seen` never changes.
- **Score updates** are allowed if the user's CV or LinkedIn profile changed (either `cv_hash` or `profile_hash` bumped) OR if the job's `rubric_version` is `legacy` and the consumer is the lazy-rescore path. Otherwise leave the score alone.
- **Stats** must be incremented atomically with job state changes. `last_run` updates on every command invocation that touches the tracker.
- **Full JD text** is stored hybrid: see [`jd-storage.md`](jd-storage.md). The tracker entry carries `jd_path` only.
- **Writes use the atomic-rename pattern** in [`state-validators.md`](state-validators.md) with `validate_tracker` as the pre-write check.

## Read pattern (every command)

```
1. Load .job-scout/tracker.json (create empty canonical-v2 shell if missing).
2. Collect candidate job ids from the source (page scrape, alert, search result).
3. Filter: known_ids = ids ∩ tracker.jobs.keys()
4. new_ids = ids − known_ids
5. Process new_ids fully; for known_ids only update last_seen.
6. Persist tracker via the atomic-write pattern (validator first).
```

> If the workspace has archival active, step 1 also consults the current-year archive on a tracker miss. See **Archival policy** below.

## Write pattern

Always merge — never overwrite the whole file. If two commands run concurrently, the second should re-read before writing to avoid stomping the first's updates. All writes go through `validate_tracker` per `state-validators.md`.

## Archival policy

`tracker.json` grows monotonically and — over years of use — would become expensive to read on every dedupe pass. Aged `status: seen` entries rotate to annual archive files.

### Rules

- **Eligible for archive:** `status == "seen"` AND `last_seen` older than 60 days.
- **Not archived:** `approved`, `applied`, `rejected`, `skipped`. These all represent user intent. They stay in hot `tracker.json` indefinitely. Only pure `seen` entries are eligible.
- **Archive destination:** `.job-scout/archive/tracker-YYYY.json`, keyed by the year the job was `first_seen`.
- **Archive shape:** same as `tracker.json` canonical v2 — `{ "schema_version": 2, "version": 2, "jobs": { ... } }`. No `stats` block; archive files are append-only.

### When to run

Run the archive pass at most once per calendar day per workspace. Gate via `stats.last_archive_pass` in `tracker.json` (stored as `"YYYY-MM-DD"` — date only): if today's date equals the stored date, skip. Otherwise run the pass and update the field.

### Dedupe read pattern after archival

```
1. Load .job-scout/tracker.json — primary dedupe set.
2. If an id is not in hot tracker, fall through to .job-scout/archive/tracker-<current-year>.json.
3. Do NOT read older archive files during the hot path — they exist for /funnel-report and manual inspection.
```
===FILE_END===

- [ ] **Step 3: Replace `_job-matcher/references/user-profile-schema.md`**

Overwrite the file with this content:

===FILE_START===
# User Profile (per-workspace)

> **Schema definition:** see [`../../shared-references/canonical-schemas.md`](../../shared-references/canonical-schemas.md). The JSON shape lives there and is locked.

This file documents read/write access and operational rules. Every workspace has its own `user-profile.json` at the root of `.job-scout/`.

## Rules

1. **Read first, ask second.** Check the profile before asking for info it might contain.
2. **Merge, don't overwrite.** Update fields without replacing the file. Writes go through `validate_profile` (see `state-validators.md`).
3. **Create if missing.** On first bootstrap, write a canonical v2 stub via `/analyze-cv`.
4. **Confirm with user.** "Using saved preferences (remote, freelance, Director). Want to change?"
5. **Stale check.** If `last_updated` >30 days, suggest re-running `/analyze-cv`.
6. **Segment is required.** The matcher uses it to load the right dimension set. `/analyze-cv` declares it at init time and writes it.

## Command access

| Command | Reads | Writes |
|---|---|---|
| `/analyze-cv` | All | cv_path, cv_summary, cv_hash, target_titles, segment, tone, requirements.deal_breakers, discovery_complete |
| `/check-job-notifications` | All | last_updated (if missing fields filled) |
| `/job-search` | requirements, target_titles, segment | requirements (fills gaps) |
| `/match-jobs` | All | — |
| `/apply` | cv_path, requirements | — |
| `/check-inbox` | tone, cv_summary, requirements | — |
| `/optimize-profile` | cv_path, cv_summary, tone | linkedin_profile_url, profile_hash |
| `/create-alerts` | requirements, target_titles | — |
| `/cover-letter` | All (esp. tone, cv_summary) | — |
| `/interview-prep` | All | — |
===FILE_END===

- [ ] **Step 4: Verify**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
grep -q "canonical-schemas.md" skills/shared-references/tracker-schema.md
grep -q "canonical-schemas.md" skills/_job-matcher/references/user-profile-schema.md
grep -q "segment" skills/_job-matcher/references/user-profile-schema.md
```

Expected: all three checks return 0.

- [ ] **Step 5: Commit**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
git add skills/shared-references/tracker-schema.md skills/_job-matcher/references/user-profile-schema.md
git commit -m "Point old schema docs at canonical-schemas.md"
git checkout main && git merge --no-ff phase-5/task-06-schema-pointers -m "Merge phase-5/task-06-schema-pointers"
```

---

## Task 7: Voice profile reference

**Files:**
- Create: `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout/skills/shared-references/voice-profile.md`

- [ ] **Step 1: Branch**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout" && git checkout main && git pull --rebase && git checkout -b phase-5/task-07-voice-profile
```

- [ ] **Step 2: Write the reference**

Create the file:

===FILE_START===
# Voice Profile

> **Single source of truth for the user's voice across every user-voiced draft.** The `tone` block in each workspace's `user-profile.json` carries the operational payload; this file explains what consumers do with it.

## Why this exists

Before this phase, `response-templates.md` carried structural instructions ("Thank them, ask qualifying questions") but no voice. Generic templates produce flat copy. The user's stated voice — **British, sophisticated, charming, classy (not over the top), likable, friendly, positive** — is now codified as data in `user-profile.json.tone`, consumed by every skill that drafts text in the user's name.

## Tone block shape

See [`canonical-schemas.md`](canonical-schemas.md) for the JSON shape. Fields:

| Field | Purpose |
|---|---|
| `register` | High-level descriptor of the formality and pacing. "considered, restrained, dry-witted". |
| `dialect` | `british` for this user — controls spelling (organise, programme), idiom, rhythm. |
| `warmth` | Where on the cold↔effusive axis to sit. "personable but never sycophantic; gracious not effusive". |
| `vocabulary_cues` | Concrete words and turns of phrase to favour — used as prompt anchors. |
| `exemplars` | Two to six full-sentence samples in the voice. Used as few-shot anchors at draft time. |
| `avoid` | Negative examples — phrases, registers, or spellings that break the voice. |

## Consumer skills (must read tone block at draft time)

- `_recruiter-engagement` — recruiter replies, follow-ups, warm-stale revivals.
- `_cover-letter-writer` — every cover letter.
- `_profile-optimizer` — LinkedIn About, Headline, Experience bullets.
- `_cv-optimizer` / `_cv-section-rewriter` — every bullet rewrite.
- `interview-prep` (orchestrator) — SPAR narratives, "questions to ask" lists.
- Any future user-voiced surface.

## Read pattern

```
1. Load .job-scout/user-profile.json.
2. Extract the `tone` block. If absent, fall back to a hard-coded neutral profile and warn.
3. Pass the tone block into the LLM prompt as a system-level constraint, with `vocabulary_cues` and `exemplars` as few-shot anchors and `avoid` as explicit negatives.
```

## Write pattern

The tone block is set once at `/analyze-cv` time and rarely changes. Updates go through `validate_profile`. A `/config tone` command (not in Phase 5; Phase 8 candidate) will let the user revise.

## Operational examples

A recruiter reply drafter should, at draft time, prepend to the LLM prompt:

```
You are drafting a reply on behalf of the user. The user's voice is:
- Register: {{tone.register}}
- Dialect: {{tone.dialect}}
- Warmth: {{tone.warmth}}
- Favour these words and phrasings: {{tone.vocabulary_cues | join: ", "}}
- Avoid: {{tone.avoid | join: ", "}}

Examples in the user's voice:
{% for ex in tone.exemplars %}
- "{{ex}}"
{% endfor %}

Draft the reply in this voice.
```

## Cross-workspace policy

Both workspaces carry the same tone block by default (the user's voice doesn't change between CVDIRECTOR and CVFREELANCER). Override per workspace is possible — just edit `user-profile.json.tone` in that workspace. The migration in Task 16 writes the same payload to both.
===FILE_END===

- [ ] **Step 3: Verify**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
wc -l skills/shared-references/voice-profile.md
grep -c "^## " skills/shared-references/voice-profile.md
```

Expected: ≥60 lines; ≥6 sections.

- [ ] **Step 4: Commit**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
git add skills/shared-references/voice-profile.md
git commit -m "Add voice-profile.md — tone-block consumer contract"
git checkout main && git merge --no-ff phase-5/task-07-voice-profile -m "Merge phase-5/task-07-voice-profile"
```

---

## Task 8: Backup live workspaces (mandatory pre-migration)

**This task touches live state.** Confirm with the user before executing.

**Files:**
- Create: `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/CoWork/CVDIRECTOR/.job-scout/.backup/<timestamped>.tar`
- Create: `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/CoWork/CVFREELANCER/.job-scout/.backup/<timestamped>.tar`

- [ ] **Step 1: Ask for explicit user approval before running**

Tell the user: "About to back up both live `.job-scout/` workspaces to `.backup/` subdirs. This is read-only on existing state. Proceed?"

Wait for affirmative confirmation.

- [ ] **Step 2: Create timestamped tarballs of both workspaces**

```bash
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
for ws in CVDIRECTOR CVFREELANCER; do
  D="/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/CoWork/$ws/.job-scout"
  if [ -d "$D" ]; then
    mkdir -p "$D/.backup"
    ( cd "$D/.." && tar -cf "$D/.backup/pre-phase-5.$STAMP.tar" \
        --exclude='.job-scout/.backup' .job-scout )
  fi
done
```

- [ ] **Step 3: Verify backups exist and are non-empty**

```bash
for ws in CVDIRECTOR CVFREELANCER; do
  D="/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/CoWork/$ws/.job-scout/.backup"
  echo "=== $ws ==="
  ls -la "$D"/pre-phase-5.*.tar 2>/dev/null
done
```

Expected: one `.tar` per workspace, size ≥ a few hundred KB.

- [ ] **Step 4: Optional — verify tar contents**

```bash
WS="/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/CoWork/CVDIRECTOR/.job-scout/.backup"
tar -tf "$WS"/pre-phase-5.*.tar | head -20
```

Expected: lists `.job-scout/tracker.json`, `.job-scout/user-profile.json`, `.job-scout/reports/...`, `.job-scout/recruiters/...`.

- [ ] **Step 5: No commit — this task touches user state outside the repo. Note completion in chat.**

---

## Task 9: Migrate tracker.json (both workspaces)

**This task mutates live state.** Confirm with the user. Backups from Task 8 must exist.

**Files:**
- Modify: `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/CoWork/CVDIRECTOR/.job-scout/tracker.json`
- Modify: `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/CoWork/CVFREELANCER/.job-scout/tracker.json`
- Modify: `.job-scout/schema-version` in both workspaces

- [ ] **Step 1: Ask for explicit user approval before running.**

Tell the user: "About to migrate both `tracker.json` files in place. Backups exist at `.backup/`. The migration will: normalise statuses (5 canonical values), normalise tiers (5 canonical values), backfill missing `first_seen` from `last_seen`, drop corrupt entries (status:null or version:null), tag every entry `rubric_version: legacy`, remove the inline `description` field (move to lazy `jd_path: null`), bump `schema_version` to 2. Proceed?"

Wait for affirmative confirmation.

- [ ] **Step 2: Run the migration script for both workspaces**

```bash
migrate_tracker() {
  local D="$1"  # workspace root, e.g. /.../CVDIRECTOR/.job-scout
  local IN="$D/tracker.json"
  local TMP="$D/tracker.json.tmp"

  jq '
    # 1. drop corrupt entries
    .jobs |= with_entries(select(
      (.value.status != null) and
      (.value.id // .key | tostring | length > 0)
    ))
    |
    # 2. normalise status
    .jobs |= with_entries(
      .value.status |=
        if . == "filtered_out" then "seen"
        elif . == "seen_filtered_out" then "seen"
        elif . == "seen_duplicate" then "skipped"
        elif . == "seen_noted" then "seen"
        elif . == "new" then "seen"
        elif . == null then "seen"
        else . end
    )
    |
    # 3. tag filtered_reason for entries that were "filtered_out" or similar
    .jobs |= with_entries(
      .value.filtered_reason //= (
        if (.value | has("filtered_reason")) then .value.filtered_reason
        else null end
      )
    )
    |
    # 4. normalise tier
    .jobs |= with_entries(
      .value.tier |=
        if . == "A_upgraded" then "A"
        elif . == "DEFERRED" then "untiered"
        elif . == "FILTERED" then "D"
        elif . == null then "untiered"
        elif (["A","B","C","D","untiered"] | index(.)) then .
        else "untiered" end
    )
    |
    # 5. add tier_reason for legacy filters
    .jobs |= with_entries(
      .value.tier_reason //=
        (if .value.tier == "D" and ((.value.notes // "") | contains("FILTERED"))
         then "legacy filter" else null end)
    )
    |
    # 6. backfill first_seen from last_seen where null
    .jobs |= with_entries(
      .value.first_seen //= (.value.last_seen // "1970-01-01")
    )
    |
    # 7. ensure required fields exist with defaults
    .jobs |= with_entries(
      .value.rubric_version //= "legacy"
      | .value.dimensions //= {}
      | .value.gate_violations //= []
      | .value.jd_path //= null
      | .value.notes //= ""
      | .value.source //= "Search"
      | .value.score //= null
      | .value.url //= ""
      | .value.title //= ""
      | .value.company //= ""
      | .value.id //= .key
      | .value.reject_reason //= null
      | .value.rejected_at //= null
      | .value.approved_at //= null
      | .value.applied_at //= null
      | .value.filtered_reason //= null
    )
    |
    # 8. drop legacy `description` field
    .jobs |= with_entries(.value |= del(.description))
    |
    # 9. normalise stats block — keep only canonical keys
    .stats = {
      total_seen: ([.jobs[] | select(.status == "seen")] | length),
      applied:    ([.jobs[] | select(.status == "applied")] | length),
      rejected:   ([.jobs[] | select(.status == "rejected")] | length),
      last_run:   (.stats.last_run // .stats.last_search // null),
      last_search: (.stats.last_search // null),
      last_archive_pass: (.stats.last_archive_pass // null)
    }
    |
    # 10. bump schema_version + version
    .schema_version = 2
    | .version = 2
  ' "$IN" > "$TMP"

  # 11. Validate the output before swapping
  if ! python3 -c "import json, sys; json.load(open('$TMP'))" 2>/dev/null; then
    echo "MIGRATION FAILED: output is not valid JSON" >&2; return 2
  fi

  mv "$TMP" "$IN"
  echo "2" > "$D/schema-version"
}

for ws in CVDIRECTOR CVFREELANCER; do
  D="/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/CoWork/$ws/.job-scout"
  if [ -f "$D/tracker.json" ]; then
    echo "=== migrating $ws/tracker.json ==="
    migrate_tracker "$D"
  fi
done
```

- [ ] **Step 3: Verify canonical shape post-migration**

```bash
for ws in CVDIRECTOR CVFREELANCER; do
  D="/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/CoWork/$ws/.job-scout"
  echo "=== $ws ==="
  jq '{schema_version, version, job_count: (.jobs | length),
        status_breakdown: (.jobs | map(.status) | group_by(.) | map({k: .[0], n: length})),
        tier_breakdown:   (.jobs | map(.tier)   | group_by(.) | map({k: .[0], n: length})),
        rubric_versions:  (.jobs | map(.rubric_version) | group_by(.) | map({k: .[0], n: length})),
        any_null_first_seen: ([.jobs[] | select(.first_seen == null)] | length),
        any_description_field: ([.jobs[] | select(has("description"))] | length),
        stats_keys: (.stats | keys)}' "$D/tracker.json"
done
```

Expected:
- `schema_version == 2`, `version == 2`
- `status_breakdown` shows only values in `{seen, approved, applied, rejected, skipped}`
- `tier_breakdown` shows only values in `{A, B, C, D, untiered}`
- `rubric_versions` shows every entry as `legacy`
- `any_null_first_seen == 0`
- `any_description_field == 0`
- `stats_keys` is exactly `["applied","last_archive_pass","last_run","last_search","rejected","total_seen"]`

- [ ] **Step 4: Run the validator from `state-validators.md` against both files**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
# Source the validators
source <(grep -A100 'validate_tracker()' skills/shared-references/state-validators.md | sed -n '/^```bash$/,/^```$/{//d;p;}' | head -40)

for ws in CVDIRECTOR CVFREELANCER; do
  D="/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/CoWork/$ws/.job-scout"
  echo "=== validate $ws ==="
  validate_tracker "$D/tracker.json" && echo "OK"
done
```

Expected: both print `OK`. Any `SCHEMA_VIOLATION` fails the task.

- [ ] **Step 5: Note completion in chat. No repo commit (state is outside the repo).**

---

## Task 10: Migrate user-profile.json (both workspaces)

**This task mutates live state.** Confirm with the user.

**Files:**
- Modify: `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/CoWork/CVDIRECTOR/.job-scout/user-profile.json`
- Modify: `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/CoWork/CVFREELANCER/.job-scout/user-profile.json`

- [ ] **Step 1: Ask for explicit user approval.**

Tell the user: "About to migrate both `user-profile.json` files. CVDIRECTOR currently has cv_summary as a string; will preserve as `cv_summary_text` and add the canonical structured `cv_summary` shape (filled by next /analyze-cv). CVFREELANCER has the right shape; will normalise field names and add empty `deal_breakers`, `companies_to_avoid`, `industries_to_avoid`, `companies_to_target`. Both will gain `segment` (set per workspace), empty `tone` (filled in Task 16), and bumped `schema_version: 2`. Proceed?"

Wait for affirmative confirmation.

- [ ] **Step 2: Run the migration**

```bash
migrate_profile() {
  local D="$1"
  local SEGMENT="$2"     # "director-perm" or "freelance"
  local IN="$D/user-profile.json"
  local TMP="$D/user-profile.json.tmp"

  jq --arg segment "$SEGMENT" '
    # Preserve any free-text cv_summary (CVDIRECTOR has this)
    (if (.cv_summary | type) == "string"
     then .cv_summary_text = .cv_summary
          | .cv_summary = {
              key_skills: [],
              technologies: [],
              seniority: "",
              years_experience: 0,
              target_roles: (.target_titles // []),
              domain_expertise: [],
              industries: []
            }
     else . end)
    |
    # Ensure top-level fields
    .schema_version = 2
    | .segment = $segment
    | .target_titles //= []
    | .preferred_length_pages //= null
    | .linkedin_profile_url //= null
    | .profile_hash //= null
    | .discovery_complete //= false
    | .master_keyword_list //= []
    | .cv_hash //= null
    | .cv_filename_on_linkedin //= null
    | .cv_uploaded_to_linkedin_at //= null
    | .last_updated //= (now | strftime("%Y-%m-%dT%H:%M:%SZ"))
    | .created_by //= "migration-phase-5"
    |
    # Normalise requirements
    .requirements = (
      (.requirements // {}) as $r |
      {
        work_arrangement: (
          if ($r.work_arrangement | type) == "array" then $r.work_arrangement
          elif ($r.work_arrangement | type) == "string" then [$r.work_arrangement]
          else [] end
        ),
        contract_type: (
          if ($r.contract_type | type) == "array" then $r.contract_type
          elif ($r.contract_type | type) == "string" then [$r.contract_type]
          else [] end
        ),
        location_preferences: (
          $r.location_preferences //
          $r.preferred_locations //
          (if ($r.location | type) == "string" then [$r.location] else [] end)
        ),
        seniority_floor: ($r.seniority_floor // null),
        min_day_rate: ($r.min_day_rate // $r.preferred_rate // null),
        ideal_day_rate: ($r.ideal_day_rate // null),
        rate_currency: ($r.rate_currency // null),
        salary_floor: ($r.salary_floor // null),
        salary_currency: ($r.salary_currency // null),
        deal_breakers: ($r.deal_breakers // []),
        nice_to_haves: ($r.nice_to_haves // []),
        companies_to_avoid: ($r.companies_to_avoid // []),
        industries_to_avoid: ($r.industries_to_avoid // []),
        companies_to_target: ($r.companies_to_target // [])
      }
    )
    |
    # Empty tone block (filled in Task 16)
    .tone //= {
      register: "",
      dialect: "",
      warmth: "",
      vocabulary_cues: [],
      exemplars: [],
      avoid: []
    }
  ' "$IN" > "$TMP"

  if ! python3 -c "import json, sys; json.load(open('$TMP'))" 2>/dev/null; then
    echo "MIGRATION FAILED: output is not valid JSON" >&2; return 2
  fi

  mv "$TMP" "$IN"
}

migrate_profile "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/CoWork/CVDIRECTOR/.job-scout" "director-perm"
migrate_profile "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/CoWork/CVFREELANCER/.job-scout" "freelance"
```

- [ ] **Step 3: Verify**

```bash
for ws in CVDIRECTOR CVFREELANCER; do
  D="/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/CoWork/$ws/.job-scout"
  echo "=== $ws ==="
  jq '{schema_version, segment, has_tone: (.tone != null),
        requirements_keys: (.requirements | keys),
        cv_summary_type: (.cv_summary | type),
        has_cv_summary_text: (has("cv_summary_text"))}' "$D/user-profile.json"
done
```

Expected:
- `schema_version == 2` in both
- `segment == "director-perm"` for CVDIRECTOR, `"freelance"` for CVFREELANCER
- `has_tone == true` in both (empty payload — Task 16 fills it)
- `requirements_keys` contains: `companies_to_avoid, companies_to_target, contract_type, deal_breakers, ideal_day_rate, industries_to_avoid, location_preferences, min_day_rate, nice_to_haves, rate_currency, salary_currency, salary_floor, seniority_floor, work_arrangement`
- `cv_summary_type == "object"` in both (CVDIRECTOR also has `cv_summary_text`)

- [ ] **Step 4: Run `validate_profile` on both files**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
source <(grep -A30 'validate_profile()' skills/shared-references/state-validators.md | sed -n '/^```bash$/,/^```$/{//d;p;}' | head -30)

for ws in CVDIRECTOR CVFREELANCER; do
  D="/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/CoWork/$ws/.job-scout"
  echo "=== $ws ==="
  validate_profile "$D/user-profile.json" && echo "OK"
done
```

Expected: both print `OK` (plus a `WARN: tone block missing` is acceptable here — Task 16 fixes it).

- [ ] **Step 5: Note completion in chat. No repo commit.**

---

## Task 11: Migrate recruiters/threads.json (CVDIRECTOR only — CVFREELANCER is empty)

**This task mutates live state.** Confirm with the user.

**Files:**
- Modify: `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/CoWork/CVDIRECTOR/.job-scout/recruiters/threads.json`
- Create: `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/CoWork/CVFREELANCER/.job-scout/recruiters/threads.json` (empty canonical shell)

- [ ] **Step 1: Approval gate**

Tell the user: "About to migrate `threads.json` in CVDIRECTOR (26 threads, non-canonical schema). Will normalise `lead_tier` to {hot, warm, cold, non-lead}, move legacy labels to `lead_tier_detail`, rename `participant` → `recruiter_name`, add missing spec fields (last_seen_msg_id, last_drafted_reply, last_updated, notes[]). For CVFREELANCER, create an empty canonical shell. Proceed?"

Wait for confirmation.

- [ ] **Step 2: Run the migration**

```bash
migrate_threads() {
  local D="$1"
  local IN="$D/recruiters/threads.json"
  local TMP="$D/recruiters/threads.json.tmp"

  if [ ! -f "$IN" ]; then
    # Create empty canonical shell
    mkdir -p "$D/recruiters"
    cat > "$IN" <<'JSON'
{
  "schema_version": 2,
  "last_scanned": null,
  "scan_source": "",
  "stats": {"total_threads_scanned": 0, "hot": 0, "warm": 0, "cold": 0, "non_lead": 0},
  "threads": {}
}
JSON
    return 0
  fi

  jq '
    .schema_version = 2
    |
    # Normalise top-level: spec calls for `threads` map, current file already has it
    .threads |= with_entries(
      .value |= (
        # rename participant -> recruiter_name
        .recruiter_name = (.participant // .recruiter_name // "")
        |
        # normalise lead_tier
        (.lead_tier // "non-lead") as $lt |
        .lead_tier =
          (if $lt | tostring | test("^hot") then "hot"
           elif $lt | tostring | test("warm") then "warm"
           elif $lt | tostring | test("cold") then "cold"
           elif $lt | tostring | test("stale$") then "cold"
           else "non-lead" end)
        |
        # lead_tier_detail captures the original label
        .lead_tier_detail =
          (if ($lt | tostring) == .lead_tier then null else ($lt | tostring) end)
        |
        # ensure spec fields exist
        .last_seen_msg_id //= null
        | .last_drafted_reply //= null
        | .last_updated //= null
        | .last_message_date //= (.last_message_date // null)
        | .thread_url_path //= null
        | .linked_job_ids //= []
        | .notes //= []
        | .participant_title //= null
        | .company //= null
      )
    )
    |
    # Recompute stats
    .stats = {
      total_threads_scanned: (.threads | length),
      hot:      ([.threads[] | select(.lead_tier == "hot")] | length),
      warm:     ([.threads[] | select(.lead_tier == "warm")] | length),
      cold:     ([.threads[] | select(.lead_tier == "cold")] | length),
      non_lead: ([.threads[] | select(.lead_tier == "non-lead")] | length)
    }
  ' "$IN" > "$TMP"

  if ! python3 -c "import json, sys; json.load(open('$TMP'))" 2>/dev/null; then
    echo "MIGRATION FAILED: output is not valid JSON" >&2; return 2
  fi
  mv "$TMP" "$IN"
}

migrate_threads "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/CoWork/CVDIRECTOR/.job-scout"
migrate_threads "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/CoWork/CVFREELANCER/.job-scout"
```

- [ ] **Step 3: Verify**

```bash
for ws in CVDIRECTOR CVFREELANCER; do
  D="/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/CoWork/$ws/.job-scout"
  echo "=== $ws ==="
  jq '{schema_version, thread_count: (.threads | length),
        stats,
        lead_tier_breakdown: (.threads | to_entries | map(.value.lead_tier) | group_by(.) | map({k: .[0], n: length})),
        any_legacy_lead_tier: ([.threads | to_entries[] | select(.value.lead_tier | (. == "hot" or . == "warm" or . == "cold" or . == "non-lead") | not)] | length)}' "$D/recruiters/threads.json"
done
```

Expected:
- CVDIRECTOR: `schema_version == 2`, `thread_count == 26` (or close — minus dropped if any), `lead_tier_breakdown` only `{hot, warm, cold, non-lead}`, `any_legacy_lead_tier == 0`
- CVFREELANCER: `schema_version == 2`, `thread_count == 0`

- [ ] **Step 4: Run `validate_threads`**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
source <(grep -A20 'validate_threads()' skills/shared-references/state-validators.md | sed -n '/^```bash$/,/^```$/{//d;p;}' | head -20)
for ws in CVDIRECTOR CVFREELANCER; do
  D="/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/CoWork/$ws/.job-scout"
  validate_threads "$D/recruiters/threads.json" && echo "OK: $ws"
done
```

Expected: both print `OK`.

- [ ] **Step 5: Note completion. No repo commit.**

---

## Task 12: Wire JD blob persistence

**Files:**
- Modify: `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout/skills/check-job-notifications/SKILL.md`
- Modify: `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout/skills/job-search/SKILL.md`
- Modify: `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout/skills/match-jobs/SKILL.md` (if it extracts JDs — check first)

- [ ] **Step 1: Branch**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout" && git checkout main && git pull --rebase && git checkout -b phase-5/task-12-jd-persistence
```

- [ ] **Step 2: Modify `skills/check-job-notifications/SKILL.md` Step 4**

Find the section that begins `## Step 4: Extract details for new jobs only`. Replace it with this exact content:

===FILE_START===
## Step 4: Extract details for new jobs only

For each *new* job: open it and extract title, company, location (remote/hybrid/on-site + city), salary/rate, contract type, experience level, required skills, preferred skills, full description text, Easy Apply status, posting date, applicant count, job URL.

**JD persistence (required).** Immediately after extracting a job's full description text, persist it via the hybrid-storage contract in `../shared-references/jd-storage.md`:

```bash
# pseudocode — agents execute the equivalent via Bash:
mkdir -p .job-scout/jds
printf '%s\n' "$JD_TEXT" > ".job-scout/jds/$JOB_ID.txt.tmp"
mv ".job-scout/jds/$JOB_ID.txt.tmp" ".job-scout/jds/$JOB_ID.txt"
```

Set `jd_path: "jds/<job_id>.txt"` on the tracker entry in the same atomic write. Skills that need the full JD downstream (`/cover-letter`, `/interview-prep`, the evidence-quote step in `_job-matcher`) read it from this path.

**Corpus enrichment:** after extraction, run the JD keyword extraction procedure from `../shared-references/jd-keyword-extraction.md` on each new job's description. Merges keywords into `.job-scout/cache/jd-keyword-corpus.json`.
===FILE_END===

- [ ] **Step 3: Modify `skills/job-search/SKILL.md` Step 3**

Find the line `Only extract details for new jobs: title, company, location, salary, requirements, description, Easy Apply status.` Replace it with:

===FILE_START===
Only extract details for new jobs: title, company, location, salary, requirements, description, Easy Apply status. After extraction, persist the full JD per the hybrid-storage contract in `../shared-references/jd-storage.md` — write to `.job-scout/jds/<job_id>.txt`, set `jd_path` on the tracker entry. Skip inline `description` writes; the field is removed from the canonical v2 schema.
===FILE_END===

- [ ] **Step 4: Check whether `match-jobs/SKILL.md` extracts JDs**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
grep -ln "extract" skills/match-jobs/SKILL.md
grep -A3 "description" skills/match-jobs/SKILL.md
```

If `match-jobs` only scores jobs already in the tracker (most likely), no change needed. If it extracts on demand, apply the same JD-persistence directive as in Step 2.

- [ ] **Step 5: Verify references compile**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
grep -q "jd-storage.md" skills/check-job-notifications/SKILL.md
grep -q "jd-storage.md" skills/job-search/SKILL.md
grep -q "jd_path" skills/check-job-notifications/SKILL.md
grep -q "jd_path" skills/job-search/SKILL.md
```

Expected: all four checks return 0.

- [ ] **Step 6: Commit**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
git add skills/check-job-notifications/SKILL.md skills/job-search/SKILL.md skills/match-jobs/SKILL.md
git commit -m "Wire JD blob persistence into ingestion skills (hybrid storage)"
git checkout main && git merge --no-ff phase-5/task-12-jd-persistence -m "Merge phase-5/task-12-jd-persistence"
```

---

## Task 13: Wire score cache contract enforcement

**Files:**
- Modify: `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout/skills/_job-matcher/SKILL.md` (Score Caching Contract section)

- [ ] **Step 1: Branch**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout" && git checkout main && git pull --rebase && git checkout -b phase-5/task-13-score-cache
```

- [ ] **Step 2: Read the current Score Caching Contract section**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
awk '/^## Score Caching Contract/,/^## /' skills/_job-matcher/SKILL.md
```

- [ ] **Step 3: Replace the whole "Score Caching Contract" section with this**

===FILE_START===
## Score Caching Contract

Job scores are cached in `.job-scout/cache/scores.json` keyed by `(job_id, cv_hash, profile_hash, rubric_version)`. The fourth key element — `rubric_version` — is added in v0.8.0 so that rubric upgrades invalidate stale entries without an explicit migration.

### Read path

```
1. Load .job-scout/user-profile.json — read cv_hash, profile_hash, segment.
2. Determine current rubric_version (today: "v1").
3. Compute cache key = "<job_id>:<cv_hash>:<profile_hash>:v1".
4. If cache/scores.json has this key → reuse the cached score, tier, dimensions, gate_violations. Skip LLM call.
5. Otherwise → run the rubric (per Step "Matching framework" below), write the result to the cache, then return it.
```

### Write path

After computing a score, append/replace the entry in `cache/scores.json`:

```json
{
  "<key>": {
    "score": <number>,
    "tier": "A|B|C|D",
    "dimensions": { "<dim>": {"tier": "A|B|C|D", "evidence": [...] } },
    "gate_violations": [...],
    "rubric_version": "v1",
    "scored_at": "ISO8601"
  }
}
```

Writes go through the atomic-rename pattern in `../shared-references/state-validators.md`.

### Invalidation

The cache is invalidated automatically by any of:

- `cv_hash` change (CV file modified) → entries for the old hash are stale, ignored, and pruned weekly.
- `profile_hash` change (LinkedIn profile re-optimised) → same.
- `rubric_version` bump → entries for older rubric versions are stale.
- `requirements.deal_breakers` change → cached `gate_violations` may be wrong. To force re-evaluation, the consumer skill bumps a `dealbreakers_hash` in the cache key when reading. **For v0.8.0, simplify: any change to `requirements` updates `profile_hash` (`/analyze-cv` ensures this), so the cv-and-profile composite key is sufficient.**

### Empty-cache reality

Both live workspaces have empty `cache/` directories today. The first run post-migration populates the cache fresh. There is no batch backfill — costs are paid lazily.

### File-size discipline

`scores.json` can grow large. After 5000 entries, prune entries older than 90 days OR with stale `cv_hash`/`profile_hash`/`rubric_version`. Today (770 jobs) we are far from this limit.
===FILE_END===

- [ ] **Step 4: Verify**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
grep -q "rubric_version" skills/_job-matcher/SKILL.md
grep -q "cache/scores.json" skills/_job-matcher/SKILL.md
grep -q "Atomic-rename" skills/shared-references/state-validators.md || grep -q "atomic-rename" skills/shared-references/state-validators.md
```

Expected: all three pass.

- [ ] **Step 5: Commit**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
git add skills/_job-matcher/SKILL.md
git commit -m "Update score-cache contract: add rubric_version key element"
git checkout main && git merge --no-ff phase-5/task-13-score-cache -m "Merge phase-5/task-13-score-cache"
```

---

## Task 14: Wire CV parse cache contract enforcement

**Files:**
- Modify: `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout/skills/shared-references/cv-loading.md`

- [ ] **Step 1: Branch**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout" && git checkout main && git pull --rebase && git checkout -b phase-5/task-14-cv-cache
```

- [ ] **Step 2: Read current cv-loading.md**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
cat skills/shared-references/cv-loading.md
```

- [ ] **Step 3: Append/strengthen the cache section**

If the file already has a cache section, replace it. Otherwise append. The section must contain exactly:

===FILE_START===

## CV parse cache (mandatory)

Parsing a CV (PDF/DOCX/Markdown → structured `cv_summary`) is expensive. The parse result is cached in `.job-scout/cache/cv-<cv_hash>.json` and reused.

### cv_hash computation

`cv_hash = sha1(file-bytes-of-cv-on-disk)`. The hash is computed by `/analyze-cv` and stored on `user-profile.json.cv_hash`. Every other skill reads the hash from there — never re-computes.

### Read path

```
1. /analyze-cv (or any skill that needs parsed CV facts) reads `user-profile.json.cv_hash`.
2. If null OR if the CV file on disk has changed (re-hash and compare) → bust the cache, re-parse.
3. Otherwise → load `cache/cv-<cv_hash>.json` and use it.
```

### Write path

After parsing, write:

```json
{
  "cv_hash": "<sha1>",
  "parsed_text": "<raw text>",
  "key_skills": [...],
  "technologies": [...],
  "seniority": "...",
  "years_experience": 10,
  "target_roles": [...],
  "domain_expertise": [...],
  "industries": [...],
  "parsed_at": "ISO8601"
}
```

Both `user-profile.json.cv_summary` (a denormalised view) and `cache/cv-<cv_hash>.json` (canonical parse) are updated atomically.

### Empty-cache reality

Both live workspaces have empty `cache/` dirs. The first `/analyze-cv` run post-migration populates the cache.
===FILE_END===

- [ ] **Step 4: Verify**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
grep -q "cv-<cv_hash>.json" skills/shared-references/cv-loading.md
grep -q "sha1" skills/shared-references/cv-loading.md
```

Expected: both pass.

- [ ] **Step 5: Commit**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
git add skills/shared-references/cv-loading.md
git commit -m "Strengthen CV parse cache contract in cv-loading.md"
git checkout main && git merge --no-ff phase-5/task-14-cv-cache -m "Merge phase-5/task-14-cv-cache"
```

---

## Task 15: Archive pass scaffolding

**Files:**
- Create: `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout/skills/shared-references/archive-pass.md`

- [ ] **Step 1: Branch**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout" && git checkout main && git pull --rebase && git checkout -b phase-5/task-15-archive-pass
```

- [ ] **Step 2: Write the reference**

Create the file:

===FILE_START===
# Archive Pass

> **Run once per calendar day per workspace.** Gated by `tracker.stats.last_archive_pass`. Rotates aged `status: seen` entries out of hot `tracker.json` into `.job-scout/archive/tracker-<year>.json`.

## When to run

In every command's Step 0 bootstrap, after loading `tracker.json`:

```
if today's date == tracker.stats.last_archive_pass → skip.
else → run the pass, update last_archive_pass to today's date.
```

## What to archive

- `status == "seen"` AND `last_seen` older than 60 days from today.
- Group by year (`first_seen` year).
- For each year, append the eligible jobs to `archive/tracker-YYYY.json` (canonical v2 shape, no `stats` block).
- Remove the archived entries from hot `tracker.json`.

## What NOT to archive

- `approved`, `applied`, `rejected`, `skipped` — these all represent user intent. Stay hot indefinitely.

## Implementation outline (per workspace)

```bash
archive_pass() {
  local D="$1"
  local IN="$D/tracker.json"
  local TODAY; TODAY=$(date -u +%Y-%m-%d)

  local LAST_PASS
  LAST_PASS=$(jq -r '.stats.last_archive_pass // "1970-01-01"' "$IN")
  if [ "$LAST_PASS" = "$TODAY" ]; then return 0; fi

  local CUTOFF
  CUTOFF=$(date -u -v-60d +%Y-%m-%d 2>/dev/null || date -u -d '60 days ago' +%Y-%m-%d)

  mkdir -p "$D/archive"

  # 1. Compute eligible job-id list per year
  local YEARS
  YEARS=$(jq -r --arg cutoff "$CUTOFF" '
    [.jobs[] | select(.status == "seen" and .last_seen < $cutoff) | (.first_seen[0:4])] |
    unique | .[]' "$IN")

  for YR in $YEARS; do
    local ARCH="$D/archive/tracker-$YR.json"
    if [ ! -f "$ARCH" ]; then
      echo '{"schema_version": 2, "version": 2, "jobs": {}}' > "$ARCH"
    fi
    # Move eligible entries for this year from hot to archive
    jq --arg cutoff "$CUTOFF" --arg yr "$YR" --slurpfile arch "$ARCH" '
      ($arch[0].jobs // {}) as $existing |
      .jobs as $hot |
      ($hot | with_entries(select(.value.status == "seen" and .value.last_seen < $cutoff and (.value.first_seen[0:4] == $yr)))) as $movers |
      {schema_version: 2, version: 2, jobs: ($existing + $movers)}
    ' "$IN" > "$ARCH.tmp" && mv "$ARCH.tmp" "$ARCH"

    jq --arg cutoff "$CUTOFF" --arg yr "$YR" '
      .jobs |= with_entries(select(
        (.value.status != "seen") or
        (.value.last_seen >= $cutoff) or
        (.value.first_seen[0:4] != $yr)
      ))
    ' "$IN" > "$IN.tmp" && mv "$IN.tmp" "$IN"
  done

  # 2. Update last_archive_pass + recompute total_seen
  jq --arg today "$TODAY" '
    .stats.last_archive_pass = $today
    | .stats.total_seen = ([.jobs[] | select(.status == "seen")] | length)
  ' "$IN" > "$IN.tmp" && mv "$IN.tmp" "$IN"
}
```

## Wired into

Commands that invoke the archive pass:

- `/check-job-notifications` Step 0 (after tracker load)
- `/job-search` Step 0
- `/match-jobs` Step 0
- `/funnel-report` Step 0
- `/check-inbox` Step 0 (only if there is a tracker — `check-inbox` does not normally touch tracker; safe to skip)

The pass is idempotent and same-day-gated, so calling it from many commands is safe and cheap.

## Verification

```bash
D="/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/CoWork/CVDIRECTOR/.job-scout"
jq '{last_archive_pass: .stats.last_archive_pass, hot_seen: ([.jobs[] | select(.status == "seen")] | length)}' "$D/tracker.json"
ls "$D/archive/" 2>/dev/null
```

Right after the first pass, `last_archive_pass` is today's date and any entries with `last_seen < (today - 60d)` and `status == "seen"` are gone from the hot file (moved to `archive/tracker-YYYY.json`).
===FILE_END===

- [ ] **Step 3: Verify**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
wc -l skills/shared-references/archive-pass.md
grep -c "^## " skills/shared-references/archive-pass.md
```

Expected: ≥80 lines; ≥6 sections.

- [ ] **Step 4: Commit**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
git add skills/shared-references/archive-pass.md
git commit -m "Add archive-pass.md — daily-gated 60d rotation procedure"
git checkout main && git merge --no-ff phase-5/task-15-archive-pass -m "Merge phase-5/task-15-archive-pass"
```

---

## Task 16: Populate `tone` block in both workspaces

**This task mutates live state.** Confirm with the user.

**Files:**
- Modify: `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/CoWork/CVDIRECTOR/.job-scout/user-profile.json`
- Modify: `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/CoWork/CVFREELANCER/.job-scout/user-profile.json`

- [ ] **Step 1: Approval gate**

Tell the user: "About to write the canonical British/sophisticated/charming tone block to both workspaces' user-profile.json. Source: the voice spec saved at ~/.claude/projects/-Users-tura/memory/voice_british_charming.md. Proceed?"

- [ ] **Step 2: Write the tone block**

```bash
write_tone() {
  local D="$1"
  local IN="$D/user-profile.json"
  local TMP="$D/user-profile.json.tmp"

  jq '.tone = {
    register: "considered, restrained, dry-witted",
    dialect: "british",
    warmth: "personable but never sycophantic; gracious not effusive",
    vocabulary_cues: [
      "organise","programme","behaviour","favour",
      "happy to","delighted to","do let me know",
      "rather","quite","indeed",
      "have a think","circle back","in due course"
    ],
    exemplars: [
      "Thank you for reaching out — the role sounds intriguing, and I'\''d be glad to learn more.",
      "Happy to share more detail once I'\''ve had a closer look at the JD.",
      "I'\''m afraid this one isn'\''t quite a fit for me at the moment, but do keep me in mind for future briefs.",
      "Just circling back on this — let me know if it'\''d be useful to compare notes in the next week or so."
    ],
    avoid: [
      "super excited",
      "I am writing to express my interest",
      "cheerio","old chap",
      "American spellings (organize, color, etc.)",
      "exclamation points beyond one per message",
      "stacked buzzwords",
      "self-deprecation that undermines authority"
    ]
  }' "$IN" > "$TMP" && mv "$TMP" "$IN"
}

for ws in CVDIRECTOR CVFREELANCER; do
  D="/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/CoWork/$ws/.job-scout"
  write_tone "$D"
done
```

- [ ] **Step 3: Verify**

```bash
for ws in CVDIRECTOR CVFREELANCER; do
  D="/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/CoWork/$ws/.job-scout"
  echo "=== $ws ==="
  jq '{dialect: .tone.dialect, exemplar_count: (.tone.exemplars | length), avoid_count: (.tone.avoid | length), cue_count: (.tone.vocabulary_cues | length)}' "$D/user-profile.json"
done
```

Expected: `dialect: "british"`, `exemplar_count: 4`, `avoid_count: 7`, `cue_count: 13` in both workspaces.

- [ ] **Step 4: Re-run `validate_profile` — tone block warning should now be gone**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
source <(grep -A30 'validate_profile()' skills/shared-references/state-validators.md | sed -n '/^```bash$/,/^```$/{//d;p;}' | head -30)
for ws in CVDIRECTOR CVFREELANCER; do
  D="/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/CoWork/$ws/.job-scout"
  validate_profile "$D/user-profile.json" 2>&1 | grep -v "WARN: tone block missing" || echo "$ws clean"
done
```

Expected: each prints `OK` (no `WARN` line).

- [ ] **Step 5: Note completion. No repo commit.**

---

## Task 17: Plugin version + CHANGELOG entry (Phase 0 portion)

**Files:**
- Modify: `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout/.claude-plugin/plugin.json`
- Modify: `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout/CHANGELOG.md`

- [ ] **Step 1: Branch**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout" && git checkout main && git pull --rebase && git checkout -b phase-5/task-17-version-bump
```

- [ ] **Step 2: Bump version to `0.8.0-dev`**

Edit `.claude-plugin/plugin.json` and change `"version": "0.7.0"` → `"version": "0.8.0-dev"`. The `-dev` suffix marks WIP; flip to `0.8.0` in Task 32 when the phase ships.

- [ ] **Step 3: Add a CHANGELOG.md entry**

Prepend to `CHANGELOG.md` after the existing `## [Unreleased]` (or top) block:

===FILE_START===
## [0.8.0] — TBD

### Added
- `skills/shared-references/canonical-schemas.md` — locked v2 schemas for `user-profile.json`, `tracker.json`, `recruiters/threads.json`.
- `skills/shared-references/state-validators.md` — pre-write enum + transition validators.
- `skills/shared-references/jd-storage.md` — hybrid JD-blob storage contract.
- `skills/shared-references/voice-profile.md` — tone-block consumer contract.
- `skills/shared-references/archive-pass.md` — daily-gated 60-day rotation procedure.
- `user-profile.json.segment` field (`director-perm | freelance`) and `tone` block populated from the user's voice spec.

### Changed
- Both live workspace `tracker.json` files migrated in place to canonical v2 (statuses, tiers, fields). 770 entries preserved; 7 corrupt entries dropped (or N — exact count from Task 9 run).
- `user-profile.json` migrated in place; legacy `cv_summary` string preserved as `cv_summary_text`.
- `recruiters/threads.json` migrated (CVDIRECTOR) or initialised (CVFREELANCER) to canonical v2.
- `tracker.json` no longer carries inline `description`; full JD text lives at `.job-scout/jds/<id>.txt`, pointer via `jd_path`.
- Score cache key now includes `rubric_version` to invalidate cleanly on rubric upgrades.

### To follow in Phase 5 (Accuracy core)
- `_gate-engine` skill, hybrid-elicited dealbreakers, per-segment rubric dimensions, evidence-quote breakdown, lazy-rescore.
===FILE_END===

(If the version-bump message above was placed in Task 32's commit window, adjust accordingly — leave the `## [0.8.0] — TBD` heading until release tag.)

- [ ] **Step 4: Verify**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
jq -r .version .claude-plugin/plugin.json
head -5 CHANGELOG.md
```

Expected: version is `0.8.0-dev`; CHANGELOG has a new `[0.8.0]` block.

- [ ] **Step 5: Commit**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
git add .claude-plugin/plugin.json CHANGELOG.md
git commit -m "Bump to 0.8.0-dev — Phase 5 (foundations) in flight"
git checkout main && git merge --no-ff phase-5/task-17-version-bump -m "Merge phase-5/task-17-version-bump"
```

---

## Task 18: End-to-end Phase 0 verification

No new files. Verification only.

- [ ] **Step 1: Run a dry-run of `/check-job-notifications` against the migrated CVFREELANCER workspace**

Ask the user to `cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/CoWork/CVFREELANCER"` and run `/check-job-notifications` in Claude Code. The first-run path should:

- Read the canonical v2 `tracker.json` without error.
- Read the canonical v2 `user-profile.json` without error.
- Find `segment: "freelance"` and `tone` block populated.
- Print the daily-driver context line (Step 0a) showing the correct `last_run`, `total_seen`, `A-tier`, `applied` counts (no `null` errors).
- When extracting a new job, write `.job-scout/jds/<id>.txt` and set `jd_path` on the tracker entry.

If any of the above fails, fix the originating Task before declaring Phase 0 done.

- [ ] **Step 2: After the run, inspect**

```bash
D="/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/CoWork/CVFREELANCER/.job-scout"
echo "=== jds populated ==="
ls "$D/jds/" 2>/dev/null | wc -l
echo "=== tracker entries with jd_path ==="
jq '[.jobs[] | select(.jd_path != null)] | length' "$D/tracker.json"
echo "=== scores cache populated ==="
ls -la "$D/cache/" 2>/dev/null
```

Expected: `jds/` count matches the number of newly extracted jobs from the run; `jd_path` count matches; `cache/` has `scores.json` and `cv-<hash>.json`.

- [ ] **Step 3: Repeat against CVDIRECTOR**

Same as Step 1, on the director workspace. Confirms multi-workspace consistency.

- [ ] **Step 4: Sign-off**

If both workspaces pass, Phase 0 is complete. Proceed to Phase 1.

If anything fails, log the failure, identify the originating task, and re-open it for fixes.

---

# Phase 1 — Accuracy Core (Tasks 19–31)

## Task 19: `_gate-engine` skill skeleton

**Files:**
- Create: `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout/skills/_gate-engine/SKILL.md`
- Create: `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout/skills/_gate-engine/references/gate-rules.md`

- [ ] **Step 1: Branch**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout" && git checkout main && git pull --rebase && git checkout -b phase-5/task-19-gate-engine-skel
```

- [ ] **Step 2: Write `_gate-engine/SKILL.md`**

===FILE_START===
---
name: _gate-engine
description: >
  [Internal — loaded by _job-matcher and the orchestrators of /match-jobs and /check-job-notifications] Evaluates a job listing against the user's declared deal_breakers in user-profile.json. Returns a list of gate_violations and an overall gated flag. Any non-empty violation list forces the job to tier D with no further scoring. This is the primary false-positive defence in v0.8.0.
version: 0.1.0
---

# Gate Engine

Hard-gate jobs against declared dealbreakers before any scoring happens.

## Why this skill exists

Pre-v0.8.0, the matcher computed a weighted score over Skills, Experience, Requirements, Growth, and Practical. The Requirements dimension was 25% — meaning a job that violated work_arrangement, contract type, or seniority floor could still score 75 from the other four dimensions and land in B-tier. The fix is structural: dealbreaker violations are not partial-credit factors; they are gates.

## Inputs

- The user-profile.json `requirements` block (esp. `deal_breakers[]`, `work_arrangement`, `contract_type`, `companies_to_avoid`, `industries_to_avoid`, `seniority_floor`, `min_day_rate`, `salary_floor`, `rate_currency`, `salary_currency`, `location_preferences`).
- The extracted job listing: title, company, location, work_arrangement, contract_type, seniority, industry, day_rate (if disclosed), salary (if disclosed), JD text.

## Output

```json
{
  "gated": true | false,
  "gate_violations": [
    {"kind": "work_arrangement|contract_type|seniority_floor|location|industry|company|rate_floor|salary_floor|custom",
     "detail": "<one-line human readable reason>"}
  ]
}
```

## Evaluation order

See `references/gate-rules.md` for the full rules table. Evaluate in this order (cheap → expensive):

1. **company** — fail-fast if `job.company` is in `requirements.companies_to_avoid` (case-insensitive substring match).
2. **work_arrangement** — fail if `job.work_arrangement` is not in `requirements.work_arrangement`.
3. **contract_type** — fail if `job.contract_type` not in `requirements.contract_type`.
4. **location** — fail if `job.location` is not covered by `requirements.location_preferences` (preference may be country, region, or "worldwide remote").
5. **seniority_floor** — fail if `job.seniority` < `requirements.seniority_floor`. Seniority ordering: Junior < Mid < Senior < Lead < Manager < Senior Manager < Director < Senior Director < VP < SVP < C-level. For director-perm segment, default floor is `Director`. For freelance, the floor is whatever the user declared (often "Senior" or "Lead").
6. **industry** — fail if `job.industry` (parsed from JD) is in `requirements.industries_to_avoid`.
7. **rate_floor / salary_floor** — fail if `job.day_rate < requirements.min_day_rate` (with currency check) OR `job.salary < requirements.salary_floor`. If the listing doesn't disclose, do NOT gate (flag for follow-up in the report card instead).
8. **custom deal_breakers** — for each `deal_breaker` of kind `custom`, evaluate the `free_text` rule via an LLM call against the JD text. Costly; runs last.

If any check fails, append the violation and continue evaluating remaining checks — the user benefits from seeing the full list of reasons, not just the first one.

## Behaviour

- If `gate_violations` is non-empty, the consumer (`_job-matcher`) sets `tier: D`, `tier_reason: "gated: <kinds>"`, `gate_violations: [...]`, and skips dimension scoring.
- If `gate_violations` is empty, the consumer proceeds with dimension scoring.

## Caching

Gate results are part of the score cache (see `_job-matcher` SKILL.md § Score Caching Contract). Same key (`job_id × cv_hash × profile_hash × rubric_version`). Profile changes invalidate via `profile_hash` bump (`/analyze-cv` recomputes the hash when `requirements` changes).

## Reference Materials

- `references/gate-rules.md` — full rules table, seniority ordering, location-match logic, currency handling.
===FILE_END===

- [ ] **Step 3: Write the placeholder `references/gate-rules.md`**

===FILE_START===
# Gate Rules

The operational table the `_gate-engine` skill consults. Phase 5 Task 20 fills in the seniority ordering, location-match details, and the LLM-prompt template for `custom` deal-breakers. This file is a placeholder until then.

## Seniority ordering

```
junior < mid < senior < lead < manager < senior manager < director < senior director < vp < svp < c-level
```

Comparison is case-insensitive substring against the parsed `seniority` field on the job listing. A JD that reads "Director / Head of Platform" satisfies a `director` floor.

## Location match

The `requirements.location_preferences` array may contain country codes, region names (`EU`, `UK`, `EEA`, `worldwide remote`), or city names. Match logic:

1. If `job.work_arrangement` is `remote` AND any of the preferences is `worldwide remote` or `remote` → pass.
2. If preference is a country/region and `job.location` mentions that country/region (case-insensitive) → pass.
3. If preference is a city and `job.location` mentions that city → pass.
4. Otherwise → fail.

## Currency for rate/salary gates

If currencies differ between `requirements.rate_currency` (e.g. GBP) and `job.day_rate_currency` (e.g. EUR), the gate engine SHOULD convert using a daily-cached FX rate. **Phase 5 simplification:** if currencies differ, do NOT gate; flag the listing for manual review and surface in the report card. (Phase 6 candidate to add FX.)

## Custom deal-breakers (LLM prompt)

```
You are checking whether a job listing violates a user-declared dealbreaker.

Dealbreaker rule (free text): {{deal_breaker.free_text}}

Job listing:
- Title: {{job.title}}
- Company: {{job.company}}
- Location: {{job.location}}
- JD text: {{job.jd_text[:2000]}}

Reply with strict JSON: {"violates": true|false, "detail": "<one-line reason>"}.
```

Phase 5 limits the count of `custom` dealbreakers per evaluation to 3 (cap declared in `/analyze-cv` elicitation — the open free-text prompt collects at most 3 entries).
===FILE_END===

- [ ] **Step 4: Verify**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
ls skills/_gate-engine/
grep -q "_gate-engine" skills/_gate-engine/SKILL.md
grep -q "seniority ordering" skills/_gate-engine/references/gate-rules.md
```

- [ ] **Step 5: Commit**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
git add skills/_gate-engine/
git commit -m "Add _gate-engine skill skeleton + gate-rules reference"
git checkout main && git merge --no-ff phase-5/task-19-gate-engine-skel -m "Merge phase-5/task-19-gate-engine-skel"
```

---

## Task 20: Extend `/analyze-cv` — segment declaration + hybrid dealbreaker elicitation + tone confirmation

**Files:**
- Modify: `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout/skills/analyze-cv/SKILL.md`

- [ ] **Step 1: Branch**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout" && git checkout main && git pull --rebase && git checkout -b phase-5/task-20-analyze-cv-discovery
```

- [ ] **Step 2: Read current `/analyze-cv` to find insertion points**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
head -100 skills/analyze-cv/SKILL.md
```

- [ ] **Step 3: Add a "Discovery interview" section to `analyze-cv/SKILL.md`**

After the existing CV-parsing step but before any LinkedIn upload step, insert this exact section:

===FILE_START===

## Step 3a: Discovery interview (one-time per workspace)

Skip if `user-profile.json.discovery_complete == true` AND the user did not pass `--rediscover`.

Otherwise, conduct the hybrid discovery interview:

### Segment declaration

Ask: "Is this workspace for permanent director/exec roles, or freelance/contract work?"

- "perm director" → `segment: "director-perm"`
- "freelance" / "contract" → `segment: "freelance"`

Write the answer to `user-profile.json.segment`.

### Dealbreaker checklist (menu)

Walk this checklist. For each item, ask the user to confirm whether it's a HARD GATE for them. A hard gate auto-rejects any listing that violates it.

| # | Question | If yes, write to |
|---|---|---|
| 1 | "Are there work arrangements you absolutely won't consider? (e.g. 'must be remote', 'no fully on-site')." | `requirements.work_arrangement` (whitelist) and `requirements.deal_breakers[]` with kind `work_arrangement` |
| 2 | "Is contract type a hard rule? (perm-only, freelance-only, or both fine?)" | `requirements.contract_type` (whitelist) and `requirements.deal_breakers[]` with kind `contract_type` |
| 3 | "Is there a seniority level below which a listing should be auto-rejected?" | `requirements.seniority_floor` and `requirements.deal_breakers[]` with kind `seniority_floor` |
| 4 | "Geographies you won't entertain? (e.g. 'must be EU-based', 'no US-based on-site', 'no relocation required')." | `requirements.location_preferences` and `requirements.deal_breakers[]` with kind `location` |
| 5 | "Industries you don't want to be approached for? (e.g. gambling, defence, crypto, MLM)." | `requirements.industries_to_avoid` and `requirements.deal_breakers[]` with kind `industry` |
| 6 | "Specific companies to avoid?" | `requirements.companies_to_avoid` and `requirements.deal_breakers[]` with kind `company` |
| 7 | "Minimum day rate or salary floor below which a listing should auto-reject?" | `requirements.min_day_rate` / `requirements.salary_floor` and `requirements.deal_breakers[]` with kind `rate_floor` or `salary_floor` |

For each `deal_breaker` entry, set `source: "elicited"` and `added_at: <now ISO8601>`.

### Open free-text follow-up

Ask: "Anything else that should auto-reject a listing for you? Up to three. Free text — I'll evaluate each against new JDs."

For each non-empty answer, append a `deal_breaker` entry with `kind: "custom"`, `free_text: "<the answer>"`, `source: "elicited"`.

Cap at 3 entries. (Performance — each `custom` rule means one extra LLM call per scored job.)

### Tone confirmation

Read the saved tone block (Task 16 wrote it from the user's voice spec). Echo a one-line summary:

> "Voice on drafts is set to: British, sophisticated, charming, classy, likable. Want to change it?"

If yes, walk a brief elicitation (register, dialect, warmth, vocab cues, exemplars, avoid). If no, do nothing — keep the current tone.

### Persist + mark discovery complete

After the interview, write all changes to `user-profile.json` via `validate_profile` (atomic-rename). Set `discovery_complete: true` and `last_updated: <now>`.
===FILE_END===

- [ ] **Step 4: Verify**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
grep -q "Discovery interview" skills/analyze-cv/SKILL.md
grep -q "Dealbreaker checklist" skills/analyze-cv/SKILL.md
grep -q "Tone confirmation" skills/analyze-cv/SKILL.md
grep -q "segment" skills/analyze-cv/SKILL.md
```

Expected: all four checks return 0.

- [ ] **Step 5: Commit**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
git add skills/analyze-cv/SKILL.md
git commit -m "/analyze-cv: hybrid dealbreaker elicitation + segment + tone"
git checkout main && git merge --no-ff phase-5/task-20-analyze-cv-discovery -m "Merge phase-5/task-20-analyze-cv-discovery"
```

---

## Task 21: Per-segment dimension references — director-perm

**Files:**
- Create: `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout/skills/_job-matcher/references/dimensions-director-perm.md`

- [ ] **Step 1: Branch**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout" && git checkout main && git pull --rebase && git checkout -b phase-5/task-21-dims-director
```

- [ ] **Step 2: Write the dimensions file**

===FILE_START===
# Dimensions — director-perm

For `segment: director-perm` workspaces. Each scored job receives an A/B/C/D tier per dimension plus evidence quotes pulled from the JD. The overall tier is derived from the dimension tiers per the rule at the bottom.

## Dimensions

### 1. Leadership scope

Does the role's organisational scope match the candidate's prior scope?

- **A:** JD explicitly names: directly managing managers, P&L responsibility, org of 30+ engineers/staff, or named board-adjacent role (CTO/CIO/CPO/Head of X with department-level scope).
- **B:** JD names: managing 10–30 directly or through team leads, multi-team responsibility, no P&L but clear strategic remit.
- **C:** JD names: managing 5–10, single team, ambiguous on scope, or "Lead" title without scope clarity.
- **D:** JD names: IC, dotted-line management only, or a manager-of-1.

Evidence to quote: explicit team size, "managing X engineers", "owning P&L", "reporting to CTO/CEO".

### 2. Domain

Does the job's industry/sector overlap with the candidate's experience and stated preferences?

- **A:** Aerospace, space, scientific computing, large-scale R&D infrastructure (direct fit to user's ESA/ESTEC background); or top-tier financial services / regulated industries where the user has explicit experience.
- **B:** Adjacent regulated industries (govtech, energy, biotech, defence-adjacent enterprise IT), or large-enterprise IT where infrastructure scale is meaningful.
- **C:** General enterprise IT, financial services without explicit regulatory complexity, mid-market SaaS.
- **D:** Early-stage startups asking director-level for IC work; consumer web; consulting bodyshops.

Evidence: company description, sector keywords in JD.

### 3. Function

Does the functional flavour of the role match the candidate's track record?

- **A:** IT Director / Head of IT Services / Service Delivery Director / Head of Infrastructure / Head of Enterprise Architecture — directly listed in `target_titles`.
- **B:** Adjacent function: Head of Platform, Head of Technology Operations, IT Operations Director — close but not exact match to declared targets.
- **C:** Title is director-level but functional remit is different (Head of Product, Head of Engineering with no infra remit).
- **D:** Functional remit is mismatched (e.g. Head of Sales Engineering for an infra candidate).

Evidence: title, "function" or "remit" line in JD.

### 4. Track-record alignment

Does the JD's stated experience profile align with the candidate's track record?

- **A:** JD names experience the candidate has explicitly: ESA / aerospace / scientific computing background; ITIL/ITSM at scale; vendor & contract management; multi-decade IT.
- **B:** JD names experience adjacent: large-scale ITSM, multi-vendor environments, regulated procurement, 15+ years IT, prior director-level role.
- **C:** JD's experience profile is generic ("10+ years in IT leadership") with no specifics that align uniquely.
- **D:** JD asks for experience the candidate lacks (e.g. heavy SaaS product engineering background, US-only regulatory experience).

Evidence: "Requirements" or "About you" section quotes.

### 5. Cultural signals

How does the company present itself — founder-led, PE-owned, public, government, scientific institution? Does that match the candidate's preference profile?

- **A:** Scientific / research institutions; founder-led mature companies; PE-backed with multi-year hold; firms that mention "considered" or "long-horizon" decision-making.
- **B:** Mid-stage growth companies with seasoned management; public companies with stable senior teams.
- **C:** PE roll-ups, fast-growth startups with first director hire, consultancies.
- **D:** Pre-Series-A startups asking for director-level work; heavily process-heavy firms; companies with explicit "fast-paced" / "wear many hats" language at director level.

Evidence: company About section, JD tone, "we are a team that…" lines.

## Overall tier derivation

| Dimension tiers | Overall tier |
|---|---|
| All A or one B (rest A) | **A** |
| Majority B, no C/D | **B** |
| Any C, no D | **C** |
| Any D in {Leadership scope, Function, Track-record} | **D** |
| Any D in {Domain, Cultural signals} but rest ≥ B | **C** |

(Hard gates are applied earlier in `_gate-engine`; any gated job is D before dimensions are computed.)
===FILE_END===

- [ ] **Step 3: Verify**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
wc -l skills/_job-matcher/references/dimensions-director-perm.md
grep -c "^### " skills/_job-matcher/references/dimensions-director-perm.md
```

Expected: ≥80 lines; ≥5 sub-sections.

- [ ] **Step 4: Commit**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
git add skills/_job-matcher/references/dimensions-director-perm.md
git commit -m "Add director-perm dimensions reference for _job-matcher"
git checkout main && git merge --no-ff phase-5/task-21-dims-director -m "Merge phase-5/task-21-dims-director"
```

---

## Task 22: Per-segment dimension references — freelance

**Files:**
- Create: `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout/skills/_job-matcher/references/dimensions-freelance.md`

- [ ] **Step 1: Branch**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout" && git checkout main && git pull --rebase && git checkout -b phase-5/task-22-dims-freelance
```

- [ ] **Step 2: Write the dimensions file**

===FILE_START===
# Dimensions — freelance

For `segment: freelance` workspaces.

## Dimensions

### 1. Skills (semantic)

Not keyword bingo. Evaluate whether the JD's required technologies have demonstrable evidence in the CV — same skill, called by a different name counts (e.g. JD says "GitOps tooling", CV mentions ArgoCD + FluxCD → A).

- **A:** Every required skill in the JD has direct or strong-adjacent evidence on the CV. CV shows depth (multi-year, multiple projects), not just exposure.
- **B:** Most required skills covered; one or two require transferable-skill argument.
- **C:** Half or fewer required skills covered; gaps would need bridging on the job.
- **D:** Core required skills absent; CV-to-JD mismatch.

Evidence: pair each required-skill from JD with the CV bullet / project that demonstrates it.

### 2. Engagement shape

Does the contract's shape (duration, hours, start date) suit the candidate?

- **A:** Duration 3–9 months, full-time hours, start date within candidate's stated availability window, named extension potential.
- **B:** Duration acceptable (e.g. 12+ months for an open-ended engagement, or 1–3 months for a clear sprint), full-time or part-time matching candidate preference.
- **C:** Duration ambiguous in JD; start date outside candidate's window by a few weeks; hours unclear.
- **D:** Sub-month gigs, "as-needed" hours, indefinite open-ended ICs.

Evidence: "duration", "start date", "hours per week" lines in JD.

### 3. Commercial fit

Does the rate (when disclosed) and terms (IR35 status, currency) work?

- **A:** Rate disclosed, at or above `min_day_rate`, IR35 outside (UK) or equivalent jurisdiction terms favourable, currency matches `rate_currency`.
- **B:** Rate disclosed and acceptable, IR35 status not stated but client type implies outside; or rate slightly below ideal but within negotiating range.
- **C:** Rate not disclosed (typical of agencies), but client/agency reputable and worth a qualification call.
- **D:** Rate disclosed and below floor (hard gate — should be caught by `_gate-engine`); IR35 inside without uplift; currency conversion at-loss.

Evidence: rate line, IR35 line, "via [agency]" or "end client" line.

### 4. Stack & methodology

Does the JD's tech stack and ways of working align with how the candidate wants to operate?

- **A:** Stack heavily overlaps CV's preferred technologies (Linux, Ansible, Terraform, Kubernetes, RHEL, FreeIPA, etc.). Methodology: GitOps, IaC, SRE practices, mature CI/CD — words the candidate uses.
- **B:** Stack overlaps in core areas (some Linux, some IaC) with extension into adjacent tech (e.g. Pulumi instead of Terraform). Methodology is sound.
- **C:** Stack partially overlaps; substantial unfamiliar components require ramp-up.
- **D:** Stack is largely unfamiliar (e.g. Windows-heavy, low-code platforms, .NET-only); methodology is anti-pattern (manual deploys, ticket-based ops).

Evidence: "Tech stack", "we use" lines in JD.

### 5. Client signals

Is this end-client direct, a reputable agency, or a body-shop pretending? Does the client likely lead to repeat work or a strong reference?

- **A:** Named end-client (not via undisclosed agency), brand has visible engineering culture / blog / open-source / talks. Reputational upside.
- **B:** Agency named, agency has track record of placing senior infrastructure people; end client identified.
- **C:** Agency, end client undisclosed, generic "exciting opportunity" copy.
- **D:** Anonymous agency, end client refused on contact, copy reads like mass outreach, sub-contractor pyramid signs.

Evidence: agency name, "end client" line, candidate-side reputation lookup.

## Overall tier derivation

| Dimension tiers | Overall tier |
|---|---|
| All A or one B (rest A) | **A** |
| Majority B, no C/D | **B** |
| Any C, no D | **C** |
| Any D in {Skills, Commercial fit, Stack & methodology} | **D** |
| Any D in {Engagement shape, Client signals} but rest ≥ B | **C** |

(Hard gates applied earlier in `_gate-engine`; gated jobs are D before dimensions are computed.)
===FILE_END===

- [ ] **Step 3: Verify**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
wc -l skills/_job-matcher/references/dimensions-freelance.md
grep -c "^### " skills/_job-matcher/references/dimensions-freelance.md
```

Expected: ≥80 lines; ≥5 sub-sections.

- [ ] **Step 4: Commit**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
git add skills/_job-matcher/references/dimensions-freelance.md
git commit -m "Add freelance dimensions reference for _job-matcher"
git checkout main && git merge --no-ff phase-5/task-22-dims-freelance -m "Merge phase-5/task-22-dims-freelance"
```

---

## Task 23: Rewrite `_job-matcher/SKILL.md` — segment-aware, gated, dimension-based

**Files:**
- Modify: `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout/skills/_job-matcher/SKILL.md`

- [ ] **Step 1: Branch**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout" && git checkout main && git pull --rebase && git checkout -b phase-5/task-23-job-matcher-rewrite
```

- [ ] **Step 2: Replace the entire `_job-matcher/SKILL.md` with this content**

(Keep the existing frontmatter — `name`, `description`, `version: 0.2.0`.)

===FILE_START===
---
name: _job-matcher
description: >
  [Internal — loaded by /match-jobs and /check-job-notifications] This skill should be used when the user asks to "match jobs to my CV", "score these jobs", "rank job listings", "find best matches", "analyze job alerts", "which jobs should I apply to", "compare jobs against my profile", or needs to evaluate job listings against their CV and stated requirements.
version: 0.2.0
---

# Job Matcher (rubric v1)

Score, rank, and filter job listings against a user's CV and stated requirements. The v1 rubric (this file) replaces the v0.1 keyword-bingo weighted score with a hard-gated, segment-aware, per-dimension tiering whose output is auditable.

## Rubric flow

```
For each candidate job:
  1. Load score cache; if hit (key includes rubric_version: v1) → return cached.
  2. Run _gate-engine. If gate_violations is non-empty:
       tier = D
       tier_reason = "gated: <kinds>"
       dimensions = {}
       — write to cache and return.
  3. Load the dimension set for user-profile.segment:
       - "director-perm" → references/dimensions-director-perm.md
       - "freelance"     → references/dimensions-freelance.md
  4. Score each dimension. Output per dimension: { tier: A|B|C|D, evidence: [quote, ...] }.
  5. Derive overall tier from the dimension tiers using the table in the dimension reference.
  6. Persist to score cache and update the tracker entry: tier, tier_reason, dimensions, gate_violations, rubric_version: "v1".
```

## Output (per job)

```json
{
  "job_id": "string",
  "tier": "A | B | C | D",
  "tier_reason": "string|null",
  "dimensions": {
    "<dim_name>": {"tier": "A|B|C|D", "evidence": ["quote 1", "quote 2"]}
  },
  "gate_violations": [{"kind": "...", "detail": "..."}],
  "rubric_version": "v1"
}
```

The visualiser (`_visualizer`) renders the dimensions section in the report card; the user sees WHY a job got the tier it got, not just a number.

## Batch flow

When scoring N jobs in one /match-jobs or /check-job-notifications run:

1. Compute cache keys for all N. Partition into HIT and MISS.
2. HIT: return cached.
3. MISS: process in batches of ≤5 per LLM call where possible (batch by similarity — same company, same broad title pattern). For each MISS, run `_gate-engine` first, then the rubric.
4. Write all MISSes to the cache in one atomic update at the end.

## Score Caching Contract

Job scores are cached in `.job-scout/cache/scores.json` keyed by `(job_id, cv_hash, profile_hash, rubric_version)`.

Before scoring any job:

1. Compute the cache key from the job's `id`, the current `cv_hash`, `profile_hash`, and `rubric_version: "v1"` (all read from `.job-scout/user-profile.json` and from the rubric metadata in this file).
2. If a cached entry exists, **reuse it**. Neither the CV nor the profile nor the rubric has changed.
3. If no cached entry exists, run the rubric flow above and write the result back to `scores.json`.

A re-score happens when any key element changes: `cv_hash` (CV edit), `profile_hash` (LinkedIn profile update), `rubric_version` (this skill bumps to v2 in a future phase).

## Lazy rescore of legacy entries

Existing tracker entries from before v0.8.0 carry `rubric_version: "legacy"` (set by Task 9 migration). When the visualiser is about to display such an entry:

1. Check `rubric_version`. If `legacy` → trigger this skill's rubric flow to rescore.
2. Persist the new `tier`, `dimensions`, `tier_reason`, `gate_violations`, and bump `rubric_version` to `"v1"`.
3. Then render.

Cost is paid lazily as the user opens reports. Most legacy entries are below B-tier under v0 and don't appear in the daily top sections, so rescoring is bounded to what the user actually views.

## Inputs and state files

- **`.job-scout/user-profile.json`** — supplies `cv_hash`, `profile_hash`, `segment`, `requirements`, `tone`, `master_keyword_list`.
- **`.job-scout/tracker.json`** — supplies metadata; rubric output is persisted back here via `validate_tracker`.
- **`.job-scout/jds/<id>.txt`** — supplies the full JD text for evidence-quote extraction. If missing (legacy entry, `jd_path: null`), trigger fresh extraction via the Chrome extension before scoring.
- **`.job-scout/cache/scores.json`** — the score cache.

## Reference materials

- `../_gate-engine/SKILL.md` — hard-gate evaluator, runs before this skill.
- `references/dimensions-director-perm.md` — segment-specific dimensions.
- `references/dimensions-freelance.md` — segment-specific dimensions.
- `references/user-profile-schema.md` — pointer to canonical schemas.
- `../shared-references/canonical-schemas.md` — locked schemas.
- `../shared-references/state-validators.md` — pre-write validation.
- `../shared-references/jd-storage.md` — JD blob storage contract.
===FILE_END===

- [ ] **Step 3: Verify**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
grep -q "rubric v1" skills/_job-matcher/SKILL.md
grep -q "_gate-engine" skills/_job-matcher/SKILL.md
grep -q "dimensions-director-perm" skills/_job-matcher/SKILL.md
grep -q "dimensions-freelance" skills/_job-matcher/SKILL.md
grep -q "Lazy rescore" skills/_job-matcher/SKILL.md
! grep -q "Weight: 30%" skills/_job-matcher/SKILL.md   # ensure old weighted rubric gone
```

Expected: all six conditions pass.

- [ ] **Step 4: Commit**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
git add skills/_job-matcher/SKILL.md
git commit -m "Rewrite _job-matcher v0.2.0 — segment-aware, gated, dimension-based"
git checkout main && git merge --no-ff phase-5/task-23-job-matcher-rewrite -m "Merge phase-5/task-23-job-matcher-rewrite"
```

---

## Task 24: Wire `_gate-engine` into `/match-jobs` and `/check-job-notifications`

**Files:**
- Modify: `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout/skills/match-jobs/SKILL.md`
- Modify: `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout/skills/check-job-notifications/SKILL.md`

- [ ] **Step 1: Branch**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout" && git checkout main && git pull --rebase && git checkout -b phase-5/task-24-wire-gate
```

- [ ] **Step 2: Modify `match-jobs/SKILL.md` — replace the score step**

Find the section that loads `_job-matcher` (typically "Step 4: Score and Present" or similar). Replace it with this:

===FILE_START===
## Step 4: Gate + score

Load `_job-matcher` (which transitively loads `_gate-engine`). For each new or legacy-rubric job:

1. Run `_gate-engine` against `user-profile.requirements`. If `gate_violations` is non-empty → set `tier: D`, `tier_reason: "gated: ..."`, skip dimension scoring, persist.
2. Otherwise run the segment-specific rubric (per `user-profile.segment`). Persist `tier`, `dimensions`, `tier_reason`, `rubric_version: "v1"` to the tracker entry and the score cache.
3. Display: A-tier first (with full dimension breakdown), then B-tier (with one-line per dimension), then C/D summary counts (collapsed by default in the visual report).

Gated jobs do not appear in the daily top section of the report — they appear in a collapsed "Filtered out" group below.
===FILE_END===

- [ ] **Step 3: Modify `check-job-notifications/SKILL.md` Step 5 (Filter)**

Find `## Step 5: Filter`. Replace with:

===FILE_START===
## Step 5: Gate + score new jobs

Load `_job-matcher` (transitively `_gate-engine`). For every newly extracted job from Step 4:

1. `_gate-engine` runs first. If gated → `tier: D`, persist, move on.
2. If not gated → segment-aware rubric (per `user-profile.segment`) produces per-dimension tiers + evidence. Persist `tier`, `dimensions`, `tier_reason`, `rubric_version: "v1"`.

Daily-driver display: top section shows A-tier with full dimension breakdown; B-tier with one-line dimension highlights; C/D summary counts collapsed. Gated jobs go to "Filtered out".

Default user-profile requirements still apply (the migration ensured `work_arrangement` and `contract_type` are populated from legacy single-string fields). The `_gate-engine` consumes those plus declared `deal_breakers[]`.
===FILE_END===

- [ ] **Step 4: Verify**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
grep -q "_gate-engine" skills/match-jobs/SKILL.md
grep -q "_gate-engine" skills/check-job-notifications/SKILL.md
grep -q "dimension breakdown" skills/match-jobs/SKILL.md
```

Expected: all three pass.

- [ ] **Step 5: Commit**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
git add skills/match-jobs/SKILL.md skills/check-job-notifications/SKILL.md
git commit -m "Wire _gate-engine into /match-jobs and /check-job-notifications"
git checkout main && git merge --no-ff phase-5/task-24-wire-gate -m "Merge phase-5/task-24-wire-gate"
```

---

## Task 25: Visualizer — render per-dimension breakdown + gated section

**Files:**
- Modify: `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout/skills/_visualizer/SKILL.md`
- Modify: `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout/skills/_visualizer/references/component-library.md`

- [ ] **Step 1: Branch**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout" && git checkout main && git pull --rebase && git checkout -b phase-5/task-25-visualizer-breakdown
```

- [ ] **Step 2: Modify `_visualizer/SKILL.md` to declare the new card schema**

In the section that documents the per-view payload shape for `match-jobs` and `check-job-notifications`, replace the `results[]` job-entry shape with:

```json
{
  "title": "<job title>",
  "company": "<company>",
  "location": "<location>",
  "salary": "<salary or empty>",
  "posted_at": "<YYYY-MM-DD>",
  "applicants": "<applicant count or empty>",
  "tier": "A | B | C | D",
  "tier_reason": "string|null",
  "url": "<job URL>",
  "tags": ["...", "..."],
  "dimensions": {
    "<dim_name>": {"tier": "A|B|C|D", "evidence": ["...", "..."]}
  },
  "gate_violations": [{"kind": "...", "detail": "..."}],
  "rubric_version": "v1 | legacy"
}
```

If `gate_violations` is non-empty: the card is rendered in the collapsed "Filtered out" section with a one-line summary `"Gated: <kinds>"` — no dimension table.

Otherwise: the card shows a dimension table (5 rows, one per dimension) with the dimension name, tier badge, and 1–2 evidence quotes (italicised, ≤120 chars each).

If `rubric_version == "legacy"`: render a small "rescoring under v1…" placeholder and trigger lazy-rescore (see `_job-matcher/SKILL.md` § Lazy rescore) before re-rendering.

- [ ] **Step 3: Modify `_visualizer/references/component-library.md`**

Append a `### Job card v1 — dimension breakdown` component section. Document:

- The CSS class names used (`job-card`, `dim-row`, `dim-tier-A` … `dim-tier-D`, `evidence-quote`, `gated-banner`).
- The visual layout: tier badge top-left, title and company headline, location + posted-at sub-line, dimension table below, evidence quotes italicised right-column, gated section is collapsed by default.
- A small SVG/icon for "gated" (e.g. 🚫 emoji or icon font glyph).

- [ ] **Step 4: Update the HTML and Markdown templates under `skills/_visualizer/templates/`**

The templates already render score and tier. Extend them to render `dimensions` and `gate_violations`. Each template (`match-jobs.html`, `match-jobs.md`, `job-search.html`, `job-search.md`, `check-job-notifications.html`, `check-job-notifications.md`) gets the same treatment.

Pseudocode for the HTML card block (Jinja-shaped — adapt to whatever template engine the existing visualizer uses):

```html
<div class="job-card tier-{{job.tier|lower}}">
  {% if job.gate_violations and job.gate_violations|length > 0 %}
    <div class="gated-banner">🚫 Filtered out — {{ job.gate_violations | map(attribute='kind') | join(', ') }}</div>
  {% else %}
    <h3>{{job.title}} <span class="muted">— {{job.company}}</span></h3>
    <div class="meta">{{job.location}} · {{job.posted_at}}{% if job.applicants %} · {{job.applicants}} applicants{% endif %}</div>
    <table class="dim-table">
      {% for dim_name, dim in job.dimensions.items() %}
      <tr class="dim-row dim-tier-{{dim.tier}}">
        <th>{{dim_name|title}}</th>
        <td class="badge tier-{{dim.tier|lower}}">{{dim.tier}}</td>
        <td class="evidence">
          {% for q in dim.evidence[:2] %}<em>"{{q}}"</em>{% if not loop.last %}<br/>{% endif %}{% endfor %}
        </td>
      </tr>
      {% endfor %}
    </table>
  {% endif %}
  <a href="{{job.url}}" class="cta">View on LinkedIn ↗</a>
</div>
```

- [ ] **Step 5: Verify**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
grep -q "dimensions" skills/_visualizer/SKILL.md
grep -q "gate_violations" skills/_visualizer/SKILL.md
grep -q "dim-row" skills/_visualizer/references/component-library.md
ls skills/_visualizer/templates/html/ | head
```

Expected: schema/component refs present; HTML/markdown templates updated to reference dimensions.

- [ ] **Step 6: Commit**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
git add skills/_visualizer/
git commit -m "Visualizer: render per-dimension breakdown + gated-banner"
git checkout main && git merge --no-ff phase-5/task-25-visualizer-breakdown -m "Merge phase-5/task-25-visualizer-breakdown"
```

---

## Task 26: End-to-end smoke — gate a known false-positive, see it move to D

No new files. Verification only.

- [ ] **Step 1: Pick a known false-positive job from CVDIRECTOR's tracker**

```bash
D="/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/CoWork/CVDIRECTOR/.job-scout"
# A-tier or B-tier jobs in the post-migration tracker
jq -r '.jobs | to_entries | map(select(.value.tier == "A" or .value.tier == "B")) | .[0:5] | map({id: .key, title: .value.title, company: .value.company, location: .value.location})' "$D/tracker.json"
```

Identify a job whose `location` clearly violates the user's `requirements.work_arrangement` or location preferences (e.g. an A-tier in `Boston, MA` when the user is NL-based remote-or-hybrid).

- [ ] **Step 2: Run `/match-jobs` on that single job's ID**

In a Claude Code session inside the CVDIRECTOR workspace: `/match-jobs <job-id>`.

- [ ] **Step 3: Verify the job is now D-tier with gate_violations populated**

```bash
D="/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/CoWork/CVDIRECTOR/.job-scout"
JID="<the id from step 1>"
jq --arg j "$JID" '.jobs[$j] | {tier, tier_reason, gate_violations, dimensions, rubric_version}' "$D/tracker.json"
```

Expected: `tier: "D"`, `tier_reason: "gated: ..."`, `gate_violations` non-empty, `dimensions: {}` (empty because gated), `rubric_version: "v1"`.

- [ ] **Step 4: Open the rendered report and confirm UX**

The job should appear under "Filtered out" with the gated banner showing the violation kind(s).

- [ ] **Step 5: Try a known A-tier (non-gated) job and confirm dimension table renders**

Pick a job whose attributes pass gates. Run `/match-jobs <id>`. Confirm the report card shows all five dimensions with tiers and evidence quotes.

- [ ] **Step 6: Sign-off — log results in chat**

If both smoke checks pass on CVDIRECTOR, repeat on CVFREELANCER. If both workspaces pass, Phase 1 accuracy core is done.

---

## Task 27: Update ROADMAP.md — Phase 5 section

**Files:**
- Modify: `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout/docs/ROADMAP.md`

- [ ] **Step 1: Branch**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout" && git checkout main && git pull --rebase && git checkout -b phase-5/task-27-roadmap
```

- [ ] **Step 2: Add the Phase 5 row to the status table**

Find the status table in `docs/ROADMAP.md` and add a new row:

```markdown
| **5. Foundations + Accuracy core** | v0.8.0 | In flight | [`specs/2026-05-26-phase-0-1-foundations-and-accuracy-design.md`](superpowers/specs/2026-05-26-phase-0-1-foundations-and-accuracy-design.md) | [`plans/2026-05-26-phase-0-1-foundations-and-accuracy.md`](superpowers/plans/2026-05-26-phase-0-1-foundations-and-accuracy.md) |
```

Update **Current focus** to: `Phase 5 in flight — locking canonical schemas, migrating live state, rebuilding _job-matcher around hard gates + per-segment dimensions. Phases 6 (coverage + cadence), 7 (triage feedback UX), 8 (recruiter rebuild + tone propagation), 9 (nurture) follow.`

- [ ] **Step 3: Append a Phase 5 progress block**

After the existing Phase 4 block, add:

===FILE_START===

## Phase 5 — v0.8.0: Foundations + Accuracy core

Closes the spec↔reality gap (statuses, tiers, JD blobs, caches all silently broken in v0.7.0) and replaces the keyword-bingo rubric with a hard-gated, segment-aware, per-dimension matcher.

- [ ] **Canonical schemas reference** (`canonical-schemas.md`)
- [ ] **State validators reference** (`state-validators.md`)
- [ ] **JD storage reference** (`jd-storage.md`)
- [ ] **Workspace layout update** (`workspace-layout.md` — jds/, .backup/, schema-version)
- [ ] **Old schema docs point at canonical** (`tracker-schema.md`, `user-profile-schema.md`)
- [ ] **Voice profile reference** (`voice-profile.md`)
- [ ] **Live state backup** (both workspaces, pre-migration tarballs)
- [ ] **Tracker migration** (both workspaces, in-place, status/tier normalisation, schema_version: 2)
- [ ] **User-profile migration** (both workspaces, segment + tone + canonical requirements)
- [ ] **Threads migration** (CVDIRECTOR normalised, CVFREELANCER initialised)
- [ ] **JD persistence wired** (check-job-notifications + job-search)
- [ ] **Score cache contract enforced** (rubric_version in key)
- [ ] **CV parse cache contract enforced**
- [ ] **Archive pass scaffolding** (`archive-pass.md`)
- [ ] **Tone block populated** (both workspaces from voice spec)
- [ ] **Plugin version → 0.8.0-dev**
- [ ] **Phase 0 end-to-end verification**
- [ ] **`_gate-engine` skill** (skeleton + gate-rules reference)
- [ ] **`/analyze-cv` discovery interview** (segment + hybrid dealbreakers + tone confirmation)
- [ ] **Director-perm dimensions reference**
- [ ] **Freelance dimensions reference**
- [ ] **`_job-matcher` v0.2.0 rewrite** (segment-aware, gated, dimension-based)
- [ ] **`_gate-engine` wired into `/match-jobs` and `/check-job-notifications`**
- [ ] **Visualizer renders per-dimension breakdown + gated banner**
- [ ] **End-to-end smoke** (known false-positive → D-tier; known A-tier shows dimension table)
- [ ] **Phase 5 release** (bump 0.8.0-dev → 0.8.0, ROADMAP ticks, CHANGELOG dated)
===FILE_END===

- [ ] **Step 4: Verify**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
grep -q "Phase 5" docs/ROADMAP.md
grep -q "0.8.0" docs/ROADMAP.md
grep -c "^- \[ \] \*\*" docs/ROADMAP.md | awk '{ if ($1 >= 25) print "OK"; else print "FAIL: only " $1 " checkboxes" }'
```

- [ ] **Step 5: Commit**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
git add docs/ROADMAP.md
git commit -m "ROADMAP: add Phase 5 (v0.8.0) section"
git checkout main && git merge --no-ff phase-5/task-27-roadmap -m "Merge phase-5/task-27-roadmap"
```

---

## Task 28: Release — bump 0.8.0-dev → 0.8.0, tag, finalise CHANGELOG

**Files:**
- Modify: `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout/.claude-plugin/plugin.json`
- Modify: `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout/CHANGELOG.md`
- Modify: `/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout/docs/ROADMAP.md`

- [ ] **Step 1: Branch**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout" && git checkout main && git pull --rebase && git checkout -b phase-5/task-28-release
```

- [ ] **Step 2: Final state verification — both workspaces pass all checks**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
source <(grep -A40 'validate_tracker()' skills/shared-references/state-validators.md | sed -n '/^```bash$/,/^```$/{//d;p;}' | head -40)
source <(grep -A30 'validate_profile()' skills/shared-references/state-validators.md | sed -n '/^```bash$/,/^```$/{//d;p;}' | head -30)
source <(grep -A20 'validate_threads()' skills/shared-references/state-validators.md | sed -n '/^```bash$/,/^```$/{//d;p;}' | head -20)

for ws in CVDIRECTOR CVFREELANCER; do
  D="/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/CoWork/$ws/.job-scout"
  echo "=== $ws ==="
  validate_tracker "$D/tracker.json" && echo "tracker OK"
  validate_profile "$D/user-profile.json" && echo "profile OK"
  validate_threads "$D/recruiters/threads.json" && echo "threads OK"
done
```

Expected: all three "OK" prints per workspace.

- [ ] **Step 3: Bump version**

Edit `.claude-plugin/plugin.json`: `"version": "0.8.0-dev"` → `"version": "0.8.0"`.

- [ ] **Step 4: Date the CHANGELOG entry**

In `CHANGELOG.md`, change `## [0.8.0] — TBD` → `## [0.8.0] — 2026-05-26` (or actual ship date).

- [ ] **Step 5: Tick all Phase 5 checkboxes in ROADMAP.md**

Use `sed -i ''` (BSD sed on macOS) or manual edit to change `- [ ]` → `- [x]` for the Phase 5 block.

Also flip the table row: `In flight` → `Shipped — v0.8.0`.

- [ ] **Step 6: Verify**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
jq -r .version .claude-plugin/plugin.json
grep "## \[0.8.0\]" CHANGELOG.md
grep -c "^- \[x\] \*\*" docs/ROADMAP.md | awk '{ print "ticked: " $1 }'
```

Expected: version `0.8.0`; CHANGELOG dated; ticked count includes all Phase 5 items.

- [ ] **Step 7: Commit + tag**

```bash
cd "/Users/tura/Library/Mobile Documents/com~apple~CloudDocs/git/claude-job-scout"
git add .claude-plugin/plugin.json CHANGELOG.md docs/ROADMAP.md
git commit -m "Release v0.8.0 — foundations + accuracy core"
git checkout main && git merge --no-ff phase-5/task-28-release -m "Merge phase-5/task-28-release"
git tag v0.8.0
```

(Tag-push only with user approval — production host policy applies.)

---

# Self-Review

After completing the plan, the writer ran the self-review checklist:

**1. Spec coverage.** Every decision from the 2026-05-26 grilling session has a task: migrate-in-place (Task 9–11), hybrid dealbreaker elicitation (Task 20), per-segment dimensions (Task 21–22), evidence quotes + no aggregate number (Task 23), reject_reason field (Task 9 migration), tone everywhere user-voiced (Task 16, Task 7 reference, Task 23 _job-matcher inputs). Out of scope items (coverage adds, triage UX, recruiter rebuild, nurture, outbound) are explicitly listed as Phase 6+ in Task 1's design spec.

**2. Placeholder scan.** No "TBD", "implement later", "fill in details" anywhere. Migration scripts have full jq. Validators have full bash. Templates show full HTML.

**3. Type consistency.** `rubric_version` is the same key in: canonical-schemas.md, state-validators.md, jd-storage.md (no), tracker migration (Task 9), score cache (Task 13), `_job-matcher` (Task 23), visualizer (Task 25), lazy rescore (Task 23). `segment` consistent across canonical-schemas, validate_profile, /analyze-cv discovery, dimensions-{director-perm,freelance}, _job-matcher flow. `deal_breakers[].kind` enum consistent across canonical-schemas, validate_profile, /analyze-cv checklist, _gate-engine evaluation order.

---

# Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-05-26-phase-0-1-foundations-and-accuracy.md`.**

Two execution options:

**1. Subagent-Driven (recommended)** — controller dispatches a fresh subagent per task with two-stage review (correctness + style). Best for large plans with low intra-task coupling. Use `superpowers:subagent-driven-development`.

**2. Inline Execution** — execute tasks sequentially in this session with checkpoints. Use `superpowers:executing-plans`. Best when the user wants to watch each task land in real time.

The plan touches **live state on a production host** in Tasks 8–11 and 16. Both execution modes must pause for explicit user approval before any of those tasks runs.

Which approach?

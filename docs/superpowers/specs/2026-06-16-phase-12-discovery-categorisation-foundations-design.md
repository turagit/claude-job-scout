# Phase 12 — Discovery & Categorisation Foundations ("Phase A") Design Spec (v0.12.0)

**Status:** Drafted 2026-06-16 — **PARKED**. Design locked via `/grill-me` this session (every Decision below is a user-approved branch). Not yet scheduled for build; no implementation plan written yet.

> Numbering note: the queued Phases 8–10 (triage feedback, recruiter rebuild, nurture) remain deferred. This is **Phase A** of the discovery + categorisation improvement track surfaced by the post-v0.11.0 analysis; it follows Phase 11 (ultramode). Phases B (faceted opportunity-map / maturity bands / job "gettability") and C (reject-reason re-weighting / approved-job corpus boost / source-quality) are separate, later phases. Target release `v0.12.0`.

**Problem.** Discovery and matching are mature (Boolean title clusters, skill-combination queries from the JD-keyword corpus, query-stats learning, repost dedupe, and v0.11.0 ultramode multi-source). But the user's stated biggest remaining challenge is **unearthing the roles the candidate is a *great* match for**. Two leaks remain:

1. **"Right job, wrong words" (recall).** Great-fit roles are routinely written in different vocabulary — retitled, domain-jargon-rebranded, or described at the *function* level ("scale + availability + observability") rather than the *tool* level ("Kubernetes"). Lexical Boolean title/skill queries miss them (estimated ~20–30% of missed great-fits — directional, to be measured).
2. **Flat ranking (categorisation).** The report is a flat A/B/C list. It does not distinguish where the candidate is a **standout** (exceptional for the role) versus merely qualified, nor how **confident** each match is — so the bulletproof great-fits don't rise within their tier.

**Goal.** Ship `v0.12.0` that (a) **widens discovery** via a CV-derived **capability graph** + a **jargon/alias map** feeding the *existing* query plan, and (b) **sharpens categorisation** with a **parallel competitiveness signal** + **deterministic confidence/explanation tags** surfaced in the report — all **without** disturbing the v1 tier rubric, the score cache, or the dedupe-before-extract efficiency.

---

## Decisions

1. **Competitiveness is a PARALLEL signal, not a 6th rubric dimension.** The v1 tier rubric, its fixed load-bearing/modifying derivation table, and the score-cache key (`<job_id>:<cv_hash>:<profile_hash>:v1`) are **unchanged** — **no `rubric_version` bump, no forced re-score**. Competitiveness rides *beside* the A/B/C/D tier as additive metadata used for within-tier sorting and badges; it does not change what A/B/C mean.

2. **Competitiveness is judged by the matcher for A/B-tier jobs only; confidence + tags are deterministic.** Inside the existing batched scoring fan-out, `_job-matcher` emits `competitiveness: high | med | low` (+ one evidence quote) **only** for jobs that score A or B (skip gated-D and weak C). Separately, `confidence: high | med | low` and `match_explanation_tag` (`all-fit | one-gap | multiple-gaps | overqualified | underqualified | trajectory-concern`) are **deterministic** derivations from the per-dimension tiers — **no LLM call**. (Draft derivation, finalised in the plan: `all-fit` = all dims A; `one-gap`/`multiple-gaps` = exactly-one / ≥2 non-A dims; `trajectory-concern` = a D in a *modifying* dimension; `overqualified` = competitiveness `high` with a modifying-dim demotion; `confidence` = high when all load-bearing dims are A with ≤1 modifying gap, medium on a single load-bearing B, low when a C is present or ≥2 gaps.)

3. **The recall layer is QUERY-EXPANSION only.** The capability graph (functional / latent / adjacent capabilities) and the alias map (title/skill synonyms) emit a new **`capability` query family** into the plan. There is **no pre-scoring normalisation or early-filter** — the gate engine + rubric remain the *only* things that drop a job, and the LLM rubric already reads full JD text and resolves synonyms at scoring time. A lexical pre-filter would add false-positive risk (e.g. QA≠Quality) and could drop the very reworded roles we want to catch.

4. **`capability` queries run on all sweeps, capped and learning-gated.** They feed `/job-search`, `/deep-sweep`, and ultramode; capped at ~2–3 per run; subject to the **existing query-stats lifecycle** — a query with 3 consecutive zero-new runs **retires**; a query yielding ≥3 A/B-tier jobs **promotes** into its cluster. The exploratory footprint is therefore self-limiting: winners graduate into permanent clusters, losers die.

5. **The capability graph is built, proposed, and approved in `/analyze-cv`.** A new discovery step (between dimensions [3c] and clusters [3d]) runs one LLM pass over the CV to derive `{stated, latent, adjacent}` capabilities, **presented for approval/trim** — the same propose-then-approve pattern as dimensions, clusters, and the ultramode registry — then cached to `.job-scout/cache/capability-graph.json` (keyed by `cv_hash`, rebuilt when the CV changes). The user vets which adjacencies widen the net, so a wrong inference can't quietly flood results. Existing workspaces auto-build on the first discovery run if the cache is absent, with a one-time "review these?" prompt (no need to redo `/analyze-cv` from scratch).

6. **The jargon/alias map is conservative and corpus-fed.** `.job-scout/cache/jargon-normalizer.json` (persistent) is seeded with a **hand-curated, human-reviewed** alias map (high-confidence title/skill synonyms only), grown from the `jd-keyword-corpus` and an LLM first-encounter expansion. It feeds the `capability` family and cluster expansion. Conservative seeding limits false-positive equivalences.

7. **Render: badges + within-tier confidence sort.** `_visualizer` adds **competitiveness + confidence + explanation-tag badges** to the Tier-1 job cards, and sorts **within each tier by confidence (high→med→low) then recency** — so the bulletproof standout matches rise to the top of their tier. Rendered through `_visualizer` per Hard Rule #8; British English.

## Schema impact

Additive; no migration; **no `rubric_version` bump**.

- **New caches:** `.job-scout/cache/capability-graph.json` (keyed by `cv_hash`; shape `{stated:[{skill,type,cv_evidence}], latent:[{capability,from_skills,cv_evidence}], adjacent:[{role_family,transferable_to,domain_bridge}]}`) and `.job-scout/cache/jargon-normalizer.json` (persistent alias map). Both deletable/regenerable.
- **`query-stats.json`** gains the `capability` family under the existing retire/promote lifecycle (no schema change beyond a new `family` value).
- **Tracker job entry + score-cache value object** gain additive optional fields: `competitiveness` (`high|med|low|null`), `competitiveness_evidence` (`string|null`), `confidence` (`high|med|low|null`), `match_explanation_tag` (`enum|null`). The **score-cache key is unchanged** (`…:v1`); pre-Phase-A entries simply lack these fields and gain them **lazily** on the next scoring — no forced re-score.
- **`user-profile.json.dimensions[]` is UNCHANGED** (competitiveness is not a dimension); the capability graph lives in cache, not the profile.

## Workstream map

| # | Workstream | Touches |
|---|---|---|
| W1 | Capability-graph build + propose/approve step + cache | `analyze-cv` (new step 3c↔3d), `canonical-schemas.md`, new cache |
| W2 | Jargon/alias map (seed + corpus growth + first-encounter expansion) | new `jargon-normalizer.md` reference, `jd-keyword-extraction.md`, new cache |
| W3 | `capability` query family + cap + query-stats integration | `linkedin-search.md`, `job-search`, `deep-sweep`, ultramode (`_source-sweep` query construction) |
| W4 | Competitiveness LLM axis (A/B only) + deterministic confidence/tag derivation + persist | `_job-matcher`, `_gate-engine` (untouched, confirm), `canonical-schemas.md` |
| W5 | Render: competitiveness/confidence/tag badges + within-tier confidence sort | `_visualizer` templates, `render-orchestration.md`, `component-library.md` |
| W6 | Docs + release v0.12.0 | `plugin.json`, `CHANGELOG.md`, `README.md`, `ROADMAP.md` |

## Out of scope (this phase)

Phase B (faceted opportunity-map, maturity bands, job "gettability"/applicant-count signal) and Phase C (reject-reason → dimension re-weighting, approved-job corpus boost, source-quality scoring) are separate later phases. Anything outside discovery+categorisation (warm-path/referral, apply mechanics, recruiter, interview, offer). External embeddings / vector DBs (constraint: "semantic" = LLM-as-judge + cached deterministic signals, no external ML service).

## Verification (for the eventual build)

No automated suite (per CLAUDE.md). Checks: `grep` that `rubric_version` stays `v1` and the score-cache key is unchanged (proves no cache invalidation); a deterministic-derivation unit-check of `confidence`/`match_explanation_tag` against a table of sample dimension-tier combinations; `jq`-validate a sample `capability-graph.json` + `jargon-normalizer.json`; `grep` that the recall layer adds queries only and no step *drops* a job pre-scoring; `python3`+`jinja2` render of the new badges + confirm within-tier confidence sort; confirm the `capability` family is capped and flows through query-stats retire/promote; British-English `grep -i` over new prose; full read-through of each touched SKILL.md for Hard-Rule and subagent-protocol conformance.

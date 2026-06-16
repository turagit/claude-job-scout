# Phase 12 — Discovery & Categorisation Foundations ("Phase A") Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `v0.12.0` that (a) widens discovery via a CV-derived **capability graph** + a **jargon/alias map** feeding the existing query plan as a new `capability` query family, and (b) sharpens categorisation with a **parallel competitiveness signal** + deterministic **confidence/explanation tags** surfaced in the report — without disturbing the v1 tier rubric, the score cache, or dedupe-before-extract.

**Architecture:** Markdown skill files + references + JSON state under `.job-scout/`. No test suite; verification = `jq`/`grep`/`python3`/`jinja2`. Everything here is **additive** — no `rubric_version` bump, no migration. "Semantic" = the Claude model judging + cached deterministic signals; **no external ML/embeddings**.

**Tech Stack:** Markdown skills, Jinja2-shaped templates, JSON state, `Agent` subagents (per `subagent-protocol.md`), the Chrome extension / read-only `WebFetch` lanes (unchanged from Phase 11).

**Design spec:** [`docs/superpowers/specs/2026-06-16-phase-12-discovery-categorisation-foundations-design.md`](../specs/2026-06-16-phase-12-discovery-categorisation-foundations-design.md) — decisions referenced as **D1–D7**.

**Roadmap:** [`docs/ROADMAP.md`](../../ROADMAP.md)

**Branching & merge order (revised after adversarial review):** one branch per task off `main` (`phase-12/task-NN-<slug>`), merged serially; **no task edits a file a later task created**. Foundations land first: schema (T1) → jargon map (T2) → capability graph (T3) → then consumers: capability query family (T4) → matcher fields (T5) → render + within-tier sort (T6) → release (T7) → smoke (T8). T4 depends on T2+T3; T5 depends on T1; T6 depends on T1+T5. Repo-relative paths throughout.

**Hard-rule conformance (every task):** additive only (no `rubric_version` bump; the v1 tier-derivation table and the score-cache **key** stay unchanged); commands keep `disable-model-invocation: true`; subagents follow `subagent-protocol.md` with explicit `allowed_tools`; internal skills `_`-prefixed; British English; Tier-1 job-card output renders via `_visualizer`; no `.job-scout/` committed. **Skill-description hygiene:** no angle-bracket tokens in any SKILL `description` frontmatter (the Phase-11 validation bug). **Schema-doc hygiene:** schema *examples* in references use real values inside code fences, never angle-bracket placeholders in prose.

**No-angle-bracket scanner (run in every task that adds/edits a SKILL, and in T8):**
```bash
python3 - <<'PY'
import re,glob
bad=0
for f in glob.glob('skills/*/SKILL.md'):
    m=re.match(r'^---\n(.*?)\n---', open(f,encoding='utf-8').read(), re.S)
    if not m: continue
    d=re.search(r'(?m)^description:\s*(.*(?:\n(?:[ \t]+.*|))*?)(?=\n[A-Za-z_-]+:|\Z)', m.group(1))
    for tg in re.findall(r'<[^>\n]+>', d.group(1) if d else ''): print('OFFENDER',f,tg); bad+=1
print('clean' if not bad else 'FAIL')
PY
```

**BE-CHECK:** `grep -niE "résumé|resume|reach out|circle back|touch base|optimize|analyze|organize|color|center|dialog|while we process" <files> | grep -viE "analyze-cv|/analyze|colour|behaviour" || echo "BE clean"`

---

## Task 1: Additive schema — scoring fields, dimension `type`, the two caches, `capability` family enum

**Files:** Edit `skills/shared-references/canonical-schemas.md`, `skills/shared-references/workspace-layout.md`, `skills/shared-references/state-validators.md`.

- [ ] **Step 1: Branch** `phase-12/task-01-schema`
- [ ] **Step 2: Additive scoring fields + reader contract (D1/D2).** Add to the tracker job entry AND the score-cache value object (NOT the key): `competitiveness` (enum high/med/low or null), `competitiveness_evidence` (string or null), `confidence` (enum high/med/low or null), `match_explanation_tag` (enum all-fit/one-gap/multiple-gaps/overqualified/underqualified/trajectory-concern or null). State explicitly: the score-cache **key stays the four-part `job_id`+`cv_hash`+`profile_hash`+`v1` form**; `rubric_version` stays `v1`; these fields are written **lazily** on next scoring and the key is **omitted entirely** (not written as null) for entries not yet populated. **Reader contract:** every reader/template MUST treat the keys as optionally-absent (Jinja `job.confidence` then `or ''`; Python `job.get('confidence')`) — never assume presence. The fields are optional additive, so the **tracker file `schema_version` is NOT bumped** (still v3).
- [ ] **Step 3: Dimension `type` for deterministic derivation (review fix).** Extend the `dimensions[]` entry with an optional `type` field, enum `load-bearing` or `modifying` (default when absent = `load-bearing`). This is what makes the T5 confidence/tag derivation deterministic for *custom* per-workspace rubrics. Additive + back-compatible (absent → load-bearing). Give a concrete `dimensions[]` example **in a code fence** showing the `type` field with real values (no angle-bracket placeholders).
- [ ] **Step 4: Two new caches.** Document `.job-scout/cache/capability-graph.json` (keyed by `cv_hash`; a cache envelope `{ schema_version, cv_hash, built_at, stated[], latent[], adjacent[] }` — the envelope fields are standard cache metadata; the spec's `{stated,latent,adjacent}` is the payload) and `.job-scout/cache/jargon-normalizer.json` (persistent: `{ schema_version, updated_at, aliases }` where `aliases` maps a canonical term string to a list of alias strings). Show both shapes **in code fences with real example values** (e.g. `"sre": ["site reliability engineer", "reliability engineer"]`), never angle-bracket placeholders. Add both to `workspace-layout.md`'s tree (regenerable/deletable caches).
- [ ] **Step 5: `capability` query family enum (review fix).** Update the `query-stats.json` `family` enum in `canonical-schemas.md` (currently `title | skill | synonym | explicit`) to add `capability`, and update the `family` check in `state-validators.md` to accept it. This task OWNS the enum bump (T4 assumes it is already done).

**Verification:**
```bash
grep -nE "competitiveness|competitiveness_evidence|confidence|match_explanation_tag" skills/shared-references/canonical-schemas.md
grep -niE "key stays|key.*unchanged|omitted entirely|job.get|or ''|optionally-absent" skills/shared-references/canonical-schemas.md   # reader contract present
grep -nE "load-bearing|modifying" skills/shared-references/canonical-schemas.md                 # dimension type added
grep -nE "capability" skills/shared-references/canonical-schemas.md skills/shared-references/state-validators.md   # family enum bumped both places
grep -nE "capability-graph.json|jargon-normalizer.json" skills/shared-references/canonical-schemas.md skills/shared-references/workspace-layout.md
# schema-doc hygiene: no angle-bracket placeholder tokens in the new prose/examples
grep -nE "<[a-z_]+>" skills/shared-references/canonical-schemas.md && echo "FAIL: angle-bracket placeholder in schema doc" || echo "OK no placeholders"
# BE-CHECK over edited files
```

---

## Task 2: Jargon/alias map — seed + full write contract (seed ∪ corpus ∪ first-encounter)

**Files:** Create `skills/shared-references/jargon-normalizer.md`, `skills/shared-references/jargon-seed.json`. Edit `skills/shared-references/jd-keyword-extraction.md`.

- [ ] **Step 1: Branch** `phase-12/task-02-jargon`
- [ ] **Step 2: Seed map (D6).** Create `jargon-seed.json` — conservative, hand-curated, high-confidence-only title/skill synonyms (real JSON, e.g. `{"sre":["site reliability engineer","reliability engineer"],"platform engineer":["infrastructure engineer"],"backend":["back-end","server-side"]}`). Document it must be human-reviewed; no risky equivalences (e.g. do not alias "QA" to "Quality").
- [ ] **Step 3: Full write contract (D6, review fix).** In `jargon-normalizer.md`, specify the COMPLETE lifecycle of `.job-scout/cache/jargon-normalizer.json` so T4 can consume a well-defined cache: (1) **seeded** from `jargon-seed.json` on first use; (2) **grown** from the `jd-keyword-corpus` (new high-frequency terms become alias candidates); (3) **expanded** via a single LLM call on first encounter of a genuinely-new term, result cached. State the write is atomic (temp + rename per `state-validators.md`). State the **recall-only invariant (D3): the alias map only ever EXPANDS queries; it MUST NOT be used to drop/filter a candidate job** — the gate engine + rubric remain the only droppers.
- [ ] **Step 4: Corpus hook.** In `jd-keyword-extraction.md`, document the seam where a newly-extracted keyword triggers first-encounter alias expansion (bounded, cached) and feeds the alias map.

**Verification:**
```bash
python3 -c "import json; a=json.load(open('skills/shared-references/jargon-seed.json')); assert all(isinstance(v,list) and v for v in a.values()); print('seed OK', len(a),'terms')"
grep -niE "recall-only|MUST NOT.*drop|never.*drop|only.*expand" skills/shared-references/jargon-normalizer.md   # no-drop invariant explicit
grep -niE "seed|corpus|first encounter|first-encounter|atomic" skills/shared-references/jargon-normalizer.md      # full write contract
# BE-CHECK
```

---

## Task 3: Capability-graph build + propose/approve as a new `/analyze-cv` step

**Files:** Create `skills/shared-references/capability-graph.md`. Edit `skills/analyze-cv/SKILL.md`.

- [ ] **Step 1: Branch** `phase-12/task-03-capability-graph`
- [ ] **Step 2: `capability-graph.md` reference.** Document the build: one LLM pass over `cv_summary` + full CV text + the approved `dimensions[]`, producing the `{stated, latent, adjacent}` payload (Task 1 cache shape). **Bound `adjacent`:** every adjacent entry carries an explicit `domain_bridge` justification, so each adjacency is defensible and reviewable. Document how the graph + jargon aliases later form `capability` queries (T4 consumes it). No angle-bracket placeholders — examples in code fences.
- [ ] **Step 3: New `/analyze-cv` step (D5, review fix — explicit placement & atomic write).** Add a **new Step 3e** AFTER the existing query-cluster step (3d), so it can read the CV + the already-approved dimensions (and does not disturb 3c/3d numbering). It: builds the capability graph, **presents it for approval/trim** (same propose-then-approve UX as dimensions/clusters), and on approval writes `.job-scout/cache/capability-graph.json` (keyed by `cv_hash`) via the **atomic temp+rename** pattern, *immediately* on approval (not batched with the end-of-run profile write — so a later crash can't lose it). If the cache is absent at discovery time on an existing workspace, auto-build with a one-time "review these adjacencies?" prompt (no full `/analyze-cv` redo).
- [ ] **Step 4: Description hygiene.** Confirm the `/analyze-cv` `description` frontmatter is unchanged and contains no angle-bracket tokens (run the scanner).

**Verification:**
```bash
grep -niE "Step 3e|capability graph|capability-graph.json|approve|trim|review these adjacencies|atomic" skills/analyze-cv/SKILL.md
grep -niE "domain_bridge|stated|latent|adjacent|cv_hash" skills/shared-references/capability-graph.md
python3 -c "import json,sys; s=json.load(open('/tmp/capgraph-sample.json')); assert {'stated','latent','adjacent'} <= set(s); assert all('domain_bridge' in a for a in s['adjacent']); print('shape+bridge OK')"  # author /tmp sample per the doc
# run the no-angle-bracket scanner (above) → clean
# BE-CHECK
```

---

## Task 4: The `capability` query family — construction, cap enforcement, query-stats, all three surfaces

**Files:** Edit `skills/shared-references/linkedin-search.md`, `skills/job-search/SKILL.md`, `skills/deep-sweep/SKILL.md`, `skills/_source-sweep/SKILL.md` (ultramode keyword sweep).

- [ ] **Step 1: Branch** `phase-12/task-04-capability-queries`
- [ ] **Step 2: Define the family (D3/D4) + name the cap location.** In `linkedin-search.md` §3, add the `capability` family: built from the approved `capability-graph.json` (functional/latent/adjacent terms) **plus** `jargon-normalizer.json` aliases (the cache T2 built). Rendered in the existing Boolean grammar; tagged `family: "capability"`. **Cap = at most 3 capability entries per plan, enforced in the query-plan CONSTRUCTION step** (state this explicitly — the cap lives in plan assembly, not execution). Flows through the **existing** query-stats retire (3 zero-new) / promote (≥3 A/B → cluster) lifecycle. **Query-expansion only:** no pre-scoring filter; the gate engine + rubric stay the only droppers; scoring is family-agnostic (a capability-sourced job is scored exactly like any other — no family metadata is threaded into the matcher).
- [ ] **Step 3: Wire all three surfaces.** `/job-search`, `/deep-sweep`, and ultramode's keyword sweep (`_source-sweep`) each add the `capability` family to their plan by REFERENCE to `linkedin-search.md` (do not duplicate construction logic). Each respects the cap + query-stats ordering.
- [ ] **Step 4: Description hygiene.** `_source-sweep` `description` edited? Re-run the no-angle-bracket scanner (this is the file the Phase-11 bug was in).

**Verification:**
```bash
grep -niE "family.*capability|capability.*family|cap.*3|at most 3|enforced in.*construction" skills/shared-references/linkedin-search.md
grep -niE "query-expansion only|no pre-scoring|gate.*rubric.*only|family-agnostic" skills/shared-references/linkedin-search.md
grep -niE "capability" skills/job-search/SKILL.md skills/deep-sweep/SKILL.md skills/_source-sweep/SKILL.md   # ALL THREE surfaces
grep -niE "retire|promote" skills/shared-references/linkedin-search.md                                       # reuses existing lifecycle
# run the no-angle-bracket scanner → clean (regression guard on _source-sweep)
# BE-CHECK over edited files
```

---

## Task 5: Competitiveness axis (A/B only) + deterministic confidence/tag — emit AND write all four fields

**Files:** Edit `skills/_job-matcher/SKILL.md`, `skills/_job-matcher/references/dimensions-default.md`. Create `skills/_job-matcher/references/confidence-derivation-rules.json`.

- [ ] **Step 1: Branch** `phase-12/task-05-competitiveness`
- [ ] **Step 2: Competitiveness judgement (D2).** In the existing batched scoring flow, AFTER the per-dimension scoring derives the overall tier, **for jobs that are overall A or B only** (skip gated-D and C), emit `competitiveness` (high/med/low) + one `competitiveness_evidence` quote: does the candidate *exceed* the role's bar / are they a standout. **The tier-derivation table is UNCHANGED — competitiveness never feeds the tier (D1).**
- [ ] **Step 3: Deterministic confidence + tag, codified (D2, review fix).** Tag the 5 default dimensions in `dimensions-default.md` with their `type` (`load-bearing`: Skills & technical fit / Role shape match / Engagement fit; `modifying`: Domain & context / Trajectory fit). Author `confidence-derivation-rules.json` — a decision table mapping a dimension-tier profile (counts of A/B/C/D among load-bearing vs modifying dims) to `{confidence, match_explanation_tag}`, with a `test_cases[]` block of worked examples and the two enums. Document the rule in `_job-matcher`: it reads each dimension's `type` (absent → load-bearing) and computes `confidence`/`tag` **deterministically, no LLM call**. Examples: all dims A → `confidence: high`, `tag: all-fit`; one load-bearing B → `medium`, `one-gap`; any C → `low`; a D in a modifying dim → `tag: trajectory-concern`; competitiveness high with a modifying demotion → `tag: overqualified`.
- [ ] **Step 4: Emit AND persist ALL FOUR fields (review fix).** State explicitly that `_job-matcher` **writes** `competitiveness`, `competitiveness_evidence`, `confidence`, `match_explanation_tag` into the score-cache value + tracker entry (the deterministic two for every scored A/B/C job; competitiveness only for A/B). The cache **key construction is untouched** (still `…:v1`).

**Verification:**
```bash
grep -niE "A or B only|A/B-tier only|standout|exceed.*bar" skills/_job-matcher/SKILL.md
grep -niE "no LLM|deterministic|type.*load-bearing|modifying" skills/_job-matcher/SKILL.md
# competitiveness must NOT participate in tier derivation:
grep -niE "competitiveness" skills/_job-matcher/SKILL.md | grep -iE "tier|derive|overall|gate" && echo "FAIL: competitiveness in tier logic" || echo "OK competitiveness parallel"
# cache key never edited:
grep -nE "cache key|:v1|key *=" skills/_job-matcher/SKILL.md   # read-through confirms key format string unchanged
# derivation table is real + complete:
python3 -c "import json; r=json.load(open('skills/_job-matcher/references/confidence-derivation-rules.json')); tc=r['test_cases']; ce=set(r['confidence_enum']); te=set(r['tag_enum']); assert tc and all(c['expected_confidence'] in ce and c['expected_tag'] in te for c in tc); print(len(tc),'test cases OK')"
# the 5 default dims carry a type:
grep -nE "load-bearing|modifying" skills/_job-matcher/references/dimensions-default.md
# BE-CHECK; no-angle-bracket scanner
```

---

## Task 6: Render badges + within-tier confidence sort (commands sort; templates render)

**Files:** Edit the **job-card** views only: `skills/_visualizer/templates/{html,markdown}/{match-jobs,job-search,check-job-notifications,deep-sweep,ultramode}.j2`; `skills/_visualizer/references/component-library.md`; `skills/shared-references/render-orchestration.md`; and the payload-build step of the consuming commands `skills/{match-jobs,job-search,check-job-notifications,deep-sweep,ultramode}/SKILL.md`. Add example payloads under `skills/_visualizer/examples/`.

- [ ] **Step 1: Branch** `phase-12/task-06-render`
- [ ] **Step 2: Badges (D7), back-compat.** Render `competitiveness` + `confidence` + `match_explanation_tag` as chips on A/B-tier cards, reusing existing `.tag-chip`/`.score-pill` classes (no new CSS). Use safe-absent access (`job.confidence or ''`) so **pre-Phase-A entries with the keys absent render nothing and do not error**. Scope: **only the five job-card views** above — explicitly NOT `check-inbox` (recruiter threads), `funnel-report` (metrics), or `interview-prep` (packet), which render no job cards.
- [ ] **Step 3: Within-tier sort (D7) — in the COMMANDS (review fix).** The within-tier order (confidence high→med→low, then `posted_at` desc) is applied in each consuming command's **payload-build step**, before dispatching to `_visualizer`; the template renders in supplied order (mirrors the existing tier-order contract). Add the sort to the payload-build of `match-jobs`, `job-search`, `check-job-notifications`, `deep-sweep`, and ultramode. Document it in `render-orchestration.md`.
- [ ] **Step 4: Contract + two example payloads (review fix).** Update `render-orchestration.md` + `component-library.md` payload docs with the new optional fields. Create TWO example payloads: one **with** competitiveness/confidence/tags, one **pre-Phase-A without** them (keys absent).

**Verification:**
```bash
# both variants render without error (back-compat):
for p in with-tags pre-phase-a; do
 python3 -c "import jinja2,json; e=jinja2.Environment(loader=jinja2.FileSystemLoader('skills/_visualizer/templates/html')); out=e.get_template('match-jobs.html.j2').render(**json.load(open('skills/_visualizer/examples/match-jobs-$p.json'))); assert len(out)>150; print('$p renders', len(out))"
done
grep -niE "competitiveness|confidence|match_explanation_tag" skills/_visualizer/references/component-library.md skills/shared-references/render-orchestration.md
# the sort lives in the commands, not just the template:
grep -niE "confidence.*sort|sort.*confidence|within.tier.*confidence" skills/match-jobs/SKILL.md skills/job-search/SKILL.md skills/deep-sweep/SKILL.md skills/check-job-notifications/SKILL.md skills/ultramode/SKILL.md
# scope guard: no job-card badges leaked into non-job views
grep -lE "competitiveness" skills/_visualizer/templates/html/{check-inbox,funnel-report,interview-prep}.html.j2 2>/dev/null && echo "FAIL: badge in non-job view" || echo "OK scoped to job views"
# BE-CHECK
```

---

## Task 7: Docs + release v0.12.0

**Files:** Edit `.claude-plugin/plugin.json`, `CHANGELOG.md`, `README.md`, `docs/ROADMAP.md`.

- [ ] **Step 1: Branch** `phase-12/task-07-release`
- [ ] **Step 2:** Bump `plugin.json` → `0.12.0`.
- [ ] **Step 3: CHANGELOG** `## [0.12.0] — <date>`: Added — CV capability-graph + jargon recall layer (`capability` query family) across all sweeps; candidate-competitiveness (A/B-tier) + deterministic confidence/explanation tags with within-tier confidence sort. Changed — `dimensions[]` gains an optional `type` field (additive, default load-bearing); `query-stats` `family` gains `capability`. No `rubric_version` bump; no migration.
- [ ] **Step 4: README** — a short "Sharper matching & wider recall" subsection.
- [ ] **Step 5: ROADMAP** — flip Phase 12 row to *Shipped — v0.12.0 (smoke deferred to first real use)*; add a Phase 12 section + dated Log entry.

**Verification:** `test "$(jq -r .version .claude-plugin/plugin.json)" = "0.12.0"`; `grep -n "0.12.0" CHANGELOG.md`; ROADMAP row updated; BE-CHECK over additions.

---

## Task 8: End-to-end smoke — HARD gates vs SOFT (deferrable) gates

**HARD gates (non-deferrable — release blocks if any fail):**
- [ ] **H1 Additivity:** `rubric_version` still `v1`; score-cache **key format unchanged**; `dimensions[]` `type` is optional (absent → load-bearing). Grep + read-through prove no key mutation and no tier-derivation change.
- [ ] **H2 Deterministic derivation:** `confidence-derivation-rules.json` test-cases all pass; a sample of dimension-tier profiles maps to the documented `confidence`/`tag`.
- [ ] **H3 Back-compat render:** both example payloads (with / without the new fields) render with no error; absent fields render empty.
- [ ] **H4 Recall-only:** grep confirms the jargon map and capability family never drop a job (gate + rubric are the only droppers); capability cap ≤3 enforced in plan construction across all three surfaces.
- [ ] **H5 Description hygiene regression:** the no-angle-bracket scanner over all `skills/*/SKILL.md` is clean (guards the Phase-11 bug).
- [ ] **H6 Competitiveness parallel:** grep confirms `competitiveness` appears in no tier/derive/gate logic.

**SOFT gates (interactive; may defer to first real use, per the Phase 4/5 precedent):**
- [ ] S1 `/analyze-cv` proposes + writes an approved `capability-graph.json`; capability queries appear in `query-stats.json` with `family: "capability"`, obey the cap, and a deliberately-noisy one retires after 3 empty runs.
- [ ] S2 Scoring writes `competitiveness` (A/B only) + `confidence`/`tag` (A/B/C); the report shows the badges and within-tier confidence order; a pre-Phase-A entry still renders.

**Pass criteria:** all HARD gates green to tag the release; SOFT gates captured in merge notes or deferred to first real use. Capture the capability-graph + a rendered report screenshot.

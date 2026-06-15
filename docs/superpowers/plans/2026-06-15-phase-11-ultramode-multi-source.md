# Phase 11 — Ultramode: Multi-Source Discovery & Sweep Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `v0.11.0` with an opt-in **ultramode** that widens sourcing beyond LinkedIn into a per-workspace, CV-derived, verified source registry, sweeps those sources, and folds every job — regardless of source — into the existing tracker/scoring/render pipeline as one unified, tier-ranked report with a direct link per role. The LinkedIn core ships unchanged; ultramode defaults **off**.

**Architecture:** This plugin's "code" is markdown skill files, markdown references, and per-project JSON state under `.job-scout/`. Validation is manual via shell (`jq`, `grep`, `wc`, `python3`+`jinja2`) and end-to-end runs in a scratch workspace. Ultramode adds two internal subagents — `_source-discovery` (builds the verified `sources.json`) and `_source-sweep` (collects + dedupes + extracts per source) — both dispatched via the `Agent` tool per `skills/shared-references/subagent-protocol.md`. Sourcing over HTTP uses read-only `WebFetch`; the Chrome extension remains the only mechanism that touches the user's logged-in session. Scoring (`_job-matcher`/`_gate-engine`) and rendering (`_visualizer`) are **reused unchanged**.

**Tech Stack:** Markdown skill files; Jinja2-shaped templates; vanilla CSS + JS; JSON state; `Agent` (subagents) + `WebFetch` (read-only HTTP) + Claude Chrome extension (in-browser only).

**Design spec:** [`docs/superpowers/specs/2026-06-15-phase-11-ultramode-multi-source-design.md`](../specs/2026-06-15-phase-11-ultramode-multi-source-design.md) — decisions referenced as **D1–D10**.

**Roadmap:** [`docs/ROADMAP.md`](../../ROADMAP.md)

**Branching:** each task is one branch off `main` named `phase-11/task-NN-<short-slug>`, merged serially.

**Merge order & dependency rule (revised after adversarial review):** tasks merge **serially** in numerical order, and **no task edits a file created by a later task**. The orchestrating `/ultramode` command (Task 7) lands **after** the engines, priority logic, and view it calls (Tasks 3–6), so it never forward-references unbuilt artefacts. Priority/dedupe logic (Task 5) lives in the shared reference + `_source-sweep` — it does **not** edit the command. Key handling (D7) is folded into the command task (Task 7), not a post-hoc edit. All paths are repo-relative to the plugin root.

**Progress tracking:** after each task merges, tick its checkbox in `docs/ROADMAP.md`'s Phase 11 section (added by the release task).

**Hard-rule conformance (every task):** new browser work goes through the Chrome extension only (D1 carve-out covers read-only `WebFetch` for public HTTP); every command carries `disable-model-invocation: true`; subagents follow `subagent-protocol.md` **including an explicit `allowed_tools` list in the dispatch envelope**; internal skills are `_`-prefixed; all user-facing copy is British English (each task that touches user-facing text carries a British-English `grep -i` check); Tier 1 output renders via `_visualizer`. No `.job-scout/` content is committed.

**Conventions used by verifications below:**
- **Slug charset:** provider/board slugs are normalised at discovery to `[a-z0-9-]` (lowercase; `[^a-z0-9-]→-`; compress repeated `-`; trim). **No underscores inside a slug.**
- **External job ID:** `<provider>__<board>__<externalid>` — `__` (double underscore) is the only separator; since slugs never contain `_`, segments are unambiguous and collision-free. LinkedIn IDs stay bare numeric.
- **British-English grep (BE-CHECK):** `grep -niE "résumé|resume|reach out|circle back|touch base|optimize|analyze|organize|color|center|dialog|while we process" <files> || echo "BE clean"`

---

## Task 1: Schema foundation — structured `source`, namespaced IDs, `sources.json`, profile additions, migration

**Files:** Edit `skills/shared-references/canonical-schemas.md`, `skills/shared-references/workspace-layout.md`, `skills/shared-references/state-validators.md`. Create `skills/shared-references/sources-schema-example.json`.

- [ ] **Step 1: Branch** `phase-11/task-01-schema`
- [ ] **Step 2: Structured `source` + read shim (D-Schema).** Replace the six-value LinkedIn `source` enum with `source: { lane, provider, board }`. Define a canonical reader **`tracker_read_source(value)`** in `state-validators.md`: a bare legacy string `"Search"` lifts to `{lane:"linkedin", provider:"linkedin", board:"Search"}`; a structured value passes through. **Every** skill that reads `tracker.jobs[*].source` MUST call this shim. Document **lazy upgrade**: reads accept both shapes; on the next write of an entry it is rewritten structured; tracker file `schema_version` bumps v2 → v3 on first write.
- [ ] **Step 3: Namespaced IDs (collision-proof).** Document the slug charset + `__`-separated ID format above. Add the normalisation rule and state: tracker keys, `cache/scores.json` keys, and `jds/<id>.txt` paths all use the tracker entry's `id` **verbatim** — readers MUST NOT infer ID format (LinkedIn = numeric, external = namespaced). IDs are unique **within a source**, not globally; cross-source sameness is a fingerprint concern (Task 5), not an ID concern.
- [ ] **Step 4: `sources.json` schema (single workspace registry).** `{ schema_version, base_country, target_geography, priority_order[], backbone[], sources[] }` — **no top-level `lane`** (one registry per workspace holds mixed-lane sources). Each source = `{name, url, category, access_lane, endpoint, needs_key, needs_slug, priority, poll_method, notes, verified_at}`; `category ∈ {ats-provider, remote-board, aggregator, national-board, freelance-marketplace, community}`; `access_lane ∈ {api, rss, html, extension}`. Write `sources-schema-example.json` with 4 real sources (one ats, one remote-board, one aggregator, one freelance-marketplace) for use by validators.
- [ ] **Step 5: `user-profile.json` additions + migration.** Add `requirements.base_country: string|null` (default `null`), `requirements.target_geography: string|array|null`, and top-level `ultramode: { default:false, api_keys:{}, registry_built_at:null }`. The v2 → v3 workspace migration (document in `workspace-layout.md`) sets `base_country:null`; it is **only ever populated by onboarding (Task 7), never inferred**.
- [ ] **Step 6: Score-cache migration + template macro contract.** Document a v2→v3 cache step in `workspace-layout.md`: LinkedIn `scores.json` keys stay numeric; external entries score fresh (cache-miss is acceptable); no destructive rewrite required. Define a `source_chip(source)` macro contract (to live in `base.html.j2`/`base.md.j2`) that renders a structured `source` as a string chip — existing templates must stop rendering `{{ job.source }}` directly.

**Verification:**
```bash
python3 -c "import json,re; s=json.load(open('skills/shared-references/sources-schema-example.json')); \
assert all(x['access_lane'] in {'api','rss','html','extension'} for x in s['sources']); \
assert all(x['category'] in {'ats-provider','remote-board','aggregator','national-board','freelance-marketplace','community'} for x in s['sources']); \
assert all(len(x.get('endpoint','').strip())>0 for x in s['sources'] if x['access_lane'] in {'api','rss'}); \
assert 'lane' not in s; print('OK sources.json schema')"
# namespaced-ID round-trip + slug charset
python3 -c "import re; i='greenhouse__miro__4012345'; p=i.split('__'); assert len(p)==3 and all(re.fullmatch(r'[a-z0-9-]+',x) for x in p); print('OK id round-trip', p)"
grep -n "tracker_read_source" skills/shared-references/state-validators.md          # shim defined
grep -RnE "\{\{[^}]*\.source[^}]*\}\}" skills/_visualizer/templates/ && echo "FAIL: raw .source accessor remains; must use source_chip()" || echo "OK no raw source accessors"
```

---

## Task 2: Access-lane reference + browser-policy carve-out + machine-readable backbone + ATS resolver

**Files:** Create `skills/shared-references/ultramode-sources.md`. Edit `skills/shared-references/browser-policy.md`.

- [ ] **Step 1: Branch** `phase-11/task-02-sources-reference`
- [ ] **Step 2: `browser-policy.md` carve-out (D1).** Read-only `WebFetch` (public HTTP GET, no session, no automation framework) is permitted for ultramode source fetching and is **not** a violation of Hard Rule #1, which still governs all *in-browser* work; the Chrome extension stays the only mechanism touching the logged-in session; Playwright/Selenium/Puppeteer/headless/computer-use remain forbidden verbatim; login-walled sources use the **extension lane**, never credentialed HTTP scraping.
- [ ] **Step 3: Taxonomy & lanes.** Six categories; four access lanes with ingestion method — `api`→GET+parse JSON; `rss`→fetch+parse XML; `html`→fetch + **client-side full-text filter** (D9: never trust `category=`/`search=` params); `extension`→logged-in browser sweep with dedupe-before-extract.
- [ ] **Step 4: Universal backbone (D3) — machine-readable.** A `## Universal Backbone` section containing a fenced JSON array (occupation-agnostic, multi-country) that Task 3 ingests verbatim; mark each `needs_key`. National-board entries are resolved by `base_country`.
- [ ] **Step 5: ATS slug resolver (D9) — concrete algorithm.** Provide runnable pseudocode for probe-and-cache: derive candidate slugs from a company name → probe each provider's keyless endpoint (Greenhouse/Lever/Ashby/Workable/Recruitee/Personio/SmartRecruiters/Workday URL patterns, given in the spec validation) → cache `{company → provider, board}` in `.job-scout/cache/ats-slugs.json` → extension fallback on miss. Task 5 instantiates this directly.
- [ ] **Step 6: Cross-source dedupe + canonical (D6).** Fingerprint `lower(company)|lower(title)|lower(location)` with a documented location-normalisation rule; canonical preference **ATS > LinkedIn > aggregator > marketplace**; retain `also_seen_on[]`; when an aggregator hit's canonical is ATS, fetch the full JD from the ATS.

**Verification:**
```bash
python3 -c "import re,json; t=open('skills/shared-references/ultramode-sources.md').read(); \
m=re.search(r'## Universal Backbone.*?\`\`\`json(.*?)\`\`\`', t, re.S); b=json.loads(m.group(1)); \
assert isinstance(b,list) and all('needs_key' in x for x in b); print('OK backbone parseable', len(b))"
grep -nE "html.*client-side|client-side.*filter" skills/shared-references/ultramode-sources.md || echo "FAIL: html-lane client-side filter not documented"
grep -nE "extension.*login|login-walled.*extension" skills/shared-references/ultramode-sources.md || echo "FAIL: extension-lane login requirement not documented"
grep -niE "playwright|selenium|puppeteer|headless|computer use" skills/shared-references/browser-policy.md   # still forbidden
# BE-CHECK over both files
```

---

## Task 3: `_source-discovery` — verified fan-out engine that builds `sources.json`

**Files:** Create `skills/_source-discovery/SKILL.md`, `skills/_source-discovery/references/discovery-protocol.md`.

- [ ] **Step 1: Branch** `phase-11/task-03-source-discovery`
- [ ] **Step 2: Contract + dispatch envelope.** Internal `_`-prefixed subagent dispatched via `Agent` per `subagent-protocol.md` with **`allowed_tools: ["Read","Grep","WebFetch","WebSearch"]`** (web enumeration + live probing). Input: `{base_country, target_geography, work_arrangement, contract_type, field, cv_keywords[], user_sources[]}` — `field`/lane is a **single workspace-derived value**, one discovery dispatch per workspace. Output (delta-return): a verified `sources.json` fragment.
- [ ] **Step 3: Engine (D3).** Enumerate along independent axes (category · region/country led by `base_country` · occupation+synonyms · professional bodies · live web-search) → **live-probe + adversarially verify** each candidate before inclusion (live? carries lane roles? access lane + endpoint + needs_key/needs_slug) → **loop-until-dry** with a completeness critic → merge the parsed universal backbone (Task 2). **Hard invariant, stated explicitly in the SKILL.md:** nothing enters `sources.json` unverified, and the synthesis step uses ONLY confirmed candidates — it must not invent sources (logged lesson: an empty upstream makes a lone synth hallucinate).
- [ ] **Step 4: User sources (D4) + persistence.** `user_sources[]` probed, access-lane-classified, always retained (login-walled → extension lane). Writes `.job-scout/sources.json`; sets `ultramode.registry_built_at`. Re-runnable via `/ultramode sources`.

**Verification:**
```bash
# after a scratch dispatch produces .job-scout/sources.json:
python3 -c "import json; s=json.load(open('.job-scout/sources.json')); \
assert s['sources'] and all(x.get('access_lane') in {'api','rss','html','extension'} for x in s['sources']); \
assert all(len(x.get('endpoint','').strip())>0 for x in s['sources'] if x['access_lane'] in {'api','rss'}); \
print('OK discovery output', len(s['sources']),'sources')"
grep -niE "verified|live-probe|invent nothing|only.*confirmed|never.*unverified" skills/_source-discovery/SKILL.md
grep -n '"Read","Grep","WebFetch","WebSearch"\|allowed_tools' skills/_source-discovery/SKILL.md   # envelope documented
# BE-CHECK over skills/_source-discovery/
```

---

## Task 4: `_source-sweep` — per-source collect, dedupe-before-extract, score

**Files:** Create `skills/_source-sweep/SKILL.md`.

- [ ] **Step 1: Branch** `phase-11/task-04-source-sweep`
- [ ] **Step 2: Contract + dispatch envelope.** Internal `_`-prefixed subagent, **one dispatch per source**, with **`allowed_tools: ["Read","Grep","Write","WebFetch"]`**. Input: a single `sources.json` entry + lane keywords + the tracker snapshot. Honours the source's `access_lane` + `poll_method`. **Tracker-coordination:** the command loads `tracker.json` once and passes the candidate-fingerprint set to each subagent; subagents return **delta-only** new roles; the command merges deltas serially (no concurrent writes) — documented here and in Task 7.
- [ ] **Step 3: Dedupe-before-extract (Hard Rule #2).** Collect candidate IDs/fingerprints first → filter against the passed tracker set + cross-source fingerprints → fetch JD only for genuinely new roles → write `jds/<namespaced-id>.txt`, set structured `source` + namespaced id.
- [ ] **Step 4: Client-side filter (D9).** For `html`/feed sources, filter to lane relevance over full text (title+tags+description); do **not** rely on `category=`/`search=` params.
- [ ] **Step 5: ATS watchlist auto-seed (D9) + cold-start.** For `ats-provider` sources, build the watchlist from the tracker's A/B-tier employers + `requirements.companies_to_target[]` + manual; resolve slugs via the Task 2 resolver. **Cold-start:** with `< 1` A/B employer, seed from `companies_to_target[]` only and note the watchlist enriches after LinkedIn sweeps populate the tracker.
- [ ] **Step 6: Score.** New roles → `_job-matcher`/`_gate-engine` unchanged (batch per protocol).

**Verification:**
```bash
# live keyless smoke — endpoint reachable, JSON parseable, client-side filter yields infra-type roles, dedupe fields present
curl -sS -A "Mozilla/5.0" --max-time 30 "https://remoteok.com/api" -o /tmp/ro.json
python3 -c "import json,re; a=json.load(open('/tmp/ro.json'))[1:]; \
f=[j for j in a if re.search(r'devops|sre|platform|infrastructure|kubernetes|linux',(j.get('position','')+' '+' '.join(j.get('tags',[]))).lower())]; \
assert all(k in a[0] for k in ('id','company','position','url')); print('OK keyless smoke: %d filtered of %d, dedupe fields present'%(len(f),len(a)))"
grep -niE "dedupe|filter.*before.*(extract|fetch)|collect.*ids.*first" skills/_source-sweep/SKILL.md   # Hard Rule #2 ordering
grep -n '"Read","Grep","Write","WebFetch"\|allowed_tools' skills/_source-sweep/SKILL.md
# BE-CHECK over skills/_source-sweep/
```

---

## Task 5: Adaptive priority + cross-source dedupe + canonical (reference + sweep only)

**Files:** Edit `skills/shared-references/ultramode-sources.md`, `skills/_source-sweep/SKILL.md`. Create `skills/shared-references/examples/ultramode-dedupe-example.json`.

- [ ] **Step 1: Branch** `phase-11/task-05-priority-dedupe`
- [ ] **Step 2: Adaptive priority (D5).** Document deriving `priority_order` from `requirements` (`contract_type` · `work_arrangement` · `location_preferences`): freelance+remote → remote-board + contract-aggregator + freelance-marketplace first, ATS contract-filtered second; permanent → ATS-first. The sweep (Task 4) applies it; **no command-file edit** (the command reads the reference).
- [ ] **Step 3: Canonical selection (D6).** Implement in `_source-sweep`. Author `ultramode-dedupe-example.json`: three jobs, identical fingerprint, sources `{ats, linkedin, aggregator}`; the fixture encodes the resolved `canonical` (ats) and `also_seen_on[]` (the other two).

**Verification:**
```bash
python3 -c "import json; e=json.load(open('skills/shared-references/examples/ultramode-dedupe-example.json')); \
assert e['canonical']['source']['lane']=='ats'; assert sorted(x['lane'] for x in e['also_seen_on'])==['aggregator','linkedin']; \
print('OK canonical = ats, also_seen_on = 2')"
grep -niE "priority_order.*requirements|derive.*from.*requirements|not hardcoded" skills/shared-references/ultramode-sources.md
# BE-CHECK over edited files
```

---

## Task 6: Unified results view (report) — source-agnostic, tier-ranked, direct link

**Files:** Create `skills/_visualizer/templates/html/ultramode.html.j2`, `skills/_visualizer/templates/markdown/ultramode.md.j2`, and example payloads under `skills/_visualizer/examples/`. Edit `skills/_visualizer/SKILL.md`, `skills/_visualizer/references/component-library.md`, `skills/shared-references/render-orchestration.md`, plus `base.html.j2`/`base.md.j2` (add the `source_chip()` macro from Task 1).

- [ ] **Step 1: Branch** `phase-11/task-06-ultramode-view`
- [ ] **Step 2: View (D8).** One unified, **source-agnostic** list; source shown only as a **chip** (via `source_chip()`); ranked **tier A→B→C, freshest-first within tier**; each row a **direct link** to the canonical listing + "also seen on N"; gated jobs collapse into the existing "Filtered out" group. Reuse the theme tokens, tier pills, per-dimension table, "⚡ apply early" chip, toolbar. Add only: source chip, "also seen on N", apply-at-source CTA.
- [ ] **Step 3: Orchestration + data contract.** Add the `ultramode` view to `render-orchestration.md` (filename `ultramode-<YYYY-MM-DD>.html`, summary line); Hard Rule #8: `/ultramode` renders via `_visualizer`, never inline. Document the payload (same tier/dimension shape as `match-jobs`, plus `source:{lane,provider,board}` and `also_seen_on[]` per result). Commit example payloads: `ultramode-multi-source.json`, `ultramode-gated.json`, `ultramode-empty.json`, `ultramode-also-seen.json`.

**Verification:**
```bash
for f in multi-source gated empty also-seen; do
  python3 -c "import jinja2,json,sys; \
e=jinja2.Environment(loader=jinja2.FileSystemLoader('skills/_visualizer/templates/html')); \
t=e.get_template('ultramode.html.j2'); \
out=t.render(**json.load(open('skills/_visualizer/examples/ultramode-$f.json'))); \
assert len(out)>200; print('OK render $f', len(out),'bytes')"
done
grep -niE "source_chip" skills/_visualizer/templates/html/ultramode.html.j2   # uses macro, not raw .source
# BE-CHECK over templates + component-library.md
```

---

## Task 7: `/ultramode` command + first-run onboarding + `/config` toggle + key handling

**Files:** Create `skills/ultramode/SKILL.md`. Edit `skills/config/SKILL.md`, `skills/shared-references/ultramode-sources.md` (key-handling notes).

- [ ] **Step 1: Branch** `phase-11/task-07-ultramode-command`
- [ ] **Step 2: Frontmatter.** `name: ultramode`, `disable-model-invocation: true` (Hard Rule #4), British-English description. Sub-commands: bare (sweep), `sources` (re-run `_source-discovery`), `onboarding` (re-run lane interview).
- [ ] **Step 3: First-run onboarding (D4).** When `sources.json` is absent: read `cv_summary`/`target_titles`/`query_clusters`/`master_keyword_list`/`jd-keyword-corpus`; **ask `base_country` explicitly and confirm it back to the user out loud — never infer (not from email, not from CV alone)**; read `requirements` for `target_geography`/`work_arrangement`/`contract_type`/field and ask only for gaps; ask "which sources do you already use?" → `user_sources[]`. Dispatch `_source-discovery`, present the registry for approval, persist.
- [ ] **Step 4: Sweep flow.** Load `sources.json`; order via the reference's adaptive priority (Task 5); load `tracker.json` once; dispatch `_source-sweep` per source (Task 4) passing the fingerprint set; merge deltas serially; render via the `ultramode` view (Task 6).
- [ ] **Step 5: Key handling (D7).** Keyless-first: runs with zero keys. When discovery flags a keyed aggregator that materially helps the lane, prompt inline with the signup link and **gracefully skip** if declined (log `Skipped <provider> (no API key)` into the report). Keys live in `ultramode.api_keys` (gitignored) — **never** entered into a browser form. `/config` gains add/remove of a provider key and the `ultramode.default` toggle (default false).

**Verification:**
```bash
grep -n "disable-model-invocation: true" skills/ultramode/SKILL.md
grep -n "disable-model-invocation: true" skills/config/SKILL.md          # preserved after edit
grep -niE "infer|assume|detect.*from email|from the email" skills/ultramode/SKILL.md && echo "FAIL: inference language present" || echo "OK no inference language"
grep -niE "confirm.*base_country|base_country.*out loud|read.*back.*base_country|ask.*where.*based" skills/ultramode/SKILL.md || echo "FAIL: explicit base_country ask/confirm not found"
grep -niE "reuse|read.*cv_summary|master_keyword_list|jd-keyword-corpus" skills/ultramode/SKILL.md   # corpus reuse, no re-asking skills
grep -niE "Skipped.*no API key|gracefully skip|never.*browser form" skills/ultramode/SKILL.md
# BE-CHECK over skills/ultramode/
```

---

## Task 8: Wire `ultramode.default` into `/job-search` and `/deep-sweep`

**Files:** Edit `skills/job-search/SKILL.md`, `skills/deep-sweep/SKILL.md`.

- [ ] **Step 1: Branch** `phase-11/task-08-default-toggle-wiring`
- [ ] **Step 2: Widen-when-on (D2).** Both commands read `ultramode.default`; when `true`, after the LinkedIn sweep they also run the ultramode sweep (reusing Task 7's flow) and render the unified view; when `false` (default) behaviour is **byte-for-byte unchanged**. This is the explicit owner of the spec's "config toggle widens existing commands" commitment.

**Verification:**
```bash
grep -niE "ultramode\.default" skills/job-search/SKILL.md skills/deep-sweep/SKILL.md
# diff-guard: with ultramode.default false/absent, the pre-existing flow is unchanged (read-through + scratch run yields identical LinkedIn-only behaviour)
grep -n "disable-model-invocation: true" skills/job-search/SKILL.md skills/deep-sweep/SKILL.md   # preserved
# BE-CHECK over edited files
```

---

## Task 9: Docs + release v0.11.0

**Files:** Edit `.claude-plugin/plugin.json`, `CHANGELOG.md`, `README.md`, `docs/ROADMAP.md`.

- [ ] **Step 1: Branch** `phase-11/task-09-release`
- [ ] **Step 2: Bump** `.claude-plugin/plugin.json` → `0.11.0`.
- [ ] **Step 3: CHANGELOG** — one `## [0.11.0] - <date>` Keep-a-Changelog section (Added: opt-in ultramode, `/ultramode`, verified `sources.json`, unified source-agnostic tier-ranked report).
- [ ] **Step 4: README** — an Ultramode section (opt-in/off-by-default, `/ultramode`, source categories, keyless-first, base-country onboarding).
- [ ] **Step 5: ROADMAP** — flip the Phase 11 row to *Shipped — v0.11.0*; add a Phase 11 section + Log entry.

**Verification:**
```bash
test "$(jq -r '.version' .claude-plugin/plugin.json)" = "0.11.0" && echo "OK version"
grep -n "0.11.0" CHANGELOG.md
grep -niE "ultramode" README.md | head
# BE-CHECK over CHANGELOG.md README.md (Phase 11 additions)
```

---

## Task 10: End-to-end smoke (scratch workspace) — quantified gate

- [ ] **Step 1:** First-run `/ultramode`: onboarding asks `base_country` explicitly; `_source-discovery` produces a schema-valid, verified `sources.json` with **≥ 5 sources** for the lane; approve it.
- [ ] **Step 2:** Sweep: keyless sources fetched over `WebFetch`; dedupe-before-extract honoured; **≥ 10 roles** scored by the unchanged matcher and written to the tracker with structured `source` + namespaced ids; **zero duplicate fingerprints** in the final report.
- [ ] **Step 3:** Report: unified, source-agnostic, tier-ranked A→B→C; **every** non-gated role has a source chip and a direct "apply at source" link; gated jobs collapsed into "Filtered out" with a count; opens in Chrome via the extension (markdown fallback if HTML/open fails).
- [ ] **Step 4: Migration checks.** A v2 workspace upgraded to v3 has `requirements.base_country: null` and prompts on first `/ultramode`; `cache/scores.json` has no broken keys; `jds/` paths round-trip for both numeric (LinkedIn) and namespaced (external) ids.
- [ ] **Step 5: Toggle.** Set `ultramode.default` on → `/job-search`/`/deep-sweep` widen; off → core behaviour byte-for-byte unchanged.

**Pass criteria (the release gate):** Steps 1–5 all green; capture `sources.json` stats + a report screenshot in the merge notes. (Same deferral pattern as Phases 4/5 is permitted only for the interactive open-in-Chrome step; the data assertions above are not deferrable.)

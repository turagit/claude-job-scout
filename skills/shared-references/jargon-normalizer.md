# Jargon Normaliser (recall layer — seed, corpus growth, first-encounter expansion)

> **Single source of truth for the jargon/alias recall layer (Phase 12).** This reference defines how `.job-scout/cache/jargon-normalizer.json` is seeded, grown, and read — so the `capability` query family (built in `linkedin-search.md` §3) can consume a well-defined alias map. The cache **shape** is locked in `canonical-schemas.md` § `cache/jargon-normalizer.json`; this file owns its **lifecycle and invariants**.
>
> Companion references: `canonical-schemas.md` (the cache shape `{schema_version, updated_at, aliases}`), `jd-keyword-extraction.md` (the corpus that grows the map, plus the first-encounter expansion seam), `state-validators.md` (the atomic temp-then-rename write pattern), `linkedin-search.md` §3 (the `capability` query family that reads the map).

## What this is

A **persistent** alias dictionary mapping a canonical term to the surface forms hiring teams actually write. It powers jargon recall — letting a CV's "site reliability engineer" reach a JD that only ever says "SRE", and the other way round. Unlike `cache/capability-graph.json`, this file is **not keyed by `cv_hash`**: it accretes across runs and across a workspace's accumulated vocabulary. It is **regenerable and deletable** — it holds no source-of-truth state; deleting it is a cache miss that re-seeds on next use, never an error.

The on-disk shape (locked in `canonical-schemas.md`) maps a canonical term **string** to a **list of alias strings**:

```json
{
  "schema_version": 1,
  "updated_at": "2026-06-16T09:00:00Z",
  "aliases": {
    "sre": ["site reliability engineer", "reliability engineer"],
    "platform engineer": ["infrastructure engineer", "platform engineering"],
    "kubernetes": ["k8s", "container orchestration"]
  }
}
```

## The recall-only invariant (D3) — never a dropper

**The alias map only ever EXPANDS queries. It MUST NOT be used to drop, filter, normalise-away, or merge a candidate job.** Recall is its whole purpose: it adds surface forms to the search so reworded great-fit roles surface; it never subtracts.

- The map feeds the `capability` query family and cluster expansion in `linkedin-search.md` — it widens what is searched, nothing more.
- There is **no pre-scoring normalisation and no early lexical filter** anywhere in this layer. The **gate engine and the v1 rubric remain the only things that drop a job** — and the LLM rubric already reads full JD text and resolves synonyms at scoring time, so a lexical pre-filter would only add false-positive risk (the very reason the seed is conservative — see below) and could discard the reworded roles this layer exists to catch.
- Concretely: no consumer may use `aliases` to decide a candidate is "the same as" an existing one (that is the fingerprint/dedupe concern, handled in `linkedin-search.md` §5 and `ultramode-sources.md`), nor to reject a candidate whose JD vocabulary does not match an expected term. **Expand-only.** A reader that would drop a job on the strength of this map is a bug.

## The seed map — conservative, human-reviewed (D6)

`jargon-seed.json` (alongside this reference) ships a **hand-curated, high-confidence-only** alias map: title and skill synonyms that are genuinely interchangeable in hiring vocabulary. It is the cold-start content for `aliases`.

**Hard rules for the seed (and for anything that ever writes into the map):**

- **Human-reviewed only.** Every seed entry is reviewed by a person before it ships. The seed is not machine-generated; it is the trustworthy floor the corpus and first-encounter expansion build on top of.
- **High-confidence equivalences only — no risky pairs.** An alias must be a near-exact synonym that a recruiter would write interchangeably for the same role or skill. Spelling/orthography variants (`back-end` ↔ `backend`), well-known acronym pairs (`k8s` ↔ `kubernetes`, `sre` ↔ `site reliability engineer`), and settled title synonyms (`platform engineer` ↔ `infrastructure engineer`) qualify.
- **No broadening, no hypernyms, no risky abbreviations.** Do **not** alias `qa` to `quality` (quality is a far wider word than the QA role), do not alias a specific tool to its whole category beyond a settled industry shorthand, and do not chain weak associations. When in doubt, leave it out — a missing alias costs a little recall; a wrong one pollutes every future query that touches the canonical term. Because the layer is recall-only it can never *drop* a job, but a loose alias still wastes browser steps on off-lane results.

A worked slice of the seed:

```json
{
  "sre": ["site reliability engineer", "reliability engineer"],
  "backend": ["back-end", "server-side"],
  "ci/cd": ["continuous integration", "continuous delivery", "continuous deployment"],
  "kubernetes": ["k8s", "container orchestration"]
}
```

The seed file is `aliases`-shaped (canonical-term string → list of alias strings) but carries **no envelope** — it is the raw map only. The envelope (`schema_version`, `updated_at`) is added when the seed is lifted into the cache (below).

## Full write contract — the cache lifecycle (seed ∪ corpus ∪ first-encounter)

`.job-scout/cache/jargon-normalizer.json` is built and maintained by three additive sources, in order of trust. Each one only ever **adds** alias surface forms; nothing in the lifecycle removes a canonical term or shrinks a list (a stale alias costs nothing under the recall-only invariant). The `capability` query family (Task 4) consumes the result.

### 1. Seeded — from `jargon-seed.json` on first use

On the **first use** in a workspace (the cache file is absent — a cache miss, not an error), build it by lifting the seed:

1. Read `jargon-seed.json` (the raw `aliases`-shaped map).
2. Wrap it in the envelope — set `schema_version` to `1`, set `updated_at` to the current ISO8601 timestamp (for example `"2026-06-16T09:00:00Z"`), and place the seed map under `aliases`:

```json
{
  "schema_version": 1,
  "updated_at": "2026-06-16T09:00:00Z",
  "aliases": {
    "sre": ["site reliability engineer", "reliability engineer"],
    "backend": ["back-end", "server-side"]
  }
}
```

3. Write it atomically (below).

Deleting the cache and re-running re-seeds from the same trustworthy floor — so a corrupted or drifted cache is recovered by deletion.

### 2. Grown — from the `jd-keyword-corpus`

As the workspace ingests JDs, `.job-scout/cache/jd-keyword-corpus.json` accumulates the vocabulary the market actually uses (see `jd-keyword-extraction.md`). High-frequency corpus terms become **alias candidates**:

- A corpus keyword that is a known surface form of an existing canonical term (a spelling variant, an acronym/expansion pair, a settled title synonym) is added to that term's alias list, if not already present.
- Growth is **gated on corpus maturity** to keep noise out: only consider corpus terms once the corpus is ripe (the same `≥10 source jobs` threshold the skill family in `linkedin-search.md` §3b uses before trusting corpus-derived queries — below that the corpus is noise). A single rare term is never promoted.
- Growth is **monotonic and additive**: it appends surface forms to existing lists; it does not invent new canonical terms from raw corpus frequency alone, and it never deletes. The same conservatism as the seed applies — a corpus co-occurrence is a *candidate*, not a guaranteed synonym; only high-confidence equivalences are written.

### 3. Expanded — one LLM call on first encounter of a genuinely-new term

When the pipeline meets a **genuinely-new** term — one that is neither a canonical key nor a known alias in the cache, and not resolvable from the seed or corpus — it earns **one bounded LLM call** to propose its high-confidence aliases, and the result is **cached** so the term is never expanded twice:

- **Bounded and cached (first-encounter only).** The expansion fires **once per genuinely-new term**, on first encounter. Before calling, check the cache: if the term is already a canonical key or appears in any alias list, **skip the call** (cache hit). The expansion's result is written back, so the term is permanently resolved and the cost is paid at most once.
- **Conservative output.** The LLM is asked for **high-confidence synonyms only**, under the same no-risky-pairs rule as the seed (no hypernyms, no broadening, no `qa`→`quality`-class equivalences). A new canonical term plus its vetted aliases is added to `aliases`.
- **Recall-only, still.** The expanded entry widens future queries; it is never used to drop a candidate. If the LLM returns nothing high-confidence, the term is recorded with an **empty alias list** so the first-encounter call is not repeated — recall is unchanged, and the budget is spent once.

The detailed corpus/first-encounter **seam** — where in JD ingestion a newly-extracted keyword triggers this bounded, cached expansion and feeds the alias map — is documented additively in `jd-keyword-extraction.md`.

### Atomic write (per `state-validators.md`)

Every write to the cache — seed lift, corpus growth, first-encounter expansion — follows the **atomic temp-then-rename** pattern in `state-validators.md` § Atomic write pattern: build the full new file content in a temp file, then `mv` it over the target in one step. A partial or interrupted write never leaves a half-written cache on disk; the previous good file stays in place until the rename succeeds. `updated_at` is refreshed to the current ISO8601 timestamp on every write. The cache is workspace state under `.job-scout/cache/` and is gitignored like all `.job-scout/` state.

```
# Lifecycle, in one line each:
seed lift          : absent cache  -> wrap jargon-seed.json in envelope -> atomic write
corpus growth      : ripe corpus   -> append high-confidence surface forms to existing terms -> atomic write
first-encounter    : new term      -> cache miss -> one LLM call -> append term + vetted aliases (or empty list) -> atomic write
read (capability)  : load aliases  -> EXPAND queries only; never drop a job
```

## Reader contract

Consumers (today: the `capability` query family in `linkedin-search.md` §3, and cluster expansion) read the map defensively:

- **Absent file = cache miss, not error.** Seed it (step 1) or treat as an empty map for this run; never abort.
- **A canonical term with an empty alias list is valid** — it means "expanded, genuinely no high-confidence synonyms" (mirrors the absent-vs-null distinction the score cache draws in `canonical-schemas.md`). Skip it for expansion; do not re-expand.
- **Expand-only at read time.** Use `aliases` to add OR-terms to a query group; never to filter, dedupe, or reject. The recall-only invariant binds every reader.

## Consumers

- `linkedin-search.md` §3 — the `capability` query family folds the canonical term's aliases into the Boolean OR-group it builds (Task 4 consumes this cache). Capped, query-stats-governed, expand-only.
- `jd-keyword-extraction.md` — both grows the map (corpus terms → alias candidates) and hosts the first-encounter expansion seam (Task 4). Additive to existing corpus behaviour.

## Token cost

Near-zero on the steady path. The seed lift is a file copy. Corpus growth is a JSON read-merge-write over data already in context (the corpus is loaded for scoring anyway) — no LLM call. The only LLM cost is the **one bounded first-encounter call per genuinely-new term**, cached permanently thereafter, so a maturing workspace pays steadily less as its vocabulary settles.

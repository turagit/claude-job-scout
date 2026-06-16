# CV Capability Graph (recall engine — derive, propose, cache)

> **Single source of truth for the CV capability graph (Phase 12).** This reference defines how `.job-scout/cache/capability-graph.json` is built, presented for approval, and read — so the `capability` query family (built in `linkedin-search.md` §3) can search beyond literal keyword overlap. The cache **shape** is locked in `canonical-schemas.md` § `cache/capability-graph.json`; this file owns its **build, the bounded-adjacency rule, and its read contract**.
>
> Companion references: `canonical-schemas.md` (the cache shape `{schema_version, cv_hash, built_at, stated, latent, adjacent}`), `jargon-normalizer.md` (the alias map the graph combines with to form `capability` queries in Task 4), `cv-loading.md` (`cv_hash` derivation and the CV parse cache), `state-validators.md` (the atomic temp-then-rename write pattern), `linkedin-search.md` §3 (the `capability` query family that reads the graph).

## What this is

A derived map of what the user's CV can **credibly speak to** — not just the literal terms on the page. It exists so discovery and search can reach the great-fit roles that a pure keyword match misses: roles worded around an implied skill, or a one-hop-adjacent role the user could step into. It is the **recall engine** behind the `capability` query family.

It is a **regenerable, deletable cache keyed by `cv_hash`**. If the CV changes the hash changes and the graph is rebuilt; deleting the file simply forces a rebuild on next use. Its absence is a cache miss, never an error. It holds no source-of-truth state — `user-profile.json` remains canonical for the CV summary and the approved dimensions.

The graph has three bands, in descending order of how literally the CV evidences them:

- **`stated`** — capabilities the CV names outright: the literal skills, tools, and named techniques on the page. Highest confidence; a recruiter reads these directly off the document.
- **`latent`** — capabilities strongly implied by the stated ones but not named. Someone who ran on-call rotations for a payments platform latently knows incident response even if those words never appear; a chef who lists a tasting-menu role latently knows menu costing and brigade leadership. Each latent entry must trace back to specific stated evidence.
- **`adjacent`** — neighbouring capabilities a short, defensible hop away that the user could credibly grow into, or that a recruiter would read across to. **Every adjacent entry is bounded by an explicit `domain_bridge`** (below) — the one-sentence justification that names the hop. No free-floating adjacencies.

## The build — one LLM pass

The graph is built in a **single LLM pass** over three inputs, all already in context during `/analyze-cv`:

1. `cv_summary` from `user-profile.json` (`key_skills`, `technologies`, `seniority`, `years_experience`, `target_roles`, `domain_expertise`, `industries`).
2. The **full CV text** (the parsed text from the CV parse cache under `cache/`, the `cv-` file keyed by `cv_hash` — e.g. `cache/cv-a1b2c3.json`, per `cv-loading.md`) — so the pass sees named techniques, contexts, and achievements the denormalised summary drops.
3. The **approved `dimensions[]`** from `user-profile.json` (Step 3c of `/analyze-cv`) — so the adjacencies are pulled towards this workspace's lane rather than wandering into unrelated fields.

The pass emits the `{stated, latent, adjacent}` payload directly. One pass, not three — the bands are derived together so `latent` can lean on `stated` and `adjacent` can be checked against both. The whole graph is small (tens of entries, not hundreds): the point is recall lift on the roles a keyword match misses, not an exhaustive ontology.

**Prompt shape (the one pass):**

> Given this CV summary, full CV text, and the approved scoring dimensions, list what this candidate can credibly speak to, in three bands. `stated`: capabilities named outright on the CV. `latent`: capabilities strongly implied by the stated ones but not named — each must trace to specific CV evidence. `adjacent`: capabilities one short, defensible hop away that the candidate could credibly grow into or that a recruiter would read across to — each must carry a one-sentence `domain_bridge` naming the hop from a stated/latent capability. Stay inside this workspace's lane (the dimensions and segment). Prefer omission to a weak entry: a missing capability costs a little recall; a wrong one wastes browser steps on off-lane roles.

## Bounded adjacency — the `domain_bridge` rule (defensible by construction)

`adjacent` is the band most likely to drift, so it is the most tightly bounded. **Every adjacent entry is an object carrying a `domain_bridge`** — a single sentence that names the bridge from a `stated` or `latent` capability to the adjacent one. The bridge is what makes each adjacency **reviewable and defensible**: at approval time the user reads the bridge and keeps or trims the entry on its strength, rather than guessing why the graph proposed it.

- **One hop only.** The bridge must connect to something the CV already evidences (a `stated` or `latent` band entry). No chains — do not bridge from one adjacent capability to a further adjacent one. Two hops out is a different career, not an adjacency.
- **Named, not generic.** "Could probably learn it" is not a bridge. The sentence must name the concrete overlap — the shared tool, transferable practice, or sector read-across that carries the candidate across the gap.
- **Inside the lane.** The hop lands somewhere this workspace's `dimensions[]` and `segment` would actually search. An adjacency into an unrelated field is omitted even if technically defensible.
- **Prefer omission.** When the bridge would be a stretch, leave the entry out. The graph is recall lift, not aspiration — and because the downstream `capability` family is recall-only (it never drops a job, only widens the search), a thin adjacency costs nothing but wasted browser steps on off-lane results.

The `stated` and `latent` bands are plain capability strings; only `adjacent` entries carry the `domain_bridge`. A worked adjacency, showing the bridge tracing back to evidence:

```json
{
  "capability": "platform engineering",
  "domain_bridge": "CV states Terraform and AWS Lambda in production and latently shows infrastructure-as-code ownership; platform engineering is the team-facing extension of that same toolchain."
}
```

## Worked example — a full graph

A complete `capability-graph.json` for a backend/SRE-leaning CV, with every band populated and every adjacency bridged:

```json
{
  "schema_version": 1,
  "cv_hash": "a1b2c3d4e5f6",
  "built_at": "2026-06-16T09:00:00Z",
  "stated": ["python", "postgresql", "aws lambda", "terraform", "on-call rotation"],
  "latent": ["incident response", "infrastructure as code", "cost optimisation"],
  "adjacent": [
    {
      "capability": "kubernetes",
      "domain_bridge": "CV states containerised AWS Lambda services and Terraform-managed infrastructure; Kubernetes is the orchestration step recruiters routinely read across to from that container-plus-IaC base."
    },
    {
      "capability": "platform engineering",
      "domain_bridge": "Stated Terraform and Lambda plus latent infrastructure-as-code ownership bridge to platform engineering, which is the team-facing extension of the same self-service tooling."
    },
    {
      "capability": "data engineering",
      "domain_bridge": "Stated PostgreSQL at scale plus Python pipelines bridge to data engineering; the SQL-modelling and batch-Python skills transfer directly to ETL ownership."
    }
  ]
}
```

The `stated` and `latent` strings are lowercased surface terms (so they fold cleanly into Boolean OR-groups downstream); the `adjacent` objects carry a human-readable bridge sentence in addition to the lowercased `capability` term.

## How the graph forms `capability` queries (Task 4 consumes this)

The capability graph is one of the two inputs to the **`capability` query family** added to `linkedin-search.md` §3 (Task 4) — the other is the jargon alias map (`jargon-normalizer.md`). Task 4 is where they combine; this section documents the seam so the contract is clear.

For each capability the family decides to search:

1. Take the capability term from the graph — a `stated`, `latent`, or `adjacent` `capability` string.
2. Fold in its surface forms from the jargon alias map: look the term up in `cache/jargon-normalizer.json` `aliases` and OR-group it with every alias. So `kubernetes` becomes `("kubernetes" OR "k8s" OR "container orchestration")` when the alias map carries those forms.
3. Anchor the group to the lane the way the skill family does (§3b) — a context term drawn from the `segment` or a cluster label — so a broad capability does not pull in off-lane roles.

```
graph term        : "kubernetes"  (adjacent, bridged)
jargon aliases     : kubernetes -> ["k8s", "container orchestration"]
capability query   : ("kubernetes" OR "k8s" OR "container orchestration") AND (<lane anchor>)
query-stats family : "capability"
```

**Recall-only, governed, and band-ordered.** The `capability` family is **expand-only** — exactly like the jargon layer, it only ever widens the search; it never drops, filters, or dedupes a job (the gate engine and the v1 rubric remain the only things that drop a job). It is capped and query-stats-governed (§4), so an unproductive capability query retires like any other. The family searches the bands in confidence order — `stated` first, then `latent`, then the bridged `adjacent` entries last — so a rate-limit interruption costs the least-evidenced capabilities, not the best ones. Each capability query is recorded in `query-stats.json` under `family: "capability"` (the enum gained this value in `canonical-schemas.md` § Canonical enums).

## Read contract

Consumers (today: the `capability` query family in `linkedin-search.md` §3) read the graph defensively:

- **Absent file = cache miss, not error.** Auto-build it (see `/analyze-cv` Step 3e — the one-time review-the-adjacencies prompt) or treat as no capability queries for this run; never abort.
- **Stale by `cv_hash`.** If the on-disk `cv_hash` does not match the current CV's hash, the graph is stale — rebuild it. A graph built for a different CV is a cache miss, not a usable fallback.
- **`adjacent` entries are always objects with a `domain_bridge`.** A reader that meets a bare-string adjacent entry (or one missing its bridge) treats the file as malformed and rebuilds rather than searching an unbounded adjacency.
- **Expand-only at read time.** Use the bands to add OR-terms to the search; never to filter, dedupe, or reject a candidate. A reader that would drop a job on the strength of this graph is a bug.

## Atomic write (per `state-validators.md`)

Every write to the cache follows the **atomic temp-then-rename** pattern in `state-validators.md` § Atomic write pattern: build the full new file content in a temp file, then `mv` it over the target in one step. A partial or interrupted write never leaves a half-written graph on disk; the previous good file stays in place until the rename succeeds. The cache is workspace state under `.job-scout/cache/` and is gitignored like all `.job-scout/` state.

The write happens **immediately on the user's approval** in `/analyze-cv` Step 3e — not batched with the end-of-run profile write — so a later crash in the same run cannot lose an already-approved graph. `built_at` is set to the current ISO8601 timestamp on each build; `cv_hash` is copied from the CV the graph was built against.

```
# Lifecycle, in one line each:
build      : one LLM pass over cv_summary + full CV text + approved dimensions[] -> {stated, latent, adjacent}
approve    : user reviews + trims adjacencies -> approved payload
write      : atomic temp-then-rename to cache/capability-graph.json, immediately on approval, keyed by cv_hash
rebuild    : cv_hash changed OR file absent/malformed -> rebuild (auto-build offers a one-time adjacency review)
read (cap) : load bands -> fold in jargon aliases -> EXPAND queries only; never drop a job
```

## Token cost

One LLM pass per CV, cached permanently by `cv_hash`. The inputs (`cv_summary`, full CV text, `dimensions[]`) are already in context during `/analyze-cv`, so the build adds a single bounded call, not a fan-out. Every subsequent run on the same CV is a cache read. The auto-build fallback at discovery time pays the same single call once, then never again until the CV changes.

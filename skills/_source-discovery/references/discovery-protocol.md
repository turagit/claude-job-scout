# Discovery Protocol (for `_source-discovery`)

The full engine for the `_source-discovery` subagent: the enumeration axes, the live-probe/verify rubric, the loop-until-dry completeness critic, and how the universal backbone is ingested. Loaded by `../SKILL.md`. Read the **Hard invariant** in `../SKILL.md` first — everything here serves it.

> **One dispatch per workspace.** This protocol runs once per workspace, against a single `field` lane value derived from `user-profile.json`. It is not invoked once per occupation or once per lane. The enumeration axes below are how a *single* run achieves breadth.

## The loop at a glance

```
confirmed = []                       # the ONLY set synthesis may read
seen      = set()                    # candidate URLs already probed (no re-probe)

round = 1
while true:
    candidates = ENUMERATE(round, gaps)        # §1 — wide, may be speculative
    for c in candidates not in seen:
        seen.add(c.url)
        verdict = PROBE_AND_VERIFY(c)          # §2 — live, adversarial
        if verdict.admitted:
            confirmed.append(verdict.entry)    # classified, endpoint, lanes set
    gaps = CRITIC(confirmed, inputs)           # §3 — names what is still missing
    if round added 0 new confirmed AND gaps is empty:
        break
    round += 1

registry = MERGE_BACKBONE(confirmed)           # §4 — backbone read verbatim
fragment = SYNTHESISE(registry)                # §5 — reads confirmed ONLY
```

Nothing reaches `confirmed` without passing §2. `SYNTHESISE` reads `confirmed` (plus the backbone) and nothing else — it never invents an entry to "round out" a thin lane.

---

## §1 — Enumerate (independent axes)

Generate candidate sources along these axes. Run them as **independent** generators and union the results — breadth comes from covering several axes, not from one deep one. This is the **only** stage permitted to name a source it has not yet confirmed; everything it names is a hypothesis until §2.

1. **Category axis.** Walk the six categories (`ats-provider`, `remote-board`, `aggregator`, `national-board`, `freelance-marketplace`, `community`) and ask "which concrete providers in this category plausibly serve this workspace?". ATS providers are per-company (resolved via the slug resolver in `../../shared-references/ultramode-sources.md`, seeded from target companies), so here enumerate the *companies* to resolve, not generic ATS names.
2. **Region / country axis.** Led by `base_country`, then each entry of `target_geography`. For each, enumerate that territory's notable national / public-sector / vertical boards. When `base_country` is null, skip country-pinned enumeration — do not guess a country.
3. **Occupation + synonyms axis.** Expand `field` into occupation synonyms and adjacent titles using `cv_keywords` (e.g. "backend software engineering" → "backend developer", "platform engineer", "Python developer"). Niche occupations have niche boards; the synonyms surface them.
4. **Professional-body axis.** For the occupation, enumerate professional associations, trade bodies, guilds, and institutes that run their own job boards (common in regulated or craft fields — engineering institutions, chef/hospitality guilds, healthcare colleges, legal societies). These are high-signal, low-noise sources standard aggregators miss.
5. **Live web-search axis.** Issue real `WebSearch` queries of the form *"best job boards for `<field>` in `<geography>`"*, *"`<occupation>` jobs `<country>` site list"*, *"`<professional body>` job board"*. Harvest concrete board names/URLs from the results. This axis catches sources the model would not recall and grounds enumeration in current, real listings.

Each candidate is a `{name, url_guess}` hypothesis. De-duplicate by normalised URL before probing; never re-probe a URL already in `seen`.

---

## §2 — Live-probe + adversarially verify (before inclusion)

Every candidate is probed **before** it can enter the confirmed-set. The probe is read-only (`WebFetch` for endpoints/pages, the carve-out in `../../shared-references/browser-policy.md`; `WebSearch` only to *find* a candidate, never to stand in for probing it). Be adversarial: assume a candidate is noise until the probe proves otherwise.

### Gate A — Is it live?

- `WebFetch` the homepage / candidate endpoint. A non-2xx, a parked-domain page, a redirect to an unrelated site, or an empty body fails the gate. Drop the candidate.

### Gate B — Does it carry roles for THIS lane?

- Confirm the source actually returns **current job postings** relevant to `field` / occupation synonyms — not an empty board, not a "no results" stub, not a marketing page, not a paywalled teaser with zero readable roles.
- For feeds/APIs: fetch the feed and confirm a non-empty array of postings whose text plausibly matches the occupation (apply a client-side full-text check — never trust a `category=`/`search=` URL parameter, **Decision 9** in `../../shared-references/ultramode-sources.md`).
- A board that is live but carries nothing for this lane fails Gate B and is dropped — it is not "kept just in case".

### Gate C — Classify access lane + resolve endpoint

For a candidate that passes A and B, observe (do not assume) its real polling shape and set the schema fields:

| Observation | `access_lane` | `endpoint` |
|---|---|---|
| A documented JSON endpoint returns a postings array | `api` | the JSON URL (non-empty, required) |
| A `…/rss`, `…/feed`, or `application/rss+xml`/`atom` feed exists | `rss` | the feed URL (non-empty, required) |
| Only a public HTML listing page exists | `html` | the listings URL (client-side filter; Decision 9) |
| The source needs a login to read its roles | `extension` | `""` (empty — logged-in sweep, dedupe-before-extract) |

- **Login-walled → `extension`, always.** Most freelance marketplaces and Slack/Discord communities sit behind a login. They are classified into the `extension` lane and **retained**, never dropped and never read by credentialed HTTP. The extension lane is load-bearing (`../../shared-references/ultramode-sources.md`).
- **`needs_key`** is `true` only if the probe shows the endpoint demands an API key/token (the key is later looked up in `user-profile.json` `ultramode.api_keys`). Keyless feeds are `false`.
- **`needs_slug`** is `true` for per-board sources — chiefly ATS providers where each query needs a company board slug (resolved via the ATS slug resolver).
- **Slugs** in `name`/provider follow the charset rule in `../../shared-references/canonical-schemas.md`: lowercase, `[^a-z0-9-]` → `-`, compress repeats, trim — **no underscores**.

### Admit

Only on passing A + B + C is a `sources[]` entry constructed — with a real `verified_at` (the probe time) — and appended to `confirmed`. Every field is sourced from the probe, never from prior knowledge of the provider.

---

## §3 — Loop until dry (completeness critic)

After each round, a **completeness critic** inspects `confirmed` against the inputs and produces an explicit list of named gaps. It is adversarial about coverage — its job is to find what is missing, not to declare victory early.

The critic names a gap when:

- A **category** has zero confirmed sources but the workspace plausibly has roles there (e.g. no `national-board` confirmed yet `base_country` is set; no `freelance-marketplace` yet `contract_type` includes `freelance`).
- A **geography** in `target_geography` has no confirmed source pinned to it.
- An **occupation synonym** or **professional body** from §1 has not yet been searched/probed.
- A **lane skew** looks wrong (e.g. only aggregators confirmed, no direct-to-employer ATS path for the target companies).

Each named gap **seeds the next enumeration round** — the critic hands §1 the specific axis+term to expand (e.g. "enumerate freelance marketplaces for `<field>` in `<base_country>`"). The loop terminates only when a full round adds **zero** new confirmed sources **and** the critic reports no actionable gaps. Genuinely dry lanes (the critic asked, §2 confirmed nothing) are recorded as a `lane_dry` entry in `errors[]` — **not** papered over with an invented source.

> **Budget interaction.** If the loop reaches `budget_lines` before going dry, stop, return `status: "partial"` with the current `confirmed` synthesised into the fragment and the critic's outstanding gaps in `errors[]`, and emit a `continuation_cursor`. The continuation picks the loop back up from the unexplored gaps. A partial result is still fully verified.

---

## §4 — Ingest the universal backbone

The backbone is the always-on, occupation-agnostic, multi-country safety net so even thin lanes get coverage before niche discovery.

1. **Read** the `## Universal Backbone` JSON array from `../../shared-references/ultramode-sources.md` **verbatim** (via `Read`). Do not retype it from memory — read the file.
2. **Normalise slugs** in each entry's `name`/provider to the canonical charset.
3. **Fill `{country}` placeholders** in `endpoint`/`url` from `base_country` (e.g. `gb`, `pt`, `nl`). When `base_country` is null, **skip** the national-board backbone entries that need a country — do not guess one.
4. **Keyed backbone entries** (e.g. Adzuna, Jooble) keep `needs_key: true`; their keys are looked up later in `user-profile.json` `ultramode.api_keys`. The backbone is the same whether or not a key is present — absence of a key is a poll-time concern, not a discovery-time drop.
5. **Union** the resolved backbone with `confirmed`. List the backbone source names in the registry's `backbone[]`. On a name/fingerprint clash between a discovered source and a backbone source, keep one entry (prefer the more direct-to-employer / better-classified one) and do not double-list.

The backbone is **read, not invented** — it lives in a versioned reference precisely so the engine never reconstructs it from memory.

---

## §5 — Synthesise (confirmed-set only)

Assemble the `sources_fragment` returned in the delta:

- **Source list** = the `confirmed` discovered sources + retained `user_sources[]`. The backbone is named in `backbone[]`; the dispatcher holds its bodies. (Whether the engine inlines resolved backbone bodies or only names them is the dispatcher's merge contract — either way the engine never *fabricates* a backbone entry.)
- **`priority` / `priority_order`** by canonical preference: `ats-provider` first, then `remote-board` / `national-board`, then `aggregator`, then `community`, then `freelance-marketplace` last (mirrors the canonical-selection order in `../../shared-references/ultramode-sources.md`). Lower `priority` number polls first.
- **Schema conformance.** Every entry matches the `sources.json` schema in `../../shared-references/canonical-schemas.md` exactly: `name`, `url`, `category` (six-value enum), `access_lane` (four-value enum), `endpoint` (non-empty for `api`/`rss`), `needs_key`, `needs_slug`, `priority`, `poll_method`, `notes`, `verified_at`. Compare against `../../shared-references/sources-schema-example.json` for the field shapes.

**Reaffirming the Hard invariant at the synthesis boundary:** `SYNTHESISE` reads `confirmed` and the read-from-file backbone — and nothing else. It does not consult the model's general knowledge of "boards that probably exist". An empty `confirmed` produces a fragment whose `sources[]` is empty (or user-sources-only), with the backbone carrying coverage and `errors[]` naming the dry lanes. Fabricating a plausible-looking entry to avoid an empty result is the prohibited failure mode this whole protocol exists to prevent.

---

## Worked shape (illustrative)

For a Portugal-based backend engineer wanting Portugal + remote-EU, permanent and freelance, a healthy confirmed-set after the loop might be: an ATS board or two for named target companies (`ats-provider`/`api`/`needs_slug`), a Portugal tech board such as the user's own Landing.jobs (`national-board`/`html`), a remote board confirmed live (`remote-board`/`api`), a freelance marketplace classified `extension` because it is login-walled, plus the backbone (Adzuna, Jooble, RemoteOK, EURES-PT, …). Every non-backbone entry carries a `verified_at` because it was probed; nothing is present because it "ought to be".

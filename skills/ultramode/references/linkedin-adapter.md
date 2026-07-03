# The LinkedIn adapter — LinkedIn as a registry source

LinkedIn is one source in the registry (`category: "linkedin"`), swept on the MAIN THREAD via the Claude Chrome extension (Hard Rule #1) by the dispatcher during `/ultramode` Step 4d. It produces exactly the envelope every other source produces — the engine neither knows nor cares that this one is special. What used to be `/deep-sweep`'s body lives here.

## Inputs (from the dispatcher)

The Step 4b snapshot path, the Step 1 lane corpus (`query_clusters[]`/`target_titles[]`, `lane_keywords[]`, `not_terms[]` incl. `requirements.exclusion_terms[]`), `requirements` (for the GATE_BLOCK semantics and filter-addressed URLs), and `.job-scout/cache/query-stats.json`.

## The sweep (query plan v2 — reference, do not duplicate)

1. **Build the plan** per `../../shared-references/linkedin-search.md` §3, exactly as `/job-search` Step 2's zero-arg branch: Boolean title-cluster queries (per-title fallback), 2–3 skill-combination queries when the corpus is ripe, the `capability` family per §3f (≤3, cache-miss ⇒ skip), geo iteration across `location_preferences[]`, ordering from query-stats (proven first, retired excluded).
2. **Run every query** filter-addressed per §1: encoded Boolean `keywords`, `f_TPR=r604800` (Past Week), `f_WT`/`f_JT` from requirements, `sortBy=DD`; pages 1–3, collect IDs per page. Confirm filter chips on the run's first query; on drift fall back to the UI for that filter and record it in the envelope's `errors[]`.
3. **Dedupe before extract** (Hard Rule #2): drop every ID in the snapshot's `known_ids`; drop repost fingerprints per §5 (a repost match bumps nothing here — record it in `counts.scanned` only). **Adaptive synonym rescue** per `/job-search` Step 3b: a `family: "title"` query yielding <5 new gets 2–3 synonym variants (max 3, never expand a synonym).
4. **Sweep the extra surfaces:** Top picks (`/jobs/collections/recommended/`, 2–3 scrolls) and Saved (`/my-items/saved-jobs/`, all), tagging `source.board` accordingly. Surface priority on duplicate sightings: `Top Picks > Saved > Search`.
5. **Extract each genuinely-new role** (open the listing): title, company, location, salary, posted_at, applicant count, URL, full JD text → `jds/<id>.txt` per `../../shared-references/jd-storage.md`; run JD keyword extraction per `../../shared-references/jd-keyword-extraction.md`. Apply the GATE_BLOCK drop-on-explicit rule (stated permanent/onsite/hybrid ⇒ count in `counts.dropped_explicit_violation`, do not extract); record honest `signals` for the rest.
6. **Write query-stats** per §4: per-query candidates/new counts now; after the dispatcher's Step 4f scoring, complete the tier-count writes, retirement (3 consecutive zero-new), and synonym promotion — the adapter owns both halves of the §4 lifecycle.

## The envelope

Same shape as every sweep (validated by `validate_delta.py` before merge): `status`, `counts` (`scanned` = every ID seen incl. known/reposts; `matched` = lane-relevant AND genuinely-new; `dropped_explicit_violation`; `returned`; `capped` — cap 60 for this source, disclosed), `deltas[]` with **bare numeric LinkedIn ids** (never namespaced — back-compat with the whole tracker), `url`, title/company/location, `source: {"lane": "linkedin", "provider": "linkedin", "board": "Search" | "Top Picks" | "Saved" | "Similar"}`, `fingerprint` via `bash <SCRIPTS>/fingerprint.sh`, `posted_at`, `jd_path`, `signals`, `tags`. Checkpoint stage: `sweep-linkedin`.

## Post-scoring similar-jobs expansion

Owned by `/ultramode` Step 4f.3 (one supplemental envelope, stage `sweep-linkedin-similar`, `board: "Similar"`, ≤5 per A-tier seed, one round only).

## Failure modes

Rate-limited mid-run → stop this source, emit the partial envelope with an `errors[]` entry naming the in-flight query, and let the run continue (the scorecard discloses it; the next run's snapshot dedupe makes the retry cheap). Not logged in → `errors[]` `{"code": "login_required", "message": "LinkedIn session not active — log in and re-run /ultramode linkedin"}`, zero counts, never prompt for credentials.

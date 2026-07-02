# Live acceptance — v0.14.0 (Deterministic engine spine)

The user-run smoke that flips Phase 14 from "built" to "shipped". It exercises the three headline mechanisms — **the scripted pipeline**, **always-render + resume**, and **the near-miss rail + `/bend`** — against the real CVFREELANCER workspace. Expect the full run to take 30–45 minutes; you can walk away, the checkpoints have you covered.

**Legend:** `slash` = type into Claude Code, run from the workspace folder; `$` = shell, run in the workspace terminal (or in Claude Code with a leading `!`). All `$` commands assume you are in the workspace root (`~/Library/Mobile Documents/com~apple~CloudDocs/CoWork/CVFREELANCER`).

---

## 0 · Setup (2 min)

1. Update the plugin to **v0.14.0** (pull/reinstall from `turagit/claude-job-scout`) and reload Claude Code.
2. Confirm the version and the new command are live:

```bash
$ git -C <plugin-repo> log --oneline -1          # expect: 2604114 Phase 14: ROADMAP status …
```
In Claude Code, type `/` — the command list should now include **`/bend`**.

3. Set a helper for the checks below:

```bash
$ TODAY=$(date +%F); WS=.job-scout; echo "$TODAY"
```

## 1 · The full run (30–45 min)

```slash
/ultramode
```

**Watch for (no action needed):** a resume-or-fresh announcement at the start; subagent sweeps validated as they return; the extension lane opening tabs for ~4 marketplaces (Malt/Toptal/Worksome-class — the rotation subset); a fetch-then-gate stage with a budget line; and at the end a summary line **plus scorecard disclosure lines** — every cap, skip, deferral, and rotation named. The report must open (or render as markdown) **even if some stage complained**.

### Pass gates (run after it finishes)

```bash
# G1 — every scored entry from this run has a persisted JD (the 2 July defect):
$ jq --arg t "$TODAY" '[.jobs[] | select(.first_seen==$t and .tier!="untiered" and .jd_path==null)] | length' $WS/tracker.json
# expect: 0

# G2 — zero prose source strings among this run's entries:
$ jq --arg t "$TODAY" '[.jobs[] | select(.first_seen==$t) | select((.source|type)=="string")] | length' $WS/tracker.json
# expect: 0

# G3 — all new external ids are namespaced provider__board__id:
$ jq --arg t "$TODAY" -r '[.jobs | to_entries[] | select(.value.first_seen==$t) | .key | select((test("^[0-9]+$")|not) and (test("^[a-z0-9-]+__[a-z0-9-]+__")|not))] | length' $WS/tracker.json
# expect: 0

# G4 — the run dir + scorecard exist; ≥3 marketplaces were actually picked for sweeping:
$ RD=$(ls -1dr $WS/cache/run/*/ | head -1); echo "$RD"; jq '.rotation.picked' "$RD/scorecard.json"
# expect: an array of ~4 marketplace names

# G5 — scorecard reconciles with the tracker (same new-role count):
$ jq '.tiers | add' "$RD/scorecard.json"; jq --arg t "$TODAY" '[.jobs[] | select(.first_seen==$t)] | length' $WS/tracker.json
# expect: the two numbers match

# G6 — nothing silent: every cap/skip/deferral is a disclosure line:
$ jq -r '.disclosures[]' "$RD/scorecard.json"
# expect: human-readable lines (or none if genuinely nothing was capped)

# G7 — detachering passes the gate (your 2 July ruling):
$ jq --arg t "$TODAY" -r '[.jobs[] | select(.first_seen==$t and ((.tier_reason // "") | test("detachering")))] | .[] | "\(.tier) \(.title) — \(.tier_reason)"' $WS/tracker.json
# expect: any detachering role at/above €750/day is NOT gated on contract_type

# G8 — near-misses exist as structured data (if the market produced any):
$ jq --arg t "$TODAY" '[.jobs[] | select(.first_seen==$t and .near_miss==true)] | length' $WS/tracker.json
# expect: ≥0; each such role appears in the report's "Near-misses — would you bend?" rail
```

**Overall pass:** G1–G3 are exactly 0, G4–G6 look sane, the report rendered, and the summary printed the scorecard lines.

## 2 · The kill-test (resume + always-render) (10 min)

1. Start a second run: `/ultramode`.
2. **Interrupt it** (Esc / stop the response) once you see the gate/score stage begin — after sweeps, mid-scoring.
3. Run `/ultramode` again.

**Pass:** it announces **resuming** (not a fresh start), skips the completed sweep stages, finishes, and **a report renders**. Verify the stages ledger:

```bash
$ RD=$(ls -1dr $WS/cache/run/*/ | head -1); jq '.stages' "$RD/manifest.json"
# expect: all stages "done", including "render"
```

## 3 · `/bend` (5 min)

Pick any id from the report's near-miss rail (G8 — skip this section if the rail is empty this week):

```slash
/bend <tracker-id>
```

**Pass:** one-line before/after (e.g. `Bent <id>: D (gated: contract_type) → A …`), and:

```bash
$ jq '.jobs["<tracker-id>"] | {tier, bent, near_miss, tier_reason}' $WS/tracker.json
# expect: tier = the rubric tier, bent: true, near_miss still true, tier_reason starts "bent: …"
```

## 4 · Report back

Paste into the dev session: the summary line + disclosures from §1, any gate (G1–G8) that failed with its output, whether §2 resumed and rendered, and the `/bend` before/after. Anything that failed becomes a v0.14.1 fix; a clean sheet flips the ROADMAP to **shipped** and counts as week 1 of the two-week Phase 15 publish gate.

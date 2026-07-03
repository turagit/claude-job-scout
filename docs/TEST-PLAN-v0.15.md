# Live acceptance — v0.15.0 (The ultramode merge)

Two halves: a **fresh-workspace end-to-end** (proves a stranger's first run works) and the **publish gate** (two consecutive clean weekly runs on both live workspaces). `slash` = Claude Code from the workspace; `$` = shell there.

## A · Fresh-workspace end-to-end (~1 h)

```bash
mkdir -p ~/job-hunt-fresh && cd ~/job-hunt-fresh && cp /path/to/your-cv.pdf .
```
Update the plugin to v0.15.0, reload, then in order:

1. `/analyze-cv` — the interview (segment, deal-breakers, dimensions, clusters, capability graph).
2. `/ultramode` — with NO registry it must announce the `/sources` interview first, run it (country question asked explicitly and read back — never guessed), build the registry through the gates (approval table with discovered counts), THEN sweep the full market and open one unified report with the scorecard.
   - `$ jq '.sources | length' .job-scout/sources.json` → ≥ 12; `$ jq '[.sources[] | select(.category=="linkedin")] | length'` → 1.
3. `/tune` — shows titles/keywords/gates; `/tune add title "Site Reliability Engineer"` → confirm line with `profile_hash old → new`; `/tune` again shows it.
4. `/deep-sweep` — prints the deprecation pointer, then runs the full-market sweep.
5. `/ultramode linkedin` — sweeps ONLY LinkedIn (no external sources in the scorecard; report renders; similar-jobs expansion fires for A-tier LinkedIn roles).
6. `/sources` then `/sources add <a board URL you use>` — the list renders with the LinkedIn row; the added board is probed, classified, and appears in the list immediately after.
7. `/tune add title "Platform Engineer"` then `/ultramode linkedin` — the announced query plan includes the new title (or its cluster).
8. `/config ultramode default true` — prints the retirement notice, writes nothing.

**Pass:** every step behaves as written; the report renders; no stage improvises.

## B · Publish gate (weeks 1–2)

On **CVFREELANCER** and **CVDIRECTOR**, once per week for two weeks:

```slash
/ultramode
```

After each run (workspace shell; `TODAY` = run date):

```bash
$ RD=$(ls -1dr .job-scout/cache/run/*/ | head -1)
$ jq '.stages.render' "$RD/manifest.json"                      # "done"
$ jq '.sources | keys | length' "$RD/scorecard.json"           # ≥ 15 sources swept (incl. "linkedin")
$ jq '.sources.linkedin' "$RD/scorecard.json"                  # LinkedIn counts present
$ jq -r '.disclosures[]' "$RD/scorecard.json"                  # every cap/skip named
$ jq --arg t "$TODAY" '[.jobs[] | select(.first_seen==$t and (.source|type)=="object" and .jd_path==null and (.tier=="A" or .tier=="B" or .tier=="C" or .near_miss==true))] | length' .job-scout/tracker.json   # 0
```

**Clean run** = render done, LinkedIn + externals in one scorecard, gates hold, runtime ≤ 45 min. Four clean runs (2 workspaces × 2 weeks) ⇒ the publish gate passes; the plugin goes to marketplace-readiness (Phase 16 opens with the WebFetch-cap fetch-runner investigation).

## C · Report back

Per run: the summary line, the disclosure list, runtime, and any gate failure with its output.

#!/usr/bin/env python3
"""Serial, schema-validating, atomic tracker merge. stdlib only.
Usage: merge_tracker.py --ws WS --tracker TRACKER --today YYYY-MM-DD delta.json [...]
Deltas merge in argument order (serial by construction). Any invalid delta
aborts the whole merge with the tracker untouched. Exit 0 on success with a
one-line JSON summary on stdout."""
import argparse, json, os, subprocess, sys, tempfile

RANK = {"ats": 0, "ats-provider": 0, "linkedin": 1, "national-board": 2, "remote-board": 2,
        "community": 2, "aggregator": 3, "freelance-marketplace": 4, "freelance": 4}
STATUSES = {"seen", "approved", "applied", "rejected", "skipped"}
TIERS = {"A", "B", "C", "D", "untiered"}
HERE = os.path.dirname(os.path.abspath(__file__))

def rank(source): return RANK.get((source or {}).get("lane", ""), 5)

def fp_of(company, title, location):
    out = subprocess.run(["jq", "-nr", "-L", os.path.join(HERE, "lib"),
                          "--arg", "c", company or "", "--arg", "t", title or "", "--arg", "l", location or "",
                          'include "fingerprint"; fp($c; $t; $l)'],
                         capture_output=True, text=True, check=True)
    return out.stdout.strip()

def live_fp_map(tracker_path):
    """One jq pass over the tracker: fingerprint -> first non-rejected entry id."""
    prog = ('include "fingerprint"; [.jobs | to_entries[] | .value '
            '| select((.status // "seen") != "rejected") '
            '| {id: .id, fp: fp((.company // ""); (.title // ""); (.location // ""))}]')
    out = subprocess.run(["jq", "-c", "-L", os.path.join(HERE, "lib"), prog, tracker_path],
                         capture_output=True, text=True, check=True)
    m = {}
    for row in json.loads(out.stdout):
        m.setdefault(row["fp"], row["id"])
    return m

def read_source(v):
    """The tracker_read_source shim: tolerate legacy prose strings on read.
    Every legacy string in live trackers is a LinkedIn surface (or a pre-Phase-14
    prose write) — rank it as linkedin so an aggregator can never 'upgrade' it."""
    if isinstance(v, dict): return v
    return {"lane": "linkedin", "provider": "linkedin", "board": str(v)[:60]}

def sighting(entry, src):
    tri = {k: src[k] for k in ("lane", "provider", "board")}
    own = {k: read_source(entry.get("source"))[k] for k in ("lane", "provider", "board")}
    seen = entry.setdefault("also_seen_on", [])
    if tri != own and tri not in seen: seen.append(tri)

def validate_final(t, ws):
    errs = []
    for k, j in t["jobs"].items():
        if j.get("id") != k: errs.append(f"jobs[{k}].id mismatch")
        if j.get("status") not in STATUSES: errs.append(f"jobs[{k}].status {j.get('status')!r}")
        if j.get("tier") not in TIERS: errs.append(f"jobs[{k}].tier {j.get('tier')!r}")
        jd = j.get("jd_path")
        if jd:
            rel = jd[len(".job-scout/"):] if jd.startswith(".job-scout/") else jd
            if not os.path.isfile(os.path.join(ws, rel)): errs.append(f"jobs[{k}].jd_path missing file {jd}")
    return errs

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ws", required=True); ap.add_argument("--tracker", required=True)
    ap.add_argument("--today", required=True); ap.add_argument("deltas", nargs="+")
    a = ap.parse_args()

    for d in a.deltas:  # gate: refuse unvalidated input, all-or-nothing
        v = subprocess.run(["python3", os.path.join(HERE, "validate_delta.py"), "--ws", a.ws, d],
                           capture_output=True, text=True)
        if v.returncode != 0:
            sys.stderr.write(f"REFUSED {d}:\n{v.stderr}"); sys.exit(1)

    t = json.load(open(a.tracker))
    jobs = t["jobs"]
    live_fp = live_fp_map(a.tracker)

    merged = seen_known = upgrades = collisions = 0
    merged_this_run = set()

    def new_entry(e):
        j = {"id": e["id"], "url": e["url"], "title": e["title"], "company": e["company"],
             "location": e.get("location", ""), "source": e["source"],
             "tier": "untiered", "tier_reason": None, "status": "seen",
             "first_seen": a.today, "last_seen": a.today,
             "jd_path": e.get("jd_path"), "tags": e.get("tags") or [], "notes": ""}
        if e.get("posted_at"): j["posted_at"] = e["posted_at"]
        if e.get("signals"): j["signals"] = e["signals"]
        return j

    for d in a.deltas:
        env = json.load(open(d))
        for e in env.get("deltas") or []:
            # authoritative recompute — the declared fingerprint is only a sweep-side dedupe aid
            fp = fp_of(e.get("company", ""), e.get("title", ""), e.get("location") or "")
            if e["id"] in jobs:  # known id: sighting only
                sighting(jobs[e["id"]], e["source"]); jobs[e["id"]]["last_seen"] = a.today
                seen_known += 1; continue
            if fp in live_fp:  # fingerprint collision
                inc_id = live_fp[fp]; inc = jobs[inc_id]
                better = rank(e["source"]) < rank(read_source(inc.get("source")))
                if better and inc_id in merged_this_run:
                    # both arrived this run: the better-ranked one BECOMES the entry,
                    # the earlier one is recorded as a sighting on it
                    j = new_entry(e)
                    j["also_seen_on"] = inc.get("also_seen_on") or []
                    sighting(j, read_source(inc.get("source")))
                    del jobs[inc_id]; merged_this_run.discard(inc_id)
                    jobs[e["id"]] = j; merged_this_run.add(e["id"]); live_fp[fp] = e["id"]
                elif better:
                    # pre-existing incumbent: ids are immutable — upgrade the apply URL only
                    inc["url"] = e["url"]
                    if not inc.get("jd_path") and e.get("jd_path"): inc["jd_path"] = e["jd_path"]
                    note = f"canonical upgraded to {e['source']['provider']} ({a.today})"
                    inc["notes"] = ((inc.get("notes") or "") + ("; " if inc.get("notes") else "") + note)
                    upgrades += 1
                    sighting(inc, e["source"]); inc["last_seen"] = a.today
                else:
                    sighting(inc, e["source"]); inc["last_seen"] = a.today
                collisions += 1; continue
            jobs[e["id"]] = new_entry(e)  # genuinely new
            live_fp[fp] = e["id"]; merged_this_run.add(e["id"]); merged += 1

    t["schema_version"] = 3
    t.setdefault("stats", {})["total_seen"] = len(jobs)
    t["stats"]["last_run"] = a.today

    errs = validate_final(t, a.ws)
    if errs:
        sys.stderr.write("MERGE ABORTED (validation):\n" + "\n".join(errs) + "\n"); sys.exit(1)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(a.tracker)), suffix=".tmp")
    with os.fdopen(fd, "w") as fh: json.dump(t, fh, indent=1, ensure_ascii=False)
    os.replace(tmp, a.tracker)
    print(json.dumps({"merged": merged, "collisions_also_seen": collisions,
                      "url_upgrades": upgrades, "skipped_known": seen_known}))

if __name__ == "__main__":
    main()

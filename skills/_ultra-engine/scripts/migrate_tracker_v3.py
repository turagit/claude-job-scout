#!/usr/bin/env python3
"""One-shot canonicalisation of a drifted tracker.json (Phase 17, D15). stdlib only.
Usage: migrate_tracker_v3.py --tracker tracker.json [--sources sources.json] [--dry-run]"""
import argparse, json, os, re, sys, tempfile
from datetime import datetime, timezone

STATUSES = {"seen", "approved", "applied", "rejected", "skipped"}
STATUS_AS_APPLIED = {"closed", "interviewing", "in_conversation", "awaiting_info"}
TIERS = {"A", "B", "C", "D", "untiered"}
KINDS = {"work_arrangement", "contract_type", "seniority_floor", "location", "industry", "company", "rate_floor", "salary_floor", "custom"}
BOARD_RULES = [(r"top.?pick|recommend", "Top Picks"), (r"saved", "Saved"), (r"similar", "Similar"),
               (r"inbox|recruiter", "Inbox"), (r"alert|notification", "Job Alert")]

def board_of(text):
    t = (text or "").lower()
    for rx, b in BOARD_RULES:
        if re.search(rx, t): return b
    return "Search"

def note(e, s):
    n = e.get("notes"); n = n if isinstance(n, str) else ""
    e["notes"] = (n + ("; " if n else "") + s) if s not in n else n

def date_only(v, fallback):
    if isinstance(v, str) and re.match(r"^\d{4}-\d{2}-\d{2}", v): return v[:10]
    return fallback

def slug(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())

def lane_for(provider, sources):
    p_slug = slug(provider)
    for s in sources:
        name = s.get("name") or s.get("provider") or ""
        n_slug = slug(name)
        if p_slug and n_slug == p_slug:
            return s.get("category") or "aggregator"
        if p_slug and len(p_slug) >= 6 and (n_slug.startswith(p_slug) or p_slug.startswith(n_slug)):
            return s.get("category") or "aggregator"
    return "aggregator"

def fix(key, e, sources, today, by):
    orig = json.dumps(e, sort_keys=True)
    if e.get("id") != key: e["id"] = key; by["id"] += 1
    src = e.get("source")
    if not (isinstance(src, dict) and all(isinstance(src.get(k), str) and src.get(k) for k in ("lane", "provider", "board"))):
        text = src if isinstance(src, str) else " ".join(str(v) for v in (src or {}).values()) if isinstance(src, dict) else ""
        parts = key.split("__")
        if len(parts) >= 2 and not key.isdigit():
            provider = parts[0]
            if len(parts) >= 3:
                board = parts[1]
            else:
                if isinstance(src, dict) and isinstance(src.get("board"), str): board = src["board"]
                elif text.strip() == "Inbox": board = "Inbox"
                else: board = "html"
            e["source"] = {"lane": lane_for(provider, sources), "provider": provider, "board": board}
            if isinstance(src, str) and src.strip().lower() not in (provider.lower(), board.lower()): note(e, f"source(legacy): {src.strip()}")
        else:
            b = board_of(text); e["source"] = {"lane": "linkedin", "provider": "linkedin", "board": b}
            if isinstance(src, str) and src.strip().lower() != b.lower(): note(e, f"source(legacy): {src.strip()}")
        by["source"] += 1
    st = e.get("status")
    if st not in STATUSES:
        note(e, f"status(legacy): {st}")
        if st in STATUS_AS_APPLIED:
            e["status"] = "applied"
        else:
            if st == "gated" and e.get("tier") in (None, "untiered"): e["tier"] = "D"
            e["status"] = "seen"
        by["status"] += 1
    if e.get("tier") not in TIERS: e["tier"] = "untiered"; by["tier"] += 1
    if e.get("rubric_version") not in ("legacy", "v1"): e["rubric_version"] = "legacy"; by["rubric_version"] += 1
    gv = e.get("gate_violations")
    if isinstance(gv, list):
        new = []
        for v in gv:
            if isinstance(v, str): new.append({"kind": v if v in KINDS else "custom", "detail": v})
            elif isinstance(v, dict): new.append({"kind": v.get("kind") if v.get("kind") in KINDS else "custom", "detail": str(v.get("detail", ""))})
            else: new.append({"kind": "custom", "detail": repr(v)})
        if new != gv: e["gate_violations"] = new; by["gate_violations"] += 1
    fs, ls = e.get("first_seen"), e.get("last_seen")
    nfs = date_only(fs, date_only(ls, today)); nls = date_only(ls, nfs)
    if (nfs, nls) != (fs, ls): e["first_seen"], e["last_seen"] = nfs, nls; by["dates"] += 1
    for f in ("employment_type", "rate_disclosed"):
        if f in e:
            if e[f] not in (None, ""): note(e, f"{f}: {e[f]}")
            del e[f]; by["adhoc_fields"] += 1
    if not isinstance(e.get("notes"), str): e["notes"] = ""
    return json.dumps(e, sort_keys=True) != orig

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--tracker", required=True); ap.add_argument("--sources"); ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    try:
        t = json.load(open(a.tracker))
    except (json.JSONDecodeError, ValueError) as e:
        print(f"migrate: bad input ({type(e).__name__})", file=sys.stderr)
        sys.exit(1)
    jobs = t.get("jobs")
    if not isinstance(jobs, dict): print("migrate: bad input (jobs is not an object)", file=sys.stderr); sys.exit(1)
    sources = []
    if a.sources and os.path.isfile(a.sources):
        try:
            sources = json.load(open(a.sources)).get("sources", [])
        except (json.JSONDecodeError, ValueError) as e:
            print(f"migrate: bad input (sources.json: {type(e).__name__})", file=sys.stderr)
            sys.exit(1)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    by = {k: 0 for k in ("id", "source", "status", "tier", "rubric_version", "gate_violations", "dates", "adhoc_fields", "skipped_non_dict")}
    n_before = len(jobs)
    non_dict_count = 0
    changed = 0
    for k, e in jobs.items():
        if isinstance(e, dict):
            if fix(k, e, sources, today, by): changed += 1
        else:
            non_dict_count += 1
            by["skipped_non_dict"] += 1
    if non_dict_count > 0: print(f"migrate: warning: {non_dict_count} non-dict entries left untouched", file=sys.stderr)
    if len(jobs) != n_before: print("migrate: entry count changed — aborting", file=sys.stderr); sys.exit(2)
    t["schema_version"] = 3
    backup = None
    if not a.dry_run:
        d = os.path.dirname(os.path.abspath(a.tracker)); os.makedirs(os.path.join(d, ".backup"), exist_ok=True)
        backup = os.path.join(d, ".backup", f"tracker.json.{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.pre-phase17.json")
        with open(a.tracker) as src, open(backup, "w") as dst: dst.write(src.read())
        fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
        with os.fdopen(fd, "w") as fh: json.dump(t, fh, indent=1, ensure_ascii=False)
        os.replace(tmp, a.tracker)
    print(json.dumps({"entries": n_before, "changed": changed, "by_rule": by, "backup": backup, "dry_run": a.dry_run}))

if __name__ == "__main__":
    main()

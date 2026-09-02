#!/usr/bin/env python3
"""The alert ledger (.job-scout/alerts.json). stdlib only, atomic writes.
Commands: plan | start | page | complete | prune  (see plan Task 4 for arguments)."""
import argparse, json, os, sys, tempfile
from datetime import date

REASONS = ("divider", "drift", "valve", "no_next")
COUNTS = ("cards_seen", "before_divider", "known", "reposts", "new")

def load(path):
    if not os.path.isfile(path): return {"schema_version": 1, "alerts": {}}
    with open(path) as fh: return json.load(fh)

def save(path, ledger):
    d = os.path.dirname(os.path.abspath(path)); os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    with os.fdopen(fd, "w") as fh: json.dump(ledger, fh, indent=1, ensure_ascii=False)
    os.replace(tmp, path)

def rec_of(alert, today, run_id):
    return {"keywords": alert["keywords"], "geo_id": alert.get("geo_id", ""), "since_epoch": alert["since_epoch"],
            "since": alert.get("since"), "params": alert.get("params", ""), "first_seen": today, "status": "partial",
            "last_page": 0, "stop_reason": None, "cards_seen": 0, "before_divider": 0, "known": 0, "reposts": 0, "new": 0,
            "run_id": run_id}

def main():
    try:
        ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
        p = sub.add_parser("plan"); p.add_argument("--ledger", required=True); p.add_argument("--alerts", required=True); p.add_argument("--today", required=True)
        s = sub.add_parser("start"); s.add_argument("--ledger", required=True); s.add_argument("--alert-json", required=True); s.add_argument("--today", required=True); s.add_argument("--run-id", required=True)
        g = sub.add_parser("page"); g.add_argument("--ledger", required=True); g.add_argument("--key", required=True); g.add_argument("--page", type=int, required=True)
        for c in COUNTS: g.add_argument("--" + c.replace("_", "-"), type=int, required=True)
        c = sub.add_parser("complete"); c.add_argument("--ledger", required=True); c.add_argument("--key", required=True); c.add_argument("--reason", required=True, choices=REASONS)
        r = sub.add_parser("prune"); r.add_argument("--ledger", required=True); r.add_argument("--today", required=True); r.add_argument("--days", type=int, default=30)
        a = ap.parse_args()

        try:
            L = load(a.ledger)
            if "alerts" not in L or not isinstance(L["alerts"], dict): raise ValueError("missing or invalid alerts dict")
            al = L["alerts"]
        except Exception as e:
            print(f"alerts_ledger: bad input ({e})", file=sys.stderr); sys.exit(1)

        if a.cmd == "plan":
            try:
                with open(a.alerts) as fh: parsed = json.load(fh)
                if "alerts" not in parsed or not isinstance(parsed["alerts"], list): raise ValueError("missing or invalid alerts list")
                parsed = parsed["alerts"]
            except Exception as e:
                print(f"alerts_ledger: bad input ({e})", file=sys.stderr); sys.exit(1)
            walk, skipped = [], 0
            for x in parsed:
                k = x["alert_key"]; cur = al.get(k)
                if cur is None: walk.append({"alert_key": k, "resume_page": 1, "status": "new"})
                elif cur["status"] == "complete": skipped += 1
                else: walk.append({"alert_key": k, "resume_page": int(cur.get("last_page", 0)) + 1, "status": "partial"})
            print(json.dumps({"walk": walk, "skipped_complete": skipped})); return

        if a.cmd == "start":
            try:
                with open(a.alert_json) as fh: x = json.load(fh)
                for req in ("alert_key", "keywords", "since_epoch"):
                    if req not in x: raise ValueError(f"missing {req}")
            except Exception as e:
                print(f"alerts_ledger: bad input ({e})", file=sys.stderr); sys.exit(1)
            k = x["alert_key"]
            if k not in al: al[k] = rec_of(x, a.today, a.run_id)
            else: al[k]["run_id"] = a.run_id
            save(a.ledger, L); print(json.dumps(al[k])); return

        if a.cmd in ("page", "complete"):
            if a.key not in al: print(f"alerts_ledger: unknown key {a.key}", file=sys.stderr); sys.exit(1)
            rec = al[a.key]
            if a.cmd == "page":
                for cnt in COUNTS: rec[cnt] = int(rec.get(cnt, 0)) + int(getattr(a, cnt))
                rec["last_page"] = a.page
            else:
                rec["status"] = "complete"; rec["stop_reason"] = a.reason
            save(a.ledger, L); print(json.dumps(rec)); return

        if a.cmd == "prune":
            try:
                today = date.fromisoformat(a.today)
            except Exception as e:
                print(f"alerts_ledger: bad input ({e})", file=sys.stderr); sys.exit(1)
            keep, pruned, malformed = {}, 0, 0
            for k, rec in al.items():
                try:
                    if "first_seen" not in rec: raise ValueError("missing first_seen")
                    first_seen = rec["first_seen"]
                    if (today - date.fromisoformat(first_seen)).days > a.days: pruned += 1
                    else: keep[k] = rec
                except Exception:
                    malformed += 1
            L["alerts"] = keep; save(a.ledger, L); print(json.dumps({"pruned": pruned, "kept": len(keep), "malformed": malformed}))
    except Exception as e:
        print(f"alerts_ledger: bad input ({e})", file=sys.stderr); sys.exit(1)

if __name__ == "__main__":
    main()

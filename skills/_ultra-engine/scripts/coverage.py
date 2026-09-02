#!/usr/bin/env python3
"""Per-alert coverage table for one run. stdlib only.
Usage: coverage.py --ledger alerts.json --run-id R --out coverage.json [--reposts reposts.json]"""
import argparse, json, os

KEYS = ("cards_seen", "before_divider", "known", "reposts", "new")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger", required=True); ap.add_argument("--run-id", required=True)
    ap.add_argument("--out", required=True); ap.add_argument("--reposts")
    a = ap.parse_args()
    alerts = json.load(open(a.ledger))["alerts"] if os.path.isfile(a.ledger) else {}
    rows = []
    for k, r in alerts.items():
        if r.get("run_id") != a.run_id: continue
        rows.append({"alert_key": k, "keywords": r.get("keywords"), "since": r.get("since"),
                     "pages_walked": int(r.get("last_page", 0)), "stop_reason": r.get("stop_reason"), "status": r.get("status"),
                     **{x: int(r.get(x, 0)) for x in KEYS}})
    rows.sort(key=lambda r: r["since"] or "", reverse=True)
    totals = {"alerts": len(rows), "complete": sum(1 for r in rows if r["status"] == "complete"),
              "partial": sum(1 for r in rows if r["status"] == "partial"), **{x: sum(r[x] for r in rows) for x in KEYS}}
    reposts = json.load(open(a.reposts)) if a.reposts and os.path.isfile(a.reposts) else []
    tmp = a.out + ".tmp"
    with open(tmp, "w") as fh: json.dump({"rows": rows, "totals": totals, "reposts_disclosed": len(reposts)}, fh, indent=1)
    os.replace(tmp, a.out)
    print(json.dumps(totals))

if __name__ == "__main__":
    main()

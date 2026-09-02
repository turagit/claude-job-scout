#!/usr/bin/env python3
"""D5 stop rules for one alert results page. stdlib only.
Usage: walk_stop.py --alert alert.json --page parsed.json --page-no N [--valve 10] [--model-says-match true|false]
Order: divider -> valve -> no_next -> drift. Never mid-page."""
import argparse, json, re, sys

STOP = {"and", "or", "not", "the", "contract", "remote", "hybrid", "onsite", "on-site", "freelance", "job", "jobs"}

def terms(keywords):
    return [t for t in re.findall(r"[a-z0-9][a-z0-9+#.-]{2,}", keywords.lower()) if t not in STOP]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--alert", required=True); ap.add_argument("--page", required=True)
    ap.add_argument("--page-no", type=int, required=True); ap.add_argument("--valve", type=int, default=10)
    ap.add_argument("--model-says-match", choices=["true", "false"])
    a = ap.parse_args()
    try:
        alert = json.load(open(a.alert)); page = json.load(open(a.page)); cards = page["cards"]
    except Exception as e:
        print(f"walk_stop: bad input ({e})", file=sys.stderr); sys.exit(1)
    out = {"stop": False, "reason": None, "needs_model_check": False, "undecided_ids": [], "matched_ids": []}
    def done(reason): out.update({"stop": True, "reason": reason}); print(json.dumps(out)); sys.exit(0)
    if page.get("divider_seen"): done("divider")
    if a.page_no >= a.valve: done("valve")
    if not page.get("has_next"): done("no_next")
    quals = set(alert.get("qualifiers") or [])
    if quals:
        out["matched_ids"] = [c["id"] for c in cards if c.get("workplace") in quals]
        if not out["matched_ids"]: done("drift")
        print(json.dumps(out)); return
    ts = terms(alert.get("keywords", ""))
    for c in cards:
        title = (c.get("title") or "").lower()
        if any(re.search(r"\b" + re.escape(t), title) for t in ts): out["matched_ids"].append(c["id"])
    if out["matched_ids"]:
        print(json.dumps(out)); return
    if a.model_says_match == "true":
        print(json.dumps(out)); return
    if a.model_says_match == "false": done("drift")
    out["needs_model_check"] = True; out["undecided_ids"] = [c["id"] for c in cards]
    print(json.dumps(out))

if __name__ == "__main__":
    main()

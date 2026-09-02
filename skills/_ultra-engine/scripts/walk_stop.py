#!/usr/bin/env python3
"""D5 stop rules for one alert results page. stdlib only.
Usage: walk_stop.py --alert alert.json --page parsed.json --page-no N [--valve 10] [--model-says-match true|false]
Order: divider -> valve -> no_next -> drift. Never mid-page."""
import argparse, json, re, sys

STOP = {"and", "or", "not", "the", "contract", "remote", "hybrid", "onsite", "on-site", "freelance", "job", "jobs"}

def terms(keywords):
    return [t for t in re.findall(r"[a-z0-9][a-z0-9+#.-]{2,}", keywords.lower()) if t not in STOP]

def validate(alert, page):
    if not isinstance(alert, dict): raise ValueError("alert must be a dict")
    if not isinstance(page, dict): raise ValueError("page must be a dict")
    if "cards" not in page: raise ValueError("page must have 'cards' key")
    if not isinstance(page["cards"], list): raise ValueError("page['cards'] must be a list")
    quals = alert.get("qualifiers")
    if quals is not None and not isinstance(quals, list): raise ValueError("alert['qualifiers'] must be a list or absent")
    kw = alert.get("keywords")
    if kw is not None and not isinstance(kw, str): raise ValueError("alert['keywords'] must be a string or absent")
    for c in page["cards"]:
        if not isinstance(c, dict): raise ValueError("each card must be a dict")
        if "id" not in c or not isinstance(c["id"], str): raise ValueError("each card must have a string 'id'")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--alert", required=True); ap.add_argument("--page", required=True)
    ap.add_argument("--page-no", type=int, required=True); ap.add_argument("--valve", type=int, default=10)
    ap.add_argument("--model-says-match", choices=["true", "false"])
    a = ap.parse_args()
    try:
        alert = json.load(open(a.alert)); page = json.load(open(a.page))
        validate(alert, page); cards = page["cards"]
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
    if not cards:
        print(json.dumps(out)); return
    if a.model_says_match == "true":
        print(json.dumps(out)); return
    if a.model_says_match == "false": done("drift")
    out["needs_model_check"] = True; out["undecided_ids"] = [c["id"] for c in cards]
    print(json.dumps(out))

if __name__ == "__main__":
    main()

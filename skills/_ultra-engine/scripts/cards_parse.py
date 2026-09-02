#!/usr/bin/env python3
"""Page dump -> card records. stdlib only.
Usage: cards_parse.py --surface alert|toppicks|saved [--today YYYY-MM-DD] < dump.json
Exit 0: {"surface","page","claimed_results","cards":[...],"divider_seen","cards_before_divider","has_next","note","dropped_bad_id","zero_cards"}
Exit 3: extractor_mismatch (page claims results, zero cards parsed). Exit 1: bad input.
With --today, each card also gets "posted_at": minutes/hours/"just now" -> today; "N day(s)" -> today-N;
"N week(s)" -> today-7N; "N month(s)" -> today-30N; unparseable/absent -> "". Without --today the key is absent."""
import argparse, json, re, sys
from datetime import date, timedelta

AGO_UNIT_RE = re.compile(r"^(\d+)\s+(second|minute|hour|day|week|month)s?\s+ago$", re.I)
JUST_NOW_RE = re.compile(r"^just now$", re.I)

def posted_at_for(posted_ago, today):
    if not today or not posted_ago:
        return ""
    s = posted_ago.strip()
    if JUST_NOW_RE.match(s):
        return today
    m = AGO_UNIT_RE.match(s)
    if not m:
        return ""
    n, unit = int(m.group(1)), m.group(2).lower()
    try:
        d = date.fromisoformat(today)
    except ValueError:
        return ""
    if unit in ("second", "minute", "hour"):
        return today
    if unit == "day":
        d -= timedelta(days=n)
    elif unit == "week":
        d -= timedelta(days=7 * n)
    elif unit == "month":
        d -= timedelta(days=30 * n)
    return d.isoformat()

ID_RE = re.compile(r"^\d{6,}$")
SAL_RE = re.compile(r"(\$|€|£|\bEUR\b|\bUSD\b|\bGBP\b|\bCHF\b|\bPLN\b).*(/hr|/hour|/day|/month|/yr|/year|per\s+(year|annum|month|day|hour)|p\.?a\.?)|\d+k\b.*(\$|€|£|\bEUR\b|\bUSD\b|\bGBP\b|\bCHF\b|\bPLN\b)|(/hr|/day|/month)\b", re.I)
POSTED_RE = re.compile(r"^Posted\s+(.+)$", re.I)
AGO_RE = re.compile(r"^\d+\s+(second|minute|hour|day|week|month)s?\s+ago$", re.I)
LOC_RE = re.compile(r"\((Remote|Hybrid|On-site)\)\s*$", re.I)
FLAGS = {"viewed": "Viewed", "promoted": "Promoted", "easy_apply": "Easy Apply",
         "early_applicant": "Be an early applicant", "reviewing": "Actively reviewing applicants"}
NOISE = {"·", "Verified job"}

def workplace(location):
    m = re.search(r"\((Remote|Hybrid|On-site)\)\s*$", location or "", re.I)
    if not m: return "unknown"
    return {"remote": "remote", "hybrid": "hybrid", "on-site": "onsite"}[m.group(1).lower()]

def parse_text(text):
    lines = [l.strip() for l in (text or "").split("\n")]
    lines = [l for l in lines if l and l not in NOISE]
    if not lines: return None
    title = lines[0]
    if title.startswith("Selected, "): title = title[len("Selected, "):]
    title = re.sub(r"\s*\(Verified job\)\s*$", "", title).strip()
    rest = lines[1:]
    if rest and re.sub(r"\s*\(Verified job\)\s*$", "", rest[0]).strip() == title: rest = rest[1:]  # aria twin
    rec = {"title": title, "company": None, "location": None, "workplace": "unknown", "salary_text": None,
           "posted_ago": None, "viewed": False, "promoted": False, "easy_apply": False, "early_applicant": False, "parse_warning": False}
    body = []
    for l in rest:
        hit = False
        for k, label in FLAGS.items():
            if l == label:
                if k != "reviewing": rec[k] = True
                hit = True; break
        if hit: continue
        m = POSTED_RE.match(l)
        if m: rec["posted_ago"] = m.group(1).strip(); continue
        if AGO_RE.match(l):
            if rec["posted_ago"] is None: rec["posted_ago"] = l
            continue
        if SAL_RE.search(l) and rec["salary_text"] is None: rec["salary_text"] = l; continue
        body.append(l)
    # Pattern-first location detection: find line ending with (Remote|Hybrid|On-site)
    location_by_pattern = None
    body_without_location = []
    for l in body:
        if LOC_RE.search(l):
            location_by_pattern = l
        else:
            body_without_location.append(l)
    if location_by_pattern:
        rec["location"] = location_by_pattern
        if body_without_location:
            rec["company"] = body_without_location[0]
    else:
        # Fall back to positional rule
        if body_without_location:
            rec["company"] = body_without_location[0]
        if len(body_without_location) > 1:
            rec["location"] = body_without_location[1]
    if rec["company"] is None or rec["location"] is None:
        rec["parse_warning"] = True
    rec["workplace"] = workplace(rec["location"])
    return rec

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--surface", required=True, choices=["alert", "toppicks", "saved"])
    ap.add_argument("--today", default=None)
    a = ap.parse_args()
    try:
        dump = json.load(sys.stdin); cards_in = dump.get("cards"); assert isinstance(cards_in, list)
    except Exception as e:
        print(f"cards_parse: bad input ({e})", file=sys.stderr); sys.exit(1)
    div = dump.get("divider_index"); divider_seen = isinstance(div, int)
    out, bad, seen = [], 0, set()
    for i, c in enumerate(cards_in):
        cid = str(c.get("id", ""))
        if not ID_RE.match(cid): bad += 1; continue
        if cid in seen: continue
        rec = parse_text(c.get("text", ""))
        if rec is None: bad += 1; continue
        seen.add(cid)
        rec.update({"id": cid, "surface": a.surface, "before_divider": (not divider_seen) or i < div})
        if a.today:
            rec["posted_at"] = posted_at_for(rec.get("posted_ago"), a.today)
        out.append(rec)
    claimed = dump.get("claimed_results"); claimed_n = 0
    if isinstance(claimed, str):
        m = re.match(r"^\s*([\d,]+)", claimed); claimed_n = int(m.group(1).replace(",", "")) if m else 0
    note = None
    if a.surface == "saved" and not out and (dump.get("saved_count") == 0): note = "saved_empty"
    if not out and claimed_n > 0:
        print(f"extractor_mismatch: page claims {claimed_n} results, parsed 0 cards ({dump.get('url','')})", file=sys.stderr); sys.exit(3)
    low_conf = sum(1 for r in out if r.get("parse_warning", False))
    print(json.dumps({"surface": a.surface, "page": dump.get("page", 1), "claimed_results": claimed, "cards": out,
                      "divider_seen": divider_seen, "cards_before_divider": sum(1 for r in out if r["before_divider"]),
                      "has_next": bool(dump.get("has_next")), "note": note, "dropped_bad_id": bad, "low_confidence": low_conf,
                      "zero_cards": len(out) == 0}, ensure_ascii=False))

if __name__ == "__main__":
    main()

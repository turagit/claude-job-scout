#!/usr/bin/env python3
"""notifications.js dump -> alert records. stdlib only. Usage: alerts_parse.py < dump.json
Exit 0 with {"alerts": [...], "dropped_duplicates": n}; exit 1 with one stderr line on bad input."""
import hashlib, json, re, sys
from datetime import datetime, timezone
from urllib.parse import urlsplit, parse_qsl, urlencode

DROP = {"currentJobId", "originToLandingJobPostings"}
BASE = "https://www.linkedin.com/jobs/search-results/?"

def qualifiers(keywords):
    k = keywords.lower(); q = []
    if re.search(r"\bremote\b", k): q.append("remote")
    if re.search(r"\bhybrid\b", k): q.append("hybrid")
    if re.search(r"\bon[- ]?site\b", k): q.append("onsite")
    return q

def parse_one(href, age_text):
    u = urlsplit(href)
    pairs = parse_qsl(u.query, keep_blank_values=True)
    q = dict(pairs)
    if q.get("alertAction") != "viewjobs" or "keywords" not in q or "f_TPR" not in q:
        return None
    m = re.match(r"^a(\d+)-?$", q["f_TPR"])
    if not m:
        return None
    epoch = int(m.group(1))
    keywords = q["keywords"]; geo = q.get("geoId", "")
    params = urlencode([(k, v) for k, v in pairs if k not in DROP])
    preview = [i for i in q.get("originToLandingJobPostings", "").split(",") if i]
    return {
        "alert_key": hashlib.sha1(f"{keywords}|{geo}|{epoch}".encode()).hexdigest()[:16],
        "keywords": keywords, "geo_id": geo, "since_epoch": epoch,
        "since": datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "params": params, "results_url": BASE + params,
        "preview_ids": preview, "qualifiers": qualifiers(keywords), "age_text": age_text or "",
    }

def main():
    try:
        dump = json.load(sys.stdin)
        links = dump["alerts"]
        assert isinstance(links, list)
    except Exception as e:
        print(f"alerts_parse: bad input ({e})", file=sys.stderr); sys.exit(1)
    seen, out, dups = set(), [], 0
    for item in links:
        rec = parse_one(str(item.get("href", "")), item.get("age_text"))
        if rec is None:
            continue
        if rec["alert_key"] in seen:
            dups += 1; continue
        seen.add(rec["alert_key"]); out.append(rec)
    print(json.dumps({"alerts": out, "dropped_duplicates": dups}, ensure_ascii=False))

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Plain-text phone digest from the notifications payload. stdlib only.
Usage: digest.py --payload payload.json --profile user-profile.json --out digest.txt [--max-chars 7500] [--last-success DATE]"""
import argparse, json, os, re, sys

def rate_of(j):
    r = (j.get("signals") or {}).get("rate") or j.get("salary_text") or j.get("salary") or ""
    return r if r else "rate not disclosed"

def job_line(prefix, j, evidence=False):
    line = f"{prefix} · {j.get('title','')} — {j.get('company','')} · {rate_of(j)} · {j.get('location','')} · {j.get('url','')}"
    if evidence:
        for dim in (j.get("dimensions") or {}).values():
            ev = dim.get("evidence") or []
            if ev: return line + " · " + str(ev[0])
    return line

def gates_line(profile):
    parts = []
    for db in ((profile.get("requirements") or {}).get("deal_breakers") or []):
        vals = ", ".join(str(v) for v in (db.get("values") or []))
        ft = db.get("free_text")
        s = f"{db.get('kind')}={vals}" if vals else f"{db.get('kind')}"
        if ft: s += f" ({ft})"
        parts.append(s)
    return "Gates: " + "; ".join(parts) if parts else "Gates: none declared"

def build(pl, profile, last_success, ws_name):
    cov = (pl.get("coverage") or {}).get("totals") or {}
    tail = [gates_line(profile), f"Styled report: iCloud Drive → CoWork → {ws_name} → .job-scout/reports/"]
    if pl.get("run_status") == "no_scrape":
        head = [f"NO FRESH SCRAPE — {pl.get('no_scrape_reason') or 'reason not recorded'}. Last successful run: {last_success or 'unknown'}."]
        return head, [], [], [], tail
    tc = pl.get("tier_counts") or {}
    head = [f"Fresh scrape {pl.get('generated_at','')} · alerts walked {cov.get('alerts',0)} · cards {cov.get('cards_seen',0)} · new {tc.get('total',0)} · A:{tc.get('a',0)} B:{tc.get('b',0)} C:{tc.get('c',0)} · filtered {tc.get('d',0)} · queued {len(pl.get('queued') or [])}"]
    res = pl.get("results") or []
    matches = ["", "A/B/C MATCHES"] + [job_line(j["tier"], j, evidence=(j["tier"] == "A")) for j in res if j.get("tier") in ("A", "B", "C") and not j.get("gate_violations")]
    if len(matches) == 2: matches.append("none cleared the gates today")
    nm = pl.get("near_misses") or []
    near = ["", "NEAR MISSES"] + [job_line(j.get("would_be_tier", "B"), j) + f" · would be {j.get('would_be_tier','B')}; failed {(j.get('failed_gate') or {}).get('kind','?')}: {(j.get('failed_gate') or {}).get('detail','')}; {j.get('bend_hint','')}" for j in nm] if nm else []
    filt = [j for j in res if j.get("gate_violations")]
    filtered = ["", f"FILTERED OUT ({len(filt)})"] + [f"{i}. {j.get('title','')} — {j.get('company','')} · {j.get('location','')} · " + ", ".join(v.get("kind", "?") for v in j["gate_violations"]) + f" · {j.get('url','')}" for i, j in enumerate(filt, 1)]
    q = pl.get("queued") or []
    queued = ["", f"QUEUED FOR TOMORROW ({len(q)})"] + [f"- {j.get('title','')} — {j.get('company','')} · {j.get('location','')} · {j.get('url','')}" for j in q]
    rest = ["", f"REPOSTS SKIPPED: {(pl.get('coverage') or {}).get('reposts_disclosed', 0)}",
            f"Alerts walked: {cov.get('alerts',0)} (complete {cov.get('complete',0)}, partial {cov.get('partial',0)}) · cards {cov.get('cards_seen',0)} · new {cov.get('new',0)}", ""]
    return head + matches + near, filtered, queued, rest, tail

def render(head, filtered, queued, rest, tail): return "\n".join(head + filtered + queued + rest + tail) + "\n"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--payload", required=True); ap.add_argument("--profile", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--max-chars", type=int, default=7500); ap.add_argument("--last-success"); ap.add_argument("--workspace-name", default="CVFREELANCER")
    a = ap.parse_args()
    try:
        with open(a.payload) as f: pl = json.load(f)
        profile = {}
        if os.path.isfile(a.profile):
            with open(a.profile) as f: profile = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"digest: bad input ({e})", file=sys.stderr)
        sys.exit(1)
    head, filtered, queued, rest, tail = build(pl, profile, a.last_success, a.workspace_name)
    trimmed = False
    for section in (filtered, queued):  # D11: drop from the end of FILTERED OUT first, then QUEUED
        if len(render(head, filtered, queued, rest, tail)) <= a.max_chars: break
        dropped = 0
        while len(section) > 2 and len(render(head, filtered, queued, rest, tail)) > a.max_chars:
            section.pop(); dropped += 1
        if dropped:
            section.append(f"…and {dropped} more — see the styled report"); trimmed = True
    text = render(head, filtered, queued, rest, tail)
    if len(text) > a.max_chars:  # last resort: hard cut on a line boundary, keep the tail
        body = "\n".join(head)[: a.max_chars - len("\n".join(tail)) - 60]
        text = body + "\n…truncated — see the styled report\n" + "\n".join(tail) + "\n"; trimmed = True
    text = re.sub(r"\n{3,}", "\n\n", text)
    tmp = a.out + ".tmp"
    with open(tmp, "w") as fh: fh.write(text)
    os.replace(tmp, a.out)
    print(json.dumps({"chars": len(text), "trimmed": trimmed}))

if __name__ == "__main__":
    main()

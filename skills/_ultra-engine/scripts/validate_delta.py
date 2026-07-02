#!/usr/bin/env python3
"""Validate a _source-sweep return envelope before merge. stdlib only.
Usage: validate_delta.py --ws <workspace-dir> <delta.json>
Exit 0 = valid. Exit 1 = invalid, one violation per stderr line."""
import argparse, json, os, re, sys

ID_RE = re.compile(r"^([0-9]+|[a-z0-9-]+__[a-z0-9-]+__[^_\s]\S*)$")
DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})?$")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ws", required=True)
    ap.add_argument("delta")
    a = ap.parse_args()
    errs = []
    try:
        env = json.load(open(a.delta))
    except Exception as e:
        print(f"envelope: unparseable JSON ({e})", file=sys.stderr); sys.exit(1)

    if env.get("status") not in ("ok", "partial"):
        errs.append("envelope.status: must be ok|partial")
    c = env.get("counts")
    if not isinstance(c, dict):
        errs.append("envelope.counts: required object {scanned,matched,dropped_explicit_violation,returned,capped}")
    else:
        for k in ("scanned", "matched", "dropped_explicit_violation", "returned"):
            if not isinstance(c.get(k), int): errs.append(f"counts.{k}: required int")
        if isinstance(c.get("returned"), int) and isinstance(c.get("matched"), int) \
           and isinstance(c.get("dropped_explicit_violation"), int):
            truncated = c["returned"] < (c["matched"] - c["dropped_explicit_violation"])
            if truncated and c.get("capped") is not True:
                errs.append("counts.capped: truncation occurred but capped is not true (silent cap)")
    if not isinstance(env.get("errors"), list):
        errs.append("envelope.errors: required list")

    deltas = env.get("deltas")
    if not isinstance(deltas, list):
        errs.append("envelope.deltas: required list")
        deltas = []
    for i, d in enumerate(deltas):
        p = f"deltas[{i}]"
        for k in ("id", "url", "title", "company"):
            if not isinstance(d.get(k), str) or not d.get(k):
                errs.append(f"{p}.{k}: required non-empty string")
        if not isinstance(d.get("location", ""), str):
            errs.append(f"{p}.location: must be string")
        if isinstance(d.get("id"), str) and not ID_RE.match(d["id"]):
            errs.append(f"{p}.id: not bare-numeric or provider__board__externalid: {d['id']!r}")
        s = d.get("source")
        if not (isinstance(s, dict) and all(isinstance(s.get(k), str) and s.get(k) for k in ("lane", "provider", "board"))):
            errs.append(f"{p}.source: required structured object {{lane,provider,board}} — prose strings are the Phase-14 defect")
        fp = d.get("fingerprint", "")
        if not (isinstance(fp, str) and fp.count("|") == 2):
            errs.append(f"{p}.fingerprint: required 'company|title|location' form")
        pa = d.get("posted_at", "")
        if pa is None:
            pa = ""
        if not isinstance(pa, str) or not DATE_RE.match(pa):
            errs.append(f"{p}.posted_at: YYYY-MM-DD or empty")
        jd = d.get("jd_path")
        if jd is not None:
            if not isinstance(jd, str) or not jd:
                errs.append(f"{p}.jd_path: string or null")
            else:
                rel = jd[len(".job-scout/"):] if jd.startswith(".job-scout/") else jd
                if not os.path.isfile(os.path.join(a.ws, rel)):
                    errs.append(f"{p}.jd_path: file not found under workspace: {jd}")
    if errs:
        for e in errs: print(e, file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

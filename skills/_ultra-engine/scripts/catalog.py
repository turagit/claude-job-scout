#!/usr/bin/env python3
"""Source-catalogue validate/select + scope config-read. See test_catalog.py."""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
from identity import identity_key  # noqa: E402

SCOPES = ("eu-nl", "eu-broad")
REFRESH = ("manual",)
CATEGORIES = ("ats-provider", "remote-board", "aggregator", "national-board",
              "freelance-marketplace", "community")
LANES = ("api", "rss", "html", "extension")
SOURCE_REQUIRED = ("name", "url", "category", "access_lane", "endpoint",
                   "needs_key", "needs_slug", "poll_method", "notes",
                   "auth_required", "evidence_url", "evidence_checked_at")


def fail(errs):
    for e in errs:
        print(e, file=sys.stderr)
    sys.exit(2)


def validate(cat):
    errs = []
    if not isinstance(cat.get("catalog_version"), int) or cat["catalog_version"] < 1:
        errs.append("catalog_version must be an int >= 1")
    if cat.get("default_scope") not in SCOPES:
        errs.append("default_scope must be one of %s" % (SCOPES,))
    for k in ("identity_aliases", "retired_identities", "packs"):
        if not isinstance(cat.get(k), list):
            errs.append("%s must be a list" % k)
            cat[k] = []
    pack_ids, seen = set(), {}
    for p in cat["packs"]:
        pid = p.get("id") or "?"
        if pid in pack_ids:
            errs.append("duplicate pack id: %s" % pid)
        pack_ids.add(pid)
        if not isinstance(p.get("priority"), int):
            errs.append("%s: priority must be an int" % pid)
        scopes = p.get("scopes") or []
        if not scopes or not set(scopes) <= set(SCOPES):
            errs.append("%s: scopes must be a non-empty subset of %s" % (pid, SCOPES))
        if "eu-nl" in scopes and "eu-broad" not in scopes:
            errs.append("%s: a pack visible at eu-nl must also be visible at eu-broad (superset guarantee)" % pid)
        if not isinstance(p.get("countries"), list):
            errs.append("%s: countries must be a list" % pid)
        for s in p.get("sources") or []:
            label = "%s/%s" % (pid, s.get("name", "?"))
            missing = [k for k in SOURCE_REQUIRED if k not in s]
            if missing:
                errs.append("%s: missing fields %s" % (label, missing))
                continue
            if s["category"] == "linkedin":
                errs.append("%s: linkedin is never a catalogue candidate" % label)
                continue
            if s["category"] not in CATEGORIES:
                errs.append("%s: bad category %r" % (label, s["category"]))
            if s["access_lane"] not in LANES:
                errs.append("%s: bad access_lane %r" % (label, s["access_lane"]))
            if s["access_lane"] in ("api", "rss", "html") and not s["endpoint"]:
                errs.append("%s: endpoint required for lane %s" % (label, s["access_lane"]))
            if "priority" in s or "verified_at" in s:
                errs.append("%s: priority/verified_at are registry fields, not catalogue fields" % label)
            key = identity_key(s["url"], s["category"])
            if key in seen:
                errs.append("duplicate identity %s (%s vs %s)" % (key, seen[key], label))
            seen[key] = label
    return errs


def select(cat, scope):
    out = []
    for p in sorted(cat["packs"], key=lambda p: p["priority"]):
        if scope in p["scopes"]:
            for s in p["sources"]:
                c = dict(s)
                c["pack"] = p["id"]
                out.append(c)
    return out


def config_read(profile):
    um = profile.get("ultramode") or {}
    scope = um.get("source_scope", "eu-nl")
    refresh = um.get("source_refresh", "manual")
    errs = []
    if scope not in SCOPES:
        errs.append("invalid ultramode.source_scope: %r (allowed: %s)" % (scope, SCOPES))
    if refresh not in REFRESH:
        errs.append("invalid ultramode.source_refresh: %r (allowed: %s)" % (refresh, REFRESH))
    if errs:
        fail(errs)
    return {"source_scope": scope, "source_refresh": refresh}


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate")
    v.add_argument("catalogue")
    s = sub.add_parser("select")
    s.add_argument("catalogue")
    s.add_argument("--scope", required=True)
    c = sub.add_parser("config-read")
    c.add_argument("profile")
    a = ap.parse_args()

    if a.cmd == "validate":
        errs = validate(json.load(open(a.catalogue)))
        if errs:
            fail(errs)
        print("ok")
    elif a.cmd == "select":
        if a.scope not in SCOPES:
            fail(["invalid scope: %r (allowed: %s)" % (a.scope, SCOPES)])
        cat = json.load(open(a.catalogue))
        errs = validate(cat)
        if errs:
            fail(errs)
        json.dump(select(cat, a.scope), sys.stdout, indent=2)
        print()
    elif a.cmd == "config-read":
        json.dump(config_read(json.load(open(a.profile))), sys.stdout)
        print()


if __name__ == "__main__":
    main()

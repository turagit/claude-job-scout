#!/usr/bin/env python3
# skills/_ultra-engine/scripts/project.py
"""Catalogue candidate -> frozen registry entry. The projection boundary (D11)."""
import argparse
import json
import re
import sys

ALLOWED = ("name", "url", "category", "access_lane", "endpoint", "needs_key",
           "needs_slug", "poll_method", "notes", "pack")
CATALOGUE_ONLY = ("lane_tags", "auth_required", "evidence_url", "evidence_checked_at")
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$")


def die(msg):
    print(msg, file=sys.stderr)
    sys.exit(2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--priority", type=int, required=True)
    ap.add_argument("--verified-at", dest="verified_at", required=True)
    a = ap.parse_args()

    if not ISO.match(a.verified_at):
        die("verified_at must be ISO8601 (a live probe timestamp — the admission proof)")
    src = sys.stdin if a.candidate == "-" else open(a.candidate)
    c = json.load(src)

    unknown = set(c) - set(ALLOWED) - set(CATALOGUE_ONLY)
    if unknown:
        die("unknown candidate fields: %s" % sorted(unknown))
    if c.get("category") == "linkedin":
        die("linkedin entries are ensured by the dispatcher, never projected")
    if c.get("access_lane") in ("api", "rss", "html") and not c.get("endpoint"):
        die("endpoint required for access_lane %s" % c.get("access_lane"))

    entry = {k: c[k] for k in ALLOWED if k in c}
    entry["priority"] = a.priority
    entry["verified_at"] = a.verified_at
    entry["auth_state"] = "auth-required" if c.get("auth_required") else "public"
    json.dump(entry, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()

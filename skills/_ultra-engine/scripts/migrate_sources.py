#!/usr/bin/env python3
"""sources.json v1 -> v2 (Phase 16): auth_state + lifecycle lists. Idempotent, atomic."""
import json
import os
import re
import sys

LOGIN_RE = re.compile(r"login|sign[ -]?in|sign[ -]?up|account|credential", re.I)


def default_state(s):
    if s.get("category") == "linkedin":
        return "auth-required"
    blob = "%s %s" % (s.get("notes", ""), s.get("poll_method", ""))
    if s.get("access_lane") == "extension" and LOGIN_RE.search(blob):
        return "auth-required"
    return "public"


def main():
    path = sys.argv[1]
    d = json.load(open(path))
    if d.get("schema_version", 1) >= 2:
        print(json.dumps({"migrated": False, "schema_version": d["schema_version"],
                          "sources": len(d.get("sources", []))}))
        return
    d["schema_version"] = 2
    d.setdefault("identity_aliases", [])
    d.setdefault("retired_identities", [])
    for s in d.get("sources", []):
        s.setdefault("auth_state", default_state(s))
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(d, f, indent=2)
        f.write("\n")
    json.load(open(tmp))
    os.replace(tmp, path)
    print(json.dumps({"migrated": True, "schema_version": 2,
                      "sources": len(d["sources"])}))


if __name__ == "__main__":
    main()

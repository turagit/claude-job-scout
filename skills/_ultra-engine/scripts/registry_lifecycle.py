#!/usr/bin/env python3
"""Atomic sources.json lifecycle: catalogue-admission merge + retirement.

Invariants (spec D11): user sources retained; absence from a catalogue is not
retirement; tombstones block re-admission; aliases redirect identities; exact
counts; single linkedin entry; catalogue-only fields never persisted; atomic,
conflict-aware writes.
"""
import argparse
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
from identity import identity_key  # noqa: E402

CATALOGUE_ONLY = ("lane_tags", "auth_required", "evidence_url", "evidence_checked_at")
UPDATE_FIELDS = ("endpoint", "poll_method", "notes", "verified_at", "pack", "priority")


def die(msg, code=2):
    print(msg, file=sys.stderr)
    sys.exit(code)


def write_atomic(path, data):
    tmp = path + ".tmp.%d" % os.getpid()
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    json.load(open(tmp))
    os.replace(tmp, path)


def load_registry(path):
    raw = open(path, "rb").read()
    digest = hashlib.sha256(raw).hexdigest()
    reg = json.loads(raw)
    if reg.get("schema_version", 1) < 2:
        die("sources.json is schema_version %s — run migrate_sources.py first"
            % reg.get("schema_version", 1))
    return reg, digest


def guarded_write(path, data, load_time_digest):
    """Re-read the registry immediately before writing to narrow the
    check-then-write race to the OS-level minimum. Not a substitute for
    real locking, but this is a single-operator CLI — full locking is
    out of scope."""
    raw = open(path, "rb").read()
    if hashlib.sha256(raw).hexdigest() != load_time_digest:
        die("registry changed during merge — re-read and retry", 3)
    write_atomic(path, data)


def load_json_or_die(path, which):
    try:
        return json.load(open(path))
    except FileNotFoundError as e:
        die("cannot read %s file: %s (%s)" % (which, path, e), 2)
    except json.JSONDecodeError as e:
        die("cannot read %s file: %s (%s)" % (which, path, e), 2)


def build_aliases(reg, cat):
    m = {}
    for a in (reg.get("identity_aliases") or []) + ((cat or {}).get("identity_aliases") or []):
        m[a["from"]] = a["to"]
    return m


def resolve(key, aliases):
    seen = set()
    while key in aliases and key not in seen:
        seen.add(key)
        key = aliases[key]
    return key


def merge(a):
    reg, digest = load_registry(a.registry)
    if a.expect_sha256 and digest != a.expect_sha256:
        die("registry changed since read — re-read and retry", 3)
    cands = load_json_or_die(a.candidates, "candidates")
    cat = load_json_or_die(a.catalogue, "catalogue") if a.catalogue else None
    aliases = build_aliases(reg, cat)
    retired = set(reg.get("retired_identities") or []) \
        | set((cat or {}).get("retired_identities") or [])

    existing = {}
    for s in reg["sources"]:
        k = resolve(identity_key(s["url"], s["category"]), aliases)
        if k in existing:
            die("duplicate identity already in registry: %s" % k)
        existing[k] = s

    retained = len(reg["sources"])
    added = updated = tomb = 0
    for c in cands:
        leak = set(CATALOGUE_ONLY) & set(c)
        if leak:
            die("catalogue-only fields leaked into candidate %r: %s"
                % (c.get("name", "?"), sorted(leak)))
        if not c.get("verified_at"):
            die("candidate %r has no verified_at — not admissible (never-fabricate)"
                % c.get("name", "?"))
        if c.get("category") == "linkedin":
            die("linkedin entries are ensured by the dispatcher, never catalogue-admitted")
        key = resolve(identity_key(c["url"], c["category"]), aliases)
        if key in retired:
            tomb += 1
            continue
        if key in existing:
            e = existing[key]
            for f in UPDATE_FIELDS:
                if f in c:
                    e[f] = c[f]
            e.setdefault("auth_state", c.get("auth_state", "public"))
            updated += 1
        else:
            existing[key] = c
            added += 1

    out = list(existing.values())
    if sum(1 for s in out if s.get("category") == "linkedin") > 1:
        die("more than one category: linkedin entry")
    if len(out) != retained + added:
        die("exact-count invariant broken: %d != %d retained + %d added"
            % (len(out), retained, added))
    reg["sources"] = out
    guarded_write(a.registry, reg, digest)
    print(json.dumps({"retained": retained, "added": added, "updated": updated,
                      "tombstoned_skipped": tomb, "total": len(out)}))


def retire(a):
    reg, digest = load_registry(a.registry)
    hits = [s for s in reg["sources"] if s["name"] == a.name]
    if not hits:
        die("unknown source: %s" % a.name)
    key = identity_key(hits[0]["url"], hits[0]["category"])
    reg["sources"] = [s for s in reg["sources"] if s["name"] != a.name]
    reg.setdefault("retired_identities", [])
    if key not in reg["retired_identities"]:
        reg["retired_identities"].append(key)
    reg["priority_order"] = [n for n in reg.get("priority_order", []) if n != a.name]
    reg["backbone"] = [n for n in reg.get("backbone", []) if n != a.name]
    guarded_write(a.registry, reg, digest)
    print(json.dumps({"retired": a.name, "identity": key, "total": len(reg["sources"])}))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("merge")
    m.add_argument("--registry", required=True)
    m.add_argument("--candidates", required=True)
    m.add_argument("--catalogue")
    m.add_argument("--expect-sha256", dest="expect_sha256")
    r = sub.add_parser("retire")
    r.add_argument("--registry", required=True)
    r.add_argument("--name", required=True)
    a = ap.parse_args()
    merge(a) if a.cmd == "merge" else retire(a)


if __name__ == "__main__":
    main()

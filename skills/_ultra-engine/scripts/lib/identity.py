#!/usr/bin/env python3
# skills/_ultra-engine/scripts/lib/identity.py
"""THE host-identity normalisation. Never re-derive elsewhere (spec D11).

Identity = normalised homepage host + category. Mutable endpoint URLs are
deliberately excluded from identity.
"""
import re
import sys


def norm_host(url):
    h = url.strip().lower()
    h = re.sub(r'^[a-z][a-z0-9+.-]*://', '', h)      # scheme
    h = h.split('/', 1)[0].split('?', 1)[0].split('#', 1)[0]
    h = h.rsplit('@', 1)[-1]                          # userinfo
    h = h.split(':', 1)[0]                            # port
    if h.startswith('www.'):
        h = h[4:]
    return h.rstrip('.')


def identity_key(url, category):
    return "%s|%s" % (norm_host(url), category)


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "normalise":
        print(norm_host(sys.argv[2]))
    elif len(sys.argv) >= 4 and sys.argv[1] == "key":
        print(identity_key(sys.argv[2], sys.argv[3]))
    else:
        print("usage: identity.py normalise <url> | key <url> <category>",
              file=sys.stderr)
        sys.exit(2)

import json, os, shutil, subprocess, tempfile, unittest

HERE = os.path.dirname(__file__)
SCRIPT = os.path.join(HERE, "..", "scripts", "migrate_sources.py")
FIXTURE = os.path.join(HERE, "fixtures", "sources-v1-compat.json")


def run(path):
    return subprocess.run(["python3", SCRIPT, path], capture_output=True, text=True)


class TestMigrate(unittest.TestCase):
    def setUp(self):
        self.path = tempfile.mktemp(suffix=".json")
        shutil.copy(FIXTURE, self.path)

    def tearDown(self):
        os.unlink(self.path)

    def test_v1_round_trip(self):
        r = run(self.path)
        self.assertEqual(0, r.returncode, r.stderr)
        d = json.load(open(self.path))
        self.assertEqual(2, d["schema_version"])
        self.assertEqual([], d["identity_aliases"])
        self.assertEqual([], d["retired_identities"])
        by = {s["name"]: s for s in d["sources"]}
        self.assertEqual("auth-required", by["LinkedIn"]["auth_state"])   # linkedin heuristic
        self.assertEqual("auth-required", by["Malt"]["auth_state"])       # login-wall notes heuristic
        self.assertEqual("public", by["RemoteOK"]["auth_state"])          # everything else
        for s in d["sources"]:
            self.assertNotIn("auth_state_observed_at", s)                 # omitted until observed
        # untouched fields survive
        self.assertEqual("2026-07-01", by["Malt"]["last_swept_at"])
        self.assertEqual(["Malt", "RemoteOK"], d["priority_order"])

    def test_idempotent(self):
        run(self.path)
        before = open(self.path).read()
        r = run(self.path)
        self.assertEqual(0, r.returncode)
        self.assertFalse(json.loads(r.stdout)["migrated"])
        self.assertEqual(before, open(self.path).read())


if __name__ == "__main__":
    unittest.main()

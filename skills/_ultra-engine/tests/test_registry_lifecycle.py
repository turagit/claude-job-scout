import hashlib, json, os, shutil, subprocess, tempfile, unittest

HERE = os.path.dirname(__file__)
SCRIPT = os.path.join(HERE, "..", "scripts", "registry_lifecycle.py")
MIGRATE = os.path.join(HERE, "..", "scripts", "migrate_sources.py")
FIXTURE = os.path.join(HERE, "fixtures", "sources-v1-compat.json")

NEW = {"name": "Jobs.lu", "url": "https://www.jobs.lu/", "category": "national-board",
       "access_lane": "html", "endpoint": "https://www.jobs.lu/en/it-jobs",
       "needs_key": False, "needs_slug": False, "poll_method": "GET listing pages",
       "notes": "Luxembourg national board.", "pack": "benelux", "priority": 7,
       "verified_at": "2026-07-14T12:00:00Z", "auth_state": "public"}


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def run(*args):
    return subprocess.run(["python3", SCRIPT] + list(args), capture_output=True, text=True)


def tmp_json(data):
    f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    json.dump(data, f)
    f.close()
    return f.name


class TestLifecycle(unittest.TestCase):
    def setUp(self):
        self.reg = tempfile.mktemp(suffix=".json")
        shutil.copy(FIXTURE, self.reg)
        subprocess.run(["python3", MIGRATE, self.reg], capture_output=True)

    def tearDown(self):
        os.unlink(self.reg)

    def test_merge_adds_and_retains(self):
        r = run("merge", "--registry", self.reg, "--candidates", tmp_json([NEW]))
        self.assertEqual(0, r.returncode, r.stderr)
        c = json.loads(r.stdout)
        self.assertEqual({"retained": 3, "added": 1, "updated": 0,
                          "tombstoned_skipped": 0, "total": 4}, c)
        d = json.load(open(self.reg))
        self.assertEqual(4, len(d["sources"]))          # user sources retained
        self.assertIn("Jobs.lu", [s["name"] for s in d["sources"]])

    def test_known_identity_updates_and_preserves_observations(self):
        upd = dict(NEW, name="Malt (EU)", url="http://WWW.malt.nl/",  # same identity, new spelling
                   category="freelance-marketplace", access_lane="extension", endpoint="",
                   notes="refreshed", pack="eu-contract", priority=2,
                   auth_state="auth-required")
        r = run("merge", "--registry", self.reg, "--candidates", tmp_json([upd]))
        c = json.loads(r.stdout)
        self.assertEqual((3, 0, 1), (c["retained"], c["added"], c["updated"]), r.stderr)
        malt = [s for s in json.load(open(self.reg))["sources"]
                if s["url"] == "https://www.malt.nl"][0]
        self.assertEqual("refreshed", malt["notes"])            # updated field
        self.assertEqual("Malt", malt["name"])                  # existing name kept
        self.assertEqual("2026-07-01", malt["last_swept_at"])   # observation preserved
        self.assertEqual("auth-required", malt["auth_state"])   # observed state not overwritten

    def test_tombstone_blocks_admission(self):
        d = json.load(open(self.reg))
        d["retired_identities"] = ["jobs.lu|national-board"]
        json.dump(d, open(self.reg, "w"))
        c = json.loads(run("merge", "--registry", self.reg,
                           "--candidates", tmp_json([NEW])).stdout)
        self.assertEqual((0, 1), (c["added"], c["tombstoned_skipped"]))

    def test_alias_redirects_identity(self):
        cat = {"catalog_version": 1, "default_scope": "eu-nl", "packs": [],
               "identity_aliases": [{"from": "jobs.lu|national-board",
                                     "to": "malt.nl|freelance-marketplace"}],
               "retired_identities": []}
        c = json.loads(run("merge", "--registry", self.reg,
                           "--candidates", tmp_json([NEW]),
                           "--catalogue", tmp_json(cat)).stdout)
        self.assertEqual((0, 1), (c["added"], c["updated"]))  # lands on Malt, no new entry

    def test_leaked_catalogue_field_rejected(self):
        r = run("merge", "--registry", self.reg,
                "--candidates", tmp_json([dict(NEW, auth_required=False)]))
        self.assertEqual(2, r.returncode)
        self.assertIn("catalogue-only", r.stderr)

    def test_missing_verified_at_rejected(self):
        bad = dict(NEW); del bad["verified_at"]
        self.assertEqual(2, run("merge", "--registry", self.reg,
                                "--candidates", tmp_json([bad])).returncode)

    def test_second_linkedin_rejected(self):
        li = dict(NEW, name="LinkedIn 2", url="https://linkedin.example", category="linkedin",
                  access_lane="extension", endpoint="")
        self.assertEqual(2, run("merge", "--registry", self.reg,
                                "--candidates", tmp_json([li])).returncode)

    def test_conflict_detected(self):
        r = run("merge", "--registry", self.reg, "--candidates", tmp_json([NEW]),
                "--expect-sha256", "0" * 64)
        self.assertEqual(3, r.returncode)
        r2 = run("merge", "--registry", self.reg, "--candidates", tmp_json([NEW]),
                 "--expect-sha256", sha(self.reg))
        self.assertEqual(0, r2.returncode, r2.stderr)

    def test_retire_writes_tombstone(self):
        run("merge", "--registry", self.reg, "--candidates", tmp_json([NEW]))
        r = run("retire", "--registry", self.reg, "--name", "Jobs.lu")
        self.assertEqual(0, r.returncode, r.stderr)
        d = json.load(open(self.reg))
        self.assertNotIn("Jobs.lu", [s["name"] for s in d["sources"]])
        self.assertIn("jobs.lu|national-board", d["retired_identities"])
        # and a rebuild cannot re-admit it
        c = json.loads(run("merge", "--registry", self.reg,
                           "--candidates", tmp_json([NEW])).stdout)
        self.assertEqual(1, c["tombstoned_skipped"])

    def test_v1_registry_refused(self):
        raw = tempfile.mktemp(suffix=".json")
        shutil.copy(FIXTURE, raw)
        r = run("merge", "--registry", raw, "--candidates", tmp_json([NEW]))
        self.assertEqual(2, r.returncode)
        self.assertIn("migrate", r.stderr)
        os.unlink(raw)


if __name__ == "__main__":
    unittest.main()

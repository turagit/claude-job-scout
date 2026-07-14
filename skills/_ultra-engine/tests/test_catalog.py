import copy, json, os, subprocess, tempfile, unittest

HERE = os.path.dirname(__file__)
SCRIPT = os.path.join(HERE, "..", "scripts", "catalog.py")
FIXTURE = os.path.join(HERE, "fixtures", "catalogue-mini.json")


def run(*args):
    return subprocess.run(["python3", SCRIPT] + list(args),
                          capture_output=True, text=True)


def tmp_json(data):
    f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    json.dump(data, f)
    f.close()
    return f.name


class TestValidate(unittest.TestCase):
    def test_fixture_is_valid(self):
        r = run("validate", FIXTURE)
        self.assertEqual(0, r.returncode, r.stderr)
        self.assertEqual("ok", r.stdout.strip())

    def test_duplicate_identity_across_packs_rejected(self):
        cat = json.load(open(FIXTURE))
        dupe = copy.deepcopy(cat["packs"][0]["sources"][0])
        dupe["name"] = "EU Remote Jobs (again)"
        dupe["url"] = "http://WWW.euremotejobs.com"     # spelling variant, same identity
        cat["packs"][1]["sources"].append(dupe)
        r = run("validate", tmp_json(cat))
        self.assertEqual(2, r.returncode)
        self.assertIn("duplicate identity", r.stderr)

    def test_bad_scope_rejected(self):
        cat = json.load(open(FIXTURE))
        cat["packs"][0]["scopes"] = ["global"]
        r = run("validate", tmp_json(cat))
        self.assertEqual(2, r.returncode)

    def test_linkedin_candidate_rejected(self):
        cat = json.load(open(FIXTURE))
        cat["packs"][0]["sources"][0]["category"] = "linkedin"
        r = run("validate", tmp_json(cat))
        self.assertEqual(2, r.returncode)
        self.assertIn("linkedin", r.stderr)

    def test_missing_evidence_rejected(self):
        cat = json.load(open(FIXTURE))
        del cat["packs"][0]["sources"][0]["evidence_checked_at"]
        r = run("validate", tmp_json(cat))
        self.assertEqual(2, r.returncode)

    def test_eu_nl_without_eu_broad_violates_superset_guarantee(self):
        cat = json.load(open(FIXTURE))
        cat["packs"][0]["scopes"] = ["eu-nl"]
        r = run("validate", tmp_json(cat))
        self.assertEqual(2, r.returncode)
        self.assertIn("superset", r.stderr)

    def test_candidate_with_verified_at_rejected(self):
        cat = json.load(open(FIXTURE))
        cat["packs"][0]["sources"][0]["verified_at"] = "2026-01-01T00:00:00Z"
        r = run("validate", tmp_json(cat))
        self.assertEqual(2, r.returncode)
        self.assertIn("verified_at", r.stderr)

    def test_invalid_default_scope_rejected(self):
        cat = json.load(open(FIXTURE))
        cat["default_scope"] = "global"
        r = run("validate", tmp_json(cat))
        self.assertEqual(2, r.returncode)
        self.assertIn("default_scope", r.stderr)


class TestSelect(unittest.TestCase):
    def test_eu_nl_excludes_broad_only_packs(self):
        r = run("select", FIXTURE, "--scope", "eu-nl")
        self.assertEqual(0, r.returncode, r.stderr)
        names = [c["name"] for c in json.loads(r.stdout)]
        self.assertEqual(["EU Remote Jobs", "Jobs.lu"], names)

    def test_eu_broad_is_superset_and_ordered(self):
        r = run("select", FIXTURE, "--scope", "eu-broad")
        got = json.loads(r.stdout)
        self.assertEqual(["EU Remote Jobs", "Jobs.lu", "Upwork"],
                         [c["name"] for c in got])
        self.assertEqual(["eu-core", "benelux", "authenticated-marketplaces"],
                         [c["pack"] for c in got])

    def test_invalid_scope_rejected(self):
        r = run("select", FIXTURE, "--scope", "everywhere")
        self.assertEqual(2, r.returncode)


class TestConfigRead(unittest.TestCase):
    def test_defaults_without_write(self):
        p = tmp_json({"schema_version": 2, "x_custom": {"a": 1}})
        before = open(p, "rb").read()
        r = run("config-read", p)
        self.assertEqual(0, r.returncode, r.stderr)
        self.assertEqual({"source_scope": "eu-nl", "source_refresh": "manual"},
                         json.loads(r.stdout))
        self.assertEqual(before, open(p, "rb").read())  # read never writes

    def test_stored_values_returned(self):
        p = tmp_json({"ultramode": {"source_scope": "eu-broad"}})
        self.assertEqual("eu-broad", json.loads(run("config-read", p).stdout)["source_scope"])

    def test_invalid_values_rejected(self):
        self.assertEqual(2, run("config-read", tmp_json(
            {"ultramode": {"source_scope": "global"}})).returncode)
        self.assertEqual(2, run("config-read", tmp_json(
            {"ultramode": {"source_refresh": "weekly"}})).returncode)


if __name__ == "__main__":
    unittest.main()

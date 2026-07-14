import json, os, subprocess, tempfile, unittest

HERE = os.path.dirname(__file__)
SCRIPT = os.path.join(HERE, "..", "scripts", "project.py")

CAND = {
    "name": "Jobs.lu", "url": "https://www.jobs.lu/", "category": "national-board",
    "access_lane": "html", "endpoint": "https://www.jobs.lu/en/it-jobs",
    "needs_key": False, "needs_slug": False,
    "poll_method": "GET the IT listing pages; filter client-side.",
    "notes": "Luxembourg national board.", "pack": "benelux",
    "lane_tags": ["*"], "auth_required": False,
    "evidence_url": "https://www.jobs.lu/", "evidence_checked_at": "2026-07-14T09:00:00Z",
}


def run(cand, *extra):
    f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    json.dump(cand, f)
    f.close()
    args = ["python3", SCRIPT, "--candidate", f.name,
            "--priority", "7", "--verified-at", "2026-07-14T12:00:00Z"] + list(extra)
    return subprocess.run(args, capture_output=True, text=True)


class TestProject(unittest.TestCase):
    def test_projection_strips_catalogue_fields(self):
        r = run(CAND)
        self.assertEqual(0, r.returncode, r.stderr)
        e = json.loads(r.stdout)
        for k in ("lane_tags", "auth_required", "evidence_url", "evidence_checked_at"):
            self.assertNotIn(k, e)
        self.assertEqual(7, e["priority"])
        self.assertEqual("2026-07-14T12:00:00Z", e["verified_at"])
        self.assertEqual("public", e["auth_state"])
        self.assertEqual("benelux", e["pack"])
        self.assertNotIn("auth_state_observed_at", e)

    def test_auth_required_maps_to_state(self):
        c = dict(CAND, auth_required=True, access_lane="extension", endpoint="")
        e = json.loads(run(c).stdout)
        self.assertEqual("auth-required", e["auth_state"])

    def test_bad_verified_at_rejected(self):
        f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        json.dump(CAND, f); f.close()
        r = subprocess.run(["python3", SCRIPT, "--candidate", f.name,
                            "--priority", "7", "--verified-at", "yesterday"],
                           capture_output=True, text=True)
        self.assertEqual(2, r.returncode)

    def test_unknown_field_rejected(self):
        self.assertEqual(2, run(dict(CAND, surprise=1)).returncode)

    def test_empty_endpoint_on_html_rejected(self):
        self.assertEqual(2, run(dict(CAND, endpoint="")).returncode)

    def test_linkedin_rejected(self):
        self.assertEqual(2, run(dict(CAND, category="linkedin")).returncode)


if __name__ == "__main__":
    unittest.main()

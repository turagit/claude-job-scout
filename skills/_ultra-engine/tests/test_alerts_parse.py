import json, os, subprocess, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "scripts", "alerts_parse.py")
FIX = os.path.join(HERE, "fixtures", "p17-notifications-dump.json")

def run(payload):
    return subprocess.run(["python3", SCRIPT], input=json.dumps(payload), capture_output=True, text=True)

class T(unittest.TestCase):
    def setUp(self):
        self.dump = json.load(open(FIX))
        p = run(self.dump); self.assertEqual(p.returncode, 0, p.stderr)
        self.out = json.loads(p.stdout)

    def test_dedupes_doubled_anchor_and_drops_non_alert(self):
        self.assertEqual(len(self.out["alerts"]), 3)
        self.assertEqual(self.out["dropped_duplicates"], 1)

    def test_same_keywords_newer_epoch_is_a_distinct_alert(self):
        keys = {a["alert_key"] for a in self.out["alerts"] if a["keywords"] == "linux engineer Contract Remote"}
        self.assertEqual(len(keys), 2)

    def test_fields(self):
        a = self.out["alerts"][0]
        self.assertEqual(a["keywords"], "linux engineer Contract Remote")
        self.assertEqual(a["geo_id"], "91000000")
        self.assertEqual(a["since_epoch"], 1788218797)
        self.assertEqual(a["since"], "2026-08-31T23:26:37Z")
        self.assertEqual(a["preview_ids"], ["4461737101","4461723921","4461789493","4461758173","4454761864","4461780431"])
        self.assertEqual(a["qualifiers"], ["remote"])
        self.assertEqual(len(a["alert_key"]), 16)
        self.assertNotIn("currentJobId", a["params"]); self.assertNotIn("originToLandingJobPostings", a["params"])
        self.assertIn("alertAction=viewjobs", a["params"])
        self.assertTrue(a["results_url"].startswith("https://www.linkedin.com/jobs/search-results/?"))

    def test_salary_param_kept_and_no_qualifier(self):
        a = [x for x in self.out["alerts"] if x["keywords"] == "linux security engineer"][0]
        self.assertIn("f_SAL=", a["params"]); self.assertEqual(a["qualifiers"], [])

    def test_deterministic_key(self):
        again = json.loads(run(self.dump).stdout)
        self.assertEqual([a["alert_key"] for a in again["alerts"]], [a["alert_key"] for a in self.out["alerts"]])

    def test_bad_input_is_clean_error(self):
        p = run({"surface": "notifications"})
        self.assertEqual(p.returncode, 1); self.assertNotIn("Traceback", p.stderr)

if __name__ == "__main__":
    unittest.main()

import json, os, subprocess, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.join(HERE, "..", "scripts")
def parsed(fixture):
    d = json.load(open(os.path.join(HERE, "fixtures", fixture)))
    p = subprocess.run(["python3", os.path.join(S, "cards_parse.py"), "--surface", "alert"], input=json.dumps(d), capture_output=True, text=True)
    return json.loads(p.stdout)
def tmpjson(obj):
    f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False); json.dump(obj, f); f.close(); return f.name
def stop(alert, page, page_no, extra=()):
    p = subprocess.run(["python3", os.path.join(S, "walk_stop.py"), "--alert", tmpjson(alert), "--page", tmpjson(page),
                        "--page-no", str(page_no), "--valve", "10", *extra], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    return json.loads(p.stdout)
def bad_input(alert, page, page_no):
    p = subprocess.run(["python3", os.path.join(S, "walk_stop.py"), "--alert", tmpjson(alert), "--page", tmpjson(page),
                        "--page-no", str(page_no), "--valve", "10"], capture_output=True, text=True)
    return p.returncode, p.stderr
REMOTE = {"alert_key": "k1", "keywords": "linux engineer Contract Remote", "qualifiers": ["remote"]}
NOQUAL = {"alert_key": "k2", "keywords": "ipa kerberos", "qualifiers": []}

class T(unittest.TestCase):
    def test_divider_stops(self):
        r = stop(REMOTE, parsed("p17-results-page1.json"), 1)
        self.assertEqual((r["stop"], r["reason"]), (True, "divider"))
    def test_no_divider_remote_present_continues(self):
        r = stop(REMOTE, parsed("p17-results-page2.json"), 2)
        self.assertEqual((r["stop"], r["reason"]), (False, None)); self.assertFalse(r["needs_model_check"])
    def test_whole_page_without_qualifier_is_drift(self):
        r = stop(REMOTE, parsed("p17-results-drift.json"), 3)
        self.assertEqual((r["stop"], r["reason"]), (True, "drift"))
    def test_valve(self):
        r = stop(REMOTE, parsed("p17-results-page2.json"), 10)
        self.assertEqual((r["stop"], r["reason"]), (True, "valve"))
    def test_no_next(self):
        pg = parsed("p17-results-page2.json"); pg["has_next"] = False
        r = stop(REMOTE, pg, 2); self.assertEqual((r["stop"], r["reason"]), (True, "no_next"))
    def test_no_qualifier_strong_term_required(self):
        alert = {"alert_key": "k3", "keywords": "devops engineer", "qualifiers": []}
        r = stop(alert, parsed("p17-results-page2.json"), 2)  # 'engineer' alone no longer counts; no title has 'devops'
        self.assertFalse(r["stop"]); self.assertTrue(r["needs_model_check"])
        alert = {"alert_key": "k4", "keywords": "linux engineer", "qualifiers": []}
        r = stop(alert, parsed("p17-results-page2.json"), 2)  # "Linux Expert" matches the strong term
        self.assertFalse(r["stop"]); self.assertFalse(r["needs_model_check"]); self.assertIn("4460622080", r["matched_ids"])
    def test_qualifier_page_of_remote_spam_is_drift(self):
        alert = {"alert_key": "k5", "keywords": "lead platform engineer Contract Remote", "qualifiers": ["remote"]}
        page = {"cards": [{"id": "1", "title": "Senior Backend Engineer (Remote)", "workplace": "remote", "before_divider": True},
                          {"id": "2", "title": "Mechanical Engineer (Remote)", "workplace": "remote", "before_divider": True}],
                "divider_seen": False, "has_next": True}
        r = stop(alert, page, 2); self.assertEqual((r["stop"], r["reason"]), (True, "drift"))
        page["cards"].append({"id": "3", "title": "Cloud Native Platform Engineer", "workplace": "remote", "before_divider": True})
        r = stop(alert, page, 2); self.assertFalse(r["stop"]); self.assertEqual(r["matched_ids"], ["3"])
    def test_qualifier_only_alert_keeps_workplace_rule(self):
        alert = {"alert_key": "k6", "keywords": "Remote", "qualifiers": ["remote"]}
        page = {"cards": [{"id": "1", "title": "Anything (Remote)", "workplace": "remote", "before_divider": True}], "divider_seen": False, "has_next": True}
        self.assertFalse(stop(alert, page, 1)["stop"])
    def test_no_qualifier_no_overlap_asks_model(self):
        r = stop(NOQUAL, parsed("p17-results-drift.json"), 3)
        self.assertFalse(r["stop"]); self.assertTrue(r["needs_model_check"]); self.assertEqual(len(r["undecided_ids"]), 3)
    def test_model_verdicts(self):
        self.assertFalse(stop(NOQUAL, parsed("p17-results-drift.json"), 3, ("--model-says-match", "true"))["stop"])
        r = stop(NOQUAL, parsed("p17-results-drift.json"), 3, ("--model-says-match", "false"))
        self.assertEqual((r["stop"], r["reason"]), (True, "drift"))
    def test_divider_beats_everything(self):
        pg = parsed("p17-results-page1.json"); pg["has_next"] = False
        self.assertEqual(stop(REMOTE, pg, 10)["reason"], "divider")
    def test_bad_alert_shape_returns_error(self):
        rc, stderr = bad_input([], parsed("p17-results-page2.json"), 1)
        self.assertEqual(rc, 1); self.assertNotIn("Traceback", stderr); self.assertIn("bad input", stderr)
    def test_bad_keywords_type_returns_error(self):
        bad_alert = {"alert_key": "k4", "keywords": 42, "qualifiers": []}
        rc, stderr = bad_input(bad_alert, parsed("p17-results-page2.json"), 1)
        self.assertEqual(rc, 1); self.assertNotIn("Traceback", stderr); self.assertIn("bad input", stderr)
    def test_empty_page_no_model_check(self):
        alert = {"alert_key": "k5", "keywords": "engineer", "qualifiers": []}
        r = stop(alert, {"cards": [], "has_next": True}, 1)
        self.assertFalse(r["stop"]); self.assertFalse(r["needs_model_check"]); self.assertEqual(r["undecided_ids"], [])

if __name__ == "__main__":
    unittest.main()

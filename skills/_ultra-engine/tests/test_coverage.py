import json, os, subprocess, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); S = os.path.join(HERE, "..", "scripts")
LEDGER = {"schema_version": 1, "alerts": {
  "k1": {"keywords": "linux engineer Contract Remote", "since": "2026-08-31T23:26:37Z", "first_seen": "2026-09-02", "status": "complete", "last_page": 2, "stop_reason": "divider", "cards_seen": 49, "before_divider": 24, "known": 10, "reposts": 1, "new": 13, "run_id": "r1"},
  "k2": {"keywords": "ipa kerberos", "since": "2026-08-31T10:17:37Z", "first_seen": "2026-09-02", "status": "partial", "last_page": 1, "stop_reason": None, "cards_seen": 25, "before_divider": 25, "known": 20, "reposts": 0, "new": 5, "run_id": "r1"},
  "k0": {"keywords": "old", "since": "2026-08-30T10:00:00Z", "first_seen": "2026-08-31", "status": "complete", "last_page": 1, "stop_reason": "no_next", "cards_seen": 3, "before_divider": 3, "known": 3, "reposts": 0, "new": 0, "run_id": "r0"}}}
class T(unittest.TestCase):
    def test_rows_and_totals(self):
        d = tempfile.mkdtemp(); L = os.path.join(d, "alerts.json"); json.dump(LEDGER, open(L, "w"))
        R = os.path.join(d, "reposts.json"); json.dump([{"id": "1", "matched_id": "2", "alert_key": "k1"}], open(R, "w"))
        out = os.path.join(d, "coverage.json")
        p = subprocess.run(["python3", os.path.join(S, "coverage.py"), "--ledger", L, "--run-id", "r1", "--reposts", R, "--out", out], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr); c = json.load(open(out))
        self.assertEqual([r["alert_key"] for r in c["rows"]], ["k1", "k2"])
        self.assertEqual(c["rows"][0]["pages_walked"], 2)
        self.assertEqual(c["totals"], {"alerts": 2, "complete": 1, "partial": 1, "cards_seen": 74, "before_divider": 49, "known": 30, "reposts": 1, "new": 18, "dropped": 0})
        self.assertEqual(c["reposts_disclosed"], 1)
    def test_dropped_column_included(self):
        d = tempfile.mkdtemp(); L = os.path.join(d, "alerts.json")
        ledger = json.loads(json.dumps(LEDGER)); ledger["alerts"]["k1"]["dropped"] = 4; ledger["alerts"]["k2"]["dropped"] = 2
        json.dump(ledger, open(L, "w"))
        out = os.path.join(d, "coverage.json")
        p = subprocess.run(["python3", os.path.join(S, "coverage.py"), "--ledger", L, "--run-id", "r1", "--out", out], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr); c = json.load(open(out))
        self.assertEqual([r["dropped"] for r in c["rows"]], [4, 2])
        self.assertEqual(c["totals"]["dropped"], 6)
    def test_missing_ledger_gives_empty(self):
        d = tempfile.mkdtemp(); out = os.path.join(d, "coverage.json")
        p = subprocess.run(["python3", os.path.join(S, "coverage.py"), "--ledger", os.path.join(d, "none.json"), "--run-id", "r1", "--out", out], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0); self.assertEqual(json.load(open(out))["rows"], [])
    def test_corrupt_ledger(self):
        d = tempfile.mkdtemp(); L = os.path.join(d, "alerts.json"); open(L, "w").write("{not valid json")
        out = os.path.join(d, "coverage.json")
        p = subprocess.run(["python3", os.path.join(S, "coverage.py"), "--ledger", L, "--run-id", "r1", "--out", out], capture_output=True, text=True)
        self.assertEqual(p.returncode, 1, p.stderr); self.assertNotIn("Traceback", p.stderr); self.assertIn("bad input", p.stderr)
    def test_corrupt_reposts(self):
        d = tempfile.mkdtemp(); L = os.path.join(d, "alerts.json"); json.dump(LEDGER, open(L, "w"))
        R = os.path.join(d, "reposts.json"); open(R, "w").write('{"not": "a list"}')
        out = os.path.join(d, "coverage.json")
        p = subprocess.run(["python3", os.path.join(S, "coverage.py"), "--ledger", L, "--run-id", "r1", "--reposts", R, "--out", out], capture_output=True, text=True)
        self.assertEqual(p.returncode, 1); self.assertNotIn("Traceback", p.stderr); self.assertIn("bad input", p.stderr)
if __name__ == "__main__":
    unittest.main()

import json, os, subprocess, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.join(HERE, "..", "scripts")
def sh(*args):
    p = subprocess.run(["python3", os.path.join(S, "alerts_ledger.py"), *map(str, args)], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    return json.loads(p.stdout)
def tmpjson(obj):
    f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False); json.dump(obj, f); f.close(); return f.name
A1 = {"alert_key": "aaaa000000000001", "keywords": "linux engineer Contract Remote", "geo_id": "91000000", "since_epoch": 1788218797,
      "since": "2026-08-31T23:26:37Z", "params": "keywords=linux+engineer&f_TPR=a1788218797-", "results_url": "https://x/?a", "preview_ids": [], "qualifiers": ["remote"], "age_text": "43m"}
A2 = dict(A1, alert_key="aaaa000000000002", keywords="ipa kerberos", qualifiers=[], since_epoch=1788171457)

class T(unittest.TestCase):
    def setUp(self):
        self.L = os.path.join(tempfile.mkdtemp(), "alerts.json")
        self.parsed = tmpjson({"alerts": [A1, A2], "dropped_duplicates": 0})
    def test_plan_on_missing_ledger_walks_everything_from_page_1(self):
        r = sh("plan", "--ledger", self.L, "--alerts", self.parsed, "--today", "2026-09-02")
        self.assertEqual([(w["alert_key"], w["resume_page"], w["status"]) for w in r["walk"]],
                         [("aaaa000000000001", 1, "new"), ("aaaa000000000002", 1, "new")])
        self.assertFalse(os.path.exists(self.L))  # plan is read-only
    def test_start_page_complete_lifecycle(self):
        rec = sh("start", "--ledger", self.L, "--alert-json", tmpjson(A1), "--today", "2026-09-02", "--run-id", "2026-09-02-0310")
        self.assertEqual((rec["status"], rec["last_page"], rec["first_seen"]), ("partial", 0, "2026-09-02"))
        rec = sh("page", "--ledger", self.L, "--key", A1["alert_key"], "--page", 1, "--cards-seen", 25, "--before-divider", 24, "--known", 10, "--reposts", 1, "--new", 13)
        rec = sh("page", "--ledger", self.L, "--key", A1["alert_key"], "--page", 2, "--cards-seen", 25, "--before-divider", 25, "--known", 20, "--reposts", 0, "--new", 5)
        self.assertEqual((rec["last_page"], rec["cards_seen"], rec["known"], rec["new"]), (2, 50, 30, 18))
        r = sh("plan", "--ledger", self.L, "--alerts", self.parsed, "--today", "2026-09-02")
        self.assertEqual([(w["alert_key"], w["resume_page"], w["status"]) for w in r["walk"]][0], (A1["alert_key"], 3, "partial"))
        rec = sh("complete", "--ledger", self.L, "--key", A1["alert_key"], "--reason", "divider")
        self.assertEqual((rec["status"], rec["stop_reason"]), ("complete", "divider"))
        r = sh("plan", "--ledger", self.L, "--alerts", self.parsed, "--today", "2026-09-02")
        self.assertEqual([w["alert_key"] for w in r["walk"]], [A2["alert_key"]]); self.assertEqual(r["skipped_complete"], 1)
    def test_start_is_idempotent(self):
        sh("start", "--ledger", self.L, "--alert-json", tmpjson(A1), "--today", "2026-09-02", "--run-id", "r1")
        sh("page", "--ledger", self.L, "--key", A1["alert_key"], "--page", 1, "--cards-seen", 5, "--before-divider", 5, "--known", 1, "--reposts", 0, "--new", 4)
        rec = sh("start", "--ledger", self.L, "--alert-json", tmpjson(A1), "--today", "2026-09-03", "--run-id", "r2")
        self.assertEqual((rec["last_page"], rec["first_seen"], rec["run_id"]), (1, "2026-09-02", "r2"))
    def test_prune(self):
        sh("start", "--ledger", self.L, "--alert-json", tmpjson(A1), "--today", "2026-07-01", "--run-id", "r0")
        sh("start", "--ledger", self.L, "--alert-json", tmpjson(A2), "--today", "2026-09-01", "--run-id", "r1")
        r = sh("prune", "--ledger", self.L, "--today", "2026-09-02"); self.assertEqual((r["pruned"], r["kept"]), (1, 1))
        with open(self.L) as fh: self.assertNotIn(A1["alert_key"], json.load(fh)["alerts"])
    def test_bad_reason_rejected(self):
        sh("start", "--ledger", self.L, "--alert-json", tmpjson(A1), "--today", "2026-09-02", "--run-id", "r")
        p = subprocess.run(["python3", os.path.join(S, "alerts_ledger.py"), "complete", "--ledger", self.L, "--key", A1["alert_key"], "--reason", "tired"], capture_output=True, text=True)
        self.assertNotEqual(p.returncode, 0)

if __name__ == "__main__":
    unittest.main()

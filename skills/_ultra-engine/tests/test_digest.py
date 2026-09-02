import json, os, subprocess, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); S = os.path.join(HERE, "..", "scripts")
PROFILE = {"requirements": {"deal_breakers": [{"kind": "work_arrangement", "values": ["remote"]}, {"kind": "contract_type", "values": ["freelance", "detachering"]}, {"kind": "rate_floor", "values": ["650"], "free_text": "EUR/day"}]}}

def payload(rd, status="fresh", reason=""):
    p = subprocess.run(["bash", os.path.join(S, "payload_notifications.sh"), os.path.join(HERE, "fixtures", "p17-tracker-run.json"), rd, "2026-09-02", status, reason], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr; return json.loads(p.stdout)

class T(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        json.dump({"coverage": {"rows": [], "totals": {"alerts": 3, "complete": 2, "partial": 1, "cards_seen": 70, "new": 9}, "reposts_disclosed": 2}, "budget": {"limit": 150, "used": 9, "queued": 1}}, open(os.path.join(self.d, "scorecard.json"), "w"))
        json.dump([{"id": "1888", "title": "Queued role", "company": "Eps", "location": "Remote", "url": "https://www.linkedin.com/jobs/view/1888/"}], open(os.path.join(self.d, "queued.json"), "w"))
        self.prof = os.path.join(self.d, "profile.json"); json.dump(PROFILE, open(self.prof, "w"))
    def run_digest(self, pl, extra=()):
        pf = os.path.join(self.d, "payload.json"); json.dump(pl, open(pf, "w")); out = os.path.join(self.d, "digest.txt")
        p = subprocess.run(["python3", os.path.join(S, "digest.py"), "--payload", pf, "--profile", self.prof, "--out", out, *extra], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr); return open(out).read(), json.loads(p.stdout)
    def test_fresh_digest_order_and_content(self):
        txt, meta = self.run_digest(payload(self.d))
        lines = txt.split("\n")
        self.assertTrue(lines[0].startswith("Fresh scrape 2026-09-02"))
        self.assertLess(txt.index("A/B/C MATCHES"), txt.index("NEAR MISSES")); self.assertLess(txt.index("NEAR MISSES"), txt.index("FILTERED OUT"))
        self.assertLess(txt.index("FILTERED OUT"), txt.index("QUEUED FOR TOMORROW")); self.assertLess(txt.index("QUEUED FOR TOMORROW"), txt.index("Gates:"))
        self.assertIn("A · Lead Platform Engineer — Acme · €800/day · Amsterdam (Remote) · https://www.linkedin.com/jobs/view/1001/ · kubernetes", txt)
        self.assertIn("B · SRE — Beta · rate not disclosed · Berlin (Remote) · https://www.linkedin.com/jobs/view/1002/", txt)
        self.assertIn("would be B; failed work_arrangement: hybrid stated; /bend 1003", txt)
        self.assertIn("REPOSTS SKIPPED: 2", txt); self.assertIn("Alerts walked: 3 (complete 2, partial 1)", txt)
        self.assertIn("DROPPED ON CARD: 0", txt)
        self.assertLess(txt.index("REPOSTS SKIPPED"), txt.index("DROPPED ON CARD")); self.assertLess(txt.index("DROPPED ON CARD"), txt.index("Alerts walked"))
        self.assertIn("Gates: work_arrangement=remote; contract_type=freelance, detachering; rate_floor=650 (EUR/day)", txt)
        self.assertIn("Styled report: iCloud Drive", txt); self.assertNotIn("](", txt); self.assertNotIn("**", txt)
        self.assertFalse(meta["trimmed"])
    def test_dropped_count_reflected(self):
        json.dump([{"id": "1999", "title": "Onsite role", "company": "Onco", "location": "Berlin", "workplace": "onsite", "alert_key": "k1"},
                   {"id": "2000", "title": "Hybrid role", "company": "Hyco", "location": "Munich", "workplace": "hybrid", "alert_key": "k1"}],
                  open(os.path.join(self.d, "dropped-cards.json"), "w"))
        txt, _ = self.run_digest(payload(self.d))
        self.assertIn("DROPPED ON CARD: 2", txt)
    def test_no_scrape_digest(self):
        txt, _ = self.run_digest(payload(self.d, "no_scrape", "browser unavailable"), ("--last-success", "2026-09-01"))
        self.assertTrue(txt.startswith("NO FRESH SCRAPE — browser unavailable. Last successful run: 2026-09-01."))
        self.assertNotIn("A/B/C MATCHES", txt); self.assertIn("Gates:", txt)
    def test_trim(self):
        pl = payload(self.d)
        pl["results"] += [dict(pl["near_misses"][0], id=str(5000 + i), title="Filtered role %d" % i, near_miss=False) for i in range(200)]
        txt, meta = self.run_digest(pl, ("--max-chars", "3000"))
        self.assertLessEqual(len(txt), 3000); self.assertTrue(meta["trimmed"]); self.assertIn("more — see the styled report", txt)
        self.assertIn("A/B/C MATCHES", txt); self.assertIn("Gates:", txt)
if __name__ == "__main__":
    unittest.main()

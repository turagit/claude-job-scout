import json, os, subprocess, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "scripts", "cards_parse.py")
def fix(n):
    with open(os.path.join(HERE, "fixtures", n)) as f:
        return json.load(f)
def run(payload, surface):
    return subprocess.run(["python3", SCRIPT, "--surface", surface], input=json.dumps(payload), capture_output=True, text=True)

class T(unittest.TestCase):
    def test_page1_records(self):
        p = run(fix("p17-results-page1.json"), "alert"); self.assertEqual(p.returncode, 0, p.stderr)
        o = json.loads(p.stdout)
        self.assertTrue(o["divider_seen"]); self.assertEqual(o["cards_before_divider"], 4); self.assertTrue(o["has_next"])
        c = {x["id"]: x for x in o["cards"]}
        self.assertEqual(len(c), 5)
        a = c["4461737101"]
        self.assertEqual(a["title"], "Platform Engineer (Remote)"); self.assertEqual(a["company"], "Hire Feed")
        self.assertEqual(a["location"], "France (Remote)"); self.assertEqual(a["workplace"], "remote")
        self.assertEqual(a["salary_text"], "$40/hr - $100/hr"); self.assertEqual(a["posted_ago"], "19 hours ago")
        self.assertTrue(a["viewed"]); self.assertFalse(a["promoted"]); self.assertTrue(a["before_divider"])
        v = c["4459517621"]
        self.assertEqual(v["title"], "Staff Engineer - DevOps"); self.assertEqual(v["company"], "Hard Rock Digital")
        h = c["4460933633"]
        self.assertEqual(h["workplace"], "hybrid"); self.assertTrue(h["easy_apply"]); self.assertTrue(h["promoted"]); self.assertIsNone(h["salary_text"])
        self.assertFalse(c["4461709378"]["before_divider"])

    def test_page2_no_divider(self):
        o = json.loads(run(fix("p17-results-page2.json"), "alert").stdout)
        self.assertFalse(o["divider_seen"]); self.assertEqual(o["cards_before_divider"], 3)
        self.assertEqual(o["cards"][2]["salary_text"], "5,000 EUR/month - 6,000 EUR/month")
        self.assertTrue(all(x["before_divider"] for x in o["cards"]))

    def test_toppicks_old_markup_and_bad_id_dropped(self):
        o = json.loads(run(fix("p17-toppicks-page1.json"), "toppicks").stdout)
        self.assertEqual([x["id"] for x in o["cards"]], ["4428875133", "4401921503"])
        self.assertEqual(o["dropped_bad_id"], 1)
        self.assertEqual(o["cards"][0]["workplace"], "onsite"); self.assertTrue(o["cards"][0]["viewed"])
        self.assertEqual(o["cards"][1]["workplace"], "unknown"); self.assertEqual(o["cards"][1]["posted_ago"], "2 days ago")

    def test_saved_empty_is_ok_with_note(self):
        p = run(fix("p17-saved-empty.json"), "saved"); self.assertEqual(p.returncode, 0)
        o = json.loads(p.stdout); self.assertEqual(o["cards"], []); self.assertEqual(o["note"], "saved_empty")

    def test_mismatch_is_loud(self):
        p = run(fix("p17-results-mismatch.json"), "alert")
        self.assertEqual(p.returncode, 3); self.assertIn("extractor_mismatch", p.stderr)

    def test_bad_input(self):
        p = subprocess.run(["python3", SCRIPT, "--surface", "alert"], input="{", capture_output=True, text=True)
        self.assertEqual(p.returncode, 1); self.assertNotIn("Traceback", p.stderr)

    def test_no_company_line_yields_parse_warning(self):
        payload = {"surface": "alert", "claimed_results": "10 results", "page": 1, "divider_index": None, "has_next": False, "saved_count": None,
                   "cards": [{"id": "4461234567", "text": "DevOps Engineer\n\nAmsterdam (Remote)\n\nBe an early applicant"}]}
        o = json.loads(run(payload, "alert").stdout)
        card = o["cards"][0]
        self.assertIsNone(card["company"]); self.assertEqual(card["location"], "Amsterdam (Remote)")
        self.assertEqual(card["workplace"], "remote"); self.assertTrue(card["parse_warning"])
        self.assertEqual(o["low_confidence"], 1)

    def test_unmatched_salary_format_doesnt_shift_location(self):
        payload = {"surface": "alert", "claimed_results": "10 results", "page": 1, "divider_index": None, "has_next": False, "saved_count": None,
                   "cards": [{"id": "4461234568", "text": "Backend Engineer\n\nTech Corp\n\nEUR 50,000 per year\n\nBerlin (On-site)"}]}
        o = json.loads(run(payload, "alert").stdout)
        card = o["cards"][0]
        self.assertEqual(card["salary_text"], "EUR 50,000 per year"); self.assertEqual(card["location"], "Berlin (On-site)")
        self.assertEqual(card["company"], "Tech Corp"); self.assertEqual(card["workplace"], "onsite")
        self.assertFalse(card["parse_warning"]); self.assertEqual(o["low_confidence"], 0)

    def test_normal_card_has_parse_warning_false(self):
        payload = {"surface": "alert", "claimed_results": "10 results", "page": 1, "divider_index": None, "has_next": False, "saved_count": None,
                   "cards": [{"id": "4461234569", "text": "Senior SRE\n\nGlobal Tech\n\nStockholm (Remote)\n\n$80/hr - $120/hr\n\nBe an early applicant"}]}
        o = json.loads(run(payload, "alert").stdout)
        card = o["cards"][0]
        self.assertFalse(card["parse_warning"]); self.assertEqual(o["low_confidence"], 0)

if __name__ == "__main__":
    unittest.main()

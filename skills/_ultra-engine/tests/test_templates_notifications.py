import json, os, subprocess, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); S = os.path.join(HERE, "..", "scripts")
TPL = os.path.join(HERE, "..", "..", "_visualizer", "templates")
try:
    import jinja2
except ImportError:
    jinja2 = None

def payload(status="fresh", reason=""):
    rd = tempfile.mkdtemp()
    with open(os.path.join(rd, "scorecard.json"), "w") as f:
        json.dump({"coverage": {"rows": [{"alert_key": "k1", "keywords": "linux engineer Contract Remote", "since": "2026-08-31T23:26:37Z", "pages_walked": 2, "stop_reason": "divider", "status": "complete", "cards_seen": 49, "before_divider": 24, "known": 10, "reposts": 1, "new": 13}], "totals": {"alerts": 1, "complete": 1, "partial": 0, "cards_seen": 49, "before_divider": 24, "known": 10, "reposts": 1, "new": 13}, "reposts_disclosed": 1}, "budget": {"limit": 150, "used": 13, "queued": 1}, "disclosures": []}, f)
    with open(os.path.join(rd, "reposts.json"), "w") as f:
        json.dump([{"id": "1777", "matched_id": "1001", "alert_key": "k1", "title": "Lead Platform Engineer", "company": "Acme", "location": "Amsterdam (Remote)"}], f)
    with open(os.path.join(rd, "queued.json"), "w") as f:
        json.dump([{"id": "1888", "title": "Queued role", "company": "Eps", "location": "Remote", "url": "https://www.linkedin.com/jobs/view/1888/"}], f)
    with open(os.path.join(rd, "dropped-cards.json"), "w") as f:
        json.dump([{"id": "1999", "title": "Onsite role", "company": "Onco", "location": "Berlin", "workplace": "onsite", "alert_key": "k1"}], f)
    p = subprocess.run(["bash", os.path.join(S, "payload_notifications.sh"), os.path.join(HERE, "fixtures", "p17-tracker-run.json"), rd, "2026-09-02", status, reason], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr; return json.loads(p.stdout)

@unittest.skipIf(jinja2 is None, "jinja2 not installed — template render test skipped")
class T(unittest.TestCase):
    def render(self, fmt, data):
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.join(TPL, fmt)), autoescape=False)
        return env.get_template("check-job-notifications.%s.j2" % ("html" if fmt == "html" else "md")).render(data=data)
    def test_html_sections(self):
        h = self.render("html", payload())
        for s in ("Alert coverage", "linux engineer Contract Remote", "divider", "Queued for tomorrow", "Queued role", "Treated as reposts", "1777", "Would you bend", "/bend 1003", "View posting", "Dropped on card", "Onsite role"):
            self.assertIn(s, h)
        self.assertNotIn("no fresh scrape", h.lower())
    def test_html_no_scrape_banner(self):
        h = self.render("html", payload("no_scrape", "browser unavailable"))
        self.assertIn("No fresh scrape", h); self.assertIn("browser unavailable", h)
    def test_markdown_sections(self):
        m = self.render("markdown", payload())
        for s in ("### Alert coverage", "| linux engineer Contract Remote |", "### Queued for tomorrow", "### Treated as reposts", "### Near misses", "/bend 1003", "Dropped on card", "Onsite role"):
            self.assertIn(s, m)
    def test_missing_optional_fields_do_not_error(self):
        d = payload(); d.pop("coverage"); d.pop("queued"); d.pop("reposts"); d.pop("near_misses"); d.pop("budget"); d.pop("dropped")
        self.render("html", d); self.render("markdown", d)
        d2 = payload(); d2["coverage"].pop("totals"); d2.pop("budget")
        self.render("html", d2); self.render("markdown", d2)
        d3 = payload()
        for j in d3["near_misses"]:
            j.pop("failed_gate")
        h3 = self.render("html", d3); m3 = self.render("markdown", d3)
        self.assertIn("unknown", h3); self.assertIn("unknown", m3)
    def test_markdown_disclosures_render_without_results(self):
        d = payload(); d["results"] = []
        m = self.render("markdown", d)
        for s in ("### Near misses", "### Queued for tomorrow", "### Treated as reposts", "No notifications today."):
            self.assertIn(s, m)
if __name__ == "__main__":
    unittest.main()

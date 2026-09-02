import json, os, shutil, subprocess, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); S = os.path.join(HERE, "..", "scripts")
KINDS = {"work_arrangement","contract_type","seniority_floor","location","industry","company","rate_floor","salary_floor","custom"}
class T(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); self.t = os.path.join(self.d, "tracker.json")
        shutil.copy(os.path.join(HERE, "fixtures", "p17-tracker-drifted.json"), self.t)
        json.dump({"schema_version": 2, "sources": [{"name": "Greenhouse", "provider": "greenhouse", "category": "ats-provider"}, {"name": "JustJoin.it", "category": "aggregator"}, {"name": "IT-Contracts.nl", "category": "freelance-marketplace"}]}, open(os.path.join(self.d, "sources.json"), "w"))
    def run_it(self, *extra):
        p = subprocess.run(["python3", os.path.join(S, "migrate_tracker_v3.py"), "--tracker", self.t, "--sources", os.path.join(self.d, "sources.json"), *extra], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr); return json.loads(p.stdout)
    def test_dry_run_changes_nothing(self):
        before = open(self.t).read(); s = self.run_it("--dry-run")
        self.assertEqual(open(self.t).read(), before); self.assertTrue(s["dry_run"]); self.assertIsNone(s["backup"]); self.assertGreater(s["changed"], 0)
    def test_migration(self):
        s = self.run_it(); t = json.load(open(self.t)); j = t["jobs"]
        self.assertEqual(s["entries"], 6); self.assertEqual(len(j), 6); self.assertTrue(os.path.isfile(s["backup"]))
        self.assertEqual(t["schema_version"], 3); self.assertEqual(t["stats"]["closed_applications"], 7)
        a = j["4401921503"]
        self.assertEqual(a["id"], "4401921503"); self.assertEqual(a["source"], {"lane": "linkedin", "provider": "linkedin", "board": "Top Picks"})
        self.assertEqual((a["status"], a["tier"]), ("seen", "D")); self.assertEqual(a["first_seen"], "2026-09-02"); self.assertEqual(a["last_seen"], "2026-09-02")
        self.assertEqual(a["gate_violations"], [{"kind": "contract_type", "detail": "contract_type"}, {"kind": "custom", "detail": "skills_mismatch"}])
        self.assertNotIn("employment_type", a); self.assertNotIn("rate_disclosed", a); self.assertIn("employment_type: FULL_TIME", a["notes"]); self.assertIn("status(legacy): gated", a["notes"])
        self.assertEqual(a["rubric_version"], "legacy")
        b = j["4461737101"]; self.assertEqual(b["source"]["board"], "Job Alert"); self.assertIn("source(legacy): Job Alert (gap lanes", b["notes"]); self.assertEqual(b["first_seen"], "2026-09-01")
        c = j["4459517621"]; self.assertEqual(c["source"]["board"], "Search"); self.assertEqual(c["tier"], "untiered"); self.assertEqual(c["notes"], "source(legacy): Ultramode LinkedIn sweep 2026-08-18")
        g = j["greenhouse__miro__4012345"]; self.assertEqual(g["source"], {"lane": "ats-provider", "provider": "greenhouse", "board": "miro"})
        ok = j["4400000001"]; self.assertEqual(ok["source"]["board"], "Search"); self.assertEqual(ok["notes"], "fine")
        self.assertEqual(j["4400000002"]["source"]["board"], "Inbox"); self.assertEqual(j["4400000002"]["last_seen"], "2026-07-12")
        for e in j.values():
            self.assertIn(e["status"], {"seen","approved","applied","rejected","skipped"}); self.assertIn(e["tier"], {"A","B","C","D","untiered"})
            for v in e.get("gate_violations", []): self.assertIn(v["kind"], KINDS)
    def test_idempotent(self):
        self.run_it(); once = open(self.t).read(); s = self.run_it(); self.assertEqual(s["changed"], 0); self.assertEqual(open(self.t).read(), once)
    def test_validator_passes_after(self):
        self.run_it()
        chk = subprocess.run(["jq", "-e", '[.jobs[] | select(.status as $s | ["seen","approved","applied","rejected","skipped"] | index($s) | not)] | length == 0', self.t], capture_output=True)
        self.assertEqual(chk.returncode, 0)
    def test_corrupt_json(self):
        with open(self.t, "w") as f: f.write("{invalid json")
        p = subprocess.run(["python3", os.path.join(S, "migrate_tracker_v3.py"), "--tracker", self.t, "--sources", os.path.join(self.d, "sources.json")], capture_output=True, text=True)
        self.assertEqual(p.returncode, 1); self.assertIn("bad input", p.stderr); self.assertNotIn("Traceback", p.stderr)
    def test_bad_input_jobs_not_object(self):
        with open(self.t, "w") as f: json.dump({"schema_version": 2, "jobs": "nope"}, f)
        p = subprocess.run(["python3", os.path.join(S, "migrate_tracker_v3.py"), "--tracker", self.t], capture_output=True, text=True)
        self.assertEqual(p.returncode, 1); self.assertIn("bad input", p.stderr); self.assertNotIn("Traceback", p.stderr)
    def test_gate_violations_mixed_types(self):
        t = json.load(open(self.t)); t["jobs"]["999"] = {"id": "999", "title": "Test", "company": "Test Co", "source": "search", "gate_violations": [None, 42, "contract_type", {"detail": "detail_x"}]}
        with open(self.t, "w") as f: json.dump(t, f)
        s = self.run_it(); result = json.load(open(self.t)); gv = result["jobs"]["999"]["gate_violations"]
        self.assertEqual(len(gv), 4); self.assertEqual(gv[0], {"kind": "custom", "detail": "None"}); self.assertEqual(gv[1], {"kind": "custom", "detail": "42"}); self.assertEqual(gv[2]["kind"], "contract_type"); self.assertEqual(gv[3]["kind"], "custom")
    def test_namespaced_legacy_note(self):
        t = json.load(open(self.t)); t["jobs"]["greenhouse__miro__999"] = {"id": "greenhouse__miro__999", "title": "Test", "company": "Miro", "source": "greenhouse (via aggregator XYZ)", "status": "seen"}
        with open(self.t, "w") as f: json.dump(t, f)
        s = self.run_it(); result = json.load(open(self.t)); e = result["jobs"]["greenhouse__miro__999"]
        self.assertEqual(e["source"], {"lane": "ats-provider", "provider": "greenhouse", "board": "miro"}); self.assertIn("source(legacy): greenhouse (via aggregator XYZ)", e["notes"])
    def test_non_dict_entries(self):
        t = json.load(open(self.t)); t["jobs"]["999"] = "not a dict"; t["jobs"]["888"] = None
        with open(self.t, "w") as f: json.dump(t, f)
        p = subprocess.run(["python3", os.path.join(S, "migrate_tracker_v3.py"), "--tracker", self.t, "--sources", os.path.join(self.d, "sources.json")], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0); s = json.loads(p.stdout); self.assertEqual(s["by_rule"]["skipped_non_dict"], 2); self.assertIn("migrate: warning: 2 non-dict entries left untouched", p.stderr)
    def test_corrupt_sources_json(self):
        with open(os.path.join(self.d, "sources.json"), "w") as f: f.write("{bad json")
        p = subprocess.run(["python3", os.path.join(S, "migrate_tracker_v3.py"), "--tracker", self.t, "--sources", os.path.join(self.d, "sources.json")], capture_output=True, text=True)
        self.assertEqual(p.returncode, 1); self.assertIn("bad input (sources.json:", p.stderr); self.assertNotIn("Traceback", p.stderr)
    def test_status_as_applied(self):
        t = json.load(open(self.t)); t["jobs"]["int1"] = {"id": "int1", "title": "Test", "company": "Test Co", "source": "search", "status": "interviewing", "tier": "B"}
        with open(self.t, "w") as f: json.dump(t, f)
        s = self.run_it(); result = json.load(open(self.t)); e = result["jobs"]["int1"]
        self.assertEqual(e["status"], "applied"); self.assertIn("status(legacy): interviewing", e["notes"])
    def test_two_segment_namespaced_with_object_source(self):
        t = json.load(open(self.t)); t["jobs"]["justjoinit__relout-linux"] = {"id": "justjoinit__relout-linux", "title": "Test", "company": "Test Co", "source": {"board": "html", "name": "JustJoin.it"}, "status": "seen"}
        with open(self.t, "w") as f: json.dump(t, f)
        s = self.run_it(); result = json.load(open(self.t)); e = result["jobs"]["justjoinit__relout-linux"]
        self.assertEqual(e["source"], {"lane": "aggregator", "provider": "justjoinit", "board": "html"})
    def test_two_segment_namespaced_with_inbox_source(self):
        t = json.load(open(self.t)); t["jobs"]["verda__7998465"] = {"id": "verda__7998465", "title": "Test", "company": "Test Co", "source": "Inbox", "status": "seen"}
        with open(self.t, "w") as f: json.dump(t, f)
        s = self.run_it(); result = json.load(open(self.t)); e = result["jobs"]["verda__7998465"]
        self.assertEqual(e["source"]["board"], "Inbox"); self.assertEqual(e["source"]["provider"], "verda")
    def test_slug_matching_itcontracts(self):
        t = json.load(open(self.t)); t["jobs"]["itcontracts__287911"] = {"id": "itcontracts__287911", "title": "Test", "company": "Test Co", "source": "aggregator", "status": "seen"}
        with open(self.t, "w") as f: json.dump(t, f)
        s = self.run_it(); result = json.load(open(self.t)); e = result["jobs"]["itcontracts__287911"]
        self.assertEqual(e["source"]["lane"], "freelance-marketplace"); self.assertEqual(e["source"]["provider"], "itcontracts")
if __name__ == "__main__":
    unittest.main()

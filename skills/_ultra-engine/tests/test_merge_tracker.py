import json, os, shutil, subprocess, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "scripts", "merge_tracker.py")
FX = os.path.join(HERE, "fixtures")

def delta(entries, counts=None):
    n = len(entries)
    return {"status": "ok", "counts": counts or {"scanned": n, "matched": n, "dropped_explicit_violation": 0, "returned": n, "capped": False},
            "deltas": entries, "errors": [], "continuation_cursor": None}

def entry(i, company="Initech", title="Platform Engineer", loc="Remote", lane="remote-board", prov="remotive", board="remotive", jd=True):
    return {"id": i, "url": f"https://x/{i}", "title": title, "company": company, "location": loc,
            "source": {"lane": lane, "provider": prov, "board": board},
            "fingerprint": f"{company.lower()}|{title.lower()}|{loc.lower()}",
            "posted_at": "2026-07-01", "jd_path": f"jds/{i}.txt" if jd else None, "tags": []}

class T(unittest.TestCase):
    def setUp(self):
        self.ws = tempfile.mkdtemp(); os.makedirs(os.path.join(self.ws, "jds"))
        self.tracker = os.path.join(self.ws, "tracker.json")
        shutil.copy(os.path.join(FX, "tracker-mini.json"), self.tracker)
        self.jd("greenhouse__miro__7")  # fixture entry carries a jd_path — final validation checks the file exists

    def jd(self, i): open(os.path.join(self.ws, "jds", f"{i}.txt"), "w").write("jd")

    def run_merge(self, *deltas):
        paths = []
        for k, d in enumerate(deltas):
            p = os.path.join(self.ws, f"d{k}.json"); json.dump(d, open(p, "w")); paths.append(p)
        return subprocess.run(["python3", SCRIPT, "--ws", self.ws, "--tracker", self.tracker,
                               "--today", "2026-07-02"] + paths, capture_output=True, text=True)

    def load(self): return json.load(open(self.tracker))

    def test_new_role_merges_with_lazy_fields(self):
        e = entry("remotive__remotive__9"); self.jd(e["id"])
        p = self.run_merge(delta([e])); self.assertEqual(p.returncode, 0, p.stderr)
        t = self.load(); j = t["jobs"]["remotive__remotive__9"]
        self.assertEqual(j["status"], "seen"); self.assertEqual(j["tier"], "untiered")
        self.assertEqual(j["first_seen"], "2026-07-02")
        self.assertNotIn("competitiveness", j)          # written lazily — omitted, never null
        self.assertEqual(t["schema_version"], 3)
        self.assertEqual(t["stats"]["total_seen"], len(t["jobs"]))

    def test_known_fingerprint_records_sighting_not_duplicate(self):
        e = entry("jobicy__jobicy__1", company="Miro", title="Platform Engineer", loc="Remote",
                  lane="remote-board", prov="jobicy", board="jobicy"); self.jd(e["id"])
        p = self.run_merge(delta([e])); self.assertEqual(p.returncode, 0, p.stderr)
        t = self.load()
        self.assertNotIn("jobicy__jobicy__1", t["jobs"])
        seen = t["jobs"]["greenhouse__miro__7"]["also_seen_on"]
        self.assertIn({"lane": "remote-board", "provider": "jobicy", "board": "jobicy"}, seen)
        self.assertEqual(t["jobs"]["greenhouse__miro__7"]["last_seen"], "2026-07-02")

    def test_within_run_collision_ats_wins(self):
        a = entry("aggro__board__1", company="Vandelay", lane="aggregator", prov="aggro", board="board")
        g = entry("greenhouse__vandelay__2", company="Vandelay", lane="ats", prov="greenhouse", board="vandelay")
        self.jd(a["id"]); self.jd(g["id"])
        p = self.run_merge(delta([a]), delta([g])); self.assertEqual(p.returncode, 0, p.stderr)
        t = self.load()
        self.assertIn("greenhouse__vandelay__2", t["jobs"]); self.assertNotIn("aggro__board__1", t["jobs"])
        self.assertIn({"lane": "aggregator", "provider": "aggro", "board": "board"},
                      t["jobs"]["greenhouse__vandelay__2"]["also_seen_on"])

    def test_url_upgrade_on_existing_incumbent(self):
        # incumbent 4001 (linkedin, rank 1) vs incoming ATS (rank 0) same fingerprint
        e = entry("greenhouse__acme__5", company="Acme", title="Senior SRE", loc="Amsterdam",
                  lane="ats", prov="greenhouse", board="acme"); self.jd(e["id"])
        p = self.run_merge(delta([e])); self.assertEqual(p.returncode, 0, p.stderr)
        t = self.load(); j = t["jobs"]["4001"]
        self.assertEqual(j["url"], "https://x/greenhouse__acme__5")
        self.assertIn("canonical upgraded to greenhouse", j["notes"])
        self.assertNotIn("greenhouse__acme__5", t["jobs"])
        self.assertEqual(j["jd_path"], "jds/greenhouse__acme__5.txt")

    def test_invalid_delta_aborts_untouched(self):
        e = entry("x__y__1"); e["source"] = "prose string"; self.jd("x__y__1")
        before = open(self.tracker).read()
        p = self.run_merge(delta([e]))
        self.assertEqual(p.returncode, 1)
        self.assertEqual(before, open(self.tracker).read())

    def test_location_variant_upgrades_not_duplicates(self):
        # naive producer fingerprint ("...amsterdam area") must NOT defeat dedupe:
        # the merge recomputes via jq, matching incumbent 4001 ("Amsterdam")
        e = entry("greenhouse__acme__9", company="Acme", title="Senior SRE", loc="Amsterdam Area",
                  lane="ats", prov="greenhouse", board="acme")
        self.jd(e["id"])
        p = self.run_merge(delta([e]))
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(json.loads(p.stdout.strip()),
                         {"merged": 0, "collisions_also_seen": 1, "url_upgrades": 1, "skipped_known": 0})
        t = self.load()
        self.assertNotIn("greenhouse__acme__9", t["jobs"])
        self.assertEqual(t["jobs"]["4001"]["url"], "https://x/greenhouse__acme__9")

    def test_rejected_fingerprint_does_not_block_new_entry(self):
        # 4002 (rejected) shares this fingerprint after normalisation; rejected entries
        # are excluded from the live set, so the role merges as genuinely new
        e = entry("jobicy__jobicy__7", company="Globex", title="DevOps Engineer", loc="Berlin",
                  lane="remote-board", prov="jobicy", board="jobicy")
        self.jd(e["id"])
        p = self.run_merge(delta([e]))
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("jobicy__jobicy__7", self.load()["jobs"])

if __name__ == "__main__":
    unittest.main()

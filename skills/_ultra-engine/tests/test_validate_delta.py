import json, os, subprocess, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "scripts", "validate_delta.py")

def run(ws, payload):
    f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    json.dump(payload, f); f.close()
    p = subprocess.run(["python3", SCRIPT, "--ws", ws, f.name], capture_output=True, text=True)
    os.unlink(f.name); return p

class T(unittest.TestCase):
    def setUp(self):
        self.ws = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.ws, "jds"))
        with open(os.path.join(HERE, "fixtures", "delta-good.json")) as fh:
            self.good = json.load(fh)
        open(os.path.join(self.ws, "jds", "remotive__remotive__555.txt"), "w").write("full jd text")

    def test_good_passes(self):
        self.assertEqual(run(self.ws, self.good).returncode, 0)

    def test_prose_source_rejected(self):
        bad = json.loads(json.dumps(self.good)); bad["deltas"][0]["source"] = "ultramode [Remotive]"
        p = run(self.ws, bad); self.assertEqual(p.returncode, 1); self.assertIn("source", p.stderr)

    def test_missing_jd_file_rejected(self):
        bad = json.loads(json.dumps(self.good)); bad["deltas"][0]["jd_path"] = "jds/nope.txt"
        self.assertEqual(run(self.ws, bad).returncode, 1)

    def test_bad_id_rejected(self):
        bad = json.loads(json.dumps(self.good)); bad["deltas"][0]["id"] = "himalayas-devops-alma"
        p = run(self.ws, bad); self.assertEqual(p.returncode, 1); self.assertIn("id", p.stderr)

    def test_undisclosed_cap_rejected(self):
        bad = json.loads(json.dumps(self.good)); bad["counts"]["capped"] = False  # 2 < 6-3 ⇒ must be true
        self.assertEqual(run(self.ws, bad).returncode, 1)

    def test_missing_counts_rejected(self):
        bad = json.loads(json.dumps(self.good)); del bad["counts"]
        self.assertEqual(run(self.ws, bad).returncode, 1)

if __name__ == "__main__":
    unittest.main()

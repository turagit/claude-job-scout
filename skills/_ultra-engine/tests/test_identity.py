import os, subprocess, sys, unittest

SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "scripts")
sys.path.insert(0, os.path.join(SCRIPTS, "lib"))
from identity import norm_host, identity_key  # noqa: E402


class TestNormHost(unittest.TestCase):
    def test_spelling_variants_collapse(self):
        for u in ("https://WWW.Example.com/jobs?x=1",
                  "http://example.com./",
                  "example.com",
                  "https://user@example.com:443/board#top"):
            self.assertEqual("example.com", norm_host(u), u)

    def test_subdomain_is_significant(self):
        self.assertEqual("jobs.example.com", norm_host("https://jobs.example.com/"))

    def test_identity_key(self):
        self.assertEqual("malt.nl|freelance-marketplace",
                         identity_key("https://www.Malt.nl/", "freelance-marketplace"))

    def test_cli(self):
        out = subprocess.run(
            ["python3", os.path.join(SCRIPTS, "lib", "identity.py"),
             "key", "https://www.jobs.lu/en/", "national-board"],
            capture_output=True, text=True)
        self.assertEqual(0, out.returncode)
        self.assertEqual("jobs.lu|national-board", out.stdout.strip())


if __name__ == "__main__":
    unittest.main()

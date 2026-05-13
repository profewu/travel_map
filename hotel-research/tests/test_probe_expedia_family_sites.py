from pathlib import Path
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "probe_expedia_family_sites.py"


class ProbeExpediaFamilySitesTest(unittest.TestCase):
    def test_probe_script_uses_cloakbrowser_cdp_connection(self):
        source = SCRIPT.read_text(encoding="utf-8")

        self.assertIn("connect_over_cdp", source)
        self.assertIn("--remote-debugging-port", source)
        self.assertIn("ensure_binary", source)
        self.assertIn("build_args", source)
        self.assertNotIn("launch_async", source)


if __name__ == "__main__":
    unittest.main()

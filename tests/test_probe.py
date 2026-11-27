import unittest
from unittest.mock import patch, MagicMock
from netpulse.probe import validate_target, probe_host, probe_many

class ValidationTests(unittest.TestCase):
    def test_ipv4(self):
        self.assertEqual(validate_target("192.168.1.1"), "192.168.1.1")
    def test_ipv6(self):
        self.assertEqual(validate_target("2001:db8::1"), "2001:db8::1")
    def test_hostname(self):
        self.assertEqual(validate_target("example.com"), "example.com")
    def test_rejects_shell_injection(self):
        with self.assertRaises(ValueError):
            validate_target("127.0.0.1; rm -rf /")
    def test_rejects_empty(self):
        with self.assertRaises(ValueError):
            validate_target("  ")

class ProbeTests(unittest.TestCase):
    @patch("netpulse.probe.shutil.which", return_value="/bin/ping")
    @patch("netpulse.probe.subprocess.run")
    def test_successful_probe(self, run, _which):
        run.return_value = MagicMock(stdout="64 bytes from 1.1.1.1: time=12.5 ms\n64 bytes from 1.1.1.1: time=10.5 ms", stderr="", returncode=0)
        result = probe_host("1.1.1.1", count=2)
        self.assertTrue(result.reachable)
        self.assertEqual(result.received, 2)
        self.assertEqual(result.average_latency_ms, 11.5)
    @patch("netpulse.probe.shutil.which", return_value=None)
    def test_missing_ping(self, _which):
        result = probe_host("1.1.1.1", count=2)
        self.assertFalse(result.reachable)
        self.assertIn("not found", result.error)

if __name__ == "__main__":
    unittest.main()

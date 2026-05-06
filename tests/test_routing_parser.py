"""
Tests unitaires pour le parseur de tables de routage PCH (src/routing/parser.py).
"""

import os
import tempfile
import unittest

from src.routing.parser import (
    _flatten_as_path,
    compute_ip_coverage,
    get_as_paths,
    parse_routing_table,
)

# ── Contenu d'une table de routage fictive ────────────────────────────────────
SAMPLE_TABLE = """\
BGP table version is 1, local router ID is 194.42.48.1
Status codes: s suppressed, d damped, h history, * valid, > best, i - internal
Origin codes: i - IGP, e - EGP, ? - incomplete

   Network          Next Hop            Metric LocPrf Weight Path
*> 1.0.0.0/24       194.42.48.80             0      0      0 13335 i
*> 1.0.138.0/24     194.42.48.80             0      0      0 6939 38040 23969 i
*> 1.0.139.0/24     194.42.48.80             0      0      0 6939 38040 23969 i
*  1.0.138.0/24     194.42.48.99             0      0      0 3356 38040 23969 i
*> 8.8.8.0/24       194.42.48.80             0      0      0 15169 i
*> 192.0.2.0/24     194.42.48.80             0      0      0 64500 {64501,64502} i
"""


def _write_table(content: str) -> str:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8")
    f.write(content)
    f.close()
    return f.name


class TestFlattenAsPath(unittest.TestCase):

    def test_simple_path(self):
        self.assertEqual(_flatten_as_path("6939 38040 23969"), [6939, 38040, 23969])

    def test_as_set_takes_first_member(self):
        result = _flatten_as_path("{64501,64502}")
        self.assertEqual(result, [64501])

    def test_consecutive_duplicates_removed(self):
        self.assertEqual(_flatten_as_path("100 100 200"), [100, 200])

    def test_empty_string(self):
        self.assertEqual(_flatten_as_path(""), [])


class TestParseRoutingTable(unittest.TestCase):

    def setUp(self):
        self.tmpfile = _write_table(SAMPLE_TABLE)

    def tearDown(self):
        os.unlink(self.tmpfile)

    def test_parses_correct_count(self):
        # 5 lignes *> valides + 1 ligne * (non best) = 6 lignes BGP
        entries = parse_routing_table(self.tmpfile)
        self.assertEqual(len(entries), 6)

    def test_first_entry_prefix(self):
        entries = parse_routing_table(self.tmpfile)
        self.assertEqual(entries[0]["prefix"], "1.0.0.0/24")

    def test_as_path_is_list_of_ints(self):
        entries = parse_routing_table(self.tmpfile)
        for e in entries:
            self.assertIsInstance(e["as_path"], list)
            for asn in e["as_path"]:
                self.assertIsInstance(asn, int)

    def test_file_not_found_raises(self):
        with self.assertRaises(FileNotFoundError):
            parse_routing_table("/nonexistent/path.txt")


class TestComputeIpCoverage(unittest.TestCase):

    def setUp(self):
        self.tmpfile = _write_table(SAMPLE_TABLE)

    def tearDown(self):
        os.unlink(self.tmpfile)

    def test_unique_prefixes_deduped(self):
        result = compute_ip_coverage(self.tmpfile)
        # 1.0.138.0/24 apparaît 2x → compté une seule fois
        self.assertEqual(result["unique_prefixes"], 5)

    def test_ip_count_is_sum_of_prefix_sizes(self):
        result = compute_ip_coverage(self.tmpfile)
        # 5 préfixes /24 → 5 × 256 = 1280
        self.assertEqual(result["ip_count"], 5 * 256)

    def test_total_ipv4(self):
        result = compute_ip_coverage(self.tmpfile)
        self.assertEqual(result["total_ipv4"], 2 ** 32)

    def test_percentage_positive(self):
        result = compute_ip_coverage(self.tmpfile)
        self.assertGreater(result["percentage"], 0)
        self.assertLessEqual(result["percentage"], 100)


class TestGetAsPaths(unittest.TestCase):

    def setUp(self):
        self.tmpfile = _write_table(SAMPLE_TABLE)

    def tearDown(self):
        os.unlink(self.tmpfile)

    def test_returns_list_of_lists(self):
        paths = get_as_paths(self.tmpfile)
        self.assertIsInstance(paths, list)
        for p in paths:
            self.assertIsInstance(p, list)

    def test_known_path_present(self):
        paths = get_as_paths(self.tmpfile)
        self.assertIn([6939, 38040, 23969], paths)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import argparse
import json
import os
import sys
import unittest
from types import SimpleNamespace

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from scripts.backfill_intake_v6_order_snapshots import _order_looks_like_v6, _parse_args  # noqa: E402


class TestBackfillIntakeV6OrderSnapshots(unittest.TestCase):
    def test_detects_v6_order_from_notes_linkage(self):
        order = SimpleNamespace(
            notes=json.dumps({"intake_v6_order_linkage_v1": {"source_quote_id": 11}}),
            snapshot_line_items=None,
        )
        self.assertTrue(_order_looks_like_v6(order))

    def test_detects_v6_order_from_snapshot_created_from(self):
        order = SimpleNamespace(
            notes=None,
            snapshot_line_items=json.dumps({"created_from": "intake_v6"}),
        )
        self.assertTrue(_order_looks_like_v6(order))

    def test_ignores_non_v6_order(self):
        order = SimpleNamespace(
            notes=json.dumps({"some_other_linkage": {"source_quote_id": 3}}),
            snapshot_line_items=json.dumps({"created_from": "intake_v4"}),
        )
        self.assertFalse(_order_looks_like_v6(order))

    def test_parse_args_supports_plan_generation_flags(self):
        original_argv = sys.argv
        try:
            sys.argv = [
                "backfill_intake_v6_order_snapshots.py",
                "6",
                "7",
                "--generate-plans",
                "--no-skip-existing-plans",
                "--fail-fast",
            ]
            args = _parse_args()
        finally:
            sys.argv = original_argv

        self.assertIsInstance(args, argparse.Namespace)
        self.assertEqual(args.order_ids, [6, 7])
        self.assertTrue(args.generate_plans)
        self.assertTrue(args.no_skip_existing_plans)
        self.assertTrue(args.fail_fast)


if __name__ == "__main__":
    unittest.main()
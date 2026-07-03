import unittest

from routers.execution import _read_codes


class _RowsResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class _FakeSession:
    def __init__(self, execute_plan):
        self._execute_plan = list(execute_plan)
        self.execute_calls = 0
        self.rollback_calls = 0

    async def execute(self, _sql):
        self.execute_calls += 1
        item = self._execute_plan.pop(0)
        if isinstance(item, Exception):
            raise item
        return _RowsResult(item)

    async def rollback(self):
        self.rollback_calls += 1


class TestExecutionRegistryProbe(unittest.IsolatedAsyncioTestCase):
    async def test_read_codes_rolls_back_then_uses_fallback(self):
        db = _FakeSession(
            execute_plan=[
                Exception("relation public.skills does not exist"),
                [("QC",), ("CNC",)],
            ]
        )

        rows = await _read_codes(
            db,
            "SELECT skill_code FROM public.skills",
            "SELECT skill_code FROM skills",
        )

        self.assertEqual(rows, ["QC", "CNC"])
        self.assertEqual(db.rollback_calls, 1)
        self.assertEqual(db.execute_calls, 2)

    async def test_read_codes_returns_none_when_both_fail(self):
        db = _FakeSession(
            execute_plan=[
                Exception("primary missing"),
                Exception("fallback missing"),
            ]
        )

        rows = await _read_codes(
            db,
            "SELECT skill_code FROM public.skills",
            "SELECT skill_code FROM skills",
        )

        self.assertIsNone(rows)
        self.assertEqual(db.rollback_calls, 2)
        self.assertEqual(db.execute_calls, 2)

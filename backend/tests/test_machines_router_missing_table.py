import pytest
from fastapi import HTTPException

from routers.machines import get_machine, get_machines_stats, list_machines


class _FakeResult:
    def __init__(self, scalar_value=None):
        self._scalar_value = scalar_value

    def scalar(self):
        return self._scalar_value


class _FakeDb:
    def __init__(self, table_exists: bool):
        self._table_exists = table_exists
        self.executed_sql = []

    async def execute(self, sql, params=None):
        sql_text = str(getattr(sql, "text", sql))
        self.executed_sql.append(sql_text)

        if "sqlite_master" in sql_text:
            return _FakeResult(1 if self._table_exists else None)

        if "to_regclass('public.machines')" in sql_text:
            return _FakeResult("machines" if self._table_exists else None)

        raise AssertionError(f"Unexpected query while table is missing: {sql_text}")


@pytest.mark.asyncio
async def test_list_machines_returns_empty_when_table_missing():
    db = _FakeDb(table_exists=False)

    result = await list_machines(db=db)

    assert result == []
    assert len(db.executed_sql) == 1
    assert "sqlite_master" in db.executed_sql[0]


@pytest.mark.asyncio
async def test_get_machines_stats_returns_zero_payload_when_table_missing():
    db = _FakeDb(table_exists=False)

    result = await get_machines_stats(db=db)

    assert result == {
        "total": 0,
        "available": 0,
        "statusCounts": {},
        "typeCounts": {},
    }
    assert len(db.executed_sql) == 1
    assert "sqlite_master" in db.executed_sql[0]


@pytest.mark.asyncio
async def test_get_machine_returns_404_when_table_missing():
    db = _FakeDb(table_exists=False)

    with pytest.raises(HTTPException) as exc_info:
        await get_machine("MCH-ANY", db=db)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Machine 'MCH-ANY' not found"
    assert len(db.executed_sql) == 1
    assert "sqlite_master" in db.executed_sql[0]

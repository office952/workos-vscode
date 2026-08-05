"""Canonical SQLite connection PRAGMA helpers.

Resource State R3 requires ``PRAGMA foreign_keys=ON`` on every product
SQLite connection path (DatabaseManager, Alembic, IsolatedDBFixture, and
new R3 sync/async test engines). Activation must come from a SQLAlchemy
``connect`` event listener — not ad-hoc per-test PRAGMA after connect.
"""

from __future__ import annotations

from sqlalchemy import event
from sqlalchemy.engine import Engine


def enable_sqlite_foreign_keys(dbapi_connection, connection_record=None) -> None:
    """Enable SQLite foreign key enforcement for one DB-API connection."""
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
    finally:
        cursor.close()


def register_sqlite_foreign_keys(engine) -> None:
    """Register the FK pragma listener on a sync or async SQLAlchemy engine.

    Safe to call once per engine. For ``AsyncEngine``, the listener is
    attached to ``engine.sync_engine``. Non-SQLite engines are ignored.
    """
    sync_engine = getattr(engine, "sync_engine", engine)
    if not isinstance(sync_engine, Engine):
        return
    if sync_engine.dialect.name != "sqlite":
        return
    # Avoid duplicate listeners if init paths re-run in the same process.
    if getattr(sync_engine, "_workos_sqlite_fk_listener", False):
        return
    event.listen(sync_engine, "connect", enable_sqlite_foreign_keys)
    setattr(sync_engine, "_workos_sqlite_fk_listener", True)

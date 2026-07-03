"""Shared DB fixture for isolating test suites.

Root cause of the discovery failure: every suite imports the global
`core.database.db_manager` singleton, but each suite assumed it owned the
underlying engine / sessionmaker. When `unittest discover` runs several
suites in the same process, the first suite that finishes closes the
engine (or binds a different tempfile DB) and the next suite tries to
query tables that don't exist in that file.

This module provides a tiny helper every suite can call in
`setUpClass` / `tearDownClass` to get its OWN engine + sessionmaker,
patch them onto `db_manager`, and cleanly restore the previous state
afterwards. It also owns the per-suite tempfile lifecycle.

Usage (synchronous unittest.TestCase):

    from tests._db_fixture import IsolatedDBFixture

    class MySuite(unittest.TestCase):
        @classmethod
        def setUpClass(cls):
            cls.db = IsolatedDBFixture()
            cls.db.setup()

        @classmethod
        def tearDownClass(cls):
            cls.db.teardown()

The fixture creates all tables from `core.database.Base.metadata` (which
must already have every model imported). Each suite is responsible for
importing its own model modules BEFORE calling `setup()` so the metadata
is complete.
"""

from __future__ import annotations

import asyncio
import os
import tempfile
from typing import Optional

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


class IsolatedDBFixture:
    """Per-suite isolated SQLite DB bound onto the global `db_manager`.

    - Creates a unique tempfile SQLite database (avoids shared `:memory:`
      across connections).
    - Builds its own async engine + sessionmaker.
    - Patches `core.database.db_manager.engine` /
      `core.database.db_manager.async_session_maker` so any code path
      that reaches for the singleton resolves to this suite's DB.
    - Restores the previous values on teardown and removes the tempfile.
    """

    def __init__(self, prefix: str = "mgx_testdb_"):
        self._prefix = prefix
        self._tmp_path: Optional[str] = None
        self._engine = None
        self._session_maker = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        # Saved previous singleton state, restored on teardown.
        self._prev_engine = None
        self._prev_session_maker = None
        self._prev_initialized = None

    # ---- properties ----

    @property
    def session_maker(self) -> async_sessionmaker[AsyncSession]:
        assert self._session_maker is not None, "fixture not set up"
        return self._session_maker

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        assert self._loop is not None, "fixture not set up"
        return self._loop

    @property
    def database_url(self) -> str:
        assert self._tmp_path is not None, "fixture not set up"
        return f"sqlite+aiosqlite:///{self._tmp_path}"

    # ---- lifecycle ----

    def setup(self) -> None:
        # 1) Dedicated event loop per suite (unittest drives sync; we use it for async setup).
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        # 2) Unique on-disk SQLite DB (shared across connections in the same engine).
        fd, self._tmp_path = tempfile.mkstemp(prefix=self._prefix, suffix=".sqlite")
        os.close(fd)

        # 3) Build a fresh engine + sessionmaker for this suite only.
        self._engine = create_async_engine(
            self.database_url,
            echo=False,
            connect_args={"check_same_thread": False},
        )
        self._session_maker = async_sessionmaker(
            self._engine, class_=AsyncSession, expire_on_commit=False
        )

        # 4) Patch the global db_manager so service code that uses it
        #    resolves to THIS suite's DB.
        from core.database import Base, db_manager  # imported late on purpose

        self._prev_engine = getattr(db_manager, "engine", None)
        self._prev_session_maker = getattr(db_manager, "async_session_maker", None)
        self._prev_initialized = getattr(db_manager, "_initialized", None)

        db_manager.engine = self._engine
        db_manager.async_session_maker = self._session_maker
        db_manager._initialized = True

        # 5) Create all tables known to the metadata.
        async def _create_all():
            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

        self._loop.run_until_complete(_create_all())

    def teardown(self) -> None:
        from core.database import db_manager  # late import

        # Dispose this suite's engine first.
        if self._engine is not None and self._loop is not None:
            try:
                self._loop.run_until_complete(self._engine.dispose())
            except Exception:
                pass

        # Restore previous singleton state (likely `None` / `False`).
        try:
            db_manager.engine = self._prev_engine
            db_manager.async_session_maker = self._prev_session_maker
            if self._prev_initialized is not None:
                db_manager._initialized = self._prev_initialized
            else:
                db_manager._initialized = False
        except Exception:
            pass

        # Close the dedicated loop.
        if self._loop is not None:
            try:
                self._loop.close()
            except Exception:
                pass

        # Remove the tempfile.
        if self._tmp_path is not None and os.path.exists(self._tmp_path):
            try:
                os.remove(self._tmp_path)
            except OSError:
                pass

        self._engine = None
        self._session_maker = None
        self._loop = None
        self._tmp_path = None

    # ---- convenience helpers ----

    def run(self, coro):
        """Run a coroutine on this fixture's event loop."""
        return self.loop.run_until_complete(coro)

    def reset_tables(self, tables) -> None:
        """Delete all rows from the given ORM tables (preserves schema)."""

        async def _do():
            async with self._session_maker() as s:
                for t in tables:
                    await s.execute(t.__table__.delete())
                await s.commit()

        self.run(_do())
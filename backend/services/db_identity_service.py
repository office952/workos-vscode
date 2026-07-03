"""DBIdentityService — diagnostic-only, read-only.

STRICTLY READ-ONLY. This service NEVER writes to any table.

Purpose
-------
Return non-secret identity information about the Postgres connection the
backend runtime is currently bound to, so we can compare it with the
workspace-side DSN and conclusively answer whether the live backend and
the workspace ORM resolve to the same (database, schema, user, host) tuple.

Security contract
-----------------
- NEVER return the full ``DATABASE_URL``.
- NEVER return the Postgres password.
- ``server_addr`` and ``server_port`` are returned ONLY when the feature
  flag ``DEBUG_DB_IDENTITY_EXPOSE_HOST`` is set to a truthy value
  (``"1"``, ``"true"``, ``"yes"``, case-insensitive). Otherwise they are
  omitted and only ``probe_host_fingerprint_sha256_12`` is returned.
- The fingerprint is the first 12 hex chars of
  ``SHA-256(current_database|server_addr|server_port|current_user|current_schema)``.
  It is non-reversible and safe to publish.
- All SQL is executed inside a ``BEGIN TRANSACTION READ ONLY; … COMMIT;``
  wrapper when the underlying dialect supports it (PostgreSQL). On
  dialects that do not support ``SET TRANSACTION READ ONLY`` (e.g. the
  SQLite test fixture), the wrapper degrades gracefully: the payload still
  reports ``read_only_transaction_applied=false`` but performs only
  ``SELECT`` statements — zero writes are ever issued.

Diagnostic-only
---------------
This service is created for a time-boxed investigation
(``plan__backend_db_identity_alignment``). The companion router gate and
cleanup plan are documented in the investigation log. After the
investigation concludes, the router path and this service MUST be
removed or disabled.
"""

from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import text
from sqlalchemy.sql.elements import TextClause
from sqlalchemy.ext.asyncio import AsyncSession


_FEATURE_FLAG_ENABLE = "DEBUG_DB_IDENTITY_ENABLED"
_FEATURE_FLAG_EXPOSE_HOST = "DEBUG_DB_IDENTITY_EXPOSE_HOST"

# Read-only tables the diagnostic inspects for count-only visibility.
# These are the exact five tables mandated by the investigation plan.
#
# SECURITY NOTE (fix for ISSUE-012):
# ----------------------------------
# Each entry is a HARDCODED, module-level, pre-compiled ``text()`` statement.
# Table names are NEVER interpolated into SQL at runtime. There is NO
# user input path into these statements. The mapping is a closed whitelist:
# callers can only look up one of the five keys below. Any other table
# name simply will not be present in the dict and will be reported as
# ``"table_not_present"`` without any SQL being issued.
_READ_ONLY_COUNT_TABLES: tuple[str, ...] = (
    "execution_observation_config",
    "orders",
    "quotes",
    "execution_plan",
    "execution_reality",
)

# Static mapping of whitelisted table name -> pre-compiled read-only
# COUNT statement. Keys are literal, values are constant ``TextClause``
# objects built at import time. No f-strings, no format(), no string
# concatenation involving runtime values. The quoted double-quote
# identifier form is required by PostgreSQL; on SQLite the identifier
# is accepted as well.
_READ_ONLY_COUNT_STATEMENTS: dict[str, TextClause] = {
    "execution_observation_config": text(
        'SELECT count(*) FROM "execution_observation_config"'
    ),
    "orders": text('SELECT count(*) FROM "orders"'),
    "quotes": text('SELECT count(*) FROM "quotes"'),
    "execution_plan": text('SELECT count(*) FROM "execution_plan"'),
    "execution_reality": text('SELECT count(*) FROM "execution_reality"'),
}


def _truthy(val: Optional[str]) -> bool:
    if val is None:
        return False
    return val.strip().lower() in ("1", "true", "yes", "on")


def is_enabled() -> bool:
    """Return True when the diagnostic endpoint is enabled via env flag."""
    return _truthy(os.environ.get(_FEATURE_FLAG_ENABLE))


def expose_host() -> bool:
    """Return True when server_addr / server_port can be returned raw."""
    return _truthy(os.environ.get(_FEATURE_FLAG_EXPOSE_HOST))


def _iso_now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fingerprint(
    current_database: Optional[str],
    server_addr: Optional[str],
    server_port: Optional[int],
    current_user: Optional[str],
    current_schema: Optional[str],
) -> str:
    """SHA-256-12 of the concatenated identity tuple. Non-reversible."""
    parts = [
        current_database or "",
        str(server_addr) if server_addr is not None else "",
        str(server_port) if server_port is not None else "",
        current_user or "",
        current_schema or "",
    ]
    raw = "|".join(parts).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:12]


class DBIdentityService:
    """Diagnostic-only, read-only DB identity probe.

    No method in this class performs any write, DDL, or TCL that commits
    state changes. Only ``SELECT`` and ``SHOW`` statements are issued.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Dialect helpers
    # ------------------------------------------------------------------
    def _dialect_name(self) -> str:
        try:
            return self.db.bind.dialect.name  # type: ignore[union-attr]
        except Exception:
            # Falls back to postgresql assumption; all probes are guarded.
            return "postgresql"

    # ------------------------------------------------------------------
    # Identity probes (read-only)
    # ------------------------------------------------------------------
    async def _probe_identity_postgres(self) -> Dict[str, Any]:
        """Postgres-specific identity probe."""
        out: Dict[str, Any] = {
            "current_database": None,
            "current_schema": None,
            "current_user": None,
            "server_addr": None,
            "server_port": None,
            "search_path": None,
        }
        q = text(
            "SELECT current_database() AS db, "
            "current_schema() AS schema, "
            "current_user AS usr, "
            "inet_server_addr()::text AS addr, "
            "inet_server_port() AS port"
        )
        res = await self.db.execute(q)
        row = res.mappings().first()
        if row is not None:
            out["current_database"] = row.get("db")
            out["current_schema"] = row.get("schema")
            out["current_user"] = row.get("usr")
            out["server_addr"] = row.get("addr")
            port = row.get("port")
            out["server_port"] = int(port) if port is not None else None

        try:
            res2 = await self.db.execute(text("SHOW search_path"))
            sp = res2.scalar()
            out["search_path"] = sp if sp is not None else None
        except Exception as exc:
            out["search_path"] = None
            out["_search_path_error"] = type(exc).__name__
        return out

    async def _probe_identity_sqlite(self) -> Dict[str, Any]:
        """SQLite-specific identity probe (for tests only).

        SQLite has no ``current_database()`` or ``inet_server_addr()``;
        we emulate the fields with non-secret equivalents.
        """
        out: Dict[str, Any] = {
            "current_database": "main",
            "current_schema": "main",
            "current_user": None,
            "server_addr": None,
            "server_port": None,
            "search_path": "main",
        }
        try:
            res = await self.db.execute(text("PRAGMA database_list"))
            rows = res.mappings().all()
            # row: (seq, name, file)
            if rows:
                out["current_database"] = rows[0].get("name") or "main"
        except Exception:
            pass
        return out

    async def _probe_counts(self) -> Dict[str, Any]:
        """Read-only ``SELECT count(*)`` on the five canonical tables.

        SECURITY (fix for ISSUE-012):
          - No f-string / format / concatenation is used to build SQL.
          - The statements are looked up by key from the closed, hardcoded
            whitelist ``_READ_ONLY_COUNT_STATEMENTS`` defined at import time.
          - The loop iterates only over ``_READ_ONLY_COUNT_TABLES``, which
            is a module-level constant tuple. There is no user input.

        Missing tables are reported as ``"table_not_present"`` instead of
        raising; the diagnostic's purpose is to see what this runtime
        actually sees, including gaps.
        """
        counts: Dict[str, Any] = {}
        for t in _READ_ONLY_COUNT_TABLES:
            stmt = _READ_ONLY_COUNT_STATEMENTS.get(t)
            if stmt is None:
                # Defensive: whitelist/key mismatch would be a code-level
                # bug, not a runtime attack surface. Report and continue.
                counts[t] = "error: whitelist_mismatch"
                continue
            try:
                res = await self.db.execute(stmt)
                counts[t] = int(res.scalar() or 0)
            except Exception as exc:
                msg = str(exc)
                if "does not exist" in msg or "no such table" in msg.lower():
                    counts[t] = "table_not_present"
                else:
                    counts[t] = f"error: {type(exc).__name__}"
        return counts

    # ------------------------------------------------------------------
    # Public entrypoint
    # ------------------------------------------------------------------
    async def run(self, release_version: Optional[str] = None) -> Dict[str, Any]:
        """Return the full diagnostic payload.

        Applies a read-only transaction on PostgreSQL. On other dialects
        the transaction guard is skipped but the statements issued are
        still read-only.
        """
        dialect = self._dialect_name()
        ro_applied = False

        # Apply READ ONLY transaction guard (Postgres only).
        if dialect == "postgresql":
            try:
                await self.db.execute(text("SET TRANSACTION READ ONLY"))
                ro_applied = True
            except Exception:
                # SET TRANSACTION can only run at the start of a tx; if the
                # ORM already opened a tx with default access mode, this
                # will no-op. We still ran zero writes below.
                ro_applied = False

        # Probe identity.
        if dialect == "postgresql":
            identity = await self._probe_identity_postgres()
        elif dialect == "sqlite":
            identity = await self._probe_identity_sqlite()
        else:
            identity = {
                "current_database": None,
                "current_schema": None,
                "current_user": None,
                "server_addr": None,
                "server_port": None,
                "search_path": None,
            }

        # Probe counts.
        counts = await self._probe_counts()

        # Compute fingerprint over the FULL identity (even when host is hidden).
        fp = _fingerprint(
            identity.get("current_database"),
            identity.get("server_addr"),
            identity.get("server_port"),
            identity.get("current_user"),
            identity.get("current_schema"),
        )

        # Build public payload with optional host omission.
        payload: Dict[str, Any] = {
            "release_version": release_version,
            "generated_at": _iso_now_utc(),
            "current_database": identity.get("current_database"),
            "current_schema": identity.get("current_schema"),
            "current_user": identity.get("current_user"),
            "search_path": identity.get("search_path"),
            "counts": counts,
            "probe_host_fingerprint_sha256_12": fp,
            "notes": {
                "read_only_endpoint": True,
                "no_write_operations_performed": True,
                "no_credentials_exposed": True,
                "diagnostic_only": True,
                "read_only_transaction_applied": ro_applied,
                "dialect": dialect,
                "host_raw_exposed": expose_host(),
            },
        }
        if expose_host():
            payload["server_addr"] = identity.get("server_addr")
            payload["server_port"] = identity.get("server_port")
        return payload
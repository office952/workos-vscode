"""
Foundation Registries — read-only service layer.

Source of truth: /workspace/docs/spec/spec__foundation_registries_api.md

This module implements the M2 Foundation Registries API backend logic as
SQLAlchemy Core read-only SELECT queries against the live M1 tables
(public.roles, public.skills, public.workcenters).

Design decisions (per approved PRE-CHANGE REPORT, Variant B):
- No ORM models. No registration in Base.metadata. All access via
  ``session.execute(text("SELECT ..."), params)``.
- Read-only. No INSERT / UPDATE / DELETE. Mutations are not importable.
- All bound params are parameterized; there is no string concatenation of
  user input into SQL bodies. Dynamic fragments (sort direction, sort
  column, enum filters) are validated against explicit whitelists before
  being interpolated.
- UUID -> code resolution is done via a single JOIN against the target
  registry table, preserving array order with ``WITH ORDINALITY``.
- Empty-list semantics for administrative roles and the TEMPORARY_PARTIAL
  flag for (OP_HOTWIRE, WC_INSTALLATION_PREP) are resolved from spec-only
  constants (not from DB or from hardcoded UUIDs).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Spec-anchored constants (no UUIDs, only canonical codes).
# ---------------------------------------------------------------------------

# spec__role_skill_model.md §8.1.2 — administrative roles whose
# related_skill_ids[] and related_workcenter_ids[] are intentionally empty.
ADMINISTRATIVE_ROLE_CODES: frozenset[str] = frozenset(
    {"MGR_PRODUCTION", "RESP_INVENTORY", "RESP_SALES_QUOTES"}
)

ADMINISTRATIVE_EMPTY_RATIONALE_SKILLS: str = (
    "Administrative role per spec__role_skill_model.md §8.1.2; "
    "empty related_skill_ids[] is legitimate and NOT a dead information gap."
)

ADMINISTRATIVE_EMPTY_RATIONALE_WORKCENTERS: str = (
    "Administrative role per spec__role_skill_model.md §8.1.2; "
    "empty related_workcenter_ids[] is legitimate."
)

# spec__role_skill_model.md §8.1.3 — TEMPORARY_PARTIAL cell.
TEMPORARY_PARTIAL_CELLS: frozenset[Tuple[str, str]] = frozenset(
    {("OP_HOTWIRE", "WC_INSTALLATION_PREP")}
)

TEMPORARY_PARTIAL_RATIONALE: str = (
    "No dedicated WC_HOTWIRE / foam-cutting workcenter exists in the "
    "16-workcenter canonical registry. Interim assignment to "
    "WC_INSTALLATION_PREP as staging area. A future amendment MAY introduce "
    "a dedicated wc_foam_cutting / wc_hotwire workcenter_type. Flagged per "
    "spec__role_skill_model.md §8.1.3."
)


# ---------------------------------------------------------------------------
# Validation helpers — path param format & code regex.
# ---------------------------------------------------------------------------

# Canonical codes are ALL_CAPS_SNAKE: letters, digits, underscore.
# Length capped defensively at 64.
import re

_CODE_RE: re.Pattern[str] = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")


def is_valid_code(code: str) -> bool:
    """Return True iff ``code`` matches the canonical ALL_CAPS_SNAKE shape."""
    if not isinstance(code, str):
        return False
    return bool(_CODE_RE.match(code))


# ---------------------------------------------------------------------------
# Spec-whitelisted enums (validated server-side; unknown → 400).
# ---------------------------------------------------------------------------

ROLE_TYPE_VALUES: frozenset[str] = frozenset(
    {
        "operation_execution",
        "assembly_install",
        "electrical_led",
        "prepress",
        "design",
        "management",
        "inventory_responsibility",
        "sales_responsibility",
        "logistics",
    }
)

ROLE_ADMINISTRATIVE_TYPES: frozenset[str] = frozenset(
    {"management", "inventory_responsibility", "sales_responsibility"}
)

SKILL_CATEGORY_VALUES: frozenset[str] = frozenset(
    {
        "operation_execution",
        "software_tool",
        "assembly",
        "installation",
        "measurement",
        "electrical",
        "logistics",
        "material_handling",
        "quality_control",
    }
)

WORKCENTER_TYPE_VALUES: frozenset[str] = frozenset(
    {
        "wc_file_prep",
        "wc_cnc_routing",
        "wc_laser_cutting",
        "wc_print_large_format",
        "wc_vinyl_cutting",
        "wc_laminating",
        "wc_edge_bending",
        "wc_plexi_cutting",
        "wc_welding",
        "wc_led_assembly",
        "wc_lightbox_assembly",
        "wc_volumetric_letter_assembly",
        "wc_quality_control",
        "wc_packaging",
        "wc_installation_prep",
        "wc_shipping",
    }
)

OPERATIONAL_STATUS_VALUES: frozenset[str] = frozenset(
    {"active", "maintenance", "inactive", "decommissioned"}
)


# Whitelisted sort columns per resource. Key = API-facing sort name
# (stable public contract), value = SQL column name in the live DB.
# NOTE: The live DB column is ``role_category``; the API continues to use
# ``role_type`` as the public-facing sort/filter parameter per the approved
# Foundation Registries API spec (§9.1), so only the value-side changes.
_ROLE_SORT_COLUMNS: Mapping[str, str] = {
    "role_code": "role_code",
    "role_name": "role_name",
    "role_type": "role_category",
    "created_at": "created_at",
    "updated_at": "updated_at",
}

_SKILL_SORT_COLUMNS: Mapping[str, str] = {
    "skill_code": "skill_code",
    "skill_name": "skill_name",
    "skill_category": "skill_category",
    "created_at": "created_at",
    "updated_at": "updated_at",
}

_WORKCENTER_SORT_COLUMNS: Mapping[str, str] = {
    "workcenter_code": "workcenter_code",
    "workcenter_name": "workcenter_name",
    "workcenter_type": "workcenter_type",
    "operational_status": "operational_status",
    "created_at": "created_at",
    "updated_at": "updated_at",
}


class InvalidQueryParamError(ValueError):
    """Raised when a query param fails whitelist validation.

    Carries ``param`` and ``reason`` for the error envelope.
    """

    def __init__(self, param: str, reason: str):
        super().__init__(f"Invalid query param '{param}': {reason}")
        self.param = param
        self.reason = reason


def _parse_sort(
    sort: Optional[str], whitelist: Mapping[str, str], default_column: str
) -> Tuple[str, str]:
    """Parse a sort expression (e.g. ``-role_code``) against a whitelist.

    Returns a ``(column_sql, direction_sql)`` tuple where both values are
    safe to interpolate into SQL because they come from the whitelist.
    """
    if not sort:
        return whitelist[default_column], "ASC"
    raw = sort.strip()
    if not raw:
        return whitelist[default_column], "ASC"
    direction = "ASC"
    key = raw
    if raw.startswith("-"):
        direction = "DESC"
        key = raw[1:]
    if key not in whitelist:
        raise InvalidQueryParamError(
            "sort",
            f"'{raw}' is not an allowed sort field (allowed: {sorted(whitelist.keys())}).",
        )
    return whitelist[key], direction


def _check_pagination(limit: int, offset: int) -> None:
    if not isinstance(limit, int) or limit < 1 or limit > 200:
        raise InvalidQueryParamError("limit", "must be an integer in [1, 200].")
    if not isinstance(offset, int) or offset < 0:
        raise InvalidQueryParamError("offset", "must be an integer >= 0.")


def _check_q(q: Optional[str]) -> Optional[str]:
    if q is None:
        return None
    if not isinstance(q, str) or len(q) > 100:
        raise InvalidQueryParamError("q", "must be a string of length <= 100.")
    trimmed = q.strip()
    return trimmed or None


def _is_administrative(role_code: str) -> bool:
    """Return True iff role_code is in the administrative whitelist (spec §8.1.2)."""
    return role_code in ADMINISTRATIVE_ROLE_CODES


def _is_temporary_partial(role_code: str, workcenter_code: str) -> bool:
    """Return True iff the (role_code, workcenter_code) pair is the spec §8.1.3 cell."""
    return (role_code, workcenter_code) in TEMPORARY_PARTIAL_CELLS


# ---------------------------------------------------------------------------
# Row -> dict mapping helpers. These produce plain dicts shaped per spec §9.
# ---------------------------------------------------------------------------


def _row_to_role(row: Mapping[str, Any]) -> Dict[str, Any]:
    related_skill_ids = row.get("related_skill_ids") or []
    related_workcenter_ids = row.get("related_workcenter_ids") or []
    related_skill_ids_str: List[str] = [str(v) for v in related_skill_ids]
    related_workcenter_ids_str: List[str] = [str(v) for v in related_workcenter_ids]
    # DB column is ``role_category``; SELECT aliases it as ``role_type`` so
    # the public API field name stays stable per spec §9.1.
    role_type: Optional[str] = row.get("role_type")
    is_operational: bool = bool(role_type) and role_type not in ROLE_ADMINISTRATIVE_TYPES
    return {
        "role_id": str(row["id"]),
        "role_code": row["role_code"],
        "role_name": row["role_name"],
        "role_type": role_type,
        "is_operational": is_operational,
        "description": row.get("description"),
        "active": bool(row.get("active", True)),
        "related_skill_ids": related_skill_ids_str,
        "related_workcenter_ids": related_workcenter_ids_str,
        "skill_count": len(related_skill_ids_str),
        "workcenter_count": len(related_workcenter_ids_str),
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
    }


def _row_to_skill(row: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "skill_id": str(row["id"]),
        "skill_code": row["skill_code"],
        "skill_name": row["skill_name"],
        "skill_category": row.get("skill_category"),
        "description": row.get("description"),
        "active": bool(row.get("active", True)),
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
    }


def _row_to_workcenter(row: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "workcenter_id": str(row["id"]),
        "workcenter_code": row["workcenter_code"],
        "workcenter_name": row["workcenter_name"],
        "workcenter_type": row.get("workcenter_type"),
        "operational_status": row.get("operational_status"),
        "active": bool(row.get("active", True)),
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
    }


def _row_to_skill_embedded(row: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "skill_id": str(row["id"]),
        "skill_code": row["skill_code"],
        "skill_name": row["skill_name"],
        "skill_category": row.get("skill_category"),
        "active": bool(row.get("active", True)),
    }


def _row_to_workcenter_embedded(row: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "workcenter_id": str(row["id"]),
        "workcenter_code": row["workcenter_code"],
        "workcenter_name": row["workcenter_name"],
        "workcenter_type": row.get("workcenter_type"),
        "operational_status": row.get("operational_status"),
        "active": bool(row.get("active", True)),
    }


# ---------------------------------------------------------------------------
# Read-only services.
# ---------------------------------------------------------------------------


class RolesReadService:
    """Read-only access to public.roles plus linkage expansion helpers."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(
        self,
        *,
        role_type: Optional[str] = None,
        is_operational: Optional[bool] = None,
        active: Optional[bool] = True,
        q: Optional[str] = None,
        sort: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        _check_pagination(limit, offset)
        q_norm = _check_q(q)
        if role_type is not None and role_type not in ROLE_TYPE_VALUES:
            raise InvalidQueryParamError(
                "role_type",
                f"must be one of {sorted(ROLE_TYPE_VALUES)}.",
            )
        sort_col, sort_dir = _parse_sort(sort, _ROLE_SORT_COLUMNS, "role_code")

        where_clauses: List[str] = []
        params: Dict[str, Any] = {}
        # DB column is ``role_category``. The public API param name is
        # preserved as ``role_type`` per spec §9.1; only the SQL column
        # name is adjusted here.
        if role_type is not None:
            where_clauses.append("role_category = :role_type")
            params["role_type"] = role_type
        if is_operational is True:
            # Non-administrative role types only.
            where_clauses.append("role_category NOT IN :admin_types")
            params["admin_types"] = tuple(sorted(ROLE_ADMINISTRATIVE_TYPES))
        elif is_operational is False:
            where_clauses.append("role_category IN :admin_types")
            params["admin_types"] = tuple(sorted(ROLE_ADMINISTRATIVE_TYPES))
        if active is True:
            where_clauses.append("active = TRUE")
        elif active is False:
            where_clauses.append("active = FALSE")
        if q_norm is not None:
            where_clauses.append("(role_code ILIKE :q OR role_name ILIKE :q)")
            params["q"] = f"%{q_norm}%"

        where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        # Use expanding IN binding for tuple parameters if needed.
        from sqlalchemy import bindparam

        count_sql = text(f"SELECT COUNT(*) AS c FROM public.roles{where_sql}")
        # Live DB columns: role_id (PK), role_category (NOT role_type).
        # Alias both to the names already consumed by _row_to_role to
        # keep the row-mapper and the API response contract unchanged.
        list_sql = text(
            "SELECT role_id AS id, role_code, role_name, "
            "role_category AS role_type, description, active, "
            "related_skill_ids, related_workcenter_ids, created_at, updated_at "
            f"FROM public.roles{where_sql} "
            f"ORDER BY {sort_col} {sort_dir}, role_code ASC "
            "LIMIT :limit OFFSET :offset"
        )
        if "admin_types" in params:
            count_sql = count_sql.bindparams(bindparam("admin_types", expanding=True))
            list_sql = list_sql.bindparams(bindparam("admin_types", expanding=True))

        total_result = await self.db.execute(count_sql, params)
        total: int = int(total_result.scalar() or 0)

        list_params = {**params, "limit": limit, "offset": offset}
        rows_result = await self.db.execute(list_sql, list_params)
        items = [_row_to_role(r) for r in rows_result.mappings().all()]

        return {
            "items": items,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": total,
                "has_more": offset + len(items) < total,
            },
        }

    async def get_by_code(self, role_code: str) -> Optional[Dict[str, Any]]:
        # Live DB columns: role_id (PK), role_category (NOT role_type).
        # Alias to ``id`` / ``role_type`` to keep _row_to_role unchanged
        # and to keep the public API response shape stable.
        sql = text(
            "SELECT role_id AS id, role_code, role_name, "
            "role_category AS role_type, description, active, "
            "related_skill_ids, related_workcenter_ids, created_at, updated_at "
            "FROM public.roles WHERE role_code = :role_code LIMIT 1"
        )
        result = await self.db.execute(sql, {"role_code": role_code})
        row = result.mappings().first()
        if not row:
            return None
        return _row_to_role(row)

    async def list_role_skills(
        self,
        role_code: str,
        *,
        active: Optional[bool] = True,
        sort: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Return expanded skills for a role, preserving array order by default.

        Returns None if the role does not exist. Otherwise returns the full
        ``RoleSkillsExpanded`` dict shape per spec §9.7.
        """
        # First, resolve the role itself (need role_id + related_skill_ids[]).
        # Live DB: PK column is role_id (aliased to ``id`` for compatibility
        # with the row-mapper contract used throughout this module).
        role_sql = text(
            "SELECT role_id AS id, role_code, related_skill_ids "
            "FROM public.roles WHERE role_code = :role_code LIMIT 1"
        )
        role_row = (await self.db.execute(role_sql, {"role_code": role_code})).mappings().first()
        if not role_row:
            return None

        role_id = str(role_row["id"])
        administrative = _is_administrative(role_code)

        # Optional explicit sort (overrides array order).
        sort_override: Optional[Tuple[str, str]] = None
        if sort is not None:
            allowed = {
                "skill_code": "skill_code",
                "skill_name": "skill_name",
                "skill_category": "skill_category",
            }
            sort_override = _parse_sort(sort, allowed, "skill_code")

        active_clause = ""
        if active is True:
            active_clause = " AND s.active = TRUE"
        elif active is False:
            active_clause = " AND s.active = FALSE"

        if sort_override is None:
            # Preserve canonical order via WITH ORDINALITY.
            # Live DB: skills PK is ``skill_id``; alias to ``id`` for the
            # embedded row-mapper contract.
            skills_sql = text(
                "SELECT s.skill_id AS id, s.skill_code, s.skill_name, "
                "s.skill_category, s.active "
                "FROM public.roles r "
                "LEFT JOIN LATERAL UNNEST(r.related_skill_ids) WITH ORDINALITY AS u(skill_id, ord) ON TRUE "
                "JOIN public.skills s ON s.skill_id = u.skill_id "
                "WHERE r.role_code = :role_code"
                f"{active_clause} "
                "ORDER BY u.ord ASC"
            )
        else:
            col, direction = sort_override
            skills_sql = text(
                "SELECT s.skill_id AS id, s.skill_code, s.skill_name, "
                "s.skill_category, s.active "
                "FROM public.roles r "
                "JOIN public.skills s ON s.skill_id = ANY(r.related_skill_ids) "
                "WHERE r.role_code = :role_code"
                f"{active_clause} "
                f"ORDER BY s.{col} {direction}, s.skill_code ASC"
            )

        rows = (await self.db.execute(skills_sql, {"role_code": role_code})).mappings().all()
        skills = [_row_to_skill_embedded(r) for r in rows]

        empty_intentional = len(skills) == 0 and administrative
        semantics: Dict[str, Any] = {
            "empty_is_intentional": empty_intentional,
            "administrative_role": administrative,
        }
        if empty_intentional:
            semantics["rationale"] = ADMINISTRATIVE_EMPTY_RATIONALE_SKILLS

        return {
            "role_code": role_code,
            "role_id": role_id,
            "skills": skills,
            "skill_count": len(skills),
            "semantics": semantics,
        }

    async def list_role_workcenters(
        self,
        role_code: str,
        *,
        active: Optional[bool] = True,
        operational_status: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        if operational_status is not None and operational_status not in OPERATIONAL_STATUS_VALUES:
            raise InvalidQueryParamError(
                "operational_status",
                f"must be one of {sorted(OPERATIONAL_STATUS_VALUES)}.",
            )

        # Live DB: roles.PK is role_id, workcenters.PK is workcenter_id.
        # Alias both to ``id`` for row-mapper compatibility.
        role_sql = text(
            "SELECT role_id AS id, role_code, related_workcenter_ids "
            "FROM public.roles WHERE role_code = :role_code LIMIT 1"
        )
        role_row = (await self.db.execute(role_sql, {"role_code": role_code})).mappings().first()
        if not role_row:
            return None

        role_id = str(role_row["id"])
        administrative = _is_administrative(role_code)

        active_clause = ""
        if active is True:
            active_clause = " AND w.active = TRUE"
        elif active is False:
            active_clause = " AND w.active = FALSE"

        params: Dict[str, Any] = {"role_code": role_code}
        status_clause = ""
        if operational_status is not None:
            status_clause = " AND w.operational_status = :operational_status"
            params["operational_status"] = operational_status

        wc_sql = text(
            "SELECT w.workcenter_id AS id, w.workcenter_code, w.workcenter_name, "
            "w.workcenter_type, w.operational_status, w.active "
            "FROM public.roles r "
            "LEFT JOIN LATERAL UNNEST(r.related_workcenter_ids) WITH ORDINALITY AS u(workcenter_id, ord) ON TRUE "
            "JOIN public.workcenters w ON w.workcenter_id = u.workcenter_id "
            "WHERE r.role_code = :role_code"
            f"{active_clause}{status_clause} "
            "ORDER BY u.ord ASC"
        )

        rows = (await self.db.execute(wc_sql, params)).mappings().all()
        workcenters = [_row_to_workcenter_embedded(r) for r in rows]

        # TEMPORARY_PARTIAL detection by (role_code, workcenter_code).
        temp_partial = any(
            _is_temporary_partial(role_code, w["workcenter_code"]) for w in workcenters
        )

        flags: Dict[str, Any] = {"temporary_partial": temp_partial}
        if temp_partial:
            flags["temporary_partial_rationale"] = TEMPORARY_PARTIAL_RATIONALE

        empty_intentional = len(workcenters) == 0 and administrative
        semantics: Dict[str, Any] = {
            "empty_is_intentional": empty_intentional,
            "administrative_role": administrative,
        }
        if empty_intentional:
            semantics["rationale"] = ADMINISTRATIVE_EMPTY_RATIONALE_WORKCENTERS

        return {
            "role_code": role_code,
            "role_id": role_id,
            "workcenters": workcenters,
            "workcenter_count": len(workcenters),
            "flags": flags,
            "semantics": semantics,
        }


class SkillsReadService:
    """Read-only access to public.skills."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(
        self,
        *,
        skill_category: Optional[str] = None,
        active: Optional[bool] = True,
        q: Optional[str] = None,
        sort: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        _check_pagination(limit, offset)
        q_norm = _check_q(q)
        if skill_category is not None and skill_category not in SKILL_CATEGORY_VALUES:
            raise InvalidQueryParamError(
                "skill_category",
                f"must be one of {sorted(SKILL_CATEGORY_VALUES)}.",
            )
        sort_col, sort_dir = _parse_sort(sort, _SKILL_SORT_COLUMNS, "skill_code")

        where_clauses: List[str] = []
        params: Dict[str, Any] = {}
        if skill_category is not None:
            where_clauses.append("skill_category = :skill_category")
            params["skill_category"] = skill_category
        if active is True:
            where_clauses.append("active = TRUE")
        elif active is False:
            where_clauses.append("active = FALSE")
        if q_norm is not None:
            where_clauses.append("(skill_code ILIKE :q OR skill_name ILIKE :q)")
            params["q"] = f"%{q_norm}%"

        where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        count_sql = text(f"SELECT COUNT(*) AS c FROM public.skills{where_sql}")
        # Live DB: skills PK is ``skill_id``; alias to ``id`` for mapper.
        list_sql = text(
            "SELECT skill_id AS id, skill_code, skill_name, skill_category, "
            "description, active, created_at, updated_at "
            f"FROM public.skills{where_sql} "
            f"ORDER BY {sort_col} {sort_dir}, skill_code ASC "
            "LIMIT :limit OFFSET :offset"
        )

        total = int((await self.db.execute(count_sql, params)).scalar() or 0)
        list_params = {**params, "limit": limit, "offset": offset}
        rows = (await self.db.execute(list_sql, list_params)).mappings().all()
        items = [_row_to_skill(r) for r in rows]
        return {
            "items": items,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": total,
                "has_more": offset + len(items) < total,
            },
        }

    async def get_by_code(self, skill_code: str) -> Optional[Dict[str, Any]]:
        # Live DB: skills PK is ``skill_id``; alias to ``id`` for mapper.
        sql = text(
            "SELECT skill_id AS id, skill_code, skill_name, skill_category, "
            "description, active, created_at, updated_at "
            "FROM public.skills WHERE skill_code = :skill_code LIMIT 1"
        )
        row = (await self.db.execute(sql, {"skill_code": skill_code})).mappings().first()
        if not row:
            return None
        return _row_to_skill(row)


class WorkcentersReadService:
    """Read-only access to public.workcenters."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(
        self,
        *,
        workcenter_type: Optional[str] = None,
        operational_status: Optional[str] = None,
        active: Optional[bool] = True,
        q: Optional[str] = None,
        sort: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        _check_pagination(limit, offset)
        q_norm = _check_q(q)
        if workcenter_type is not None and workcenter_type not in WORKCENTER_TYPE_VALUES:
            raise InvalidQueryParamError(
                "workcenter_type",
                f"must be one of {sorted(WORKCENTER_TYPE_VALUES)}.",
            )
        if operational_status is not None and operational_status not in OPERATIONAL_STATUS_VALUES:
            raise InvalidQueryParamError(
                "operational_status",
                f"must be one of {sorted(OPERATIONAL_STATUS_VALUES)}.",
            )
        sort_col, sort_dir = _parse_sort(
            sort, _WORKCENTER_SORT_COLUMNS, "workcenter_code"
        )

        where_clauses: List[str] = []
        params: Dict[str, Any] = {}
        if workcenter_type is not None:
            where_clauses.append("workcenter_type = :workcenter_type")
            params["workcenter_type"] = workcenter_type
        if operational_status is not None:
            where_clauses.append("operational_status = :operational_status")
            params["operational_status"] = operational_status
        if active is True:
            where_clauses.append("active = TRUE")
        elif active is False:
            where_clauses.append("active = FALSE")
        if q_norm is not None:
            where_clauses.append("(workcenter_code ILIKE :q OR workcenter_name ILIKE :q)")
            params["q"] = f"%{q_norm}%"

        where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        count_sql = text(f"SELECT COUNT(*) AS c FROM public.workcenters{where_sql}")
        # Live DB: workcenters PK is ``workcenter_id``; alias to ``id``.
        list_sql = text(
            "SELECT workcenter_id AS id, workcenter_code, workcenter_name, "
            "workcenter_type, operational_status, active, created_at, updated_at "
            f"FROM public.workcenters{where_sql} "
            f"ORDER BY {sort_col} {sort_dir}, workcenter_code ASC "
            "LIMIT :limit OFFSET :offset"
        )

        total = int((await self.db.execute(count_sql, params)).scalar() or 0)
        list_params = {**params, "limit": limit, "offset": offset}
        rows = (await self.db.execute(list_sql, list_params)).mappings().all()
        items = [_row_to_workcenter(r) for r in rows]
        return {
            "items": items,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": total,
                "has_more": offset + len(items) < total,
            },
        }

    async def get_by_code(self, workcenter_code: str) -> Optional[Dict[str, Any]]:
        # Live DB: workcenters PK is ``workcenter_id``; alias to ``id``.
        sql = text(
            "SELECT workcenter_id AS id, workcenter_code, workcenter_name, "
            "workcenter_type, operational_status, active, created_at, updated_at "
            "FROM public.workcenters WHERE workcenter_code = :workcenter_code LIMIT 1"
        )
        row = (
            await self.db.execute(sql, {"workcenter_code": workcenter_code})
        ).mappings().first()
        if not row:
            return None
        return _row_to_workcenter(row)


# Public re-exports.
__all__: Sequence[str] = (
    "RolesReadService",
    "SkillsReadService",
    "WorkcentersReadService",
    "InvalidQueryParamError",
    "is_valid_code",
    "ADMINISTRATIVE_ROLE_CODES",
    "TEMPORARY_PARTIAL_CELLS",
)
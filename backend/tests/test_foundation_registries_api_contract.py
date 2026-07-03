"""Pytest contract tests — M2 Foundation Registries API (read-only).

Sprint: S0_6_1_GO_7A_M2_PYTEST_CONTRACT_TESTS
Depends on: S0_6_1_GO_9_M2_API_SCHEMA_MAPPING_FIX_AND_RESMOKE (COMPLETED)

Purpose
-------
Translate the contract-test spec into runnable pytest cases executed against
the FastAPI app via TestClient with mocked service layer.

Constraints (enforced by this file)
-----------------------------------
* Every test is a ``GET`` against ``/api/v1/...`` — no ``POST/PUT/PATCH/DELETE``.
* Zero DB writes, zero SQL, zero migration, zero seed, zero frontend, zero deploy.
* Zero modification of API implementation.
"""

from __future__ import annotations

import os
import re
import sys
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, patch

import pytest

# Ensure backend root is on path
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

# Must set env vars BEFORE importing app
os.environ.setdefault("MGX_IGNORE_INIT_DB", "1")
os.environ.setdefault("MGX_IGNORE_INIT_DATA", "1")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///test_placeholder.db")

from fastapi.testclient import TestClient

from services.foundation_registries import (
    ADMINISTRATIVE_ROLE_CODES,
    ADMINISTRATIVE_EMPTY_RATIONALE_SKILLS,
    ADMINISTRATIVE_EMPTY_RATIONALE_WORKCENTERS,
    InvalidQueryParamError,
    TEMPORARY_PARTIAL_RATIONALE,
)

# --------------------------------------------------------------------------- #
# Configuration                                                               #
# --------------------------------------------------------------------------- #

API_PREFIX = "/api/v1"

# Canonical M1 baseline (spec §3.1).
EXPECTED_ROLES_TOTAL = 20
EXPECTED_SKILLS_TOTAL = 33
EXPECTED_WORKCENTERS_TOTAL = 16

# Administrative roles (spec__role_skill_model.md §8.1.2).
ADMIN_ROLE_CODES = (
    "MGR_PRODUCTION",
    "RESP_INVENTORY",
    "RESP_SALES_QUOTES",
)

# TEMPORARY_PARTIAL anchor (spec__role_skill_model.md §8.1.3).
HOTWIRE_ROLE_CODE = "OP_HOTWIRE"
HOTWIRE_EXPECTED_WC_CODE = "WC_INSTALLATION_PREP"


# --------------------------------------------------------------------------- #
# Mock data factories                                                         #
# --------------------------------------------------------------------------- #


def _make_role(
    code: str,
    *,
    role_type: str = "operation_execution",
    is_operational: bool = True,
    active: bool = True,
    skill_ids: Optional[List[str]] = None,
    wc_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    s_ids = skill_ids or []
    w_ids = wc_ids or []
    return {
        "role_id": f"uuid-{code.lower()}",
        "role_code": code,
        "role_name": f"Role {code}",
        "role_type": role_type,
        "is_operational": is_operational,
        "description": f"Description for {code}",
        "active": active,
        "related_skill_ids": s_ids,
        "related_workcenter_ids": w_ids,
        "skill_count": len(s_ids),
        "workcenter_count": len(w_ids),
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z",
    }


def _make_skill(code: str, *, category: str = "operation_execution", active: bool = True) -> Dict[str, Any]:
    return {
        "skill_id": f"uuid-{code.lower()}",
        "skill_code": code,
        "skill_name": f"Skill {code}",
        "skill_category": category,
        "description": f"Description for {code}",
        "active": active,
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z",
    }


def _make_workcenter(
    code: str, *, wc_type: str = "wc_cnc_routing", status: str = "active", active: bool = True
) -> Dict[str, Any]:
    return {
        "workcenter_id": f"uuid-{code.lower()}",
        "workcenter_code": code,
        "workcenter_name": f"Workcenter {code}",
        "workcenter_type": wc_type,
        "operational_status": status,
        "active": active,
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z",
    }


# Build canonical mock datasets
_OPERATIONAL_ROLES = [
    _make_role(
        f"OP_ROLE_{i:02d}",
        skill_ids=[f"skill-{i}-1", f"skill-{i}-2"],
        wc_ids=[f"wc-{i}-1"],
    )
    for i in range(1, 18)
]
# Override one to be OP_CNC_ROUTER
_OPERATIONAL_ROLES[0] = _make_role(
    "OP_CNC_ROUTER",
    skill_ids=["uuid-cnc-skill-1", "uuid-cnc-skill-2"],
    wc_ids=["uuid-wc-cnc-routing"],
)
# Override one to be OP_HOTWIRE
_OPERATIONAL_ROLES[1] = _make_role(
    "OP_HOTWIRE",
    skill_ids=["uuid-hotwire-skill-1"],
    wc_ids=["uuid-wc-installation-prep"],
)

_ADMIN_ROLES = [
    _make_role(code, role_type="management", is_operational=False, skill_ids=[], wc_ids=[])
    for code in ADMIN_ROLE_CODES
]

ALL_ROLES = sorted(_OPERATIONAL_ROLES + _ADMIN_ROLES, key=lambda r: r["role_code"])
assert len(ALL_ROLES) == EXPECTED_ROLES_TOTAL

ALL_SKILLS = sorted(
    [_make_skill(f"SKILL_{i:02d}") for i in range(1, EXPECTED_SKILLS_TOTAL + 1)],
    key=lambda s: s["skill_code"],
)

ALL_WORKCENTERS = sorted(
    [_make_workcenter(f"WC_{i:02d}") for i in range(1, EXPECTED_WORKCENTERS_TOTAL + 1)],
    key=lambda w: w["workcenter_code"],
)
# Ensure WC_INSTALLATION_PREP exists
ALL_WORKCENTERS[0] = _make_workcenter("WC_INSTALLATION_PREP", wc_type="wc_installation_prep")
ALL_WORKCENTERS = sorted(ALL_WORKCENTERS, key=lambda w: w["workcenter_code"])


def _paginate(items: List[Dict], limit: int, offset: int) -> Dict[str, Any]:
    total = len(items)
    page = items[offset : offset + limit]
    return {
        "items": page,
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": total,
            "has_more": offset + len(page) < total,
        },
    }


# --------------------------------------------------------------------------- #
# Mocked service implementations                                              #
# --------------------------------------------------------------------------- #


class MockRolesReadService:
    """Mock that replicates the service contract without DB access."""

    def __init__(self, db=None):
        pass

    async def list(
        self,
        *,
        role_type=None,
        is_operational=None,
        active=True,
        q=None,
        sort=None,
        limit=50,
        offset=0,
    ):
        from services.foundation_registries import (
            InvalidQueryParamError,
            ROLE_TYPE_VALUES,
            _parse_sort,
            _ROLE_SORT_COLUMNS,
        )

        if role_type is not None and role_type not in ROLE_TYPE_VALUES:
            raise InvalidQueryParamError("role_type", f"must be one of {sorted(ROLE_TYPE_VALUES)}.")

        # Parse sort to validate it
        _parse_sort(sort, _ROLE_SORT_COLUMNS, "role_code")

        items = list(ALL_ROLES)
        if is_operational is True:
            items = [r for r in items if r["is_operational"] is True]
        elif is_operational is False:
            items = [r for r in items if r["is_operational"] is False]
        if role_type is not None:
            items = [r for r in items if r["role_type"] == role_type]
        if q is not None:
            q_lower = q.lower()
            items = [
                r for r in items
                if q_lower in r["role_code"].lower() or q_lower in r["role_name"].lower()
            ]

        # Apply sort
        if sort:
            desc = sort.startswith("-")
            key = sort.lstrip("-")
            items = sorted(items, key=lambda r: r.get(key, ""), reverse=desc)
        else:
            items = sorted(items, key=lambda r: r["role_code"])

        return _paginate(items, limit, offset)

    async def get_by_code(self, role_code: str):
        for r in ALL_ROLES:
            if r["role_code"] == role_code:
                return r
        return None

    async def list_role_skills(self, role_code: str, *, active=True, sort=None):
        role = await self.get_by_code(role_code)
        if role is None:
            return None

        administrative = role_code in ADMINISTRATIVE_ROLE_CODES
        # Build embedded skills from role's skill_ids
        skills = []
        for sid in role["related_skill_ids"]:
            skills.append({
                "skill_id": sid,
                "skill_code": f"SK_{sid.split('-')[-1].upper()}",
                "skill_name": f"Skill {sid}",
                "skill_category": "operation_execution",
                "active": True,
            })

        empty_intentional = len(skills) == 0 and administrative
        semantics = {
            "empty_is_intentional": empty_intentional,
            "administrative_role": administrative,
        }
        if empty_intentional:
            semantics["rationale"] = ADMINISTRATIVE_EMPTY_RATIONALE_SKILLS

        return {
            "role_code": role_code,
            "role_id": role["role_id"],
            "skills": skills,
            "skill_count": len(skills),
            "semantics": semantics,
        }

    async def list_role_workcenters(self, role_code: str, *, active=True, operational_status=None):
        from services.foundation_registries import (
            OPERATIONAL_STATUS_VALUES,
            InvalidQueryParamError,
            TEMPORARY_PARTIAL_CELLS,
            TEMPORARY_PARTIAL_RATIONALE,
        )

        if operational_status is not None and operational_status not in OPERATIONAL_STATUS_VALUES:
            raise InvalidQueryParamError(
                "operational_status",
                f"must be one of {sorted(OPERATIONAL_STATUS_VALUES)}.",
            )

        role = await self.get_by_code(role_code)
        if role is None:
            return None

        administrative = role_code in ADMINISTRATIVE_ROLE_CODES

        # Build embedded workcenters
        workcenters = []
        for wid in role["related_workcenter_ids"]:
            wc_code = "WC_CNC_ROUTING"
            if role_code == HOTWIRE_ROLE_CODE:
                wc_code = HOTWIRE_EXPECTED_WC_CODE
            workcenters.append({
                "workcenter_id": wid,
                "workcenter_code": wc_code,
                "workcenter_name": f"Workcenter {wc_code}",
                "workcenter_type": "wc_cnc_routing",
                "operational_status": "active",
                "active": True,
            })

        # TEMPORARY_PARTIAL detection
        temp_partial = any(
            (role_code, w["workcenter_code"]) in TEMPORARY_PARTIAL_CELLS
            for w in workcenters
        )

        flags = {"temporary_partial": temp_partial}
        if temp_partial:
            flags["temporary_partial_rationale"] = TEMPORARY_PARTIAL_RATIONALE

        empty_intentional = len(workcenters) == 0 and administrative
        semantics = {
            "empty_is_intentional": empty_intentional,
            "administrative_role": administrative,
        }
        if empty_intentional:
            semantics["rationale"] = ADMINISTRATIVE_EMPTY_RATIONALE_WORKCENTERS

        return {
            "role_code": role_code,
            "role_id": role["role_id"],
            "workcenters": workcenters,
            "workcenter_count": len(workcenters),
            "flags": flags,
            "semantics": semantics,
        }


class MockSkillsReadService:
    def __init__(self, db=None):
        pass

    async def list(self, *, skill_category=None, active=True, q=None, sort=None, limit=50, offset=0):
        from services.foundation_registries import (
            InvalidQueryParamError,
            SKILL_CATEGORY_VALUES,
            _parse_sort,
            _SKILL_SORT_COLUMNS,
        )

        if skill_category is not None and skill_category not in SKILL_CATEGORY_VALUES:
            raise InvalidQueryParamError("skill_category", f"must be one of {sorted(SKILL_CATEGORY_VALUES)}.")
        _parse_sort(sort, _SKILL_SORT_COLUMNS, "skill_code")

        items = list(ALL_SKILLS)
        if q:
            q_lower = q.lower()
            items = [s for s in items if q_lower in s["skill_code"].lower() or q_lower in s["skill_name"].lower()]

        if sort:
            desc = sort.startswith("-")
            key = sort.lstrip("-")
            items = sorted(items, key=lambda s: s.get(key, ""), reverse=desc)

        return _paginate(items, limit, offset)

    async def get_by_code(self, skill_code: str):
        for s in ALL_SKILLS:
            if s["skill_code"] == skill_code:
                return s
        return None


class MockWorkcentersReadService:
    def __init__(self, db=None):
        pass

    async def list(self, *, workcenter_type=None, operational_status=None, active=True, q=None, sort=None, limit=50, offset=0):
        from services.foundation_registries import (
            InvalidQueryParamError,
            WORKCENTER_TYPE_VALUES,
            OPERATIONAL_STATUS_VALUES,
            _parse_sort,
            _WORKCENTER_SORT_COLUMNS,
        )

        if workcenter_type is not None and workcenter_type not in WORKCENTER_TYPE_VALUES:
            raise InvalidQueryParamError("workcenter_type", f"must be one of {sorted(WORKCENTER_TYPE_VALUES)}.")
        if operational_status is not None and operational_status not in OPERATIONAL_STATUS_VALUES:
            raise InvalidQueryParamError("operational_status", f"must be one of {sorted(OPERATIONAL_STATUS_VALUES)}.")
        _parse_sort(sort, _WORKCENTER_SORT_COLUMNS, "workcenter_code")

        items = list(ALL_WORKCENTERS)
        if q:
            q_lower = q.lower()
            items = [w for w in items if q_lower in w["workcenter_code"].lower() or q_lower in w["workcenter_name"].lower()]

        if sort:
            desc = sort.startswith("-")
            key = sort.lstrip("-")
            items = sorted(items, key=lambda w: w.get(key, ""), reverse=desc)

        return _paginate(items, limit, offset)

    async def get_by_code(self, workcenter_code: str):
        for w in ALL_WORKCENTERS:
            if w["workcenter_code"] == workcenter_code:
                return w
        return None


# --------------------------------------------------------------------------- #
# Fixtures                                                                    #
# --------------------------------------------------------------------------- #


@pytest.fixture
def client():
    """TestClient with mocked auth and service layer."""
    from main import app
    from dependencies.auth import get_current_user
    from schemas.auth import UserResponse

    async def _override_auth():
        return UserResponse(
            id="test-user-id",
            email="test@example.com",
            name="Test Admin",
            role="admin",
            last_login=None,
        )

    app.dependency_overrides[get_current_user] = _override_auth

    with patch("routers.foundation_roles.RolesReadService", MockRolesReadService), \
         patch("routers.foundation_skills.SkillsReadService", MockSkillsReadService), \
         patch("routers.foundation_workcenters.WorkcentersReadService", MockWorkcentersReadService):
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c

    app.dependency_overrides.clear()


def _get(client, path: str, **kwargs) -> Any:
    return client.get(f"{API_PREFIX}{path}", **kwargs)


def _assert_no_stack_leak(body_text: str) -> None:
    lowered = body_text.lower()
    forbidden_markers = (
        "traceback",
        'file "/',
        "\n  at ",
        "psycopg2",
        "asyncpg",
        "sqlalchemy.exc",
        "postgresql://",
        "postgres://",
        "dsn=",
    )
    for marker in forbidden_markers:
        assert marker not in lowered, (
            f"Forbidden stack/internal marker leaked into response body: {marker!r}"
        )


def _extract_detail(payload: Any) -> Dict[str, Any]:
    if isinstance(payload, dict) and "detail" in payload:
        return payload["detail"]
    return payload


# --------------------------------------------------------------------------- #
# Baseline / fixture-guard tests (§3.4 TC_BL_*)                               #
# --------------------------------------------------------------------------- #


def test_bl_001_roles_count(client) -> None:
    """TC_BL_001 — ``public.roles`` surfaces as 20 items via the list API."""
    r = _get(client, "/roles", params={"limit": 200})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["pagination"]["total"] == EXPECTED_ROLES_TOTAL
    assert len(body["items"]) == EXPECTED_ROLES_TOTAL


def test_bl_002_skills_count(client) -> None:
    """TC_BL_002 — ``public.skills`` surfaces as 33 items via the list API."""
    r = _get(client, "/skills", params={"limit": 200})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["pagination"]["total"] == EXPECTED_SKILLS_TOTAL
    assert len(body["items"]) == EXPECTED_SKILLS_TOTAL


def test_bl_003_workcenters_count(client) -> None:
    """TC_BL_003 — ``public.workcenters`` surfaces as 16 items via list API."""
    r = _get(client, "/workcenters", params={"limit": 200})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["pagination"]["total"] == EXPECTED_WORKCENTERS_TOTAL
    assert len(body["items"]) == EXPECTED_WORKCENTERS_TOTAL


def test_bl_004_operational_admin_split(client) -> None:
    """TC_BL_004 — 17 operational + 3 administrative roles (GO-4B matrix)."""
    r_ops = _get(client, "/roles", params={"is_operational": "true", "limit": 200})
    assert r_ops.status_code == 200, r_ops.text
    assert r_ops.json()["pagination"]["total"] == 17

    r_admin = _get(client, "/roles", params={"is_operational": "false", "limit": 200})
    assert r_admin.status_code == 200, r_admin.text
    admin_body = r_admin.json()
    assert admin_body["pagination"]["total"] == 3
    admin_codes = {item["role_code"] for item in admin_body["items"]}
    assert admin_codes == set(ADMIN_ROLE_CODES)


# --------------------------------------------------------------------------- #
# §4.1 — GET /api/v1/roles (list)                                             #
# --------------------------------------------------------------------------- #


def test_roles_hp_001_default_list(client) -> None:
    """TC_ROLES_HP_001 — default list returns 20 items; shape conforms."""
    r = _get(client, "/roles", params={"limit": 200})
    assert r.status_code == 200, r.text
    body = r.json()
    assert isinstance(body["items"], list)
    assert body["pagination"]["total"] == EXPECTED_ROLES_TOTAL
    for item in body["items"]:
        assert isinstance(item["role_id"], str) and item["role_id"]
        assert isinstance(item["role_code"], str) and item["role_code"]
        assert isinstance(item["role_name"], str)
        assert isinstance(item["role_type"], str)
        assert isinstance(item["is_operational"], bool)
        assert isinstance(item["active"], bool)
        assert isinstance(item["related_skill_ids"], list)
        assert isinstance(item["related_workcenter_ids"], list)
        assert isinstance(item["skill_count"], int)
        assert isinstance(item["workcenter_count"], int)


def test_roles_hp_002_counts_match_arrays(client) -> None:
    """TC_ROLES_HP_002 — ``skill_count``/``workcenter_count`` derived from arrays."""
    r = _get(client, "/roles", params={"limit": 200})
    assert r.status_code == 200, r.text
    for item in r.json()["items"]:
        assert item["skill_count"] == len(item["related_skill_ids"]), item["role_code"]
        assert item["workcenter_count"] == len(item["related_workcenter_ids"]), item["role_code"]


def test_roles_hp_003_is_operational_split(client) -> None:
    """TC_ROLES_HP_003 — exactly 17 operational + 3 non-operational items."""
    r = _get(client, "/roles", params={"limit": 200})
    assert r.status_code == 200, r.text
    items = r.json()["items"]
    ops = [i for i in items if i["is_operational"] is True]
    non_ops = [i for i in items if i["is_operational"] is False]
    assert len(ops) == 17
    assert len(non_ops) == 3
    admin_codes = {i["role_code"] for i in non_ops}
    assert admin_codes == set(ADMIN_ROLE_CODES)


def test_roles_sf_002_is_operational_false_returns_admins(client) -> None:
    """TC_ROLES_SF_002 — ``is_operational=false`` returns exactly the 3 admins."""
    r = _get(client, "/roles", params={"is_operational": "false", "limit": 200})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["pagination"]["total"] == 3
    for item in body["items"]:
        assert item["role_code"] in ADMIN_ROLE_CODES
        assert item["related_skill_ids"] == []
        assert item["related_workcenter_ids"] == []


def test_roles_sf_003_is_operational_true_count(client) -> None:
    """TC_ROLES_SF_003 — ``is_operational=true`` returns exactly 17 items."""
    r = _get(client, "/roles", params={"is_operational": "true", "limit": 200})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["pagination"]["total"] == 17
    for item in body["items"]:
        assert item["is_operational"] is True
        assert item["role_code"] not in ADMIN_ROLE_CODES


def test_roles_sf_004_sort_desc_role_code(client) -> None:
    """TC_ROLES_SF_004 — ``sort=-role_code`` yields lex-DESC ordering."""
    r = _get(client, "/roles", params={"sort": "-role_code", "limit": 200})
    assert r.status_code == 200, r.text
    codes = [item["role_code"] for item in r.json()["items"]]
    assert codes == sorted(codes, reverse=True)


def test_roles_sf_005_q_search_substring(client) -> None:
    """TC_ROLES_SF_005 — ``q=OP_CNC`` matches case-insensitively."""
    r = _get(client, "/roles", params={"q": "OP_CNC", "limit": 200})
    assert r.status_code == 200, r.text
    items = r.json()["items"]
    assert len(items) >= 1
    returned_codes = {item["role_code"] for item in items}
    assert "OP_CNC_ROUTER" in returned_codes
    for item in items:
        haystack = (item["role_code"] + " " + item["role_name"]).lower()
        assert "op_cnc" in haystack or "op cnc" in haystack


def test_roles_pg_001_custom_limit_offset(client) -> None:
    """TC_ROLES_PG_001 — custom limit/offset reflects correctly in pagination."""
    r = _get(client, "/roles", params={"limit": 5, "offset": 0})
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["items"]) == 5
    assert body["pagination"]["limit"] == 5
    assert body["pagination"]["offset"] == 0
    assert body["pagination"]["total"] == EXPECTED_ROLES_TOTAL
    assert body["pagination"]["has_more"] is True


def test_roles_pg_002_last_page(client) -> None:
    """TC_ROLES_PG_002 — last page has ``has_more=false``."""
    r = _get(client, "/roles", params={"limit": 5, "offset": 15})
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["items"]) == 5
    assert body["pagination"]["has_more"] is False


def test_roles_pg_003_offset_past_end(client) -> None:
    """TC_ROLES_PG_003 — offset past end returns [] with total preserved."""
    r = _get(client, "/roles", params={"limit": 5, "offset": 500})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["items"] == []
    assert body["pagination"]["has_more"] is False
    assert body["pagination"]["total"] == EXPECTED_ROLES_TOTAL


def test_roles_400_001_unknown_sort_field(client) -> None:
    """TC_ROLES_400_001 — unknown sort field → 400 INVALID_QUERY_PARAM."""
    r = _get(client, "/roles", params={"sort": "-bogus_field"})
    assert r.status_code == 400, r.text
    detail = _extract_detail(r.json())
    assert isinstance(detail, dict)
    assert detail.get("code") == "INVALID_QUERY_PARAM"
    _assert_no_stack_leak(r.text)


def test_roles_400_002_bad_role_type_enum(client) -> None:
    """TC_ROLES_400_002 — invalid ``role_type`` enum → 400."""
    r = _get(client, "/roles", params={"role_type": "bogus_category"})
    assert r.status_code == 400, r.text
    detail = _extract_detail(r.json())
    assert detail.get("code") == "INVALID_QUERY_PARAM"
    _assert_no_stack_leak(r.text)


def test_roles_400_004_limit_above_max(client) -> None:
    """TC_ROLES_400_004 — ``limit=999`` → 400 or 422 per runtime actual."""
    r = _get(client, "/roles", params={"limit": 999})
    assert r.status_code in (400, 422), r.text
    _assert_no_stack_leak(r.text)


# --------------------------------------------------------------------------- #
# §4.2 — GET /api/v1/roles/{role_code}                                        #
# --------------------------------------------------------------------------- #


def test_role_detail_hp_001_operational(client) -> None:
    """TC_ROLE_DETAIL_HP_001 — OP_CNC_ROUTER returns linked skills+wc."""
    r = _get(client, "/roles/OP_CNC_ROUTER")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["role_code"] == "OP_CNC_ROUTER"
    assert body["is_operational"] is True
    assert body["skill_count"] == len(body["related_skill_ids"])
    assert body["workcenter_count"] == len(body["related_workcenter_ids"])
    assert body["skill_count"] >= 1
    assert body["workcenter_count"] >= 1


def test_role_detail_hp_002_administrative(client) -> None:
    """TC_ROLE_DETAIL_HP_002 — MGR_PRODUCTION returns admin with empty arrays."""
    r = _get(client, "/roles/MGR_PRODUCTION")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["role_code"] == "MGR_PRODUCTION"
    assert body["is_operational"] is False
    assert body["related_skill_ids"] == []
    assert body["related_workcenter_ids"] == []
    assert body["skill_count"] == 0
    assert body["workcenter_count"] == 0
    assert body["active"] is True


def test_role_detail_hp_003_hotwire(client) -> None:
    """TC_ROLE_DETAIL_HP_003 — OP_HOTWIRE has exactly one workcenter linkage."""
    r = _get(client, f"/roles/{HOTWIRE_ROLE_CODE}")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["role_code"] == HOTWIRE_ROLE_CODE
    assert body["workcenter_count"] == 1
    assert len(body["related_workcenter_ids"]) == 1


def test_role_detail_404_001_unknown(client) -> None:
    """TC_ROLE_DETAIL_404_001 — unknown role → 404 ROLE_NOT_FOUND envelope."""
    r = _get(client, "/roles/UNKNOWN_ROLE")
    assert r.status_code == 404, r.text
    detail = _extract_detail(r.json())
    assert isinstance(detail, dict)
    assert detail.get("code") == "ROLE_NOT_FOUND"
    assert "UNKNOWN_ROLE" in detail.get("message", "")
    assert detail.get("details", {}).get("role_code") == "UNKNOWN_ROLE"
    _assert_no_stack_leak(r.text)


# --------------------------------------------------------------------------- #
# §4.3 — GET /api/v1/roles/{role_code}/skills                                 #
# --------------------------------------------------------------------------- #


def test_role_skills_hp_001_operational(client) -> None:
    """TC_ROLE_SKILLS_HP_001 — OP_CNC_ROUTER exposes embedded skills[]."""
    r = _get(client, "/roles/OP_CNC_ROUTER/skills")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["role_code"] == "OP_CNC_ROUTER"
    assert body["skill_count"] >= 1
    assert isinstance(body["skills"], list)
    assert len(body["skills"]) == body["skill_count"]
    for skill in body["skills"]:
        assert "skill_code" in skill and skill["skill_code"]
        assert "skill_name" in skill
    semantics = body.get("semantics", {})
    assert semantics.get("empty_is_intentional") is False
    assert semantics.get("administrative_role") is False


@pytest.mark.parametrize("role_code", ADMIN_ROLE_CODES)
def test_role_skills_sem_admin_empty(role_code: str, client) -> None:
    """TC_ROLE_SKILLS_SEM_001..003 — admin roles → 200 [] + intentional flag."""
    r = _get(client, f"/roles/{role_code}/skills")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["role_code"] == role_code
    assert body["skills"] == []
    assert body["skill_count"] == 0
    semantics = body.get("semantics", {})
    assert semantics.get("empty_is_intentional") is True
    assert semantics.get("administrative_role") is True
    rationale = semantics.get("rationale", "")
    assert rationale and "spec__role_skill_model.md" in rationale


def test_role_skills_404_001_unknown_role(client) -> None:
    """TC_ROLE_SKILLS_404_001 — unknown role on /skills → 404."""
    r = _get(client, "/roles/OP_UNKNOWN/skills")
    assert r.status_code == 404, r.text
    detail = _extract_detail(r.json())
    assert detail.get("code") == "ROLE_NOT_FOUND"
    _assert_no_stack_leak(r.text)


# --------------------------------------------------------------------------- #
# §4.4 — GET /api/v1/roles/{role_code}/workcenters                            #
# --------------------------------------------------------------------------- #


def test_role_wc_hp_001_operational(client) -> None:
    """TC_ROLE_WC_HP_001 — OP_CNC_ROUTER → WC_CNC_ROUTING, not TEMPORARY_PARTIAL."""
    r = _get(client, "/roles/OP_CNC_ROUTER/workcenters")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["workcenter_count"] >= 1
    codes = [w["workcenter_code"] for w in body["workcenters"]]
    assert "WC_CNC_ROUTING" in codes
    flags = body.get("flags", {})
    assert flags.get("temporary_partial") is False
    semantics = body.get("semantics", {})
    assert semantics.get("empty_is_intentional") is False
    assert semantics.get("administrative_role") is False


def test_role_wc_sem_001_hotwire_temporary_partial(client) -> None:
    """TC_ROLE_WC_SEM_001 — OP_HOTWIRE → WC_INSTALLATION_PREP w/ temporary_partial=true."""
    r = _get(client, f"/roles/{HOTWIRE_ROLE_CODE}/workcenters")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["workcenter_count"] == 1
    assert body["workcenters"][0]["workcenter_code"] == HOTWIRE_EXPECTED_WC_CODE
    flags = body.get("flags", {})
    assert flags.get("temporary_partial") is True
    rationale = flags.get("temporary_partial_rationale", "")
    assert rationale and "spec__role_skill_model.md" in rationale


def test_role_wc_sem_002_other_roles_not_temporary_partial(client) -> None:
    """TC_ROLE_WC_SEM_002 — ONLY OP_HOTWIRE is flagged TEMPORARY_PARTIAL."""
    r_list = _get(client, "/roles", params={"is_operational": "true", "limit": 200})
    assert r_list.status_code == 200, r_list.text
    op_codes = [item["role_code"] for item in r_list.json()["items"]]
    assert HOTWIRE_ROLE_CODE in op_codes

    for role_code in op_codes:
        if role_code == HOTWIRE_ROLE_CODE:
            continue
        r = _get(client, f"/roles/{role_code}/workcenters")
        assert r.status_code == 200, f"{role_code}: {r.text}"
        flags = r.json().get("flags", {})
        assert flags.get("temporary_partial") is False, (
            f"Unexpected temporary_partial=true on role {role_code}"
        )


@pytest.mark.parametrize("role_code", ADMIN_ROLE_CODES)
def test_role_wc_sem_admin_empty(role_code: str, client) -> None:
    """TC_ROLE_WC_SEM_003..005 — admin roles → 200 [] + administrative semantics."""
    r = _get(client, f"/roles/{role_code}/workcenters")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["workcenters"] == []
    assert body["workcenter_count"] == 0
    flags = body.get("flags", {})
    assert flags.get("temporary_partial") is False
    semantics = body.get("semantics", {})
    assert semantics.get("empty_is_intentional") is True
    assert semantics.get("administrative_role") is True


# --------------------------------------------------------------------------- #
# §4.5 — GET /api/v1/skills (list)                                            #
# --------------------------------------------------------------------------- #


def test_skills_hp_001_default_list(client) -> None:
    """TC_SKILLS_HP_001 — default list returns 33 items; shape conforms."""
    r = _get(client, "/skills", params={"limit": 200})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["pagination"]["total"] == EXPECTED_SKILLS_TOTAL
    for item in body["items"]:
        assert isinstance(item["skill_id"], str) and item["skill_id"]
        assert isinstance(item["skill_code"], str) and item["skill_code"]
        assert isinstance(item["skill_name"], str)
        assert isinstance(item["skill_category"], str)
        assert isinstance(item["active"], bool)


def test_skills_hp_002_default_sort_ascending(client) -> None:
    """TC_SKILLS_HP_002 — default sort is ``skill_code`` ASC."""
    r = _get(client, "/skills", params={"limit": 200})
    assert r.status_code == 200, r.text
    codes = [item["skill_code"] for item in r.json()["items"]]
    assert codes == sorted(codes)


def test_skills_pg_001_custom_page(client) -> None:
    """TC_SKILLS_PG_001 — custom page ``limit=10&offset=20`` returns 10 items."""
    r = _get(client, "/skills", params={"limit": 10, "offset": 20})
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["items"]) == 10
    assert body["pagination"]["offset"] == 20
    assert body["pagination"]["has_more"] is True


def test_skills_pg_002_last_page(client) -> None:
    """TC_SKILLS_PG_002 — offset=30 returns the final 3 items with has_more=false."""
    r = _get(client, "/skills", params={"limit": 10, "offset": 30})
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["items"]) == 3
    assert body["pagination"]["has_more"] is False


# --------------------------------------------------------------------------- #
# §4.6 — GET /api/v1/skills/{skill_code}                                      #
# --------------------------------------------------------------------------- #


def test_skill_detail_404_001_unknown(client) -> None:
    """TC_SKILL_DETAIL_404_001 — unknown skill → 404 SKILL_NOT_FOUND."""
    r = _get(client, "/skills/UNKNOWN_SKILL")
    assert r.status_code == 404, r.text
    detail = _extract_detail(r.json())
    assert detail.get("code") == "SKILL_NOT_FOUND"
    assert detail.get("details", {}).get("skill_code") == "UNKNOWN_SKILL"
    _assert_no_stack_leak(r.text)


def test_skill_detail_hp_existing_from_list(client) -> None:
    """Happy-path detail lookup for a live skill (code discovered from list)."""
    r_list = _get(client, "/skills", params={"limit": 1})
    assert r_list.status_code == 200, r_list.text
    items = r_list.json()["items"]
    assert items, "Skills list should not be empty"
    first_code = items[0]["skill_code"]

    r = _get(client, f"/skills/{first_code}")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["skill_code"] == first_code
    assert isinstance(body["skill_category"], str) and body["skill_category"]
    assert isinstance(body["active"], bool)


# --------------------------------------------------------------------------- #
# §4.7 — GET /api/v1/workcenters (list)                                       #
# --------------------------------------------------------------------------- #


def test_wc_hp_001_default_list(client) -> None:
    """TC_WC_HP_001 — default list returns 16 items; shape conforms."""
    r = _get(client, "/workcenters", params={"limit": 200})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["pagination"]["total"] == EXPECTED_WORKCENTERS_TOTAL
    for item in body["items"]:
        assert isinstance(item["workcenter_id"], str) and item["workcenter_id"]
        assert isinstance(item["workcenter_code"], str) and item["workcenter_code"]
        assert isinstance(item["workcenter_name"], str)
        assert isinstance(item["workcenter_type"], str)
        assert isinstance(item["operational_status"], str)
        assert isinstance(item["active"], bool)


def test_wc_hp_002_default_sort_ascending(client) -> None:
    """TC_WC_HP_002 — default sort is ``workcenter_code`` ASC."""
    r = _get(client, "/workcenters", params={"limit": 200})
    assert r.status_code == 200, r.text
    codes = [item["workcenter_code"] for item in r.json()["items"]]
    assert codes == sorted(codes)


def test_wc_pg_001_custom_page(client) -> None:
    """TC_WC_PG_001 — custom page ``limit=5&offset=10`` returns 5 items, has_more."""
    r = _get(client, "/workcenters", params={"limit": 5, "offset": 10})
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["items"]) == 5
    assert body["pagination"]["has_more"] is True


def test_wc_pg_002_last_page(client) -> None:
    """TC_WC_PG_002 — offset=15 returns final 1 item, has_more=false."""
    r = _get(client, "/workcenters", params={"limit": 5, "offset": 15})
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["items"]) == 1
    assert body["pagination"]["has_more"] is False


# --------------------------------------------------------------------------- #
# §4.8 — GET /api/v1/workcenters/{workcenter_code}                            #
# --------------------------------------------------------------------------- #


def test_wc_detail_404_001_unknown(client) -> None:
    """TC_WC_DETAIL_404_001 — unknown workcenter → 404 WORKCENTER_NOT_FOUND."""
    r = _get(client, "/workcenters/UNKNOWN_WC")
    assert r.status_code == 404, r.text
    detail = _extract_detail(r.json())
    assert detail.get("code") == "WORKCENTER_NOT_FOUND"
    assert detail.get("details", {}).get("workcenter_code") == "UNKNOWN_WC"
    _assert_no_stack_leak(r.text)


def test_wc_detail_hp_001_installation_prep(client) -> None:
    """TC_WC_DETAIL_HP_002 — WC_INSTALLATION_PREP exists (HOTWIRE cross-check)."""
    r = _get(client, f"/workcenters/{HOTWIRE_EXPECTED_WC_CODE}")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["workcenter_code"] == HOTWIRE_EXPECTED_WC_CODE
    assert body["operational_status"] == "active"


# --------------------------------------------------------------------------- #
# §13 — Error envelope cross-cutting                                          #
# --------------------------------------------------------------------------- #


def test_err_shape_404_envelope(client) -> None:
    """TC_ERR_SHAPE_002 — 404 envelope carries code + message + details."""
    r = _get(client, "/roles/UNKNOWN_SHAPE_CHECK")
    assert r.status_code == 404, r.text
    detail = _extract_detail(r.json())
    assert isinstance(detail, dict)
    code = detail.get("code", "")
    assert isinstance(code, str) and code, "error.code must be non-empty"
    assert re.match(r"^[A-Z][A-Z0-9_]+$", code), (
        f"error.code must be SCREAMING_SNAKE_CASE, got {code!r}"
    )
    message = detail.get("message", "")
    assert isinstance(message, str) and message
    assert isinstance(detail.get("details"), dict)
    _assert_no_stack_leak(r.text)


def test_err_shape_400_envelope(client) -> None:
    """TC_ERR_SHAPE_001 — 400 envelope carries SCREAMING_SNAKE_CASE code."""
    r = _get(client, "/roles", params={"sort": "-bogus_field"})
    assert r.status_code == 400, r.text
    detail = _extract_detail(r.json())
    assert isinstance(detail, dict)
    code = detail.get("code", "")
    assert re.match(r"^[A-Z][A-Z0-9_]+$", code), code
    assert isinstance(detail.get("message"), str) and detail["message"]
    _assert_no_stack_leak(r.text)


def test_err_no_stack_trace_leak(client) -> None:
    """TC_ERR_NO_LEAK_001 — error bodies never leak stack traces or DB internals."""
    r = _get(client, "/roles/UNKNOWN_ROLE")
    assert r.status_code == 404
    _assert_no_stack_leak(r.text)

    r2 = _get(client, "/roles", params={"role_type": "bogus_category"})
    assert r2.status_code == 400
    _assert_no_stack_leak(r2.text)
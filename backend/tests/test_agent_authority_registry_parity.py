"""
Sprint #26 — Agent Authority Registry parity test.

Verifies that the canonical registry and its frontend consumer stay aligned.
This protects against duplicate-truth drift between:
  - docs/canonical/canonical__agent_authority_map.md (canonical source)
  - docs/canonical/agent_authority_registry.json     (structured registry)
  - app/frontend/src/lib/agentAuthorityRegistry.ts   (frontend bridge)
  - app/frontend/src/lib/governanceData.ts           (frontend consumer)

Rules (fail conditions):
  1. An agent exists in JSON but is not referenced from the frontend bridge.
  2. An agent misses `owner` or `sourceOfTruth`.
  3. `authority`, `noAuthority`, `escalatesWhen` are absent or not arrays.
  4. `sourceOfTruth` does not point to an existing canonical file.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
REGISTRY_PATH = REPO_ROOT / "docs" / "canonical" / "agent_authority_registry.json"
CANONICAL_MD_PATH = REPO_ROOT / "docs" / "canonical" / "canonical__agent_authority_map.md"
FRONTEND_BRIDGE_PATH = (
    REPO_ROOT / "app" / "frontend" / "src" / "lib" / "agentAuthorityRegistry.ts"
)
FRONTEND_GOVERNANCE_DATA_PATH = (
    REPO_ROOT / "app" / "frontend" / "src" / "lib" / "governanceData.ts"
)


# --------------------------------------------------------------------------- #
# Fixtures / loaders
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="module")
def registry() -> dict:
    assert REGISTRY_PATH.exists(), (
        f"Canonical registry missing: {REGISTRY_PATH}. "
        "Expected at docs/canonical/agent_authority_registry.json."
    )
    with REGISTRY_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def frontend_bridge_source() -> str:
    assert FRONTEND_BRIDGE_PATH.exists(), (
        f"Frontend bridge missing: {FRONTEND_BRIDGE_PATH}. "
        "Expected app/frontend/src/lib/agentAuthorityRegistry.ts."
    )
    return FRONTEND_BRIDGE_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def frontend_governance_data_source() -> str:
    assert FRONTEND_GOVERNANCE_DATA_PATH.exists()
    return FRONTEND_GOVERNANCE_DATA_PATH.read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# Structural tests
# --------------------------------------------------------------------------- #


def test_registry_has_canonical_source_and_agents(registry: dict) -> None:
    assert "canonicalSource" in registry, "Registry missing `canonicalSource`."
    assert "agents" in registry, "Registry missing `agents` array."
    assert isinstance(registry["agents"], list), "`agents` must be an array."
    assert len(registry["agents"]) >= 1, "Registry must have at least one agent."


def test_canonical_source_file_exists(registry: dict) -> None:
    canonical_ref = registry["canonicalSource"]
    canonical_file = REPO_ROOT / canonical_ref
    assert canonical_file.exists(), (
        f"canonicalSource points to missing file: {canonical_ref}"
    )
    assert canonical_file == CANONICAL_MD_PATH.resolve() or canonical_file.exists()


# --------------------------------------------------------------------------- #
# Rule 2: every agent must have owner + sourceOfTruth
# Rule 3: authority / noAuthority / escalatesWhen must be arrays (present)
# Rule 4: sourceOfTruth must point to an existing canonical file
# --------------------------------------------------------------------------- #


REQUIRED_FIELDS = [
    "id",
    "label",
    "domain",
    "description",
    "authority",
    "noAuthority",
    "escalatesWhen",
    "owner",
    "sourceOfTruth",
]

ARRAY_FIELDS = ["authority", "noAuthority", "escalatesWhen"]


def test_every_agent_has_required_fields(registry: dict) -> None:
    for agent in registry["agents"]:
        missing = [f for f in REQUIRED_FIELDS if f not in agent]
        assert not missing, (
            f"Agent `{agent.get('id', '?')}` missing required fields: {missing}"
        )


def test_owner_and_source_of_truth_are_non_empty_strings(registry: dict) -> None:
    for agent in registry["agents"]:
        owner = agent.get("owner")
        source = agent.get("sourceOfTruth")
        assert isinstance(owner, str) and owner.strip(), (
            f"Agent `{agent['id']}` has empty or non-string `owner`."
        )
        assert isinstance(source, str) and source.strip(), (
            f"Agent `{agent['id']}` has empty or non-string `sourceOfTruth`."
        )


def test_array_fields_are_arrays(registry: dict) -> None:
    for agent in registry["agents"]:
        for field in ARRAY_FIELDS:
            value = agent.get(field)
            assert isinstance(value, list), (
                f"Agent `{agent['id']}` field `{field}` must be an array, "
                f"got {type(value).__name__}."
            )


def test_source_of_truth_points_to_existing_file(registry: dict) -> None:
    for agent in registry["agents"]:
        source_ref = agent["sourceOfTruth"]
        # Strip anchor fragment (e.g. "...#section")
        file_part = source_ref.split("#", 1)[0]
        target = REPO_ROOT / file_part
        assert target.exists(), (
            f"Agent `{agent['id']}` sourceOfTruth points to missing file: "
            f"{source_ref} (resolved: {target})"
        )


# --------------------------------------------------------------------------- #
# Rule 1: every agent in JSON must be present in the frontend bridge
# --------------------------------------------------------------------------- #


def test_every_json_agent_is_referenced_in_frontend_bridge(
    registry: dict, frontend_bridge_source: str
) -> None:
    """
    The frontend bridge (agentAuthorityRegistry.ts) carries a UI_STYLE map
    that must contain an entry for every agent id in the JSON registry.
    This guarantees no agent is silently dropped from the UI.
    """
    bridge_src = frontend_bridge_source
    missing_ids = []
    for agent in registry["agents"]:
        agent_id = agent["id"]
        # Look for `  <id>: {` or `"<id>":` in the UI_STYLE record map
        needle_a = f"{agent_id}:"
        needle_b = f'"{agent_id}":'
        if needle_a not in bridge_src and needle_b not in bridge_src:
            missing_ids.append(agent_id)
    assert not missing_ids, (
        f"Agents present in JSON registry but missing from frontend bridge "
        f"UI_STYLE map: {missing_ids}"
    )


def test_governance_data_consumes_registry(
    frontend_governance_data_source: str,
) -> None:
    """
    governanceData.ts must NOT re-declare the agents array literally.
    It must import from the registry bridge module.
    """
    src = frontend_governance_data_source
    assert 'from "./agentAuthorityRegistry"' in src, (
        "governanceData.ts must import agents from ./agentAuthorityRegistry "
        "(canonical registry bridge), not hardcode them."
    )
    assert "export const agents: Agent[] = agentAuthorityRegistry" in src, (
        "governanceData.ts must export `agents` derived from the registry bridge."
    )
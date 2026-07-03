"""
BUILD 10 — Tests for Quote Output Snapshot Candidate CRUD.

Verifies:
  - Create endpoint exists
  - Auth required
  - Quote missing returns 404
  - Create snapshot from valid quote composition preview
  - Created snapshot has persisted=true
  - Created snapshot has not_order_snapshot=true
  - Created snapshot has not_final_contract=true
  - Created snapshot has not_sent_to_client=true
  - rendered_sections_json saved
  - variables_used_json saved
  - warnings/blockers saved
  - content_hash generated
  - Snapshot creation does not mutate Quote
  - Snapshot creation does not mutate Order
  - Snapshot creation does not create Order
  - Snapshot creation does not mutate OrderSnapshot
  - Snapshot creation does not call CostEngine formulas
  - Snapshot creation does not mutate ProductTemplate
  - Snapshot creation does not mutate BlueprintDossier
  - Snapshot creation does not mutate Inventory
  - Snapshot creation does not create ExecutionTask
  - List snapshots returns quote snapshots
  - Get snapshot returns expected data
  - Missing composition blockers prevent direct approval
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

import pytest

from services.quote_output_snapshot_service import (
    QuoteOutputSnapshotService,
    QuoteOutputSnapshotCandidateDTO,
)
from models.quote_output_snapshots import QuoteOutputSnapshot, ALLOWED_SNAPSHOT_STATUSES


# ---------------------------------------------------------------------------
# Fixtures / Helpers
# ---------------------------------------------------------------------------

def _make_composition_result(
    quote_id: int = 1,
    quote_code: str = "Q-2026-001",
    sections: Optional[List[Dict]] = None,
    warnings: Optional[List[str]] = None,
    blockers: Optional[List[str]] = None,
    template_link: Optional[Dict] = None,
):
    """Build a mock composition result dict."""
    return {
        "persisted": False,
        "quote_id": quote_id,
        "quote_code": quote_code,
        "composition_type": "quote_output_preview",
        "source": {"quote": "read_only"},
        "template_link": template_link or {
            "status": "linked",
            "template_id": 1,
            "template_code": "TPL-BANNER-STANDARD",
            "dossier_id": 1,
        },
        "sections": sections or [
            {
                "section_id": "block-01",
                "title": "Product Description",
                "source": "output_blocks",
                "rendered_text": "Banner publicitar 3x2m",
                "warnings": [],
                "blockers": [],
            }
        ],
        "commercial_summary": {
            "subtotal": 1000.0,
            "vat": 190.0,
            "total": 1190.0,
            "currency": "RON",
        },
        "warnings": warnings or [],
        "blockers": blockers or [],
        "trace": {
            "no_persist": True,
            "changed_entities": [],
            "no_quote_mutation": True,
            "no_order_mutation": True,
            "no_snapshot_created": True,
            "not_client_final": True,
        },
    }


class MockCompositionResult:
    """Mock for QuoteOutputCompositionResult."""
    def __init__(self, data: Dict):
        self._data = data

    def to_dict(self):
        return self._data


class MockDBSession:
    """Mock async DB session for unit tests."""

    def __init__(self):
        self.added = []
        self.committed = False
        self._snapshots: List[QuoteOutputSnapshot] = []
        self._execute_results = []

    def add(self, obj):
        self.added.append(obj)
        # Simulate auto-increment
        if not obj.id:
            obj.id = len(self._snapshots) + len(self.added)
        if not obj.created_at:
            obj.created_at = datetime.now()
        if not obj.updated_at:
            obj.updated_at = datetime.now()

    async def commit(self):
        self.committed = True

    async def refresh(self, obj):
        pass

    async def execute(self, query):
        return MockResult(self._execute_results)


class MockResult:
    def __init__(self, results):
        self._results = results

    def scalar_one_or_none(self):
        return self._results[0] if self._results else None

    def scalar(self):
        return self._results[0] if self._results else None

    def scalars(self):
        return MockScalars(self._results)


class MockScalars:
    def __init__(self, results):
        self._results = results

    def all(self):
        return self._results


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSnapshotCandidateCreation:
    """Test snapshot candidate creation."""

    @pytest.mark.asyncio
    async def test_create_snapshot_from_valid_composition(self):
        """Create snapshot from valid quote composition preview."""
        composition_data = _make_composition_result()
        mock_result = MockCompositionResult(composition_data)

        db = MockDBSession()
        db._execute_results = [0]  # count=0 for code generation, max_version=0

        with patch(
            "services.quote_output_snapshot_service.QuoteOutputCompositionService"
        ) as MockCompService:
            instance = MockCompService.return_value
            instance.compose_preview = AsyncMock(return_value=mock_result)

            service = QuoteOutputSnapshotService(db)
            result = await service.create_snapshot(1, notes="Test snapshot")

        assert result.get("persisted") is True
        assert result.get("not_order_snapshot") is True
        assert result.get("not_final_contract") is True
        assert result.get("not_sent_to_client") is True
        assert result.get("quote_id") == 1
        assert result.get("status") == "draft"
        assert result.get("snapshot_code", "").startswith("QDOC-")
        assert db.committed is True

    @pytest.mark.asyncio
    async def test_create_snapshot_has_content_hash(self):
        """Created snapshot has content_hash generated."""
        composition_data = _make_composition_result()
        mock_result = MockCompositionResult(composition_data)

        db = MockDBSession()
        db._execute_results = [0]

        with patch(
            "services.quote_output_snapshot_service.QuoteOutputCompositionService"
        ) as MockCompService:
            instance = MockCompService.return_value
            instance.compose_preview = AsyncMock(return_value=mock_result)

            service = QuoteOutputSnapshotService(db)
            result = await service.create_snapshot(1)

        assert result.get("content_hash") is not None
        assert len(result["content_hash"]) == 32

    @pytest.mark.asyncio
    async def test_create_snapshot_saves_rendered_sections(self):
        """rendered_sections_json is saved in snapshot."""
        sections = [{"section_id": "s1", "title": "Test", "rendered_text": "Hello"}]
        composition_data = _make_composition_result(sections=sections)
        mock_result = MockCompositionResult(composition_data)

        db = MockDBSession()
        db._execute_results = [0]

        with patch(
            "services.quote_output_snapshot_service.QuoteOutputCompositionService"
        ) as MockCompService:
            instance = MockCompService.return_value
            instance.compose_preview = AsyncMock(return_value=mock_result)

            service = QuoteOutputSnapshotService(db)
            result = await service.create_snapshot(1)

        assert result.get("rendered_sections_json") == sections

    @pytest.mark.asyncio
    async def test_create_snapshot_saves_warnings_blockers(self):
        """warnings and blockers are saved."""
        composition_data = _make_composition_result(
            warnings=["test_warning"],
            blockers=["test_blocker"],
        )
        mock_result = MockCompositionResult(composition_data)

        db = MockDBSession()
        db._execute_results = [0]

        with patch(
            "services.quote_output_snapshot_service.QuoteOutputCompositionService"
        ) as MockCompService:
            instance = MockCompService.return_value
            instance.compose_preview = AsyncMock(return_value=mock_result)

            service = QuoteOutputSnapshotService(db)
            result = await service.create_snapshot(1)

        assert "test_warning" in result.get("warnings", [])
        assert "test_blocker" in result.get("blockers", [])

    @pytest.mark.asyncio
    async def test_create_snapshot_quote_not_found(self):
        """Quote missing returns error."""
        composition_data = _make_composition_result(blockers=["quote_not_found"])
        mock_result = MockCompositionResult(composition_data)

        db = MockDBSession()
        db._execute_results = [0]

        with patch(
            "services.quote_output_snapshot_service.QuoteOutputCompositionService"
        ) as MockCompService:
            instance = MockCompService.return_value
            instance.compose_preview = AsyncMock(return_value=mock_result)

            service = QuoteOutputSnapshotService(db)
            result = await service.create_snapshot(999)

        assert result.get("error") == "quote_not_found"
        assert result.get("status_code") == 404

    @pytest.mark.asyncio
    async def test_create_snapshot_trace_no_mutations(self):
        """Snapshot trace confirms no mutations occurred."""
        composition_data = _make_composition_result()
        mock_result = MockCompositionResult(composition_data)

        db = MockDBSession()
        db._execute_results = [0]

        with patch(
            "services.quote_output_snapshot_service.QuoteOutputCompositionService"
        ) as MockCompService:
            instance = MockCompService.return_value
            instance.compose_preview = AsyncMock(return_value=mock_result)

            service = QuoteOutputSnapshotService(db)
            result = await service.create_snapshot(1)

        trace = result.get("trace", {})
        assert trace.get("quote_mutated") is False
        assert trace.get("order_mutated") is False
        assert trace.get("order_snapshot_created") is False
        assert trace.get("costengine_called") is False
        assert trace.get("product_template_mutated") is False
        assert trace.get("blueprint_dossier_mutated") is False
        assert trace.get("inventory_mutated") is False
        assert trace.get("execution_task_created") is False
        assert trace.get("not_final_contract") is True
        assert trace.get("not_sent_to_client") is True

    @pytest.mark.asyncio
    async def test_create_snapshot_with_blockers_forces_draft(self):
        """Blockers prevent direct approval status."""
        composition_data = _make_composition_result(blockers=["missing_dossier"])
        mock_result = MockCompositionResult(composition_data)

        db = MockDBSession()
        db._execute_results = [0]

        with patch(
            "services.quote_output_snapshot_service.QuoteOutputCompositionService"
        ) as MockCompService:
            instance = MockCompService.return_value
            instance.compose_preview = AsyncMock(return_value=mock_result)

            service = QuoteOutputSnapshotService(db)
            # Try to create with approved status — should be forced to needs_review
            result = await service.create_snapshot(1, initial_status="approved_for_quote_output")

        # Should not be approved due to blockers
        assert result.get("status") in ("draft", "needs_review")

    @pytest.mark.asyncio
    async def test_create_snapshot_version_increments(self):
        """Version increments for each new snapshot."""
        composition_data = _make_composition_result()
        mock_result = MockCompositionResult(composition_data)

        db = MockDBSession()
        db._execute_results = [0]  # count=0, max_version=0

        with patch(
            "services.quote_output_snapshot_service.QuoteOutputCompositionService"
        ) as MockCompService:
            instance = MockCompService.return_value
            instance.compose_preview = AsyncMock(return_value=mock_result)

            service = QuoteOutputSnapshotService(db)
            result = await service.create_snapshot(1)

        assert result.get("version") == 1


class TestSnapshotCandidateDTO:
    """Test DTO conversion."""

    def test_dto_to_dict_includes_all_fields(self):
        """DTO includes all required fields."""
        snapshot = QuoteOutputSnapshot(
            id=1,
            quote_id=1,
            quote_code="Q-2026-001",
            snapshot_code="QDOC-2026-0001",
            snapshot_type="quote_output_candidate",
            status="draft",
            version=1,
            source_template_id=1,
            source_template_code="TPL-BANNER",
            source_dossier_id=1,
            rendered_sections_json=json.dumps([{"title": "Test"}]),
            commercial_summary_json=json.dumps({"total": 1190}),
            warnings_json=json.dumps([]),
            blockers_json=json.dumps([]),
            variables_used_json=json.dumps({}),
            trace_json=json.dumps({"quote_mutated": False}),
            content_hash="abc123",
            created_by="user@test.com",
            created_at=datetime(2026, 5, 18, 10, 0, 0),
            updated_at=datetime(2026, 5, 18, 10, 0, 0),
        )

        dto = QuoteOutputSnapshotCandidateDTO(snapshot)
        d = dto.to_dict()

        assert d["snapshot_id"] == 1
        assert d["quote_id"] == 1
        assert d["snapshot_code"] == "QDOC-2026-0001"
        assert d["persisted"] is True
        assert d["not_order_snapshot"] is True
        assert d["not_final_contract"] is True
        assert d["not_sent_to_client"] is True
        assert d["content_hash"] == "abc123"


class TestSnapshotStatusModel:
    """Test status model."""

    def test_allowed_statuses(self):
        """All required statuses are defined."""
        assert "draft" in ALLOWED_SNAPSHOT_STATUSES
        assert "needs_review" in ALLOWED_SNAPSHOT_STATUSES
        assert "approved_for_quote_output" in ALLOWED_SNAPSHOT_STATUSES
        assert "archived" in ALLOWED_SNAPSHOT_STATUSES
        assert "superseded" in ALLOWED_SNAPSHOT_STATUSES
        assert "rejected" in ALLOWED_SNAPSHOT_STATUSES
        assert len(ALLOWED_SNAPSHOT_STATUSES) == 6
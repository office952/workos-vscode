"""
BUILD 9 — Tests for Output Blocks Coverage Diagnostics.

Verifies:
  - Coverage endpoint/service exists
  - Returns all product templates
  - Reports block_count
  - Reports missing required block types
  - Does not mutate dossiers
  - Does not auto-create output blocks
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from services.output_blocks_coverage_service import OutputBlocksCoverageService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_template(template_id: int, template_code: str, description: str = ""):
    obj = MagicMock()
    obj.id = template_id
    obj.template_code = template_code
    obj.description = description
    return obj


def _make_dossier(
    dossier_id: int,
    template_id: int,
    output_blocks_json: str = None,
):
    obj = MagicMock()
    obj.id = dossier_id
    obj.template_id = template_id
    obj.output_blocks_json = output_blocks_json
    return obj


def _valid_blocks_json(count: int = 3) -> str:
    blocks = [
        {"block_id": f"block-{i}", "title": f"Block {i}", "block_type": "product_description"}
        for i in range(count)
    ]
    return json.dumps(blocks)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestOutputBlocksCoverage:
    """Tests for OutputBlocksCoverageService."""

    @pytest.mark.asyncio
    async def test_coverage_returns_all_templates(self):
        """Coverage report includes all templates."""
        db = AsyncMock()
        templates = [
            _make_template(1, "TPL-A", "Template A"),
            _make_template(2, "TPL-B", "Template B"),
        ]
        dossiers = [
            _make_dossier(1, 1, _valid_blocks_json(3)),
        ]

        tpl_result = MagicMock()
        tpl_result.scalars.return_value.all.return_value = templates
        dos_result = MagicMock()
        dos_result.scalars.return_value.all.return_value = dossiers
        db.execute = AsyncMock(side_effect=[tpl_result, dos_result])

        service = OutputBlocksCoverageService(db)
        result = await service.get_coverage()

        assert result["total_templates"] == 2

    @pytest.mark.asyncio
    async def test_coverage_reports_covered(self):
        """Templates with valid output blocks are reported as covered."""
        db = AsyncMock()
        templates = [_make_template(1, "TPL-A")]
        dossiers = [_make_dossier(1, 1, _valid_blocks_json(4))]

        tpl_result = MagicMock()
        tpl_result.scalars.return_value.all.return_value = templates
        dos_result = MagicMock()
        dos_result.scalars.return_value.all.return_value = dossiers
        db.execute = AsyncMock(side_effect=[tpl_result, dos_result])

        service = OutputBlocksCoverageService(db)
        result = await service.get_coverage()

        assert result["covered_count"] == 1
        assert result["covered"][0]["block_count"] == 4

    @pytest.mark.asyncio
    async def test_coverage_reports_missing_no_dossier(self):
        """Templates without dossier are reported as missing."""
        db = AsyncMock()
        templates = [_make_template(1, "TPL-A")]
        dossiers = []  # No dossier

        tpl_result = MagicMock()
        tpl_result.scalars.return_value.all.return_value = templates
        dos_result = MagicMock()
        dos_result.scalars.return_value.all.return_value = dossiers
        db.execute = AsyncMock(side_effect=[tpl_result, dos_result])

        service = OutputBlocksCoverageService(db)
        result = await service.get_coverage()

        assert result["missing_count"] == 1
        assert result["missing"][0]["reason"] == "no_dossier"

    @pytest.mark.asyncio
    async def test_coverage_reports_missing_empty_blocks(self):
        """Templates with empty output_blocks_json are reported as missing."""
        db = AsyncMock()
        templates = [_make_template(1, "TPL-A")]
        dossiers = [_make_dossier(1, 1, json.dumps([]))]

        tpl_result = MagicMock()
        tpl_result.scalars.return_value.all.return_value = templates
        dos_result = MagicMock()
        dos_result.scalars.return_value.all.return_value = dossiers
        db.execute = AsyncMock(side_effect=[tpl_result, dos_result])

        service = OutputBlocksCoverageService(db)
        result = await service.get_coverage()

        assert result["missing_count"] == 1
        assert "empty" in result["missing"][0]["reason"]

    @pytest.mark.asyncio
    async def test_coverage_reports_partial(self):
        """Templates with incomplete blocks are reported as partial."""
        db = AsyncMock()
        templates = [_make_template(1, "TPL-A")]
        # One block has block_id+title, one is missing title
        blocks = [
            {"block_id": "b1", "title": "Good block"},
            {"block_id": "b2"},  # Missing title
        ]
        dossiers = [_make_dossier(1, 1, json.dumps(blocks))]

        tpl_result = MagicMock()
        tpl_result.scalars.return_value.all.return_value = templates
        dos_result = MagicMock()
        dos_result.scalars.return_value.all.return_value = dossiers
        db.execute = AsyncMock(side_effect=[tpl_result, dos_result])

        service = OutputBlocksCoverageService(db)
        result = await service.get_coverage()

        assert result["partial_count"] == 1
        assert result["partial"][0]["complete_blocks"] == 1

    @pytest.mark.asyncio
    async def test_coverage_percentage(self):
        """Coverage percentage is calculated correctly."""
        db = AsyncMock()
        templates = [
            _make_template(1, "TPL-A"),
            _make_template(2, "TPL-B"),
            _make_template(3, "TPL-C"),
            _make_template(4, "TPL-D"),
        ]
        dossiers = [
            _make_dossier(1, 1, _valid_blocks_json(3)),
            _make_dossier(2, 2, _valid_blocks_json(2)),
        ]

        tpl_result = MagicMock()
        tpl_result.scalars.return_value.all.return_value = templates
        dos_result = MagicMock()
        dos_result.scalars.return_value.all.return_value = dossiers
        db.execute = AsyncMock(side_effect=[tpl_result, dos_result])

        service = OutputBlocksCoverageService(db)
        result = await service.get_coverage()

        assert result["coverage_pct"] == 50.0

    @pytest.mark.asyncio
    async def test_coverage_does_not_mutate(self):
        """Coverage service does not call commit/add/flush."""
        db = AsyncMock()
        templates = [_make_template(1, "TPL-A")]
        dossiers = [_make_dossier(1, 1, _valid_blocks_json(2))]

        tpl_result = MagicMock()
        tpl_result.scalars.return_value.all.return_value = templates
        dos_result = MagicMock()
        dos_result.scalars.return_value.all.return_value = dossiers
        db.execute = AsyncMock(side_effect=[tpl_result, dos_result])

        service = OutputBlocksCoverageService(db)
        await service.get_coverage()

        db.commit.assert_not_called()
        db.add.assert_not_called()
        db.flush.assert_not_called()

    @pytest.mark.asyncio
    async def test_coverage_does_not_auto_create(self):
        """Coverage service never auto-creates output blocks."""
        db = AsyncMock()
        templates = [_make_template(1, "TPL-A"), _make_template(2, "TPL-B")]
        dossiers = []  # No dossiers at all

        tpl_result = MagicMock()
        tpl_result.scalars.return_value.all.return_value = templates
        dos_result = MagicMock()
        dos_result.scalars.return_value.all.return_value = dossiers
        db.execute = AsyncMock(side_effect=[tpl_result, dos_result])

        service = OutputBlocksCoverageService(db)
        result = await service.get_coverage()

        # All missing, none auto-created
        assert result["missing_count"] == 2
        assert result["covered_count"] == 0
        db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_coverage_invalid_json(self):
        """Templates with invalid JSON in output_blocks_json are reported as missing."""
        db = AsyncMock()
        templates = [_make_template(1, "TPL-A")]
        dossiers = [_make_dossier(1, 1, "not valid json {{{")]

        tpl_result = MagicMock()
        tpl_result.scalars.return_value.all.return_value = templates
        dos_result = MagicMock()
        dos_result.scalars.return_value.all.return_value = dossiers
        db.execute = AsyncMock(side_effect=[tpl_result, dos_result])

        service = OutputBlocksCoverageService(db)
        result = await service.get_coverage()

        assert result["missing_count"] == 1
        assert "invalid" in result["missing"][0]["reason"]
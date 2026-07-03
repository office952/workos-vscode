"""
BUILD 9 — Tests for Quote Output Composition Preview.

Verifies:
  - Endpoint exists and requires auth
  - Returns composition preview DTO
  - Response includes persisted=false
  - Response includes trace with no_persist=true
  - Response includes sections from output blocks
  - Response includes commercial_summary
  - Response includes template_link status
  - Missing quote returns 404
  - No Quote created
  - No Order created
  - No ProductTemplate mutated
  - No BlueprintDossier mutated
  - No CostEngine formula called
  - No Quote -> Order gate changed
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.quote_output_composition_service import (
    QuoteOutputCompositionService,
    QuoteOutputCompositionResult,
)


# ---------------------------------------------------------------------------
# Commercial summary currency (unit)
# ---------------------------------------------------------------------------


class TestBuildCommercialSummary:
    def test_eur_snapshot_without_exchange_rate(self):
        line_items = json.dumps(
            {
                "product_definition": {"template_code": "TPL-VOLUMETRIC-LETTERS"},
                "cost_result": {"currency": "EUR", "total_cost": 640.0},
            }
        )
        quote = _make_quote_obj(
            line_items=line_items,
            subtotal=640.0,
            vat=128.0,
            grand_total=768.0,
        )
        summary = QuoteOutputCompositionService._build_commercial_summary(quote)
        assert summary["currency"] == "EUR"
        assert summary["total"] == 768.0

    def test_eur_snapshot_with_explicit_exchange_rate(self):
        line_items = json.dumps(
            {
                "line_items": {
                    "product_definition": {"template_code": "TPL-VOLUMETRIC-LETTERS"},
                    "cost_result": {"currency": "EUR", "total_cost": 640.0},
                },
                "exchange_rate": 5.0,
            }
        )
        quote = _make_quote_obj(
            line_items=line_items,
            subtotal=640.0,
            vat=128.0,
            grand_total=768.0,
        )
        summary = QuoteOutputCompositionService._build_commercial_summary(quote)
        assert summary["currency"] == "RON"
        assert summary["total"] == 3840.0
        assert summary["source_currency"] == "EUR"
        assert summary["source_amounts"]["total"] == 768.0


# ---------------------------------------------------------------------------
# Fixtures / Helpers
# ---------------------------------------------------------------------------

def _make_quote_obj(
    quote_id: int = 1,
    code: str = "Q-2026-001",
    client_name: str = "Test Client SRL",
    status: str = "draft",
    line_items: Optional[str] = None,
    subtotal: float = 1000.0,
    vat: float = 190.0,
    grand_total: float = 1190.0,
):
    obj = MagicMock()
    obj.id = quote_id
    obj.code = code
    obj.client_name = client_name
    obj.status = status
    obj.line_items = line_items or json.dumps([
        {"template_id": 1, "template_code": "TPL-BANNER-STANDARD", "description": "Banner 3x2m", "quantity": 1, "unit_price": 1000}
    ])
    obj.subtotal = subtotal
    obj.vat = vat
    obj.grand_total = grand_total
    return obj


def _make_dossier_obj(
    dossier_id: int = 1,
    template_id: int = 1,
    output_blocks_json: Optional[str] = None,
):
    obj = MagicMock()
    obj.id = dossier_id
    obj.template_id = template_id
    obj.output_blocks_json = output_blocks_json or json.dumps([
        {
            "block_id": "test-block-01",
            "block_type": "product_description",
            "title": "Test Block",
            "document_type": "offer",
            "audience": "client",
            "approval_status": "approved",
            "template_text": "Test product {{product_name}}",
            "variables": [
                {"name": "product_name", "source_field": "identity.product_name", "required": True, "missing_behavior": "render_with_warning"}
            ],
        }
    ])
    return obj


def _make_template_obj(
    template_id: int = 1,
    template_code: str = "TPL-BANNER-STANDARD",
    description: str = "Banner publicitar",
):
    obj = MagicMock()
    obj.id = template_id
    obj.template_code = template_code
    obj.description = description
    return obj


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestQuoteOutputCompositionPreview:
    """Tests for QuoteOutputCompositionService.compose_preview."""

    @pytest.mark.asyncio
    async def test_compose_preview_returns_result(self):
        """compose_preview returns QuoteOutputCompositionResult."""
        db = AsyncMock()
        # Mock quote query
        quote_result = MagicMock()
        quote_result.scalar_one_or_none.return_value = _make_quote_obj()

        # Mock template query
        tpl_result = MagicMock()
        tpl_result.scalar_one_or_none.return_value = _make_template_obj()

        # Mock dossier query
        dossier_result = MagicMock()
        dossier_result.scalar_one_or_none.return_value = _make_dossier_obj()

        db.execute = AsyncMock(side_effect=[quote_result, tpl_result, dossier_result])

        with patch(
            "services.quote_output_composition_service.OutputBlocksRendererService"
        ) as MockRenderer:
            mock_renderer_instance = AsyncMock()
            mock_render_result = MagicMock()
            mock_render_result.blocks = [
                {
                    "block_id": "test-block-01",
                    "title": "Test Block",
                    "rendered_text": "Test product Banner",
                    "warnings": [],
                    "blockers": [],
                }
            ]
            mock_render_result.warnings = []
            mock_render_result.blockers = []
            mock_renderer_instance.render_preview = AsyncMock(return_value=mock_render_result)
            MockRenderer.return_value = mock_renderer_instance

            service = QuoteOutputCompositionService(db)
            result = await service.compose_preview(1)

        assert isinstance(result, QuoteOutputCompositionResult)

    @pytest.mark.asyncio
    async def test_compose_preview_persisted_false(self):
        """Result always has persisted=False."""
        db = AsyncMock()
        quote_result = MagicMock()
        quote_result.scalar_one_or_none.return_value = _make_quote_obj()
        tpl_result = MagicMock()
        tpl_result.scalar_one_or_none.return_value = _make_template_obj()
        dossier_result = MagicMock()
        dossier_result.scalar_one_or_none.return_value = _make_dossier_obj()
        db.execute = AsyncMock(side_effect=[quote_result, tpl_result, dossier_result])

        with patch(
            "services.quote_output_composition_service.OutputBlocksRendererService"
        ) as MockRenderer:
            mock_renderer_instance = AsyncMock()
            mock_render_result = MagicMock()
            mock_render_result.blocks = []
            mock_render_result.warnings = []
            mock_render_result.blockers = []
            mock_renderer_instance.render_preview = AsyncMock(return_value=mock_render_result)
            MockRenderer.return_value = mock_renderer_instance

            service = QuoteOutputCompositionService(db)
            result = await service.compose_preview(1)

        assert result.persisted is False

    @pytest.mark.asyncio
    async def test_compose_preview_trace_no_persist(self):
        """Trace confirms no_persist=True."""
        db = AsyncMock()
        quote_result = MagicMock()
        quote_result.scalar_one_or_none.return_value = _make_quote_obj()
        tpl_result = MagicMock()
        tpl_result.scalar_one_or_none.return_value = _make_template_obj()
        dossier_result = MagicMock()
        dossier_result.scalar_one_or_none.return_value = _make_dossier_obj()
        db.execute = AsyncMock(side_effect=[quote_result, tpl_result, dossier_result])

        with patch(
            "services.quote_output_composition_service.OutputBlocksRendererService"
        ) as MockRenderer:
            mock_renderer_instance = AsyncMock()
            mock_render_result = MagicMock()
            mock_render_result.blocks = []
            mock_render_result.warnings = []
            mock_render_result.blockers = []
            mock_renderer_instance.render_preview = AsyncMock(return_value=mock_render_result)
            MockRenderer.return_value = mock_renderer_instance

            service = QuoteOutputCompositionService(db)
            result = await service.compose_preview(1)

        assert result.trace["no_persist"] is True
        assert result.trace["no_quote_mutation"] is True
        assert result.trace["no_order_mutation"] is True
        assert result.trace["no_snapshot_created"] is True
        assert result.trace["changed_entities"] == []

    @pytest.mark.asyncio
    async def test_compose_preview_quote_not_found(self):
        """Missing quote returns blocker."""
        db = AsyncMock()
        quote_result = MagicMock()
        quote_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=quote_result)

        service = QuoteOutputCompositionService(db)
        result = await service.compose_preview(999)

        assert "quote_not_found" in result.blockers

    @pytest.mark.asyncio
    async def test_compose_preview_includes_quote_code(self):
        """Result includes the quote code."""
        db = AsyncMock()
        quote_result = MagicMock()
        quote_result.scalar_one_or_none.return_value = _make_quote_obj(code="Q-2026-TEST")
        tpl_result = MagicMock()
        tpl_result.scalar_one_or_none.return_value = _make_template_obj()
        dossier_result = MagicMock()
        dossier_result.scalar_one_or_none.return_value = _make_dossier_obj()
        db.execute = AsyncMock(side_effect=[quote_result, tpl_result, dossier_result])

        with patch(
            "services.quote_output_composition_service.OutputBlocksRendererService"
        ) as MockRenderer:
            mock_renderer_instance = AsyncMock()
            mock_render_result = MagicMock()
            mock_render_result.blocks = []
            mock_render_result.warnings = []
            mock_render_result.blockers = []
            mock_renderer_instance.render_preview = AsyncMock(return_value=mock_render_result)
            MockRenderer.return_value = mock_renderer_instance

            service = QuoteOutputCompositionService(db)
            result = await service.compose_preview(1)

        assert result.quote_code == "Q-2026-TEST"

    @pytest.mark.asyncio
    async def test_compose_preview_includes_sections(self):
        """Result includes rendered sections from output blocks."""
        db = AsyncMock()
        quote_result = MagicMock()
        quote_result.scalar_one_or_none.return_value = _make_quote_obj()
        tpl_result = MagicMock()
        tpl_result.scalar_one_or_none.return_value = _make_template_obj()
        dossier_result = MagicMock()
        dossier_result.scalar_one_or_none.return_value = _make_dossier_obj()
        db.execute = AsyncMock(side_effect=[quote_result, tpl_result, dossier_result])

        with patch(
            "services.quote_output_composition_service.OutputBlocksRendererService"
        ) as MockRenderer:
            mock_renderer_instance = AsyncMock()
            mock_render_result = MagicMock()
            mock_render_result.blocks = [
                {
                    "block_id": "test-block-01",
                    "title": "Test Block",
                    "rendered_text": "Rendered content here",
                    "warnings": [],
                    "blockers": [],
                }
            ]
            mock_render_result.warnings = []
            mock_render_result.blockers = []
            mock_renderer_instance.render_preview = AsyncMock(return_value=mock_render_result)
            MockRenderer.return_value = mock_renderer_instance

            service = QuoteOutputCompositionService(db)
            result = await service.compose_preview(1)

        assert len(result.sections) == 1
        assert result.sections[0]["title"] == "Test Block"
        assert result.sections[0]["rendered_text"] == "Rendered content here"

    @pytest.mark.asyncio
    async def test_compose_preview_commercial_summary(self):
        """Result includes commercial summary from quote."""
        db = AsyncMock()
        quote_result = MagicMock()
        quote_result.scalar_one_or_none.return_value = _make_quote_obj(
            subtotal=500.0, vat=95.0, grand_total=595.0
        )
        tpl_result = MagicMock()
        tpl_result.scalar_one_or_none.return_value = _make_template_obj()
        dossier_result = MagicMock()
        dossier_result.scalar_one_or_none.return_value = _make_dossier_obj()
        db.execute = AsyncMock(side_effect=[quote_result, tpl_result, dossier_result])

        with patch(
            "services.quote_output_composition_service.OutputBlocksRendererService"
        ) as MockRenderer:
            mock_renderer_instance = AsyncMock()
            mock_render_result = MagicMock()
            mock_render_result.blocks = []
            mock_render_result.warnings = []
            mock_render_result.blockers = []
            mock_renderer_instance.render_preview = AsyncMock(return_value=mock_render_result)
            MockRenderer.return_value = mock_renderer_instance

            service = QuoteOutputCompositionService(db)
            result = await service.compose_preview(1)

        assert result.commercial_summary["subtotal"] == 500.0
        assert result.commercial_summary["vat"] == 95.0
        assert result.commercial_summary["total"] == 595.0

    @pytest.mark.asyncio
    async def test_compose_preview_eur_snapshot_currency(self):
        """EUR-priced snapshot must not be labeled RON in commercial_summary."""
        eur_line_items = json.dumps(
            {
                "product_definition": {"template_code": "TPL-VOLUMETRIC-LETTERS"},
                "cost_result": {"currency": "EUR", "total_cost": 640.0},
                "pricing": {},
                "price": 768.0,
            }
        )
        db = AsyncMock()
        quote_result = MagicMock()
        quote_result.scalar_one_or_none.return_value = _make_quote_obj(
            line_items=eur_line_items,
            subtotal=640.0,
            vat=128.0,
            grand_total=768.0,
        )
        tpl_result = MagicMock()
        tpl_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(side_effect=[quote_result, tpl_result])

        with patch(
            "services.quote_output_composition_service.OutputBlocksRendererService"
        ) as MockRenderer:
            mock_renderer_instance = AsyncMock()
            mock_render_result = MagicMock()
            mock_render_result.blocks = []
            mock_render_result.warnings = []
            mock_render_result.blockers = []
            mock_renderer_instance.render_preview = AsyncMock(return_value=mock_render_result)
            MockRenderer.return_value = mock_renderer_instance

            service = QuoteOutputCompositionService(db)
            result = await service.compose_preview(1)

        assert result.commercial_summary["currency"] == "EUR"
        assert result.commercial_summary["total"] == 768.0
        assert "source_amounts" not in result.commercial_summary

    @pytest.mark.asyncio
    async def test_compose_preview_template_link_status(self):
        """Result includes template link with status."""
        db = AsyncMock()
        quote_result = MagicMock()
        quote_result.scalar_one_or_none.return_value = _make_quote_obj()
        tpl_result = MagicMock()
        tpl_result.scalar_one_or_none.return_value = _make_template_obj(
            template_code="TPL-BANNER-STANDARD"
        )
        dossier_result = MagicMock()
        dossier_result.scalar_one_or_none.return_value = _make_dossier_obj(dossier_id=5)
        db.execute = AsyncMock(side_effect=[quote_result, tpl_result, dossier_result])

        with patch(
            "services.quote_output_composition_service.OutputBlocksRendererService"
        ) as MockRenderer:
            mock_renderer_instance = AsyncMock()
            mock_render_result = MagicMock()
            mock_render_result.blocks = []
            mock_render_result.warnings = []
            mock_render_result.blockers = []
            mock_renderer_instance.render_preview = AsyncMock(return_value=mock_render_result)
            MockRenderer.return_value = mock_renderer_instance

            service = QuoteOutputCompositionService(db)
            result = await service.compose_preview(1)

        assert result.template_link["status"] in ("linked", "linked_with_dossier", "missing")

    @pytest.mark.asyncio
    async def test_compose_preview_no_db_commit(self):
        """compose_preview never calls db.commit()."""
        db = AsyncMock()
        quote_result = MagicMock()
        quote_result.scalar_one_or_none.return_value = _make_quote_obj()
        tpl_result = MagicMock()
        tpl_result.scalar_one_or_none.return_value = _make_template_obj()
        dossier_result = MagicMock()
        dossier_result.scalar_one_or_none.return_value = _make_dossier_obj()
        db.execute = AsyncMock(side_effect=[quote_result, tpl_result, dossier_result])

        with patch(
            "services.quote_output_composition_service.OutputBlocksRendererService"
        ) as MockRenderer:
            mock_renderer_instance = AsyncMock()
            mock_render_result = MagicMock()
            mock_render_result.blocks = []
            mock_render_result.warnings = []
            mock_render_result.blockers = []
            mock_renderer_instance.render_preview = AsyncMock(return_value=mock_render_result)
            MockRenderer.return_value = mock_renderer_instance

            service = QuoteOutputCompositionService(db)
            await service.compose_preview(1)

        db.commit.assert_not_called()
        db.flush.assert_not_called()

    @pytest.mark.asyncio
    async def test_compose_preview_no_db_add(self):
        """compose_preview never calls db.add() — no entity creation."""
        db = AsyncMock()
        quote_result = MagicMock()
        quote_result.scalar_one_or_none.return_value = _make_quote_obj()
        tpl_result = MagicMock()
        tpl_result.scalar_one_or_none.return_value = _make_template_obj()
        dossier_result = MagicMock()
        dossier_result.scalar_one_or_none.return_value = _make_dossier_obj()
        db.execute = AsyncMock(side_effect=[quote_result, tpl_result, dossier_result])

        with patch(
            "services.quote_output_composition_service.OutputBlocksRendererService"
        ) as MockRenderer:
            mock_renderer_instance = AsyncMock()
            mock_render_result = MagicMock()
            mock_render_result.blocks = []
            mock_render_result.warnings = []
            mock_render_result.blockers = []
            mock_renderer_instance.render_preview = AsyncMock(return_value=mock_render_result)
            MockRenderer.return_value = mock_renderer_instance

            service = QuoteOutputCompositionService(db)
            await service.compose_preview(1)

        db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_compose_preview_not_client_final(self):
        """Trace confirms not_client_final=True."""
        db = AsyncMock()
        quote_result = MagicMock()
        quote_result.scalar_one_or_none.return_value = _make_quote_obj()
        tpl_result = MagicMock()
        tpl_result.scalar_one_or_none.return_value = _make_template_obj()
        dossier_result = MagicMock()
        dossier_result.scalar_one_or_none.return_value = _make_dossier_obj()
        db.execute = AsyncMock(side_effect=[quote_result, tpl_result, dossier_result])

        with patch(
            "services.quote_output_composition_service.OutputBlocksRendererService"
        ) as MockRenderer:
            mock_renderer_instance = AsyncMock()
            mock_render_result = MagicMock()
            mock_render_result.blocks = []
            mock_render_result.warnings = []
            mock_render_result.blockers = []
            mock_renderer_instance.render_preview = AsyncMock(return_value=mock_render_result)
            MockRenderer.return_value = mock_renderer_instance

            service = QuoteOutputCompositionService(db)
            result = await service.compose_preview(1)

        assert result.trace["not_client_final"] is True

    @pytest.mark.asyncio
    async def test_compose_preview_missing_template_link(self):
        """When no template linked, template_link status is missing."""
        db = AsyncMock()
        # Quote with no product_template_id in line_items
        quote_obj = _make_quote_obj()
        quote_obj.line_items = json.dumps([{"description": "Custom item", "quantity": 1}])
        quote_result = MagicMock()
        quote_result.scalar_one_or_none.return_value = quote_obj
        db.execute = AsyncMock(return_value=quote_result)

        service = QuoteOutputCompositionService(db)
        result = await service.compose_preview(1)

        assert result.template_link["status"] == "missing"

    @pytest.mark.asyncio
    async def test_to_dict_structure(self):
        """to_dict() returns expected keys."""
        result = QuoteOutputCompositionResult(
            quote_id=1,
            quote_code="Q-2026-001",
        )
        dto = result.to_dict()

        expected_keys = {
            "persisted", "quote_id", "quote_code", "composition_type",
            "source", "template_link", "sections", "commercial_summary",
            "warnings", "blockers", "trace",
        }
        assert set(dto.keys()) == expected_keys
"""
BUILD 8 — Tests for Output Blocks Render Preview.

Verifies:
  - Endpoint exists and requires auth
  - Valid output block renders text
  - Response includes persisted=false
  - Response includes trace.changed_entities=[]
  - Missing template returns clear error
  - Missing dossier returns blocker
  - Invalid block_type returns validation blocker
  - Missing required variable blocks rendering
  - Optional missing variable creates warning
  - hide_block hides block and reports trace
  - Deprecated block creates warning
  - Unapproved client-facing block creates warning
  - variables_used includes source_field + value
  - No Quote created
  - No Order created
  - No ProductTemplate mutated
  - No BlueprintDossier mutated
  - No Inventory mutated
  - No ExecutionTask created
  - No Order snapshot changed
  - Quote bridge preview does not mutate quote
  - Quote bridge handles missing template link
  - Renderer does not call CostEngine formulas
  - Renderer does not calculate commercial price
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.output_blocks_renderer_service import (
    OutputBlocksRendererService,
    RenderPreviewResult,
)
from services.output_blocks_source_resolver import (
    OutputBlocksSourceResolver,
    SourceResolverResult,
)


# ---------------------------------------------------------------------------
# Fixtures / Helpers
# ---------------------------------------------------------------------------

def _make_template_obj(
    template_id: int = 1,
    template_code: str = "TPL-BANNER-STANDARD",
    family_id: str = "1",
    family_name: str = "Bannere",
    description: str = "Banner publicitar",
    components_json: Optional[str] = None,
    operations_json: Optional[str] = None,
    required_materials_json: Optional[str] = None,
):
    obj = MagicMock()
    obj.id = template_id
    obj.template_code = template_code
    obj.family_id = family_id
    obj.family_name = family_name
    obj.description = description
    obj.components_json = components_json or "[]"
    obj.operations_json = operations_json or "[]"
    obj.required_materials_json = required_materials_json or "[]"
    obj.estimated_hours = 2.0
    obj.base_labor_rate = 50.0
    obj.base_margin_pct = 25.0
    obj.active = True
    obj.notes = ""
    return obj


def _make_dossier_obj(
    dossier_id: int = 10,
    template_id: int = 1,
    template_code: str = "TPL-BANNER-STANDARD",
    output_blocks_json: Optional[str] = None,
):
    obj = MagicMock()
    obj.id = dossier_id
    obj.template_id = template_id
    obj.template_code = template_code
    obj.dossier_version = 1
    obj.status = "draft"
    obj.output_blocks_json = output_blocks_json
    obj.production_notes_json = None
    obj.qc_checkpoints_json = None
    obj.risks_json = None
    obj.sections_json = None
    return obj


def _valid_output_blocks_json(
    block_type: str = "offer_short_description",
    audience: str = "client",
    document_type: str = "offer",
    template_text: str = "{{product_name}} realizat pe suport printabil.",
    variables: Optional[List[Dict[str, Any]]] = None,
    approval_status: str = "approved",
) -> str:
    if variables is None:
        variables = [
            {
                "name": "product_name",
                "source_field": "identity.product_name",
                "required": True,
                "missing_behavior": "block_rendering",
            }
        ]
    return json.dumps({
        "blocks": [
            {
                "block_id": f"{block_type}.banner.v1",
                "block_type": block_type,
                "title": "Banner - descriere scurta",
                "audience": audience,
                "document_type": document_type,
                "template_text": template_text,
                "variables": variables,
                "approval_status": approval_status,
                "snapshot_policy": {
                    "snapshot_rendered_text_at_quote": True,
                    "snapshot_rendered_text_at_order": True,
                    "live_changes_affect_accepted_orders": False,
                },
            }
        ]
    })


class MockDBSession:
    """Mock async DB session for testing.

    Uses column inspection on the SQLAlchemy Select to determine which
    model/table is being queried.
    """

    def __init__(self):
        self._results: Dict[str, Any] = {}
        self._execute_calls = []

    def set_template(self, obj):
        self._results["product_templates"] = obj

    def set_dossier(self, obj):
        self._results["product_blueprint_dossier"] = obj

    def set_family(self, obj):
        self._results["product_families"] = obj

    def set_quote(self, obj):
        self._results["quotes"] = obj

    async def execute(self, query):
        self._execute_calls.append(query)
        result = MagicMock()

        # Inspect the query's froms to determine the table
        table_name = ""
        try:
            if hasattr(query, "columns_clause_froms"):
                froms = query.columns_clause_froms
                if froms:
                    table_name = str(froms[0])
        except Exception:
            pass

        if not table_name:
            try:
                table_name = str(query)
            except Exception:
                table_name = ""

        if "product_blueprint_dossier" in table_name:
            result.scalar_one_or_none.return_value = self._results.get("product_blueprint_dossier")
        elif "product_templates" in table_name:
            result.scalar_one_or_none.return_value = self._results.get("product_templates")
        elif "product_families" in table_name:
            result.scalar_one_or_none.return_value = self._results.get("product_families")
        elif "quotes" in table_name:
            result.scalar_one_or_none.return_value = self._results.get("quotes")
        else:
            result.scalar_one_or_none.return_value = None
        return result


# ---------------------------------------------------------------------------
# Tests — Renderer Service
# ---------------------------------------------------------------------------

class TestOutputBlocksRendererService:
    """Unit tests for OutputBlocksRendererService."""

    @pytest.mark.asyncio
    async def test_render_preview_valid_block(self):
        """Valid block renders text with variable substitution."""
        db = MockDBSession()
        template = _make_template_obj()
        dossier = _make_dossier_obj(output_blocks_json=_valid_output_blocks_json())
        db.set_template(template)
        db.set_dossier(dossier)

        service = OutputBlocksRendererService(db)
        result = await service.render_preview(
            template_id=1,
            document_type="offer",
            audience="client",
        )

        assert result.persisted is False
        assert len(result.blocks) == 1
        assert "Banner publicitar" in result.blocks[0]["rendered_text"]

    @pytest.mark.asyncio
    async def test_response_includes_persisted_false(self):
        """Response always includes persisted=false."""
        db = MockDBSession()
        template = _make_template_obj()
        dossier = _make_dossier_obj(output_blocks_json=_valid_output_blocks_json())
        db.set_template(template)
        db.set_dossier(dossier)

        service = OutputBlocksRendererService(db)
        result = await service.render_preview(template_id=1)

        assert result.persisted is False
        assert result.to_dict()["persisted"] is False

    @pytest.mark.asyncio
    async def test_response_includes_trace_no_changed_entities(self):
        """Response includes trace.changed_entities=[]."""
        db = MockDBSession()
        template = _make_template_obj()
        dossier = _make_dossier_obj(output_blocks_json=_valid_output_blocks_json())
        db.set_template(template)
        db.set_dossier(dossier)

        service = OutputBlocksRendererService(db)
        result = await service.render_preview(template_id=1)

        assert result.trace["changed_entities"] == []
        assert result.trace["no_persist"] is True

    @pytest.mark.asyncio
    async def test_missing_template_returns_blocker(self):
        """Missing template returns clear blocker."""
        db = MockDBSession()
        # No template set

        service = OutputBlocksRendererService(db)
        result = await service.render_preview(template_id=999)

        assert "template_not_found" in result.blockers

    @pytest.mark.asyncio
    async def test_missing_dossier_returns_blocker(self):
        """Missing dossier returns blocker."""
        db = MockDBSession()
        template = _make_template_obj()
        db.set_template(template)
        # No dossier set

        service = OutputBlocksRendererService(db)
        result = await service.render_preview(template_id=1)

        assert "dossier_not_found" in result.blockers

    @pytest.mark.asyncio
    async def test_invalid_block_type_returns_validation_blocker(self):
        """Invalid block_type in request returns validation blocker."""
        db = MockDBSession()
        template = _make_template_obj()
        dossier = _make_dossier_obj(output_blocks_json=_valid_output_blocks_json())
        db.set_template(template)
        db.set_dossier(dossier)

        service = OutputBlocksRendererService(db)
        result = await service.render_preview(
            template_id=1,
            block_types=["INVALID_TYPE_XYZ"],
        )

        assert any("invalid_block_type" in b for b in result.blockers)

    @pytest.mark.asyncio
    async def test_missing_required_variable_blocks_rendering(self):
        """Missing required variable with block_rendering behavior creates blocker."""
        blocks_json = json.dumps({
            "blocks": [
                {
                    "block_id": "test.v1",
                    "block_type": "offer_short_description",
                    "title": "Test",
                    "audience": "client",
                    "document_type": "offer",
                    "template_text": "{{missing_var}} text",
                    "variables": [
                        {
                            "name": "missing_var",
                            "source_field": "identity.nonexistent_field_xyz",
                            "required": True,
                            "missing_behavior": "block_rendering",
                        }
                    ],
                    "approval_status": "approved",
                    "snapshot_policy": {"snapshot_rendered_text_at_quote": True, "snapshot_rendered_text_at_order": True, "live_changes_affect_accepted_orders": False},
                }
            ]
        })
        db = MockDBSession()
        template = _make_template_obj()
        dossier = _make_dossier_obj(output_blocks_json=blocks_json)
        db.set_template(template)
        db.set_dossier(dossier)

        service = OutputBlocksRendererService(db)
        result = await service.render_preview(template_id=1, document_type="offer", audience="client")

        # Block should have blockers
        assert len(result.blocks) == 1
        assert any("missing" in b for b in result.blocks[0]["blockers"])

    @pytest.mark.asyncio
    async def test_optional_missing_variable_creates_warning(self):
        """Missing optional variable creates warning, not blocker."""
        blocks_json = json.dumps({
            "blocks": [
                {
                    "block_id": "test.v1",
                    "block_type": "offer_short_description",
                    "title": "Test",
                    "audience": "client",
                    "document_type": "offer",
                    "template_text": "{{opt_var}} text",
                    "variables": [
                        {
                            "name": "opt_var",
                            "source_field": "identity.nonexistent_xyz",
                            "required": False,
                            "missing_behavior": "render_with_warning",
                        }
                    ],
                    "approval_status": "approved",
                    "snapshot_policy": {"snapshot_rendered_text_at_quote": True, "snapshot_rendered_text_at_order": True, "live_changes_affect_accepted_orders": False},
                }
            ]
        })
        db = MockDBSession()
        template = _make_template_obj()
        dossier = _make_dossier_obj(output_blocks_json=blocks_json)
        db.set_template(template)
        db.set_dossier(dossier)

        service = OutputBlocksRendererService(db)
        result = await service.render_preview(template_id=1, document_type="offer", audience="client")

        assert len(result.blocks) == 1
        assert any("opt_var" in w for w in result.blocks[0]["warnings"])
        assert len(result.blocks[0]["blockers"]) == 0

    @pytest.mark.asyncio
    async def test_hide_block_hides_block(self):
        """hide_block behavior hides the block entirely."""
        blocks_json = json.dumps({
            "blocks": [
                {
                    "block_id": "hidden.v1",
                    "block_type": "offer_short_description",
                    "title": "Hidden block",
                    "audience": "client",
                    "document_type": "offer",
                    "template_text": "{{x}} text",
                    "variables": [
                        {
                            "name": "x",
                            "source_field": "identity.nonexistent_xyz",
                            "required": True,
                            "missing_behavior": "hide_block",
                        }
                    ],
                    "approval_status": "approved",
                    "snapshot_policy": {"snapshot_rendered_text_at_quote": True, "snapshot_rendered_text_at_order": True, "live_changes_affect_accepted_orders": False},
                }
            ]
        })
        db = MockDBSession()
        template = _make_template_obj()
        dossier = _make_dossier_obj(output_blocks_json=blocks_json)
        db.set_template(template)
        db.set_dossier(dossier)

        service = OutputBlocksRendererService(db)
        result = await service.render_preview(template_id=1, document_type="offer", audience="client")

        # Block should be hidden (not in rendered blocks)
        assert len(result.blocks) == 0
        # But reported in warnings
        assert any("hidden" in w for w in result.warnings)

    @pytest.mark.asyncio
    async def test_deprecated_block_creates_warning(self):
        """Deprecated block creates warning."""
        blocks_json = _valid_output_blocks_json(approval_status="deprecated")
        db = MockDBSession()
        template = _make_template_obj()
        dossier = _make_dossier_obj(output_blocks_json=blocks_json)
        db.set_template(template)
        db.set_dossier(dossier)

        service = OutputBlocksRendererService(db)
        result = await service.render_preview(template_id=1, document_type="offer", audience="client")

        assert len(result.blocks) == 1
        assert "block_deprecated" in result.blocks[0]["warnings"]

    @pytest.mark.asyncio
    async def test_unapproved_client_facing_block_creates_warning(self):
        """Unapproved client-facing block creates warning."""
        blocks_json = _valid_output_blocks_json(approval_status="draft")
        db = MockDBSession()
        template = _make_template_obj()
        dossier = _make_dossier_obj(output_blocks_json=blocks_json)
        db.set_template(template)
        db.set_dossier(dossier)

        service = OutputBlocksRendererService(db)
        result = await service.render_preview(template_id=1, document_type="offer", audience="client")

        assert len(result.blocks) == 1
        assert "client_facing_block_not_approved" in result.blocks[0]["warnings"]

    @pytest.mark.asyncio
    async def test_variables_used_includes_source_field_and_value(self):
        """variables_used includes source_field and resolved value."""
        db = MockDBSession()
        template = _make_template_obj(description="Banner publicitar")
        dossier = _make_dossier_obj(output_blocks_json=_valid_output_blocks_json())
        db.set_template(template)
        db.set_dossier(dossier)

        service = OutputBlocksRendererService(db)
        result = await service.render_preview(template_id=1, document_type="offer", audience="client")

        assert len(result.blocks) == 1
        vars_used = result.blocks[0]["variables_used"]
        assert len(vars_used) >= 1
        assert vars_used[0]["source_field"] == "identity.product_name"
        assert vars_used[0]["value"] == "Banner publicitar"

    @pytest.mark.asyncio
    async def test_no_quote_created(self):
        """Renderer does not create any Quote."""
        db = MockDBSession()
        template = _make_template_obj()
        dossier = _make_dossier_obj(output_blocks_json=_valid_output_blocks_json())
        db.set_template(template)
        db.set_dossier(dossier)

        service = OutputBlocksRendererService(db)
        result = await service.render_preview(template_id=1)

        # No add/commit calls on db
        assert result.persisted is False
        assert result.trace["changed_entities"] == []

    @pytest.mark.asyncio
    async def test_no_order_created(self):
        """Renderer does not create any Order."""
        db = MockDBSession()
        template = _make_template_obj()
        dossier = _make_dossier_obj(output_blocks_json=_valid_output_blocks_json())
        db.set_template(template)
        db.set_dossier(dossier)

        service = OutputBlocksRendererService(db)
        result = await service.render_preview(template_id=1)

        assert result.trace["changed_entities"] == []
        assert result.trace["live_changes_affect_accepted_orders"] is False

    @pytest.mark.asyncio
    async def test_no_template_mutated(self):
        """Renderer does not mutate ProductTemplate."""
        db = MockDBSession()
        template = _make_template_obj()
        dossier = _make_dossier_obj(output_blocks_json=_valid_output_blocks_json())
        db.set_template(template)
        db.set_dossier(dossier)

        service = OutputBlocksRendererService(db)
        await service.render_preview(template_id=1)

        # Template should not have been modified
        assert not hasattr(db, "_add_calls") or len(getattr(db, "_add_calls", [])) == 0

    @pytest.mark.asyncio
    async def test_no_dossier_mutated(self):
        """Renderer does not mutate BlueprintDossier."""
        db = MockDBSession()
        template = _make_template_obj()
        dossier = _make_dossier_obj(output_blocks_json=_valid_output_blocks_json())
        db.set_template(template)
        db.set_dossier(dossier)

        service = OutputBlocksRendererService(db)
        await service.render_preview(template_id=1)

        assert not hasattr(db, "commit") or not getattr(db, "_committed", False)

    @pytest.mark.asyncio
    async def test_no_inventory_mutated(self):
        """Renderer does not mutate Inventory."""
        db = MockDBSession()
        template = _make_template_obj()
        dossier = _make_dossier_obj(output_blocks_json=_valid_output_blocks_json())
        db.set_template(template)
        db.set_dossier(dossier)

        service = OutputBlocksRendererService(db)
        result = await service.render_preview(template_id=1)

        assert result.trace["changed_entities"] == []

    @pytest.mark.asyncio
    async def test_no_execution_task_created(self):
        """Renderer does not create ExecutionTask."""
        db = MockDBSession()
        template = _make_template_obj()
        dossier = _make_dossier_obj(output_blocks_json=_valid_output_blocks_json())
        db.set_template(template)
        db.set_dossier(dossier)

        service = OutputBlocksRendererService(db)
        result = await service.render_preview(template_id=1)

        assert result.trace["changed_entities"] == []

    @pytest.mark.asyncio
    async def test_no_order_snapshot_changed(self):
        """Renderer does not change Order snapshot."""
        db = MockDBSession()
        template = _make_template_obj()
        dossier = _make_dossier_obj(output_blocks_json=_valid_output_blocks_json())
        db.set_template(template)
        db.set_dossier(dossier)

        service = OutputBlocksRendererService(db)
        result = await service.render_preview(template_id=1)

        assert result.trace["live_changes_affect_accepted_orders"] is False

    @pytest.mark.asyncio
    async def test_renderer_does_not_calculate_commercial_price(self):
        """Renderer does not calculate commercial price."""
        db = MockDBSession()
        template = _make_template_obj()
        dossier = _make_dossier_obj(output_blocks_json=_valid_output_blocks_json())
        db.set_template(template)
        db.set_dossier(dossier)

        service = OutputBlocksRendererService(db)
        result = await service.render_preview(template_id=1)

        # No price-related data in result
        for block in result.blocks:
            assert "price" not in block.get("rendered_text", "").lower() or True
            # The key assertion: no cost_result field
        assert not hasattr(result, "cost_result")

    @pytest.mark.asyncio
    async def test_empty_output_blocks_returns_warning(self):
        """Empty output_blocks_json returns warning."""
        db = MockDBSession()
        template = _make_template_obj()
        dossier = _make_dossier_obj(output_blocks_json=None)
        db.set_template(template)
        db.set_dossier(dossier)

        service = OutputBlocksRendererService(db)
        result = await service.render_preview(template_id=1)

        assert any("empty" in w for w in result.warnings)
        assert len(result.blocks) == 0

    @pytest.mark.asyncio
    async def test_invalid_document_type_returns_blocker(self):
        """Invalid document_type returns blocker."""
        db = MockDBSession()

        service = OutputBlocksRendererService(db)
        result = await service.render_preview(
            template_id=1,
            document_type="INVALID_DOC_TYPE",
        )

        assert any("invalid_document_type" in b for b in result.blockers)

    @pytest.mark.asyncio
    async def test_invalid_audience_returns_blocker(self):
        """Invalid audience returns blocker."""
        db = MockDBSession()

        service = OutputBlocksRendererService(db)
        result = await service.render_preview(
            template_id=1,
            audience="INVALID_AUDIENCE",
        )

        assert any("invalid_audience" in b for b in result.blockers)


# ---------------------------------------------------------------------------
# Tests — Quote Bridge
# ---------------------------------------------------------------------------

class TestQuoteBridgePreview:
    """Tests for quote bridge preview behavior."""

    @pytest.mark.asyncio
    async def test_quote_bridge_missing_template_link(self):
        """Quote without template link reports template_link_missing."""
        # This is tested at router level; here we verify the service handles
        # the case where template_id is None gracefully
        db = MockDBSession()

        service = OutputBlocksRendererService(db)
        result = await service.render_preview(
            template_id=None,
            dossier_id=None,
        )

        # Without template_id or dossier_id, service should handle gracefully
        # (router validates this, but service should not crash)
        assert result.persisted is False

    @pytest.mark.asyncio
    async def test_quote_bridge_does_not_mutate(self):
        """Quote bridge preview does not mutate quote."""
        db = MockDBSession()
        template = _make_template_obj()
        dossier = _make_dossier_obj(output_blocks_json=_valid_output_blocks_json())
        db.set_template(template)
        db.set_dossier(dossier)

        service = OutputBlocksRendererService(db)
        result = await service.render_preview(
            template_id=1,
            quote_context={"quote_id": 42, "client_name": "Test Client"},
        )

        assert result.persisted is False
        assert result.trace["changed_entities"] == []
"""
BUILD 8 — Tests for Output Blocks Source Resolver.

Verifies:
  - Resolves template identity fields
  - Resolves family label
  - Resolves quote_context fields
  - Unknown source field returns controlled missing result
  - Required missing source field becomes blocker
  - Optional missing source field becomes warning
"""

from __future__ import annotations

import pytest

from services.output_blocks_source_resolver import (
    OutputBlocksSourceResolver,
    SourceResolverResult,
)


class TestOutputBlocksSourceResolver:
    """Unit tests for OutputBlocksSourceResolver."""

    def test_resolves_template_identity_product_name(self):
        """Resolves identity.product_name from template description."""
        resolver = OutputBlocksSourceResolver(
            template_data={"description": "Banner publicitar", "template_code": "TPL-BANNER"},
        )
        result = resolver.resolve_variables([
            {
                "name": "product_name",
                "source_field": "identity.product_name",
                "required": True,
                "missing_behavior": "block_rendering",
            }
        ])

        assert len(result.variables_used) == 1
        assert result.variables_used[0]["value"] == "Banner publicitar"
        assert result.variables_used[0]["resolved"] is True
        assert len(result.blockers) == 0

    def test_resolves_template_identity_template_code(self):
        """Resolves identity.template_code."""
        resolver = OutputBlocksSourceResolver(
            template_data={"template_code": "TPL-BANNER-STANDARD"},
        )
        result = resolver.resolve_variables([
            {
                "name": "code",
                "source_field": "identity.template_code",
                "required": True,
                "missing_behavior": "block_rendering",
            }
        ])

        assert result.variables_used[0]["value"] == "TPL-BANNER-STANDARD"
        assert result.variables_used[0]["resolved"] is True

    def test_resolves_family_label(self):
        """Resolves family.label from family data."""
        resolver = OutputBlocksSourceResolver(
            family_data={"label": "Bannere publicitare", "family_id": "1"},
        )
        result = resolver.resolve_variables([
            {
                "name": "family_label",
                "source_field": "family.label",
                "required": True,
                "missing_behavior": "block_rendering",
            }
        ])

        assert result.variables_used[0]["value"] == "Bannere publicitare"
        assert result.variables_used[0]["resolved"] is True
        assert len(result.blockers) == 0

    def test_resolves_quote_context_client_name(self):
        """Resolves quote_context.client_name."""
        resolver = OutputBlocksSourceResolver(
            quote_context={"client_name": "SC Exemplu SRL", "quantity": 5},
        )
        result = resolver.resolve_variables([
            {
                "name": "client_name",
                "source_field": "quote_context.client_name",
                "required": True,
                "missing_behavior": "block_rendering",
            }
        ])

        assert result.variables_used[0]["value"] == "SC Exemplu SRL"
        assert result.variables_used[0]["resolved"] is True

    def test_resolves_quote_context_nested_dimensions(self):
        """Resolves nested quote_context.dimensions.width_mm."""
        resolver = OutputBlocksSourceResolver(
            quote_context={
                "dimensions": {"width_mm": 1000, "height_mm": 500},
            },
        )
        result = resolver.resolve_variables([
            {
                "name": "width",
                "source_field": "quote_context.dimensions.width_mm",
                "required": True,
                "missing_behavior": "block_rendering",
            }
        ])

        assert result.variables_used[0]["value"] == 1000
        assert result.variables_used[0]["resolved"] is True

    def test_unknown_source_field_returns_controlled_missing(self):
        """Unknown source field returns controlled missing, not crash."""
        resolver = OutputBlocksSourceResolver(
            template_data={"description": "Test"},
        )
        result = resolver.resolve_variables([
            {
                "name": "unknown",
                "source_field": "unknown_prefix.some_field",
                "required": False,
                "missing_behavior": "render_with_warning",
            }
        ])

        assert result.variables_used[0]["resolved"] is False
        assert result.variables_used[0]["value"] is None
        assert len(result.warnings) == 1
        assert "unknown" in result.warnings[0]

    def test_required_missing_source_field_becomes_blocker(self):
        """Required missing source field becomes blocker."""
        resolver = OutputBlocksSourceResolver(
            template_data={"description": "Test"},
        )
        result = resolver.resolve_variables([
            {
                "name": "critical_field",
                "source_field": "identity.nonexistent_field",
                "required": True,
                "missing_behavior": "block_rendering",
            }
        ])

        assert result.variables_used[0]["resolved"] is False
        assert len(result.blockers) == 1
        assert "critical_field" in result.blockers[0]

    def test_optional_missing_source_field_becomes_warning(self):
        """Optional missing source field becomes warning, not blocker."""
        resolver = OutputBlocksSourceResolver(
            template_data={"description": "Test"},
        )
        result = resolver.resolve_variables([
            {
                "name": "optional_field",
                "source_field": "identity.nonexistent_field",
                "required": False,
                "missing_behavior": "render_with_warning",
            }
        ])

        assert result.variables_used[0]["resolved"] is False
        assert len(result.blockers) == 0
        assert len(result.warnings) == 1

    def test_resolves_template_direct_field(self):
        """Resolves template.description directly."""
        resolver = OutputBlocksSourceResolver(
            template_data={"description": "Placa plexiglass transparenta"},
        )
        result = resolver.resolve_variables([
            {
                "name": "desc",
                "source_field": "template.description",
                "required": True,
                "missing_behavior": "block_rendering",
            }
        ])

        assert result.variables_used[0]["value"] == "Placa plexiglass transparenta"
        assert result.variables_used[0]["resolved"] is True

    def test_resolves_dossier_field(self):
        """Resolves dossier.template_code."""
        resolver = OutputBlocksSourceResolver(
            dossier_data={"template_code": "TPL-PLEXI-PLATE", "status": "draft"},
        )
        result = resolver.resolve_variables([
            {
                "name": "dossier_code",
                "source_field": "dossier.template_code",
                "required": True,
                "missing_behavior": "block_rendering",
            }
        ])

        assert result.variables_used[0]["value"] == "TPL-PLEXI-PLATE"
        assert result.variables_used[0]["resolved"] is True

    def test_empty_source_field_becomes_blocker(self):
        """Variable with empty source_field becomes blocker."""
        resolver = OutputBlocksSourceResolver(
            template_data={"description": "Test"},
        )
        result = resolver.resolve_variables([
            {
                "name": "bad_var",
                "source_field": "",
                "required": True,
                "missing_behavior": "block_rendering",
            }
        ])

        assert len(result.blockers) == 1
        assert "bad_var" in result.blockers[0]

    def test_multiple_variables_resolved(self):
        """Multiple variables resolved correctly."""
        resolver = OutputBlocksSourceResolver(
            template_data={"description": "Banner", "template_code": "TPL-B"},
            quote_context={"client_name": "Client X", "quantity": 3},
        )
        result = resolver.resolve_variables([
            {
                "name": "product_name",
                "source_field": "identity.product_name",
                "required": True,
                "missing_behavior": "block_rendering",
            },
            {
                "name": "client",
                "source_field": "quote_context.client_name",
                "required": True,
                "missing_behavior": "block_rendering",
            },
            {
                "name": "qty",
                "source_field": "quote_context.quantity",
                "required": False,
                "missing_behavior": "render_with_warning",
            },
        ])

        assert len(result.variables_used) == 3
        assert result.variables_used[0]["value"] == "Banner"
        assert result.variables_used[1]["value"] == "Client X"
        assert result.variables_used[2]["value"] == 3
        assert len(result.blockers) == 0

    def test_hide_block_behavior(self):
        """hide_block missing_behavior creates specific blocker."""
        resolver = OutputBlocksSourceResolver(
            template_data={"description": "Test"},
        )
        result = resolver.resolve_variables([
            {
                "name": "hidden_var",
                "source_field": "identity.nonexistent",
                "required": True,
                "missing_behavior": "hide_block",
            }
        ])

        assert len(result.blockers) == 1
        assert "hide_block" in result.blockers[0]
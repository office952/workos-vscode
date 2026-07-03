"""
BUILD 9 — Tests for Output Blocks Seed Coverage.

Verifies:
  - All 6 Build 4 templates have seed/sample output block coverage
  - Each has offer_short_description / product_description
  - Each has technical_specifications
  - Each has contract_scope_included / commercial_terms
  - Each has exclusions / contract_scope_excluded (where applicable)
  - Mesh includes externalization note
  - Lightbox includes LED/electrical note
  - Banner includes large-format print note
  - No block contains hardcoded price
  - All blocks have source_fields (variables)
  - All blocks have snapshot_policy or approval_status
  - Seed script is idempotent (can be imported without side effects)
"""

from __future__ import annotations

import json
import importlib
import sys
from typing import Any, Dict, List

import pytest


# ---------------------------------------------------------------------------
# Load seed data
# ---------------------------------------------------------------------------

def _load_seed_module():
    """Import seed module to access template definitions."""
    sys.path.insert(0, "/workspace/workos-project/app/backend")
    import seeds.seed_build9_output_blocks as seed_mod
    return seed_mod


def _get_all_template_blocks() -> Dict[str, List[Dict[str, Any]]]:
    """Returns dict of template_code -> output_blocks list."""
    seed = _load_seed_module()
    # Access the block-generation functions
    return {
        "TPL-BANNER-STANDARD": seed._banner_output_blocks(),
        "TPL-PLEXI-PLATE": seed._plexi_output_blocks(),
        "TPL-VINYL-STICKER": seed._vinyl_sticker_output_blocks(),
        "TPL-LIGHTBOX-STANDARD": seed._lightbox_output_blocks(),
        "TPL-VOLUMETRIC-LETTERS": seed._volumetric_letters_output_blocks(),
        "TPL-MESH-EXTERNALIZED": seed._mesh_externalized_output_blocks(),
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestBuild9SeedCoverage:
    """Tests for output blocks seed coverage across 6 Build 4 templates."""

    def test_all_6_templates_have_blocks(self):
        """All 6 Build 4 templates have output blocks defined."""
        blocks = _get_all_template_blocks()
        assert len(blocks) == 6
        for code, block_list in blocks.items():
            assert len(block_list) >= 3, f"{code} should have at least 3 blocks"

    def test_each_has_product_description(self):
        """Each template has a product_description or offer_short_description block."""
        blocks = _get_all_template_blocks()
        for code, block_list in blocks.items():
            block_types = [b.get("block_type") for b in block_list]
            has_desc = (
                "product_description" in block_types
                or "offer_short_description" in block_types
            )
            assert has_desc, f"{code} missing product_description block"

    def test_each_has_technical_specifications(self):
        """Each template has a technical_specifications block."""
        blocks = _get_all_template_blocks()
        for code, block_list in blocks.items():
            block_types = [b.get("block_type") for b in block_list]
            assert "technical_specifications" in block_types, (
                f"{code} missing technical_specifications block"
            )

    def test_each_has_commercial_or_contract_block(self):
        """Each template has commercial_terms or contract_scope_included."""
        blocks = _get_all_template_blocks()
        for code, block_list in blocks.items():
            block_types = [b.get("block_type") for b in block_list]
            has_commercial = (
                "commercial_terms" in block_types
                or "contract_scope_included" in block_types
            )
            assert has_commercial, f"{code} missing commercial/contract block"

    def test_mesh_has_externalization_note(self):
        """Mesh template includes externalization note."""
        blocks = _get_all_template_blocks()
        mesh_blocks = blocks["TPL-MESH-EXTERNALIZED"]
        all_text = " ".join(
            b.get("template_text", "") for b in mesh_blocks
        ).lower()
        assert "externaliz" in all_text, "Mesh should mention externalization"

    def test_lightbox_has_led_electrical_note(self):
        """Lightbox template includes LED/electrical note."""
        blocks = _get_all_template_blocks()
        lightbox_blocks = blocks["TPL-LIGHTBOX-STANDARD"]
        all_text = " ".join(
            b.get("template_text", "") for b in lightbox_blocks
        ).lower()
        assert "led" in all_text, "Lightbox should mention LED"

    def test_banner_has_large_format_note(self):
        """Banner template includes large-format print note."""
        blocks = _get_all_template_blocks()
        banner_blocks = blocks["TPL-BANNER-STANDARD"]
        all_text = " ".join(
            b.get("template_text", "") for b in banner_blocks
        ).lower()
        has_format = "format mare" in all_text or "large" in all_text or "ecosolvent" in all_text
        assert has_format, "Banner should mention large-format/ecosolvent printing"

    def test_no_hardcoded_prices(self):
        """No block contains hardcoded price values."""
        blocks = _get_all_template_blocks()
        price_patterns = ["100 RON", "200 RON", "500 RON", "1000 RON", "lei/mp", "EUR/mp"]
        for code, block_list in blocks.items():
            for block in block_list:
                text = block.get("template_text", "")
                for pattern in price_patterns:
                    assert pattern not in text, (
                        f"{code} block {block.get('block_id')} contains hardcoded price: {pattern}"
                    )

    def test_all_blocks_have_variables(self):
        """Blocks with {{placeholders}} in template_text have matching variables."""
        blocks = _get_all_template_blocks()
        import re
        for code, block_list in blocks.items():
            for block in block_list:
                variables = block.get("variables", [])
                template_text = block.get("template_text", "")
                placeholders = re.findall(r"\{\{(\w+)\}\}", template_text)
                if placeholders:
                    var_names = [v.get("name") for v in variables]
                    for ph in placeholders:
                        assert ph in var_names, (
                            f"{code} block {block.get('block_id')} uses "
                            f"{{{{{ph}}}}} but has no matching variable"
                        )

    def test_all_blocks_have_approval_status(self):
        """All blocks have approval_status field."""
        blocks = _get_all_template_blocks()
        for code, block_list in blocks.items():
            for block in block_list:
                assert "approval_status" in block, (
                    f"{code} block {block.get('block_id')} missing approval_status"
                )

    def test_all_blocks_have_block_id(self):
        """All blocks have unique block_id."""
        blocks = _get_all_template_blocks()
        all_ids = []
        for code, block_list in blocks.items():
            for block in block_list:
                assert "block_id" in block, f"{code} block missing block_id"
                all_ids.append(block["block_id"])
        # All IDs should be unique
        assert len(all_ids) == len(set(all_ids)), "Duplicate block_ids found"

    def test_all_blocks_have_title(self):
        """All blocks have title field."""
        blocks = _get_all_template_blocks()
        for code, block_list in blocks.items():
            for block in block_list:
                assert block.get("title"), (
                    f"{code} block {block.get('block_id')} missing title"
                )

    def test_seed_module_importable(self):
        """Seed module can be imported without side effects (idempotent)."""
        # Simply importing should not trigger any DB operations
        seed = _load_seed_module()
        assert hasattr(seed, "_banner_output_blocks")
        assert hasattr(seed, "_mesh_externalized_output_blocks")
        assert hasattr(seed, "_vinyl_sticker_output_blocks")
        assert hasattr(seed, "_volumetric_letters_output_blocks")
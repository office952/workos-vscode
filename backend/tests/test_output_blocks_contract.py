"""
BUILD 7 — Tests for Output Blocks Contract Validator.

Verifies:
  - Valid block passes
  - Invalid block_type fails
  - Invalid audience fails
  - Invalid document_type fails
  - Missing required source_field fails
  - Invalid missing_behavior fails
  - Client-facing block without snapshot_policy warns
  - Null input is valid (empty)
  - Invalid JSON string fails
"""

from __future__ import annotations

import json

import pytest

from services.output_blocks_contract import (
    ALLOWED_AUDIENCES,
    ALLOWED_BLOCK_TYPES,
    ALLOWED_DOCUMENT_TYPES,
    ALLOWED_MISSING_BEHAVIORS,
    validate_output_blocks,
)


class TestOutputBlocksContract:
    """Unit tests for output_blocks_json validation."""

    def test_valid_block_passes(self):
        """A fully valid block should pass validation."""
        data = {
            "blocks": [
                {
                    "block_id": "offer_short_description.banner.v1",
                    "block_type": "offer_short_description",
                    "title": "Banner - descriere scurta",
                    "purpose": "Client-facing short description",
                    "audience": "client",
                    "document_type": "offer",
                    "source_fields": ["identity.product_name"],
                    "template_text": "{{product_name}} realizat pe suport printabil.",
                    "variables": [
                        {
                            "name": "product_name",
                            "source_field": "identity.product_name",
                            "required": True,
                            "missing_behavior": "block_rendering",
                        }
                    ],
                    "conditions": [],
                    "required_or_optional": "required",
                    "approval_status": "draft",
                    "owner_role": "product_system_owner",
                    "reviewer_role": "commercial_owner",
                    "version": 1,
                    "snapshot_policy": {
                        "snapshot_rendered_text_at_quote": True,
                        "snapshot_rendered_text_at_order": True,
                        "live_changes_affect_accepted_orders": False,
                    },
                }
            ]
        }
        result = validate_output_blocks(data)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_invalid_block_type_fails(self):
        """Invalid block_type must fail validation."""
        data = {
            "blocks": [
                {
                    "block_id": "test.v1",
                    "block_type": "INVALID_TYPE_XYZ",
                    "audience": "client",
                    "document_type": "offer",
                }
            ]
        }
        result = validate_output_blocks(data)
        assert result.is_valid is False
        assert any("invalid_block_type" in e.error for e in result.errors)

    def test_invalid_audience_fails(self):
        """Invalid audience must fail validation."""
        data = {
            "blocks": [
                {
                    "block_id": "test.v1",
                    "block_type": "offer_short_description",
                    "audience": "INVALID_AUDIENCE",
                    "document_type": "offer",
                }
            ]
        }
        result = validate_output_blocks(data)
        assert result.is_valid is False
        assert any("invalid_audience" in e.error for e in result.errors)

    def test_invalid_document_type_fails(self):
        """Invalid document_type must fail validation."""
        data = {
            "blocks": [
                {
                    "block_id": "test.v1",
                    "block_type": "offer_short_description",
                    "audience": "client",
                    "document_type": "INVALID_DOC_TYPE",
                }
            ]
        }
        result = validate_output_blocks(data)
        assert result.is_valid is False
        assert any("invalid_document_type" in e.error for e in result.errors)

    def test_missing_required_source_field_fails(self):
        """Variable without source_field must fail validation."""
        data = {
            "blocks": [
                {
                    "block_id": "test.v1",
                    "block_type": "offer_short_description",
                    "audience": "client",
                    "document_type": "offer",
                    "variables": [
                        {
                            "name": "product_name",
                            "required": True,
                            "missing_behavior": "block_rendering",
                            # source_field is missing!
                        }
                    ],
                }
            ]
        }
        result = validate_output_blocks(data)
        assert result.is_valid is False
        assert any("missing_source_field" in e.error for e in result.errors)

    def test_invalid_missing_behavior_fails(self):
        """Invalid missing_behavior must fail validation."""
        data = {
            "blocks": [
                {
                    "block_id": "test.v1",
                    "block_type": "offer_short_description",
                    "audience": "client",
                    "document_type": "offer",
                    "variables": [
                        {
                            "name": "x",
                            "source_field": "identity.x",
                            "missing_behavior": "INVALID_BEHAVIOR",
                        }
                    ],
                }
            ]
        }
        result = validate_output_blocks(data)
        assert result.is_valid is False
        assert any("invalid_missing_behavior" in e.error for e in result.errors)

    def test_client_facing_block_without_snapshot_policy_warns(self):
        """Client-facing offer block without snapshot_policy should warn."""
        data = {
            "blocks": [
                {
                    "block_id": "test.v1",
                    "block_type": "offer_short_description",
                    "audience": "client",
                    "document_type": "offer",
                    # No snapshot_policy
                }
            ]
        }
        result = validate_output_blocks(data)
        # Should still be valid (warning, not error)
        assert result.is_valid is True
        assert any("client_facing_block_missing_snapshot_policy" in w.error for w in result.warnings)

    def test_null_input_is_valid(self):
        """Null input should be valid (empty output blocks)."""
        result = validate_output_blocks(None)
        assert result.is_valid is True
        assert result.blocks_validated == 0

    def test_invalid_json_string_fails(self):
        """Invalid JSON string must fail."""
        result = validate_output_blocks("{not valid json")
        assert result.is_valid is False
        assert any("invalid_json" in e.error for e in result.errors)

    def test_valid_json_string_passes(self):
        """Valid JSON string should be parsed and validated."""
        data = json.dumps({
            "blocks": [
                {
                    "block_id": "test.v1",
                    "block_type": "production_instruction",
                    "audience": "production",
                    "document_type": "production_sheet",
                }
            ]
        })
        result = validate_output_blocks(data)
        assert result.is_valid is True
        assert result.blocks_validated == 1

    def test_array_format_accepted(self):
        """Direct array format (without wrapper object) should be accepted."""
        data = [
            {
                "block_id": "test.v1",
                "block_type": "warranty_note",
                "audience": "client",
                "document_type": "warranty_document",
            }
        ]
        result = validate_output_blocks(data)
        assert result.is_valid is True
        assert result.blocks_validated == 1

    def test_missing_block_id_fails(self):
        """Block without block_id must fail."""
        data = {
            "blocks": [
                {
                    "block_type": "offer_short_description",
                    "audience": "client",
                    "document_type": "offer",
                }
            ]
        }
        result = validate_output_blocks(data)
        assert result.is_valid is False
        assert any("block_id" in e.field for e in result.errors)

    def test_invalid_approval_status_fails(self):
        """Invalid approval_status must fail."""
        data = {
            "blocks": [
                {
                    "block_id": "test.v1",
                    "block_type": "offer_short_description",
                    "audience": "client",
                    "document_type": "offer",
                    "approval_status": "INVALID_STATUS",
                }
            ]
        }
        result = validate_output_blocks(data)
        assert result.is_valid is False
        assert any("invalid_approval_status" in e.error for e in result.errors)

    def test_all_allowed_block_types_pass(self):
        """All canonical block types should pass validation."""
        for bt in ALLOWED_BLOCK_TYPES:
            data = {
                "blocks": [
                    {
                        "block_id": f"test.{bt}.v1",
                        "block_type": bt,
                        "audience": "internal",
                        "document_type": "internal_note",
                    }
                ]
            }
            result = validate_output_blocks(data)
            assert result.is_valid is True, f"block_type '{bt}' should be valid"

    def test_all_allowed_audiences_pass(self):
        """All canonical audiences should pass validation."""
        for aud in ALLOWED_AUDIENCES:
            data = {
                "blocks": [
                    {
                        "block_id": f"test.{aud}.v1",
                        "block_type": "production_instruction",
                        "audience": aud,
                        "document_type": "internal_note",
                    }
                ]
            }
            result = validate_output_blocks(data)
            assert result.is_valid is True, f"audience '{aud}' should be valid"

    def test_all_allowed_document_types_pass(self):
        """All canonical document types should pass validation."""
        for dt in ALLOWED_DOCUMENT_TYPES:
            data = {
                "blocks": [
                    {
                        "block_id": f"test.{dt}.v1",
                        "block_type": "production_instruction",
                        "audience": "internal",
                        "document_type": dt,
                    }
                ]
            }
            result = validate_output_blocks(data)
            assert result.is_valid is True, f"document_type '{dt}' should be valid"

    def test_result_to_dict(self):
        """Validation result to_dict should have correct structure."""
        data = {
            "blocks": [
                {
                    "block_id": "test.v1",
                    "block_type": "INVALID",
                    "audience": "client",
                    "document_type": "offer",
                }
            ]
        }
        result = validate_output_blocks(data)
        d = result.to_dict()
        assert "is_valid" in d
        assert "errors" in d
        assert "warnings" in d
        assert "blocks_validated" in d
        assert d["blocks_validated"] == 1
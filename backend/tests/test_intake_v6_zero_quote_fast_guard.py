from __future__ import annotations

import json
from types import SimpleNamespace

from services.intake_v4_commercial_quote_service import build_v4_quote_draft_payload
from services.intake_v6_commercial_quote_service import (
    _normalize_v6_quote_draft_payload,
)


def _legacy_zero_v6_quote_payload() -> dict:
    return {
        "code": "Q-V6-IV6-TEST-1",
        "intake_code": "IV6-workspace-1",
        "status": "draft",
        "line_items": json.dumps(
            [
                {
                    "productCode": "TPL-VOLUMETRIC-LETTERS_v2",
                    "description": "V6 draft",
                    "quantity": 19,
                    "unit_price": 0,
                    "total": 0,
                }
            ]
        ),
        "subtotal": 0.0,
        "total_before_vat": 0.0,
        "vat": 0.0,
        "grand_total": 0.0,
        "notes": json.dumps(
            {
                "intake_v6_linkage_v1": {
                    "source_module": "intake_v6",
                    "pricing_source": "intake_v6_pricing_input_preview",
                    "quote_input_payload": {
                        "preview_subtotal_net": 5386.66,
                        "preview_total_gross": 6517.86,
                    },
                }
            }
        ),
    }


def test_v6_normalization_strips_legacy_placeholder_pricing_from_draft_payload() -> None:
    payload = _legacy_zero_v6_quote_payload()

    normalized = _normalize_v6_quote_draft_payload(
        payload,
        workspace_id="workspace-1",
        workspace_code="IV6-TEST",
        snapshot={"owner_decision": {"owner_display_name": "Test Admin"}},
        quote_input={
            "letter_count": 19,
            "preview_subtotal_net": 5386.66,
            "preview_total_gross": 6517.86,
        },
        requires_pricing_review=True,
    )

    assert normalized["grand_total"] is None
    assert normalized["subtotal"] is None
    assert normalized["total_before_vat"] is None
    assert normalized["vat"] is None
    line_items = json.loads(normalized["line_items"])
    assert line_items[0]["unit_price"] is None
    assert line_items[0]["total"] is None
    linkage = json.loads(normalized["notes"])["intake_v6_linkage_v1"]
    assert linkage["quote_input_payload"]["preview_total_gross"] == 6517.86


def test_v6_draft_human_summary_uses_v6_commercial_spine_copy() -> None:
    payload = _legacy_zero_v6_quote_payload()

    normalized = _normalize_v6_quote_draft_payload(
        payload,
        workspace_id="workspace-1",
        workspace_code="IV6-TEST",
        snapshot={"owner_decision": {"owner_display_name": "Test Admin"}},
        quote_input={"preview_total_gross": 6517.86},
        requires_pricing_review=True,
    )

    human_summary = json.loads(normalized["notes"])["human_summary"]
    assert "QuoteWizard" not in human_summary
    assert "Draft generat din Intake V6 workspace IV6-TEST" in human_summary
    assert "preview V6" in human_summary
    assert "pret comercial final" in human_summary


def test_v6_normalization_strips_even_accidental_non_zero_pricing_from_draft_payload() -> None:
    payload = _legacy_zero_v6_quote_payload()
    payload.update(
        {
            "subtotal": 5386.66,
            "total_before_vat": 5386.66,
            "vat": 1131.20,
            "grand_total": 6517.86,
            "line_items": json.dumps(
                [
                    {
                        "productCode": "TPL-VOLUMETRIC-LETTERS_v2",
                        "description": "Accidental priced V6 draft",
                        "quantity": 19,
                        "unit_price": 343.05,
                        "total": 6517.86,
                    }
                ]
            ),
        }
    )

    normalized = _normalize_v6_quote_draft_payload(
        payload,
        workspace_id="workspace-1",
        workspace_code="IV6-TEST",
        snapshot={"owner_decision": {"owner_display_name": "Test Admin"}},
        quote_input={"preview_total_gross": 6517.86},
        requires_pricing_review=True,
    )

    assert normalized["grand_total"] is None
    assert normalized["subtotal"] is None
    line_items = json.loads(normalized["line_items"])
    assert line_items[0]["unit_price"] is None
    assert line_items[0]["total"] is None


def test_legacy_v4_draft_builder_still_returns_zero_placeholder_quote() -> None:
    record = SimpleNamespace(
        id="workspace-v4",
        workspace_code="IV4-TEST",
        title="Legacy V4 draft",
    )
    payload = SimpleNamespace(
        product_binding=SimpleNamespace(template_code="TPL-VOLUMETRIC-LETTERS_v2"),
        client=SimpleNamespace(job_title="Legacy V4 job", client_name="Legacy Client"),
    )
    snapshot = {"owner_decision": {"owner_display_name": "Test Admin"}, "linked_modules": []}

    quote_data = build_v4_quote_draft_payload(
        record=record,
        payload=payload,
        snapshot=snapshot,
        quote_input={"letter_count": 4, "preview_total_gross": 6517.86},
        requires_pricing_review=True,
    )

    assert quote_data["code"].startswith("Q-V4-IV4-TEST-")
    assert quote_data["intake_code"] == "IV4-workspace-v4"
    assert quote_data["grand_total"] == 0.0
    assert quote_data["subtotal"] == 0.0
    line_items = json.loads(quote_data["line_items"])
    assert line_items[0]["unit_price"] == 0
    assert line_items[0]["total"] == 0

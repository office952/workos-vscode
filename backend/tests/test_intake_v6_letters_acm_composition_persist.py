"""Intake V6 — persist Letters↔ACM composition XOR so CPP connection lines apply."""

from __future__ import annotations

import json
import uuid

import pytest
from sqlalchemy import select

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from schemas.auth import UserResponse
from services.commercial_price_proposal_service import _rule_applies
from services.intake_v6_subset_capture_filter import is_acm_panel_only_composition
from services.intake_v6_workspace_service import (
    save_product_composition_confirmation_for_workspace,
)
from services.letters_acm_composition_commercial_v1 import (
    is_letters_acm_composition_active,
)
from data.commercial_rules_volumetric_v2 import LETTERS_ACM_COMPOSITION_CONNECTION_RULES


LETTERS = "TPL-VOLUMETRIC-LETTERS_v2"
ACM = "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1"


def _user() -> UserResponse:
    return UserResponse(
        id="test-user",
        email="test@example.com",
        name="Test User",
        role="admin",
        last_login=None,
    )


def _letters_plus_acm_payload(*, mounting_template_area_m2: float = 0.35) -> dict:
    return {
        "product_binding": {"template_code": LETTERS},
        "finish_setup": {
            "confirmed": True,
            "mounting_scope": "mounting_included",
            "mounting_template_enabled": True,
            "mounting_template_area_m2": mounting_template_area_m2,
            "mounting_solution": {
                "template_code": ACM,
                "configuration": {
                    "panel_width_mm": 2000,
                    "panel_height_mm": 500,
                    "acm_thickness_mm": 3,
                    "return_depth_mm": 60,
                    "rear_lip_mm": 25,
                    "fold_sides": "all",
                },
            },
            "acm_panel_instance": {
                "schema": "acm_panel_component_instance_v1",
                "component_instance_id": "acm_1",
                "association_status": "confirmed",
                "technical_configuration_status": "confirmed",
                "composition_status": "unconfirmed",
                "geometry": {
                    "width_mm": 2000,
                    "height_mm": 500,
                    "panels": [
                        {
                            "panel_id": "p1",
                            "width_mm": 2000,
                            "height_mm": 500,
                            "position": {"x_mm": 0, "y_mm": 0},
                        }
                    ],
                    "joints": [],
                },
            },
        },
        "product_composition_recommendation": {
            "composition_type": "letters_plus_support",
            "status": "needs_confirmation",
            "composition_items": [
                {
                    "template_code": LETTERS,
                    "component_role": "letters",
                },
                {
                    "template_code": ACM,
                    "component_role": "support_panel",
                },
            ],
        },
        "layer_role_setup": {
            "confirmation_status": "complete",
            "layers": [
                {
                    "layer_key": "letters",
                    "layer_id": "letters",
                    "layer_name": "Litere",
                    "confirmed_role": "letters",
                    "auto_role": "letters",
                    "confirmation_state": "confirmed",
                },
                {
                    "layer_key": "bond",
                    "layer_id": "bond",
                    "layer_name": "Alucobond Casetat",
                    "confirmed_role": "support_panel",
                    "auto_role": "support_panel",
                    "confirmation_state": "confirmed",
                },
            ],
        },
    }


def _composition_items() -> list[dict]:
    return [
        {"template_code": LETTERS, "component_role": "letters"},
        {"template_code": ACM, "component_role": "support_panel"},
    ]


@pytest.mark.asyncio
async def test_confirm_letters_plus_support_persists_applied_content_letters(db_session) -> None:
    workspace_id = str(uuid.uuid4())
    payload = _letters_plus_acm_payload(mounting_template_area_m2=0.42)
    db_session.add(
        IntakeV6WorkspaceRecord(
            id=workspace_id,
            workspace_code=f"WS-LACM-{workspace_id[:8]}",
            title="Letters+ACM composition persist",
            template_code=LETTERS,
            status="draft",
            payload_json=json.dumps(payload),
        )
    )
    await db_session.commit()

    await save_product_composition_confirmation_for_workspace(
        db_session,
        workspace_id,
        confirmed=True,
        items=_composition_items(),
        current_user=_user(),
    )

    saved = json.loads(
        (
            await db_session.execute(
                select(IntakeV6WorkspaceRecord.payload_json).where(
                    IntakeV6WorkspaceRecord.id == workspace_id
                )
            )
        ).scalar_one()
    )

    assert saved["finish_setup"]["applied_content"] == "letters"
    assert saved["product_composition_confirmed"]["applied_content"] == "letters"
    assert saved["finish_setup"]["letters_layer_outbox_m2"] == pytest.approx(0.42)
    assert saved["product_composition_confirmed"]["letters_layer_outbox_m2"] == pytest.approx(
        0.42
    )
    assert is_acm_panel_only_composition(saved) is False
    assert is_letters_acm_composition_active(saved) is True

    modules = {"sablon_montaj", "structura_suport", "ambalare_livrare_montaj"}
    for rule in LETTERS_ACM_COMPOSITION_CONNECTION_RULES:
        assert _rule_applies(rule, modules, saved) is True


@pytest.mark.asyncio
async def test_confirm_letters_plus_support_creates_finish_bag_when_missing(db_session) -> None:
    """Composition confirm must persist applied_content even before Montaj seeds finish_setup."""
    workspace_id = str(uuid.uuid4())
    payload = {
        "product_binding": {"template_code": LETTERS},
        "product_composition_recommendation": {
            "composition_type": "letters_plus_support",
            "status": "needs_confirmation",
            "composition_items": _composition_items(),
        },
        "layer_role_setup": {
            "confirmation_status": "complete",
            "layers": [
                {
                    "layer_key": "letters",
                    "confirmed_role": "letters",
                    "confirmation_state": "confirmed",
                },
                {
                    "layer_key": "bond",
                    "confirmed_role": "support_panel",
                    "confirmation_state": "confirmed",
                },
            ],
        },
    }
    db_session.add(
        IntakeV6WorkspaceRecord(
            id=workspace_id,
            workspace_code=f"WS-LACM2-{workspace_id[:8]}",
            title="Letters+ACM missing finish bag",
            template_code=LETTERS,
            status="draft",
            payload_json=json.dumps(payload),
        )
    )
    await db_session.commit()

    await save_product_composition_confirmation_for_workspace(
        db_session,
        workspace_id,
        confirmed=True,
        items=_composition_items(),
        current_user=_user(),
    )
    saved = json.loads(
        (
            await db_session.execute(
                select(IntakeV6WorkspaceRecord.payload_json).where(
                    IntakeV6WorkspaceRecord.id == workspace_id
                )
            )
        ).scalar_one()
    )
    assert saved["finish_setup"]["applied_content"] == "letters"
    assert saved["product_composition_confirmed"]["applied_content"] == "letters"
    # Gate needs ACM mounting payload too — XOR field alone is what this test proves.
    assert not (saved.get("finish_setup") or {}).get("mounting_solution")


@pytest.mark.asyncio
async def test_confirm_support_only_still_persists_none(db_session) -> None:
    workspace_id = str(uuid.uuid4())
    payload = _letters_plus_acm_payload()
    payload["product_composition_recommendation"]["composition_type"] = "support_only"
    payload["product_composition_recommendation"]["composition_items"] = [
        {"template_code": ACM, "component_role": "support_panel"}
    ]
    db_session.add(
        IntakeV6WorkspaceRecord(
            id=workspace_id,
            workspace_code=f"WS-ACMO-{workspace_id[:8]}",
            title="ACM panel-alone persist regression",
            template_code=ACM,
            status="draft",
            payload_json=json.dumps(payload),
        )
    )
    await db_session.commit()

    await save_product_composition_confirmation_for_workspace(
        db_session,
        workspace_id,
        confirmed=True,
        items=[{"template_code": ACM, "component_role": "support_panel"}],
        current_user=_user(),
    )

    saved = json.loads(
        (
            await db_session.execute(
                select(IntakeV6WorkspaceRecord.payload_json).where(
                    IntakeV6WorkspaceRecord.id == workspace_id
                )
            )
        ).scalar_one()
    )
    assert saved["finish_setup"]["applied_content"] == "none"
    assert saved["product_composition_confirmed"]["applied_content"] == "none"
    assert is_acm_panel_only_composition(saved) is True
    assert is_letters_acm_composition_active(saved) is False

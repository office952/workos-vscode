"""Read-only Form System contract backbone for owner-valid product roots."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from schemas.intake_v4 import IntakeV4LayerRoleSetup
from services.active_template_scope import is_owner_valid_active_template
from services.intake_v4_finish_truth_service import artwork_finish_runtime_boolean_state, mounting_scope_runtime_state
from services.intake_v4_layer_role_service import selected_layer_refs_runtime_state
from services.template_architecture_scope import (
    STRUCTURE_PREMOUNT_TEMPLATE_CODE,
    VOLUM_ALUMINUM_TEMPLATE_CODE,
    VOLUMETRIC_BACK_TEMPLATE_CODE,
    VOLUMETRIC_FACE_TEMPLATE_CODE,
    VOLUMETRIC_FINISH_TEMPLATE_CODE,
    VOLUMETRIC_LED_TEMPLATE_CODE,
    VOLUMETRIC_LOGO_BACK_TEMPLATE_CODE,
    VOLUMETRIC_LOGO_FACE_TEMPLATE_CODE,
    VOLUMETRIC_LOGO_FINISH_TEMPLATE_CODE,
    VOLUMETRIC_LOGO_LIGHTING_TEMPLATE_CODE,
    VOLUMETRIC_LOGO_MOUNTING_TEMPLATE_CODE,
    VOLUMETRIC_LOGO_RETURN_TEMPLATE_CODE,
    VOLUMETRIC_LOGO_TEMPLATE_CODE,
    VOLUMETRIC_V2_TEMPLATE_CODE,
)

CONTRACT_VERSION = "form_system_backbone_v1"
ALLOWED_ROOT_TYPE = "product_template"
ALLOWED_QUOTE_MODE = "product_total"
LEGACY_LETTERS_ALIAS = "TPL-VOLUMETRIC-LETTERS"

LOGO_LEGACY_COMPONENT_TEMPLATE_CODES = frozenset(
    {
        VOLUMETRIC_LOGO_FACE_TEMPLATE_CODE,
        VOLUMETRIC_LOGO_BACK_TEMPLATE_CODE,
        VOLUMETRIC_LOGO_RETURN_TEMPLATE_CODE,
        VOLUMETRIC_LOGO_FINISH_TEMPLATE_CODE,
        VOLUMETRIC_LOGO_MOUNTING_TEMPLATE_CODE,
    }
)
SHARED_COMPONENT_TEMPLATE_CODES = frozenset(
    {
        VOLUMETRIC_FACE_TEMPLATE_CODE,
        VOLUMETRIC_BACK_TEMPLATE_CODE,
        VOLUM_ALUMINUM_TEMPLATE_CODE,
        VOLUMETRIC_FINISH_TEMPLATE_CODE,
        STRUCTURE_PREMOUNT_TEMPLATE_CODE,
        VOLUMETRIC_LED_TEMPLATE_CODE,
    }
)
STRATEGY_PROFILE_ONLY_TEMPLATE_CODES = frozenset({VOLUMETRIC_LOGO_LIGHTING_TEMPLATE_CODE})


def _normalize_code(template_code: str | None) -> str:
    return str(template_code or "").strip().upper()


def _canonicalize_template_code(template_code: str | None) -> str:
    normalized = _normalize_code(template_code)
    if normalized in {LEGACY_LETTERS_ALIAS, VOLUMETRIC_V2_TEMPLATE_CODE.upper()}:
        return VOLUMETRIC_V2_TEMPLATE_CODE
    if normalized == VOLUMETRIC_LOGO_TEMPLATE_CODE.upper():
        return VOLUMETRIC_LOGO_TEMPLATE_CODE
    for code in SHARED_COMPONENT_TEMPLATE_CODES | LOGO_LEGACY_COMPONENT_TEMPLATE_CODES | STRATEGY_PROFILE_ONLY_TEMPLATE_CODES:
        if normalized == code.upper():
            return code
    return normalized


def _blocked_root(
    *,
    requested_code: str | None,
    canonical_code: str,
    root_type: str,
    quote_mode: str,
    blocker_code: str,
    reason: str,
) -> dict[str, Any]:
    blockers = [
        {
            "blocker_code": blocker_code,
            "severity": "blocked",
            "message": reason,
            "blocks": ["quote_preview", "priced_quote", "order_snapshot", "product_definition"],
        }
    ]
    return {
        "contract_version": CONTRACT_VERSION,
        "read_only": True,
        "root": {
            "requested_code": requested_code,
            "code": canonical_code,
            "canonical_code": canonical_code,
            "root_type": root_type,
            "quote_mode": quote_mode,
            "offerability_status": "blocked",
            "canonical_alias_resolution": canonical_code != str(requested_code or "").strip(),
            "allowed": False,
            "blocked": True,
            "blocker_code": blocker_code,
            "reason": reason,
        },
        "components": [],
        "fields": [],
        "readiness": {
            "status": "blocked",
            "blockers": blockers,
            "operator_confirmation_required": [],
            "suggestions_allowed": [],
            "fallback_or_hydrated_not_confirmed": [],
            "downstream_later": [],
        },
        "blockers": deepcopy(blockers),
        "downstream_write_intent": _downstream_write_intent(),
        "notes": ["Fail-closed Form System backbone response. No runtime writes were performed."],
    }


def _downstream_write_intent() -> dict[str, bool]:
    return {
        "pricing_write": False,
        "quote_write": False,
        "order_write": False,
        "product_definition_write": False,
        "product_aggregate_write": False,
        "task_graph_write": False,
        "execution_runtime_write": False,
        "inventory_movement": False,
        "db_write": False,
    }


COMPONENTS: list[dict[str, Any]] = [
    {
        "component_key": "svg_layer_roles",
        "label": "SVG / layer roles",
        "component_template_code": None,
        "module_code": "geometry_svg",
        "coverage": "covered",
        "role": "suggestion_source",
        "contract_reference": "Intake V6 SVG Analyzer / geometry_svg",
        "operations_contract_reference": "contract_only_non_priced_gate",
        "notes": "Analyzer suggests layer/group roles and geometry; operator confirmation is required.",
    },
    {
        "component_key": "face",
        "label": "Face",
        "component_template_code": VOLUMETRIC_FACE_TEMPLATE_CODE,
        "module_code": "debitare_fata",
        "coverage": "covered",
        "role": "front_visual_face",
        "contract_reference": "shared_volumetric_component_contracts.volumetric_face",
        "operations_contract_reference": "face.geometry_review / face.cut preview_only",
        "notes": "Owns face layer, material, thickness, area and face finish target requirements.",
    },
    {
        "component_key": "back",
        "label": "Back",
        "component_template_code": VOLUMETRIC_BACK_TEMPLATE_CODE,
        "module_code": "debitare_spate",
        "coverage": "partial",
        "role": "back_panel",
        "contract_reference": "shared_volumetric_component_contracts.volumetric_back",
        "operations_contract_reference": "back.cut preview_only",
        "notes": "Back material/mode exists in current contracts; explicit confirmation state remains partial.",
    },
    {
        "component_key": "return_cant",
        "label": "Return / cant",
        "component_template_code": VOLUM_ALUMINUM_TEMPLATE_CODE,
        "module_code": "modelare_cant",
        "coverage": "covered",
        "role": "return_side_wall",
        "contract_reference": "shared_volumetric_component_contracts.volumetric_return_side",
        "operations_contract_reference": "return.perimeter_review / return.form preview_only",
        "notes": "Owns return depth, material, perimeter basis and return finish requirements.",
    },
    {
        "component_key": "finish_artwork",
        "label": "Finish / artwork",
        "component_template_code": VOLUMETRIC_FINISH_TEMPLATE_CODE,
        "module_code": "finisaje",
        "coverage": "partial",
        "role": "surface_finish_and_artwork",
        "contract_reference": "shared_volumetric_component_contracts.volumetric_surface_finish",
        "operations_contract_reference": "finish.target_review / finish.apply_* preview_only",
        "notes": "Finish options exist, but finish target/stage and artwork confirmation remain partial.",
    },
    {
        "component_key": "lighting_led",
        "label": "Lighting / LED",
        "component_template_code": VOLUMETRIC_LED_TEMPLATE_CODE,
        "module_code": "sistem_led",
        "coverage": "partial",
        "role": "lighting_and_led",
        "contract_reference": "shared_volumetric_component_contracts.volumetric_lighting",
        "operations_contract_reference": "led.lighting_review / led.install preview_only",
        "notes": "Shared LED component is active for Letters; electrical strategy remains partial and no LED formula is invented here.",
    },
    {
        "component_key": "mounting_support",
        "label": "Mounting / support",
        "component_template_code": STRUCTURE_PREMOUNT_TEMPLATE_CODE,
        "module_code": "structura_suport",
        "coverage": "partial",
        "role": "mounting_support_structure",
        "contract_reference": "shared_volumetric_component_contracts.volumetric_mounting_interface",
        "operations_contract_reference": "mounting.method_select / structure.prepare preview_only",
        "notes": "Mounting exists; support trigger alignment remains a warning until a future scoped cleanup.",
    },
    {
        "component_key": "electrical",
        "label": "Electrical",
        "component_template_code": VOLUMETRIC_LED_TEMPLATE_CODE,
        "module_code": "sistem_led",
        "coverage": "partial",
        "role": "electrical_dependency",
        "contract_reference": "lighting_electrical reusable component contract",
        "operations_contract_reference": "led.wire / led.electrical_test preview_only",
        "notes": "Electrical truth is modeled as part of lighting/LED for this slice; detailed electrical component remains future.",
    },
    {
        "component_key": "production_operations_reference",
        "label": "Production operations reference",
        "component_template_code": None,
        "module_code": None,
        "coverage": "covered",
        "role": "contract_reference_only",
        "contract_reference": "PRODUCT_SYSTEM_COMPONENT_PRODUCTION_OPERATIONS_CONTRACT.md",
        "operations_contract_reference": "contract_only_no_materialization",
        "notes": "References component-owned operation contracts only; no task graph, execution plan, or materialization intent.",
    },
]


FIELDS: list[dict[str, Any]] = [
    {
        "field_key": "svg.layer_group_role",
        "operator_label": "Rol strat/grup SVG",
        "owning_component": "svg_layer_roles",
        "component_template_code": None,
        "source_type": "svg_suggested",
        "state": "suggested",
        "product_truth_path": "svg.layer_roles[].suggested_role",
        "required_for": ["quote_preview", "priced_quote", "order_snapshot", "product_definition", "execution_later"],
        "blocker_code": "LAYER_ROLES_INCOMPLETE",
        "notes": "Suggestion only. Operator confirmation must create the confirmed role map.",
        "requires_operator_confirmation": True,
    },
    {
        "field_key": "svg.selected_layer_group",
        "operator_label": "Layer/grup selectat",
        "owning_component": "svg_layer_roles",
        "component_template_code": None,
        "source_type": "operator_confirmed",
        "state": "missing",
        "product_truth_path": "svg.selected_layer_refs[]",
        "required_for": ["quote_preview", "priced_quote", "order_snapshot", "product_definition", "execution_later"],
        "blocker_code": "SELECTED_FACE_LAYER_MISSING",
        "notes": "Explicit selected/confirmed layer refs are required before quote-safe truth.",
        "requires_operator_confirmation": True,
    },
    {
        "field_key": "face.material",
        "operator_label": "Material față",
        "owning_component": "face",
        "component_template_code": VOLUMETRIC_FACE_TEMPLATE_CODE,
        "source_type": "manual_input",
        "state": "missing",
        "product_truth_path": "components.face.material",
        "required_for": ["quote_preview", "priced_quote", "order_snapshot", "product_definition", "execution_later"],
        "blocker_code": "FACE_MATERIAL_MISSING",
        "notes": "SVG cannot decide face material; Form System asks and operator confirms.",
    },
    {
        "field_key": "face.finish_artwork_target",
        "operator_label": "Țintă finisaj/artwork față",
        "owning_component": "finish_artwork",
        "component_template_code": VOLUMETRIC_FINISH_TEMPLATE_CODE,
        "source_type": "operator_confirmed",
        "state": "missing",
        "product_truth_path": "components.finish.target",
        "required_for": ["quote_preview", "priced_quote", "order_snapshot", "product_definition", "execution_later"],
        "blocker_code": "FACE_FINISH_TARGET_MISSING",
        "notes": "Separates face, return/cant, and artwork finish targets.",
    },
    {
        "field_key": "finish.print_required",
        "operator_label": "Print artwork necesar",
        "owning_component": "finish_artwork",
        "component_template_code": VOLUMETRIC_FINISH_TEMPLATE_CODE,
        "source_type": "payload_artwork_rows",
        "state": "blocked",
        "product_truth_path": "components.artwork.items[].printRequired",
        "required_for": ["quote_preview", "priced_quote", "order_snapshot", "product_definition", "execution_later"],
        "blocker_code": "PRINT_REQUIRED_UNKNOWN",
        "notes": "Artwork print requirement must be captured explicitly per artwork finish row; no global aggregation is canonical truth.",
        "requires_operator_confirmation": True,
    },
    {
        "field_key": "finish.lamination_required",
        "operator_label": "Laminare artwork necesară",
        "owning_component": "finish_artwork",
        "component_template_code": VOLUMETRIC_FINISH_TEMPLATE_CODE,
        "source_type": "payload_artwork_rows",
        "state": "blocked",
        "product_truth_path": "components.artwork.items[].laminationRequired",
        "required_for": ["quote_preview", "priced_quote", "order_snapshot", "product_definition", "execution_later"],
        "blocker_code": "LAMINATION_REQUIRED_UNKNOWN",
        "notes": "Artwork lamination requirement must be captured explicitly per artwork finish row; no global aggregation is canonical truth.",
        "requires_operator_confirmation": True,
    },
    {
        "field_key": "return.material",
        "operator_label": "Material cant/return",
        "owning_component": "return_cant",
        "component_template_code": VOLUM_ALUMINUM_TEMPLATE_CODE,
        "source_type": "manual_input",
        "state": "missing",
        "product_truth_path": "components.return.material",
        "required_for": ["quote_preview", "priced_quote", "order_snapshot", "product_definition", "execution_later"],
        "blocker_code": "RETURN_CANT_MATERIAL_MISSING",
        "notes": "Current contracts expose return profile families; final material remains operator/form truth.",
    },
    {
        "field_key": "return.depth_mm",
        "operator_label": "Adâncime cant",
        "owning_component": "return_cant",
        "component_template_code": VOLUM_ALUMINUM_TEMPLATE_CODE,
        "source_type": "hydrated",
        "state": "hydrated",
        "product_truth_path": "components.return.depth_mm",
        "required_for": ["quote_preview", "priced_quote", "order_snapshot", "product_definition", "execution_later"],
        "blocker_code": "RETURN_CANT_HEIGHT_CONFIRMATION_REQUIRED",
        "notes": "A hydrated/default depth such as 60 mm does not count as confirmed until operator acceptance.",
        "requires_operator_confirmation": True,
    },
    {
        "field_key": "lighting.type",
        "operator_label": "Tip iluminare",
        "owning_component": "lighting_led",
        "component_template_code": VOLUMETRIC_LED_TEMPLATE_CODE,
        "source_type": "fallback",
        "state": "fallback",
        "product_truth_path": "components.lighting.illumination_type",
        "required_for": ["quote_preview", "priced_quote", "order_snapshot", "product_definition", "execution_later"],
        "blocker_code": "LIGHTING_MODE_CONFIRMATION_REQUIRED",
        "notes": "Fallback/hydrated lighting defaults do not unlock quote by themselves.",
        "requires_operator_confirmation": True,
    },
    {
        "field_key": "lighting.led_profile",
        "operator_label": "Profil LED / sursă strategie",
        "owning_component": "lighting_led",
        "component_template_code": VOLUMETRIC_LED_TEMPLATE_CODE,
        "source_type": "contract_default",
        "state": "warning",
        "product_truth_path": "components.lighting.strategy_profile",
        "required_for": ["product_definition", "execution_later"],
        "blocker_code": None,
        "notes": "Letters LED strategy is contract-level direction; detailed formula remains future and not pricing truth.",
    },
    {
        "field_key": "mounting.support_option",
        "operator_label": "Opțiune montaj/suport",
        "owning_component": "mounting_support",
        "component_template_code": STRUCTURE_PREMOUNT_TEMPLATE_CODE,
        "source_type": "hydrated",
        "state": "hydrated",
        "product_truth_path": "components.mounting.system",
        "required_for": ["quote_preview", "priced_quote", "order_snapshot", "product_definition", "execution_later"],
        "blocker_code": "MOUNTING_SYSTEM_CONFIRMATION_REQUIRED",
        "notes": "Hydrated mounting system must be confirmed; support trigger mismatch remains a warning.",
        "requires_operator_confirmation": True,
    },
    {
        "field_key": "mounting.mounting_scope",
        "operator_label": "Scope comercial montaj",
        "owning_component": "mounting_support",
        "component_template_code": STRUCTURE_PREMOUNT_TEMPLATE_CODE,
        "source_type": "operator_confirmed",
        "state": "missing",
        "product_truth_path": "components.mounting.mountingScope",
        "required_for": ["quote_preview", "priced_quote", "order_snapshot", "product_definition", "execution_later"],
        "blocker_code": "MOUNTING_SCOPE_MISSING",
        "notes": "Commercial mounting scope must be captured explicitly from operator finish setup; mounting_system and support_type are separate fields.",
        "requires_operator_confirmation": True,
    },
    {
        "field_key": "readiness.product_truth_blockers",
        "operator_label": "Blockere Product Truth",
        "owning_component": "readiness",
        "component_template_code": None,
        "source_type": "blocked",
        "state": "blocked",
        "product_truth_path": "readiness.blockers[]",
        "required_for": ["quote_preview", "priced_quote", "order_snapshot", "product_definition", "execution_later"],
        "blocker_code": "PRODUCT_TRUTH_INCOMPLETE",
        "notes": "Readiness summarizes missing required truth. It is not a pricing or execution write intent.",
    },
]


def _root_blocker_for(canonical_code: str, root_type: str, quote_mode: str) -> tuple[str, str] | None:
    if root_type != ALLOWED_ROOT_TYPE:
        return "ROOT_TYPE_BLOCKED", "Only product_template root is enabled for this Form System backbone slice."
    if quote_mode != ALLOWED_QUOTE_MODE:
        return "QUOTE_MODE_BLOCKED", "Only product_total quote mode is enabled; component_only remains owner-gated."
    normalized = _normalize_code(canonical_code)
    if normalized == VOLUMETRIC_LOGO_TEMPLATE_CODE.upper():
        return "LOGO_NOT_OFFERABLE", "TPL-VOLUMETRIC-LOGO_v1 remains candidate-only and is not Work Intake offerable."
    if normalized in {_normalize_code(code) for code in LOGO_LEGACY_COMPONENT_TEMPLATE_CODES}:
        return "LEGACY_LOGO_COMPONENT_BLOCKED", "Legacy Logo component templates are hidden/deprecated and cannot own active fields."
    if normalized in {_normalize_code(code) for code in SHARED_COMPONENT_TEMPLATE_CODES}:
        return "COMPONENT_ROOT_BLOCKED", "Shared Component Templates are not Work Intake roots and component quote is disabled."
    if normalized in {_normalize_code(code) for code in STRATEGY_PROFILE_ONLY_TEMPLATE_CODES}:
        return "STRATEGY_PROFILE_ROOT_BLOCKED", "Strategy/profile sources are not primary components or Work Intake roots."
    if not is_owner_valid_active_template(canonical_code):
        return "UNKNOWN_TEMPLATE_BLOCKED", "Unknown template code is not owner-valid for this Form System backbone."
    if canonical_code != VOLUMETRIC_V2_TEMPLATE_CODE:
        return "ROOT_NOT_OWNER_VALID", "Only TPL-VOLUMETRIC-LETTERS_v2 is enabled as the owner-valid root."
    return None


def _field_blocks_readiness(field: dict[str, Any]) -> bool:
    return bool(field.get("blocker_code")) and field.get("state") not in {"confirmed", "ready"}


def _build_readiness(fields: list[dict[str, Any]]) -> dict[str, Any]:
    blockers = [
        {
            "field_key": field["field_key"],
            "owning_component": field["owning_component"],
            "blocker_code": field["blocker_code"],
            "state": field["state"],
            "blocks": field["required_for"],
            "message": field["notes"],
        }
        for field in fields
        if _field_blocks_readiness(field)
    ]
    return {
        "status": "blocked" if blockers else "ready",
        "blockers": blockers,
        "operator_confirmation_required": [
            field["field_key"]
            for field in fields
            if field.get("requires_operator_confirmation") is True
        ],
        "suggestions_allowed": [
            field["field_key"]
            for field in fields
            if field.get("source_type") == "svg_suggested"
        ],
        "fallback_or_hydrated_not_confirmed": [
            field["field_key"]
            for field in fields
            if field.get("state") in {"fallback", "hydrated"}
        ],
        "downstream_later": ["product_aggregate", "task_graph", "owner_gated_execution_later", "shop_floor", "employee_mobile"],
    }


def _overlay_runtime_selected_layer_field(
    fields: list[dict[str, Any]],
    payload_raw: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    if not isinstance(payload_raw, dict):
        return fields
    setup_raw = payload_raw.get("layer_role_setup")
    setup = IntakeV4LayerRoleSetup.model_validate(setup_raw) if isinstance(setup_raw, dict) else None
    runtime = selected_layer_refs_runtime_state(setup)
    persisted_svg = payload_raw.get("svg") if isinstance(payload_raw.get("svg"), dict) else {}
    persisted_refs = persisted_svg.get("selected_layer_refs") if isinstance(persisted_svg.get("selected_layer_refs"), list) else []

    for field in fields:
        if field.get("field_key") != "svg.selected_layer_group":
            continue
        if runtime["status"] == "confirmed" and persisted_refs:
            field.update(
                {
                    "source_type": "payload_persisted",
                    "state": "confirmed",
                    "blocker_code": None,
                    "notes": "Persisted selected layer refs captured from confirmed layer_role_setup are available as runtime truth.",
                }
            )
            return fields
        blocker_code = runtime["blocker_code"] or "SELECTED_LAYER_REFS_MISSING"
        field.update(
            {
                "source_type": "operator_confirmed",
                "state": "blocked" if blocker_code != "SELECTED_LAYER_REFS_MISSING" else "missing",
                "blocker_code": blocker_code,
                "notes": "Selected layer refs runtime field is missing, unconfirmed, or ambiguous until confirmed layer refs are persisted.",
            }
        )
        return fields
    return fields


def _overlay_runtime_finish_target_field(
    fields: list[dict[str, Any]],
    payload_raw: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    if not isinstance(payload_raw, dict):
        return fields
    finish = payload_raw.get("finish_setup") if isinstance(payload_raw.get("finish_setup"), dict) else None
    if finish is None:
        return fields
    finish_target = str(finish.get("finish_target") or "").strip()
    finish_confirmed = finish.get("confirmed") is True

    for field in fields:
        if field.get("field_key") != "face.finish_artwork_target":
            continue
        if finish_target and finish_confirmed:
            field.update(
                {
                    "source_type": "payload_persisted",
                    "state": "confirmed",
                    "blocker_code": None,
                    "notes": "Persisted finish_setup.finish_target captured from confirmed operator finish setup is available as runtime truth.",
                }
            )
        return fields
    return fields


def _overlay_runtime_artwork_finish_boolean_fields(
    fields: list[dict[str, Any]],
    payload_raw: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    if not isinstance(payload_raw, dict):
        return fields
    finish_setup = payload_raw.get("finish_setup") if isinstance(payload_raw.get("finish_setup"), dict) else None
    if finish_setup is None:
        return fields

    runtime_by_key = {
        "finish.print_required": artwork_finish_runtime_boolean_state(finish_setup, "print_required"),
        "finish.lamination_required": artwork_finish_runtime_boolean_state(finish_setup, "lamination_required"),
    }
    for field in fields:
        runtime = runtime_by_key.get(field.get("field_key"))
        if runtime is None:
            continue
        if runtime["status"] == "confirmed":
            field.update(
                {
                    "source_type": "payload_persisted",
                    "state": "confirmed",
                    "blocker_code": None,
                    "notes": f"Persisted {runtime['source_path']} values are present on all artwork finish rows and anchored by finish or row confirmation.",
                }
            )
            continue
        field.update(
            {
                "source_type": "payload_artwork_rows",
                "state": "blocked",
                "blocker_code": runtime["blocker_code"],
                "notes": f"{runtime['source_path']} remains blocked until every persisted artwork finish row carries an explicit value and confirmation.",
            }
        )
    return fields


def _overlay_runtime_mounting_scope_field(
    fields: list[dict[str, Any]],
    payload_raw: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    if not isinstance(payload_raw, dict):
        return fields
    finish_setup = payload_raw.get("finish_setup") if isinstance(payload_raw.get("finish_setup"), dict) else None
    runtime = mounting_scope_runtime_state(finish_setup)

    for field in fields:
        if field.get("field_key") != "mounting.mounting_scope":
            continue
        if runtime["status"] == "confirmed":
            field.update(
                {
                    "source_type": "payload_persisted",
                    "state": "confirmed",
                    "blocker_code": None,
                    "notes": "Persisted finish_setup.mounting_scope captured from confirmed operator finish setup is available as runtime truth.",
                }
            )
            return fields
        field.update(
            {
                "source_type": "operator_confirmed",
                "state": "missing" if runtime["status"] == "missing" else "blocked",
                "blocker_code": "MOUNTING_SCOPE_MISSING",
                "notes": "Mounting scope remains blocked until finish_setup.mounting_scope is explicitly persisted and confirmed. No fallback from mounting_system or support_type is allowed.",
            }
        )
        return fields
    return fields


def _linked_template_composition() -> dict[str, Any]:
    return {
        "contract_version": "linked_template_composition_v1",
        "read_only": True,
        "root_template_code": VOLUMETRIC_V2_TEMPLATE_CODE,
        "root_role": "root_product",
        "composition_mode": "root_with_linked_segments",
        "linked_templates": [
            {
                "template_code": VOLUMETRIC_LOGO_TEMPLATE_CODE,
                "composition_role": "linked_logo_segment",
                "binding_status": "suggested",
                "activation_state": "child_only_not_root_offerable",
                "source": "svg_layer_binding",
                "segment_discovery": {
                    "status": "runtime_payload_required",
                    "runtime_sources": [
                        "payload.layer_role_setup.layer_bindings",
                        "payload.finish_setup.artwork_finishes",
                    ],
                    "expected_layer_role": "printed_artwork",
                    "notes": "The backbone service has no workspace runtime payload. Segment keys such as logo-stanga or logo-dreapta must come from the Intake V6 workspace payload.",
                },
                "segments": [],
                "product_truth_path": "linked_templates.logo",
                "quote_policy": "no_separate_quote",
                "root_offerability_policy": "blocked_as_root_in_this_flow",
                "component_quote_policy": "blocked",
                "task_merge_policy": "emit_intents_merge_later_no_task_runtime_now",
            }
        ],
        "no_duplicate_task_policy": {
            "status": "declared_only",
            "task_graph_implemented": False,
            "rule": "Linked templates may contribute future task intents; duplicate real operations must be merged later under an owner-approved task composer.",
        },
        "forbidden_runtime_effects": [
            "no_pricing_change",
            "no_quote_or_order_change",
            "no_execution_runtime_change",
            "no_product_aggregate_change",
            "no_db_write",
            "no_seed_or_migration",
        ],
    }


def build_form_system_contract_map(
    template_code: str,
    *,
    root_type: str = ALLOWED_ROOT_TYPE,
    quote_mode: str = ALLOWED_QUOTE_MODE,
    payload_raw: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a deterministic read-only contract map for the current owner-valid root."""
    canonical_code = _canonicalize_template_code(template_code)
    root_blocker = _root_blocker_for(canonical_code, root_type, quote_mode)
    if root_blocker is not None:
        blocker_code, reason = root_blocker
        return _blocked_root(
            requested_code=template_code,
            canonical_code=canonical_code,
            root_type=root_type,
            quote_mode=quote_mode,
            blocker_code=blocker_code,
            reason=reason,
        )

    fields = _overlay_runtime_finish_target_field(
        _overlay_runtime_mounting_scope_field(
            _overlay_runtime_artwork_finish_boolean_fields(
                _overlay_runtime_selected_layer_field(deepcopy(FIELDS), payload_raw),
                payload_raw,
            ),
            payload_raw,
        ),
        payload_raw,
    )
    readiness = _build_readiness(fields)
    return {
        "contract_version": CONTRACT_VERSION,
        "read_only": True,
        "root": {
            "requested_code": template_code,
            "code": VOLUMETRIC_V2_TEMPLATE_CODE,
            "canonical_code": VOLUMETRIC_V2_TEMPLATE_CODE,
            "root_type": ALLOWED_ROOT_TYPE,
            "quote_mode": ALLOWED_QUOTE_MODE,
            "offerability_status": "allowed_owner_valid_root",
            "canonical_alias_resolution": _normalize_code(template_code) != VOLUMETRIC_V2_TEMPLATE_CODE.upper(),
            "allowed": True,
            "blocked": False,
            "blocker_code": None,
            "reason": "Owner-valid product template root for read-only Form System backbone.",
        },
        "components": deepcopy(COMPONENTS),
        "fields": fields,
        "readiness": readiness,
        "blockers": deepcopy(readiness["blockers"]),
        "linked_template_composition": _linked_template_composition(),
        "downstream_write_intent": _downstream_write_intent(),
        "notes": [
            "Read-only contract map. It does not create Product Truth, quote, order, execution, tasks, inventory movements, or DB writes.",
            "SVG suggested values, fallback values, and hydrated values remain distinct from confirmed operator truth.",
            "ProductDefinition may be listed in required_for only as a consumer boundary; no ProductDefinition write behavior is invoked.",
        ],
    }


def get_form_system_backbone_for_product_template(template_code: str) -> dict[str, Any]:
    """Compatibility alias for callers that prefer product-template wording."""
    return build_form_system_contract_map(template_code)
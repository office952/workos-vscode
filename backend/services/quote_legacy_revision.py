"""On-demand legacy revision source reconstruction — no DB migrations, no CostEngine."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from sqlalchemy.ext.asyncio import AsyncSession

from models.product_templates import Product_templates
from services.company_commercial_settings_service import DEFAULT_VAT_PCT


def _legacy_quote_vat_pct(quote_obj: Any) -> float:
    raw = getattr(quote_obj, "vat", None)
    if raw is None:
        return float(DEFAULT_VAT_PCT)
    return float(raw)


@dataclass
class LegacyRevisionSourceResult:
    ok: bool
    source: Optional[Dict[str, Any]] = None
    missing_fields: List[str] = field(default_factory=list)
    message: str = ""
    legacy_reconstructed: bool = False


def _is_canonical_snapshot(obj: Any) -> bool:
    if not isinstance(obj, dict) or isinstance(obj, list):
        return False
    return "product_definition" in obj and (
        "cost_result" in obj or "pricing" in obj or "price" in obj
    )


def extract_snapshot_from_line_items(raw: Optional[str]) -> Optional[Dict[str, Any]]:
    """Return canonical QuoteCalculationSnapshot dict from persisted line_items."""
    if not raw or not str(raw).strip():
        return None
    try:
        parsed = json.loads(raw)
    except Exception:
        return None

    if isinstance(parsed, list):
        return None

    if not isinstance(parsed, dict):
        return None

    if parsed.get("revision_source") and isinstance(parsed["revision_source"], dict):
        return None

    if _is_canonical_snapshot(parsed):
        return parsed

    inner = parsed.get("line_items")
    if _is_canonical_snapshot(inner):
        return inner

    return None


def extract_revision_source_from_line_items(raw: Optional[str]) -> Optional[Dict[str, Any]]:
    if not raw or not str(raw).strip():
        return None
    try:
        parsed = json.loads(raw)
    except Exception:
        return None
    if not isinstance(parsed, dict):
        return None
    src = parsed.get("revision_source")
    return src if isinstance(src, dict) else None


def _extract_linkage_from_notes(raw: Optional[str]) -> Optional[Dict[str, Any]]:
    if not raw or not str(raw).strip():
        return None
    try:
        parsed = json.loads(raw)
    except Exception:
        return None
    if not isinstance(parsed, dict):
        return None

    for key in ("intake_v6_linkage_v1", "intake_v4_linkage_v1"):
        linkage = parsed.get(key)
        if isinstance(linkage, dict):
            return linkage
    return None


def _parse_json_field(raw: Any) -> Any:
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except Exception:
            return raw
    return raw


def _linked_vector_file(workspace_payload: Dict[str, Any] | None) -> str | None:
    if not isinstance(workspace_payload, dict):
        return None
    svg_source = workspace_payload.get("svg_source")
    if not isinstance(svg_source, dict):
        return None
    for key in ("file_name", "file_hash", "upload_status"):
        value = svg_source.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _infer_vector_file_type(filename: str | None) -> str | None:
    if not isinstance(filename, str):
        return None
    text = filename.strip().lower()
    if not text or "." not in text:
        return None
    ext = text.rsplit(".", 1)[-1]
    if ext in {"svg", "dxf", "dwg"}:
        return ext
    return "other"


def _linked_product_spec(
    workspace_payload: Dict[str, Any] | None,
    quote_input: Dict[str, Any] | None,
) -> Dict[str, Any] | None:
    if not isinstance(workspace_payload, dict):
        return None

    svg_source = workspace_payload.get("svg_source")
    if not isinstance(svg_source, dict):
        return None

    vector_file_name = svg_source.get("file_name")
    vector_file_type = _infer_vector_file_type(vector_file_name)
    upload_status = str(svg_source.get("upload_status") or "").strip().lower()
    has_analysis = isinstance(workspace_payload.get("svg_analysis_json"), dict)

    product_spec: Dict[str, Any] = {
        "vector_file_present": True,
        "vector_file_name": vector_file_name,
    }
    if vector_file_type:
        product_spec["vector_file_type"] = vector_file_type
    if has_analysis or upload_status == "analyzed":
        product_spec["vector_analysis_status"] = "analyzed"
    elif upload_status:
        product_spec["vector_analysis_status"] = "attached_unanalyzed"

    if isinstance(quote_input, dict):
        for key in ("letter_face_area_m2", "letter_perimeter_m"):
            value = quote_input.get(key)
            if value is not None:
                product_spec[key] = value

    return product_spec


def collect_template_quote_input_keys(product_template: Dict[str, Any]) -> Set[str]:
    """Return union of requires_quote_input keys declared on the template."""
    keys: Set[str] = set()
    for field_name in ("components_json", "operations_json", "required_materials_json"):
        payload = _parse_json_field(product_template.get(field_name))
        entries: List[Any] = []
        if isinstance(payload, list):
            entries = payload
        elif isinstance(payload, dict):
            entries = list(payload.values())

        for entry in entries:
            if not isinstance(entry, dict):
                continue
            req = entry.get("requires_quote_input")
            if isinstance(req, list):
                keys.update(str(k) for k in req if k)
            materials = entry.get("materials")
            if isinstance(materials, list):
                for mat in materials:
                    if isinstance(mat, dict):
                        mreq = mat.get("requires_quote_input")
                        if isinstance(mreq, list):
                            keys.update(str(k) for k in mreq if k)
    return keys


def template_dict_from_row(tpl: Product_templates) -> Dict[str, Any]:
    return {
        "id": tpl.id,
        "template_code": tpl.template_code,
        "family_id": tpl.family_id,
        "family_name": tpl.family_name,
        "description": tpl.description,
        "components_json": tpl.components_json,
        "operations_json": tpl.operations_json,
        "required_materials_json": tpl.required_materials_json,
        "estimated_hours": tpl.estimated_hours,
        "base_labor_rate": tpl.base_labor_rate,
        "base_margin_pct": tpl.base_margin_pct,
        "active": bool(tpl.active),
    }


def _mark_svg_readiness_non_priced(product_template: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(product_template)
    components = _parse_json_field(normalized.get("components_json"))
    if not isinstance(components, list):
        return normalized

    changed = False
    patched_components: List[Dict[str, Any]] = []
    for component in components:
        if not isinstance(component, dict):
            patched_components.append(component)
            continue
        operations = component.get("operations")
        if not isinstance(operations, list):
            patched_components.append(component)
            continue

        patched_operations: List[Any] = []
        component_changed = False
        for operation in operations:
            if not isinstance(operation, dict) or operation.get("code") != "svg_geometry_analysis":
                patched_operations.append(operation)
                continue
            patched_operation = dict(operation)
            patched_operation["quote_priced"] = False
            patched_operations.append(patched_operation)
            component_changed = True

        if component_changed:
            patched_component = dict(component)
            patched_component["operations"] = patched_operations
            patched_components.append(patched_component)
            changed = True
        else:
            patched_components.append(component)

    if changed:
        normalized["components_json"] = patched_components
    return normalized


def build_legacy_revision_source_from_snapshot(
    *,
    snapshot: Dict[str, Any],
    product_template: Dict[str, Any],
    margin_pct: float,
    discount_pct: float,
    vat_pct: float,
) -> LegacyRevisionSourceResult:
    """Sync reconstruction when template dict is already available."""
    missing: List[str] = []

    required_qi = collect_template_quote_input_keys(product_template)
    if required_qi:
        missing.append("quote_input")
        return LegacyRevisionSourceResult(
            ok=False,
            missing_fields=missing,
            message=(
                "Oferta folosește un șablon cu intrări formula (quote_input) care nu sunt "
                "salvate pe ofertele legacy. Creează o ofertă nouă din cerere / QuoteWizard."
            ),
        )

    pd = snapshot.get("product_definition")
    if not isinstance(pd, dict):
        missing.append("product_definition")
        return LegacyRevisionSourceResult(
            ok=False,
            missing_fields=missing,
            message="Snapshot-ul ofertei nu conține product_definition.",
        )

    quantity = pd.get("quantity")
    dimensions = pd.get("dimensions") if isinstance(pd.get("dimensions"), dict) else {}
    if not quantity:
        missing.append("product_definition.quantity")
    if not dimensions.get("width_mm"):
        missing.append("product_definition.dimensions.width_mm")
    if not dimensions.get("height_mm"):
        missing.append("product_definition.dimensions.height_mm")

    if missing:
        return LegacyRevisionSourceResult(
            ok=False,
            missing_fields=missing,
            message=(
                "Snapshot-ul legacy nu conține datele de configurare necesare pentru recalcul sigur."
            ),
        )

    pricing_snapshot = snapshot.get("pricing") if isinstance(snapshot.get("pricing"), dict) else {}
    user_config: Dict[str, Any] = {
        "quantity": int(quantity),
        "dimensions": {
            "width_mm": float(dimensions.get("width_mm")),
            "height_mm": float(dimensions.get("height_mm")),
            "depth_mm": float(dimensions.get("depth_mm") or 0),
        },
    }
    product_id = pd.get("product_id") or product_template.get("template_code")
    if product_id:
        user_config["product_id"] = str(product_id)

    source: Dict[str, Any] = {
        "product_template": product_template,
        "user_config": user_config,
        "quote_input": None,
        "pricing": {
            "margin_pct": float(pricing_snapshot.get("margin_pct", margin_pct)),
            "discount_pct": float(pricing_snapshot.get("discount_pct", discount_pct)),
            "vat_pct": float(pricing_snapshot.get("vat_pct", vat_pct)),
        },
        "legacy_reconstructed": True,
    }
    return LegacyRevisionSourceResult(
        ok=True,
        source=source,
        legacy_reconstructed=True,
        message="Sursă legacy reconstruită din snapshot + șablon.",
    )


async def build_legacy_revision_source_from_quote(
    db: AsyncSession,
    quote_obj: Any,
) -> LegacyRevisionSourceResult:
    """Attempt on-demand legacy revision source reconstruction for a quote row."""
    existing = extract_revision_source_from_line_items(getattr(quote_obj, "line_items", None))
    if existing:
        return LegacyRevisionSourceResult(ok=True, source=existing, legacy_reconstructed=False)

    snapshot = extract_snapshot_from_line_items(getattr(quote_obj, "line_items", None))
    if snapshot is None:
        linkage = _extract_linkage_from_notes(getattr(quote_obj, "notes", None))
        if isinstance(linkage, dict):
            quote_input = linkage.get("quote_input_payload")
            snapshot = linkage.get("snapshot")
            workspace_payload = snapshot.get("workspace_payload_snapshot") if isinstance(snapshot, dict) else None
            product_binding = workspace_payload.get("product_binding") if isinstance(workspace_payload, dict) else None
            template_id = None
            template_code = None
            if isinstance(product_binding, dict):
                template_id = product_binding.get("template_id")
                template_code = product_binding.get("template_code")

            try:
                quantity = 1
                parsed_line_items = json.loads(getattr(quote_obj, "line_items", "") or "[]")
                if isinstance(parsed_line_items, list) and parsed_line_items:
                    quantity = int(parsed_line_items[0].get("quantity") or 1)
            except Exception:
                quantity = 1

            if isinstance(quote_input, dict):
                try:
                    from services.product_templates import Product_templatesService

                    tpl_service = Product_templatesService(db)
                    tpl = None
                    if template_id is not None:
                        try:
                            tpl = await tpl_service.get_by_id(int(template_id))
                        except (TypeError, ValueError):
                            tpl = None
                    if tpl is None and template_code:
                        tpl = await tpl_service.get_by_field("template_code", str(template_code))

                    if tpl is not None:
                        if not quote_input.get("vector_file"):
                            vector_file = _linked_vector_file(workspace_payload)
                            if vector_file:
                                quote_input = dict(quote_input)
                                quote_input["vector_file"] = vector_file
                        dimensions = {
                            "width_mm": float(quote_input.get("width_mm") or 0),
                            "height_mm": float(quote_input.get("height_mm") or 0),
                            "depth_mm": float(
                                quote_input.get("depth_mm")
                                or quote_input.get("return_depth_mm")
                                or 0
                            ),
                        }
                        source: Dict[str, Any] = {
                            "product_template": _mark_svg_readiness_non_priced(template_dict_from_row(tpl)),
                            "user_config": {
                                "quantity": max(int(quantity), 1),
                                "dimensions": dimensions,
                                "product_id": str(getattr(tpl, "template_code", "") or ""),
                            },
                            "quote_input": quote_input,
                            "product_spec_json": _linked_product_spec(workspace_payload, quote_input),
                            "pricing": {
                                "margin_pct": float(
                                    getattr(quote_obj, "margin_pct", 0) or getattr(tpl, "base_margin_pct", 0) or 0
                                ),
                                "discount_pct": float(getattr(quote_obj, "discount_pct", 0) or 0),
                                "vat_pct": _legacy_quote_vat_pct(quote_obj),
                            },
                            "legacy_reconstructed": True,
                        }
                        return LegacyRevisionSourceResult(
                            ok=True,
                            source=source,
                            legacy_reconstructed=True,
                            message="Sursă legacy reconstruită din linkage notes + șablon.",
                        )
                except Exception:
                    pass

        return LegacyRevisionSourceResult(
            ok=False,
            missing_fields=["revision_source", "canonical_snapshot"],
            message=(
                "Această ofertă a fost creată înainte de suportul pentru revizii și nu conține "
                "datele necesare pentru recalcul sigur."
            ),
        )

    template_id = snapshot.get("template_id")
    if template_id is None:
        return LegacyRevisionSourceResult(
            ok=False,
            missing_fields=["template_id"],
            message="Snapshot-ul legacy nu conține template_id — recalculul nu este sigur.",
        )

    try:
        template_id_int = int(template_id)
    except (TypeError, ValueError):
        return LegacyRevisionSourceResult(
            ok=False,
            missing_fields=["template_id"],
            message="template_id invalid în snapshot-ul legacy.",
        )

    from services.product_templates import Product_templatesService

    tpl = await Product_templatesService(db).get_by_id(template_id_int)
    if tpl is None:
        return LegacyRevisionSourceResult(
            ok=False,
            missing_fields=["product_template"],
            message=f"Șablonul #{template_id_int} nu mai există — recalcul legacy imposibil.",
        )

    return build_legacy_revision_source_from_snapshot(
        snapshot=snapshot,
        product_template=template_dict_from_row(tpl),
        margin_pct=float(getattr(quote_obj, "margin_pct", 0) or 0),
        discount_pct=float(getattr(quote_obj, "discount_pct", 0) or 0),
        vat_pct=_legacy_quote_vat_pct(quote_obj),
    )

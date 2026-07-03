"""Shape validation for intake_requests.product_spec_json (capture only)."""

from __future__ import annotations

from typing import Any, Dict, Optional

from services.svg_manual_layer_mapping import normalize_svg_layer_mappings

ALLOWED_KEYS = frozenset({
    "text",
    "font",
    "width_mm",
    "height_mm",
    "letter_height_mm",
    "depth_mm",
    "return_depth_mm",
    "letter_face_area_m2",
    "letter_perimeter_m",
    "letter_count",
    "illumination_type",
    "face_finish",
    "face_finish_type",
    "face_vinyl_color_code",
    "face_vinyl_color_name",
    "face_vinyl_roll_width_mm",
    "face_vinyl_finish",
    "face_vinyl_notes",
    "volume_finish",
    "ral_color",
    "paint_ral_code",
    "paint_ral_name",
    "paint_finish",
    "paint_tube_count",
    "selected_psu_watts",
    "lighting_notes",
    "indoor_outdoor",
    "mounting_type",
    "premounting_type",
    "premount_bar_material",
    "mounting_system",
    "mounting_template_enabled",
    "mounting_template_area_m2",
    "mounting_template_material_type",
    "mounting_bar_profile",
    "mounting_bar_count",
    "mounting_bar_length_m",
    "mounting_notes",
    "backing_chamfer",
    "back_bevel_enabled",
    "face_miter_chamfer",
    "visual_chamfer_included",
    "illumination_family",
    "face_vinyl_enabled",
    "face_wrap_enabled",
    "return_color",
    "return_edge_color",
    "lighting_system_type",
    "led_module_power_w",
    "led_strip_density",
    "led_strip_power_w_per_ml",
    "light_color",
    "led_color_temperature",
    "total_led_watts",
    "required_psu_watts",
    "psu_sizing_status",
    "psu_sizing_warning",
    "notes",
    "vector_file_present",
    "vector_file_name",
    "vector_file_url",
    "vector_attachment_id",
    "vector_file_type",
    "vector_analysis_status",
    "vector_manual_review_approved",
    "vector_manual_review_notes",
    "vector_metrics_source",
    "vector_layer_mapping_status",
    "svg_layer_mappings",
    "vector_parse_status",
    "vector_analysis_warnings",
    "vector_detected_layers_summary",
    "vector_preview_available",
    "vector_file_source",
    "vector_file_mime",
    "vector_file_size_bytes",
    "vector_file_selected_at",
    "vector_file_extension",
    "vector_file_quality_notes",
    "vector_layer_alignment_status",
    "vector_fast_ask_applied_at",
    "intake_input_pathway",
    "vector_svg_analyzed",
    "vector_svg_width",
    "vector_svg_height",
    "vector_svg_viewbox",
    "vector_detected_layer_count",
    "vector_detected_layers",
    "vector_layer_mapping_confirmed",
    "vector_primary_letters_layer_id",
    "vector_primary_letters_layer_name",
    "vector_letters_layer_suggestion_confidence",
    "vector_layer_mapping_confirmed_at",
    "vector_layer_analysis_warnings",
    "vector_geometry_analyzed",
    "vector_geometry_confidence",
    "vector_geometry_warnings",
    "vector_geometry_parser_version",
    "vector_geometry_suggestions_ignored",
    "vector_suggested_assembly_width_mm",
    "vector_suggested_assembly_height_mm",
    "vector_suggested_letter_layer_width_mm",
    "vector_suggested_letter_layer_height_mm",
    "vector_suggested_support_width_mm",
    "vector_suggested_support_height_mm",
    "vector_suggested_support_area_m2",
    "vector_suggested_frame_width_mm",
    "vector_suggested_frame_height_mm",
    "vector_suggested_letter_element_count",
    "vector_suggested_letter_perimeter_m",
    "vector_suggested_letter_face_area_m2",
    "vector_suggested_letter_count",
    "letter_bounding_boxes",
    "face_vinyl_pieces",
    "geometry_source",
    "svgLetterGroups",
    "letterGroupFinishAssignments",
    "svgArtworkLayersPending",
    "svgArtworkFinishAssignments",
    "workFileAttachments",
})

SVG_LETTER_GROUP_KEYS = frozenset({
    "groupId",
    "sourceLayerName",
    "sourceFillColor",
    "sourceStrokeColor",
    "visualLabel",
    "elementCount",
    "faceAreaM2",
    "perimeterM",
    "status",
    "mergedIntoGroupId",
})

LETTER_GROUP_FACE_KEYS = frozenset({
    "finishType",
    "materialCode",
    "colorCode",
    "colorName",
    "notes",
})

LETTER_GROUP_RETURN_KEYS = LETTER_GROUP_FACE_KEYS | frozenset({"depthMm"})

LETTER_GROUP_BACKING_KEYS = frozenset({
    "materialType",
    "notes",
})

SVG_ARTWORK_PENDING_KEYS = frozenset({
    "layerId",
    "layerName",
    "elementCount",
    "distinctFillCount",
    "distinctFills",
    "reason",
    "status",
    "note",
})

SVG_ARTWORK_FINISH_ASSIGNMENT_KEYS = frozenset({
    "layerId",
    "layerName",
    "executionType",
    "materialCode",
    "colorMode",
    "estimatedAreaM2",
    "elementCount",
    "distinctFillCount",
    "returnCant",
    "printFile",
    "notes",
    "confirmedByOperator",
})

SVG_ARTWORK_PRINT_FILE_KEYS = frozenset({
    "fileName",
    "storedFileName",
    "sizeBytes",
    "contentType",
    "uploadedAt",
})

SVG_ARTWORK_EXECUTION_TYPES = frozenset({
    "print_laminate",
    "print_translucent",
    "printed_vinyl_on_face",
    "separate_emblem",
    "ignore_reference",
    "needs_decision",
})

SVG_ARTWORK_COLOR_MODES = frozenset({
    "polychrome",
    "single_color",
    "unknown",
})

WORK_FILE_ATTACHMENT_KEYS = frozenset({
    "id",
    "fileName",
    "fileUrl",
    "storedFileName",
    "mimeType",
    "extension",
    "sizeBytes",
    "role",
    "usableFor",
    "uploadedAt",
    "uploadedBy",
    "notes",
    "isPrimary",
})

WORK_FILE_ROLES = frozenset({
    "master_work_file",
    "cnc_source",
    "print_source",
    "cut_source",
    "modeling_source",
    "reference",
})

WORK_FILE_USABLE_FOR = frozenset({
    "cnc",
    "print",
    "cutter_plotter",
    "modeling",
    "mounting",
    "sales",
    "general_production",
})

VECTOR_FILE_SOURCES = frozenset({"local_manual", "server_upload"})
INTAKE_INPUT_PATHWAYS = frozenset({"vector", "manual", "quick_estimate"})
VECTOR_LAYER_ALIGNMENT_STATUSES = frozenset({"aligned", "needs_review", "unknown"})
VECTOR_GEOMETRY_CONFIDENCE = frozenset({"high", "medium", "low"})
GEOMETRY_SOURCES = frozenset({"manual", "svg_suggestion_confirmed"})

VECTOR_PARSE_STATUSES = frozenset({"parsed", "parsed_sanitized", "failed"})

ILLUMINATION_TYPES = frozenset({"frontlit", "backlit", "halo", "non_illuminated"})
ILLUMINATION_FAMILIES = frozenset({"front_lit"})
RETURN_COLORS = frozenset({"white", "black"})
LIGHTING_SYSTEM_TYPES = frozenset({"led_modules", "led_strip", "led_module"})
LED_STRIP_DENSITIES = frozenset({"60_led_per_m", "120_led_per_m", "60_5w", "120_10w"})
LIGHT_COLORS = frozenset({"warm", "cold"})
PSU_SIZING_STATUSES = frozenset({"ok", "pending_geometry", "insufficient_capacity"})
RETURN_EDGE_COLORS = RETURN_COLORS
LED_COLOR_TEMPERATURES = frozenset({"warm", "cool"})
FACE_FINISHES = frozenset({
    "plexi",
    "oracal_651",
    "oracal_8500_translucent",
    "print_laminated",
    "other",
})
FACE_FINISH_TYPES = frozenset({
    "none",
    "oracal_651",
    "oracal_8500",
    "printed_vinyl",
    "printed_laminated_vinyl",
})
INDOOR_OUTDOOR = frozenset({"indoor", "outdoor"})
MOUNTING_TYPES = frozenset({"direct_wall", "premounted"})
PREMOUNTING_TYPES = frozenset({"none", "metal_structure", "acm_casetted_panel"})
PREMOUNT_BAR_MATERIALS = frozenset({"steel", "aluminum"})
MOUNTING_SYSTEMS = frozenset({"direct_wall", "steel_bars", "aluminum_bars", "acm_panel"})
VOLUME_FINISHES = frozenset({
    "oracal_651_before_forming",
    "paint_after_face_miter_bond",
    "none",
})
PAINT_FINISHES = frozenset({"matte", "gloss", "satin", "not_specified"})
FACE_VINYL_FINISHES = frozenset({"gloss", "matte", "translucent_matte", "satin"})
PSU_WATTS = frozenset({60, 100, 160, 200})
ROLL_WIDTHS = frozenset({1000, 1260})
VECTOR_FILE_TYPES = frozenset({"svg", "dxf", "dwg", "other"})
VECTOR_ANALYSIS_STATUSES = frozenset({
    "not_provided",
    "attached_unanalyzed",
    "analyzed",
    "analysis_failed",
    "manual_review_approved",
})
VECTOR_LAYER_MAPPING_STATUSES = frozenset({
    "not_required",
    "pending",
    "mapped",
    "failed",
})
VECTOR_METRICS_SOURCES = frozenset({
    "manual",
    "svg_analysis",
    "dxf_analysis",
    "dwg_manual",
})

VECTOR_LAYER_ROLES = frozenset({
    "volumetric_letters",
    "letter_face",
    "side_return",
    "support_panel",
    "metal_frame",
    "guide_reference",
    "ignore",
    "unknown",
})


def _positive_number(value: Any, key: str) -> float:
    try:
        num = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"product_spec_json.{key} must be a number") from exc
    if num <= 0:
        raise ValueError(f"product_spec_json.{key} must be positive")
    return num


def _enum(value: Any, key: str, allowed: frozenset) -> str:
    val = str(value).strip()
    if val not in allowed:
        raise ValueError(f"product_spec_json.{key} must be one of: {sorted(allowed)}")
    return val


def _bool_value(value: Any, key: str) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in ("true", "1", "yes"):
        return True
    if text in ("false", "0", "no"):
        return False
    raise ValueError(f"product_spec_json.{key} must be a boolean")


def _optional_string(value: Any) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    stripped = value.strip()
    return stripped if stripped else None


def _optional_number(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_string_subobject(
    value: Any,
    allowed_keys: frozenset[str],
    numeric_keys: frozenset[str] = frozenset(),
) -> Optional[Dict[str, Any]]:
    if not isinstance(value, dict):
        return None
    out: Dict[str, Any] = {}
    for key, raw in value.items():
        if key not in allowed_keys:
            continue
        if key in numeric_keys:
            num = _optional_number(raw)
            if num is not None:
                out[key] = num
            continue
        text = _optional_string(raw)
        if text is not None:
            out[key] = text
    return out if out else None


def _normalize_svg_letter_groups(value: Any) -> Optional[list[Dict[str, Any]]]:
    if not isinstance(value, list):
        raise ValueError("product_spec_json.svgLetterGroups must be a list")
    rows: list[Dict[str, Any]] = []
    string_keys = {
        "groupId",
        "sourceLayerName",
        "sourceFillColor",
        "sourceStrokeColor",
        "visualLabel",
        "status",
        "mergedIntoGroupId",
    }
    numeric_keys = {"elementCount", "faceAreaM2", "perimeterM"}
    for item in value:
        if not isinstance(item, dict):
            continue
        row: Dict[str, Any] = {}
        for key, raw in item.items():
            if key not in SVG_LETTER_GROUP_KEYS:
                continue
            if key in string_keys:
                text = _optional_string(raw)
                if text is not None:
                    row[key] = text
            elif key in numeric_keys:
                num = _optional_number(raw)
                if num is not None:
                    row[key] = num
        group_id = row.get("groupId")
        if group_id:
            rows.append(row)
    return rows if rows else None


def _normalize_letter_group_finish_assignments(
    value: Any,
) -> Optional[list[Dict[str, Any]]]:
    if not isinstance(value, list):
        raise ValueError("product_spec_json.letterGroupFinishAssignments must be a list")
    rows: list[Dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        group_id = _optional_string(item.get("groupId"))
        if not group_id:
            continue
        row: Dict[str, Any] = {"groupId": group_id}
        face = _normalize_string_subobject(item.get("face"), LETTER_GROUP_FACE_KEYS)
        if face is not None:
            row["face"] = face
        return_cant = _normalize_string_subobject(
            item.get("returnCant"),
            LETTER_GROUP_RETURN_KEYS,
            numeric_keys=frozenset({"depthMm"}),
        )
        if return_cant is not None:
            row["returnCant"] = return_cant
        backing = _normalize_string_subobject(item.get("backing"), LETTER_GROUP_BACKING_KEYS)
        if backing is not None:
            row["backing"] = backing
        if "confirmedByOperator" in item:
            try:
                row["confirmedByOperator"] = _bool_value(
                    item.get("confirmedByOperator"),
                    "letterGroupFinishAssignments.confirmedByOperator",
                )
            except ValueError:
                pass
        rows.append(row)
    return rows if rows else None


def _normalize_svg_artwork_layers_pending(
    value: Any,
) -> Optional[list[Dict[str, Any]]]:
    if not isinstance(value, list):
        raise ValueError("product_spec_json.svgArtworkLayersPending must be a list")
    rows: list[Dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        row: Dict[str, Any] = {}
        for key, raw in item.items():
            if key not in SVG_ARTWORK_PENDING_KEYS:
                continue
            if key in {"elementCount", "distinctFillCount"}:
                num = _optional_number(raw)
                if num is not None:
                    row[key] = int(num)
            elif key == "distinctFills":
                if not isinstance(raw, list):
                    continue
                fills = [_optional_string(fill) for fill in raw]
                cleaned = [fill for fill in fills if fill]
                if cleaned:
                    row[key] = cleaned
            else:
                text = _optional_string(raw)
                if text is not None:
                    row[key] = text
        if row.get("layerName") or row.get("layerId"):
            rows.append(row)
    return rows if rows else None


def _normalize_svg_artwork_finish_assignments(
    value: Any,
) -> Optional[list[Dict[str, Any]]]:
    if not isinstance(value, list):
        raise ValueError("product_spec_json.svgArtworkFinishAssignments must be a list")
    rows: list[Dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        row: Dict[str, Any] = {}
        for key, raw in item.items():
            if key not in SVG_ARTWORK_FINISH_ASSIGNMENT_KEYS:
                continue
            if key in {"elementCount", "distinctFillCount"}:
                num = _optional_number(raw)
                if num is not None:
                    row[key] = int(num)
            elif key == "estimatedAreaM2":
                num = _optional_number(raw)
                if num is not None:
                    row[key] = num
            elif key == "executionType":
                text = _optional_string(raw)
                if text in SVG_ARTWORK_EXECUTION_TYPES:
                    row[key] = text
            elif key == "colorMode":
                text = _optional_string(raw)
                if text in SVG_ARTWORK_COLOR_MODES:
                    row[key] = text
            elif key == "confirmedByOperator":
                try:
                    row[key] = _bool_value(
                        raw,
                        "svgArtworkFinishAssignments.confirmedByOperator",
                    )
                except ValueError:
                    pass
            elif key == "returnCant":
                return_cant = _normalize_string_subobject(
                    raw,
                    LETTER_GROUP_RETURN_KEYS,
                    numeric_keys=frozenset({"depthMm"}),
                )
                if return_cant is not None:
                    row[key] = return_cant
            elif key == "printFile":
                print_file = _normalize_string_subobject(
                    raw,
                    SVG_ARTWORK_PRINT_FILE_KEYS,
                    numeric_keys=frozenset({"sizeBytes"}),
                )
                if print_file is not None and print_file.get("fileName"):
                    row[key] = print_file
            else:
                text = _optional_string(raw)
                if text is not None:
                    row[key] = text
        if row.get("layerName") or row.get("layerId"):
            if "executionType" not in row:
                row["executionType"] = "needs_decision"
            if "colorMode" not in row:
                row["colorMode"] = "polychrome"
            if "confirmedByOperator" not in row:
                row["confirmedByOperator"] = False
            rows.append(row)
    return rows if rows else None


def _normalize_work_file_attachments(value: Any) -> Optional[list[Dict[str, Any]]]:
    if not isinstance(value, list):
        raise ValueError("product_spec_json.workFileAttachments must be a list")
    rows: list[Dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        row: Dict[str, Any] = {}
        for key, raw in item.items():
            if key not in WORK_FILE_ATTACHMENT_KEYS:
                continue
            if key == "sizeBytes":
                num = _optional_number(raw)
                if num is not None:
                    row[key] = int(num)
            elif key == "isPrimary":
                try:
                    row[key] = _bool_value(raw, "workFileAttachments.isPrimary")
                except ValueError:
                    pass
            elif key == "role":
                text = _optional_string(raw)
                if text in WORK_FILE_ROLES:
                    row[key] = text
            elif key == "usableFor":
                if not isinstance(raw, list):
                    continue
                cleaned = [
                    val
                    for val in (_optional_string(entry) for entry in raw)
                    if val in WORK_FILE_USABLE_FOR
                ]
                if cleaned:
                    row[key] = cleaned
            else:
                text = _optional_string(raw)
                if text is not None:
                    row[key] = text
        file_id = row.get("id")
        file_name = row.get("fileName")
        file_url = row.get("fileUrl")
        if file_id and file_name and file_url:
            if "role" not in row:
                row["role"] = "master_work_file"
            if "usableFor" not in row:
                row["usableFor"] = ["general_production"]
            rows.append(row)
    return rows if rows else None


def validate_intake_product_spec(spec: Any) -> Optional[Dict[str, Any]]:
    """Validate and normalize product_spec_json. None clears the field."""
    if spec is None:
        return None
    if not isinstance(spec, dict):
        raise ValueError("product_spec_json must be a JSON object")

    out: Dict[str, Any] = {}
    for key, value in spec.items():
        if key not in ALLOWED_KEYS:
            continue
        if value is None:
            continue
        if key in (
            "text",
            "font",
            "ral_color",
            "notes",
            "mounting_notes",
            "lighting_notes",
            "face_vinyl_notes",
            "paint_ral_code",
            "paint_ral_name",
            "face_vinyl_color_code",
            "face_vinyl_color_name",
            "mounting_bar_profile",
            "vector_file_name",
            "vector_file_url",
            "vector_manual_review_notes",
            "vector_file_mime",
            "vector_file_selected_at",
            "vector_file_extension",
            "vector_file_quality_notes",
            "vector_fast_ask_applied_at",
            "vector_svg_width",
            "vector_svg_height",
            "vector_svg_viewbox",
            "vector_geometry_parser_version",
            "psu_sizing_warning",
        ):
            if not isinstance(value, str):
                raise ValueError(f"product_spec_json.{key} must be a string")
            stripped = value.strip()
            if stripped:
                out[key] = stripped
            continue
        if key in (
            "width_mm",
            "height_mm",
            "letter_height_mm",
            "depth_mm",
            "return_depth_mm",
            "letter_face_area_m2",
            "letter_perimeter_m",
            "letter_count",
            "mounting_template_area_m2",
            "paint_tube_count",
            "mounting_bar_count",
            "mounting_bar_length_m",
            "vector_file_size_bytes",
            "vector_detected_layer_count",
            "vector_suggested_assembly_width_mm",
            "vector_suggested_assembly_height_mm",
            "vector_suggested_letter_layer_width_mm",
            "vector_suggested_letter_layer_height_mm",
            "vector_suggested_support_width_mm",
            "vector_suggested_support_height_mm",
            "vector_suggested_support_area_m2",
            "vector_suggested_frame_width_mm",
            "vector_suggested_frame_height_mm",
            "vector_suggested_letter_element_count",
            "vector_suggested_letter_perimeter_m",
            "vector_suggested_letter_face_area_m2",
            "vector_suggested_letter_count",
            "total_led_watts",
            "required_psu_watts",
            "led_strip_power_w_per_ml",
        ):
            out[key] = _positive_number(value, key)
            continue
        if key in (
            "vector_svg_analyzed",
            "vector_layer_mapping_confirmed",
            "vector_geometry_analyzed",
            "vector_geometry_suggestions_ignored",
        ):
            out[key] = _bool_value(value, key)
            continue
        if key == "vector_geometry_confidence":
            out[key] = _enum(value, key, VECTOR_GEOMETRY_CONFIDENCE)
            continue
        if key == "geometry_source":
            out[key] = _enum(value, key, GEOMETRY_SOURCES)
            continue
        if key == "vector_file_source":
            out[key] = _enum(value, key, VECTOR_FILE_SOURCES)
            continue
        if key == "intake_input_pathway":
            out[key] = _enum(value, key, INTAKE_INPUT_PATHWAYS)
            continue
        if key == "vector_layer_alignment_status":
            out[key] = _enum(value, key, VECTOR_LAYER_ALIGNMENT_STATUSES)
            continue
        if key == "illumination_type":
            out[key] = _enum(value, key, ILLUMINATION_TYPES)
            continue
        if key == "return_edge_color":
            out[key] = _enum(value, key, RETURN_COLORS)
            continue
        if key == "return_color":
            out[key] = _enum(value, key, RETURN_COLORS)
            continue
        if key == "illumination_family":
            out[key] = _enum(value, key, ILLUMINATION_FAMILIES)
            continue
        if key == "lighting_system_type":
            out[key] = _enum(value, key, LIGHTING_SYSTEM_TYPES)
            continue
        if key == "led_strip_density":
            out[key] = _enum(value, key, LED_STRIP_DENSITIES)
            continue
        if key == "light_color":
            out[key] = _enum(value, key, LIGHT_COLORS)
            continue
        if key == "psu_sizing_status":
            out[key] = _enum(value, key, PSU_SIZING_STATUSES)
            continue
        if key == "led_module_power_w":
            try:
                module_w = round(float(value), 2)
            except (TypeError, ValueError) as exc:
                raise ValueError("product_spec_json.led_module_power_w must be numeric") from exc
            if module_w not in {0.72, 0.75, 1.0, 1.44}:
                raise ValueError(
                    "product_spec_json.led_module_power_w must be one of: 0.72, 0.75, 1, 1.44"
                )
            out["led_module_power_w"] = module_w
            out["led_module_wattage"] = module_w
            continue
        if key == "led_color_temperature":
            out[key] = _enum(value, key, LED_COLOR_TEMPERATURES)
            continue
        if key == "face_finish":
            out[key] = _enum(value, key, FACE_FINISHES)
            continue
        if key == "face_finish_type":
            out[key] = _enum(value, key, FACE_FINISH_TYPES)
            continue
        if key == "volume_finish":
            out[key] = _enum(value, key, VOLUME_FINISHES)
            continue
        if key == "indoor_outdoor":
            out[key] = _enum(value, key, INDOOR_OUTDOOR)
            continue
        if key == "mounting_type":
            out[key] = _enum(value, key, MOUNTING_TYPES)
            continue
        if key == "premounting_type":
            out[key] = _enum(value, key, PREMOUNTING_TYPES)
            continue
        if key == "premount_bar_material":
            out[key] = _enum(value, key, PREMOUNT_BAR_MATERIALS)
            continue
        if key == "mounting_system":
            out[key] = _enum(value, key, MOUNTING_SYSTEMS)
            continue
        if key == "paint_finish":
            out[key] = _enum(value, key, PAINT_FINISHES)
            continue
        if key == "face_vinyl_finish":
            out[key] = _enum(value, key, FACE_VINYL_FINISHES)
            continue
        if key == "selected_psu_watts":
            try:
                watts = int(float(value))
            except (TypeError, ValueError) as exc:
                raise ValueError("product_spec_json.selected_psu_watts must be an integer") from exc
            if watts not in PSU_WATTS:
                raise ValueError(
                    f"product_spec_json.selected_psu_watts must be one of: {sorted(PSU_WATTS)}"
                )
            out[key] = watts
            continue
        if key == "face_vinyl_roll_width_mm":
            try:
                roll = int(float(value))
            except (TypeError, ValueError) as exc:
                raise ValueError("product_spec_json.face_vinyl_roll_width_mm must be an integer") from exc
            if roll not in ROLL_WIDTHS:
                raise ValueError(
                    "product_spec_json.face_vinyl_roll_width_mm must be 1000 or 1260"
                )
            out[key] = roll
            continue
        if key in (
            "backing_chamfer",
            "back_bevel_enabled",
            "face_miter_chamfer",
            "visual_chamfer_included",
            "face_vinyl_enabled",
            "face_wrap_enabled",
            "mounting_template_enabled",
            "vector_file_present",
            "vector_manual_review_approved",
            "vector_preview_available",
        ):
            out[key] = _bool_value(value, key)
            continue
        if key == "vector_file_type":
            out[key] = _enum(value, key, VECTOR_FILE_TYPES)
            continue
        if key == "vector_analysis_status":
            out[key] = _enum(value, key, VECTOR_ANALYSIS_STATUSES)
            continue
        if key == "vector_layer_mapping_status":
            out[key] = _enum(value, key, VECTOR_LAYER_MAPPING_STATUSES)
            continue
        if key == "vector_metrics_source":
            out[key] = _enum(value, key, VECTOR_METRICS_SOURCES)
            continue
        if key == "vector_attachment_id":
            try:
                att_id = int(float(value))
            except (TypeError, ValueError) as exc:
                raise ValueError("product_spec_json.vector_attachment_id must be an integer") from exc
            if att_id > 0:
                out[key] = att_id
            continue
        if key == "svg_layer_mappings":
            normalized = normalize_svg_layer_mappings(value)
            if normalized:
                out[key] = normalized
            continue
        if key in ("letter_bounding_boxes", "face_vinyl_pieces"):
            if not isinstance(value, list):
                raise ValueError(f"product_spec_json.{key} must be a list")
            rows: list[dict[str, Any]] = []
            for index, item in enumerate(value):
                if not isinstance(item, dict):
                    continue
                try:
                    width_mm = _positive_number(item.get("width_mm"), f"{key}.width_mm")
                    height_mm = _positive_number(item.get("height_mm"), f"{key}.height_mm")
                except ValueError:
                    continue
                piece_id = str(item.get("piece_id") or item.get("id") or f"piece_{index + 1}").strip()
                row: dict[str, Any] = {
                    "piece_id": piece_id,
                    "width_mm": width_mm,
                    "height_mm": height_mm,
                }
                label = str(item.get("label") or item.get("name") or "").strip()
                if label:
                    row["label"] = label
                source = str(item.get("source") or "").strip()
                if source:
                    row["source"] = source
                source_layer_id = str(item.get("source_layer_id") or "").strip()
                if source_layer_id:
                    row["source_layer_id"] = source_layer_id
                confidence = str(item.get("confidence") or "").strip()
                if confidence:
                    row["confidence"] = confidence
                rows.append(row)
            if rows:
                out[key] = rows
            continue
        if key == "vector_parse_status":
            out[key] = _enum(value, key, VECTOR_PARSE_STATUSES)
            continue
        if key in ("vector_analysis_warnings", "vector_geometry_warnings"):
            if not isinstance(value, list):
                raise ValueError(f"product_spec_json.{key} must be a list")
            warnings = [str(item).strip() for item in value if str(item).strip()]
            if warnings:
                out[key] = warnings
            continue
        if key == "vector_layer_analysis_warnings":
            if not isinstance(value, list):
                raise ValueError("product_spec_json.vector_layer_analysis_warnings must be a list")
            warnings = [str(item).strip() for item in value if str(item).strip()]
            if warnings:
                out[key] = warnings
            continue
        if key == "vector_detected_layers":
            if not isinstance(value, list):
                raise ValueError("product_spec_json.vector_detected_layers must be a list")
            rows = []
            for item in value:
                if not isinstance(item, dict):
                    continue
                layer_id = str(item.get("id", "")).strip()
                label = str(item.get("label", "")).strip()
                if not layer_id or not label:
                    continue
                try:
                    element_count = int(float(item.get("element_count", 0)))
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        "product_spec_json.vector_detected_layers.element_count must be an integer"
                    ) from exc
                if element_count < 0:
                    continue
                suggested = str(item.get("suggested_role", "unknown")).strip()
                confirmed = str(item.get("confirmed_role", "unknown")).strip()
                if suggested not in VECTOR_LAYER_ROLES:
                    suggested = "unknown"
                if confirmed not in VECTOR_LAYER_ROLES:
                    confirmed = "unknown"
                rows.append({
                    "id": layer_id,
                    "label": label,
                    "element_count": element_count,
                    "suggested_role": suggested,
                    "confirmed_role": confirmed,
                })
            if rows:
                out[key] = rows
            continue
        if key == "vector_detected_layers_summary":
            if not isinstance(value, list):
                raise ValueError(
                    "product_spec_json.vector_detected_layers_summary must be a list"
                )
            rows = []
            for item in value:
                if not isinstance(item, dict):
                    continue
                name = str(item.get("layer_name", "")).strip()
                if not name:
                    continue
                row: Dict[str, Any] = {"layer_name": name}
                for field in (
                    "mapping_status",
                    "mapped_by",
                    "mapped_target",
                    "mapped_template_code",
                    "detected_kind",
                ):
                    raw = item.get(field)
                    if raw is None:
                        continue
                    text = str(raw).strip()
                    if text:
                        row[field] = text
                rows.append(row)
            if rows:
                out[key] = rows
            continue
        if key == "svgLetterGroups":
            normalized = _normalize_svg_letter_groups(value)
            if normalized:
                out[key] = normalized
            continue
        if key == "letterGroupFinishAssignments":
            normalized = _normalize_letter_group_finish_assignments(value)
            if normalized:
                out[key] = normalized
            continue
        if key == "svgArtworkLayersPending":
            normalized = _normalize_svg_artwork_layers_pending(value)
            if normalized:
                out[key] = normalized
            continue
        if key == "svgArtworkFinishAssignments":
            normalized = _normalize_svg_artwork_finish_assignments(value)
            if normalized:
                out[key] = normalized
            continue
        if key == "workFileAttachments":
            normalized = _normalize_work_file_attachments(value)
            if normalized:
                out[key] = normalized
            continue

    return out if out else None

"""
ProductSystemService — builds a ProductDefinition from a product_template + user_config.

Canonical rules:
  - Defines the product, NOT the cost.
  - Does NOT read price/cost data.
  - Marks missing fields explicitly in ProductValidationResult.
  - Returns a ProductDefinition whose validation.is_valid reflects completeness.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from data_models.product_contracts import (
    ProductComponent,
    ProductDefinition,
    ProductDimensions,
    ProductLayer,
    ProductMaterial,
    ProductProcess,
    ProductValidationResult,
)
from services.order_execution_snapshot_mapper import resolve_canonical_task_type


def _safe_json_loads(raw: Any, default):
    if raw is None or raw == "":
        return default
    if isinstance(raw, (list, dict)):
        return raw
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return default


class ProductSystemService:
    """Service that turns raw template+config into a canonical ProductDefinition.

    Inputs:
      - product_template: dict-like (row from product_templates table or equivalent)
      - user_config: dict (quantity, dimensions, selected variants, overrides)

    Output:
      - ProductDefinition (with validation result)
    """

    def build_product_definition(
        self,
        product_template: Optional[Dict[str, Any]],
        user_config: Optional[Dict[str, Any]] = None,
    ) -> ProductDefinition:
        user_config = user_config or {}
        missing: List[str] = []
        warnings: List[str] = []

        if not product_template:
            # We cannot build a product without a template — mark invalid explicitly.
            return ProductDefinition(
                product_id=str(user_config.get("product_id", "")),
                product_type="",
                quantity=int(user_config.get("quantity", 1) or 1),
                validation=ProductValidationResult(
                    is_valid=False,
                    missing_fields=["product_template"],
                    warnings=[],
                ),
            )

        # --- Basic identity ---
        product_id = str(
            user_config.get("product_id")
            or product_template.get("template_code")
            or product_template.get("id")
            or ""
        )
        product_type = str(
            product_template.get("family_name")
            or product_template.get("family_id")
            or ""
        )
        if not product_type:
            missing.append("product_type")

        # --- Quantity (strict, Sprint #10 Flow Hardening — Option B) ---
        # A quote MUST have an explicit positive quantity. No silent
        # fallback to 1 — missing/invalid quantity MUST block the quote
        # (router maps this to HTTP 422 via `product_invalid:quantity`).
        raw_qty = user_config.get("quantity", None)
        quantity = 0
        if raw_qty is None or raw_qty == "":
            missing.append("quantity")
        else:
            try:
                quantity = int(raw_qty)
                if quantity <= 0:
                    missing.append("quantity")
                    quantity = 0
            except (TypeError, ValueError):
                missing.append("quantity")
                quantity = 0

        # --- Dimensions (strict where necessary, Sprint #10 — Option B) ---
        # A quote MUST have at least one meaningful dimension (width OR
        # height > 0). Depth alone is not sufficient. If neither width
        # nor height is provided, block the quote — no silent default
        # geometry.
        dims_raw = user_config.get("dimensions") or {}
        dimensions = ProductDimensions(
            width_mm=float(dims_raw.get("width_mm") or 0),
            height_mm=float(dims_raw.get("height_mm") or 0),
            depth_mm=float(dims_raw.get("depth_mm") or 0),
        )
        if dimensions.width_mm <= 0 and dimensions.height_mm <= 0:
            missing.append("dimensions")

        # --- Layers from template ---
        # template.components_json: list[str] legacy
        # template.operations_json: list[operation dicts]
        # template.required_materials_json: list[material dicts]
        components_raw = _safe_json_loads(product_template.get("components_json"), [])
        operations_raw = _safe_json_loads(product_template.get("operations_json"), [])
        materials_raw = _safe_json_loads(product_template.get("required_materials_json"), [])

        if not materials_raw:
            warnings.append("template_has_no_required_materials")
        if not operations_raw:
            warnings.append("template_has_no_operations")

        layers = self._build_layers(
            components_raw=components_raw,
            operations_raw=operations_raw,
            materials_raw=materials_raw,
            user_config=user_config,
            missing=missing,
        )

        if not layers:
            missing.append("layers")

        is_valid = len(missing) == 0

        return ProductDefinition(
            product_id=product_id,
            product_type=product_type,
            quantity=quantity,
            dimensions=dimensions,
            layers=layers,
            validation=ProductValidationResult(
                is_valid=is_valid,
                missing_fields=missing,
                warnings=warnings,
            ),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _build_layers(
        self,
        components_raw: Any,
        operations_raw: Any,
        materials_raw: Any,
        user_config: Dict[str, Any],
        missing: List[str],
    ) -> List[ProductLayer]:
        """Minimal layer synthesis:
        - 1 layer of type "structure" per material in required_materials_json
        - Components attached = legacy string components mapped to pcs=1
        - Processes attached to the first structure layer only
        """
        layers: List[ProductLayer] = []

        # Normalize components (legacy shape is list[str])
        components: List[ProductComponent] = []
        if isinstance(components_raw, list):
            for idx, c in enumerate(components_raw):
                if isinstance(c, str) and c.strip():
                    components.append(
                        ProductComponent(
                            component_id=f"comp_{idx+1}",
                            type=c.strip(),
                            quantity=1,
                            unit="pcs",
                        )
                    )
                elif isinstance(c, dict):
                    components.append(
                        ProductComponent(
                            component_id=str(c.get("component_id") or c.get("code") or f"comp_{idx+1}"),
                            type=str(c.get("type") or c.get("name") or ""),
                            quantity=float(c.get("quantity") or 1),
                            unit=str(c.get("unit") or "pcs"),
                        )
                    )

        # Normalize processes
        processes: List[ProductProcess] = []
        if isinstance(operations_raw, list):
            for idx, op in enumerate(operations_raw):
                if not isinstance(op, dict):
                    continue
                process_id = str(op.get("code") or f"proc_{idx+1}")
                op_type = str(op.get("workcenter") or op.get("type") or op.get("code") or "").lower()
                # Map workcenter heuristically to canonical process types
                mapped_type = op_type
                for canonical in ("cut", "print", "cnc", "assembly", "wiring"):
                    if canonical in op_type:
                        mapped_type = canonical
                        break
                canonical_type = resolve_canonical_task_type(
                    process_id=process_id,
                    legacy_type=mapped_type,
                )
                processes.append(
                    ProductProcess(
                        process_id=process_id,
                        type=canonical_type or mapped_type or "assembly",
                        machine_type=op.get("workcenter"),
                        estimated_time_minutes=float(op.get("estimatedMinutes") or 0),
                    )
                )

        # If no materials, we still want at least one layer if components/processes exist
        if not materials_raw and (components or processes):
            layers.append(
                ProductLayer(
                    layer_id="layer_1",
                    layer_type="structure",
                    material=ProductMaterial(material_id="", name="", unit="pcs"),
                    thickness_mm=0,
                    finish="",
                    components=components,
                    processes=processes,
                )
            )
            missing.append("material_ref")
            return layers

        if not isinstance(materials_raw, list):
            return layers

        for idx, mat in enumerate(materials_raw):
            if not isinstance(mat, dict):
                continue
            material_id = str(mat.get("materialCode") or mat.get("material_id") or "")
            if not material_id:
                missing.append(f"material_id[layer_{idx+1}]")
            unit = str(mat.get("unit") or "pcs")
            layer = ProductLayer(
                layer_id=f"layer_{idx+1}",
                layer_type="structure",
                material=ProductMaterial(
                    material_id=material_id,
                    name=str(mat.get("name") or ""),
                    unit=unit,
                ),
                thickness_mm=float(mat.get("thickness_mm") or 0),
                finish=str(mat.get("finish") or ""),
                components=components if idx == 0 else [],
                processes=processes if idx == 0 else [],
            )
            # Carry material quantity as a synthetic component so CostEngine
            # can see the requested material consumption.
            material_qty = float(mat.get("quantity") or 0)
            if material_qty > 0:
                layer.components.append(
                    ProductComponent(
                        component_id=f"mat_qty_{idx+1}",
                        type=f"material:{material_id}",
                        quantity=material_qty,
                        unit=unit,
                    )
                )
            layers.append(layer)

        return layers
"""
ExecutionPlanService — WorkOS Execution Layer v1.

STRICT BOUNDARIES (non-negotiable):
  - Reads ONLY from the Order row and its `snapshot_line_items` JSON.
  - Does NOT import CostEngine, QuoteOrchestrator, ProductSystemService,
    ProductTemplate, MaterialRate, or anything upstream.
  - Missing/invalid snapshot fields MUST raise a structured 422-equivalent
    error. There are NO `or 0`, `or None`, `or []`, `or "pcs"` fallbacks.
    Missing data is reported explicitly, never silently coerced.
  - Task descent strategy (v1):
      * For every process in every layer of product_definition, emit one task.
      * If no processes are found across all layers, emit ONE coarse task
        "produce_order" with estimated_time_minutes taken from
        cost_result.estimated_time_minutes. This is documented in the spec
        as a v1 fallback for MINIMAL, CORRECT coverage — it does not
        invent or import anything, it only reads the existing snapshot.
      * If cost_result.estimated_time_minutes is also missing, raise 422.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List

from services.volumetric_execution_dispatch import resolve_execution_task_display_name


class SnapshotIncompleteError(Exception):
    """Raised when the OrderSnapshot lacks a required field.

    The router layer converts this into HTTP 422 with a structured detail.
    """

    def __init__(self, field_path: str, message: str = ""):
        self.field_path = field_path
        self.message = message or f"snapshot_incomplete:{field_path}"
        super().__init__(self.message)


@dataclass
class PlannedTask:
    task_id: str
    name: str
    layer_id: str
    process_type: str
    machine_type: str
    estimated_time_minutes: float
    quantity: float
    process_id: str = ""
    display_name: str = ""

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            "task_id": self.task_id,
            "name": self.display_name or self.name,
            "layer_id": self.layer_id,
            "process_type": self.process_type,
            "machine_type": self.machine_type,
            "estimated_time_minutes": self.estimated_time_minutes,
            "quantity": self.quantity,
        }
        if self.process_id:
            payload["process_id"] = self.process_id
        if self.display_name:
            payload["display_name"] = self.display_name
        # Preserve technical key for routing/debug consumers.
        payload["technical_name"] = self.name
        return payload


@dataclass
class ExecutionPlanDTO:
    order_id: int
    order_code: str
    snapshot_version: int
    tasks: List[PlannedTask] = field(default_factory=list)
    total_estimated_time_minutes: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "order_code": self.order_code,
            "snapshot_version": self.snapshot_version,
            "tasks": [t.to_dict() for t in self.tasks],
            "total_estimated_time_minutes": self.total_estimated_time_minutes,
        }


def _require(d: Dict[str, Any], key: str, path: str) -> Any:
    """Strict getter — raises SnapshotIncompleteError if key is absent.

    NO fallback. NO default. NO silent coercion. This is intentional and
    enforced by the audit.
    """
    if not isinstance(d, dict):
        raise SnapshotIncompleteError(path, f"snapshot_not_object:{path}")
    if key not in d:
        raise SnapshotIncompleteError(f"{path}.{key}" if path else key)
    return d[key]


def _require_number(value: Any, path: str) -> float:
    if value is None:
        raise SnapshotIncompleteError(path, f"snapshot_null_number:{path}")
    if isinstance(value, bool):
        # bool is a subtype of int in Python; reject it explicitly.
        raise SnapshotIncompleteError(path, f"snapshot_bool_for_number:{path}")
    if not isinstance(value, (int, float)):
        raise SnapshotIncompleteError(path, f"snapshot_not_number:{path}")
    return float(value)


def _require_str(value: Any, path: str, allow_empty: bool = False) -> str:
    if value is None:
        raise SnapshotIncompleteError(path, f"snapshot_null_string:{path}")
    if not isinstance(value, str):
        raise SnapshotIncompleteError(path, f"snapshot_not_string:{path}")
    if not allow_empty and value == "":
        raise SnapshotIncompleteError(path, f"snapshot_empty_string:{path}")
    return value


class ExecutionPlanService:
    """Generates an ExecutionPlanDTO from an Order row.

    The only inputs it touches on the order are:
      - order.id
      - order.code
      - order.snapshot_version
      - order.snapshot_line_items  (JSON string)

    Anything else is off-limits on purpose.
    """

    def from_order(self, order_row: Any) -> ExecutionPlanDTO:
        # 1) Validate presence of required Order fields (direct attribute reads).
        order_id = getattr(order_row, "id", None)
        if order_id is None:
            raise SnapshotIncompleteError("order.id")
        order_code = getattr(order_row, "code", None)
        if order_code is None or order_code == "":
            raise SnapshotIncompleteError("order.code")
        snapshot_version = getattr(order_row, "snapshot_version", None)
        if snapshot_version is None:
            raise SnapshotIncompleteError("order.snapshot_version")
        snapshot_raw = getattr(order_row, "snapshot_line_items", None)
        if snapshot_raw is None or snapshot_raw == "":
            raise SnapshotIncompleteError("order.snapshot_line_items")

        # 2) Parse snapshot JSON — no silent fallback on parse errors.
        try:
            snapshot = json.loads(snapshot_raw)
        except (TypeError, ValueError) as e:
            raise SnapshotIncompleteError(
                "order.snapshot_line_items",
                f"snapshot_invalid_json:{e}",
            )

        if not isinstance(snapshot, dict):
            raise SnapshotIncompleteError(
                "order.snapshot_line_items",
                "snapshot_not_object",
            )

        # 3) Required snapshot sub-trees.
        product_definition = _require(snapshot, "product_definition", "snapshot")
        cost_result = _require(snapshot, "cost_result", "snapshot")

        # 4) ProductDefinition fields we care about.
        quantity_raw = _require(product_definition, "quantity", "snapshot.product_definition")
        product_quantity = _require_number(quantity_raw, "snapshot.product_definition.quantity")
        if product_quantity <= 0:
            raise SnapshotIncompleteError(
                "snapshot.product_definition.quantity",
                "snapshot_non_positive_quantity",
            )

        layers_raw = _require(
            product_definition, "layers", "snapshot.product_definition"
        )
        if not isinstance(layers_raw, list):
            raise SnapshotIncompleteError(
                "snapshot.product_definition.layers",
                "snapshot_layers_not_list",
            )

        product_id_raw = product_definition.get("product_id")
        product_id = (
            str(product_id_raw)
            if isinstance(product_id_raw, str) and product_id_raw.strip()
            else None
        )

        # 5) Walk layers/processes and build tasks.
        tasks: List[PlannedTask] = []
        seq = 0
        for layer_idx, layer in enumerate(layers_raw):
            if not isinstance(layer, dict):
                raise SnapshotIncompleteError(
                    f"snapshot.product_definition.layers[{layer_idx}]",
                    "snapshot_layer_not_object",
                )
            layer_id = _require_str(
                _require(layer, "layer_id", f"snapshot.product_definition.layers[{layer_idx}]"),
                f"snapshot.product_definition.layers[{layer_idx}].layer_id",
            )
            processes_raw = _require(
                layer, "processes", f"snapshot.product_definition.layers[{layer_idx}]"
            )
            if not isinstance(processes_raw, list):
                raise SnapshotIncompleteError(
                    f"snapshot.product_definition.layers[{layer_idx}].processes",
                    "snapshot_processes_not_list",
                )
            for proc_idx, proc in enumerate(processes_raw):
                if not isinstance(proc, dict):
                    raise SnapshotIncompleteError(
                        f"snapshot.product_definition.layers[{layer_idx}].processes[{proc_idx}]",
                        "snapshot_process_not_object",
                    )
                base_path = (
                    f"snapshot.product_definition.layers[{layer_idx}].processes[{proc_idx}]"
                )
                process_id = _require_str(
                    _require(proc, "process_id", base_path),
                    f"{base_path}.process_id",
                )
                process_type = _require_str(
                    _require(proc, "type", base_path),
                    f"{base_path}.type",
                )
                est_minutes_raw = _require(
                    proc, "estimated_time_minutes", base_path
                )
                est_minutes = _require_number(
                    est_minutes_raw, f"{base_path}.estimated_time_minutes"
                )
                if est_minutes <= 0:
                    # Zero-minute processes are not execution tasks.
                    continue
                machine_type_val = proc.get("machine_type")
                if machine_type_val is None:
                    machine_type = ""
                elif isinstance(machine_type_val, str):
                    machine_type = machine_type_val
                else:
                    raise SnapshotIncompleteError(
                        f"{base_path}.machine_type",
                        "snapshot_machine_type_not_string",
                    )
                seq += 1
                technical_name = f"{process_type}:{process_id}"
                display_name = resolve_execution_task_display_name(
                    process_id=process_id,
                    process_type=process_type,
                    product_id=product_id,
                )
                tasks.append(
                    PlannedTask(
                        task_id=f"T-{seq:03d}",
                        name=technical_name,
                        display_name=display_name,
                        process_id=process_id,
                        layer_id=layer_id,
                        process_type=process_type,
                        machine_type=machine_type,
                        estimated_time_minutes=est_minutes * product_quantity,
                        quantity=product_quantity,
                    )
                )

        # 6) Coarse fallback — only when there are genuinely no processes.
        if not tasks:
            est_total_raw = _require(
                cost_result, "estimated_time_minutes", "snapshot.cost_result"
            )
            est_total = _require_number(
                est_total_raw, "snapshot.cost_result.estimated_time_minutes"
            )
            if est_total <= 0:
                raise SnapshotIncompleteError(
                    "snapshot.cost_result.estimated_time_minutes",
                    "snapshot_no_tasks_and_no_total_time",
                )
            tasks.append(
                PlannedTask(
                    task_id="T-001",
                    name="produce_order",
                    display_name=resolve_execution_task_display_name(
                        process_id="produce_order",
                        process_type="produce_order",
                        product_id=product_id,
                    ),
                    process_id="produce_order",
                    layer_id="",
                    process_type="produce_order",
                    machine_type="",
                    estimated_time_minutes=est_total,
                    quantity=product_quantity,
                )
            )

        total_estimated = round(sum(t.estimated_time_minutes for t in tasks), 2)

        return ExecutionPlanDTO(
            order_id=int(order_id),
            order_code=str(order_code),
            snapshot_version=int(snapshot_version),
            tasks=tasks,
            total_estimated_time_minutes=total_estimated,
        )
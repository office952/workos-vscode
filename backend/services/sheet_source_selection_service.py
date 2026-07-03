"""Sheet source selection foundation — prefer inventory offcuts, fallback to new sheet.

Inventory write is deferred: no dimensional offcut inventory model or
``offcut_created`` StockMovement type exists yet. This service builds
read-only candidate metadata for nesting summaries and future intake.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, MutableMapping, Sequence

SELECTION_POLICY = "prefer_existing_offcuts_then_new_sheet"
FOUNDATION_MODE = "foundation_only"
INVENTORY_DEFERRED_REASON = "no_dimensional_offcut_inventory_model"


@dataclass(frozen=True)
class SheetSourceCandidate:
    source_type: str
    material_code: str
    width_mm: float
    height_mm: float
    thickness_mm: float | None = None
    inventory_item_id: str | None = None
    condition: str | None = None
    location: str | None = None
    source: str = "material_profile"

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "source_type": self.source_type,
            "material_code": self.material_code,
            "width_mm": self.width_mm,
            "height_mm": self.height_mm,
            "source": self.source,
        }
        if self.thickness_mm is not None:
            payload["thickness_mm"] = self.thickness_mm
        if self.inventory_item_id:
            payload["inventory_item_id"] = self.inventory_item_id
        if self.condition:
            payload["condition"] = self.condition
        if self.location:
            payload["location"] = self.location
        return payload


def _piece_bbox_area_mm2(piece: Mapping[str, Any]) -> float:
    try:
        w = float(piece.get("width_mm") or 0)
        h = float(piece.get("height_mm") or 0)
    except (TypeError, ValueError):
        return 0.0
    if w <= 0 or h <= 0:
        return 0.0
    return w * h


def _pieces_fit_sheet(
    pieces: Sequence[Mapping[str, Any]],
    *,
    sheet_width_mm: float,
    sheet_height_mm: float,
) -> bool:
    """Minimal feasibility: total bbox area fits one sheet (no real nesting)."""
    if sheet_width_mm <= 0 or sheet_height_mm <= 0:
        return False
    sheet_area = sheet_width_mm * sheet_height_mm
    used = sum(_piece_bbox_area_mm2(p) for p in pieces)
    return used > 0 and used <= sheet_area


def build_sheet_source_candidates(
    *,
    material_code: str,
    thickness_mm: float | None,
    inventory_offcuts: Sequence[Mapping[str, Any]] | None = None,
    material_profile: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Build ordered source candidates without inventory writes."""
    candidates: list[dict[str, Any]] = []

    for raw in inventory_offcuts or []:
        if not isinstance(raw, Mapping):
            continue
        try:
            width = float(raw.get("width_mm") or 0)
            height = float(raw.get("height_mm") or 0)
        except (TypeError, ValueError):
            continue
        if width <= 0 or height <= 0:
            continue
        candidates.append(
            SheetSourceCandidate(
                source_type="inventory_offcut",
                material_code=str(raw.get("material_code") or material_code),
                width_mm=width,
                height_mm=height,
                thickness_mm=(
                    float(raw["thickness_mm"])
                    if raw.get("thickness_mm") is not None
                    else thickness_mm
                ),
                inventory_item_id=str(raw.get("inventory_item_id") or raw.get("id") or ""),
                condition=str(raw.get("condition") or "usable"),
                location=str(raw.get("location") or "") or None,
                source="inventory",
            ).to_dict()
        )

    profile = material_profile or {}
    try:
        new_w = float(profile.get("sheet_width_mm") or profile.get("width_mm") or 0)
        new_h = float(profile.get("sheet_height_mm") or profile.get("height_mm") or 0)
    except (TypeError, ValueError):
        new_w = 0.0
        new_h = 0.0
    if new_w > 0 and new_h > 0:
        candidates.append(
            SheetSourceCandidate(
                source_type="new_sheet",
                material_code=material_code,
                width_mm=new_w,
                height_mm=new_h,
                thickness_mm=thickness_mm,
                source=str(profile.get("source") or "material_profile"),
            ).to_dict()
        )

    return candidates


def select_sheet_sources_for_pieces(
    pieces: Sequence[Mapping[str, Any]],
    sheet_sources: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Pick a minimal source plan for required pieces (foundation heuristic)."""
    offcuts = [s for s in sheet_sources if s.get("source_type") == "inventory_offcut"]
    new_sheets = [s for s in sheet_sources if s.get("source_type") == "new_sheet"]
    inventory_available = len(offcuts) > 0

    selected: list[dict[str, Any]] = []
    remaining = list(pieces)

    for offcut in offcuts:
        if not remaining:
            break
        if _pieces_fit_sheet(
            remaining,
            sheet_width_mm=float(offcut.get("width_mm") or 0),
            sheet_height_mm=float(offcut.get("height_mm") or 0),
        ):
            selected.append({**offcut, "selected": True, "covers_all_pieces": True})
            remaining = []
            break

    if remaining and new_sheets:
        selected.append({**new_sheets[0], "selected": True, "covers_all_pieces": True})

    return {
        "enabled": True,
        "mode": FOUNDATION_MODE,
        "selection_policy": SELECTION_POLICY,
        "inventory_offcuts_available": inventory_available,
        "inventory_integration_status": "deferred" if not inventory_available else "mock_only",
        "source_candidates": list(sheet_sources),
        "selected_sources": selected,
        "current_estimate_basis": (
            "inventory_offcut" if selected and selected[0].get("source_type") == "inventory_offcut"
            else "new_sheet_profile"
        ),
        "reason": None if inventory_available else INVENTORY_DEFERRED_REASON,
    }


def build_sheet_source_selection_summary(
    *,
    material_code: str,
    thickness_mm: float | None,
    pieces: Sequence[Mapping[str, Any]] | None = None,
    inventory_offcuts: Sequence[Mapping[str, Any]] | None = None,
    material_profile: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Public entry for nesting summaries — metadata only, no inventory truth."""
    candidates = build_sheet_source_candidates(
        material_code=material_code,
        thickness_mm=thickness_mm,
        inventory_offcuts=inventory_offcuts,
        material_profile=material_profile,
    )
    selection = select_sheet_sources_for_pieces(pieces or [], candidates)
    return {
        "status": FOUNDATION_MODE,
        "policy": SELECTION_POLICY,
        "inventory_offcuts_available": selection["inventory_offcuts_available"],
        "current_estimate_basis": selection["current_estimate_basis"],
        "inventory_integration_status": selection["inventory_integration_status"],
        "source_candidates": candidates,
        "selected_sources": selection["selected_sources"],
        "reason": selection.get("reason"),
    }


def attach_sheet_source_selection_to_summary(
    summary: MutableMapping[str, Any],
    *,
    role: str,
    material_code: str,
    thickness_mm: float | None,
    pieces: Sequence[Mapping[str, Any]] | None,
    material_profile: Mapping[str, Any] | None,
    inventory_offcuts: Sequence[Mapping[str, Any]] | None = None,
) -> None:
    """Attach per-role sheet source metadata to flat material nesting summary."""
    block = build_sheet_source_selection_summary(
        material_code=material_code,
        thickness_mm=thickness_mm,
        pieces=pieces,
        inventory_offcuts=inventory_offcuts,
        material_profile=material_profile,
    )
    block["role"] = role
    selections = summary.setdefault("sheet_source_selection", [])
    if isinstance(selections, list):
        selections.append(block)

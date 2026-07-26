"""Declarative component sold-scope requirements (generic, product-agnostic)."""

from __future__ import annotations

from dataclasses import dataclass, field

LED_MOUNT_SURFACE = "LED_MOUNT_SURFACE"


@dataclass(frozen=True)
class ComponentSoldRequirement:
    sold_code: str
    requires_calc: tuple[str, ...] = ()
    requires_capabilities: tuple[str, ...] = ()
    requires_sold: tuple[str, ...] = ()
    excludes: tuple[str, ...] = ()
    standalone_allowed: bool = True


SLICE1_COMPONENT_REQUIREMENTS: dict[str, ComponentSoldRequirement] = {
    "FACE": ComponentSoldRequirement(
        sold_code="FACE",
        requires_calc=("GEOMETRY", "FACE_AREA"),
        standalone_allowed=True,
    ),
    "RETURN-CANT": ComponentSoldRequirement(
        sold_code="RETURN-CANT",
        requires_calc=("GEOMETRY", "PERIMETER"),
        standalone_allowed=True,
    ),
    "BACK": ComponentSoldRequirement(
        sold_code="BACK",
        requires_calc=("GEOMETRY", "FACE_AREA"),
        standalone_allowed=True,
    ),
    "LIGHTING": ComponentSoldRequirement(
        sold_code="LIGHTING",
        requires_calc=("GEOMETRY", "FACE_AREA"),
        requires_capabilities=(LED_MOUNT_SURFACE,),
        standalone_allowed=True,
    ),
    "ELECTRICAL": ComponentSoldRequirement(
        sold_code="ELECTRICAL",
        requires_calc=("GEOMETRY", "LED_COUNT"),
        excludes=("LIGHTING",),
        standalone_allowed=True,
    ),
}

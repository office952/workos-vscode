"""Build volumetric flat-material handoff blocks for quote/order snapshots."""

from __future__ import annotations

from typing import Any, Mapping

from sqlalchemy.ext.asyncio import AsyncSession

from services.flat_material_nesting_summary_service import build_flat_material_nesting_summary
from services.flat_material_offcut_foundation import enrich_handoff_with_offcut_foundation
from services.flat_material_profile_resolver import (
    load_registry_row_for_material_code,
    resolve_plexiglass_face_material_code,
)
from services.volumetric_face_vinyl_service import build_face_vinyl_handoff_for_quote
from services.volumetric_forex_backing_nesting_service import (
    DEFAULT_FOREX_MATERIAL_CODE,
    build_forex_backing_nesting_for_quote,
)
from services.volumetric_plexiglass_face_nesting_service import (
    build_plexiglass_face_nesting_for_quote,
)


async def build_volumetric_flat_material_handoff(
    db: AsyncSession,
    quote_input: Mapping[str, Any],
    *,
    product_spec: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return face vinyl + sheet nesting blocks, summary, and offcut foundation."""
    plexi_code = resolve_plexiglass_face_material_code(quote_input, product_spec)
    plexi_registry = await load_registry_row_for_material_code(db, plexi_code)
    forex_registry = await load_registry_row_for_material_code(db, DEFAULT_FOREX_MATERIAL_CODE)

    face_vinyl_handoff = build_face_vinyl_handoff_for_quote(
        quote_input,
        product_spec=product_spec,
    )
    plexiglass_face_nesting = build_plexiglass_face_nesting_for_quote(
        quote_input,
        product_spec=product_spec,
        registry_row=plexi_registry,
    )
    forex_backing_nesting = build_forex_backing_nesting_for_quote(
        quote_input,
        product_spec=product_spec,
        registry_row=forex_registry,
    )
    flat_material_nesting_summary = build_flat_material_nesting_summary(
        face_vinyl_handoff=face_vinyl_handoff,
        plexiglass_face_nesting=plexiglass_face_nesting,
        forex_backing_nesting=forex_backing_nesting,
    )

    offcut_meta: dict[str, Any] = {}
    enrich_handoff_with_offcut_foundation(
        offcut_meta,
        plexiglass_face_nesting=plexiglass_face_nesting,
        forex_backing_nesting=forex_backing_nesting,
    )

    return {
        "face_vinyl_handoff": face_vinyl_handoff,
        "plexiglass_face_nesting": plexiglass_face_nesting,
        "forex_backing_nesting": forex_backing_nesting,
        "flat_material_nesting_summary": flat_material_nesting_summary,
        **offcut_meta,
    }

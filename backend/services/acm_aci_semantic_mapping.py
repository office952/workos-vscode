"""Central ACI color → production path semantic mapping for AcmPanel DXF.

Owner golden DXFs use a single layer (`Layer 1`); semantics are encoded in ACI color.
Pricing must not own or duplicate this map.

ArtCAM owner settings (2026-07-23):
- black outer closed path = Cut outside → CUT (Decupare)
- red lines = V-groove along line → V_GROOVE_L1 / L2
Docs: docs/architecture/ACM_ARTCAM_DXF_OWNER_GOLDEN.md
"""

from __future__ import annotations

from typing import Literal

AcmPathSemantic = Literal["CUT", "V_GROOVE_L1", "V_GROOVE_L2", "UNKNOWN"]

ACM_ACI_SEMANTIC_MAPPING_VERSION = "acm_aci_semantic_mapping_v1"
ACM_ACI_SEMANTIC_MAPPING_SOURCE = (
    "owner_golden_dxf_2026-07-20:un-pliu.dxf+2-pliuri-100x30.dxf"
)

# Observed ACI colors on golden fixtures (Layer 1, SPLINE entities).
# 256 = ByLayer (used as CUT on single-fold golden)
# 250 = CUT closed outer on double-fold golden
# 1   = red → V-groove L1
# 242 = V-groove L2
_ACI_TO_SEMANTIC: dict[int, AcmPathSemantic] = {
    256: "CUT",
    250: "CUT",
    1: "V_GROOVE_L1",
    242: "V_GROOVE_L2",
}


def classify_aci_color(aci_color: int | None) -> AcmPathSemantic:
    """Map ACI color to path semantic. Unknown → UNKNOWN (never auto-bucket into CUT/V)."""
    if aci_color is None:
        return "UNKNOWN"
    try:
        code = int(aci_color)
    except (TypeError, ValueError):
        return "UNKNOWN"
    return _ACI_TO_SEMANTIC.get(code, "UNKNOWN")


def known_aci_colors() -> dict[int, AcmPathSemantic]:
    return dict(_ACI_TO_SEMANTIC)


def mapping_metadata() -> dict[str, object]:
    return {
        "version": ACM_ACI_SEMANTIC_MAPPING_VERSION,
        "source": ACM_ACI_SEMANTIC_MAPPING_SOURCE,
        "aci_to_semantic": {str(k): v for k, v in sorted(_ACI_TO_SEMANTIC.items())},
        "layer_name_dependency": False,
        "notes": (
            "Golden owner DXFs place all entities on 'Layer 1'. "
            "Semantic class is ACI color only for mapping version v1. "
            "ArtCAM: black Cut outside → CUT; red V-groove along line → V_GROOVE_*."
        ),
    }

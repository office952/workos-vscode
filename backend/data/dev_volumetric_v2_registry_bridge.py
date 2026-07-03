"""Step 8 dev bridge — interim volumetric v2 material rates for local freeze QA.

NOT the official Pricing Registry (Step 7I). Merged into EstimatedInternalCost
``_load_pricing_context`` only in local/development/test environments when DB
rows lack ``unit_cost``. Mirrors pytest ``SAMPLE_RATES`` / ``INVENTORY_CATALOG``.
"""

from __future__ import annotations

# RON unit costs — reference-only dev bridge until inventory registry is complete.
DEV_BRIDGE_MATERIAL_RATES: dict[str, float] = {
    "MAT-SABLON-MONTAJ": 8.0,
    "MAT-SABLON-HARTIE": 2.0,
    "MAT-LED-MODULE": 0.5,
    "MAT-LED-PSU-12V-100W": 45.0,
    "MAT-LED-PSU-12V-60W": 30.0,
    "MAT-LED-PSU-12V-160W": 55.0,
    "MAT-LED-PSU-12V-200W": 65.0,
    "MAT-PROFIL-LATERAL-LITERE-60MM": 3.0,
    "MAT-PROFIL-LATERAL-LITERE-30MM": 2.0,
    "MAT-PROFIL-LATERAL-LITERE-80MM": 4.0,
    "MAT-PROFIL-LATERAL-LITERE-100MM": 5.0,
    "MAT-PROFIL-LATERAL-LITERE": 3.0,
    # Linked-module aggregate shorthand codes (dev bridge until dossier codes normalized)
    "MAT-PROFIL-LATERAL-LITERE-30": 2.0,
    "MAT-PROFIL-LATERAL-LITERE-60": 3.0,
    "MAT-PROFIL-LATERAL-LITERE-80": 4.0,
    "MAT-PROFIL-LATERAL-LITERE-100": 5.0,
    "MAT-PROFIL-LATERAL-LITERE-10": 2.5,
    "MAT-ORACAL-651": 9.0,
    "MAT-ACP-FATA-LITERE": 15.0,
    "MAT-SPATE-PVC-LITERE": 8.0,
    "MAT-ADEZIV-CANT-LITERE": 4.0,
    "MAT-VOPSEA-RAL": 10.0,
    "MAT-VINYL-PRINT": 5.0,
    "MAT-CONSUMABILE-MONTAJ": 2.0,
    "MAT-CABLU-MYYUP-2X075": 3.0,
    "MAT-PREMOUNT-BAR-STEEL": 12.0,
    "MAT-PREMOUNT-BAR-ALUMINUM": 11.0,
}

DEV_BRIDGE_SOURCE = "dev_volumetric_v2_registry_bridge:step8_qa"

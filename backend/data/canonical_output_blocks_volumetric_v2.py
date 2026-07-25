"""Canonical output blocks for TPL-VOLUMETRIC-LETTERS_v2 — in-code, not dossier-backed."""

from __future__ import annotations

from typing import Any

CANONICAL_OUTPUT_BLOCKS_V2: dict[str, Any] = {
    "blocks": [
        {
            "block_id": "letters-desc-01",
            "block_type": "product_description",
            "title": "Descriere Litere Volumetrice",
            "document_type": "offer",
            "audience": "client",
            "approval_status": "approved",
            "template_text": (
                "Litere volumetrice 3D {{product_name}} — față plexiglas 3mm PMMA - opal, "
                "bordură profil aluminiu, spate Forex 10 mm, iluminare LED opțională."
            ),
            "variables": [
                {
                    "name": "product_name",
                    "source_field": "identity.product_name",
                    "required": True,
                    "missing_behavior": "render_with_warning",
                },
            ],
        },
        {
            "block_id": "letters-tech-01",
            "block_type": "technical_specifications",
            "title": "Specificații Tehnice Litere Volumetrice",
            "document_type": "production_sheet",
            "audience": "internal",
            "approval_status": "approved",
            "template_text": "Față: plexiglas 3mm PMMA - opal; Bordură: profil aluminiu; Spate: Forex 10 mm; LED opțional.",
            "variables": [],
        },
    ]
}

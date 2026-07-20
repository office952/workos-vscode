"""Canonical display names and compatibility notes for inventory material seeds.

Codes are stable for CostEngine — only `name` / `source_notes` clarify identity.
See docs/architecture/MATERIAL_CANONICAL_NAMING_AND_ALIASES.md
"""

from __future__ import annotations

from typing import Dict, TypedDict


class CanonicalMaterialNaming(TypedDict):
    code: str
    canonical_name: str
    source_notes: str


_LEGACY_CODE_NOTE = "Cod operațional păstrat pentru compatibilitate CostEngine — fără redenumire."

# Registry codes → canonical display + notes (new inserts / owner patch seeds).
CANONICAL_MATERIAL_NAMING: Dict[str, CanonicalMaterialNaming] = {
    "MAT-ACP-3MM": {
        "code": "MAT-ACP-3MM",
        "canonical_name": "Panou compozit aluminiu (ACM/ACP) 3 mm — legacy alias",
        "source_notes": (
            "LEGACY ALIAS — nu este a doua opțiune tehnică/pricing echivalentă. "
            "Preferred/canonical SKU: MAT-ACM-BOND-3MM. "
            "Păstrat pentru compatibilitate CostEngine/legacy seeds; fără ștergere și fără migrare distructivă. "
            "Aliasuri populare: ACP, Dibond, Alucobond, bond. "
            f"{_LEGACY_CODE_NOTE}"
        ),
    },
    "MAT-ACM-BOND-PANEL": {
        "code": "MAT-ACM-BOND-PANEL",
        "canonical_name": "Panou compozit aluminiu (ACM/ACP) — rezolvare grosime",
        "source_notes": (
            "Alias template — rezolvat la quote time către MAT-ACM-BOND-3MM / 4MM. "
            "Preferred thickness SKU: MAT-ACM-BOND-3MM. "
            "Nu spate literă Forex. Identitate completă ACM necesită grosime folie Al + finisaj."
        ),
    },
    "MAT-ACM-BOND-3MM": {
        "code": "MAT-ACM-BOND-3MM",
        "canonical_name": "Panou compozit aluminiu (ACM/ACP) 3 mm",
        "source_notes": (
            "CANONICAL / PREFERRED SKU pentru panou ACM 3 mm (AcmPanel / boxed mounting). "
            "MAT-ACP-3MM este legacy alias — nu afișa ca alternativă tehnică echivalentă. "
            "Aliasuri populare: Dibond, Alucobond, bond. "
            "Grosime folie aluminiu (ex. 0.21 vs 0.30 mm) = SKU distinct la registry matur. "
            f"{_LEGACY_CODE_NOTE}"
        ),
    },
    "MAT-ACM-BOND-4MM": {
        "code": "MAT-ACM-BOND-4MM",
        "canonical_name": "Panou compozit aluminiu (ACM/ACP) 4 mm",
        "source_notes": (
            "Variantă grosime 4 mm. Aliasuri: Dibond, Alucobond, bond. "
            "Preț owner review până la confirmare. "
            f"{_LEGACY_CODE_NOTE}"
        ),
    },
    "MAT-ACP-FATA-LITERE": {
        "code": "MAT-ACP-FATA-LITERE",
        "canonical_name": "PMMA / plexiglas acrilic 3 mm — față litere",
        "source_notes": (
            "Material brut: PMMA/plexiglas. Cod legacy conține ACP — nu este panou ACM/Bond. "
            "Utilizare: față litere volumetrice (letter_face_area). "
            "Finisaj opțional: Oracal/vinyl separat. "
            f"{_LEGACY_CODE_NOTE}"
        ),
    },
    "MAT-SPATE-PVC-LITERE": {
        "code": "MAT-SPATE-PVC-LITERE",
        "canonical_name": "PVC expandat 10 mm",
        "source_notes": (
            "Material brut: PVC expandat 10 mm. Alias popular: Forex 10 mm. "
            "Utilizare: spate litere volumetrice — nu panou ACM. "
            f"{_LEGACY_CODE_NOTE}"
        ),
    },
    "MAT-SABLON-MONTAJ": {
        "code": "MAT-SABLON-MONTAJ",
        "canonical_name": "PVC expandat 3 mm — șablon montaj",
        "source_notes": (
            "Material brut: PVC expandat 3 mm. Alias: Forex 3 mm. "
            "Utilizare: șablon montaj litere (mounting_template_area_m2). CNC separat. "
            f"{_LEGACY_CODE_NOTE}"
        ),
    },
    "MAT-SABLON-HARTIE": {
        "code": "MAT-SABLON-HARTIE",
        "canonical_name": "Șablon hârtie",
        "source_notes": (
            "Material consumabil: șablon hârtie pentru montaj litere. "
            "Utilizare: mounting_template_material_type=paper; cantitate din mounting_template_area_m2. "
            "Fără CNC Forex. "
            f"{_LEGACY_CODE_NOTE}"
        ),
    },
    "MAT-PREMOUNT-BAR-STEEL": {
        "code": "MAT-PREMOUNT-BAR-STEEL",
        "canonical_name": "Țeavă pătrată oțel 30×30×1.5 mm",
        "source_notes": (
            "Material brut: țeavă/profil oțel 30×30×1.5. "
            "Utilizare legacy în cod: bare premontaj litere (steel_bars). "
            "Țintă viitoare cod: MAT-STEEL-SQUARE-TUBE-30X30X1_5 — necesită migrare alias. "
            f"{_LEGACY_CODE_NOTE}"
        ),
    },
    "MAT-PREMOUNT-BAR-ALUMINUM": {
        "code": "MAT-PREMOUNT-BAR-ALUMINUM",
        "canonical_name": "Țeavă pătrată aluminiu 30×30×1.5 mm",
        "source_notes": (
            "Material brut: profil/țeavă aluminiu 30×30×1.5. "
            "Utilizare legacy: bare premontaj litere (aluminum_bars). "
            f"{_LEGACY_CODE_NOTE}"
        ),
    },
    "MAT-ORACAL-651": {
        "code": "MAT-ORACAL-651",
        "canonical_name": "Folie autocolantă PVC — Oracal 651",
        "source_notes": (
            "Brand: Oracal. Serie: 651. Material generic: folie autocolantă PVC. "
            "Utilizare: finisaj față litere (opțional). "
            f"{_LEGACY_CODE_NOTE}"
        ),
    },
    "MAT-VINYL-PRINT": {
        "code": "MAT-VINYL-PRINT",
        "canonical_name": "Folie autocolantă PVC — print față litere",
        "source_notes": (
            "Material generic: folie autocolantă printabilă. "
            "Utilizare: finisaj față litere (printed_vinyl). "
            f"{_LEGACY_CODE_NOTE}"
        ),
    },
    "MAT-VINYL-PRINT-LAMINATED": {
        "code": "MAT-VINYL-PRINT-LAMINATED",
        "canonical_name": "Folie autocolantă PVC — print + laminare față litere",
        "source_notes": (
            "Material generic: folie autocolantă print + laminare. "
            "Utilizare: finisaj față litere. "
            f"{_LEGACY_CODE_NOTE}"
        ),
    },
    "MAT-PLEXI-TRANSP-3MM": {
        "code": "MAT-PLEXI-TRANSP-3MM",
        "canonical_name": "PMMA / plexiglas acrilic transparent 3 mm",
        "source_notes": "Aliasuri: Plexiglas, plexi, Stiplex, acril.",
    },
    "MAT-PLEXI-TRANSP-5MM": {
        "code": "MAT-PLEXI-TRANSP-5MM",
        "canonical_name": "PMMA / plexiglas acrilic transparent 5 mm",
        "source_notes": "Aliasuri: Plexiglas, plexi, Stiplex, acril.",
    },
    "MAT-PLEXI-ALB-3MM": {
        "code": "MAT-PLEXI-ALB-3MM",
        "canonical_name": "PMMA / plexiglas acrilic alb 3 mm",
        "source_notes": "Aliasuri: Plexiglas, plexi, acril.",
    },
    "MAT-PLEXI-COLOR-3MM": {
        "code": "MAT-PLEXI-COLOR-3MM",
        "canonical_name": "PMMA / plexiglas acrilic colorat 3 mm",
        "source_notes": "Aliasuri: Plexiglas, plexi, acril.",
    },
    "MAT-PLEXI-OPAL-3MM": {
        "code": "MAT-PLEXI-OPAL-3MM",
        "canonical_name": "PMMA / plexiglas acrilic opal 3 mm",
        "source_notes": "Variantă opal/difuzor. Aliasuri: Plexiglas, plexi.",
    },
    "MAT-PLEXI-OPAL-10MM": {
        "code": "MAT-PLEXI-OPAL-10MM",
        "canonical_name": "PMMA / plexiglas acrilic opal 10 mm",
        "source_notes": "Variantă opal/relief. Aliasuri: Plexiglas, plexi.",
    },
    "MAT-PLEXI-TRANSP-10MM": {
        "code": "MAT-PLEXI-TRANSP-10MM",
        "canonical_name": "PMMA / plexiglas acrilic transparent 10 mm",
        "source_notes": "Aliasuri: Plexiglas, plexi, acril.",
    },
    "MAT-PROFIL-LATERAL-LITERE-30MM": {
        "code": "MAT-PROFIL-LATERAL-LITERE-30MM",
        "canonical_name": "Profil aluminiu return/cant 30 mm",
        "source_notes": (
            "Material brut: profil aluminiu. Utilizare: cant lateral litere volumetrice. "
            f"{_LEGACY_CODE_NOTE}"
        ),
    },
    "MAT-PROFIL-LATERAL-LITERE-60MM": {
        "code": "MAT-PROFIL-LATERAL-LITERE-60MM",
        "canonical_name": "Profil aluminiu return/cant 60 mm",
        "source_notes": "Utilizare: cant lateral litere volumetrice.",
    },
    "MAT-PROFIL-LATERAL-LITERE-80MM": {
        "code": "MAT-PROFIL-LATERAL-LITERE-80MM",
        "canonical_name": "Profil aluminiu return/cant 80 mm",
        "source_notes": "Utilizare: cant lateral litere volumetrice.",
    },
    "MAT-PROFIL-LATERAL-LITERE-100MM": {
        "code": "MAT-PROFIL-LATERAL-LITERE-100MM",
        "canonical_name": "Profil aluminiu return/cant 100 mm",
        "source_notes": "Utilizare: cant lateral litere volumetrice.",
    },
}


def canonical_name_for_code(code: str, fallback: str) -> str:
    entry = CANONICAL_MATERIAL_NAMING.get(code)
    return entry["canonical_name"] if entry else fallback


def source_notes_for_code(code: str, existing: str | None = None) -> str | None:
    entry = CANONICAL_MATERIAL_NAMING.get(code)
    if not entry:
        return existing
    notes = entry["source_notes"]
    if existing and existing.strip() and existing.strip() not in notes:
        return f"{notes} {existing.strip()}"
    return notes

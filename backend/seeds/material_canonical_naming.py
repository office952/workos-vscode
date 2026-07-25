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

# Owner lock 2026-07-23 — letter-face plexi stock display (exact string).
LETTERS_FACE_PLEXI_3MM_OPAL_DISPLAY_NAME = "plexiglas 3mm PMMA - opal"

# Owner lock 2026-07-23 — letter-face finish materials (exact display strings).
LETTERS_FACE_FINISH_ORACAL_8500_DISPLAY_NAME = "Oracal 8500"
LETTERS_FACE_FINISH_ORACAL_641_DISPLAY_NAME = "Oracal 641"
LETTERS_FACE_FINISH_ORACAL_651_DISPLAY_NAME = "Oracal 651"
LETTERS_FACE_FINISH_PRINT_LAMINATED_DISPLAY_NAME = "Printat / Laminat"

# Owner lock 2026-07-23 — letter Sistem LED materials (exact display strings).
LETTERS_LED_MODULE_DISPLAY_NAME = "Modul LED 12V"
LETTERS_LED_STRIP_DISPLAY_NAME = "Bandă LED 12V"
LETTERS_LED_PSU_SELECTOR_DISPLAY_NAME = "Sursă LED 12V — alege puterea (60/100/160/200 W)"

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
        "canonical_name": LETTERS_FACE_PLEXI_3MM_OPAL_DISPLAY_NAME,
        "source_notes": (
            "Owner display lock 2026-07-23: exact name «plexiglas 3mm PMMA - opal». "
            "Material brut: PMMA/plexiglas opal 3 mm. Cod legacy conține ACP — nu este panou ACM/Bond. "
            "Utilizare: față litere volumetrice (letter_face_area). "
            "Finisaj opțional: Oracal/vinyl separat (FINISH). "
            f"{_LEGACY_CODE_NOTE}"
        ),
    },
    "MAT-SPATE-PVC-LITERE": {
        "code": "MAT-SPATE-PVC-LITERE",
        "canonical_name": "Forex 10 mm",
        "source_notes": (
            "Owner display lock 2026-07-23. Material brut: PVC expandat 10 mm (alias Forex). "
            "Pas structură: Capac spate. Nu panou ACM, nu șablon montaj 3 mm. "
            f"{_LEGACY_CODE_NOTE}"
        ),
    },
    "MAT-LED-MODULE": {
        "code": "MAT-LED-MODULE",
        "canonical_name": LETTERS_LED_MODULE_DISPLAY_NAME,
        "source_notes": (
            "Owner display lock 2026-07-23. Standard Sistem LED litere (led_modules). "
            "Montaj pe spate Forex. Nu bandă LED. "
            f"{_LEGACY_CODE_NOTE}"
        ),
    },
    "MAT-LED-STRIP": {
        "code": "MAT-LED-STRIP",
        "canonical_name": LETTERS_LED_STRIP_DISPLAY_NAME,
        "source_notes": (
            "Owner display lock 2026-07-23. Alternativă Sistem LED (led_strip). "
            "Nu înlocuiește Modul LED 12V ca standard. "
            f"{_LEGACY_CODE_NOTE}"
        ),
    },
    "MAT-LED-PSU-12V": {
        "code": "MAT-LED-PSU-12V",
        "canonical_name": LETTERS_LED_PSU_SELECTOR_DISPLAY_NAME,
        "source_notes": (
            "Owner display lock 2026-07-23. Selector template — fără preț unic. "
            "Rezolvă variante 60/100/160/200 W via selected_psu_watts. "
            "Nu multiplica prețul cu valoarea W. "
            f"{_LEGACY_CODE_NOTE}"
        ),
    },
    "MAT-LED-PSU-12V-60W": {
        "code": "MAT-LED-PSU-12V-60W",
        "canonical_name": "Sursă LED 12V 60W",
        "source_notes": (
            "Owner display lock 2026-07-23. Varianta PSU pe clasă de putere (EUR/buc). "
            f"{_LEGACY_CODE_NOTE}"
        ),
    },
    "MAT-LED-PSU-12V-100W": {
        "code": "MAT-LED-PSU-12V-100W",
        "canonical_name": "Sursă LED 12V 100W",
        "source_notes": (
            "Owner display lock 2026-07-23. Varianta PSU pe clasă de putere (EUR/buc). "
            f"{_LEGACY_CODE_NOTE}"
        ),
    },
    "MAT-LED-PSU-12V-160W": {
        "code": "MAT-LED-PSU-12V-160W",
        "canonical_name": "Sursă LED 12V 160W",
        "source_notes": (
            "Owner display lock 2026-07-23. Varianta PSU pe clasă de putere (EUR/buc). "
            f"{_LEGACY_CODE_NOTE}"
        ),
    },
    "MAT-LED-PSU-12V-200W": {
        "code": "MAT-LED-PSU-12V-200W",
        "canonical_name": "Sursă LED 12V 200W",
        "source_notes": (
            "Owner display lock 2026-07-23. Varianta PSU pe clasă de putere (EUR/buc). "
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
    "MAT-ORACAL-641": {
        "code": "MAT-ORACAL-641",
        "canonical_name": LETTERS_FACE_FINISH_ORACAL_641_DISPLAY_NAME,
        "source_notes": (
            "Owner display lock 2026-07-23. Brand: Oracal. Serie: 641. "
            "Utilizare: finisaj față litere (opțional). "
            f"{_LEGACY_CODE_NOTE}"
        ),
    },
    "MAT-ORACAL-651": {
        "code": "MAT-ORACAL-651",
        "canonical_name": LETTERS_FACE_FINISH_ORACAL_651_DISPLAY_NAME,
        "source_notes": (
            "Owner display lock 2026-07-23. Brand: Oracal. Serie: 651. "
            "Utilizare: finisaj față litere (opțional). "
            f"{_LEGACY_CODE_NOTE}"
        ),
    },
    "MAT-ORACAL-8500": {
        "code": "MAT-ORACAL-8500",
        "canonical_name": LETTERS_FACE_FINISH_ORACAL_8500_DISPLAY_NAME,
        "source_notes": (
            "Owner display lock 2026-07-23. Brand: Oracal. Serie: 8500 (translucent stock). "
            "Utilizare: finisaj față litere (opțional). "
            f"{_LEGACY_CODE_NOTE}"
        ),
    },
    "MAT-VINYL-PRINT": {
        "code": "MAT-VINYL-PRINT",
        "canonical_name": "Folie autocolantă PVC — print față litere",
        "source_notes": (
            "Material generic: folie autocolantă printabilă (fără laminare combinată). "
            "Utilizare: finisaj față litere (printed_vinyl). "
            f"{_LEGACY_CODE_NOTE}"
        ),
    },
    "MAT-VINYL-PRINT-LAMINATED": {
        "code": "MAT-VINYL-PRINT-LAMINATED",
        "canonical_name": LETTERS_FACE_FINISH_PRINT_LAMINATED_DISPLAY_NAME,
        "source_notes": (
            "Owner display lock 2026-07-23. Print + laminare combinat pe față. "
            "Utilizare: finisaj față litere / artwork. "
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
        "canonical_name": LETTERS_FACE_PLEXI_3MM_OPAL_DISPLAY_NAME,
        "source_notes": (
            "Same owner display lock as MAT-ACP-FATA-LITERE (2026-07-23). "
            "Variantă opal/difuzor 3 mm. Aliasuri: Plexiglas, plexi, PMMA."
        ),
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
    "MAT-PROFIL-LATERAL-LITERE": {
        "code": "MAT-PROFIL-LATERAL-LITERE",
        "canonical_name": "Volum aluminiu — alege lățimea (30/60/80/100)",
        "source_notes": (
            "Owner display lock 2026-07-23. Selector template — fără unit_cost unic. "
            "Rezolvă la MAT-PROFIL-LATERAL-LITERE-{30|60|80|100}MM via return_depth_mm. "
            "Nu ACM, nu premontaj, nu profil casetă. "
            f"{_LEGACY_CODE_NOTE}"
        ),
    },
    "MAT-PROFIL-LATERAL-LITERE-30MM": {
        "code": "MAT-PROFIL-LATERAL-LITERE-30MM",
        "canonical_name": "Volum aluminiu 30 mm",
        "source_notes": (
            "Owner display lock 2026-07-23. Profil Al 0.6 mm — lățime/adâncime 30 mm. "
            "Pas structură: Volum aluminiu (RETURN-CANT). "
            f"{_LEGACY_CODE_NOTE}"
        ),
    },
    "MAT-PROFIL-LATERAL-LITERE-60MM": {
        "code": "MAT-PROFIL-LATERAL-LITERE-60MM",
        "canonical_name": "Volum aluminiu 60 mm",
        "source_notes": (
            "Owner display lock 2026-07-23. Profil Al 0.6 mm — lățime/adâncime 60 mm. "
            "Pas structură: Volum aluminiu (RETURN-CANT)."
        ),
    },
    "MAT-PROFIL-LATERAL-LITERE-80MM": {
        "code": "MAT-PROFIL-LATERAL-LITERE-80MM",
        "canonical_name": "Volum aluminiu 80 mm",
        "source_notes": (
            "Owner display lock 2026-07-23. Profil Al 0.6 mm — lățime/adâncime 80 mm. "
            "Pas structură: Volum aluminiu (RETURN-CANT)."
        ),
    },
    "MAT-PROFIL-LATERAL-LITERE-100MM": {
        "code": "MAT-PROFIL-LATERAL-LITERE-100MM",
        "canonical_name": "Volum aluminiu 100 mm",
        "source_notes": (
            "Owner display lock 2026-07-23. Profil Al 0.6 mm — lățime/adâncime 100 mm. "
            "Pas structură: Volum aluminiu (RETURN-CANT)."
        ),
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

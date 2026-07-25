"""CNC processable badge — shared capability identifier (not decorative UI).

Carriers (v1 — narrow):
- Material: MAT-ACP-FATA-LITERE (plexiglas 3mm PMMA - opal)
- Machine: MCH-CNC-4020 (CNC 4020) only — not every cnc_router / polystyrene CNC

Frontend mirror: frontend/src/lib/cnc/cncProcessableBadge.ts
"""

from __future__ import annotations

import re
from typing import Final

CNC_PROCESSABLE_BADGE_LABEL: Final[str] = "CNC"
CNC_PROCESSABLE_BADGE_CODE: Final[str] = "BADGE-CNC-PROCESSABLE"
CNC_PROCESSABLE_BADGE_TITLE_RO: Final[str] = "Procesabil CNC"
CNC_PROCESSABLE_BADGE_MEANING_RO: Final[str] = (
    "Identificator de capacitate: plexiglas 3mm PMMA - opal (față litere) "
    "se prelucrează pe CNC 4020 — același badge pe material și pe acest utilaj."
)

CNC_PROCESSABLE_MATERIAL_CODES: Final[frozenset[str]] = frozenset({"MAT-ACP-FATA-LITERE"})
CNC_PROCESSABLE_MACHINE_CODES: Final[frozenset[str]] = frozenset({"MCH-CNC-4020"})

CNC_PROCESSABLE_LETTER_FACE_SERVICES: Final[tuple[str, ...]] = (
    "Debitare",
    "Șanfren / Canal",
)

_EXCLUDED_NAME = re.compile(r"POLISTIREN|POLYSTYRENE|FOAM|EPS", re.IGNORECASE)
_CNC_4020_NAME = re.compile(r"\bCNC\s*4020\b", re.IGNORECASE)


def _norm(value: str | None) -> str:
    return str(value or "").strip().upper().replace("-", "_")


def material_carries_cnc_processable_badge(material_code: str | None) -> bool:
    code = _norm(material_code).replace("_", "-")
    return any(_norm(entry).replace("_", "-") == code for entry in CNC_PROCESSABLE_MATERIAL_CODES)


def machine_carries_cnc_processable_badge(
    *,
    machine_type: str | None = None,
    machine_id: str | None = None,
    machine_name: str | None = None,
    workcenter_code: str | None = None,
) -> bool:
    """True only for CNC 4020 — never by broad type or shared workcenter."""
    del machine_type, workcenter_code  # intentionally unused — do not broaden match
    if _norm(machine_id) in {_norm(c) for c in CNC_PROCESSABLE_MACHINE_CODES}:
        return True
    name = str(machine_name or "").strip()
    if not name:
        return False
    upper = name.upper()
    if "MCH-CNC-4020" in upper or "MCH_CNC_4020" in upper:
        return True
    if _CNC_4020_NAME.search(name):
        return True
    if "CNC" in upper and "4020" in upper and not _EXCLUDED_NAME.search(name):
        return True
    return False

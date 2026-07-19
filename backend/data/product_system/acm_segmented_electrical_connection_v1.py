"""Shell-owned electrical connection management for segmented ACM/ACP assemblies.

Nested under finish_setup.segmented_background.electrical_connection_management.
Does not absorb letter-local LED/wiring truth. No pricing / task materialization.
"""

from __future__ import annotations

from typing import Any

ELECTRICAL_SCHEMA = "acm_segmented_electrical_connection_v1"
ELECTRICAL_CONTRACT_VERSION = "acm_segmented_electrical_connection/v1"

ELEC_STATUS_INACTIVE = "INACTIVE"
ELEC_STATUS_DRAFT = "DRAFT"
ELEC_STATUS_CONFIRMED = "CONFIRMED"

SUPPLY_DIRECT = "DIRECT_220V"
SUPPLY_SHARED = "SHARED_FROM_PANEL"
SUPPLY_NONE = "NO_LOCAL_220V"
SUPPLY_UNCONFIRMED = "UNCONFIRMED"

POSITION_TOP_LEFT = "TOP_LEFT"
POSITION_TOP_RIGHT = "TOP_RIGHT"
POSITION_BOTTOM_LEFT = "BOTTOM_LEFT"
POSITION_BOTTOM_RIGHT = "BOTTOM_RIGHT"
POSITION_TOP_CENTER = "TOP_CENTER"
POSITION_BOTTOM_CENTER = "BOTTOM_CENTER"
POSITION_LEFT_CENTER = "LEFT_CENTER"
POSITION_RIGHT_CENTER = "RIGHT_CENTER"
POSITION_CUSTOM = "CUSTOM"
POSITION_NONE = "NONE"

SERVICE_POSITIONS = frozenset(
    {
        POSITION_TOP_LEFT,
        POSITION_TOP_RIGHT,
        POSITION_BOTTOM_LEFT,
        POSITION_BOTTOM_RIGHT,
        POSITION_TOP_CENTER,
        POSITION_BOTTOM_CENTER,
        POSITION_LEFT_CENTER,
        POSITION_RIGHT_CENTER,
        POSITION_CUSTOM,
        POSITION_NONE,
    }
)

SUPPLY_MODES = frozenset(
    {SUPPLY_DIRECT, SUPPLY_SHARED, SUPPLY_NONE, SUPPLY_UNCONFIRMED}
)

CONN_LV_FEED = "LV_FEED"
CONN_INTERCONNECT = "INTERCONNECT"
CONN_OTHER = "OTHER"

MSG_ELEC_INDICATE_220V = "ELEC_INDICATE_220V"
MSG_ELEC_ROUTE_CABLES = "ELEC_ROUTE_CABLES"
MSG_ELEC_SHARED_FROM_PANEL = "ELEC_SHARED_FROM_PANEL"
MSG_ELEC_RESERVE = "ELEC_RESERVE"
MSG_ELEC_AFTER_ALIGNMENT = "ELEC_AFTER_ALIGNMENT"
MSG_ELEC_UNCONFIRMED = "ELEC_UNCONFIRMED"
MSG_ELEC_CONFIRMED = "ELEC_CONFIRMED"
MSG_ELEC_INVALID_PANEL = "ELEC_INVALID_PANEL"
MSG_ELEC_INVALID_SHARED = "ELEC_INVALID_SHARED"
MSG_ELEC_SELF_SHARED = "ELEC_SELF_SHARED"
MSG_ELEC_CUSTOM_NOTE = "ELEC_CUSTOM_NOTE"
MSG_ELEC_CONTRADICTION = "ELEC_CONTRADICTION"
MSG_ELEC_INVALID_CONNECTION = "ELEC_INVALID_CONNECTION"

OPERATOR_MESSAGES_RO: dict[str, str] = {
    MSG_ELEC_INDICATE_220V: "Indica unde este alimentarea de 220V pentru acest panou.",
    MSG_ELEC_ROUTE_CABLES: "Pregateste cablurile panoului spre pozitia de alimentare declarata.",
    MSG_ELEC_SHARED_FROM_PANEL: "Acest panou primeste alimentarea dintr-un alt panou al ansamblului.",
    MSG_ELEC_RESERVE: "Lasa rezerva de cablu pentru legatura finala dintre panouri.",
    MSG_ELEC_AFTER_ALIGNMENT: "Aceasta legatura se finalizeaza dupa alinierea panourilor.",
    MSG_ELEC_UNCONFIRMED: "Pozitia alimentarii nu este confirmata.",
    MSG_ELEC_CONFIRMED: "Configuratia electrica a ansamblului a fost confirmata.",
    MSG_ELEC_INVALID_PANEL: "Referinta de panou electrica este invalida.",
    MSG_ELEC_INVALID_SHARED: "Panoul sursa pentru alimentare partajata nu exista in ansamblu.",
    MSG_ELEC_SELF_SHARED: "Un panou nu poate primi alimentarea de la el insusi.",
    MSG_ELEC_CUSTOM_NOTE: "Pentru pozitie personalizata, adauga nota sau referinta de schita.",
    MSG_ELEC_CONTRADICTION: "Modul de alimentare si pozitia 220V sunt contradictorii.",
    MSG_ELEC_INVALID_CONNECTION: "Legatura inter-panou refera panouri invalide.",
}

POSITION_LABELS_RO: dict[str, str] = {
    POSITION_TOP_LEFT: "Stanga sus",
    POSITION_TOP_RIGHT: "Dreapta sus",
    POSITION_BOTTOM_LEFT: "Stanga jos",
    POSITION_BOTTOM_RIGHT: "Dreapta jos",
    POSITION_TOP_CENTER: "Centru sus",
    POSITION_BOTTOM_CENTER: "Centru jos",
    POSITION_LEFT_CENTER: "Centru stanga",
    POSITION_RIGHT_CENTER: "Centru dreapta",
    POSITION_CUSTOM: "Pozitie dupa schita",
    POSITION_NONE: "Fara punct local 220V",
}

SUPPLY_LABELS_RO: dict[str, str] = {
    SUPPLY_DIRECT: "220V direct pe panou",
    SUPPLY_SHARED: "Alimentare din alt panou",
    SUPPLY_NONE: "Fara 220V local",
    SUPPLY_UNCONFIRMED: "Neconfirmat",
}


def operator_message(code: str) -> str:
    return OPERATOR_MESSAGES_RO.get(code, code)


def electrical_meta() -> dict[str, Any]:
    return {
        "schema": ELECTRICAL_SCHEMA,
        "contract_version": ELECTRICAL_CONTRACT_VERSION,
        "ownership": "ACM_ACP_SHELL_ASSEMBLY",
        "letters_electrical": "EXTERNAL — letter-local LED/wiring unchanged",
        "no_psu_sizing": True,
        "no_pricing": True,
        "no_task_materialization": True,
        "future_task_intent_authority": "INFORMATIONAL_ONLY",
    }

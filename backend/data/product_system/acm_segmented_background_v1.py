"""ACM/ACP segmented background assembly contract (shell-owned).

One SUPPORT_CONTOUR remains the assembly envelope (MAX_ONE).
Physical panels nest under the shell — they are not separate products.

SVG Analyzer may propose; operator confirmation is authority.
PROPOSED / INACTIVE → zero ProductDefinition / Aggregate downstream effects.
"""

from __future__ import annotations

from typing import Any

CONTRACT_VERSION = "acm_segmented_background/v1"
SCHEMA = "acm_segmented_background_v1"
HOST_SHELL_TEMPLATE = "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1"

# Assembly confirmation / mode
STATUS_SINGLE_PANEL = "SINGLE_PANEL"
STATUS_PROPOSED = "PROPOSED"
STATUS_CONFIRMED = "CONFIRMED"
STATUS_INACTIVE = "INACTIVE"

# Element construction types (shell-facing classification; letters keep own construction)
CONSTRUCTION_APPLIED_VOLUMETRIC = "APPLIED_VOLUMETRIC_LETTER"
CONSTRUCTION_SIMPLE_APPLIED = "SIMPLE_APPLIED"
CONSTRUCTION_CUTOUT = "CUTOUT"
CONSTRUCTION_ACRYLIC_INSERT = "ACRYLIC_INSERT"

# Crossing classification
CROSSING_NONE = "NONE"
CROSSING_APPLIED_VOLUMETRIC_JOINT = "APPLIED_VOLUMETRIC_JOINT"
CROSSING_CUTOUT_JOINT = "CUTOUT_JOINT"
CROSSING_ACRYLIC_INSERT_JOINT = "ACRYLIC_INSERT_JOINT"

# Mount strategy (interface context only — does not absorb letter process)
MOUNT_STANDARD = "STANDARD"
MOUNT_TWO_STAGE_JOINT = "TWO_STAGE_JOINT_CROSSING"

# Operator message codes → Romanian copy (never show enums to operators)
MSG_SEGMENTATION_PROPOSAL = "SEGMENTATION_PROPOSAL"
MSG_GRAPHIC_DISTRIBUTED = "GRAPHIC_DISTRIBUTED"
MSG_APPLIED_CROSSING = "APPLIED_CROSSING_TWO_STAGE"
MSG_CUTOUT_CROSSING_BLOCKER = "CUTOUT_CROSSING_BLOCKER"
MSG_INSERT_CROSSING_BLOCKER = "INSERT_CROSSING_BLOCKER"
MSG_INVALID_PANEL_REF = "INVALID_PANEL_REF"
MSG_DUPLICATE_PANEL_ID = "DUPLICATE_PANEL_ID"
MSG_CROSSING_ON_SINGLE_PANEL = "CROSSING_ON_SINGLE_PANEL"

OPERATOR_MESSAGES_RO: dict[str, str] = {
    MSG_SEGMENTATION_PROPOSAL: (
        "Am gasit mai multe fundaluri apropiate care par sa formeze un singur ansamblu. "
        "Confirma daca sunt panouri ale aceluiasi fundal."
    ),
    MSG_GRAPHIC_DISTRIBUTED: (
        "Grafica este distribuita pe mai multe panouri. "
        "Confirma ordinea si continuitatea ansamblului."
    ),
    MSG_APPLIED_CROSSING: (
        "Aceasta litera trece peste imbinare si necesita montaj in doua etape."
    ),
    MSG_CUTOUT_CROSSING_BLOCKER: (
        "O litera sau un decupaj trece peste imbinarea dintre panouri. "
        "Muta imbinarea sau modifica grafica."
    ),
    MSG_INSERT_CROSSING_BLOCKER: (
        "O litera sau un decupaj trece peste imbinarea dintre panouri. "
        "Muta imbinarea sau modifica grafica."
    ),
    MSG_INVALID_PANEL_REF: "Referinta de panou lipseste sau este invalida. Verifica legatura elementului.",
    MSG_DUPLICATE_PANEL_ID: "Exista panouri cu acelasi identificator. Corecteaza identificatorii.",
    MSG_CROSSING_ON_SINGLE_PANEL: (
        "Un element este marcat ca trecand peste imbinare, dar exista un singur panou."
    ),
}

CUTOUT_LIKE_CONSTRUCTIONS = frozenset({CONSTRUCTION_CUTOUT, CONSTRUCTION_ACRYLIC_INSERT})
APPLIED_LIKE_CONSTRUCTIONS = frozenset(
    {CONSTRUCTION_APPLIED_VOLUMETRIC, CONSTRUCTION_SIMPLE_APPLIED}
)

SEGMENTATION_CAPABILITY = "segmented_background_assembly"


def operator_message(code: str) -> str:
    return OPERATOR_MESSAGES_RO.get(code, code)


def contract_meta() -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "contract_version": CONTRACT_VERSION,
        "host_component_template_code": HOST_SHELL_TEMPLATE,
        "support_contour_role": "ASSEMBLY_ENVELOPE_MAX_ONE",
        "panels_role": "PHYSICAL_MEMBERS_NESTED",
        "detection_authority": "PROPOSAL_ONLY",
        "confirmation_authority": "OPERATOR",
        "letters_ownership": "EXTERNAL — interface binding only",
        "no_auto_divide": True,
        "no_task_materialization": True,
        "no_pricing": True,
    }

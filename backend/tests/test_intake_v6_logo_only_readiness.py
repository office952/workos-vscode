"""Logo-only readiness stays candidate/non-offerable (owner policy).

Does not activate Logo root. Does not mutate DB/seeds.
Canonical letters readiness spine is covered elsewhere.
"""

from schemas.intake_v6 import (
    IntakeV6ArtworkFinish,
    IntakeV6FinishSetup,
    IntakeV6LayerRoleLayer,
    IntakeV6LayerRoleSetup,
    IntakeV6SvgSource,
    IntakeV6WorkspacePayload,
)
from services.intake_v6_workspace_service import _derive_readiness_status
from services.template_usage_mode_policy import (
    TPL_VOLUMETRIC_LOGO_V1,
    is_candidate_only_template,
    is_root_offerable_template,
)


def test_logo_only_candidate_unconfirmed_artwork_stays_not_offerable():
    payload = IntakeV6WorkspacePayload(
        product_binding={
            "template_code": "TPL-VOLUMETRIC-LETTERS_v2",
            "template_label": "Litere volumetrice",
            "product_family": "litere_volumetrice",
        },
        svg_source=IntakeV6SvgSource(
            file_name="logo.svg",
            file_size_bytes=943,
            file_hash="logo-source-hash",
            upload_status="analyzed",
        ),
        layer_role_setup=IntakeV6LayerRoleSetup(
            confirmation_status="complete",
            layers=[
                IntakeV6LayerRoleLayer(
                    layer_key="logo-dreapta",
                    layer_id="logo-dreapta",
                    layer_name="logo dreapta",
                    auto_role="printed_artwork",
                    auto_confidence="high",
                    confirmed_role="printed_artwork",
                    confirmation_state="confirmed",
                ),
            ],
        ),
        finish_setup=IntakeV6FinishSetup(
            letter_group_finishes=[],
            artwork_finishes=[
                IntakeV6ArtworkFinish(
                    layer_key="logo-dreapta",
                    layer_name="logo dreapta",
                    execution_type="print_laminate",
                    color_mode="polychrome",
                    confirmed=False,
                ),
            ],
            confirmed=True,
        ),
    )

    assert _derive_readiness_status(payload) == "logo_only_candidate_not_offerable"


def test_logo_root_confirmed_artwork_stays_candidate_not_offerable():
    """Confirmed constructive model must not imply root quote readiness for Logo."""
    assert is_candidate_only_template(TPL_VOLUMETRIC_LOGO_V1) is True
    assert is_root_offerable_template(TPL_VOLUMETRIC_LOGO_V1) is False

    payload = IntakeV6WorkspacePayload(
        product_binding={
            "template_code": "TPL-VOLUMETRIC-LOGO_v1",
            "template_label": "Logo volumetric",
            "product_family": "litere_volumetrice",
        },
        svg_source=IntakeV6SvgSource(
            file_name="logo.svg",
            file_size_bytes=943,
            file_hash="logo-source-hash",
            upload_status="analyzed",
        ),
        layer_role_setup=IntakeV6LayerRoleSetup(
            confirmation_status="complete",
            layers=[
                IntakeV6LayerRoleLayer(
                    layer_key="logo-dreapta",
                    layer_id="logo-dreapta",
                    layer_name="logo dreapta",
                    auto_role="printed_artwork",
                    auto_confidence="high",
                    confirmed_role="printed_artwork",
                    confirmation_state="confirmed",
                ),
            ],
        ),
        finish_setup=IntakeV6FinishSetup(
            letter_group_finishes=[],
            artwork_finishes=[
                IntakeV6ArtworkFinish(
                    layer_key="logo-dreapta",
                    layer_name="logo dreapta",
                    execution_type="print_laminate",
                    color_mode="polychrome",
                    confirmed=True,
                ),
            ],
            confirmed=True,
        ),
    )

    assert _derive_readiness_status(payload) == "logo_only_candidate_not_offerable"
    assert _derive_readiness_status(payload) != "ready_for_quote_preview"


def test_letters_with_artwork_does_not_use_logo_only_guard():
    """Letters + artwork follows the normal spine; capture blockers stay authoritative."""
    payload = IntakeV6WorkspacePayload(
        product_binding={
            "template_code": "TPL-VOLUMETRIC-LETTERS_v2",
            "template_label": "Litere volumetrice",
            "product_family": "litere_volumetrice",
        },
        svg_source=IntakeV6SvgSource(
            file_name="gradi-curat.svg",
            file_size_bytes=27173,
            file_hash="gradi-source-hash",
            upload_status="analyzed",
        ),
        layer_role_setup=IntakeV6LayerRoleSetup(
            confirmation_status="complete",
            layers=[
                IntakeV6LayerRoleLayer(
                    layer_key="pseudo:maria",
                    layer_name="pseudo maria (blue)",
                    auto_role="face",
                    confirmed_role="face",
                    confirmation_state="confirmed",
                ),
                IntakeV6LayerRoleLayer(
                    layer_key="logo-dreapta",
                    layer_name="logo dreapta",
                    auto_role="printed_artwork",
                    confirmed_role="printed_artwork",
                    confirmation_state="confirmed",
                ),
            ],
        ),
        finish_setup=IntakeV6FinishSetup(
            letter_group_finishes=[{"group_key": "pseudo:maria", "confirmed": True}],
            artwork_finishes=[{"layer_key": "logo-dreapta", "confirmed": True}],
            confirmed=True,
        ),
    )

    status = _derive_readiness_status(payload)
    assert status != "logo_only_candidate_not_offerable"
    assert status == "runtime_capture_blocked"

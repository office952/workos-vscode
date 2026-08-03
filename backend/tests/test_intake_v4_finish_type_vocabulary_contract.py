"""AGENT-B-F004 remediation (F7E G4): face/return finish-type fields reject arbitrary
free text instead of silently accepting it.

Scope: backend/schemas/intake_v4.py only — FaceFinishTypeToken / ReturnFinishTypeToken.
See docs/qa/workos-f7d-intake-v6-acm-commercial-integrity-audit-v1/agent-b-findings.json
(AGENT-B-F004) and docs/qa/workos-f7e-intake-v6-acm-finish-commercial-integrity-remediation-v1/.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from schemas.intake_v4 import (
    IntakeV4ArtworkFinish,
    IntakeV4FinishSetup,
    IntakeV4LetterGroupFinish,
)


class TestFaceFinishTypeRejectsArbitraryFreeText:
    def test_unknown_face_finish_type_on_finish_setup_is_rejected(self):
        with pytest.raises(ValidationError, match="face_finish_type"):
            IntakeV4FinishSetup(face_finish_type="not_a_real_finish_xyz")

    def test_unknown_face_finish_type_on_letter_group_is_rejected(self):
        with pytest.raises(ValidationError, match="face_finish_type"):
            IntakeV4LetterGroupFinish(group_key="a", face_finish_type="not_a_real_finish_xyz")

    @pytest.mark.parametrize(
        "value",
        ["none", "oracal_641", "oracal_651", "oracal_8500", "print_laminate"],
    )
    def test_live_ui_face_finish_values_are_accepted(self, value):
        setup = IntakeV4FinishSetup(face_finish_type=value)
        assert setup.face_finish_type == value


class TestReturnFinishTypeRejectsArbitraryFreeText:
    def test_unknown_return_finish_type_on_finish_setup_is_rejected(self):
        with pytest.raises(ValidationError, match="return_finish_type"):
            IntakeV4FinishSetup(return_finish_type="not_a_real_finish_xyz")

    def test_unknown_return_finish_type_on_letter_group_is_rejected(self):
        with pytest.raises(ValidationError, match="return_finish_type"):
            IntakeV4LetterGroupFinish(group_key="a", return_finish_type="not_a_real_finish_xyz")

    def test_unknown_return_finish_type_on_artwork_finish_is_rejected(self):
        with pytest.raises(ValidationError, match="return_finish_type"):
            IntakeV4ArtworkFinish(layer_key="logo", return_finish_type="not_a_real_finish_xyz")

    def test_agent_b_f004_repro_value_is_a_legitimate_documented_token(self):
        """AGENT-B-F004's repro value ('mirror_silver') is the documented internal token
        the UI's 'silver' cant option already normalizes to (see
        frontend/src/lib/intakeV6/intakeV6ReturnFinishRules.ts UI_TO_INTERNAL) — it must
        stay accepted; only genuinely unknown tokens should be rejected."""
        setup = IntakeV4FinishSetup(return_finish_type="mirror_silver")
        assert setup.return_finish_type == "mirror_silver"

    @pytest.mark.parametrize(
        "value",
        [
            "none",
            "same_as_face",
            "white_aluminum",
            "black_aluminum",
            "gold_aluminum",
            "mirror_silver",
            "standard_aluminum",
            "oracal_wrapped",
            "ral_paint",
        ],
    )
    def test_live_ui_return_finish_values_are_accepted(self, value):
        setup = IntakeV4FinishSetup(return_finish_type=value)
        assert setup.return_finish_type == value

    @pytest.mark.parametrize(
        "value",
        ["oracal_651", "vinyl", "painted", "paint", "raw_material", "raw", "prefinished", "ral", "stock"],
    )
    def test_legacy_adapter_alias_values_stay_accepted(self, value):
        """Pre-existing legacy tokens already handled by services/intake_v4_finish_adapter.py
        aliases and read back through IntakeV4WorkspacePayload.model_validate on quote
        accept / material breakdown / EIC preview must not start failing validation."""
        setup = IntakeV4FinishSetup(return_finish_type=value)
        assert setup.return_finish_type == value

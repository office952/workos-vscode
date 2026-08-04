"""Phase B — controlled pre-start reassignment / unassignment request schemas."""

from __future__ import annotations

import re
import uuid
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from models.execution_task_assignment_transition import REASON_NOTE_MAX_LEN

PHASE_B_REASON_CODES = (
    "EMPLOYEE_UNAVAILABLE",
    "EMPLOYEE_INACTIVE",
    "ELIGIBILITY_CHANGED",
    "INCORRECT_INITIAL_ASSIGNMENT",
    "MANAGER_CORRECTION",
    "PLANNING_CHANGE",
    "OPERATIONAL_REBALANCE_PRE_START",
    "OTHER",
)

# Reject control characters; allow letters/digits/punctuation/whitespace (incl. Unicode letters).
_SAFE_NOTE_RE = re.compile(r"^[\w\s.,;:!?()\[\]'\"/+%-]+$", re.UNICODE)


def normalize_reason_note(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    trimmed = value.strip()
    if not trimmed:
        return None
    return trimmed


class ReassignPlanTaskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transition_id: str
    expected_current_employee_id: int
    new_employee_id: int
    reason_code: str
    reason_note: Optional[str] = None
    # Reject legacy bypass if clients send them.
    controlled: Optional[bool] = None
    allow_reassign: Optional[bool] = None

    @field_validator("transition_id")
    @classmethod
    def _uuid_transition(cls, value: str) -> str:
        raw = (value or "").strip()
        if not raw:
            raise ValueError("transition_id_required")
        try:
            return str(uuid.UUID(raw))
        except (TypeError, ValueError) as exc:
            raise ValueError("transition_id_invalid_uuid") from exc

    @field_validator("expected_current_employee_id", "new_employee_id")
    @classmethod
    def _positive_employee(cls, value: int) -> int:
        if not isinstance(value, int) or value <= 0:
            raise ValueError("employee_id_invalid")
        return value

    @field_validator("reason_code")
    @classmethod
    def _reason(cls, value: str) -> str:
        code = (value or "").strip()
        if code not in PHASE_B_REASON_CODES:
            raise ValueError("reason_code_invalid")
        return code

    @field_validator("reason_note")
    @classmethod
    def _note(cls, value: Optional[str]) -> Optional[str]:
        note = normalize_reason_note(value)
        if note is None:
            return None
        if len(note) > REASON_NOTE_MAX_LEN:
            raise ValueError("reason_note_too_long")
        if not _SAFE_NOTE_RE.match(note):
            raise ValueError("reason_note_unsafe_characters")
        return note

    @model_validator(mode="after")
    def _cross(self) -> "ReassignPlanTaskRequest":
        if self.controlled is False:
            raise ValueError("legacy_controlled_false_forbidden")
        if self.allow_reassign is True:
            raise ValueError("silent_reassignment_forbidden")
        if self.new_employee_id == self.expected_current_employee_id:
            raise ValueError("new_employee_must_differ_from_current")
        if self.reason_code == "OTHER" and not self.reason_note:
            raise ValueError("reason_note_required_for_other")
        return self


class UnassignPlanTaskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transition_id: str
    expected_current_employee_id: int
    reason_code: str
    reason_note: Optional[str] = None
    controlled: Optional[bool] = None
    allow_reassign: Optional[bool] = None

    @field_validator("transition_id")
    @classmethod
    def _uuid_transition(cls, value: str) -> str:
        raw = (value or "").strip()
        if not raw:
            raise ValueError("transition_id_required")
        try:
            return str(uuid.UUID(raw))
        except (TypeError, ValueError) as exc:
            raise ValueError("transition_id_invalid_uuid") from exc

    @field_validator("expected_current_employee_id")
    @classmethod
    def _positive_employee(cls, value: int) -> int:
        if not isinstance(value, int) or value <= 0:
            raise ValueError("employee_id_invalid")
        return value

    @field_validator("reason_code")
    @classmethod
    def _reason(cls, value: str) -> str:
        code = (value or "").strip()
        if code not in PHASE_B_REASON_CODES:
            raise ValueError("reason_code_invalid")
        return code

    @field_validator("reason_note")
    @classmethod
    def _note(cls, value: Optional[str]) -> Optional[str]:
        note = normalize_reason_note(value)
        if note is None:
            return None
        if len(note) > REASON_NOTE_MAX_LEN:
            raise ValueError("reason_note_too_long")
        if not _SAFE_NOTE_RE.match(note):
            raise ValueError("reason_note_unsafe_characters")
        return note

    @model_validator(mode="after")
    def _cross(self) -> "UnassignPlanTaskRequest":
        if self.controlled is False:
            raise ValueError("legacy_controlled_false_forbidden")
        if self.allow_reassign is True:
            raise ValueError("silent_reassignment_forbidden")
        if self.reason_code == "OTHER" and not self.reason_note:
            raise ValueError("reason_note_required_for_other")
        return self


TransitionOperation = Literal["REASSIGN", "UNASSIGN"]

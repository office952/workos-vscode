"""Assisted quote delivery log — persisted in quotes.line_items wrapper (no DB migration)."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException

QUOTE_SEND_CHANNELS = frozenset(
    {"email_manual", "whatsapp", "phone", "print", "other"}
)

QUOTE_SEND_LOG_ALLOWED_STATUSES = frozenset(
    {"draft", "priced", "sent", "viewed", "negotiating", "accepted"}
)

QUOTE_SEND_LOG_BLOCKED_STATUSES = frozenset({"rejected", "expired"})

QUOTE_SEND_STATUS_TO_SENT = frozenset({"draft", "priced"})

MAX_SEND_NOTE_LEN = 500
MAX_SEND_DOCUMENT_REF_LEN = 200
MAX_SEND_RECIPIENT_LEN = 200


@dataclass
class QuoteSendLogValidation:
    channel: str
    recipient: Optional[str]
    note: Optional[str]
    document_ref: Optional[str]


def validate_send_log_payload(
    *,
    channel: str,
    recipient: Optional[str] = None,
    note: Optional[str] = None,
    document_ref: Optional[str] = None,
) -> QuoteSendLogValidation:
    normalized_channel = str(channel or "").strip().lower()
    if normalized_channel not in QUOTE_SEND_CHANNELS:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "invalid_send_channel",
                "message": "Canalul de trimitere nu este valid.",
                "allowed_channels": sorted(QUOTE_SEND_CHANNELS),
            },
        )

    clean_recipient = (recipient or "").strip() or None
    if clean_recipient and len(clean_recipient) > MAX_SEND_RECIPIENT_LEN:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "invalid_recipient",
                "message": f"Destinatarul depășește {MAX_SEND_RECIPIENT_LEN} caractere.",
            },
        )

    clean_note = (note or "").strip() or None
    if clean_note and len(clean_note) > MAX_SEND_NOTE_LEN:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "invalid_note",
                "message": f"Notița depășește {MAX_SEND_NOTE_LEN} caractere.",
            },
        )

    clean_document_ref = (document_ref or "").strip() or None
    if clean_document_ref and len(clean_document_ref) > MAX_SEND_DOCUMENT_REF_LEN:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "invalid_document_ref",
                "message": f"Referința document depășește {MAX_SEND_DOCUMENT_REF_LEN} caractere.",
            },
        )

    return QuoteSendLogValidation(
        channel=normalized_channel,
        recipient=clean_recipient,
        note=clean_note,
        document_ref=clean_document_ref,
    )


def extract_commercial_delivery_log(raw: Optional[str]) -> List[Dict[str, Any]]:
    if not raw or not str(raw).strip():
        return []
    try:
        parsed = json.loads(raw)
    except Exception:
        return []
    if not isinstance(parsed, dict):
        return []
    logs = parsed.get("commercial_delivery_log")
    if not isinstance(logs, list):
        return []
    return [entry for entry in logs if isinstance(entry, dict)]


def append_commercial_delivery_log(
    raw_line_items: Optional[str],
    entry: Dict[str, Any],
) -> str:
    """Append log entry without modifying pricing snapshot payload."""
    if raw_line_items and str(raw_line_items).strip():
        try:
            parsed = json.loads(raw_line_items)
        except Exception as exc:
            raise ValueError(f"invalid_line_items_json: {exc}") from exc
        if isinstance(parsed, dict):
            wrapper = dict(parsed)
        else:
            wrapper = {"line_items": parsed}
    else:
        wrapper = {"line_items": []}

    logs = wrapper.get("commercial_delivery_log")
    if not isinstance(logs, list):
        logs = []
    else:
        logs = list(logs)
    logs.append(entry)
    wrapper["commercial_delivery_log"] = logs
    return json.dumps(wrapper)


def build_send_log_entry(
    *,
    quote_obj: Any,
    old_status: str,
    new_status: str,
    validation: QuoteSendLogValidation,
    actor_id: Optional[str] = None,
    actor_email: Optional[str] = None,
) -> Dict[str, Any]:
    sent_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    entry: Dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "event_type": "quote_send_assisted",
        "entity_type": "Quote",
        "entity_id": str(getattr(quote_obj, "id", "")),
        "quote_code": str(getattr(quote_obj, "code", "")),
        "quote_version": int(getattr(quote_obj, "version", 1) or 1),
        "channel": validation.channel,
        "sent_at": sent_at,
        "old_status": old_status,
        "new_status": new_status,
        "assisted_delivery": True,
        "metadata": {
            "quote_code": str(getattr(quote_obj, "code", "")),
            "quote_version": int(getattr(quote_obj, "version", 1) or 1),
            "channel": validation.channel,
            "assisted_delivery": True,
        },
    }
    if validation.recipient:
        entry["recipient"] = validation.recipient
        entry["metadata"]["recipient"] = validation.recipient
    if validation.note:
        entry["note"] = validation.note
        entry["metadata"]["note"] = validation.note
    if validation.document_ref:
        entry["document_ref"] = validation.document_ref
        entry["metadata"]["document_ref"] = validation.document_ref
    if actor_id:
        entry["actor_id"] = actor_id
        entry["metadata"]["actor_id"] = actor_id
    if actor_email:
        entry["actor_email"] = actor_email
        entry["metadata"]["actor_email"] = actor_email
    return entry


def assert_send_log_status_allowed(current_status: str) -> Tuple[bool, str]:
    status = str(current_status or "")
    if status in QUOTE_SEND_LOG_BLOCKED_STATUSES:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "quote_not_eligible_for_send_log",
                "quote_status": status,
                "message": "Trimiterea asistată nu este permisă pentru oferte respinse sau expirate.",
            },
        )
    if status not in QUOTE_SEND_LOG_ALLOWED_STATUSES:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "quote_not_eligible_for_send_log",
                "quote_status": status,
                "message": "Status ofertă neeligibil pentru trimitere asistată.",
            },
        )
    new_status = "sent" if status in QUOTE_SEND_STATUS_TO_SENT else status
    return status in QUOTE_SEND_STATUS_TO_SENT, new_status

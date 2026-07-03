"""Shape validation for intake_requests.site_audit_json (capture only)."""

from __future__ import annotations

from typing import Any, Mapping, Optional

LOCATION_PHOTOS_STATUSES = frozenset(
    {"missing", "received", "verified", "needs_clarification"}
)
POWER_VALUES = frozenset({"unknown", "yes", "no"})
MOUNTING_ACCESS_VALUES = frozenset({"unknown", "ok", "limited", "blocked"})
CABLE_ROUTE_VALUES = frozenset({"unknown", "ok", "needs_review"})


def _as_bool(value: Any) -> bool:
    return bool(value) if value is not None else False


def validate_intake_site_audit(raw: Any) -> Optional[dict[str, Any]]:
    """Normalize site audit JSON for storage. Returns None when empty."""
    if raw is None or raw == "":
        return None
    if not isinstance(raw, dict):
        raise ValueError("site_audit_json must be a JSON object")

    photos = str(raw.get("location_photos_status") or "missing").strip()
    if photos not in LOCATION_PHOTOS_STATUSES:
        photos = "missing"

    power = str(raw.get("power_available") or "unknown").strip()
    if power not in POWER_VALUES:
        power = "unknown"

    access = str(raw.get("mounting_access") or "unknown").strip()
    if access not in MOUNTING_ACCESS_VALUES:
        access = "unknown"

    cable = str(raw.get("cable_route") or "unknown").strip()
    if cable not in CABLE_ROUTE_VALUES:
        cable = "unknown"

    checks_raw = raw.get("checks") if isinstance(raw.get("checks"), Mapping) else {}
    checks = {
        "address_confirmed": _as_bool(checks_raw.get("address_confirmed")),
        "photos_verified": _as_bool(checks_raw.get("photos_verified")),
        "power_confirmed": _as_bool(checks_raw.get("power_confirmed")),
        "access_confirmed": _as_bool(checks_raw.get("access_confirmed")),
    }

    normalized = {
        "mounting_address": str(raw.get("mounting_address") or "").strip(),
        "location_photos_status": photos,
        "power_available": power,
        "mounting_access": access,
        "cable_route": cable,
        "notes": str(raw.get("notes") or "").strip(),
        "checks": checks,
    }

    if not any(
        [
            normalized["mounting_address"],
            normalized["notes"],
            normalized["location_photos_status"] != "missing",
            normalized["power_available"] != "unknown",
            normalized["mounting_access"] != "unknown",
            normalized["cable_route"] != "unknown",
            any(checks.values()),
        ]
    ):
        return None

    return normalized


def site_audit_to_storage(spec: Any) -> Optional[str]:
    import json

    normalized = validate_intake_site_audit(spec)
    if normalized is None:
        return None
    return json.dumps(normalized, ensure_ascii=False)

from __future__ import annotations

import re
from urllib.parse import unquote


_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://")
_WINDOWS_DRIVE_RE = re.compile(r"^[a-zA-Z]:[\\/]")
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x1f\x7f]")
_MAX_OBJECT_KEY_LENGTH = 1024


def validate_storage_object_key(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("Invalid storage object key")

    if value == "" or value.strip() == "":
        raise ValueError("Invalid storage object key")

    # Reject caller input that relies on implicit trimming.
    if value != value.strip():
        raise ValueError("Invalid storage object key")

    if len(value) > _MAX_OBJECT_KEY_LENGTH:
        raise ValueError("Invalid storage object key")

    if _CONTROL_CHAR_RE.search(value):
        raise ValueError("Invalid storage object key")

    if "\\" in value:
        raise ValueError("Invalid storage object key")

    if _WINDOWS_DRIVE_RE.match(value):
        raise ValueError("Invalid storage object key")

    if value.startswith("/"):
        raise ValueError("Invalid storage object key")

    if _SCHEME_RE.match(value):
        raise ValueError("Invalid storage object key")

    if value.endswith("/"):
        raise ValueError("Invalid storage object key")

    decoded = unquote(value)

    # Block encoded schemes/path escapes after URL decoding.
    if _SCHEME_RE.match(decoded):
        raise ValueError("Invalid storage object key")

    for candidate in (value, decoded):
        if "\\" in candidate:
            raise ValueError("Invalid storage object key")

        if _WINDOWS_DRIVE_RE.match(candidate):
            raise ValueError("Invalid storage object key")

        if candidate.startswith("/"):
            raise ValueError("Invalid storage object key")

        if "//" in candidate:
            raise ValueError("Invalid storage object key")

        if candidate.endswith("/"):
            raise ValueError("Invalid storage object key")

        parts = candidate.split("/")
        if any(part in (".", "..") for part in parts):
            raise ValueError("Invalid storage object key")

    return value


def is_valid_storage_object_key(value: str) -> bool:
    try:
        validate_storage_object_key(value)
        return True
    except ValueError:
        return False

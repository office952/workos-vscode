from __future__ import annotations

import base64
import hashlib
import os

from cryptography.fernet import Fernet, InvalidToken


class SecretCryptoUnavailableError(RuntimeError):
    pass


class SecretCryptoInvalidCipherError(RuntimeError):
    pass


def _resolve_secret_key() -> str:
    for key in ("INTEGRATION_SECRET_KEY", "WORKOS_SECRET_KEY", "APP_SECRET_KEY", "MASK_KEY"):
        value = os.environ.get(key, "").strip()
        if value:
            return value
    raise SecretCryptoUnavailableError(
        "Missing integration secret key. Set INTEGRATION_SECRET_KEY (or WORKOS_SECRET_KEY / APP_SECRET_KEY)."
    )


def _derive_fernet_key(key_material: str) -> bytes:
    digest = hashlib.sha256(key_material.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def _fernet() -> Fernet:
    return Fernet(_derive_fernet_key(_resolve_secret_key()))


def encrypt_secret(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    token = _fernet().encrypt(raw.encode("utf-8")).decode("utf-8")
    return f"enc:v1:{token}"


def decrypt_secret(value: str) -> str:
    token = (value or "").strip()
    if not token:
        return ""
    token = token.removeprefix("enc:v1:")
    try:
        plain = _fernet().decrypt(token.encode("utf-8"))
    except InvalidToken as exc:
        raise SecretCryptoInvalidCipherError("Stored integration secret cannot be decrypted.") from exc
    return plain.decode("utf-8")


def mask_secret(value: str) -> str:
    text = (value or "").strip()
    if not text:
        return ""
    if len(text) <= 4:
        return "*" * len(text)
    return f"{text[:2]}***{text[-2:]}"


def mask_username(value: str) -> str:
    text = (value or "").strip()
    if not text:
        return ""
    if "@" in text:
        local, domain = text.split("@", 1)
        head = local[:2] if len(local) >= 2 else local[:1]
        return f"{head}***@{domain}"
    if len(text) <= 2:
        return f"{text[:1]}***"
    return f"{text[:2]}***"
"""UTF-8 text integrity: detect and safely repair confirmed mojibake.

Canonical contract: operator-visible and persisted human text is UTF-8 end-to-end.
Repair uses Windows-1252 (cp1252) → UTF-8 for confirmed single-pass corruption only.
Never apply blind latin1 round-trips or whole-document decode loops.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, Iterator, List, Optional, Sequence, Tuple

# Suspicious sequences produced when UTF-8 bytes were decoded as Windows-1252/CP1252.
# Do NOT treat lone Romanian letters (Ă Â Î Ș Ț ă â î ș ț) as mojibake.
_SUSPICIOUS_RE = re.compile(
    r"(?:"
    r"Ä[ƒ„‚]|"  # ă / Ă digraphs (Ä+ƒ, etc.)
    r"Ã[¢®îÎ‚]|"  # â î Â Î fragments
    r"È[™›˜š]|"  # ș ț Ș Ț fragments (cp1252)
    r"â€[”–’“„]|"  # curly quotes / dashes (3-char UTF-8 misreads)
    r"â€”|â€“|â€™|â€œ|"  # explicit common sequences
    r"�"  # replacement character
    r")"
)

# Non-ASCII runs — candidates for segment repair inside mixed clean/corrupt text.
_NON_ASCII_RUN_RE = re.compile(r"[^\x00-\x7f]+")

# Romanian letters used to validate repaired operator labels (not required for punctuation-only).
_RO_LETTER_RE = re.compile(r"[ăâîșțĂÂÎȘȚ]")

_PUNCT_OK = frozenset("—–‘’“”…€×²²³")


class TextClass(str, Enum):
    CLEAN_UTF8 = "CLEAN_UTF8"
    MOJIBAKE_SINGLE_PASS_CONFIRMED = "MOJIBAKE_SINGLE_PASS_CONFIRMED"
    MOJIBAKE_DOUBLE_PASS_CONFIRMED = "MOJIBAKE_DOUBLE_PASS_CONFIRMED"
    AMBIGUOUS = "AMBIGUOUS"
    UNRECOVERABLE = "UNRECOVERABLE"
    LEGITIMATE_NON_ROMANIAN_TEXT = "LEGITIMATE_NON_ROMANIAN_TEXT"


@dataclass(frozen=True)
class Classification:
    text_class: TextClass
    suspicious: bool
    repaired: Optional[str] = None
    passes: int = 0
    reason: str = ""


def has_suspicious_mojibake(value: str) -> bool:
    if not value:
        return False
    return _SUSPICIOUS_RE.search(value) is not None


def try_cp1252_utf8_repair(value: str) -> Optional[str]:
    """One-pass recovery: UTF-8 bytes misread as CP1252, then stored as Unicode."""
    if not value:
        return None
    try:
        candidate = value.encode("cp1252").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return None
    if candidate == value:
        return None
    return candidate


def _looks_meaningful_repair(original: str, repaired: str) -> bool:
    if not repaired or repaired == original:
        return False
    if "\ufffd" in repaired:
        return False
    # Must reduce suspicion; prefer Romanian or known punctuation recovery.
    if has_suspicious_mojibake(repaired):
        return False
    if has_suspicious_mojibake(original):
        if _RO_LETTER_RE.search(repaired) or any(ch in _PUNCT_OK for ch in repaired):
            return True
        # ASCII-only recovery from mojibake punctuation / short tokens still OK if shorter suspicion.
        if not has_suspicious_mojibake(repaired) and len(repaired) <= len(original):
            return True
    return False


def repair_mojibake_segments(value: str) -> Tuple[str, int]:
    """Repair confirmed mojibake segments inside mixed clean/corrupt strings.

    Returns (new_text, repair_segment_count). Clean UTF-8 is left untouched.
    """
    if not value or not has_suspicious_mojibake(value):
        return value, 0

    out: List[str] = []
    last = 0
    repairs = 0
    for match in _NON_ASCII_RUN_RE.finditer(value):
        chunk = match.group(0)
        out.append(value[last : match.start()])
        last = match.end()
        if not has_suspicious_mojibake(chunk):
            out.append(chunk)
            continue
        candidate = try_cp1252_utf8_repair(chunk)
        if candidate is not None and _looks_meaningful_repair(chunk, candidate):
            out.append(candidate)
            repairs += 1
        else:
            out.append(chunk)
    out.append(value[last:])
    return "".join(out), repairs


def classify_text(value: str) -> Classification:
    if value is None:
        return Classification(TextClass.CLEAN_UTF8, False, reason="empty")
    if not isinstance(value, str):
        return Classification(TextClass.AMBIGUOUS, False, reason="non_string")

    if not has_suspicious_mojibake(value):
        return Classification(TextClass.CLEAN_UTF8, False, repaired=None, reason="no_suspicious_pattern")

    once, n1 = repair_mojibake_segments(value)
    if n1 > 0 and not has_suspicious_mojibake(once) and once != value:
        # Check double-pass only when single-pass left suspicion (should not happen here)
        return Classification(
            TextClass.MOJIBAKE_SINGLE_PASS_CONFIRMED,
            True,
            repaired=once,
            passes=1,
            reason=f"cp1252_segment_repairs={n1}",
        )

    if n1 > 0 and has_suspicious_mojibake(once):
        twice, n2 = repair_mojibake_segments(once)
        if n2 > 0 and not has_suspicious_mojibake(twice):
            return Classification(
                TextClass.MOJIBAKE_DOUBLE_PASS_CONFIRMED,
                True,
                repaired=twice,
                passes=2,
                reason=f"cp1252_segment_repairs={n1}+{n2}",
            )
        return Classification(
            TextClass.AMBIGUOUS,
            True,
            repaired=None,
            passes=0,
            reason="residual_suspicion_after_repair",
        )

    # Whole-string single pass (no segment success) — try once for fully-corrupt short labels
    whole = try_cp1252_utf8_repair(value)
    if whole is not None and _looks_meaningful_repair(value, whole):
        if has_suspicious_mojibake(whole):
            whole2 = try_cp1252_utf8_repair(whole)
            if whole2 is not None and _looks_meaningful_repair(whole, whole2) and not has_suspicious_mojibake(whole2):
                return Classification(
                    TextClass.MOJIBAKE_DOUBLE_PASS_CONFIRMED,
                    True,
                    repaired=whole2,
                    passes=2,
                    reason="cp1252_whole_double",
                )
            return Classification(
                TextClass.AMBIGUOUS,
                True,
                reason="whole_repair_still_suspicious",
            )
        return Classification(
            TextClass.MOJIBAKE_SINGLE_PASS_CONFIRMED,
            True,
            repaired=whole,
            passes=1,
            reason="cp1252_whole_single",
        )

    # Suspicious markers but no safe repair — do not mutate.
    if _RO_LETTER_RE.search(value) and not has_suspicious_mojibake(value.replace("Ä", "").replace("È", "")):
        return Classification(TextClass.AMBIGUOUS, True, reason="mixed_or_unknown")

    return Classification(
        TextClass.UNRECOVERABLE if "�" in value else TextClass.AMBIGUOUS,
        True,
        reason="suspicious_no_safe_repair",
    )


def safe_repair_text(value: str) -> Tuple[str, Classification]:
    """Return repaired text only for confirmed classes; otherwise original."""
    classification = classify_text(value)
    if classification.text_class in (
        TextClass.MOJIBAKE_SINGLE_PASS_CONFIRMED,
        TextClass.MOJIBAKE_DOUBLE_PASS_CONFIRMED,
    ) and classification.repaired is not None:
        return classification.repaired, classification
    return value, classification


def assert_no_mojibake(value: str, *, context: str = "") -> None:
    """Raise AssertionError when confirmed/ambiguous mojibake is present."""
    if has_suspicious_mojibake(value):
        loc = f" ({context})" if context else ""
        raise AssertionError(f"Suspicious mojibake detected{loc}: {value!r}")


def walk_repair_json(obj: Any) -> Tuple[Any, List[dict]]:
    """Deep-repair JSON-like structures. Returns (new_obj, audit_rows)."""
    audit: List[dict] = []

    def _walk(node: Any, path: str) -> Any:
        if isinstance(node, str):
            repaired, classification = safe_repair_text(node)
            if repaired != node:
                audit.append(
                    {
                        "path": path,
                        "old": node,
                        "new": repaired,
                        "class": classification.text_class.value,
                        "passes": classification.passes,
                        "reason": classification.reason,
                    }
                )
            return repaired
        if isinstance(node, list):
            return [_walk(v, f"{path}[{i}]") for i, v in enumerate(node)]
        if isinstance(node, dict):
            return {k: _walk(v, f"{path}.{k}" if path != "$" else f"$.{k}") for k, v in node.items()}
        return node

    return _walk(obj, "$"), audit


def repair_source_text(content: str) -> Tuple[str, List[dict]]:
    """Repair confirmed mojibake segments in a UTF-8 source file body."""
    if content.startswith("\ufeff"):
        body = content.lstrip("\ufeff")
        bom = True
    else:
        body = content
        bom = False

    audit: List[dict] = []
    out: List[str] = []
    last = 0
    for match in _NON_ASCII_RUN_RE.finditer(body):
        chunk = match.group(0)
        out.append(body[last : match.start()])
        last = match.end()
        repaired, classification = safe_repair_text(chunk)
        if repaired != chunk:
            audit.append(
                {
                    "start": match.start(),
                    "old": chunk,
                    "new": repaired,
                    "class": classification.text_class.value,
                    "passes": classification.passes,
                }
            )
            out.append(repaired)
        else:
            out.append(chunk)
    out.append(body[last:])
    text = "".join(out)
    # Prefer UTF-8 without BOM for source files.
    return text, audit


def structural_commercial_fingerprint(obj: Any) -> Any:
    """Mask strings; keep keys, array order/length, numbers, bools, nulls."""
    if isinstance(obj, dict):
        return {k: structural_commercial_fingerprint(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [structural_commercial_fingerprint(v) for v in obj]
    if isinstance(obj, str):
        return "<<STR>>"
    if isinstance(obj, bool) or obj is None:
        return obj
    if isinstance(obj, (int, float)):
        return obj
    return f"<<OTHER:{type(obj).__name__}>>"


def fingerprint_hash(obj: Any) -> str:
    import hashlib
    import json as _json

    canon = _json.dumps(
        structural_commercial_fingerprint(obj),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


__all__ = [
    "TextClass",
    "Classification",
    "has_suspicious_mojibake",
    "try_cp1252_utf8_repair",
    "repair_mojibake_segments",
    "classify_text",
    "safe_repair_text",
    "assert_no_mojibake",
    "walk_repair_json",
    "repair_source_text",
    "structural_commercial_fingerprint",
    "fingerprint_hash",
]

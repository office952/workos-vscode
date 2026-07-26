"""Owner-valid active template scope for quote/pricing flows."""

from __future__ import annotations

from typing import FrozenSet, Iterable, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.product_templates import Product_templates
from services.template_usage_mode_policy import (
    ROOT_OFFERABLE_TEMPLATE_CODES,
    TPL_METAL_PREMOUNT_STRUCTURE_V1,
    TPL_VOLUMETRIC_LETTERS_V2,
)

OWNER_VALID_ACTIVE_TEMPLATE_CODE = TPL_VOLUMETRIC_LETTERS_V2
OWNER_VALID_STRUCTURE_TEMPLATE_CODE = TPL_METAL_PREMOUNT_STRUCTURE_V1
OWNER_VALID_ACTIVE_TEMPLATE_CODES: FrozenSet[str] = ROOT_OFFERABLE_TEMPLATE_CODES

ARCHIVE_NOTE_MARKER = "Archived/experimental — not active for quote/pricing"
ARCHIVE_NOTE_SUFFIX = (
    f"{ARCHIVE_NOTE_MARKER}. "
    f"Owner-valid scope is {', '.join(sorted(OWNER_VALID_ACTIVE_TEMPLATE_CODES))}."
)


def normalize_template_code(template_code: str | None) -> str:
    return str(template_code or "").strip().upper()


def is_owner_valid_active_template(template_code: str | None) -> bool:
    return normalize_template_code(template_code) in OWNER_VALID_ACTIVE_TEMPLATE_CODES


def template_active_for_quote(
    template_code: str | None,
    *,
    db_active: bool | None,
) -> bool:
    """True when template is active in DB and owner-valid for quote flows."""
    if db_active is False:
        return False
    return is_owner_valid_active_template(template_code)


async def load_active_template_codes(session: AsyncSession) -> List[str]:
    """Template codes with active=True in product_templates."""
    rows = (
        await session.execute(
            select(Product_templates.template_code).where(
                Product_templates.active.is_(True)
            )
        )
    ).scalars().all()
    return sorted(
        {
            normalize_template_code(code)
            for code in rows
            if code and str(code).strip()
        }
    )


async def load_quote_active_template_codes(session: AsyncSession) -> List[str]:
    """Owner-valid templates that are also active in DB."""
    codes = await load_active_template_codes(session)
    return [c for c in codes if is_owner_valid_active_template(c)]


def append_archive_note(existing_notes: str | None) -> str:
    notes = str(existing_notes or "").strip()
    if ARCHIVE_NOTE_MARKER in notes:
        return notes
    if notes:
        return f"{notes} {ARCHIVE_NOTE_SUFFIX}"
    return ARCHIVE_NOTE_SUFFIX


TEMPLATE_INACTIVE_BLOCKERS: tuple[str, ...] = (
    "template_inactive",
    "template_not_active_for_quote",
)


def merge_blockers(
    base: Iterable[str],
    extra: Iterable[str],
) -> tuple[str, ...]:
    return tuple(sorted(set(base) | set(extra)))

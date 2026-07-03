"""Migration: legacy `product_family` labels → canonical `family_id` slugs.

Sprint #5 utility script. Scans `intake_requests.product_family` for values
that are NOT valid canonical `family_id` slugs (from `product_families`) and
rewrites them to the matching slug when a deterministic mapping exists.

Rules:
  - If `product_family` already equals an ACTIVE registry slug: SKIP (noop).
  - If it matches (case-insensitive, trim) a registry row `label`: REWRITE to
    that row's `family_id`.
  - If it matches one of the hand-curated legacy aliases below: REWRITE.
  - Otherwise: UNMAPPED (left untouched, reported in summary).

The script is idempotent (re-running produces 0 rewrites) and supports
`--dry-run` to preview without committing.

Usage:
    python -m scripts.migrate_legacy_family_labels            # apply
    python -m scripts.migrate_legacy_family_labels --dry-run  # preview only
"""

from __future__ import annotations

import argparse
import asyncio
import logging
from typing import Dict, List, Tuple

from sqlalchemy import select

from core.database import db_manager
from models.intake_requests import Intake_requests
from models.product_families import Product_families
import models  # noqa: F401  - ensure all models registered

logger = logging.getLogger(__name__)


# Hand-curated aliases observed in historic intake data. Keys are lowercased
# and trimmed; values are canonical `family_id` slugs.
LEGACY_ALIASES: Dict[str, str] = {
    # print_large_format
    "print format mare": "print_large_format",
    "print mare format": "print_large_format",
    "print digital": "print_large_format",
    "banner pvc": "print_large_format",
    "backlit": "print_large_format",
    # casete_luminoase
    "casete luminoase": "casete_luminoase",
    "casete luminoase led": "casete_luminoase",
    "caseta luminoasa": "casete_luminoase",
    "caseta led": "casete_luminoase",
    # litere_volumetrice
    "litere volumetrice": "litere_volumetrice",
    "litere 3d": "litere_volumetrice",
    "litere volumetrice luminoase": "litere_volumetrice",
    # colantari_auto
    "colantari auto": "colantari_auto",
    "colantare auto": "colantari_auto",
    "colantare vehicule": "colantari_auto",
    "wrap auto": "colantari_auto",
    # semnalistica_interioara
    "semnalistica interioara": "semnalistica_interioara",
    "semnalistica interior": "semnalistica_interioara",
    "placute interior": "semnalistica_interioara",
    # semnalistica_exterioara
    "semnalistica exterioara": "semnalistica_exterioara",
    "semnalistica exterior": "semnalistica_exterioara",
    "totem": "semnalistica_exterioara",
    "totemuri": "semnalistica_exterioara",
    # panouri_publicitare
    "panouri publicitare": "panouri_publicitare",
    "panou publicitar": "panouri_publicitare",
    "billboard": "panouri_publicitare",
    # textile_banner
    "textile banner": "textile_banner",
    "textile si banner": "textile_banner",
    "banner textil": "textile_banner",
    "steag": "textile_banner",
    "steaguri": "textile_banner",
    # cnc_debitare
    "cnc debitare": "cnc_debitare",
    "debitare cnc": "cnc_debitare",
    "cnc": "cnc_debitare",
    # servicii_montaj
    "servicii montaj": "servicii_montaj",
    "montaj": "servicii_montaj",
    "instalare": "servicii_montaj",
}


def _normalize(s: str) -> str:
    return " ".join(s.strip().lower().split())


async def _build_registry_indexes() -> Tuple[Dict[str, str], Dict[str, str]]:
    """Return (slug_set_lower, label_to_slug_lower).

    - slug_set_lower: {lowercased active slug: canonical slug}.
    - label_to_slug_lower: {normalized label: canonical slug} (active only).
    """
    async with db_manager.async_session_maker() as session:
        rows = (
            await session.execute(
                select(Product_families).where(Product_families.active == True)  # noqa: E712
            )
        ).scalars().all()

    slug_map = {r.family_id.lower(): r.family_id for r in rows}
    label_map = {_normalize(r.label): r.family_id for r in rows if r.label}
    return slug_map, label_map


async def migrate_intake_legacy_labels(dry_run: bool = False) -> Dict[str, int]:
    """Scan intake_requests.product_family and rewrite legacy labels.

    Args:
        dry_run: If True, do not commit changes; only report what would change.

    Returns:
        Stats dict with keys: scanned, already_canonical, rewritten,
        unmapped, empty.
    """
    slug_map, label_map = await _build_registry_indexes()

    stats = {
        "scanned": 0,
        "already_canonical": 0,
        "rewritten": 0,
        "unmapped": 0,
        "empty": 0,
    }
    unmapped_samples: List[Tuple[int, str, str]] = []
    rewritten_samples: List[Tuple[int, str, str, str]] = []

    async with db_manager.async_session_maker() as session:
        rows = (await session.execute(select(Intake_requests))).scalars().all()
        for row in rows:
            stats["scanned"] += 1
            pf = row.product_family
            if not pf:
                stats["empty"] += 1
                continue

            norm = _normalize(pf)

            # 1) Already a canonical active slug?
            if norm in slug_map:
                # Normalize casing to canonical form if different
                canonical = slug_map[norm]
                if pf == canonical:
                    stats["already_canonical"] += 1
                    continue
                # Only a casing difference — treat as rewrite for cleanliness.
                rewritten_samples.append((row.id, row.code, pf, canonical))
                stats["rewritten"] += 1
                if not dry_run:
                    row.product_family = canonical
                continue

            # 2) Matches an active registry label?
            if norm in label_map:
                target = label_map[norm]
                rewritten_samples.append((row.id, row.code, pf, target))
                stats["rewritten"] += 1
                if not dry_run:
                    row.product_family = target
                continue

            # 3) Matches a hand-curated legacy alias?
            if norm in LEGACY_ALIASES:
                target = LEGACY_ALIASES[norm]
                # sanity-check target exists in registry
                if target in slug_map.values():
                    rewritten_samples.append((row.id, row.code, pf, target))
                    stats["rewritten"] += 1
                    if not dry_run:
                        row.product_family = target
                    continue

            # 4) Unmapped
            stats["unmapped"] += 1
            unmapped_samples.append((row.id, row.code, pf))

        if not dry_run and stats["rewritten"] > 0:
            await session.commit()

    # Report
    logger.info(
        "[migrate_legacy_family_labels] dry_run=%s scanned=%d already_canonical=%d "
        "rewritten=%d unmapped=%d empty=%d",
        dry_run,
        stats["scanned"],
        stats["already_canonical"],
        stats["rewritten"],
        stats["unmapped"],
        stats["empty"],
    )
    if rewritten_samples:
        logger.info("Rewrites (up to 20 shown):")
        for rid, code, old, new in rewritten_samples[:20]:
            logger.info("  id=%s code=%s  %r -> %r", rid, code, old, new)
    if unmapped_samples:
        logger.warning("Unmapped labels (up to 20 shown):")
        for rid, code, old in unmapped_samples[:20]:
            logger.warning("  id=%s code=%s  %r", rid, code, old)

    stats["_rewritten_samples"] = rewritten_samples  # type: ignore[assignment]
    stats["_unmapped_samples"] = unmapped_samples  # type: ignore[assignment]
    return stats


async def _main(dry_run: bool) -> None:
    await db_manager.init_db()
    stats = await migrate_intake_legacy_labels(dry_run=dry_run)
    print(
        "[migrate_legacy_family_labels] "
        f"dry_run={dry_run} "
        f"scanned={stats['scanned']} "
        f"already_canonical={stats['already_canonical']} "
        f"rewritten={stats['rewritten']} "
        f"unmapped={stats['unmapped']} "
        f"empty={stats['empty']}"
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Migrate legacy intake.product_family labels to canonical family_id slugs.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without committing to the database.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    args = _parse_args()
    asyncio.run(_main(dry_run=args.dry_run))
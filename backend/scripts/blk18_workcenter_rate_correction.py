"""
BLK-18 Workcenter Rate Mapping DB Correction Script
====================================================
Executes the approved namespace corrections:
1. workcenter_rates.code: 6 short names -> WC_* prefixed names
2. machines.workcenter_code: 2 typo/word-order fixes

This script is a ONE-TIME correction. It includes pre-flight checks,
executes the corrections in a transaction, and performs post-checks.

Usage: python -m scripts.blk18_workcenter_rate_correction
"""

import asyncio
import json
import logging
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Approved mappings
WORKCENTER_RATES_MAPPINGS = [
    ("ASSEMBLY", "WC_LIGHTBOX_ASSEMBLY"),
    ("CNC_ROUTER", "WC_CNC_ROUTING"),
    ("FINISHING", "WC_QUALITY_CONTROL"),
    ("INSTALL_PREP", "WC_INSTALLATION_PREP"),
    ("LED_ASSEMBLY", "WC_LED_ASSEMBLY"),
    ("PANEL_CUTTING", "WC_LASER_CUTTING"),
]

MACHINES_CORRECTIONS = [
    ("MCH-EDGEBANDER-01", "WC_EDGE_BANDING", "WC_EDGE_BENDING"),
    ("MCH-PRINTER-LF-01", "WC_LARGE_FORMAT_PRINT", "WC_PRINT_LARGE_FORMAT"),
    ("MCH-PRINTER-LF-02", "WC_LARGE_FORMAT_PRINT", "WC_PRINT_LARGE_FORMAT"),
]

TARGET_WORKCENTER_CODES = [
    "WC_LIGHTBOX_ASSEMBLY", "WC_CNC_ROUTING", "WC_QUALITY_CONTROL",
    "WC_INSTALLATION_PREP", "WC_LED_ASSEMBLY", "WC_LASER_CUTTING",
    "WC_EDGE_BENDING", "WC_PRINT_LARGE_FORMAT",
]

RESULTS = {
    "precheck": {},
    "execution": {},
    "postcheck": {},
    "verdict": "NOT_STARTED",
}


def get_database_url():
    """Get and normalize the database URL."""
    from core.config import settings
    raw_url = settings.database_url
    if not raw_url:
        raise ValueError("DATABASE_URL not set")
    # Normalize to async driver
    if raw_url.startswith("postgresql://") or raw_url.startswith("postgres://"):
        raw_url = raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        raw_url = raw_url.replace("postgres://", "postgresql+asyncpg://", 1)
    # Remove unsupported params
    if "channel_binding" in raw_url:
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        parsed = urlparse(raw_url)
        params = parse_qs(parsed.query)
        params.pop("channel_binding", None)
        new_query = urlencode(params, doseq=True)
        raw_url = urlunparse(parsed._replace(query=new_query))
    return raw_url


async def run_prechecks(session: AsyncSession) -> bool:
    """Run all pre-flight checks. Returns True if all pass."""
    logger.info("=" * 60)
    logger.info("PRE-CHECKS")
    logger.info("=" * 60)
    all_pass = True

    # PC-01: workcenter_rates row count
    result = await session.execute(text("SELECT COUNT(*) FROM workcenter_rates"))
    count = result.scalar()
    pc01 = count == 6
    RESULTS["precheck"]["PC-01_row_count"] = {"expected": 6, "actual": count, "pass": pc01}
    logger.info(f"PC-01 workcenter_rates count: {count} (expected 6) -> {'PASS' if pc01 else 'FAIL'}")
    if not pc01:
        all_pass = False

    # PC-02: workcenter_rates codes match expected
    result = await session.execute(text("SELECT code FROM workcenter_rates ORDER BY code"))
    codes = [row[0] for row in result.fetchall()]
    expected_codes = sorted(["ASSEMBLY", "CNC_ROUTER", "FINISHING", "INSTALL_PREP", "LED_ASSEMBLY", "PANEL_CUTTING"])
    pc02 = codes == expected_codes
    RESULTS["precheck"]["PC-02_codes_match"] = {"expected": expected_codes, "actual": codes, "pass": pc02}
    logger.info(f"PC-02 codes match: {codes} -> {'PASS' if pc02 else 'FAIL'}")
    if not pc02:
        all_pass = False

    # PC-03: All rates active with rate > 0
    result = await session.execute(
        text("SELECT COUNT(*) FROM workcenter_rates WHERE status = 'active' AND rate_per_hour > 0")
    )
    active_count = result.scalar()
    pc03 = active_count == 6
    RESULTS["precheck"]["PC-03_all_active"] = {"expected": 6, "actual": active_count, "pass": pc03}
    logger.info(f"PC-03 all active with rate > 0: {active_count} -> {'PASS' if pc03 else 'FAIL'}")
    if not pc03:
        all_pass = False

    # PC-04: No WC_-prefixed codes exist yet
    result = await session.execute(text("SELECT COUNT(*) FROM workcenter_rates WHERE code LIKE 'WC_%'"))
    wc_count = result.scalar()
    pc04 = wc_count == 0
    RESULTS["precheck"]["PC-04_no_wc_prefix"] = {"expected": 0, "actual": wc_count, "pass": pc04}
    logger.info(f"PC-04 no WC_ prefix codes: {wc_count} -> {'PASS' if pc04 else 'FAIL'}")
    if not pc04:
        all_pass = False

    # PC-05: Target workcenter codes exist in workcenters
    for target_code in TARGET_WORKCENTER_CODES:
        result = await session.execute(
            text("SELECT COUNT(*) FROM workcenters WHERE workcenter_code = :code"),
            {"code": target_code}
        )
        exists = result.scalar() == 1
        RESULTS["precheck"][f"PC-05_{target_code}"] = {"exists": exists}
        logger.info(f"PC-05 {target_code} in workcenters: {'YES' if exists else 'NO'}")
        if not exists:
            all_pass = False

    # PC-06: No duplicate target codes in workcenter_rates
    result = await session.execute(
        text("SELECT code, COUNT(*) FROM workcenter_rates GROUP BY code HAVING COUNT(*) > 1")
    )
    duplicates = result.fetchall()
    pc06 = len(duplicates) == 0
    RESULTS["precheck"]["PC-06_no_duplicates"] = {"duplicates": [str(d) for d in duplicates], "pass": pc06}
    logger.info(f"PC-06 no duplicates: {'PASS' if pc06 else 'FAIL'}")
    if not pc06:
        all_pass = False

    # PC-07: machines typo rows exist
    result = await session.execute(
        text("""SELECT machine_code, workcenter_code FROM machines
               WHERE workcenter_code IN ('WC_EDGE_BANDING', 'WC_LARGE_FORMAT_PRINT')
               ORDER BY machine_code""")
    )
    machine_rows = [(row[0], row[1]) for row in result.fetchall()]
    expected_machines = [
        ("MCH-EDGEBANDER-01", "WC_EDGE_BANDING"),
        ("MCH-PRINTER-LF-01", "WC_LARGE_FORMAT_PRINT"),
        ("MCH-PRINTER-LF-02", "WC_LARGE_FORMAT_PRINT"),
    ]
    pc07 = machine_rows == expected_machines
    RESULTS["precheck"]["PC-07_machine_typos"] = {
        "expected": expected_machines, "actual": machine_rows, "pass": pc07
    }
    logger.info(f"PC-07 machine typo rows: {machine_rows} -> {'PASS' if pc07 else 'FAIL'}")
    if not pc07:
        all_pass = False

    # PC-08: machines total count
    result = await session.execute(text("SELECT COUNT(*) FROM machines"))
    machine_count = result.scalar()
    pc08 = machine_count == 14
    RESULTS["precheck"]["PC-08_machine_count"] = {"expected": 14, "actual": machine_count, "pass": pc08}
    logger.info(f"PC-08 machines count: {machine_count} -> {'PASS' if pc08 else 'FAIL'}")
    if not pc08:
        all_pass = False

    # PC-09: Confirm 0 direct matches before correction
    result = await session.execute(
        text("""SELECT COUNT(*) FROM workcenter_rates wr
               JOIN workcenters w ON wr.code = w.workcenter_code""")
    )
    match_count = result.scalar()
    pc09 = match_count == 0
    RESULTS["precheck"]["PC-09_zero_matches"] = {"expected": 0, "actual": match_count, "pass": pc09}
    logger.info(f"PC-09 zero direct matches before correction: {match_count} -> {'PASS' if pc09 else 'FAIL'}")
    if not pc09:
        all_pass = False

    RESULTS["precheck"]["all_pass"] = all_pass
    logger.info(f"\nPRE-CHECK VERDICT: {'ALL PASS' if all_pass else 'FAILED'}")
    return all_pass


async def execute_corrections(session: AsyncSession) -> bool:
    """Execute the approved corrections. Returns True if successful."""
    logger.info("=" * 60)
    logger.info("EXECUTING CORRECTIONS")
    logger.info("=" * 60)

    # Correction 1: workcenter_rates.code
    logger.info("\n--- Correction 1: workcenter_rates.code ---")
    wr_rows_affected = 0
    for old_code, new_code in WORKCENTER_RATES_MAPPINGS:
        result = await session.execute(
            text("UPDATE workcenter_rates SET code = :new_code WHERE code = :old_code"),
            {"new_code": new_code, "old_code": old_code}
        )
        affected = result.rowcount
        wr_rows_affected += affected
        logger.info(f"  {old_code} -> {new_code}: {affected} row(s) affected")
        if affected != 1:
            logger.error(f"  UNEXPECTED: Expected 1 row affected, got {affected}")
            RESULTS["execution"]["workcenter_rates"] = {
                "status": "FAIL",
                "reason": f"Unexpected rowcount for {old_code}: {affected}",
                "rows_affected": wr_rows_affected,
            }
            return False

    RESULTS["execution"]["workcenter_rates"] = {
        "status": "PASS",
        "rows_affected": wr_rows_affected,
        "mappings": {old: new for old, new in WORKCENTER_RATES_MAPPINGS},
    }
    logger.info(f"  Total workcenter_rates rows affected: {wr_rows_affected}")

    # Correction 2: machines.workcenter_code
    logger.info("\n--- Correction 2: machines.workcenter_code ---")
    mc_rows_affected = 0
    for machine_code, old_wc, new_wc in MACHINES_CORRECTIONS:
        result = await session.execute(
            text("""UPDATE machines SET workcenter_code = :new_wc
                   WHERE machine_code = :machine_code AND workcenter_code = :old_wc"""),
            {"new_wc": new_wc, "machine_code": machine_code, "old_wc": old_wc}
        )
        affected = result.rowcount
        mc_rows_affected += affected
        logger.info(f"  {machine_code}: {old_wc} -> {new_wc}: {affected} row(s) affected")
        if affected != 1:
            logger.error(f"  UNEXPECTED: Expected 1 row affected, got {affected}")
            RESULTS["execution"]["machines"] = {
                "status": "FAIL",
                "reason": f"Unexpected rowcount for {machine_code}: {affected}",
                "rows_affected": mc_rows_affected,
            }
            return False

    RESULTS["execution"]["machines"] = {
        "status": "PASS",
        "rows_affected": mc_rows_affected,
        "corrections": {mc: f"{old} -> {new}" for mc, old, new in MACHINES_CORRECTIONS},
    }
    logger.info(f"  Total machines rows affected: {mc_rows_affected}")

    return True


async def run_postchecks(session: AsyncSession) -> bool:
    """Run all post-checks. Returns True if all pass."""
    logger.info("=" * 60)
    logger.info("POST-CHECKS")
    logger.info("=" * 60)
    all_pass = True

    # POC-01: workcenter_rates row count unchanged
    result = await session.execute(text("SELECT COUNT(*) FROM workcenter_rates"))
    count = result.scalar()
    poc01 = count == 6
    RESULTS["postcheck"]["POC-01_row_count"] = {"expected": 6, "actual": count, "pass": poc01}
    logger.info(f"POC-01 row count unchanged: {count} -> {'PASS' if poc01 else 'FAIL'}")
    if not poc01:
        all_pass = False

    # POC-02: All codes are WC_-prefixed
    result = await session.execute(text("SELECT COUNT(*) FROM workcenter_rates WHERE code NOT LIKE 'WC_%'"))
    non_wc = result.scalar()
    poc02 = non_wc == 0
    RESULTS["postcheck"]["POC-02_all_wc_prefix"] = {"non_wc_count": non_wc, "pass": poc02}
    logger.info(f"POC-02 all WC_ prefixed: non-WC count={non_wc} -> {'PASS' if poc02 else 'FAIL'}")
    if not poc02:
        all_pass = False

    # POC-03: All codes exist in workcenters
    result = await session.execute(
        text("""SELECT wr.code FROM workcenter_rates wr
               LEFT JOIN workcenters w ON wr.code = w.workcenter_code
               WHERE w.workcenter_code IS NULL""")
    )
    orphans = [row[0] for row in result.fetchall()]
    poc03 = len(orphans) == 0
    RESULTS["postcheck"]["POC-03_all_in_workcenters"] = {"orphans": orphans, "pass": poc03}
    logger.info(f"POC-03 all codes in workcenters: orphans={orphans} -> {'PASS' if poc03 else 'FAIL'}")
    if not poc03:
        all_pass = False

    # POC-04: Rates unchanged
    result = await session.execute(
        text("SELECT code, rate_per_hour FROM workcenter_rates ORDER BY code")
    )
    rates = {row[0]: float(row[1]) for row in result.fetchall()}
    expected_rates = {
        "WC_CNC_ROUTING": 110.0,
        "WC_INSTALLATION_PREP": 90.0,
        "WC_LASER_CUTTING": 80.0,
        "WC_LED_ASSEMBLY": 110.0,
        "WC_LIGHTBOX_ASSEMBLY": 100.0,
        "WC_QUALITY_CONTROL": 80.0,
    }
    poc04 = rates == expected_rates
    RESULTS["postcheck"]["POC-04_rates_unchanged"] = {"expected": expected_rates, "actual": rates, "pass": poc04}
    logger.info(f"POC-04 rates unchanged: {rates} -> {'PASS' if poc04 else 'FAIL'}")
    if not poc04:
        all_pass = False

    # POC-05: Labels unchanged
    result = await session.execute(
        text("SELECT code, label FROM workcenter_rates ORDER BY code")
    )
    labels = {row[0]: row[1] for row in result.fetchall()}
    RESULTS["postcheck"]["POC-05_labels"] = {"labels": labels}
    logger.info(f"POC-05 labels: {labels}")

    # POC-06: Status unchanged
    result = await session.execute(
        text("SELECT COUNT(*) FROM workcenter_rates WHERE status != 'active'")
    )
    non_active = result.scalar()
    poc06 = non_active == 0
    RESULTS["postcheck"]["POC-06_all_active"] = {"non_active": non_active, "pass": poc06}
    logger.info(f"POC-06 all active: non_active={non_active} -> {'PASS' if poc06 else 'FAIL'}")
    if not poc06:
        all_pass = False

    # POC-07: No duplicate codes
    result = await session.execute(
        text("SELECT code, COUNT(*) FROM workcenter_rates GROUP BY code HAVING COUNT(*) > 1")
    )
    dups = result.fetchall()
    poc07 = len(dups) == 0
    RESULTS["postcheck"]["POC-07_no_duplicates"] = {"pass": poc07}
    logger.info(f"POC-07 no duplicates: {'PASS' if poc07 else 'FAIL'}")
    if not poc07:
        all_pass = False

    # POC-08: Machine typo fixes applied
    result = await session.execute(
        text("""SELECT machine_code, workcenter_code FROM machines
               WHERE machine_code IN ('MCH-EDGEBANDER-01', 'MCH-PRINTER-LF-01', 'MCH-PRINTER-LF-02')
               ORDER BY machine_code""")
    )
    machine_rows = [(row[0], row[1]) for row in result.fetchall()]
    expected_machine_rows = [
        ("MCH-EDGEBANDER-01", "WC_EDGE_BENDING"),
        ("MCH-PRINTER-LF-01", "WC_PRINT_LARGE_FORMAT"),
        ("MCH-PRINTER-LF-02", "WC_PRINT_LARGE_FORMAT"),
    ]
    poc08 = machine_rows == expected_machine_rows
    RESULTS["postcheck"]["POC-08_machine_fixes"] = {
        "expected": expected_machine_rows, "actual": machine_rows, "pass": poc08
    }
    logger.info(f"POC-08 machine fixes: {machine_rows} -> {'PASS' if poc08 else 'FAIL'}")
    if not poc08:
        all_pass = False

    # POC-09: Machine total unchanged
    result = await session.execute(text("SELECT COUNT(*) FROM machines"))
    mc_count = result.scalar()
    poc09 = mc_count == 14
    RESULTS["postcheck"]["POC-09_machine_count"] = {"expected": 14, "actual": mc_count, "pass": poc09}
    logger.info(f"POC-09 machine count: {mc_count} -> {'PASS' if poc09 else 'FAIL'}")
    if not poc09:
        all_pass = False

    # POC-10: Direct match count improved
    result = await session.execute(
        text("""SELECT COUNT(*) FROM workcenter_rates wr
               JOIN workcenters w ON wr.code = w.workcenter_code""")
    )
    match_count = result.scalar()
    poc10 = match_count == 6
    RESULTS["postcheck"]["POC-10_direct_matches"] = {"expected": 6, "actual": match_count, "pass": poc10}
    logger.info(f"POC-10 direct matches: {match_count} (expected 6) -> {'PASS' if poc10 else 'FAIL'}")
    if not poc10:
        all_pass = False

    # POC-11: Deferred orphans unchanged
    result = await session.execute(
        text("""SELECT machine_code, workcenter_code FROM machines
               WHERE workcenter_code IN ('WC_PAINT_BOOTH', 'WC_UV_FLATBED_PRINT')
               ORDER BY machine_code""")
    )
    deferred = [(row[0], row[1]) for row in result.fetchall()]
    expected_deferred = [
        ("MCH-PAINTBOOTH-01", "WC_PAINT_BOOTH"),
        ("MCH-PRINTER-UV-01", "WC_UV_FLATBED_PRINT"),
    ]
    poc11 = deferred == expected_deferred
    RESULTS["postcheck"]["POC-11_deferred_unchanged"] = {
        "expected": expected_deferred, "actual": deferred, "pass": poc11
    }
    logger.info(f"POC-11 deferred unchanged: {deferred} -> {'PASS' if poc11 else 'FAIL'}")
    if not poc11:
        all_pass = False

    # POC-12: Old short codes no longer exist
    result = await session.execute(
        text("""SELECT code FROM workcenter_rates
               WHERE code IN ('ASSEMBLY', 'CNC_ROUTER', 'FINISHING', 'INSTALL_PREP', 'LED_ASSEMBLY', 'PANEL_CUTTING')""")
    )
    old_codes = [row[0] for row in result.fetchall()]
    poc12 = len(old_codes) == 0
    RESULTS["postcheck"]["POC-12_old_codes_gone"] = {"old_codes": old_codes, "pass": poc12}
    logger.info(f"POC-12 old codes gone: {old_codes} -> {'PASS' if poc12 else 'FAIL'}")
    if not poc12:
        all_pass = False

    # POC-13: Old machine codes no longer exist
    result = await session.execute(
        text("""SELECT machine_code, workcenter_code FROM machines
               WHERE workcenter_code IN ('WC_EDGE_BANDING', 'WC_LARGE_FORMAT_PRINT')""")
    )
    old_mc = result.fetchall()
    poc13 = len(old_mc) == 0
    RESULTS["postcheck"]["POC-13_old_machine_codes_gone"] = {"remaining": [str(r) for r in old_mc], "pass": poc13}
    logger.info(f"POC-13 old machine codes gone: {[str(r) for r in old_mc]} -> {'PASS' if poc13 else 'FAIL'}")
    if not poc13:
        all_pass = False

    RESULTS["postcheck"]["all_pass"] = all_pass
    logger.info(f"\nPOST-CHECK VERDICT: {'ALL PASS' if all_pass else 'FAILED'}")
    return all_pass


async def main():
    """Main execution flow."""
    logger.info("BLK-18 Workcenter Rate Mapping DB Correction")
    logger.info("=" * 60)

    db_url = get_database_url()
    logger.info(f"Database URL: {db_url[:30]}...")

    engine = create_async_engine(db_url, poolclass=NullPool)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with session_maker() as session:
            async with session.begin():
                # Phase 1: Pre-checks
                precheck_pass = await run_prechecks(session)
                if not precheck_pass:
                    RESULTS["verdict"] = "ABORTED_PRECHECK_FAILED"
                    logger.error("PRE-CHECKS FAILED — ABORTING. No changes made.")
                    print(json.dumps(RESULTS, indent=2, default=str))
                    return

                # Phase 2: Execute corrections
                exec_pass = await execute_corrections(session)
                if not exec_pass:
                    RESULTS["verdict"] = "ROLLED_BACK_EXECUTION_FAILED"
                    logger.error("EXECUTION FAILED — ROLLING BACK. No changes committed.")
                    # Transaction will be rolled back automatically since we don't commit
                    raise Exception("Execution failed, triggering rollback")

                # Phase 3: Post-checks (within same transaction)
                postcheck_pass = await run_postchecks(session)
                if not postcheck_pass:
                    RESULTS["verdict"] = "ROLLED_BACK_POSTCHECK_FAILED"
                    logger.error("POST-CHECKS FAILED — ROLLING BACK.")
                    raise Exception("Post-checks failed, triggering rollback")

                # All passed — transaction will be committed by context manager
                RESULTS["verdict"] = "BLK18_WORKCENTER_RATE_MAPPING_DB_CORRECTION_COMPLETED"
                logger.info("=" * 60)
                logger.info("ALL CHECKS PASSED — COMMITTING TRANSACTION")
                logger.info("VERDICT: BLK18_WORKCENTER_RATE_MAPPING_DB_CORRECTION_COMPLETED")
                logger.info("=" * 60)

    except Exception as e:
        if RESULTS["verdict"] == "NOT_STARTED":
            RESULTS["verdict"] = f"FAILED: {str(e)}"
        logger.error(f"Transaction rolled back: {e}")
    finally:
        await engine.dispose()

    # Output results as JSON
    print("\n=== RESULTS JSON ===")
    print(json.dumps(RESULTS, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
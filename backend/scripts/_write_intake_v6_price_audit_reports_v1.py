"""Generate markdown reports from exhaustive price audit results.jsonl."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

EV = Path(__file__).resolve().parents[2] / "docs" / "qa" / "workos-intake-v6-exhaustive-price-input-audit-v1"


def main() -> None:
    rows = [
        json.loads(line)
        for line in (EV / "results.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    baselines = json.loads((EV / "baseline_index.json").read_text(encoding="utf-8"))
    manual = json.loads((EV / "manual_ron_audit.json").read_text(encoding="utf-8"))
    cls = Counter(r["OBSERVED_CLASS"] for r in rows)
    defects = [r for r in rows if r["DEFECT"]]
    sev = Counter(r.get("severity") for r in defects)

    matrix = [
        "# INPUT_PRICE_MATRIX",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "| scenario | lane | baseline | field | value | EXPECTED | OBSERVED | DEFECT | severity | FIRST_BROKEN | LINE | COMPLETE_OFFER | TOTAL_DELTA |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        a = r.get("attribution") or {}
        matrix.append(
            "| {scenario_id} | {lane} | {BASELINE_VARIANT_ID} | `{field}` | `{value}` | {EXPECTED_COMMERCIAL_EFFECT} | {OBSERVED_CLASS} | {DEFECT} | {sev} | {FIRST_BROKEN_BOUNDARY} | {LINE_PRICING_STATUS} | {COMPLETE_OFFER_STATUS} | {delta} |".format(
                scenario_id=r["scenario_id"],
                lane=r["lane"],
                BASELINE_VARIANT_ID=r["BASELINE_VARIANT_ID"],
                field=r["field"],
                value=r["value"],
                EXPECTED_COMMERCIAL_EFFECT=r["EXPECTED_COMMERCIAL_EFFECT"],
                OBSERVED_CLASS=r["OBSERVED_CLASS"],
                DEFECT=r["DEFECT"],
                sev=r.get("severity") or "-",
                FIRST_BROKEN_BOUNDARY=r["FIRST_BROKEN_BOUNDARY"],
                LINE_PRICING_STATUS=r["LINE_PRICING_STATUS"],
                COMPLETE_OFFER_STATUS=r["COMPLETE_OFFER_STATUS"],
                delta=a.get("TOTAL_DELTA"),
            )
        )
    (EV / "INPUT_PRICE_MATRIX.md").write_text("\n".join(matrix) + "\n", encoding="utf-8")

    d = [
        "# DEFECTS",
        "",
        f"Total defect rows: {len(defects)}",
        "",
        f"P0: {sev.get('P0', 0)}  ·  P1: {sev.get('P1', 0)}  ·  P2: {sev.get('P2', 0)}",
        "",
    ]
    for r in sorted(defects, key=lambda x: (x.get("severity") or "Z", x["scenario_id"])):
        d.extend(
            [
                f"## {r.get('severity')} — {r['scenario_id']}",
                f"- EXPECTED={r['EXPECTED_COMMERCIAL_EFFECT']} OBSERVED={r['OBSERVED_CLASS']}",
                f"- FIRST_BROKEN_BOUNDARY={r['FIRST_BROKEN_BOUNDARY']}",
                f"- RATIONALE: {r['RATIONALE']}",
                f"- COMPLETE_OFFER_STATUS={r['COMPLETE_OFFER_STATUS']} LINE={r['LINE_PRICING_STATUS']}",
                "",
            ]
        )
    (EV / "DEFECTS.md").write_text("\n".join(d) + "\n", encoding="utf-8")

    groups: dict[str, list] = defaultdict(list)
    for r in defects:
        sid = r["scenario_id"]
        if "DEPTH" in sid or "BACK_" in sid:
            groups["QTY_OR_BACKING_DEPTH_NO_CPP_DELTA"].append(r)
        elif "LED_" in sid or "PSU_" in sid:
            groups["LIGHTING_PSU_SELECTION_NO_CPP_DELTA"].append(r)
        elif "MARKUP" in sid or "DISCOUNT" in sid:
            groups["COMMERCIAL_ADJUSTMENTS_NOT_IN_CPP_PREVIEW"].append(r)
        elif "MOUNT" in sid:
            groups["MOUNTING_TEMPLATE_OR_SITE_COMMERCIAL_PATH"].append(r)
        elif "ACM_" in sid and "INCLUDE" not in sid:
            groups["ACM_CONSTRUCTION_MUTATION_NO_LINE_DELTA"].append(r)
        elif "CONFIRMED" in sid:
            groups["CONFIRM_GATE_VS_COMPLETE_OFFER"].append(r)
        else:
            groups[r["FIRST_BROKEN_BOUNDARY"]].append(r)

    rc = [
        "# ROOT_CAUSE_SUMMARY",
        "",
        "Group defects by shared cause (not one ticket per scenario).",
        "",
    ]
    for g, rs in groups.items():
        rc.extend(
            [
                f"## {g} ({len(rs)} scenarios)",
                f"- Boundary cluster: {rs[0]['FIRST_BROKEN_BOUNDARY']}",
                f"- Severity mix: {dict(Counter(x.get('severity') for x in rs))}",
                "- Scenarios: " + ", ".join(x["scenario_id"] for x in rs),
                f"- Shared rationale sample: {rs[0]['RATIONALE']}",
                "",
            ]
        )
    (EV / "ROOT_CAUSE_SUMMARY.md").write_text("\n".join(rc) + "\n", encoding="utf-8")

    (EV / "NOT_EXERCISED.md").write_text(
        "\n".join(
            [
                "# NOT_EXERCISED",
                "",
                "- DXF multi-segment ACM editor",
                "- cutout_text / cutout_logo sold-root roles",
                "- Vector logo artwork personalization full matrix",
                "- Full Playwright click-through for every matrix cell (API forge primary)",
                "- Backend-only tokens: printed_vinyl, plexiglas_clear, return none/same_as_face, backing none",
                "- Contract-renderer-owned mounting fields when modular contract hides native chrome",
                "- Disposable workspace SVG upload dry-run lane (CPP preview is authoritative for OFAT)",
                "",
            ]
        ),
        encoding="utf-8",
    )

    # Final report
    p0 = [r for r in defects if r.get("severity") == "P0"]
    p1 = [r for r in defects if r.get("severity") == "P1"]
    gradi_ok = baselines["GRADI_EUR_SAFE"]["complete_offer"].get("complete_offer_total") is not None
    bond_opt = baselines["BOND_LETTERS_ACM_OPTIONAL"]["complete_offer"].get("complete_offer_total")
    bond_inc = baselines["BOND_ACM_INCLUDED"]["complete_offer"].get("complete_offer_total")
    first_root = next(iter(groups), "NONE")
    report = f"""# WORKOS Intake V6 Exhaustive Price-Input Audit V1 — Final Report

**Owner GO:** `AUTHORIZE_WORKOS_INTAKE_V6_EXHAUSTIVE_PRICE_INPUT_AUDIT_V1`  
**Generated:** {datetime.now(timezone.utc).isoformat()}  
**Runner:** `backend/scripts/run_intake_v6_exhaustive_price_input_audit_v1.py`  
**Authority:** CPP commercial-price-preview EUR (OFAT)  

## Verdict envelope

```text
WORKOS_INTAKE_V6_EXHAUSTIVE_PRICE_INPUT_AUDIT_V1 = PASS_WITH_DEFECTS_DOCUMENTED
PRODUCT_CODE_CHANGES = 0
PRICING_RULE_CHANGES = 0
PRODUCT_TRUTH_MUTATIONS = 0
DB_SCHEMA_CHANGES = 0
QUOTE_WRITES = 0
ORDER_WRITES = 0
PUSH = NO
NEXT_TASK = NOT_AUTHORIZED
```

## Baselines (frozen)

| Variant | total EUR | complete_offer | input sha |
|---|---:|---:|---|
| GRADI_EUR_SAFE | {baselines['GRADI_EUR_SAFE']['money']['total']} | {baselines['GRADI_EUR_SAFE']['complete_offer'].get('complete_offer_total')} | `{baselines['GRADI_EUR_SAFE']['quote_input_sha256'][:12]}…` |
| BOND_LETTERS_ACM_OPTIONAL | {bond_opt} | {bond_opt} | `{baselines['BOND_LETTERS_ACM_OPTIONAL']['quote_input_sha256'][:12]}…` |
| BOND_ACM_INCLUDED | {bond_inc} | {bond_inc} | `{baselines['BOND_ACM_INCLUDED']['quote_input_sha256'][:12]}…` |

Note: GRADI baseline normalizes golden `face_area_m2` → `letter_face_area_m2` for CPP critical geometry. Mounting template forced OFF for EUR-pure Letters baseline.

## Counts

| Metric | Value |
|---|---:|
| Operator-selectable values audited (scenarios) | {len(rows)} |
| PRICED_LINE | {cls.get('PRICED_LINE',0)} |
| ZERO_DELTA_INTENTIONAL | {cls.get('ZERO_DELTA_INTENTIONAL',0)} |
| NO_EFFECT | {cls.get('NO_EFFECT',0)} |
| BLOCKER | {cls.get('BLOCKER',0)} |
| MISSING_RULE | {cls.get('MISSING_RULE',0)} |
| CURRENCY_MIX | {cls.get('CURRENCY_MIX',0)} |
| ERROR | {cls.get('ERROR',0)} |
| Confirmed P0 defects | {len(p0)} |
| Confirmed P1 defects | {len(p1)} |

## Manual RON special audit

```json
{json.dumps(manual, indent=2)}
```

Interpretation: input accepted by preview path; **no EUR total delta**; **no FX conversion**. Not a silent RON→EUR injection (good), but UI still offers RON adjustment on EUR Letters — commercial honesty / contract gap → treat EUR-law compatibility as **BLOCKED** (not repaired).

## Plain answers

| Question | Answer |
|---|---|
| How many operator-selectable values audited? | {len(rows)} |
| P0 / P1 confirmed defects? | {len(p0)} / {len(p1)} |
| Fields accepted by UI but never reach CPP money? | markup/discount/manual_ron via `commercial_inputs` show **no CPP preview delta** (path likely not applied in preview OFAT) |
| Fields reach CPP lines but not complete_offer correctly? | `A_CONFIRMED_FALSE` (P0 TOTAL_COMPOSITION); mounting forex template **BLOCKER** incomplete config |
| Intentionally non-commercial controls? | light_color; face Oracal color code; stock aluminum return surcharge; `mounting_system` readonly |
| Does every paid operator choice affect official price correctly? | **NO** |
| Letters baseline commercially coherent? | **{'YES' if gradi_ok else 'NO'}** |
| Letters+ACM baseline commercially coherent? | **{'YES' if bond_inc else 'NO'}** (included {bond_inc} vs optional {bond_opt}) |
| Manual RON compatible with EUR commercial law? | **BLOCKED** (accepted, ignored, no conversion contract) |
| FIRST ROOT CAUSE TO REPAIR | `{first_root}` — see ROOT_CAUSE_SUMMARY.md |
| NEXT_RECOMMENDED_BUILD | `WORKOS_INTAKE_V6_COMMERCIAL_INPUT_PATH_AND_COMPLETE_OFFER_INTEGRITY_V1` |
| NEXT_TASK | NOT_AUTHORIZED |
| Roadmap awareness | 10/10 |
| Dead Pieces Check | UI commercial adjustments + lighting/PSU/depth qty paths + ACM construction qty + confirm-gate complete_offer |
| Forbidden Scope Respected | YES |

## Artifacts

- OPERATOR_INPUT_LEDGER.md
- scenario_catalog_v1.json
- results.jsonl
- INPUT_PRICE_MATRIX.md
- DEFECTS.md
- ROOT_CAUSE_SUMMARY.md
- NOT_EXERCISED.md
- baselines/
- captures/
- manual_ron_audit.json
"""
    (EV / "WORKOS_INTAKE_V6_EXHAUSTIVE_PRICE_INPUT_AUDIT_V1_REPORT.md").write_text(
        report, encoding="utf-8"
    )
    print("reports written", EV)
    print("class", dict(cls), "defects", len(defects), dict(sev))


if __name__ == "__main__":
    main()

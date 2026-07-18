# Worklog — ACP Internal Frame Local Configuration — STOP

| Field | Value |
|-------|-------|
| Date | 2026-07-18 |
| Owner GO | `GO_ACP_INTERNAL_FRAME_LOCAL_CONFIGURATION_COMPLETION` |
| Start | `ACP_INTERNAL_FRAME_LOCAL_CONFIGURATION_IN_PROGRESS` |
| **Verdict** | **`FRAME_RESOURCE_OPTIONS_MISSING`** |
| Co-blocker | `FRAME_PROFILE_CATALOG_MISSING` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD before | `525ab979b1ea5e42eea39659d3dc5b97cde1a382` |
| App edits | **None** (stop gate before implementation) |

## Why STOP

Owner acceptance requires material and profile from **canonical Resource Options / catalogs** — no free text, no mock catalog, no seed/migration without GO.

Discovery (runtime + active code):

| Need | Status |
|------|--------|
| ACP frame material Resource Options (otel / aluminiu) | **MISSING** |
| ACP frame profile catalog | **MISSING** |
| Metal Premount `bar_material` steel/aluminum | Wrong product; must not become ACP frame authority |
| Metal Premount `mounting_bar_profile` `30x30x1.5` | Letter bars only; must not be assumed ACP default |
| Named Resource Option registry/service | Does not exist as subsystem |

Per build STOP gates → halt before Step 2/PD/Aggregate implementation.

## Owner correction applied in audit docs

Cadru interior ≠ premontaj; **no global XOR**. Composition guards XOR mounting-support templates (Alucobond panel vs Metal Premount), not nested frame vs premount.

## Proposed codes (not seeded)

**Material (owner-facing):**
- `OPT-ACP-FRAME-MAT-STEEL` — Oțel
- `OPT-ACP-FRAME-MAT-ALUMINIUM` — Aluminiu

**Profile:** owner must confirm sections before any catalog freeze (do not invent `20x20x1.5` as rule).

## Commits this session

1. Audit docs only (XOR correction included): `docs(product-system): record ACP internal frame contract audit`
2. This STOP worklog may ship with docs commit or follow-up docs commit — no feature commits.

## Next safe step

**Option 2 — STOP FOR FRAME PROFILE AND CROSSBAR OWNER RULES**  
(also confirm material Resource Option codes / registry home before any completion build)

## STOP

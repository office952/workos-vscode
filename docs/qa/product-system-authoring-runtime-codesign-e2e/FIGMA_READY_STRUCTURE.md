# Figma-ready structure — Product System authoring (co-design)

| Field | Value |
|-------|--------|
| File | `0CDPIuqoaZ1OQgNnvNyl1F` |
| Date | 2026-07-20 |
| Rule | **Do not invent FINAL frame IDs.** Existing Intake frames are authority for operator runtime. PS authoring frames below are proposed structure for designer write — implement UI against contract freeze now. |

## Existing Intake frames (verified via MCP — Agent C 2026-07-20)

| Frame | Node ID | Role | MCP verify |
|-------|---------|------|------------|
| FINAL — Confirmare 1440×900 | `66:2` | Operator confirm; checkbox → ConfirmJobProductTruth | **PASS** — name/size match |
| FINAL — Configurare Finisaje 1440×900 | `64:2` | Config / Finisaje | **PASS** — name/size match |
| FINAL — Configurare Iluminare 1440×900 | `65:2` | Lighting | **PASS** — name/size match |
| FINAL — Configurare Montaj 1440×900 | `65:106` | Mounting | **PASS** — name/size match |
| PinFooter (on Confirmare) | `67:18` | Sticky footer pattern (handoff / continue) | **PASS** — nested under `66:2` |

Evidence PNGs: `screenshots/figma_01_*` … `figma_10_*`.

## Product System authoring frames — CREATED (Agent C, write access OK)

Page: **`PS — Authoring Studio`** · page id **`91:2`**

| Frame | Node ID | Role | FINAL? |
|-------|---------|------|--------|
| PS Template Authoring Shell | `91:3` | Tabs overview / composition / contracts / dossier / readiness / publication | **NEEDS_POLISH** — implemented against; not owner-FINAL |
| Component Contract + Used-by | `91:12` | Child/dual-role PT, usage_mode, instance_schema_id | **NEEDS_POLISH** |
| Blueprint Dossier Studio split | `91:21` | Tree + editor + rail + sticky footer (`91:32`) | **NEEDS_POLISH** |
| Publication states | `91:36` | DRAFT→…→ARCHIVED + `active ≠ published` | **NEEDS_POLISH** |
| Readiness PASS / BLOCKED | `91:60` | Honest BLOCKED when aluminiu inactive | **NEEDS_POLISH** |
| Canvas note | `91:75` | Provenance note for Agent C closure | n/a |
| 01 Product System Landing | `91:76` | Pack shell (closure map) | PROPOSED |
| 02 Product Template Overview | `91:79` | Pack shell | PROPOSED |
| 03 Composition / Components | `91:82` | Pack shell | PROPOSED |
| 06 Validation Rail | `91:85` | Pack shell | PROPOSED |
| 07 E2E Readiness Collapsed | `91:88` | Pack shell | PROPOSED |
| 08 E2E Readiness Expanded | `91:91` | Pack shell | PROPOSED |
| 10 Publication Ready | `91:94` | Pack shell | PROPOSED |
| 11 Version Status | `91:97` | Pack shell | PROPOSED |
| 12 Runtime Preview | `91:100` | Pack shell | PROPOSED |

Write access: **granted** (Full seat on plan; `use_figma` created page + frames). IDs are real from MCP return — not invented. Core five + note created by Agent C; pack shells `91:76`–`91:100` also present on page (closure map).

Owner still must promote any frame to **FINAL** naming before UI may claim Figma FINAL parity.

## UI implemented against contract (code)

| Surface | Route / component | Live surface note (Agent C) |
|---------|-------------------|-----------------------------|
| Publication panel | `ProductTemplatePublicationPanel` | Visible on Blueprint Dossier Studio; **not** on catalog detail Lifecycle tab |
| Component contracts | `ComponentContractUsedByPanel` | Same as publication (dossier rail) |
| E2E Readiness | `ProductE2EReadinessPanel` | Same; catalog Lifecycle uses older `TemplateLifecycleReadinessPanel` |
| Sticky footer | `blueprint-dossier-sticky-publish-footer` | Captured on dossier |
| Confirmare wiring | `useIntakeV6FinalHandoff` → confirm-job | Confirmare step reachable on fixture |

## Pattern reuse from PinFooter `67:18`

Sticky bottom bar: status text left + primary CTA right; dark `#111827` / border `#2a364a`.

# ACM Face-Treatment Optical / Illumination Catalog Closure — CP0 Freeze

| Field | Value |
|-------|--------|
| Date | 2026-07-21 |
| Kickoff HEAD | `9bdcfaa89f12c83f151d5d9ceec76b7aa82bbaf0` (`9bdcfaa8`) — reconfirmed tip |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Status | **FROZEN** — optical catalog closure Axis B |
| Prior path | `ACM_FACE_TREATMENT_COMMERCIAL_PATH_*` — structural path already PASS_WITH_WARNINGS |
| Engine | native inline |
| Dirty tree | preserved; allowlist-only |
| Publication | **KEEP_DRAFT** |

## Owner GO readback

Close commercial blockers for routed/cut-out + acrylic insert/relief + treatment illumination **where selected**, using only owner-confirmed rates from canonical project truth. No invented rates. No remapping volumetric or LIGHT-ROUTED into Axis B authority. Dual-select deferred. No new SKU. No push/PR.

## Frozen identities (unchanged from commercial path CP0)

| Role | Code / rule |
|------|-------------|
| Root | `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` |
| Routed treatment | `FACE-TREATMENT-ROUTED-BACKLIT-CUTOUT` |
| Routed module | `ACP-LOCAL-MODULE-ROUTED-BACKLIT` |
| Insert treatment | `FACE-TREATMENT-ACRYLIC-INSERT` |
| Insert module | `ACP-LOCAL-MODULE-ACRYLIC-INSERT` |
| Relief badge | `RELIEF_PLEXI_10MM` — UI only |
| Legacy | `TPL-ACP-LIGHT-ROUTED` = `PARALLEL_LEGACY_COST_PATH` — **not** authority |
| Electrical model | `SHELL_COMMON_WITH_ZONE_INTENTS` |
| Resource authority stamp | `MISSING_OPTICAL_ELECTRICAL_RO` until owner RO exists |

## Rate remapping freeze

| Source | Axis B authority? |
|--------|-------------------|
| ACM panel owner rates (`acm_*`, `ACM_PANEL_*`) | Yes — panel shell only (already wired) |
| `MAT-PLEXI-*-10MM` stubs (`missing_price`) | **No priced wire** — KEY_STUB_NO_RATE |
| `MAT-ACP-FATA-LITERE` (letter face 3 mm) | **WRONG_PRODUCT** — do not remap |
| Volumetric `MAT-LED-*` / PSU | **Do not remap** — letters ≠ ACM cavity |
| LIGHT-ROUTED CostEngine formulas | **LEGACY_FORBIDDEN** |
| Invented EUR | Forbidden |

## Ownership freeze

| Concern | Owner |
|---------|-------|
| Panel sheet / area / casetare / root assembly / global mount | ACM shell root |
| Routed: length / contours / routing / cleanup / backing / treatment illum intent / assembly | Routed local module |
| Insert: plexi / thickness / area / cut / count / edge / adhesive / spacers / mounting | Acrylic insert local module |
| Shell PSU / wiring | Shell common with zone intents — no per-zone duplicate PSU |

## Illumination commercial policy (frozen)

| Coexistence | Optical BLOCK | Illumination BLOCK |
|-------------|---------------|--------------------|
| `none` (panel-only) | No | No |
| `insert_only` | Yes (`FACE_TREATMENT_OPTICAL_CATALOG_MISSING`) | **No** — insert-only must not inherit routed illumination BLOCK |
| `routed_only` | Yes | Yes (`FACE_TREATMENT_ILLUMINATION_RATES_MISSING`) |
| `both` | Yes | Yes |

Routed illuminated keeps optical + illumination BLOCK until owner RO. Domain readiness and CPP/EIC gate must agree.

## Resolution statuses (frozen vocabulary)

`WIRED` | `KEY_STUB_NO_RATE` | `WRONG_PRODUCT` | `LEGACY_FORBIDDEN` | `GENUINELY_MISSING`

Priced treatment commercial lines emit only when status is `WIRED` **and** owner rate + unit are proven. Expect **zero** optical WIRED this run.

## Non-scope (frozen)

No XOR change; no volumetric dual-select; no logo/ACM/VL publish; no new SKU; no PI/CI/CT; no LIGHT-ROUTED revival; no broad pricing redesign; no hourly commercial price; no Execution materialization; no Alembic; no desktop/SVG; no push/PR.

## CP0 exit

- [x] Identities reconfirmed
- [x] Remapping freeze locked
- [x] Illumination scoping policy locked
- [x] Shared catalog map ready
- [ ] CP1–CP6 implementation (this run)

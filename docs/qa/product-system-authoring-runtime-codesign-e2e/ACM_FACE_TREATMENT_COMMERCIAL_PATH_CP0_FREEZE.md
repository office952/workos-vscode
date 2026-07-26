# ACM / Bond Face-Treatment Commercial Path — CP0 Freeze

| Field | Value |
|-------|--------|
| Date | 2026-07-21 |
| Kickoff HEAD | `290a4540481b68826d684dd79798c1e751335383` (`290a4540`) — reconfirmed tip |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Status | **FROZEN** — Axis B owner GO |
| Axis | **B** shell-local face treatments (not volumetric applied_content) |
| Engine | native inline |
| Dirty tree | preserved; allowlist-only |

## Owner decision readback

| Item | Locked value |
|------|----------------|
| Axis | **B only** — routed/backlit cut-out + acrylic insert/relief commercial path |
| Axis A | Volumetric letters/logo **unchanged**; XOR **not demoted this build** |
| Root | `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` — KEEP_DRAFT, unpublished |
| Domain | `acm_face_treatments_v1` with `routed_cutouts[]` + `acrylic_inserts[]` |
| Orthogonality | Face treatments **orthogonal** to `applied_content` XOR |
| Logo / VL links | Do **not** create applied_content volumetric links; live outbound = 0 is honest |
| Insert vs relief | **SAME product** — `FACE-TREATMENT-ACRYLIC-INSERT`; `RELIEF_PLEXI_10MM` = UI badge for ~10 mm owner variant only |

## Frozen identities (reconfirmed)

| Role | Code / rule |
|------|-------------|
| Routed treatment | `FACE-TREATMENT-ROUTED-BACKLIT-CUTOUT` |
| Routed geometry | `CUTOUT_TEXT` / `CUTOUT_LOGO` |
| Routed module | `ACP-LOCAL-MODULE-ROUTED-BACKLIT` |
| Insert treatment | `FACE-TREATMENT-ACRYLIC-INSERT` |
| Insert geometry | `ACRYLIC_INSERT` |
| Insert module | `ACP-LOCAL-MODULE-ACRYLIC-INSERT` |
| Insert thickness default | `10.0` mm — `OWNER_CONFIRMED_VARIANT`; **not** sole admitted |
| UI badge (optional) | `RELIEF_PLEXI_10MM` — display only; not a second PT |
| Legacy dead | `TPL-ACP-LIGHT-ROUTED`, `TPL-CUT-ACM-LETTERS`, ghost aliases — **not** commercial authority |
| Frame | `acp_internal_frame` optional — checkbox preserved; unchanged |
| XOR | `applied_content` letters\|logo — **do not change this build** |

## Coexistence (frozen)

| Scenario | Allowed |
|----------|---------|
| Neither (panel-only) | Yes — readiness must not block for absent optional treatments |
| Routed only | Yes |
| Insert only | Yes |
| Both routed + insert | Yes |
| + optional frame | Yes (orthogonal) |
| + applied_content letters/logo XOR | Yes (orthogonal; XOR rules unchanged) |

## Ownership (frozen)

| Concern | Owner |
|---------|-------|
| Panel sheet / casetare / global mount | ACM shell root |
| Routed: route/cut face, optical backing, treatment-specific illum intent, assembly intents | Routed local module |
| Insert: insert material/thickness/cut/edge/adhesive/spacers/retention | Acrylic insert local module |
| Shell PSU/wiring | `SHELL_COMMON_WITH_ZONE_INTENTS` — no per-zone duplicate PSU |
| Volumetric letters electrical | Separate product — not ACP cavity |
| ACM sheet charge | **Once** on shell — treatments must not double-count panel sheet |

## Commercial honesty (frozen)

| Concern | Policy |
|---------|--------|
| Optical / plexi / LED catalogs | `MISSING_OPTICAL_ELECTRICAL_RO` — **BLOCK** commercial lines; do not invent rates |
| CPP panel lines | Remain panel-only `paid_*` ACM path |
| Treatment CPP/EIC | Honest blocker until owner optical catalog GO |
| External artwork | Consume confirmed fields only — no SVG/DWG/DXF parser |

## Non-scope (frozen)

No XOR change; no letters+logo dual-select; no logo/ACM/VL publish; no new panel/composite SKU; no LIGHT-ROUTED revival; no PI/CI/ComponentTemplate; no generic bags; no desktop parsers; no auto optical design; no shared power optimization; no Pricing Registry reopen; no Execution materialization; no Alembic; no dirty-tree reset.

## CP0 exit criteria

- [x] Identities reconfirmed (routed + insert; relief = badge)
- [x] Insert ≠ relief STOP **not** triggered (same product)
- [x] Orthogonal to XOR frozen
- [x] Allowlist + shared map ready
- [ ] CP1–CP7 implementation (this run)

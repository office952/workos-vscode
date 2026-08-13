# Wave 1 report — AppShell + role homes

| Field | Value |
|-------|--------|
| Date | 2026-08-13 |
| Program | `WORKOS_UNIFICATION_AND_SIMPLIFICATION_PROGRAM` |
| Authorization | MEGA-AUDIT + CHARTER + DOCS/EVIDENCE ONLY |
| Freeze | `CURRENT_WORKOS_FROZEN_AS_REFERENCE` |
| Implementation | NO |
| Cleanup | NO |
| Unfreeze | NO |
| Owner DB mutations | 0 |
| Frontend | `http://127.0.0.1:3000` (reused live stack) |
| Backend | `http://127.0.0.1:8000` (healthy) |
| Next task | **NOT_AUTHORIZED** |

## Verdict

**WAVE 1 EVIDENCE COMPLETE — PASS WITH WARNINGS.**

AppShell and the three role homes were traversed in light and dark. Every visible nav edge was followed once. Full vertical scroll was exhausted on the **real** container (`main.overflow-auto`), including quote filter tabs and the nested admin sidebar.

This GO does **not** claim page `FINAL`, production polish, or percent-complete readiness.

## What was audited

| Surface | Roles | Themes | Full scroll |
|---------|-------|--------|-------------|
| AppShell chrome + user menu + collapse | admin, sales, operator | light, dark | Nav nested scroller PASS (admin 0→624) |
| `/dashboard` | admin | light, dark | PASS 0→1299, 3 segments |
| `/quotes` default + Ciornă + Tarifat + Acceptat + selected | admin; sales default | light, dark | PASS (longest 0→4440, 7 segments) |
| `/shop-floor` | admin, operator | light, dark | PASS 0→818, 3 segments |

Nav follow: **92 / 92** `FOLLOWED=YES` (admin / sales / operator × light / dark). Destinations are first-viewport only by charter.

## Scroll honesty

The first capture helper scrolled `window`. WorkOS desktop chrome is `h-screen overflow-hidden`; the page scroller is `main.overflow-auto`. Those early home shots are **superseded**. Exhaustion log: `wave-1/scroll-exhaust-log.json`. Manifest fields `FULL_VERTICAL_SCROLL`, `BOTTOM_REACHED`, `SCROLL_SEGMENT_COUNT`, `NESTED_SCROLL_CONTAINERS` are filled.

All 20 exhausted surfaces: **PASS**. FAIL count: **0**.

## Findings (observe only)

1. **Incomplete day-mode** — light sidebar still reads as a cool rail against a white canvas (same as 2026-08-02 U1).
2. **Admin home is an audit stack** — next-step + operational-truth + gaps + unlabeled KPI chips before any work list. Charts/util% only after scroll.
3. **Sales home is the strongest of the three** — Romanian H1 “Oferte”, live totals, status filters. Still page-local cards, 7-viewport list, disabled V6 send.
4. **Operator home is honest about Atelier** — H1 matches nav. Internal WC keys (`CNC_ROUTING`, `METAL_FAB`) remain the card titles. English breadcrumb “Shop Floor”.
5. **Role projection works** — `workos-dev-role` shows the U7 IA: operator has no Oferte/Control; sales has no Atelier/HR; admin sees AUDIT/COMPAT/preview honesty chips.
6. **Hardcoded UI** — homes do not use `PageShell` / `DataTableWrapper`. Shared bits: `ThemeToggle`, `SourceBadge`, some notices. Repeat pattern: page-local card grids + banner stacks.

## Explicit non-claims

- Destination pages after nav follow are **not** audited.
- Quote create / send / accept were **not** executed.
- No unfreeze, cleanup, or implementation.

## Stop

`NEXT_TASK = NOT_AUTHORIZED`.

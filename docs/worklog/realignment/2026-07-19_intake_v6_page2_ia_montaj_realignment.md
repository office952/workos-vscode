# Worklog — Intake V6 Page 2 IA & Montaj realignment

**Date:** 2026-07-19  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Initial HEAD:** `5511a6b`  
**Scope:** Frontend IA / UI only — no backend/schema/pricing

## Design checkpoint

`docs/qa/intake-v6-page2-ia-montaj-realignment-2026-07-19/DESIGN_CHECKPOINT.md`

## Structure before → after

**Before:** Flat Montaj dump; Iluminare “Electrică”=PSU; non-sticky blockers; legacy corner competing with segmented 220V.

**After:**
- Tabs: Finisaje · **Iluminare și surse** · Montaj
- Sticky final-blocker summary above tabs (navigable while blocked)
- Montaj: readiness strip → **Montaj comercial** (collapsed accordion) → **Fundal și carcasă** cluster (solution/ACP/segmented/220V) → **Avansat** (collapsed) → site
- Legacy corner hidden when segmented multi-panel CONFIRMED; demoted note while PROPOSED

## Components moved / collapsed

| Item | Change |
|------|--------|
| Segmented + electrical | Inside `intake-v6-fundal-carcasa-cluster` |
| Scope / șablon prep | `intake-v6-montaj-commercial-cluster` accordion |
| Ownership notes, fixing, process, volum | `intake-v6-montaj-advanced-cluster` |
| Legacy service corner | Precedence helper; superseded note in Fundal |
| Operator blocker banner | Sticky + final confirmation extras + focus→tab |

## Tests

- Unit: precedence, final blockers, review tabs, blocker banner — **PASS** (36)
- Playwright CASE 1 segmented live — **PASS** (~14s) against `:3001`/`:8003`
- Live IA runner screenshots — primary path **PASS** (sticky, rename, fundal, elec, reload CONFIRMED)

## Evidence

`docs/qa/intake-v6-page2-ia-montaj-realignment-2026-07-19/`

## Hidden regressions found / fixed

- Nested `lg:overflow-hidden` on tab panels removed
- Blocker summary title updated; composition included in sticky extras
- Cross-SVG optional in docs runner (flaky import wait) — not a product regression
- OWNER_GATE raw enums remain in ACP face modules (demoted visually by Advanced/Fundal hierarchy; full silence deferred)

## Remaining

- Figma frames still predate Fundal cluster (runtime is authority)
- Commercial site section still outside commercial accordion (visible secondary)
- Electrical confirm not always green in IA runner when draft remains — persistence of CONFIRMED segmented verified

## Next step

Owner GO for Build 2: electrical vocabulary polish + corner precedence edge cases / Figma sync — or stop here if IA accepted.

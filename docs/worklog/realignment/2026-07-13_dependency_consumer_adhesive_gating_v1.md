# Worklog — DEPENDENCY_CONSUMER_ADHESIVE_GATING_V1

**Date:** 2026-07-13  
**Branch:** main  
**HEAD before:** 2881823  
**Scope:** Wire `LED_MOUNT_SURFACE` validation into downstream LIGHTING consumers (adhesive, install op/task)

## Investigation — consumer ownership table

| Consumer | Source | Prior gate | New gate |
|----------|--------|------------|----------|
| `adhesive_led_modules` | `intake_v4_consumables_adhesive_wiring_service` | `illuminated` only | `resolve_lighting_mount_consumers().include_led_adhesive` |
| `led_install_letters` op | BOM / aggregate / live calc | `LIGHTING` subscope | + `include_led_install_operation` |
| `led_installation` task | execution plan reader | `LIGHTING` subscope | + `include_led_install_task` |
| `material.adhesive_led` logical line | gradi logical list filter | `LIGHTING` subscope | + mount consumer |
| `sistem_led_install` EIC | estimated internal cost | `LIGHTING` subscope | + mount consumer |
| `sistem_led_module` CPP | commercial proposal | `LIGHTING` subscope | modules always when LIGHTING sold |
| LED modules material | all paths | `LIGHTING` sold | unchanged (`include_led_modules`) |

**Canonical helper:** `backend/services/lighting_mount_consumer_service.py` → `resolve_lighting_mount_consumers(...)`

## Mount/service ownership decision

`LED_MOUNT_SURFACE_NOT_SOLD` confirms **physical support only** (existent/client-supplied surface) — not installation-by-us.

Smallest distinction added without new subsystem:
- `CODE_LED_INSTALLATION_BY_US` in `dependency_confirmations`
- Optional UI prompt after external mount confirm: "Montaj de noi"

| Signal | Meaning |
|--------|---------|
| Sold BACK or FACE+RETURN-CANT | `installation_by_us=true` (we provide mount surface) |
| `LED_MOUNT_SURFACE_NOT_SOLD` | `external_mount_confirmed=true`, readiness satisfied |
| `LED_INSTALLATION_BY_US` | workshop performs adhesive + install on external surface |

**Verdict:** PASS — no `BLOCKED_BY_MOUNT_SERVICE_OWNERSHIP_GAP`

## Shared consumer decision fields

`LightingMountConsumerDecision`: `lighting_sold`, `mount_surface_satisfied`, `sold_mount_provider`, `external_mount_confirmed`, `installation_by_us`, `include_led_modules`, `include_led_adhesive`, `include_led_install_operation`, `include_led_install_task`, `reason_codes`

Applied via `led_consumer_row_allowed()` in: BOM, material breakdown, logical list, EIC, CPP, live calc, execution plan ops/tasks. Quote snapshot freezes `dependency_confirmations`.

## Phase 4 — empty→BACK→LIGHTING flake

**Classification:** `APPLICATION_DEFECT` — server hydrate overwrote in-flight local checkbox state when BACK save returned before LIGHTING toggle persisted.

**Fix:** `IntakeV6OfferScopePanel.tsx` hydrate effect skips when `latestIntentRef` differs from persisted serialized scope.

## Validation

- Backend: `test_lighting_mount_consumer_gating.py` (18 tests) + updated `test_intake_v6_lighting_electrical_scope.py` — **121 passed**
- Frontend Vitest: dependency + readiness + panel — **28 passed**
- Frontend build: `npm run build` — **PASS**
- Playwright: `dependency-consumer-adhesive-gating-v1.spec.ts` on IR-MRI01769

## Direction score

**92/100%** — consumer gating lands on shared helper; external-mount vs install-by-us explicitly split; flake root cause fixed at hydrate boundary.

## Runtime QA (2026-07-13)

- **Verdict:** PASS
- **Stack:** backend :8000, frontend :3000 (existing dev processes; health 200)
- **Playwright:** `dependency-consumer-adhesive-gating-v1.spec.ts` — **1 passed**, **21.6s**, workspace route **IR-MRI01769**
- **Evidence:** 10 screenshots under `docs/qa/dependency-consumer-adhesive-gating-v1/screenshots/`; `evidence_report.json` records **20** offer-scope PUTs
- **E2E follow-up:** aligned scope helpers with validator spec (one PUT per toggle); `captureScenario` skips subset checkbox reads in full-product mode

**Prior blocker cleared:** `BLOCKED_BY_RUNTIME_QA_SAVE_HANG` — no longer reproduces after hydrate guard + sequential persist waits in e2e.

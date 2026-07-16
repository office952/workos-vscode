# WorkOS E2E — Canonical Issue Registry

**Authority:** `docs/master/workos-e2e/WORKOS_E2E_ISSUE_REGISTRY.md`  
**Supersedes active use of:** `docs/qa/workos-e2e-operational-coherence-audit-v1/ISSUE_REGISTRY.md`, `docs/qa/workos-e2e-operational-coherence-audit-v1-true-e2e/ISSUE_REGISTRY.md` (retained as SUPPORTING_EVIDENCE)  
**Baseline HEAD:** `fe6c6f7`  
**Imported from:** TRUE E2E audit TE2E-001–027

## Registry rules

- One active registry only — this file
- Status flow: `open` → `planned` → `active` → `fixed` → `verified` → `closed`
- Tasks reference `WORKOS_E2E_TASK_GRAPH.md`
- Old E2E-001..015 map to TE2E equivalents (do not duplicate)

## Issues

| ID | Title | Class | Sev | Stage | Upstream dep | Downstream impact | Root cause | Owner | Status | Impl task | Test gate | Runtime route | Screenshot | Figma ref | Closure commit |
|----|-------|-------|-----|-------|--------------|-------------------|------------|-------|--------|-----------|-----------|---------------|------------|-----------|----------------|
| TE2E-001 | Mounting blocker ignores mounting_solution | Defect | P1 | Intake V6 | — | PD, handoff, Offer | CONFIRMED legacy gate | Intake/FormSystem | **verified** | W1-L-SPINE | pytest capture + spine tests | `/intake-v6/.../operator` step 2 Montaj | Montaj tab screenshot | PD03, MASTER 09 | W1-INT-02 |
| TE2E-002 | ready_for_quote_preview with blockers | Defect | P1 | Intake V6 | TE2E-001 partial | Offer CTA tone | CONFIRMED readiness derive | Intake workspace | **verified** | W1-L-SPINE | workspace readiness tests | step 2–3 | capture JSON | MASTER 04 | W1-INT-02 |
| TE2E-003 | Finish truth not persisted | Defect | P1 | Intake V6 | — | PD, capture | CONFIRMED UI gap | Intake finish | **verified** | W1-L-FINISH | finish_setup persistence tests | step 2 review | capture JSON | PD02, MASTER 02 | W1-INT-02 |
| TE2E-004 | Autosave setPayload crash | Defect | P1 | Intake V6 | — | — | CONFIRMED orphan call | Intake Review | **closed** | F-001 | commercialSettings test | step 2 | F001 supporting | — | `fe6c6f7` |
| TE2E-005 | Step 2 diagnostic overload | UX | P2 | Intake V6 | TE2E-001,002 | operator confusion | CONFIRMED multi-channel | Frontend Intake | open | W6-T01 | UI snapshot tests | step 2 | `03-intake-step2-configurare.png` | MASTER 07,08 | — |
| TE2E-006 | Cant finish incomplete | Defect | P2 | Intake V6 | — | confirm path | CONFIRMED review mapper gap | Intake finish | **verified** | W1-L-CANT | cant finish tests | step 3 review | `w1-int-02-step3-review-handoff.png` | PD02 | W1-INT-02 |
| TE2E-007 | Residual unclassified vector | Defect | P2 | Intake V6 | — | layer setup | CONFIRMED fixture | Intake analyzer | open | W1-T04 | analyzer fixture test | step 1 | `02-intake-step1-layers.png` | — | — |
| TE2E-008 | Missing pricing rates (20/21) | Defect | P2 | Calcul | — | estimate gap | CONFIRMED registry | Pricing | open | W3-T02 | pricing registry test | step 2 rail | `04-intake-step2-preview-rail.png` | MASTER 10 | — |
| TE2E-009 | Cant/volum label drift | Terminology | P3 | Calcul | — | operator terms | CONFIRMED label | Frontend | open | W6-T02 | label snapshot | step 2 rail | preview rail | — | — |
| TE2E-010 | PD operator page missing | Missing surface | P1 | Definire produs | Intake handoff | stage gap | CONFIRMED no route | PD frontend | open | W2-T03 | route + panel tests | embedded only | pd01 figma | PD01, MASTER 02 | — |
| TE2E-011 | PD01 dev vocabulary | UX | P2 | Definire produs | — | confusion | CONFIRMED Figma | PD UX | open | W6-T03 | Figma parity review | — | pd01 | PD01 | — |
| TE2E-012 | PS stub tabs navigable | Missing surface | P2 | Product System | — | dead ends | CONFIRMED stub | Product System | open | W6-T04 | tab gating test | `/product-system/components` | `15-ps-components-stub-runtime.png` | MASTER 01 | — |
| TE2E-013 | Same-scenario spine absent | Risk | P2 | Cross-cutting | TE2E-001+ | final E2E | RESOLVED — continuous Letters lineage proven | QA | **closed** | W7-T01 | full spine test | `/execution/92402` | `same-scenario-e2e-2026-07-16/01_execution_order_92402.png` | MASTER 00 | `91d8a3f` + truth promotion |
| TE2E-014 | Handoff ignores capture blockers | Defect | P1 | Intake→Ofertă | TE2E-001,002 | bad offer truth | CONFIRMED policy | Intake commercial | **verified** | W1-L-SPINE | handoff policy tests | code path | — | MASTER 05 | W1-INT-02 |
| TE2E-015 | merge_policy_findings unused | Defect | P2 | Intake→Ofertă | TE2E-014 | blockers not merged | CONFIRMED unwired | Intake | **verified** | W1-L-SPINE | policy merge test | code | — | MASTER 05 | W1-INT-02 |
| TE2E-020 | Offers policy banner on operator UI | UX | P2 | Ofertă | — | debug on primary | CONFIRMED | Quotes UI | open | W6-T05 | empty state test | `/quotes` | `20-offers-list-empty.png` | MASTER 07 | — |
| TE2E-021 | Global 2 critical header | UX | P2 | Cross-cutting | — | alarm fatigue | INFERRED source | Shell | open | W6-T06 | header alert test | commercial routes | offers/orders | MASTER 08 | — |
| TE2E-022 | Order freeze unproven same-scenario | Risk | P2 | Comandă | TE2E-013 | freeze boundary | PARTIAL — freeze observed on IR-BUILD1→order `92402` / `QSN2-2026-0002`; dedicated immutability mutation gate still open | Order | open | W4-T02 | snapshot immutability test | `/orders/:id` | same-scenario evidence pack | MASTER 10 | — |
| TE2E-028 | Same-scenario / W7-T02 remaining limitations | Accepted debt | P2 | Cross-cutting | TE2E-013 | follow-up builds | Planning-minute **source** still often 0 (variance mechanics work); stock G3 not forced; labor $ excluded; DETERMINISTIC_LOCAL_SCENARIO fixture origin; not all templates — W7-T02 closed ops UI + breadth, did **not** clear these | QA | open | follow-up | per-gap builds | — | W7-T02 evidence pack | MASTER 00 | — |
| TE2E-023 | Execution session gate | Risk | P3 | Execuție | — | runtime proof | CONFIRMED auth race | Auth shell | open | W5-T03 | auth navigation test | `/execution` | session gate | MASTER 11 | — |
| TE2E-024 | Execution typography dense | UX | P3 | Execuție | — | readability | CONFIRMED code | Execution UI | open | W6-T07 | typography audit | `/execution` | code only | MASTER 06 | — |
| TE2E-025 | Dual pricing path 7G/7H vs CostEngine | Risk | P2 | Calcul | — | cost authority | CONFIRMED parallel | Pricing/Cost | **planned** | W3-T01–T03 | cost trace test | API routers | — | MASTER 10 | D-010 decided |
| TE2E-026 | structura_suport terminology | Terminology | P3 | Aggregate | — | term drift | CONFIRMED module_code | Aggregate | open | W6-T02 | terminology matrix | aggregate API | aggregate JSON | MASTER 09 | — |
| TE2E-027 | ARCH Figma not auditable | Risk | P2 | Cross-cutting | — | architecture gap | CONFIRMED no export | PD UX | open | W0-T02 | Figma MASTER created | — | — | ARCH→MASTER | — |

## Summary

| Severity | Open | Closed |
|----------|------|--------|
| P1 | 5 | 1 |
| P2 | 14 | 1 |
| P3 | 4 | 0 |
| **Total** | **22** | **2** |

Note: TE2E-013 closed; TE2E-028 added as one consolidated residual-limitations entry (net open P2 unchanged).

## Independent downstream (12)

TE2E-008, 009, 010, 011, 012, 020, 021, 023, 024, 025, 026, 027

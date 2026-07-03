# WorkOS Visual Roadmap

**Status:** Document-only  
**Data:** 2026-06-12  
**Horizon:** Incremental — fără big-bang redesign

---

## Overview

```
Phase 0  Owner decisions          ████░░░░░░  gate: decizii formale
Phase 1  Tokens documentation    ██████████  gate: acest build (docs)
Phase 2  Shared primitives       ░░░░░░░░░░  gate: 4 componente + token CSS
Phase 3  Module rollout          ░░░░░░░░░░  gate: module-by-module PASS
Phase 4  Shell / global          ░░░░░░░░░░  gate: după ≥2 module + primitives
```

---

## Phase 0 — Owner decisions

**Scop:** Decizii de produs/design care blochează implementarea consistentă.

| Decizie | Recomandare | Alternativă | Impact dacă amânat |
|---------|-------------|-------------|-------------------|
| Badge shape | Rectangular `--wo-radius-sm` (6px) | Pill `rounded-full` | Inconsistență Quotes vs Plăți |
| Tabs pattern | Underline default | Segmented control | Plăți angajați vs Settings |
| Danger red exact | Alege hex + pereche bg/border | Lăsat TBD | Badge respins/eroare divergent |
| Shell timing | Netouchat până Phase 4 | Rescriere sidebar acum | Regresii nav globală |
| Module priority | Plăți → Quotes → Orders → Exec → Tablet → Pricing | Altă ordine | Resurse dezvoltare |

### Deliverables Phase 0

- [ ] Owner sign-off badge + tabs
- [ ] `--wo-status-danger` valoare finală
- [ ] Ordine Phase 3 confirmată
- [ ] Acceptare strategie „shell last”

### PASS / FAIL — Phase 0

| Criteriu | PASS | FAIL |
|----------|------|------|
| Badge formă | Decizie documentată | Încă deschis la implementare |
| Danger token | Hex ales | TBD la Phase 2 |
| Shell | Explicit amânat Phase 4 | Presiune rescriere globală imediată |
| Prioritate module | Listă ordonată | „Tot odată” |

---

## Phase 1 — Tokens documentation

**Scop:** Formalizare charter + tokeni + status map + component plan — **zero runtime**.

### Deliverables Phase 1 (acest build)

- [x] `WORKOS_VISUAL_IDENTITY_CHARTER.md`
- [x] `WORKOS_UI_TOKENS_DRAFT.md`
- [x] `WORKOS_SEMANTIC_STATUS_MAP.md`
- [x] `WORKOS_COMPONENT_STANDARDIZATION_PLAN.md`
- [x] `WORKOS_VISUAL_ROADMAP.md`
- [x] `BUILD_WORKOS_VISUAL_IDENTITY_CHARTER_AND_TOKENS.md`

### PASS / FAIL — Phase 1

| Criteriu | PASS | FAIL |
|----------|------|------|
| Scope | Doar fișiere `docs/design/` + `docs/qa/` | Orice diff `frontend/`, `backend/` |
| CSS | Niciun `--wo-*` în index.css | Tokeni implementați prematur |
| React | Zero componente noi/modificate | PR include .tsx |
| Backend/DB | Zero | Migrations, routers |
| Charter | Principii + ce nu facem + faze | Doc incomplet |

**Status Phase 1:** PASS (document-only build)

---

## Phase 2 — Shared primitives

**Scop:** Extrage componente partajate + introdu `--wo-*` în CSS/Tailwind (primul cod).

### Componente țintă

1. `StatusBadge` — mapă centralizată semantic
2. `MetricCard` — unifică KPICard + duplicate locale
3. `SourceBadge` — unifică DataSourceBadge
4. `EmptyState` — un singur export

### Tehnical scope

- Adaugă `--wo-*` în `frontend/src/index.css` (sau `workos-tokens.css` importat)
- Extinde `tailwind.config.ts` cu colors `wo`
- Vitest targeted pe componente noi + Quotes/Orders smoke tests existente
- **Nu** atinge App shell layout

### PASS / FAIL — Phase 2

| Criteriu | PASS | FAIL |
|----------|------|------|
| Primitivi | 4 componente exportate din loc unic | Doar documentație |
| Tokeni CSS | `--wo-*` definți, folosiți în primitivi | Hex inline în primitivi |
| Regresii | Teste targeted verde | Schimbare behavior status/lifecycle |
| Shell | Neschimbat | Sidebar/topbar modificat |
| validate:frontend | Nu declarat gate | Declarat green fără audit TS |

---

## Phase 3 — Module rollout

**Scop:** Migrare vizuală modul cu modul — înlocuire hex inline, adoptare primitivi.

### Ordine recomandată

| # | Modul | Rute / zone | Focus |
|---|-------|-------------|-------|
| 1 | **Employee Payments** | Plăți angajați | Figma alignment, FilterChipGroup, FinancialSummaryPanel |
| 2 | **Quotes** | `/quotes`, ClientWorkspace | StatusBadge, ComponentBreakdownTable, MetricCard KPI |
| 3 | **Orders** | `/orders` | SourceBadge, OrderExecutionPanel extract, payment badges |
| 4 | **Execution** | Execution views, reality | Task status, RealityQualityBadge tone alignment |
| 5 | **Operator / Tablet** | `/operator`, `/tablet` | TaskCard, EmptyState live, dense spacing |
| 6 | **ProductSystem / Pricing** | Templates, QuoteWizard | Doar după build dedicat — protected area |

### Per-modul checklist

- [ ] Înlocuit hex `#111827` / `#1A2236` / `#1E293B` cu tokeni
- [ ] Status badges prin `StatusBadge`
- [ ] Source prin `SourceBadge` unde aplicabil
- [ ] Empty states live vs mock clar
- [ ] Vitest + pytest targeted verde
- [ ] QA doc `BUILD_*` pentru modul

### PASS / FAIL — Phase 3 (per modul)

| Criteriu | PASS | FAIL |
|----------|------|------|
| Vizual | Tokeni `--wo-*` în modul | Hex ad-hoc rămas fără justificare |
| Semantic | Status map respectat | Culori arbitrare per pagină |
| Funcțional | Zero regresii lifecycle/API | Logică business atinsă |
| Mock/live | SourceBadge vizibil | Mock ascuns |
| Docs | BUILD QA modul | Fără evidencă teste |

---

## Phase 4 — Shell / global last

**Scop:** App shell, `index.css` global, sidebar, topbar — **doar după evidență Phase 2–3**.

### Scope

- Mapare shadcn `.dark` vars → `--wo-*` unde sigur
- Sidebar / topbar background `--wo-bg-shell`
- Nav active `--wo-text-nav-active`
- Page header global spacing 24px (dacă owner aprobă)

### Preconditions (hard gate)

- ≥2 module Phase 3 PASS
- Phase 2 primitivi stabili 2+ săptămâni fără regresii majore
- Owner sign-off explicit shell

### PASS / FAIL — Phase 4

| Criteriu | PASS | FAIL |
|----------|------|------|
| Timing | După module evidence | Shell first |
| Coerență | Shell folosește aceiași tokeni ca module | Al treilea set culori |
| Regresii | Smoke E2E workintake-finish dacă aplicabil | Navigație ruptă |
| Rollback | Plan revert per commit | Big-bang fără boundary |

---

## Riscuri cross-phase

| Risc | Mitigare |
|------|----------|
| Al treilea sistem vizual | Charter interzice; review diff pentru hex noi |
| Pierdere densitate operator | Spacing rules în token draft |
| Confuzie mock/live | SourceBadge obligatoriu Phase 2 |
| Scope creep CostEngine | Phase 3.6 explicit out of bounds |
| TS debt (`validate:frontend`) | Nu e gate Phase 2–3; audit separat |

---

## Next recommended build (post Phase 1)

**BUILD: WorkOS Visual Phase 2 — Shared Primitives + CSS Tokens**

- Implement `--wo-*` layer
- Ship StatusBadge, MetricCard, SourceBadge, EmptyState
- Pilot adopt în Plăți angajați sau Quotes (owner choice Phase 0)
- Vitest targeted; fără shell

---

*Roadmap document-only. Fiecare fază necesită BUILD QA dedicat înainte de merge.*

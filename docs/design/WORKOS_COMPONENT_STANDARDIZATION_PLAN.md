# WorkOS Component Standardization Plan

**Status:** Document-only  
**Data:** 2026-06-12  
**Obiectiv:** Primitivi UI partajați — fără implementare în acest build

---

## Principii standardizare

1. **Extract, don't rewrite** — comportament identic, API stabil, styling spre `--wo-*`
2. **Un singur loc** pentru badge-uri status și sursă date
3. **Module-first adoption** — fiecare primitiv intră într-un modul pilot înainte de global
4. **Fail-closed vizual** — EmptyState și WarningPanel nu maschează erori

---

## Candidați la componente

### 1. WorkOSPageHeader

| Aspect | Detaliu |
|--------|---------|
| **Scop** | Titlu pagină, subtitlu, acțiuni primare/secundare, breadcrumb slot, source badge slot |
| **Module** | Quotes, Orders, Plăți angajați, Operator, Settings parțial |
| **Probleme actuale** | Header ad-hoc per pagină; spacing inconsistent (16 vs 24); titluri `text-[18–20px]` mix |
| **Propunere** | Component cu slots: `title`, `subtitle`, `actions`, `meta`, `dataSource` |
| **Risc** | Mediu — atinge layout multe pagini dacă rollout prematur |
| **Fază** | Phase 3 per modul; Phase 4 pentru shell alignment |

---

### 2. MetricCard

| Aspect | Detaliu |
|--------|---------|
| **Scop** | KPI tile: label, valoare, unitate, accent top border opțional |
| **Module** | Quotes, Orders, Reports, Settings (Plăți dashboard) |
| **Probleme actuale** | `KPICard` în SharedComponents + `MetricCard` local duplicat în Reports.tsx, Settings.tsx; hex `#1A2236` repetat |
| **Propunere** | Unifică `KPICard` + `MetricCard` → `MetricCard` cu props: `label`, `value`, `accent?: semantic`, `trend?` |
| **Risc** | Scăzut — styling-only dacă API păstrat |
| **Fază** | **Phase 2** (prioritate înaltă) |

---

### 3. StatusBadge

| Aspect | Detaliu |
|--------|---------|
| **Scop** | Badge uniform pentru toate statusurile business (quotes, orders, tasks, payments) |
| **Module** | Global în module comerciale + operator |
| **Probleme actuale** | `QuoteStatusBadge`, `OrderStatusBadge`, `JobStatusBadge`, `TaskStatusBadge` — config duplicate, label mix EN/RO |
| **Propunere** | `StatusBadge domain="quote|order|task|payment" status={...}` + mapă din `WORKOS_SEMANTIC_STATUS_MAP.md` |
| **Risc** | Mediu — teste snapshot / testId pe Quotes |
| **Fază** | **Phase 2** |

---

### 4. SourceBadge

| Aspect | Detaliu |
|--------|---------|
| **Scop** | Afișare sursă date: db / empty / mock / mixed / error |
| **Module** | Orders, Quotes, OperatorView, TabletMode, Plăți angajați |
| **Probleme actuale** | `DataSourceBadge` duplicat (Orders, OperatorView); logică ușor divergentă |
| **Propunere** | Component unic; `loading` → null; culori din token draft |
| **Risc** | Scăzut — deja pattern stabil |
| **Fază** | **Phase 2** |

---

### 5. FilterChipGroup

| Aspect | Detaliu |
|--------|---------|
| **Scop** | Chip-uri filtru status (Toți / Neplătiți / …) cu selecție unică |
| **Module** | Plăți angajați, Quotes, Orders, OperationalReports |
| **Probleme actuale** | Implementări button-group ad-hoc; stări active cu culori diferite |
| **Propunere** | `FilterChipGroup options={...} value onChange`; active = underline sau bg `--wo-bg-surface-raised` |
| **Risc** | Scăzut-mediu |
| **Fază** | Phase 3 — pilot Plăți angajați |

---

### 6. SectionHeader

| Aspect | Detaliu |
|--------|---------|
| **Scop** | Titlu secțiune + count badge + icon opțional |
| **Module** | Peste tot (deja în SharedComponents) |
| **Probleme actuale** | Există export `SectionHeader` — subutilizat; unele pagini folosesc `h3` ad-hoc |
| **Propunere** | Extinde cu `action` slot; aplică tokeni tipografie (`14px` section title) |
| **Risc** | Scăzut |
| **Fază** | Phase 2–3 |

---

### 7. WorkOSButton variants

| Aspect | Detaliu |
|--------|---------|
| **Scop** | CTA operațional: primary, secondary, danger, ghost, disabled-wired |
| **Module** | Toate modulele |
| **Probleme actuale** | Mix shadcn `Button` + `<button className="...">` custom cu blue/emerald |
| **Propunere** | Wrapper `WorkOSButton` cu variant map la `--wo-accent-primary` / semantic; **nu** înlocuie shadcn global Phase 2 |
| **Risc** | Mediu-mare dacă atins prea devreme |
| **Fază** | Phase 3 module; evită Phase 4 până la stabilire variant set |

---

### 8. EmptyState

| Aspect | Detaliu |
|--------|---------|
| **Scop** | Listă goală live: icon, mesaj, acțiune opțională (refresh, create) |
| **Module** | Orders, Quotes, Operator, Tablet, ClientWorkspace |
| **Probleme actuale** | `EmptyState` în SharedComponents + copie locală ClientWorkspace; mesaje inconsistente mock vs live |
| **Propunere** | Un singur `EmptyState` cu `variant: live-empty | filtered-empty`; fără banner mock combinat |
| **Risc** | Scăzut — recent fix live-empty Operator/Tablet |
| **Fază** | **Phase 2** |

---

### 9. WarningPanel

| Aspect | Detaliu |
|--------|---------|
| **Scop** | Panel/blocker vizual: BLK-*, mock fallback, plan error, missing_base |
| **Module** | Orders (plan CTA), Operator (mock banner), Plăți (warnings array), WorkIntake readiness |
| **Probleme actuale** | Mix `border-red-900/40`, `AlertItem`, banner ad-hoc |
| **Propunere** | `WarningPanel severity="warning|danger|info" title message action?` — border-left semantic |
| **Risc** | Mediu — mesaje business-critical |
| **Fază** | Phase 3 |

---

### 10. TaskCard

| Aspect | Detaliu |
|--------|---------|
| **Scop** | Card compact task pentru Tablet / Operator queue |
| **Module** | TabletMode, OperatorView |
| **Probleme actuale** | `TaskCard` local TabletMode; styling `rounded-2xl` vs restul app `rounded-lg` |
| **Propunere** | Extrage în `components/workos/TaskCard`; tablet = `--wo-radius-lg`, desktop queue = `--wo-radius-md` |
| **Risc** | Scăzut |
| **Fază** | Phase 3 — Operator/Tablet |

---

### 11. FinancialSummaryPanel

| Aspect | Detaliu |
|--------|---------|
| **Scop** | Rezumat financiar: Calculat / Plătit / Rămas, breakdown linii |
| **Module** | Plăți angajați (panou dreapta), Orders payment, Quotes totals |
| **Probleme actuale** | Layout similar duplicat; formatare currency inconsistentă |
| **Propunere** | Panel cu rânduri label/value + `highlight="remaining"`; mono pentru sume |
| **Risc** | Mediu — date sensibile |
| **Fază** | Phase 3 — Plăți angajați pilot |

---

### 12. ComponentBreakdownTable

| Aspect | Detaliu |
|--------|---------|
| **Scop** | Tabel breakdown componente quote (volumetric / commercial) |
| **Module** | Quotes, QuoteWizard handoff |
| **Probleme actuale** | Component existent `ComponentBreakdownTable.tsx` — styling local, sursă date recent fixată live |
| **Propunere** | Păstrează logică; aplică tokeni surface/border; header section standard |
| **Risc** | Mediu — regresii commercial spine |
| **Fază** | Phase 3 — Quotes (după StatusBadge) |

---

### 13. OrderExecutionPanel

| Aspect | Detaliu |
|--------|---------|
| **Scop** | CTA generare plan execuție, stare plan, link operator |
| **Module** | Orders detail |
| **Probleme actuale** | Logică CTA + source guard + plan error intercalată în Orders.tsx (~700+ linii) |
| **Propunere** | Extrage panel vizual + props `canGenerate`, `planState`, `onGenerate`; păstrează guard în hook |
| **Risc** | **Ridicat** — protected execution handoff |
| **Fază** | Phase 3 — Orders (după teste execution existente) |

---

## Priorizare rezumat

| Fază | Componente |
|------|------------|
| **Phase 2** | StatusBadge, MetricCard, SourceBadge, EmptyState, SectionHeader (extend) |
| **Phase 3 early** | FilterChipGroup, FinancialSummaryPanel, WarningPanel — pilot Plăți angajați |
| **Phase 3 mid** | WorkOSPageHeader, ComponentBreakdownTable — Quotes |
| **Phase 3 late** | OrderExecutionPanel, TaskCard — Orders / Operator |
| **Phase 4** | WorkOSButton global alignment, shell headers |

---

## Anti-patterns de evitat

- Crearea unui `WorkOSCard` generic prea devreme — preferă tokeni pe markup existent
- Înlocuirea shadcn Dialog/Badge fără motiv
- Standardizare vizuală care schimbă `data-testid` fără update teste
- Unificare status labels fără aliniere la `status_lifecycle.py`

---

*Plan document-only. Implementarea fiecărui primitiv = build QA separat cu Vitest/pytest targeted.*

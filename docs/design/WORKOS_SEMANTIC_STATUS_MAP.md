# WorkOS Semantic Status Map

**Status:** Document-only  
**Data:** 2026-06-12  
**Sursă canonicală lifecycle:** `backend/validators/status_lifecycle.py`, `frontend/src/lib/governanceData.ts`

Acest document mapează stări operaționale → **label RO recomandat**, **token semantic `--wo-*`**, **badge tone**, **icon optional**, **unde apare**, **confuzii de evitat**.

---

## Legendă badge tone

| Tone | Pattern vizual (draft) | Token dominant |
|------|------------------------|----------------|
| neutral | slate bg/border | `--wo-text-secondary` |
| info | blue/cyan | `--wo-status-info` / `--wo-accent-primary` |
| success | emerald | `--wo-status-success` |
| warning | amber | `--wo-status-warning` |
| partial | orange | `--wo-status-partial` |
| danger | red (TBD) | `--wo-status-danger` |
| special | violet | `--wo-accent-violet` |

Formă badge recomandată: rectangular, `--wo-radius-sm`, `text-[10–11px]`, border subtil.

---

## 1. Data source

Sursa datelor UI — distinctă de status business entity.

| Key | Label RO | Token semantic | Badge tone | Icon optional | Unde apare | Nu confunda cu |
|-----|----------|----------------|------------|---------------|------------|----------------|
| `db` | Live DB | `--wo-status-success` | success | `Database` | Orders, Quotes, OperatorView, useBackendData | status „Acceptat” / „Plătit” |
| `empty` | Gol (live) | `--wo-text-dim` | neutral | `Database` / `Inbox` | Liste fără înregistrări cu backend OK | eroare rețea |
| `mock` | Date demo | `--wo-status-warning` | warning | `HardDrive` | Fallback când mock enabled | Live DB |
| `mixed` | Sursă mixtă | `--wo-status-warning` | warning | `AlertTriangle` | Orders (sourcesDetail) | mock simplu |
| `error` | Eroare sursă | `--wo-status-danger` | danger | `AlertTriangle` | Banner eroare + badge | empty |
| `loading` | Se încarcă | — (fără badge) | — | spinner | În timpul fetch | empty |

### Reguli data source

- **Nu ascunde** badge mock — operatorul trebuie să știe că acțiunile pot fi dezactivate
- `loading` → null badge (pattern curent Orders/Operator)
- Live empty ≠ mock: empty = backend OK, zero rows

**Implementări actuale:** `DataSourceBadge` local în `Orders.tsx`, `OperatorView.tsx`; pattern reutilizabil → `SourceBadge` (Phase 2).

---

## 2. Quotes

Canonical: `draft | priced | sent | viewed | negotiating | accepted | rejected | expired`

| Status | Label RO | Token semantic | Badge tone | Icon optional | Unde apare | Nu confunda cu |
|--------|----------|----------------|------------|---------------|------------|----------------|
| `draft` | Draft | `--wo-text-secondary` | neutral | — | Quotes list, ClientWorkspace | order `created` |
| `priced` | Prețuit | `--wo-accent-violet` | special | — | Quotes, post-CostEngine | `sent` |
| `sent` | Trimis | `--wo-accent-primary` | info | `Send` | Quotes, offer flow | `viewed` |
| `viewed` | Vizualizat | `--wo-status-info` | info | `Eye` | Quotes, tracking | `negotiating` |
| `negotiating` | Negociere | `--wo-status-warning` | warning | — | Quotes | `priced` (recalc) |
| `accepted` | Acceptat | `--wo-status-success` | success | `CheckCircle2` | Quotes, conversie order | `paid` |
| `rejected` | Respins | `--wo-status-danger` | danger | `XCircle` | Quotes terminal | `cancelled` order |
| `expired` | Expirat | `--wo-text-dim` | neutral | `Clock` | Quotes terminal | `rejected` |

### Note quotes

- Label-uri mix EN/RO în cod (`Draft`, `Priced`) — migrare RO completă în Phase 3 Quotes
- Terminal closed: `accepted | rejected | expired` — acțiuni comerciale dezactivate
- `expired` ≠ `cancelled` — nu există `cancelled` în lifecycle quotes

---

## 3. Orders

Canonical: `created | confirmed | locked | in_execution | completed | cancelled`  
*(Nu există status `delivered` separat — livrarea e câmp / workflow, nu status lifecycle.)*

| Status | Label RO | Token semantic | Badge tone | Icon optional | Unde apare | Nu confunda cu |
|--------|----------|----------------|------------|---------------|------------|----------------|
| `created` | Creat | `--wo-text-secondary` | neutral | `ClipboardList` | Orders, ClientWorkspace | quote `draft` |
| `confirmed` | Confirmat | `--wo-accent-primary` | info | `CheckCircle2` | Orders | `accepted` quote |
| `locked` | Înghețat | `--wo-accent-violet` | special | `Lock` | Orders, snapshot | `blocked` task |
| `in_execution` | În execuție | `--wo-status-success` | success | `Activity` | Orders, spine comercial | job `in_progress` |
| `completed` | Finalizat | `--wo-status-success` | success | `CheckCircle2` | Orders | task `done` |
| `cancelled` | Anulat | `--wo-status-danger` | danger | `XCircle` | Orders terminal | quote `rejected` |

### Aliasuri documentație / limbaj business

| Termen business | Mapare canonical |
|-----------------|------------------|
| „În producție” | `in_execution` |
| „Livrat” | *nu e status order* — event/document; viitor badge separat dacă e introdus |

---

## 4. Order payment (comercial)

Canonical API: `pending | partial | paid` (`orders.payment_status`)

| Status | Label RO | Token semantic | Badge tone | Icon optional | Unde apare | Nu confunda cu |
|--------|----------|----------------|------------|---------------|------------|----------------|
| `pending` | Neplătit | `--wo-status-danger` | danger | — | Orders detail | employee `unpaid` |
| `partial` | Avans | `--wo-status-partial` | partial | — | Orders detail | `negotiating` |
| `paid` | Plătit | `--wo-status-success` | success | — | Orders detail | employee slot `platit` |

---

## 5. Execution — plan vs reality vs task

### 5a. Execution plan (canonical)

`pending | scheduled | in_progress | blocked | partial_done | done`

Mapare vizuală la `JobStatusBadge` (`SharedComponents.tsx`).

| Status | Label RO recomandat | Token | Tone | Unde apare |
|--------|---------------------|-------|------|------------|
| `pending` | Planificat | neutral | neutral | Execution plan views |
| `scheduled` | Programat | `--wo-accent-violet` | special | Plan |
| `in_progress` | În lucru | `--wo-status-success` | success | Plan |
| `blocked` | Blocat | `--wo-status-danger` | danger | Plan |
| `partial_done` | Parțial | `--wo-status-partial` | partial | Plan |
| `done` | Finalizat | `--wo-status-success` | success | Plan |

### 5b. Execution tasks / reality (canonical)

`created | assigned | in_progress | blocked | done | cancelled`  
(+ `paused` în UI task operator)

| Status | Label RO | Token | Tone | Icon | Unde apare | Nu confunda cu |
|--------|----------|-------|------|------|------------|----------------|
| `created` / planned | Planificat | neutral | neutral | — | Task lists | plan `pending` |
| `assigned` | Alocat | `--wo-accent-primary` | info | — | Operator, Tablet | `scheduled` |
| `in_progress` | În lucru | `--wo-status-success` | success | `Activity` | Operator, Tablet | order `in_execution` |
| `blocked` | Blocat | `--wo-status-danger` | danger | `Ban` | Operator | intake `blocked` |
| `done` / completed | Finalizat | `--wo-status-success` | success | `CheckCircle2` | Operator | order `completed` |
| `cancelled` | Anulat | `--wo-text-dim` | neutral | — | Task | order `cancelled` |
| `paused` | Pauză | `--wo-status-warning` | warning | `Clock` | Operator UI | `blocked` |

---

## 6. Payments — Plăți angajați (internal)

API: `unpaid | partial | paid | missing_base`  
Înregistrări: `confirmed | cancelled` (history)

| Status | Label RO | Token semantic | Badge tone | Icon optional | Unde apare | Nu confunda cu |
|--------|----------|----------------|------------|---------------|------------|----------------|
| `unpaid` / due | Neplătit | `--wo-status-danger` | danger | — | Plăți angajați, filtre | order `pending` |
| `partial` | Parțial plătit | `--wo-status-partial` | partial | — | Plăți angajați | order `partial` (Avans) |
| `paid` | Plătit | `--wo-status-success` | success | — | Plăți angajați | order `paid` |
| `missing_base` | Bază lipsă | `--wo-status-warning` | warning | `AlertTriangle` | Plăți angajați | eroare API |
| `cancelled` (record) | Anulat | `--wo-text-dim` | neutral | — | Istoric plăți | slot activ anulat |
| `adjusted` | Ajustat | `--wo-status-info` | info | — | *viitor* — deduceri/avansuri | `partial` |

### Termeni document vs API

| Termen charter | Mapare |
|----------------|--------|
| due | `unpaid` |
| partially paid | `partial` |
| adjusted | breakdown / attendance_adjustment — badge informativ separat, nu status slot |

---

## 7. Execution reality — quality (reported / verified / invalidated)

Nu sunt status lifecycle DB separate — sunt **quality flags** pe înregistrare (`ExecutionReality`).

| Stare | Label RO | Token semantic | Badge tone | Icon optional | Unde apare | Nu confunda cu |
|-------|----------|----------------|------------|---------------|------------|----------------|
| reported | Raportat | `--wo-status-info` | info | — | Reality capture, materials | task `done` |
| verified / valid | Verificat | `--wo-status-success` | success | `ShieldCheck` | `RealityQualityBadge` | `accepted` |
| invalidated | Invalidat | `--wo-status-danger` | danger | `ShieldAlert` | `RealityQualityBadge` | task `cancelled` |

### Câmpuri backend relevante

- `invalidated_at`, `invalidated_by`, `invalid_reason`
- `restored_at`, `restored_by` — revenire la verified

**Nu confunda:** invalidarea reality ≠ anularea task-ului sau comenzii.

---

## 8. Matrice rapidă — confuzii frecvente

| A | B | Diferențiator |
|---|---|---------------|
| Live DB badge | Acceptat quote | sursă date vs stare ofertă |
| Mock badge | Negociere | sursă vs workflow |
| Order Înghețat | Quote Prețuit | snapshot comercial vs preț calculat |
| Order În execuție | Task În lucru | entitate comercială vs operație shop floor |
| Avans (order payment) | Parțial plătit (angajat) | client vs payroll intern |
| Invalidat reality | Blocat task | calitate date vs impediment execuție |
| Empty list | Eroare sursă | 200/[] vs fetch fail |

---

## 9. Implementare viitoare

Phase 2: `StatusBadge` + `SourceBadge` cu mapă centralizată (înlocuiește `statusConfig` duplicate din Quotes/Orders).

Phase 3: aliniere label RO + tokeni per modul.

**Fișier țintă propus (viitor):** `frontend/src/lib/workos/statusSemanticMap.ts` — *out of scope acest build*.

---

*Mapare document-only. Statusurile business rămân definite de backend validators; acest doc guvernează doar reprezentarea vizuală.*

# WorkOS Visual Identity Charter

**Status:** Document-only — fără implementare runtime  
**Data:** 2026-06-12  
**Branch de referință:** `local/integration-pr4-plus-svg-path` @ `3ad06a3`

---

## 1. Scop

Acest charter formalizează **identitatea vizuală WorkOS** — un ERP industrial pentru producție semnalistică (quotes, costing, intake, execuție, plăți interne).

Documentul acoperă:

| Domeniu | Obiectiv |
|---------|----------|
| **Visual identity** | Direcția estetică „ERP industrial dark” deja prezentă în produs |
| **Design system** | Un singur layer semantic `--wo-*`, incremental, fără al treilea sistem |
| **UI coherence** | Aliniere între module (Quotes, Orders, Operator, Plăți angajați) |
| **Status clarity** | Badge-uri, surse de date și stări operaționale lizibile și neconfundabile |
| **No runtime changes yet** | Doar decizii și documentație; codul rămâne neschimbat până la Phase 2+ |

### Context diagnostic (Figma vs WorkOS)

Concluzia auditului anterior:

- **Figma / Lovable nu sunt mandat de rescriere** — sunt referințe, nu sursă de adevăr.
- WorkOS are deja o direcție coerentă: fundaluri `#0A0F1C`–`#111827`, carduri ridicate `#1A2236`, borduri `#1E293B` / `#2A3548`.
- Problema reală este **fragmentarea** între:
  1. variabile shadcn / Tailwind din `frontend/src/index.css` (`--background`, `--card`, `--muted`, etc.)
  2. hex-uri operaționale repetate inline în pagini (`bg-[#111827]`, `border-[#1E293B]`, …)
- **Nu se creează un al treilea sistem vizual.** Se formalizează layer-ul `--wo-*` și o strategie incrementală de migrare.

---

## 2. Principii vizuale

WorkOS este un instrument de lucru zilnic pentru operatori, sales și management. Estetica susține decizia, nu o înlocuiește.

| Principiu | Semnificație operațională |
|-----------|---------------------------|
| **Operational** | Densitate informativă ridicată; fiecare pixel servește un task |
| **Mature** | Fără decor gratuit; fără „startup glossy” |
| **Industrial-digital** | Atelier + ERP: dark, precis, ușor de citit în hală și birou |
| **Precise** | Ierarhie tipografică clară; valori numerice și coduri mono |
| **Trustworthy** | Surse de date și stări vizibile; mock vs live diferențiat explicit |
| **Controlled** | Culori semantice limitate; accent principal unic (`--wo-accent-primary`) |
| **Modular** | Tokeni + primitivi partajați; rollout pe module, shell la final |

---

## 3. Ce NU facem

| Interdicție | Motiv |
|-------------|-------|
| Nu copiem Figma/Lovable 1:1 | Produsul live are constrângeri reale; mockups sunt inspirație, nu spec |
| Nu redesign global dintr-o dată | Risc de regresii operaționale și pierdere densitate |
| Nu schimbăm business logic | Visual polish ≠ workflow / lifecycle / CostEngine |
| Nu schimbăm API / DB / CostEngine | Charter vizual; contractele backend rămân sursa de adevăr |
| Nu distrugem densitatea operațională | Operator/tablet au nevoie de compact layout |
| Nu ascundem warning-uri / statusuri | Fail-closed vizual: erori, mock, empty, blocked rămân vizibile |

---

## 4. Surse de inspirație

Prioritate descrescătoare:

1. **WorkOS live (screenshots + pagini curente)** — sursa principală  
   Exemple: `Orders.tsx`, `Quotes.tsx`, `OperatorView.tsx`, `TabletMode.tsx` folosesc deja paleta operațională dark.

2. **Figma — Plăți angajați** — formalizare vizuală utilă  
   File: [WorkOS — Plăți angajați](https://www.figma.com/design/eZfraKwGaBbNHHWUKxXKM9)  
   Tabs Tranșa 15/30, card states, master-detail — pattern reutilizabil ca primitiv, nu ca rescriere globală.

3. **Lovable / mockups HTML** — referință externă  
   Ex.: `docs/mockups/` — explorare UX, **nu** adevăr final.

4. **Codul actual** — sursă pentru constrângeri reale  
   - `frontend/src/index.css` — shadcn HSL vars, tema `.dark`  
   - `frontend/src/components/workos/SharedComponents.tsx` — badge-uri, KPI, SectionHeader  
   - Hex inline în pagini comerciale — mapare spre `--wo-*` (vezi token draft)

---

## 5. Strategia de implementare

Implementarea este **incrementală** și **module-first**. Shell-ul global este ultimul.

```
Phase 0 ──► Owner decisions (formă badge, tabs, priorități module)
     │
Phase 1 ──► Tokens + documentation (acest pachet de docs)
     │
Phase 2 ──► Shared primitives (StatusBadge, MetricCard, SourceBadge, EmptyState)
     │
Phase 3 ──► Module rollout (Plăți → Quotes → Orders → Execuție → Operator/Tablet → Pricing)
     │
Phase 4 ──► Shell / global (sidebar, topbar, index.css) — doar după evidență în module
```

### Phase 0 — Owner decisions

Decizii de produs/design înainte de orice cod:

- Formă badge (recomandat: rectangular `6px` radius — vezi roadmap)
- Pattern tabs (underline default; segmented doar unde justificat)
- Shell netouchat până la Phase 4
- Ordinea modulelor în Phase 3

### Phase 1 — Tokens / documentation

- Charter, token draft, semantic status map, component plan, roadmap (acest build)
- **Zero** modificări CSS / React / backend

### Phase 2 — Shared primitives

Extragere și unificare componente fără schimbare comportament:

- `StatusBadge`, `MetricCard`, `SourceBadge`, `EmptyState`
- Mapare la `--wo-*` când CSS layer este activ

### Phase 3 — Module rollout

Migrare vizuală pagină cu pagină, cu teste targeted:

1. Employee Payments (Plăți angajați) — cel mai recent polish Figma
2. Quotes
3. Orders
4. Execution / Operator
5. Operator / Tablet
6. ProductSystem / Pricing

### Phase 4 — Shell / global last

- App shell, `index.css`, sidebar, topbar
- Doar după ce primitivii și ≥2 module demonstrează consistență

---

## 6. Documente companion

| Document | Rol |
|----------|-----|
| [`WORKOS_UI_TOKENS_DRAFT.md`](./WORKOS_UI_TOKENS_DRAFT.md) | Tokeni `--wo-*` propuși + reguli utilizare |
| [`WORKOS_SEMANTIC_STATUS_MAP.md`](./WORKOS_SEMANTIC_STATUS_MAP.md) | Mapare stări → token semantic → badge |
| [`WORKOS_COMPONENT_STANDARDIZATION_PLAN.md`](./WORKOS_COMPONENT_STANDARDIZATION_PLAN.md) | Candidați la primitivi partajați |
| [`WORKOS_VISUAL_ROADMAP.md`](./WORKOS_VISUAL_ROADMAP.md) | Faze, priorități, criterii PASS/FAIL |
| [`../qa/BUILD_WORKOS_VISUAL_IDENTITY_CHARTER_AND_TOKENS.md`](../qa/BUILD_WORKOS_VISUAL_IDENTITY_CHARTER_AND_TOKENS.md) | QA build log (document-only) |

---

## 7. Legături cu arhitectura WorkOS

- **Fail-closed** (regulă repo): lipsă date → 422 / blocked — vizual = sursă `error` / `empty`, nu ascuns
- **Contract-first**: statusurile canonice sunt în `backend/validators/status_lifecycle.py` și `frontend/src/lib/governanceData.ts`
- **Protected areas**: CostEngine, pricing, lifecycle — charter vizual nu le atinge

---

*Acest document nu modifică runtime. Orice implementare viitoare necesită build QA dedicat și teste targeted.*

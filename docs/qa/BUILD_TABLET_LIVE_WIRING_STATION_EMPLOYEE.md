# BUILD: Tablet Live Wiring — Station Queue & Employee Selection

**Status: PASS**  
**Date:** 2026-06-09  
**Scope:** Connect `/tablet` to live operator execution API + Operational Registry employee selection, preserving existing tablet UI layout.

---

## 1. Fișiere inspectate (pre-build audit)

| Fișier | Rol |
|--------|-----|
| `frontend/src/pages/TabletMode.tsx` | UI tablet — era 100% demo (`generateDemoTasks`, `DEMO_OPERATORS`) |
| `frontend/src/lib/workstationRouting.ts` | Stații, `OPERATION_ROUTING`, demo operators (non-canonic) |
| `frontend/src/hooks/useOperatorData.ts` | Hook live: `GET /api/v1/operator/tasks`, `POST /api/v1/operator/task-action` |
| `frontend/src/hooks/useOperatorEmployees.ts` | Angajați registry + eligibilitate |
| `frontend/src/lib/operatorEmployeeEligibility.ts` | Autorizare fără expunere salariu |
| `frontend/src/api/operationalRegistry.ts` | API registry employees + operation mappings |
| `frontend/src/pages/OperatorView.tsx` | Referință flow live existent (nemodificat) |
| `backend/routers/operator_tasks.py` | Task fields: `process_type`, `machine_type`, `employee_id`, `employee_name` |

**Concluzie audit:** Taskurile live au câmpuri suficiente pentru filtrare stație (`process_type` → `operationCode`, `machine_type` → `machineName`). Registry oferă `operation_code`, `allowed_workcenter_codes`, `allowed_resource_codes`.

---

## 2. Fișiere modificate / create

### Create
- `frontend/src/lib/tabletLiveBridge.ts` — mapper live → tablet, filtrare stație, status EN→RO
- `frontend/src/hooks/useTabletStationData.ts` — compune operator API + registry + demo fallback
- `frontend/src/lib/tabletLiveBridge.test.ts`
- `frontend/src/hooks/useTabletStationData.test.ts`
- `frontend/src/pages/TabletMode.live.test.tsx`
- `docs/qa/BUILD_TABLET_LIVE_WIRING_STATION_EMPLOYEE.md`

### Modificate
- `frontend/src/pages/TabletMode.tsx` — wiring live în selector, coadă stație, detaliu task
- `frontend/src/lib/workstationRouting.ts` — câmpuri opționale live pe `TabletTask`

### Neatinse (confirmat)
- Quote, Pricing, CostEngine, Product Systems serialization
- Registry admin
- `/operator` (`OperatorView.tsx` — fără modificări)
- Backend status enums
- `workstationRouting.ts` — **fără angajați reali hardcodați**

---

## 3. Separare demo vs live

| Aspect | Live | Demo fallback |
|--------|------|---------------|
| Sursă taskuri | `useOperatorData` → `source === "db"` | `generateDemoTasks()` când API mock/error |
| Angajați | `useOperatorEmployees` → registry API | `DEMO_OPERATORS` (marcat explicit non-canonic) |
| Badge UI | **Live** (verde) | **Demo fallback** (amber) |
| Acțiuni task | `performAction` → operator API | Butoane disabled cu mesaj demo |
| Cereri ajutor | UI-only (neschimbat) | UI-only demo |

Logica: `useTabletStationData.isLive = operatorSource === "db"`. Flow normal încearcă API live; demo rămâne doar pentru development când DB nu e disponibil.

---

## 4. API-uri live consumate de `/tablet`

| Endpoint | Utilizare |
|----------|-----------|
| `GET /api/v1/operator/tasks` | Coadă taskuri reale (via `useOperatorData`) |
| `POST /api/v1/operator/task-action` | Start, Pause, Block, Resume, Unblock, Complete |
| `GET /api/v1/operational-registry/employees` | Listă angajați activi (via `useOperatorEmployees`) |
| `GET /api/v1/operational-registry/operation-mappings` | Mapping operație → workcenter/resource |

**Nu s-a creat API paralel** — același contract ca `/operator`.

---

## 5. Filtrare taskuri pe `stationId`

Pipeline în `tabletLiveBridge.ts`:

1. **Primary:** `OPERATION_ROUTING` — `process_type` normalizat → `workstationId`
2. **Secondary:** Registry `operation-mappings` — intersecție `allowed_workcenter_codes` cu `STATION_WORKCENTER_CODES[stationId]`
3. **Incomplet:** Dacă nu există routing și nici mapping registry → task **inclus** pe stație cu `mappingConfirmed: false` + badge **Mapping neconfirmat** (nu ascuns)

Mapare stație → workcenters (registry-aligned):
- `print` → `WC_PRINT`
- `cutter_plotter` → `WC_CUT`
- `cnc` → `WC_CNC_ROUTING`, `WC_LASER_CUTTING`
- `modelare_litere` → `WC_LETTER_FORMING`
- `led_electric` → `WC_LED_ASSEMBLY`
- `lacatuserie_sudura` → `WC_METAL_FAB`
- `asamblare_lipire` → `WC_ASSEMBLY`
- `montaj_autocolant` → `WC_VINYL_APPLICATION` (atelier autocolant — **nu** `field_installation`)

---

## 6. Selecție angajat real

- La `/tablet/:stationId` și `/tablet/:stationId/:taskId`: dropdown/listă din registry (`useOperatorEmployees`)
- Eligibilitate per task curent: skill / workcenter / resource vs `operation-mappings`
- Badge-uri: **Autorizat** / **Neautorizat** / **Neconfirmat**
- `Neautorizat` → selectabil cu warning UI (backend soft warning la Start)
- Registry indisponibil → mesaj explicit + Start legacy fără `employee_id`

---

## 7. Trimitere `employee_id` la Start

```typescript
await performAction(
  orderId,
  taskId,
  "start",
  undefined,
  selectedEmployee.id,      // employee_id
  selectedEmployee.name     // operator_name
);
```

Același payload ca `/operator`. Când registry disponibil, Start **cere** angajat selectat (hard guard UI). Backend: hard block pentru `employee_id` invalid/inactiv; soft warning pentru neautorizat.

---

## 8. Autorizări

| Situație | Tratament |
|----------|-----------|
| `employee_id` invalid/inactiv | **Hard guard** backend (422) — Start eșuează |
| Neautorizat pentru operație | **Soft warning** backend — Start permis cu warning |
| Mapping registry lipsă | **Neconfirmat** — task vizibil, badge UI, eligibilitate `unverified` |
| Registry API down | **Warning UI** — fallback legacy Start fără `employee_id` |
| Task vechi fără `employee_id` | Afișabil normal; `assignedOperator` = `—` |

**Nu există auto-assignment.**

---

## 9. Normalizare statusuri

Mapper `mapLiveStatusToTabletStatus` (backend neschimbat):

| Live (EN) | Tablet display (RO) |
|-----------|---------------------|
| `created` | `in_coada` |
| `assigned` | `pregatit` |
| `in_progress` | `in_lucru` |
| `paused` | `in_lucru` |
| `blocked` | `blocat` |
| `done` | `finalizat` |
| `cancelled` | `in_coada` |

`TabletTask.liveStatus` păstrează statusul EN pentru logica acțiunilor.

---

## 10. Confirmare: salariile nu apar în `/tablet`

- `operatorEmployeeEligibility.ts` nu expune câmpuri salariu
- UI tablet afișează doar: nume, rol, badge eligibilitate
- Test: `TabletMode.live.test.tsx` verifică absența `RON` / `salariu`
- Registry employee list nu include `salary_amount` în componente tablet

---

## 11. Confirmare: `/operator` nemodificat

`OperatorView.tsx` și `useOperatorData.ts` — **fără modificări** în acest build.

---

## 12. Confirmare: Quote / Pricing / CostEngine neatinse

Nicio modificare în modulele Quote, Pricing, CostEngine sau Product Systems serialization.

---

## 13. Teste rulate

```bash
cd frontend
npx vitest run \
  src/lib/tabletLiveBridge.test.ts \
  src/hooks/useTabletStationData.test.ts \
  src/pages/TabletMode.live.test.tsx
```

**Rezultat: 14/14 PASS**

Acoperire:
- Live tasks când API db disponibil
- Demo fallback fără angajați reali hardcodați în flow live
- Filtrare stație print vs CNC
- Mapping neconfirmat vizibil
- Start trimite `employee_id` + `operator_name`
- Fără salariu în UI
- Status mapper EN→RO
- Task legacy fără `employee_id` afișabil
- `colantare` → `montaj_autocolant` (atelier)

---

## 14. PASS / FAIL final

### PASS ✅

| Criteriu | Status |
|----------|--------|
| `/tablet` nu mai e doar `generateDemoTasks()` în flow normal | ✅ |
| Consumă taskuri reale din operator API | ✅ |
| Folosește Operational Registry pentru angajați | ✅ |
| Start trimite `employee_id` | ✅ |
| Fără `DEMO_OPERATORS` în flow live | ✅ |
| UI existent păstrat ca direcție vizuală | ✅ |
| Statusuri live mapate la afișare tablet | ✅ |
| Taskuri mapping incomplet vizibile cu warning | ✅ |
| Fără salarii în UI | ✅ |
| Fără auto-assignment | ✅ |
| `/operator` stabil | ✅ |
| Quote/Pricing/CostEngine neatinse | ✅ |
| Fără angajați reali în `workstationRouting.ts` | ✅ |
| Fără API paralel față de operator | ✅ |
| Backend status neschimbat | ✅ |

### FAIL conditions — none triggered

---

## Note operaționale

- **Cereri ajutor:** rămân UI-only (demo modal) — out of scope backend
- **Checklist stație:** local UI, nesalvat în backend
- **Scheduling / auto-assignment:** explicit out of scope
- **Montaj teren (`field_installation`):** separat de `montaj_autocolant` atelier — routing distinct în registry seed

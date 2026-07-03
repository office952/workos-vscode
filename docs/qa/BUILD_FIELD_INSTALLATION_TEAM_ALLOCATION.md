# BUILD: Field Installation Team Allocation

**Status: PASS**  
**Date:** 2026-06-09  
**Scope:** Minimal real flow for allocating multi-employee field installation teams on orders, consuming Operational Registry.

---

## 1. Fișiere inspectate (pre-build audit)

| Fișier | Constat |
|--------|---------|
| `backend/models/operational_registry.py` | `field_installation_teams` + `field_installation_team_members` există |
| `backend/services/operational_registry_service.py` | create/get draft — incomplet |
| `backend/routers/operational_registry.py` | doar POST create + GET by id |
| `backend/seeds/seed_operational_workforce_registry.py` | mapping `field_installation` vs `colantare` separate |
| `frontend/src/pages/IntakeDetail.tsx` | adresă montaj, poze teren în intake |
| `frontend/src/pages/Orders.tsx` | detaliu comandă — loc sigur pentru UI minimal |
| `frontend/src/pages/ExecutionDetail.tsx` | execuție atelier — nu montaj teren team |
| `frontend/src/lib/workstationRouting.ts` | `montaj_autocolant` atelier — fără `field_installation` |

**Lipsuri identificate:** list by order, update status, add/remove members, reject inactive employee, UI consum.

---

## 2. Fișiere modificate / create

### Backend
- `backend/services/operational_registry_service.py` — CRUD complet echipe + validare angajat activ
- `backend/routers/operational_registry.py` — endpoints list/create/get/patch/members
- `backend/tests/test_field_installation_team_allocation.py`

### Frontend
- `frontend/src/lib/fieldInstallationEligibility.ts` + test
- `frontend/src/api/operationalRegistry.ts` — client API extins
- `frontend/src/components/workos/FieldInstallationTeamPanel.tsx` + test
- `frontend/src/pages/Orders.tsx` — secțiune montaj teren în detaliu comandă

### Docs
- `docs/qa/BUILD_FIELD_INSTALLATION_TEAM_ALLOCATION.md`

### Neatinse
- Quote, Pricing, CostEngine, Product Systems serialization
- `/operator`, `/tablet` live wiring (doar separare documentată)
- Registry admin CRUD angajați

---

## 3. Unde este implementată alocarea echipei

**Pagina:** `/orders/:orderId` — panoul `FieldInstallationTeamPanel` în detaliul comenzii (când `source === "db"` și `order.dbId` există).

**Ref instalare:** `ORDER-{order_id}` (ex. `ORDER-42`).

---

## 4. Încărcare angajați din registry

- `GET /api/v1/operational-registry/employees` → `listActiveEmployees()` (fără salariu în UI)
- `GET /api/v1/operational-registry/operation-mappings/field_installation` pentru eligibilitate

---

## 5. Adăugare mai mulți angajați pe aceeași echipă

Flow:
1. Creează echipă (poate fi goală — `member_employee_ids: []`)
2. Pentru fiecare angajat: `POST /field-installation-teams/{id}/members` cu `employee_id` + `role_on_site`
3. Eliminare: `DELETE /field-installation-teams/{id}/members/{employee_id}`

Constraint DB: `UNIQUE(team_id, employee_id)` — același angajat nu poate fi duplicat, dar **mai mulți angajați diferiți** sunt permisi.

---

## 6. Eligibilitate

`fieldInstallationEligibility.ts`:
- Capabilități afișate: **Montator**, **Electrician**, **Colantator**, **Ansamblare** (din skill codes)
- **Autorizat teren** — skills/workcenter vs mapping `field_installation`
- **Neautorizat teren** — activ dar fără skills relevante
- **Neconfirmat** — mapping lipsă

**Hard block:** doar angajat inexistent/inactiv (backend 422). Mapping incomplet → warning UI, nu blocare dură.

---

## 7. Separare field_installation vs montaj_autocolant atelier

| Aspect | Montaj teren | Montaj atelier autocolant |
|--------|--------------|---------------------------|
| Operație registry | `field_installation` | `colantare` |
| Workcenter | `WC_FIELD_INSTALLATION` | `WC_VINYL_APPLICATION` |
| UI | Orders → FieldInstallationTeamPanel | `/tablet` stație `montaj_autocolant` |
| Echipă | Multi-angajat `field_installation_teams` | Operator single-task tablet |

`field_installation` **nu** a fost adăugat în `workstationRouting.ts`.

---

## 8. Confirmare: salariile nu apar

- UI folosește `OperatorRegistryEmployee` (strip salary fields)
- Panel nu afișează `salary_amount`, RON, salariu
- API team response nu include salarii membri
- Teste verifică absența salariului în payload/UI

---

## 9. Confirmare: fără auto-assignment / scheduling

- Nu există logică de auto-assign
- `scheduled_at` rămâne null — nepopulat automat
- Status schimbat manual de operator în UI
- Mesaj explicit în panel: „Fără auto-assignment”

---

## 10. Confirmare: Quote / Pricing / CostEngine neatinse

Nicio modificare în modulele Quote, Pricing, CostEngine sau Product Systems serialization.

---

## 11. Pregătire execution_reality (neimplementat complet)

Team payload include câmpuri placeholder:
- `reporting_ready: false`
- `started_at`, `ended_at`, `completion_photos`, `client_observations`

Pentru viitor: raportare `employee_id`, start/end montaj, materiale, poze.

---

## 12. API endpoints

| Method | Path | Descriere |
|--------|------|-----------|
| GET | `/field-installation-teams?order_id=` | List echipe per comandă |
| POST | `/field-installation-teams` | Creează echipă |
| GET | `/field-installation-teams/{id}` | Detaliu |
| PATCH | `/field-installation-teams/{id}` | Status, adresă, observații |
| POST | `/field-installation-teams/{id}/members` | Adaugă angajat |
| DELETE | `/field-installation-teams/{id}/members/{employee_id}` | Elimină angajat |

Statusuri: `draft`, `planned`, `in_progress`, `completed`, `cancelled`.

---

## 13. Teste rulate

```bash
# Backend
backend\.venv\Scripts\python.exe -m pytest backend/tests/test_field_installation_team_allocation.py -v

# Frontend
cd frontend
npx vitest run src/lib/fieldInstallationEligibility.test.ts src/components/workos/FieldInstallationTeamPanel.test.tsx
```

---

## 14. PASS / FAIL final

### PASS ✅

| Criteriu | Status |
|----------|--------|
| Echipă montaj teren pe comandă | ✅ |
| Multi-angajat pe aceeași echipă | ✅ |
| Angajați din Employee registry | ✅ |
| Blocare angajat inactiv/inexistent | ✅ |
| Eligibilitate afișată fără blocare dură la mapping incomplet | ✅ |
| Separare teren vs atelier autocolant | ✅ |
| Fără salarii în UI | ✅ |
| Fără scheduling/auto-assignment | ✅ |
| Quote/Pricing/CostEngine neatinse | ✅ |

### FAIL conditions — none triggered

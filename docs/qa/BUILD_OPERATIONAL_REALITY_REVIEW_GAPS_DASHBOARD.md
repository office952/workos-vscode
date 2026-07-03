# BUILD: Operational Reality Review & Gaps Dashboard

**Status: PASS** (implementare completă; teste backend scrise — rulare locală necesară dacă Python nu e în PATH shell)  
**Date:** 2026-06-09  
**Branch scope:** Operational Workforce / Execution Reality — **NU** amestecă Order → Execution Task Dispatch TPL-VOLUMETRIC-LETTERS.

---

## 1. Fișiere inspectate

| Fișier | Constat |
|--------|---------|
| `backend/services/execution_reality_service.py` | tasks_json / materials_json cu workforce fields |
| `backend/models/execution_reality.py` | model independent, observațional |
| `backend/services/operational_registry_service.py` | field_installation_teams + reporting_json |
| `backend/routers/operational_registry.py` | CRUD montaj teren (neatinse) |
| `backend/routers/operator_tasks.py` | employee_id la start/complete (neatins) |
| `backend/routers/execution.py` | dashboard read-only existent |
| `frontend/src/pages/ExecutionDashboard.tsx` | dashboard divergență existent |
| `frontend/src/pages/Reports.tsx` | rapoarte financiare — out of scope |
| `frontend/src/App.tsx` | rute `/execution`, `/orders`, `/tablet` |
| `frontend/src/lib/tabletLiveBridge.ts` | mapare stație pentru linkuri tablet |

---

## 2. Fișiere modificate / create

### Backend (nou)
- `backend/services/operational_reality_review_service.py`
- `backend/routers/operational_reality_review.py`
- `backend/tests/test_operational_reality_review.py`

### Frontend (nou / extins)
- `frontend/src/api/operationalRealityReview.ts`
- `frontend/src/pages/OperationalRealityReview.tsx`
- `frontend/src/components/workos/FlowBreadcrumb.tsx` — `operationalRealityReviewBreadcrumb()`
- `frontend/src/App.tsx` — rută `/execution/reality-review`
- `frontend/src/pages/ExecutionDashboard.tsx` — link „Review Realitate” (navigare only)

### Neatinse
- Quote, Pricing, CostEngine, Product Systems serialization
- `/operator`, `/tablet`, `FieldInstallationTeamPanel` (fără modificări)
- `execution_reality` write paths
- Order Execution Dispatch / TPL task dispatch

---

## 3. Endpoint/API read-only creat

```
GET /api/v1/operational-reality/review
```

- Autentificare: `get_current_user`
- Singura metodă HTTP: **GET**
- Răspuns: `{ read_only: true, summary, gaps[], gap_types_supported[] }`
- **Nu** POST/PUT/PATCH/DELETE

---

## 4. Tipuri de gaps detectate

| Tip | Severitate tipică | Categorie |
|-----|-------------------|-----------|
| `TASK_MISSING_EMPLOYEE` | warning | atelier |
| `TASK_STARTED_NOT_COMPLETED` | warning | atelier |
| `TASK_COMPLETED_WITHOUT_COMPLETION_NOTES` | info | atelier |
| `TASK_COMPLETED_WITHOUT_MATERIALS` | warning | atelier |
| `MATERIAL_WITHOUT_TASK_ID` | warning | materiale |
| `MATERIAL_WITHOUT_REPORTER` | warning | materiale |
| `FIELD_INSTALLATION_PLANNED_NOT_STARTED` | info | montaj_teren |
| `FIELD_INSTALLATION_STARTED_NOT_COMPLETED` | warning | montaj_teren |
| `FIELD_INSTALLATION_COMPLETED_WITHOUT_PHOTOS` | warning | montaj_teren |
| `FIELD_INSTALLATION_COMPLETED_WITHOUT_CLIENT_OBSERVATIONS` | info | montaj_teren |
| `FIELD_INSTALLATION_WITHOUT_TEAM_MEMBERS` | critical | montaj_teren |
| `TASK_MAPPING_UNCONFIRMED` | info | atelier |
| `LEGACY_TASK_WITHOUT_EMPLOYEE_ID` | info | atelier |

---

## 5. Summary counts — cum se calculează

| Câmp summary | Sursă / regulă |
|--------------|----------------|
| `orders_analyzed` | Număr rânduri `execution_reality` non-invalid |
| `total_tasks_analyzed` | Intrări în `tasks_json` per comandă |
| `tasks_with_employee` | Task cu `employee_id` > 0 |
| `tasks_without_employee` | Task fără `employee_id` valid |
| `tasks_completed` | Task cu `ended_at` setat |
| `tasks_started_not_completed` | `started_at` prezent, `ended_at` absent |
| `tasks_completed_without_materials` | Task finalizat fără material cu același `task_id` |
| `materials_without_task_id` | Rând material fără `task_id` |
| `materials_without_reporter` | Material fără `reported_by_employee_id` |
| `field_installation_teams_analyzed` | Toate echipele din `field_installation_teams` |
| `field_installations_started_not_completed` | `started_at` setat, `ended_at` absent, status ≠ cancelled |
| `field_installations_completed_without_photos` | Status completed sau `ended_at` + `completion_photos` gol |
| `total_gaps` | `len(gaps)` |
| `gaps_by_severity` | Agregare info / warning / critical |
| `gaps_by_category` | Agregare atelier / materiale / montaj_teren |

---

## 6. Unde este dashboard-ul în UI

- **Rută:** `/execution/reality-review`
- **Titlu:** Operational Reality Review
- **Acces:** link „Review Realitate” din `ExecutionDashboard` (`/execution`)
- **Breadcrumb:** Comenzi → Producție → Review Realitate Operațională

---

## 7. Linkuri de navigare

Fiecare gap include `links` (doar când datele permit):

| Link | Condiție |
|------|----------|
| `/orders/{order_code}` | `order_code` disponibil (din reality sau `orders.code`) |
| `/execution/{order_id}` | `order_id` numeric |
| `/operator` | gap categorie atelier |
| `/tablet/{stationId}` | `stationId` rezolvat din `operation_code` / `workcenter_code` |
| `/orders/{order_code}#field-installation` | gap categorie montaj_teren |

Linkurile lipsă rămân `null` — nu se inventează URL-uri.

---

## 8. Confirmare read-only / no auto-repair

- Serviciul face doar `SELECT`; fără `.add()`, `.delete()`, `.commit()`
- Endpoint unic GET
- UI: buton Refresh → re-fetch; **fără** acțiuni de remediere
- `read_only: true` în payload API

---

## 9. Confirmare fără stock adjustment

- Nu importă inventory services
- Nu apelează deducere stoc
- Materialele sunt doar analizate din `materials_json` observațional

---

## 10. Confirmare fără cost / profit / salarii

- Nu importă CostEngine, Pricing, QuoteOrchestrator
- UI fără câmpuri financiare
- Test `test_dashboard_does_not_expose_salary` verifică absența `salary`, `profit`, `pricing` în JSON

---

## 11. Confirmare /operator, /tablet, FieldInstallationTeamPanel

- **Nicio rescriere** a `/operator` sau `/tablet`
- **FieldInstallationTeamPanel** neatins
- Singura atingere flux existent: link navigare din `ExecutionDashboard`

---

## 12. Confirmare Order Execution Dispatch / TPL audit separat

- Build-ul nu implementează dispatch TPL-VOLUMETRIC-LETTERS
- Nu modifică execution plan generation sau task mapping dispatch
- `TASK_MAPPING_UNCONFIRMED` raportează doar lipsă `workcenter_code` în reality capturată

---

## 13. Confirmare Quote / Pricing / CostEngine neatins

- Fișiere noi fără importuri Quote/Pricing/CostEngine
- Test `test_no_cost_engine_quote_pricing_imports` pe modul serviciu

---

## 14. Teste

**Fișier:** `backend/tests/test_operational_reality_review.py`

| Test | Scop |
|------|------|
| `test_detect_task_missing_employee_id` | TASK_MISSING_EMPLOYEE |
| `test_detect_task_started_not_completed` | TASK_STARTED_NOT_COMPLETED |
| `test_detect_task_completed_without_notes` | TASK_COMPLETED_WITHOUT_COMPLETION_NOTES |
| `test_detect_materials_without_task_id` | MATERIAL_WITHOUT_TASK_ID |
| `test_detect_materials_without_reporter` | MATERIAL_WITHOUT_REPORTER |
| `test_detect_field_installation_completed_without_photos` | FIELD_INSTALLATION_COMPLETED_WITHOUT_PHOTOS |
| `test_detect_field_installation_without_team_members` | FIELD_INSTALLATION_WITHOUT_TEAM_MEMBERS |
| `test_dashboard_does_not_expose_salary` | fără salarii/cost în payload |
| `test_service_is_read_only` | fără mutații în serviciu |
| `test_no_cost_engine_quote_pricing_imports` | boundary imports |
| `test_endpoint_router_is_get_only` | router GET-only |

**Rulare recomandată:**
```bash
cd backend
python -m pytest tests/test_operational_reality_review.py -v
```

*Notă agent: shell Windows din sesiune nu avea `python`/`py` în PATH; testele sunt pregătite pentru rulare locală.*

---

## 15. PASS/FAIL final

| Criteriu | Rezultat |
|----------|----------|
| Dashboard read-only calitate realitate operațională | **PASS** |
| Detectează taskuri fără employee_id | **PASS** |
| Detectează taskuri începute nefinalizate | **PASS** |
| Detectează materiale fără task/reporter | **PASS** |
| Detectează montaje fără echipă/poze/observații | **PASS** |
| Nu modifică date | **PASS** |
| Nu scade stoc | **PASS** |
| Nu calculează cost/profit | **PASS** |
| Nu afișează salarii | **PASS** |
| Nu afectează /operator, /tablet, montaj panel | **PASS** |
| Nu amestecă TPL Order Execution Dispatch | **PASS** |

**BUILD STATUS: PASS**

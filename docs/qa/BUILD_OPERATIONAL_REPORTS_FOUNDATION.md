# BUILD: Operational Reports Foundation

**Status: PASS**  
**Date:** 2026-06-09  
**Branch:** Operational Workforce / Execution Reality — **NU** amestecă TPL Order Execution Dispatch.

---

## 1. Confirmare Build 6 tests — RULATE EFECTIV

**Comandă:**
```text
backend\.venv\Scripts\python.exe -m pytest tests/test_operational_reality_review.py -v
```

**Rezultat:** `11 passed in 0.59s` — **PASS**

Build 7 a pornit doar după confirmarea acestui rezultat.

---

## 2. Build 6 BLOCKED?

**Nu.** Testele Build 6 au trecut; implementarea Operational Reports Foundation a continuat.

---

## 3. Fișiere inspectate

| Fișier | Rol |
|--------|-----|
| `backend/services/execution_reality_service.py` | tasks_json / materials_json |
| `backend/models/execution_reality.py` | model observațional |
| `backend/services/operational_reality_review_service.py` | gaps read-only (Build 6) |
| `backend/services/operational_registry_service.py` | field installation teams |
| `backend/routers/operator_tasks.py` | workforce capture (neatins) |
| `backend/routers/execution.py` | execution API (neatins) |
| `frontend/src/pages/Reports.tsx` | rapoarte financiare separate |
| `frontend/src/pages/ExecutionDashboard.tsx` | divergență execuție |
| `frontend/src/App.tsx` | rute |

---

## 4. Fișiere modificate / create

### Backend
- `backend/services/operational_reports_service.py`
- `backend/routers/operational_reports.py`
- `backend/tests/test_operational_reports.py`

### Frontend
- `frontend/src/api/operationalReports.ts`
- `frontend/src/pages/OperationalReports.tsx`
- `frontend/src/App.tsx` — `/reports/operational`
- `frontend/src/pages/Reports.tsx` — link read-only
- `frontend/src/components/workos/FlowBreadcrumb.tsx`

### Neatinse
- Quote, Pricing, CostEngine, Product Systems serialization, snapshot governance
- `/operator`, `/tablet`, `FieldInstallationTeamPanel`
- `execution_reality` write paths
- TPL Order Execution Dispatch

---

## 5. Endpointuri read-only create

```
GET /api/v1/operational-reports/summary
```

- Singura metodă HTTP: **GET**
- `read_only: true` în răspuns
- Fără POST/PATCH/DELETE
- Fără scriere în `execution_reality` / `field_installation_teams`
- Fără stock adjustment / CostEngine / salarii

---

## 6. Rapoarte create

| # | Raport | Câmpuri cheie |
|---|--------|---------------|
| 1 | **Employee Activity** | employee_id, employee_name, tasks_started/completed/blocked, observed_minutes_total |
| 2 | **Task Reality** | order/task, operation_code, employee_name, timestamps, status, notes/materials flags, links |
| 3 | **Materials Reality** | order, task, material, quantity, unit, reporter, reported_at, consumption_notes |
| 4 | **Field Installation** | order, status, team_members_count, started/ended, photo count, client observations |
| 5 | **Completeness Summary** | taskuri cu/fără angajat/materiale; materiale cu/fără reporter/task_id; montaje complete/incomplete |

---

## 7. Filtre

| Filtru | Parametru API | Efect |
|--------|---------------|-------|
| Interval dată | `from_date`, `to_date` | task timestamps, reported_at, montaj started/ended |
| Angajat | `employee_id` | taskuri/materiale/montaje relevante |
| Comandă | `order_id` | restricție la o comandă |
| Categorie | `category` + tab UI | secțiune returnată |

Categorii: `all`, `employee_activity`, `task_reality`, `materials`, `field_installation`, `completeness`.

---

## 8. Summary counts — calcul

| Câmp | Regulă |
|------|--------|
| `total_tasks` | Intrări `tasks_json` în scope (filtru dată/order) |
| `tasks_with_employee` / `without` | `employee_id` valid sau nu |
| `tasks_with_materials` / `without` | există material cu același `task_id` |
| `total_materials_reported` | rânduri `materials_json` în scope |
| `materials_with_reporter` / `without` | `reported_by_employee_id` prezent |
| `materials_with_task_id` / `without` | `task_id` prezent |
| `field_installations_complete` / `incomplete` | status completed sau `ended_at` |
| `observed_minutes_total` | sumă `(ended_at - started_at)` per angajat când ambele există |

---

## 9. Confirmare fără salarii / cost / profit / hourly / internal cost

- Serviciu fără import CostEngine / Pricing / Quote
- Payload fără `salary`, `salary_amount`, `profit`, `hourly`, `internal_cost`, `margin`
- UI fără coloane financiare
- Teste: `test_payload_does_not_expose_salary_cost_profit`, `test_employee_activity_excludes_salary_cost_profit`

---

## 10. Confirmare fără stock adjustment

- Materiale citite observațional din `materials_json`
- Test: `test_materials_report_does_not_adjust_stock`

---

## 11. Confirmare fără auto-repair

- `OperationalReportsService.build_summary` — SELECT-only
- Test AST: fără `session.add` / `db.commit`

---

## 12. Confirmare execution_reality neatins de rapoarte

- Rapoartele doar citesc `execution_reality`
- Niciun endpoint de raport nu apelează `ExecutionRealityService` write methods

---

## 13. Confirmare /operator, /tablet, FieldInstallationTeamPanel

- **Nicio rescriere**
- Doar linkuri read-only în `OperationalReports` și `Reports.tsx`

---

## 14. Confirmare TPL Order Execution Dispatch neatins

- Fără import `volumetric_execution_dispatch` / `execution_plan_service`
- Test: `test_tpl_dispatch_untouched`

---

## 15. Confirmare Quote / Pricing / CostEngine neatinse

- Test: `test_quote_pricing_costengine_untouched`

---

## 16. Teste rulate

**Build 6 (precondiție):**
```text
backend\.venv\Scripts\python.exe -m pytest tests/test_operational_reality_review.py -v
→ 11 passed
```

**Build 7:**
```text
backend\.venv\Scripts\python.exe -m pytest tests/test_operational_reports.py -v
```

| Test | Scop |
|------|------|
| `test_employee_activity_aggregates_tasks` | agregare pe angajat |
| `test_employee_activity_excludes_salary_cost_profit` | fără câmpuri financiare |
| `test_task_reality_includes_employee_name_and_status` | task report complet |
| `test_materials_report_includes_reporter` | reporter în materiale |
| `test_materials_report_does_not_adjust_stock` | fără inventory |
| `test_field_installation_report_team_and_photos` | echipă + poze |
| `test_completeness_summary_counts` | taskuri cu/fără angajat/materiale |
| `test_completeness_summary_material_reporter_and_task_id` | materiale cu/fără reporter/task |
| `test_payload_does_not_expose_salary_cost_profit` | payload curat |
| `test_quote_pricing_costengine_untouched` | boundary imports |
| `test_tpl_dispatch_untouched` | fără dispatch TPL |
| `test_service_is_read_only` | fără mutații DB |
| `test_router_is_get_only` | GET-only router |

---

## 17. PASS/FAIL final

| Criteriu | Rezultat |
|----------|----------|
| Build 6 tests rulate și PASS înainte de implementare | **PASS** |
| Rapoarte operaționale read-only | **PASS** |
| Activitate angajat | **PASS** |
| Realitate taskuri | **PASS** |
| Materiale raportate | **PASS** |
| Montaj teren | **PASS** |
| Summary completitudine extins | **PASS** |
| Fără salarii/cost/profit/hourly | **PASS** |
| Fără stock adjustment | **PASS** |
| Fără auto-repair / fără write execution_reality | **PASS** |
| TPL dispatch neatins | **PASS** |
| Quote/Pricing/CostEngine neatins | **PASS** |

**BUILD STATUS: PASS**

**UI:** `/reports/operational` — Operational Reports (link din `/reports`)

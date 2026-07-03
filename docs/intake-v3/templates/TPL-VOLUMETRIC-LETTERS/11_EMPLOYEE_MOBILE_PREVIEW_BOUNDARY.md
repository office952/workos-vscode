# TPL-VOLUMETRIC-LETTERS — Employee Mobile Preview Boundary

**Contract:** `EmployeePreviewSeed` — `non_executable=true` (hard-validat)  
**UI shell:** `/intake-v3` afișează `employee_mobile_action_allowed=false` în boundary banner; preview din backend sau fallback local.

---

## Rol

Arată operatorului **cum ar putea arăta** un task în Employee Mobile, din perspectiva Intake — fără acțiuni reale.

---

## Ce este preview-ul

| Permis | Interzis |
|--------|----------|
| `preview_tasks[]` cu titlu + instrucțiune | Start Task |
| `mobile_instruction_preview` text | work sessions |
| material preview read-only | status changes (in_progress, done) |
| dependențe ca text informativ | atribuire reală employee_id |

---

## Flux real vs preview

```text
Intake EmployeePreviewSeed     →  DEMO / orientare
ExecutionPlan + Mobile       →  taskuri EXECUTABILE
```

Buton „Începe task” din Atoms prototype = **vizual disabled** — același principiu în V3.

---

## Date din seed

Preview-ul poate reflecta `ProductionHandoff.task_seed` tradus în format Mobile-friendly:

- titlu = `display_name` din Operation Catalog;
- instrucțiune = checklist scurt;
- material = din MaterialIntent summary.

---

## Boundary

Nu modifica: `employee_mobile_tasks_service`, task start gates, PWA sessions.

---

## Legături

- Global: [../../../03_WORK_INTAKE_TO_QUOTES_ORDERS_PRODUCTION.md](../../../03_WORK_INTAKE_TO_QUOTES_ORDERS_PRODUCTION.md)
- Handoff: [10_PRODUCTION_HANDOFF_ADAPTER.md](./10_PRODUCTION_HANDOFF_ADAPTER.md)

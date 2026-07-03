# Work Intake — Lifecycle

**Strat:** global conceptual  
**Boundary:** nu modifică lifecycle runtime V1/V2 actual

---

## Flux principal

```text
New request
  → Product / template selection
  → Vector / material / finish capture
  → Operator confirmation
  → Readiness evaluation
  → Ready for quote
  → PricingInput adapter
  → Quote created
  → Order created (după accept)
  → Production handoff preview / seed
  → Execution plan real (după Order)
  → Employee Mobile (taskuri reale)
```

---

## Statusuri conceptuale Intake V3

| Status | Semnificație |
|--------|--------------|
| `draft` | cerere nouă, date minime |
| `collecting_data` | operator completează zone |
| `waiting_operator_confirmation` | așteaptă confirmare model / finisaje |
| `blocked_for_quote` | blockers active — CTA ofertă dezactivat |
| `ready_for_quote` | readiness OK — poate trimite la ofertare |
| `quote_created` | există quote legat |
| `order_created` | quote acceptat → order |
| `production_handoff_ready` | preview seed complet pentru handoff |
| `archived` / `cancelled` | închis fără producție (conceptual) |

Tranzițiile exacte vor fi definite în build de persistență; acest document fixează **semantica**, nu implementarea DB.

**Implementat (foundation):** tabel `intake_v3_workspaces` cu statusuri draft `draft` / `collecting_data` / `blocked` / `ready_for_quote_preview` / `archived`. Fără `quote_created` automat.

**Implementat (field editor):** `PATCH /api/v1/intake-v3/workspaces/{id}/fields` — allowlist patches pe zone esențiale (dimensiuni, finisaje, support context), sanitize + regenerare preview. Flux:

```text
Workspace draft loaded
  → controlled field patch (batch)
  → sanitize_intake_v3_workspace_payload
  → readiness re-eval
  → pricing input preview
  → production handoff preview
  → UI updated
```

Scenario preview fără draft salvat rămâne read-only.

**UX polish (local):** command bar (mode/source/editor state), operational stepper (6 pași derivați incl. Pre-Quote Review), readiness panel cu mesaje actionable per blocker, pre-quote review panel (quote readiness gate), wording preview-safe pentru pricing/handoff.

**SVG raw analysis (local):** `POST /api/v1/intake-v3/workspaces/{id}/svg` — upload pe draft salvat, validare sigură, analiză brută în payload (`vector_asset`, `raw_svg_analysis`, `raw_analysis_status`). Fără confirmare model producție. Flux:

```text
Draft workspace loaded
  → upload SVG (multipart)
  → validate + raw analysis
  → save payload + regenerate preview
  → operator reviews raw facts / warnings
  → (future) confirmed production model
```

**Production model confirm (local):** `GET/POST .../production-model/review-candidate|confirm` — operator enters real letter/cut/hole counts (ex. HUB 18/27/9), explicit checkbox, saves `confirmed_production_model` without removing `raw_svg_analysis`. Flux:

```text
Raw SVG analysis present
  → review candidate (read-only suggestions)
  → operator confirms counts + checkbox
  → confirmed_production_model saved
  → readiness re-eval (UNCONFIRMED_LETTER_MODEL cleared when valid)
```

**Finish assignment per letter/group (local):** `GET/PATCH .../finish-assignments` — optional overrides on top of global finish after confirmed model. Flux:

```text
Confirmed production model
  → operator defines group and/or letter finish overrides
  → PATCH finish-assignments (validate + save payload)
  → preview regenerated (variations noted; no tasks created)
```

**Finish variation summary (local):** workspace preview includes `finish_variation_summary` — material/operation notes and pricing/handoff preview notes. No CostEngine or final price calculation.

---

## Zone proces (workspace intern)

Pentru pilot volumetric (Atoms reference, V3 target):

`Context` → `Vector` → `Litere` → `Finisaje` → `Materiale` → `Iluminare` → `Handoff`

Acestea sunt **tab-uri interne** în pagina Intake, nu rute App.tsx globale.

---

## Ce urmează

- Readiness: [04_READINESS_AND_BLOCKERS_MODEL.md](./04_READINESS_AND_BLOCKERS_MODEL.md)
- Quotes/Orders boundary: [03_WORK_INTAKE_TO_QUOTES_ORDERS_PRODUCTION.md](./03_WORK_INTAKE_TO_QUOTES_ORDERS_PRODUCTION.md)

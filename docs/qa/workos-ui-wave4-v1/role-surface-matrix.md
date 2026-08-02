# Wave 4 desktop role-surface matrix

Source: `frontend/src/lib/rbac.ts` and `shellNavigation.ts` at `10fca478`. This is navigation exposure, not proof that every deep link independently enforces every action; backend permission checks remain authoritative.

| Role | Primary desktop surfaces | May write through existing flows | Must not receive as a primary surface | Wave 4 implication |
|---|---|---|---|---|
| Viewer | Control producție | None | Commercial, execution, HR, pricing, admin | Closure/profitability remains absent. |
| Operator | Atelier, Shop Floor, Operator, Control producție, Inventar, Utilaje | Start, complete, block tasks; bounded stock operations where backend permits | Pricing, margins, HR/payroll, governance | Needs a concise work-complete/blocked signal, not margin or salary exposure. |
| Sales | Cereri, Produse, Oferte, Comenzi, Planificare, Clients, Documents, Reports | Intake/quote edits, quote acceptance, order creation | Shop-floor peer surfaces, pricing/admin, profit | Needs commercial-to-order continuity; does not own actual cost or closure. |
| Manager | Broad commercial and operations, Ops-Graph, people, payments, reports | Existing task, intake/quote/order, inventory writes; reality invalidation | Settings/governance/pricing/advances navigation | Primary reader for a truthful post-job/closure decision; actual profitability must remain unavailable when input is missing. |
| Admin | Full AppShell, including pricing, advances, governance, settings | All listed existing permissions, including restore-valid | Nothing by nav policy, except production hides DEV tooling | Owns policy/config resolution but must not use UI to bypass backend closure gates. |

## Sensitive truth boundaries

| Truth | Appropriate exposure | Explicit boundary |
|---|---|---|
| Planned task time and execution reality | Operator, manager, admin; sales has execution visibility but no task authority | UI must show backend truth and reason codes; no optimistic task completion. |
| Accepted commercial revenue / frozen EIC | Manager/admin as appropriate; sales commercial context | Not a current actual-cost claim. |
| Actual labor cost, actual material cost, actual margin | Manager/admin only, and only when available | Operator must not see salary/margin data; missing is not zero. |
| Job closure eligibility | Manager/admin decision support | No auto-close or UI-derived closure. Backend/policy must supply the authority. |
| HR payments and advances | Manager/admin according to permission | Keep distinct from operational navigation and commercial data. |

## Role-fit verdict

The role model is materially better than the pre-Wave 0 baseline: known roles project navigation and unknown production roles fail closed to viewer. The main remaining fit issue is not raw access; it is **manager cognitive load**. Managers see multiple concurrent execution homes and, inside execution detail, too many operational and financial-adjacent panels without one clear “can this job be truthfully closed?” synthesis.

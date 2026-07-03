# Work Intake — General Model

**Strat:** global Intake V3  
**Nu acoperă:** detalii template-specific (vezi `templates/TPL-VOLUMETRIC-LETTERS/`)

---

## Work Intake este

Locul unde o **cerere devine lucrare structurată**, înainte de ofertare comercială și producție.

| Responsabilitate | Descriere |
|------------------|-----------|
| Context client | client, job, livrare, montaj intent |
| Produs / template | selecție `TPL-*`, pathway |
| Fișier / vector | upload, analiză brută |
| Dimensiuni | lățime, înălțime, adâncime relevantă |
| Finisaje | față, cant, spate — pe all/group/custom |
| Material intent | estimări roll/sheet/LED/PSU |
| Clarificări operator | confirmări, corecții model |
| Readiness | blockers, warnings, CTA eligibility |
| Pregătire ofertare | `PricingInput` adapter (viitor) |
| Preview producție | `ProductionHandoff` seed (nu plan real) |

### Principiu

```text
Work Intake confirms the work reality before commercial and production handoff.
```

---

## Work Intake NU este

| Nu este | De ce |
|---------|-------|
| CostEngine | calculează cost în alt strat |
| Calculator ofertă final | QuoteWizard / Quotes orchestrator |
| Creator automat de comenzi | Order se creează după accept quote |
| Creator execution plan real | ExecutionPlanService după Order |
| Inventory writer | MaterialIntent ≠ stoc |
| Employee Mobile executor | preview non-executable |
| Task session manager | work sessions după plan |
| Payroll / HR | în afara scope |
| Project management generic | intake = configurare lucrare, nu PM |

---

## Relație V1 / V2 / V3

| Versiune | Rol curent |
|----------|------------|
| V1 | legacy list + detail |
| V2 | volumetric pilot operativ (`/intake-v2/:id`) |
| V3 | greenfield pe contracte; coexistă, nu înlocuiește încă |

V3 învață din V2 dar **nu copiază** structura V2.

---

## Ce urmează

- Lifecycle: [02_WORK_INTAKE_LIFECYCLE.md](./02_WORK_INTAKE_LIFECYCLE.md)
- Handoff comercial: [03_WORK_INTAKE_TO_QUOTES_ORDERS_PRODUCTION.md](./03_WORK_INTAKE_TO_QUOTES_ORDERS_PRODUCTION.md)

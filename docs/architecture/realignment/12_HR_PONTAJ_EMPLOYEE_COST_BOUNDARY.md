# HR / Pontaj — Employee Cost Boundary

**Version:** 1.0.0  
**Status:** Target architecture (documentation only)  
**Related:** Employee architecture decisions under `docs/architecture/EMPLOYEE_*`

---

## 1. Rolul sistemului

HR/Pontaj este sistem **intern P-Media** pentru angajați, roluri, pontaj, concedii, avansuri, datorii, plăți, cost intern angajat și disponibilitate — **fără** rol în formularea prețului comercial client.

---

## 2. Ce detine

| Categorie | Conținut |
|-----------|----------|
| **Angajați** | Identity, roles, teams |
| **Pontaj / attendance** | Check-in/out, schedules |
| **Concedii** | Leave requests, balances |
| **Avansuri / datorii / plăți** | Personal payments |
| **Cost intern angajat** | For internal analytics |
| **Disponibilitate** | Capacity for assignment |
| **Manager reporting** | Team workspace |
| **Mobile employee portal** | Task room, attendance integration |

---

## 3. Ce NU detine

| Exclus |
|--------|
| Preț comercial client |
| Formula universală de ofertă |
| `/price` endpoint logic |
| CommercialPriceProposal |
| Client-facing billing |
| Quote commercial transform |
| ProfitabilityAnalysis engine (consumes HR data — doesn't own it) |

**Regulă:** Costurile angajat pot ajuta la analiză internă și ProfitabilityAnalysis — **nu** transformă oferta în „ore × tarif”.

---

## 4. Inputuri

| Sursă | Date |
|-------|------|
| Owner / HR admin | Employee records, rates (internal) |
| Employee Mobile | Attendance, task sessions |
| ExecutionActuals | Who worked how long |
| Governance | Access control policies |

---

## 5. Outputuri

| Output | Consumator |
|--------|------------|
| Employee availability | ExecutionPlan assignment |
| Attendance records | Payroll-adjacent, analytics |
| Internal labor cost signals | ProfitabilityAnalysis (post-job) |
| Session identity | ExecutionActuals attribution |

---

## 6. Source of truth

| Aspect | Status |
|--------|--------|
| People / attendance truth | **Internal source of truth** |
| Commercial pricing | **NOT** |
| Real task duration | ExecutionActuals — HR provides identity |
| Employee hourly cost for client quote | **FORBIDDEN** |

---

## 7. Conexiuni cu celelalte sisteme

```
HR/Pontaj (internal people truth)
    ↔ ExecutionActuals (employee on task sessions)
    → ProfitabilityAnalysis (internal labor cost component)
    ✗ CommercialPriceProposal
    ✗ Quote snapshot commercial_price
```

| Sistem | Relație |
|--------|---------|
| ExecutionPlan | Assignment eligibility |
| Employee Mobile | Active task work room |
| Settings hourly fallback | **FROZEN** — must not become commercial path |
| Cost Engine | **NO** direct HR hourly → client price |

---

## 8. Reguli owner obligatorii

1. HR data **never** drives client offer formula.
2. Protected foundation — preserve HR paths (audit acceptance).
3. Employee Mobile sessions = ExecutionActuals input — not billing.
4. Internal employee cost rates — analytics only unless owner defines otherwise — **NEEDS_OWNER_DECISION** for exact policy.
5. No impersonation/production auth changes without dedicated decisions.

---

## 9. Riscuri actuale din audit

| Risc | Detaliu | Tag |
|------|---------|-----|
| Settings labour_rate | Could be conflated with commercial | `FROZEN_UNTIL_REALIGNED` |
| WC rate vs employee cost | Naming confusion | `MISLEADING_UI` |
| Attendance ↔ task integration | Partial — documented in architecture decisions | `ACTIVE_OPERATIONAL` |
| HR hourly in CE path | Indirect via settings fallback | `HIGH_RISK_WRONG_DIRECTION` if commercial |

---

## 10. Target state

| Aspect | Țintă |
|--------|-------|
| Clear boundary docs | HR ≠ commercial |
| ProfitabilityAnalysis consumption | Employee cost as actual margin input |
| Assignment only | HR → ExecutionPlan |
| Labels | „Cost intern angajat” — never „tarif client” |
| Access control | Documented decisions preserved |

---

## 11. Forbidden behavior

| Interzis |
|----------|
| Export HR hourly rate to CommercialPriceProposal |
| Client quote line „X ore × salariu/oră” |
| Pontaj hours auto-update quote price |
| Use attendance gaps to reprice accepted order |
| Bundle HR changes with commercial pricing fixes |

---

## 12. Acceptance criteria

| Criteriu | OK când |
|----------|---------|
| No HR → commercial path | Code + docs audit |
| Sessions attributed | Employee ↔ task ↔ order |
| Profitability can consume | Post-job labor cost available |
| UI boundaries | Step 11 HR screens labeled internal |
| Protected status maintained | No unscoped HR rewrite |

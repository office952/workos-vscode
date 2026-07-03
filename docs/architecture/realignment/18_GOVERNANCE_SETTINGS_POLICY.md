# Governance & Settings Policy

**Version:** 1.0.2  
**Status:** Target architecture + **worklog / GO discipline** (sync 2026-06-30 after Slice 10.2 + 10.3)

---

## 1. Rolul sistemului

Governance deține **reguli owner, settings, feature flags, aprobări, forbidden scope, readiness gates, audit logs conceptuale** — mecanismul prin care **nimic major nu se modifică fără GO explicit owner**.

---

## 2. Ce detine

| Categorie | Conținut |
|-----------|----------|
| **Reguli owner** | Pricing law, no-hourly commercial, protected foundations |
| **Settings** | App config — including CE fallbacks (**FROZEN paths flagged**) |
| **Feature flags** | Scoped enablement — **UNKNOWN** full inventory |
| **Aprobări** | Owner approval on quote, pricing review gates |
| **Forbidden scope** | FROZEN_UNTIL_REALIGNED list |
| **Readiness gates** | Intake confirm, quote accept, order convert |
| **Audit logs (conceptual)** | Who approved what, when |
| **Agent constraints** | AGENTS.md, BUILD_* boundaries |
| **Documentation truth** | docs/architecture/* as contract |
| **Worklog discipline** | `docs/worklog/realignment/` — **mandatory** per audit/runtime/implementation task |
| **Owner visual verification** | Required in reports for UI/QA tasks — see doc 17 |

---

## 3. Ce NU detine

| Exclus |
|--------|
| Business logic product compilation |
| Commercial price calculation |
| Automatic override of owner decisions |
| Silent feature enablement of frozen paths |
| Implementation without GO |

**Regulă:** **Nicio schimbare majoră fără GO owner.**

---

## 4. Inputuri

| Sursă | Date |
|-------|------|
| Owner decisions | GO/NO-GO per step |
| Audit acceptance | WORKOS_FULL_SYSTEM_REALITY_AUDIT_ACCEPTANCE.md |
| Master plan | Steps 7G–12 |
| BUILD QA docs | docs/qa/BUILD_*.md when exist |

---

## 5. Outputuri

| Output | Consumator |
|--------|------------|
| GO/NO-GO records | Team, agents |
| Freeze enforcement (intent) | No ad-hoc /price fixes |
| Gate definitions | Intake, quote, order services |
| Settings policy | Admin UI — labeled dangerous settings |

---

## 6. Source of truth

| Aspect | Status |
|--------|--------|
| Owner pricing law | **Binding** — docs/architecture |
| Runtime settings | **Operational** — some FROZEN for commercial misuse |
| Feature flags | **UNKNOWN** complete map |
| Protected foundations list | Audit acceptance §2 |

---

## 7. Conexiuni cu celelalte sisteme

```
Governance (policy layer)
    wraps all systems:

Intake V6 gates → confirm only when ready
CommercialPriceProposal → owner GO for 7G runtime
EstimatedInternalCost → owner GO for 7H
Quote snapshot → owner approval flow exists today
ExecutionPlan → explicit approval target
ProfitabilityAnalysis → owner GO for recommendations → registry
Legacy cleanup → owner GO Step 12 only
```

---

## 8. Reguli owner obligatorii

### Global forbidden without GO

| Category | Examples |
|----------|----------|
| Runtime pricing | /price, reprice Quote 4, Step 7E.2 |
| Engine rewrite | Cost Engine, QuoteOrchestrator |
| Data | DB reset, reseed, migration |
| Protected areas | CostEngine formulas, Pricing Registry ad-hoc, Status lifecycle |
| UI | Redesign, CSS drive-by |
| Product | Intake V6 redesign, partial ACM activation |

### Blocking rules (target — from master plan §10)

**Blochează CommercialPriceProposal:**

- Geometrie critică lipsă
- Material critic lipsă (commercial rule context)
- Regulă comercială lipsă pentru modul activ
- Finish groups neconfirmate (când policy cere)
- Configurație invalidă

**NU blochează CommercialPriceProposal:**

- Lipsă rate_per_hour
- Lipsă estimare minute
- Lipsă runtime actual pre-producție
- Lipsă employee hourly cost
- Lipsă ProfitabilityAnalysis pre-execuție

**Blochează doar confidence / analytics:**

- Cost intern incomplet
- Lipsă reguli interne non-hourly
- Lipsă istoric timp real post-job

---

## 9. Riscuri actuale din audit

| Risc | Detaliu | Tag |
|------|---------|-----|
| Settings hourly fallback | Silent commercial path risk | `FROZEN_UNTIL_REALIGNED` |
| Agent ad-hoc fixes | Without GO | Governance gap |
| Blockers conflated | WC rate blocks commercial | Policy violation today |
| No feature flag on /price | Frozen intent docs-only | `NEEDS_OWNER_DECISION` |
| BUILD boundary drift | Overlapping agent work | AGENTS.md mitigates |

---

## 10. Target state

| Aspect | Țintă |
|--------|-------|
| GO log per step | 7G–12 tracked |
| Dangerous settings labeled | labour_rate, machine_rate — internal only |
| Blocker taxonomy enforced | Commercial vs internal confidence |
| docs/qa/BUILD_* per significant build | AGENTS.md discipline |
| Agent + human read realignment/ first | Onboarding |
| Worklog per significant task | status, scope, files, tests, runtime, forbidden scope, direction score, next step |
| No task closed without worklog | `docs/worklog/realignment/` |

### Worklog rule (2026-06-30)

Every audit, runtime restore, QA, implementation slice, and docs sync **must** leave a persistent worklog in `docs/worklog/realignment/`. **Without worklog = task not closed.**

Minimum fields: status, scope, architecture readback summary, files changed, tests/validation, runtime status, forbidden path confirmation, owner decisions needed, next recommended step, direction score (X/100%).

Agent prompts must include **roadmap awareness checkpoint** and **owner GO** for implementation.

---

## 11. Forbidden behavior

| Interzis |
|----------|
| Implement without GO |
| Weaken tests to greenwash |
| Declare validate:frontend green |
| Bundle unrelated refactors |
| Commit secrets |
| Auto DB reset as fix |
| Deprecate code without owner Step 12 |

---

## 12. Acceptance criteria

| Criteriu | OK când |
|----------|---------|
| Freeze list published | Matches audit acceptance §3 |
| GO gates on roadmap | Each step marked |
| Blocker taxonomy documented | Master plan §10 in ops |
| Settings audit | Hourly fallbacks flagged |
| Agent constraints aligned | AGENTS.md + this folder linked |

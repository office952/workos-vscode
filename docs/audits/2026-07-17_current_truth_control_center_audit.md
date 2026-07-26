# Current Truth Control Center — Present-truth audit

**Priority:** `CURRENT_TRUTH_CONTROL_CENTER_AUDIT = ACTIVE`  
**Pages:** `/modules` · `/governance`  
**Date:** 2026-07-17  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Audit HEAD:** `75e11cf` (after 01C pause preserve) · 01B at `5cb5aa6`  
**Runtime:** `http://127.0.0.1:3000` · `http://127.0.0.1:8001`  
**Type:** Audit only — **no application code changes**  
**Verdict:** `CROSS_PAGE_CONFLICT` (modules dual-spine + governance stale boundaries) with recoverable path via one coherent rewrite build

**Preserved prior work:** UI-TRUTH-01C **PAUSED** (canonical title: Failure, stale, retry, and drill-down states) — commit `75e11cf`.

---

## 0. Audit principle applied

Primary views must answer: what exists / is active / is connected / who owns / which contract / runtime status / verify where / current limitation — **now**.

Authority order: runtime → code → API/DB → tests → current QA → master docs → old plans.

---

## 1. Executive summary

| Page | Overall quality | Main failure mode |
|------|-----------------|-------------------|
| `/modules` | Useful as honesty projection; **weak as present control center** | Three spines (commercial honesty · OC→TK contracts · health cards); PROVEN_V1 archaeology in primary notes; runtime cards stuck Neverificat |
| `/governance` | Ownership tab usable; **other tabs mix policy museum with live claims** | Boundaries/Gates contradict Modules honesty; most rules documentation-only; G13 only partial enforcement |

**Biggest present-truth problems**

1. Dual/triple system taxonomies presented as one map.  
2. Historical PROVEN_V1 / commit / order IDs in primary architecture and handoff UI.  
3. Governance Boundaries still say “Quotes calculează” vs Modules freeze spine.  
4. Gates tab `isCalculable` model not found in backend.  
5. Runtime health aggregate vs empty public `checks` confusion.  
6. Shell mock `2 critical` + Dashboard `Live` (deferred UI-TRUTH-01C) still pollute trust outside these pages.

---

## 2. Source map (how content is produced)

| Source | Used by | Live? | Role |
|--------|---------|-------|------|
| `truthPagesHonestyBaseline.ts` | Modules Harta/Handoffs/Evidence · Governance ownership | Static FE | Present commercial-spine projection (PARTIAL) |
| `useModuleChainData` `CONTRACT_HANDOFFS` | Modules Contracte detaliate | Static FE | Legacy OC→TK technical chain (REFERINȚĂ) |
| `GET /api/v1/system/health` | Modules Stare runtime (30s poll) | Live | Aggregate status only; `checks:{}` always |
| `EnvironmentBanner` / `useRuntimeHealth` | Global shell | Live | Separate 45s poll — not shared with Modules |
| `governanceData.ts` arrays | Governance boundaries/status/gates/guardrails/products/ui-rules | Static FE | Mostly policy museum |
| `agent_authority_registry.json` | Governance agents | Static JSON | Process personas — not RBAC |
| `GET /api/v1/system/documentation` | Governance ownership/truth Important Docs | Live | B2 index — strongest live doc truth |

---

## 3. `/modules` — tab audit summary

### 3.1 Harta sistemelor

| Section | Exact text (sample) | Source | Truth | Classification | Action |
|---------|---------------------|--------|-------|----------------|--------|
| Banner | proiecție read-only, acoperire parțială | hardcoded | Accurate self-description | CURRENT_CONFIRMED | KEEP |
| Node WI | Preluare lucrare / Intrare comercială… | honesty baseline | Role OK; nav still EN Work Intake | CURRENT_CONFIRMED | KEEP purpose; terminology later |
| Node PS | Catalog produse / Definiții șablon | honesty | OK | CURRENT_CONFIRMED | KEEP |
| Node PD | Definiție produs / fără pagină dedicată | honesty | True gap | CURRENT_PARTIAL | MARK_PARTIAL |
| Node Aggregate | …proven pe Letters (ad25fa9)… | honesty | Purpose OK; commit in primary | CURRENT_PARTIAL + HISTORICAL | REWRITE note → present purpose; MOVE proof to evidence |
| Node EP/Exec | PROVEN_V1 … order 92402 … Wave 7 | honesty | Scenario stamp as architecture | HISTORICAL in primary | REWRITE / MOVE_TO_EVIDENCE |
| Resources | Tarife/Inventar/… NEVALIDAT | honesty | Honest partial | CURRENT_PARTIAL | KEEP + show limitation text |

### 3.2 Contracte și transferuri

| Section | Classification | Action |
|---------|----------------|--------|
| Transferuri baseline PROVEN_V1 edges (IR/order stamps) | HISTORICAL sold as current | MOVE_TO_EVIDENCE; primary edges = present contract only |
| Contracte detaliate OC→TK REFERINȚĂ | STALE / DUPLICATE spine | REMOVE_FROM_PRIMARY or clearly isolate as legacy technical appendix |
| CostEngine in contracts but absent from Harta | CROSS_PAGE / dual taxonomy | OWNER_DECISION: one spine |

### 3.3 Stare runtime

| Claim | Runtime | Classification | Action |
|-------|---------|----------------|--------|
| Aggregate DEGRADAT/VERIFICAT from `health.status` | Live verified | CURRENT_PARTIAL | KEEP; clarify “aggregate only” |
| Module cards Neverificat | Expected: public `checks:{}` | CURRENT_CONFIRMED idle honesty | KEEP wording; explain why never “activ” |
| Chip “Health API” while cards Neverificat | Confusing | MISLEADING UX | REWRITE chip copy |
| Separate poller vs banner | Compatible status today | DUPLICATE | KEEP per 01C G3; SHARE later |

### 3.4 Surse și dovezi

| Item | Classification | Action |
|------|----------------|--------|
| Architecture policy docs CURRENT | CURRENT_CONFIRMED pointers | KEEP |
| Health API PARTIAL | CURRENT_CONFIRMED | KEEP |
| Same-scenario / W7 packs labeled CURRENT | HISTORICAL evidence | MOVE_TO_EVIDENCE / rename status to DOVADĂ / ISTORIC |
| UI-TRUTH-01B / Wave 7 acceptance | Gate stamps | KEEP in evidence with clear “acceptance” kind |

---

## 4. `/governance` — tab audit summary

| Tab | Source | Enforcement | Classification | Action |
|-----|--------|-------------|----------------|--------|
| Cine deține adevărul | honesty + docs API | Policy + live index | CURRENT_PARTIAL | KEEP as primary; add Work Intake row |
| Harta limitelor | `boundaryLayers` | Docs-only | STALE / MISLEADING | REWRITE to match Modules honesty or REMOVE_FROM_PRIMARY |
| Fluxuri de stare | `moduleStatusFlows` | Partial backend validators | STALE / CURRENT_PARTIAL | MARK_PARTIAL; align WI/Quotes/Orders only |
| Autoritatea agenților | JSON registry | Not RBAC | HISTORICAL / UNSUPPORTED as control | MOVE_TO_EVIDENCE / REFERINȚĂ only |
| Surse de adevăr | hierarchy + docs API | Policy + API | CURRENT_PARTIAL | KEEP hierarchy as policy; docs live |
| Pregătit pentru ofertare | `gateLevels` / isCalculable | **isCalculable absent in backend** | STALE / MISLEADING | REMOVE_FROM_PRIMARY or rewrite to real readiness API |
| Reguli de protecție G01–G13 | `guardrails` | Mostly policy; G13 partial tests/seeds | CURRENT_PARTIAL | KEEP G13; rewrite G01 Quotes-calculează; mark others POLICY |
| Catalog produse | static nomenclator | Not Product System | DUPLICATE / UNSUPPORTED | REMOVE_FROM_PRIMARY → link `/product-system` |
| Reguli de adevăr UI | `uiTruthRules` | Guidance only | CURRENT_PARTIAL | KEEP as guidance; Romanian examples |

**G13:** Display + seed/tests/helpers — **not** wired as FE runtime warn on every string. Classification: CURRENT_PARTIAL (do not claim full e2e enforcement on this page alone).

---

## 5. Runtime verification (2026-07-17)

| URL / check | Result |
|-------------|--------|
| Ports | `:3000` / `:8001` listening |
| `/modules` Harta | Nodes + Wave7/PROVEN notes visible (live a11y) |
| `/modules` Stare runtime | Aggregate DEGRADAT; modules Neverificat; Ultima verificare present |
| Global banner | `Staging · Backend cu avertisment · DB neverificată` (01B) — does not contradict aggregate warning |
| `GET /api/v1/system/health` | `status=warning`, `checks={}` (known contract) |
| `/governance` ownership | Matrix + read-only banner |
| `/governance` Reguli | G13 UTF-8 card present |
| Build 1 / W7 data | Not mutated (read-only) |

---

## 6. Cross-page consistency

| Topic | `/modules` | `/governance` | Mismatch |
|-------|------------|---------------|----------|
| Commercial spine | WI→PS→PD→PA→Quotes→Orders→EP→Exec | Boundaries: Templates→Quotes→Orders→WorkOS→OC | **CONFLICT** |
| Quotes role | Îngheț comercial | “Quotes calculează” (G01/Boundaries) | **CONFLICT** |
| Work Intake ownership | Node present | Missing from ownership table | **GAP** |
| CostEngine | Runtime/contracts only | Boundary/agents era | **DUPLICATE taxonomy** |
| Honesty baseline | Shared import | Shared import | Aligned where used |
| Runtime health | Runtime tab | Not claimed | OK |

---

## 7. Conflict register

| ID | Page | Claim | Runtime/code truth | Conflict | Authority | Proposed resolution | Owner gate |
|----|------|-------|--------------------|----------|-----------|---------------------|------------|
| CTC-01 | Modules + Gov | One system map | Two/three spines | Taxonomy clash | Honesty baseline vs governanceData/ModuleChain | Single present spine on both pages | YES — spine choice |
| CTC-02 | Governance Boundaries/G01 | Quotes calculează | Quotes freeze; cost elsewhere | Role false | honesty + services | Rewrite G01/Boundaries | YES if touching guardrails |
| CTC-03 | Governance Gates | isCalculable readiness | Field absent in backend | Fake gate model | code search | Remove/rewrite to real readiness | YES |
| CTC-04 | Modules Harta/Handoffs | PROVEN_V1 as architecture status | Scenario proof | History as present | honesty notes | Relocate to evidence | NO (content model) |
| CTC-05 | Modules Runtime | Health API + Neverificat cards | checks redacted | Confusing but technically honest | health contract | Clarify copy; don’t invent DB | NO |
| CTC-06 | Modules Contracte | OC→TK detailed contracts | Parallel legacy chain | Duplicate | CONTRACT_HANDOFFS | Demote/remove from primary | YES if removing |
| CTC-07 | Shell (related) | 2 critical / Dashboard Live | Mock / stats≠health | Trust pollution | App/Dashboard | Deferred 01C G1/G2 | Already deferred |

---

## 8. Content decision register (implementation backlog seed)

| Item | Decision |
|------|----------|
| Modules read-only banner | KEEP |
| Architecture node present-purpose notes | REWRITE (strip commit/order archaeology) |
| PROVEN_V1 handoff primary list | MOVE_TO_EVIDENCE |
| Contracte detaliate OC→TK | REMOVE_FROM_PRIMARY or MARK_INACTIVE appendix |
| Runtime aggregate badge | KEEP + CONNECT copy clarity |
| Evidence scenario packs | MARK as DOVADĂ/ISTORIC not CURRENT architecture |
| Governance ownership | KEEP + add Work Intake |
| Governance Boundaries | REWRITE or REMOVE_FROM_PRIMARY |
| Governance Gates isCalculable | REMOVE_FROM_PRIMARY |
| Governance Agents | MOVE_TO_EVIDENCE |
| Governance product catalog | REMOVE_FROM_PRIMARY → link Product System |
| G13 card | KEEP (policy) + honest PARTIAL enforcement note |
| G01 Quotes calculează | REWRITE |
| Shell critical / Dashboard Live | OUT_OF_SCOPE here (01C deferred) |

---

## 9. Proposed final content model (not implemented)

### `/modules` — each active system card

- name (RO) + technical alias  
- current purpose (1 line)  
- owner  
- status: ACTIVE / PARTIAL / INACTIVE / UNKNOWN (from runtime when safe, else honesty)  
- input → output → consumer  
- verify link (route or API)  
- current limitation  
- evidence link (secondary)

### `/governance` — each rule card

- rule name  
- authority/owner  
- present requirement  
- enforcement point (code path / test / policy-only)  
- evidence  
- exception / owner gate  
- status: ENFORCED / PARTIAL / POLICY_ONLY / STALE  

### History

Primary tabs: present only.  
History/proof: Surse și dovezi with kinds DOVADĂ / ACCEPTANCE / WORKLOG — or evidence drawer — not green PROVEN_V1 as architecture health.

---

## 10. Recommended coherent implementation build

**Name:** `CURRENT_TRUTH_CONTROL_CENTER_V1`  
**Objective:** Make `/modules` and `/governance` present-truth control surfaces: one spine, ownership aligned, history demoted, stale gate/boundary models removed or rewritten, Romanian clarity, safe runtime copy — without becoming a control plane editor.

| Area | Work |
|------|------|
| Pages | `/modules`, `/governance` only |
| Data | honesty baseline rewrite; demote CONTRACT_HANDOFFS; trim governanceData stale tabs |
| Runtime | Clarify Modules health copy; **do not** invent public DB; KEEP separate poller unless later SHARE |
| Terminology | Operator RO; keep technical aliases |
| Tests | ModuleChain + Governance Vitest for present model; no LIVE/DB; no Quotes-calculează |
| Visual | Desktop smoke both pages all tabs |
| Commits | One or two: content model · optional evidence status rename |

**Owner gates before GO**

1. Single spine: honesty commercial vs OC→TK — which is primary?  
2. Remove vs rewrite Boundaries/Gates tabs?  
3. History: MOVE TO EVIDENCE only?  
4. Runtime: docs-only status vs connect more APIs?

**Boundaries / exclusions**

- No UI-TRUTH-01C implementation  
- No Wave 7 / PostJobTruth / UTF-8 tooling  
- No Product System catalog rewrite  
- No shell Live/critical (deferred)  
- No new governance policy engine  
- No DB mutation  

---

## 11. Terminology / diacritics (spot)

| Issue | Notes |
|-------|--------|
| Nav EN vs Modules RO | Work Intake / Product System vs Preluare lucrare / Catalog produse |
| PROVEN_V1 English stamp | Operator-facing primary |
| Quotes / Oferte dual | Acceptable with alias |
| G01 “Quotes calculează” | Wrong role language |
| Diacritics on honesty/gov banners | Generally correct (ă, ț, ș) |
| UI01 examples EN Ready/Blocked | Guidance mixed language |

---

## 12. Explicit exclusions

UI-TRUTH-01C · shell Live/critical · FLEX · TE2E-028 · Logo · PreOrder · DB cleanup · broad nav rename · Figma MASTER creation.

---

## 13. Appendix — system questions (commercial honesty spine)

| System | Owns now | Input | Output | Consumer | Connection | Prove UI | Limitation |
|--------|----------|-------|--------|----------|------------|----------|------------|
| Work Intake | Commercial request/workspace | Customer/product intent | Workspace + template selection | PD/PS | Active | `/intake`, `/intake-v6` | Step2 UX debt remains |
| Product System | Template config | Template codes | Definitions | PD/Intake | Active readonly catalog | `/product-system` | Not price SoT |
| ProductDefinition | Compile/preview | Composition | Graph | Aggregate | Partial — no dedicated page | API/embedded | TE2E-010 |
| ProductAggregate | Technical BOM/task_contract | Graph | Aggregate + tasks | Plan/Quotes path | Partial proven Letters | API | Not universal |
| Quotes | Commercial freeze | Aggregate/commercial | Snapshot | Orders | Active | `/quotes` | Dual cost debt TE2E-025 |
| Orders | Approved snapshot | Quote snapshot | Locked order | ExecutionPlan | Active | `/orders` | Immutability gate open TE2E-022 |
| ExecutionPlan | Planned tasks | Frozen snapshot/contract | Plan/tasks | Reality | Proven bounded | `/execution/:id` | Not all templates |
| Execution Reality | Actuals/sessions | Plan | Actual truth + PostJob derived | Post-job panel | Proven bounded | `/execution/:id` | Partial actuals |

---

## 14. Owner decision pack

```text
CURRENT TRUTH CONTROL CENTER = APROBAT / REWORK / STOP

MODULES MODEL = APROBAT / REWORK
GOVERNANCE MODEL = APROBAT / REWORK
HISTORY = MOVE TO EVIDENCE / KEEP / REMOVE
RUNTIME CONNECTION = APPROVE SAFE CONNECTIONS / DOCS ONLY
TERMINOLOGY = APPROVE / REWORK

AUDIT COMMIT = DA / NU
IMPLEMENTATION = GO / STOP
```

**Recommended:** APROBAT models · HISTORY=MOVE TO EVIDENCE · RUNTIME=DOCS ONLY (+ clarify copy) · TERMINOLOGY=APPROVE with G01 rewrite · AUDIT COMMIT=DA · IMPLEMENTATION=GO after gates.

---

## 15. Owner decisions applied (2026-07-17 — implementation authorized)

```text
CURRENT TRUTH CONTROL CENTER = APROBAT
MODULES MODEL = APROBAT
GOVERNANCE MODEL = APROBAT
HISTORY = MOVE TO EVIDENCE
RUNTIME CONNECTION = APPROVE SAFE CONNECTIONS
TERMINOLOGY = APPROVE, including G01 rewrite
AUDIT COMMIT = DA
IMPLEMENTATION = GO
UI-TRUTH-01C = remains PAUSED
```

**Canonical primary spine (owner-approved):**  
Intake V6 → ProductDefinition → ProductAggregate → Pricing / Commercial → Quote Snapshot → Order Snapshot → ExecutionPlan → Execution Reality → Post-Job

Legacy OC→TK: historical evidence only — not an active parallel spine.

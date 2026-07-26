# GOV-INT-01 — Audit E2E System Governance (all tabs) + Module Chain overlap

**Task:** `GOV-INT-01` — `AUDIT_E2E_SYSTEM_GOVERNANCE_ALL_TABS_AND_MODULE_CHAIN_OVERLAP_V1`  
**Date:** 2026-07-15  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Starting HEAD:** `1e9d32e`  
**Runtime:** backend `http://127.0.0.1:8001` · frontend `http://127.0.0.1:3000`  
**Scope:** Audit only — no code, UI, DB, or canonical doc changes.

---

## Executive summary

`/governance` is **not** a canonical governance control plane. It is a **read-only documentation aggregator** built from hardcoded TypeScript (`governanceData.ts`) plus one JSON registry (`agent_authority_registry.json`). It makes **no backend calls**. The **"25 canonical docs"** badge is **hardcoded** and **not proven** — `docs/canonical/` is **empty**.

Compared with `/modules` (MODULE-INT-01: hybrid static + aggregate health), `/governance` is **fully static** but **duplicates** much of the same architectural vocabulary (events, status flows, golden-rule concepts) from a **different, contradictory** boundary model.

**Core question answer:** **B** — two duplicated documentation surfaces (with **D**-class contradictions between them and within Governance Boundary Map vs Status Flows).

**Verdict:** `GOVERNANCE_AUDIT_BLOCKED_STATIC_DUPLICATION`

**User direction honored:** No page merge, no MODULE-PLAN-01, no implementation.

**Next task:** `GOV-MODULE-AUTH-01-CANONICAL-PURPOSE-AND-UNIFICATION-DECISIONS`

---

## Verdict

`GOVERNANCE_AUDIT_BLOCKED_STATIC_DUPLICATION`

Supporting blockers also proven: stale/misleading canonical docs claim; contradictory boundary truths; enforcement gaps on the page itself.

---

## Repository safety

- **Code changed:** NO  
- **DB changed:** NO  
- **Implementation authorized:** NO  
- **Only:** audit worklog, evidence JSON, screenshots, `WORKOS_E2E_STATUS.md` / `WORKOS_E2E_TASK_GRAPH.md` updates.

---

## Governance route classification

| Label | Applies |
|-------|---------|
| LOCAL_DEFINITION_VIEW | YES |
| DOCUMENTATION_AGGREGATOR | YES |
| STATIC_REFERENCE | YES |
| HYBRID | YES (static content + global LIVE banner — not governance data) |
| CANONICAL_GOVERNANCE_REFERENCE | NO |
| GOVERNANCE_CONTROL_PLANE | NO |
| CONTRADICTORY_REFERENCE | PARTIAL (internal + vs `/modules`) |

**Page ownership**

| Item | Value |
|------|-------|
| Route file | `frontend/src/App.tsx` |
| Page | `frontend/src/pages/Governance.tsx` |
| Data | `frontend/src/lib/governanceData.ts` |
| Agent bridge | `frontend/src/lib/agentAuthorityRegistry.ts` |
| Backend calls | **0** |
| Refresh | None |

---

## Canonical documents ("25" claim)

| Check | Result |
|-------|--------|
| Exactly 25? | **NO** — badge is literal string, not counted |
| Hardcoded or calculated? | **Hardcoded** (`Governance.tsx:1580`) |
| All loaded? | **NO** — 1 JSON only |
| `docs/canonical/` | **Empty** |
| Freshness UI | **None** |
| Stale doc can stay "canonical"? | **YES** — no loader, no version |

**Found:** `frontend/src/canonical/agent_authority_registry.json` (7 agents, v1.0.0, updatedAt 2026-03-09)  
**Missing:** `docs/canonical/canonical__agent_authority_map.md` (referenced but absent)

`governanceData.ts` header claims *"Extracted from canonical .md files"* — **false**; content is inline arrays.

---

## Tab audits (8/8)

### Tab 1 — Boundary Map — **CONTRADICTED / STATIC**

**UI:** Templates → Quotes → Orders → WorkOS → OC; Formula Canonică with *Quotes calculează*.

**Frontend:** `boundaryLayers` in `governanceData.ts`.

**Backend:** None.

**Mismatch vs module chain / real architecture:**

| Governance | Modules / real |
|------------|----------------|
| Templates (prepare) | WI + PS + Product Definition |
| Quotes **calculează** | **CostEngine** calculează; Quotes = ofertă |
| No Intake | WI explicit |
| No CostEngine | CE explicit |
| OC **after** WorkOS | OC **starts** chain |
| 5 nodes | 8 modules |

### Tab 2 — Status Flows — **PARTIAL / STATIC**

**UI:** 8 modules (OC, WI, PS, CE, QT, OR, WO, TK) + cross-module events + invalid patterns.

**Overlap with `/modules`:** Same event names (`WI_READY_FOR_QUOTE`, `COST_CALCULATED`, …) — duplicated static constants.

**Backend:** WI `ready_for_quote` / V6 `ready_for_quote_preview` partially align; WO/ExecutionReality not proven as displayed enums. **Product Definition** and **ExecutionReality** domains **omitted**.

### Tab 3 — Agent Authority — **STATIC**

**Meaning of "Agent":** Compound-engineering **role personas** (Nucleu, Contracte, Costing/OC, …) — not AI agents, not RBAC.

**Source:** Only tab with JSON registry; still **not** runtime enforcement.

**Conflict:** Does not reflect OWNER-DECISION-03 **A1–A22** (0 CONFIRMATE).

### Tab 4 — Source of Truth — **PARTIAL / CONTRADICTED**

8-level hierarchy elevates **Fișiere .md canonice** — but this page **does not load any .md**.

Meta-contradiction: page presents canonical hierarchy while violating level-2 itself.

### Tab 5 — Ready for Quotes — **PARTIAL / LEGACY terminology**

Template/Blueprint Studio gate logic (4 levels) — **documentation**.

**Runtime:** `intake_v6_canonical_readiness_service`, `volumetric_quote_ready_policy`, `is_ready_for_quote` — **not wired to this page**.

Legacy EN label "Quotes" vs RO "Ofertă" elsewhere.

### Tab 6 — Guardrails — **DOCUMENTED_ONLY**

12 guardrails (G01–G12). **G01** text repeats Boundary formula (*Quotes calculează*) — **contradicts** `/modules` Golden Rule.

Enforcement exists **elsewhere** (snapshot accept gate, readiness tests) — **not** via `/governance`.

### Tab 7 — Product Catalog — **STATIC / DUPLICATE**

50 products, 12 categories — RC Publimedia nomenclator. **Not** Product System `TPL-*` registry. Search-indexed only.

### Tab 8 — UI Truth Rules — **DOCUMENTED_ONLY**

5 UI standards (UI01–UI05). No linter/test binding to Governance page. Irony: governance page displays gates/rules as **static cards**.

---

## Search and filter

- **Source:** `buildSearchIndex()` — flattens all `governanceData` + agents (~100+ entries).
- **Scope:** Client-side; case-insensitive substring.
- **Not indexed:** `invalidPatterns`.
- **Risk:** Results navigate to static content; implies authority without runtime proof.
- **Proof:** Search `CostEngine` → 2 results (CE status flow + COST_CALCULATED event) — screenshot `10-search-costengine.png`.

---

## Governance vs Modules

| Dimension | `/governance` | `/modules` |
|-----------|---------------|------------|
| Backend | None | `GET /api/v1/system/health` |
| Flow poster | 5-layer boundary | 8-module chain |
| Cost authority | Quotes (wrong) | CostEngine |
| Events | Static | Static (Referință) |
| Shared source | **NO** | **NO** |
| Relationship | **DUPLICATE** + **CONTRADICTORY** | MODULE-INT-01 HYBRID |

**Recommended relationship (no merge now):** Keep both **labeled reference-only** until **GOV-MODULE-AUTH-01** owner decisions + **shared versioned architecture definition**.

---

## E2E scenarios

### Scenario 1 — Product intake → order

- **Governance:** Templates prepare → Quotes calculate → …  
- **Modules:** OC → WI → PS → CE → QT → OR → WO → TK  
- **Runtime:** Intake V6 readiness → PD/Aggregate → CostEngine → Quote snapshot → Order lock  
- **Mismatch:** Governance boundary omits Intake, PD, CE.

### Scenario 2 — Cost and commercial truth

- **Governance:** Quotes calculează.  
- **Modules:** CE owns cost; QT owns commercial offer.  
- **Runtime:** CostEngine services + quote_snapshot_v2.  
- **Mismatch:** **CONTRADICTED**.

### Scenario 3 — Execution truth

- **Governance:** WorkOS monolith executes; OC guards after.  
- **Runtime:** ExecutionPlanV2, operations, Employee Mobile tasks.  
- **Mismatch:** Oversimplified; OC placement wrong.

### Scenario 4 — Authority violation

- Tests prove snapshot accept gates, mobile auth boundaries — **not** displayed/enforced on Governance page.  
- Governance **documents** rules that real code partially enforces elsewhere.

### Scenario 5 — Document drift

- Badge claims 25 docs; repo has **0** markdown canonical files.  
- Page **cannot** detect or surface drift — no loader, no freshness.

---

## Tests

| Suite | Passed | Failed | Skipped | Notes |
|-------|--------|--------|---------|-------|
| `test_quote_output_snapshot_governance` + `test_system_health` | 27 | 0 | 0 | Related runtime governance (not page) |
| `test_volumetric_quote_ready_policy` + snapshot + identity boundary | 61 | 0 | 0 | Readiness / boundary enforcement |
| Governance.tsx / governanceData tests | 0 | — | — | **No dedicated tests** |

**Tests overall:** **PARTIAL** (backend enforcement proven; page untested and non-authoritative).

---

## Principal idea recommendation

**Candidate 4 — Owner decision required** before any unification.

Interim framing (not implementation): **System Reference Center** with explicit **NON-CANONICAL** labeling until a **single versioned architecture/policy source** exists. Neither `/governance` nor `/modules` is that source today.

**Shared source required:** **YES** (documentation/config — not necessarily runtime registry).

**Pages to keep (for now):** Both — reference only.  
**Page to retire:** **NONE** until GOV-MODULE-AUTH-01.

---

## Impact

| Item | Impact |
|------|--------|
| MODULE-AUTH-01 M1–M16 | Still 0 CONFIRMATE; audit adds G1–G? governance purpose decisions needed |
| MODULE-PLAN-01 | **BLOCKED_PENDING_GOV_INT_01** — do not open remediation plan on `/modules` alone |
| Roadmap | Unification blocked; enforcement closure is separate (`GOVERNANCE-RUNTIME-01` not authorized) |

---

## Honest opinion

`/governance` looks more authoritative than it is: shield icon, "25 canonical docs", search, export — but it is **another static layer**, partly **older/wrong** (Boundary Map), partly **aligned** with Status Flows tab (which itself duplicates `/modules`). The global **LIVE/DB** banner makes this **more dangerous** than `/modules` alone because it contradicts the page's own disclaimer.

Your direction is correct: **establish truth of Governance before any merge or MODULE-PLAN-01**.

---

## Evidence

- **Matrices:** `docs/qa/product-system-active-path-isolation-v1/gov_int_01/*.json`  
- **Screenshots:** `docs/qa/product-system-active-path-isolation-v1/gov_int_01/screenshots/` (10 files)

---

## Delivery footer

| Field | Value |
|-------|-------|
| Task | GOV-INT-01 |
| Starting HEAD | 1e9d32e |
| Governance classification | HYBRID → LOCAL_DEFINITION_VIEW + DOCUMENTATION_AGGREGATOR |
| Tabs audited | 8/8 |
| Canonical docs claimed | 25 |
| Canonical docs found | 1 |
| Canonical docs current | 1 |
| Canonical docs stale | 0 (24 never existed) |
| Canonical docs conflicting | 1+ |
| Boundary Map | CONTRADICTED |
| Status Flows | PARTIAL / STATIC |
| Agent Authority | STATIC |
| Source of Truth | PARTIAL |
| Ready for Quotes | PARTIAL / LEGACY |
| Guardrails | DOCUMENTED_ONLY |
| Product Catalog | STATIC / DUPLICATE |
| UI Truth Rules | DOCUMENTED_ONLY |
| Governance vs Modules | DUPLICATE + CONTRADICTORY |
| Recommended relationship | Separate until shared source + owner decisions |
| Principal idea | Owner decision required (Candidate 4) |
| Shared source required | YES |
| Duplicate truths | 15+ |
| Contradictory truths | 8+ |
| Legacy concepts | 6+ |
| Dead pieces | 12 |
| Screenshots | 10 |
| Tests | PARTIAL |
| MODULE-PLAN-01 | BLOCKED_PENDING_GOV_INT_01 |
| Next task | GOV-MODULE-AUTH-01-CANONICAL-PURPOSE-AND-UNIFICATION-DECISIONS |
| Verdict | GOVERNANCE_AUDIT_BLOCKED_STATIC_DUPLICATION |

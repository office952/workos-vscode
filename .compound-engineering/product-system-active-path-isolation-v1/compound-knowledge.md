# Compound knowledge — Product System V2 active-path isolation (V1)

**Task:** `PRODUCT_SYSTEM_ACTIVE_PATH_ISOLATION_V1_COMPOUND`  
**Status:** Closeout — reusable for future agents without rereading full task history  
**Code-review verdict:** `APPROVE_WITH_NON_BLOCKING_FOLLOWUPS`  
**Runtime verdict:** `PASS_V2_PILOT_WITH_LEGACY_BRIDGE`  
**Snapshot verdict:** `PARTIAL_BLOCKED_BY_SNAPSHOT_RUNTIME_DATA`

---

## Core lesson (read first)

This task established **one canonical V2 active path for the pilot** (Letters V2 + ACM + Premount policy/aggregate). It did **not** prove full WorkOS business E2E for every product, non-V2 template, or Cost → Offer → Order → Execution with real fixtures.

Do not collapse "V2 pilot isolation proven" into "repo-wide canonical truth" or "complete commercial flow proven."

---

## 1. What problem was solved?

Hidden **parallel template identity** and **Dossier compiler authority** let legacy aliases and approved dossier JSON influence V2 compilation without an explicit, auditable boundary. Operators could not trust that Product System V2 endpoints reflected one canonical technical truth path.

**Solved:** Explicit canonical identity enforcement on active compile/write surfaces; dossier limited to metadata/provenance on V2 pilot; canonical template contracts own behavior-bearing fields for Letters V2; capability policy aligned for ACM/Premount.

---

## 2. What was the root architectural risk?

**Silent identity redirection** — accepting `TPL-VOLUMETRIC-LETTERS` (or trim/case variants) on write/compile paths and persisting non-canonical codes.

**Parallel compiler input** — approved Dossier JSON (variants, output blocks, task rules, cost mapping) acting as a second source of technical truth alongside `product_templates`, module links, and component contracts.

---

## 3. What implementation pattern solved it?

### Canonical identity pattern

| Layer | Mechanism | Location |
|-------|-----------|----------|
| Normalize | trim + uppercase | `normalize_template_code()` |
| Read bridge | explicit legacy alias with metadata | `resolve_template_identity()` |
| Active gate | reject non-canonical / legacy alias | `require_canonical_template_code()` |
| Stored identity | DB/registry lookups use resolved canonical casing | aggregate, definition builder, mini-modules |

**Active compile/write surfaces** (all use `require_canonical_template_code`):

- ProductAggregate, ProductDefinition, mini-modules, cost-bom preview, commercial price, EIC, Quote Snapshot V2 preview/freeze

**Behavior:**

- Canonical exact / trim / case → accept; return stored canonical casing
- Known legacy alias on active path → **422** `rejected_alias` (explicit envelope)
- Unknown alias → **404** `template_not_found`
- No silent persistence, no default-template fallback

### Dossier authority pattern

| Role | V2 pilot |
|------|----------|
| Allowed | metadata, provenance, inspection, approval visibility |
| Forbidden | components, operations, task rules, variants, output blocks as compiler input |
| Enforcement | `dossier_consumption_policy.py` + `CanonicalTemplateContractService` |
| Trace | `DOSSIER_METADATA_ONLY`, `CANONICAL_CONTRACT_AUTHORITY` warnings on aggregate |

**Canonical owners (Letters V2 pilot):**

- Variants / output blocks → `backend/data/canonical_*_volumetric_v2.py` via `canonical_template_contract_service.py`
- Components / graph → `product_templates` + module links + aggregate builder
- Operations / task generation (readiness) → canonical path uses template operations, not dossier task_rules

**Non-V2 legacy bridge (documented, not removed):**

- `product_readiness_service`, intake v4 fallback variants, non-canonical templates may still read dossier — explicit `LEGACY_BRIDGE`, not repo-wide isolation

### Modularity and ownership pattern

- **Product Template composes** — does not own component internals
- **Component path owns component truth** — module templates + links
- **ProductDefinition composes** coherent solution previews from form contracts + registry
- **ProductAggregate is the technical graph** — root + linked children identifiable downstream
- **ACM** — root offerable + linked child; standalone ProductDefinition builder
- **Premount** — root offerable + linked child; aggregate 200; ProductDefinition unavailable until form contract (explicit 404, not silent downgrade)
- **Risk avoided:** hidden parent truth, duplicated operations — gated by canonical identity + dossier consumption policy

---

## 4. What approaches were rejected?

| Rejected | Why |
|----------|-----|
| Silent alias acceptance on compile/write | Hides parallel ownership; fails audit |
| Dossier as default compiler for V2 | Restores parallel truth |
| Restoring dead Intake V3 OpenAPI paths in dev readiness | Masks real readiness; keeps deprecated surface alive |
| Changing ports to bypass :8000 ghost listener | Wrong fix; document and stop after budget |
| Fabricating snapshot rows during runtime proof | Invalidates proof; static boundary review only |
| Claiming repo-wide dossier isolation | Non-V2 paths still consume dossier by design |
| UI-only write prevention for dossier | Backend must be source of truth |
| Committing `dev.db` or seed as application truth | Environment contamination |

---

## 5. What runtime/tooling failures occurred?

| Failure | Symptom |
|---------|---------|
| Stale Intake V3 readiness gate | `/health` 200 but `dev:stack` failed — missing deprecated OpenAPI paths |
| PowerShell parser error | Unicode em-dash in `start-dev.ps1` diagnostics string → script never started processes |
| Empty dev.db | Stack OK but catalog/capability proof blocked (`FAIL_CAPABILITY_TRUTH`) |
| Probe stdout encoding | Romanian characters in API output → `UnicodeEncodeError`; fixed by JSON file write |
| Blueprint Dossier UI | Entity API 4 rows; studio chip "Active (0)" when template list empty |
| Snapshot tables empty | Expected after catalog seed; no V2 snapshot fixture in repo seed |

---

## 6. How were failures diagnosed?

- **Readiness vs health:** compare `Test-HttpOk(/health)` vs OpenAPI path predicate in `scripts/start-dev.ps1`
- **Parser-only validation:** `[System.Management.Automation.Language.Parser]::ParseFile` before runtime
- **DB pre/post counts:** explicit `DATABASE_URL` + sqlite queries; backup before seed
- **Single stack owner:** one `npm run dev:stack`; reuse healthy backend PID when possible
- **API matrix probes:** canonical / legacy / unknown template codes with status + envelope inspection
- **Parallel read-only workstreams:** identity, dossier, capability, snapshot, UI — coordinator synthesizes once

---

## 7. Fixture activation rules (canonical)

1. **Seed is not application runtime truth** — dev fixture only
2. **`dev.db` never committed** — backup before mutation (`dev.pre-*.db`)
3. **Explicit `DATABASE_URL`** — target worktree path (`C:/w/psiso/backend/dev.db`), never assume AGENTS example path
4. **One seed owner, one execution** — `scripts/seed_sync_all.py` for catalog/dossier metadata/module links
5. **Pre/post counts** — verify canonical templates, dossier rows, forbidden commercial tables stay 0
6. **Health gate must not require product fixtures** — stack ready ≠ catalog populated
7. **Proof preconditions outside general readiness** — seed owner GO separate from stack start
8. **Snapshot fixtures must not be fabricated** — accept `PARTIAL_BLOCKED_BY_SNAPSHOT_RUNTIME_DATA` or dedicated future seed
9. **No second stack** during proof/review phases

---

## 8. Figma workflow (canonical)

1. **Read-only** — Figma MCP/plugin; no design edits during proof
2. **Exact file / page / node** — e.g. ERP PUBLIMEDIA `911Q6oRKcEursrRoT4Qj0h`, nodes 7:6, 7:18, 7:29
3. **Figma = UI truth reference, not business truth** — backend policy/API wins on conflicts
4. **Runtime screenshot required** — store under `docs/qa/product-system-active-path-isolation-v1/`
5. **`NO_RELEVANT_FIGMA_FRAME`** when admin/dossier surfaces have no frame — do not invent PASS
6. **Classify drift:** functional (missing card, wrong filter) vs cosmetic (tab label, badge)
7. **Never UI PASS from Figma alone**

---

## 9. Multitasking model (canonical)

| Rule | Detail |
|------|--------|
| Worktree | Official linked worktree `C:\w\psiso`; protect main workspace |
| Owners | One implementation owner; one DB mutation owner; one runtime owner |
| Analysts | Parallel **read-only** workstreams (A–H); **AWAIT ALL**; coordinator synthesizes once |
| Edits | No concurrent edits to same file; no duplicate stacks |
| Review/compound | Documentation only — no app code, no DB, no runtime |

---

## 10. What remains outside this task?

- Premount operational catalog card (FE filter parity)
- Premount Intake V6 form contract / ProductDefinition builder
- Blueprint Dossier Studio list wiring (Active 0 vs entity API)
- Snapshot V2 → Order → ExecutionPlan runtime fixture chain
- Full Cost → Offer → Order → Execution business case
- Non-V2 template canonical promotion
- Complete Product Definition solution selection UX
- Employee Mobile, materialization, production deployment truth

---

## 11. What must future agents never claim?

- Repo-wide Dossier isolation (non-V2 legacy bridge remains)
- All non-V2 templates on canonical path
- Complete WorkOS E2E commercial flow proven
- Snapshot/execution frozen chain proven at runtime (only static architecture unless fixtures exist)
- Premount ProductDefinition available (404 is expected until form contract)
- Frontend catalog parity with backend `ROOT_OFFERABLE_TEMPLATE_CODES` (Premount omitted in FE scope)
- PASS based on empty DB or seed rows alone without boundary behavior proof
- Dossier safe based on UI hiding alone
- `validate:frontend` green (known TS debt)

---

## 12. Next roadmap position

**Closeout complete** for Product System V2 canonical active-path isolation (pilot). **Next:** scoped owner commit → dedicated builds for FE parity, Premount form contract, snapshot fixtures, then broader E2E product composition (Cost → Offer → Order → Execution).

Recommended shortcut after commit: broader **Product Definition solution selection** and **snapshot fixture** builds — not automatic.

---

## Proven vs partial vs not proven

### Proven

- V2 canonical identity boundary (active reject + read bridge)
- Legacy write rejection (422) and unknown alias (404)
- V2 Dossier metadata-only boundary (pilot consumers)
- ACM/Premount capability policy (backend)
- Runtime stability (single stack, health/OpenAPI/frontend 200 post-seed)
- Catalog/detail runtime proof (Letters, ACM; Premount direct URL)
- Figma read-only verification + runtime screenshots
- Targeted pytest (47 pass across identity, dossier, aggregate, template scope)

### Static or partial

- Snapshot/execution frozen-chain **runtime** proof
- Premount ProductDefinition (explicit unavailable)
- Complete frontend parity (`activeTemplateScope` omits Premount)
- Full Product Definition solution selection
- Full Cost → Offer → Order → Execution business case
- Blueprint Dossier studio list vs entity API

### Not proven

- Repo-wide Dossier isolation
- All non-V2 templates on canonical contracts
- Complete WorkOS E2E
- Employee Mobile, materialization, production deployment truth

---

## Key file map (future agents)

| Concern | Primary files |
|---------|----------------|
| Identity | `backend/services/template_architecture_scope.py` |
| Dossier gate | `backend/services/dossier_consumption_policy.py` |
| Canonical contracts | `backend/services/canonical_template_contract_service.py`, `backend/data/canonical_*_volumetric_v2.py` |
| Capability | `backend/services/template_usage_mode_policy.py` |
| Aggregate | `backend/services/product_aggregate_service.py` |
| Definition | `backend/services/product_definition_builder_service.py` |
| Snapshot | `backend/routers/quote_snapshot_v2.py`, `backend/services/quote_snapshot_v2_service.py` |
| FE scope (stale vs backend) | `frontend/src/lib/activeTemplateScope.ts`, `productSystemCanonicalCatalogModel.ts` |
| Dev stack | `scripts/start-dev.ps1` |
| Tests | `backend/tests/test_product_system_identity_boundary.py`, `test_dossier_true_isolation.py`, `test_dossier_consumption_policy.py` |

---

## Commit preparation (reference only — do not stage from compound task)

See `final-report.md` § Include/Exclude for grouped staging list.

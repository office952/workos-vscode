# Product System — Finish & Task Organization Comparison

| Field | Value |
|-------|-------|
| Date | 2026-07-18 |
| GO | `GO_AUDIT_HISTORICAL_PRODUCT_SYSTEM_BLUEPRINT_UI` |
| Related | `docs/audits/2026-07-18_product_system_blueprint_historical_ui_audit.md` |

---

## 1. Finishes — where they live

| Location | Organization style | Authority today | Reuse? |
|----------|-------------------|-----------------|--------|
| Blueprint Dossier | **Absent** as finish registry | N/A | Do not invent finish SoT in dossier |
| ProductSystem component-first maps | Component keys (`volumetric_surface_finish`, return cant finish fields) with `shouldOwn` / gaps | Readonly readiness / truth mapping | CONCEPT + REUSE_WITH_ADAPTER |
| Intake V6 FinishSetup | Operator-confirmed face/return/artwork finishes; Oracal/RAL paths | **Job instance truth** for sold surfaces | Keep |
| Color registries (FE) | RAL / Oracal config | Display / selection — not automatic CostEngine rates | Keep boundary |
| ACM / ACP panel config | Thickness, fold, frame — not full multi-face finish matrix | Product component config (Intake Step 2) | Current ACP path; extend later under contracts |

### Finish questions (audit answers)

| Question | Answer |
|----------|--------|
| Good reusable model? | **Partial** — component ownership maps + Intake FinishSetup; not Blueprint Dossier |
| UI without authority? | Yes — some ProductSystem warnings still show mixed hydration |
| Tied to right component? | Directionally yes for letters face/cant/finish; incomplete for ACP multi-zone faces |
| Parallel names? | Yes historically (`finish_target`, `return_finish_type`, mounting vs product) |
| Material–finish deps? | Partially in Intake / registries; not in dossier |
| Conditional applicability? | Sold-scope visibility in Intake; weak in Product System catalog |
| Inactive isolation? | Template activation scope stronger now than dossier |

### ACP finish expressiveness (old Blueprint vs need)

| Treatment | In old Blueprint Dossier? | Where it should live |
|-----------|---------------------------|----------------------|
| ACP stock color | No | Component / material RO + job config |
| Oracal | No (letters Intake) | Finish component / Intake |
| Painted RAL | No | Finish / paint path |
| Face cut-out | Partial mock type only (`FATA_ACP_ROUTATA` in ProductSystem viz) | Composition + geometry |
| Plexiglas back | Letters Intake / modules | Component contracts |
| Insert plexiglas 10 mm | No dedicated Blueprint org | Future composition zones |
| Multiple treatments same face | **No** | Needs composable face model — **not** recovered from lost Blueprint canvas |

---

## 2. Tasks & operations — where they live

| Location | What it stores | Classification |
|----------|----------------|----------------|
| Dossier `task_rules_json` | Name, required/optional, trigger, time, notes | **Documentation configurator** — “nu creează task-uri” |
| Modular process resolver → Aggregate | Compiled `task_rules` for letters path | **Canonical compile** |
| Existing tasking / ExecutionPlan | Operational tasks | **Canonical runtime** |
| Template operational tab | Ops / capabilities on product template | **Technical config** |
| Planned `/product-system/operations` | Stub “Planificat” | **Mock / planned** |
| Operator production blueprint | Live order ops view | **Execution domain** |

### Desired chain (unchanged)

```text
component / interface contracts
→ resolver process DAG
→ ProductAggregate task_rules
→ existing mature tasking
```

Blueprint may **visualize and document** rules. It must not create a new scheduler.

### Parallel tasking risks

| Risk | Severity | Action |
|------|----------|--------|
| Treat dossier task_rules as production SoT | High | Keep guidance banner; no new generators |
| Build React Flow task graph “from Blueprint” | High | Reject — never existed; unsafe parallel |
| Wire Operator blueprint into Product System admin | Medium | Keep domains separate |

---

## 3. Side-by-side organization quality

| Concern | Historical clearer UI (IA + Dossier groups) | Current active UI |
|---------|---------------------------------------------|-------------------|
| Seeing “what belongs where” | Stronger (tabs + section groups) | Weaker overview; stronger honesty |
| Editing finishes | Weaker (not in dossier) | Intake + partial ProductSystem maps |
| Editing task rules safely | Dossier docs editor OK | Aggregate/resolver path maturer for letters |
| ACP mixed faces | Neither era complete | Current contracts + Intake closer to path |

---

## 4. Concepts worth recovering (finishes/tasks)

1. **Section groups with explicit authority banners** (quote vs production vs docs).
2. **Primary navigation that separates Products / Components / Dossiers / Guards** (IA pattern) — as labels over live contracts, not empty stubs pretending to work.
3. **Task rules editor UX** — only as documentation adapter over Aggregate-visible rules.
4. **Not** recovering finish SoT into dossier JSON.

---

## 5. Out of scope reminders

CPP · new task engine · Execution · Employee Mobile · schema/migration for “Blueprint v2”.

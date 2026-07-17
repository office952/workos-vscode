# Plan — Product Process Contract + Simple Resolver (future GO)

| Field | Value |
|-------|-------|
| Date | 2026-07-17 |
| Status | PARTIALLY DELIVERED — process path + typed Intake fields + typed cable qty on live materials; channel/template commercial gaps guarded; persistence still gated |
| Depends on | Owner review of CPP electrical input wiring before channel formula / persistence GO |
| Pilot product | Litere volumetrice luminoase / `TPL-VOLUMETRIC-LETTERS_v2` |
| Out of scope | Build 4B, 4C.1, 4D, Intake UI rewrite, CPP redesign, schema/migration unless gate forces |

---

## 1. Goal (single future build)

Deliver **one coherent build** after owner GO:

`PRODUCT_PROCESS_CONTRACT` + **simple dependency resolver** + **one canonical product** (volumetric illuminated letters).

Not: BPM engine, 100-product rollout, Employee Mobile, ExecutionPlan writes, task materialization.

---

## 2. Recommended architecture (locked for plan)

**Hybrid A+C** (see integration audit §3):

- Shared process/state/capability **catalog** (versioned JSON).
- Component Templates own local process fragments + material roles.
- Product Template composes components + interface contracts.
- Job instance stays Intake → ProductDefinition → Aggregate → Snapshot.
- Resolver emits `task_rules` with real `depends_on` (sequence = tie-break).
- Freeze + Build 4C remain read-only consumers.

---

## 3. Implementation units (after GO)

### Unit 1 — Shared catalogs (docs → data file)

- `process_catalog_volumetric_v1.json` (or dossier section) matching process graph codes.
- `state_catalog_v1.json`.
- Capability codes mapped to existing `OperationResourceRequirement` where possible.
- Tests: catalog unique codes; no curing state; vinyl→form edge present.

### Unit 2 — Component process fragments

- Map Face / Cant / Back / LED / Support / Electrical / Finish to fragments.
- Prefer activating inert `TPL-COMP-LETTER-*` patterns **or** versioned JSON beside mini-modules — owner gate chooses storage.
- Tests: cant vinyl branch activates APPLY before FORM; RAL after BOND; no-support omits channel.

### Unit 3 — Product composition + interfaces

- Product Template references components + interface `FACE_CANT_BOND`, `BODY_TO_BACK`, `BACK_TO_SUPPORT`.
- Replace hardwired FACE+CANT-only knowledge gradually; do not break ActiveScope isolation tests.

### Unit 4 — Simple resolver service

```text
resolve_process_graph(config) -> {
  active_processes, states, edges, topo_order, blockers, task_rules
}
```

- Pure function; no DB writes.
- Cycle detection; orphan edge detection; scope.errors → blocked (no fail-open).
- Tests: full / vinyl / RAL / bars / alucobond / no-support / template parallel.

### Unit 5 — Text generators

- Three templates: commercial / technical / internal.
- Inputs: confirmed geometry + config + active process summary.
- Tests: Config A/B/C golden strings (Romanian).

### Unit 6 — Aggregate emit (thin bridge)

- Extend `ProductAggregateTaskRule` **in-memory / schema** with optional `depends_on_process_ids` (prefer no migration).
- Compile from resolver output; keep priced_operation bridge.
- Regression: Build 3 subset isolation + Build 4A/4C tests green.

### Unit 7 — Freeze projection only

- Ensure Snapshot V2 carries enriched task_contract.
- Build 4C projects edges if present; else sequence fallback (guard documented).
- **No** ExecutionPlan persist; **no** materialize.

---

## 4. Explicit non-goals

- Snapshot disposable persistence (4B)
- Owner-facing Execution preview UI (4C.1)
- Task materialization / assignments / sessions (4D+)
- Generic multi-tenant process engine
- Redesign CPP formulas wholesale
- Seed all 100 products
- Delete dead V1 paths

---

## 5. Sequencing

```text
Owner gates answered
  → GO PRODUCT_PROCESS_CONTRACT_AND_SIMPLE_RESOLVER
  → Units 1–5 (contract + resolver + texts)
  → Unit 6 Aggregate bridge
  → Unit 7 freeze/4C consume edges
  → Owner review runtime proof (read-only)
  → Separate GO for Intake field gaps (cable, corner, screws)
  → Much later: 4B/4D if still needed
```

---

## 6. Test plan (future)

| Layer | Scenarios |
|-------|-----------|
| Unit | active_when matrix; DAG acyclic; vinyl order; RAL order; LED adhesives; no channel on alucobond; no-support pack PSU |
| Golden texts | Config A/B/C |
| Regression | Build 3 / 4A / 4A.1 / 4C |
| Negative | cycle; missing material role; scope.errors; unsupported V1 |
| No-write | resolver + preview endpoints |

---

## 7. Risk register

| Risk | Mitigation |
|------|------------|
| Dual SoT fight | Owner gate authority before coding |
| Naming drift ops | Alias map in catalog; don’t mass-rename CostEngine keys in same build |
| CPP cable missing | Commercial gate; resolver can emit material role without price |
| Scope creep to 4D | Hard stop list in GO |
| Break FACE+CANT isolation | Keep Build 3 assertions as gate |

---

## 8. Success criteria for future build

- Workshop branches expressible without curing / separate drill process.
- Resolver DAG matches process graph doc.
- One product only.
- No schema/migration unless owner forced Option 3.
- No Execution writes.
- Docs updated; worklog; isolated commit when GO includes commit.

---

## 9. Next step now

**Owner review only** (see owner gates). Do not start Units 1–7 until GO.

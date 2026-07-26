# Product Process Contract (cross-product)

| Field | Value |
|-------|-------|
| Status | CONTRACT_V1 / IMPLEMENTED_PILOT (resolver + catalogs) |
| Date | 2026-07-17 |
| Pilot | Litere volumetrice luminoase |
| Runtime | Pure resolver + **live Aggregate overlay** (`apply_modular_process_graph_to_aggregate`); Intake/CPP/UI unchanged |

This contract generalizes the letters canonical process so future products can reuse the same spine without a BPM engine.

---

## 1. Law

```text
Product Template
  composes Component Templates
  + interface contracts
  + text templates
  + form bindings
  + refs into shared process/state/capability catalog

Component Template
  owns local process fragments
  + material roles
  + capability needs
  + local dependencies

Job instance (Intake → ProductDefinition → Aggregate)
  resolves active processes for THIS job
  emits task_rules + depends_on
  feeds CPP (money) and Snapshot (freeze)

Frozen snapshot / Execution preview
  consume resolved truth
  NEVER become the rule authoring surface
```

---

## 2. Shared catalogs

| Catalog | Contents | Non-goals |
|---------|----------|-----------|
| Process | `process_code`, name, default deps, capability, material roles, commercial_visibility | Not runtime task IDs |
| State | small reusable tokens | No academic states; no adhesive curing |
| Capability | codes mapped to machines registry | No machine SKU on product |

Version: `catalog_version`. Products pin the version they were authored against.

---

## 3. Component process fragment (shape)

```json
{
  "component_code": "COMP-LETTER-CANT",
  "processes": [
    {
      "process_code": "APPLY_CANT_VINYL",
      "active_when": { "cant_finish": "vinyl" },
      "requires_states": ["CANT_STRIP_READY"],
      "produces_states": ["CANT_VINYLED"],
      "depends_on": ["PREPARE_CANT_STRIP"],
      "material_roles": ["CANT_VINYL"]
    }
  ]
}
```

---

## 4. Interface contract (shape)

```json
{
  "interface_code": "INTERFACE_FACE_CANT",
  "active_when": { "modules": ["face", "cant"] },
  "processes": ["BOND_FACE_TO_CANT"],
  "material_roles": ["CYANOACRYLATE_ADHESIVE", "CYANOACRYLATE_ACTIVATOR"],
  "requires_states": ["FACE_READY", "CANT_FORMED"],
  "produces_states": ["LETTER_BODY_READY"]
}
```

Interfaces own cross-component bonding/attach rules so Product Template does not hardcode FACE+CANT forever.

---

## 5. Resolver (minimal)

Pure function; no persistence; no inventory reservation; no ExecutionPlan.

Inputs: confirmed config + composed fragments + interfaces + catalog version.  
Outputs: active processes, state expectations, DAG edges, topo order, blockers, task_rules, text payloads.

Failure modes: cycle, missing role, `scope.errors`, unsupported legacy → **blocked/degraded**, never silent full-product invent.

---

## 6. Relation to existing docs

- Extends `PRODUCT_SYSTEM_PRODUCT_TEMPLATE_VS_COMPONENT_TEMPLATE_CONTRACT.md`
- Compatible intent with `PRODUCT_COMPONENT_DOSSIER_TASK_DEPENDENCY_CONTRACT.md`
- Letters instance: `LITERE_VOLUMETRICE_LUMINOASE_*` docs
- Does **not** replace Build 4 frozen graph law

---

## 7. Forbidden

- Process Template as parallel Product System
- Frozen graph as authoring SoT
- All-operations → tasks
- Hardcoded machine names on products
- Second material registry
- Schema-first BPM without owner Option 3

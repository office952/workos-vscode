# NEXT_BUILD_OPTIONS_AND_RECOMMENDATION

**Post tip:** `8b960a19` · **Fixture:** 92401 / 13 · **Authorize:** false

## Options compared

| Option | Available truth | False-semantics risk | Ops value | Dependencies | Reversible | Systems touched | DB mutation | Frozen snap impact | Component-owned fit | E2E ready? | Pricing mix risk | Inventory mix risk | Premature materialize risk | Verdict |
|--------|-----------------|----------------------|-----------|--------------|------------|-----------------|-------------|--------------------|---------------------|------------|------------------|--------------------|----------------------------|---------|
| **A. Upstream Material Quantity & Ownership Contract** | formula_id×20; geometry/config; provenance; roles | Low if contract is explicit & null-honest | Unlocks all later material work | Product Truth / Aggregate compile | High (docs+compile rules before re-freeze) | ProductDefinition, Aggregate, templates | Prefer none until new DEV freeze | New version only if accepted | **Best fit** | Foundation for E2E | Low if prices excluded | Low if inventory excluded | None | **RECOMMENDED** |
| B. Material Planning Hints RO | Codes/units/provenance only; qty null | **High** if hints imply need/stock | Medium UI | Needs A for non-misleading hints | High | Execution read model | None | None | Weak until A | No | Medium | Medium | Low | Premature as *next* sole build |
| C. Procurement Readiness audit/RO | No owned qty; no OC contract | **Very high** false “ready to buy” | Low/misleading | A (+ maybe B) | Medium | Procurement/OC | Likely later | None | Poor | No | Medium | High | Low | Defer |
| D. Material → Operation contract | Empty material_inputs; no binding | High if mapped by name only | High later | A first (what to map) | Medium | Execution envelope / task contract | Possibly | Risk if rewritten in place | Needs owned materials | No | Low | Low | Medium (temptation to rematerialize) | Defer |
| E. Inventory integration | Stock exists elsewhere | **Critical** if used as BOM qty | Availability only later | A + D | Low once coupled | Inventory | Likely | Live drift risk | Violates component-owned BOM | No | Medium | **Critical** | Medium | **Reject as next** |
| F. Materialization | Envelope already 18 ops; authorize false | Rewrites ops risk | None for materials truth | DEC-003/005/006/007 + Owner GO | Low | Execution | Write | Indirect | Irrelevant to qty ownership | No | — | — | **Critical** | **Reject** |
| G. Other repo-demonstrated | Task WC/minutes enrichment | Medium if invent | Scheduling | Separate DECs | Medium | Execution | Possibly | — | Orthogonal | Partial | Low | Low | Medium | Parallel track, not materials next |

---

## Recommendation

```text
OWNER GO — Upstream Material Quantity & Ownership Contract
```

### Smallest coherent frontier

1. Define per-family ownership (component vs composition vs config vs reference-only).
2. Define quantity model per family (A/B/C/D — **not E**).
3. Define active-variant rules (face finish exclusivity; return depth exclusivity; parent vs linked_module same-code rows).
4. Define freeze rules: evaluate formula → persist quantity **or** explicit null with reason code; never null→0.
5. Produce Owner-stamped contract + gap list for which formulas can compute on current 92401 inputs vs missing inputs.
6. **No** inventory, procurement mutation, material_inputs fill, rematerialize, pricing.

### Explicitly out of scope

- Inventory stock/reservation/consumption
- Procurement PO / OC mutation
- Material → operation mapping implementation
- Further materialization / authorize / sessions / actuals
- WC/minutes invent
- RETURN production collapse (separate Owner decision; may run in parallel docs)
- Employee Mobile / HR / SVG-DWG parse
- UI redesign beyond what a future contract surface needs

### Why not the others

| Option | Why not next |
|--------|----------------|
| B Planning Hints | Without owned qty/active variants, hints overstate BOM (22 rows include alternatives). |
| C Procurement Readiness | Cannot declare buy-ready without quantity ownership. |
| D Material→Op | Nothing truthful to bind; empty inputs are honesty, not absence. |
| E Inventory | Answers availability, cannot invent product technical need. |
| F Materialization | Already done for 92401; DEC-009 blocks further POST; does not fix qty ownership. |
| G Task enrichment | Valuable but orthogonal; does not close materials upstream gap exposed by `8b960a19`. |

---

## Preconditions already satisfied for A

- Frozen materials visible and honest (`8b960a19`)
- Provenance + formula_id mostly present
- Inventory/pricing boundaries held on ops-graph
- Owner GO format available without combining forbidden scopes

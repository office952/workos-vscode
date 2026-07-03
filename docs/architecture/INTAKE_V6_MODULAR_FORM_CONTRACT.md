# Intake V6 Modular Form Contract

**Version:** 1.0.0  
**Status:** Step 5 — read-only form contract aligned with mini-module registry  
**Pilot template:** `TPL-VOLUMETRIC-LETTERS_v2`  
**Companion docs:** [MODULAR_PRODUCT_FLOW_CONTRACT.md](./MODULAR_PRODUCT_FLOW_CONTRACT.md), [MINI_MODULE_CONTRACT_REGISTRY.md](./MINI_MODULE_CONTRACT_REGISTRY.md)

---

## 1. Purpose

Intake V6 must not be free-form data collection. Each field must:

1. Activate or configure a mini-module  
2. Produce a canonical key for ProductDefinition (Step 6)  
3. Be traceable in ProductAggregate  
4. Have a declared path to Cost Engine / Quote / Order / Task — or be `FUTURE_RESERVED_STEP_X`

Step 5 defines the **modular form contract** without pricing, without full ProductDefinition builder, without DB writes.

---

## 2. Relationship to mini-module registry

```
Mini-module Registry (Step 4)
    ↓ consumed_form_fields, activation_rules
Intake V6 Modular Form Contract (Step 5)
    ↓ field_bindings.workspace_path
Intake V6 workspace payload (finish_setup, quote_geometry, svg_source)
    ↓ pricing input adapter
quote_input_payload
    ↓ Step 6
ProductDefinition
```

**Endpoint (read-only):**

```
GET /api/v1/intake-v6/form-contract/{template_code}
```

Implementation: `intake_v6_modular_form_contract_service.py` derives from registry + volumetric field map.

---

## 3. Intake V6 flow (current)

| Step | ID | UI | Primary payload keys |
|------|-----|-----|----------------------|
| 1 | `layers` | SVG analyzer | `svg_source`, `svg_analysis_json`, `layer_role_setup`, `quote_geometry` |
| 2 | `review` | Finish / lighting / mounting | `finish_setup` |
| 3 | `confirm` | Handoff / preview | reads `pricing-input-preview` → `quote_input_payload` |

**Workspace schema:** `IntakeV4WorkspacePayload` aliased as V6 (`backend/schemas/intake_v6.py`).

**Quote input builder:** `intake_v4_pricing_input_service.py` → `intake_v6_pricing_input_service.py`.

**Template form options (existing):** `GET .../workspaces/{id}/template-form-contract` — dossier variant fields for UI dropdowns. Step 5 contract is **template-level modular map**, complementary not replacement.

---

## 4. ACTIVE modules — form mapping

### geometry_svg (always_on)

| Consumes | Workspace path | PD keys | Task direct? |
|----------|----------------|---------|--------------|
| vector_file, dimensions, counts, perimeter | svg_source, client, quote_geometry | dimensions, quantity, geometry metrics | **NO** — readiness gate only |

### debitare_fata (always_on)

| Consumes | Required |
|----------|----------|
| face_finish_type, letter_face_area_m2, letter_group_finishes | face_finish_type |

### modelare_cant (required_module)

| Consumes | Activates via |
|----------|---------------|
| return_depth_mm, return_finish_type, volum_aluminum_module_template_code | required_module link + form selector |

### debitare_spate (always_on)

| Consumes | Required |
|----------|----------|
| backing_mode, back_bevel_enabled | backing_mode |

### sistem_led (conditional)

| Consumes | Activates when |
|----------|----------------|
| lighting_system_type, led_module_count, selected_psu_watts | illuminated / lighting_system_type set |

### finisaje (conditional)

| Consumes | Activates when |
|----------|----------------|
| mounting_template_enabled, letter_group_finishes, mounting_template_area_m2 | sablon gate optional |

### structura_suport (optional_addon)

| Canonical Intake | Derived quote_input |
|------------------|---------------------|
| **finish_setup.mounting_system** | metal_support_required, premount_bar_length_ml, bar_material |

---

## 5. TRIGGER_FIELD_MISMATCH resolution

**Problem:** DB module link uses `trigger_field: metal_support_required`. Intake operator uses `finish_setup.mounting_system`.

**Canonical trigger (Step 5):** `finish_setup.mounting_system`

**Derivation (existing, preserved):**

```
mounting_system in ('steel_bars', 'aluminum_bars')
  → quote adapter sets metal_support_required=true
  → linked_modules[TPL-METAL-PREMOUNT-STRUCTURE_v1]
```

**We do NOT:**

- Hide ProductAggregate `TRIGGER_FIELD_MISMATCH` warning  
- Change DB module link in Step 5  
- Add fake `finish_setup.metal_support_required` UI control  

**We DO:**

- Document alignment in form contract `trigger_alignments`  
- Mark `metal_support_required` as `derived_quote_input`  
- Keep backwards compatibility for existing quote payloads  

**Future:** migrate module link `trigger_field` to `mounting_system` in approved DB step (not Step 5).

---

## 6. Valid / invalid combinations

### Valid (examples)

- Full volumetric with LED + sablon optional  
- Premount when mounting_system = steel_bars | aluminum_bars  
- modelare_cant always on for v2  

### Invalid (examples)

- structura_suport expected without bar mounting selection  
- Orphan finish_setup fields without module binding  
- Treating parent template 1/1/2 counts as full product structure  

---

## 7. Orphan fields audit (documented, not removed in Step 5)

| Field | Status | Reason |
|-------|--------|--------|
| finish_setup.illuminated | READONLY_EXPLANATORY | UI gate → lighting_system_type |
| finish_setup.commercial_inputs | READONLY_EXPLANATORY | Quote layer, not product module |
| finish_setup.emblem_lighting_mode | FUTURE_RESERVED_STEP_6 | electrica_logo OPEN QUESTION |
| finish_setup.artwork_complexity_decisions | FUTURE_RESERVED_STEP_6 | Artwork-only path |

---

## 8. What Step 5 is NOT

- Not pricing / Cost Engine / reprice quote 4  
- Not ProductDefinition builder (Step 6)  
- Not full Intake UI re-layout (Step 5B optional)  
- Not DB seed / migration  

---

## 9. Step 6 handoff

ProductDefinition builder should consume:

- `field_bindings[].product_definition_keys`  
- `modules[].product_definition_outputs`  
- Active module set derived from form values + activation rules  

---

## 10. Acceptance criteria (Step 5)

- [x] This document exists  
- [x] Form contract schema + read-only service  
- [x] GET endpoint  
- [x] All 7 ACTIVE modules mapped  
- [x] TRIGGER_FIELD_MISMATCH documented with canonical key  
- [x] Orphan audit documented  
- [x] Library card guard (parent vs aggregate counts)  
- [x] Tests pass  
- [ ] Intake UI modular sections (Step 5B — optional)  

---

*Contract version 1.0.0 — aligned with mini-module registry 1.0.0.*

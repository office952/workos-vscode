# INTAKE_V6_ACM_COMPONENT_INSTANTIATION_AND_RELATIONSHIP_V1

| Field | Value |
|-------|--------|
| Date | 2026-07-20 |
| Mode | Implementation — owner GO on corrected plan |
| Runtime proof WS | `IV6-DB2F86B7` / `a7b0162b-dc91-467f-aa24-c1279fb3a073` |
| Evidence | `docs/audits/_evidence/2026-07-20_acm-component-instantiation/` |
| Boundaries | No blueprint impl, no 21st/Figma redesign, no historic remediation writes, no firmă/totem products |

---

## 1. Rezumat executiv

Gap-ul CFG este închis pe calea forward: confirmarea rolului `support_panel` produce **atomic** o instanță `AcmPanelComponentInstance` (association/technical = **proposed**), binding `SUPPORT_CONTOUR` (adapter Intake), mounting, `segmented_background` PROPOSED cu 2 panouri nested, relații geometrice cu status, **fără** auto-confirm composition și **fără** selection `confirmed` implicit.

Runtime `IV6-DB2F86B7`: toate check-urile PASS (inclusiv refresh). Composition confirmată doar după click operator.

**Scor direcție stabilită: 86/100**

---

## 2. Capability inventory

| Instrument | Folosit |
|---|---|
| Repo search | Da |
| Playwright runtime + screenshots 1440×900 | Da |
| API `:8003` (FE API base) | Da |
| SQL read-only / list scan | Da (dry-run) |
| Vitest / pytest | Da |
| 21st / Figma | Doar update handoff |
| Subagenți | Discovery plan mode |

---

## 3. Plan și workstreams

A/B/C atomic AcmPanel* · G race+domain_action · D composition explicit · E relații generice · F PD proposal panels · tests · runtime · docs/commit.

---

## 4. Contract final

### Nucleu generic
- `AcmPanelComponentInstance` / `Configuration` / `Capabilities` / `Geometry` / `ComponentRelation`
- Template: `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1`
- `SUPPORT_CONTOUR` = **adapter** consumer litere pe suport, nu definiția universală

### Stări
| Axis | La role confirm |
|---|---|
| role_status | confirmed |
| association_status | proposed |
| technical_configuration_status | proposed |
| composition_status | unconfirmed → confirmed doar după operator composition |

### Catalog defaults
`fold_count`, L1/L2, `acm_thickness_mm`, frame → `field_authority: catalog_default` (critical class, dar **nu** technical confirmed).

### Domain action
`acm_panel_domain_action = preserve | upsert | clear`

---

## 5. Atomic write-path

`buildAtomicAcmPanelInstantiationPatch` → un singur `persistFinishPatch` (Confirm All + manual).  
Segmented inclus în același PUT. Fără auto composition.

---

## 6. Binding și instanțiere

- SUPPORT_CONTOUR DRAFT când association=proposed
- Idempotent pe contour/hash
- Instance id: `acm_{contourId}_{svgHash12}`
- Embed de rezervă: `svg_support_selection.acm_panel_instance` (+ mounting.configuration)

---

## 7. Mounting hydrate

`buildAcmMountingSolutionProposed` — geometry detected, casing/thickness catalog_default, technical_configuration_status=proposed.

---

## 8. Composition

Recommendation actualizată din bindings/instance.  
`product_composition_confirmed` **doar** după CTA operator.  
Backend sync `composition_status` pe instanță la confirm.

---

## 9. Relationships

Geometry-derived: `belongs_to_assembly`, `positioned_on` / `contained_by` (sau `unknown` dacă multi-panel ambiguu).  
**Nu** auto `mounts_on` / `attached_to_structure`.

---

## 10. ProductDefinition

- `acm_panel_instance` + selection proposed → `acp_panel_active`, `acp_panel_technical_confirmed=false`
- `segmented_background_proposal` include `panels[]` (informational, no materials/tasks)
- CONFIRMED segmented rămâne gated

---

## 11. Aggregate

Nested panels via proposal observability; no pricing/task materialization pe proposal.

---

## 12. Tests

| Suite | Result |
|---|---|
| Vitest `acmPanel/instantiate.test.ts` + confirmation path | 4 passed |
| pytest coalesce + PD proposal + svg_support PD | 7 passed |

---

## 13. Runtime proof

Workspace: **IV6-DB2F86B7**  
Fixture: `litere-cu-fundal-acm-segmentat.svg` (clean)  
`runtime-summary.json`: **pass=true**

Highlights:
- SUPPORT binding DRAFT, selection **proposed**, mounting ACM, 2 panels PROPOSED
- instance `acm_cc_7af1352f_ff5c35da170d`
- composition not auto; operator confirm → true
- refresh keeps shell + instance + panels
- 0 artwork phantom
- relations: 2× belongs_to_assembly + positioned_on unknown (multi-panel — correct, no mounts_on)

---

## 14. Screenshot proof

URL: `/intake-v6/{id}/operator` · viewport 1440×900  
Evidence: `01-before-upload.png` … `05-after-refresh-layers.png`  
UI changes: behavior-only (atomic persist / preserve); no shell/token redesign.

---

## 15. Payload before/after

See evidence `payload-after-roles.json`, `payload-after-refresh.json`, `runtime-summary.json`.

---

## 16. Blueprint readiness delta

Now available on instance: stable component id, panels[], joints, bbox, dims, relations[], capabilities, field_authority, provenance, status axes.  
Still not implemented: blueprint read model UI, cutouts/inserts populated, MULTI ACM instances.

---

## 17. Remediation dry-run

Scan 216 WS (`dry-run-remediation.json`):

| Metric | Count |
|---|---:|
| CFG support without SUPPORT binding | 20 |
| CFG segmented without binding | 2 |
| Binding without acm_instance (historic) | 51 |
| P1 missing segmented | 18 |
| With quote | 0 |

Safe auto-repair candidates: P1 + upsert instance pe WS fără quote.  
Operator review: roluri ambigue / technical confirm.  
**No writes executed.**

---

## 18. Dead pieces check

- Orphan contour cards still unused in Step 1 — OK.
- Residual PD graph edge name `visual_mounting_support` — coupling cunoscut, composition sibling pe template.
- MAX_ONE SUPPORT_CONTOUR — blochează totem multi-face până la extensie cardinality.

---

## 19. Roadmap checkpoint

### Reuse firmă luminoasă ACM
Același `AcmPanelComponentInstance` + activate `graphic_cutouts`, `plexiglass_inserts`, `led_system`, `rear_closure` — fără template duplicat.

### Reuse totem
Multiple instances (extensie MULTI) + `totem_face` + `attached_to_structure` (operator) — modelul nu presupune „mereu support litere”.

### Modules supported now
`boxed_returns`, `rear_lip`, `segmented_panels` (+ slots inactive listate pe instanță).

### Extensions later
MULTI cardinality, cutouts/inserts/LED wiring, PD edge rename, association/technical operator confirm UI, safe historic auto-repair.

### Coupling residual
finish_setup transport; SUPPORT_CONTOUR adapter MAX_ONE; PD linked-child metaphor.

---

## 20. Commit

Single isolated commit (see git log).

---

## 21. Opinia sinceră

Implementarea respectă corecțiile owner (stări separate, fără auto composition, catalog_default, domain_action, relații generice). Race-ul letter-sync e adresat (queue + preserve). Punctul slab rămas: confirmarea tehnică a casing-ului încă nu are UI dedicat — defaults rămân proposed, corect, dar operatorul trebuie ghidat ulterior. Totem MULTI încă nu e posibil fără build separat.

---

## 22. Cat suntem in directia stabilita: **86/100**

---

## Owner gate

Așteaptă decizie pentru: remediation istorică · UI system audit · 21st integration · blueprint Nivel 1.

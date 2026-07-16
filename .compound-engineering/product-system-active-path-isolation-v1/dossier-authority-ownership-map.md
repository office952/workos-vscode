# Dossier Authority Ownership Map

Task: `PRODUCT_SYSTEM_DOSSIER_TRUE_ISOLATION_COMPLETION_V1`  
Pilot: `TPL-VOLUMETRIC-LETTERS_v2`

## Authority model (final)

| Behavior field | Canonical owner | Dossier role |
|----------------|-----------------|--------------|
| Components | `product_templates.components_json` + mini-module registry | metadata/provenance only |
| Materials | `product_templates.required_materials_json` + linked child templates | metadata only |
| Operations | `product_templates.operations_json` + linked modules | metadata only |
| Variants | `canonical_template_variants_volumetric_v2.py` | metadata only |
| Form contract | `IntakeV6ModularFormContractService` / `VOLUMETRIC_FIELD_BINDINGS` | metadata only |
| Output blocks (v2) | `canonical_output_blocks_volumetric_v2.py` | metadata only |
| Task rules | Template operations (partial) — full task mapping **OWNER_DECISION** | metadata only |
| Cost mapping | Template BOM / formula materials | metadata only |
| Dependencies | Component template links | metadata only |
| Readiness gates | Template.active + canonical completeness (v2) | dossier.status inspectable only |

## Legacy bridge (non-v2 Build 4)

Non-pilot templates retain approved-dossier legacy path for output blocks until PROMOTE_CODE per template. Classified `legacy_bridge_needing_isolation`.

## Blocked without owner decision

- Task-rule canonical owner for volumetric v2 (operations vs dedicated task contract module)
- Whether `ready_for_quote` still requires dossier `approved` vs template-only gate

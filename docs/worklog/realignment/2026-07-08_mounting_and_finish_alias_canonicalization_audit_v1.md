# 2026-07-08 — mounting and finish alias canonicalization audit v1

Summary:
- audited mounting and finish aliases across frontend/backend/docs/UI
- confirmed one live Product System mismatch: frontend displayed `TPL-VOLUMETRIC-MOUNTING-STRUCTURE_v1` although backend/runtime canonical code is `TPL-METAL-PREMOUNT-STRUCTURE_v1`
- finish drift in this slice is display aliasing only; no conflicting active finish template code found

What changed:
- updated Product System shared volumetric mappings to use `TPL-METAL-PREMOUNT-STRUCTURE_v1`
- updated focused Product System tests to assert the canonical mounting template code
- captured new `/product-system` runtime proof screenshots

What stayed intentionally unchanged:
- UI aliases `volumetric_finish` and `volumetric_mounting_structure`
- intake bridge `mounting_system` -> `metal_support_required`
- QuoteWizard / ProductDefinition / CostEngine semantics

Validation:
- `npm.cmd run test -- src/features/product-system/TemplateLibraryView.test.tsx` from `frontend/` -> PASS (13/13)

Risk note:
- docs and older exports still contain `TPL-VOLUMETRIC-MOUNTING-STRUCTURE_v1`; treat that name as documentation drift unless and until a dedicated migration slice says otherwise

Recommended next slice:
- UI-only canonical display cleanup for Product System owner keys and labels, without changing backend/runtime truth
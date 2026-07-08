# 2026-07-08 - return cant component truth paths canonicalization v1

HEAD before:

- `4c22e4f`

HEAD after:

- pending at write time

Fisiere citite:

- `RETURN_CANT_TRUTH_FIELDS_READONLY_MAPPER_CONTRACT.md`
- `RETURN_CANT_MISSING_TRUTH_FIELDS_CONTRACT.md`
- `RETURN_CANT_COMPONENT_PREVIEW_READINESS_REMEDIATION.md`
- `FORM_SYSTEM_COMPONENT_FIELD_OWNERSHIP_MAP.md`
- QA snapshot pentru mapper slice
- worklog pentru mapper slice
- `frontend/src/lib/intakeV6/productTruth/productTruthTypes.ts`
- `frontend/src/lib/intakeV6/productTruth/productTruthDraftBuilder.ts`
- `backend/services/form_system_contract_backbone_service.py`
- `backend/services/intake_v6_modular_form_contract_service.py`
- `backend/services/product_definition_builder_service.py`
- `frontend/src/lib/intakeV6/intakeV6QuoteGeometry.ts`
- `frontend/src/lib/intakeV6/intakeV6LayerRoleBridge.ts`
- `backend/services/letter_group_finish_readiness_service.py`

Ipoteza locala testata:

```text
Poate exista deja in runtime un path canonic explicit pentru face perimeter sau return_cant component truth.
```

Check-ul care a disconfirmat ipoteza:

- nu exista `components.face.confirmed_perimeter` in suprafetele read-only actuale;
- nu exista `components.return_cant.*` in read models actuale;
- exista doar fragmente necanonice: `components.return.depth_mm`, `components.returnCant.depthMm`, `quote_geometry.letter_perimeter_m`, `return_oracal_code`.

Concluzie:

- runtime-ul nu este pregatit sa exprime singur schema canonica;
- dar schema poate fi definita contractual suficient de precis pentru implementarea urmatorului mapper read-only.

Fisiere atinse:

- `docs/architecture/product-system/RETURN_CANT_COMPONENT_TRUTH_PATHS_CANONICALIZATION.md`
- `docs/qa/return-cant-component-truth-paths-canonicalization-2026-07-08/RETURN_CANT_COMPONENT_TRUTH_PATHS_CANONICALIZATION_V1.md`
- `docs/worklog/realignment/2026-07-08_return_cant_component_truth_paths_canonicalization_v1.md`

Decizie:

- `RETURN_CANT_CANONICAL_PATHS_READY_FOR_MAPPER_IMPLEMENTATION`

Interpretare:

- canonical path model-ul este acum destul de clar incat mapperul sa poata fi implementat fara sa ghiceasca ownership-ul;
- implementarea efectiva ramane separata de acest task.

Forbidden scope confirmation:

- fara component root
- fara component quote
- fara Logo offerability
- fara Pricing / Quote / Order / Execution
- fara ProductAggregate / TaskGraph / ExecutionPlan
- fara DB / seed / migration
- fara UI nou
- fara endpoint public nou

Next recommended prompt:

- `RETURN_CANT_TRUTH_FIELDS_READONLY_MAPPER_IMPLEMENTATION_V1`
# 2026-07-08 - return cant truth fields readonly mapper slice v1

HEAD before:

- `64a2a44`

HEAD after:

- pending at write time

Fisiere citite:

- `RETURN_CANT_MISSING_TRUTH_FIELDS_CONTRACT.md`
- `RETURN_CANT_COMPONENT_PREVIEW_READINESS_REMEDIATION.md`
- `FORM_SYSTEM_COMPONENT_FIELD_OWNERSHIP_MAP.md`
- QA snapshot pentru missing truth fields
- worklog pentru missing truth fields
- `backend/services/form_system_contract_backbone_service.py`
- `backend/services/intake_v6_modular_form_contract_service.py`
- `backend/services/product_definition_builder_service.py`
- `frontend/src/lib/intakeV6/productTruth/productTruthDraftBuilder.ts`
- `frontend/src/lib/intakeV6/productTruth/productTruthTypes.ts`
- `frontend/src/lib/intakeV6/productTruth/productTruthFixtures.ts`
- ancore Review / Confirm / layer confirmation / geometry

Ipoteza locala testata:

```text
Exista poate un loc sigur langa Product Truth draft pentru un helper read-only nelegat in UI.
```

Check-ul care a disconfirmat ipoteza:

```text
ProductTruthGeometryInput nu retine quote_geometry.letter_perimeter_m,
iar read model-ul curent nu poate exprima explicit face.confirmed_perimeter.
```

Concluzie:

- varianta mica de cod ar forta remapare implicita sau ar masca debt-ul de naming/path ownership;
- varianta sigura pentru acest task este docs-only mapper contract.

Fisiere atinse:

- `docs/architecture/product-system/RETURN_CANT_TRUTH_FIELDS_READONLY_MAPPER_CONTRACT.md`
- `docs/qa/return-cant-truth-fields-readonly-mapper-2026-07-08/RETURN_CANT_TRUTH_FIELDS_READONLY_MAPPER_SLICE_V1.md`
- `docs/worklog/realignment/2026-07-08_return_cant_truth_fields_readonly_mapper_slice_v1.md`

Decizie:

- `RETURN_CANT_MAPPER_BLOCKED`

Interpretare:

- contractul mapperului este gata;
- implementarea trebuie amanata pana cand suprafata de input poate raporta onest fallback context-ul de perimetru si dependency path-ul explicit.

Forbidden scope confirmation:

- fara component root
- fara component quote
- fara Logo offerability
- fara Pricing / Quote / Order / Execution
- fara ProductAggregate / TaskGraph / ExecutionPlan
- fara DB / seed / migration
- fara UI
- fara endpoint public nou

Next recommended prompt:

- `RETURN_CANT_TRUTH_FIELDS_READONLY_MAPPER_IMPLEMENTATION_V1`
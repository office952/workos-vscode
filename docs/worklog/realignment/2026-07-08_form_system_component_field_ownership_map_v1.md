# 2026-07-08 - form system component field ownership map v1

Summary:

- am documentat harta explicita de ownership pentru fields relevante pe componente;
- am separat clar component truth de product context, fallback default, UI display si ProductDefinition-derived consequence;
- am fixat MVP-ul `return_cant` ca urmator candidat, dar numai cu dependency explicita pentru perimetru si cu campurile lipsa tratate ca blockers.

Constatarea cea mai importanta:

- problema nu este lipsa totala de ownership;
- problema este ca ownership-ul real este impartit intre Backbone, Product Truth draft si downstream consequence trace, iar path-urile nu sunt inca unificate pentru aceleasi concepte.

Return/cant MVP dupa acest slice:

- partial_ready
- poate merge mai departe spre preview read-only
- nu este inca pregatit pentru calcul onest fara `material_profile`, `perimeter_source`, `layer_group_ids` si `confirmation_state`

Boundary pastrat:

- fara cod
- fara UI
- fara endpoint
- fara component root
- fara component quote
- fara Pricing / Quote / Order / Execution
- fara ProductAggregate / TaskGraph / ExecutionPlan
- fara DB/seed/migration

Recommended next prompt:

- `INTAKE_V6_RETURN_CANT_COMPONENT_PREVIEW_READONLY_SLICE_V1`
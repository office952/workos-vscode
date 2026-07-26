# WORKOS — Template Lifecycle Source Map

Maps each lifecycle stage to authority + primary evidence sources.

| Stage | Authority | Primary sources |
|-------|-----------|-----------------|
| PRODUCT_FAMILY | Product System | `product_templates.family_*`, availability family fields |
| PRODUCT_TEMPLATE | Product System | `product_templates`, `template_usage_mode_policy` |
| COMPONENT_TEMPLATES | Product System | module links, `svg_bindable_components` |
| INTERFACE_CONTRACTS | Product System | `svg_component_binding_contract.py` |
| INTAKE_AVAILABILITY | Intake V6 / PS | `ProductTemplateAvailabilityService`, NewIntakeDialog |
| INTAKE_STEP_1 | Intake V6 | SvgAnalyzerStep, svgComponentBindings, composition recommendation |
| INTAKE_STEP_2 | Intake V6 | ReviewStep, mountingSolution hydrate |
| FINISH_SETUP | Intake V6 | `IntakeV4FinishSetup.svg_component_bindings` |
| PRODUCT_DEFINITION | PD compiler | `ProductDefinitionBuilderService.build_preview` |
| PRODUCT_AGGREGATE | PA compiler | `ProductAggregateService.build` |
| CPP | CPP registry | owner gate only in V1 |
| OFFER | Commercial | `quote_offerable` / candidate policy |
| ORDER_SNAPSHOT | Snapshot | preview / owner gate |
| TASK_RULES_PROJECTION | Existing task_rules | preview; no parallel task model |
| TASK_MATERIALIZATION | Tasking | owner gate |
| EXECUTION | ExecutionPlan | NOT_STARTED in V1 |
| RUNTIME_PROOF | QA / E2E | worklogs, e2e smoke |

Trust order: runtime → active code → PS contracts → registries → PD/PA output → CPP/tasking → tests → docs → worklogs.

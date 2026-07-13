# Structured Blocker Catalog

| Code | Dimension | Severity | Owner | Meaning |
|------|-----------|----------|-------|---------|
| TEMPLATE_INACTIVE | technical/pricing/execution | blocking | registry | DB inactive template |
| MISSING_REQUIRED_MODULE | technical | blocking | composition | Linked module template missing |
| MISSING_PARENT_TEMPLATE | technical | blocking | composition | Parent template missing |
| INCOMPLETE_COMPOSITION | technical | blocking | composition | Parent without modules |
| INVALID_COMPONENT_CONTRACT | technical | blocking | registry | Invalid components_json |
| MISSING_PRICING_REGISTRY_ENTRY | pricing | blocking | pricing | No commercial material price |
| PRICING_NEEDS_REVIEW | pricing | warning | pricing | Owner review required |
| MISSING_OPERATION_RATE | pricing | blocking | pricing | No commercial operation rate |
| MISSING_CANONICAL_OPERATION | execution | blocking | execution | No operations on template |
| MISSING_TASK_RULE | execution | blocking | execution | Dossier task rules missing |
| TEMPLATE_DEPRECATED | commercial | blocking | policy | Archived/inactive commercial posture |
| OWNER_GO_REQUIRED | commercial | blocking | policy | Candidate blocked for root offer |
| INTERNAL_MODULE_ONLY | commercial | blocking | policy | Internal module not root-offerable |
| NOT_ROOT_OFFERABLE | commercial | blocking | policy | Outside root offerable policy |

Target routes use Product System tabs or `/inventory/pricing` where applicable.

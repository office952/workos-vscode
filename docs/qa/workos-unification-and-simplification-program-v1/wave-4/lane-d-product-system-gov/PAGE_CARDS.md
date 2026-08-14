# Lane D — Wave 4 page cards

Read-only. No FINAL. D owns these cards.

## `/product-system/products` — Catalog / V2 workspace

| Field | Value |
|-------|--------|
| PURPOSE | Browse/select product templates; default V2 workspace for Letters |
| PRIMARY USER | admin / manager / sales (owner-style catalog) |
| PRIMARY DECISION | Which template is the current product language? |
| SYSTEM OWNER | Product System catalog (design-time) |
| READS | template catalog / availability APIs |
| WRITES | none in this audit (editor exists; not saved) |
| UPSTREAM | none (definition lab) |
| DOWNSTREAM | Intake V6 (link without workspace context) |
| Disposition | KEEP + SIMPLIFY (TPL codes, compiler chrome) |
| Audience | mixed admin/owner; not operator shop-floor |

Runtime: admin L+D; manager/sales light. Operator denied → `/shop-floor`. Library often lands on last/default `TPL-VOLUMETRIC-LETTERS_v2`.

## `/product-system/products/TPL-VOLUMETRIC-LETTERS_v2`

| Field | Value |
|-------|--------|
| PURPOSE | Letters root structure (readonly V2) + honesty chips |
| PRIMARY USER | admin / product owner |
| PRIMARY DECISION | Understand FACE/RETURN/BACK/LED/FINISH/MOUNTING readiness |
| OWNS | template structure display |
| PROJECTS | ProductDefinition PREVIEW / Aggregate READ MODEL |
| Affects V6/Quote/Order/Execution | Only after Intake binding + compile + freeze — **not** by viewing this page |

## `/product-system/products/TPL-ACM-BOXED-MOUNTING-SUPPORT_v1`

| Field | Value |
|-------|--------|
| PURPOSE | Boxed ACM mounting support (second owner-valid root) |
| PRIMARY USER | admin |
| Disposition | KEEP (active root + linked-child capable) |

## Planned sections `/product-system/{components,operations,…}`

| Field | Value |
|-------|--------|
| PURPOSE | Placeholder “coming” sections |
| Disposition | PLANNED / AUDIT_ONLY |
| Runtime | Routed; `plannedSection: true`; not operational chrome |

## `/product-system/blueprint-dossier`

| Field | Value |
|-------|--------|
| PURPOSE | Blueprint dossier studio |
| Nav | DEV tooling · AUDIT |
| Disposition | AUDIT_ONLY |

## `/product-system/output-blocks-preview`

| Field | Value |
|-------|--------|
| PURPOSE | Lab output-blocks preview |
| Nav | none |
| Disposition | AUDIT_ONLY / UNREGISTERED_PAGE |

## `/modules` — Harta

| Field | Value |
|-------|--------|
| PURPOSE | Level-1 system map (`PRESENT_SYSTEMS`) |
| PRIMARY USER | admin |
| PRIMARY DECISION | What is official vs limitation |
| OWNER | `currentTruthControlCenter.ts` |
| RBAC | `view:modules` admin only |

## `/governance`

| Field | Value |
|-------|--------|
| PURPOSE | Ownership, boundaries, gates, guardrails |
| PRIMARY USER | admin |
| PRIMARY DECISION | Who may change which truth |
| OWNER | same PRESENT_* + `governanceData.ts` (static tabs) |
| RBAC | `view:governance` admin only |

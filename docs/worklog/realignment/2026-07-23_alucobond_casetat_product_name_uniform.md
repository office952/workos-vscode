# 2026-07-23 — Uniform product name: Alucobond casetat

| Field | Value |
|-------|-------|
| **Type** | UI / display vocabulary only |
| **Owner choice** | Option 3 — **Alucobond casetat** (fără „Panou”) |
| **Template code** | unchanged `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` |

## Decision

- **Product title:** `Alucobond casetat`
- **Not product titles:** Dibond casetat, Panou ACM casetat, Suport ACM casetat
- **Material aliases (remain):** ACM / ACP / Dibond / Alucobond on material strip
- **Family/category (remain):** Panouri ACP / ACM

## Touch points

- `ACM_BOXED_OWNER_LABEL_RO` in `acmBoxedTemplateIdentity.ts`
- `humanTemplateName` + canonical catalog `displayName` override
- Intake V6 product-facing labels aligned to the same title

## Out of scope

- DB / seed `family_name` rename, CostEngine, pricing formulas, template code rename

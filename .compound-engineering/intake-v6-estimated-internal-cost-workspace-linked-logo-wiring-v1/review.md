# INTAKE_V6_ESTIMATED_INTERNAL_COST_WORKSPACE_LINKED_LOGO_WIRING_V1 — Review

**Phase:** REVIEW COMPLETE  
**Reviewer:** implementation agent (self-review per plan)  
**Verdict:** APPROVED_WITH_DOCUMENTED_DEBT

---

## Checklist

| Question | Answer |
|---|---|
| EIC uses Cost BOM builder? | **YES** — `AggregateCostBomBuilderService.build_preview` |
| Workspace-aware chain when workspace_id? | **YES** |
| Template-only path compatible? | **YES** — builder falls back to template-only PA; existing preview tests green |
| Cost BOM canonical input? | **YES** — consumes `bom.costable_materials`, status, warnings |
| EIC recites bindings? | **NO** |
| EIC recites recommendation? | **NO** |
| EIC rebuilds ProductDefinition beyond existing PD preview? | **NO** — only existing `pd_builder.build_preview` for payload/modules |
| Segment identity preserved? | **YES** — namespaced `component_code`, separate stanga/dreapta |
| Logo materials separate? | **YES** — no cross-segment dedupe |
| Artwork area only for artwork-owned materials? | **YES** — `print_media`, `laminate_media` only |
| Partial does not become ready? | **YES** — `status=partial`, `ready=False` |
| Missing rate not zero? | **YES** — `INTERNAL_MATERIAL_COST_MISSING` blocker |
| Logo operations included? | **NO** — intentional V1 boundary |
| Commercial pricing absent? | **YES** |
| DB/downstream untouched? | **YES** |
| Implementation minimal? | **YES** — single service + targeted tests |
| Tests real? | **YES** — workspace fixtures, API POST, boundary unit tests |

## Documented debt

1. **Workspace-linked logo operation internal costs are not included in V1.** Letters operations unchanged via `RULES_BY_TEMPLATE`; `bom.costable_operations` not mapped for logo.
2. **Do not proceed to CommercialPriceProposal** until logo operation internal cost has owner GO.

## Risks remaining

- Real builder path (non-patched) depends on inventory/registry seeding for logo material rates — same as upstream Cost BOM.
- `_enrich_payload_artwork_finishes_from_pd` reads PD linked segment finish metadata for quantity only (not bindings/recommendation) — bounded DEC-EIC-03 input.

## Forbidden scope

Confirmed not touched in staged diff.

---

## REVIEW COMPLETE

**Verdict:** APPROVED_WITH_DOCUMENTED_DEBT  
Proceed to commit.

# CP0 — Shared contract freeze (Authoring Continuation)

| Field | Value |
|-------|--------|
| Date | 2026-07-20 |
| Status | **FROZEN** |
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD at freeze | `e2f3fc9` |

## Canonical ownership (unchanged)

```text
Product Family
  └─ Product Template (root | dual-role | child)
       ├─ Composition links: product_template_module_links
       │     + usage_mode + instance_schema_id (+ relation_type, active, modes)
       ├─ Component contract = child/dual-role PT (NO component_templates table)
       ├─ Blueprint Dossier = docs / review / decisions / approved bridges
       │     ≠ BOM SoT ≠ Pricing SoT ≠ Product Truth authority
       └─ publication_status: NULL|DRAFT|VALIDATED|E2E_CHECKED|PUBLISHED|DEPRECATED|ARCHIVED
```

## Dual status vocabulary (UI + readiness)

| Axis | Meaning | Source |
|------|---------|--------|
| BUILD / DB active | Template row `active` | availability / DB |
| TEMPLATE publication | Lifecycle publication_status | publication API |
| Offerability | Policy + children active | readiness / availability |
| E2E-ready | Static + optional dry-run | e2e-readiness API |

**`active=true` ≠ published ≠ offerable ≠ E2E-ready.**

BUILD may be PASS_WITH_WARNINGS while TEMPLATE PUBLICATION is BLOCKED (inactive Aluminiu child) — **correct honesty**.

## External Artwork Analysis (locked)

- Desktop owns SVG/DWG/DXF intelligence.
- WorkOS consume-only (`artwork_analysis_contract_v1` + adapter).
- Adapter never writes Product Truth.
- Geometry fields in component contract UI are **inputs only** — no geometry inference / SVG checks in publish gate.
- Transport TBD — out of scope.

## Template detail tab contract (product roots)

| Tab id | Authority | Mutability |
|--------|-----------|------------|
| `overview` | Identity + dual status + scope | read |
| `composition` | Module links authoring | edit links (no Aluminiu auto-activate) |
| `components` | Availability composition rows | read |
| `contracts` | ComponentContractUsedByPanel | edit usage_mode / instance_schema_id |
| `relationships` | Used-by / parent-child map | read |
| `materials` | Material roles from PD preview (template-only) | read |
| `dossier` | Deep-link to Blueprint Dossier Studio | navigate |
| `runtime-preview` | PD template-only preview | read |
| `readiness` | ProductE2EReadinessPanel | check (no-write dry-run) |
| `publication` | ProductTemplatePublicationPanel | lifecycle transitions fail-closed |
| `guards` | Availability / legacy guards | read |

Lifecycle tab may remain as a **compat alias** that hosts readiness + publication + artwork stub, or split into dedicated tabs — UI must not bury publication off-route.

## Dossier Studio command model

Sticky footer order (left→right authority):

1. **Save** — dossier documentation only
2. **Validate** — dossier JSON / readiness summary (not publish)
3. **E2E Check** — focus / run Product E2E Readiness (template authority)
4. **Publish** — navigate/focus Product Template publication (fail-closed; no auto-publish)

Dossier status ≠ template publication_status.

## Composition authoring rules

- Add/remove/order/role via existing `product_template_module_links` (+ soft deactivate via `active=false` when delete endpoint absent).
- Order: stable sort by `id` (or notes convention) until explicit order column exists — **no destructive migration** for ordering in this continuation.
- Required/optional/conditional expressed via `relation_type` + `active` + contract `usage_mode`.
- Inactive Aluminiu child remains a **real publication blocker** — never auto-activate.

## Runtime Preview rules

- Read-only ProductDefinition (template-only or optional workspace_id).
- Progressive disclosure: modules → components → materials → operations → composition graph → validation/provenance.
- External analysis appears only as provenance / review refs — never as Product Truth.

## Figma classification policy

| Frame | ID | Classification |
|-------|-----|----------------|
| Template Authoring Shell | `91:3` | NEEDS_POLISH (implement against) |
| Component Contract + Used-by | `91:12` | NEEDS_POLISH |
| Blueprint Dossier Studio | `91:21` / footer `91:32` | NEEDS_POLISH |
| Publication states | `91:36` | NEEDS_POLISH |
| Readiness PASS/BLOCKED | `91:60` | NEEDS_POLISH |
| Pack shells `91:76`–`91:100` | map | DESIGN_ONLY / NEEDS_POLISH |
| Intake Confirmare etc. | `66:2`… | FINAL (operator runtime — do not reopen) |

No invented IDs. No claim of Figma FINAL for PS authoring without owner promotion.

## Forbidden confirmation (must remain true)

- No ComponentTemplate table
- No PI/CI
- No Build 2
- No Aluminiu activation
- No Logo/Cassetted activation
- No pricing / CostEngine reopen
- No Execution materialization
- No desktop transport
- No SVG/DWG/DXF analysis extension
- No fake Publication ready for VolumetricLetters while Aluminiu inactive

# SOLD_SCOPE_SNAPSHOT_ACTIVE_SCOPE_CLOSURE_V1 — Phase 2 Synthesis

**HEAD:** `c0d5358` · **Status:** READY FOR SINGLE WRITER

## Intake V6 intent (freeze path only)

| Field | Class | Source |
|-------|-------|--------|
| `payload.offer_scope.mode` | OPERATOR_INTENT | PUT offer-scope |
| `payload.offer_scope.sold_modules` | OPERATOR_INTENT | PUT offer-scope |
| `payload.offer_scope.contract_version` | OPERATOR_INTENT | stamp |
| `offer_scope_confirmed.*` | OPERATOR_INTENT (readiness) | not compile input |
| `ActiveScopeResult` | DERIVED | `compile_active_scope` |

No form redesign. Freeze reads persisted payload / quote_input merge via `extract_offer_scope`.

## Frozen contract

Embed `QuoteSnapshotActiveScope` on Quote/Order/FrozenComponentScope:

- `active_scope_snapshot_version` = `active_scope_snapshot/v1`
- `compatibility_mode` = `enriched` | `legacy_scope_fallback`
- `source_workspace_id` (provenance only)
- `source_template_code`, `source_offer_scope_version`
- `compiled_at` (freeze-only; excluded from semantic compare)
- `compiled: ActiveScopeResult`

## Source map

| Frozen field | Primary |
|--------------|---------|
| sold_module_codes | Intake offer_scope |
| active/inactive/commercial/execution/calc/exclusions/deps | `compile_active_scope` |

## Semantic equality

Local helper: sort set-like lists; null≈[]; drop compiled_at; keep resolver/version/source; compare deps + exclusions. Fail closed with exact field diffs.

## Compat / Exec

Enriched → use `composition_excluded_operations` + prefer execution/commercial runtime sets.  
Legacy thin → `legacy_scope_fallback` + existing RETURN-CANT hardcode.  
No workspace reread after freeze.

## Test matrix

RETURN-CANT primary; FACE/BACK/LIGHTING; full; preview=freeze semantic; Order copy; Exec enriched; legacy fallback; no minute price.

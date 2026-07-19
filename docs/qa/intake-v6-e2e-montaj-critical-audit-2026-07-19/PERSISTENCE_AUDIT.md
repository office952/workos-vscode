# Persistence Audit — Montaj Fields

## Container

- Table: `intake_v6_workspaces`
- Column: `payload_json`
- Path: `payload.finish_setup.*`
- API: `PUT /api/v1/intake-v6/workspaces/{id}/finish-setup`
- FE: `intakeV4Api.ts` finish-setup PUT
- BE save: `intake_v6_workspace_service.py` (merge SVG patches, normalize bindings, coalesce segmented)

No dedicated Montaj SQL columns.

## Field persistence matrix (ACM WS readback)

| Field | Set in WS? | Visible after reload? | API same? | Client-only? | Notes |
|-------|------------|----------------------|-----------|--------------|-------|
| mounting_scope | `none` | yes (commercial collapsed) | yes | no | Explicit none |
| mounting_solution ACM | yes | yes | yes | no | Persists with full configuration |
| mounting_template_* | enabled/forex/0.7004 | implied | yes | no | Persists **despite** scope none |
| svg_support_selection | confirmed ALUCOBOND | drives dims | yes | no | Synced from bindings |
| segmented_background | PROPOSED | UI text claims confirmed | yes PROPOSED | no | **Visibility ≠ payload status** |
| electrical nested | present in UI | yes | under segmented | no | |
| mains_cable_length_m | null | hidden | null | no | |
| power_supply_service_corner | null | advanced/elsewhere | null | no | Aggregate still requires |
| mounting_fixing_system | null | — | null | no | |
| legacy mounting_system | null | — | null | no | stripped when solution exists |

## Save/reload exercise

Playwright reload on Montaj tab: Fundal/ACM/segmented UI still present; API keys unchanged (`montaj_capture_summary.json` / `07_montaj_acm_after_reload.png`).

## Stale fallback risks

1. Segmented read may also look under `mounting_solution.configuration.segmented_background` (compatibility).
2. `svg_support_selection` vs bindings dual write.
3. Service corner precedence across three sources at save (`svg_component_binding_persistence`).
4. Scope hydrate can infer `preparation_only` from template signals **only when scope empty** — here scope is explicit `none`, so template+scope coexistence is a real persisted inconsistency, not hydrate.

## Postman

No Postman MCP/collection used. Live HTTP against acceptance BE only.

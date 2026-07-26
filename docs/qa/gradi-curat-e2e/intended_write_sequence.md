# GRADI-CURAT intended runtime write sequence (before first write)

Diagnostic: WORKOS-GRADI-CURAT-SVG-SAME-SCENARIO-E2E-DIAGNOSTIC-V1
Runtime: http://127.0.0.1:8001 + http://127.0.0.1:3000
Auth: Authorization: Bearer __DEV_BYPASS_TOKEN__
Template root (provisional): TPL-VOLUMETRIC-LETTERS_v2 with linked logo composition layers

## Allowed write sequence (stop at first genuine blocker)

1. POST /api/v1/intake-v6/workspaces
   - title: GRADI-CURAT-E2E-DIAG-{timestamp}
   - template_code / selected_template_code: TPL-VOLUMETRIC-LETTERS_v2
   - analyzer_mode: analyzer_first
   - client_name: Gradi Curat E2E Diagnostic

2. PUT /api/v1/intake-v6/workspaces/{id}/analysis-bundle
   - real gradi-curat.svg text + nest2 analyzer JSON + confirmed layer roles
   - roles: 4x face letter groups + 2x printed_artwork logos

3. Inspect GET workspace + pricing-input-preview + product-definition / readiness surfaces
   - if composition confirmation required: PUT product-composition-confirmation only if owner gates already allow

4. PUT finish-setup only with values already supported by contract (no invented commercial rules)
   - illuminated / materials / finishes require operator or owner input — stop if missing required fields without inventing

5. Quote Snapshot V2 create/freeze only if readiness PASS without bypass

6. Accept/convert → Order Snapshot V2 only if quote freeze succeeded

7. Execution Plan V2 preview/persist/materialize only if order freeze + owner gates permit

8. Sessions / stock deduction / post-job only if materialization succeeded

## Forbidden

- legacy /price
- direct SQL
- manual snapshot/template injection
- SVG modification
- ACM mounting unless operator-confirmed (not for this file)

## Product interpretation note

File is letters+logo composition (not letters-only). Root template TPL-VOLUMETRIC-LETTERS_v2 is the documented letters-root path with linked logo candidates. Illumination / finish / ACM remain operator/owner inputs — not inferred from SVG.

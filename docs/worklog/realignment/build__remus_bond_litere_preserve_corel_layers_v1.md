# Build — Remus bond+litere preserve Corel layers v1

| Field | Value |
|-------|-------|
| **Date** | 2026-07-24 |
| **Problem** | Operator UI showed 1 card (verde litere); black Alucobond stroke as „Stroke decorativ” — no Contur suport |
| **Root cause** | FE analyzer `shouldPreserveExistingLayerStructure` only kept `Layer_x0020_N`; named Corel `Alucobond`+`Litere` fell into color-pseudo split and dropped stroke panel |

## Fix

- `isSupportPanelLayerName` in `layerNameSemantics.ts`
- Preserve ≥2 named production Corel layers in `pseudoLayerExpansionGuard.ts`
- Tests: `remusBondLitereLayers.test.ts`, guard Remus case

## Honest UI evidence

```powershell
cd frontend
$env:PW_SKIP_WEB_SERVER='1'
npx pnpm@8.10.0 exec playwright test e2e/intake-v6-remus-letters-acm-composition-calc-ui.spec.ts
```

`verdict.json` path=`operator_ui_no_layer_inject` → **PASS** (2 role cards + VL + acm_* + letters_acm_conn_*).

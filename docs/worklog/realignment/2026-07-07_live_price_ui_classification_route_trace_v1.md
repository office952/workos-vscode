# 2026-07-07 Live Price UI Classification Route Trace V1

## Head Before

- HEAD before: `7881126`

## Safety

- `git status -sb`: tracked worktree clean, only unrelated untracked files present
- `git diff --cached --name-only`: none
- `git status --short --untracked-files=no`: none
- `git diff --check`: clean before and after edit

## Route Summary

Common live price route confirmed:

```text
/inventory/pricing
-> GET /api/v1/pricing/registry
-> PricingRegistryService
-> inventory_materials / workcenter_rates
-> material_code / pricing_code / technical_source

Intake V6
-> material-breakdown
-> logical-list-read-model
-> priced-quote-dry-run
-> IntakeV6LiveCalculationSummary
-> UI row classification / grouping / visibility
```

This slice changed only the frontend classification/grouping layer.

## Classification Root Cause

Exact controlling function: `classifyLogicalRow` in `frontend/src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.tsx`.

Root cause:

1. Positive priced rows with real route identity could still be bucketed as `missing`, `excluded`, or `diagnostic` if they carried `PARTIAL`, `SPLIT_IN_RUNTIME`, or fallback warnings.
2. Group merge logic allowed a weaker grouped row to downgrade the final shared row after a valid priced row had already been included.
3. Placeholder or unresolved sibling rows could still influence a shared grouped bucket such as `material.plexiglas_shared`.

Observed effect:

- `Forex 10 mm` moved into diagnostics on live workspaces despite positive quantity and subtotal.
- `Material print Orafol`, `Material laminare Orafol`, `Serviciu print`, `Serviciu laminare X-PRO`, `Serviciu aplicare` could be pushed out of the main list despite being real priced rows.
- Shared Plexiglas groups were at risk of downgrade by placeholder logo-side siblings.

## Files Changed

- `frontend/src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.test.tsx`

## Fix

### Classifier changes

Added a narrow rule:

- if a logical row has positive quantity
- and positive subtotal
- and a real logical route identity

then it remains in the visible main list even when status/gap metadata indicates warning or split runtime.

This keeps owner-visible warning rows visible instead of diagnostic-only.

### Grouping changes

- placeholder or non-priced grouped siblings no longer downgrade an already valid visible grouped row
- shared grouped rows preserve the valid priced contribution as the controlling visible bucket
- warning/status metadata still remains visible via the chip/details path

### Placeholder handling

- null-quantity / null-subtotal siblings are prevented from controlling a shared grouped result
- existing `cerc100cm` generic shared Plexiglas behavior remains preserved

## Focused Tests

Command run:

```powershell
Push-Location C:\Users\offic\workos_app_vs\frontend
npm.cmd test -- src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.test.tsx
Pop-Location
```

Result:

- PASS
- 19 tests passed

Added / verified coverage:

1. positive `PARTIAL` row remains visible in main list
2. positive `SPLIT_IN_RUNTIME` material/service rows remain visible in main list
3. placeholder logo Plexiglas row does not downgrade a valid shared Plexiglas row
4. generic labels remain preserved
5. `cerc100` style `Plexiglas 3 mm = 1 m2 = 16 EUR` remains preserved in focused regression fixture

## Runtime Verification Matrix

### `IR-MRAUMOXT` / `cerc100cm.svg`

- Plexiglas visible: yes, `1 m2`, `16,00 EUR`
- Forex visible: yes, `1.0004 m2`, `19,21 EUR`
- Cant visible: yes
- LED visible: yes
- no `7 m2 / 112 EUR` regression observed
- diagnostics remain only for zero-quantity accessory rows

### `IR-MR2MP11C` / `gradi-curat.svg`

- Plexiglas visible: yes, `2.0643 m2`, `33,03 EUR`
- Forex visible: yes, `1.2638 m2`, `20,22 EUR`, warning chip visible
- Cant visible: yes
- print material visible: yes, `0.8005 m2`, `1,44 EUR`, warning chip visible
- lamination material visible: yes, `0.8005 m2`, `9,61 EUR`, warning chip visible
- print service visible: yes, `0.9606 m2`, `8,17 EUR`, warning chip visible
- lamination service visible: yes, `0.9606 m2`, `1,92 EUR`, warning chip visible
- application service visible: yes, `2.4771 m2`, `7,43 EUR`, warning chip visible
- diagnostics: none for these priced rows

### `IR-MR8TNT0O` / `logo.svg`

- Plexiglas visible: yes, `1.5547 m2`, `24,88 EUR`
- Forex visible: yes, `2.2506 m2`, `43,21 EUR`
- print material visible: yes
- lamination material visible: yes
- print service visible: yes
- lamination service visible: yes
- application service visible: yes
- remaining route mismatch still present: logical Plexiglas quantity `1.5547 m2` vs Forex `2.2506 m2`, consistent with prior audit that source-level quantity alignment is not fixed in this UI slice

### `IR-MR87EU55` / `litere-vol-1-layer.svg`

- Plexiglas visible: yes, `1.2 m2`, `19,20 EUR`
- Forex visible: yes, `1.2 m2`, `19,20 EUR`, warning chip visible
- Cant visible: yes
- LED visible: yes
- diagnostics: none for these priced rows

### `IR-MR8FWG1N` / `litere-vol-2-layere.svg`

- Plexiglas visible: yes, `1.1395 m2`, `18,23 EUR`
- Forex visible: yes, `1.1395 m2`, `18,23 EUR`, warning chip visible
- Cant visible: yes
- LED visible: yes
- diagnostics: none for these priced rows

## Validation

Commands run:

```powershell
Push-Location C:\Users\offic\workos_app_vs
git diff --check
Pop-Location
```

```powershell
Push-Location C:\Users\offic\workos_app_vs\frontend
npm.cmd test -- src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.test.tsx
Pop-Location
```

Results:

- `git diff --check`: PASS
- focused frontend test: PASS
- backend untouched in this slice

## Remaining Risks

1. `logo.svg` still shows source-route quantity mismatch between logical/UI and underlying route expectations; this was intentionally left out of scope for this UI-only fix.
2. Technical details still expose verbose source/gap wording; visibility is corrected, but route-trace field cleanup remains future work.
3. Runtime extraction showed duplicated DOM copies in spine/detail layouts; behavior is correct, but future tests should target the details container explicitly to reduce noise.

## Scope Confirmation

- no Pricing Registry rewrite
- no price changes
- no formula rewrite
- no Quote/Order
- no Execution
- no ProductAggregate/TaskGraph/ExecutionPlan
- no DB/seed/migration
- no Logo root activation
- no ACP root activation
- no Image Analyzer runtime edits

## Next

After this:

- `WORKOS_E2E_TERMINOLOGY_AND_LINKAGE_ALIGNMENT_AUDIT_V1`
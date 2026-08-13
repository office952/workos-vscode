# TEST_RESULTS

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/components/workos/intake-v6/IntakeV6PricingInputPanel.test.tsx `
  src/lib/intakeV6/intakeV6LogicalListD2Schedule.test.ts `
  src/lib/intakeV6/intakeV6AnalysisIdentity.test.ts `
  src/lib/intakeV6/intakeV6WorkspaceReducer.test.ts
```

```text
Test Files  4 passed (4)
Tests       34 passed (34)
```

Coverage added/extended:

1. null `eurToRonRate` commercialSliders does not throw
2. D2 initial gen 0/0 fetch; null settle not_ready; not markup_only_skip
3. analysis identity ignores `updated_at`
4. server_rehydrate preserves Configurare step

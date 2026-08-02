# Test results — U7

## Frontend targeted

```text
command: npm test -- --run src/lib/shellNavigation.test.ts src/lib/rbac.test.ts src/lib/executionFlowUi.test.ts src/components/execution-result src/lib/executionClosureUi.test.ts src/App.test.tsx src/contexts/AuthContext.test.tsx
passed: 63
failed: 0
skipped: 0
duration: ~9.3s
warnings: React Router future flags in App.test (preexisting)
```

## Typecheck

```text
command: npx tsc --noEmit -p tsconfig.json
passed: yes (exit 0)
```

## Backend

```text
Not run for functional change (UI-only). Protected baseline read-only verified on dev.db.
```

## Not run

```text
full frontend suite
full backend suite
Pricing.badges
```

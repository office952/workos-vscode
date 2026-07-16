# Intake V6 autosync remount + Vector Logo residual readiness

## Problem

Operator Review showed permanent `Sincronizare automata in asteptare` after remount/HMR, and a false “unclassified artwork / Confirm Logo 1/2” warning for Vector Logos already classified in Step 1 with execution decided.

## Root causes

1. **Autosync:** pending-save compared merged local letter/artwork to payload-only rows; post-save local mirrors were sometimes skipped via a partial finish signature.
2. **Readiness:** residual perimeter required all artwork rows `confirmed=true`, dropping every logo perimeter when any finish flag lagged.

## Fix

- Mirror finish state after every successful persist; pending uses remount baselines matching hydration merge.
- Count Vector Logo perimeter per eligible row (execution decided), generically for N logos; incomplete logo excludes only itself.
- Demote perimeter messaging when logos are classified; remove hardcoded Logo 1/2 copy.

## Verification

Focused BE residual tests + FE readiness/hydration tests; same-workspace dry-run pricing non-regression at 2513.5626; browser remount leaves autosave green.

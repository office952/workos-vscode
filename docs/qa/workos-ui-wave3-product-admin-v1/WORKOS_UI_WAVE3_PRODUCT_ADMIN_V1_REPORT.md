# WorkOS UI Wave 3 — Product/Admin V1

| Field | Value |
|---|---|
| Date | 2026-08-02 |
| Track | U3 |
| Base | `8a89693a` |
| Branch | `feat/ui-wave3-product-admin-v1` |
| Scope | Product System, Pricing, Utilaje, Setări, Guvernanță |
| Wave 2 closure | PASS WITH WARNINGS |

## Outcome

Romanian-first page identity and a presentation-only continuity strip now connect **Produs → Șabloane → Prețuri → Utilaje → Setări**. The strip does not change routing, authority, calculations, or persistence.

Pricing visibly separates **Materiale**, **Reguli ofertă**, **Cost intern estimativ**, **Capacitate**, and **Legacy**. Template pricing states that templates reference catalog rates and do not own them. Utilaje identifies capacity as feasibility rather than client pricing. Settings and Governance have distinct purposes.

## Boundaries kept

- No AppShell, `shellNavigation.ts`, AuthContext, App router ownership, or wholesale theme edit.
- Dev Mode and `VITE_ENABLE_DEV_AUTH` untouched.
- No graphical file processing, Employee Mobile, CostEngine formula change, inventory write, or new Product Truth authority.

## Verification

- `npx --yes pnpm@8.10.0 exec vitest run src/lib/adminProductTruthUi.test.ts` — pass (1 test).
- `npx --yes pnpm@8.10.0 run build` — pass.
- `git diff --check` — pass.
- Existing `Pricing.badges.test.tsx` was also run with adjacent tests but remains red due its pre-existing `Pricing` maximum-update-depth loop, before registry rows render. This track does not change the route's search-param effect.

## Runtime screenshot blocker

Wave 3 Vite started on `127.0.0.1:3036` against the available backend at `127.0.0.1:8000`. The browser stopped at the application integrity guard: the backend advertised an incompatible/old system version and the UI blocked API writes/route loading. No screenshot is claimed for this mismatch.

## Direction score

**86/100.** The primary Product/Admin navigation story is clearer and the ownership labels are explicit. Deeper legacy/dark diagnostic panels remain and should be reduced only in a separately scoped visual debt pass.

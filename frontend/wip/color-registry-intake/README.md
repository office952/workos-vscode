# Color Registry — Intake integration (WIP)

Patch helpers that map `ColorRegistryItem` selections into `IntakeProductSpec` fields.

**Not part of the standalone color registry build.** Re-enable when Work Intake V2 color integration is scheduled.

Files:
- `colorRegistrySpec.ts` — `patchReturnRalSelection`, `patchFaceVinylSelection`, `isReturnFinishComplete`, etc.

Depends on `@/lib/intakeProductSpec` (off-limits for standalone registry commit).

Tests for patch helpers belong in a future Work Intake integration build (not collected by default Vitest when kept here).

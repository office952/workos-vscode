# Intake V6 Configurare — hide status / confirmation badges (V1)

**Date:** 2026-07-24  
**Status:** COMPLETE  
**Owner ask:** „nu mai vreau sa vad nici un badge” / „nu mai vreau sa existe confirmat de operator” pe Configurare → Panou Alucobond.

## Change

Shared flag:

- `frontend/src/lib/intakeV6/intakeV6OperatorConfigStatusChrome.ts`
- `INTAKE_V6_OPERATOR_CONFIG_HIDE_STATUS_BADGES = true`

When hidden (default), operator Config surfaces stop rendering:

- Section header status pills (Rezumat / Geometrie / Construcție / Segmente)
- Field-level `AuthorityHint` lines (`Confirmat de operator`, catalog/proposed, etc.)
- Top-right workbench teal status chip
- Blueprint readiness badge (`Nivel L1-* · Confirmat`) and authority parentheticals
- Shell-finish `· confirmat` / `· neconfirmat` suffixes
- DXF production status pill
- Product-component list status chips
- Fundal summary „Stare: …“ lines
- Finisaje letter/artwork card status `AtomsBadge`s

**Kept:** sticky `Confirmă panoul Alucobond` (and other confirm CTAs), persistence / Product Truth logic unchanged. Read-model labels remain in `uiReadModel` for tests/diagnostics — not painted on operator Config.

## Verify

- Live Remus Configurare → Panou/carcasă: DOM text grep of ACM form → zero `Confirmat de operator` / `Neaplicabil` / readiness badge; confirm button present.
- Targeted Vitest: ACM workbench + artwork finish badge expectations updated.

## Out of scope / remains

- Confirmare step (page 3) operational summary may still show confirmation language.
- Pricing / rail guidance that names the confirm **action** (not a status chip).
- Tab pending counts (Finisaje pending) intentionally kept from prior badge-noise pass.

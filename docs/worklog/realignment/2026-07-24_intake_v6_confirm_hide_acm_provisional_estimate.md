# Intake V6 Confirm — hide ACM provisional estimate

**Date:** 2026-07-24  
**Owner ask:** „asta trebuie sa dispara de la pas 3” — Estimare provizorie — panou Alucobond pe Confirmare.

## Change

- Removed `AcmPanelProvisionalPricingBlock` from Confirm (`IntakeV6FinalConfigurationSummary` CTA card).
- Confirm live-calc fallback passes `hideAcmPanelProvisional` so the bar layout does not reintroduce it.
- Configurare (pas 2 / Review) still shows the provisional block via live-calc.

## Why

On Confirm, **Ofertă client** is the commercial story. The yellow provisional ACM card (geometry, “Dovadă indisponibilă”, “Ofertă fermă indisponibilă”) is noise and confuses the operator.

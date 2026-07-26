/**
 * Letters↔ACM composition — șablon commercial process (owner SoT).
 * Display / contract teaching only. Not CostEngine authority until Intake wiring GO.
 *
 * OWNER_CONFIRMED 2026-07-23:
 * - One bundled process: material + cutter/plotter + transfer + apply
 * - Rate: 20 EUR/mp
 * - Area basis: outbox of volumetric letters as one integral layer (not sum of per-letter boxes)
 */

/** Bundled process rate — material + cutter + transfer + apply. Never hourly. */
export const LETTERS_ACM_SABLON_PROCESS_RATE_EUR_PER_MP = 20 as const;

export const LETTERS_ACM_SABLON_PROCESS_UNIT = "mp" as const;

/**
 * Qty basis for the 20 EUR/mp line.
 * Outbox = bounding box of the letters layout treated as one integral layer,
 * not piece-by-piece letter outboxes summed.
 */
export const LETTERS_ACM_SABLON_AREA_BASIS_ID = "letters_layer_outbox_integral" as const;

export const LETTERS_ACM_SABLON_AREA_BASIS_RO =
  "Outbox (bounding box) al literelor volumetrice ca layer integral — nu sumă piesă cu piesă.";

export const LETTERS_ACM_SABLON_PROCESS_LABEL_RO =
  "Proces șablon pe Alucobond (material + cutter/plotter + transfer + aplicare)";

export const LETTERS_ACM_SABLON_PROCESS_MEANING_RO =
  "Un singur calcul pe mp: autocolant transparent, decupare cutter/plotter, folie transfer, aplicare transfer și aplicare șablon pe bond. Nu orar. Nu linii separate material/cutter/transfer/aplicare.";

export const LETTERS_ACM_SABLON_BUNDLED_STEPS_RO = [
  "Material șablon (autocolant transparent)",
  "Decupare cutter / plotter",
  "Folie transfer",
  "Aplicare folie transfer",
  "Aplicare șablon pe bond",
] as const;

export function formatLettersAcmSablonProcessRateRo(): string {
  return `${LETTERS_ACM_SABLON_PROCESS_RATE_EUR_PER_MP} EUR/${LETTERS_ACM_SABLON_PROCESS_UNIT}`;
}

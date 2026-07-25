/**
 * Letters↔ACM connection commercial price sheet (teaching SoT).
 * Not CostEngine / Offer authority until Intake wiring GO.
 *
 * - Șablon 20 EUR/mp = OWNER_LOCKED
 * - Remaining lines = AI proposed, owner verified coherent 2026-07-23 (may revisit)
 * Never hourly / time-based.
 */

import {
  LETTERS_ACM_SABLON_AREA_BASIS_ID,
  LETTERS_ACM_SABLON_AREA_BASIS_RO,
  LETTERS_ACM_SABLON_PROCESS_LABEL_RO,
  LETTERS_ACM_SABLON_PROCESS_RATE_EUR_PER_MP,
  LETTERS_ACM_SABLON_PROCESS_UNIT,
} from "./lettersAcmCompositionSablonProcess";

export type LettersAcmConnectionPriceDecision =
  | "OWNER_LOCKED"
  | "OWNER_VERIFIED_COHERENT"
  | "AI_PROPOSED_PENDING_OWNER_VERIFY";

export type LettersAcmConnectionPriceUnit = "mp" | "buc";

export type LettersAcmConnectionPriceLineId =
  | "sablon_process"
  | "fasten_forex_on_bond"
  | "electric_psu_in_cassette"
  | "supply_cable_5m_220v"
  | "light_test"
  | "attach_body_to_forex"
  | "pack_composite";

export type LettersAcmConnectionPriceLine = {
  id: LettersAcmConnectionPriceLineId;
  order: number;
  labelRo: string;
  rateEur: number;
  unit: LettersAcmConnectionPriceUnit;
  /** Qty basis — same outbox as șablon when unit is mp */
  qtyBasisRo: string;
  minEur?: number;
  decision: LettersAcmConnectionPriceDecision;
  rationaleRo: string;
};

export const LETTERS_ACM_CONNECTION_PRICES_PAGE_TITLE_RO =
  "Prețuri conexiune Litere ↔ Alucobond";

export const LETTERS_ACM_CONNECTION_PRICES_HELPER_RO =
  "Linii comerciale pe conexiune (montaj pe casetă). Nu orar. Șablon = owner blocat; restul = AI, verificate owner ca coerente (2026-07-23).";

export const LETTERS_ACM_CONNECTION_PRICE_SHEET: readonly LettersAcmConnectionPriceLine[] = [
  {
    id: "sablon_process",
    order: 1,
    labelRo: LETTERS_ACM_SABLON_PROCESS_LABEL_RO,
    rateEur: LETTERS_ACM_SABLON_PROCESS_RATE_EUR_PER_MP,
    unit: LETTERS_ACM_SABLON_PROCESS_UNIT,
    qtyBasisRo: LETTERS_ACM_SABLON_AREA_BASIS_RO,
    decision: "OWNER_LOCKED",
    rationaleRo:
      "Owner 2026-07-23: bundle material + cutter/plotter + transfer + aplicare. Baza: outbox layer integral.",
  },
  {
    id: "fasten_forex_on_bond",
    order: 2,
    labelRo: "Prindere spate Forex pe bond (autoforante)",
    rateEur: 8,
    unit: "mp",
    qtyBasisRo: LETTERS_ACM_SABLON_AREA_BASIS_RO,
    decision: "OWNER_VERIFIED_COHERENT",
    rationaleRo:
      "AI propus; owner 2026-07-23: coerent momentan. Manoperă + prinderi pe outbox layer.",
  },
  {
    id: "electric_psu_in_cassette",
    order: 3,
    labelRo: "Electrică în carcasa bond + legare transformator",
    rateEur: 35,
    unit: "buc",
    qtyBasisRo: "1 × ansamblu composition (fără SKU PSU — Litere/registry)",
    decision: "OWNER_VERIFIED_COHERENT",
    rationaleRo:
      "AI propus; owner 2026-07-23: coerent momentan. Manoperă trasee + legare PSU în carcasă.",
  },
  {
    id: "supply_cable_5m_220v",
    order: 4,
    labelRo: "Cablu alimentare 5 m 220V (2×1.5) + atasare",
    rateEur: 6,
    unit: "buc",
    qtyBasisRo: "1 × ansamblu — default PH2-OD-09 (5 m 2×1.5)",
    decision: "OWNER_VERIFIED_COHERENT",
    rationaleRo:
      "AI propus; owner 2026-07-23: coerent momentan. Speță = PH2-OD-09.",
  },
  {
    id: "light_test",
    order: 5,
    labelRo: "Test lumină",
    rateEur: 8,
    unit: "buc",
    qtyBasisRo: "1 × ansamblu (QC înainte de prinderea corpului)",
    decision: "OWNER_VERIFIED_COHERENT",
    rationaleRo: "AI propus; owner 2026-07-23: coerent momentan.",
  },
  {
    id: "attach_body_to_forex",
    order: 6,
    labelRo: "Prindere corp (plexi + volum) pe Forex — autoforante fine vopsite",
    rateEur: 12,
    unit: "mp",
    qtyBasisRo: LETTERS_ACM_SABLON_AREA_BASIS_RO,
    decision: "OWNER_VERIFIED_COHERENT",
    rationaleRo:
      "AI propus; owner 2026-07-23: coerent momentan. Șuruburi fine + vopsire cant/volum.",
  },
  {
    id: "pack_composite",
    order: 7,
    labelRo: "Impachetare ansamblu Litere + Alucobond",
    rateEur: 10,
    unit: "mp",
    qtyBasisRo: LETTERS_ACM_SABLON_AREA_BASIS_RO,
    minEur: 15,
    decision: "OWNER_VERIFIED_COHERENT",
    rationaleRo:
      "AI propus; owner 2026-07-23: coerent momentan. Pack o dată; min. 15 EUR.",
  },
] as const;

export function formatLettersAcmConnectionPriceRo(line: LettersAcmConnectionPriceLine): string {
  const base = `${line.rateEur.toFixed(line.rateEur % 1 === 0 ? 0 : 2)} EUR/${line.unit}`;
  if (line.minEur != null) {
    return `${base} (min. ${line.minEur} EUR)`;
  }
  return base;
}

export function decisionBadgeRo(decision: LettersAcmConnectionPriceDecision): string {
  switch (decision) {
    case "OWNER_LOCKED":
      return "Owner blocat";
    case "OWNER_VERIFIED_COHERENT":
      return "Owner verificat (coerent)";
    case "AI_PROPOSED_PENDING_OWNER_VERIFY":
      return "AI — de verificat";
    default: {
      const _exhaustive: never = decision;
      return _exhaustive;
    }
  }
}

export function countAiProposedConnectionPrices(): number {
  return LETTERS_ACM_CONNECTION_PRICE_SHEET.filter(
    (l) => l.decision === "AI_PROPOSED_PENDING_OWNER_VERIFY",
  ).length;
}

export function countOwnerVerifiedConnectionPrices(): number {
  return LETTERS_ACM_CONNECTION_PRICE_SHEET.filter(
    (l) => l.decision === "OWNER_VERIFIED_COHERENT",
  ).length;
}

export function countOwnerLockedConnectionPrices(): number {
  return LETTERS_ACM_CONNECTION_PRICE_SHEET.filter((l) => l.decision === "OWNER_LOCKED").length;
}

export function assertSablonLineMatchesOwnerLock(): boolean {
  const sablon = LETTERS_ACM_CONNECTION_PRICE_SHEET.find((l) => l.id === "sablon_process");
  return (
    sablon?.rateEur === LETTERS_ACM_SABLON_PROCESS_RATE_EUR_PER_MP &&
    sablon.decision === "OWNER_LOCKED" &&
    LETTERS_ACM_SABLON_AREA_BASIS_ID === "letters_layer_outbox_integral"
  );
}

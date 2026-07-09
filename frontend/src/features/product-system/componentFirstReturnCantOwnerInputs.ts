import { FINISH_TYPE_VALUES, RETURN_CANT_WORKSHOP_FIELDS } from "./componentFirstLettersProductTruthWorkshop";

export type OwnerConfirmedValueStatus =
  | "owner_confirmed"
  | "partial_confirmed"
  | "owner_input_required"
  | "blocked_until_owner_decision"
  | "not_applicable_yet";

export type ReturnCantOwnerInputSource =
  | "owner_confirmed_in_chat"
  | "existing_project_memory"
  | "not_confirmed";

export type ReturnCantBlockingArea =
  | "pricing"
  | "product_definition"
  | "execution"
  | "workshop_only";

export type ReturnCantOwnerInput = {
  key: string;
  labelRo: string;
  value: string | number | boolean | string[] | null;
  unit?: "mm" | "ml" | "mp" | "buc" | "set" | "lei" | "eur" | "none";
  status: OwnerConfirmedValueStatus;
  source: ReturnCantOwnerInputSource;
  blockingArea: ReturnCantBlockingArea[];
  ownerQuestionRo?: string;
  notesRo: string;
  mustNotInvent: boolean;
};

export const RETURN_CANT_OWNER_INPUT_DISPLAY_UNKNOWN = "OWNER INPUT REQUIRED" as const;

export const RETURN_CANT_CONFIRMED_SO_FAR: string[] = [
  "Variante finisaj cant: Culoare Stock · Oracal · Vopsit RAL",
  "Oracal selector: listă completă (catalog efectiv încă necesar)",
  "Oracal pricing: preț pe cod/familie (tabel prețuri încă necesar)",
  "RAL mode: selector standard (sursă/listă RAL încă necesară)",
  "Adâncimi standard cant: 30 / 60 / 80 / 100 mm",
  "Material cant: aluminiu 0.6 mm",
  "Unitate material cant: ml",
  "Unitate manoperă cant: ml",
  "Culoare Stock: fără impact preț — doar informație atelier",
  "Geometrie cant: perimetru/contur real al literelor",
  "Vopsit RAL: material și manoperă tratate separat (model, nu prețuri)",
  "Calcul separat: necesită component-owned truth pe path componentă",
  "Fără activare: no Product Truth write · no Pricing · no Work Intake",
];

export const RETURN_CANT_PARTIAL_SO_FAR: string[] = [
  "Catalog Oracal: țintă coduri oficiale confirmată — import pending",
  "Tabel prețuri Oracal: owner are tabelul — valori neintroduse",
  "Minim Vopsit RAL: 100 lei confirmat — scope pending",
];

export const RETURN_CANT_STILL_MISSING_BEFORE_PRICING: string[] = [
  "Import catalog coduri Oracal efectiv",
  "Valori tabel prețuri Oracal pe cod/familie",
  "Scope minim Vopsit RAL (100 lei confirmat)",
];

export const RETURN_CANT_STILL_MISSING_BEFORE_PRODUCT_DEFINITION: string[] = [];

/** Owner questions kept visible until answered — no invented answers. */
export const RETURN_CANT_OWNER_QUESTIONS_PENDING: string[] = [
  "Import catalog Oracal: sursă/listă efectivă pentru toate codurile oficiale?",
  "Tabel prețuri Oracal: valori pe cod/familie?",
  "Scope minim Vopsit RAL 100 lei: lucrare / set / culoare / comandă? material / manoperă / total?",
  "Formă catalog Oracal: cod simplu vs cod + nume + familie?",
];

function confirmedInput(
  partial: Omit<ReturnCantOwnerInput, "status" | "source" | "mustNotInvent"> & {
    value: NonNullable<ReturnCantOwnerInput["value"]>;
  },
): ReturnCantOwnerInput {
  return {
    ...partial,
    status: "owner_confirmed",
    source: partial.source ?? "existing_project_memory",
    mustNotInvent: false,
  };
}

function partialInput(
  partial: Omit<ReturnCantOwnerInput, "status" | "source" | "mustNotInvent"> & {
    value: NonNullable<ReturnCantOwnerInput["value"]>;
  },
): ReturnCantOwnerInput {
  return {
    ...partial,
    status: "partial_confirmed",
    source: partial.source ?? "owner_confirmed_in_chat",
    mustNotInvent: true,
  };
}

function pendingInput(
  partial: Omit<ReturnCantOwnerInput, "status" | "source" | "value" | "mustNotInvent">,
): ReturnCantOwnerInput {
  return {
    ...partial,
    value: null,
    status: "owner_input_required",
    source: "not_confirmed",
    mustNotInvent: true,
  };
}

function blockedInput(
  partial: Omit<ReturnCantOwnerInput, "status" | "source" | "value" | "mustNotInvent">,
): ReturnCantOwnerInput {
  return {
    ...partial,
    value: null,
    status: "blocked_until_owner_decision",
    source: "not_confirmed",
    mustNotInvent: true,
  };
}

export const RETURN_CANT_OWNER_INPUTS: ReturnCantOwnerInput[] = [
  confirmedInput({
    key: "finish_type_variants",
    labelRo: "Variante finisaj cant",
    value: [...FINISH_TYPE_VALUES],
    source: "owner_confirmed_in_chat",
    blockingArea: ["pricing", "product_definition"],
    notesRo: "Cele 3 variante universale confirmate de owner.",
  }),
  confirmedInput({
    key: "stock_color_note_mode",
    labelRo: "Culoare Stock — mod operator",
    value: "Operator tastează culoarea pentru atelier",
    source: "owner_confirmed_in_chat",
    blockingArea: ["execution"],
    notesRo: "Informație clară atelier. Cost diferit NU este presupus fără confirmare owner.",
  }),
  confirmedInput({
    key: "stock_color_affects_price",
    labelRo: "Culoare Stock influențează prețul?",
    value: false,
    unit: "none",
    source: "owner_confirmed_in_chat",
    blockingArea: ["pricing"],
    notesRo:
      "Owner confirmat: NU — culoarea tastată este doar informație atelier, fără impact preț.",
  }),
  confirmedInput({
    key: "oracal_selector_mode",
    labelRo: "Mod selector Oracal",
    value: "listă completă Oracal",
    source: "owner_confirmed_in_chat",
    blockingArea: ["pricing", "execution"],
    notesRo:
      "Owner chose B — selector listă completă. Catalogul efectiv de coduri rămâne OWNER INPUT REQUIRED.",
  }),
  partialInput({
    key: "oracal_code_list",
    labelRo: "Catalog coduri Oracal (date efective)",
    value: "Țintă: toate codurile Oracal oficiale — import pending",
    source: "owner_confirmed_in_chat",
    blockingArea: ["pricing", "execution"],
    ownerQuestionRo: "Sursă/import listă completă Oracal oficială?",
    notesRo: "Țintă catalog confirmată — fără coduri Oracal inventate.",
  }),
  confirmedInput({
    key: "oracal_pricing_mode",
    labelRo: "Mod pricing Oracal",
    value: "preț pe cod/familie",
    source: "owner_confirmed_in_chat",
    blockingArea: ["pricing"],
    notesRo:
      "Owner chose B — preț diferit pe cod/familie. Tabelul de prețuri rămâne OWNER INPUT REQUIRED.",
  }),
  confirmedInput({
    key: "ral_input_mode",
    labelRo: "Mod introducere RAL",
    value: "selector standard RAL",
    source: "owner_confirmed_in_chat",
    blockingArea: ["pricing", "execution"],
    notesRo:
      "Owner chose B — selector standard RAL. Sursa/lista RAL efectivă rămâne OWNER INPUT REQUIRED.",
  }),
  confirmedInput({
    key: "ral_selector_source",
    labelRo: "Sursă/listă selector RAL standard",
    value: "RAL Classic (ca în Intake V6 / colorRegistry)",
    source: "owner_confirmed_in_chat",
    blockingArea: ["pricing", "execution"],
    notesRo: "Owner confirmat RAL Classic — cross-ref colorRegistry/ralColors.ts.",
  }),
  confirmedInput({
    key: "ral_material_labor_separation",
    labelRo: "Separare material / manoperă Vopsit RAL",
    value: "Material și manoperă separate (model confirmat, prețuri neconfirmate)",
    source: "owner_confirmed_in_chat",
    blockingArea: ["pricing", "workshop_only"],
    notesRo: "Model de business confirmat — nu include prețuri sau formule.",
  }),
  confirmedInput({
    key: "return_depths_standard",
    labelRo: "Adâncimi standard cant",
    value: ["30", "60", "80", "100"],
    unit: "mm",
    source: "owner_confirmed_in_chat",
    blockingArea: ["pricing", "product_definition"],
    notesRo: "Owner confirmat: 30 / 60 / 80 / 100 mm.",
  }),
  confirmedInput({
    key: "return_material",
    labelRo: "Material cant",
    value: "aluminiu 0.6 mm",
    source: "owner_confirmed_in_chat",
    blockingArea: ["pricing", "product_definition"],
    notesRo: "Owner confirmat: aluminiu 0.6 mm (material + grosime).",
  }),
  confirmedInput({
    key: "return_material_unit",
    labelRo: "Unitate calcul material cant",
    value: "ml",
    unit: "ml",
    source: "owner_confirmed_in_chat",
    blockingArea: ["pricing"],
    notesRo: "Material cant calculat pe ml (metru liniar).",
  }),
  confirmedInput({
    key: "return_labor_unit",
    labelRo: "Unitate manoperă cant",
    value: "ml",
    unit: "ml",
    source: "owner_confirmed_in_chat",
    blockingArea: ["pricing"],
    notesRo: "Manoperă cant calculată pe ml (metru liniar).",
  }),
  confirmedInput({
    key: "ral_material_price_rule",
    labelRo: "Regulă preț material Vopsit RAL",
    value:
      "30=2.00 EUR/ml · 60=2.50 · 80=3.00 · 100=4.00 EUR/ml (consumabile ofertare)",
    unit: "eur",
    source: "owner_confirmed_in_chat",
    blockingArea: ["pricing"],
    notesRo: "Prețuri owner confirmate — fără activare pricing engine.",
  }),
  confirmedInput({
    key: "ral_labor_price_rule",
    labelRo: "Regulă manoperă Vopsit RAL",
    value: "1.00 EUR/ml — același preț toate adâncimile",
    unit: "eur",
    source: "owner_confirmed_in_chat",
    blockingArea: ["pricing"],
    notesRo: "Preț manoperă owner confirmat — fără activare pricing engine.",
  }),
  partialInput({
    key: "minimum_price_rule",
    labelRo: "Minim preț Vopsit RAL",
    value: "100 lei — scope pending",
    unit: "lei",
    source: "owner_confirmed_in_chat",
    blockingArea: ["pricing"],
    ownerQuestionRo:
      "Pe ce bază se aplică minimul 100 lei: lucrare, set, culoare, comandă? Material, manoperă sau total?",
    notesRo: "Minim confirmat — fără conversie automată lei→EUR.",
  }),
  confirmedInput({
    key: "perimeter_geometry_source",
    labelRo: "Sursă perimetru / geometrie cant",
    value: "perimetru/contur real al literelor",
    source: "owner_confirmed_in_chat",
    blockingArea: ["product_definition"],
    notesRo:
      "Owner confirmat: calcul pe perimetru/contur real. Algoritm SVG/nesting ne modificat în acest task.",
  }),
  confirmedInput({
    key: "material_depth_compatibility",
    labelRo: "Compatibilitate material ↔ adâncime",
    value: "aluminiu 0.6 mm valid pentru 30 / 60 / 80 / 100 mm",
    source: "owner_confirmed_in_chat",
    blockingArea: ["product_definition"],
    notesRo: "Owner confirmat: toate adâncimile standard compatibile.",
  }),
  confirmedInput({
    key: "separate_calculation_component_truth",
    labelRo: "Calcul separat — component-owned truth",
    value: true,
    source: "existing_project_memory",
    blockingArea: ["product_definition", "workshop_only"],
    notesRo: "Adevărul cant stă pe componentă / TPL-COMP / Product Truth path — nu pe Product Template.",
  }),
  blockedInput({
    key: "pricing_activation",
    labelRo: "Activare pricing cant",
    blockingArea: ["pricing", "workshop_only"],
    notesRo: "Pricing blocked — fără activare în acest task.",
  }),
];

export type ReturnCantOwnerInputSummary = {
  globalStatus: "OWNER_INPUT_REQUIRED";
  confirmedCount: number;
  partialCount: number;
  pendingCount: number;
  blockedCount: number;
  missingBeforePricingCount: number;
  missingBeforeProductDefinitionCount: number;
};

export function formatReturnCantOwnerInputDisplayValue(input: ReturnCantOwnerInput): string {
  const hasDisplayValue =
    (input.status === "owner_confirmed" || input.status === "partial_confirmed") &&
    input.value !== null;

  if (!hasDisplayValue) {
    return RETURN_CANT_OWNER_INPUT_DISPLAY_UNKNOWN;
  }

  if (input.key === "stock_color_affects_price" && typeof input.value === "boolean") {
    return input.value ? "Da" : "Nu — doar informație atelier";
  }

  if (Array.isArray(input.value)) {
    return input.value.map((v) => `${v} mm`).join(" · ");
  }

  if (typeof input.value === "boolean") {
    return input.value ? "Da (model confirmat)" : "Nu";
  }

  return String(input.value);
}

export function buildReturnCantOwnerInputSummary(
  inputs: ReturnCantOwnerInput[] = RETURN_CANT_OWNER_INPUTS,
): ReturnCantOwnerInputSummary {
  const confirmedCount = inputs.filter((i) => i.status === "owner_confirmed").length;
  const partialCount = inputs.filter((i) => i.status === "partial_confirmed").length;
  const pendingCount = inputs.filter((i) => i.status === "owner_input_required").length;
  const blockedCount = inputs.filter((i) => i.status === "blocked_until_owner_decision").length;
  const missingBeforePricingCount = inputs.filter(
    (i) =>
      i.status !== "owner_confirmed" &&
      i.status !== "partial_confirmed" &&
      i.blockingArea.includes("pricing") &&
      i.key !== "pricing_activation",
  ).length;
  const missingBeforeProductDefinitionCount = inputs.filter(
    (i) =>
      i.status !== "owner_confirmed" &&
      i.status !== "partial_confirmed" &&
      i.blockingArea.includes("product_definition"),
  ).length;

  return {
    globalStatus: "OWNER_INPUT_REQUIRED",
    confirmedCount,
    partialCount,
    pendingCount,
    blockedCount,
    missingBeforePricingCount,
    missingBeforeProductDefinitionCount,
  };
}

export function getReturnCantOwnerInput(key: string): ReturnCantOwnerInput | null {
  return RETURN_CANT_OWNER_INPUTS.find((i) => i.key === key) ?? null;
}

/** Align workshop field keys with owner input keys where applicable. */
export function workshopFieldAlignedWithOwnerInputs(): boolean {
  const workshopKeys = new Set(RETURN_CANT_WORKSHOP_FIELDS.map((f) => f.fieldKey));
  const criticalKeys = [
    "finish_type",
    "stock_color_note",
    "oracal_code",
    "ral_code",
    "return_depth_mm",
    "return_material",
    "return_material_unit",
    "return_labor_unit",
    "ral_material_price_rule",
    "ral_labor_price_rule",
    "separate_calculation_allowed",
    "pricing_status",
  ];
  return criticalKeys.every((k) => workshopKeys.has(k));
}

export function ownerConfirmedValueStatusLabel(status: OwnerConfirmedValueStatus): string {
  switch (status) {
    case "owner_confirmed":
      return "CONFIRMED";
    case "partial_confirmed":
      return "PARTIAL";
    case "owner_input_required":
      return "OWNER INPUT";
    case "blocked_until_owner_decision":
      return "BLOCKED";
    case "not_applicable_yet":
      return "N/A";
    default:
      return status.toUpperCase();
  }
}

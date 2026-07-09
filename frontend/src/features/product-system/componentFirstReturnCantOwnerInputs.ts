import { FINISH_TYPE_VALUES, RETURN_CANT_WORKSHOP_FIELDS } from "./componentFirstLettersProductTruthWorkshop";

export type OwnerConfirmedValueStatus =
  | "owner_confirmed"
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
  "Culoare Stock: operator tastează culoarea pentru atelier (fără presupunere cost diferit)",
  "Vopsit RAL: material și manoperă tratate separat (model, nu prețuri)",
  "Calcul separat: necesită component-owned truth pe path componentă",
  "Fără activare: no Product Truth write · no Pricing · no Work Intake",
];

export const RETURN_CANT_STILL_MISSING_BEFORE_PRICING: string[] = [
  "Listă coduri Oracal",
  "Mod pricing Oracal (preț unic vs pe cod/familie)",
  "Mod RAL (text liber vs selector vs listă standard)",
  "Adâncimi standard cant (30/60/80/100 mm?)",
  "Material cant (aluminiu, PVC, plexi, altceva?)",
  "Unitate material cant",
  "Unitate manoperă cant",
  "Regulă preț material Vopsit RAL",
  "Regulă manoperă Vopsit RAL",
  "Minim preț (dacă există)",
];

export const RETURN_CANT_STILL_MISSING_BEFORE_PRODUCT_DEFINITION: string[] = [
  "Adâncimi standard cant confirmate",
  "Sursă geometrie / perimetru necesar calcul cant",
  "Compatibilitate material ↔ adâncime",
];

/** Owner questions kept visible until answered — no invented answers. */
export const RETURN_CANT_OWNER_QUESTIONS_PENDING: string[] = [
  "Adâncimi standard cant: 30 mm? 60 mm? 80 mm? 100 mm? altele?",
  "Material cant: aluminiu? PVC? plexiglas/acrylic? altceva? 30/60 mm același material sau diferit?",
  "Culoare Stock: culoarea tastată influențează prețul sau este doar informație atelier?",
  "Oracal: selector complet? coduri uzuale + alt cod? text liber? preț unic sau pe cod/familie?",
  "Vopsit RAL material: preț material 30/60/80 mm? unitate ml/mp/set/bucată?",
  "Vopsit RAL manoperă: pe ml? set? piesă/literă? mp? minim + ml?",
  "Unitate generală calcul cant: material și manoperă pe ml de cant? altă regulă?",
  "RAL: text liber sau selector? Există listă standard?",
  "Sursă perimetru pentru calcul cant: față confirmată? alt path?",
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
  pendingInput({
    key: "stock_color_affects_price",
    labelRo: "Culoare Stock influențează prețul?",
    unit: "none",
    blockingArea: ["pricing"],
    ownerQuestionRo:
      "Culoarea tastată influențează prețul sau este doar informație atelier?",
    notesRo: "Decizie owner — nu presupunem impact pricing.",
  }),
  pendingInput({
    key: "oracal_code_list",
    labelRo: "Listă coduri Oracal",
    blockingArea: ["pricing", "execution"],
    ownerQuestionRo:
      "Selector complet? Coduri uzuale + alt cod? Text liber? Care coduri intră în listă?",
    notesRo: "Fără listă Oracal inventată.",
  }),
  pendingInput({
    key: "oracal_pricing_mode",
    labelRo: "Mod pricing Oracal",
    blockingArea: ["pricing"],
    ownerQuestionRo: "Preț unic pentru toate codurile Oracal sau preț diferit pe cod/familie?",
    notesRo: "Fără mod pricing presupus.",
  }),
  pendingInput({
    key: "ral_input_mode",
    labelRo: "Mod introducere RAL",
    blockingArea: ["pricing", "execution"],
    ownerQuestionRo: "RAL ca text liber, selector sau listă standard?",
    notesRo: "Fără tabel RAL inventat.",
  }),
  confirmedInput({
    key: "ral_material_labor_separation",
    labelRo: "Separare material / manoperă Vopsit RAL",
    value: "Material și manoperă separate (model confirmat, prețuri neconfirmate)",
    source: "owner_confirmed_in_chat",
    blockingArea: ["pricing", "workshop_only"],
    notesRo: "Model de business confirmat — nu include prețuri sau formule.",
  }),
  pendingInput({
    key: "return_depths_standard",
    labelRo: "Adâncimi standard cant",
    unit: "mm",
    blockingArea: ["pricing", "product_definition"],
    ownerQuestionRo: "30 mm? 60 mm? 80 mm? 100 mm? altele?",
    notesRo: "Fără adâncimi default inventate.",
  }),
  pendingInput({
    key: "return_material",
    labelRo: "Material cant",
    blockingArea: ["pricing", "product_definition"],
    ownerQuestionRo:
      "Aluminiu? PVC? plexiglas/acrylic? altceva? 30/60 mm același material sau diferit?",
    notesRo: "Fără material implicit.",
  }),
  pendingInput({
    key: "return_material_unit",
    labelRo: "Unitate calcul material cant",
    unit: "none",
    blockingArea: ["pricing"],
    ownerQuestionRo: "Material pe ml, mp, bucată, set sau altă unitate?",
    notesRo: "Fără unitate presupusă.",
  }),
  pendingInput({
    key: "return_labor_unit",
    labelRo: "Unitate manoperă cant",
    unit: "none",
    blockingArea: ["pricing"],
    ownerQuestionRo: "Manoperă pe ml, bucată, set, mp sau altfel?",
    notesRo: "Fără unitate presupusă.",
  }),
  pendingInput({
    key: "ral_material_price_rule",
    labelRo: "Regulă preț material Vopsit RAL",
    unit: "lei",
    blockingArea: ["pricing"],
    ownerQuestionRo: "Preț material 30 mm? 60 mm? 80 mm? Unitate ml/mp/set/bucată?",
    notesRo: "Fără prețuri material inventate.",
  }),
  pendingInput({
    key: "ral_labor_price_rule",
    labelRo: "Regulă manoperă Vopsit RAL",
    unit: "lei",
    blockingArea: ["pricing"],
    ownerQuestionRo: "Pe ml? set? piesă/literă? mp? minim + ml?",
    notesRo: "Fără formule manoperă inventate.",
  }),
  pendingInput({
    key: "minimum_price_rule",
    labelRo: "Minim preț cant (dacă există)",
    unit: "lei",
    blockingArea: ["pricing"],
    ownerQuestionRo: "Există minim de preț pentru cant? Dacă da, pe ce bază?",
    notesRo: "Fără minim inventat.",
  }),
  pendingInput({
    key: "perimeter_geometry_source",
    labelRo: "Sursă perimetru / geometrie cant",
    blockingArea: ["product_definition"],
    ownerQuestionRo: "Perimetrul vine din față confirmată? Alt path Product Truth?",
    notesRo: "Necesar pentru ProductDefinition — neconfirmat.",
  }),
  pendingInput({
    key: "material_depth_compatibility",
    labelRo: "Compatibilitate material ↔ adâncime",
    blockingArea: ["product_definition"],
    ownerQuestionRo: "Ce combinații material/adâncime sunt valide?",
    notesRo: "Reguli de compatibilitate neconfirmate.",
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
  pendingCount: number;
  blockedCount: number;
  missingBeforePricingCount: number;
  missingBeforeProductDefinitionCount: number;
};

export function formatReturnCantOwnerInputDisplayValue(input: ReturnCantOwnerInput): string {
  if (input.status !== "owner_confirmed" || input.value === null) {
    return RETURN_CANT_OWNER_INPUT_DISPLAY_UNKNOWN;
  }
  if (Array.isArray(input.value)) {
    return input.value.join(" · ");
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
  const pendingCount = inputs.filter((i) => i.status === "owner_input_required").length;
  const blockedCount = inputs.filter((i) => i.status === "blocked_until_owner_decision").length;
  const missingBeforePricingCount = inputs.filter(
    (i) =>
      i.status !== "owner_confirmed" &&
      i.blockingArea.includes("pricing") &&
      i.key !== "pricing_activation",
  ).length;
  const missingBeforeProductDefinitionCount = inputs.filter(
    (i) => i.status !== "owner_confirmed" && i.blockingArea.includes("product_definition"),
  ).length;

  return {
    globalStatus: "OWNER_INPUT_REQUIRED",
    confirmedCount,
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

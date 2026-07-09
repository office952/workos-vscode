export type ReturnCantCatalogInputStatus =
  | "owner_confirmed"
  | "owner_input_required"
  | "partial_confirmed"
  | "blocked_until_owner_decision"
  | "future_catalog_source_required";

export type ReturnCantPricingInputStatus =
  | "owner_confirmed"
  | "owner_input_required"
  | "partial_confirmed"
  | "not_pricing_active"
  | "blocked_until_owner_decision";

export type ReturnCantCatalogPriceCategory =
  | "oracal_catalog"
  | "oracal_pricing"
  | "ral_catalog"
  | "ral_material_pricing"
  | "ral_labor_pricing"
  | "minimum_rule"
  | "material_depth_compatibility";

export type ReturnCantCatalogPriceBlock =
  | "pricing"
  | "product_definition"
  | "execution"
  | "catalog"
  | "operator_ui";

export type ReturnCantCatalogPriceInput = {
  key: string;
  labelRo: string;
  category: ReturnCantCatalogPriceCategory;
  status: ReturnCantCatalogInputStatus | ReturnCantPricingInputStatus;
  confirmedValue: string | number | boolean | string[] | null;
  unit?: "ml" | "mp" | "buc" | "set" | "lei" | "eur" | "none";
  knownSoFarRo: string;
  stillMissingRo: string[];
  ownerQuestionRo: string;
  blocks: ReturnCantCatalogPriceBlock[];
  mustNotInvent: boolean;
  pricingActive: false;
};

export const RETURN_CANT_DEPTH_MM_PLACEHOLDERS = ["30", "60", "80", "100"] as const;

export const RETURN_CANT_CATALOG_PRICE_INPUTS: ReturnCantCatalogPriceInput[] = [
  {
    key: "oracal_selector_source",
    labelRo: "Sursă listă completă Oracal",
    category: "oracal_catalog",
    status: "partial_confirmed",
    confirmedValue: "listă completă Oracal",
    knownSoFarRo: "Owner confirmat: selector listă completă Oracal.",
    stillMissingRo: [
      "Sursa listei complete",
      "Format catalog",
      "Cine întreține catalogul",
      "Cod + nume + culoare + familie + disponibilitate",
    ],
    ownerQuestionRo:
      "Care este sursa listei complete Oracal? O introducem manual într-un catalog intern, importăm din fișier, sau o ținem ca listă administrabilă mai târziu?",
    blocks: ["catalog", "operator_ui", "pricing"],
    mustNotInvent: true,
    pricingActive: false,
  },
  {
    key: "oracal_catalog_shape",
    labelRo: "Formă catalog Oracal (doar structură)",
    category: "oracal_catalog",
    status: "owner_input_required",
    confirmedValue: null,
    knownSoFarRo: "Propunere structură: code · name · family · color_group · active · notes — fără date.",
    stillMissingRo: [
      "Confirmare câmpuri stocate",
      "Catalog efectiv de coduri",
    ],
    ownerQuestionRo:
      "Pentru codurile Oracal vrei să stocăm doar codul sau cod + nume culoare + familie + grupă culoare?",
    blocks: ["catalog", "operator_ui"],
    mustNotInvent: true,
    pricingActive: false,
  },
  {
    key: "oracal_price_mode",
    labelRo: "Mod pricing Oracal",
    category: "oracal_pricing",
    status: "owner_confirmed",
    confirmedValue: "preț pe cod/familie",
    knownSoFarRo: "Owner confirmat: preț diferit pe cod/familie.",
    stillMissingRo: [
      "Tabel prețuri efectiv",
      "Monedă",
      "Unitate preț",
      "Mapare familie",
    ],
    ownerQuestionRo: "Care sunt prețurile Oracal pe cod/familie?",
    blocks: ["pricing"],
    mustNotInvent: true,
    pricingActive: false,
  },
  {
    key: "oracal_price_unit",
    labelRo: "Unitate preț Oracal",
    category: "oracal_pricing",
    status: "owner_input_required",
    confirmedValue: null,
    knownSoFarRo:
      "Material/manoperă cant confirmate pe ml — unitatea Oracal pricing nu este presupusă.",
    stillMissingRo: ["Unitate calcul preț Oracal (ml / mp folie / altceva)"],
    ownerQuestionRo:
      "Prețul Oracal îl calculăm pe ml de cant, mp de folie, sau altă unitate? Pentru cant recomandarea tehnică este ml, dar nu confirmăm fără owner.",
    blocks: ["pricing"],
    mustNotInvent: true,
    pricingActive: false,
  },
  {
    key: "oracal_price_table",
    labelRo: "Tabel prețuri Oracal",
    category: "oracal_pricing",
    status: "owner_input_required",
    confirmedValue: null,
    knownSoFarRo: "Mod preț pe cod/familie confirmat — fără tabel inventat.",
    stillMissingRo: [
      "Cod/familie",
      "Preț unitar",
      "Monedă",
      "Unitate",
      "Dată efectivă (opțional, mai târziu)",
    ],
    ownerQuestionRo: "Care sunt prețurile Oracal pe cod/familie?",
    blocks: ["pricing"],
    mustNotInvent: true,
    pricingActive: false,
  },
  {
    key: "ral_selector_source",
    labelRo: "Sursă selector RAL standard",
    category: "ral_catalog",
    status: "partial_confirmed",
    confirmedValue: "selector standard RAL",
    knownSoFarRo: "Owner confirmat: mod selector standard RAL.",
    stillMissingRo: [
      "Sursa listei standard RAL",
      "Colectie (RAL Classic / Design / Effect / altă)",
      "Cod + nume culoare",
    ],
    ownerQuestionRo: "Folosim RAL Classic ca listă standard sau altă listă RAL?",
    blocks: ["catalog", "operator_ui", "pricing"],
    mustNotInvent: true,
    pricingActive: false,
  },
  {
    key: "ral_catalog_shape",
    labelRo: "Formă catalog RAL (doar structură)",
    category: "ral_catalog",
    status: "owner_input_required",
    confirmedValue: null,
    knownSoFarRo: "Propunere structură: ral_code · ral_name · collection · active — fără date.",
    stillMissingRo: ["Confirmare câmpuri stocate", "Listă RAL efectivă"],
    ownerQuestionRo: "Pentru RAL vrei cod simplu sau cod + nume culoare?",
    blocks: ["catalog", "operator_ui"],
    mustNotInvent: true,
    pricingActive: false,
  },
  {
    key: "ral_material_unit",
    labelRo: "Unitate preț material Vopsit RAL",
    category: "ral_material_pricing",
    status: "owner_confirmed",
    confirmedValue: "ml",
    unit: "ml",
    knownSoFarRo: "Owner confirmat: material Vopsit RAL pe ml.",
    stillMissingRo: [
      "Valoare preț",
      "Diferențiere pe adâncime 30/60/80/100 mm",
      "Monedă",
    ],
    ownerQuestionRo:
      "Care este prețul material Vopsit RAL pe ml pentru 30 / 60 / 80 / 100 mm? Este același sau diferit pe adâncime?",
    blocks: ["pricing"],
    mustNotInvent: true,
    pricingActive: false,
  },
  {
    key: "ral_material_price_by_depth",
    labelRo: "Preț material Vopsit RAL pe adâncime",
    category: "ral_material_pricing",
    status: "owner_input_required",
    confirmedValue: null,
    unit: "ml",
    knownSoFarRo: "Unitate ml confirmată — fără valori preț.",
    stillMissingRo: RETURN_CANT_DEPTH_MM_PLACEHOLDERS.map((d) => `${d} mm — OWNER INPUT REQUIRED`),
    ownerQuestionRo:
      "Care este prețul material Vopsit RAL pe ml pentru 30 / 60 / 80 / 100 mm? Este același sau diferit pe adâncime?",
    blocks: ["pricing"],
    mustNotInvent: true,
    pricingActive: false,
  },
  {
    key: "ral_labor_unit",
    labelRo: "Unitate preț manoperă Vopsit RAL",
    category: "ral_labor_pricing",
    status: "owner_confirmed",
    confirmedValue: "ml",
    unit: "ml",
    knownSoFarRo: "Owner confirmat: manoperă Vopsit RAL pe ml.",
    stillMissingRo: [
      "Valoare preț manoperă",
      "Regulă minim",
      "Diferențiere pe adâncime",
    ],
    ownerQuestionRo:
      "Care este prețul manoperă Vopsit RAL pe ml pentru 30 / 60 / 80 / 100 mm? Este același sau diferit pe adâncime?",
    blocks: ["pricing"],
    mustNotInvent: true,
    pricingActive: false,
  },
  {
    key: "ral_labor_price_by_depth",
    labelRo: "Preț manoperă Vopsit RAL pe adâncime",
    category: "ral_labor_pricing",
    status: "owner_input_required",
    confirmedValue: null,
    unit: "ml",
    knownSoFarRo: "Unitate ml confirmată — fără valori preț.",
    stillMissingRo: RETURN_CANT_DEPTH_MM_PLACEHOLDERS.map((d) => `${d} mm — OWNER INPUT REQUIRED`),
    ownerQuestionRo:
      "Care este prețul manoperă Vopsit RAL pe ml pentru 30 / 60 / 80 / 100 mm? Este același sau diferit pe adâncime?",
    blocks: ["pricing"],
    mustNotInvent: true,
    pricingActive: false,
  },
  {
    key: "ral_minimum_rule",
    labelRo: "Regulă minim Vopsit RAL",
    category: "minimum_rule",
    status: "owner_input_required",
    confirmedValue: null,
    knownSoFarRo: "Fără minim presupus.",
    stillMissingRo: [
      "Există minim?",
      "Valoare minim",
      "Se aplică la material / manoperă / total?",
    ],
    ownerQuestionRo:
      "Există preț minim pentru Vopsit RAL pe lucrare/set? Dacă da, care este minimul și se aplică la material, manoperă sau total?",
    blocks: ["pricing"],
    mustNotInvent: true,
    pricingActive: false,
  },
  {
    key: "return_material_depth_compatibility",
    labelRo: "Compatibilitate material ↔ adâncime",
    category: "material_depth_compatibility",
    status: "owner_input_required",
    confirmedValue: null,
    knownSoFarRo: "Material cant = aluminiu 0.6 mm. Adâncimi = 30 / 60 / 80 / 100 mm.",
    stillMissingRo: [
      "Validitate aluminiu 0.6 mm pentru toate adâncimile",
      "Excepții sau combinații interzise",
      "Adâncimi care cer alt material/grosime",
    ],
    ownerQuestionRo:
      "Aluminiu 0.6 mm este valid pentru toate adâncimile 30 / 60 / 80 / 100 mm sau există combinații interzise?",
    blocks: ["product_definition", "pricing"],
    mustNotInvent: true,
    pricingActive: false,
  },
];

export type ReturnCantCatalogPriceSection = {
  sectionKey: string;
  labelRo: string;
  category: ReturnCantCatalogPriceCategory;
};

export const RETURN_CANT_CATALOG_PRICE_SECTIONS: ReturnCantCatalogPriceSection[] = [
  { sectionKey: "oracal_catalog", labelRo: "A. Oracal catalog", category: "oracal_catalog" },
  { sectionKey: "oracal_pricing", labelRo: "B. Oracal pricing", category: "oracal_pricing" },
  { sectionKey: "ral_catalog", labelRo: "C. RAL catalog", category: "ral_catalog" },
  { sectionKey: "ral_material_pricing", labelRo: "D. RAL material pricing", category: "ral_material_pricing" },
  { sectionKey: "ral_labor_pricing", labelRo: "E. RAL labor pricing", category: "ral_labor_pricing" },
  { sectionKey: "minimum_rule", labelRo: "F. Minimum rule", category: "minimum_rule" },
  {
    sectionKey: "material_depth_compatibility",
    labelRo: "G. Material-depth compatibility",
    category: "material_depth_compatibility",
  },
];

export const RETURN_CANT_BLOCKERS_BEFORE_PRICING = [
  "Oracal actual catalog missing",
  "Oracal price table missing",
  "RAL selector source/list missing",
  "RAL material prices missing",
  "RAL labor prices/minimum missing",
  "Material/depth compatibility missing",
] as const;

export type ReturnCantCatalogPriceSummary = {
  totalCatalogPriceInputs: number;
  ownerConfirmedCount: number;
  partialConfirmedCount: number;
  ownerInputRequiredCount: number;
  pricingActiveCount: number;
  readyForPricing: false;
  blockersBeforePricing: readonly string[];
};

export function catalogPriceInputStatusLabel(
  status: ReturnCantCatalogPriceInput["status"],
): string {
  switch (status) {
    case "owner_confirmed":
      return "CONFIRMED";
    case "partial_confirmed":
      return "PARTIAL";
    case "owner_input_required":
      return "OWNER INPUT";
    case "future_catalog_source_required":
      return "CATALOG SOURCE";
    case "not_pricing_active":
      return "NOT ACTIVE";
    case "blocked_until_owner_decision":
      return "BLOCKED";
    default:
      return status.toUpperCase();
  }
}

export function catalogPriceInputStatusTone(
  status: ReturnCantCatalogPriceInput["status"],
): "emerald" | "cyan" | "amber" | "rose" | "slate" {
  if (status === "owner_confirmed") return "emerald";
  if (status === "partial_confirmed") return "cyan";
  if (status === "owner_input_required" || status === "future_catalog_source_required") return "amber";
  if (status === "blocked_until_owner_decision") return "rose";
  return "slate";
}

export function getReturnCantCatalogPriceInputsByCategory(
  category: ReturnCantCatalogPriceCategory,
  inputs: ReturnCantCatalogPriceInput[] = RETURN_CANT_CATALOG_PRICE_INPUTS,
): ReturnCantCatalogPriceInput[] {
  return inputs.filter((input) => input.category === category);
}

export function buildReturnCantCatalogPriceSummary(
  inputs: ReturnCantCatalogPriceInput[] = RETURN_CANT_CATALOG_PRICE_INPUTS,
): ReturnCantCatalogPriceSummary {
  return {
    totalCatalogPriceInputs: inputs.length,
    ownerConfirmedCount: inputs.filter((i) => i.status === "owner_confirmed").length,
    partialConfirmedCount: inputs.filter((i) => i.status === "partial_confirmed").length,
    ownerInputRequiredCount: inputs.filter((i) => i.status === "owner_input_required").length,
    pricingActiveCount: inputs.filter((i) => i.pricingActive).length,
    readyForPricing: false,
    blockersBeforePricing: RETURN_CANT_BLOCKERS_BEFORE_PRICING,
  };
}

export function getReturnCantCatalogPriceInput(key: string): ReturnCantCatalogPriceInput | null {
  return RETURN_CANT_CATALOG_PRICE_INPUTS.find((i) => i.key === key) ?? null;
}

export function formatCatalogPriceConfirmedValue(input: ReturnCantCatalogPriceInput): string {
  if (input.confirmedValue === null) {
    return "OWNER INPUT REQUIRED";
  }
  if (Array.isArray(input.confirmedValue)) {
    return input.confirmedValue.join(" · ");
  }
  if (typeof input.confirmedValue === "boolean") {
    return input.confirmedValue ? "Da" : "Nu";
  }
  return String(input.confirmedValue);
}

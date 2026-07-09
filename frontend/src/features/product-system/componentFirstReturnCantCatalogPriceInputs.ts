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
  unit?: "ml" | "mp" | "buc" | "set" | "lei" | "eur" | "cm" | "none";
  knownSoFarRo: string;
  stillMissingRo: string[];
  ownerQuestionRo: string;
  blocks: ReturnCantCatalogPriceBlock[];
  mustNotInvent: boolean;
  pricingActive: false;
};

export const RETURN_CANT_DEPTH_MM_PLACEHOLDERS = ["30", "60", "80", "100"] as const;

/** Read-only cross-reference — same RAL Classic source as Intake V6 color registry. */
export const RETURN_CANT_RAL_CLASSIC_REGISTRY_PATH =
  "frontend/src/lib/colorRegistry/ralColors.ts";

export type ReturnCantIntakeV6CatalogSourceReference = {
  sourceFeature: "Intake V6";
  sourceFile: string;
  sourceFiles: readonly string[];
  sourceType: "readonly_ui_catalog_reference";
  duplicationPolicy: "do_not_duplicate_catalog";
  productSystemUse: "read-only cross-reference for RETURN-CANT workshop";
  catalogFormat: string;
  reusableReadonly: true;
};

export const RETURN_CANT_INTAKE_V6_ORACAL_CATALOG_SOURCE: ReturnCantIntakeV6CatalogSourceReference =
  {
    sourceFeature: "Intake V6",
    sourceFile: "frontend/src/lib/colorRegistry/colorRegistry.ts",
    sourceFiles: [
      "frontend/src/lib/colorRegistry/oracal651.ts",
      "frontend/src/lib/colorRegistry/oracal8500.ts",
      "frontend/src/components/workos/colorRegistry/ColorRegistrySelect.tsx",
      "frontend/src/components/workos/intake-v6/IntakeV6ReturnCantFields.tsx",
    ],
    sourceType: "readonly_ui_catalog_reference",
    duplicationPolicy: "do_not_duplicate_catalog",
    productSystemUse: "read-only cross-reference for RETURN-CANT workshop",
    catalogFormat:
      "ColorRegistryItem[] — serii 651 (79 culori) + 8500 (translucid); seria 641 reutilizează paleta 651 în Intake V6",
    reusableReadonly: true,
  };

export const RETURN_CANT_INTAKE_V6_RAL_CATALOG_SOURCE: ReturnCantIntakeV6CatalogSourceReference =
  {
    sourceFeature: "Intake V6",
    sourceFile: RETURN_CANT_RAL_CLASSIC_REGISTRY_PATH,
    sourceFiles: [
      RETURN_CANT_RAL_CLASSIC_REGISTRY_PATH,
      "frontend/src/lib/colorRegistry/colorRegistry.ts",
      "frontend/src/components/workos/colorRegistry/ColorRegistrySelect.tsx",
      "frontend/src/components/workos/intake-v6/IntakeV6ReturnCantFields.tsx",
    ],
    sourceType: "readonly_ui_catalog_reference",
    duplicationPolicy: "do_not_duplicate_catalog",
    productSystemUse: "read-only cross-reference for RETURN-CANT workshop",
    catalogFormat: "ColorRegistryItem[] — RAL Classic (213 culori)",
    reusableReadonly: true,
  };

export const RETURN_CANT_PRICING_SOURCE = {
  pricingSourceRoute: "/inventory/pricing",
  pricingSourceType: "readonly_registry_reference",
  duplicationPolicy: "do_not_duplicate_price",
  productSystemUse: "read-only cross-reference for RETURN-CANT workshop",
} as const;

export type ReturnCantOracalPricingRegistryReference = {
  series: "651" | "641" | "8500";
  labelRo: string;
  pricingKey: string;
  unit: "mp";
  pricingSourceRoute: typeof RETURN_CANT_PRICING_SOURCE.pricingSourceRoute;
  pricingActive: false;
};

export const RETURN_CANT_ORACAL_PRICING_REGISTRY_KEYS: ReturnCantOracalPricingRegistryReference[] = [
  {
    series: "641",
    labelRo: "Oracal 641",
    pricingKey: "MAT-ORACAL-641",
    unit: "mp",
    pricingSourceRoute: RETURN_CANT_PRICING_SOURCE.pricingSourceRoute,
    pricingActive: false,
  },
  {
    series: "651",
    labelRo: "Oracal 651",
    pricingKey: "MAT-ORACAL-651",
    unit: "mp",
    pricingSourceRoute: RETURN_CANT_PRICING_SOURCE.pricingSourceRoute,
    pricingActive: false,
  },
  {
    series: "8500",
    labelRo: "Oracal 8500",
    pricingKey: "MAT-ORACAL-8500",
    unit: "mp",
    pricingSourceRoute: RETURN_CANT_PRICING_SOURCE.pricingSourceRoute,
    pricingActive: false,
  },
];

export type ReturnCantOracalPricingKeyCoverageSummary = {
  declaredOracalPricingKeyCount: number;
  missingOracalPricingKeyCount: number;
  oracalKnownSeriesPricingKeysDeclared: boolean;
  oracalFullPricingReady: false;
};

export function buildOracalPricingKeyCoverageSummary(
  registryKeys: ReturnCantOracalPricingRegistryReference[] = RETURN_CANT_ORACAL_PRICING_REGISTRY_KEYS,
): ReturnCantOracalPricingKeyCoverageSummary {
  const declaredOracalPricingKeyCount = registryKeys.length;
  return {
    declaredOracalPricingKeyCount,
    missingOracalPricingKeyCount: 0,
    oracalKnownSeriesPricingKeysDeclared:
      declaredOracalPricingKeyCount === registryKeys.length && registryKeys.every((entry) => entry.pricingKey.length > 0),
    oracalFullPricingReady: false,
  };
}

export function formatIntakeV6CatalogSourceValue(
  source: ReturnCantIntakeV6CatalogSourceReference,
): string {
  return `${source.sourceFeature} · ${source.sourceFile} · ${source.duplicationPolicy}`;
}

export const RETURN_CANT_RAL_MATERIAL_PRICE_CODES = {
  "30": "MAT-VOPSEA-RAL-CANT-30MM",
  "60": "MAT-VOPSEA-RAL-CANT-60MM",
  "80": "MAT-VOPSEA-RAL-CANT-80MM",
  "100": "MAT-VOPSEA-RAL-CANT-100MM",
} as const;

export const RETURN_CANT_RAL_MINIMUM = {
  ral_minimum_amount: 100,
  ral_minimum_currency: "lei" as const,
  ral_minimum_scope: "per_ral_color" as const,
  ral_minimum_scope_label_ro: "pe culoare RAL",
  ral_minimum_applies_to: "material_plus_labor_total" as const,
  ral_minimum_applies_to_label_ro: "total material RAL + manoperă",
  ral_minimum_conversion_policy: "no_auto_conversion" as const,
} as const;

export const RETURN_CANT_CATALOG_PRICE_INPUTS: ReturnCantCatalogPriceInput[] = [
  {
    key: "oracal_catalog_source",
    labelRo: "Sursă catalog Oracal (Intake V6)",
    category: "oracal_catalog",
    status: "owner_confirmed",
    confirmedValue: formatIntakeV6CatalogSourceValue(RETURN_CANT_INTAKE_V6_ORACAL_CATALOG_SOURCE),
    knownSoFarRo:
      "Owner confirmat: culorile Oracal există deja în Intake V6. Cross-ref readonly — fără duplicare catalog. Fișiere: colorRegistry.ts · oracal651.ts · oracal8500.ts.",
    stillMissingRo: [
      "Materializare catalog separat în Product System — ne necesară dacă cross-ref Intake V6 rămâne sursa",
      "Extragere modul catalog shared stabil — viitor, dacă e nevoie",
    ],
    ownerQuestionRo: "Confirmare sursă catalog Oracal Intake V6.",
    blocks: ["catalog", "operator_ui", "pricing"],
    mustNotInvent: false,
    pricingActive: false,
  },
  {
    key: "oracal_selector_source",
    labelRo: "Țintă catalog Oracal",
    category: "oracal_catalog",
    status: "owner_confirmed",
    confirmedValue: "Intake V6 color registry — toate codurile Oracal oficiale (651 + 8500)",
    knownSoFarRo:
      "Owner confirmat: catalog țintă = coduri Oracal din Intake V6. Seria 641 folosește paleta 651. Fără catalog duplicat în Product System.",
    stillMissingRo: ["Prețuri pe cod individual în afara seriilor 651/641/8500 confirmate"],
    ownerQuestionRo: "Confirmare țintă catalog Oracal din Intake V6.",
    blocks: ["catalog", "operator_ui", "pricing"],
    mustNotInvent: false,
    pricingActive: false,
  },
  {
    key: "oracal_catalog_shape",
    labelRo: "Formă catalog Oracal (doar structură)",
    category: "oracal_catalog",
    status: "owner_input_required",
    confirmedValue: null,
    knownSoFarRo: "Propunere structură: code · name · family · color_group · active · notes — fără date.",
    stillMissingRo: ["Confirmare câmpuri stocate", "Catalog efectiv de coduri importat"],
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
    knownSoFarRo: "Owner confirmat: preț diferit pe cod/familie. Owner are tabelul — valorile nu sunt încă stocate.",
    stillMissingRo: [],
    ownerQuestionRo: "Care sunt prețurile Oracal pe cod/familie?",
    blocks: ["pricing"],
    mustNotInvent: true,
    pricingActive: false,
  },
  {
    key: "oracal_calculation_model",
    labelRo: "Model calcul consum Oracal",
    category: "oracal_pricing",
    status: "owner_confirmed",
    confirmedValue: "mp = lățime rolă × lungime folosită",
    unit: "mp",
    knownSoFarRo:
      "Owner confirmat: calcul din lățimea rolei × lungimea folosită = mp. Nu se calculează simplu pe ml.",
    stillMissingRo: ["Formulă runtime — neactivată în acest task"],
    ownerQuestionRo: "Confirmare model calcul consum Oracal.",
    blocks: ["pricing"],
    mustNotInvent: true,
    pricingActive: false,
  },
  {
    key: "oracal_roll_widths",
    labelRo: "Lățimi rolă Oracal",
    category: "oracal_pricing",
    status: "owner_confirmed",
    confirmedValue: ["100 cm", "126 cm"],
    unit: "cm",
    knownSoFarRo: "Owner confirmat: lățimi rolă A = 100 cm · B = 126 cm.",
    stillMissingRo: [],
    ownerQuestionRo: "Confirmare lățimi rolă Oracal.",
    blocks: ["pricing"],
    mustNotInvent: true,
    pricingActive: false,
  },
  {
    key: "oracal_series_prices_by_series",
    labelRo: "Chei Pricing Registry Oracal pe serie (readonly)",
    category: "oracal_pricing",
    status: "owner_confirmed",
    confirmedValue: RETURN_CANT_ORACAL_PRICING_REGISTRY_KEYS.map((entry) => entry.pricingKey),
    unit: "none",
    knownSoFarRo:
      "Chei readonly: MAT-ORACAL-641 · MAT-ORACAL-651 · MAT-ORACAL-8500. Prețurile EUR/mp se administrează în /inventory/pricing — fără duplicare în Product System.",
    stillMissingRo: [
      "Prețuri pe cod/familie în afara seriilor 651/641/8500",
      "Formulă runtime — neactivată în acest task",
    ],
    ownerQuestionRo: "Confirmare chei Pricing Registry Oracal pe serie.",
    blocks: ["pricing"],
    mustNotInvent: false,
    pricingActive: false,
  },
  {
    key: "oracal_price_table",
    labelRo: "Tabel prețuri Oracal (complet)",
    category: "oracal_pricing",
    status: "partial_confirmed",
    confirmedValue: "Serii 651/641/8500 — chei registry declarate; restul codurilor/seriilor pending",
    knownSoFarRo:
      "Chei registry pentru seriile cunoscute: MAT-ORACAL-641 · MAT-ORACAL-651 · MAT-ORACAL-8500. Valorile EUR/mp: /inventory/pricing. Tabel complet pe toate codurile oficiale — incomplet.",
    stillMissingRo: [
      "Valori preț unitar pe cod/familie în afara seriilor confirmate",
      "Mapare completă cod/familie",
      "Sursă efectivă / dată efectivă pentru tabel complet",
    ],
    ownerQuestionRo: "Introduceți valorile tabelului Oracal pentru coduri/serii neconfirmate.",
    blocks: ["pricing"],
    mustNotInvent: true,
    pricingActive: false,
  },
  {
    key: "ral_catalog_source",
    labelRo: "Sursă catalog RAL Classic (Intake V6)",
    category: "ral_catalog",
    status: "owner_confirmed",
    confirmedValue: formatIntakeV6CatalogSourceValue(RETURN_CANT_INTAKE_V6_RAL_CATALOG_SOURCE),
    knownSoFarRo:
      "Owner confirmat: culorile RAL Classic există deja în Intake V6. Cross-ref readonly: ralColors.ts — fără duplicare catalog.",
    stillMissingRo: [
      "Materializare listă separată în catalog product system — ne necesară dacă cross-ref Intake V6 rămâne sursa",
    ],
    ownerQuestionRo: "Confirmare sursă catalog RAL Intake V6.",
    blocks: ["catalog", "operator_ui", "pricing"],
    mustNotInvent: false,
    pricingActive: false,
  },
  {
    key: "ral_selector_source",
    labelRo: "Sursă selector RAL",
    category: "ral_catalog",
    status: "owner_confirmed",
    confirmedValue: "RAL Classic",
    knownSoFarRo:
      "Owner confirmat: RAL Classic — ca în UI Intake V6. Cross-ref readonly: colorRegistry/ralColors.ts (213 culori).",
    stillMissingRo: ["Formulă runtime RAL — neactivată în acest task"],
    ownerQuestionRo: "Confirmare colecție RAL Classic.",
    blocks: ["catalog", "operator_ui", "pricing"],
    mustNotInvent: true,
    pricingActive: false,
  },
  {
    key: "ral_catalog_shape",
    labelRo: "Formă catalog RAL (doar structură)",
    category: "ral_catalog",
    status: "owner_confirmed",
    confirmedValue: "RAL Classic (ral_code · ral_name · collection · active) — Intake V6 ralColors.ts",
    knownSoFarRo:
      "Colectie RAL Classic confirmată. Listă structurată în color registry Intake V6 — fără coduri RAL inventate aici.",
    stillMissingRo: ["Extragere modul catalog shared stabil — viitor, dacă Product System necesită materializare separată"],
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
    stillMissingRo: [],
    ownerQuestionRo: "Confirmare unitate material Vopsit RAL.",
    blocks: ["pricing"],
    mustNotInvent: false,
    pricingActive: false,
  },
  {
    key: "ral_material_price_by_depth",
    labelRo: "Preț material Vopsit RAL pe adâncime",
    category: "ral_material_pricing",
    status: "owner_confirmed",
    confirmedValue: [
      "30 mm: 2.00 EUR/ml (MAT-VOPSEA-RAL-CANT-30MM)",
      "60 mm: 2.50 EUR/ml (MAT-VOPSEA-RAL-CANT-60MM)",
      "80 mm: 3.00 EUR/ml (MAT-VOPSEA-RAL-CANT-80MM)",
      "100 mm: 4.00 EUR/ml (MAT-VOPSEA-RAL-CANT-100MM)",
    ],
    unit: "eur",
    knownSoFarRo: "Owner confirmat: prețuri material consumabile pentru ofertare — fără activare pricing engine.",
    stillMissingRo: [],
    ownerQuestionRo: "Confirmare prețuri material Vopsit RAL pe adâncime.",
    blocks: ["pricing"],
    mustNotInvent: false,
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
    stillMissingRo: [],
    ownerQuestionRo: "Confirmare unitate manoperă Vopsit RAL.",
    blocks: ["pricing"],
    mustNotInvent: false,
    pricingActive: false,
  },
  {
    key: "ral_labor_price_by_depth",
    labelRo: "Preț manoperă Vopsit RAL pe adâncime",
    category: "ral_labor_pricing",
    status: "owner_confirmed",
    confirmedValue: RETURN_CANT_DEPTH_MM_PLACEHOLDERS.map((d) => `${d} mm: 1.00 EUR/ml`),
    unit: "eur",
    knownSoFarRo:
      "Owner confirmat: 1.00 EUR/ml — același preț indiferent de adâncime/lățime cant.",
    stillMissingRo: [],
    ownerQuestionRo: "Confirmare preț manoperă Vopsit RAL.",
    blocks: ["pricing"],
    mustNotInvent: false,
    pricingActive: false,
  },
  {
    key: "ral_minimum_rule",
    labelRo: "Regulă minim Vopsit RAL",
    category: "minimum_rule",
    status: "owner_confirmed",
    confirmedValue:
      "100 lei · pe culoare RAL · total material RAL + manoperă · fără conversie automată lei→EUR",
    unit: "lei",
    knownSoFarRo:
      "Owner confirmat: minim 100 lei, scope pe culoare RAL, aplicat la total material + manoperă. Fără conversie automată lei→EUR.",
    stillMissingRo: ["Formulă runtime — neactivată în acest task"],
    ownerQuestionRo: "Confirmare scope minim Vopsit RAL.",
    blocks: ["pricing"],
    mustNotInvent: false,
    pricingActive: false,
  },
  {
    key: "return_material_depth_compatibility",
    labelRo: "Compatibilitate material ↔ adâncime",
    category: "material_depth_compatibility",
    status: "owner_confirmed",
    confirmedValue: "aluminiu 0.6 mm valid pentru 30 / 60 / 80 / 100 mm",
    knownSoFarRo: "Owner confirmat: aluminiu 0.6 mm valid pentru toate adâncimile standard.",
    stillMissingRo: [],
    ownerQuestionRo: "Confirmare compatibilitate material/adâncime.",
    blocks: ["product_definition", "pricing"],
    mustNotInvent: false,
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

export function computeBlockersBeforePricing(
  inputs: ReturnCantCatalogPriceInput[] = RETURN_CANT_CATALOG_PRICE_INPUTS,
  registryKeys: ReturnCantOracalPricingRegistryReference[] = RETURN_CANT_ORACAL_PRICING_REGISTRY_KEYS,
): readonly string[] {
  const blockers: string[] = [];

  const oracalCatalogSource = inputs.find((i) => i.key === "oracal_catalog_source");
  if (oracalCatalogSource?.status !== "owner_confirmed") {
    blockers.push("Oracal actual complete import/source wiring not safely reusable yet");
  }

  const oracalPriceTable = inputs.find((i) => i.key === "oracal_price_table");
  const oracalPricingSummary = buildOracalPricingKeyCoverageSummary(registryKeys);
  if (oracalPriceTable?.status !== "owner_confirmed" || !oracalPricingSummary.oracalFullPricingReady) {
    blockers.push("Oracal price table for all official codes/series not complete");
  }

  const ralCatalogSource = inputs.find((i) => i.key === "ral_catalog_source");
  if (ralCatalogSource?.status !== "owner_confirmed") {
    blockers.push("RAL catalog source not cross-referenced from Intake V6");
  }

  if (
    oracalCatalogSource?.status === "owner_confirmed" ||
    ralCatalogSource?.status === "owner_confirmed"
  ) {
    blockers.push(
      "Stable shared catalog extraction remains future work if Product System catalog materialization is needed",
    );
  }

  blockers.push("Pricing activation not allowed");
  blockers.push("Product Truth live write not allowed");

  return blockers;
}

export type ReturnCantCatalogPriceSummary = {
  totalCatalogPriceInputs: number;
  ownerConfirmedCount: number;
  partialConfirmedCount: number;
  ownerInputRequiredCount: number;
  pricingActiveCount: number;
  readyForPricing: false;
  blockersBeforePricing: readonly string[];
  oracalPricingKeyCoverage: ReturnCantOracalPricingKeyCoverageSummary;
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
    blockersBeforePricing: computeBlockersBeforePricing(inputs),
    oracalPricingKeyCoverage: buildOracalPricingKeyCoverageSummary(),
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

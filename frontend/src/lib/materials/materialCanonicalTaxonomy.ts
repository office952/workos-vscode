/**
 * Static canonical material taxonomy — no DB/schema.
 * Source: docs/architecture/MATERIAL_CANONICAL_NAMING_AND_ALIASES.md
 */

export type MaterialFamilyId =
  | "acm_acp_panel"
  | "pvc_expanded"
  | "pmma_acrylic"
  | "vinyl_film"
  | "steel_profile"
  | "aluminium_profile"
  | "polycarbonate"
  | "mounting_consumables";

export interface MaterialFamilyDefinition {
  material_family: MaterialFamilyId;
  canonical_label: string;
  aliases: string[];
  brand_terms: string[];
  series_terms: string[];
  usage_warning_terms: string[];
  examples: string[];
  recommended_sku_pattern: string;
}

export const MATERIAL_CANONICAL_FAMILIES: readonly MaterialFamilyDefinition[] = [
  {
    material_family: "acm_acp_panel",
    canonical_label: "Panou compozit aluminiu (ACM/ACP)",
    aliases: [
      "acm",
      "acp",
      "bond",
      "dibond",
      "alucobond",
      "panou bond",
      "aluminiu compozit",
      "material compozit aluminiu",
      "panou compozit",
    ],
    brand_terms: ["dibond", "alucobond"],
    series_terms: [],
    usage_warning_terms: ["fata litere", "față litere", "spate litere", "casetare"],
    examples: ["ACM 3 mm alu 0.30 alb mat", "Panou compozit aluminiu 4 mm"],
    recommended_sku_pattern: "MAT-ACM-{TOTAL}MM-ALU{FOIL}-FINISH",
  },
  {
    material_family: "pvc_expanded",
    canonical_label: "PVC expandat",
    aliases: ["forex", "pvc", "pvc expandat", "placa pvc", "placă pvc", "foam pvc"],
    brand_terms: ["forex", "komatex"],
    series_terms: [],
    usage_warning_terms: ["spate litere", "sablon montaj", "șablon montaj", "premontaj"],
    examples: ["PVC expandat 10 mm alb", "Forex 3 mm șablon montaj"],
    recommended_sku_pattern: "MAT-PVC-EXPANDED-{THICKNESS}MM",
  },
  {
    material_family: "pmma_acrylic",
    canonical_label: "PMMA / plexiglas acrilic",
    aliases: ["plexiglas", "plexi", "acril", "acrilic", "pmma", "stiplex", "acrylic"],
    brand_terms: ["plexiglas", "acrylon", "stiplex"],
    series_terms: [],
    usage_warning_terms: ["fata litere", "față litere", "difuzor"],
    examples: ["PMMA opal 3 mm", "Plexiglas transparent 5 mm"],
    recommended_sku_pattern: "MAT-PMMA-{VARIANT}-{THICKNESS}MM",
  },
  {
    material_family: "vinyl_film",
    canonical_label: "Folie autocolantă PVC",
    aliases: [
      "folie",
      "autocolant",
      "vinyl",
      "sticker",
      "print vinyl",
      "oracal",
      "autocolant print",
    ],
    brand_terms: ["oracal"],
    series_terms: ["641", "651", "8500"],
    usage_warning_terms: ["fata litere", "față litere", "cant", "return"],
    examples: ["Oracal 651 — autocolant față", "Folie autocolantă print + laminare"],
    recommended_sku_pattern: "MAT-VINYL-{TYPE} sau MAT-ORACAL-{SERIES}",
  },
  {
    material_family: "steel_profile",
    canonical_label: "Țeavă / profil oțel",
    aliases: [
      "teava",
      "țeavă",
      "profil otel",
      "profil oțel",
      "bara",
      "bară",
      "bare",
      "patrat",
      "pătrat",
      "rectangular",
      "rotund",
      "cornier",
      "platbanda",
      "platbandă",
      "otel",
      "oțel",
    ],
    brand_terms: [],
    series_terms: [],
    usage_warning_terms: [
      "premount",
      "premontaj",
      "litere",
      "structura suport",
      "structură suport",
      "cadru",
      "rama",
      "ramă",
    ],
    examples: ["Țeavă pătrată oțel 30×30×1.5 mm"],
    recommended_sku_pattern: "MAT-STEEL-SQUARE-TUBE-{W}x{H}x{T}",
  },
  {
    material_family: "aluminium_profile",
    canonical_label: "Profil aluminiu",
    aliases: [
      "aluminiu",
      "profil al",
      "profil aluminiu",
      "profil rama",
      "profil ramă",
      "profil caseta",
      "profil casetă",
      "profil textil",
      "profil banner",
      "profil litera",
      "profil literă",
      "profil structural aluminiu",
    ],
    brand_terms: [],
    series_terms: [],
    usage_warning_terms: [
      "litere volumetrice",
      "caseta",
      "casetă",
      "caseta luminoasa",
      "casetă luminoasă",
      "premontaj",
      "cant",
      "lateral",
    ],
    examples: ["Profil aluminiu return/cant 60 mm", "Profil ramă casetă luminoasă"],
    recommended_sku_pattern: "MAT-ALU-PROFILE-{SHAPE}-{WxHxT}",
  },
  {
    material_family: "polycarbonate",
    canonical_label: "Policarbonat",
    aliases: ["policarbonat", "polycarbonate", "pc"],
    brand_terms: [],
    series_terms: [],
    usage_warning_terms: ["difuzor", "opal"],
    examples: ["Policarbonat opal 3 mm difuzor"],
    recommended_sku_pattern: "MAT-PC-{VARIANT}-{THICKNESS}MM",
  },
  {
    material_family: "mounting_consumables",
    canonical_label: "Consumabile montaj",
    aliases: [
      "surub",
      "șurub",
      "cablu",
      "conector",
      "adeziv",
      "distantier",
      "distanțier",
      "silicon",
      "capse",
      "banda",
      "bandă",
    ],
    brand_terms: [],
    series_terms: [],
    usage_warning_terms: ["montaj litere", "finisaj"],
    examples: ["Șurub autofiletant", "Adeziv montaj litere"],
    recommended_sku_pattern: "MAT-CONSUMABLE-{KIND}",
  },
] as const;

export function getMaterialFamilyById(id: MaterialFamilyId): MaterialFamilyDefinition {
  const found = MATERIAL_CANONICAL_FAMILIES.find((f) => f.material_family === id);
  if (!found) throw new Error(`Unknown material family: ${id}`);
  return found;
}

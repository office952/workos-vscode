/**
 * Read-only Product System modularity + honesty vocabulary.
 * Display truth only — does not change product runtime behavior.
 */

export const LETTERS_TEMPLATE_CODE = "TPL-VOLUMETRIC-LETTERS_v2";
export const LOGO_TEMPLATE_CODE = "TPL-VOLUMETRIC-LOGO_v1";
export const ACM_BOXED_TEMPLATE_CODE = "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1";
export const ACM_CASSETTE_TEMPLATE_CODE = "TPL-ACM-CASSETTED-PANEL";

export const MODULARITY_LAW_LINES_RO = [
  "UN MODUL NEALES NU ESTE O PROBLEMĂ.",
  "UN MODUL ALES TREBUIE SĂ SE SUSȚINĂ SINGUR.",
  "TEMPLATE-UL COMBINĂ MODULE — NU LE ȚINE CAPTIVE.",
] as const;

export const SETTINGS_OWNERSHIP_CONFLICT_RO =
  "Cataloage de opțiuni multiple — conflict nerezolvat";

export type HonestyAxisRow = {
  axis: string;
  valueRo: string;
  testId?: string;
};

export type ModuleTruthRow = {
  moduleKey: string;
  labelRo: string;
  independenceRo: string;
  scopeRo?: string;
  noteRo?: string;
};

export type CompositionDependencyTruth = {
  sourceRo: string;
  dependencyRo: string;
  classId: "HARD_TECHNICAL" | "CONDITIONAL" | "COMPOSITION_ONLY" | "COMMERCIAL" | "EXECUTION";
  classLabelRo: string;
  meaningRo: string;
};

export type ProductModularityTruth = {
  templateCode: string;
  commercialChipRo: string;
  capabilityChipRo?: string;
  headlineRo: string;
  summaryChipsRo: string[];
  axes: HonestyAxisRow[];
  modules: ModuleTruthRow[];
  falseGeneric: ModuleTruthRow[];
  compositionDependencies: CompositionDependencyTruth[];
  settingsConflictVisible: boolean;
  showModularityLaw: boolean;
};

const LETTERS_TRUTH: ProductModularityTruth = {
  templateCode: LETTERS_TEMPLATE_CODE,
  commercialChipRo: "Rădăcină folosită azi",
  capabilityChipRo: "De sine stătător",
  headlineRo: "Rădăcină ofertabilă · Slice 1 stabilizat · Stabilizare generală parțială",
  summaryChipsRo: [
    "Rădăcină ofertabilă",
    "Slice 1 stabilizat",
    "Stabilizare generală parțială",
  ],
  axes: [
    { axis: "Existență", valueRo: "Înregistrat", testId: "modularity-axis-existence" },
    { axis: "Ofertabilitate rădăcină", valueRo: "Ofertabil ca rădăcină", testId: "modularity-axis-root" },
    { axis: "Maturitate runtime", valueRo: "Confirmat cu limitări (Slice 1)", testId: "modularity-axis-runtime" },
    { axis: "Stabilizare", valueRo: "Stabilizat pentru Slice · Stabilizare generală parțială", testId: "modularity-axis-stabilization" },
    { axis: "Rădăcină versus copil", valueRo: "Rădăcină ofertabilă (nu copil)", testId: "modularity-axis-root-vs-child" },
    { axis: "Standalone", valueRo: "Produs complet + subset Slice 1 de sine stătător", testId: "modularity-axis-standalone" },
    { axis: "Compoziție", valueRo: "Composer pentru module active", testId: "modularity-axis-composition" },
    { axis: "Independență active-scope", valueRo: "Dovedită pe Slice 1", testId: "modularity-axis-active-scope" },
    { axis: "Independență comercială", valueRo: "Dovedită pe Slice 1", testId: "modularity-axis-commercial" },
    { axis: "Independență execuție", valueRo: "Preview dovedit pe Slice 1", testId: "modularity-axis-execution" },
    { axis: "Module captive / amânate", valueRo: "FINISH · MOUNTING — captiv / amânat", testId: "modularity-axis-captive" },
    { axis: "Ownership setări", valueRo: "CONFLICTED — cataloage multiple", testId: "modularity-axis-settings" },
  ],
  modules: [
    { moduleKey: "FACE", labelRo: "Față (FACE)", independenceRo: "de sine stătător · confirmat" },
    {
      moduleKey: "RETURN-CANT",
      labelRo: "Cant / return (RETURN-CANT)",
      independenceRo: "de sine stătător · confirmat",
      noteRo: "Bonding-ul față–cant nu este cerință standalone — doar în compoziția completă.",
    },
    { moduleKey: "BACK", labelRo: "Spate (BACK)", independenceRo: "de sine stătător · confirmat" },
    {
      moduleKey: "LIGHTING",
      labelRo: "Iluminare / electric",
      independenceRo: "confirmat cu limitări",
    },
    {
      moduleKey: "FINISH",
      labelRo: "Finisaj (FINISH)",
      independenceRo: "captiv · amânat · Activare neaprobată",
      scopeRo: "LETTERS_ONLY",
      noteRo: "Proprietar țintă: modul FINISH · Cataloage conflictuale · fără chip sold",
    },
    {
      moduleKey: "MOUNTING",
      labelRo: "Montaj (MOUNTING)",
      independenceRo: "captiv · amânat · Activare neaprobată",
      scopeRo: "SHARED_WITHIN_SIGNAGE",
      noteRo:
        "Suport legat parțial · mounting_system metodă canonică · metal_support_required = alias",
    },
  ],
  falseGeneric: [
    {
      moduleKey: "sistem_led",
      labelRo: "sistem_led",
      independenceRo: "LETTERS_ONLY",
      noteRo: "Nu este infrastructură LED reutilizabilă global.",
    },
    {
      moduleKey: "finisaje",
      labelRo: "finisaje",
      independenceRo: "LETTERS_ONLY · SURFACE_FINISH",
      noteRo: "Finisaj suprafață îngustat — nu șablon, nu ambalare.",
    },
    {
      moduleKey: "sablon_montaj",
      labelRo: "sablon_montaj",
      independenceRo: "LETTERS_ONLY · INSTALLATION_TEMPLATE",
      noteRo: "Sub-capacitate MOUNTING — nu chip sold.",
    },
    {
      moduleKey: "ambalare_livrare_montaj",
      labelRo: "ambalare_livrare_montaj",
      independenceRo: "LETTERS composition/logistics",
      noteRo: "Nu se activează din MOUNTING-only; nu chip sold.",
    },
    {
      moduleKey: "structura_suport",
      labelRo: "structura_suport",
      independenceRo: "SHARED_WITHIN_SIGNAGE",
      noteRo: "Reutilizare globală neprobată.",
    },
    {
      moduleKey: "geometry_svg",
      labelRo: "geometry_svg",
      independenceRo: "LETTERS_ONLY · prerequisite de calcul",
      noteRo: "Poartă de calcul — nu modul comercial sold.",
    },
  ],
  compositionDependencies: [
    {
      sourceRo: "RETURN-CANT",
      dependencyRo: "lipire față–cant (bonding)",
      classId: "COMPOSITION_ONLY",
      classLabelRo: "Doar în compoziție",
      meaningRo:
        "Bonding-ul nu este cerință standalone pentru RETURN-CANT. Este inclus numai în compoziția completă.",
    },
  ],
  settingsConflictVisible: true,
  showModularityLaw: true,
};

const LOGO_TRUTH: ProductModularityTruth = {
  templateCode: LOGO_TEMPLATE_CODE,
  commercialChipRo: "Candidat · rădăcină blocată",
  capabilityChipRo: "Copil legat",
  headlineRo: "Rădăcină blocată · Copil legat parțial · Independență neprobată",
  summaryChipsRo: ["Rădăcină blocată", "Copil legat parțial", "Independență neprobată"],
  axes: [
    { axis: "Existență", valueRo: "Înregistrat", testId: "modularity-axis-existence" },
    { axis: "Ofertabilitate rădăcină", valueRo: "Blocat ca rădăcină / neofertabil", testId: "modularity-axis-root" },
    { axis: "Maturitate runtime", valueRo: "Parțial (compunere legată)", testId: "modularity-axis-runtime" },
    { axis: "Stabilizare", valueRo: "Neînceput ca rădăcină", testId: "modularity-axis-stabilization" },
    { axis: "Rădăcină versus copil", valueRo: "Rădăcină blocată · copil legat parțial", testId: "modularity-axis-root-vs-child" },
    { axis: "Standalone", valueRo: "Neprobat ca produs independent", testId: "modularity-axis-standalone" },
    { axis: "Compoziție", valueRo: "Parțial ca linked-child sub Letters", testId: "modularity-axis-composition" },
    { axis: "Independență active-scope", valueRo: "Neprobată (în afara Slice 1)", testId: "modularity-axis-active-scope" },
    { axis: "Independență comercială", valueRo: "Nu ca rădăcină", testId: "modularity-axis-commercial" },
    { axis: "Independență execuție", valueRo: "Nu ca rădăcină", testId: "modularity-axis-execution" },
    { axis: "Module captive / amânate", valueRo: "Nu dovedesc root ofertabil", testId: "modularity-axis-captive" },
    { axis: "Ownership setări", valueRo: "MIXED / CONFLICTED pe căi legate", testId: "modularity-axis-settings" },
  ],
  modules: [
    {
      moduleKey: "LOGO-ROOT",
      labelRo: "Rădăcină Logo",
      independenceRo: "blocată · neofertabilă",
    },
    {
      moduleKey: "LOGO-LINKED",
      labelRo: "Copil legat",
      independenceRo: "parțial în compoziție",
      noteRo: "Prezența copilului legat nu dovedește independența rădăcinii Logo.",
    },
  ],
  falseGeneric: [],
  compositionDependencies: [
    {
      sourceRo: "Logo legat",
      dependencyRo: "Letters produs complet",
      classId: "COMPOSITION_ONLY",
      classLabelRo: "Doar în compoziție",
      meaningRo: "Linii Logo pot apărea în produsul complet Letters — nu ca root Logo ofertabil.",
    },
  ],
  settingsConflictVisible: true,
  showModularityLaw: true,
};

const ACM_BOXED_TRUTH: ProductModularityTruth = {
  templateCode: ACM_BOXED_TEMPLATE_CODE,
  commercialChipRo: "Montaj ACM · parțial",
  capabilityChipRo: "Copil legat / montaj",
  headlineRo: "Montaj ACM · parțial · Panou independent nepregătit · Casetat arhivat",
  summaryChipsRo: ["Montaj ACM · parțial", "Panou independent nepregătit", "Casetat arhivat"],
  axes: [
    { axis: "Existență", valueRo: "Înregistrat (montaj boxed)", testId: "modularity-axis-existence" },
    { axis: "Ofertabilitate rădăcină", valueRo: "Montaj / suport — nu panou independent", testId: "modularity-axis-root" },
    { axis: "Maturitate runtime", valueRo: "Parțial", testId: "modularity-axis-runtime" },
    { axis: "Stabilizare", valueRo: "Parțial pe calea boxed", testId: "modularity-axis-stabilization" },
    { axis: "Rădăcină versus copil", valueRo: "Suport boxed · poate fi copil sub Letters", testId: "modularity-axis-root-vs-child" },
    { axis: "Standalone", valueRo: "Parțial ca montaj — panou independent nepregătit", testId: "modularity-axis-standalone" },
    { axis: "Compoziție", valueRo: "Parțial sub Letters / mounting chain", testId: "modularity-axis-composition" },
    { axis: "Independență active-scope", valueRo: "Parțială (în afara Slice 1 Letters)", testId: "modularity-axis-active-scope" },
    { axis: "Independență comercială", valueRo: "Parțială pe montaj", testId: "modularity-axis-commercial" },
    { axis: "Independență execuție", valueRo: "Parțială", testId: "modularity-axis-execution" },
    { axis: "Module captive / amânate", valueRo: "Casetat arhivat · ACP light/cut arhivat", testId: "modularity-axis-captive" },
    { axis: "Ownership setări", valueRo: "MIXED — conflict vizibil, nerezolvat aici", testId: "modularity-axis-settings" },
  ],
  modules: [
    {
      moduleKey: "ACM-BOXED",
      labelRo: "Montaj ACM boxed",
      independenceRo: "parțial",
      noteRo: "Nu implică panou ACM independent pregătit.",
    },
    {
      moduleKey: "ACM-PANEL",
      labelRo: "Panou ACM independent",
      independenceRo: "nepregătit",
    },
    {
      moduleKey: "ACM-CASSETTE",
      labelRo: "Casetat ACM",
      independenceRo: "arhivat",
      noteRo: `${ACM_CASSETTE_TEMPLATE_CODE} rămâne arhivat.`,
    },
  ],
  falseGeneric: [],
  compositionDependencies: [
    {
      sourceRo: "Suport ACM / metal",
      dependencyRo: "soluție montaj / trigger",
      classId: "CONDITIONAL",
      classLabelRo: "Condițional",
      meaningRo: "Nu echivalează cu chip-ul sold MOUNTING pe Letters.",
    },
  ],
  settingsConflictVisible: true,
  showModularityLaw: true,
};

const BY_CODE: Record<string, ProductModularityTruth> = {
  [LETTERS_TEMPLATE_CODE]: LETTERS_TRUTH,
  [LOGO_TEMPLATE_CODE]: LOGO_TRUTH,
  [ACM_BOXED_TEMPLATE_CODE]: ACM_BOXED_TRUTH,
};

export function getProductModularityTruth(
  templateCode: string | null | undefined,
): ProductModularityTruth | null {
  if (!templateCode) return null;
  return BY_CODE[templateCode] ?? null;
}

export function commercialChipForTemplateCode(templateCode: string): string | null {
  return getProductModularityTruth(templateCode)?.commercialChipRo ?? null;
}

export function capabilityChipRoFromCapabilityLabel(
  capabilityLabel: string,
): string {
  if (capabilityLabel === "Standalone" || capabilityLabel === "Both") {
    return "De sine stătător";
  }
  if (capabilityLabel === "Linked child") {
    return "Copil legat";
  }
  return capabilityLabel;
}

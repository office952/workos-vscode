import { COMPONENT_FIRST_PRODUCT_TRUTH_MAPPING_CONTRACT } from "./componentFirstReadonlyProductTruthMapping";

export type OwnerInputStatus =
  | "confirmed"
  | "owner_input_required"
  | "assumption_not_allowed"
  | "blocked_until_owner_decision"
  | "derived_later";

export type TruthFieldAudience =
  | "operator"
  | "atelier"
  | "pricing"
  | "product_definition"
  | "execution"
  | "admin";

export type TruthFieldRequirement =
  | "required_for_pricing"
  | "required_for_product_definition"
  | "required_for_execution"
  | "optional"
  | "informational";

export type TruthPathSource = "confirmed_mapping" | "proposed_workshop";

export type ComponentTruthField = {
  fieldKey: string;
  labelRo: string;
  componentCode: string;
  truthPath: string;
  pathSource: TruthPathSource;
  audience: TruthFieldAudience[];
  requirement: TruthFieldRequirement[];
  inputType:
    | "select"
    | "text"
    | "number"
    | "boolean"
    | "money"
    | "unit_rate"
    | "formula_placeholder"
    | "owner_decision";
  unit?: "mm" | "ml" | "mp" | "buc" | "lei" | "eur" | "percent" | "none";
  allowedValues?: string[];
  visibleWhen?: string;
  defaultValue?: string | number | boolean | null;
  status: OwnerInputStatus;
  ownerQuestionRo?: string;
  notesRo: string;
  mustNotInvent: boolean;
};

export type ComponentTruthWorkshop = {
  componentCode: string;
  componentLabelRo: string;
  componentShortLabel: string;
  role: string;
  ownsTruthFor: string[];
  doesNotOwnTruthFor: string[];
  fields: ComponentTruthField[];
  ownerQuestions: string[];
  blockers: string[];
};

export type WorkshopGlobalStatus = "OWNER_INPUT_REQUIRED" | "PARTIAL_CONFIRMED" | "BLOCKED";

export type OwnerQuestionSeverity =
  | "required_before_pricing"
  | "required_before_product_definition"
  | "required_before_execution"
  | "optional_clarification";

export type OwnerQuestionExport = {
  componentCode: string;
  componentShortLabel: string;
  fieldKey: string | null;
  questionRo: string;
  severity: OwnerQuestionSeverity;
  status: OwnerInputStatus;
};

export type WorkshopSummary = {
  globalStatus: WorkshopGlobalStatus;
  confirmedFields: number;
  ownerInputRequiredFields: number;
  blockedFields: number;
  requiredBeforePricing: number;
  requiredBeforeProductDefinition: number;
  requiredBeforeExecution: number;
  totalFields: number;
};

const RETURN_CANT_CODE = "TPL-COMP-LETTER-RETURN-CANT_v1";
const FACE_CODE = "TPL-COMP-LETTER-FACE_v1";
const BACK_CODE = "TPL-COMP-LETTER-BACK_v1";
const LED_CODE = "TPL-COMP-LETTER-LED_v1";
const FINISH_CODE = "TPL-COMP-LETTER-FINISH_v1";
const MOUNTING_CODE = "TPL-COMP-LETTER-MOUNTING_v1";

export const FINISH_TYPE_VALUES = ["Culoare Stock", "Oracal", "Vopsit RAL"] as const;

function resolvePath(
  componentCode: string,
  fieldGroupHint: string,
  proposedPath: string,
): { truthPath: string; pathSource: TruthPathSource } {
  const byFieldGroup = COMPONENT_FIRST_PRODUCT_TRUTH_MAPPING_CONTRACT.find(
    (entry) => entry.templateCode === componentCode && entry.fieldGroup === fieldGroupHint,
  );
  if (byFieldGroup) {
    return { truthPath: byFieldGroup.futureProductTruthPath, pathSource: "confirmed_mapping" };
  }

  const byExactPath = COMPONENT_FIRST_PRODUCT_TRUTH_MAPPING_CONTRACT.find(
    (entry) => entry.templateCode === componentCode && entry.futureProductTruthPath === proposedPath,
  );
  if (byExactPath) {
    return { truthPath: byExactPath.futureProductTruthPath, pathSource: "confirmed_mapping" };
  }

  return { truthPath: proposedPath, pathSource: "proposed_workshop" };
}

function field(
  partial: Omit<ComponentTruthField, "pathSource" | "truthPath"> & {
    fieldGroupHint?: string;
    truthPath?: string;
  },
): ComponentTruthField {
  const proposed = partial.truthPath ?? `product.components.${partial.componentCode.split("-").pop()?.toLowerCase()}.${partial.fieldKey}`;
  const resolved = resolvePath(partial.componentCode, partial.fieldGroupHint ?? partial.fieldKey, proposed);
  const { fieldGroupHint: _fg, truthPath: _tp, ...rest } = partial;
  return {
    ...rest,
    truthPath: resolved.truthPath,
    pathSource: resolved.pathSource,
  };
}

export const RETURN_CANT_WORKSHOP_FIELDS: ComponentTruthField[] = [
  field({
    fieldKey: "finish_type",
    labelRo: "Tip finisaj cant",
    componentCode: RETURN_CANT_CODE,
    fieldGroupHint: "return_finish",
    truthPath: "product.components.return_cant.finish_type",
    audience: ["operator", "product_definition", "pricing", "atelier"],
    requirement: ["required_for_pricing", "required_for_product_definition"],
    inputType: "select",
    allowedValues: [...FINISH_TYPE_VALUES],
    status: "confirmed",
    notesRo: "Una dintre cele 3 variante universale: Culoare Stock, Oracal, Vopsit RAL.",
    mustNotInvent: false,
  }),
  field({
    fieldKey: "stock_color_note",
    labelRo: "Culoare stock dorită",
    componentCode: RETURN_CANT_CODE,
    truthPath: "product.components.return_cant.stock_color_note",
    visibleWhen: "finish_type = Culoare Stock",
    audience: ["operator", "atelier"],
    requirement: ["informational", "required_for_execution"],
    inputType: "text",
    status: "confirmed",
    notesRo:
      "Operatorul tastează culoarea pentru atelier. Nu presupune cost diferit fără confirmare owner.",
    mustNotInvent: false,
  }),
  field({
    fieldKey: "oracal_code",
    labelRo: "Cod Oracal",
    componentCode: RETURN_CANT_CODE,
    truthPath: "product.components.return_cant.oracal_code",
    visibleWhen: "finish_type = Oracal",
    audience: ["operator", "atelier", "pricing"],
    requirement: ["required_for_pricing"],
    inputType: "select",
    status: "owner_input_required",
    ownerQuestionRo: "Care coduri Oracal intră în catalogul complet? (mod selector listă completă confirmat)",
    notesRo:
      "Owner confirmat: selector listă completă Oracal + preț pe cod/familie. Catalog efectiv și tabel prețuri rămân de completat.",
    mustNotInvent: true,
  }),
  field({
    fieldKey: "ral_code",
    labelRo: "Cod RAL",
    componentCode: RETURN_CANT_CODE,
    truthPath: "product.components.return_cant.ral_code",
    visibleWhen: "finish_type = Vopsit RAL",
    audience: ["operator", "atelier", "pricing"],
    requirement: ["required_for_pricing"],
    inputType: "select",
    status: "owner_input_required",
    ownerQuestionRo: "Care este sursa/lista RAL pentru selector standard? (mod selector confirmat)",
    notesRo:
      "Owner confirmat: selector standard RAL. Sursa/lista efectivă rămâne de completat — fără tabel RAL inventat.",
    mustNotInvent: true,
  }),
  field({
    fieldKey: "return_depth_mm",
    labelRo: "Adâncime / volum cant",
    componentCode: RETURN_CANT_CODE,
    fieldGroupHint: "return_depth",
    truthPath: "product.components.return_cant.depth",
    audience: ["operator", "product_definition", "pricing", "execution"],
    requirement: ["required_for_product_definition", "required_for_pricing"],
    inputType: "number",
    unit: "mm",
    allowedValues: ["30", "60", "80", "100"],
    status: "confirmed",
    notesRo: "Owner confirmat: adâncimi standard 30 / 60 / 80 / 100 mm.",
    mustNotInvent: false,
  }),
  field({
    fieldKey: "return_material",
    labelRo: "Material cant",
    componentCode: RETURN_CANT_CODE,
    fieldGroupHint: "return_material",
    truthPath: "product.components.return_cant.material",
    audience: ["pricing", "product_definition", "atelier"],
    requirement: ["required_for_pricing"],
    inputType: "select",
    allowedValues: ["aluminiu 0.6 mm"],
    status: "confirmed",
    notesRo: "Owner confirmat: aluminiu 0.6 mm.",
    mustNotInvent: false,
  }),
  field({
    fieldKey: "return_material_unit",
    labelRo: "Unitate calcul material cant",
    componentCode: RETURN_CANT_CODE,
    truthPath: "product.components.return_cant.material_unit",
    audience: ["pricing", "product_definition", "admin"],
    requirement: ["required_for_pricing"],
    inputType: "owner_decision",
    allowedValues: ["ml", "mp", "buc", "set"],
    defaultValue: "ml",
    status: "confirmed",
    notesRo: "Owner confirmat: material cant pe ml.",
    mustNotInvent: false,
  }),
  field({
    fieldKey: "return_labor_unit",
    labelRo: "Unitate manoperă cant",
    componentCode: RETURN_CANT_CODE,
    truthPath: "product.components.return_cant.labor_unit",
    audience: ["pricing", "product_definition", "admin"],
    requirement: ["required_for_pricing"],
    inputType: "owner_decision",
    allowedValues: ["ml", "buc", "set", "mp"],
    defaultValue: "ml",
    status: "confirmed",
    notesRo: "Owner confirmat: manoperă cant pe ml.",
    mustNotInvent: false,
  }),
  field({
    fieldKey: "ral_material_price_rule",
    labelRo: "Regulă material Vopsit RAL",
    componentCode: RETURN_CANT_CODE,
    truthPath: "product.components.return_cant.ral_material_price_rule",
    visibleWhen: "finish_type = Vopsit RAL",
    audience: ["pricing", "admin"],
    requirement: ["required_for_pricing"],
    inputType: "formula_placeholder",
    unit: "ml",
    status: "owner_input_required",
    ownerQuestionRo: "Valori preț material Vopsit RAL pe adâncime? (unitate ml confirmată)",
    notesRo: "Unitate ml confirmată — fără prețuri material inventate.",
    mustNotInvent: true,
  }),
  field({
    fieldKey: "ral_labor_price_rule",
    labelRo: "Regulă manoperă Vopsit RAL",
    componentCode: RETURN_CANT_CODE,
    truthPath: "product.components.return_cant.ral_labor_price_rule",
    visibleWhen: "finish_type = Vopsit RAL",
    audience: ["pricing", "admin"],
    requirement: ["required_for_pricing"],
    inputType: "formula_placeholder",
    unit: "ml",
    status: "owner_input_required",
    ownerQuestionRo: "Valori preț manoperă și minim? (unitate ml confirmată)",
    notesRo: "Unitate ml confirmată — fără prețuri/formule manoperă inventate.",
    mustNotInvent: true,
  }),
  field({
    fieldKey: "separate_calculation_allowed",
    labelRo: "Calcul separat permis",
    componentCode: RETURN_CANT_CODE,
    truthPath: "product.components.return_cant.separate_calculation_allowed",
    audience: ["product_definition", "pricing", "admin"],
    requirement: ["required_for_product_definition"],
    inputType: "boolean",
    defaultValue: true,
    status: "confirmed",
    notesRo:
      "Componenta poate fi calculată separat doar dacă deține adevărul necesar. Adevărul stă pe componentă / Component Template / Product Truth component path, nu pe Product Template.",
    mustNotInvent: false,
  }),
  field({
    fieldKey: "pricing_status",
    labelRo: "Status pricing cant",
    componentCode: RETURN_CANT_CODE,
    truthPath: "product.components.return_cant.pricing_status",
    audience: ["pricing", "admin"],
    requirement: ["optional"],
    inputType: "owner_decision",
    status: "blocked_until_owner_decision",
    notesRo: "Pricing nu se activează în acest task. Doar identificăm ce lipsește.",
    mustNotInvent: true,
  }),
];

function skeletonWorkshop(
  componentCode: string,
  componentLabelRo: string,
  componentShortLabel: string,
  role: string,
  ownsTruthFor: string[],
  doesNotOwnTruthFor: string[],
  ownerQuestions: string[],
  blockers: string[],
): ComponentTruthWorkshop {
  return {
    componentCode,
    componentLabelRo,
    componentShortLabel,
    role,
    ownsTruthFor,
    doesNotOwnTruthFor,
    fields: [],
    ownerQuestions,
    blockers,
  };
}

export const COMPONENT_FIRST_LETTERS_PRODUCT_TRUTH_WORKSHOPS: ComponentTruthWorkshop[] = [
  {
    componentCode: RETURN_CANT_CODE,
    componentLabelRo: "Cant / return literă",
    componentShortLabel: "RETURN-CANT",
    role:
      "Componenta deține adevărul pentru cantul literei / grosimea volumului / finisajul cantului / material și manoperă de cant, acolo unde este calculabil separat.",
    ownsTruthFor: [
      "cant litere / grosime volum",
      "finisaj cant (Culoare Stock / Oracal / Vopsit RAL)",
      "material cant",
      "manoperă cant (separat de material)",
      "reguli RAL material + manoperă pe cant",
    ],
    doesNotOwnTruthFor: [
      "material față (FACE)",
      "decupare față / bounding (FACE)",
      "LED / iluminat (LED)",
      "montaj site (MOUNTING) — doar dacă owner confirmă separarea",
    ],
    fields: RETURN_CANT_WORKSHOP_FIELDS,
    ownerQuestions: RETURN_CANT_WORKSHOP_FIELDS.filter((f) => f.ownerQuestionRo).map(
      (f) => f.ownerQuestionRo!,
    ),
    blockers: [
      "Lista Oracal neconfirmată",
      "Reguli RAL material/manoperă neconfirmate",
      "Adâncimi standard cant neconfirmate",
      "Unități material/manoperă neconfirmate",
      "Pricing blocked — fără activare în acest task",
    ],
  },
  skeletonWorkshop(
    FACE_CODE,
    "Față literă",
    "FACE",
    "Componenta deține adevărul pentru material față, grosime, suprafață/bounding/cut path.",
    [
      "material față",
      "grosime față",
      "suprafață / bounding / cut path",
      "culoare/finisaj față dacă ține de față",
      "relație front vinyl/print — doar dacă owner confirmă",
    ],
    ["finisaj cant (RETURN-CANT)", "LED", "montaj (MOUNTING)"],
    [
      "Ce materiale față folosim standard: plexiglas 3mm, 5mm, 10mm, altceva?",
      "Grosimea se alege manual sau vine din template?",
      "Fața are folie/print separat sau se mută la FINISH?",
      "Decuparea se calculează pe bounding/nesting, nu pe arie — corect pentru materiale?",
    ],
    ["Skeleton only — câmpuri detaliate după RETURN-CANT"],
  ),
  skeletonWorkshop(
    BACK_CODE,
    "Spate literă",
    "BACK",
    "Componenta deține adevărul pentru material spate, grosime, backing/prindere.",
    [
      "material spate",
      "grosime spate",
      "backing / prindere",
      "găuri / distanțieri dacă țin de spate",
    ],
    ["cant (RETURN-CANT)", "montaj final (MOUNTING) — de clarificat"],
    [
      "Ce materiale spate folosim: Forex, PVC, plexi, ACP?",
      "Grosimi standard?",
      "Spatele este mereu separat de cant?",
      "Găurile de montaj țin de BACK sau MOUNTING?",
    ],
    ["Skeleton only — owner input pending"],
  ),
  skeletonWorkshop(
    LED_CODE,
    "Iluminat LED",
    "LED",
    "Componenta deține adevărul pentru tip LED, densitate, putere, sursă, wiring, consum.",
    [
      "tip LED",
      "densitate module",
      "putere per modul",
      "sursă alimentare",
      "wiring",
      "consum",
      "lumina front-lit/halo — dacă owner confirmă",
    ],
    ["material față/spate", "finisaj cant"],
    [
      "LED actual este 1.44W modul?",
      "Densitatea standard rămâne 50–60 module/mp sau altfel?",
      "Calculăm LED pe mp, pe contur, pe volum sau după regulă separată?",
      "Sursele sunt 60W / 100W / 200W?",
      "Există rezervă procentuală pentru sursă?",
    ],
    ["Skeleton only — densitate/putere neconfirmate în contract"],
  ),
  skeletonWorkshop(
    FINISH_CODE,
    "Finisaj vizual",
    "FINISH",
    "Componenta deține adevărul pentru folie, print, laminare, vopsire, finisaj vizual general.",
    ["folie", "print", "laminare", "vopsire", "finisaj vizual general"],
    ["finisaj cant RAL (RETURN-CANT) — overlap de clarificat", "material față brut (FACE)"],
    [
      "Ce rămâne la FINISH și ce rămâne la FACE/RETURN-CANT?",
      "Print + laminare se aplică pe față sau pe alte componente?",
      "Aplicare folie se calculează separat de material?",
      "Vopsirea RAL pe cant rămâne la RETURN-CANT sau la FINISH?",
    ],
    ["Overlap FINISH vs RETURN-CANT vs FACE — decizie owner"],
  ),
  skeletonWorkshop(
    MOUNTING_CODE,
    "Montaj / premount",
    "MOUNTING",
    "Componenta deține adevărul pentru montaj, șablon, distanțieri, dibluri, premount.",
    [
      "montaj",
      "șablon montaj",
      "distanțieri",
      "dibluri / șuruburi",
      "premount structure",
      "suport/structură dacă nu ține de alt produs",
    ],
    ["găuri spate (BACK) — de clarificat", "servicii montaj extern — de clarificat"],
    [
      "Montajul se calculează în Product System sau rămâne serviciu separat?",
      "Distanțierii țin de mounting sau backing?",
      "Există minim de montaj?",
      "Montaj extern București 200 EUR + TVA rămâne regulă validă?",
      "Structura premount se folosește când?",
    ],
    ["Skeleton only — reguli comerciale montaj neconfirmate"],
  ),
];

export function getWorkshopByComponentCode(code: string): ComponentTruthWorkshop | null {
  const normalized = code.trim().toUpperCase();
  return (
    COMPONENT_FIRST_LETTERS_PRODUCT_TRUTH_WORKSHOPS.find(
      (w) => w.componentCode.toUpperCase() === normalized,
    ) ?? null
  );
}

export function getWorkshopByShortLabel(label: string): ComponentTruthWorkshop | null {
  const normalized = label.trim().toUpperCase();
  return (
    COMPONENT_FIRST_LETTERS_PRODUCT_TRUTH_WORKSHOPS.find(
      (w) => w.componentShortLabel.toUpperCase() === normalized,
    ) ?? null
  );
}

function severityForField(field: ComponentTruthField): OwnerQuestionSeverity {
  if (field.requirement.includes("required_for_pricing")) return "required_before_pricing";
  if (field.requirement.includes("required_for_product_definition")) {
    return "required_before_product_definition";
  }
  if (field.requirement.includes("required_for_execution")) return "required_before_execution";
  return "optional_clarification";
}

export function exportOwnerQuestions(): OwnerQuestionExport[] {
  const exports: OwnerQuestionExport[] = [];

  for (const workshop of COMPONENT_FIRST_LETTERS_PRODUCT_TRUTH_WORKSHOPS) {
    for (const fieldEntry of workshop.fields) {
      if (fieldEntry.ownerQuestionRo) {
        exports.push({
          componentCode: workshop.componentCode,
          componentShortLabel: workshop.componentShortLabel,
          fieldKey: fieldEntry.fieldKey,
          questionRo: fieldEntry.ownerQuestionRo,
          severity: severityForField(fieldEntry),
          status: fieldEntry.status,
        });
      }
    }
    for (const question of workshop.ownerQuestions) {
      const alreadyFromField = workshop.fields.some((f) => f.ownerQuestionRo === question);
      if (!alreadyFromField) {
        exports.push({
          componentCode: workshop.componentCode,
          componentShortLabel: workshop.componentShortLabel,
          fieldKey: null,
          questionRo: question,
          severity: "optional_clarification",
          status: "owner_input_required",
        });
      }
    }
  }

  return exports;
}

export function groupOwnerQuestionsBySeverity(): Record<OwnerQuestionSeverity, OwnerQuestionExport[]> {
  const all = exportOwnerQuestions();
  return {
    required_before_pricing: all.filter((q) => q.severity === "required_before_pricing"),
    required_before_product_definition: all.filter(
      (q) => q.severity === "required_before_product_definition",
    ),
    required_before_execution: all.filter((q) => q.severity === "required_before_execution"),
    optional_clarification: all.filter((q) => q.severity === "optional_clarification"),
  };
}

export function groupOwnerQuestionsByStatus(): Record<OwnerInputStatus, OwnerQuestionExport[]> {
  const all = exportOwnerQuestions();
  const buckets: Record<OwnerInputStatus, OwnerQuestionExport[]> = {
    confirmed: [],
    owner_input_required: [],
    assumption_not_allowed: [],
    blocked_until_owner_decision: [],
    derived_later: [],
  };
  for (const q of all) {
    buckets[q.status].push(q);
  }
  return buckets;
}

export function buildWorkshopSummary(
  workshops: ComponentTruthWorkshop[] = COMPONENT_FIRST_LETTERS_PRODUCT_TRUTH_WORKSHOPS,
): WorkshopSummary {
  const allFields = workshops.flatMap((w) => w.fields);
  const confirmedFields = allFields.filter((f) => f.status === "confirmed").length;
  const ownerInputRequiredFields = allFields.filter((f) => f.status === "owner_input_required").length;
  const blockedFields = allFields.filter(
    (f) => f.status === "blocked_until_owner_decision" || f.status === "assumption_not_allowed",
  ).length;

  const requiredBeforePricing = allFields.filter((f) =>
    f.requirement.includes("required_for_pricing"),
  ).length;
  const requiredBeforeProductDefinition = allFields.filter((f) =>
    f.requirement.includes("required_for_product_definition"),
  ).length;
  const requiredBeforeExecution = allFields.filter((f) =>
    f.requirement.includes("required_for_execution"),
  ).length;

  const hasBlocked = blockedFields > 0 || ownerInputRequiredFields > 0;
  const globalStatus: WorkshopGlobalStatus = hasBlocked ? "OWNER_INPUT_REQUIRED" : "PARTIAL_CONFIRMED";

  return {
    globalStatus,
    confirmedFields,
    ownerInputRequiredFields,
    blockedFields,
    requiredBeforePricing,
    requiredBeforeProductDefinition,
    requiredBeforeExecution,
    totalFields: allFields.length,
  };
}

export function ownerInputStatusLabel(status: OwnerInputStatus): string {
  switch (status) {
    case "confirmed":
      return "CONFIRMED";
    case "owner_input_required":
      return "OWNER INPUT";
    case "assumption_not_allowed":
      return "NO ASSUMPTION";
    case "blocked_until_owner_decision":
      return "BLOCKED";
    case "derived_later":
      return "DERIVED LATER";
    default:
      return status.toUpperCase();
  }
}

export function pathSourceLabel(source: TruthPathSource): string {
  return source === "confirmed_mapping" ? "mapping contract" : "proposed workshop";
}

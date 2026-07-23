/**
 * Letters FINISH / MOUNTING ownership + runtime decoupling contract (V1).
 * Documents precise responsibilities. Sold FINISH/MOUNTING chips remain deferred.
 */

export type OwnershipOwnerToken =
  | "PLATFORM"
  | "COMPANY"
  | "PRODUCT_FAMILY"
  | "PRODUCT_TEMPLATE"
  | "COMPONENT"
  | "MODULE"
  | "WORKSPACE"
  | "DERIVED"
  | "COMMERCIAL"
  | "EXECUTION";

export type OwnershipRuntimeStatus =
  | "CURRENT"
  | "TARGET"
  | "COMPATIBILITY_ALIAS"
  | "LEGACY"
  | "BLOCKED";

export type OwnershipValueLayer =
  | "intent"
  | "workspace_value"
  | "derived"
  | "commercial_authority"
  | "execution_requirement"
  | "catalog_conflict"
  | "runtime_bucket";

export type OwnershipResponsibility =
  | "SURFACE_FINISH"
  | "INSTALLATION_TEMPLATE"
  | "PACKAGING_LOGISTICS"
  | "STRUCTURE_SUPPORT"
  | "LEGACY_ALIAS"
  | "SOLD_DEFERRED";

export type OwnershipSettingRecord = {
  id: string;
  fieldKey: string;
  labelRo: string;
  domain: "FINISH" | "MOUNTING" | "LOGISTICS" | "SHARED";
  responsibility: OwnershipResponsibility;
  canonical_owner: OwnershipOwnerToken;
  ownerDetailRo: string;
  value_layer: OwnershipValueLayer;
  runtime_status: OwnershipRuntimeStatus;
  compatibility_status: OwnershipRuntimeStatus;
  current_or_target: "CURRENT" | "TARGET";
  consumers: readonly string[];
  activation_gate: string;
  noteRo: string;
};

export type OwnershipOwnerGateId =
  | "MOUNTING_MAP_NARROWING_OWNER_GATE"
  | "MINI_MODULE_SPLIT_OWNER_GATE"
  | "SOLD_CHIP_ACTIVATION_OWNER_GATE"
  | "PACKAGING_SOLD_CHIP";

export const LETTERS_OWNERSHIP_OWNER_GATES: readonly {
  id: OwnershipOwnerGateId;
  status: "APPROVED" | "NOT_APPROVED" | "NOT_PLANNED";
  labelRo: string;
  meaningRo: string;
}[] = [
  {
    id: "MOUNTING_MAP_NARROWING_OWNER_GATE",
    status: "APPROVED",
    labelRo: "Îngustare mapă MOUNTING",
    meaningRo:
      "MOUNTING → {structura_suport, sablon_montaj}. Fără finisaje suprafață. Fără ambalare automată.",
  },
  {
    id: "MINI_MODULE_SPLIT_OWNER_GATE",
    status: "APPROVED",
    labelRo: "Separare responsabilități finisaje",
    meaningRo:
      "finisaje = suprafață; sablon_montaj = șablon; ambalare_livrare_montaj = logistică. Modulul finisaje rămâne.",
  },
  {
    id: "SOLD_CHIP_ACTIVATION_OWNER_GATE",
    status: "NOT_APPROVED",
    labelRo: "Activare chip-uri sold",
    meaningRo: "FINISH și MOUNTING rămân amânate — fără chip-uri ofertabile.",
  },
  {
    id: "PACKAGING_SOLD_CHIP",
    status: "NOT_PLANNED",
    labelRo: "Chip sold ambalare",
    meaningRo: "Ambalarea este responsabilitate de compoziție / logistică — nu modul vândut.",
  },
] as const;

export const FINISH_MOUNTING_OWNERSHIP_LAW_RO = [
  "NU SCOATEM NIMIC DIN PRODUS.",
  "FINISH RĂMÂNE FINISH. ȘABLONUL DEVINE ȘABLON. AMBALAREA DEVINE LOGISTICĂ.",
  "VECHILE SNAPSHOTURI RĂMÂN CITIBILE. NOILE SNAPSHOTURI DEVIN PRECISE.",
  "HIDDEN DEFAULT ≠ RESPONSABILITATE ACTIVĂ.",
] as const;

export const RUNTIME_RESPONSIBILITY_CODES = {
  surfaceFinish: "finisaje",
  installationTemplate: "sablon_montaj",
  packaging: "ambalare_livrare_montaj",
  support: "structura_suport",
} as const;

export const MOUNTING_RUNTIME_MAP_NARROWED = ["structura_suport", "sablon_montaj"] as const;
export const FINISH_RUNTIME_MAP = ["finisaje"] as const;
export const LEGACY_FINISAJE_ALIAS_CODES = [
  "finisaje",
  "sablon_montaj",
  "ambalare_livrare_montaj",
] as const;

export const SNAPSHOT_WRITER_VERSION = "active_scope_snapshot/v2";
export const SNAPSHOT_LEGACY_VERSION = "active_scope_snapshot/v1";

/** Canonical mounting field model (persisted names). */
export const MOUNTING_FIELD_MODEL_V1 = {
  mounting_scope: {
    role: "canonical_commercial_prep_intent" as const,
    status: "CURRENT" as const,
    labelRo: "Intent comercial pregătire / montaj site",
  },
  mounting_system: {
    role: "canonical_mounting_method" as const,
    status: "CURRENT" as const,
    labelRo: "Metodă de montaj (câmp canonic V1)",
  },
  mounting_solution: {
    role: "canonical_support_composition" as const,
    status: "CURRENT" as const,
    labelRo: "Compoziție suport tehnic (Product System)",
  },
  metal_support_required: {
    role: "derived_compatibility_alias" as const,
    status: "COMPATIBILITY_ALIAS" as const,
    labelRo: "Alias derivat — nu autoritate independentă",
  },
  mounting_method: {
    role: "target_future_name_only" as const,
    status: "TARGET" as const,
    labelRo: "Nume țintă viitor pentru mounting_system — nu câmp persistat separat în V1",
  },
} as const;

export const BAR_MOUNTING_METHODS = ["steel_bars", "aluminum_bars"] as const;

export type MountingSupportContradictionInput = {
  mounting_system?: string | null;
  mounting_solution?: { kind?: string | null; template_code?: string | null } | null | unknown;
  metal_support_required?: boolean | null;
};

export type OwnershipDiagnostic = {
  code: string;
  severity: "compatibility_warning";
  messageRo: string;
  canonicalWins: true;
};

function hasSupportSolution(solution: MountingSupportContradictionInput["mounting_solution"]): boolean {
  if (!solution || typeof solution !== "object") return false;
  const record = solution as { kind?: unknown; template_code?: unknown; product_system_template?: unknown };
  if (typeof record.template_code === "string" && record.template_code.trim()) return true;
  if (typeof record.product_system_template === "string" && record.product_system_template.trim()) {
    return true;
  }
  if (record.kind === "product_system_template" || record.kind === "installation_template") {
    return true;
  }
  return Object.keys(record).length > 0;
}

function methodImpliesBars(mountingSystem: string | null | undefined): boolean {
  if (!mountingSystem) return false;
  return (BAR_MOUNTING_METHODS as readonly string[]).includes(mountingSystem);
}

export function diagnoseMountingOwnershipConflicts(
  input: MountingSupportContradictionInput,
): OwnershipDiagnostic[] {
  const diagnostics: OwnershipDiagnostic[] = [];
  const alias = input.metal_support_required;
  const method = input.mounting_system ?? null;
  const solutionPresent = hasSupportSolution(input.mounting_solution);
  const bars = methodImpliesBars(method);

  if (alias === true && !solutionPresent && !bars && method === "direct_wall") {
    diagnostics.push({
      code: "MOUNTING_ALIAS_TRUE_WITHOUT_SUPPORT_INTENT",
      severity: "compatibility_warning",
      messageRo:
        "Alias metal_support_required=true, dar metoda canonică este direct_wall și nu există mounting_solution. Aliasul nu redefinește intentul canonic.",
      canonicalWins: true,
    });
  }

  if (alias === false && (solutionPresent || bars)) {
    diagnostics.push({
      code: "MOUNTING_ALIAS_FALSE_WITH_SUPPORT_INTENT",
      severity: "compatibility_warning",
      messageRo:
        "Alias metal_support_required=false, dar câmpurile canonice implică suport. Se respectă mounting_solution / mounting_system; aliasul este doar compatibilitate.",
      canonicalWins: true,
    });
  }

  if (bars && solutionPresent) {
    const solution = input.mounting_solution as { kind?: string } | null;
    if (solution?.kind === "installation_template") {
      diagnostics.push({
        code: "MOUNTING_METHOD_BARS_VS_INSTALLATION_SOLUTION",
        severity: "compatibility_warning",
        messageRo:
          "mounting_system implică bare, iar mounting_solution este installation_template. Verificați intentul — câmpurile canonice rămân sursa de adevăr.",
        canonicalWins: true,
      });
    }
  }

  return diagnostics;
}

export function deriveMetalSupportRequiredAlias(
  input: Pick<MountingSupportContradictionInput, "mounting_system" | "mounting_solution">,
): boolean | null {
  if (hasSupportSolution(input.mounting_solution)) return true;
  if (methodImpliesBars(input.mounting_system)) return true;
  if (input.mounting_system === "direct_wall") return false;
  if (!input.mounting_system && !hasSupportSolution(input.mounting_solution)) return null;
  return false;
}

export const FINISH_OWNERSHIP_SETTINGS: readonly OwnershipSettingRecord[] = [
  {
    id: "finish.sold_module",
    fieldKey: "FINISH",
    labelRo: "Chip sold FINISH",
    domain: "FINISH",
    responsibility: "SOLD_DEFERRED",
    canonical_owner: "PRODUCT_TEMPLATE",
    ownerDetailRo: "Sold module amânat (SLICE1_DEFERRED)",
    value_layer: "runtime_bucket",
    runtime_status: "BLOCKED",
    compatibility_status: "BLOCKED",
    current_or_target: "CURRENT",
    consumers: ["offer_scope", "Intake V6 (absent chip)"],
    activation_gate: "SOLD_CHIP_ACTIVATION_OWNER_GATE",
    noteRo: "Activare neaprobată. Captiv / amânat.",
  },
  {
    id: "finish.runtime_surface",
    fieldKey: "finisaje",
    labelRo: "Finisaj suprafață (runtime)",
    domain: "FINISH",
    responsibility: "SURFACE_FINISH",
    canonical_owner: "MODULE",
    ownerDetailRo: "Responsabilitate SURFACE_FINISH — vinyl / print / vopsire / protecție",
    value_layer: "runtime_bucket",
    runtime_status: "CURRENT",
    compatibility_status: "CURRENT",
    current_or_target: "CURRENT",
    consumers: ["ProductDefinition", "Aggregate", "CPP"],
    activation_gate: "none",
    noteRo: "Modulul finisaje rămâne. Nu mai deține șablonul sau ambalarea pe snapshoturi noi.",
  },
  {
    id: "finish.legacy_alias",
    fieldKey: "legacy_finisaje_aggregate_alias",
    labelRo: "Alias agregat legacy finisaje",
    domain: "SHARED",
    responsibility: "LEGACY_ALIAS",
    canonical_owner: "MODULE",
    ownerDetailRo: "Doar pentru snapshoturi vechi (v1) — citire, nu rescriere",
    value_layer: "runtime_bucket",
    runtime_status: "LEGACY",
    compatibility_status: "COMPATIBILITY_ALIAS",
    current_or_target: "CURRENT",
    consumers: ["Execution sold-scope reader", "active_scope_snapshot/v1"],
    activation_gate: "none",
    noteRo: "Alias agregat legacy pentru snapshoturi vechi. Nu este modelul canonic curent.",
  },
  {
    id: "finish.face_intent",
    fieldKey: "face_finish_type",
    labelRo: "Intent finisaj față (vinyl/print)",
    domain: "FINISH",
    responsibility: "SURFACE_FINISH",
    canonical_owner: "MODULE",
    ownerDetailRo: "Proprietar: modul FINISH (finisaje)",
    value_layer: "intent",
    runtime_status: "CURRENT",
    compatibility_status: "CURRENT",
    current_or_target: "CURRENT",
    consumers: ["Intake finish_setup", "form contract", "PD"],
    activation_gate: "none",
    noteRo: "FINISH surface — nu RETURN-CANT.",
  },
  {
    id: "finish.face_workspace",
    fieldKey: "letter_group_finishes.face_*",
    labelRo: "Valoare concretă finisaj față",
    domain: "FINISH",
    responsibility: "SURFACE_FINISH",
    canonical_owner: "WORKSPACE",
    ownerDetailRo: "Selecție proiect în finish_setup",
    value_layer: "workspace_value",
    runtime_status: "CURRENT",
    compatibility_status: "CURRENT",
    current_or_target: "CURRENT",
    consumers: ["Intake V6", "PD facts"],
    activation_gate: "none",
    noteRo: "WORKSPACE deține valorile concrete selectate.",
  },
  {
    id: "finish.return_oracal_ral",
    fieldKey: "return_finish_type",
    labelRo: "Oracal / RAL cant",
    domain: "FINISH",
    responsibility: "SURFACE_FINISH",
    canonical_owner: "COMPONENT",
    ownerDetailRo: "RETURN-CANT component",
    value_layer: "workspace_value",
    runtime_status: "CURRENT",
    compatibility_status: "CURRENT",
    current_or_target: "CURRENT",
    consumers: ["Intake", "modelare_cant", "PD"],
    activation_gate: "none",
    noteRo: "Nu este ownership FINISH surface — rămâne la RETURN-CANT.",
  },
  {
    id: "finish.catalogs",
    fieldKey: "face_finish_catalogs",
    labelRo: "Cataloage finisaj față",
    domain: "FINISH",
    responsibility: "SURFACE_FINISH",
    canonical_owner: "MODULE",
    ownerDetailRo: "SoT sub responsabilitatea SURFACE_FINISH",
    value_layer: "catalog_conflict",
    runtime_status: "CURRENT",
    compatibility_status: "LEGACY",
    current_or_target: "CURRENT",
    consumers: ["form contract", "FE option maps", "dossier"],
    activation_gate: "none",
    noteRo: "Cataloagele rămân; nu se elimină opțiuni de finisaj.",
  },
  {
    id: "finish.derived_area",
    fieldKey: "finish_coverage_measurements",
    labelRo: "Arii paint/foil/print",
    domain: "FINISH",
    responsibility: "SURFACE_FINISH",
    canonical_owner: "DERIVED",
    ownerDetailRo: "ProductAggregate measurements",
    value_layer: "derived",
    runtime_status: "CURRENT",
    compatibility_status: "CURRENT",
    current_or_target: "CURRENT",
    consumers: ["Aggregate", "CPP commercial_measurements"],
    activation_gate: "none",
    noteRo: "DERIVED — nu preț. CPP consumă măsurători; Registry deține tarife.",
  },
  {
    id: "finish.cpp_money",
    fieldKey: "cpp_7g",
    labelRo: "Autoritate bani finisaj",
    domain: "FINISH",
    responsibility: "SURFACE_FINISH",
    canonical_owner: "COMMERCIAL",
    ownerDetailRo: "CPP 7G (+ Pricing Registry tarife)",
    value_layer: "commercial_authority",
    runtime_status: "CURRENT",
    compatibility_status: "CURRENT",
    current_or_target: "CURRENT",
    consumers: ["CPP 7G", "/inventory/pricing"],
    activation_gate: "none",
    noteRo: "Nu CostEngine. Nu minute ca preț.",
  },
  {
    id: "finish.execution",
    fieldKey: "painting_vinyl_print_ops",
    labelRo: "Cerințe execuție finisaj suprafață",
    domain: "FINISH",
    responsibility: "SURFACE_FINISH",
    canonical_owner: "EXECUTION",
    ownerDetailRo: "finisaje / Execution (precis pe snapshot v2)",
    value_layer: "execution_requirement",
    runtime_status: "CURRENT",
    compatibility_status: "CURRENT",
    current_or_target: "CURRENT",
    consumers: ["ExecutionPlan preview"],
    activation_gate: "none",
    noteRo: "Fără materializare task. Operații de suprafață doar sub finisaje.",
  },
] as const;

export const INSTALLATION_TEMPLATE_OWNERSHIP_SETTINGS: readonly OwnershipSettingRecord[] = [
  {
    id: "template.runtime",
    fieldKey: "sablon_montaj",
    labelRo: "Șablon montaj (runtime)",
    domain: "MOUNTING",
    responsibility: "INSTALLATION_TEMPLATE",
    canonical_owner: "MODULE",
    ownerDetailRo: "Responsabilitate INSTALLATION_TEMPLATE — sub-capacitate MOUNTING",
    value_layer: "runtime_bucket",
    runtime_status: "CURRENT",
    compatibility_status: "CURRENT",
    current_or_target: "CURRENT",
    consumers: ["ProductDefinition", "Aggregate", "CPP", "Execution"],
    activation_gate: "none",
    noteRo: "Activ doar când mounting_template_enabled. Nu cere finisaj suprafață.",
  },
  {
    id: "template.enabled",
    fieldKey: "mounting_template_enabled",
    labelRo: "Activare șablon montaj",
    domain: "MOUNTING",
    responsibility: "INSTALLATION_TEMPLATE",
    canonical_owner: "WORKSPACE",
    ownerDetailRo: "Intent workspace — nu finisaj suprafață",
    value_layer: "intent",
    runtime_status: "CURRENT",
    compatibility_status: "CURRENT",
    current_or_target: "CURRENT",
    consumers: ["Intake", "form contract", "PD"],
    activation_gate: "none",
    noteRo: "INSTALLATION TEMPLATE ≠ SURFACE FINISH.",
  },
] as const;

export const PACKAGING_OWNERSHIP_SETTINGS: readonly OwnershipSettingRecord[] = [
  {
    id: "packaging.runtime",
    fieldKey: "ambalare_livrare_montaj",
    labelRo: "Ambalare / logistică (runtime)",
    domain: "LOGISTICS",
    responsibility: "PACKAGING_LOGISTICS",
    canonical_owner: "PRODUCT_TEMPLATE",
    ownerDetailRo: "Responsabilitate de compoziție / logistică — nu modul sold",
    value_layer: "runtime_bucket",
    runtime_status: "CURRENT",
    compatibility_status: "CURRENT",
    current_or_target: "CURRENT",
    consumers: ["Full Letters composition", "Aggregate", "CPP"],
    activation_gate: "PACKAGING_SOLD_CHIP",
    noteRo: "Nu se activează din MOUNTING-only. Full Letters poate activa explicit prin compoziție.",
  },
] as const;

export const MOUNTING_OWNERSHIP_SETTINGS: readonly OwnershipSettingRecord[] = [
  {
    id: "mounting.sold_module",
    fieldKey: "MOUNTING",
    labelRo: "Chip sold MOUNTING",
    domain: "MOUNTING",
    responsibility: "SOLD_DEFERRED",
    canonical_owner: "PRODUCT_TEMPLATE",
    ownerDetailRo: "Sold module blocat / amânat",
    value_layer: "runtime_bucket",
    runtime_status: "BLOCKED",
    compatibility_status: "BLOCKED",
    current_or_target: "CURRENT",
    consumers: ["offer_scope"],
    activation_gate: "SOLD_CHIP_ACTIVATION_OWNER_GATE",
    noteRo: "Modul vândut: blocat. Activare neaprobată.",
  },
  {
    id: "mounting.scope",
    fieldKey: "mounting_scope",
    labelRo: "Scope montaj",
    domain: "MOUNTING",
    responsibility: "STRUCTURE_SUPPORT",
    canonical_owner: "WORKSPACE",
    ownerDetailRo: "Intent comercial pregătire / site",
    value_layer: "intent",
    runtime_status: "CURRENT",
    compatibility_status: "CURRENT",
    current_or_target: "CURRENT",
    consumers: ["Intake V6", "commercial prep"],
    activation_gate: "none",
    noteRo: "Câmp canonic V1 pentru intent comercial.",
  },
  {
    id: "mounting.system",
    fieldKey: "mounting_system",
    labelRo: "Metodă montaj",
    domain: "MOUNTING",
    responsibility: "STRUCTURE_SUPPORT",
    canonical_owner: "WORKSPACE",
    ownerDetailRo: "Câmp metodă canonic V1",
    value_layer: "workspace_value",
    runtime_status: "CURRENT",
    compatibility_status: "CURRENT",
    current_or_target: "CURRENT",
    consumers: ["Intake", "PD legacy bridge", "FE preview"],
    activation_gate: "none",
    noteRo: "mounting_method este doar nume țintă viitor — nu al doilea câmp persistat.",
  },
  {
    id: "mounting.solution",
    fieldKey: "mounting_solution",
    labelRo: "Soluție suport",
    domain: "MOUNTING",
    responsibility: "STRUCTURE_SUPPORT",
    canonical_owner: "WORKSPACE",
    ownerDetailRo: "Compoziție tehnică → Module produs (child Product Template)",
    value_layer: "workspace_value",
    runtime_status: "CURRENT",
    compatibility_status: "CURRENT",
    current_or_target: "CURRENT",
    consumers: ["Intake", "PD composition", "structura_suport"],
    activation_gate: "none",
    noteRo: "Suport legat: parțial (premount / ACM boxed). Nu panou independent.",
  },
  {
    id: "mounting.alias",
    fieldKey: "metal_support_required",
    labelRo: "Alias metal_support_required",
    domain: "MOUNTING",
    responsibility: "LEGACY_ALIAS",
    canonical_owner: "DERIVED",
    ownerDetailRo: "COMPATIBILITY_ALIAS derivat",
    value_layer: "derived",
    runtime_status: "COMPATIBILITY_ALIAS",
    compatibility_status: "COMPATIBILITY_ALIAS",
    current_or_target: "CURRENT",
    consumers: ["quote_input", "module_link trigger (legacy DB)"],
    activation_gate: "none",
    noteRo: "Nu este autoritate. Contradicțiile → compatibility_warning.",
  },
  {
    id: "mounting.method_target_name",
    fieldKey: "mounting_method",
    labelRo: "Nume țintă mounting_method",
    domain: "MOUNTING",
    responsibility: "STRUCTURE_SUPPORT",
    canonical_owner: "WORKSPACE",
    ownerDetailRo: "TARGET FUTURE NAME ONLY",
    value_layer: "intent",
    runtime_status: "TARGET",
    compatibility_status: "TARGET",
    current_or_target: "TARGET",
    consumers: ["documentation", "UI labels marked TARGET"],
    activation_gate: "none",
    noteRo: "Nu introduceți un al doilea câmp persistat în V1.",
  },
  {
    id: "mounting.runtime_map",
    fieldKey: "MOUNTING→runtime",
    labelRo: "Mapă runtime MOUNTING (îngustată)",
    domain: "MOUNTING",
    responsibility: "STRUCTURE_SUPPORT",
    canonical_owner: "PRODUCT_TEMPLATE",
    ownerDetailRo: "{structura_suport, sablon_montaj}",
    value_layer: "runtime_bucket",
    runtime_status: "CURRENT",
    compatibility_status: "CURRENT",
    current_or_target: "CURRENT",
    consumers: ["offer_scope_canonical_map"],
    activation_gate: "MOUNTING_MAP_NARROWING_OWNER_GATE",
    noteRo: "Fără finisaje. Fără ambalare_livrare_montaj. Gate îngustare: APROBAT.",
  },
  {
    id: "mounting.support_runtime",
    fieldKey: "structura_suport",
    labelRo: "Structură suport (runtime)",
    domain: "MOUNTING",
    responsibility: "STRUCTURE_SUPPORT",
    canonical_owner: "MODULE",
    ownerDetailRo: "Responsabilitate STRUCTURE_SUPPORT",
    value_layer: "runtime_bucket",
    runtime_status: "CURRENT",
    compatibility_status: "CURRENT",
    current_or_target: "CURRENT",
    consumers: ["ProductDefinition", "Aggregate", "CPP"],
    activation_gate: "none",
    noteRo: "Bare / panou / hardware — separat de șablon și de finisaj suprafață.",
  },
] as const;

export const ALL_FINISH_MOUNTING_OWNERSHIP_SETTINGS: readonly OwnershipSettingRecord[] = [
  ...FINISH_OWNERSHIP_SETTINGS,
  ...INSTALLATION_TEMPLATE_OWNERSHIP_SETTINGS,
  ...PACKAGING_OWNERSHIP_SETTINGS,
  ...MOUNTING_OWNERSHIP_SETTINGS,
];

export function ownershipRowsByResponsibility(
  responsibility: OwnershipResponsibility,
): OwnershipSettingRecord[] {
  return ALL_FINISH_MOUNTING_OWNERSHIP_SETTINGS.filter((r) => r.responsibility === responsibility);
}

export function ownershipStatusBadgeRo(status: OwnershipRuntimeStatus): string {
  return ownershipStatusLabelRo(status);
}

export function ownershipStatusLabelRo(status: OwnershipRuntimeStatus): string {
  switch (status) {
    case "CURRENT":
      return "CURRENT";
    case "TARGET":
      return "TARGET";
    case "COMPATIBILITY_ALIAS":
      return "COMPATIBILITY_ALIAS";
    case "LEGACY":
      return "LEGACY";
    case "BLOCKED":
      return "BLOCKED";
    default:
      return status;
  }
}

export const FINISH_OWNERSHIP_SUMMARY_RO = {
  soldStatusRo: "Captiv / amânat · Activare neaprobată",
  targetOwnerRo: "Responsabilitate curentă: finisaje = SURFACE_FINISH",
  catalogsRo: "Opțiuni finisaj păstrate — niciuna eliminată",
  runtimeBucketRo: "finisaje îngustat · șablon/ambalare separate",
} as const;

export const MOUNTING_OWNERSHIP_SUMMARY_RO = {
  linkedSupportRo: "Suport: structura_suport",
  soldStatusRo: "Modul vândut: blocat",
  methodFieldRo: "Câmp metodă curent: mounting_system",
  solutionFieldRo: "Soluție suport: mounting_solution",
  aliasFieldRo: "Alias compatibilitate: metal_support_required",
  mapGateRo: "Mapă îngustată: {structura_suport, sablon_montaj}",
} as const;

export const TEMPLATE_OWNERSHIP_SUMMARY_RO = {
  runtimeCodeRo: "sablon_montaj",
  roleRo: "Sub-capacitate MOUNTING / INSTALLATION_TEMPLATE",
  inactiveRo: "Inactiv → fără materiale, linii, operații, avertismente șablon",
} as const;

export const PACKAGING_OWNERSHIP_SUMMARY_RO = {
  runtimeCodeRo: "ambalare_livrare_montaj",
  roleRo: "Compoziție / logistică — nu chip sold",
  mountingLeakRo: "Nu se activează din MOUNTING-only",
} as const;

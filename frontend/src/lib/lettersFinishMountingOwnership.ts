/**
 * Letters FINISH / MOUNTING settings ownership contract (V1).
 * Metadata + diagnostics only — does not change sold scope, Aggregate, CPP, or Execution.
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

export type OwnershipSettingRecord = {
  id: string;
  fieldKey: string;
  labelRo: string;
  domain: "FINISH" | "MOUNTING" | "SHARED";
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
  | "SOLD_CHIP_ACTIVATION_OWNER_GATE";

export const LETTERS_OWNERSHIP_OWNER_GATES: readonly {
  id: OwnershipOwnerGateId;
  status: "NOT_APPROVED";
  labelRo: string;
  meaningRo: string;
}[] = [
  {
    id: "MOUNTING_MAP_NARROWING_OWNER_GATE",
    status: "NOT_APPROVED",
    labelRo: "Îngustare mapă MOUNTING",
    meaningRo:
      "Nu se schimbă MOUNTING → {structura_suport, finisaje}. Maparea runtime rămâne neschimbată.",
  },
  {
    id: "MINI_MODULE_SPLIT_OWNER_GATE",
    status: "NOT_APPROVED",
    labelRo: "Separare modul finisaje",
    meaningRo:
      "Nu se împarte finisaje în coduri registry noi. Bucket-ul mixt rămâne documentat, nu remediat.",
  },
  {
    id: "SOLD_CHIP_ACTIVATION_OWNER_GATE",
    status: "NOT_APPROVED",
    labelRo: "Activare chip-uri sold",
    meaningRo: "FINISH și MOUNTING rămân amânate — fără chip-uri ofertabile.",
  },
] as const;

export const FINISH_MOUNTING_OWNERSHIP_LAW_RO = [
  "CONTRACTELE ÎNTÂI. ACTIVAREA MAI TÂRZIU.",
  "HIDDEN DEFAULT ≠ SOLD MODULE.",
  "UI TRUTH MUST MATCH CONTRACT TRUTH.",
] as const;

/** Canonical mounting field model for V1 (persisted names). */
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
  /** Canonical method field (V1 persisted). */
  mounting_system?: string | null;
  /** Canonical support composition. */
  mounting_solution?: { kind?: string | null; template_code?: string | null } | null | unknown;
  /** Compatibility alias — never authoritative. */
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

/**
 * Pure diagnostics — does not rewrite values or change runtime activation.
 * Canonical current fields win; alias never silently becomes canonical.
 */
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

/** Derive expected alias from canonical fields — documentation/helper only. */
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
    id: "finish.runtime_bucket",
    fieldKey: "finisaje",
    labelRo: "Bucket runtime finisaje",
    domain: "FINISH",
    canonical_owner: "MODULE",
    ownerDetailRo: "Mixt (suprafață + șablon + ambalare) — neschimbat în V1",
    value_layer: "runtime_bucket",
    runtime_status: "CURRENT",
    compatibility_status: "LEGACY",
    current_or_target: "CURRENT",
    consumers: ["ProductDefinition", "Aggregate", "CPP"],
    activation_gate: "MINI_MODULE_SPLIT_OWNER_GATE",
    noteRo: "Separarea bucket-ului necesită owner gate separat. Ieșirile curente rămân neschimbate.",
  },
  {
    id: "finish.face_intent",
    fieldKey: "face_finish_type",
    labelRo: "Intent finisaj față (vinyl/print)",
    domain: "FINISH",
    canonical_owner: "MODULE",
    ownerDetailRo: "Proprietar țintă: modul FINISH",
    value_layer: "intent",
    runtime_status: "TARGET",
    compatibility_status: "CURRENT",
    current_or_target: "TARGET",
    consumers: ["Intake finish_setup", "form contract", "PD"],
    activation_gate: "SOLD_CHIP_ACTIVATION_OWNER_GATE",
    noteRo: "Țintă documentată. Runtime actual încă leagă vizibilitatea de FACE sold — neschimbat.",
  },
  {
    id: "finish.face_workspace",
    fieldKey: "letter_group_finishes.face_*",
    labelRo: "Valoare concretă finisaj față",
    domain: "FINISH",
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
    canonical_owner: "MODULE",
    ownerDetailRo: "Țintă: un singur SoT sub modul FINISH",
    value_layer: "catalog_conflict",
    runtime_status: "CURRENT",
    compatibility_status: "LEGACY",
    current_or_target: "CURRENT",
    consumers: ["form contract", "FE option maps", "dossier", "QuoteWizard LEGACY"],
    activation_gate: "MINI_MODULE_SPLIT_OWNER_GATE",
    noteRo: "Cataloage conflictuale — conflict nerezolvat. Nu se unifică în V1.",
  },
  {
    id: "finish.mounting_template_misown",
    fieldKey: "mounting_template_*",
    labelRo: "Șablon montaj (sub finisaje azi)",
    domain: "MOUNTING",
    canonical_owner: "MODULE",
    ownerDetailRo: "Țintă: MOUNTING prep / INSTALLATION_TEMPLATE",
    value_layer: "intent",
    runtime_status: "TARGET",
    compatibility_status: "CURRENT",
    current_or_target: "TARGET",
    consumers: ["form montaj_template", "finisaje runtime"],
    activation_gate: "MINI_MODULE_SPLIT_OWNER_GATE",
    noteRo: "Mis-owned sub finisaje în runtime curent. Nu se mută liniile/operațiile în V1.",
  },
  {
    id: "finish.derived_area",
    fieldKey: "finish_coverage_measurements",
    labelRo: "Arii paint/foil/print",
    domain: "FINISH",
    canonical_owner: "DERIVED",
    ownerDetailRo: "ProductAggregate measurements",
    value_layer: "derived",
    runtime_status: "TARGET",
    compatibility_status: "CURRENT",
    current_or_target: "TARGET",
    consumers: ["Aggregate", "CPP commercial_measurements"],
    activation_gate: "SOLD_CHIP_ACTIVATION_OWNER_GATE",
    noteRo: "DERIVED — nu preț. CPP consumă măsurători; Registry deține tarife.",
  },
  {
    id: "finish.cpp_money",
    fieldKey: "cpp_7g",
    labelRo: "Autoritate bani finisaj",
    domain: "FINISH",
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
    labelRo: "Cerințe execuție finisaj",
    domain: "FINISH",
    canonical_owner: "EXECUTION",
    ownerDetailRo: "FINISH module / Execution (țintă)",
    value_layer: "execution_requirement",
    runtime_status: "TARGET",
    compatibility_status: "CURRENT",
    current_or_target: "TARGET",
    consumers: ["ExecutionPlan preview"],
    activation_gate: "SOLD_CHIP_ACTIVATION_OWNER_GATE",
    noteRo: "Fără materializare task în V1. Ieșirile curente neschimbate.",
  },
] as const;

export const MOUNTING_OWNERSHIP_SETTINGS: readonly OwnershipSettingRecord[] = [
  {
    id: "mounting.sold_module",
    fieldKey: "MOUNTING",
    labelRo: "Chip sold MOUNTING",
    domain: "MOUNTING",
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
    canonical_owner: "WORKSPACE",
    ownerDetailRo: "Compoziție tehnică → child templates",
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
    canonical_owner: "DERIVED",
    ownerDetailRo: "COMPATIBILITY_ALIAS derivat",
    value_layer: "derived",
    runtime_status: "COMPATIBILITY_ALIAS",
    compatibility_status: "COMPATIBILITY_ALIAS",
    current_or_target: "CURRENT",
    consumers: ["quote_input", "module_link trigger (legacy DB)"],
    activation_gate: "none",
    noteRo: "Nu este autoritate. Contradicțiile → compatibility_warning. Nu rescrie câmpurile canonice.",
  },
  {
    id: "mounting.method_target_name",
    fieldKey: "mounting_method",
    labelRo: "Nume țintă mounting_method",
    domain: "MOUNTING",
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
    labelRo: "Mapă runtime MOUNTING",
    domain: "MOUNTING",
    canonical_owner: "PRODUCT_TEMPLATE",
    ownerDetailRo: "{structura_suport, finisaje} — neschimbată",
    value_layer: "runtime_bucket",
    runtime_status: "CURRENT",
    compatibility_status: "CURRENT",
    current_or_target: "CURRENT",
    consumers: ["offer_scope_canonical_map"],
    activation_gate: "MOUNTING_MAP_NARROWING_OWNER_GATE",
    noteRo: "Îngustarea mapei nu este aprobată în V1.",
  },
] as const;

export const ALL_FINISH_MOUNTING_OWNERSHIP_SETTINGS: readonly OwnershipSettingRecord[] = [
  ...FINISH_OWNERSHIP_SETTINGS,
  ...MOUNTING_OWNERSHIP_SETTINGS,
];

export function ownershipStatusBadgeRo(status: OwnershipRuntimeStatus): string {
  return ownershipStatusLabelRo(status);
}

/** Operator-facing labels — correct Romanian (CURĂTOR avoided; use CURRENT). */
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
  targetOwnerRo: "Proprietar țintă: modul FINISH",
  catalogsRo: "Cataloage conflictuale",
  runtimeBucketRo: "Bucket runtime finisaje = mixt (neschimbat)",
} as const;

export const MOUNTING_OWNERSHIP_SUMMARY_RO = {
  linkedSupportRo: "Suport legat: parțial",
  soldStatusRo: "Modul vândut: blocat",
  methodFieldRo: "Câmp metodă curent: mounting_system",
  solutionFieldRo: "Soluție suport: mounting_solution",
  aliasFieldRo: "Alias compatibilitate: metal_support_required",
  mapGateRo: "Îngustare mapă: neaprobată",
} as const;

import type { ProductTemplateAvailabilityItem, ProductTemplateEntity } from "@/lib/api";
import {
  CANDIDATE_MODULE_COMPOSER_TEMPLATE_CODE,
  CANDIDATE_MODULE_COMPONENT_TEMPLATE_CODES,
  CANDIDATE_MODULE_EXPECTED_ROW_COUNT,
  CANDIDATE_MODULE_EXPECTED_TEMPLATE_CODES,
  assessCandidateModuleProdusLiveCompleteness,
  isCandidateModuleProdusLettersTemplate,
  normalizeCandidateModuleProdusTemplateCode,
  type CandidateModuleProdusCompletenessAssessment,
  type CandidateModuleProdusSourceMode,
  type CandidateModuleProdusTemplateCode,
} from "./candidateModuleProdusReadonlyCompleteness";

export type CandidateModuleProdusReadonlyComponent = {
  templateCode: string;
  componentId: string;
  roleLabel: string;
  componentKind: string;
  targetProductTruthPath: string;
  dependencies: string[];
  blockers: string[];
  readinessState: string;
  activationGuard: string;
  active: boolean;
  liveRowPresent: boolean;
};

export type CandidateModuleProdusReadonlySetModel = {
  sourceMode: CandidateModuleProdusSourceMode;
  foundRowCount: number;
  expectedRowCount: number;
  missingTemplateCodes: CandidateModuleProdusTemplateCode[];
  invalidActiveTemplateCodes: CandidateModuleProdusTemplateCode[];
  selectedTemplateCode: string;
  composerTemplateCode: string;
  composerActive: boolean;
  composerCatalogStatus: string;
  composerReadiness: string;
  composerActivationGuard: string;
  composerBlockers: string[];
  compositionList: Array<{
    componentId: string;
    componentTemplateCode: string;
    role: string;
    kind: string;
    targetProductTruthPath: string;
  }>;
  dependencyGraph: Array<{ from: string; to: string }>;
  noModuleLinks: boolean;
  noWorkIntakeExposure: boolean;
  noPricingActivation: boolean;
  noProductDefinitionActivation: boolean;
  noProductAggregateRuntimeWiring: boolean;
  noExecutableOperations: boolean;
  noExecutableBom: boolean;
  components: CandidateModuleProdusReadonlyComponent[];
};

function safeJsonParse<T>(raw: string | undefined | null, fallback: T): T {
  if (!raw) return fallback;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

export function buildFallbackCandidateModuleProdusReadonlySetModel(
  selectedTemplateCode: string,
  assessment?: CandidateModuleProdusCompletenessAssessment
): CandidateModuleProdusReadonlySetModel {
  return {
    sourceMode: assessment?.sourceMode ?? "code_contract_fallback",
    foundRowCount: assessment?.foundRowCount ?? 0,
    expectedRowCount: assessment?.expectedRowCount ?? CANDIDATE_MODULE_EXPECTED_ROW_COUNT,
    missingTemplateCodes: assessment?.missingTemplateCodes ?? [...CANDIDATE_MODULE_EXPECTED_TEMPLATE_CODES],
    invalidActiveTemplateCodes: assessment?.invalidActiveTemplateCodes ?? [],
    selectedTemplateCode,
    composerTemplateCode: CANDIDATE_MODULE_COMPOSER_TEMPLATE_CODE,
    composerActive: false,
    composerCatalogStatus: "not_seeded_live",
    composerReadiness: "planned",
    composerActivationGuard: "CANDIDATE_MODULE_SET_INERT_UNTIL_OWNER_GO",
    composerBlockers: [
      "OWNER_GO_REQUIRED",
      "COMPONENT_TRUTH_NOT_IMPLEMENTED",
      "WORK_INTAKE_NOT_ENABLED",
      "PRICING_NOT_ENABLED",
      "PRODUCT_DEFINITION_NOT_ENABLED",
    ],
    compositionList: [
      {
        componentId: "comp_letter_face_v1",
        componentTemplateCode: "TPL-COMP-LETTER-FACE_v1",
        role: "face",
        kind: "structural",
        targetProductTruthPath: "components.face.instances[]",
      },
      {
        componentId: "comp_letter_back_v1",
        componentTemplateCode: "TPL-COMP-LETTER-BACK_v1",
        role: "back",
        kind: "structural",
        targetProductTruthPath: "components.back.instances[]",
      },
      {
        componentId: "comp_letter_return_cant_v1",
        componentTemplateCode: "TPL-COMP-LETTER-RETURN-CANT_v1",
        role: "return_cant",
        kind: "structural",
        targetProductTruthPath: "components.return_cant.instances[]",
      },
      {
        componentId: "comp_letter_led_v1",
        componentTemplateCode: "TPL-COMP-LETTER-LED_v1",
        role: "lighting",
        kind: "functional",
        targetProductTruthPath: "components.led.instances[]",
      },
      {
        componentId: "comp_letter_finish_v1",
        componentTemplateCode: "TPL-COMP-LETTER-FINISH_v1",
        role: "finish",
        kind: "functional",
        targetProductTruthPath: "components.finish.instances[]",
      },
      {
        componentId: "comp_letter_mounting_v1",
        componentTemplateCode: "TPL-COMP-LETTER-MOUNTING_v1",
        role: "mounting",
        kind: "functional",
        targetProductTruthPath: "components.mounting.instances[]",
      },
    ],
    dependencyGraph: [
      { from: "comp_letter_face_v1", to: "comp_letter_return_cant_v1" },
      { from: "comp_letter_face_v1", to: "comp_letter_back_v1" },
      { from: "comp_letter_face_v1", to: "comp_letter_led_v1" },
      { from: "comp_letter_face_v1", to: "comp_letter_finish_v1" },
      { from: "comp_letter_back_v1", to: "comp_letter_finish_v1" },
      { from: "comp_letter_return_cant_v1", to: "comp_letter_finish_v1" },
      { from: "comp_letter_back_v1", to: "comp_letter_mounting_v1" },
      { from: "product_root", to: "comp_letter_mounting_v1" },
    ],
    noModuleLinks: true,
    noWorkIntakeExposure: true,
    noPricingActivation: true,
    noProductDefinitionActivation: true,
    noProductAggregateRuntimeWiring: true,
    noExecutableOperations: true,
    noExecutableBom: true,
    components: [
      {
        templateCode: "TPL-COMP-LETTER-FACE_v1",
        componentId: "comp_letter_face_v1",
        roleLabel: "structural face",
        componentKind: "structural",
        targetProductTruthPath: "components.face.instances[]",
        dependencies: [],
        blockers: ["SOURCE_LAYERS_UNCONFIRMED", "FACE_MATERIAL_MISSING", "FACE_THICKNESS_MISSING"],
        readinessState: "planned",
        activationGuard: "FACE_CONTRACT_ONLY_NOT_EXECUTABLE",
        active: false,
        liveRowPresent: false,
      },
      {
        templateCode: "TPL-COMP-LETTER-BACK_v1",
        componentId: "comp_letter_back_v1",
        roleLabel: "structural back",
        componentKind: "structural",
        targetProductTruthPath: "components.back.instances[]",
        dependencies: ["comp_letter_face_v1"],
        blockers: ["FACE_GEOMETRY_REF_MISSING", "BACK_MATERIAL_MISSING", "BACKING_MODE_MISSING"],
        readinessState: "planned",
        activationGuard: "BACK_CONTRACT_ONLY_NOT_EXECUTABLE",
        active: false,
        liveRowPresent: false,
      },
      {
        templateCode: "TPL-COMP-LETTER-RETURN-CANT_v1",
        componentId: "comp_letter_return_cant_v1",
        roleLabel: "structural return/cant",
        componentKind: "structural",
        targetProductTruthPath: "components.return_cant.instances[]",
        dependencies: ["components.face.confirmed_perimeter"],
        blockers: ["SOURCE_FACE_PERIMETER_REF_MISSING", "MATERIAL_PROFILE_MISSING", "DEPTH_MM_MISSING", "CONFIRMATION_STATE_MISSING"],
        readinessState: "planned",
        activationGuard: "RETURN_CANT_CONTRACT_ONLY_NOT_EXECUTABLE",
        active: false,
        liveRowPresent: false,
      },
      {
        templateCode: "TPL-COMP-LETTER-LED_v1",
        componentId: "comp_letter_led_v1",
        roleLabel: "functional lighting",
        componentKind: "functional",
        targetProductTruthPath: "components.led.instances[]",
        dependencies: ["components.face.confirmed_area"],
        blockers: ["LIGHTING_MODE_MISSING", "SOURCE_FACE_AREA_REF_MISSING", "LED_DENSITY_CONFIG_MISSING"],
        readinessState: "planned",
        activationGuard: "LED_CONTRACT_ONLY_NOT_EXECUTABLE",
        active: false,
        liveRowPresent: false,
      },
      {
        templateCode: "TPL-COMP-LETTER-FINISH_v1",
        componentId: "comp_letter_finish_v1",
        roleLabel: "functional finish",
        componentKind: "functional",
        targetProductTruthPath: "components.finish.instances[]",
        dependencies: ["comp_letter_face_v1", "comp_letter_back_v1", "comp_letter_return_cant_v1"],
        blockers: ["FINISH_TARGET_MISSING", "FINISH_TYPE_MISSING", "COLOR_DECISION_MISSING"],
        readinessState: "planned",
        activationGuard: "FINISH_CONTRACT_ONLY_NOT_EXECUTABLE",
        active: false,
        liveRowPresent: false,
      },
      {
        templateCode: "TPL-COMP-LETTER-MOUNTING_v1",
        componentId: "comp_letter_mounting_v1",
        roleLabel: "functional mounting",
        componentKind: "functional",
        targetProductTruthPath: "components.mounting.instances[]",
        dependencies: ["comp_letter_back_v1", "product.install_context"],
        blockers: ["MOUNTING_MODE_MISSING", "SUPPORT_REQUIRED_UNKNOWN", "INSTALL_CONTEXT_MISSING"],
        readinessState: "planned",
        activationGuard: "MOUNTING_CONTRACT_ONLY_NOT_EXECUTABLE",
        active: false,
        liveRowPresent: false,
      },
    ],
  };
}

function parseLiveCandidateModuleProdusComponent(
  template: ProductTemplateEntity,
  templateCode: CandidateModuleProdusTemplateCode
): CandidateModuleProdusReadonlyComponent {
  const notes = safeJsonParse<Record<string, unknown>>(template.notes, {});
  const componentContracts = safeJsonParse<Array<Record<string, unknown>>>(template.components_json, []);
  const component = componentContracts[0] ?? {};
  const dependencies = Array.isArray(component.dependencies)
    ? component.dependencies.map((entry) => {
        if (typeof entry === "string") return entry;
        if (entry && typeof entry === "object") {
          const record = entry as Record<string, unknown>;
          return String(record.source_path ?? record.source_component_id ?? record.dependency_key ?? "unknown");
        }
        return "unknown";
      })
    : [];
  const blockers = Array.isArray(component.blockers)
    ? component.blockers.map((entry) => String(entry))
    : [];

  return {
    templateCode,
    componentId: String(component.component_id ?? ""),
    roleLabel: String(component.role_label ?? component.role_key ?? "component"),
    componentKind: String(component.component_kind ?? "unknown"),
    targetProductTruthPath: String(component.target_product_truth_path ?? ""),
    dependencies,
    blockers,
    readinessState: String(component.readiness_state ?? notes.readiness ?? "planned"),
    activationGuard: String(component.activation_guard ?? notes.activation_guard ?? "OWNER_GO_REQUIRED"),
    active: template.active !== false,
    liveRowPresent: true,
  };
}

export function buildCandidateModuleProdusReadonlySetModel(
  templates: ProductTemplateEntity[],
  availabilityItems: ProductTemplateAvailabilityItem[],
  selectedTemplateCode: string | null | undefined
): CandidateModuleProdusReadonlySetModel | null {
  if (!isCandidateModuleProdusLettersTemplate(selectedTemplateCode)) {
    return null;
  }

  const assessment = assessCandidateModuleProdusLiveCompleteness(templates);
  if (assessment.sourceMode === "code_contract_fallback") {
    return buildFallbackCandidateModuleProdusReadonlySetModel(String(selectedTemplateCode), assessment);
  }

  const fallback = buildFallbackCandidateModuleProdusReadonlySetModel(String(selectedTemplateCode), assessment);
  const templateByCode = new Map(templates.map((template) => [normalizeCandidateModuleProdusTemplateCode(template.template_code), template]));
  const availabilityByCode = new Map(availabilityItems.map((item) => [normalizeCandidateModuleProdusTemplateCode(item.template_code), item]));
  const composer = templateByCode.get(normalizeCandidateModuleProdusTemplateCode(CANDIDATE_MODULE_COMPOSER_TEMPLATE_CODE));

  const composerComponents = composer
    ? safeJsonParse<Array<Record<string, unknown>>>(composer.components_json, [])
    : fallback.compositionList.map((entry) => ({
        component_id: entry.componentId,
        component_template_code: entry.componentTemplateCode,
        role: entry.role,
        kind: entry.kind,
        target_product_truth_path: entry.targetProductTruthPath,
      }));
  const composerNotes = composer
    ? safeJsonParse<Record<string, unknown>>(composer.notes, {})
    : {
        readiness: fallback.composerReadiness,
        activation_guard: fallback.composerActivationGuard,
        blockers: fallback.composerBlockers,
        component_dependency_graph: fallback.dependencyGraph.map((entry) => ({
          from: entry.from,
          to: entry.to,
        })),
        work_intake_exposed: fallback.noWorkIntakeExposure ? false : true,
        pricing_active: fallback.noPricingActivation ? false : true,
        product_definition_active: fallback.noProductDefinitionActivation ? false : true,
        product_aggregate_runtime_consumed: fallback.noProductAggregateRuntimeWiring ? false : true,
        no_executable_operations: fallback.noExecutableOperations,
        no_executable_bom: fallback.noExecutableBom,
      };
  const composerAvailability = availabilityByCode.get(normalizeCandidateModuleProdusTemplateCode(CANDIDATE_MODULE_COMPOSER_TEMPLATE_CODE));

  const components = CANDIDATE_MODULE_COMPONENT_TEMPLATE_CODES.map((templateCode) => {
    const template = templateByCode.get(normalizeCandidateModuleProdusTemplateCode(templateCode));
    if (template) {
      return parseLiveCandidateModuleProdusComponent(template, templateCode);
    }
    const fallbackComponent = fallback.components.find((entry) => entry.templateCode === templateCode);
    return fallbackComponent ?? null;
  }).filter((entry): entry is CandidateModuleProdusReadonlyComponent => Boolean(entry));

  return {
    sourceMode: assessment.sourceMode,
    foundRowCount: assessment.foundRowCount,
    expectedRowCount: assessment.expectedRowCount,
    missingTemplateCodes: assessment.missingTemplateCodes,
    invalidActiveTemplateCodes: assessment.invalidActiveTemplateCodes,
    selectedTemplateCode: String(selectedTemplateCode),
    composerTemplateCode: composer?.template_code ?? fallback.composerTemplateCode,
    composerActive: composer ? composer.active !== false : false,
    composerCatalogStatus: composerAvailability?.status ?? (composer ? "archived" : "not_seeded_live"),
    composerReadiness: String(composerNotes.readiness ?? "planned"),
    composerActivationGuard: String(composerNotes.activation_guard ?? "OWNER_GO_REQUIRED"),
    composerBlockers: Array.isArray(composerNotes.blockers)
      ? composerNotes.blockers.map((entry) => String(entry))
      : [],
    compositionList: composerComponents.map((entry) => ({
      componentId: String(entry.component_id ?? ""),
      componentTemplateCode: String(entry.component_template_code ?? ""),
      role: String(entry.role ?? ""),
      kind: String(entry.kind ?? ""),
      targetProductTruthPath: String(entry.target_product_truth_path ?? ""),
    })),
    dependencyGraph: Array.isArray(composerNotes.component_dependency_graph)
      ? composerNotes.component_dependency_graph.map((entry) => {
          const record = (entry ?? {}) as Record<string, unknown>;
          return {
            from: String(record.from ?? "unknown"),
            to: String(record.to ?? "unknown"),
          };
        })
      : fallback.dependencyGraph,
    noModuleLinks:
      (composerAvailability?.module_codes?.length ?? 0) === 0 &&
      (composerAvailability?.child_module_codes?.length ?? 0) === 0 &&
      composerAvailability?.has_modules !== true,
    noWorkIntakeExposure: composer ? composerNotes.work_intake_exposed === false : true,
    noPricingActivation: composer ? composerNotes.pricing_active === false : true,
    noProductDefinitionActivation: composer ? composerNotes.product_definition_active === false : true,
    noProductAggregateRuntimeWiring: composer ? composerNotes.product_aggregate_runtime_consumed === false : true,
    noExecutableOperations: composer ? composerNotes.no_executable_operations === true : true,
    noExecutableBom: composer ? composerNotes.no_executable_bom === true : true,
    components,
  };
}

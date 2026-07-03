/**
 * Staged intake readiness — display/routing only.
 * Does not change backend ready_for_quote or CostEngine policy.
 *
 * Stages:
 * - stage0_unresolved — no work type
 * - stage1_spec — template/spec in progress
 * - stage2_simulation — preliminary simulation allowed
 * - stage3_commercial_quote — legacy mark-ready / commercial offer path
 * - stage4_production — order/production handoff (informational)
 */

import type { IntakeProductSpec } from "@/lib/intakeProductSpec";
import { isFaceVinylEnabled } from "@/lib/volumetricFrontlitIntake";
import { parseSiteAuditJson, type IntakeSiteAuditJson } from "@/lib/intakeSiteAudit";
import { isUnresolvedIntakeProductFamily } from "@/lib/intakeProductFamilyDisplay";
import {
  evaluateIntakeReadyPrerequisites,
  type IntakeReadinessInput,
} from "@/lib/intakeReadiness";
import type { IntakeStatus } from "@/lib/mockData";
import { buildVolumetricQuotePrepSummary } from "@/lib/volumetricIntakeFormPrep";
import { getEffectiveQuoteGeometrySpec } from "@/lib/vectorGeometryInvalidation";
import { buildVectorIntakeRepairMissing } from "@/lib/svgIntakeFlow";
import {
  buildInitialVolumetricQuoteFlowState,
  buildEffectiveQuoteInputStrings,
} from "@/lib/volumetricQuoteFlowState";
import {
  TPL_VOLUMETRIC_LETTERS,
  effectiveReturnDepthMm,
  isCantRalPaintEnabled,
  volumetricQuoteInputStepValid,
} from "@/lib/volumetricQuoteInput";
import type { VolumetricQuoteFlowState } from "@/lib/volumetricQuoteFlowState";

export type IntakeReadinessStageId =
  | "stage0_unresolved"
  | "stage1_spec"
  | "stage2_simulation"
  | "stage3_commercial_quote"
  | "stage4_production";

export interface StagedMissingGroup {
  stage: IntakeReadinessStageId;
  label: string;
  description: string;
  missing: string[];
  ready: boolean;
}

export interface IntakeReadinessStagesResult {
  currentStage: IntakeReadinessStageId;
  workingStage: IntakeReadinessStageId;
  stageLabel: string;
  stageDescription: string;
  canSimulate: boolean;
  /** Legacy intake ops gate — same as evaluateIntakeReadyPrerequisites.canMarkReady */
  canMarkCommercial: boolean;
  canProduction: boolean;
  simulationMissing: string[];
  commercialMissing: string[];
  productionMissing: string[];
  specMissing: string[];
  grouped: StagedMissingGroup[];
  /** True when status === ready_for_quote (legacy flag, commercial gate) */
  legacyReadyForQuote: boolean;
}

export interface IntakeReadinessStagesInput {
  productFamily: string | null | undefined;
  status: IntakeStatus;
  confirmedTemplateCode?: string | null;
  showVolumetricForm: boolean;
  readinessInput: IntakeReadinessInput;
  requiresInstallAudit: boolean;
}

const STAGE_LABELS: Record<IntakeReadinessStageId, string> = {
  stage0_unresolved: "Intake nerezolvat",
  stage1_spec: "Specificație începută",
  stage2_simulation: "Gata pentru simulare",
  stage3_commercial_quote: "Gata pentru ofertă comercială",
  stage4_production: "Gata pentru producție",
};

const STAGE_DESCRIPTIONS: Record<IntakeReadinessStageId, string> = {
  stage0_unresolved: "Alege tipul lucrării pentru a deschide formularul relevant.",
  stage1_spec: "Completează câmpurile necesare pentru simulare preliminară.",
  stage2_simulation:
    "Poți rula simularea preliminară. Oferta comercială finală poate avea condiții suplimentare.",
  stage3_commercial_quote:
    "Condițiile pentru ofertă comercială și marcare Gata pt. Ofertă sunt îndeplinite.",
  stage4_production:
    "Detaliile de producție și montaj sunt complete pentru handoff comandă.",
};

export function getStageLabel(stage: IntakeReadinessStageId): string {
  return STAGE_LABELS[stage];
}

export function getStageDescription(stage: IntakeReadinessStageId): string {
  return STAGE_DESCRIPTIONS[stage];
}

function hasStructuredVolumetricEnvelope(
  spec: IntakeProductSpec | null | undefined
): boolean {
  if (!spec) return false;
  const width = spec.width_mm;
  const height = spec.height_mm ?? spec.letter_height_mm;
  const depth = spec.depth_mm ?? spec.return_depth_mm;
  return (
    width != null &&
    width > 0 &&
    height != null &&
    height > 0 &&
    depth != null &&
    depth > 0
  );
}

function isVolumetricTemplate(confirmedTemplateCode: string | null | undefined): boolean {
  return (confirmedTemplateCode ?? "").trim() === TPL_VOLUMETRIC_LETTERS;
}

function uniquePush(list: string[], item: string): void {
  if (!list.includes(item)) list.push(item);
}

/** Classify legacy prerequisite strings into commercial vs simulation buckets. */
export function classifyMissingReasonStage(
  reason: string
): "simulation" | "commercial" | "production" | "spec" {
  const r = reason.toLowerCase();
  if (r.includes("dimensiuni din specificație") || r.includes("width/height/depth")) {
    return "simulation";
  }
  if (r.includes("template") && r.includes("neconfirmat")) {
    return "spec";
  }
  if (r.includes("specificație produs") && r.includes("nesalvată")) {
    return "spec";
  }
  if (r.includes("audit teren")) {
    return "commercial";
  }
  if (
    r.includes("asignat") ||
    r.includes("descriere") ||
    r.includes("livrare") ||
    r.includes("dimensiuni —")
  ) {
    return "commercial";
  }
  return "commercial";
}

function specForSimulationCheck(
  spec: IntakeProductSpec | null | undefined
): IntakeProductSpec | null | undefined {
  if (!spec) return spec;
  const depth = effectiveReturnDepthMm(spec);
  if (depth != null && spec.return_depth_mm == null) {
    return { ...spec, return_depth_mm: depth };
  }
  return spec;
}

export function evaluateSimulationReadiness(input: {
  showVolumetricForm: boolean;
  confirmedTemplateCode?: string | null;
  productSpec?: IntakeProductSpec | null;
  /** Live quote flow state — when set, validates operator edits instead of spec-only prefill. */
  flowState?: VolumetricQuoteFlowState;
}): { ready: boolean; missing: string[] } {
  const missing: string[] = [];
  const template = (input.confirmedTemplateCode ?? "").trim();
  const volumetric = input.showVolumetricForm && isVolumetricTemplate(template);

  if (!template) {
    uniquePush(missing, "Template produs — neconfirmat");
    return { ready: false, missing };
  }

  if (volumetric) {
    const spec = getEffectiveQuoteGeometrySpec(input.productSpec);
    if (!spec || Object.keys(spec).length === 0) {
      uniquePush(missing, "Specificație produs — nesalvată");
    }
    if (!hasStructuredVolumetricEnvelope(spec)) {
      uniquePush(
        missing,
        "Dimensiuni din specificație — width/height/depth lipsă"
      );
    }

    const prep = buildVolumetricQuotePrepSummary(spec);
    for (const item of prep.missingForSimulate) {
      if (
        (item.includes("Adâncime cant") || item.includes("Adâncime cant / retur")) &&
        effectiveReturnDepthMm(spec) != null
      ) {
        continue;
      }
      uniquePush(missing, item);
    }

    const flowState =
      input.flowState ??
      buildInitialVolumetricQuoteFlowState(specForSimulationCheck(spec));
    const simulateReady = volumetricQuoteInputStepValid(
      buildEffectiveQuoteInputStrings(flowState),
      {
        widthMm: flowState.widthMm,
        cantRalPaintEnabled: isCantRalPaintEnabled(spec),
      }
    );
    if (!simulateReady && missing.length === 0) {
      uniquePush(missing, "Parametri CostEngine — incompleți pentru simulare");
    }

    return {
      ready: simulateReady,
      missing: simulateReady ? [] : missing,
    };
  }

  return { ready: true, missing };
}

export function evaluateCommercialQuoteReadiness(input: {
  readinessInput: IntakeReadinessInput;
  showVolumetricForm: boolean;
  confirmedTemplateCode?: string | null;
  productSpec?: IntakeProductSpec | null;
}): { ready: boolean; missing: string[] } {
  const legacy = evaluateIntakeReadyPrerequisites(input.readinessInput);
  const missing: string[] = [...legacy.missing];

  if (
    input.showVolumetricForm &&
    isVolumetricTemplate(input.confirmedTemplateCode)
  ) {
    const prep = buildVolumetricQuotePrepSummary(input.productSpec);
    for (const item of prep.missingForFinalQuote) {
      uniquePush(missing, item);
    }
  }

  return { ready: missing.length === 0, missing };
}

export function evaluateProductionReadiness(input: {
  productSpec?: IntakeProductSpec | null;
  siteAudit?: IntakeSiteAuditJson | null;
  requiresInstallAudit: boolean;
  showVolumetricForm: boolean;
  confirmedTemplateCode?: string | null;
}): { ready: boolean; missing: string[] } {
  const missing: string[] = [];
  const spec = input.productSpec ?? {};

  if (
    input.showVolumetricForm &&
    isVolumetricTemplate(input.confirmedTemplateCode)
  ) {
    if (
      !spec.vector_manual_review_approved &&
      spec.vector_analysis_status !== "manual_review_approved" &&
      spec.vector_analysis_status !== "analyzed"
    ) {
      uniquePush(missing, "Verificare vector finală pentru producție");
    }

    const face = spec.face_finish_type;
    if (
      isFaceVinylEnabled(spec) &&
      (face === "oracal_651" || face === "oracal_8500")
    ) {
      if (!spec.face_vinyl_color_code?.trim()) {
        uniquePush(missing, "Cod culoare folie Oracal (confirmare producție)");
      }
    }
    if (
      isCantRalPaintEnabled(spec) &&
      (spec.paint_tube_count ?? 0) > 0 &&
      !spec.paint_ral_code?.trim() &&
      !spec.ral_color?.trim()
    ) {
      uniquePush(missing, "Cod RAL vopsea confirmat pentru producție");
    }
  }

  if (input.requiresInstallAudit) {
    const audit = parseSiteAuditJson(input.siteAudit);
    if (!audit.checks.access_confirmed) {
      uniquePush(missing, "Acces montaj confirmat (teren)");
    }
    if (audit.location_photos_status !== "verified") {
      uniquePush(missing, "Poze locație montaj verificate pentru producție");
    }
  }

  return { ready: missing.length === 0, missing };
}

export function groupMissingReasonsByStage(groups: {
  specMissing: string[];
  simulationMissing: string[];
  commercialMissing: string[];
  productionMissing: string[];
  canSimulate: boolean;
  canMarkCommercial: boolean;
  canProduction: boolean;
  isStage0: boolean;
}): StagedMissingGroup[] {
  if (groups.isStage0) {
    return [
      {
        stage: "stage0_unresolved",
        label: STAGE_LABELS.stage0_unresolved,
        description: STAGE_DESCRIPTIONS.stage0_unresolved,
        missing: [],
        ready: false,
      },
    ];
  }

  return [
    {
      stage: "stage1_spec",
      label: STAGE_LABELS.stage1_spec,
      description: STAGE_DESCRIPTIONS.stage1_spec,
      missing: groups.specMissing,
      ready: groups.specMissing.length === 0,
    },
    {
      stage: "stage2_simulation",
      label: STAGE_LABELS.stage2_simulation,
      description: STAGE_DESCRIPTIONS.stage2_simulation,
      missing: groups.simulationMissing,
      ready: groups.canSimulate,
    },
    {
      stage: "stage3_commercial_quote",
      label: STAGE_LABELS.stage3_commercial_quote,
      description: STAGE_DESCRIPTIONS.stage3_commercial_quote,
      missing: groups.commercialMissing,
      ready: groups.canMarkCommercial,
    },
    {
      stage: "stage4_production",
      label: STAGE_LABELS.stage4_production,
      description: STAGE_DESCRIPTIONS.stage4_production,
      missing: groups.productionMissing,
      ready: groups.canProduction,
    },
  ];
}

function resolveWorkingStage(
  isStage0: boolean,
  canSimulate: boolean,
  canMarkCommercial: boolean,
  canProduction: boolean
): IntakeReadinessStageId {
  if (isStage0) return "stage0_unresolved";
  if (!canSimulate) return "stage1_spec";
  if (!canMarkCommercial) return "stage2_simulation";
  if (!canProduction) return "stage3_commercial_quote";
  return "stage4_production";
}

function resolveCurrentStage(
  isStage0: boolean,
  canSimulate: boolean,
  canMarkCommercial: boolean,
  canProduction: boolean,
  legacyReadyForQuote: boolean
): IntakeReadinessStageId {
  if (isStage0) return "stage0_unresolved";
  if (legacyReadyForQuote && canProduction) return "stage4_production";
  if (legacyReadyForQuote || canMarkCommercial) return "stage3_commercial_quote";
  if (canSimulate) return "stage2_simulation";
  return "stage1_spec";
}

export function buildIntakeReadinessStages(
  input: IntakeReadinessStagesInput
): IntakeReadinessStagesResult {
  const isStage0 = isUnresolvedIntakeProductFamily(input.productFamily);
  const legacyReadyForQuote = input.status === "ready_for_quote";

  if (isStage0) {
    return {
      currentStage: "stage0_unresolved",
      workingStage: "stage0_unresolved",
      stageLabel: STAGE_LABELS.stage0_unresolved,
      stageDescription: STAGE_DESCRIPTIONS.stage0_unresolved,
      canSimulate: false,
      canMarkCommercial: false,
      canProduction: false,
      simulationMissing: [],
      commercialMissing: [],
      productionMissing: [],
      specMissing: [],
      grouped: groupMissingReasonsByStage({
        specMissing: [],
        simulationMissing: [],
        commercialMissing: [],
        productionMissing: [],
        canSimulate: false,
        canMarkCommercial: false,
        canProduction: false,
        isStage0: true,
      }),
      legacyReadyForQuote,
    };
  }

  const simulation = evaluateSimulationReadiness({
    showVolumetricForm: input.showVolumetricForm,
    confirmedTemplateCode: input.confirmedTemplateCode,
    productSpec: input.readinessInput.productSpec,
  });

  const readinessInputWithInstall: IntakeReadinessInput = {
    ...input.readinessInput,
    requiresInstallAudit: input.requiresInstallAudit,
  };

  const commercial = evaluateCommercialQuoteReadiness({
    readinessInput: readinessInputWithInstall,
    showVolumetricForm: input.showVolumetricForm,
    confirmedTemplateCode: input.confirmedTemplateCode,
    productSpec: input.readinessInput.productSpec,
  });

  const production = evaluateProductionReadiness({
    productSpec: input.readinessInput.productSpec,
    siteAudit: input.readinessInput.siteAudit,
    requiresInstallAudit: input.requiresInstallAudit,
    showVolumetricForm: input.showVolumetricForm,
    confirmedTemplateCode: input.confirmedTemplateCode,
  });

  const specMissing: string[] = [];
  const template = (input.confirmedTemplateCode ?? "").trim();
  if (!template) {
    uniquePush(specMissing, "Template produs — neconfirmat");
  }
  if (
    input.showVolumetricForm &&
    isVolumetricTemplate(template) &&
    (!input.readinessInput.productSpec ||
      Object.keys(input.readinessInput.productSpec).length === 0)
  ) {
    uniquePush(specMissing, "Specificație produs — nesalvată");
  }

  if (input.showVolumetricForm && isVolumetricTemplate(template)) {
    for (const item of buildVectorIntakeRepairMissing(input.readinessInput.productSpec)) {
      uniquePush(specMissing, item);
    }
  }

  const simulationMissing = simulation.missing.filter(
    (m) => !specMissing.includes(m)
  );

  const commercialOnlyMissing: string[] = [];
  for (const m of commercial.missing) {
    if (simulation.missing.includes(m) || specMissing.includes(m)) continue;
    const bucket = classifyMissingReasonStage(m);
    if (bucket === "spec") {
      uniquePush(specMissing, m);
    } else {
      uniquePush(commercialOnlyMissing, m);
    }
  }

  const productionMissing = production.missing.filter(
    (m) =>
      !simulation.missing.includes(m) && !commercialOnlyMissing.includes(m)
  );

  const canSimulate = simulation.ready;
  const canMarkCommercial = commercial.ready;
  const canProduction = production.ready;

  const workingStage = resolveWorkingStage(
    false,
    canSimulate,
    canMarkCommercial,
    canProduction
  );
  const currentStage = resolveCurrentStage(
    false,
    canSimulate,
    canMarkCommercial,
    canProduction,
    legacyReadyForQuote
  );

  const grouped = groupMissingReasonsByStage({
    specMissing,
    simulationMissing,
    commercialMissing: commercialOnlyMissing,
    productionMissing,
    canSimulate,
    canMarkCommercial,
    canProduction,
    isStage0: false,
  });

  return {
    currentStage,
    workingStage,
    stageLabel: STAGE_LABELS[workingStage],
    stageDescription: STAGE_DESCRIPTIONS[workingStage],
    canSimulate,
    canMarkCommercial,
    canProduction,
    simulationMissing,
    commercialMissing: commercialOnlyMissing,
    productionMissing,
    specMissing,
    grouped,
    legacyReadyForQuote,
  };
}

/** @deprecated Prefer buildIntakeReadinessStages — thin alias for stage id. */
export function getIntakeReadinessStage(
  input: IntakeReadinessStagesInput
): IntakeReadinessStageId {
  return buildIntakeReadinessStages(input).workingStage;
}

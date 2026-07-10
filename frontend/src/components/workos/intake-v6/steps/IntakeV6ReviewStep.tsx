import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import type { IntakeV6WorkspaceHook } from "@/lib/intakeV6/useIntakeV6Workspace";
import {
  getIntakeV6AiInformationalAssistCandidate,
  getIntakeV6LogicalListReadModel,
  getIntakeV6MaterialBreakdown,
  getIntakeV6OrderBoundTaskReadiness,
  getIntakeV6ProductTruthPromotionPlanner,
  getIntakeV6PricedQuoteDryRun,
  getIntakeV6PricingInputPreview,
  getIntakeV6ProductionHandoffPreview,
  getIntakeV6ProductionTaskDryRun,
  getIntakeV6ProductSystemBinding,
  getIntakeV6QuoteHandoffPreview,
  getIntakeV6RuntimeCaptureReadModel,
  getIntakeV6TaskGenerationDryRun,
  getIntakeV6TaskPreview,
  getIntakeV6Workspace,
  type IntakeV6AiInformationalAssistPreviewResponse,
  type IntakeV6FinishSetup,
  type IntakeV6LogicalListReadModelResponse,
  type IntakeV6MaterialBreakdownResponse,
  type IntakeV6OrderBoundTaskReadinessResponse,
  type IntakeV6ProductTruthPromotionPlannerResponse,
  type IntakeV6PricedQuoteDryRunResponse,
  type IntakeV6PricingInputPreviewResponse,
  type IntakeV6ProductionHandoffPreviewResponse,
  type IntakeV6ProductSystemBindingResponse,
  type IntakeV6QuoteHandoffPreviewResponse,
  type IntakeV6RuntimeCaptureReadModelResponse,
  type IntakeV6TaskGenerationDryRunResponse,
  type IntakeV6TaskPreviewResponse,
} from "@/lib/intakeV6/intakeV6Api";
import {
  resolveIntakeV6EmblemLightingDepthMm,
  resolveLetterPerimeterForFinish,
  syncIntakeV6FinishLightingForLayerState,
} from "@/lib/intakeV6/intakeV6FinishLighting";
import {
  syncIntakeV6FinishPayloadFromLayerFinishes,
} from "@/lib/intakeV6/intakeV6FinishPayloadSync";
import {
  artworkFinishesFromPayload,
  deriveArtworkFinishesFromAnalyzer,
  mergeArtworkFinishes,
  type IntakeV6ArtworkFinish,
} from "@/lib/intakeV6/intakeV6ArtworkFinish";
import {
  DEFAULT_RETURN_DEPTH_MM,
  deriveLetterGroupsFromAnalyzer,
  letterGroupFinishesFromPayload,
  mergeLetterGroupFinishes,
  type IntakeV6LetterGroupFinish,
} from "@/lib/intakeV6/intakeV6LetterGroups";
import { INTAKE_V6_DEFAULT_RETURN_FINISH_TYPE } from "@/lib/intakeV6/intakeV6ReturnFinishOptions";
import {
  extractQuoteGeometryFromAnalyzer,
  readQuoteGeometryFromPayload,
  resolveQuoteGeometryForWorkspace,
} from "@/lib/intakeV6/intakeV6QuoteGeometry";
import { getAnalysisIdentityKey, isAnalysisReadyForReview } from "@/lib/intakeV6/intakeV6AnalysisIdentity";
import {
  buildIntakeV6GeometryMetricDisplay,
  getFullVectorPerimeterM,
  resolveIntakeV6OperatorCantPerimeterDisplay,
} from "@/lib/intakeV6/intakeV6GeometryMetricDisplay";
import type { IntakeV6SheetFootprintOverride } from "@/lib/intakeV6/intakeV6SheetFootprintOverride";
import type { SvgAnalysisCoreReport } from "@/lib/svgAnalyzer";
import IntakeV6ArtworkFinishSection from "../IntakeV6ArtworkFinishSection";
import IntakeV6ArtworkComplexityCard from "../IntakeV6ArtworkComplexityCard";
import {
  artworkComplexityDecisionsFromPayload,
  artworkComplexityFromReport,
  mergeArtworkComplexityDecisions,
  type IntakeV6ArtworkComplexityDecision,
} from "@/lib/intakeV6/intakeV6ArtworkComplexityDisplay";
import IntakeV6AiSemanticAssistPanel from "../IntakeV6AiSemanticAssistPanel";
import IntakeV6ReviewBackingSelect from "../IntakeV6ReviewBackingSelect";
import IntakeV6ReviewLightingSection from "../IntakeV6ReviewLightingSection";
import IntakeV6ReviewSaveFooter from "../IntakeV6ReviewSaveFooter";
import IntakeV6FaceBackPrepCostDraftPanel from "../IntakeV6FaceBackPrepCostDraftPanel";
import IntakeV6GeometryPanel from "../IntakeV6GeometryPanel";
import IntakeV6ReviewLetterGroupsSection from "../IntakeV6ReviewLetterGroupsSection";
import IntakeV6MaterialBreakdownPanel from "../IntakeV6MaterialBreakdownPanel";
import IntakeV6ProductionHandoffPreviewPanel from "../IntakeV6ProductionHandoffPreviewPanel";
import IntakeV6TaskGenerationDryRunPanel from "../IntakeV6TaskGenerationDryRunPanel";
import IntakeV6OrderBoundTaskReadinessPanel from "../IntakeV6OrderBoundTaskReadinessPanel";
import IntakeV6QuoteCommercialSpinePanel from "../IntakeV6QuoteCommercialSpinePanel";
import IntakeV6PricingInputPanel from "../IntakeV6PricingInputPanel";
import FormSystemBackboneAwarenessPanel from "../FormSystemBackboneAwarenessPanel";
import FormSystemRuntimeCaptureReadModelPanel from "../FormSystemRuntimeCaptureReadModelPanel";
import ProductTruthPromotionPlannerPanel from "../ProductTruthPromotionPlannerPanel";
import { toast } from "@/components/ui/sonner";
import { buildProductTruthDraft } from "@/lib/intakeV6/productTruth/productTruthDraftBuilder";
import { mapReturnCantTruthFieldsReadonly } from "@/lib/intakeV6/productTruth/returnCantTruthFieldsReadonlyMapper";
import { useTemplateFormContract } from "@/lib/intakeV6/useTemplateFormContract";
import {
  globalFinishSetupToReturnCant,
  patchGlobalFinishSetupFromReturnCant,
  shouldHideGlobalFinishSettings,
} from "@/lib/intakeV6/intakeV6ReturnCantBridge";
import IntakeV6ReturnCantFields from "../IntakeV6ReturnCantFields";
import IntakeV6ReturnCantBlockedStateAwarenessPanel from "../IntakeV6ReturnCantBlockedStateAwarenessPanel";
import IntakeV6ProductionTaskDryRunPanel from "../IntakeV6ProductionTaskDryRunPanel";
import type { IntakeV6ProductionTaskDryRunResponse } from "@/lib/intakeV6/productionTaskDryRunContracts";
import {
  faceFinishNeedsRollWidth,
  normalizeFaceVinylRollWidthMm,
} from "@/lib/intakeV6/intakeV6FaceFinishOptions";
import {
  computeIntakeV6LedModuleCount,
  INTAKE_V6_LED_MODULE_WATTAGE_OPTIONS,
  INTAKE_V6_PSU_RESERVE_RATIO,
  normalizeIntakeV6LedModuleWattage,
} from "@/lib/intakeV6/intakeV6LedLighting";
import {
  normalizeEmblemLightingMode,
  normalizeIntakeV6BackingMode,
} from "@/lib/intakeV6/intakeV6BackingMode";
import {
  isIntakeV6SelectorStatePendingSave,
} from "@/lib/intakeV6/intakeV6FinishHydration";
import {
  readIntakeV6OfferCommercialInputs,
  resolveIntakeV6OfferCommercialDefaults,
  serializeIntakeV6OfferCommercialInputs,
  type IntakeV6OfferCommercialInputs,
} from "@/lib/intakeV6/intakeV6OfferCalculator";
import IntakeV6ReviewTabNav, { type IntakeV6ReviewTabId } from "../IntakeV6ReviewTabNav";
import IntakeV6ReviewOperatorBlockerBanner from "../IntakeV6ReviewOperatorBlockerBanner";
import IntakeV6ReviewSectionShell from "../atoms/IntakeV6ReviewSectionShell";
import {
  REVIEW_FIELD_BLOCK_CLASS,
  REVIEW_FIELD_LABEL_CLASS,
  REVIEW_SELECT_CLASS,
} from "../reviewFieldLayout";
import IntakeV6TechnicalDetailsAccordion from "../atoms/IntakeV6TechnicalDetailsAccordion";
import IntakeV6LiveCalculationSummary from "../IntakeV6LiveCalculationSummary";
import IntakeV6ProductCompositionPanel from "../IntakeV6ProductCompositionPanel";
import { getProductDefinitionPreview, ProductDefinitionPreviewNotFoundError, type ProductDefinitionPreview } from "@/api/productDefinitionPreview";
import {
  LOGO_ONLY_COMMERCIAL_GUARD_MESSAGE,
  LOGO_ONLY_COMMERCIAL_GUARD_TITLE,
  LOGO_ONLY_NOT_OFFERABLE_STATUS,
  isLogoOnlyCandidateNotOfferableStatus,
} from "@/lib/intakeV6/intakeV6LogoOnlyCommercialGuard";
import { useCompanyCommercialSettings } from "@/hooks/useCompanyCommercialSettings";
import IntakeV6OperatorWorkSummaryTechnicalDetails from "../IntakeV6OperatorWorkSummaryTechnicalDetails";
import { buildIntakeV6OperatorWorkSummaryCounts } from "@/lib/intakeV6/intakeV6ConfirmSummary";
import { useIntakeV6FaceBackPrepCostDraft } from "@/lib/intakeV6/useIntakeV6FaceBackPrepCostDraft";
import {
  adaptBackingAbsentOperationLabel,
  INTAKE_V6_PREVIEW_ONLY_BANNER,
  INTAKE_V6_TASK_PREVIEW_BOUNDARY_LINE,
} from "@/lib/intakeV6/intakeV6OperatorUiDisplay";
import {
  buildReviewHandoffSurfacing,
  collectArtworkUndecidedWarnings,
  hasUnclassifiedVectorArtworkWarning,
  resolveReviewReadinessDisplay,
} from "@/lib/intakeV6/intakeV6QuoteHandoffReadiness";
import { buildOperatorBlockerBannerDisplay } from "@/lib/intakeV6/intakeV6OperatorBlockerBannerDisplay";
import {
  buildReviewDiagnosticEntryCount,
  INTAKE_V6_REVIEW_DIAGNOSTIC_SECTION_TITLE,
} from "@/lib/intakeV6/intakeV6ReviewDiagnosticEntryCount";
import {
  detectArtworkOnlyRequiresDecision,
  resolveArtworkOnlyReviewWarnings,
  sanitizeLetterGroupsForArtworkOnlyGuard,
} from "@/lib/intakeV6/intakeV6ArtworkOnlyGuard";
import IntakeV6ArtworkOnlyDecisionPanel from "../IntakeV6ArtworkOnlyDecisionPanel";
import { resolveLayerCardStatus } from "../letterGroupCardPresentation";
import { useIntakeV6WorkspaceHeaderStatus } from "../IntakeV6WorkspaceHeaderStatusContext";
import { useModularFormContract } from "@/lib/intakeV6/useModularFormContract";
import { useModularFormAwareness } from "@/lib/intakeV6/useModularFormAwareness";
import { layerRoleConfirmationToV6Setup } from "@/lib/intakeV6/intakeV6LayerRoleBridge";
import { resolveModuleActivationAttentionWarnings } from "@/lib/intakeV6/intakeV6ModuleActivationPreview";
import {
  resolveIntakeV6ReviewRefetchGroups,
  type IntakeV6ReviewDirtyDomain,
  type IntakeV6ReviewRefetchGroup,
} from "@/lib/intakeV6/intakeV6ReviewRefetchDomains";
import { v6 } from "../atoms/intakeV6Presentation";

type IntakeV6MountingSystem = NonNullable<IntakeV6FinishSetup["mounting_system"]>;
type IntakeV6MountingTemplateMaterial = NonNullable<IntakeV6FinishSetup["mounting_template_material_type"]>;

const VALID_MOUNTING_SYSTEMS: readonly string[] = ["direct_wall", "steel_bars", "aluminum_bars", "acm_panel"];

function normalizeIntakeV6MountingSystem(value: unknown): IntakeV6MountingSystem {
  return typeof value === "string" && VALID_MOUNTING_SYSTEMS.includes(value)
    ? (value as IntakeV6MountingSystem)
    : "direct_wall";
}

function normalizeIntakeV6MountingTemplateMaterial(value: unknown): IntakeV6MountingTemplateMaterial {
  return value === "paper" ? "paper" : "forex";
}

type ReviewAutosavePolicy = "short" | "long";

type ReviewPreviewRefreshState = Record<IntakeV6ReviewRefetchGroup, number>;

const INITIAL_REVIEW_PREVIEW_REFRESH: ReviewPreviewRefreshState = {
  breakdown: 0,
  pricing: 0,
  pricedQuote: 0,
  productionDryRun: 0,
  productionHandoff: 0,
  quoteHandoff: 0,
  taskGeneration: 0,
  taskPreview: 0,
  orderBoundReadiness: 0,
};

function buildFinishSetupSyncSignature(finish: IntakeV6FinishSetup): string {
  return JSON.stringify({
    face_finish_type: finish.face_finish_type ?? null,
    face_vinyl_roll_width_mm: normalizeFaceVinylRollWidthMm(
      finish.face_finish_type,
      finish.face_vinyl_roll_width_mm,
    ),
    return_finish_type: finish.return_finish_type ?? null,
    return_depth_mm: finish.return_depth_mm ?? null,
    volum_aluminum_module_template_code: finish.volum_aluminum_module_template_code ?? null,
    illuminated: finish.illuminated !== false,
    lighting_system_type: finish.lighting_system_type ?? "led_modules",
    light_color: finish.light_color ?? "neutral",
    led_module_power_w: normalizeIntakeV6LedModuleWattage(finish.led_module_power_w),
    led_strip_power_w_per_ml: finish.led_strip_power_w_per_ml ?? 5,
    led_module_count: finish.led_module_count ?? null,
    letter_led_strip_length_m: finish.letter_led_strip_length_m ?? null,
    emblem_led_strip_length_m: finish.emblem_led_strip_length_m ?? null,
    total_led_strip_length_m: finish.total_led_strip_length_m ?? null,
    estimated_led_watts: finish.estimated_led_watts ?? null,
    required_psu_watts: finish.required_psu_watts ?? null,
    psu_configuration: finish.psu_configuration ?? [],
    psu_allocation_status: finish.psu_allocation_status ?? null,
    selected_psu_watts: finish.selected_psu_watts ?? null,
    backing_mode: normalizeIntakeV6BackingMode(finish.backing_mode),
    back_bevel_enabled: finish.back_bevel_enabled === true,
    mounting_template_enabled: finish.mounting_template_enabled !== false,
    mounting_template_area_m2: finish.mounting_template_area_m2 ?? null,
    mounting_template_material_type: finish.mounting_template_material_type ?? "forex",
    mounting_system: finish.mounting_system ?? "direct_wall",
    mounting_bar_profile: finish.mounting_bar_profile ?? "30x30x1.5",
    emblem_lighting_mode: normalizeEmblemLightingMode(finish.emblem_lighting_mode),
    letter_led_module_count: finish.letter_led_module_count ?? null,
    emblem_led_module_count: finish.emblem_led_module_count ?? null,
    total_led_module_count: finish.total_led_module_count ?? null,
    confirmed: finish.confirmed === true,
  });
}

function buildJsonSignature(value: unknown): string {
  return JSON.stringify(value ?? null);
}

function finishFromPayload(payload: Record<string, unknown> | undefined): IntakeV6FinishSetup {
  const raw = payload?.finish_setup;
  if (raw == null || typeof raw !== "object" || Array.isArray(raw)) {
    return {
      face_finish_type: "oracal_651",
      face_vinyl_roll_width_mm: normalizeFaceVinylRollWidthMm("oracal_651", null),
      return_finish_type: INTAKE_V6_DEFAULT_RETURN_FINISH_TYPE,
      volum_aluminum_module_template_code: null,
      return_depth_mm: DEFAULT_RETURN_DEPTH_MM,
      illuminated: true,
      lighting_system_type: "led_modules",
      light_color: "neutral",
      led_module_power_w: 0.75,
      led_strip_power_w_per_ml: 5,
      selected_psu_watts: 100,
      letter_group_finishes: [],
      artwork_finishes: [],
      backing_mode: "forex_10_no_bevel",
      back_bevel_enabled: false,
      mounting_template_enabled: true,
      mounting_template_material_type: "forex",
      mounting_system: "direct_wall",
      mounting_bar_profile: "30x30x1.5",
      emblem_lighting_mode: "area_lit",
      confirmed: false,
    };
  }
  const setup = raw as Record<string, unknown>;
  const psuConfiguration = Array.isArray(setup.psu_configuration)
    ? setup.psu_configuration.filter((v): v is number => typeof v === "number")
    : undefined;
  const backingMode = normalizeIntakeV6BackingMode(setup.backing_mode);
  return {
    face_finish_type: typeof setup.face_finish_type === "string" ? setup.face_finish_type : "oracal_651",
    face_vinyl_roll_width_mm: normalizeFaceVinylRollWidthMm(
      typeof setup.face_finish_type === "string" ? setup.face_finish_type : "oracal_651",
      typeof setup.face_vinyl_roll_width_mm === "number" ? setup.face_vinyl_roll_width_mm : undefined,
    ),
    return_finish_type:
      typeof setup.return_finish_type === "string"
        ? setup.return_finish_type
        : INTAKE_V6_DEFAULT_RETURN_FINISH_TYPE,
    volum_aluminum_module_template_code:
      typeof setup.volum_aluminum_module_template_code === "string"
        ? setup.volum_aluminum_module_template_code
        : null,
    return_depth_mm:
      typeof setup.return_depth_mm === "number" ? setup.return_depth_mm : DEFAULT_RETURN_DEPTH_MM,
    illuminated: setup.illuminated !== false,
    lighting_system_type:
      typeof setup.lighting_system_type === "string" ? setup.lighting_system_type : "led_modules",
    light_color: typeof setup.light_color === "string" ? setup.light_color : "neutral",
    led_module_power_w:
      typeof setup.led_module_power_w === "number"
        ? normalizeIntakeV6LedModuleWattage(setup.led_module_power_w)
        : 0.75,
    led_strip_power_w_per_ml:
      typeof setup.led_strip_power_w_per_ml === "number" ? setup.led_strip_power_w_per_ml : 5,
    led_module_count:
      typeof setup.led_module_count === "number" ? setup.led_module_count : undefined,
    letter_led_strip_length_m:
      typeof setup.letter_led_strip_length_m === "number" ? setup.letter_led_strip_length_m : undefined,
    emblem_led_strip_length_m:
      typeof setup.emblem_led_strip_length_m === "number" ? setup.emblem_led_strip_length_m : undefined,
    total_led_strip_length_m:
      typeof setup.total_led_strip_length_m === "number" ? setup.total_led_strip_length_m : undefined,
    estimated_led_watts:
      typeof setup.estimated_led_watts === "number" ? setup.estimated_led_watts : undefined,
    required_psu_watts:
      typeof setup.required_psu_watts === "number" ? setup.required_psu_watts : undefined,
    psu_configuration: psuConfiguration,
    psu_allocation_status:
      typeof setup.psu_allocation_status === "string" ? setup.psu_allocation_status : undefined,
    selected_psu_watts:
      typeof setup.selected_psu_watts === "number"
        ? setup.selected_psu_watts
        : psuConfiguration && psuConfiguration.length > 0
          ? Math.max(...psuConfiguration)
          : undefined,
    letter_group_finishes: letterGroupFinishesFromPayload(payload),
    artwork_finishes: artworkFinishesFromPayload(payload),
    artwork_complexity_decisions: artworkComplexityDecisionsFromPayload(payload),
    backing_mode: backingMode,
    back_bevel_enabled:
      typeof setup.back_bevel_enabled === "boolean"
        ? setup.back_bevel_enabled
        : backingMode === "forex_10_with_bevel",
    mounting_template_enabled:
      typeof setup.mounting_template_enabled === "boolean" ? setup.mounting_template_enabled : true,
    mounting_template_area_m2:
      typeof setup.mounting_template_area_m2 === "number" ? setup.mounting_template_area_m2 : undefined,
    mounting_template_material_type: normalizeIntakeV6MountingTemplateMaterial(
      setup.mounting_template_material_type,
    ),
    mounting_system: normalizeIntakeV6MountingSystem(setup.mounting_system),
    mounting_bar_profile:
      typeof setup.mounting_bar_profile === "string" ? setup.mounting_bar_profile : "30x30x1.5",
    emblem_lighting_mode: normalizeEmblemLightingMode(setup.emblem_lighting_mode),
    letter_led_module_count:
      typeof setup.letter_led_module_count === "number" ? setup.letter_led_module_count : undefined,
    emblem_led_module_count:
      typeof setup.emblem_led_module_count === "number" ? setup.emblem_led_module_count : undefined,
    total_led_module_count:
      typeof setup.total_led_module_count === "number" ? setup.total_led_module_count : undefined,
    confirmed: setup.confirmed === true,
  };
}

function pathGeometryFromPayload(payload: Record<string, unknown> | undefined): Record<string, unknown> | undefined {
  const raw = payload?.path_geometry_summary;
  if (raw != null && typeof raw === "object" && !Array.isArray(raw)) {
    return raw as Record<string, unknown>;
  }
  return undefined;
}

function positiveNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) && value > 0 ? value : null;
}

function roundTemplateAreaM2(value: number): number {
  return Math.round(value * 10_000) / 10_000;
}

function areaFromDimensionsM2(widthMm: unknown, heightMm: unknown): number | null {
  const width = positiveNumber(widthMm);
  const height = positiveNumber(heightMm);
  if (width == null || height == null) return null;
  return roundTemplateAreaM2((width * height) / 1_000_000);
}

function resolveMountingTemplateMinimumAreaM2(
  payload: Record<string, unknown> | undefined,
  report: SvgAnalysisCoreReport | null,
  quoteGeometry: ReturnType<typeof resolveQuoteGeometryForWorkspace> | null,
): number | undefined {
  const documentArea = positiveNumber(report?.document?.boundingAreaSqm);
  if (documentArea != null) return roundTemplateAreaM2(documentArea);

  const reportDimensionArea = areaFromDimensionsM2(report?.document?.widthMm, report?.document?.heightMm);
  if (reportDimensionArea != null) return reportDimensionArea;

  const pathGeometry = pathGeometryFromPayload(payload);
  const pathBBoxArea = areaFromDimensionsM2(pathGeometry?.bbox_w_mm, pathGeometry?.bbox_h_mm);
  if (pathBBoxArea != null) return pathBBoxArea;

  const quoteDimensionArea = areaFromDimensionsM2(quoteGeometry?.width_mm, quoteGeometry?.height_mm);
  if (quoteDimensionArea != null) return quoteDimensionArea;

  const faceArea = positiveNumber(quoteGeometry?.face_area_m2);
  return faceArea != null ? roundTemplateAreaM2(faceArea) : undefined;
}

function resolveMountingTemplateAreaM2(
  currentArea: number | null | undefined,
  minimumArea: number | undefined,
): number | undefined {
  const current = positiveNumber(currentArea);
  if (minimumArea == null) return current ?? undefined;
  if (current == null || current < minimumArea) return minimumArea;
  return current;
}

function applyMountingTemplateMinimumArea(
  finish: IntakeV6FinishSetup,
  minimumArea: number | undefined,
): IntakeV6FinishSetup {
  if (finish.mounting_template_enabled === false) return finish;
  const area = resolveMountingTemplateAreaM2(finish.mounting_template_area_m2, minimumArea);
  if (area == null || area === finish.mounting_template_area_m2) return finish;
  return { ...finish, mounting_template_area_m2: area, confirmed: false };
}

export default function IntakeV6ReviewStep({ hook }: { hook: IntakeV6WorkspaceHook }) {
  const { state, saveFinishSetup, trySetStep, confirmProductComposition } = hook;
  const { setOverlay, setHandlers } = useIntakeV6WorkspaceHeaderStatus();
  const workspaceId = state.workspace?.id;
  const { vatPct, eurToRonRate } = useCompanyCommercialSettings(Boolean(workspaceId));
  const payload = state.workspace?.payload as Record<string, unknown> | undefined;
  const logoOnlyCandidateNotOfferable = isLogoOnlyCandidateNotOfferableStatus(state.workspace?.readiness_status);

  // Template form contract — drives dynamic options for face/return finish selects
  const templateContract = useTemplateFormContract(workspaceId);

  const analysisIdentityKey = getAnalysisIdentityKey(state);
  const analysisReady = isAnalysisReadyForReview(state);

  const quoteGeometry = useMemo(
    () =>
      resolveQuoteGeometryForWorkspace({
        payload,
        analyzerReport: state.analyzerReport as SvgAnalysisCoreReport | null,
        layerRoleConfirmation: state.layerRoleConfirmation,
        localFileHash: state.localFileHash,
      }),
    [payload, state.analyzerReport, state.layerRoleConfirmation, state.localFileHash],
  );

  const templateCode =
    payload?.product_binding != null &&
    typeof payload.product_binding === "object" &&
    !Array.isArray(payload.product_binding)
      ? String((payload.product_binding as Record<string, unknown>).template_code ?? "")
      : null;
  const persistedSvgFileHash =
    payload?.svg_source != null &&
    typeof payload.svg_source === "object" &&
    !Array.isArray(payload.svg_source) &&
    typeof (payload.svg_source as Record<string, unknown>).file_hash === "string"
      ? String((payload.svg_source as Record<string, unknown>).file_hash)
      : null;

  const geometryMetrics = useMemo(
    () =>
      buildIntakeV6GeometryMetricDisplay({
        report: state.analyzerReport as SvgAnalysisCoreReport | null,
        confirmation: state.layerRoleConfirmation,
        geometry: quoteGeometry,
        payload,
        analysisBundleReady: analysisReady,
        templateCode,
      }),
    [
      state.analyzerReport,
      state.layerRoleConfirmation,
      quoteGeometry,
      payload,
      analysisReady,
      templateCode,
    ],
  );

  const rasterLayerKeys = useMemo(() => {
    const report = state.analyzerReport as SvgAnalysisCoreReport | null;
    if (!report) return new Set<string>();
    const keys = new Set<string>();
    for (const layer of report.layers) {
      if (layer.layerKind === "raster_artwork") {
        keys.add(layer.id);
        keys.add(layer.name);
      }
    }
    for (const entry of state.layerRoleConfirmation?.layers ?? []) {
      keys.add(entry.layerKey);
    }
    return keys;
  }, [state.analyzerReport, state.layerRoleConfirmation]);

  const letterPerimeterM = useMemo(
    () =>
      resolveLetterPerimeterForFinish(
        pathGeometryFromPayload(payload),
        quoteGeometry,
        state.analyzerReport as SvgAnalysisCoreReport | null,
        state.layerRoleConfirmation,
      ),
    [payload, quoteGeometry, state.analyzerReport, state.layerRoleConfirmation],
  );

  const emblemOutboxAreaM2 = quoteGeometry?.artwork_area_m2 ?? null;
  const mountingTemplateAreaFallbackM2 = useMemo(() => {
    return resolveMountingTemplateMinimumAreaM2(
      payload,
      state.analyzerReport as SvgAnalysisCoreReport | null,
      quoteGeometry,
    );
  }, [payload, quoteGeometry, state.analyzerReport]);

  const syncLighting = (finish: IntakeV6FinishSetup) =>
    syncIntakeV6FinishLightingForLayerState({
      finish,
      letterPerimeterM,
      emblemAreaM2: emblemOutboxAreaM2,
      artworkBoxes: quoteGeometry?.artwork_boxes ?? [],
      letterGroups: (finish.letter_group_finishes ?? []) as IntakeV6LetterGroupFinish[],
      artworkFinishes: (finish.artwork_finishes ?? []) as IntakeV6ArtworkFinish[],
      fallbackDepthMm: finish.return_depth_mm ?? DEFAULT_RETURN_DEPTH_MM,
    });

  const [form, setForm] = useState<IntakeV6FinishSetup>(() =>
    syncLighting(applyMountingTemplateMinimumArea(finishFromPayload(payload), mountingTemplateAreaFallbackM2)),
  );
  const [letterGroups, setLetterGroups] = useState<IntakeV6LetterGroupFinish[]>(() =>
    mergeLetterGroupFinishes(
      deriveLetterGroupsFromAnalyzer(
        state.analyzerReport as SvgAnalysisCoreReport | null,
        state.layerRoleConfirmation,
        finishFromPayload(payload).return_depth_mm ?? DEFAULT_RETURN_DEPTH_MM,
      ),
      letterGroupFinishesFromPayload(payload),
    ),
  );
  const [artworkFinishes, setArtworkFinishes] = useState<IntakeV6ArtworkFinish[]>(() =>
    mergeArtworkFinishes(
      deriveArtworkFinishesFromAnalyzer(
        state.analyzerReport as SvgAnalysisCoreReport | null,
        state.layerRoleConfirmation,
        finishFromPayload(payload).return_depth_mm ?? DEFAULT_RETURN_DEPTH_MM,
      ),
      artworkFinishesFromPayload(payload),
    ),
  );
  const artworkComplexityReport = useMemo(
    () => artworkComplexityFromReport(state.analyzerReport as SvgAnalysisCoreReport | null),
    [state.analyzerReport],
  );
  const [artworkComplexityDecisions, setArtworkComplexityDecisions] = useState<
    IntakeV6ArtworkComplexityDecision[]
  >(() =>
    mergeArtworkComplexityDecisions(
      artworkComplexityDecisionsFromPayload(payload),
      artworkComplexityReport?.assessments ?? [],
    ),
  );
  const [preview, setPreview] = useState<IntakeV6TaskPreviewResponse | null>(null);
  const [pricingPreview, setPricingPreview] = useState<IntakeV6PricingInputPreviewResponse | null>(null);
  const [pricedQuoteDryRun, setPricedQuoteDryRun] = useState<IntakeV6PricedQuoteDryRunResponse | null>(null);
  const persistedCommercialInputs = useMemo(() => {
    const finishRaw = payload?.finish_setup;
    if (finishRaw == null || typeof finishRaw !== "object" || Array.isArray(finishRaw)) {
      return null;
    }
    return readIntakeV6OfferCommercialInputs(
      (finishRaw as Record<string, unknown>).commercial_inputs,
    );
  }, [payload]);
  const [commercialInputs, setCommercialInputs] = useState<IntakeV6OfferCommercialInputs>(() =>
    ({ ...resolveIntakeV6OfferCommercialDefaults(null, persistedCommercialInputs), vatPercent: vatPct }),
  );
  const [commercialInputsDirty, setCommercialInputsDirty] = useState(false);
  const [productionDryRun, setProductionDryRun] = useState<IntakeV6ProductionTaskDryRunResponse | null>(
    null,
  );
  const [aiSemanticPreview, setAiSemanticPreview] =
    useState<IntakeV6AiInformationalAssistPreviewResponse | null>(null);
  const [handoffPreview, setHandoffPreview] = useState<IntakeV6ProductionHandoffPreviewResponse | null>(
    null,
  );
  const [quoteHandoffPreview, setQuoteHandoffPreview] = useState<IntakeV6QuoteHandoffPreviewResponse | null>(
    null,
  );
  const [taskGenerationDryRun, setTaskGenerationDryRun] =
    useState<IntakeV6TaskGenerationDryRunResponse | null>(null);
  const [orderBoundReadiness, setOrderBoundReadiness] =
    useState<IntakeV6OrderBoundTaskReadinessResponse | null>(null);
  const [breakdown, setBreakdown] = useState<IntakeV6MaterialBreakdownResponse | null>(null);
  const [logicalListReadModel, setLogicalListReadModel] = useState<IntakeV6LogicalListReadModelResponse | null>(null);
  const [binding, setBinding] = useState<IntakeV6ProductSystemBindingResponse | null>(null);
  const [productDefinitionPreview, setProductDefinitionPreview] = useState<ProductDefinitionPreview | null>(null);
  const [runtimeCaptureReadModel, setRuntimeCaptureReadModel] =
    useState<IntakeV6RuntimeCaptureReadModelResponse | null>(null);
  const [productTruthPromotionPlanner, setProductTruthPromotionPlanner] =
    useState<IntakeV6ProductTruthPromotionPlannerResponse | null>(null);
  const templateFormContract = templateContract.contract;
  const modularTemplateCode =
    binding?.template_code?.trim() ||
    templateCode?.trim() ||
    state.workspace?.template_code?.trim() ||
    null;
  const modularFormContractHook = useModularFormContract(modularTemplateCode);
  const svgSourcePayload =
    payload?.svg_source != null &&
    typeof payload.svg_source === "object" &&
    !Array.isArray(payload.svg_source)
      ? (payload.svg_source as Record<string, unknown>)
      : null;
  const modularAwareness = useModularFormAwareness({
    contract: modularFormContractHook.contract,
    loading: modularFormContractHook.loading,
    error: modularFormContractHook.error,
    finishSetup: form as unknown as Record<string, unknown>,
    quoteGeometry: quoteGeometry as unknown as Record<string, unknown> | null,
    svgSource: svgSourcePayload,
    analysisReady,
  });
  const backboneRuntimeState = useMemo(
    () => ({
      layerRoleSetup: state.layerRoleConfirmation ? layerRoleConfirmationToV6Setup(state.layerRoleConfirmation) : null,
    }),
    [state.layerRoleConfirmation],
  );
  const volumAluminumModuleLinks = useMemo(
    () =>
      (binding?.module_links ?? []).filter(
        (module) =>
          module.trigger_field === "volum_aluminum_module_template_code" ||
          module.module_template_code.includes("VOLUM-ALUMINUM") ||
          module.module_template_code.includes("VOLUM-ALUMINIU"),
      ),
    [binding],
  );
  const selectedVolumAluminumModuleCode =
    form.volum_aluminum_module_template_code ?? volumAluminumModuleLinks[0]?.module_template_code ?? "";
  const selectedVolumAluminumModule = useMemo(
    () =>
      volumAluminumModuleLinks.find(
        (module) => module.module_template_code === selectedVolumAluminumModuleCode,
      ) ?? null,
    [selectedVolumAluminumModuleCode, volumAluminumModuleLinks],
  );
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [loadingPricingPreview, setLoadingPricingPreview] = useState(false);
  const [loadingProductionDryRun, setLoadingProductionDryRun] = useState(false);
  const [loadingAiSemanticPreview, setLoadingAiSemanticPreview] = useState(false);
  const [loadingHandoffPreview, setLoadingHandoffPreview] = useState(false);
  const [loadingQuoteHandoffPreview, setLoadingQuoteHandoffPreview] = useState(false);
  const [loadingTaskGenerationDryRun, setLoadingTaskGenerationDryRun] = useState(false);
  const [loadingOrderBoundReadiness, setLoadingOrderBoundReadiness] = useState(false);
  const [loadingBreakdown, setLoadingBreakdown] = useState(false);
  const [loadingRuntimeCaptureReadModel, setLoadingRuntimeCaptureReadModel] = useState(false);
  const [loadingProductTruthPromotionPlanner, setLoadingProductTruthPromotionPlanner] = useState(false);
  const [localSheetQuoteOverride, setLocalSheetQuoteOverride] =
    useState<IntakeV6SheetFootprintOverride | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [runtimeCaptureReadModelError, setRuntimeCaptureReadModelError] = useState<string | null>(null);
  const [productTruthPromotionPlannerError, setProductTruthPromotionPlannerError] = useState<string | null>(null);
  const [previewRefresh, setPreviewRefresh] = useState<ReviewPreviewRefreshState>(
    INITIAL_REVIEW_PREVIEW_REFRESH,
  );
  const autosaveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const commercialSaveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const artworkSectionRef = useRef<HTMLDivElement | null>(null);
  const liveCalcRef = useRef<HTMLDivElement | null>(null);
  const diagnosticRef = useRef<HTMLDivElement | null>(null);
  const artworkHighlightTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pendingDirtyDomainsRef = useRef<Set<IntakeV6ReviewDirtyDomain>>(new Set());
  const pendingAutosavePolicyRef = useRef<ReviewAutosavePolicy>("short");
  const [highlightArtworkUnconfirmed, setHighlightArtworkUnconfirmed] = useState(false);
  const [reviewTab, setReviewTab] = useState<IntakeV6ReviewTabId>("finisaje");
  const [diagnosticSectionOpen, setDiagnosticSectionOpen] = useState(false);
  const localRevisionRef = useRef(0);
  const autosaveRequestRef = useRef(0);
  const commercialInputsSyncKeyRef = useRef<string | null>(null);

  const selectorPendingSave = useMemo(
    () => isIntakeV6SelectorStatePendingSave(form, payload, letterGroups, artworkFinishes),
    [form, payload, letterGroups, artworkFinishes],
  );

  const autosaveIdentityKey = useMemo(
    () =>
      JSON.stringify({
        form,
        letterGroups,
        artworkFinishes,
        artworkComplexityDecisions,
        mountingTemplateAreaFallbackM2,
        commercialInputs,
      }),
    [
      form,
      letterGroups,
      artworkFinishes,
      artworkComplexityDecisions,
      mountingTemplateAreaFallbackM2,
      commercialInputs,
    ],
  );

  const commercialInputsPendingSave = useMemo(
    () =>
      commercialInputsDirty &&
      JSON.stringify(serializeIntakeV6OfferCommercialInputs(commercialInputs)) !==
      JSON.stringify(
        serializeIntakeV6OfferCommercialInputs(
          {
            ...(persistedCommercialInputs ?? resolveIntakeV6OfferCommercialDefaults(pricingPreview)),
            vatPercent: vatPct,
          },
        ),
      ),
    [commercialInputs, commercialInputsDirty, persistedCommercialInputs, pricingPreview, vatPct],
  );
  const syncedCommercialInputs = useMemo(
    () => ({
      ...resolveIntakeV6OfferCommercialDefaults(
        pricingPreview,
        persistedCommercialInputs == null
          ? undefined
          : serializeIntakeV6OfferCommercialInputs(persistedCommercialInputs),
      ),
      vatPercent: vatPct,
    }),
    [persistedCommercialInputs, pricingPreview, vatPct],
  );
  const syncedCommercialInputsKey = useMemo(
    () =>
      `${workspaceId ?? "none"}:${JSON.stringify(
        serializeIntakeV6OfferCommercialInputs(syncedCommercialInputs),
      )}`,
    [workspaceId, syncedCommercialInputs],
  );
  const localReviewEditsPending = selectorPendingSave || commercialInputsPendingSave || saving;

  const sheetQuoteOverrideFromPayload = useMemo(() => {
    const raw = payload?.sheet_quote_override;
    if (raw != null && typeof raw === "object" && !Array.isArray(raw)) {
      return raw as IntakeV6SheetFootprintOverride;
    }
    return null;
  }, [payload]);

  const effectiveSheetQuoteOverride = localSheetQuoteOverride ?? sheetQuoteOverrideFromPayload;

  const bumpPreviewRefresh = useCallback((domains: Iterable<IntakeV6ReviewDirtyDomain>) => {
    const groups = resolveIntakeV6ReviewRefetchGroups(domains);
    if (groups.length === 0) return;
    setPreviewRefresh((prev) => {
      const next = { ...prev };
      for (const group of groups) {
        next[group] += 1;
      }
      return next;
    });
  }, []);

  const handleSheetFootprintOverrideSaved = useCallback(() => {
    bumpPreviewRefresh(["sheet_footprint"]);
    if (!workspaceId) return;
    void getIntakeV6Workspace(workspaceId)
      .then((workspace) => {
        const raw = workspace.payload?.sheet_quote_override;
        if (raw != null && typeof raw === "object" && !Array.isArray(raw)) {
          setLocalSheetQuoteOverride(raw as IntakeV6SheetFootprintOverride);
        }
      })
        .catch(() => {});
      }, [bumpPreviewRefresh, workspaceId]);

  const operatorWorkSummary = useMemo(
    () =>
      buildIntakeV6OperatorWorkSummaryCounts({
        geometry: quoteGeometry,
        nestingPreview: breakdown?.nesting_preview,
        finish: form,
      }),
    [quoteGeometry, breakdown?.nesting_preview, form],
  );

  const faceBackPrepDraft = useIntakeV6FaceBackPrepCostDraft(workspaceId ?? null, analysisReady);

  useEffect(() => {
    const finish = finishFromPayload(payload);
    const nextForm = syncLighting(
      applyMountingTemplateMinimumArea(finish, mountingTemplateAreaFallbackM2),
    );
    const nextLetterGroups = mergeLetterGroupFinishes(
      deriveLetterGroupsFromAnalyzer(
        state.analyzerReport as SvgAnalysisCoreReport | null,
        state.layerRoleConfirmation,
        finish.return_depth_mm ?? DEFAULT_RETURN_DEPTH_MM,
      ),
      letterGroupFinishesFromPayload(payload),
    );
    const nextArtworkFinishes = mergeArtworkFinishes(
      deriveArtworkFinishesFromAnalyzer(
        state.analyzerReport as SvgAnalysisCoreReport | null,
        state.layerRoleConfirmation,
        finish.return_depth_mm ?? DEFAULT_RETURN_DEPTH_MM,
      ),
      artworkFinishesFromPayload(payload),
    );
    const nextComplexity = artworkComplexityFromReport(
      state.analyzerReport as SvgAnalysisCoreReport | null,
    );
    const nextArtworkComplexityDecisions = mergeArtworkComplexityDecisions(
      finish.artwork_complexity_decisions,
      nextComplexity?.assessments ?? [],
    );
    if (!localReviewEditsPending) {
      if (buildFinishSetupSyncSignature(form) !== buildFinishSetupSyncSignature(nextForm)) {
        setForm(nextForm);
      }
      if (buildJsonSignature(letterGroups) !== buildJsonSignature(nextLetterGroups)) {
        setLetterGroups(nextLetterGroups);
      }
      if (buildJsonSignature(artworkFinishes) !== buildJsonSignature(nextArtworkFinishes)) {
        setArtworkFinishes(nextArtworkFinishes);
      }
      if (
        buildJsonSignature(artworkComplexityDecisions) !==
        buildJsonSignature(nextArtworkComplexityDecisions)
      ) {
        setArtworkComplexityDecisions(nextArtworkComplexityDecisions);
      }
    }
  }, [
    payload,
    letterPerimeterM,
    emblemOutboxAreaM2,
    state.analyzerReport,
    state.layerRoleConfirmation,
    state.workspace?.id,
    mountingTemplateAreaFallbackM2,
    localReviewEditsPending,
    form,
    letterGroups,
    artworkFinishes,
    artworkComplexityDecisions,
  ]);

  useEffect(() => {
    if (!workspaceId) return;
    let cancelled = false;
    void getIntakeV6ProductSystemBinding(workspaceId)
      .then((response) => {
        if (!cancelled) setBinding(response);
      })
      .catch(() => {
        if (!cancelled) setBinding(null);
      });
    return () => {
      cancelled = true;
    };
  }, [workspaceId, analysisIdentityKey, analysisReady]);

  useEffect(() => {
    if (!workspaceId || !analysisReady || !templateCode) {
      setProductDefinitionPreview(null);
      return;
    }
    let cancelled = false;
    void getProductDefinitionPreview(templateCode, workspaceId)
      .then((response) => {
        if (!cancelled) setProductDefinitionPreview(response);
      })
      .catch((error) => {
        if (cancelled) return;
        if (error instanceof ProductDefinitionPreviewNotFoundError) {
          setProductDefinitionPreview(null);
          return;
        }
        setProductDefinitionPreview(null);
      });
    return () => {
      cancelled = true;
    };
  }, [workspaceId, analysisReady, templateCode]);

  useEffect(() => {
    if (!workspaceId) return;
    let cancelled = false;
    setLoadingPreview(true);
    void getIntakeV6TaskPreview(workspaceId)
      .then((response) => {
        if (!cancelled) setPreview(response);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Task preview indisponibil.");
        }
      })
      .finally(() => {
        if (!cancelled) setLoadingPreview(false);
      });
    return () => {
      cancelled = true;
    };
  }, [workspaceId, previewRefresh.taskPreview, analysisIdentityKey, analysisReady]);

  useEffect(() => {
    if (!workspaceId || !analysisReady) {
      setBreakdown(null);
      return;
    }
    let cancelled = false;
    const showBreakdownLoading = breakdown == null;
    if (showBreakdownLoading) {
      setLoadingBreakdown(true);
    }
    void getIntakeV6MaterialBreakdown(workspaceId)
      .then((response) => {
        if (!cancelled) setBreakdown(response);
      })
      .catch(() => {
        if (!cancelled) setBreakdown(null);
      })
      .finally(() => {
        if (!cancelled && showBreakdownLoading) setLoadingBreakdown(false);
      });
    return () => {
      cancelled = true;
    };
  }, [workspaceId, analysisIdentityKey, analysisReady, previewRefresh.breakdown]);

  useEffect(() => {
    if (!workspaceId || !analysisReady) {
      setPricingPreview(null);
      return;
    }
    let cancelled = false;
    setLoadingPricingPreview(true);
    void getIntakeV6PricingInputPreview(workspaceId)
      .then((response) => {
        if (!cancelled) setPricingPreview(response);
      })
      .catch(() => {
        if (!cancelled) setPricingPreview(null);
      })
      .finally(() => {
        if (!cancelled) setLoadingPricingPreview(false);
      });
    return () => {
      cancelled = true;
    };
  }, [workspaceId, analysisIdentityKey, analysisReady, previewRefresh.pricing]);

  useEffect(() => {
    if (!workspaceId || !analysisReady) {
      setPricedQuoteDryRun(null);
      return;
    }
    let cancelled = false;
    void getIntakeV6PricedQuoteDryRun(workspaceId)
      .then((response) => {
        if (!cancelled) setPricedQuoteDryRun(response);
      })
      .catch(() => {
        if (!cancelled) setPricedQuoteDryRun(null);
      });
    return () => {
      cancelled = true;
    };
  }, [workspaceId, analysisIdentityKey, analysisReady, previewRefresh.pricedQuote]);

  useEffect(() => {
    if (!workspaceId || !analysisReady) {
      setLogicalListReadModel(null);
      return;
    }
    let cancelled = false;
    void getIntakeV6LogicalListReadModel(workspaceId)
      .then((response) => {
        if (!cancelled) setLogicalListReadModel(response);
      })
      .catch(() => {
        if (!cancelled) setLogicalListReadModel(null);
      });
    return () => {
      cancelled = true;
    };
  }, [workspaceId, analysisIdentityKey, analysisReady, previewRefresh.breakdown, previewRefresh.pricedQuote]);

  useEffect(() => {
    if (!workspaceId) {
      setRuntimeCaptureReadModel(null);
      setRuntimeCaptureReadModelError(null);
      setLoadingRuntimeCaptureReadModel(false);
      return;
    }
    let cancelled = false;
    const resetModel = runtimeCaptureReadModel?.workspace_id !== workspaceId;
    if (resetModel) {
      setRuntimeCaptureReadModel(null);
    }
    setRuntimeCaptureReadModelError(null);
    setLoadingRuntimeCaptureReadModel(true);
    void getIntakeV6RuntimeCaptureReadModel(workspaceId)
      .then((response) => {
        if (!cancelled) setRuntimeCaptureReadModel(response);
      })
      .catch((err) => {
        if (!cancelled) {
          if (resetModel) {
            setRuntimeCaptureReadModel(null);
          }
          setRuntimeCaptureReadModelError(
            err instanceof Error ? err.message : "Runtime capture read model indisponibil.",
          );
        }
      })
      .finally(() => {
        if (!cancelled) setLoadingRuntimeCaptureReadModel(false);
      });
    return () => {
      cancelled = true;
    };
  }, [workspaceId, state.workspace?.updated_at]);

  useEffect(() => {
    if (!workspaceId) {
      setProductTruthPromotionPlanner(null);
      setProductTruthPromotionPlannerError(null);
      setLoadingProductTruthPromotionPlanner(false);
      return;
    }
    let cancelled = false;
    const resetPlanner = productTruthPromotionPlanner?.workspace_id !== workspaceId;
    if (resetPlanner) {
      setProductTruthPromotionPlanner(null);
    }
    setProductTruthPromotionPlannerError(null);
    setLoadingProductTruthPromotionPlanner(true);
    void getIntakeV6ProductTruthPromotionPlanner(workspaceId)
      .then((response) => {
        if (!cancelled) setProductTruthPromotionPlanner(response);
      })
      .catch((err) => {
        if (!cancelled) {
          if (resetPlanner) {
            setProductTruthPromotionPlanner(null);
          }
          setProductTruthPromotionPlannerError(
            err instanceof Error ? err.message : "Product truth promotion planner indisponibil.",
          );
        }
      })
      .finally(() => {
        if (!cancelled) setLoadingProductTruthPromotionPlanner(false);
      });
    return () => {
      cancelled = true;
    };
  }, [workspaceId, state.workspace?.updated_at]);

  useEffect(() => {
    if (commercialInputsDirty && commercialInputsPendingSave) return;
    if (commercialInputsSyncKeyRef.current === syncedCommercialInputsKey) return;
    commercialInputsSyncKeyRef.current = syncedCommercialInputsKey;
    setCommercialInputsDirty(false);
    setCommercialInputs(syncedCommercialInputs);
  }, [commercialInputsDirty, commercialInputsPendingSave, syncedCommercialInputs, syncedCommercialInputsKey]);

  useEffect(() => {
    if (!workspaceId || !analysisReady) {
      setProductionDryRun(null);
      return;
    }
    let cancelled = false;
    setLoadingProductionDryRun(true);
    void getIntakeV6ProductionTaskDryRun(workspaceId)
      .then((response) => {
        if (!cancelled) setProductionDryRun(response);
      })
      .catch(() => {
        if (!cancelled) setProductionDryRun(null);
      })
      .finally(() => {
        if (!cancelled) setLoadingProductionDryRun(false);
      });
    return () => {
      cancelled = true;
    };
  }, [workspaceId, analysisIdentityKey, analysisReady, previewRefresh.productionDryRun]);

  useEffect(() => {
    if (!workspaceId || !analysisReady) {
      setAiSemanticPreview(null);
      return;
    }
    let cancelled = false;
    setLoadingAiSemanticPreview(true);
    void getIntakeV6AiInformationalAssistCandidate(workspaceId)
      .then((response) => {
        if (!cancelled) setAiSemanticPreview(response);
      })
      .catch(() => {
        if (!cancelled) setAiSemanticPreview(null);
      })
      .finally(() => {
        if (!cancelled) setLoadingAiSemanticPreview(false);
      });
    return () => {
      cancelled = true;
    };
  }, [workspaceId, analysisIdentityKey, analysisReady]);

  useEffect(() => {
    if (!workspaceId || !analysisReady) {
      setHandoffPreview(null);
      return;
    }
    let cancelled = false;
    setLoadingHandoffPreview(true);
    void getIntakeV6ProductionHandoffPreview(workspaceId)
      .then((response) => {
        if (!cancelled) setHandoffPreview(response);
      })
      .catch(() => {
        if (!cancelled) setHandoffPreview(null);
      })
      .finally(() => {
        if (!cancelled) setLoadingHandoffPreview(false);
      });
    return () => {
      cancelled = true;
    };
  }, [workspaceId, analysisIdentityKey, analysisReady, previewRefresh.productionHandoff]);

  useEffect(() => {
    if (!workspaceId || !analysisReady) {
      setTaskGenerationDryRun(null);
      return;
    }
    let cancelled = false;
    setLoadingTaskGenerationDryRun(true);
    void getIntakeV6TaskGenerationDryRun(workspaceId)
      .then((response) => {
        if (!cancelled) setTaskGenerationDryRun(response);
      })
      .catch(() => {
        if (!cancelled) setTaskGenerationDryRun(null);
      })
      .finally(() => {
        if (!cancelled) setLoadingTaskGenerationDryRun(false);
      });
    return () => {
      cancelled = true;
    };
  }, [workspaceId, analysisIdentityKey, analysisReady, previewRefresh.taskGeneration]);

  useEffect(() => {
    if (!workspaceId || !analysisReady) {
      setOrderBoundReadiness(null);
      return;
    }
    let cancelled = false;
    setLoadingOrderBoundReadiness(true);
    void getIntakeV6OrderBoundTaskReadiness(workspaceId)
      .then((response) => {
        if (!cancelled) setOrderBoundReadiness(response);
      })
      .catch(() => {
        if (!cancelled) setOrderBoundReadiness(null);
      })
      .finally(() => {
        if (!cancelled) setLoadingOrderBoundReadiness(false);
      });
    return () => {
      cancelled = true;
    };
  }, [workspaceId, analysisIdentityKey, analysisReady, previewRefresh.orderBoundReadiness]);

  useEffect(() => {
    if (!workspaceId || !analysisReady) {
      setQuoteHandoffPreview(null);
      return;
    }
    let cancelled = false;
    const showQuoteHandoffLoading = quoteHandoffPreview == null;
    if (showQuoteHandoffLoading) {
      setLoadingQuoteHandoffPreview(true);
    }
    const clientAnalysisHash = state.localFileHash ?? persistedSvgFileHash;
    void getIntakeV6QuoteHandoffPreview(workspaceId, clientAnalysisHash ?? undefined)
      .then((response) => {
        if (!cancelled) setQuoteHandoffPreview(response);
      })
      .catch(() => {
        if (!cancelled) setQuoteHandoffPreview(null);
      })
      .finally(() => {
        if (!cancelled && showQuoteHandoffLoading) setLoadingQuoteHandoffPreview(false);
      });
    return () => {
      cancelled = true;
    };
  }, [
    workspaceId,
    analysisIdentityKey,
    analysisReady,
    previewRefresh.quoteHandoff,
    state.localFileHash,
    persistedSvgFileHash,
  ]);

  const activeTasks = useMemo(
    () => preview?.items.filter((item) => item.active) ?? [],
    [preview],
  );

  function markLocalFinishChanged(
    domains: Iterable<IntakeV6ReviewDirtyDomain>,
    autosavePolicy: ReviewAutosavePolicy = "short",
  ) {
    localRevisionRef.current += 1;
    for (const domain of domains) {
      pendingDirtyDomainsRef.current.add(domain);
    }
    if (autosavePolicy === "long") {
      pendingAutosavePolicyRef.current = "long";
    }
  }

  function updateForm(
    patch: Partial<IntakeV6FinishSetup>,
    options: {
      domains: IntakeV6ReviewDirtyDomain[];
      autosavePolicy?: ReviewAutosavePolicy;
    },
  ) {
    markLocalFinishChanged(options.domains, options.autosavePolicy);
    setForm((prev) => syncLighting({ ...prev, ...patch, confirmed: false }));
  }

  function syncFormFromLayerFinishes(args: {
    letterGroups: IntakeV6LetterGroupFinish[];
    artworkFinishes: IntakeV6ArtworkFinish[];
  }, options: { domains: IntakeV6ReviewDirtyDomain[]; autosavePolicy?: ReviewAutosavePolicy }) {
    markLocalFinishChanged(options.domains, options.autosavePolicy);
    setForm((prev) => {
      const layered = syncIntakeV6FinishPayloadFromLayerFinishes(
        {
          ...prev,
          letter_group_finishes: args.letterGroups,
          artwork_finishes: args.artworkFinishes,
          confirmed: false,
        },
        args.letterGroups,
        args.artworkFinishes,
      );
      return syncLighting(layered);
    });
  }

  function buildCurrentFinishBody(
    confirmed = true,
    commercialInputsOverride?: IntakeV6OfferCommercialInputs,
  ): IntakeV6FinishSetup {
    return syncLighting(
      syncIntakeV6FinishPayloadFromLayerFinishes(
        {
          ...form,
          face_vinyl_roll_width_mm: normalizeFaceVinylRollWidthMm(
            form.face_finish_type,
            form.face_vinyl_roll_width_mm,
          ),
          mounting_template_area_m2:
            form.mounting_template_enabled !== false
              ? resolveMountingTemplateAreaM2(
                  form.mounting_template_area_m2,
                  mountingTemplateAreaFallbackM2,
                )
              : form.mounting_template_area_m2,
          letter_group_finishes: letterGroups,
          artwork_finishes: artworkFinishes,
          artwork_complexity_decisions: artworkComplexityDecisions,
          commercial_inputs: serializeIntakeV6OfferCommercialInputs(
            commercialInputsOverride ?? commercialInputs,
          ),
          confirmed,
        },
        letterGroups,
        artworkFinishes,
      ),
    );
  }

  function updateSelectedPsuWatts(watts: number) {
    updateForm(
      {
        selected_psu_watts: watts,
        psu_configuration: [watts],
      },
      { domains: ["lighting"] },
    );
  }

  async function saveCurrentFinish(
    confirmed = true,
    commercialInputsOverride?: IntakeV6OfferCommercialInputs,
  ) {
    if (!workspaceId) return;
    const requestId = autosaveRequestRef.current + 1;
    autosaveRequestRef.current = requestId;
    const revisionAtStart = localRevisionRef.current;
    setSaving(true);
    setError(null);
    try {
      const body = buildCurrentFinishBody(confirmed, commercialInputsOverride);
      const pendingDomains = new Set(pendingDirtyDomainsRef.current);
      const workspace = await saveFinishSetup(body);
      if (
        workspace &&
        requestId === autosaveRequestRef.current &&
        revisionAtStart === localRevisionRef.current
      ) {
        const nextFinish = finishFromPayload(workspace.payload as Record<string, unknown>);
        const nextPayload = workspace.payload as Record<string, unknown>;
        const syncedNextForm = syncLighting(nextFinish);
        const nextLetterGroups = letterGroupFinishesFromPayload(nextPayload);
        const nextArtworkFinishes = artworkFinishesFromPayload(nextPayload);
        const nextCommercialInputs = resolveIntakeV6OfferCommercialDefaults(
          pricingPreview,
          nextFinish.commercial_inputs,
        );
        const nextSettingsVatCommercialInputs = { ...nextCommercialInputs, vatPercent: vatPct };
        if (buildFinishSetupSyncSignature(syncedNextForm) !== buildFinishSetupSyncSignature(form)) {
          setForm(syncedNextForm);
        }
        if (buildJsonSignature(nextLetterGroups) !== buildJsonSignature(letterGroups)) {
          setLetterGroups(nextLetterGroups);
        }
        if (buildJsonSignature(nextArtworkFinishes) !== buildJsonSignature(artworkFinishes)) {
          setArtworkFinishes(nextArtworkFinishes);
        }
        if (
          buildJsonSignature(serializeIntakeV6OfferCommercialInputs(commercialInputs)) !==
          buildJsonSignature(serializeIntakeV6OfferCommercialInputs(nextSettingsVatCommercialInputs))
        ) {
          setCommercialInputsDirty(false);
          setCommercialInputs(nextSettingsVatCommercialInputs);
        }
        pendingDirtyDomainsRef.current.clear();
        pendingAutosavePolicyRef.current = "short";
        bumpPreviewRefresh(pendingDomains.size > 0 ? pendingDomains : ["lighting", "face_finish", "artwork_finish", "backing", "mounting", "template", "commercial_preview"]);
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Salvare finisaje esuata.";
      setError(msg);
      toast.error("Salvare finisaje eșuată", { description: msg, duration: 6000 });
    } finally {
      if (requestId === autosaveRequestRef.current) {
        setSaving(false);
      }
    }
  }

  useEffect(() => {
    if (!workspaceId || !analysisReady || !selectorPendingSave) return;
    if (autosaveTimerRef.current) {
      clearTimeout(autosaveTimerRef.current);
    }
    const debounceMs = pendingAutosavePolicyRef.current === "long" ? 1400 : 700;
    autosaveTimerRef.current = setTimeout(() => {
      autosaveTimerRef.current = null;
      void saveCurrentFinish(true);
    }, debounceMs);
    return () => {
      if (autosaveTimerRef.current) {
        clearTimeout(autosaveTimerRef.current);
        autosaveTimerRef.current = null;
      }
    };
  }, [workspaceId, analysisReady, selectorPendingSave, commercialInputsPendingSave, autosaveIdentityKey]);

  useEffect(() => {
    return () => {
      if (commercialSaveTimerRef.current) {
        clearTimeout(commercialSaveTimerRef.current);
        commercialSaveTimerRef.current = null;
      }
    };
  }, []);

  const psuLabel =
    form.psu_configuration && form.psu_configuration.length > 0
      ? form.psu_configuration.map((w) => `${w}W`).join(" + ")
      : "—";

  const emblemLightingMode = normalizeEmblemLightingMode(form.emblem_lighting_mode);
  const ledModulePowerW = normalizeIntakeV6LedModuleWattage(form.led_module_power_w);
  const isLedModules = (form.lighting_system_type ?? "led_modules") !== "led_strip";
  const ledModuleCount = isLedModules
    ? form.letter_led_module_count ?? computeIntakeV6LedModuleCount(letterPerimeterM)
    : null;
  const emblemLedModuleCount = isLedModules ? form.emblem_led_module_count : null;
  const totalLedModuleCount = isLedModules
    ? form.total_led_module_count ?? form.led_module_count ?? ledModuleCount
    : null;
  const mountingUsesBars =
    form.mounting_system === "steel_bars" || form.mounting_system === "aluminum_bars";

  const artworkOnlyRequiresDecision = useMemo(
    () =>
      detectArtworkOnlyRequiresDecision(
        state.analyzerReport as SvgAnalysisCoreReport | null,
        state.layerRoleConfirmation,
      ),
    [state.analyzerReport, state.layerRoleConfirmation],
  );
  const effectiveLetterGroups = useMemo(
    () =>
      sanitizeLetterGroupsForArtworkOnlyGuard(
        letterGroups,
        state.analyzerReport as SvgAnalysisCoreReport | null,
        state.layerRoleConfirmation,
      ),
    [letterGroups, state.analyzerReport, state.layerRoleConfirmation],
  );
  const returnCantReadonlyAwareness = useMemo(() => {
    const svgFileName =
      typeof svgSourcePayload?.file_name === "string"
        ? svgSourcePayload.file_name
        : typeof svgSourcePayload?.fileName === "string"
          ? svgSourcePayload.fileName
          : null;
    const svgSourceHash =
      typeof svgSourcePayload?.file_hash === "string"
        ? svgSourcePayload.file_hash
        : typeof svgSourcePayload?.sourceHash === "string"
          ? svgSourcePayload.sourceHash
          : null;

    const productTruthDraft = buildProductTruthDraft({
      workspaceId,
      workspaceCode: state.workspace?.workspace_code ?? null,
      intakeId: workspaceId,
      templateCode: "TPL-VOLUMETRIC-LETTERS_v2",
      productFamily: "volumetric_letters",
      generatedAt: "2026-07-08T00:00:00.000Z",
      svgSource: {
        fileName: svgFileName,
        sourceHash: svgSourceHash,
        analysisStatus: analysisReady ? "parsed" : "missing",
      },
      quoteGeometry: quoteGeometry
        ? {
            width_mm: quoteGeometry.width_mm,
            height_mm: quoteGeometry.height_mm,
            letter_count: quoteGeometry.letter_count,
            face_area_m2: quoteGeometry.face_area_m2,
            return_material_perimeter_ml: quoteGeometry.return_material_perimeter_ml,
            geometry_source: quoteGeometry.geometry_source,
            confirmed: quoteGeometry.confirmed,
          }
        : null,
      layerRoleSetup: state.layerRoleConfirmation
        ? layerRoleConfirmationToV6Setup(state.layerRoleConfirmation)
        : null,
      finishSetup: {
        ...form,
        letter_group_finishes: effectiveLetterGroups,
        artwork_finishes: artworkFinishes,
      },
    });

    return mapReturnCantTruthFieldsReadonly({
      templateCode: "TPL-VOLUMETRIC-LETTERS_v2",
      rootType: "product_template",
      quoteMode: "product_total",
      productTruthDraft,
      quoteGeometry: quoteGeometry
        ? {
            letter_perimeter_m: quoteGeometry.letter_perimeter_m,
            geometry_source: quoteGeometry.geometry_source,
            confirmed: quoteGeometry.confirmed,
          }
        : null,
    });
  }, [analysisReady, artworkFinishes, effectiveLetterGroups, form, quoteGeometry, state.layerRoleConfirmation, state.workspace?.workspace_code, svgSourcePayload, workspaceId]);
  const modularAttentionWarnings = useMemo(
    () => resolveModuleActivationAttentionWarnings(modularAwareness.preview),
    [modularAwareness.preview],
  );
  const effectiveReviewWarnings = useMemo(() => {
    const handoffWarnings = resolveArtworkOnlyReviewWarnings(
      state.analyzerReport as SvgAnalysisCoreReport | null,
      state.layerRoleConfirmation,
      quoteHandoffPreview?.review_warnings,
    );
    return [...new Set([...handoffWarnings, ...modularAttentionWarnings])];
  }, [
    state.analyzerReport,
    state.layerRoleConfirmation,
    quoteHandoffPreview?.review_warnings,
    modularAttentionWarnings,
  ]);

  useEffect(() => {
    if (!artworkOnlyRequiresDecision || letterGroups.length === 0) return;
    setLetterGroups([]);
    syncFormFromLayerFinishes(
      { letterGroups: [], artworkFinishes },
      { domains: ["face_finish", "artwork_finish"] },
    );
  }, [artworkOnlyRequiresDecision, letterGroups.length, artworkFinishes]);

  const hideGlobalFinish = shouldHideGlobalFinishSettings({
    letterGroupCount: effectiveLetterGroups.length,
    artworkCount: artworkFinishes.length,
  });

  const operatorCantPerimeterM = resolveIntakeV6OperatorCantPerimeterDisplay({
    geometryMetrics,
    geometry: quoteGeometry,
    letterGroups,
    artworkFinishes,
  }).displayM;
  const ledDisplayPerimeterM = geometryMetrics.ledExteriorPerimeterM ?? letterPerimeterM;
  const emblemLightingDepthMm = resolveIntakeV6EmblemLightingDepthMm({
    finish: form,
    artworkFinishes,
    letterGroups,
    fallbackDepthMm: DEFAULT_RETURN_DEPTH_MM,
  });
  const reviewHandoffSurfacing = useMemo(() => {
    const allArtworkFinishesConfirmed =
      artworkFinishes.length === 0 || artworkFinishes.every((row) => row.confirmed);
    return buildReviewHandoffSurfacing({
      handoff: quoteHandoffPreview,
      handoffOptions: {
        loading: loadingQuoteHandoffPreview && quoteHandoffPreview == null,
      },
      containsMissingPrices: breakdown?.totals.contains_missing_prices === true,
      allArtworkFinishesConfirmed,
    });
  }, [
    artworkFinishes,
    quoteHandoffPreview,
    loadingQuoteHandoffPreview,
    breakdown?.totals.contains_missing_prices,
  ]);
  const operatorBlockerBannerDisplay = useMemo(
    () =>
      buildOperatorBlockerBannerDisplay({
        surfacing: reviewHandoffSurfacing,
        handoffLoading: loadingQuoteHandoffPreview && quoteHandoffPreview == null,
        runtimeModel: runtimeCaptureReadModel,
        runtimeLoading: loadingRuntimeCaptureReadModel,
        plannerModel: productTruthPromotionPlanner,
        plannerLoading: loadingProductTruthPromotionPlanner,
      }),
    [
      reviewHandoffSurfacing,
      loadingQuoteHandoffPreview,
      quoteHandoffPreview,
      runtimeCaptureReadModel,
      loadingRuntimeCaptureReadModel,
      productTruthPromotionPlanner,
      loadingProductTruthPromotionPlanner,
    ],
  );
  const reviewDiagnosticEntryCount = useMemo(
    () =>
      buildReviewDiagnosticEntryCount({
        runtimeModel: runtimeCaptureReadModel,
        plannerModel: productTruthPromotionPlanner,
        backbone: modularFormContractHook.contract?.form_system_backbone ?? null,
        runtimeState: backboneRuntimeState,
      }),
    [
      runtimeCaptureReadModel,
      productTruthPromotionPlanner,
      modularFormContractHook.contract?.form_system_backbone,
      backboneRuntimeState,
    ],
  );
  const reviewReadinessDisplay = useMemo(
    () =>
      resolveReviewReadinessDisplay(state.workspace?.readiness_status, quoteHandoffPreview, {
        loading: loadingQuoteHandoffPreview && quoteHandoffPreview == null,
      }),
    [state.workspace?.readiness_status, quoteHandoffPreview, loadingQuoteHandoffPreview],
  );
  const artworkDecisionMessages = useMemo(
    () => collectArtworkUndecidedWarnings(effectiveReviewWarnings),
    [effectiveReviewWarnings],
  );
  const stepOneConfirmedArtworkLayerKeys = useMemo(() => {
    const keys = new Set<string>();
    for (const layer of state.layerRoleConfirmation?.layers ?? []) {
      const role = layer.confirmedRole ?? layer.autoRole;
      if (
        layer.confirmationState === "confirmed" &&
        (role === "printed_artwork" || role === "logo" || role === "policromie")
      ) {
        keys.add(layer.layerKey);
        if (layer.layerName) keys.add(layer.layerName);
      }
    }
    return keys;
  }, [state.layerRoleConfirmation]);
  const allArtworkConfirmedInStepOne =
    artworkFinishes.length > 0 &&
    artworkFinishes.every((row) => stepOneConfirmedArtworkLayerKeys.has(row.layer_key) || stepOneConfirmedArtworkLayerKeys.has(row.layer_name));
  const hasUnconfirmedArtwork = artworkFinishes.some((row) => !row.confirmed);
  const allArtworkConfirmed =
    artworkFinishes.length > 0 && artworkFinishes.every((row) => row.confirmed);
  const hasVectorResidualWarning = hasUnclassifiedVectorArtworkWarning(effectiveReviewWarnings);
  const showArtworkDecisionAlert = artworkDecisionMessages.length > 0 && !allArtworkConfirmedInStepOne;
  const artworkOnlyBlocked =
    artworkOnlyRequiresDecision && (!allArtworkConfirmedInStepOne || hasUnconfirmedArtwork);

  const pendingConfirmationCount = useMemo(() => {
    let count = 0;
    for (const group of effectiveLetterGroups) {
      if (resolveLayerCardStatus(group) === "warning") count += 1;
    }
    for (const row of artworkFinishes) {
      if (!row.confirmed) count += 1;
    }
    return count;
  }, [effectiveLetterGroups, artworkFinishes]);

  const layerRoleStats = useMemo(() => {
    const layers = state.layerRoleConfirmation?.layers ?? [];
    const total = layers.length;
    const confirmed = layers.filter((layer) => layer.confirmationState === "confirmed").length;
    return { total, confirmed };
  }, [state.layerRoleConfirmation]);

  const artworkConfirmStats = useMemo(() => {
    const total = artworkFinishes.length;
    const confirmed = artworkFinishes.filter((row) => row.confirmed).length;
    return { total, confirmed };
  }, [artworkFinishes]);

  const operatorConfirmationMissing = useMemo(() => {
    const blockers =
      quoteHandoffPreview?.fatal_blockers ?? quoteHandoffPreview?.blockers ?? [];
    return blockers.includes("operator_confirmation_missing");
  }, [quoteHandoffPreview]);

  const handleJumpToLiveCalc = useCallback(() => {
    liveCalcRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, []);

  const handleJumpToDiagnostic = useCallback(() => {
    setDiagnosticSectionOpen(true);
    window.requestAnimationFrame(() => {
      diagnosticRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }, []);

  const handleVerifyArtwork = useCallback(() => {
    setHighlightArtworkUnconfirmed(true);
    artworkSectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    if (artworkHighlightTimerRef.current) {
      clearTimeout(artworkHighlightTimerRef.current);
    }
    artworkHighlightTimerRef.current = setTimeout(() => {
      artworkHighlightTimerRef.current = null;
      setHighlightArtworkUnconfirmed(false);
    }, 4000);
  }, []);

  const handleJumpToPending = useCallback(() => {
    setReviewTab("finisaje");
    if (artworkDecisionMessages.length > 0 && !allArtworkConfirmedInStepOne) {
      handleVerifyArtwork();
      return;
    }
    const firstWarning = document.querySelector('[data-layer-card-status="warning"]');
    firstWarning?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [allArtworkConfirmedInStepOne, artworkDecisionMessages.length, handleVerifyArtwork]);

  useEffect(() => {
    return () => {
      if (artworkHighlightTimerRef.current) {
        clearTimeout(artworkHighlightTimerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    setOverlay({
      loading: loadingQuoteHandoffPreview && quoteHandoffPreview == null,
      containsMissingPrices: breakdown?.totals.contains_missing_prices === true,
      layersConfirmed: layerRoleStats.confirmed,
      layersTotal: layerRoleStats.total,
      artworkTotal: artworkConfirmStats.total,
      artworkConfirmed: artworkConfirmStats.confirmed,
      operatorConfirmationMissing,
      reviewWarnings: effectiveReviewWarnings,
      surfacing: reviewHandoffSurfacing,
      pendingSave: selectorPendingSave,
      pendingConfirmationCount,
      widthMm:
        (state.analyzerReport as SvgAnalysisCoreReport | null)?.document.widthMm ??
        quoteGeometry.width_mm,
      heightMm:
        (state.analyzerReport as SvgAnalysisCoreReport | null)?.document.heightMm ??
        quoteGeometry.height_mm,
      perimeterM: getFullVectorPerimeterM(geometryMetrics),
    });
    return () => setOverlay({});
  }, [
    setOverlay,
    loadingQuoteHandoffPreview,
    quoteHandoffPreview,
    breakdown?.totals.contains_missing_prices,
    layerRoleStats,
    artworkConfirmStats,
    operatorConfirmationMissing,
    reviewHandoffSurfacing,
    selectorPendingSave,
    pendingConfirmationCount,
    effectiveReviewWarnings,
    quoteGeometry.width_mm,
    quoteGeometry.height_mm,
    geometryMetrics,
    state.analyzerReport,
  ]);

  useEffect(() => {
    setHandlers({
      onJumpToPending: handleJumpToPending,
      onJumpToLiveCalc: handleJumpToLiveCalc,
      onJumpToLayers: () => trySetStep("layers"),
      onJumpToConfirm: () => trySetStep("confirm"),
    });
    return () =>
      setHandlers({
        onJumpToPending: undefined,
        onJumpToLiveCalc: undefined,
      });
  }, [setHandlers, trySetStep, handleJumpToPending, handleJumpToLiveCalc]);

  return (
    <section data-testid="intake-v6-step-review">
      {!analysisReady ? (
        <p
          className="mb-4 rounded border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-[12px] text-amber-100"
          data-testid="intake-v6-review-blocked"
        >
          Review este blocat: analiza SVG trebuie salvată și sincronizată (file hash) înainte de finisaje și
          breakdown.
        </p>
      ) : null}
      {analysisReady ? (
        <>
      <div className="mb-4">
        <IntakeV6ProductCompositionPanel
          payload={state.workspace?.payload as Record<string, unknown> | undefined}
          linkedSegments={productDefinitionPreview?.linked_template_runtime_segments ?? null}
          onConfirm={(items) => void confirmProductComposition(items)}
        />
      </div>
      {logoOnlyCandidateNotOfferable ? (
        <div
          className="mb-4 rounded border border-amber-500/35 bg-amber-500/10 px-4 py-3 text-[12px] leading-relaxed text-amber-100"
          data-testid="intake-v6-review-logo-only-commercial-guard"
        >
          <strong>{LOGO_ONLY_COMMERCIAL_GUARD_TITLE}</strong> · {LOGO_ONLY_COMMERCIAL_GUARD_MESSAGE}
        </div>
      ) : null}
      <div className="mb-4 lg:hidden" data-testid="intake-v6-review-price-spine-mobile">
        <IntakeV6LiveCalculationSummary
          breakdown={breakdown}
          faceBackDraft={faceBackPrepDraft.draft}
          loading={loadingBreakdown || faceBackPrepDraft.loading}
          layout="bar"
          operatorCantPerimeterM={operatorCantPerimeterM}
          pendingSave={localReviewEditsPending}
          letterGroups={effectiveLetterGroups}
          artworkFinishes={artworkFinishes}
          pricingPreview={pricingPreview}
          officialPricing={pricedQuoteDryRun}
          logicalList={logicalListReadModel}
          commercialInputs={commercialInputs}
          eurToRonRate={eurToRonRate}
          artworkOnlyBlocked={artworkOnlyBlocked || logoOnlyCandidateNotOfferable}
        />
      </div>

      <div
        className="grid items-start gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(360px,420px)] xl:grid-cols-[minmax(0,1fr)_minmax(390px,460px)]"
        data-testid="intake-v6-review-layout"
      >
        <div className="min-w-0 lg:flex lg:min-h-0 lg:flex-col">
      <IntakeV6ReviewTabNav
        active={reviewTab}
        onChange={setReviewTab}
        templateCode={modularTemplateCode}
        pendingFinisaje={pendingConfirmationCount}
        illuminated={form.illuminated !== false}
      />

      <IntakeV6ReviewOperatorBlockerBanner
        display={operatorBlockerBannerDisplay}
        onJumpToDiagnostic={handleJumpToDiagnostic}
      />

      <div
        className="min-h-0 lg:flex-1 lg:overflow-hidden"
        data-testid="intake-v6-review-tab-panels"
      >
        {reviewTab === "finisaje" ? (
          <div data-testid="intake-v6-review-tab-panel-finisaje">
            {artworkOnlyRequiresDecision &&
            state.analyzerReport &&
            state.layerRoleConfirmation ? (
              <IntakeV6ArtworkOnlyDecisionPanel
                report={state.analyzerReport as SvgAnalysisCoreReport}
                confirmation={state.layerRoleConfirmation}
                variant="review"
              />
            ) : null}
            <IntakeV6ReviewSectionShell
              title="Finisaje pe layer"
              description="Față, cant și artwork — același card compact pe strat."
              testId="intake-v6-review-section-face-letters"
              compact
            >
            {effectiveLetterGroups.length > 0 ? (
            <IntakeV6ReviewLetterGroupsSection
              groups={effectiveLetterGroups}
              onChange={(next) => {
                setLetterGroups(next);
                syncFormFromLayerFinishes(
                  { letterGroups: next, artworkFinishes },
                  { domains: ["face_finish"] },
                );
              }}
              faceFinishOptions={templateContract.faceFinishOptions}
              allowedReturnDepthMm={templateContract.allowedReturnDepthMm}
              backingMode={normalizeIntakeV6BackingMode(form.backing_mode)}
              onBackingChange={(mode) =>
                updateForm(
                  {
                    backing_mode: mode,
                    back_bevel_enabled: mode === "forex_10_with_bevel",
                  },
                  { domains: ["backing"] },
                )
              }
            />
            ) : null}
            {artworkFinishes.length > 0 ? (
              <div ref={artworkSectionRef} data-testid="intake-v6-review-section-artwork">
                <IntakeV6ArtworkFinishSection
                  embedded
                  rows={artworkFinishes}
                  rasterLayerKeys={rasterLayerKeys}
                  showDecisionAlert={showArtworkDecisionAlert}
                  decisionMessages={artworkDecisionMessages}
                  onVerifyArtwork={handleVerifyArtwork}
                  showResidualVectorNotice={allArtworkConfirmed && hasVectorResidualWarning}
                  highlightUnconfirmed={highlightArtworkUnconfirmed}
                  stepOneConfirmedLayerKeys={stepOneConfirmedArtworkLayerKeys}
                  allowedReturnDepthMm={templateContract.allowedReturnDepthMm}
                  backingMode={
                    effectiveLetterGroups.length === 0
                      ? normalizeIntakeV6BackingMode(form.backing_mode)
                      : undefined
                  }
                  onBackingChange={
                    effectiveLetterGroups.length === 0
                      ? (mode) =>
                          updateForm(
                            {
                              backing_mode: mode,
                              back_bevel_enabled: mode === "forex_10_with_bevel",
                            },
                            { domains: ["backing"] },
                          )
                      : undefined
                  }
                  onChange={(next) => {
                    setArtworkFinishes(next);
                    syncFormFromLayerFinishes(
                      { letterGroups: effectiveLetterGroups, artworkFinishes: next },
                      { domains: ["artwork_finish"] },
                    );
                  }}
                />
              </div>
            ) : null}
            {effectiveLetterGroups.length === 0 && artworkFinishes.length === 0 ? (
            <div data-testid="intake-v6-review-backing-finish-integration">
              <IntakeV6ReviewBackingSelect
                embedded
                backingMode={normalizeIntakeV6BackingMode(form.backing_mode)}
                onBackingChange={(mode) =>
                  updateForm(
                    {
                      backing_mode: mode,
                      back_bevel_enabled: mode === "forex_10_with_bevel",
                    },
                    { domains: ["backing"] },
                  )
                }
              />
            </div>
            ) : null}
            <IntakeV6ReturnCantBlockedStateAwarenessPanel model={returnCantReadonlyAwareness} />
            </IntakeV6ReviewSectionShell>
          </div>
        ) : null}

        {reviewTab === "iluminare" ? (
          <div data-testid="intake-v6-review-tab-panel-iluminare" className="space-y-2">
            <IntakeV6ReviewSectionShell
              title="Iluminare"
              description="LED, consum și culoare — emblemă când există artwork."
              testId="intake-v6-review-section-lighting"
              compact
            >
              <IntakeV6ReviewLightingSection
                illuminated={form.illuminated !== false}
                onIlluminatedChange={(value) =>
                  updateForm({ illuminated: value }, { domains: ["lighting"] })
                }
                lightingSystemType={form.lighting_system_type ?? "led_modules"}
                onLightingSystemTypeChange={(value) =>
                  updateForm(
                    {
                      lighting_system_type: value,
                      psu_configuration: [],
                      selected_psu_watts: null,
                    },
                    { domains: ["lighting"] },
                  )
                }
                lightColor={form.light_color ?? "neutral"}
                onLightColorChange={(value) =>
                  updateForm({ light_color: value }, { domains: ["lighting"] })
                }
                ledModulePowerW={ledModulePowerW}
                onLedModulePowerWChange={(value) =>
                  updateForm(
                    { led_module_power_w: value, psu_configuration: [] },
                    { domains: ["lighting"] },
                  )
                }
                ledDisplayPerimeterM={ledDisplayPerimeterM}
                emblemLightingMode={emblemLightingMode}
                onEmblemLightingChange={(mode) =>
                  updateForm({ emblem_lighting_mode: mode }, { domains: ["lighting"] })
                }
                showEmblemLighting={artworkFinishes.length > 0}
                isLedModules={isLedModules}
                ledModuleCount={ledModuleCount}
                emblemOutboxAreaM2={emblemOutboxAreaM2}
                emblemLedModuleCount={emblemLedModuleCount}
                emblemLightingModeNormalized={emblemLightingMode}
                totalLedModuleCount={totalLedModuleCount}
                letterLedStripLengthM={form.letter_led_strip_length_m}
                emblemLedStripLengthM={form.emblem_led_strip_length_m}
                totalLedStripLengthM={form.total_led_strip_length_m}
                ledStripPowerWPerMl={form.led_strip_power_w_per_ml ?? 5}
                returnDepthMm={emblemLightingDepthMm ?? DEFAULT_RETURN_DEPTH_MM}
                estimatedLedWatts={form.estimated_led_watts}
                requiredPsuWatts={form.required_psu_watts}
                psuLabel={psuLabel}
                psuAllocationStatus={form.psu_allocation_status}
                psuReservePercent={Math.round(INTAKE_V6_PSU_RESERVE_RATIO * 100)}
                allowedLightingSystems={templateContract.allowedLightingSystems}
                allowedLightColors={templateContract.allowedLightColors}
                allowedLedModulePowerW={templateContract.allowedLedModulePowerW}
                allowedEmblemLightingModes={templateContract.allowedEmblemLightingModes}
              />
            </IntakeV6ReviewSectionShell>
          </div>
        ) : null}

        {reviewTab === "montaj" ? (
          <div data-testid="intake-v6-review-tab-panel-montaj">
            <IntakeV6ReviewSectionShell
              title="Montaj & template"
              description="Șablon, sistem de prindere și opțiuni legate de producție."
              testId="intake-v6-review-section-montaj"
              compact
            >
            <div className={`${v6.cardCompact} !p-3`}>
            <div className="grid gap-2 sm:grid-cols-2">
              <label className="flex items-center gap-2 rounded border border-[#2A3548] bg-[#0A0F1A] px-2.5 py-1.5 text-[11px] text-slate-100">
                <input
                  type="checkbox"
                  className="h-4 w-4 accent-cyan-400"
                  checked={form.mounting_template_enabled !== false}
                  onChange={(event) =>
                    updateForm(
                      {
                        mounting_template_enabled: event.target.checked,
                        mounting_template_area_m2: event.target.checked
                          ? resolveMountingTemplateAreaM2(
                              form.mounting_template_area_m2,
                              mountingTemplateAreaFallbackM2,
                            )
                          : form.mounting_template_area_m2,
                      },
                      { domains: ["mounting"] },
                    )
                  }
                  data-testid="intake-v6-mounting-template-enabled"
                />
                Șablon montaj
              </label>

              {form.mounting_template_enabled !== false ? (
                <>
                  <label className={REVIEW_FIELD_BLOCK_CLASS}>
                    <span className={REVIEW_FIELD_LABEL_CLASS}>Arie șablon montaj</span>
                    <div className="flex overflow-hidden rounded border border-[#2A3548] bg-[#0A0F1A] focus-within:border-cyan-400/60">
                      <input
                        type="number"
                        min={mountingTemplateAreaFallbackM2 ?? 0}
                        step="0.01"
                        className="min-w-0 flex-1 bg-transparent px-2 py-1.5 text-[11px] outline-none"
                        value={form.mounting_template_area_m2 ?? ""}
                        placeholder={
                          mountingTemplateAreaFallbackM2 != null
                            ? String(mountingTemplateAreaFallbackM2)
                            : ""
                        }
                        onChange={(event) => {
                          const raw = event.target.value;
                          updateForm(
                            {
                              mounting_template_area_m2: resolveMountingTemplateAreaM2(
                                raw ? Number(raw) : undefined,
                                mountingTemplateAreaFallbackM2,
                              ),
                            },
                            { domains: ["mounting"], autosavePolicy: "long" },
                          );
                        }}
                        onBlur={() => {
                          if (selectorPendingSave || commercialInputsPendingSave) {
                            void saveCurrentFinish(true);
                          }
                        }}
                        data-testid="intake-v6-mounting-template-area"
                      />
                      <span className="flex items-center border-l border-[#2A3548] px-2 text-[10px] font-semibold text-slate-400">
                        m²
                      </span>
                    </div>
                  </label>

                  <label className={REVIEW_FIELD_BLOCK_CLASS}>
                    <span className={REVIEW_FIELD_LABEL_CLASS}>Material șablon</span>
                    <select
                      className={REVIEW_SELECT_CLASS}
                      value={form.mounting_template_material_type ?? "forex"}
                      onChange={(event) =>
                        updateForm(
                          {
                            mounting_template_material_type:
                              event.target.value as IntakeV6MountingTemplateMaterial,
                          },
                          { domains: ["mounting"] },
                        )
                      }
                      data-testid="intake-v6-mounting-template-material"
                    >
                      {templateContract.allowedMountingTemplateMaterials.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </label>
                </>
              ) : null}

              <label className={REVIEW_FIELD_BLOCK_CLASS}>
                <span className={REVIEW_FIELD_LABEL_CLASS}>Sistem montaj</span>
                <select
                  className={REVIEW_SELECT_CLASS}
                  value={form.mounting_system ?? "direct_wall"}
                  onChange={(event) =>
                    updateForm(
                      {
                        mounting_system: event.target.value as IntakeV6MountingSystem,
                      },
                      { domains: ["mounting"] },
                    )
                  }
                  data-testid="intake-v6-mounting-system"
                >
                  {templateContract.allowedMountingSystems.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>

              {mountingUsesBars ? (
                <label className={REVIEW_FIELD_BLOCK_CLASS}>
                  <span className={REVIEW_FIELD_LABEL_CLASS}>Profil bare</span>
                  <select
                    className={REVIEW_SELECT_CLASS}
                    value={form.mounting_bar_profile ?? "30x30x1.5"}
                      onChange={(event) =>
                        updateForm(
                          { mounting_bar_profile: event.target.value },
                          { domains: ["mounting"] },
                        )
                      }
                    data-testid="intake-v6-mounting-bar-profile"
                  >
                    {templateContract.allowedMountingBarProfiles.map((profile) => (
                      <option key={profile} value={profile}>
                        {profile}
                      </option>
                    ))}
                  </select>
                </label>
              ) : null}

              {form.illuminated !== false ? (
                <label className={REVIEW_FIELD_BLOCK_CLASS}>
                  <span className={REVIEW_FIELD_LABEL_CLASS}>Sursa LED template</span>
                  <select
                    className={REVIEW_SELECT_CLASS}
                    value={form.selected_psu_watts ?? ""}
                    onChange={(event) => {
                      const raw = event.target.value;
                      if (raw) updateSelectedPsuWatts(Number(raw));
                    }}
                    data-testid="intake-v6-selected-psu-watts"
                  >
                    <option value="">-</option>
                    {templateContract.allowedPsuWatts.map((watts) => (
                      <option key={watts} value={watts}>
                        {watts}W
                      </option>
                    ))}
                  </select>
                </label>
              ) : null}

              {volumAluminumModuleLinks.length > 0 ? (
                <div className="sm:col-span-2 rounded border border-cyan-900/50 bg-cyan-950/20 px-3 py-3">
                  <div className="mb-2 flex items-start justify-between gap-3">
                    <div>
                      <p className="text-[11px] font-semibold text-cyan-300">Modul volum aluminiu</p>
                      <p className="text-[10px] text-slate-400">Legat modular de template-ul mamă.</p>
                    </div>
                    {selectedVolumAluminumModule ? (
                      <div className="flex items-center gap-2 text-[10px]">
                        <Link
                          to={`/product-system?template=${encodeURIComponent(selectedVolumAluminumModule.module_template_code)}`}
                          className="rounded border border-cyan-800/50 px-2 py-1 text-cyan-300 hover:bg-cyan-900/30"
                        >
                          Product System
                        </Link>
                        <Link
                          to={`/inventory/pricing?template=${encodeURIComponent(selectedVolumAluminumModule.module_template_code)}`}
                          className="rounded border border-cyan-800/50 px-2 py-1 text-cyan-300 hover:bg-cyan-900/30"
                        >
                          Pricing
                        </Link>
                      </div>
                    ) : null}
                  </div>
                  <label className={REVIEW_FIELD_BLOCK_CLASS}>
                    <span className={REVIEW_FIELD_LABEL_CLASS}>Template modul</span>
                    <select
                      className={REVIEW_SELECT_CLASS}
                      value={selectedVolumAluminumModuleCode}
                      onChange={(event) =>
                        updateForm(
                          {
                            volum_aluminum_module_template_code: event.target.value || null,
                          },
                          { domains: ["template"] },
                        )
                      }
                      data-testid="intake-v6-volum-aluminum-module-template"
                    >
                      {volumAluminumModuleLinks.map((module) => (
                        <option key={module.module_template_code} value={module.module_template_code}>
                          {module.module_template_label ?? module.module_template_code}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
              ) : null}
            </div>
            </div>
            </IntakeV6ReviewSectionShell>
          </div>
        ) : null}
      </div>

      <IntakeV6ReviewSaveFooter
        saving={saving}
          pendingSave={localReviewEditsPending}
        error={error}
      />
        </div>

        <div
          ref={liveCalcRef}
          className="hidden lg:block lg:sticky lg:top-4 lg:self-start"
          data-testid="intake-v6-live-calculation-sticky-shell"
        >
          <IntakeV6LiveCalculationSummary
            breakdown={breakdown}
            faceBackDraft={faceBackPrepDraft.draft}
            loading={loadingBreakdown || faceBackPrepDraft.loading}
            layout="rightPanel"
            operatorCantPerimeterM={operatorCantPerimeterM}
            pendingSave={localReviewEditsPending}
            letterGroups={effectiveLetterGroups}
            artworkFinishes={artworkFinishes}
            pricingPreview={pricingPreview}
            officialPricing={pricedQuoteDryRun}
            logicalList={logicalListReadModel}
            commercialInputs={commercialInputs}
            eurToRonRate={eurToRonRate}
            artworkOnlyBlocked={artworkOnlyBlocked || logoOnlyCandidateNotOfferable}
          />
          <IntakeV6PricingInputPanel
            preview={pricingPreview}
            breakdown={breakdown}
            officialPricing={pricedQuoteDryRun}
            loading={loadingPricingPreview}
            commercialInputs={commercialInputs}
            onCommercialInputsChange={(next) => {
              const nextCommercialInputs = { ...next, vatPercent: vatPct };
              markLocalFinishChanged(["commercial_preview"], "long");
              setCommercialInputsDirty(true);
              setCommercialInputs(nextCommercialInputs);
              if (commercialSaveTimerRef.current) {
                clearTimeout(commercialSaveTimerRef.current);
              }
              commercialSaveTimerRef.current = setTimeout(() => {
                commercialSaveTimerRef.current = null;
                void saveCurrentFinish(true, nextCommercialInputs);
              }, 700);
            }}
            eurToRonRate={eurToRonRate}
            variant="commercialSliders"
            commercialGuard={logoOnlyCandidateNotOfferable ? LOGO_ONLY_NOT_OFFERABLE_STATUS : null}
          />
        </div>
      </div>

      <IntakeV6TechnicalDetailsAccordion
        title={INTAKE_V6_REVIEW_DIAGNOSTIC_SECTION_TITLE}
        testId="intake-v6-review-technical-details"
        defaultOpen={false}
        open={diagnosticSectionOpen}
        onOpenChange={setDiagnosticSectionOpen}
        itemCount={reviewDiagnosticEntryCount}
        hint="Pentru verificare avansată"
        className="mb-4 mt-2"
      >
      <div
        ref={diagnosticRef}
        id="intake-v6-review-diagnostic-tehnic"
        data-testid="intake-v6-review-diagnostic-tehnic"
      >
      <FormSystemBackboneAwarenessPanel
        backbone={modularFormContractHook.contract?.form_system_backbone ?? null}
        runtimeState={backboneRuntimeState}
      />

      <FormSystemRuntimeCaptureReadModelPanel
        model={runtimeCaptureReadModel}
        loading={loadingRuntimeCaptureReadModel}
        error={runtimeCaptureReadModelError}
      />

      <ProductTruthPromotionPlannerPanel
        model={productTruthPromotionPlanner}
        loading={loadingProductTruthPromotionPlanner}
        error={productTruthPromotionPlannerError}
      />
      </div>
      {binding ? (
        <div className={`${v6.card} mb-0`} data-testid="intake-v6-review-binding">
          <h3 className={`mb-1 ${v6.sectionTitle}`}>ProductSystem</h3>
          <p className="text-[11px] text-slate-400">
            {binding.template_label ?? binding.template_code} · {binding.operation_count} operații
          </p>
          {binding.module_links.length > 0 ? (
            <p className="mt-2 text-[11px] text-cyan-300">
              Module active: {binding.module_links.map((module) => module.module_template_code).join(", ")}
            </p>
          ) : null}
        </div>
      ) : null}

      <IntakeV6OperatorWorkSummaryTechnicalDetails counts={operatorWorkSummary} />

      <IntakeV6AiSemanticAssistPanel
        preview={aiSemanticPreview}
        loading={loadingAiSemanticPreview}
      />

      <IntakeV6ArtworkComplexityCard
        assessments={artworkComplexityReport?.assessments ?? []}
        decisions={artworkComplexityDecisions}
        onDecisionChange={(next) => {
          markLocalFinishChanged(["artwork_finish"]);
          setArtworkComplexityDecisions(next);
          setForm((prev) => ({ ...prev, confirmed: false }));
        }}
      />

      <div className="mb-0">
        {logoOnlyCandidateNotOfferable ? (
          <div
            className={`${v6.card} mb-0 border-amber-500/30 bg-amber-500/10`}
            data-testid="intake-v6-materials-prices-logo-only-guard"
          >
            <h3 className={v6.sectionTitle}>Materiale / preturi guarded</h3>
            <p className="mt-1 text-[11px] leading-relaxed text-amber-100/90">
              Preview intern neofertabil: logo-only candidate nu este quote-ready. Materialele si preturile nu reprezinta oferta finala.
            </p>
          </div>
        ) : (
          <IntakeV6MaterialBreakdownPanel
            breakdown={breakdown}
            loading={loadingBreakdown}
            pendingSave={localReviewEditsPending}
            analysisBundlePending={!analysisReady}
            workspaceId={workspaceId}
            workspaceTitle={state.workspace?.title}
            templateCode={state.workspace?.template_code}
            sheetQuoteOverride={effectiveSheetQuoteOverride}
            onSheetFootprintOverrideSaved={handleSheetFootprintOverrideSaved}
          />
        )}
      </div>

        <IntakeV6GeometryPanel
          geometry={quoteGeometry}
          metrics={geometryMetrics}
          scopeWarnings={[]}
          variant="advanced"
        />

      {!hideGlobalFinish ? (
        <div className={`${v6.card} mb-0`} data-testid="intake-v6-global-finish-fallback">
          <h3 className={`mb-3 ${v6.sectionTitle}`}>Fallback finisaje job-level</h3>
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="block">
              <span className={v6.label}>Față (default)</span>
              <select
                className="w-full rounded border border-[#2A3548] bg-[#0A0F1A] px-3 py-2 text-[12px]"
                value={form.face_finish_type ?? templateContract.defaultFaceFinish}
                onChange={(event) =>
                  updateForm(
                    {
                      face_finish_type: event.target.value,
                      face_vinyl_roll_width_mm: normalizeFaceVinylRollWidthMm(
                        event.target.value,
                        form.face_vinyl_roll_width_mm,
                      ),
                    },
                    { domains: ["face_finish"] },
                  )
                }
                data-testid="intake-v6-face-finish"
              >
                {templateContract.faceFinishOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </label>
            <div className="sm:col-span-2">
              <IntakeV6ReturnCantFields
                idPrefix="v6-global-return"
                returnCant={globalFinishSetupToReturnCant(form)}
                onReturnChange={(cant) =>
                  updateForm(patchGlobalFinishSetupFromReturnCant(cant), {
                    domains: ["face_finish"],
                  })
                }
                testIdPrefix="intake-v6-global-return"
                allowedReturnDepthMm={templateContract.allowedReturnDepthMm}
              />
            </div>
            {faceFinishNeedsRollWidth(form.face_finish_type) ? (
              <label className="block">
                <span className={v6.label}>Lățime rolă (mm)</span>
                <select
                  className="w-full rounded border border-[#2A3548] bg-[#0A0F1A] px-3 py-2 text-[12px]"
                  value={
                    normalizeFaceVinylRollWidthMm(
                      form.face_finish_type,
                      form.face_vinyl_roll_width_mm,
                    ) ?? ""
                  }
                  onChange={(event) => {
                    const raw = event.target.value;
                    updateForm(
                      {
                        face_vinyl_roll_width_mm: raw ? Number(raw) : undefined,
                      },
                      { domains: ["face_finish"] },
                    );
                  }}
                  data-testid="intake-v6-face-roll-width"
                >
                  <option value="">—</option>
                  {templateContract.allowedVinylRollWidths.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}
          </div>
        </div>
      ) : null}

        <IntakeV6FaceBackPrepCostDraftPanel
          workspaceId={workspaceId ?? null}
          analysisReady={analysisReady}
          viewModel={faceBackPrepDraft}
        />

      <div className="mb-0">
        <IntakeV6ProductionTaskDryRunPanel
          workspaceId={workspaceId ?? null}
          workspaceLoaded={Boolean(workspaceId)}
          productionTaskDryRun={productionDryRun}
          loading={loadingProductionDryRun}
          backingMode={normalizeIntakeV6BackingMode(form.backing_mode)}
        />
      </div>

      <div className="mb-0">
        <IntakeV6ProductionHandoffPreviewPanel
          preview={handoffPreview}
          loading={loadingHandoffPreview}
        />
      </div>

      <div className="mb-0">
        <IntakeV6TaskGenerationDryRunPanel
          dryRun={taskGenerationDryRun}
          loading={loadingTaskGenerationDryRun}
        />
      </div>

      <div className="mb-0">
        <IntakeV6OrderBoundTaskReadinessPanel
          readiness={orderBoundReadiness}
          loading={loadingOrderBoundReadiness}
        />
      </div>

      <div className="mb-0">
        <IntakeV6QuoteCommercialSpinePanel
          workspaceId={workspaceId ?? ""}
          quoteId={orderBoundReadiness?.linked_quote?.quote_id ?? null}
          intakeCode={
            orderBoundReadiness?.linked_quote?.exists && workspaceId
              ? `IV6-${workspaceId}`
              : null
          }
          clientAnalysisHash={state.localFileHash ?? persistedSvgFileHash}
          onSpineUpdated={() => {
            if (!workspaceId) return;
            void getIntakeV6OrderBoundTaskReadiness(workspaceId).then(setOrderBoundReadiness);
          }}
        />
      </div>

      <IntakeV6TechnicalDetailsAccordion
        title="Detalii contract template (tehnic)"
        testId="intake-v6-template-form-contract-accordion"
      >
      <div
        className={`${v6.card} mb-0`}
        data-testid="intake-v6-template-form-contract"
        data-template-contract-status={templateFormContract?.alignment_status ?? "unavailable"}
      >
        <h3 className={`mb-3 ${v6.sectionTitle}`}>
          Template form contract
        </h3>
        {templateFormContract ? (
          <div className="space-y-3 text-[11px] text-slate-300">
            <div className="grid gap-2 md:grid-cols-3">
              <div>
                <p className="text-slate-500">Intended authority</p>
                <p>{templateFormContract.intended_form_authority}</p>
              </div>
              <div>
                <p className="text-slate-500">Current runtime authority</p>
                <p>{templateFormContract.current_runtime_authority}</p>
              </div>
              <div>
                <p className="text-slate-500">Alignment</p>
                <p data-testid="intake-v6-template-contract-alignment">
                      {templateFormContract.alignment_status}
                </p>
              </div>
            </div>
            <div className="grid gap-2 md:grid-cols-4">
              <p>
                Dossier fields:{" "}
                <span className="text-slate-100">
                  {templateFormContract.variant_fields.filter((field) => field.owner === "product_system_dossier").length}
                </span>
              </p>
              <p>
                Missing in V4:{" "}
                <span className="text-amber-200">
                    {templateFormContract.variant_fields.filter((field) => field.alignment_status === "missing_in_v4").length}
                </span>
              </p>
              <p>
                Adapter-only:{" "}
                <span className="text-amber-200">
                    {templateFormContract.variant_fields.filter((field) => field.alignment_status === "adapter_only").length}
                </span>
              </p>
              <p>
                Warnings:{" "}
                <span className="text-amber-200">{templateFormContract.warnings.length}</span>
              </p>
            </div>
            <ul className="space-y-1">
              {templateFormContract.variant_fields
                    .filter((field) => field.alignment_status !== "canonical")
                .slice(0, 6)
                .map((field) => (
                  <li key={field.field_key} className="border-t border-[#2A3548] pt-2">
                    <span className="text-slate-100">{field.field_key}</span>{" "}
                            <span className="text-slate-500">({field.alignment_status})</span>
                    {field.v4_field_key ? (
                      <span className="text-slate-500"> via {field.v4_field_key}</span>
                    ) : null}
                  </li>
                ))}
            </ul>
          </div>
        ) : (
          <p className="text-[12px] text-slate-400">Contract formular indisponibil.</p>
        )}
      </div>
      </IntakeV6TechnicalDetailsAccordion>

      <div className={`${v6.card} mb-0`} data-testid="intake-v6-task-preview">
        <h3 className={`mb-3 ${v6.sectionTitle}`}>
          Task preview producție (catalog operații)
        </h3>
        <p
          className="mb-3 rounded border border-[#2A3548] bg-[#0A0F1A]/60 px-3 py-2 text-[11px] text-slate-300"
          data-testid="intake-v6-task-preview-banner"
        >
          {INTAKE_V6_TASK_PREVIEW_BOUNDARY_LINE}
        </p>
        <p className="mb-3 text-[10px] text-slate-500">{INTAKE_V6_PREVIEW_ONLY_BANNER}</p>
        {loadingPreview ? (
          <p className="text-[12px] text-slate-400">Încarc task preview…</p>
        ) : preview ? (
          <ul className="space-y-2">
            {preview.items.filter((item) => item.active).map((item) => (
              <li
                key={item.operation_code}
                className="flex items-center justify-between gap-3 border-b border-[#2A3548] py-2 text-[11px]"
              >
                <span className="min-w-0 text-slate-200">
                  {item.sequence}.{" "}
                  {adaptBackingAbsentOperationLabel(
                    item.label,
                    normalizeIntakeV6BackingMode(form.backing_mode),
                  )}
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-[12px] text-slate-400">Task preview indisponibil.</p>
        )}
      </div>

      {state.workspace?.readiness_status ? (
          <div
            className="mb-0 text-[11px] text-slate-500"
            data-testid="intake-v6-readiness"
            data-readiness-status={state.workspace.readiness_status}
          >
            <p>Readiness: {reviewReadinessDisplay.primary}</p>
            {reviewReadinessDisplay.secondary ? (
              <p className="mt-1 text-amber-200/90" data-testid="intake-v6-readiness-secondary">
                {reviewReadinessDisplay.secondary}
              </p>
            ) : null}
          </div>
      ) : null}
      </IntakeV6TechnicalDetailsAccordion>

        </>
      ) : null}

      {error ? (
        <p className="mt-3 text-[12px] text-red-300" data-testid="intake-v6-review-error">
          {error}
        </p>
      ) : null}
    </section>
  );
}






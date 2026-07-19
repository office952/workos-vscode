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
  countConfiguredArtworkFinishes,
} from "@/lib/intakeV6/intakeV6ProductFinishCompleteness";
import {
  countIncompleteArtworkFinishesForScope,
  countIncompleteLetterGroupsForScope,
} from "@/lib/intakeV6/intakeV6SoldScopeFinishConfirmation";
import {
  filterReviewTabsBySoldScope,
  resolveActiveReviewTabForScope,
  resolveSoldScopeFieldVisibility,
} from "@/lib/intakeV6/intakeV6SoldScopeVisibility";
import { resolveIntakeV6ReviewTabs } from "@/lib/intakeV6/intakeV6ProductPlugin";
import {
  hydrateMountingScopeFromFinishSetup,
  isMountingPreparationActive,
  isSiteInstallationSectionActive,
  MOUNTING_SCOPE_OPTIONS,
  normalizeMountingScope,
  type MountingScopeV1,
} from "@/lib/intakeV6/mountingScope";
import {
  buildMountingSolutionPatch,
  hydrateMountingSolutionFromLegacy,
  isAcpProductComponentActive,
  isMountingSolutionCompositionActive,
  isMountingSolutionSelectorDisabled,
  legacyMountingBarProfile,
  legacyMountingSystemLabel,
  ACM_BOXED_MOUNTING_TEMPLATE_CODE,
  ACM_BOXED_MOUNTING_QUOTE_INPUT_FIELDS,
  METAL_PREMOUNT_TEMPLATE_CODE,
  MOUNTING_SOLUTION_OPTIONS,
  mountingSolutionSelectorValue,
  normalizeAcmMountingConfiguration,
  normalizeMetalMountingConfiguration,
  prepareMountingSolutionForSave,
  readMountingSolution,
  resolveEffectiveMountingSolution,
  type MountingSolutionSelectorValue,
} from "@/lib/intakeV6/mountingSolution";
import {
  emptyMountingFixingSystem,
  readMountingFixingSystem,
  selectVerticalSteelBracket,
  VERTICAL_STEEL_BRACKET,
} from "@/lib/intakeV6/mountingFixingSystem";
import {
  MAT_STRUCT_ALUMINIUM,
  MAT_STRUCT_STEEL,
  TOTAL_FIT_ALLOWANCE_MM,
  proposeInternalFrame,
  type CrossbarOrientation,
  type InternalFrameConfig,
} from "@/lib/intakeV6/acpInternalFrame";
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
import IntakeV6AcpLocalFaceModulesPanel from "../IntakeV6AcpLocalFaceModulesPanel";
import IntakeV6SegmentedBackgroundPanel from "../IntakeV6SegmentedBackgroundPanel";
import IntakeV6SegmentedElectricalPanel from "../IntakeV6SegmentedElectricalPanel";
import IntakeV6MontajClusterShell from "../IntakeV6MontajClusterShell";
import { readSegmentedBackground, statusLabelRo } from "@/lib/intakeV6/segmentedBackground";
import {
  finishOwnershipTechnicalHintRo,
  finishOwnershipTechnicalTitleRo,
  operatorFinishOwnershipDomainLabelRo,
  operatorReadinessLabelRo,
} from "@/lib/intakeV6/intakeV6OperatorVocabulary";
import {
  buildFinalConfirmationBlockers,
  mergeFinalBlockersIntoBannerIssues,
} from "@/lib/intakeV6/intakeV6FinalConfirmationBlockers";
import {
  legacyServiceCornerDemotedNoteRo,
  legacyServiceCornerSupersededNoteRo,
  resolveServiceCornerUiMode,
  shouldShowLegacyServiceCornerInput,
} from "@/lib/intakeV6/montajServiceCornerPrecedence";
import { isProductCompositionConfirmed } from "@/lib/intakeV6/intakeV6Readiness";
import {
  artworkComplexityDecisionsFromPayload,
  artworkComplexityFromReport,
  mergeArtworkComplexityDecisions,
  type IntakeV6ArtworkComplexityDecision,
} from "@/lib/intakeV6/intakeV6ArtworkComplexityDisplay";
import IntakeV6AiSemanticAssistPanel from "../IntakeV6AiSemanticAssistPanel";
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
import { isVolumAluminumModuleApplicable } from "@/lib/intakeV6/intakeV6VolumAluminumModule";
import { buildReturnCantCanonicalRuntimeFromPayload } from "@/lib/intakeV6/productTruth/returnCantCanonicalRuntimeFromProductTruth";
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
import IntakeV6OfferScopeReviewSummary from "../IntakeV6OfferScopeReviewSummary";
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
import {
  buildOperatorBlockerBannerDisplay,
  collectMissingPriceLineKeysFromBreakdown,
} from "@/lib/intakeV6/intakeV6OperatorBlockerBannerDisplay";
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
import { resolveLettersCanonicalFieldLabels } from "@/lib/intakeV6/lettersCanonicalFormContract";
import {
  contractCompositionProvenance,
  resolveReviewTabsFromModularContract,
} from "@/lib/intakeV6/resolveReviewTabsFromModularContract";
import { isContractRendererEnabled } from "@/lib/intakeV6/contractRenderer/isContractRendererEnabled";
import {
  finishSetupKeyFromPath,
  setByWorkspacePath,
} from "@/lib/intakeV6/contractRenderer/workspacePathAccess";
import IntakeContractSectionRenderer from "../contractRenderer/IntakeContractSectionRenderer";
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
    mounting_solution: finish.mounting_solution ?? null,
    mounting_scope: normalizeMountingScope(finish.mounting_scope, finish as Record<string, unknown>),
    site_installation_included:
      finish.site_installation_included === true
        ? true
        : finish.site_installation_included === false
          ? false
          : null,
    mains_cable_length_m: finish.mains_cable_length_m ?? null,
    power_supply_service_corner: finish.power_supply_service_corner ?? null,
    service_screw_finish: finish.service_screw_finish ?? null,
    emblem_lighting_mode: normalizeEmblemLightingMode(finish.emblem_lighting_mode),
    letter_led_module_count: finish.letter_led_module_count ?? null,
    emblem_led_module_count: finish.emblem_led_module_count ?? null,
    total_led_module_count: finish.total_led_module_count ?? null,
    confirmed: finish.confirmed === true,
    segmented_background: finish.segmented_background ?? null,
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
      mounting_scope: "preparation_only",
      site_installation_included: null,
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
    mounting_solution: resolveEffectiveMountingSolution(setup),
    ...hydrateMountingScopeFromFinishSetup(setup),
    mains_cable_length_m:
      typeof setup.mains_cable_length_m === "number" ? setup.mains_cable_length_m : null,
    power_supply_service_corner: normalizePowerSupplyServiceCorner(
      setup.power_supply_service_corner,
    ),
    service_screw_finish: normalizeServiceScrewFinish(setup.service_screw_finish),
    emblem_lighting_mode: normalizeEmblemLightingMode(setup.emblem_lighting_mode),
    letter_led_module_count:
      typeof setup.letter_led_module_count === "number" ? setup.letter_led_module_count : undefined,
    emblem_led_module_count:
      typeof setup.emblem_led_module_count === "number" ? setup.emblem_led_module_count : undefined,
    total_led_module_count:
      typeof setup.total_led_module_count === "number" ? setup.total_led_module_count : undefined,
    confirmed: setup.confirmed === true,
    // Segmented ACM/ACP proposal/confirm lives on finish_setup — must hydrate into Review form.
    segmented_background:
      setup.segmented_background != null &&
      typeof setup.segmented_background === "object" &&
      !Array.isArray(setup.segmented_background)
        ? (setup.segmented_background as Record<string, unknown>)
        : null,
    svg_component_bindings: Array.isArray(setup.svg_component_bindings)
      ? (setup.svg_component_bindings as IntakeV6FinishSetup["svg_component_bindings"])
      : undefined,
    svg_support_selection:
      setup.svg_support_selection != null &&
      typeof setup.svg_support_selection === "object" &&
      !Array.isArray(setup.svg_support_selection)
        ? (setup.svg_support_selection as Record<string, unknown>)
        : null,
  };
}

const MAINS_CABLE_LENGTH_OPTIONS_M = [
  2.5, 5, 7.5, 10, 12.5, 15, 17.5, 20, 22.5, 25,
] as const;

const POWER_SUPPLY_SERVICE_CORNERS = [
  "TOP_LEFT",
  "TOP_RIGHT",
  "BOTTOM_LEFT",
  "BOTTOM_RIGHT",
  "MANUAL_CONFIRMED",
] as const;

type PowerSupplyServiceCorner = (typeof POWER_SUPPLY_SERVICE_CORNERS)[number];
type ServiceScrewFinish = "NATURAL" | "PAINTED_TO_MATCH_CANT";

function normalizePowerSupplyServiceCorner(value: unknown): PowerSupplyServiceCorner | null {
  return typeof value === "string" &&
    (POWER_SUPPLY_SERVICE_CORNERS as readonly string[]).includes(value)
    ? (value as PowerSupplyServiceCorner)
    : null;
}

function normalizeServiceScrewFinish(value: unknown): ServiceScrewFinish | null {
  if (value === "NATURAL" || value === "PAINTED_TO_MATCH_CANT") return value;
  return null;
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
  const soldScopeVisibility = useMemo(() => resolveSoldScopeFieldVisibility(payload), [payload]);
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

  const finishDepthMm =
    finishFromPayload(payload).return_depth_mm ?? DEFAULT_RETURN_DEPTH_MM;
  const expectedLetterGroups = useMemo(
    () =>
      mergeLetterGroupFinishes(
        deriveLetterGroupsFromAnalyzer(
          state.analyzerReport as SvgAnalysisCoreReport | null,
          state.layerRoleConfirmation,
          finishDepthMm,
        ),
        letterGroupFinishesFromPayload(payload),
      ),
    [payload, state.analyzerReport, state.layerRoleConfirmation, finishDepthMm],
  );
  const expectedArtworkFinishes = useMemo(
    () =>
      mergeArtworkFinishes(
        deriveArtworkFinishesFromAnalyzer(
          state.analyzerReport as SvgAnalysisCoreReport | null,
          state.layerRoleConfirmation,
          finishDepthMm,
        ),
        artworkFinishesFromPayload(payload),
      ),
    [payload, state.analyzerReport, state.layerRoleConfirmation, finishDepthMm],
  );
  const expectedHydratedForm = useMemo(
    () =>
      syncLighting(
        applyMountingTemplateMinimumArea(finishFromPayload(payload), mountingTemplateAreaFallbackM2),
      ),
    // syncLighting closes over letterPerimeterM / emblemOutboxAreaM2 / quoteGeometry
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [payload, mountingTemplateAreaFallbackM2, letterPerimeterM, emblemOutboxAreaM2, quoteGeometry],
  );

  const [form, setForm] = useState<IntakeV6FinishSetup>(() =>
    syncLighting(applyMountingTemplateMinimumArea(finishFromPayload(payload), mountingTemplateAreaFallbackM2)),
  );
  const [letterGroups, setLetterGroups] = useState<IntakeV6LetterGroupFinish[]>(() => expectedLetterGroups);
  const [artworkFinishes, setArtworkFinishes] = useState<IntakeV6ArtworkFinish[]>(() => expectedArtworkFinishes);
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
  const lettersCanonicalFieldLabels = useMemo(
    () =>
      resolveLettersCanonicalFieldLabels(
        modularTemplateCode,
        modularFormContractHook.contract,
      ),
    [modularTemplateCode, modularFormContractHook.contract],
  );
  const contractRendererEnabled = isContractRendererEnabled(modularTemplateCode);
  const modularFormContract = modularFormContractHook.contract;
  const contractComposedReviewTabs = useMemo(
    () => resolveReviewTabsFromModularContract(modularFormContract),
    [modularFormContract],
  );
  const scopedReviewTabs = useMemo(() => {
    const base =
      contractComposedReviewTabs ?? resolveIntakeV6ReviewTabs(modularTemplateCode);
    return filterReviewTabsBySoldScope(base, soldScopeVisibility) ?? base;
  }, [contractComposedReviewTabs, modularTemplateCode, soldScopeVisibility]);
  const compositionProvenance = useMemo(
    () => contractCompositionProvenance(modularFormContract),
    [modularFormContract],
  );
  const contractValueRoot = useMemo(
    () => ({ finish_setup: form as unknown as Record<string, unknown> }),
    [form],
  );
  const handleContractFieldChange = useCallback(
    (workspacePath: string, value: unknown) => {
      const allowlist = modularFormContract?.writable_workspace_paths ?? [];
      const written = setByWorkspacePath(contractValueRoot, workspacePath, value, allowlist);
      if (!written.ok) {
        return;
      }
      const finishKey = finishSetupKeyFromPath(workspacePath);
      if (!finishKey) {
        return;
      }
      const nextFinish = (written.next.finish_setup ?? {}) as Record<string, unknown>;
      const domain =
        finishKey.startsWith("mounting_")
          ? (["mounting"] as IntakeV6ReviewDirtyDomain[])
          : finishKey.startsWith("lighting_") || finishKey.includes("psu")
            ? (["lighting"] as IntakeV6ReviewDirtyDomain[])
            : (["face_finish"] as IntakeV6ReviewDirtyDomain[]);
      updateForm(
        { [finishKey]: nextFinish[finishKey] } as Partial<IntakeV6FinishSetup>,
        { domains: domain },
      );
    },
    [contractValueRoot, modularFormContract?.writable_workspace_paths, updateForm],
  );
  const renderSectionByKey = useCallback(
    (sectionKey: string) => {
      if (!contractRendererEnabled || !modularFormContract) return null;
      const section = (modularFormContract.render_sections ?? []).find(
        (item) => item.section_key === sectionKey,
      );
      if (!section) return null;
      return (
        <IntakeContractSectionRenderer
          key={section.section_key}
          section={section}
          contract={modularFormContract}
          valueRoot={contractValueRoot}
          onFieldChange={handleContractFieldChange}
        />
      );
    },
    [
      contractRendererEnabled,
      modularFormContract,
      contractValueRoot,
      handleContractFieldChange,
    ],
  );
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
  useEffect(() => {
    const next = resolveActiveReviewTabForScope(reviewTab, scopedReviewTabs);
    if (next !== reviewTab) {
      setReviewTab(next);
    }
  }, [reviewTab, scopedReviewTabs]);
  const [diagnosticSectionOpen, setDiagnosticSectionOpen] = useState(false);
  const localRevisionRef = useRef(0);
  const autosaveRequestRef = useRef(0);
  const commercialInputsSyncKeyRef = useRef<string | null>(null);

  const selectorPendingSave = useMemo(
    () =>
      isIntakeV6SelectorStatePendingSave(form, payload, letterGroups, artworkFinishes, {
        expectedForm: expectedHydratedForm,
        expectedLetterGroups,
        expectedArtworkFinishes,
      }),
    [form, payload, letterGroups, artworkFinishes, expectedHydratedForm, expectedLetterGroups, expectedArtworkFinishes],
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

  const segmentedTruthKey = useMemo(() => {
    const seg = readSegmentedBackground(form as unknown as Record<string, unknown>);
    if (!seg) return "";
    return `${seg.status}|${seg.assembly_id || ""}|${Boolean(seg.operator_confirmed)}|${(seg.panels || []).length}`;
  }, [form]);

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
  }, [workspaceId, analysisReady, templateCode, segmentedTruthKey]);

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
    formSource: IntakeV6FinishSetup = form,
  ): IntakeV6FinishSetup {
    return syncLighting(
      syncIntakeV6FinishPayloadFromLayerFinishes(
        {
          ...formSource,
          face_vinyl_roll_width_mm: normalizeFaceVinylRollWidthMm(
            formSource.face_finish_type,
            formSource.face_vinyl_roll_width_mm,
          ),
          mounting_template_area_m2:
            formSource.mounting_template_enabled !== false
              ? resolveMountingTemplateAreaM2(
                  formSource.mounting_template_area_m2,
                  mountingTemplateAreaFallbackM2,
                )
              : formSource.mounting_template_area_m2,
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

  async function persistFinishSetupState(
    finishState: IntakeV6FinishSetup,
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
      const preparedState = prepareMountingSolutionForSave(
        finishState as unknown as Record<string, unknown>,
      ) as IntakeV6FinishSetup;
      const body = buildCurrentFinishBody(confirmed, commercialInputsOverride, preparedState);
      const pendingDomains = new Set(pendingDirtyDomainsRef.current);
      const workspace = await saveFinishSetup(body);
      if (
        workspace &&
        requestId === autosaveRequestRef.current &&
        revisionAtStart === localRevisionRef.current
      ) {
        const nextFinish = finishFromPayload(workspace.payload as Record<string, unknown>);
        const nextPayload = workspace.payload as Record<string, unknown>;
        const nextDepth = nextFinish.return_depth_mm ?? DEFAULT_RETURN_DEPTH_MM;
        const syncedNextForm = syncLighting(
          applyMountingTemplateMinimumArea(nextFinish, mountingTemplateAreaFallbackM2),
        );
        const nextLetterGroups = mergeLetterGroupFinishes(
          deriveLetterGroupsFromAnalyzer(
            state.analyzerReport as SvgAnalysisCoreReport | null,
            state.layerRoleConfirmation,
            nextDepth,
          ),
          letterGroupFinishesFromPayload(nextPayload),
        );
        const nextArtworkFinishes = mergeArtworkFinishes(
          deriveArtworkFinishesFromAnalyzer(
            state.analyzerReport as SvgAnalysisCoreReport | null,
            state.layerRoleConfirmation,
            nextDepth,
          ),
          artworkFinishesFromPayload(nextPayload),
        );
        const nextCommercialInputs = resolveIntakeV6OfferCommercialDefaults(
          pricingPreview,
          nextFinish.commercial_inputs,
        );
        const nextSettingsVatCommercialInputs = { ...nextCommercialInputs, vatPercent: vatPct };
        // Always mirror server finish state after a successful persist. Pending-save uses a
        // fuller compare than buildFinishSetupSyncSignature; skipping setForm here leaves
        // "Sincronizare automata in asteptare" stuck across remount/HMR.
        setForm(syncedNextForm);
        setLetterGroups(nextLetterGroups);
        setArtworkFinishes(nextArtworkFinishes);
        setCommercialInputsDirty(false);
        setCommercialInputs(nextSettingsVatCommercialInputs);
        pendingDirtyDomainsRef.current.clear();
        pendingAutosavePolicyRef.current = "short";
        bumpPreviewRefresh(
          pendingDomains.size > 0
            ? pendingDomains
            : ["lighting", "face_finish", "artwork_finish", "backing", "mounting", "template", "commercial_preview"],
        );
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
    await persistFinishSetupState(form, confirmed, commercialInputsOverride);
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
  const mountingUsesBars = isMountingSolutionCompositionActive(form as Record<string, unknown>);
  const selectedMountingSolutionValue = mountingSolutionSelectorValue(form as Record<string, unknown>);
  const selectedMountingSolution = resolveEffectiveMountingSolution(form as Record<string, unknown>);
  const metalMountingConfiguration = normalizeMetalMountingConfiguration(
    selectedMountingSolution?.template_code === METAL_PREMOUNT_TEMPLATE_CODE
      ? selectedMountingSolution.configuration
      : undefined,
  );
  const acmMountingConfiguration = normalizeAcmMountingConfiguration(
    selectedMountingSolution?.template_code === ACM_BOXED_MOUNTING_TEMPLATE_CODE
      ? selectedMountingSolution.configuration
      : undefined,
  );
  const legacyMountingSystemDisplay = legacyMountingSystemLabel(form as Record<string, unknown>);
  const legacyMountingProfileDisplay = legacyMountingBarProfile(form as Record<string, unknown>);
  const mountingScope = normalizeMountingScope(form.mounting_scope, form as Record<string, unknown>);
  const mountingPrepActive = isMountingPreparationActive(mountingScope);
  const acpProductActive = isAcpProductComponentActive(form as Record<string, unknown>);
  const mountingFixingSystem = readMountingFixingSystem(form as Record<string, unknown>);
  const mountingSolutionSelectorLocked = isMountingSolutionSelectorDisabled(
    mountingScope,
    selectedMountingSolutionValue,
  );
  const volumModuleApplicable = isVolumAluminumModuleApplicable(
    modularTemplateCode,
    form as unknown as Record<string, unknown>,
  );
  const siteInstallationSectionActive = isSiteInstallationSectionActive(mountingScope);

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
      canonicalRuntime: buildReturnCantCanonicalRuntimeFromPayload(payload),
    });
  }, [analysisReady, artworkFinishes, effectiveLetterGroups, form, payload, quoteGeometry, state.layerRoleConfirmation, state.workspace?.workspace_code, svgSourcePayload, workspaceId]);
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
    const allArtworkProductConfigured =
      artworkFinishes.length === 0 ||
      countIncompleteArtworkFinishesForScope(artworkFinishes, soldScopeVisibility) === 0;
    return buildReviewHandoffSurfacing({
      handoff: quoteHandoffPreview,
      handoffOptions: {
        loading: loadingQuoteHandoffPreview && quoteHandoffPreview == null,
      },
      containsMissingPrices: breakdown?.totals.contains_missing_prices === true,
      allArtworkProductConfigured,
      currentStep: "review",
    });
  }, [
    artworkFinishes,
    soldScopeVisibility,
    quoteHandoffPreview,
    loadingQuoteHandoffPreview,
    breakdown?.totals.contains_missing_prices,
  ]);
  const missingPriceLineKeys = useMemo(
    () => collectMissingPriceLineKeysFromBreakdown(breakdown),
    [breakdown],
  );
  const finalConfirmationExtraIssues = useMemo(
    () =>
      mergeFinalBlockersIntoBannerIssues(
        buildFinalConfirmationBlockers({
          payload: state.workspace?.payload as Record<string, unknown> | undefined,
          finish: form as unknown as Record<string, unknown>,
        }),
      ),
    [state.workspace?.payload, form],
  );
  const operatorBlockerBannerDisplay = useMemo(
    () =>
      buildOperatorBlockerBannerDisplay({
        surfacing: reviewHandoffSurfacing,
        handoffLoading: loadingQuoteHandoffPreview && quoteHandoffPreview == null,
        runtimeModel: runtimeCaptureReadModel,
        runtimeLoading: loadingRuntimeCaptureReadModel,
        plannerModel: productTruthPromotionPlanner,
        plannerLoading: loadingProductTruthPromotionPlanner,
        missingPriceFlagWithoutRows:
          breakdown?.totals.contains_missing_prices === true && missingPriceLineKeys.length === 0,
        missingPriceLineKeys,
        extraIssues: finalConfirmationExtraIssues,
      }),
    [
      reviewHandoffSurfacing,
      loadingQuoteHandoffPreview,
      quoteHandoffPreview,
      runtimeCaptureReadModel,
      loadingRuntimeCaptureReadModel,
      productTruthPromotionPlanner,
      loadingProductTruthPromotionPlanner,
      breakdown?.totals.contains_missing_prices,
      missingPriceLineKeys,
      finalConfirmationExtraIssues,
    ],
  );
  const handleOperatorBlockerFocus = useCallback(
    (targetId: string) => {
      if (targetId.startsWith("tab:")) {
        const tab = targetId.slice(4) as IntakeV6ReviewTabId;
        if (tab === "finisaje" || tab === "iluminare" || tab === "montaj") {
          setReviewTab(tab);
        }
        return;
      }
      if (
        targetId.includes("segmented") ||
        targetId.includes("mounting") ||
        targetId.includes("fundal") ||
        targetId.includes("elec")
      ) {
        setReviewTab("montaj");
      } else if (targetId.includes("artwork") || targetId.includes("letter")) {
        setReviewTab("finisaje");
      } else if (targetId.includes("lighting") || targetId.includes("psu") || targetId.includes("electrical-subsection")) {
        setReviewTab("iluminare");
      }
      window.setTimeout(() => {
        const node =
          document.querySelector(`[data-testid="${targetId}"]`) ||
          document.getElementById(targetId);
        if (node instanceof HTMLElement) {
          node.scrollIntoView({ behavior: "smooth", block: "center" });
          node.focus?.({ preventScroll: true });
        }
      }, 80);
    },
    [setReviewTab],
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
    return (
      countIncompleteLetterGroupsForScope(effectiveLetterGroups, soldScopeVisibility) +
      countIncompleteArtworkFinishesForScope(artworkFinishes, soldScopeVisibility)
    );
  }, [effectiveLetterGroups, artworkFinishes, soldScopeVisibility]);

  const layerRoleStats = useMemo(() => {
    const layers = state.layerRoleConfirmation?.layers ?? [];
    const total = layers.length;
    const confirmed = layers.filter((layer) => layer.confirmationState === "confirmed").length;
    return { total, confirmed };
  }, [state.layerRoleConfirmation]);

  const artworkConfirmStats = useMemo(() => {
    const total = artworkFinishes.length;
    const configured = countConfiguredArtworkFinishes(artworkFinishes);
    return { total, configured };
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
      artworkConfigured: artworkConfirmStats.configured,
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
      <div className="mb-3">
        <IntakeV6OfferScopeReviewSummary payload={payload} />
      </div>
      <IntakeV6ReviewOperatorBlockerBanner
        display={operatorBlockerBannerDisplay}
        nextStepGuidance={
          isProductCompositionConfirmed(
            state.workspace?.payload as Record<string, unknown> | undefined,
          )
            ? reviewHandoffSurfacing.nextStepGuidance
            : "Poți naviga liber între taburi. Confirmarea finală rămâne blocată până rezolvi elementele din sumarul de mai sus."
        }
        onJumpToDiagnostic={handleJumpToDiagnostic}
        onFocusTarget={handleOperatorBlockerFocus}
      />
      <IntakeV6ReviewTabNav
        active={reviewTab}
        onChange={setReviewTab}
        templateCode={modularTemplateCode}
        tabs={scopedReviewTabs}
        compositionAuthority={compositionProvenance.compositionAuthority}
        pendingFinisaje={pendingConfirmationCount}
        illuminated={form.illuminated !== false}
      />
      <div
        className="sr-only"
        data-testid="intake-v6-full-product-composition"
        data-composition-authority={
          compositionProvenance.compositionAuthority ? "true" : "false"
        }
        data-subset-activation={
          compositionProvenance.subsetActivationEnabled ? "true" : "false"
        }
        data-section-keys={compositionProvenance.sectionKeys.join(",")}
      >
        Full-product composition from modular form contract
      </div>

      <div
        className="min-h-0 lg:flex-1"
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
            {effectiveLetterGroups.length === 0 ? renderSectionByKey("finisaje_fields") : null}
            <IntakeV6ReviewSectionShell
              title="Finisaje pe layer"
              description="Față, cant și Vector Logo — același card compact pe strat."
              testId="intake-v6-review-section-face-letters"
              compact
            >
            {effectiveLetterGroups.length > 0 ? (
            <IntakeV6ReviewLetterGroupsSection
              groups={effectiveLetterGroups}
              soldScopeVisibility={soldScopeVisibility}
              analyzerReport={state.analyzerReport as SvgAnalysisCoreReport | null}
              onChange={(next) => {
                setLetterGroups(next);
                syncFormFromLayerFinishes(
                  { letterGroups: next, artworkFinishes },
                  { domains: ["face_finish", "backing"] },
                );
              }}
              faceFinishOptions={templateContract.faceFinishOptions}
              allowedReturnDepthMm={templateContract.allowedReturnDepthMm}
              globalBackingFallback={normalizeIntakeV6BackingMode(form.backing_mode)}
              fieldLabels={lettersCanonicalFieldLabels}
            />
            ) : null}
            {artworkFinishes.length > 0 ? (
              <div ref={artworkSectionRef} data-testid="intake-v6-review-section-artwork">
                <IntakeV6ArtworkFinishSection
                  embedded
                  rows={artworkFinishes}
                  soldScopeVisibility={soldScopeVisibility}
                  rasterLayerKeys={rasterLayerKeys}
                  showDecisionAlert={showArtworkDecisionAlert}
                  decisionMessages={artworkDecisionMessages}
                  onVerifyArtwork={handleVerifyArtwork}
                  showResidualVectorNotice={allArtworkConfirmed && hasVectorResidualWarning}
                  highlightUnconfirmed={highlightArtworkUnconfirmed}
                  stepOneConfirmedLayerKeys={stepOneConfirmedArtworkLayerKeys}
                  allowedReturnDepthMm={templateContract.allowedReturnDepthMm}
                  globalBackingFallback={normalizeIntakeV6BackingMode(form.backing_mode)}
                  onChange={(next) => {
                    setArtworkFinishes(next);
                    syncFormFromLayerFinishes(
                      { letterGroups: effectiveLetterGroups, artworkFinishes: next },
                      { domains: ["artwork_finish", "backing"] },
                    );
                  }}
                />
              </div>
            ) : null}
            </IntakeV6ReviewSectionShell>
            <IntakeV6TechnicalDetailsAccordion
              title={finishOwnershipTechnicalTitleRo()}
              hint={finishOwnershipTechnicalHintRo()}
              defaultOpen={false}
              testId="intake-v6-finish-ownership-note"
              className="mt-2 mb-1"
            >
              <p className="text-[11px] text-slate-300">
                Fața folosește {operatorFinishOwnershipDomainLabelRo("SURFACE_FINISH")} (vinyl / print / vopsire).
                Cantul Oracal/RAL ține de {operatorFinishOwnershipDomainLabelRo("RETURN-CANT")}.
                Valorile concrete rămân în {operatorFinishOwnershipDomainLabelRo("WORKSPACE")}.
                Șablonul de montaj nu este finisaj de suprafață; chip-ul de scope pentru finisaj este amânat.
              </p>
              <p className="mt-2 text-[10px] text-slate-500" data-testid="intake-v6-finish-ownership-technical-tokens">
                Tokenuri interne (diagnostic):{" "}
                <span className="font-mono text-slate-400">SURFACE_FINISH</span>
                {" · "}
                <span className="font-mono text-slate-400">RETURN-CANT</span>
                {" · "}
                <span className="font-mono text-slate-400">WORKSPACE</span>
                {" · "}
                <span className="font-mono text-slate-400">FINISH</span>
              </p>
            </IntakeV6TechnicalDetailsAccordion>
          </div>
        ) : null}

        {reviewTab === "iluminare" ? (
          <div data-testid="intake-v6-review-tab-panel-iluminare" className="space-y-2">
            {renderSectionByKey("iluminare")}
            <IntakeV6ReviewSectionShell
              title="Iluminare și surse"
              description="LED și surse pentru litere — separat de alimentarea 220V a carcasei."
              testId="intake-v6-review-section-lighting"
              compact
            >
              <IntakeV6ReviewLightingSection
                illuminated={form.illuminated !== false}
                onIlluminatedChange={(value) => {
                  if (!soldScopeVisibility.lighting) return;
                  updateForm({ illuminated: value }, { domains: ["lighting"] });
                }}
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
                showLightingFields={soldScopeVisibility.lighting}
                showElectricalFields={soldScopeVisibility.electrical}
                selectedPsuWatts={form.selected_psu_watts}
                onSelectedPsuChange={updateSelectedPsuWatts}
                allowedPsuWatts={templateContract.allowedPsuWatts}
                lightingSystemLabel={lettersCanonicalFieldLabels?.lighting_system_type}
                hideContractManagedFields={contractRendererEnabled}
              />
            </IntakeV6ReviewSectionShell>
          </div>
        ) : null}

        {reviewTab === "montaj" ? (
          <div data-testid="intake-v6-review-tab-panel-montaj" className="space-y-3">
            <div
              className="rounded-md border border-[#2A3548] bg-[#0A0F1A]/55 px-3 py-2"
              data-testid="intake-v6-montaj-readiness-summary"
            >
              <p className="text-[12px] font-semibold text-slate-100">Montaj — ordine de lucru</p>
              <p className="mt-0.5 text-[11px] text-slate-400">
                1) Fundal și carcasă · 2) Montaj comercial (dacă e în ofertă) · 3) Detalii avansate
              </p>
            </div>
            {renderSectionByKey("montaj_template")}
            <IntakeV6ReviewSectionShell
              title="Montaj"
              description="Fundal/carcasă, alimentare panouri, apoi opțiuni comerciale de montaj."
              testId="intake-v6-review-section-montaj"
              compact
            >
            <div className={`${v6.cardCompact} !p-3 space-y-3`}>
              <IntakeV6TechnicalDetailsAccordion
                title="Montaj comercial"
                hint={
                  mountingPrepActive
                    ? "Scope, șablon și montaj la locație"
                    : "Inactiv pentru scope-ul curent — expandă doar dacă ai nevoie"
                }
                defaultOpen={mountingPrepActive}
                testId="intake-v6-montaj-commercial-cluster"
              >
              <label className={`${REVIEW_FIELD_BLOCK_CLASS} sm:col-span-2`}>
                <span className={REVIEW_FIELD_LABEL_CLASS}>Scope comercial montaj</span>
                <select
                  className={REVIEW_SELECT_CLASS}
                  value={mountingScope}
                  onChange={(event) => {
                    const nextScope = event.target.value as MountingScopeV1;
                    setForm((prev) => {
                      const next = syncLighting({
                        ...prev,
                        mounting_scope: nextScope,
                        site_installation_included:
                          nextScope === "preparation_and_site_installation"
                            ? prev.site_installation_included ?? true
                            : prev.site_installation_included,
                        confirmed: false,
                      });
                      pendingDirtyDomainsRef.current.add("mounting");
                      void persistFinishSetupState(next, true);
                      return next;
                    });
                  }}
                  data-testid="intake-v6-mounting-scope"
                >
                  {MOUNTING_SCOPE_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>

              <div
                className={`mt-3 rounded border border-[#2A3548] bg-[#0A0F1A]/60 p-3 ${
                  mountingPrepActive || acpProductActive ? "" : "opacity-60"
                }`}
                data-testid="intake-v6-mounting-prep-section"
              >
                <p className="mb-2 text-[11px] font-semibold text-slate-200">Pregătire și montaj</p>
                {!mountingPrepActive ? (
                  <p className="mb-2 text-[10px] text-slate-400" data-testid="intake-v6-mounting-prep-readonly-note">
                    Serviciile comerciale de pregătire/montaj sunt inactive — configurarea panoului ACP
                    rămâne disponibilă separat.
                  </p>
                ) : null}
            <div className="grid gap-2 sm:grid-cols-2">
              {!contractRendererEnabled ? (
              <label className="flex items-center gap-2 rounded border border-[#2A3548] bg-[#0A0F1A] px-2.5 py-1.5 text-[11px] text-slate-100">
                <input
                  type="checkbox"
                  className="h-4 w-4 accent-cyan-400"
                  checked={form.mounting_template_enabled !== false}
                  disabled={!mountingPrepActive}
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
              ) : null}

              {form.mounting_template_enabled !== false ? (
                <>
                  {!contractRendererEnabled ? (
                  <label className={REVIEW_FIELD_BLOCK_CLASS}>
                    <span className={REVIEW_FIELD_LABEL_CLASS}>Arie șablon montaj</span>
                    <div className="flex overflow-hidden rounded border border-[#2A3548] bg-[#0A0F1A] focus-within:border-cyan-400/60">
                      <input
                        type="number"
                        min={mountingTemplateAreaFallbackM2 ?? 0}
                        step="0.01"
                        className="min-w-0 flex-1 bg-transparent px-2 py-1.5 text-[11px] outline-none disabled:cursor-not-allowed disabled:opacity-60"
                        value={form.mounting_template_area_m2 ?? ""}
                        disabled={!mountingPrepActive}
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
                  ) : null}

                  <label className={REVIEW_FIELD_BLOCK_CLASS}>
                    <span className={REVIEW_FIELD_LABEL_CLASS}>Material șablon</span>
                    <select
                      className={REVIEW_SELECT_CLASS}
                      value={form.mounting_template_material_type ?? "forex"}
                      disabled={!mountingPrepActive}
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
                </div>
              </div>

              {(selectedMountingSolutionValue === METAL_PREMOUNT_TEMPLATE_CODE ||
                selectedMountingSolutionValue === ACM_BOXED_MOUNTING_TEMPLATE_CODE) &&
              mountingPrepActive ? (
                <div
                  className="mt-3 grid gap-2 sm:grid-cols-2"
                  data-testid="intake-v6-process-electrical-fields"
                >
                  <label className={REVIEW_FIELD_BLOCK_CLASS}>
                    <span className={REVIEW_FIELD_LABEL_CLASS}>
                      Lungime cablu alimentare (m)
                    </span>
                    <select
                      className={REVIEW_SELECT_CLASS}
                      value={
                        form.mains_cable_length_m != null &&
                        (MAINS_CABLE_LENGTH_OPTIONS_M as readonly number[]).includes(
                          form.mains_cable_length_m,
                        )
                          ? String(form.mains_cable_length_m)
                          : ""
                      }
                      onChange={(event) => {
                        const raw = event.target.value;
                        updateForm(
                          {
                            mains_cable_length_m: raw === "" ? null : Number(raw),
                          },
                          { domains: ["mounting"] },
                        );
                      }}
                      data-testid="intake-v6-mains-cable-length-m"
                    >
                      <option value="">— selectează —</option>
                      {MAINS_CABLE_LENGTH_OPTIONS_M.map((length) => (
                        <option key={length} value={length}>
                          {length} m
                        </option>
                      ))}
                    </select>
                    <p className="mt-1 text-[10px] text-slate-500">
                      Pas 2.5 m · 2.5–25 · cablare pregătită (serviciu comercial)
                    </p>
                  </label>
                  {selectedMountingSolutionValue !== ACM_BOXED_MOUNTING_TEMPLATE_CODE ? (
                    <p
                      className="text-[10px] text-slate-500 self-end pb-2"
                      data-testid="intake-v6-service-corner-inactive-note"
                    >
                      Colt service: relevant doar pentru panou ACP casetat.
                    </p>
                  ) : null}
                </div>
              ) : null}

              <div
                className={`mt-3 rounded border border-[#2A3548] bg-[#0A0F1A]/60 p-3 ${siteInstallationSectionActive ? "" : "opacity-60"}`}
                data-testid="intake-v6-mounting-site-section"
              >
                <p className="mb-2 text-[11px] font-semibold text-slate-200">Montaj la locație</p>
                {!siteInstallationSectionActive ? (
                  <p className="text-[10px] text-slate-400" data-testid="intake-v6-mounting-site-inactive-note">
                    Disponibil când scope-ul include montaj la locație.
                  </p>
                ) : (
                  <label className="flex items-center gap-2 rounded border border-[#2A3548] bg-[#0A0F1A] px-2.5 py-1.5 text-[11px] text-slate-100">
                    <input
                      type="checkbox"
                      className="h-4 w-4 accent-cyan-400"
                      checked={form.site_installation_included !== false}
                      onChange={(event) =>
                        updateForm(
                          { site_installation_included: event.target.checked },
                          { domains: ["mounting"] },
                        )
                      }
                      data-testid="intake-v6-site-installation-included"
                    />
                    Montaj la locație inclus în ofertă
                  </label>
                )}
              </div>
              </IntakeV6TechnicalDetailsAccordion>

              <IntakeV6MontajClusterShell
                title="Fundal și carcasă"
                description="Ansamblu panouri, îmbinări și alimentare 220V pe panouri — o singură decizie operator."
                tone="primary"
                statusLabel={
                  (() => {
                    const seg = readSegmentedBackground(form as unknown as Record<string, unknown>);
                    if (!seg) return acpProductActive ? "Panou ACP" : "Fără segmentare";
                    const st = String(seg.status || "").toUpperCase();
                    if (st === "CONFIRMED" || st === "PROPOSED" || st === "REJECTED" || st === "INACTIVE") {
                      return statusLabelRo(st);
                    }
                    return operatorReadinessLabelRo(st);
                  })()
                }
                statusTone={
                  (() => {
                    const seg = readSegmentedBackground(form as unknown as Record<string, unknown>);
                    const st = String(seg?.status || "").toUpperCase();
                    if (st === "CONFIRMED") return "ok";
                    if (st === "PROPOSED") return "pending";
                    return "muted";
                  })()
                }
                testId="intake-v6-fundal-carcasa-cluster"
              >
              <div
                className="sm:col-span-2 rounded border border-cyan-900/50 bg-cyan-950/20 px-3 py-3"
                data-testid="intake-v6-mounting-solution-panel"
              >
                <div className="mb-2 flex items-start justify-between gap-3">
                  <div>
                    <p className="text-[11px] font-semibold text-cyan-300">
                      {acpProductActive
                        ? "Configurație Panou ACP casetat"
                        : "Structură suport / pregătire"}
                    </p>
                    <p className="text-[10px] text-slate-400">
                      {acpProductActive
                        ? "Componentă de produs — independentă de scope-ul comercial de montaj."
                        : "Metal Premount rămâne legat de pregătirea comercială."}
                    </p>
                  </div>
                  {selectedMountingSolutionValue === METAL_PREMOUNT_TEMPLATE_CODE ||
                  selectedMountingSolutionValue === ACM_BOXED_MOUNTING_TEMPLATE_CODE ? (
                    <Link
                      to={`/product-system?template=${encodeURIComponent(selectedMountingSolutionValue)}`}
                      className="rounded border border-cyan-800/50 px-2 py-1 text-[10px] text-cyan-300 hover:bg-cyan-900/30"
                    >
                      Product System
                    </Link>
                  ) : null}
                </div>

                <label className={REVIEW_FIELD_BLOCK_CLASS}>
                  <span className={REVIEW_FIELD_LABEL_CLASS}>
                    {acpProductActive ? "Panou ACP casetat" : "Soluție"}
                  </span>
                  <select
                    className={REVIEW_SELECT_CLASS}
                    value={selectedMountingSolutionValue}
                    disabled={mountingSolutionSelectorLocked}
                    onChange={(event) => {
                      const value = event.target.value as MountingSolutionSelectorValue;
                      if (
                        !mountingPrepActive &&
                        value === METAL_PREMOUNT_TEMPLATE_CODE
                      ) {
                        return;
                      }
                      const currentConfig =
                        readMountingSolution(form as Record<string, unknown>)?.configuration ??
                        hydrateMountingSolutionFromLegacy(form as Record<string, unknown>)?.configuration;
                      const patch = buildMountingSolutionPatch(value, currentConfig) as Partial<IntakeV6FinishSetup>;
                      const keepsCable =
                        value === METAL_PREMOUNT_TEMPLATE_CODE || value === ACM_BOXED_MOUNTING_TEMPLATE_CODE;
                      const keepsCorner = value === ACM_BOXED_MOUNTING_TEMPLATE_CODE;
                      updateForm(
                        {
                          ...patch,
                          mains_cable_length_m: keepsCable ? form.mains_cable_length_m ?? null : null,
                          power_supply_service_corner: keepsCorner
                            ? form.power_supply_service_corner ?? null
                            : null,
                        },
                        { domains: ["mounting"] },
                      );
                    }}
                    data-testid="intake-v6-mounting-solution-selector"
                  >
                    {MOUNTING_SOLUTION_OPTIONS.map((option) => (
                      <option
                        key={option.value || "none"}
                        value={option.value}
                        disabled={
                          !mountingPrepActive && option.value === METAL_PREMOUNT_TEMPLATE_CODE
                        }
                      >
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>

                {selectedMountingSolutionValue === METAL_PREMOUNT_TEMPLATE_CODE ? (
                  <div className="mt-3 grid gap-2 sm:grid-cols-3">
                    <label className={REVIEW_FIELD_BLOCK_CLASS}>
                      <span className={REVIEW_FIELD_LABEL_CLASS}>Material bară (PS)</span>
                      <select
                        className={REVIEW_SELECT_CLASS}
                        value={String(metalMountingConfiguration.bar_material ?? "steel")}
                        disabled={!mountingPrepActive}
                        onChange={(event) =>
                          updateForm(
                            buildMountingSolutionPatch(METAL_PREMOUNT_TEMPLATE_CODE, {
                              ...metalMountingConfiguration,
                              bar_material: event.target.value,
                            }) as Partial<IntakeV6FinishSetup>,
                            { domains: ["mounting"] },
                          )
                        }
                        data-testid="intake-v6-mounting-solution-bar-material"
                      >
                        <option value="steel">Oțel</option>
                        <option value="aluminum">Aluminiu</option>
                      </select>
                    </label>
                    <label className={REVIEW_FIELD_BLOCK_CLASS}>
                      <span className={REVIEW_FIELD_LABEL_CLASS}>Profil (PS)</span>
                      <select
                        className={REVIEW_SELECT_CLASS}
                        value={String(metalMountingConfiguration.mounting_bar_profile ?? "30x30x1.5")}
                        disabled={!mountingPrepActive}
                        onChange={(event) =>
                          updateForm(
                            buildMountingSolutionPatch(METAL_PREMOUNT_TEMPLATE_CODE, {
                              ...metalMountingConfiguration,
                              mounting_bar_profile: event.target.value,
                            }) as Partial<IntakeV6FinishSetup>,
                            { domains: ["mounting"] },
                          )
                        }
                        data-testid="intake-v6-mounting-solution-bar-profile"
                      >
                        <option value="30x30x1.5">30x30x1.5</option>
                      </select>
                    </label>
                    <label className={REVIEW_FIELD_BLOCK_CLASS}>
                      <span className={REVIEW_FIELD_LABEL_CLASS}>Număr bare (PS)</span>
                      <input
                        type="number"
                        min={1}
                        step={1}
                        className="w-full rounded border border-[#2A3548] bg-[#0A0F1A] px-2 py-1.5 text-[11px] outline-none disabled:cursor-not-allowed disabled:opacity-60"
                        value={Number(metalMountingConfiguration.bar_count ?? 2)}
                        disabled={!mountingPrepActive}
                        onChange={(event) =>
                          updateForm(
                            buildMountingSolutionPatch(METAL_PREMOUNT_TEMPLATE_CODE, {
                              ...metalMountingConfiguration,
                              bar_count: Number(event.target.value),
                            }) as Partial<IntakeV6FinishSetup>,
                            { domains: ["mounting"] },
                          )
                        }
                        data-testid="intake-v6-mounting-solution-bar-count"
                      />
                    </label>
                    <p
                      className="sm:col-span-3 text-[10px] text-slate-500"
                      data-testid="intake-v6-mounting-solution-template-identity"
                    >
                      Detaliu tehnic · ID șablon: {METAL_PREMOUNT_TEMPLATE_CODE}
                    </p>
                  </div>
                ) : null}

                {selectedMountingSolutionValue === ACM_BOXED_MOUNTING_TEMPLATE_CODE ? (
                  <div
                    className="mt-3 grid gap-2 sm:grid-cols-3"
                    data-testid="intake-v6-acp-product-config-section"
                  >
                    <div
                      className="sm:col-span-3 rounded border border-cyan-500/25 bg-cyan-500/5 px-2.5 py-2 text-[11px] text-slate-300"
                      data-testid="intake-v6-mounting-svg-dimension-source"
                    >
                      <p className="font-semibold text-slate-100">Panou ACP casetat · dimensiuni din Pasul 1</p>
                      <p className="mt-0.5">
                        Dimensiuni panou:{" "}
                        <span className="text-cyan-100">
                          {Number(acmMountingConfiguration.panel_width_mm).toFixed(1)} ×{" "}
                          {Number(acmMountingConfiguration.panel_height_mm).toFixed(1)} mm
                        </span>
                        {acmMountingConfiguration.dimension_source === "svg_support_selection" ||
                        acmMountingConfiguration.contour_id ||
                        acmMountingConfiguration.geometry_hash ? (
                          <span className="text-slate-500"> · sursă: SVG confirmat</span>
                        ) : (
                          <span className="text-amber-200"> · sursă: implicit / need SVG</span>
                        )}
                      </p>
                      {acmMountingConfiguration.unit_ambiguity ? (
                        <p
                          className="mt-1 text-amber-200"
                          data-testid="intake-v6-mounting-unit-ambiguity-guard"
                        >
                          Dimensiune SVG neconfirmată fizic (unit ambiguity / viewBox-as-mm guard).
                        </p>
                      ) : null}
                      {acmMountingConfiguration.geometry_hash ||
                      acmMountingConfiguration.contour_id ? (
                        <p className="mt-1 font-mono text-[10px] text-slate-500">
                          contour={String(acmMountingConfiguration.contour_id ?? "—")} · hash=
                          {String(acmMountingConfiguration.geometry_hash ?? "—")}
                        </p>
                      ) : null}
                    </div>
                    {ACM_BOXED_MOUNTING_QUOTE_INPUT_FIELDS.filter((field) =>
                      [
                        "panel_width_mm",
                        "panel_height_mm",
                        "acm_thickness_mm",
                        "return_depth_mm",
                        "rear_lip_mm",
                        "fold_sides",
                        "v_groove_angle_deg",
                        // frame_clearance_mm removed — not fit-allowance authority (fixed 2 mm total)
                      ].includes(field.key),
                    ).map((field) => (
                      <label key={field.key} className={REVIEW_FIELD_BLOCK_CLASS}>
                        <span className={REVIEW_FIELD_LABEL_CLASS}>
                          {field.label}
                          {field.unit ? ` (${field.unit})` : ""}
                        </span>
                        {field.selectOptions ? (
                          <select
                            className={REVIEW_SELECT_CLASS}
                            value={String(acmMountingConfiguration[field.key] ?? field.placeholder)}
                            disabled={!acpProductActive}
                            onChange={(event) =>
                              updateForm(
                                buildMountingSolutionPatch(ACM_BOXED_MOUNTING_TEMPLATE_CODE, {
                                  ...acmMountingConfiguration,
                                  [field.key]: event.target.value,
                                }) as Partial<IntakeV6FinishSetup>,
                                { domains: ["mounting"] },
                              )
                            }
                            data-testid={`intake-v6-mounting-acm-${field.key}`}
                          >
                            {field.selectOptions.map((option) => (
                              <option key={option.value} value={option.value}>
                                {option.label}
                              </option>
                            ))}
                          </select>
                        ) : field.numberOptions ? (
                          <select
                            className={REVIEW_SELECT_CLASS}
                            value={String(acmMountingConfiguration[field.key] ?? field.placeholder)}
                            disabled={!acpProductActive}
                            onChange={(event) =>
                              updateForm(
                                buildMountingSolutionPatch(ACM_BOXED_MOUNTING_TEMPLATE_CODE, {
                                  ...acmMountingConfiguration,
                                  [field.key]: Number(event.target.value),
                                }) as Partial<IntakeV6FinishSetup>,
                                { domains: ["mounting"] },
                              )
                            }
                            data-testid={`intake-v6-mounting-acm-${field.key}`}
                          >
                            {field.numberOptions.map((option) => (
                              <option key={option} value={option}>
                                {option} mm
                              </option>
                            ))}
                          </select>
                        ) : (
                          <input
                            type="number"
                            min={field.min ?? 0}
                            step={field.key.includes("_mm") ? 1 : 0.1}
                            className="w-full rounded border border-[#2A3548] bg-[#0A0F1A] px-2 py-1.5 text-[11px] outline-none disabled:cursor-not-allowed disabled:opacity-60"
                            value={Number(acmMountingConfiguration[field.key] ?? field.placeholder)}
                            disabled={!acpProductActive}
                            onChange={(event) =>
                              updateForm(
                                buildMountingSolutionPatch(ACM_BOXED_MOUNTING_TEMPLATE_CODE, {
                                  ...acmMountingConfiguration,
                                  [field.key]: Number(event.target.value),
                                }) as Partial<IntakeV6FinishSetup>,
                                { domains: ["mounting"] },
                              )
                            }
                            data-testid={`intake-v6-mounting-acm-${field.key}`}
                          />
                        )}
                      </label>
                    ))}
                    {Boolean(acmMountingConfiguration.internal_frame_enabled) ||
                    Boolean(
                      (acmMountingConfiguration.internal_frame as InternalFrameConfig | undefined)
                        ?.enabled,
                    ) ? (
                      <div
                        className="sm:col-span-3 rounded border border-amber-500/30 bg-amber-500/5 px-2.5 py-2 space-y-2"
                        data-testid="intake-v6-acm-internal-frame-section"
                      >
                        <p className="text-[11px] font-semibold text-amber-100">
                          Cadru interior panou ACP
                        </p>
                        <p className="text-[10px] text-slate-400">
                          Marja fixă de montaj: {TOTAL_FIT_ALLOWANCE_MM} mm total (nu este clearance
                          editabil).
                        </p>
                        {(() => {
                          const existing = (acmMountingConfiguration.internal_frame ||
                            {}) as Partial<InternalFrameConfig>;
                          const proposed = proposeInternalFrame({
                            enabled: true,
                            materialCode: existing.material_code ?? null,
                            profileCode: existing.profile_code ?? null,
                            panelWidthMm: Number(acmMountingConfiguration.panel_width_mm),
                            panelHeightMm: Number(acmMountingConfiguration.panel_height_mm),
                            panelThicknessMm: Number(acmMountingConfiguration.acm_thickness_mm ?? 3),
                            orientation: (existing.crossbar_orientation as CrossbarOrientation) || null,
                            confirmedCrossbarCount: existing.confirmed_crossbar_count ?? null,
                            overrideReason: existing.override_reason ?? null,
                          });
                          const patchFrame = (next: InternalFrameConfig) =>
                            updateForm(
                              buildMountingSolutionPatch(ACM_BOXED_MOUNTING_TEMPLATE_CODE, {
                                ...acmMountingConfiguration,
                                internal_frame_enabled: true,
                                internal_frame: next,
                              }) as Partial<IntakeV6FinishSetup>,
                              { domains: ["mounting"] },
                            );
                          return (
                            <>
                              <label className={REVIEW_FIELD_BLOCK_CLASS}>
                                <span className={REVIEW_FIELD_LABEL_CLASS}>Material</span>
                                <select
                                  className={REVIEW_SELECT_CLASS}
                                  disabled={!acpProductActive}
                                  value={proposed.material_code ?? ""}
                                  onChange={(event) =>
                                    patchFrame(
                                      proposeInternalFrame({
                                        enabled: true,
                                        materialCode: event.target.value || null,
                                        profileCode: null,
                                        panelWidthMm: Number(acmMountingConfiguration.panel_width_mm),
                                        panelHeightMm: Number(acmMountingConfiguration.panel_height_mm),
                                        panelThicknessMm: Number(
                                          acmMountingConfiguration.acm_thickness_mm ?? 3,
                                        ),
                                        orientation: proposed.crossbar_orientation,
                                        confirmedCrossbarCount: proposed.confirmed_crossbar_count,
                                        overrideReason: proposed.override_reason,
                                      }),
                                    )
                                  }
                                  data-testid="intake-v6-acm-internal-frame-material"
                                >
                                  <option value="">Selectează…</option>
                                  <option value={MAT_STRUCT_STEEL}>Oțel</option>
                                  <option value={MAT_STRUCT_ALUMINIUM}>Aluminiu</option>
                                </select>
                              </label>
                              <div
                                className="rounded border border-rose-500/30 bg-rose-950/20 px-2 py-1.5 text-[10px] text-rose-100"
                                data-testid="intake-v6-acm-internal-frame-profile-gate"
                              >
                                Profil: catalog gol — necesită setarea inițială a profilului (admin).
                                Nu există selector free-text; confirmă secțiunile reale înainte de
                                configurare completă.
                              </div>
                              <p
                                className="text-[11px] text-slate-200"
                                data-testid="intake-v6-acm-internal-frame-dimensions"
                              >
                                Dimensiune cadru calculată:{" "}
                                {proposed.frame_outer_width_mm?.toFixed(1) ?? "—"} ×{" "}
                                {proposed.frame_outer_height_mm?.toFixed(1) ?? "—"} mm
                              </p>
                              <p className="text-[10px] text-slate-400">
                                Spacing max traverse:{" "}
                                {proposed.max_crossbar_spacing_mm != null
                                  ? `${proposed.max_crossbar_spacing_mm} mm`
                                  : "— (selectează material)"}
                              </p>
                              <label className={REVIEW_FIELD_BLOCK_CLASS}>
                                <span className={REVIEW_FIELD_LABEL_CLASS}>Orientare traverse</span>
                                <select
                                  className={REVIEW_SELECT_CLASS}
                                  disabled={!acpProductActive || !proposed.material_code}
                                  value={proposed.crossbar_orientation ?? ""}
                                  onChange={(event) => {
                                    const orientation = (event.target.value ||
                                      null) as CrossbarOrientation | null;
                                    const next = proposeInternalFrame({
                                      enabled: true,
                                      materialCode: proposed.material_code,
                                      profileCode: proposed.profile_code,
                                      panelWidthMm: Number(acmMountingConfiguration.panel_width_mm),
                                      panelHeightMm: Number(acmMountingConfiguration.panel_height_mm),
                                      panelThicknessMm: Number(
                                        acmMountingConfiguration.acm_thickness_mm ?? 3,
                                      ),
                                      orientation,
                                      confirmedCrossbarCount: null,
                                      overrideReason: null,
                                    });
                                    patchFrame(next);
                                  }}
                                  data-testid="intake-v6-acm-internal-frame-orientation"
                                >
                                  <option value="">Selectează…</option>
                                  <option value="VERTICAL">Vertical</option>
                                  <option value="HORIZONTAL">Orizontal</option>
                                </select>
                              </label>
                              {proposed.suggested_crossbar_count != null ? (
                                <div className="space-y-1 text-[11px] text-slate-200">
                                  <p data-testid="intake-v6-acm-internal-frame-crossbar-suggestion">
                                    Propunere traverse: {proposed.suggested_crossbar_count} (confirmă)
                                  </p>
                                  <button
                                    type="button"
                                    className="rounded border border-emerald-600/40 bg-emerald-950/30 px-2 py-1 text-[10px] text-emerald-100 disabled:opacity-40"
                                    disabled={!acpProductActive}
                                    data-testid="intake-v6-acm-internal-frame-confirm-crossbars"
                                    onClick={() =>
                                      patchFrame(
                                        proposeInternalFrame({
                                          enabled: true,
                                          materialCode: proposed.material_code,
                                          profileCode: proposed.profile_code,
                                          panelWidthMm: Number(
                                            acmMountingConfiguration.panel_width_mm,
                                          ),
                                          panelHeightMm: Number(
                                            acmMountingConfiguration.panel_height_mm,
                                          ),
                                          panelThicknessMm: Number(
                                            acmMountingConfiguration.acm_thickness_mm ?? 3,
                                          ),
                                          orientation: proposed.crossbar_orientation,
                                          confirmedCrossbarCount: proposed.suggested_crossbar_count,
                                          overrideReason: null,
                                        }),
                                      )
                                    }
                                  >
                                    Confirmă propunerea
                                  </button>
                                </div>
                              ) : null}
                              <p
                                className="text-[10px] text-amber-200"
                                data-testid="intake-v6-acm-internal-frame-status"
                              >
                                Status: {proposed.confirmation_status}
                                {proposed.blockers?.length
                                  ? ` · ${proposed.blockers.join(", ")}`
                                  : ""}
                              </p>
                            </>
                          );
                        })()}
                      </div>
                    ) : null}
                    <p
                      className="sm:col-span-3 text-[10px] text-slate-500"
                      data-testid="intake-v6-mounting-solution-template-identity"
                    >
                      Detaliu tehnic · ID șablon: {ACM_BOXED_MOUNTING_TEMPLATE_CODE}
                    </p>
                  </div>
                ) : null}

                {acpProductActive ? (
                  <IntakeV6AcpLocalFaceModulesPanel
                    finish={form as unknown as Record<string, unknown>}
                    disabled={state.phase === "persisting"}
                    onPatchBindings={(next) =>
                      updateForm(
                        { svg_component_bindings: next } as Partial<IntakeV6FinishSetup>,
                        { domains: ["mounting"] },
                      )
                    }
                  />
                ) : null}

                {readSegmentedBackground(form as unknown as Record<string, unknown>) ? (
                  <IntakeV6SegmentedBackgroundPanel
                    finish={form as unknown as Record<string, unknown>}
                    disabled={state.phase === "persisting"}
                    onPatch={(patch) => {
                      // Confirm/reject must hit finish-setup immediately — do not rely on
                      // debounced autosave (operator can leave Review while "sync pending").
                      setForm((prev) => {
                        const next = syncLighting({
                          ...prev,
                          ...(patch as Partial<IntakeV6FinishSetup>),
                          confirmed: false,
                        });
                        pendingDirtyDomainsRef.current.add("mounting");
                        void persistFinishSetupState(next, true);
                        return next;
                      });
                    }}
                  />
                ) : null}

                <IntakeV6SegmentedElectricalPanel
                  finish={form as unknown as Record<string, unknown>}
                  disabled={state.phase === "persisting"}
                  onPatchSegmented={(segmentedNext) => {
                    setForm((prev) => {
                      const next = syncLighting({
                        ...prev,
                        segmented_background: segmentedNext as IntakeV6FinishSetup["segmented_background"],
                        confirmed: false,
                      });
                      pendingDirtyDomainsRef.current.add("mounting");
                      void persistFinishSetupState(next, true);
                      return next;
                    });
                  }}
                />
                {!shouldShowLegacyServiceCornerInput(form as unknown as Record<string, unknown>) ? (
                  <p
                    className="mt-2 text-[10px] text-slate-400"
                    data-testid="intake-v6-legacy-corner-superseded-note"
                  >
                    {legacyServiceCornerSupersededNoteRo()}
                  </p>
                ) : null}
              </div>
              </IntakeV6MontajClusterShell>

              <IntakeV6TechnicalDetailsAccordion
                title="Avansat"
                hint="Opțional — prindere, colț service, diagnostice ownership (tehnic)"
                defaultOpen={false}
                testId="intake-v6-montaj-advanced-cluster"
              >
                <p
                  className="rounded border border-slate-700/60 bg-slate-950/40 px-2.5 py-2 text-[10px] text-slate-400"
                  data-testid="intake-v6-mounting-ownership-note"
                >
                  Ownership: MOUNTING → structura_suport + sablon_montaj · mounting_system = metodă ·
                  mounting_solution = suport · metal_support_required = alias · ambalare ≠ MOUNTING ·
                  chip sold MOUNTING = blocat · mounting_method = doar nume țintă.
                </p>
                <p
                  className="mt-2 rounded border border-cyan-900/30 bg-cyan-950/10 px-2.5 py-2 text-[10px] text-cyan-100/80"
                  data-testid="intake-v6-template-ownership-note"
                >
                  Șablon montaj = sablon_montaj (INSTALLATION_TEMPLATE). Activ doar cu
                  mounting_template_enabled. Nu cere finisaj suprafață.
                </p>

                {acpProductActive ? (
                  <div
                    className="mt-3 rounded border border-violet-500/30 bg-violet-950/20 px-3 py-3 space-y-2"
                    data-testid="intake-v6-fixing-system-section"
                  >
                    <p className="text-[11px] font-semibold text-violet-100">Sistem de prindere</p>
                    <p className="text-[10px] text-slate-400">
                      Sistem tehnic de fixare pe perete — separat de cadrul interior ACP și de serviciul
                      comercial de montaj.
                    </p>
                    <label className={REVIEW_FIELD_BLOCK_CLASS}>
                      <span className={REVIEW_FIELD_LABEL_CLASS}>Tip sistem</span>
                      <select
                        className={REVIEW_SELECT_CLASS}
                        value={mountingFixingSystem.type_code ?? ""}
                        onChange={(event) => {
                          const value = event.target.value;
                          updateForm(
                            {
                              mounting_fixing_system:
                                value === VERTICAL_STEEL_BRACKET
                                  ? selectVerticalSteelBracket()
                                  : emptyMountingFixingSystem(),
                            } as Partial<IntakeV6FinishSetup>,
                            { domains: ["mounting"] },
                          );
                        }}
                        data-testid="intake-v6-fixing-system-type"
                      >
                        <option value="">— neconfigurat —</option>
                        <option value={VERTICAL_STEEL_BRACKET}>Brat otel vertical</option>
                      </select>
                    </label>
                    {mountingFixingSystem.type_code === VERTICAL_STEEL_BRACKET ? (
                      <div
                        className="grid gap-2 sm:grid-cols-2 text-[11px] text-slate-200"
                        data-testid="intake-v6-fixing-vertical-steel-details"
                      >
                        <p data-testid="intake-v6-fixing-main-profile">
                          <span className="text-slate-400">Profil principal: </span>
                          Bara otel 20×20×1.5 mm
                        </p>
                        <p data-testid="intake-v6-fixing-top-angle">
                          <span className="text-slate-400">Cornier superior: </span>
                          Cornier otel debitat la lucrare
                        </p>
                        <p data-testid="intake-v6-fixing-bottom-bar">
                          <span className="text-slate-400">Bara inferioară: </span>
                          Bara orizontală debitată la lucrare
                        </p>
                        <p data-testid="intake-v6-fixing-manual-dims">
                          <span className="text-slate-400">Dimensiuni cornier și bară: </span>
                          Se stabilesc de operator pentru fiecare lucrare
                        </p>
                        <p className="sm:col-span-2" data-testid="intake-v6-fixing-fastener">
                          <span className="text-slate-400">Fixare inferioară: </span>
                          Autoforante cap hexagonal 4.5×60 mm
                        </p>
                        <p className="sm:col-span-2 text-[10px] text-amber-100/90">
                          Status dimensiuni: necesită confirmare manuală — fără cotă fixă sau
                          formulă automată.
                        </p>
                      </div>
                    ) : null}
                  </div>
                ) : null}

                <div className="mt-3 grid gap-2 sm:grid-cols-2">
                  <div className={REVIEW_FIELD_BLOCK_CLASS}>
                    <span className={REVIEW_FIELD_LABEL_CLASS}>
                      {lettersCanonicalFieldLabels?.mounting_system ?? "Sistem montaj"}{" "}
                      (canonic V1 / read-only aici)
                    </span>
                    <p
                      className="rounded border border-[#2A3548] bg-[#0A0F1A] px-2 py-1.5 text-[11px] text-slate-300"
                      data-testid="intake-v6-mounting-system-readonly"
                    >
                      {templateContract.allowedMountingSystems.find(
                        (option) => option.value === legacyMountingSystemDisplay,
                      )?.label ?? legacyMountingSystemDisplay}
                    </p>
                  </div>
                  {mountingUsesBars ? (
                    <div className={REVIEW_FIELD_BLOCK_CLASS}>
                      <span className={REVIEW_FIELD_LABEL_CLASS}>Profil bare (legacy, read-only)</span>
                      <p
                        className="rounded border border-[#2A3548] bg-[#0A0F1A] px-2 py-1.5 text-[11px] text-slate-300"
                        data-testid="intake-v6-mounting-bar-profile-readonly"
                      >
                        {legacyMountingProfileDisplay}
                      </p>
                    </div>
                  ) : null}
                </div>

                {acpProductActive &&
                shouldShowLegacyServiceCornerInput(form as unknown as Record<string, unknown>) ? (
                  <div
                    className="mt-3 grid gap-2 sm:grid-cols-2"
                    data-testid="intake-v6-acp-service-corner-fields"
                  >
                    {resolveServiceCornerUiMode(form as unknown as Record<string, unknown>) ===
                    "legacy_demoted_segmented_pending" ? (
                      <p
                        className="sm:col-span-2 text-[10px] text-amber-100/90"
                        data-testid="intake-v6-legacy-corner-demoted-note"
                      >
                        {legacyServiceCornerDemotedNoteRo()}
                      </p>
                    ) : null}
                    <label className={REVIEW_FIELD_BLOCK_CLASS}>
                      <span className={REVIEW_FIELD_LABEL_CLASS}>Colt service transformator</span>
                      <select
                        className={REVIEW_SELECT_CLASS}
                        value={form.power_supply_service_corner ?? ""}
                        onChange={(event) =>
                          updateForm(
                            {
                              power_supply_service_corner: normalizePowerSupplyServiceCorner(
                                event.target.value || null,
                              ),
                            },
                            { domains: ["mounting"] },
                          )
                        }
                        data-testid="intake-v6-power-supply-service-corner"
                      >
                        <option value="">— selectează —</option>
                        <option value="TOP_LEFT">Stânga sus</option>
                        <option value="TOP_RIGHT">Dreapta sus</option>
                        <option value="BOTTOM_LEFT">Stânga jos</option>
                        <option value="BOTTOM_RIGHT">Dreapta jos</option>
                        <option value="MANUAL_CONFIRMED">Confirmat manual</option>
                      </select>
                    </label>
                  </div>
                ) : null}

                {mountingPrepActive ? (
                  <div className="mt-3 grid gap-2 sm:grid-cols-2" data-testid="intake-v6-process-body-fields">
                    <label className={REVIEW_FIELD_BLOCK_CLASS}>
                      <span className={REVIEW_FIELD_LABEL_CLASS}>Finisaj șuruburi corp</span>
                      <select
                        className={REVIEW_SELECT_CLASS}
                        value={form.service_screw_finish ?? "NATURAL"}
                        onChange={(event) =>
                          updateForm(
                            {
                              service_screw_finish: normalizeServiceScrewFinish(
                                event.target.value,
                              ) ?? "NATURAL",
                            },
                            { domains: ["mounting"] },
                          )
                        }
                        data-testid="intake-v6-service-screw-finish"
                      >
                        <option value="NATURAL">Naturale</option>
                        <option value="PAINTED_TO_MATCH_CANT">Vopsite în culoarea cantului</option>
                      </select>
                    </label>
                  </div>
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
                      disabled={!volumModuleApplicable}
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
              </IntakeV6TechnicalDetailsAccordion>
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

      {returnCantReadonlyAwareness.operator_readiness === "blocked" ? (
        <p
          className="mb-2 rounded border border-amber-500/25 bg-amber-500/5 px-3 py-2 text-[11px] leading-relaxed text-amber-100/90"
          data-testid="intake-v6-return-cant-blocked-operator-message"
        >
          Cantul necesită valori obligatorii lipsă. Verifică adâncimea și finisajul cantului.
        </p>
      ) : null}

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
      {returnCantReadonlyAwareness.operator_readiness === "blocked" ? (
        <IntakeV6ReturnCantBlockedStateAwarenessPanel model={returnCantReadonlyAwareness} />
      ) : returnCantReadonlyAwareness.technical_blockers.length > 0 ? (
        <IntakeV6ReturnCantBlockedStateAwarenessPanel
          model={returnCantReadonlyAwareness}
          variant="technicalOnly"
        />
      ) : null}
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






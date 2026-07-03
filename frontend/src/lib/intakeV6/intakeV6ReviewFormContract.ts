import type { IntakeV6FinishSetup } from "@/lib/intakeV6/intakeV6Api";
import { DEFAULT_RETURN_DEPTH_MM } from "@/lib/intakeV6/intakeV6LetterGroups";
import {
  INTAKE_V6_DEFAULT_RETURN_FINISH_TYPE,
  INTAKE_V6_RETURN_FINISH_UI_OPTIONS,
  type IntakeV6ReturnFinishUiOption,
} from "@/lib/intakeV6/intakeV6ReturnFinishRules";
import type { TemplateFormOption, TemplateFormOptions } from "@/lib/intakeV6/useTemplateFormContract";

const REVIEW_STEP_LEGACY_DEFAULTS = {
  faceFinishType: "oracal_651",
  returnFinishType: INTAKE_V6_DEFAULT_RETURN_FINISH_TYPE,
  returnDepthMm: DEFAULT_RETURN_DEPTH_MM,
  lightingSystemType: "led_modules",
  lightColor: "neutral",
  ledModulePowerW: 0.75,
  selectedPsuWatts: 100,
  mountingSystem: "direct_wall",
  mountingTemplateEnabled: true,
  mountingTemplateMaterialType: "forex",
  mountingBarProfile: "30x30x1.5",
  faceVinylRollWidthMm: 1000,
  emblemLightingMode: "area_lit",
} as const;

const RETURN_FINISH_TYPE_TO_UI_OPTION: Record<string, IntakeV6ReturnFinishUiOption | null> = {
  white_aluminum: "white",
  black_aluminum: "black",
  gold_aluminum: "gold",
  mirror_silver: "silver",
  ral_paint: "ral_paint",
  oracal_wrapped: "oracal_wrapped",
};

export interface IntakeV6ReviewFormContractAdapter {
  source: "template_contract" | "fallback";
  finishes: {
    faceFinishOptions: readonly TemplateFormOption[];
    allowedReturnDepthMm: readonly number[];
    allowedReturnFinishOptions: readonly TemplateFormOption[];
    allowedVinylRollWidths: readonly TemplateFormOption[];
  };
  lighting: {
    allowedLightingSystems: readonly TemplateFormOption[];
    allowedLightColors: readonly TemplateFormOption[];
    allowedLedModulePowerW: readonly TemplateFormOption[];
    allowedEmblemLightingModes: readonly TemplateFormOption[];
    allowedPsuWatts: readonly number[];
  };
  mounting: {
    allowedMountingSystems: readonly TemplateFormOption[];
    allowedMountingBarProfiles: readonly string[];
    allowedMountingTemplateMaterials: readonly TemplateFormOption[];
  };
  artwork: {
    allowedReturnDepthMm: readonly number[];
    allowedReturnFinishOptions: readonly TemplateFormOption[];
    allowedEmblemLightingModes: readonly TemplateFormOption[];
  };
  defaults: {
    faceFinishType: string;
    returnFinishType: NonNullable<IntakeV6FinishSetup["return_finish_type"]>;
    returnDepthMm: number;
    lightingSystemType: NonNullable<IntakeV6FinishSetup["lighting_system_type"]>;
    lightColor: NonNullable<IntakeV6FinishSetup["light_color"]>;
    ledModulePowerW: number;
    selectedPsuWatts: number;
    mountingSystem: NonNullable<IntakeV6FinishSetup["mounting_system"]>;
    mountingTemplateEnabled: boolean;
    mountingTemplateMaterialType: NonNullable<IntakeV6FinishSetup["mounting_template_material_type"]>;
    mountingBarProfile: string;
    faceVinylRollWidthMm: number;
    emblemLightingMode: NonNullable<IntakeV6FinishSetup["emblem_lighting_mode"]>;
  };
}

function hasRuntimeTemplateContract(contract: TemplateFormOptions | null | undefined): boolean {
  return Boolean(contract?.contract);
}

function coalesceOptions<T>(options: readonly T[] | null | undefined, fallback: readonly T[]): readonly T[] {
  return options != null && options.length > 0 ? options : fallback;
}

function coalesceDefault<T>(
  contractPresent: boolean,
  runtimeValue: T | null | undefined,
  fallback: T,
): T {
  return contractPresent && runtimeValue != null ? runtimeValue : fallback;
}

function resolveAllowedReturnFinishOptions(
  contract: TemplateFormOptions | null | undefined,
): readonly TemplateFormOption[] {
  const fallback = INTAKE_V6_RETURN_FINISH_UI_OPTIONS;
  const allowedTypes = contract?.allowedReturnFinishTypes ?? [];
  if (!hasRuntimeTemplateContract(contract) || allowedTypes.length === 0) {
    // TODO(intake-v6-phase2): remove fallback once template contract is mandatory for ReviewStep.
    return fallback;
  }

  const allowedUiValues = new Set<IntakeV6ReturnFinishUiOption>();
  for (const option of allowedTypes) {
    const uiValue = RETURN_FINISH_TYPE_TO_UI_OPTION[String(option.value ?? "").trim().toLowerCase()] ?? null;
    if (uiValue) {
      allowedUiValues.add(uiValue);
    }
  }

  const filtered = fallback.filter((option) => allowedUiValues.has(option.value));
  return filtered.length > 0 ? filtered : fallback;
}

export function buildIntakeV6ReviewFormContract(
  contract: TemplateFormOptions | null | undefined,
): IntakeV6ReviewFormContractAdapter {
  const contractPresent = hasRuntimeTemplateContract(contract);
  const allowedReturnFinishOptions = resolveAllowedReturnFinishOptions(contract);

  return {
    source: contractPresent ? "template_contract" : "fallback",
    finishes: {
      faceFinishOptions: coalesceOptions(contract?.faceFinishOptions, []),
      allowedReturnDepthMm: coalesceOptions(contract?.allowedReturnDepthMm, [REVIEW_STEP_LEGACY_DEFAULTS.returnDepthMm]),
      allowedReturnFinishOptions,
      allowedVinylRollWidths: coalesceOptions(contract?.allowedVinylRollWidths, [
        { value: String(REVIEW_STEP_LEGACY_DEFAULTS.faceVinylRollWidthMm), label: `${REVIEW_STEP_LEGACY_DEFAULTS.faceVinylRollWidthMm} mm` },
      ]),
    },
    lighting: {
      allowedLightingSystems: coalesceOptions(contract?.allowedLightingSystems, [
        { value: "led_modules", label: "Module LED" },
      ]),
      allowedLightColors: coalesceOptions(contract?.allowedLightColors, [
        { value: REVIEW_STEP_LEGACY_DEFAULTS.lightColor, label: "Neutral white" },
      ]),
      allowedLedModulePowerW: coalesceOptions(contract?.allowedLedModulePowerW, [
        { value: String(REVIEW_STEP_LEGACY_DEFAULTS.ledModulePowerW), label: `${REVIEW_STEP_LEGACY_DEFAULTS.ledModulePowerW} W / modul` },
      ]),
      allowedEmblemLightingModes: coalesceOptions(contract?.allowedEmblemLightingModes, [
        { value: REVIEW_STEP_LEGACY_DEFAULTS.emblemLightingMode, label: "Emblema luminoasa - calcul pe arie" },
      ]),
      allowedPsuWatts: coalesceOptions(contract?.allowedPsuWatts, [REVIEW_STEP_LEGACY_DEFAULTS.selectedPsuWatts]),
    },
    mounting: {
      allowedMountingSystems: coalesceOptions(contract?.allowedMountingSystems, [
        { value: REVIEW_STEP_LEGACY_DEFAULTS.mountingSystem, label: "Direct perete" },
      ]),
      allowedMountingBarProfiles: coalesceOptions(contract?.allowedMountingBarProfiles, [REVIEW_STEP_LEGACY_DEFAULTS.mountingBarProfile]),
      allowedMountingTemplateMaterials: coalesceOptions(contract?.allowedMountingTemplateMaterials, [
        { value: REVIEW_STEP_LEGACY_DEFAULTS.mountingTemplateMaterialType, label: "Forex" },
      ]),
    },
    artwork: {
      allowedReturnDepthMm: coalesceOptions(contract?.allowedReturnDepthMm, [REVIEW_STEP_LEGACY_DEFAULTS.returnDepthMm]),
      allowedReturnFinishOptions,
      allowedEmblemLightingModes: coalesceOptions(contract?.allowedEmblemLightingModes, [
        { value: REVIEW_STEP_LEGACY_DEFAULTS.emblemLightingMode, label: "Emblema luminoasa - calcul pe arie" },
      ]),
    },
    defaults: {
      faceFinishType: coalesceDefault(contractPresent, contract?.defaultFaceFinish, REVIEW_STEP_LEGACY_DEFAULTS.faceFinishType),
      returnFinishType: coalesceDefault(
        contractPresent,
        contract?.defaultReturnFinishType as NonNullable<IntakeV6FinishSetup["return_finish_type"]> | undefined,
        REVIEW_STEP_LEGACY_DEFAULTS.returnFinishType,
      ),
      returnDepthMm: coalesceDefault(contractPresent, contract?.defaultReturnDepthMm, REVIEW_STEP_LEGACY_DEFAULTS.returnDepthMm),
      lightingSystemType: coalesceDefault(
        contractPresent,
        contract?.defaultLightingSystemType as NonNullable<IntakeV6FinishSetup["lighting_system_type"]> | undefined,
        REVIEW_STEP_LEGACY_DEFAULTS.lightingSystemType,
      ),
      lightColor: coalesceDefault(
        contractPresent,
        contract?.defaultLightColor as NonNullable<IntakeV6FinishSetup["light_color"]> | undefined,
        REVIEW_STEP_LEGACY_DEFAULTS.lightColor,
      ),
      ledModulePowerW: coalesceDefault(contractPresent, contract?.defaultLedModulePowerW, REVIEW_STEP_LEGACY_DEFAULTS.ledModulePowerW),
      selectedPsuWatts: coalesceDefault(contractPresent, contract?.defaultPsuWatts, REVIEW_STEP_LEGACY_DEFAULTS.selectedPsuWatts),
      mountingSystem: coalesceDefault(
        contractPresent,
        contract?.defaultMountingSystem as NonNullable<IntakeV6FinishSetup["mounting_system"]> | undefined,
        REVIEW_STEP_LEGACY_DEFAULTS.mountingSystem,
      ),
      mountingTemplateEnabled: coalesceDefault(
        contractPresent,
        contract?.defaultMountingTemplateEnabled,
        REVIEW_STEP_LEGACY_DEFAULTS.mountingTemplateEnabled,
      ),
      mountingTemplateMaterialType: coalesceDefault(
        contractPresent,
        contract?.defaultMountingTemplateMaterial as NonNullable<IntakeV6FinishSetup["mounting_template_material_type"]> | undefined,
        REVIEW_STEP_LEGACY_DEFAULTS.mountingTemplateMaterialType,
      ),
      mountingBarProfile: coalesceDefault(
        contractPresent,
        contract?.defaultMountingBarProfile,
        REVIEW_STEP_LEGACY_DEFAULTS.mountingBarProfile,
      ),
      faceVinylRollWidthMm: coalesceDefault(
        contractPresent,
        contract?.defaultVinylRollWidthMm,
        REVIEW_STEP_LEGACY_DEFAULTS.faceVinylRollWidthMm,
      ),
      emblemLightingMode: coalesceDefault(
        contractPresent,
        contract?.defaultEmblemLightingMode as NonNullable<IntakeV6FinishSetup["emblem_lighting_mode"]> | undefined,
        REVIEW_STEP_LEGACY_DEFAULTS.emblemLightingMode,
      ),
    },
  };
}
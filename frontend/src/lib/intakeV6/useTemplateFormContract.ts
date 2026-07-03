/**
 * Hook: load template form contract and derive dynamic form options.
 *
 * Replaces hardcoded face/return finish option sets
 * with options driven by the TPL-VOLUMETRIC-LETTERS dossier variant_fields.
 */

import { useEffect, useRef, useState } from "react";
import { toast } from "@/components/ui/sonner";
import {
  getIntakeV6TemplateFormContract,
  type IntakeV4TemplateFormContractResponse,
  type IntakeV4TemplateFormContractField,
} from "./intakeV6Api";
import {
  INTAKE_V4_FACE_FINISH_OPTIONS,
} from "./intakeV4FaceFinishOptions";
import {
  INTAKE_V6_RETURN_FINISH_UI_OPTIONS,
  type IntakeV6ReturnFinishUiOption,
} from "./intakeV6ReturnFinishOptions";
import { ALLOWED_RETURN_DEPTH_MM } from "@/lib/volumetricQuoteInput";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface TemplateFormOption {
  value: string;
  label: string;
}

export interface TemplateFormOptions {
  faceFinishOptions: readonly TemplateFormOption[];
  returnFinishOptions: readonly { value: IntakeV6ReturnFinishUiOption; label: string }[];
  allowedReturnDepthMm: readonly number[];
  allowedPsuWatts: readonly number[];
  allowedMountingSystems: readonly TemplateFormOption[];
  allowedMountingBarProfiles: readonly string[];
  allowedReturnFinishTypes: readonly TemplateFormOption[];
  allowedLightingSystems: readonly TemplateFormOption[];
  allowedLightColors: readonly TemplateFormOption[];
  allowedLedModulePowerW: readonly TemplateFormOption[];
  allowedMountingTemplateMaterials: readonly TemplateFormOption[];
  allowedVinylRollWidths: readonly TemplateFormOption[];
  allowedEmblemLightingModes: readonly TemplateFormOption[];
  defaultFaceFinish: string;
  defaultReturnDepthMm: number;
  defaultPsuWatts: number;
  defaultMountingSystem: string;
  defaultMountingTemplateEnabled: boolean;
  defaultMountingBarProfile: string;
  defaultReturnFinishType: string;
  defaultLightingSystemType: string;
  defaultLightColor: string;
  defaultLedModulePowerW: number;
  defaultMountingTemplateMaterial: string;
  defaultVinylRollWidthMm: number;
  defaultEmblemLightingMode: string;
  templateCode: string | null;
  dossierSource: "product_blueprint_dossier" | "static_contract_fallback" | null;
  alignmentStatus: "aligned" | "partial" | "blocked" | null;
  loading: boolean;
  error: string | null;
  contract: IntakeV4TemplateFormContractResponse | null;
}

// ---------------------------------------------------------------------------
// Label maps for mapping dossier allowed_values → UI labels
// ---------------------------------------------------------------------------

const FACE_FINISH_LABEL: Record<string, string> = {
  none: "Fără finisaj — plexiglas brut",
  oracal_651: "Oracal 651",
  oracal_641: "Oracal 641",
  oracal_8500: "Oracal 8500 — translucid",
  printed_vinyl: "Print pe vinyl",
  printed_laminated_vinyl: "Print + laminare pe vinyl",
  print_laminate: "Print + laminare",
  colored_plexiglas: "Plexiglas colorat",
};

const RETURN_UI_LABEL: Record<IntakeV6ReturnFinishUiOption, string> = {
  white: "Alb",
  black: "Negru",
  gold: "Auriu",
  silver: "Argintiu",
  ral_paint: "Vopsit RAL",
  oracal_wrapped: "Oracal 651",
};

const MOUNTING_SYSTEM_LABEL: Record<string, string> = {
  direct_wall: "Direct perete",
  steel_bars: "Bare oțel",
  aluminum_bars: "Bare aluminiu",
  acm_panel: "Panou ACM",
};

const RETURN_FINISH_LABEL: Record<string, string> = {
  white_aluminum: "Alb",
  black_aluminum: "Negru",
  gold_aluminum: "Auriu",
  mirror_silver: "Argintiu",
  ral_paint: "Vopsit RAL",
  oracal_wrapped: "Oracal 651",
};

const LIGHTING_SYSTEM_LABEL: Record<string, string> = {
  led_modules: "Module LED",
  led_strip: "Banda LED",
};

const LIGHT_COLOR_LABEL: Record<string, string> = {
  warm: "Warm white",
  neutral: "Neutral white",
  cool: "Cool white",
};

const LED_MODULE_POWER_LABEL: Record<string, string> = {
  "0.75": "0.75 W / modul",
  "1": "1.00 W / modul",
  "1.44": "1.44 W / modul",
};

const MOUNTING_TEMPLATE_MATERIAL_LABEL: Record<string, string> = {
  forex: "Forex",
  paper: "Hartie",
};

const EMBLEM_LIGHTING_LABEL: Record<string, string> = {
  area_lit: "Emblema luminoasa - calcul pe arie",
  excluded: "Emblema neluminoasa",
};

// ---------------------------------------------------------------------------
// Helpers: extract options from variant_fields
// ---------------------------------------------------------------------------

function findVariantField(
  fields: IntakeV4TemplateFormContractField[],
  key: string,
): IntakeV4TemplateFormContractField | undefined {
  return fields.find((f) => f.field_key === key);
}

function fieldDefault<T>(field: IntakeV4TemplateFormContractField | undefined, fallback: T): T {
  if (!field || field.default_value == null) return fallback;
  return field.default_value as T;
}

function buildFaceFinishOptions(
  field: IntakeV4TemplateFormContractField | undefined,
): readonly TemplateFormOption[] {
  if (!field || !field.allowed_values?.length) {
    return INTAKE_V4_FACE_FINISH_OPTIONS;
  }
  return field.allowed_values.map((v) => {
    const value = String(v);
    return { value, label: FACE_FINISH_LABEL[value] ?? value.replace(/_/g, " ") };
  });
}

function buildReturnDepthOptions(
  field: IntakeV4TemplateFormContractField | undefined,
): readonly number[] {
  if (!field || !field.allowed_values?.length) {
    return ALLOWED_RETURN_DEPTH_MM;
  }
  return field.allowed_values
    .map((v) => Number(v))
    .filter((n) => Number.isFinite(n) && n > 0)
    .sort((a, b) => a - b);
}

function buildPsuWattsOptions(
  field: IntakeV4TemplateFormContractField | undefined,
): readonly number[] {
  if (!field || !field.allowed_values?.length) {
    return [60, 100, 160, 200];
  }
  return field.allowed_values
    .map((v) => Number(v))
    .filter((n) => Number.isFinite(n) && n > 0)
    .sort((a, b) => a - b);
}

function buildMountingSystemOptions(
  field: IntakeV4TemplateFormContractField | undefined,
): readonly TemplateFormOption[] {
  if (!field || !field.allowed_values?.length) {
    return [
      { value: "direct_wall", label: "Direct perete" },
      { value: "steel_bars", label: "Bare oțel" },
      { value: "aluminum_bars", label: "Bare aluminiu" },
      { value: "acm_panel", label: "Panou ACM" },
    ];
  }
  return field.allowed_values.map((v) => {
    const value = String(v);
    return { value, label: MOUNTING_SYSTEM_LABEL[value] ?? value.replace(/_/g, " ") };
  });
}

function buildMountingBarProfileOptions(
  field: IntakeV4TemplateFormContractField | undefined,
): readonly string[] {
  if (!field || !field.allowed_values?.length) {
    return ["30x30x1.5"];
  }
  return field.allowed_values.map((v) => String(v));
}

function buildLabeledOptions(
  field: IntakeV4TemplateFormContractField | undefined,
  labelMap: Record<string, string>,
  fallbackValues: readonly string[],
): readonly TemplateFormOption[] {
  const values = field?.allowed_values?.length
    ? field.allowed_values.map((v) => String(v))
    : fallbackValues;
  return values.map((v) => ({
    value: v,
    label: labelMap[v] ?? v.replace(/_/g, " "),
  }));
}

function buildNumericLabeledOptions(
  field: IntakeV4TemplateFormContractField | undefined,
  labelMap: Record<string, string>,
  fallbackValues: readonly number[],
): readonly TemplateFormOption[] {
  const values = field?.allowed_values?.length
    ? field.allowed_values.map((v) => Number(v)).filter((n) => Number.isFinite(n))
    : fallbackValues;
  return values.map((v) => ({
    value: String(v),
    label: labelMap[String(v)] ?? `${v}`,
  }));
}

function buildVinylRollWidthOptions(
  field: IntakeV4TemplateFormContractField | undefined,
): readonly TemplateFormOption[] {
  const fallback: readonly number[] = [1000, 1260];
  const values = field?.allowed_values?.length
    ? field.allowed_values.map((v) => Number(v)).filter((n) => Number.isFinite(n) && n > 0)
    : fallback;
  return values.map((v) => ({
    value: String(v),
    label: `${v} mm`,
  }));
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useTemplateFormContract(workspaceId: string | undefined): TemplateFormOptions {
  const [contract, setContract] = useState<IntakeV4TemplateFormContractResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fetchedRef = useRef<string | null>(null);

  useEffect(() => {
    if (!workspaceId) return;
    if (fetchedRef.current === workspaceId) return;
    fetchedRef.current = workspaceId;

    let cancelled = false;
    setLoading(true);
    setError(null);

    getIntakeV6TemplateFormContract(workspaceId)
      .then((data) => {
        if (cancelled) return;
        setContract(data);
        setLoading(false);

        // Toast only for hard blockers. Partial alignment and warnings are shown inline in Review.
        if (data.blockers?.length) {
          for (const blocker of data.blockers.slice(0, 3)) {
            toast.error(`Blocker: ${blocker.message}`, { duration: 10000 });
          }
        }
      })
      .catch((err) => {
        if (cancelled) return;
        const message = err instanceof Error ? err.message : "Nu am putut încărca contractul template.";
        setError(message);
        setLoading(false);
        toast.error("Eroare la încărcarea contractului template", {
          description: message,
          duration: 8000,
        });
      });

    return () => {
      cancelled = true;
    };
  }, [workspaceId]);

  // Derive options from contract variant_fields
  const fields = contract?.variant_fields ?? [];
  const faceField = findVariantField(fields, "face_finish_type");
  const depthField = findVariantField(fields, "return_depth_mm");
  const psuField = findVariantField(fields, "selected_psu_watts");
  const mountingField = findVariantField(fields, "mounting_system");
  const barProfileField = findVariantField(fields, "mounting_bar_profile");
  const mountingTemplateField = findVariantField(fields, "mounting_template_enabled");
  const returnFinishField = findVariantField(fields, "return_finish_type");
  const lightingSystemField = findVariantField(fields, "lighting_system_type");
  const lightColorField = findVariantField(fields, "light_color");
  const ledModulePowerField = findVariantField(fields, "led_module_power_w");
  const mountingTemplateMaterialField = findVariantField(fields, "mounting_template_material_type");
  const vinylRollWidthField = findVariantField(fields, "face_vinyl_roll_width_mm");
  const emblemLightingField = findVariantField(fields, "emblem_lighting_mode");

  return {
    faceFinishOptions: buildFaceFinishOptions(faceField),
    returnFinishOptions: INTAKE_V6_RETURN_FINISH_UI_OPTIONS,
    allowedReturnDepthMm: buildReturnDepthOptions(depthField),
    allowedPsuWatts: buildPsuWattsOptions(psuField),
    allowedMountingSystems: buildMountingSystemOptions(mountingField),
    allowedMountingBarProfiles: buildMountingBarProfileOptions(barProfileField),
    allowedReturnFinishTypes: buildLabeledOptions(returnFinishField, RETURN_FINISH_LABEL, ["white_aluminum", "black_aluminum", "gold_aluminum", "mirror_silver", "ral_paint", "oracal_wrapped"]),
    allowedLightingSystems: buildLabeledOptions(lightingSystemField, LIGHTING_SYSTEM_LABEL, ["led_modules", "led_strip"]),
    allowedLightColors: buildLabeledOptions(lightColorField, LIGHT_COLOR_LABEL, ["warm", "neutral", "cool"]),
    allowedLedModulePowerW: buildNumericLabeledOptions(ledModulePowerField, LED_MODULE_POWER_LABEL, [0.75, 1, 1.44]),
    allowedMountingTemplateMaterials: buildLabeledOptions(mountingTemplateMaterialField, MOUNTING_TEMPLATE_MATERIAL_LABEL, ["forex", "paper"]),
    allowedVinylRollWidths: buildVinylRollWidthOptions(vinylRollWidthField),
    allowedEmblemLightingModes: buildLabeledOptions(emblemLightingField, EMBLEM_LIGHTING_LABEL, ["area_lit", "excluded"]),
    defaultFaceFinish: String(fieldDefault(faceField, "none")),
    defaultReturnDepthMm: Number(fieldDefault(depthField, 60)),
    defaultPsuWatts: Number(fieldDefault(psuField, 100)),
    defaultMountingSystem: String(fieldDefault(mountingField, "direct_wall")),
    defaultMountingTemplateEnabled: Boolean(fieldDefault(mountingTemplateField, true)),
    defaultMountingBarProfile: String(fieldDefault(barProfileField, "30x30x1.5")),
    defaultReturnFinishType: String(fieldDefault(returnFinishField, "white_aluminum")),
    defaultLightingSystemType: String(fieldDefault(lightingSystemField, "led_modules")),
    defaultLightColor: String(fieldDefault(lightColorField, "warm")),
    defaultLedModulePowerW: Number(fieldDefault(ledModulePowerField, 0.75)),
    defaultMountingTemplateMaterial: String(fieldDefault(mountingTemplateMaterialField, "forex")),
    defaultVinylRollWidthMm: Number(fieldDefault(vinylRollWidthField, 1000)),
    defaultEmblemLightingMode: String(fieldDefault(emblemLightingField, "area_lit")),
    templateCode: contract?.template_code ?? null,
    dossierSource: contract?.dossier_source ?? null,
    alignmentStatus: contract?.alignment_status ?? null,
    loading,
    error,
    contract,
  };
}

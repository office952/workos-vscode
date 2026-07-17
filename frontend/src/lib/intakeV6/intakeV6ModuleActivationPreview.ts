/**
 * Read-only module activation preview for Intake V6 modular form contract (Step 5B).
 * Informational only — does not build ProductDefinition, price, or tasks.
 */

import type {
  IntakeV6ModularActivationKind,
  IntakeV6ModularFormContractResponse,
  IntakeV6ModularFormModuleSection,
} from "./intakeV6ModularFormContractTypes";

export type ModuleActivationPreviewState =
  | "always_on"
  | "active"
  | "inactive"
  | "pending"
  | "conditional_active";

export interface ModuleActivationPreviewItem {
  moduleCode: string;
  moduleName: string;
  activationKind: IntakeV6ModularActivationKind;
  state: ModuleActivationPreviewState;
  operatorHint: string;
  missingFields: string[];
}

export interface OperatorDisplayLine {
  key: string;
  label: string;
  hint: string;
  state: ModuleActivationPreviewState;
  missingFields: string[];
}

export interface OperatorProductSummaryView {
  geometryStatus: {
    label: string;
    ready: boolean;
  } | null;
  productReady: OperatorDisplayLine[];
  mounting: OperatorDisplayLine[];
  mountingNotApplicableNote: string | null;
  technical: OperatorDisplayLine[];
}

export interface ModuleActivationPreviewResult {
  items: ModuleActivationPreviewItem[];
  operatorView: OperatorProductSummaryView;
  missingImportantFields: string[];
  structuraSuportDerived: boolean;
  triggerMismatchNote: string | null;
}

export interface IntakeV6ModularPreviewInput {
  finishSetup: Record<string, unknown> | null | undefined;
  quoteGeometry: Record<string, unknown> | null | undefined;
  svgSource: Record<string, unknown> | null | undefined;
  analysisReady: boolean;
}

const BAR_MOUNTING = new Set(["steel_bars", "aluminum_bars"]);

function readString(obj: Record<string, unknown> | null | undefined, key: string): string | null {
  if (!obj || typeof obj !== "object") return null;
  const value = obj[key];
  if (value == null) return null;
  const text = String(value).trim();
  return text.length > 0 ? text : null;
}

function readBoolean(obj: Record<string, unknown> | null | undefined, key: string): boolean | null {
  if (!obj || typeof obj !== "object") return null;
  const value = obj[key];
  if (typeof value === "boolean") return value;
  return null;
}

function hasGeometryBasics(input: IntakeV6ModularPreviewInput): boolean {
  if (!input.analysisReady) return false;
  const svgName = readString(input.svgSource, "file_name");
  if (!svgName) return false;
  const letterCount = input.quoteGeometry?.letter_count;
  if (letterCount == null || !Number.isFinite(Number(letterCount))) return false;
  return true;
}

function isIlluminated(finish: Record<string, unknown> | null | undefined): boolean {
  const illuminated = readBoolean(finish, "illuminated");
  if (illuminated === false) return false;
  const lighting = readString(finish, "lighting_system_type");
  if (lighting && lighting !== "none") return true;
  return illuminated !== false;
}

function resolveStructuraSuportState(mountingSystem: string | null): ModuleActivationPreviewState {
  if (!mountingSystem) return "pending";
  if (BAR_MOUNTING.has(mountingSystem)) return "active";
  return "inactive";
}

function resolveSistemLedState(finish: Record<string, unknown> | null | undefined): ModuleActivationPreviewState {
  if (!isIlluminated(finish)) return "inactive";
  const lighting = readString(finish, "lighting_system_type");
  if (!lighting || lighting === "none") return "pending";
  return "conditional_active";
}

function resolveFinisajeState(_finish: Record<string, unknown> | null | undefined): ModuleActivationPreviewState {
  // Surface FINISH only — template is sablon_montaj.
  return "always_on";
}

function resolveSablonMontajState(
  finish: Record<string, unknown> | null | undefined,
): ModuleActivationPreviewState {
  return readBoolean(finish, "mounting_template_enabled") === true
    ? "conditional_active"
    : "inactive";
}

function resolveAmbalareState(): ModuleActivationPreviewState {
  // Full Letters composition responsibility — always included in product structure preview.
  return "always_on";
}

function operatorHintForState(
  module: IntakeV6ModularFormModuleSection,
  state: ModuleActivationPreviewState,
): string {
  if (state === "always_on") return "Inclus în structura produsului";
  if (state === "active") return "Detectat din selecțiile curente";
  if (state === "conditional_active") {
    if (module.module_code === "sistem_led") return "Iluminare configurată";
    if (module.module_code === "sablon_montaj") return "Șablon montaj activ";
    return "Activ când condițiile sunt îndeplinite";
  }
  if (state === "pending") {
    if (module.module_code === "geometry_svg") return "Completează analiza SVG";
    if (module.module_code === "structura_suport") return "Alege sistemul de montaj";
    if (module.module_code === "sistem_led") return "Completează setările de iluminare";
    return "Completează câmpurile necesare";
  }
  if (module.module_code === "structura_suport") return "Nu este necesar pentru montajul ales";
  if (module.module_code === "sistem_led") return "Produs neluminat";
  return "Nu se aplică";
}

function resolveModuleState(
  module: IntakeV6ModularFormModuleSection,
  input: IntakeV6ModularPreviewInput,
  finish: Record<string, unknown> | null | undefined,
): ModuleActivationPreviewState {
  const mountingSystem = readString(finish, "mounting_system");

  switch (module.module_code) {
    case "geometry_svg":
      return hasGeometryBasics(input) ? "always_on" : "pending";
    case "debitare_fata":
    case "debitare_spate":
    case "modelare_cant":
      return input.analysisReady ? "always_on" : "pending";
    case "structura_suport":
      return resolveStructuraSuportState(mountingSystem);
    case "sistem_led":
      return resolveSistemLedState(finish);
    case "finisaje":
      return resolveFinisajeState(finish);
    case "sablon_montaj":
      return resolveSablonMontajState(finish);
    case "ambalare_livrare_montaj":
      return resolveAmbalareState();
    default:
      if (module.activation_kind === "always_on" || module.activation_kind === "required_module") {
        return input.analysisReady ? "always_on" : "pending";
      }
      if (module.activation_kind === "optional_addon") return "inactive";
      return "pending";
  }
}

function collectMissingFields(
  module: IntakeV6ModularFormModuleSection,
  state: ModuleActivationPreviewState,
  finish: Record<string, unknown> | null | undefined,
  quoteGeometry: Record<string, unknown> | null | undefined,
): string[] {
  if (state === "inactive") return [];

  const missing: string[] = [];
  for (const fieldKey of module.required_form_fields ?? []) {
    if (fieldKey === "vector_file") {
      continue;
    }
    const finishValue =
      finish && fieldKey in finish
        ? finish[fieldKey]
        : undefined;
    const geometryValue =
      quoteGeometry && fieldKey in quoteGeometry
        ? quoteGeometry[fieldKey]
        : undefined;
    const hasValue =
      (finishValue != null && finishValue !== "") ||
      (geometryValue != null && geometryValue !== "");
    if (!hasValue && state !== "inactive") {
      missing.push(fieldKey);
    }
  }
  return missing;
}

const OPERATOR_LABELS: Record<string, string> = {
  debitare_fata: "Față litere",
  modelare_cant: "Laterale / cant",
  debitare_spate: "Spate litere",
  sistem_led: "Iluminare LED",
  finisaje: "Finisaje suprafață",
  sablon_montaj: "Șablon montaj",
  ambalare_livrare_montaj: "Ambalare / logistică",
  structura_suport: "Structură metalică premontaj",
  geometry_svg: "Analiză SVG și geometrie",
};

function operatorLabelForModule(moduleCode: string): string {
  return OPERATOR_LABELS[moduleCode] ?? moduleCode.replace(/_/g, " ");
}

/** Downgrade contract states when required form fields are still missing — avoids false "Inclus/Activ". */
function effectiveOperatorDisplayState(
  state: ModuleActivationPreviewState,
  missingFields: string[],
): ModuleActivationPreviewState {
  if (state === "inactive") return "inactive";
  if (missingFields.length === 0) return state;
  if (state === "always_on" || state === "active" || state === "conditional_active") {
    return "pending";
  }
  return state;
}

function toOperatorDisplayLine(
  key: string,
  state: ModuleActivationPreviewState,
  missingFields: string[],
  finish: Record<string, unknown> | null | undefined,
): OperatorDisplayLine {
  const displayState = effectiveOperatorDisplayState(state, missingFields);
  return {
    key,
    label: operatorLabelForModule(key),
    hint: operatorHintForProductLine(key, displayState, finish),
    state: displayState,
    missingFields,
  };
}

function operatorHintForProductLine(
  moduleCode: string,
  state: ModuleActivationPreviewState,
  finish: Record<string, unknown> | null | undefined,
): string {
  switch (moduleCode) {
    case "debitare_fata":
      return state === "pending" ? "Verifica daca finisajul fetelor este corect." : "Pregătită din fișierul încărcat";
    case "modelare_cant":
      return state === "pending" ? "Verifica latimea cantului." : "Volum aluminiu / cant lateral";
    case "debitare_spate":
      return state === "pending" ? "Verifica daca varianta de confectionare a spatelui este corecta." : "Capac/spate pregătit";
    case "sistem_led":
      if (state === "inactive") return "Fără iluminare";
      if (state === "pending") return "LED în curs de completare";
      return "LED configurat";
    case "finisaje":
      return "Finisaje pe față/litere (suprafață)";
    case "sablon_montaj":
      if (state === "inactive") return "Șablon montaj inactiv";
      return "Șablon montaj activ";
    case "ambalare_livrare_montaj":
      return "Ambalare / logistică (compoziție)";
    case "structura_suport":
      if (state === "active" || state === "conditional_active") {
        return "Structură metalică pentru montaj cu bare";
      }
      if (state === "pending") return "Alege sistemul de montaj";
      return "Nu se aplică pentru montajul ales";
    case "geometry_svg":
      return state === "pending" ? "Completează analiza fișierului SVG" : "Geometrie extrasă din SVG";
    default:
      return operatorHintForState(
        { module_code: moduleCode } as IntakeV6ModularFormModuleSection,
        state,
      );
  }
}

function buildOperatorProductSummaryView(
  items: ModuleActivationPreviewItem[],
  input: IntakeV6ModularPreviewInput,
  finish: Record<string, unknown> | null | undefined,
): OperatorProductSummaryView {
  const byCode = new Map(items.map((item) => [item.moduleCode, item]));

  const geometryItem = byCode.get("geometry_svg");
  const geometryReady = geometryItem?.state === "always_on";
  const geometryStatus = geometryItem
    ? {
        label: geometryReady ? "Fișier SVG analizat" : "Geometrie în curs de pregătire",
        ready: geometryReady,
      }
    : input.analysisReady
      ? { label: "Fișier SVG analizat", ready: true }
      : null;

  const productModuleOrder = [
    "debitare_fata",
    "modelare_cant",
    "debitare_spate",
    "sistem_led",
    "finisaje",
    "ambalare_livrare_montaj",
  ] as const;

  const productReady: OperatorDisplayLine[] = [];
  for (const code of productModuleOrder) {
    const item = byCode.get(code);
    if (!item) continue;
    if (item.state === "inactive" && code !== "sistem_led") continue;
    productReady.push(toOperatorDisplayLine(code, item.state, item.missingFields, finish));
  }

  const structura = byCode.get("structura_suport");
  const sablon = byCode.get("sablon_montaj");
  const mounting: OperatorDisplayLine[] = [];
  let mountingNotApplicableNote: string | null = null;

  if (structura && (structura.state === "active" || structura.state === "conditional_active")) {
    mounting.push(toOperatorDisplayLine("structura_suport", structura.state, structura.missingFields, finish));
  } else if (structura?.state === "inactive") {
    mountingNotApplicableNote = "Structură metalică: nu se aplică pentru selecția curentă.";
  }
  if (sablon && (sablon.state === "active" || sablon.state === "conditional_active")) {
    mounting.push(toOperatorDisplayLine("sablon_montaj", sablon.state, sablon.missingFields, finish));
  }

  const technical: OperatorDisplayLine[] = [];
  if (geometryItem) {
    technical.push({
      key: "geometry_svg",
      label: operatorLabelForModule("geometry_svg"),
      hint: operatorHintForProductLine("geometry_svg", geometryItem.state, finish),
      state: geometryItem.state,
      missingFields: geometryItem.missingFields,
    });
  }

  return {
    geometryStatus,
    productReady,
    mounting,
    mountingNotApplicableNote,
    technical,
  };
}

const OPERATOR_ATTENTION_MESSAGES: Partial<Record<string, string>> = {
  debitare_fata: "Verifica daca finisajul fetelor este corect.",
  modelare_cant: "Verifica latimea cantului.",
  debitare_spate: "Verifica daca varianta de confectionare a spatelui este corecta.",
};

export function resolveModuleActivationAttentionWarnings(
  preview: ModuleActivationPreviewResult | null | undefined,
): string[] {
  if (!preview) return [];

  const warnings: string[] = [];
  const lines = [
    ...preview.operatorView.productReady,
    ...preview.operatorView.mounting,
  ];

  for (const line of lines) {
    if (line.state !== "pending" && line.missingFields.length === 0) continue;
    const message = OPERATOR_ATTENTION_MESSAGES[line.key];
    if (message && !warnings.includes(message)) {
      warnings.push(message);
    }
  }

  if (preview.triggerMismatchNote && preview.structuraSuportDerived) {
    warnings.push(preview.triggerMismatchNote);
  }

  return warnings;
}

export function buildModuleActivationPreview(
  contract: IntakeV6ModularFormContractResponse | null | undefined,
  input: IntakeV6ModularPreviewInput,
): ModuleActivationPreviewResult | null {
  if (!contract?.modules?.length) return null;

  const finish =
    input.finishSetup != null && typeof input.finishSetup === "object" && !Array.isArray(input.finishSetup)
      ? (input.finishSetup as Record<string, unknown>)
      : null;
  const quoteGeometry =
    input.quoteGeometry != null && typeof input.quoteGeometry === "object" && !Array.isArray(input.quoteGeometry)
      ? (input.quoteGeometry as Record<string, unknown>)
      : null;

  const mountingSystem = readString(finish, "mounting_system");
  const structuraSuportDerived = mountingSystem != null && BAR_MOUNTING.has(mountingSystem);

  const triggerMismatchNote =
    contract.trigger_alignments?.find((a) => a.warning_code === "TRIGGER_FIELD_MISMATCH") != null
      ? structuraSuportDerived
        ? "Montaj cu bare — structura metalică va fi derivată la ofertare (compatibil cu selecția curentă)."
        : "Sistemul de montaj ales determină dacă este necesară structura metalică suplimentară."
      : null;

  const items: ModuleActivationPreviewItem[] = contract.modules
    .filter((m) => m.operational_status === "ACTIVE_OPERATIONAL")
    .map((module) => {
      const state = resolveModuleState(module, input, finish);
      const missingFields = collectMissingFields(module, state, finish, quoteGeometry);
      return {
        moduleCode: module.module_code,
        moduleName: module.module_name,
        activationKind: module.activation_kind,
        state,
        operatorHint: operatorHintForState(module, state),
        missingFields,
      };
    });

  const missingImportantFields = [
    ...new Set(items.flatMap((item) => item.missingFields)),
  ];

  const operatorView = buildOperatorProductSummaryView(items, input, finish);

  return {
    items,
    operatorView,
    missingImportantFields,
    structuraSuportDerived,
    triggerMismatchNote,
  };
}

export function modularContractLoadStatus(
  loading: boolean,
  error: string | null,
  contract: IntakeV6ModularFormContractResponse | null,
): "loading" | "loaded" | "unavailable" | "fallback" {
  if (loading) return "loading";
  if (contract) return "loaded";
  if (error) return "fallback";
  return "unavailable";
}

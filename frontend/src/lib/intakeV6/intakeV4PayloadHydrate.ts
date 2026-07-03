import type { LayerAutoRole, LayerRoleConfirmation, SvgAnalysisReport } from "@/lib/svgAnalyzer";
import type { IntakeV4LayerRoleSetup } from "./intakeV4Api";
import type { IntakeV4LayerChip, IntakeV4StepId, IntakeV4SvgFileMeta } from "./intakeV4Contracts";
import { layerChipsFromLayerRoleConfirmation } from "./intakeV4LayerRoleBridge";

export interface IntakeV4HydratedAnalyzerState {
  svg: IntakeV4SvgFileMeta;
  svgSource: string | null;
  analyzerReport: SvgAnalysisReport;
  layerRoleConfirmation: LayerRoleConfirmation;
  layerChips: IntakeV4LayerChip[];
}

function parseLayerRoleSetup(raw: unknown): IntakeV4LayerRoleSetup | null {
  if (raw == null || typeof raw !== "object" || Array.isArray(raw)) return null;
  const layers = (raw as Record<string, unknown>).layers;
  if (!Array.isArray(layers)) return null;
  return raw as IntakeV4LayerRoleSetup;
}

function isSvgAnalysisReport(raw: unknown): raw is SvgAnalysisReport {
  return raw != null && typeof raw === "object" && !Array.isArray(raw);
}

export function mergeServerLayerRolesIntoConfirmation(
  confirmation: LayerRoleConfirmation,
  serverSetup: IntakeV4LayerRoleSetup,
): LayerRoleConfirmation {
  const serverByKey = new Map(serverSetup.layers.map((layer) => [layer.layer_key, layer]));
  const layers = confirmation.layers.map((entry) => {
    const server = serverByKey.get(entry.layerKey);
    if (!server) return entry;
    const confirmedRole =
      typeof server.confirmed_role === "string"
        ? (server.confirmed_role as LayerAutoRole)
        : entry.confirmedRole;
    return {
      ...entry,
      confirmedRole,
      confirmationState: server.confirmation_state ?? entry.confirmationState,
      operatorNote: server.operator_note ?? entry.operatorNote,
    };
  });

  return {
    ...confirmation,
    layers,
    confirmationStatus: serverSetup.confirmation_status ?? confirmation.confirmationStatus,
  };
}

export function hydrateSvgMetaFromPayload(
  payload: Record<string, unknown> | undefined,
): IntakeV4SvgFileMeta | null {
  const svgSource = payload?.svg_source;
  if (svgSource == null || typeof svgSource !== "object" || Array.isArray(svgSource)) {
    return null;
  }
  const name = (svgSource as Record<string, unknown>).file_name;
  const size = (svgSource as Record<string, unknown>).file_size_bytes;
  if (typeof name !== "string" || typeof size !== "number") return null;

  const svgText =
    typeof payload?.svg_source_text === "string" && payload.svg_source_text.length > 0
      ? payload.svg_source_text
      : null;

  return {
    fileName: name,
    fileSizeBytes: size,
    previewSource: svgText,
  };
}

export function hydrateAnalyzerStateFromPayload(
  payload: Record<string, unknown> | undefined,
): IntakeV4HydratedAnalyzerState | null {
  if (!isSvgAnalysisReport(payload?.svg_analysis_json)) return null;

  const report = payload.svg_analysis_json;
  const confirmationDraft = report.layerRoleConfirmation;
  if (!confirmationDraft || !Array.isArray(confirmationDraft.layers)) return null;

  const serverSetup = parseLayerRoleSetup(payload?.layer_role_setup);
  const layerRoleConfirmation = serverSetup
    ? mergeServerLayerRolesIntoConfirmation(confirmationDraft, serverSetup)
    : confirmationDraft;

  const svg = hydrateSvgMetaFromPayload(payload);
  if (!svg) return null;

  const svgSource =
    typeof payload?.svg_source_text === "string" && payload.svg_source_text.length > 0
      ? payload.svg_source_text
      : null;

  return {
    svg,
    svgSource,
    analyzerReport: report,
    layerRoleConfirmation,
    layerChips: layerChipsFromLayerRoleConfirmation(layerRoleConfirmation),
  };
}

export function resolveIntakeV4StepFromReadiness(
  readinessStatus: string | null | undefined,
  payload: Record<string, unknown> | undefined,
): IntakeV4StepId {
  if (readinessStatus === "ready_for_quote_preview") return "confirm";
  if (readinessStatus === "finish_setup_incomplete") return "review";

  const finish = payload?.finish_setup;
  if (finish != null && typeof finish === "object" && !Array.isArray(finish)) {
    if ((finish as Record<string, unknown>).confirmed === true) return "confirm";
  }

  const hasAnalysis = payload?.svg_analysis_json != null;
  const setup = parseLayerRoleSetup(payload?.layer_role_setup);
  if (hasAnalysis && setup?.confirmation_status === "complete") return "review";

  return "layers";
}

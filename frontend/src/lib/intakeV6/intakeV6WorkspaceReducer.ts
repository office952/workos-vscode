import type {
  IntakeV6LayerChip,
  IntakeV6WorkspaceAction,
  IntakeV6WorkspaceState,
} from "./intakeV6Contracts";
import type { IntakeV6WorkspaceResponse } from "./intakeV6Api";
import {
  hydrateAnalyzerStateFromPayload,
  hydrateSvgMetaFromPayload,
  resolveIntakeV6StepFromReadiness,
} from "./intakeV6PayloadHydrate";
import { getPersistedFileHash, resolveHydratedFileHashSync } from "./intakeV6AnalysisIdentity";

export const initialIntakeV6WorkspaceState: IntakeV6WorkspaceState = {
  workspaceId: null,
  phase: "idle",
  error: null,
  loadErrorCode: null,
  currentStep: "layers",
  workspace: null,
  svg: null,
  layerChips: [],
  analysisRunId: 0,
  analyzerStatus: "idle",
  analyzerError: null,
  svgSource: null,
  analyzerReport: null,
  layerRoleConfirmation: null,
  localFileHash: null,
  unsavedAnalysis: false,
};

function applyHydratedWorkspace(
  state: IntakeV6WorkspaceState,
  workspace: IntakeV6WorkspaceResponse,
  options?: { preserveLocalAnalyzer?: boolean },
): IntakeV6WorkspaceState {
  const payload = workspace.payload;
  const hydrated = hydrateAnalyzerStateFromPayload(payload);
  const svgOnly = hydrateSvgMetaFromPayload(payload);
  const hasAnalysis = payload?.svg_analysis_json != null;

  const preserveLocalAnalyzerState =
    options?.preserveLocalAnalyzer ??
    (!hasAnalysis &&
      svgOnly == null &&
      state.analyzerStatus === "ready" &&
      state.svgSource != null &&
      state.svg?.previewSource != null);
  const hydratedStep = resolveIntakeV6StepFromReadiness(workspace.readiness_status, payload);
  const currentStep = hydratedStep === "confirm" ? "review" : hydratedStep;

  if (preserveLocalAnalyzerState) {
    return {
      ...state,
      workspace,
      error: null,
      loadErrorCode: null,
      phase: "svg_ready",
    };
  }

  if (hydrated) {
    const persistedHash = getPersistedFileHash(payload);
    const hashSync = resolveHydratedFileHashSync({
      persistedFileHash: persistedHash,
      previousLocalFileHash: state.localFileHash,
      previousUnsavedAnalysis: state.unsavedAnalysis,
    });
    return {
      ...state,
      workspace,
      error: null,
      loadErrorCode: null,
      svg: hydrated.svg,
      svgSource: hydrated.svgSource,
      analyzerReport: hydrated.analyzerReport,
      layerRoleConfirmation: hydrated.layerRoleConfirmation,
      layerChips: hydrated.layerChips,
      analyzerStatus: "ready",
      analyzerError: null,
      phase: "svg_ready",
      localFileHash: hashSync.localFileHash,
      unsavedAnalysis: hashSync.unsavedAnalysis,
      currentStep,
    };
  }

  const chips = layerChipsFromWorkspacePayload(payload);
  const svg = svgOnly;
  const persistedHash = getPersistedFileHash(payload);
  const hashSync = hasAnalysis
    ? resolveHydratedFileHashSync({
        persistedFileHash: persistedHash,
        previousLocalFileHash: state.localFileHash,
        previousUnsavedAnalysis: state.unsavedAnalysis,
      })
    : null;

  return {
    ...state,
    workspace,
    error: null,
    loadErrorCode: null,
    layerChips: chips,
    svg,
    analyzerStatus: hasAnalysis ? "ready" : "idle",
    phase: chips.length > 0 || svg ? "svg_ready" : "ready",
    localFileHash: hashSync?.localFileHash ?? state.localFileHash,
    unsavedAnalysis: hashSync?.unsavedAnalysis ?? state.unsavedAnalysis,
    currentStep,
  };
}

function applyFinishSetupPersistedWorkspace(
  state: IntakeV6WorkspaceState,
  workspace: IntakeV6WorkspaceResponse,
): IntakeV6WorkspaceState {
  const derivedStep = resolveIntakeV6StepFromReadiness(workspace.readiness_status, workspace.payload);
  const currentStep =
    state.currentStep === "review" || state.currentStep === "confirm"
      ? state.currentStep
      : derivedStep;

  return {
    ...state,
    workspace,
    error: null,
    loadErrorCode: null,
    phase: "svg_ready",
    currentStep,
    unsavedAnalysis: false,
  };
}

export function intakeV6WorkspaceReducer(
  state: IntakeV6WorkspaceState,
  action: IntakeV6WorkspaceAction,
): IntakeV6WorkspaceState {
  switch (action.type) {
    case "LOAD_START":
      if (action.workspaceId !== undefined && action.workspaceId !== state.workspaceId) {
        return {
          ...initialIntakeV6WorkspaceState,
          workspaceId: action.workspaceId,
          phase: "loading",
        };
      }
      if (state.phase === "analyzing_svg" || state.phase === "persisting") {
        return state;
      }
      return { ...state, workspaceId: action.workspaceId ?? state.workspaceId, phase: "loading", error: null, loadErrorCode: null };
    case "LOAD_SUCCESS": {
      if (state.phase === "analyzing_svg" || state.phase === "persisting") {
        return { ...state, workspace: action.workspace, error: null, loadErrorCode: null };
      }
      return applyHydratedWorkspace(state, action.workspace);
    }
    case "LOAD_ERROR":
      return { ...state, phase: "error", error: action.message, loadErrorCode: action.code };
    case "SET_STEP":
      return { ...state, currentStep: action.step };
    case "ANALYZER_START":
      return {
        ...state,
        phase: "analyzing_svg",
        analyzerStatus: "analyzing",
        analyzerError: null,
        error: null,
        loadErrorCode: null,
        analysisRunId: action.runId,
        currentStep: "layers",
        svg: { fileName: action.fileName, fileSizeBytes: action.fileSizeBytes, previewSource: null },
        layerChips: [],
        svgSource: null,
        analyzerReport: null,
        layerRoleConfirmation: null,
        localFileHash: null,
        unsavedAnalysis: true,
      };
    case "ANALYZER_READY":
      if (action.runId !== state.analysisRunId) return state;
      return {
        ...state,
        phase: "svg_ready",
        analyzerStatus: "ready",
        analyzerError: action.parseWarning ?? null,
        error: null,
        loadErrorCode: null,
        svg: {
          fileName: action.fileName,
          fileSizeBytes: action.fileSizeBytes,
          previewSource: action.previewSource,
        },
        svgSource: action.svgSource,
        localFileHash: action.localFileHash,
        unsavedAnalysis: true,
        analyzerReport: action.report,
        layerRoleConfirmation: action.layerRoleConfirmation,
        layerChips: action.layerChips,
        currentStep: "layers",
      };
    case "ANALYZER_ERROR":
      if (action.runId !== state.analysisRunId) return state;
      return {
        ...state,
        phase: "error",
        analyzerStatus: "error",
        analyzerError: action.message,
        error: action.message,
      };
    case "LAYER_ROLE_CONFIRMATION_UPDATE":
      return {
        ...state,
        layerRoleConfirmation: action.layerRoleConfirmation,
        layerChips: action.layerChips,
      };
    case "PERSIST_START":
      return { ...state, phase: "persisting", error: null };
    case "PERSIST_SUCCESS": {
      const persistedHash = getPersistedFileHash(action.workspace.payload);
      const preservedStep = state.currentStep;
      const next = applyHydratedWorkspace(
        {
          ...state,
          phase: "svg_ready",
          error: null,
          loadErrorCode: null,
          localFileHash: persistedHash ?? state.localFileHash,
          unsavedAnalysis: false,
        },
        action.workspace,
        { preserveLocalAnalyzer: false },
      );
      return { ...next, currentStep: preservedStep, unsavedAnalysis: false };
    }
    case "FINISH_SETUP_PERSIST_SUCCESS":
      return applyFinishSetupPersistedWorkspace(
        {
          ...state,
          phase: "svg_ready",
          error: null,
          loadErrorCode: null,
        },
        action.workspace,
      );
    case "PERSIST_ERROR":
      return { ...state, phase: "svg_ready", error: action.message, loadErrorCode: null };
    default:
      return state;
  }
}

export function layerChipsFromWorkspacePayload(
  payload: Record<string, unknown> | undefined,
): IntakeV6LayerChip[] {
  const setup = payload?.layer_role_setup;
  if (setup == null || typeof setup !== "object" || Array.isArray(setup)) {
    return [];
  }
  const layers = (setup as Record<string, unknown>).layers;
  if (!Array.isArray(layers)) return [];

  return layers
    .filter((layer): layer is Record<string, unknown> => layer != null && typeof layer === "object")
    .map((layer) => {
      const layerKey = String(layer.layer_key ?? layer.layer_id ?? "unknown");
      const displayName = String(layer.layer_name ?? layer.layer_id ?? layerKey);
      const stateRaw = layer.confirmation_state;
      let status: IntakeV6LayerChip["status"] = "pending";
      if (stateRaw === "confirmed") status = "confirmed";
      else if (stateRaw === "ignored") status = "ignored";
      return { layerKey, displayName, status };
    });
}


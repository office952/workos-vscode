import { useCallback, useEffect, useReducer, useRef } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  persistIntakeV6AnalysisBundle,
  fetchIntakeV6Workspace,
  bootstrapIntakeV6Workspace,
  resolveIntakeV6Workspace,
} from "./intakeV6ApiAdapter";
import { IntakeV6ApiError } from "./intakeV6Api";
import type { IntakeV6FinishSetup } from "./intakeV6Api";
import { saveIntakeV6FinishSetup, saveIntakeV6OfferScope, saveIntakeV6ProductCompositionConfirmation } from "./intakeV6Api";
import { isIntakeRequestRouteKey } from "@/lib/volumetricIntakeRoute";
import { pickIntakeV6SvgFileFromFileList } from "./intakeV6SvgUploadFlow";
import {
  analyzeSvgFileForIntakeV6Client,
} from "./intakeV6ClientSvgImport";
import {
  applyLayerRoleSelection,
  type LayerAutoRole,
} from "@/lib/svgAnalyzer";
import {
  cacheIntakeV6Workspace,
  getCachedIntakeV6Workspace,
} from "./intakeV6WorkspaceCache";
import {
  layerChipsFromLayerRoleConfirmation,
  confirmAllSuggestedLayerRoles,
  layerRoleConfirmationToV6Setup,
} from "./intakeV6LayerRoleBridge";
import type { IntakeV6LoadErrorCode, IntakeV6StepId } from "./intakeV6Contracts";
import { buildIntakeV6OperatorPath } from "./intakeV6OperatorRoutes";
import {
  initialIntakeV6WorkspaceState,
  intakeV6WorkspaceReducer,
} from "./intakeV6WorkspaceReducer";
import {
  canAccessIntakeV6Step,
  canContinueFromReviewStep,
  getIntakeV6FirstBlocker,
  isFinishSetupConfirmed,
  isIntakeV6ReadyForQuotePreview,
} from "./intakeV6Readiness";
import { sha256HexFromText } from "./intakeV6AnalysisIdentity";

type ClassifiedLoadError = {
  code: IntakeV6LoadErrorCode;
  message: string;
};

function isBackendUnavailableError(err: unknown): boolean {
  if (err instanceof TypeError) return true;
  if (!(err instanceof Error)) return false;
  return /failed to fetch|networkerror|load failed|timeout|aborted|refused/i.test(err.message);
}

function classifyIntakeV6LoadError(err: unknown, routeKey: string): ClassifiedLoadError {
  if (err instanceof IntakeV6ApiError && err.status === 404) {
    if (isIntakeRequestRouteKey(routeKey)) {
      return {
        code: "INTAKE_REQUEST_NOT_FOUND",
        message: "Cererea de intake nu există sau nu mai poate fi rezolvată în Intake V6.",
      };
    }
    return {
      code: "WORKSPACE_NOT_FOUND",
      message: "Workspace V6 inexistent sau stale. Deschide /intake-v6/operator pentru un workspace nou.",
    };
  }
  if (isBackendUnavailableError(err)) {
    return {
      code: "BACKEND_UNAVAILABLE",
      message: "Backend indisponibil pentru încărcarea workspace-ului Intake V6.",
    };
  }
  return {
    code: "UNKNOWN_LOAD_ERROR",
    message: err instanceof Error ? err.message : "Workspace unavailable.",
  };
}

function hydrateFromWorkspace(workspace: ReturnType<typeof fetchIntakeV6Workspace> extends Promise<infer T> ? T : never) {
  cacheIntakeV6Workspace(workspace);
  return { type: "LOAD_SUCCESS" as const, workspace };
}

export function useIntakeV6Workspace(workspaceId: string | undefined) {
  const navigate = useNavigate();
  const location = useLocation();
  const navigateRef = useRef(navigate);
  navigateRef.current = navigate;
  const locationRef = useRef(location);
  locationRef.current = location;

  const cachedInitial =
    workspaceId != null ? getCachedIntakeV6Workspace(workspaceId) : undefined;

  const [state, dispatch] = useReducer(
    intakeV6WorkspaceReducer,
    cachedInitial
      ? {
          ...initialIntakeV6WorkspaceState,
          workspaceId,
          workspace: cachedInitial,
          phase: "ready" as const,
        }
      : {
          ...initialIntakeV6WorkspaceState,
          workspaceId: workspaceId ?? null,
        },
  );

  const analysisRunRef = useRef(0);
  const fetchStartedRef = useRef<string | null>(null);
  const workspaceIdRef = useRef(workspaceId);
  const mountedRef = useRef(true);
  workspaceIdRef.current = workspaceId;

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const activeWorkspaceId = state.workspace?.id ?? workspaceId ?? null;

  useEffect(() => {
    if (!workspaceId) {
      let cancelled = false;
      const bootstrapTitle = locationRef.current.pathname.startsWith("/intake-v6")
        ? "Operator workspace V6"
        : "Operator workspace V4";
      dispatch({ type: "LOAD_START", workspaceId: null });
      void bootstrapIntakeV6Workspace(bootstrapTitle)
        .then((created) => {
          if (cancelled) return;
          navigateRef.current(
            buildIntakeV6OperatorPath(created.id, locationRef.current.pathname),
            { replace: true },
          );
          dispatch(hydrateFromWorkspace(created));
        })
        .catch((err) => {
          if (!cancelled) {
            const classified = classifyIntakeV6LoadError(err, "");
            dispatch({
              type: "LOAD_ERROR",
              code: classified.code,
              message: err instanceof Error ? err.message : "Nu am putut crea workspace V6.",
            });
          }
        });
      return () => {
        cancelled = true;
      };
    }

    if (fetchStartedRef.current === workspaceId) {
      return;
    }
    fetchStartedRef.current = workspaceId;

    const cached = getCachedIntakeV6Workspace(workspaceId);
    dispatch({ type: "LOAD_START", workspaceId });

    let cancelled = false;

    const load = async () => {
      try {
        const workspace = isIntakeRequestRouteKey(workspaceId)
          ? await resolveIntakeV6Workspace(workspaceId)
          : await fetchIntakeV6Workspace(workspaceId);
        if (cancelled) return;
        if (workspaceIdRef.current !== workspaceId) return;
        dispatch(hydrateFromWorkspace(workspace));
      } catch (err) {
        if (cancelled) return;
        if (workspaceIdRef.current !== workspaceId) return;
        const classified = classifyIntakeV6LoadError(err, workspaceId);
        dispatch({
          type: "LOAD_ERROR",
          code: classified.code,
          message: classified.message,
        });
      }
    };

    if (cached) {
      dispatch(hydrateFromWorkspace(cached));
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, [workspaceId]);

  const setStep = useCallback(
    (step: IntakeV6StepId) => {
      dispatch({ type: "SET_STEP", step });
    },
    [],
  );

  const trySetStep = useCallback(
    (step: IntakeV6StepId) => {
      if (!canAccessIntakeV6Step(state, step)) return false;
      dispatch({ type: "SET_STEP", step });
      return true;
    },
    [state],
  );

  const importSvgFile = useCallback(
    async (file: File): Promise<boolean> => {
      const targetWorkspaceId = workspaceIdRef.current ?? state.workspace?.id;
      if (!targetWorkspaceId) {
        dispatch({
          type: "LOAD_ERROR",
          message: "Workspace V6 indisponibil - reincarca pagina.",
        });
        return false;
      }

      const picked = pickIntakeV6SvgFileFromFileList([file]);
      if (!picked.file) {
        dispatch({
          type: "ANALYZER_ERROR",
          runId: analysisRunRef.current,
          message: picked.error ?? "Fisier SVG invalid.",
        });
        return false;
      }

      const runId = analysisRunRef.current + 1;
      analysisRunRef.current = runId;

      dispatch({
        type: "ANALYZER_START",
        runId,
        fileName: picked.file.name,
        fileSizeBytes: picked.file.size,
      });

      try {
        const analyzed = await analyzeSvgFileForIntakeV6Client(picked.file);
        if (analysisRunRef.current !== runId) return false;

        if (analyzed.ok === false) {
          dispatch({
            type: "ANALYZER_ERROR",
            runId,
            message: analyzed.message,
          });
          return false;
        }

        const localFileHash = await sha256HexFromText(analyzed.svgSource);

        dispatch({
          type: "ANALYZER_READY",
          runId,
          fileName: analyzed.fileName,
          fileSizeBytes: analyzed.fileSizeBytes,
          svgSource: analyzed.svgSource,
          previewSource: analyzed.previewSource,
          localFileHash,
          report: analyzed.report,
          layerRoleConfirmation: analyzed.layerRoleConfirmation,
          layerChips: analyzed.layerChips,
          parseWarning:
            analyzed.parseErrors.length > 0 ? analyzed.parseErrors.join(" | ") : null,
        });
        return true;
      } catch (err) {
        if (analysisRunRef.current !== runId) return false;
        dispatch({
          type: "ANALYZER_ERROR",
          runId,
          message: err instanceof Error ? err.message : "Analiza SVG esuata.",
        });
        return false;
      }
    },
    [state.workspace?.id],
  );

  const updateLayerRole = useCallback(
    (layerKey: string, role: LayerAutoRole) => {
      if (!state.layerRoleConfirmation) return;
      const next = applyLayerRoleSelection(state.layerRoleConfirmation, layerKey, role);
      dispatch({
        type: "LAYER_ROLE_CONFIRMATION_UPDATE",
        layerRoleConfirmation: next,
        layerChips: layerChipsFromLayerRoleConfirmation(next),
      });
    },
    [state.layerRoleConfirmation],
  );

  const confirmAllLayerRoles = useCallback(() => {
    if (!state.layerRoleConfirmation) return;
    const next = confirmAllSuggestedLayerRoles(state.layerRoleConfirmation, state.analyzerReport);
    dispatch({
      type: "LAYER_ROLE_CONFIRMATION_UPDATE",
      layerRoleConfirmation: next,
      layerChips: layerChipsFromLayerRoleConfirmation(next),
    });
  }, [state.analyzerReport, state.layerRoleConfirmation]);

  const persistAnalysisBundle = useCallback(
    async (options?: { advanceToReview?: boolean }) => {
      const targetWorkspaceId = workspaceIdRef.current ?? state.workspace?.id;
      if (
        !targetWorkspaceId ||
        !state.svgSource ||
        !state.analyzerReport ||
        !state.layerRoleConfirmation ||
        !state.svg?.fileName
      ) {
        return false;
      }

      dispatch({ type: "PERSIST_START" });
      try {
        const layerSetup = layerRoleConfirmationToV6Setup(state.layerRoleConfirmation);
        const workspace = await persistIntakeV6AnalysisBundle(targetWorkspaceId, {
          file_name: state.svg.fileName,
          file_size_bytes: state.svg.fileSizeBytes,
          svg_text: state.svgSource,
          svg_analysis_json: state.analyzerReport as unknown as Record<string, unknown>,
          layer_role_setup: layerSetup,
        });
        if (!mountedRef.current) return false;
        cacheIntakeV6Workspace(workspace);
        dispatch({ type: "PERSIST_SUCCESS", workspace });
        if (options?.advanceToReview) {
          dispatch({ type: "SET_STEP", step: "review" });
        }
        return true;
      } catch (err) {
        if (!mountedRef.current) return false;
        dispatch({
          type: "PERSIST_ERROR",
          message: err instanceof Error ? err.message : "Salvare analiza esuata.",
        });
        return false;
      }
    },
    [state.analyzerReport, state.layerRoleConfirmation, state.svg, state.svgSource, state.workspace?.id],
  );

  const continueFromAnalyzer = useCallback(async () => {
    if (
      !state.svgSource ||
      !state.analyzerReport ||
      !state.layerRoleConfirmation ||
      !state.svg?.fileName
    ) {
      dispatch({ type: "PERSIST_ERROR", message: "Analiza SVG nu este completa." });
      return;
    }

    if (state.layerRoleConfirmation.confirmationStatus !== "complete") {
      dispatch({
        type: "PERSIST_ERROR",
        message: "Confirma rolul pentru toate straturile inainte de Pas 2.",
      });
      return;
    }

    await persistAnalysisBundle({ advanceToReview: true });
  }, [persistAnalysisBundle, state.analyzerReport, state.layerRoleConfirmation, state.svg, state.svgSource]);

  useEffect(() => {
    if (!state.unsavedAnalysis) return;
    if (state.phase === "analyzing_svg" || state.phase === "persisting" || state.phase === "loading") {
      return;
    }
    if (!state.svgSource || !state.analyzerReport || !state.layerRoleConfirmation || !state.svg?.fileName) {
      return;
    }

    const timer = window.setTimeout(() => {
      void persistAnalysisBundle();
    }, 900);

    return () => {
      window.clearTimeout(timer);
    };
  }, [
    persistAnalysisBundle,
    state.analyzerReport,
    state.layerRoleConfirmation,
    state.phase,
    state.svg?.fileName,
    state.svgSource,
    state.unsavedAnalysis,
  ]);

  useEffect(() => {
    if (!state.unsavedAnalysis) return;
    const handler = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = "";
    };
    window.addEventListener("beforeunload", handler);
    return () => {
      window.removeEventListener("beforeunload", handler);
    };
  }, [state.unsavedAnalysis]);

  const saveFinishSetup = useCallback(
    async (finishSetup: IntakeV6FinishSetup) => {
      const targetWorkspaceId = workspaceIdRef.current ?? state.workspace?.id;
      if (!targetWorkspaceId) {
        dispatch({ type: "PERSIST_ERROR", message: "Workspace V6 indisponibil." });
        return null;
      }
      dispatch({ type: "PERSIST_START" });
      try {
        const workspace = await saveIntakeV6FinishSetup(targetWorkspaceId, finishSetup);
        if (!mountedRef.current) return null;
        cacheIntakeV6Workspace(workspace);
        dispatch({ type: "FINISH_SETUP_PERSIST_SUCCESS", workspace });
        return workspace;
      } catch (err) {
        if (!mountedRef.current) return null;
        dispatch({
          type: "PERSIST_ERROR",
          message: err instanceof Error ? err.message : "Salvare finisaje esuata.",
        });
        return null;
      }
    },
    [state.workspace?.id],
  );

  const confirmProductComposition = useCallback(
    async (items?: Array<Record<string, unknown>>) => {
      const targetWorkspaceId = workspaceIdRef.current ?? state.workspace?.id;
      if (!targetWorkspaceId) {
        dispatch({ type: "PERSIST_ERROR", message: "Workspace V6 indisponibil." });
        return null;
      }
      dispatch({ type: "PERSIST_START" });
      try {
        const workspace = await saveIntakeV6ProductCompositionConfirmation(targetWorkspaceId, {
          confirmed: true,
          items,
        });
        if (!mountedRef.current) return null;
        cacheIntakeV6Workspace(workspace);
        dispatch({ type: "PERSIST_SUCCESS", workspace });
        return workspace;
      } catch (err) {
        if (!mountedRef.current) return null;
        dispatch({
          type: "PERSIST_ERROR",
          message: err instanceof Error ? err.message : "Confirmare compozitie esuata.",
        });
        return null;
      }
    },
    [state.workspace?.id],
  );

  const saveOfferScope = useCallback(
    async (input: {
      mode: "full_product" | "component_subset";
      soldModules: Array<"FACE" | "RETURN-CANT" | "BACK" | "LIGHTING" | "ELECTRICAL">;
      confirmed: boolean;
    }) => {
      const targetWorkspaceId = workspaceIdRef.current ?? state.workspace?.id;
      if (!targetWorkspaceId) {
        dispatch({ type: "PERSIST_ERROR", message: "Workspace V6 indisponibil." });
        return false;
      }
      dispatch({ type: "PERSIST_START" });
      try {
        const workspace = await saveIntakeV6OfferScope(targetWorkspaceId, {
          mode: input.mode,
          sold_modules: input.soldModules,
          confirmed: input.confirmed,
        });
        if (!mountedRef.current) return false;
        cacheIntakeV6Workspace(workspace);
        dispatch({ type: "PERSIST_SUCCESS", workspace });
        return true;
      } catch (err) {
        if (!mountedRef.current) return false;
        dispatch({
          type: "PERSIST_ERROR",
          message: err instanceof Error ? err.message : "Salvare scope ofertă eșuată.",
        });
        return false;
      }
    },
    [state.workspace?.id],
  );

  const canImportSvg = Boolean(
    activeWorkspaceId &&
      state.workspace &&
      state.phase !== "loading" &&
      state.phase !== "analyzing_svg" &&
      state.phase !== "persisting",
  );

  const canContinueFromAnalyzer =
    state.analyzerStatus === "ready" &&
    state.layerRoleConfirmation?.confirmationStatus === "complete" &&
    state.phase !== "persisting";

  const canContinueFromReview = canContinueFromReviewStep(state);

  const firstBlocker = getIntakeV6FirstBlocker(state);

  const canAccessStep = useCallback(
    (step: IntakeV6StepId) => canAccessIntakeV6Step(state, step),
    [state],
  );

  return {
    state,
    setStep,
    trySetStep,
    canAccessStep,
    importSvgFile,
    updateLayerRole,
    confirmAllLayerRoles,
    continueFromAnalyzer,
    confirmProductComposition,
    saveOfferScope,
    saveFinishSetup,
    canImportSvg,
    canContinueFromAnalyzer,
    canContinueFromReview,
    isReadyForQuotePreview: isIntakeV6ReadyForQuotePreview(state),
    firstBlocker,
  };
}

export type IntakeV6WorkspaceHook = ReturnType<typeof useIntakeV6Workspace>;






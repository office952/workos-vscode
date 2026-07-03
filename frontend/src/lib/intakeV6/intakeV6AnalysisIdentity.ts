import type { IntakeV6WorkspaceState } from "./intakeV6Contracts";

export async function sha256HexFromText(text: string): Promise<string> {
  const data = new TextEncoder().encode(text);
  const hash = await crypto.subtle.digest("SHA-256", data);
  return Array.from(new Uint8Array(hash))
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
}

export function getPersistedFileHash(payload: Record<string, unknown> | undefined): string | null {
  const svgSource = payload?.svg_source;
  if (svgSource == null || typeof svgSource !== "object" || Array.isArray(svgSource)) return null;
  const hash = (svgSource as Record<string, unknown>).file_hash;
  return typeof hash === "string" && hash.trim() ? hash.trim() : null;
}

export function hasPersistedAnalysisJson(payload: Record<string, unknown> | undefined): boolean {
  return payload?.svg_analysis_json != null;
}

export function isLayerRoleSetupComplete(payload: Record<string, unknown> | undefined): boolean {
  const setup = payload?.layer_role_setup;
  if (setup == null || typeof setup !== "object" || Array.isArray(setup)) return false;
  return (setup as Record<string, unknown>).confirmation_status === "complete";
}

export function isAnalysisPersisted(payload: Record<string, unknown> | undefined): boolean {
  return hasPersistedAnalysisJson(payload) && getPersistedFileHash(payload) != null;
}

export function isLocalAnalysisSynced(state: IntakeV6WorkspaceState): boolean {
  const persistedHash = getPersistedFileHash(state.workspace?.payload);
  const localHash = state.localFileHash;
  if (!persistedHash || !localHash) return false;
  return persistedHash === localHash;
}

export function resolveHydratedFileHashSync(params: {
  persistedFileHash: string | null;
  previousLocalFileHash: string | null;
  previousUnsavedAnalysis: boolean;
}): { localFileHash: string | null; unsavedAnalysis: boolean } {
  const { persistedFileHash, previousLocalFileHash, previousUnsavedAnalysis } = params;

  if (persistedFileHash == null) {
    return {
      localFileHash: previousLocalFileHash,
      unsavedAnalysis: previousUnsavedAnalysis || previousLocalFileHash != null,
    };
  }

  const hasLocalMismatch =
    previousLocalFileHash != null && previousLocalFileHash !== persistedFileHash;

  if (hasLocalMismatch) {
    return {
      localFileHash: previousLocalFileHash,
      unsavedAnalysis: true,
    };
  }

  return {
    localFileHash: persistedFileHash,
    unsavedAnalysis: false,
  };
}

export function hasUnsavedAnalysis(state: IntakeV6WorkspaceState): boolean {
  if (state.analyzerStatus === "analyzing") return true;
  if (state.unsavedAnalysis) return true;
  if (state.localFileHash && !isLocalAnalysisSynced(state)) return true;
  if (state.analyzerStatus === "ready" && state.svgSource && !isLocalAnalysisSynced(state)) return true;
  return false;
}

export function getAnalysisIdentityKey(state: IntakeV6WorkspaceState): string {
  const persistedHash = getPersistedFileHash(state.workspace?.payload) ?? "none";
  const localHash = state.localFileHash ?? "none";
  const runId = state.analysisRunId;
  const updatedAt = state.workspace?.updated_at ?? "none";
  return `${persistedHash}:${localHash}:${runId}:${updatedAt}`;
}

export function isAnalysisReadyForReview(state: IntakeV6WorkspaceState): boolean {
  if (!isAnalysisPersisted(state.workspace?.payload)) return false;
  if (!isLayerRoleSetupComplete(state.workspace?.payload)) return false;
  if (hasUnsavedAnalysis(state)) return false;
  if (!isLocalAnalysisSynced(state)) return false;
  return true;
}


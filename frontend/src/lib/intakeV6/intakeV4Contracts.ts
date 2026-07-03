import type { LayerRoleConfirmation, SvgAnalysisReport } from "@/lib/svgAnalyzer";
import type { IntakeV4WorkspaceResponse } from "./intakeV4Api";

export type IntakeV4StepId = "layers" | "review" | "confirm";

export type IntakeV4WorkspacePhase =
  | "idle"
  | "loading"
  | "ready"
  | "analyzing_svg"
  | "svg_ready"
  | "persisting"
  | "error";

export type IntakeV4AnalyzerStatus = "idle" | "analyzing" | "ready" | "error";

export interface IntakeV4SvgFileMeta {
  fileName: string;
  fileSizeBytes: number;
  previewSource: string | null;
}

export interface IntakeV4LayerChip {
  layerKey: string;
  displayName: string;
  status: "pending" | "confirmed" | "ignored";
}

export interface IntakeV4WorkspaceState {
  workspaceId: string | null;
  phase: IntakeV4WorkspacePhase;
  error: string | null;
  currentStep: IntakeV4StepId;
  workspace: IntakeV4WorkspaceResponse | null;
  svg: IntakeV4SvgFileMeta | null;
  layerChips: IntakeV4LayerChip[];
  analysisRunId: number;
  analyzerStatus: IntakeV4AnalyzerStatus;
  analyzerError: string | null;
  svgSource: string | null;
  analyzerReport: SvgAnalysisReport | null;
  layerRoleConfirmation: LayerRoleConfirmation | null;
  /** SHA-256 hex of current local SVG bytes (matches backend svg_source.file_hash when synced). */
  localFileHash: string | null;
  /** True after local analyze until analysis-bundle persist succeeds. */
  unsavedAnalysis: boolean;
}

export type IntakeV4WorkspaceAction =
  | { type: "LOAD_START" }
  | { type: "LOAD_SUCCESS"; workspace: IntakeV4WorkspaceResponse }
  | { type: "LOAD_ERROR"; message: string }
  | { type: "SET_STEP"; step: IntakeV4StepId }
  | { type: "ANALYZER_START"; runId: number; fileName: string; fileSizeBytes: number }
  | {
      type: "ANALYZER_READY";
      runId: number;
      fileName: string;
      fileSizeBytes: number;
      svgSource: string;
      previewSource: string;
      localFileHash: string;
      report: SvgAnalysisReport;
      layerRoleConfirmation: LayerRoleConfirmation;
      layerChips: IntakeV4LayerChip[];
      parseWarning?: string | null;
    }
  | { type: "ANALYZER_ERROR"; runId: number; message: string }
  | { type: "LAYER_ROLE_CONFIRMATION_UPDATE"; layerRoleConfirmation: LayerRoleConfirmation; layerChips: IntakeV4LayerChip[] }
  | { type: "PERSIST_START" }
  | { type: "PERSIST_SUCCESS"; workspace: IntakeV4WorkspaceResponse }
  | { type: "PERSIST_ERROR"; message: string };

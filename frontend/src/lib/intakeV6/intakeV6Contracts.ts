import type { LayerRoleConfirmation, SvgAnalysisReport } from "@/lib/svgAnalyzer";
import type { IntakeV6WorkspaceResponse } from "./intakeV6Api";

export type IntakeV6StepId = "layers" | "review" | "confirm";

export type IntakeV6WorkspacePhase =
	| "idle"
	| "loading"
	| "ready"
	| "analyzing_svg"
	| "svg_ready"
	| "persisting"
	| "error";

export type IntakeV6AnalyzerStatus = "idle" | "analyzing" | "ready" | "error";

export type IntakeV6LoadErrorCode =
	| "INTAKE_REQUEST_NOT_FOUND"
	| "WORKSPACE_NOT_FOUND"
	| "BACKEND_UNAVAILABLE"
	| "UNKNOWN_LOAD_ERROR";

export interface IntakeV6SvgFileMeta {
	fileName: string;
	fileSizeBytes: number;
	previewSource: string | null;
}

export interface IntakeV6LayerChip {
	layerKey: string;
	displayName: string;
	status: "pending" | "confirmed" | "ignored";
}

export interface IntakeV6WorkspaceState {
	workspaceId: string | null;
	phase: IntakeV6WorkspacePhase;
	error: string | null;
	loadErrorCode: IntakeV6LoadErrorCode | null;
	currentStep: IntakeV6StepId;
	workspace: IntakeV6WorkspaceResponse | null;
	svg: IntakeV6SvgFileMeta | null;
	layerChips: IntakeV6LayerChip[];
	analysisRunId: number;
	analyzerStatus: IntakeV6AnalyzerStatus;
	analyzerError: string | null;
	svgSource: string | null;
	analyzerReport: SvgAnalysisReport | null;
	layerRoleConfirmation: LayerRoleConfirmation | null;
	localFileHash: string | null;
	unsavedAnalysis: boolean;
}

export type IntakeV6WorkspaceAction =
	| { type: "LOAD_START"; workspaceId?: string | null }
	| { type: "LOAD_SUCCESS"; workspace: IntakeV6WorkspaceResponse }
	| { type: "LOAD_ERROR"; message: string; code: IntakeV6LoadErrorCode }
	| { type: "SET_STEP"; step: IntakeV6StepId }
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
			layerChips: IntakeV6LayerChip[];
			parseWarning?: string | null;
		}
	| { type: "ANALYZER_ERROR"; runId: number; message: string }
	| {
			type: "LAYER_ROLE_CONFIRMATION_UPDATE";
			layerRoleConfirmation: LayerRoleConfirmation;
			layerChips: IntakeV6LayerChip[];
		}
	| { type: "PERSIST_START" }
	| { type: "PERSIST_SUCCESS"; workspace: IntakeV6WorkspaceResponse }
	| { type: "FINISH_SETUP_PERSIST_SUCCESS"; workspace: IntakeV6WorkspaceResponse }
	| { type: "PERSIST_ERROR"; message: string };

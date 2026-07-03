import { persistIntakeV6AnalysisBundle, getIntakeV6Workspace, createIntakeV6Workspace, ensureIntakeV6WorkspaceForIntakeRequest } from "./intakeV6Api";
import type { IntakeV6SvgUploadResponse, IntakeV6WorkspaceResponse } from "./intakeV6Api";

export async function fetchIntakeV6Workspace(
  workspaceId: string,
): Promise<IntakeV6WorkspaceResponse> {
  return getIntakeV6Workspace(workspaceId);
}

export async function bootstrapIntakeV6Workspace(
  title = "Operator workspace V6",
): Promise<IntakeV6WorkspaceResponse> {
  return createIntakeV6Workspace({
    title,
    template_code: "TPL-VOLUMETRIC-LETTERS_v2",
  });
}

export async function resolveIntakeV6Workspace(
  workspaceKey: string,
): Promise<IntakeV6WorkspaceResponse> {
  return ensureIntakeV6WorkspaceForIntakeRequest(workspaceKey);
}

export { persistIntakeV6AnalysisBundle };

export type { IntakeV6WorkspaceResponse, IntakeV6SvgUploadResponse };


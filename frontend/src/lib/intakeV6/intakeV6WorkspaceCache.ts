import type { IntakeV6WorkspaceResponse } from "./intakeV6Api";

/** Survives React remount — avoids loading flash on every page entry. */
const workspaceById = new Map<string, IntakeV6WorkspaceResponse>();

export function getCachedIntakeV6Workspace(workspaceId: string): IntakeV6WorkspaceResponse | undefined {
  return workspaceById.get(workspaceId);
}

export function cacheIntakeV6Workspace(workspace: IntakeV6WorkspaceResponse): void {
  workspaceById.set(workspace.id, workspace);
  const intakeRequestCode = workspace.payload?.intake_request_code;
  if (typeof intakeRequestCode === "string" && intakeRequestCode.trim()) {
    workspaceById.set(intakeRequestCode.trim(), workspace);
  }
}

export function clearCachedIntakeV6Workspace(workspaceId: string): void {
  workspaceById.delete(workspaceId);
}


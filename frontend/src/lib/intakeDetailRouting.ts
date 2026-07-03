/**
 * Explicit intake detail workspace routing — which UI shell renders for a record.
 */

import { isUnresolvedIntakeProductFamily } from "@/lib/intakeProductFamilyDisplay";
import { shouldUseVolumetricIntakePage } from "@/lib/volumetricIntakeRoute";
import type { IntakeRequest } from "@/lib/mockData";

export type IntakeWorkspaceShell =
  | "volumetric_modular"
  | "generic_unresolved"
  | "generic_legacy";

export const INTAKE_WORKSPACE_SHELL_LABELS: Record<IntakeWorkspaceShell, string> = {
  volumetric_modular: "volumetric modular",
  generic_unresolved: "generic unresolved",
  generic_legacy: "generic legacy",
};

export function resolveIntakeWorkspaceShell(
  confirmedTemplateCode: string | null | undefined,
  productFamily: string | null | undefined
): IntakeWorkspaceShell {
  if (isUnresolvedIntakeProductFamily(productFamily)) {
    return "generic_unresolved";
  }
  if (shouldUseVolumetricIntakePage(confirmedTemplateCode, productFamily)) {
    return "volumetric_modular";
  }
  return "generic_legacy";
}

export function shouldShowIntakeWorkspaceDiagnostic(): boolean {
  return import.meta.env.DEV;
}

export function intakeWorkspaceDiagnosticLabel(shell: IntakeWorkspaceShell): string {
  return `Workspace: ${INTAKE_WORKSPACE_SHELL_LABELS[shell]}`;
}

/** Minimal fields required to render generic IntakeDetail without crashing. */
export function getIntakeDetailRenderIssues(request: IntakeRequest): string[] {
  const issues: string[] = [];
  if (!(request.id ?? "").trim()) issues.push("missing id");
  if (!(request.status ?? "").trim()) issues.push("missing status");
  if (request.client == null) issues.push("missing client");
  return issues;
}

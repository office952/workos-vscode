/**
 * Routing helpers for templates handled by the dedicated Intake V6 shell.
 */

import { isLitereVolumetriceFamily } from "@/lib/intakeProductSpec";
import type { IntakeStatus } from "@/lib/mockData";
import { isVolumetricLettersTemplateCode } from "@/lib/volumetricQuoteInput";

export const TPL_VOLUMETRIC_LOGO_V1 = "TPL-VOLUMETRIC-LOGO_v1";

export function isIntakeV6CapableTemplateCode(
  templateCode: string | null | undefined
): boolean {
  return isVolumetricLettersTemplateCode(templateCode);
}

export function shouldUseVolumetricIntakePage(
  confirmedTemplateCode: string | null | undefined,
  productFamily: string | null | undefined
): boolean {
  const code = (confirmedTemplateCode ?? "").trim();
  if (isIntakeV6CapableTemplateCode(confirmedTemplateCode)) return true;
  if (!code && isLitereVolumetriceFamily(productFamily)) return true;
  return false;
}

/** Primary operator edit path uses intake code (e.g. IR-…) on the active Intake V6 route. */
export function buildIntakeV6Path(workspaceId?: string | null): string {
  const trimmedWorkspaceId = workspaceId?.trim();
  if (trimmedWorkspaceId) {
    return `/intake-v6/${encodeURIComponent(trimmedWorkspaceId)}/operator`;
  }
  return "/intake-v6/operator";
}

/** Work Intake / legacy intake codes routed into Intake V6 (IR-*, WI-*). */
export function isIntakeRequestRouteKey(routeKey: string | null | undefined): boolean {
  const trimmed = routeKey?.trim();
  if (!trimmed) return false;
  return /^(IR|WI)-[A-Z0-9]+$/i.test(trimmed);
}

export function buildIntakeLegacyPath(intakeCode: string): string {
  return `/intake/${encodeURIComponent(intakeCode.trim())}`;
}

export function intakeEditUsesVolumetricWorkspace(
  confirmedTemplateCode: string | null | undefined,
  productFamily: string | null | undefined
): boolean {
  return shouldUseVolumetricIntakePage(confirmedTemplateCode, productFamily);
}

export function findIntakeByRouteParam<T extends { id: string; dbId?: number | null }>(
  intakes: T[],
  routeParam: string | undefined
): T | undefined {
  if (!routeParam?.trim()) return undefined;
  const key = decodeURIComponent(routeParam.trim());
  return intakes.find(
    (r) => r.id === key || (r.dbId != null && String(r.dbId) === key)
  );
}

export function resolveIntakeEditPath(input: {
  id: string;
  confirmedTemplateCode?: string | null;
  productFamily?: string | null;
  workspaceId?: string | null;
}): string {
  const confirmedTemplateCode = input.confirmedTemplateCode?.trim() ?? "";
  if (
    intakeEditUsesVolumetricWorkspace(
      confirmedTemplateCode,
      input.productFamily ?? null
    )
  ) {
    return buildIntakeV6Path(input.workspaceId ?? input.id);
  }
  if (input.workspaceId?.trim() && !confirmedTemplateCode) {
    return buildIntakeV6Path(input.workspaceId);
  }
  return buildIntakeLegacyPath(input.id);
}

export function intakePrimaryEditLabel(
  confirmedTemplateCode: string | null | undefined,
  productFamily: string | null | undefined
): string {
  return intakeEditUsesVolumetricWorkspace(confirmedTemplateCode, productFamily)
    ? "Deschide Intake V6"
    : "Instrumentează Comanda";
}

/** Stored status is ahead of what computed readiness / template / spec allow. */
export function hasIntakeStatusReadinessConflict(
  status: IntakeStatus,
  readinessMissing: string[],
  templateOk: boolean,
  productSpecOk: boolean
): boolean {
  if (status !== "ready_for_quote") return false;
  return !templateOk || !productSpecOk || readinessMissing.length > 0;
}

/**
 * Helpers for persisting intake_requests fields via CRUD API.
 */

import { intakesApi, type IntakeRequestEntity } from "@/lib/api";
import type { IntakeSiteAuditJson } from "@/lib/intakeSiteAudit";

export async function resolveIntakeDbId(code: string): Promise<number | null> {
  const rows = await intakesApi.list({ code }, { limit: 1 });
  return rows[0]?.id ?? null;
}

export async function patchIntake(
  dbId: number,
  data: Partial<IntakeRequestEntity>
): Promise<IntakeRequestEntity> {
  return intakesApi.update(dbId, data);
}

export async function patchIntakeByCode(
  code: string,
  data: Partial<IntakeRequestEntity>
): Promise<IntakeRequestEntity | null> {
  const dbId = await resolveIntakeDbId(code);
  if (!dbId) return null;
  return patchIntake(dbId, data);
}

export type IntakeStatusTransition = IntakeRequestEntity["status"];

export async function transitionIntakeStatus(
  dbId: number,
  fromStatus: IntakeStatusTransition,
  toStatus: IntakeStatusTransition
): Promise<IntakeRequestEntity> {
  return patchIntake(dbId, { status: toStatus });
}

/** Chain new → in_review → ready_for_quote when operator marks ready from new. */
export async function markIntakeReadyForQuote(
  dbId: number,
  currentStatus: IntakeStatusTransition
): Promise<IntakeRequestEntity> {
  if (currentStatus === "ready_for_quote") {
    return patchIntake(dbId, { status: "ready_for_quote" });
  }
  if (currentStatus === "new") {
    await transitionIntakeStatus(dbId, "new", "in_review");
    return transitionIntakeStatus(dbId, "in_review", "ready_for_quote");
  }
  if (currentStatus === "in_review") {
    return transitionIntakeStatus(dbId, "in_review", "ready_for_quote");
  }
  if (currentStatus === "needs_info") {
    await transitionIntakeStatus(dbId, "needs_info", "in_review");
    return transitionIntakeStatus(dbId, "in_review", "ready_for_quote");
  }
  throw new Error(`Cannot mark ready from status ${currentStatus}`);
}

export async function persistConfirmedTemplate(
  dbId: number,
  templateCode: string,
  templateName?: string
): Promise<IntakeRequestEntity> {
  return patchIntake(dbId, {
    confirmed_template_code: templateCode,
    confirmed_template_name: templateName ?? templateCode,
  });
}

export async function persistSiteAudit(
  dbId: number,
  siteAudit: IntakeSiteAuditJson
): Promise<IntakeRequestEntity> {
  return patchIntake(dbId, { site_audit_json: siteAudit });
}

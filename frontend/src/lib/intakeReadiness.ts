/**
 * Work Intake prerequisites for marking ready_for_quote (intake ops gate).
 * Distinct from can_create_commercial_quote (backend quote gate).
 */

import type { IntakeProductSpec } from "@/lib/intakeProductSpec";
import type { IntakeSiteAuditJson } from "@/lib/intakeSiteAudit";
import { parseSiteAuditJson } from "@/lib/intakeSiteAudit";
import { TPL_VOLUMETRIC_LETTERS } from "@/lib/volumetricQuoteInput";
import type { DeliveryType } from "@/lib/mockData";

export interface IntakeReadinessInput {
  description?: string | null;
  dimensions?: string | null;
  assignedTo?: string | null;
  deliveryType?: DeliveryType | string | null;
  confirmedTemplateCode?: string | null;
  productSpec?: IntakeProductSpec | null;
  siteAudit?: IntakeSiteAuditJson | null;
  requiresInstallAudit?: boolean;
}

function hasAssigned(assignee: string | null | undefined): boolean {
  const v = (assignee ?? "").trim();
  return v.length > 0 && v !== "—";
}

function hasStructuredVolumetricEnvelope(spec: IntakeProductSpec | null | undefined): boolean {
  if (!spec) return false;
  const width = spec.width_mm;
  const height = spec.height_mm ?? spec.letter_height_mm;
  const depth = spec.depth_mm ?? spec.return_depth_mm;
  return (
    width != null &&
    width > 0 &&
    height != null &&
    height > 0 &&
    depth != null &&
    depth > 0
  );
}

function installAuditComplete(siteAudit: IntakeSiteAuditJson): boolean {
  const audit = parseSiteAuditJson(siteAudit);
  return (
    audit.checks.address_confirmed &&
    audit.checks.photos_verified &&
    audit.checks.power_confirmed
  );
}

export function evaluateIntakeReadyPrerequisites(
  input: IntakeReadinessInput
): { canMarkReady: boolean; missing: string[] } {
  const missing: string[] = [];

  if (!hasAssigned(input.assignedTo)) {
    missing.push("Persoană asignată — lipsă");
  }

  if (!(input.description ?? "").trim()) {
    missing.push("Descriere produs — lipsă");
  }

  if (!(input.deliveryType ?? "").trim()) {
    missing.push("Tip livrare — lipsă");
  }

  if (!(input.confirmedTemplateCode ?? "").trim()) {
    missing.push("Template produs — neconfirmat");
  }

  const template = (input.confirmedTemplateCode ?? "").trim();
  const isVolumetric = template === TPL_VOLUMETRIC_LETTERS;

  if (isVolumetric) {
    if (!input.productSpec || Object.keys(input.productSpec).length === 0) {
      missing.push("Specificație produs — nesalvată");
    }
    if (!hasStructuredVolumetricEnvelope(input.productSpec)) {
      missing.push("Dimensiuni din specificație — width/height/depth lipsă");
    }
  } else if (!(input.dimensions ?? "").trim()) {
    missing.push("Dimensiuni — lipsă");
  }

  if (input.requiresInstallAudit) {
    const audit = parseSiteAuditJson(input.siteAudit);
    if (!installAuditComplete(audit)) {
      missing.push("Audit teren — incomplet");
    }
  }

  return { canMarkReady: missing.length === 0, missing };
}

export function shouldShowVolumetricProductForm(
  confirmedTemplateCode: string | null | undefined,
  productFamily: string | null | undefined,
  isLitereFamily: (family: string | null | undefined) => boolean
): boolean {
  if ((confirmedTemplateCode ?? "").trim() === TPL_VOLUMETRIC_LETTERS) {
    return true;
  }
  if (!confirmedTemplateCode && isLitereFamily(productFamily)) {
    return true;
  }
  return false;
}

/**
 * Field installation (montaj teren) employee eligibility — no salary exposure.
 * Separate from atelier montaj_autocolant / tablet routing.
 */
import type { OperationResourceMapping } from "@/api/operationalRegistry";
import type { OperatorRegistryEmployee } from "@/api/operationalRegistry";

export type FieldEligibilityStatus = "authorized" | "not_authorized" | "unverified";

export const FIELD_SITE_CAPABILITY_SKILLS: Record<string, string[]> = {
  Montator: ["SK_FIELD_INSTALLER"],
  Electrician: ["SK_ELECTRICIAN"],
  Colantator: ["SK_VINYL_APPLICATOR"],
  Ansamblare: ["SK_ASSEMBLY"],
};

const FIELD_WORKCENTER = "WC_FIELD_INSTALLATION";

export function deriveFieldCapabilities(skillCodes: string[]): string[] {
  const caps: string[] = [];
  for (const [label, codes] of Object.entries(FIELD_SITE_CAPABILITY_SKILLS)) {
    if (codes.some((c) => skillCodes.includes(c))) {
      caps.push(label);
    }
  }
  return caps;
}

export function suggestRoleOnSite(skillCodes: string[]): string | null {
  const caps = deriveFieldCapabilities(skillCodes);
  if (caps.includes("Montator")) return "montator";
  if (caps.includes("Electrician")) return "electrician";
  if (caps.includes("Colantator")) return "colantator";
  if (caps.includes("Ansamblare")) return "asamblare";
  return null;
}

export function computeFieldInstallationEligibility(
  employee: Pick<OperatorRegistryEmployee, "skill_codes" | "workcenter_codes">,
  mapping: OperationResourceMapping | null
): FieldEligibilityStatus {
  if (!mapping) return "unverified";

  const required = new Set(mapping.required_skill_codes ?? []);
  const allowedWc = new Set(mapping.allowed_workcenter_codes ?? []);

  if (required.size === 0 && allowedWc.size === 0) {
    return "unverified";
  }

  const skillOk =
    required.size === 0 ||
    (employee.skill_codes ?? []).some((s) => required.has(s)) ||
    deriveFieldCapabilities(employee.skill_codes ?? []).length > 0;
  const wcOk =
    allowedWc.size === 0 ||
    (employee.workcenter_codes ?? []).includes(FIELD_WORKCENTER);

  return skillOk && wcOk ? "authorized" : "not_authorized";
}

export function orderInstallationRef(orderId: number): string {
  return `ORDER-${orderId}`;
}

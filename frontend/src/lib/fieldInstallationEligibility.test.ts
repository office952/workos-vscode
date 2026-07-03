import { describe, expect, it } from "vitest";
import {
  computeFieldInstallationEligibility,
  deriveFieldCapabilities,
  orderInstallationRef,
} from "@/lib/fieldInstallationEligibility";

describe("fieldInstallationEligibility", () => {
  it("derives montaj teren capabilities from skills", () => {
    expect(
      deriveFieldCapabilities(["SK_FIELD_INSTALLER", "SK_ELECTRICIAN", "SK_ASSEMBLY"])
    ).toEqual(["Montator", "Electrician", "Ansamblare"]);
  });

  it("marks authorized when field_installation mapping matches", () => {
    const status = computeFieldInstallationEligibility(
      {
        skill_codes: ["SK_FIELD_INSTALLER"],
        workcenter_codes: ["WC_FIELD_INSTALLATION"],
      },
      {
        operation_code: "field_installation",
        required_skill_codes: ["SK_FIELD_INSTALLER"],
        allowed_workcenter_codes: ["WC_FIELD_INSTALLATION"],
        allowed_resource_codes: [],
        authorization_mode: "hybrid",
        default_resource_code: null,
        product_system_aliases: [],
        authorized_employee_ids: [],
        notes: null,
      }
    );
    expect(status).toBe("authorized");
  });

  it("returns unverified when mapping is missing", () => {
    expect(
      computeFieldInstallationEligibility(
        { skill_codes: ["SK_FIELD_INSTALLER"], workcenter_codes: [] },
        null
      )
    ).toBe("unverified");
  });

  it("handles missing workcenter_codes without throwing", () => {
    expect(
      computeFieldInstallationEligibility(
        { skill_codes: ["SK_FIELD_INSTALLER"], workcenter_codes: undefined as unknown as string[] },
        {
          operation_code: "field_installation",
          required_skill_codes: ["SK_FIELD_INSTALLER"],
          allowed_workcenter_codes: ["WC_FIELD_INSTALLATION"],
          allowed_resource_codes: [],
          authorization_mode: "hybrid",
          default_resource_code: null,
          product_system_aliases: [],
          authorized_employee_ids: [],
          notes: null,
        }
      )
    ).toBe("not_authorized");
  });

  it("uses ORDER-{id} ref separate from atelier colantare", () => {
    expect(orderInstallationRef(42)).toBe("ORDER-42");
  });
});

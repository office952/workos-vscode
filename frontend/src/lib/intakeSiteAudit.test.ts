import { describe, expect, it } from "vitest";
import {
  auditUiToSiteAudit,
  countSiteAuditChecks,
  EMPTY_SITE_AUDIT,
  parseSiteAuditJson,
  siteAuditToTerrainChecks,
} from "./intakeSiteAudit";

describe("intakeSiteAudit", () => {
  it("round-trips audit UI to site_audit_json", () => {
    const json = auditUiToSiteAudit({
      address: "Str. Test 1",
      addressSelected: true,
      mapsOpened: true,
      addressConfirmed: true,
      photosStatus: "received",
      photoLink: "",
      techPowerSource: "220V",
      surfaceType: "",
      foundationResponsibility: "",
      foundationClientConfirmed: false,
      existingFoundationDims: "",
      heavyEquipmentAccess: "",
    });
    expect(json.mounting_address).toBe("Str. Test 1");
    expect(json.checks.photos_verified).toBe(true);
    expect(json.checks.power_confirmed).toBe(true);
  });

  it("maps site audit to quote terrain checks read-only", () => {
    const checks = siteAuditToTerrainChecks({
      mounting_address: "A",
      location_photos_status: "received",
      power_available: "yes",
      mounting_access: "ok",
      cable_route: "unknown",
      notes: "",
      checks: {
        address_confirmed: true,
        photos_verified: true,
        power_confirmed: true,
        access_confirmed: false,
      },
    });
    expect(checks.locationVerified).toBe(true);
    expect(checks.photosVerified).toBe(true);
    expect(checks.powerVerified).toBe(true);
  });

  it("counts terrain checks", () => {
    const { completed, total } = countSiteAuditChecks(
      parseSiteAuditJson({
        ...EMPTY_SITE_AUDIT,
        checks: { address_confirmed: true, photos_verified: false, power_confirmed: true, access_confirmed: false },
      })
    );
    expect(completed).toBe(2);
    expect(total).toBe(3);
  });
});

import { describe, expect, it } from "vitest";
import {
  filterReadinessMissingForDisplay,
  getDeliveryLabel,
  getDeliveryStageNote,
  hasPersistedSiteAuditData,
  INTAKE_DELIVERY_OPTIONS,
  isDeliveryCourier,
  isDeliveryNoInstall,
  isDeliveryPickup,
  isDeliveryUnset,
  isDeliveryWithInstall,
  normalizeDeliveryType,
  requiresTerrainAudit,
  TERRAIN_DATA_PRESERVED_NOTE,
} from "./intakeDeliverySemantics";
import { EMPTY_SITE_AUDIT } from "@/lib/intakeSiteAudit";

describe("intakeDeliverySemantics", () => {
  it("normalizes canonical delivery values", () => {
    expect(normalizeDeliveryType("courier")).toBe("courier");
    expect(normalizeDeliveryType("delivery_install")).toBe("delivery_install");
    expect(normalizeDeliveryType("")).toBeNull();
    expect(normalizeDeliveryType("invalid")).toBeNull();
  });

  it("classifies install delivery correctly", () => {
    expect(isDeliveryWithInstall("delivery_install")).toBe(true);
    expect(isDeliveryWithInstall("courier")).toBe(false);
    expect(isDeliveryWithInstall("pickup")).toBe(false);
  });

  it("classifies courier and pickup as no terrain", () => {
    expect(isDeliveryCourier("courier")).toBe(true);
    expect(isDeliveryPickup("pickup")).toBe(true);
    expect(isDeliveryNoInstall("delivery_standard")).toBe(true);
    expect(
      requiresTerrainAudit({
        deliveryType: "courier",
        productFamily: "litere_volumetrice",
      })
    ).toBe(false);
  });

  it("treats empty delivery as unset", () => {
    expect(isDeliveryUnset("")).toBe(true);
    expect(getDeliveryLabel("")).toBe("Livrare nealeasă");
  });

  it("requires terrain only for install with known work type", () => {
    expect(
      requiresTerrainAudit({
        deliveryType: "delivery_install",
        productFamily: "litere_volumetrice",
      })
    ).toBe(true);
    expect(
      requiresTerrainAudit({
        deliveryType: "delivery_install",
        productFamily: "",
      })
    ).toBe(false);
  });

  it("shows stage 0 neutral note for unresolved install delivery", () => {
    expect(
      getDeliveryStageNote({
        deliveryType: "delivery_install",
        productFamily: "",
      })
    ).toContain("Montajul va fi verificat");
  });

  it("shows preserved terrain note when delivery is non-install with site data", () => {
    expect(
      getDeliveryStageNote({
        deliveryType: "courier",
        productFamily: "litere_volumetrice",
        siteAudit: {
          ...EMPTY_SITE_AUDIT,
          checks: {
            ...EMPTY_SITE_AUDIT.checks,
            address_confirmed: true,
            photos_verified: false,
            power_confirmed: false,
            access_confirmed: false,
          },
        },
      })
    ).toBe(TERRAIN_DATA_PRESERVED_NOTE);
    expect(
      hasPersistedSiteAuditData({
        ...EMPTY_SITE_AUDIT,
        checks: {
          ...EMPTY_SITE_AUDIT.checks,
          address_confirmed: true,
          photos_verified: false,
          power_confirmed: false,
          access_confirmed: false,
        },
      })
    ).toBe(true);
  });

  it("filters terrain blockers from readiness display when install inactive", () => {
    expect(
      filterReadinessMissingForDisplay(
        ["Template produs — neconfirmat", "Audit teren — incomplet"],
        false
      )
    ).toEqual(["Template produs — neconfirmat"]);
    expect(
      filterReadinessMissingForDisplay(
        ["Audit teren — incomplet"],
        true
      )
    ).toEqual(["Audit teren — incomplet"]);
  });

  it("exposes Quick Start delivery options with canonical values", () => {
    expect(INTAKE_DELIVERY_OPTIONS.map((o) => o.value)).toEqual([
      "pickup",
      "delivery_standard",
      "delivery_express",
      "delivery_install",
      "courier",
    ]);
  });
});

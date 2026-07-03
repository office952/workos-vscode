import { describe, it, expect } from "vitest";
import {
  buildSheetQualityUrl,
  buildSheetQualityMaterialUrl,
  buildSheetQualityInvalidSummaryUrl,
  buildSheetQualityAuditTrailUrl,
} from "./inventorySheetQualityLinks";

describe("inventorySheetQualityLinks contract", () => {
  it("always includes tab=sheet-quality", () => {
    const url = buildSheetQualityUrl({});
    const params = new URLSearchParams(url.split("?")[1]);
    expect(params.get("tab")).toBe("sheet-quality");
  });

  it("includes sq_material_id in material url", () => {
    const url = buildSheetQualityMaterialUrl("MAT 123");
    const params = new URLSearchParams(url.split("?")[1]);
    expect(params.get("sq_material_id")).toBe("MAT 123");
  });

  it("includes sq_selected_issue_code when provided", () => {
    const url = buildSheetQualityMaterialUrl("MAT 1", "invalid_dimensions");
    const params = new URLSearchParams(url.split("?")[1]);
    expect(params.get("sq_selected_issue_code")).toBe("invalid_dimensions");
  });

  it("invalid summary sets sq_status=invalid", () => {
    const url = buildSheetQualityInvalidSummaryUrl();
    const params = new URLSearchParams(url.split("?")[1]);
    expect(params.get("sq_status")).toBe("invalid");
  });

  it("invalid summary can include sq_issue_code", () => {
    const url = buildSheetQualityInvalidSummaryUrl("partial_payload");
    const params = new URLSearchParams(url.split("?")[1]);
    expect(params.get("sq_issue_code")).toBe("partial_payload");
  });

  it("audit trail sets trail_material_id and trail_offset=0", () => {
    const url = buildSheetQualityAuditTrailUrl("MAT 2");
    const params = new URLSearchParams(url.split("?")[1]);
    expect(params.get("trail_material_id")).toBe("MAT 2");
    expect(params.get("trail_offset")).toBe("0");
  });

  it("forbidden keys are stripped", () => {
    const url = buildSheetQualityUrl({
      sq_material_id: "MAT 3",
      reason: "should not appear",
      confirm: true,
      proposed_values: "should not appear",
      proposedValues: "should not appear",
      confirmed: true,
      token: "should not appear",
      secret: "should not appear",
      password: "should not appear",
      credential: "should not appear",
      api_key: "should not appear",
      apiKey: "should not appear",
      authorization: "should not appear",
    } as any);
    const params = new URLSearchParams(url.split("?")[1]);
    [
      "reason",
      "confirm",
      "proposed_values",
      "proposedValues",
      "confirmed",
      "token",
      "secret",
      "password",
      "credential",
      "api_key",
      "apiKey",
      "authorization",
    ].forEach((k) => {
      expect(params.has(k)).toBe(false);
    });
    expect(params.get("sq_material_id")).toBe("MAT 3");
  });

  it("null/undefined/empty values are stripped", () => {
    const url = buildSheetQualityUrl({
      sq_material_id: "",
      sq_status: undefined,
      sq_issue_code: null,
      trail_limit: 25,
    } as any);
    const params = new URLSearchParams(url.split("?")[1]);
    expect(params.has("sq_material_id")).toBe(false);
    expect(params.has("sq_status")).toBe(false);
    expect(params.has("sq_issue_code")).toBe(false);
    expect(params.get("trail_limit")).toBe("25");
  });

  it("special characters are URL encoded and recoverable", () => {
    const url = buildSheetQualityUrl({
      sq_material_id: "MAT 1/2@#",
      trail_changed_by: "user@domain.com",
    });
    const params = new URLSearchParams(url.split("?")[1]);
    expect(params.get("sq_material_id")).toBe("MAT 1/2@#");
    expect(params.get("trail_changed_by")).toBe("user@domain.com");
  });

  it("ISO date strings with timezone are preserved", () => {
    const date = "2026-05-15T12:00:00+03:00";
    const url = buildSheetQualityUrl({ trail_date_from: date });
    const params = new URLSearchParams(url.split("?")[1]);
    expect(params.get("trail_date_from")).toBe(date);
  });

  it("helper does not include proposed remediation payload or confirm-like flags", () => {
    const url = buildSheetQualityUrl({
      proposed_values: "should not appear",
      proposedValues: "should not appear",
      confirm: true,
      confirmed: true,
      token: "should not appear",
      secret: "should not appear",
      password: "should not appear",
      credential: "should not appear",
      api_key: "should not appear",
      apiKey: "should not appear",
      authorization: "should not appear",
    } as any);
    const params = new URLSearchParams(url.split("?")[1]);
    [
      "proposed_values",
      "proposedValues",
      "confirm",
      "confirmed",
      "token",
      "secret",
      "password",
      "credential",
      "api_key",
      "apiKey",
      "authorization",
    ].forEach((k) => {
      expect(params.has(k)).toBe(false);
    });
  });
});

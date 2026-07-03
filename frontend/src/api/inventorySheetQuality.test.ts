import { describe, expect, it } from "vitest";
import {
  buildInventorySheetQualityAuditExportUrl,
  buildInventorySheetRemediationAuditTrailExportUrl,
} from "./inventorySheetQuality";

/** Export builders return app-relative API paths; parse with a base in happy-dom. */
const parseRelativeUrl = (url: string) => new URL(url, "http://localhost");

describe("inventorySheetQuality export URL builders", () => {
  it("quality export URL includes format and current filters", () => {
    const url = buildInventorySheetQualityAuditExportUrl({
      format: "csv",
      status: "invalid",
      issue_code: "partial_payload",
      would_block_intake_assist: true,
      limit: 1000,
      offset: 0,
    });

    const parsed = parseRelativeUrl(url);
    expect(parsed.pathname.endsWith("/api/v1/admin/inventory/sheet-quality-audit/export")).toBe(true);
    expect(parsed.searchParams.get("format")).toBe("csv");
    expect(parsed.searchParams.get("status")).toBe("invalid");
    expect(parsed.searchParams.get("issue_code")).toBe("partial_payload");
    expect(parsed.searchParams.get("would_block_intake_assist")).toBe("true");
    expect(parsed.searchParams.get("limit")).toBe("1000");
    expect(parsed.searchParams.get("offset")).toBe("0");
  });

  it("trail export URL includes format and current filters", () => {
    const date = "2026-05-15T12:00:00+03:00";
    const url = buildInventorySheetRemediationAuditTrailExportUrl({
      format: "json",
      material_id: "MAT-001",
      issue_code: "invalid_dimensions",
      changed_by: "admin@example.com",
      date_from: date,
      date_to: date,
      operation_status: "applied",
      limit: 25,
      offset: 50,
    });

    const parsed = parseRelativeUrl(url);
    expect(parsed.pathname.endsWith("/api/v1/admin/inventory/sheet-remediation-audit-trail/export")).toBe(true);
    expect(parsed.searchParams.get("format")).toBe("json");
    expect(parsed.searchParams.get("material_id")).toBe("MAT-001");
    expect(parsed.searchParams.get("issue_code")).toBe("invalid_dimensions");
    expect(parsed.searchParams.get("changed_by")).toBe("admin@example.com");
    expect(parsed.searchParams.get("date_from")).toBe(date);
    expect(parsed.searchParams.get("date_to")).toBe(date);
    expect(parsed.searchParams.get("operation_status")).toBe("applied");
    expect(parsed.searchParams.get("limit")).toBe("25");
    expect(parsed.searchParams.get("offset")).toBe("50");
  });

  it("export URL builders exclude forbidden action/secrets keys", () => {
    const qualityUrl = buildInventorySheetQualityAuditExportUrl({
      format: "csv",
      status: "all",
      issue_code: "missing_configuration",
      reason: "must be blocked",
      proposed_values: "must be blocked",
      confirm: true,
      token: "must be blocked",
      secret: "must be blocked",
      password: "must be blocked",
      api_key: "must be blocked",
      authorization: "must be blocked",
    } as any);

    const trailUrl = buildInventorySheetRemediationAuditTrailExportUrl({
      format: "json",
      material_id: "MAT-002",
      reason: "must be blocked",
      proposedValues: "must be blocked",
      confirmed: true,
      credential: "must be blocked",
      apiKey: "must be blocked",
    } as any);

    const qualityParams = parseRelativeUrl(qualityUrl).searchParams;
    const trailParams = parseRelativeUrl(trailUrl).searchParams;

    [
      "reason",
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
    ].forEach((key) => {
      expect(qualityParams.has(key)).toBe(false);
      expect(trailParams.has(key)).toBe(false);
    });
  });
});

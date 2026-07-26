import { describe, expect, it } from "vitest";
import { activeProductionGeometryAttachments } from "./productionGeometryApi";
import { formatAcmPanelPathSource } from "./acmPanelCommercialPreviewDisplay";

describe("productionGeometryApi helpers", () => {
  it("filters replaced/archived attachments", () => {
    const active = activeProductionGeometryAttachments({
      production_geometry: {
        attachments: [
          { attachment_id: "a", measurement_status: "measured" },
          { attachment_id: "b", measurement_status: "replaced" },
          { attachment_id: "c", measurement_status: "archived" },
          { attachment_id: "d", measurement_status: "stale" },
        ],
      },
    });
    expect(active.map((a) => a.attachment_id)).toEqual(["a", "d"]);
  });

  it("formats stale path source", () => {
    expect(formatAcmPanelPathSource("stale", "stale")).toContain("stale");
  });
});

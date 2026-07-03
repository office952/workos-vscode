import { describe, expect, it } from "vitest";
import { getRoutingForOperation, VOLUMETRIC_PROCESS_ID_ROUTING } from "@/lib/workstationRouting";

describe("workstationRouting canonical compatibility", () => {
  it("routes canonical cnc_routing to CNC station", () => {
    expect(getRoutingForOperation("cnc_routing")?.workstationId).toBe("cnc");
  });

  it("routes canonical led_assembly to LED station", () => {
    expect(getRoutingForOperation("led_assembly")?.workstationId).toBe("led_electric");
  });

  it("routes canonical vinyl_cutting to montaj autocolant", () => {
    expect(getRoutingForOperation("vinyl_cutting")?.workstationId).toBe("montaj_autocolant");
  });

  it("maps volumetric process_id via compatibility table", () => {
    expect(getRoutingForOperation("unknown", "face_cnc_cut")?.workstationId).toBe("cnc");
    expect(VOLUMETRIC_PROCESS_ID_ROUTING.qc_letters).toBe("quality_control");
  });

  it("preserves legacy cnc_cutting routing", () => {
    expect(getRoutingForOperation("cnc_cutting")?.workstationId).toBe("cnc");
  });
});

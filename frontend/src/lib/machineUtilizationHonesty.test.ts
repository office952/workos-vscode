import { describe, expect, it } from "vitest";
import { presentMachineUtilization } from "./machineUtilizationHonesty";
import type { Machine } from "./mockData";

function base(partial: Partial<Machine>): Machine {
  return {
    id: "m1",
    name: "CNC",
    type: "cnc",
    workcenterId: "wc",
    status: "running",
    currentJobId: null,
    currentOperationCode: null,
    currentOperator: null,
    runtimeMinutes: 0,
    utilizationPct: 70,
    queueCount: 0,
    nextJobId: null,
    ...partial,
  };
}

describe("presentMachineUtilization", () => {
  it("labels registry placeholder as GAP and hides fake percent", () => {
    const p = presentMachineUtilization(
      base({ utilizationPct: 0, utilizationKind: "placeholder", currentJobId: null }),
    );
    expect(p.kindLabel).toBe("GAP");
    expect(p.displayPct).toBe("—");
    expect(p.showBar).toBe(false);
  });

  it("does not treat 70% without job as actual util", () => {
    const p = presentMachineUtilization(base({ utilizationPct: 70, currentJobId: null }));
    expect(p.kindLabel).toBe("GAP");
    expect(p.displayPct).toBe("—");
  });

  it("keeps proxy percent when job is present", () => {
    const p = presentMachineUtilization(
      base({ utilizationPct: 82, currentJobId: "JOB-1", utilizationKind: "proxy" }),
    );
    expect(p.kindLabel).toBe("PROXY");
    expect(p.displayPct).toBe("82%");
  });
});

import { describe, expect, it } from "vitest";
import type { ResourceReadinessStatus } from "@/api/execution";
import {
  resourceReadinessStatusLabel,
  resourceReadinessStatusTone,
  resourceRequirementModeLabel,
  workcenterRegistryStatusLabel,
} from "./resourceReadinessDisplay";

const ALL_STATUSES: ResourceReadinessStatus[] = [
  "ready",
  "ready_with_warnings",
  "missing_workcenter",
  "unknown_resource_policy",
  "machine_required_but_none_compatible",
  "machine_optional_no_candidate",
  "workcenter_only",
  "machine_unavailable",
  "maintenance_conflict",
  "ambiguous_mapping",
];

describe("resource readiness display mapping", () => {
  it("gives every backend status a Romanian label and a tone, never invents 'ready'", () => {
    for (const status of ALL_STATUSES) {
      expect(resourceReadinessStatusLabel(status)).not.toEqual(status);
      expect(["success", "warning", "danger", "neutral"]).toContain(
        resourceReadinessStatusTone(status),
      );
    }
  });

  it("only tones 'ready' as success — warnings and blocked states are never green", () => {
    expect(resourceReadinessStatusTone("ready")).toBe("success");
    expect(resourceReadinessStatusTone("ready_with_warnings")).toBe("warning");
    expect(resourceReadinessStatusTone("workcenter_only")).toBe("warning");
    expect(resourceReadinessStatusTone("missing_workcenter")).toBe("danger");
    expect(resourceReadinessStatusTone("unknown_resource_policy")).toBe("danger");
    expect(resourceReadinessStatusTone("machine_required_but_none_compatible")).toBe("danger");
    expect(resourceReadinessStatusTone("machine_unavailable")).toBe("danger");
    expect(resourceReadinessStatusTone("ambiguous_mapping")).toBe("danger");
  });

  it("maps resource_requirement_mode and workcenter_registry_status to Romanian, falling back to raw code", () => {
    expect(resourceRequirementModeLabel("orr_allowlist")).toBe("Listă utilaje admise (ORR)");
    expect(resourceRequirementModeLabel("workcenter_only")).toBe("Doar punct de lucru");
    expect(resourceRequirementModeLabel("some_future_mode")).toBe("some_future_mode");

    expect(workcenterRegistryStatusLabel("resolved")).toBe("Cod canonic");
    expect(workcenterRegistryStatusLabel("non_canonical")).toBe("Cod necanonic");
    expect(workcenterRegistryStatusLabel("missing")).toBe("Cod necunoscut");
    expect(workcenterRegistryStatusLabel("empty")).toBe("Lipsă");
  });
});

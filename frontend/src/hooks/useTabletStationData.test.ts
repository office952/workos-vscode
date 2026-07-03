import { describe, expect, it, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useTabletStationData } from "@/hooks/useTabletStationData";

vi.mock("@/hooks/useOperatorData", () => ({
  useOperatorData: vi.fn(),
}));

vi.mock("@/hooks/useOperatorEmployees", () => ({
  useOperatorEmployees: vi.fn(() => ({
    employees: [],
    loading: false,
    error: null,
    source: "db",
    getMappingForTask: () => null,
    refresh: vi.fn(),
  })),
}));

vi.mock("@/api/operationalRegistry", () => ({
  operationalRegistryApi: {
    listOperationMappings: vi.fn().mockResolvedValue({ items: [], total: 0 }),
  },
}));

import { useOperatorData } from "@/hooks/useOperatorData";

describe("useTabletStationData", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("uses live tasks when operator API returns db source", async () => {
    vi.mocked(useOperatorData).mockReturnValue({
      tasks: [
        {
          id: "T-1",
          jobId: "JOB-0001",
          client: "A",
          product: "B",
          operationCode: "print",
          operationName: "Print",
          machineName: "Epson",
          status: "assigned",
          assignee: "—",
          plannedDurationMin: 10,
          actualDurationMin: null,
          startedAt: null,
          targetEndAt: null,
          instructions: "",
          inputDependencies: [],
          expectedOutput: "",
          sequenceIndex: 1,
        },
      ],
      loading: false,
      error: null,
      source: "db",
      refresh: vi.fn(),
      performAction: vi.fn(),
    });

    const { result } = renderHook(() => useTabletStationData("print"));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.isLive).toBe(true);
    expect(result.current.source).toBe("live");
    expect(result.current.tasks).toHaveLength(1);
    expect(result.current.tasks[0].isLive).toBe(true);
  });

  it("treats empty operator API as live with no demo tasks", async () => {
    vi.mocked(useOperatorData).mockReturnValue({
      tasks: [],
      loading: false,
      error: null,
      source: "empty",
      refresh: vi.fn(),
      performAction: vi.fn(),
    });

    const { result } = renderHook(() => useTabletStationData("asamblare_lipire"));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.isLive).toBe(true);
    expect(result.current.source).toBe("empty");
    expect(result.current.tasks).toHaveLength(0);
    expect(result.current.tasks.every((t) => !t.isDemo)).toBe(true);
  });

  it("falls back to demo tasks when operator source is mock", async () => {
    vi.mocked(useOperatorData).mockReturnValue({
      tasks: [],
      loading: false,
      error: null,
      source: "mock",
      refresh: vi.fn(),
      performAction: vi.fn(),
    });

    const { result } = renderHook(() => useTabletStationData("print"));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.isLive).toBe(false);
    expect(result.current.source).toBe("demo");
    expect(result.current.tasks.every((t) => t.isDemo)).toBe(true);
  });
});

import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useOperatorData } from "@/hooks/useOperatorData";

describe("useOperatorData live empty response", () => {
  beforeEach(() => {
    vi.stubEnv("VITE_ENABLE_MOCK_DATA", "true");
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it("does not substitute mock tasks when API returns empty task list", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ tasks: [] }),
      })
    );

    const { result } = renderHook(() => useOperatorData());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.source).toBe("empty");
    expect(result.current.tasks).toHaveLength(0);
  });
});

import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useModuleChainData } from "@/hooks/useModuleChainData";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("useModuleChainData honesty baseline", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("does not mark modules active/green when health checks are empty", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({
        status: "ok",
        generated_at: "2026-07-16T10:00:00.000Z",
        checks: {},
      })
    );

    const { result } = renderHook(() => useModuleChainData(60_000));
    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.isLive).toBe(true);
    expect(result.current.modules.every((m) => m.status === "idle")).toBe(true);
    expect(result.current.modules.every((m) => m.statusCounts.ok === 0)).toBe(true);
  });

  it("exposes unavailable state when health fetch fails", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("network down"));

    const { result } = renderHook(() => useModuleChainData(60_000));
    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.isLive).toBe(false);
    expect(result.current.error).toBeTruthy();
    expect(result.current.modules.every((m) => m.status === "idle")).toBe(true);
  });
});

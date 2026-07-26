import { describe, expect, it, vi } from "vitest";
import { probeProductSystemAuthoringStack } from "./ProductSystemAuthoringStackBanner";

describe("probeProductSystemAuthoringStack", () => {
  it("reports ok when publication and readiness both return 200", async () => {
    const fetchFn = vi.fn(async () => new Response("{}", { status: 200 }));
    const probe = await probeProductSystemAuthoringStack(fetchFn as unknown as typeof fetch);
    expect(probe.kind).toBe("ok");
    expect(fetchFn).toHaveBeenCalledTimes(2);
  });

  it("reports missing_routes when publication 404s (wrong BE / stale proxy)", async () => {
    const fetchFn = vi.fn(async (url: RequestInfo) => {
      const href = String(url);
      if (href.includes("/publication")) return new Response("missing", { status: 404 });
      return new Response("{}", { status: 200 });
    });
    const probe = await probeProductSystemAuthoringStack(fetchFn as unknown as typeof fetch);
    expect(probe.kind).toBe("missing_routes");
    expect(probe.publicationStatus).toBe(404);
    expect(probe.detail).toMatch(/BACKEND_PORT=8000|stale/i);
  });
});

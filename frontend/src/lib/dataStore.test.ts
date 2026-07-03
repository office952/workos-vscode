import { describe, it, expect, beforeEach, afterEach, beforeAll, afterAll, vi } from "vitest";

vi.mock("./api", () => ({
  quotesApi: {
    list: vi.fn(async () => [{ id: 42 }]),
  },
}));
vi.mock("./config", () => ({
  getAPIBaseURL: () => "https://dummy",
}));

import { createOrderFromQuote, normalizeOrderPaymentStatus, normalizeOrderStatus } from "./dataStore";

describe("normalizeOrderStatus", () => {
  it("maps legacy in_production alias to in_execution", () => {
    expect(normalizeOrderStatus("in_production")).toBe("in_execution");
  });

  it("preserves canonical order statuses", () => {
    expect(normalizeOrderStatus("locked")).toBe("locked");
    expect(normalizeOrderStatus("in_execution")).toBe("in_execution");
  });

  it("falls back unknown statuses to created", () => {
    expect(normalizeOrderStatus("unknown")).toBe("created");
  });
});

describe("normalizeOrderPaymentStatus", () => {
  it("defaults null, undefined, and empty string to pending", () => {
    expect(normalizeOrderPaymentStatus(null)).toBe("pending");
    expect(normalizeOrderPaymentStatus(undefined)).toBe("pending");
    expect(normalizeOrderPaymentStatus("")).toBe("pending");
    expect(normalizeOrderPaymentStatus("   ")).toBe("pending");
  });

  it("preserves known payment statuses", () => {
    expect(normalizeOrderPaymentStatus("pending")).toBe("pending");
    expect(normalizeOrderPaymentStatus("partial")).toBe("partial");
    expect(normalizeOrderPaymentStatus("paid")).toBe("paid");
    expect(normalizeOrderPaymentStatus("PAID")).toBe("paid");
  });

  it("falls back unknown values to pending", () => {
    expect(normalizeOrderPaymentStatus("unknown")).toBe("pending");
  });
});

describe("createOrderFromQuote", () => {
  let originalFetch: typeof globalThis.fetch;
  let originalWindow: typeof globalThis.window;
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeAll(() => {
    // Minimal window mock for code that expects window
    originalWindow = globalThis.window;
    if (typeof globalThis.window === "undefined") {
      globalThis.window = {} as any;
    }
    // Mock fetch
    originalFetch = globalThis.fetch;
    fetchMock = vi.fn(async (url: string | URL | Request, opts?: RequestInit) => {
      // Simulate backend contract for order creation
      if (typeof url === "string" && url.includes("/api/v1/entities/orders/from-quote/")) {
        return {
          ok: true,
          json: async () => ({ order_code: "ORDER-123" }),
        } as any;
      }
      // Simulate other fetches (quotesApi.list, etc.)
      if (typeof url === "string" && url.includes("/api/v1/entities/quotes")) {
        return {
          ok: true,
          json: async () => [{ id: 42 }],
        } as any;
      }
      return { ok: false, json: async () => ({}) } as any;
    });
    globalThis.fetch = fetchMock as unknown as typeof globalThis.fetch;
  });

  afterAll(() => {
    globalThis.fetch = originalFetch;
    globalThis.window = originalWindow;
  });
  beforeEach(() => {
    vi.spyOn(console, "warn").mockImplementation(() => {});
    fetchMock.mockClear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should not send acknowledge_readiness_warnings when not provided (exact body assertion)", async () => {
    const result = await createOrderFromQuote("Q-123");
    expect(result).toBe("ORDER-123");

    // Find the fetch call to the from-quote endpoint
    const orderCall = fetchMock.mock.calls.find(
      (call: any[]) => typeof call[0] === "string" && call[0].includes("/api/v1/entities/orders/from-quote/")
    );
    expect(orderCall).toBeDefined();

    const [, fetchOpts] = orderCall!;
    // When no options are provided, body must be undefined (no acknowledge fields sent)
    expect(fetchOpts?.body).toBeUndefined();
  });

  it("should send exact body with acknowledgement fields when provided", async () => {
    const result = await createOrderFromQuote("Q-123", {
      acknowledge_readiness_warnings: true,
      readiness_warning_acknowledgement_reason: "Operator reviewed warnings.",
    });
    expect(result).toBe("ORDER-123");

    // Find the fetch call to the from-quote endpoint
    const orderCall = fetchMock.mock.calls.find(
      (call: any[]) => typeof call[0] === "string" && call[0].includes("/api/v1/entities/orders/from-quote/")
    );
    expect(orderCall).toBeDefined();

    const [, fetchOpts] = orderCall!;
    const body = JSON.parse(fetchOpts?.body as string);
    expect(body).toEqual({
      acknowledge_readiness_warnings: true,
      readiness_warning_acknowledgement_reason: "Operator reviewed warnings.",
    });
  });

  it("should not send reason without acknowledgement true (reason alone does not imply ack)", async () => {
    // Contract decision: if acknowledge_readiness_warnings is not true,
    // reason is NOT sent even if provided. Frontend guards this.
    const result = await createOrderFromQuote("Q-123", {
      acknowledge_readiness_warnings: false,
      readiness_warning_acknowledgement_reason: "Some reason",
    });
    expect(result).toBe("ORDER-123");

    // Find the fetch call to the from-quote endpoint
    const orderCall = fetchMock.mock.calls.find(
      (call: any[]) => typeof call[0] === "string" && call[0].includes("/api/v1/entities/orders/from-quote/")
    );
    expect(orderCall).toBeDefined();

    const [, fetchOpts] = orderCall!;
    // Body must be undefined — acknowledge_readiness_warnings=false means nothing is sent
    expect(fetchOpts?.body).toBeUndefined();
  });

  it("should send ack=true without reason when reason is not provided", async () => {
    const result = await createOrderFromQuote("Q-123", {
      acknowledge_readiness_warnings: true,
    });
    expect(result).toBe("ORDER-123");

    // Find the fetch call to the from-quote endpoint
    const orderCall = fetchMock.mock.calls.find(
      (call: any[]) => typeof call[0] === "string" && call[0].includes("/api/v1/entities/orders/from-quote/")
    );
    expect(orderCall).toBeDefined();

    const [, fetchOpts] = orderCall!;
    const body = JSON.parse(fetchOpts?.body as string);
    // Only acknowledge_readiness_warnings should be present, no reason
    expect(body).toEqual({
      acknowledge_readiness_warnings: true,
    });
  });

  it("does not call real network — uses mocked fetch only", () => {
    // Verify that globalThis.fetch is our mock
    expect(globalThis.fetch).toBe(fetchMock);
    // No real network calls are made — all calls go through our vi.fn mock
  });
});
import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import EnvironmentBanner, { EnvironmentBannerView } from "@/components/workos/EnvironmentBanner";
import { buildRuntimeStatusSummary } from "@/components/workos/RuntimeStatusSummary";
import { EMPTY_RUNTIME_TRUTH_SNAPSHOT } from "@/types/runtimeStatus";

const mockUseAuth = vi.fn();
const mockUseRuntimeHealth = vi.fn();

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: () => mockUseAuth(),
}));

vi.mock("@/hooks/useRuntimeHealth", () => ({
  useRuntimeHealth: () => mockUseRuntimeHealth(),
}));

describe("EnvironmentBanner", () => {
  beforeEach(() => {
    mockUseAuth.mockReturnValue({ authState: "authenticated" });
    mockUseRuntimeHealth.mockReturnValue({
      snapshot: {
        ...EMPTY_RUNTIME_TRUTH_SNAPSHOT,
        backend: { state: "warning", rawStatus: "warning", checkedAt: "2026-07-17T04:00:00.000Z" },
        database: { state: "unknown", source: "none" },
        environment: { state: "local", rawValue: "development" },
      },
      isLoading: false,
      isRefreshing: false,
      refresh: vi.fn(),
      lastError: null,
    });
  });

  it("wires hook result and shows Romanian warning text without LIVE/DB", () => {
    render(<EnvironmentBanner />);
    const main = screen.getByTestId("environment-banner-main");
    expect(main.textContent).toBe("Local · Backend cu avertisment · DB neverificată");
    expect(main.textContent).not.toMatch(/LIVE/);
    expect(screen.getByTestId("environment-banner")).toHaveAttribute("data-severity", "warning");
    expect(screen.getByTestId("environment-banner-tech").textContent).toContain("status=warning");
  });

  it("authenticated alone with checking snapshot is not positive", () => {
    mockUseRuntimeHealth.mockReturnValue({
      snapshot: EMPTY_RUNTIME_TRUTH_SNAPSHOT,
      isLoading: true,
      isRefreshing: false,
      refresh: vi.fn(),
      lastError: null,
    });
    render(<EnvironmentBanner />);
    expect(screen.getByTestId("environment-banner")).toHaveAttribute("data-severity", "neutral");
    expect(screen.getByTestId("environment-banner-main").textContent).toContain("Se verifică");
    expect(screen.queryByText(/LIVE/)).toBeNull();
  });

  it("shows session note when unauthenticated without inventing healthy runtime", () => {
    mockUseAuth.mockReturnValue({ authState: "unauthenticated" });
    mockUseRuntimeHealth.mockReturnValue({
      snapshot: {
        ...EMPTY_RUNTIME_TRUTH_SNAPSHOT,
        backend: { state: "unavailable", errorKind: "NETWORK_ERROR" },
        database: { state: "unknown", source: "none" },
        environment: { state: "local" },
      },
      isLoading: false,
      isRefreshing: false,
      refresh: vi.fn(),
      lastError: "NETWORK_ERROR",
    });
    render(<EnvironmentBanner />);
    expect(screen.getByTestId("environment-banner-session").textContent).toContain("Sesiune neautentificată");
    expect(screen.getByTestId("environment-banner")).toHaveAttribute("data-severity", "critical");
  });

  it("does not crash on partial/malformed-like snapshot", () => {
    mockUseRuntimeHealth.mockReturnValue({
      snapshot: {
        backend: { state: "unknown" },
        database: { state: "unknown", source: "none" },
        environment: { state: "unknown" },
        diagnostics: { authorized: null, available: null },
        stale: false,
      },
      isLoading: false,
      isRefreshing: false,
      refresh: vi.fn(),
      lastError: "MALFORMED_RESPONSE",
    });
    expect(() => render(<EnvironmentBanner />)).not.toThrow();
    expect(screen.getByTestId("environment-banner-main").textContent).not.toMatch(/LIVE/);
  });

  it("exposes accessible status label", () => {
    const view = buildRuntimeStatusSummary({
      snapshot: {
        ...EMPTY_RUNTIME_TRUTH_SNAPSHOT,
        backend: { state: "unavailable" },
        database: { state: "unknown", source: "none" },
        environment: { state: "local" },
      },
      lastError: "TIMEOUT",
    });
    render(<EnvironmentBannerView view={view} />);
    expect(screen.getByRole("status")).toHaveAttribute("aria-label");
    expect(screen.getByRole("status").getAttribute("aria-label")).toContain("indisponibil");
  });

  it("UTF-8 neverificată / confirmată render without mojibake", () => {
    mockUseRuntimeHealth.mockReturnValue({
      snapshot: {
        ...EMPTY_RUNTIME_TRUTH_SNAPSHOT,
        backend: { state: "healthy", rawStatus: "ok" },
        database: { state: "confirmed", source: "diagnostics" },
        environment: { state: "local" },
      },
      isLoading: false,
      isRefreshing: false,
      refresh: vi.fn(),
      lastError: null,
    });
    render(<EnvironmentBanner />);
    const text = screen.getByTestId("environment-banner-main").textContent ?? "";
    expect(text).toContain("Baza de date confirmată");
    expect(text).not.toMatch(/Ã.|Äƒ|È›|â€/);
  });
});

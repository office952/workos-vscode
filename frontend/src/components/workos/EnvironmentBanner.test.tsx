import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import EnvironmentBanner, { EnvironmentBannerView } from "@/components/workos/EnvironmentBanner";
import { buildRuntimeStatusSummary } from "@/components/workos/RuntimeStatusSummary";
import { EMPTY_RUNTIME_TRUTH_SNAPSHOT } from "@/types/runtimeStatus";

const mockUseAuth = vi.fn();
const mockRefresh = vi.fn();
const mockUseRuntimeHealth = vi.fn();

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: () => mockUseAuth(),
}));

vi.mock("@/hooks/useRuntimeHealth", () => ({
  useRuntimeHealth: (opts?: { fetchDiagnostics?: boolean }) => mockUseRuntimeHealth(opts),
}));

describe("EnvironmentBanner", () => {
  beforeEach(() => {
    mockUseAuth.mockReturnValue({ authState: "authenticated" });
    mockRefresh.mockReset();
    mockUseRuntimeHealth.mockReturnValue({
      snapshot: {
        ...EMPTY_RUNTIME_TRUTH_SNAPSHOT,
        backend: { state: "warning", rawStatus: "warning", checkedAt: "2026-07-17T04:00:00.000Z" },
        database: { state: "unknown", source: "none" },
        environment: { state: "local", rawValue: "development" },
        diagnostics: { authorized: false, available: false, httpStatus: 403 },
      },
      isLoading: false,
      isRefreshing: false,
      refresh: mockRefresh,
      lastError: null,
    });
  });

  it("wires hook with diagnostics and shows Romanian warning without LIVE/DB", () => {
    render(<EnvironmentBanner />);
    expect(mockUseRuntimeHealth).toHaveBeenCalledWith(
      expect.objectContaining({ fetchDiagnostics: true }),
    );
    const main = screen.getByTestId("environment-banner-main");
    expect(main.textContent).toBe("Local · Backend cu avertisment · DB neverificată");
    expect(main.textContent).not.toMatch(/LIVE/);
    expect(screen.getByTestId("environment-banner")).toHaveAttribute("data-severity", "warning");
  });

  it("exposes refresh action and opens details with 403 explanation", () => {
    render(<EnvironmentBanner />);
    const refresh = screen.getByTestId("environment-banner-refresh");
    expect(refresh).toHaveAccessibleName("Reverifică starea");
    fireEvent.click(refresh);
    expect(mockRefresh).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByTestId("environment-banner-details-toggle"));
    expect(screen.getByTestId("environment-banner-details-toggle")).toHaveAttribute(
      "aria-expanded",
      "true",
    );
    expect(screen.getByTestId("runtime-status-details")).toBeInTheDocument();
    expect(screen.getByTestId("runtime-details-diagnostics-message")).toHaveTextContent(
      "Nu ai permisiune pentru diagnostice detaliate",
    );
  });

  it("shows stale label and retry wording when unavailable", () => {
    mockUseRuntimeHealth.mockReturnValue({
      snapshot: {
        ...EMPTY_RUNTIME_TRUTH_SNAPSHOT,
        backend: {
          state: "unavailable",
          lastSuccessfulAt: "2026-07-17T03:00:00.000Z",
          errorKind: "NETWORK_ERROR",
        },
        database: { state: "unknown", source: "none" },
        environment: { state: "local" },
        diagnostics: { authorized: null, available: null },
        stale: true,
      },
      isLoading: false,
      isRefreshing: false,
      refresh: mockRefresh,
      lastError: "NETWORK_ERROR",
    });
    render(<EnvironmentBanner />);
    expect(screen.getByTestId("environment-banner-stale")).toHaveTextContent("Stare învechită");
    expect(screen.getByTestId("environment-banner-refresh")).toHaveAccessibleName("Reîncearcă");
    expect(screen.getByTestId("environment-banner")).toHaveAttribute("data-severity", "critical");
    expect(screen.getByTestId("environment-banner")).toHaveAttribute("data-stale", "true");
  });

  it("authenticated alone with checking snapshot is not positive", () => {
    mockUseRuntimeHealth.mockReturnValue({
      snapshot: EMPTY_RUNTIME_TRUTH_SNAPSHOT,
      isLoading: true,
      isRefreshing: false,
      refresh: mockRefresh,
      lastError: null,
    });
    render(<EnvironmentBanner />);
    expect(screen.getByTestId("environment-banner")).toHaveAttribute("data-severity", "neutral");
    expect(screen.getByTestId("environment-banner-main").textContent).toContain("Se verifică");
  });

  it("EnvironmentBannerView disables refresh while busy", () => {
    const view = buildRuntimeStatusSummary({
      snapshot: {
        ...EMPTY_RUNTIME_TRUTH_SNAPSHOT,
        backend: { state: "checking" },
        environment: { state: "local" },
      },
      isLoading: true,
    });
    const onRefresh = vi.fn();
    render(
      <EnvironmentBannerView view={view} isRefreshing onRefresh={onRefresh} />,
    );
    expect(screen.getByTestId("environment-banner-refresh")).toBeDisabled();
  });
});

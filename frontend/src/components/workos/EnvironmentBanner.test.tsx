import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
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

function renderBanner(ui: React.ReactElement = <EnvironmentBanner />) {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
}

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

  it("wires hook with diagnostics and shows compact warning chip without LIVE/DB", () => {
    renderBanner();
    expect(mockUseRuntimeHealth).toHaveBeenCalledWith(
      expect.objectContaining({ fetchDiagnostics: true }),
    );
    const banner = screen.getByTestId("environment-banner");
    expect(banner).toHaveAttribute("data-presentation", "compact");
    expect(banner).toHaveAttribute("data-severity", "warning");
    const main = screen.getByTestId("environment-banner-main");
    expect(main.textContent).toBe("Stare sistem: necesită verificare");
    expect(main.textContent).not.toMatch(/LIVE/);
    expect(banner).toHaveAttribute(
      "aria-label",
      expect.stringContaining("Backend cu avertisment"),
    );
  });

  it("healthy staging shows compact available chip, not full-width strip", () => {
    mockUseRuntimeHealth.mockReturnValue({
      snapshot: {
        ...EMPTY_RUNTIME_TRUTH_SNAPSHOT,
        backend: { state: "healthy", rawStatus: "ok", checkedAt: "2026-07-17T04:00:00.000Z" },
        database: { state: "confirmed", source: "diagnostics" },
        environment: { state: "staging", rawValue: "staging" },
        diagnostics: { authorized: true, available: true, httpStatus: 200 },
      },
      isLoading: false,
      isRefreshing: false,
      refresh: mockRefresh,
      lastError: null,
    });
    renderBanner();
    expect(screen.getByTestId("environment-banner")).toHaveAttribute("data-severity", "positive");
    expect(screen.getByTestId("environment-banner-main")).toHaveTextContent(
      "Staging · Sistem disponibil",
    );
    expect(screen.queryByTestId("environment-banner-critical-strip")).not.toBeInTheDocument();
    expect(screen.queryByTestId("environment-banner-tech")).not.toBeInTheDocument();
  });

  it("DB confirmed + backend warning chip stays specific, not generic verificare", () => {
    mockUseRuntimeHealth.mockReturnValue({
      snapshot: {
        ...EMPTY_RUNTIME_TRUTH_SNAPSHOT,
        backend: { state: "warning", rawStatus: "warning", checkedAt: "2026-07-17T04:00:00.000Z" },
        database: { state: "confirmed", source: "diagnostics" },
        environment: { state: "staging", rawValue: "staging" },
        diagnostics: { authorized: true, available: true, httpStatus: 200 },
      },
      isLoading: false,
      isRefreshing: false,
      refresh: mockRefresh,
      lastError: null,
    });
    renderBanner();
    expect(screen.getByTestId("environment-banner")).toHaveAttribute("data-severity", "warning");
    expect(screen.getByTestId("environment-banner-main")).toHaveTextContent(
      "Staging · Backend cu avertisment · DB OK",
    );
    expect(screen.getByTestId("environment-banner-main").textContent).not.toMatch(
      /necesită verificare/i,
    );
  });

  it("healthy local + DB neverificată shows Backend OK, not alarmist verificare", () => {
    mockUseRuntimeHealth.mockReturnValue({
      snapshot: {
        ...EMPTY_RUNTIME_TRUTH_SNAPSHOT,
        backend: { state: "healthy", rawStatus: "ok", checkedAt: "2026-07-17T04:00:00.000Z" },
        database: { state: "unknown", source: "none" },
        environment: { state: "local", rawValue: "development" },
        diagnostics: { authorized: false, available: false, httpStatus: 403 },
      },
      isLoading: false,
      isRefreshing: false,
      refresh: mockRefresh,
      lastError: null,
    });
    renderBanner();
    expect(screen.getByTestId("environment-banner")).toHaveAttribute("data-severity", "warning");
    expect(screen.getByTestId("environment-banner-main")).toHaveTextContent(
      "Local · Backend OK · DB neverificată",
    );
    expect(screen.getByTestId("environment-banner-main").textContent).not.toMatch(
      /necesită verificare/i,
    );
  });

  it("staging with unverified DB stays warning compact, not critical", () => {
    mockUseRuntimeHealth.mockReturnValue({
      snapshot: {
        ...EMPTY_RUNTIME_TRUTH_SNAPSHOT,
        backend: { state: "healthy", rawStatus: "ok", checkedAt: "2026-07-17T04:00:00.000Z" },
        database: { state: "unknown", source: "none" },
        environment: { state: "staging", rawValue: "staging" },
        diagnostics: { authorized: false, available: false, httpStatus: 403 },
      },
      isLoading: false,
      isRefreshing: false,
      refresh: mockRefresh,
      lastError: null,
    });
    renderBanner();
    expect(screen.getByTestId("environment-banner")).toHaveAttribute("data-severity", "warning");
    expect(screen.getByTestId("environment-banner-main")).toHaveTextContent(
      "Staging · Backend OK · DB neverificată",
    );
    expect(screen.getByTestId("environment-banner-main").textContent).not.toMatch(
      /necesită verificare/i,
    );
    expect(screen.queryByTestId("environment-banner-critical-strip")).not.toBeInTheDocument();
  });

  it("exposes refresh, details toggle, and Control Center link", () => {
    renderBanner();
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
    const cc = screen.getByTestId("environment-banner-control-center-link");
    expect(cc).toHaveAttribute("href", "/modules");
    expect(cc).toHaveTextContent("Deschide Control Center");
  });

  it("shows critical strip for unavailable and keeps chip after dismiss", () => {
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
    renderBanner();
    expect(screen.getByTestId("environment-banner-stale")).toHaveTextContent("Stare învechită");
    expect(screen.getByTestId("environment-banner-refresh")).toHaveAccessibleName("Reîncearcă");
    expect(screen.getByTestId("environment-banner")).toHaveAttribute("data-severity", "critical");
    expect(screen.getByTestId("environment-banner")).toHaveAttribute("data-stale", "true");
    expect(screen.getByTestId("environment-banner-main")).toHaveTextContent("Stare sistem");
    expect(screen.getByTestId("environment-banner-critical-strip")).toBeInTheDocument();
    expect(screen.getByTestId("environment-banner-critical-text").textContent).toMatch(
      /Backend/i,
    );

    fireEvent.click(screen.getByTestId("environment-banner-critical-dismiss"));
    expect(screen.queryByTestId("environment-banner-critical-strip")).not.toBeInTheDocument();
    expect(screen.getByTestId("environment-banner")).toHaveAttribute("data-severity", "critical");
    expect(screen.getByTestId("environment-banner-main")).toHaveTextContent("Stare sistem");
  });

  it("authenticated alone with checking snapshot is not positive", () => {
    mockUseRuntimeHealth.mockReturnValue({
      snapshot: EMPTY_RUNTIME_TRUTH_SNAPSHOT,
      isLoading: true,
      isRefreshing: false,
      refresh: mockRefresh,
      lastError: null,
    });
    renderBanner();
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
    renderBanner(<EnvironmentBannerView view={view} isRefreshing onRefresh={onRefresh} />);
    expect(screen.getByTestId("environment-banner-refresh")).toBeDisabled();
  });
});

import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { ThemeProvider } from "./contexts/ThemeContext";

const mockFetch = vi.fn();

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function stubViewport(width: number) {
  Object.defineProperty(window, "innerWidth", {
    configurable: true,
    writable: true,
    value: width,
  });
  window.matchMedia = vi.fn().mockImplementation((query: string) => {
    const maxWidthMatch = /max-width:\s*(\d+)px/.exec(query);
    const matches = maxWidthMatch
      ? width <= Number(maxWidthMatch[1])
      : false;
    return {
      matches,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    };
  });
}

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: () => ({
    user: { name: "Test User", email: "test@workos.local", role: "admin" },
    loading: false,
    isAuthenticated: true,
    authState: "authenticated" as const,
    canAccessProtectedApi: true,
    devAuthEnabled: false,
    logout: vi.fn(),
    login: vi.fn(),
  }),
}));

vi.mock("./pages/Dashboard", () => ({
  default: () => <div data-testid="desktop-page-stub">Dashboard</div>,
}));

vi.mock("./pages/MaterializedOpsGraph", () => ({
  default: () => (
    <div data-testid="materialized-ops-graph-page">
      Ops graph stub · Identity · order_id=973010 · RO
    </div>
  ),
}));

vi.mock("./pages/EmployeeAttendanceEffects", () => ({
  default: () => <div data-testid="attendance-effects-console-stub">Effects</div>,
}));

import { AuthenticatedAppRoutes } from "./App";

function renderRoutes(path: string) {
  render(
    <ThemeProvider defaultTheme="light">
      <MemoryRouter initialEntries={[path]}>
        <AuthenticatedAppRoutes />
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe("AuthenticatedAppRoutes layout isolation", () => {
  beforeEach(() => {
    stubViewport(1280);
    vi.stubGlobal("fetch", mockFetch);
    mockFetch.mockReset();
    mockFetch.mockImplementation(() => Promise.resolve(jsonResponse([])));
    vi.clearAllMocks();
  });

  it.each([
    "/employee-app",
    "/employee-app/requests",
    "/employee-app/attendance",
    "/employee-app/review",
    "/employee-app/team",
  ])("renders employee mobile standalone without desktop shell on %s", async (path) => {
    renderRoutes(path);

    expect(screen.getByTestId("employee-mobile-standalone-root")).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-shell")).toBeInTheDocument();
    });
    expect(screen.getByTestId("employee-mobile-bottom-nav")).toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-header")).toBeInTheDocument();
    // Hint is optional chrome — EmployeeMobileApp suite asserts absence in current build.
    expect(screen.queryByTestId("workos-desktop-shell")).not.toBeInTheDocument();
    expect(screen.queryByTestId("workos-sidebar")).not.toBeInTheDocument();
    expect(screen.queryByTestId("workos-desktop-topbar")).not.toBeInTheDocument();
  });

  it("renders desktop shell on /dashboard without employee standalone root", () => {
    renderRoutes("/dashboard");

    expect(screen.getByTestId("workos-desktop-shell")).toBeInTheDocument();
    expect(screen.getByTestId("workos-sidebar")).toBeInTheDocument();
    expect(screen.getByTestId("workos-desktop-topbar")).toBeInTheDocument();
    expect(screen.getByTestId("desktop-page-stub")).toBeInTheDocument();
    expect(screen.queryByTestId("employee-mobile-standalone-root")).not.toBeInTheDocument();
    expect(screen.getByTestId("workos-desktop-shell")).toHaveAttribute(
      "data-nav-mode",
      "rail",
    );
    expect(screen.queryByTestId("workos-nav-drawer-toggle")).not.toBeInTheDocument();
  });

  it("keeps /attendance/effects in desktop admin shell", () => {
    renderRoutes("/attendance/effects");

    expect(screen.getByTestId("workos-desktop-shell")).toBeInTheDocument();
    expect(screen.getByTestId("attendance-effects-console-stub")).toBeInTheDocument();
    expect(screen.queryByTestId("employee-mobile-standalone-root")).not.toBeInTheDocument();
  });

  it("OR-07: narrow ops-graph starts with nav drawer closed (content-first)", async () => {
    stubViewport(390);
    renderRoutes("/execution/ops-graph");

    const shell = screen.getByTestId("workos-desktop-shell");
    await waitFor(() => {
      expect(shell).toHaveAttribute("data-nav-mode", "drawer");
    });
    expect(shell).toHaveAttribute("data-nav-drawer", "closed");
    expect(screen.getByTestId("materialized-ops-graph-page")).toBeInTheDocument();
    expect(screen.getByTestId("workos-nav-drawer-toggle")).toBeInTheDocument();
    expect(screen.getByTestId("workos-narrow-topbar-title")).toHaveTextContent(
      "WorkOS",
    );
    expect(screen.queryByTestId("environment-banner-details-toggle")).not.toBeInTheDocument();
    expect(screen.getByTestId("workos-sidebar")).toHaveAttribute(
      "data-nav-drawer-open",
      "false",
    );
    expect(screen.queryByTestId("workos-nav-drawer-backdrop")).not.toBeInTheDocument();

    fireEvent.click(screen.getByTestId("workos-nav-drawer-toggle"));
    expect(shell).toHaveAttribute("data-nav-drawer", "open");
    expect(screen.getByTestId("workos-sidebar")).toHaveAttribute(
      "data-nav-drawer-open",
      "true",
    );
    expect(screen.getByTestId("workos-nav-drawer-backdrop")).toBeInTheDocument();

    fireEvent.click(screen.getByTestId("workos-nav-drawer-backdrop"));
    expect(shell).toHaveAttribute("data-nav-drawer", "closed");
  });
});

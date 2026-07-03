import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

const mockFetch = vi.fn();

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
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

vi.mock("./pages/EmployeeAttendanceEffects", () => ({
  default: () => <div data-testid="attendance-effects-console-stub">Effects</div>,
}));

import { AuthenticatedAppRoutes } from "./App";

function renderRoutes(path: string) {
  render(
    <MemoryRouter initialEntries={[path]}>
      <AuthenticatedAppRoutes />
    </MemoryRouter>,
  );
}

describe("AuthenticatedAppRoutes layout isolation", () => {
  beforeEach(() => {
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
    expect(screen.getByTestId("employee-mobile-same-account-hint")).toBeInTheDocument();
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
  });

  it("keeps /attendance/effects in desktop admin shell", () => {
    renderRoutes("/attendance/effects");

    expect(screen.getByTestId("workos-desktop-shell")).toBeInTheDocument();
    expect(screen.getByTestId("attendance-effects-console-stub")).toBeInTheDocument();
    expect(screen.queryByTestId("employee-mobile-standalone-root")).not.toBeInTheDocument();
  });
});

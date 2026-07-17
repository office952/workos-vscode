import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

vi.mock("@/hooks/useDashboardStats", () => ({
  useDashboardStats: () => ({
    kpis: [],
    jobs: [],
    capacity: [],
    alerts: [],
    throughput: [],
    events: [],
    source: "db",
    loading: false,
    error: null,
    lastUpdate: new Date("2026-07-17T05:00:00.000Z"),
    refresh: vi.fn(),
  }),
}));

import Dashboard from "@/pages/Dashboard";

describe("Dashboard data source honesty", () => {
  it("renames misleading Live to Date disponibile", () => {
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>,
    );
    expect(screen.getByTestId("dashboard-data-source")).toHaveTextContent("Date disponibile");
    expect(screen.queryByText(/^Live$/)).not.toBeInTheDocument();
  });
});

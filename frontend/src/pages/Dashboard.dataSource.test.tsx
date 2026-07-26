import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

vi.mock("@/hooks/useDashboardStats", () => ({
  useDashboardStats: () => ({
    kpis: [
      {
        code: "KPI_MACHINE_UTIL",
        label: "Machine Util.",
        value: 56596,
        unit: "%",
        trend: "stable",
        trendValue: 0,
        status: "good",
      },
      {
        code: "KPI_ACTIVE_JOBS",
        label: "Active Jobs",
        value: 3,
        unit: "",
        trend: "stable",
        trendValue: 0,
        status: "good",
      },
      {
        code: "KPI_BLOCKED_JOBS",
        label: "Blocked",
        value: 0,
        unit: "",
        trend: "stable",
        trendValue: 0,
        status: "good",
      },
      {
        code: "KPI_OTIF",
        label: "OTIF",
        value: 90,
        unit: "%",
        trend: "stable",
        trendValue: 0,
        status: "good",
      },
      {
        code: "KPI_THROUGHPUT",
        label: "Throughput Today",
        value: 1,
        unit: "jobs",
        trend: "stable",
        trendValue: 0,
        status: "warning",
      },
    ],
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

  it("never renders absurd percent KPIs like 56596%", () => {
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>,
    );
    expect(screen.queryByText(/56596/)).not.toBeInTheDocument();
    expect(screen.getByText(">100")).toBeInTheDocument();
    expect(screen.getByText("Utilizare Utilaje")).toBeInTheDocument();
  });
});

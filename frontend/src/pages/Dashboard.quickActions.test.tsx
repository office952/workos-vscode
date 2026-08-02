import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

const mockNavigate = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>(
    "react-router-dom",
  );
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock("@/hooks/useDashboardStats", () => ({
  useDashboardStats: () => ({
    capacityModel: null,
    kpis: [],
    jobs: [],
    capacity: [],
    alerts: [],
    throughput: [],
    events: [],
    operationalTruth: {
      plannedMinutesTotal: 0,
      actualMinutesTotal: 0,
      overrunMinutesTotal: 0,
      notices: [],
      dataGaps: {},
      boundaries: {},
    },
    source: "mock",
    loading: false,
    error: null,
    lastUpdate: new Date("2026-08-02T12:00:00.000Z"),
    refresh: vi.fn(),
  }),
}));

import Dashboard from "@/pages/Dashboard";

describe("Dashboard quick actions — Intake V6 canonical entry", () => {
  beforeEach(() => {
    mockNavigate.mockReset();
  });

  it("Cerere Nouă navigates to Intake V6 shell bootstrap, not legacy /intake", () => {
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByTestId("dashboard-quick-action-cerere-noua"));

    expect(mockNavigate).toHaveBeenCalledWith("/intake-v6/operator");
    expect(mockNavigate).not.toHaveBeenCalledWith("/intake");
  });
});

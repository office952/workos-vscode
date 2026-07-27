import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

vi.mock("@/hooks/useDashboardStats", () => ({
  useDashboardStats: () => ({
    kpis: [
      {
        code: "KPI_MACHINE_UTIL",
        label: "Load planificat WC",
        value: 56596,
        unit: "%",
        trend: "stable",
        trendValue: 0,
        status: "good",
        kind: "derived",
        window: "lifetime_plan_vs_finished_sessions",
        explanation: "Media load planificat 0–100 pe workcenter.",
        gapNote:
          "Utilaj calendar/shift: date indisponibile — afișăm load planificat 0–100 pe workcenter.",
      },
      {
        code: "KPI_ACTIVE_JOBS",
        label: "Job-uri în pipeline",
        value: 3,
        unit: "",
        trend: "stable",
        trendValue: 0,
        status: "good",
        kind: "actual",
      },
      {
        code: "KPI_BLOCKED_JOBS",
        label: "Blocate (execuție)",
        value: 0,
        unit: "",
        trend: "stable",
        trendValue: 0,
        status: "good",
        kind: "actual",
      },
      {
        code: "KPI_OTIF",
        label: "OTIF (proxy)",
        value: 90,
        unit: "%",
        trend: "stable",
        trendValue: 0,
        status: "good",
        kind: "proxy",
        explanation: "Proxy slab",
        gapNote: "Semnal OTIF durabil indisponibil.",
      },
      {
        code: "KPI_THROUGHPUT",
        label: "Throughput azi (UTC)",
        value: 1,
        unit: "jobs",
        trend: "stable",
        trendValue: 0,
        status: "warning",
        kind: "actual",
        window: "utc_calendar_today",
        explanation: "Completed cu updated_at în ziua UTC curentă.",
      },
    ],
    jobs: [],
    capacity: [
      {
        workcenterId: "wc_cnc",
        workcenterName: "CNC",
        loadToday: 100,
        load7d: 100,
        load30d: 100,
        availableToday: 0,
        plannedMinutes: 100,
        actualMinutes: 200,
        overrunMinutes: 100,
        loadKind: "planned_load",
        loadLabel: "Load planificat 0–100",
      },
    ],
    alerts: [],
    throughput: [],
    events: [],
    operationalTruth: {
      plannedMinutesTotal: 100,
      actualMinutesTotal: 200,
      overrunMinutesTotal: 100,
      throughputWindow: "utc_calendar_today",
      workcenterLoadKind: "planned_load_0_100",
      calendarShiftUtilAvailable: false,
      notices: [
        "Pricing Registry: 2 rate/price lipsă — Owner data needed.",
        "Cost Intern (HR analytics/profitability — NU tarif client): 1 angajați productivi incompleți.",
        "Capacitate: util calendar/shift necunoscut — afișăm load planificat 0–100.",
        "Utilaj calendar/shift: date indisponibile — afișăm load planificat 0–100 pe workcenter (nu utilizare pe ture/calendar).",
        "Capacitate / load planificat — nu pricing comercial, nu cost orar utilaj → tarif client.",
        "Throughput azi = comenzi completed cu updated_at în ziua calendaristică UTC curentă.",
      ],
      dataGaps: {
        pricing: {
          domain: "pricing_registry",
          ownerDataNeeded: true,
          missingPriceCount: 2,
          notice: "Pricing Registry: 2 rate/price lipsă — Owner data needed.",
        },
        costIntern: {
          domain: "hr_internal_cost",
          ownerDataNeeded: true,
          incompleteEmployeeCount: 1,
          notice:
            "Cost Intern (HR analytics/profitability — NU tarif client): 1 angajați productivi incompleți.",
        },
        capacity: {
          domain: "capacity_feasibility",
          ownerDataNeeded: true,
          unknown: true,
          notice: "Capacitate: util calendar/shift necunoscut — afișăm load planificat 0–100.",
        },
      },
      boundaries: {
        pricing: "Dashboard does not compute or display client tariffs.",
      },
    },
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
    expect(screen.getByText("Load planificat WC")).toBeInTheDocument();
  });

  it("surfaces calendar/shift util gap and UTC throughput labels", () => {
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>,
    );
    expect(screen.getByTestId("dashboard-operational-truth")).toBeInTheDocument();
    expect(screen.getByTestId("capacity-calendar-gap")).toHaveTextContent(
      /calendar\/shift/i,
    );
    expect(screen.getByText("Throughput azi (UTC)")).toBeInTheDocument();
    expect(screen.getByText("OTIF (proxy)")).toBeInTheDocument();
    expect(screen.getByText(/Load planificat pe workcenter/i)).toBeInTheDocument();
  });

  it("allows progressive disclosure for honesty banner and gap noise", () => {
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>,
    );
    expect(screen.getByTestId("dashboard-honesty-banner-ack")).toBeInTheDocument();
    expect(screen.getByTestId("dashboard-honesty-gaps-ack")).toBeInTheDocument();
    expect(screen.getAllByTestId("kpi-gap-note").length).toBeGreaterThan(0);
  });

  it("surfaces Pricing / Cost Intern / Capacity data gaps without mixing domains", () => {
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>,
    );
    expect(screen.getByTestId("dashboard-data-gaps")).toBeInTheDocument();
    expect(screen.getByTestId("dashboard-data-gap-pricing")).toHaveTextContent(/Owner data needed/i);
    expect(screen.getByTestId("dashboard-data-gap-costIntern")).toHaveTextContent(/NU tarif client/i);
    expect(screen.getByTestId("dashboard-data-gap-capacity")).toHaveTextContent(/calendar\/shift/i);
    expect(screen.getByText(/Material ≠ regulă comercială ≠ cost intern ≠ capacitate/i)).toBeInTheDocument();
  });

  it("separates planned vs actual vs blocked in summary bar", () => {
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>,
    );
    expect(screen.getByTestId("dashboard-summary-bar")).toHaveTextContent(
      /planificat \/ actual \/ blocat/i,
    );
    expect(screen.getByText(/Planificate:/)).toBeInTheDocument();
    expect(screen.getByText(/În execuție:/)).toBeInTheDocument();
    expect(screen.getByText(/Blocate:/)).toBeInTheDocument();
  });
});

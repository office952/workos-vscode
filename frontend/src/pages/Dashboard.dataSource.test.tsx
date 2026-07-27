import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

vi.mock("@/hooks/useDashboardStats", () => ({
  useDashboardStats: () => ({
    capacityModel: {
      batch: "capacity_batch_04",
      materialize: "BLOCKED",
      minutesReadiness: { tasksWithMinutes: 1, tasksMissingMinutes: 2 },
      machineMappingReadiness: {
        summary: { mappedToWc: 3, unmappedWc: 1, machineCount: 4 },
        maintenance: { availability: "gap", notice: "maintenance availability: gap" },
      },
      batch04Gates: {
        assignment: { truthCount: 0, needsAssignmentCount: 4, policy: "machine_code on operational_tasks" },
        machineUtil: {
          rows: [
            {
              machineCode: "M1",
              machineUtilPct: null,
              machineUtilStatus: "GAP",
              machineUtilNote: "NEEDS ASSIGNMENT TRUTH",
            },
          ],
          policy: "CAP-013 gated",
        },
        maintenance: {
          availability: "gap",
          statusOnlyCount: 1,
          notice: "maintenance availability: gap",
        },
      },
      preMaterializeChecklist: {
        materialize: "BLOCKED",
        dec009: "A",
        readyForMaterializeGo: false,
        blockerCount: 4,
        summary: "DEC-009 blocked — 4 capacity/route blockers still open.",
        items: [
          {
            id: "DEC-009",
            label: "POST materialize GO (DEC-009)",
            status: "BLOCKED",
            blocking: true,
            detail: "DEC-009=A — materialize remains BLOCKED",
          },
          {
            id: "CAP-012",
            label: "Machine assignment truth on operational tasks",
            status: "NEEDS ASSIGNMENT TRUTH",
            blocking: true,
          },
        ],
      },
    },
    kpis: [
      {
        code: "KPI_MACHINE_UTIL",
        label: "Util% shift WC",
        value: 56596,
        unit: "%",
        trend: "stable",
        trendValue: 0,
        status: "good",
        kind: "derived",
        window: "month_2026_07_shift",
        explanation: "Media util% planned/shift pe workcenter.",
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
        loadKind: "calendar_shift_planned_load",
        loadLabel: "Planned load / ore shift (WC)",
        availableMinutes: 11040,
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
      workcenterLoadKind: "calendar_shift_planned_load",
      calendarShiftUtilAvailable: true,
      notices: [
        "Pricing Registry: 2 rate/price lipsă — Owner data needed.",
        "Cost Intern (HR analytics/profitability — NU tarif client): 1 angajați productivi incompleți.",
        "Capacitate: util% WC = planned load / ore shift (Company Calendar).",
        "Util% WC = planned load / ore shift (Company Calendar L–V 8h − sărbători RO).",
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
          ownerDataNeeded: false,
          unknown: false,
          calendarShiftUtilAvailable: true,
          notice: "Capacitate: util% WC = planned load / ore shift (Company Calendar).",
        },
      },
      boundaries: {
        pricing: "Dashboard does not compute or display client tariffs.",
      },
      capacityBatch04: {
        materialize: "BLOCKED",
        dec009: "A",
        maintenanceAvailability: "gap",
        statusOnlyMaintenanceCount: 1,
        assignmentTruthCount: 0,
        needsAssignmentCount: 4,
        preMaterializeBlockerCount: 4,
        preMaterializeSummary: "DEC-009 blocked — 4 capacity/route blockers still open.",
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
    expect(screen.getByText("Util% shift WC")).toBeInTheDocument();
  });

  it("surfaces calendar/shift util active and UTC throughput labels", () => {
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>,
    );
    expect(screen.getByTestId("dashboard-operational-truth")).toBeInTheDocument();
    expect(screen.getByTestId("capacity-calendar-active")).toHaveTextContent(
      /Calendar\/shift activ/i,
    );
    expect(screen.getByText("Throughput azi (UTC)")).toBeInTheDocument();
    expect(screen.getByText("OTIF (proxy)")).toBeInTheDocument();
    expect(screen.getByText(/Util% shift pe workcenter/i)).toBeInTheDocument();
    expect(screen.getByTestId("capacity-batch02-readiness")).toHaveTextContent(/NULL \+ WARN/i);
    expect(screen.getByTestId("capacity-maintenance-readiness")).toHaveTextContent(/gap/i);
    expect(screen.getByTestId("capacity-batch04-gates")).toHaveTextContent(/NEEDS ASSIGNMENT TRUTH/i);
    expect(screen.getByTestId("capacity-machine-util-gate")).toHaveTextContent(/GAP/i);
    expect(screen.getByTestId("capacity-pre-materialize-checklist")).toHaveTextContent(/DEC-009/i);
    expect(screen.getByTestId("capacity-pre-materialize-checklist")).toHaveTextContent(/BLOCKED/i);
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
    expect(screen.getByTestId("dashboard-data-gap-capacity")).toHaveTextContent(
      /planned load \/ ore shift/i,
    );
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

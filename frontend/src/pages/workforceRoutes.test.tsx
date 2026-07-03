import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Navigate, Route, Routes } from "react-router-dom";

const { mockLiveEmployees } = vi.hoisted(() => ({
  mockLiveEmployees: [
    {
      id: 1,
      name: "Andrei Goghi",
      status: "active",
      employee_type: "productive",
      valid_for_cost_engine: true,
      department: "Productie",
      role: "CNC",
      cost_lunar_firma: 5000,
    },
    {
      id: 2,
      name: "Calin Cimpean",
      status: "active",
      employee_type: "productive",
      valid_for_cost_engine: true,
      department: "Productie",
      role: "Sudura",
      cost_lunar_firma: 4800,
    },
  ],
}));

vi.mock("@/api/costEngine", () => ({
  employeesApi: {
    list: vi.fn().mockResolvedValue({ items: mockLiveEmployees, total: mockLiveEmployees.length }),
    create: vi.fn(),
    update: vi.fn(),
    remove: vi.fn(),
  },
}));

vi.mock("@/api/employeeBalances", () => ({
  employeeBalancesApi: {
    summary: vi.fn().mockResolvedValue({
      currency: "RON",
      totals: {
        active_balance: 0,
        advance_total: 0,
        loan_total: 0,
        retention_total: 0,
        repayment_total: 0,
        compensation_total: 0,
        transaction_count: 0,
      },
      employees: [
        {
          employee_id: 1,
          employee_name: "Andrei Goghi",
          active_balance: 0,
          advance_total: 0,
          loan_total: 0,
          retention_total: 0,
          repayment_total: 0,
          compensation_total: 0,
          transaction_count: 0,
        },
        {
          employee_id: 2,
          employee_name: "Calin Cimpean",
          active_balance: 0,
          advance_total: 0,
          loan_total: 0,
          retention_total: 0,
          repayment_total: 0,
          compensation_total: 0,
          transaction_count: 0,
        },
      ],
    }),
    listTransactions: vi.fn().mockResolvedValue([]),
    createTransaction: vi.fn(),
    cancelTransaction: vi.fn(),
  },
}));

vi.mock("@/api/employeeAttendance", () => ({
  employeeAttendanceApi: {
    summary: vi.fn().mockResolvedValue({
      year: 2026,
      month: 6,
      standard_work_hours_per_day: 8,
      employees: [
        {
          employee_id: 1,
          employee_name: "Andrei Goghi",
          standard_work_days: 22,
          standard_hours: 176,
          present_days: 22,
          absent_days: 0,
          leave_days: 0,
          sick_days: 0,
          partial_days: 0,
          overtime_hours: 0,
          total_hours: 176,
          event_count: 0,
        planned_event_count: 0,
        cancelled_event_count: 0,
        },
        {
          employee_id: 2,
          employee_name: "Calin Cimpean",
          standard_work_days: 22,
          standard_hours: 176,
          present_days: 22,
          absent_days: 0,
          leave_days: 0,
          sick_days: 0,
          partial_days: 0,
          overtime_hours: 0,
          total_hours: 176,
          event_count: 0,
          planned_event_count: 0,
          cancelled_event_count: 0,
        },
      ],
    }),
    listEvents: vi.fn().mockResolvedValue([]),
    createEvent: vi.fn(),
    updateEvent: vi.fn(),
    deleteEvent: vi.fn(),
  },
}));

vi.mock("@/api/operationalRegistry", () => ({
  operationalRegistryApi: {
    getCatalog: vi.fn().mockResolvedValue({ skills: [], workcenters: [], resources: [] }),
    getEmployee: vi.fn(),
    updateEmployeeAuthorizations: vi.fn(),
  },
}));

vi.mock("@/features/operational-registry/EmployeeOperationalPanel", () => ({
  EmployeeOperationalPanel: () => <div data-testid="operational-panel">registry panel</div>,
}));

import Employees from "./Employees";
import EmployeesRecords from "./EmployeesRecords";
import Attendance from "./Attendance";
import EmployeePayments from "./EmployeePayments";
import EmployeeAdvances from "./EmployeeAdvances";

const LEGACY_DEMO_NAMES = [
  "Ion Popescu",
  "Mihai Ionescu",
  "Andrei Vasile",
  "Elena Dumitrescu",
  "Sorin Marin",
  "Dana Gheorghe",
];

describe("workforce routes", () => {
  it("/employees renders operational Employees page with LIVE DB badges", async () => {
    render(
      <MemoryRouter initialEntries={["/employees"]}>
        <Routes>
          <Route path="/employees" element={<Employees />} />
        </Routes>
      </MemoryRouter>
    );
    expect(await screen.findByRole("heading", { name: /Angajați operaționali/i })).toBeTruthy();
    expect(screen.getByText("LIVE DB")).toBeTruthy();
    expect(screen.getByText("OPERAȚIONAL")).toBeTruthy();
  });

  it("/employees-records uses live employee names, not legacy demo roster", async () => {
    render(
      <MemoryRouter initialEntries={["/employees-records"]}>
        <Routes>
          <Route path="/employees-records" element={<EmployeesRecords />} />
        </Routes>
      </MemoryRouter>
    );
    expect(await screen.findByRole("heading", { name: /Evidență internă HR/i })).toBeTruthy();
    expect(await screen.findByText("Andrei Goghi")).toBeTruthy();
    expect(await screen.findByText("Calin Cimpean")).toBeTruthy();
    for (const legacyName of LEGACY_DEMO_NAMES) {
      expect(screen.queryByText(legacyName)).toBeNull();
    }
  });

  it("/attendance lists live operational employees", async () => {
    render(
      <MemoryRouter initialEntries={["/attendance"]}>
        <Routes>
          <Route path="/attendance" element={<Attendance />} />
        </Routes>
      </MemoryRouter>
    );
    expect(await screen.findByRole("heading", { name: /^Pontaj$/i })).toBeTruthy();
    expect(screen.getByText("LIVE DB")).toBeTruthy();
    expect(await screen.findByText("Andrei Goghi")).toBeTruthy();
    expect(screen.queryByText("Ion Popescu")).toBeNull();
    expect(screen.queryByText(/^DEMO$/)).toBeNull();
  });

  it("/employee-payments shows live employee names in payment list", async () => {
    render(
      <MemoryRouter initialEntries={["/employee-payments"]}>
        <Routes>
          <Route path="/employee-payments" element={<EmployeePayments />} />
        </Routes>
      </MemoryRouter>
    );
    expect(await screen.findByRole("heading", { name: /Plăți angajați/i })).toBeTruthy();
    expect(await screen.findByText("Andrei Goghi")).toBeTruthy();
    expect(screen.getByText("DEMO")).toBeTruthy();
    expect(screen.getByText("Fără stat de plată fiscal")).toBeTruthy();
    expect(screen.queryByText("Ion Popescu")).toBeNull();
  });

  it("/employee-advances shows live employee names", async () => {
    render(
      <MemoryRouter initialEntries={["/employee-advances"]}>
        <Routes>
          <Route path="/employee-advances" element={<EmployeeAdvances />} />
        </Routes>
      </MemoryRouter>
    );
    expect(await screen.findByRole("heading", { name: /Avansuri \/ Datorii/i })).toBeTruthy();
    expect((await screen.findAllByText("Andrei Goghi")).length).toBeGreaterThan(0);
    expect(screen.getByText("LIVE DB")).toBeTruthy();
    expect(screen.getByText("MANUAL")).toBeTruthy();
    expect(screen.queryByText(/^DEMO$/)).toBeNull();
    expect(screen.queryByText("Mihai Ionescu")).toBeNull();
  });

  it("/personal redirects to /employees", () => {
    render(
      <MemoryRouter initialEntries={["/personal"]}>
        <Routes>
          <Route path="/personal" element={<Navigate to="/employees" replace />} />
          <Route path="/employees" element={<div>employees redirect target</div>} />
        </Routes>
      </MemoryRouter>
    );
    expect(screen.getByText("employees redirect target")).toBeTruthy();
  });
});

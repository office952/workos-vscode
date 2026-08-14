import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import Employees from "./Employees";
import EmployeesRecords from "./EmployeesRecords";
import EmployeeProfile from "./EmployeeProfile";

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

describe("Employee records honesty (S2)", () => {
  it("keeps /employees as the live master, not DEMO", async () => {
    render(
      <MemoryRouter initialEntries={["/employees"]}>
        <Routes>
          <Route path="/employees" element={<Employees />} />
        </Routes>
      </MemoryRouter>,
    );
    expect(await screen.findByRole("heading", { name: /Angajați operaționali/i })).toBeTruthy();
    expect(screen.getByText("LIVE DB")).toBeTruthy();
    expect(screen.getByText("OPERAȚIONAL")).toBeTruthy();
    expect(screen.queryByText(/^DEMO$/)).toBeNull();
  });

  it("keeps live employee names and a demo dossier boundary on the records list", async () => {
    render(
      <MemoryRouter initialEntries={["/employees-records"]}>
        <Routes>
          <Route path="/employees-records" element={<EmployeesRecords />} />
        </Routes>
      </MemoryRouter>,
    );
    expect(await screen.findByRole("heading", { name: /Evidență internă HR/i })).toBeTruthy();
    expect(await screen.findByText("Andrei Goghi")).toBeTruthy();
    expect(screen.getByText("DEMO")).toBeTruthy();
    expect(screen.getByText(/Identitatea angajaților este live/i)).toBeTruthy();
    expect(screen.getByText(/Alerte active \(demo\)/i)).toBeTruthy();
  });

  it("keeps live identity and a demo dossier boundary on the detail page", async () => {
    render(
      <MemoryRouter initialEntries={["/employees-records/1"]}>
        <Routes>
          <Route path="/employees-records/:employeeId" element={<EmployeeProfile />} />
        </Routes>
      </MemoryRouter>,
    );
    expect(await screen.findByRole("heading", { name: "Andrei Goghi" })).toBeTruthy();
    expect(screen.getByText("DEMO")).toBeTruthy();
    expect(screen.getByText(/Identitatea angajatului este live/i)).toBeTruthy();
    expect(screen.getByText(/Program demonstrativ/i)).toBeTruthy();
  });
});

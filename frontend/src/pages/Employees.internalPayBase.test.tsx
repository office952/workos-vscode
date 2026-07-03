import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Employees from "@/pages/Employees";

const { mockEmployees } = vi.hoisted(() => ({
  mockEmployees: [
    {
      id: 1,
      name: "Andrei Goghi",
      status: "active",
      employee_type: "productive",
      valid_for_cost_engine: true,
      cost_lunar_firma: 8500,
      monthly_internal_pay_amount: 4000,
      ore_productive_luna: 160,
      cost_ora_calculat: 53.125,
    },
  ],
}));

vi.mock("@/features/operational-registry/EmployeeOperationalPanel", () => ({
  EmployeeOperationalPanel: () => null,
}));

vi.mock("@/api/costEngine", () => ({
  employeesApi: {
    list: vi.fn().mockResolvedValue({ items: mockEmployees, total: 1 }),
    create: vi.fn(),
    update: vi.fn(),
    remove: vi.fn(),
  },
}));

function renderPage() {
  return render(
    <MemoryRouter>
      <Employees />
    </MemoryRouter>
  );
}

describe("Employees internal pay base UI", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows internal pay field and helper in create form", async () => {
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: /Adaugă angajat/i }));
    expect(
      screen.getByText(/Sumă lunară internă pentru plată/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        /Folosită ulterior pentru calculul tranșelor 15\/30 în Plăți angajați/i
      )
    ).toBeInTheDocument();
    expect(screen.getByText(/Cost lunar firmă/i)).toBeInTheDocument();
  });

  it("shows internal pay in detail panel when employee selected", async () => {
    renderPage();
    fireEvent.click(await screen.findByText("Andrei Goghi"));
    expect(
      screen.getAllByText(/Sumă lunară internă pentru plată/i).length
    ).toBeGreaterThan(0);
    expect(screen.getByText(/4\.000/)).toBeInTheDocument();
  });
});

import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";

const { mockLiveEmployees, mockSummary, mockCreateTransaction, mockCancelTransaction } = vi.hoisted(() => ({
  mockLiveEmployees: [
    {
      id: 1,
      name: "Andrei Goghi",
      status: "active",
      employee_type: "productive",
      valid_for_cost_engine: true,
      department: "Productie",
      role: "CNC",
    },
  ],
  mockSummary: {
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
    ],
  },
  mockCreateTransaction: vi.fn(),
  mockCancelTransaction: vi.fn(),
}));

vi.mock("@/api/costEngine", () => ({
  employeesApi: {
    list: vi.fn().mockResolvedValue({ items: mockLiveEmployees, total: mockLiveEmployees.length }),
  },
}));

vi.mock("@/api/employeeBalances", () => ({
  employeeBalancesApi: {
    summary: vi.fn().mockResolvedValue(mockSummary),
    listTransactions: vi.fn().mockResolvedValue([]),
    createTransaction: mockCreateTransaction,
    cancelTransaction: mockCancelTransaction,
  },
}));

import EmployeeAdvances from "./EmployeeAdvances";

describe("EmployeeAdvances page", () => {
  beforeEach(() => {
    mockCreateTransaction.mockReset();
    mockCreateTransaction.mockResolvedValue({ id: 1, status: "active" });
    mockCancelTransaction.mockReset();
    mockCancelTransaction.mockResolvedValue({ id: 1, status: "cancelled" });
  });

  it("afișează LIVE DB și nu DEMO", async () => {
    render(
      <MemoryRouter initialEntries={["/employee-advances"]}>
        <Routes>
          <Route path="/employee-advances" element={<EmployeeAdvances />} />
        </Routes>
      </MemoryRouter>
    );
    expect(await screen.findByRole("heading", { name: /Avansuri \/ Datorii/i })).toBeTruthy();
    expect(screen.getByText("LIVE DB")).toBeTruthy();
    expect(screen.queryByText(/^DEMO$/)).toBeNull();
    expect(screen.queryByText(/payroll fiscal/i)).toBeNull();
  });

  it("afișează angajat live în summary", async () => {
    render(
      <MemoryRouter initialEntries={["/employee-advances"]}>
        <Routes>
          <Route path="/employee-advances" element={<EmployeeAdvances />} />
        </Routes>
      </MemoryRouter>
    );
    expect(await screen.findByRole("heading", { name: /Sumar sold \/ angajat/i })).toBeTruthy();
    expect((await screen.findAllByText("Andrei Goghi")).length).toBeGreaterThan(0);
  });

  it("empty state când nu există tranzacții", async () => {
    render(
      <MemoryRouter initialEntries={["/employee-advances"]}>
        <Routes>
          <Route path="/employee-advances" element={<EmployeeAdvances />} />
        </Routes>
      </MemoryRouter>
    );
    expect(
      await screen.findByText(/Nu există avansuri, datorii sau rețineri active/i)
    ).toBeTruthy();
  });

  it("form Adaugă tranzacție are câmpuri obligatorii", async () => {
    render(
      <MemoryRouter initialEntries={["/employee-advances"]}>
        <Routes>
          <Route path="/employee-advances" element={<EmployeeAdvances />} />
        </Routes>
      </MemoryRouter>
    );
    await screen.findByRole("heading", { name: /Avansuri \/ Datorii/i });
    fireEvent.click(screen.getByRole("button", { name: /Adaugă tranzacție/i }));
    expect(screen.getByText("Tip tranzacție")).toBeTruthy();
    expect(screen.getByText("Dată")).toBeTruthy();
    expect(screen.getByText("Sumă")).toBeTruthy();
    expect(screen.getByText("Monedă")).toBeTruthy();
    expect(screen.getByText("Observații")).toBeTruthy();
  });

  it("submit create trimite API corect", async () => {
    render(
      <MemoryRouter initialEntries={["/employee-advances"]}>
        <Routes>
          <Route path="/employee-advances" element={<EmployeeAdvances />} />
        </Routes>
      </MemoryRouter>
    );
    await screen.findByRole("heading", { name: /Avansuri \/ Datorii/i });
    fireEvent.click(screen.getByRole("button", { name: /Adaugă tranzacție/i }));
    const amountInput = document.querySelector('input[type="number"]') as HTMLInputElement;
    fireEvent.change(amountInput, { target: { value: "500" } });
    fireEvent.click(screen.getByRole("button", { name: /^Salvează$/i }));
    await waitFor(() => expect(mockCreateTransaction).toHaveBeenCalled());
    const payload = mockCreateTransaction.mock.calls[0][0];
    expect(payload.employee_id).toBe(1);
    expect(payload.transaction_type).toBe("advance");
    expect(payload.amount).toBe(500);
    expect(payload.currency).toBe("RON");
  });
});

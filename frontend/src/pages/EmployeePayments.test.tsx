import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import EmployeePayments from "./EmployeePayments";
import type { EmployeePaymentEmployeeDTO, PaymentSituationDTO } from "@/api/employeePayments";

const { mockGetSituation, mockCreatePayment } = vi.hoisted(() => ({
  mockGetSituation: vi.fn(),
  mockCreatePayment: vi.fn(),
}));

vi.mock("@/api/employeePayments", () => ({
  employeePaymentsApi: {
    getSituation: mockGetSituation,
    createPayment: mockCreatePayment,
    cancelPayment: vi.fn(),
  },
}));

function slot(
  slotKey: "15" | "30",
  expected: number,
  paid = 0,
  status: "unpaid" | "partial" | "paid" | "missing_base" = "unpaid"
) {
  const remaining = Math.max(0, expected - paid);
  return {
    slot: slotKey,
    period_start: slotKey === "15" ? "2026-06-01" : "2026-06-16",
    period_end: slotKey === "15" ? "2026-06-15" : "2026-06-30",
    expected_amount: expected,
    paid_amount: paid,
    remaining_amount: remaining,
    status,
    breakdown: {
      base_amount: expected,
      attendance_adjustment: 0,
      overtime_amount: 0,
      advances_debts_deduction: 0,
      existing_payments: paid,
      suggested_deduction: 0,
    },
    warnings: [],
    history: paid > 0
      ? [
          {
            id: 1,
            amount_paid: paid,
            payment_date: "2026-06-11",
            status: "confirmed",
            cancelled: false,
          },
        ]
      : [],
  };
}

function employeeRow(
  partial: Partial<EmployeePaymentEmployeeDTO> & Pick<EmployeePaymentEmployeeDTO, "employee_id" | "employee_name" | "salary_monthly">
): EmployeePaymentEmployeeDTO {
  const salary = partial.salary_monthly;
  const missing = partial.missing_pay_base ?? (salary == null || salary <= 0);
  const slotExpected = missing ? 0 : salary! / 2;
  return {
    currency: "RON",
    base_source: "employee_profile_salary",
    warnings: missing ? ["missing_profile_salary"] : [],
    attendance_label: "OK — 22/22 zile",
    advances_debts_label: "Sold 0 RON",
    monthly_expected_amount: missing ? 0 : salary!,
    monthly_paid_amount: partial.monthly_paid_amount ?? 0,
    monthly_remaining_amount: partial.monthly_remaining_amount ?? (missing ? 0 : salary!),
    missing_pay_base: missing,
    salary_amount: salary,
    slots: partial.slots ?? {
      "15": slot("15", slotExpected, partial.slots?.["15"]?.paid_amount ?? 0),
      "30": slot("30", slotExpected),
    },
    ...partial,
  };
}

function baseSituation(overrides?: Partial<PaymentSituationDTO>): PaymentSituationDTO {
  const andrei = employeeRow({
    employee_id: 7,
    employee_name: "Andrei Goghi",
    salary_monthly: 8000,
    slots: { "15": slot("15", 4000), "30": slot("30", 4000) },
  });
  const vali = employeeRow({
    employee_id: 5,
    employee_name: "Vali Colantator",
    salary_monthly: 5000,
    slots: { "15": slot("15", 2500), "30": slot("30", 2500) },
  });
  const chirila = employeeRow({
    employee_id: 8,
    employee_name: "Chirila Cristian",
    salary_monthly: 7000,
    slots: { "15": slot("15", 3500), "30": slot("30", 3500) },
  });
  const noSalary = employeeRow({
    employee_id: 99,
    employee_name: "Zero Suma",
    salary_monthly: null,
    slots: { "15": slot("15", 0, 0, "missing_base"), "30": slot("30", 0, 0, "missing_base") },
  });

  return {
    year: 2026,
    month: 6,
    currency: "RON",
    summary: {
      expected_total: 19500,
      paid_total: 0,
      remaining_total: 19500,
      unpaid_count: 6,
      partial_count: 0,
      paid_count: 0,
    },
    employees: [andrei, vali, chirila, noSalary],
    ...overrides,
  };
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={["/employee-payments"]}>
      <Routes>
        <Route path="/employee-payments" element={<EmployeePayments />} />
      </Routes>
    </MemoryRouter>
  );
}

const FORBIDDEN_TERMS = [
  "compensation profile",
  "schedule-preview",
  "payment record",
  "CostEngine",
  "cost_lunar_firma",
  "payroll fiscal",
  "configurare profil",
  "Configurează bază internă",
  "Setează baza",
  "Setează suma lunară",
];

describe("EmployeePayments master-detail UI (live API)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetSituation.mockResolvedValue(baseSituation());
    mockCreatePayment.mockResolvedValue({ id: 99 });
  });

  it("renders master-detail layout and Live DB SourceBadge", async () => {
    renderPage();
    const sourceBadge = await screen.findByText("Live DB");
    expect(sourceBadge).toHaveAttribute("data-source", "db");
    expect(sourceBadge).toHaveAttribute("data-source-tone", "emerald");
    expect(screen.getByTestId("employee-payments-master-detail")).toBeTruthy();
  });

  it("shows Andrei 8000 as 4000 per slot", async () => {
    renderPage();
    const list = await screen.findByRole("region", { name: /Lista angajați tranșă/i });
    expect(within(list).getByRole("button", { name: /Andrei Goghi.*Calculat 4\.000 RON/i })).toBeTruthy();
  });

  it("shows Vali 5000 as 2500 per slot", async () => {
    renderPage();
    const list = await screen.findByRole("region", { name: /Lista angajați tranșă/i });
    expect(within(list).getByRole("button", { name: /Vali Colantator.*Calculat 2\.500 RON/i })).toBeTruthy();
  });

  it("shows Chirila 7000 as 3500 per slot", async () => {
    renderPage();
    const list = await screen.findByRole("region", { name: /Lista angajați tranșă/i });
    fireEvent.click(within(list).getByRole("button", { name: /Chirila Cristian/i }));
    const detail = screen.getByRole("complementary", { name: /Detalii angajat selectat/i });
    expect(within(detail).getAllByText("3.500 RON").length).toBeGreaterThan(0);
  });

  it("right panel form saves partial payment via POST and refetch", async () => {
    renderPage();
    const recordSection = await screen.findByRole("region", { name: /Înregistrare plată/i });
    fireEvent.change(within(recordSection).getByRole("spinbutton"), {
      target: { value: "100" },
    });
    fireEvent.click(within(recordSection).getByRole("button", { name: /Salvează plata/i }));

    await waitFor(() => {
      expect(mockCreatePayment).toHaveBeenCalledWith(
        expect.objectContaining({
          employee_id: 7,
          slot: "15",
          amount_paid: 100,
        })
      );
    });
    expect(mockGetSituation.mock.calls.length).toBeGreaterThan(1);
  });

  it("full payment marks slot as Plătit after refetch", async () => {
    const andrei = baseSituation().employees[0];
    mockGetSituation
      .mockResolvedValueOnce(baseSituation())
      .mockResolvedValueOnce(
        baseSituation({
          employees: [
            {
              ...andrei,
              monthly_paid_amount: 4000,
              monthly_remaining_amount: 4000,
              slots: {
                "15": slot("15", 4000, 4000, "paid"),
                "30": slot("30", 4000),
              },
            },
            ...baseSituation().employees.slice(1),
          ],
        })
      );

    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: /Andrei Goghi/i }));
    const detail = screen.getByRole("complementary", {
      name: /Detalii angajat selectat/i,
    });
    const recordSection = within(detail).getByRole("region", { name: /Înregistrare plată/i });
    fireEvent.change(within(recordSection).getByRole("spinbutton"), {
      target: { value: "4000" },
    });
    fireEvent.click(within(recordSection).getByRole("button", { name: /Salvează plata/i }));

    await waitFor(() => {
      expect(within(recordSection).getByText(/Tranșa este plătită/i)).toBeTruthy();
    });
  });

  it("shows warning only when profile salary missing", async () => {
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: /Zero Suma/i }));
    expect(
      screen.getByText(/Lipsește suma lunară în profilul angajatului/i)
    ).toBeTruthy();
  });

  it("does not show missing salary warning for Chirila with profile salary", async () => {
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: /Chirila Cristian/i }));
    expect(
      screen.queryByText(/Lipsește suma lunară în profilul angajatului/i)
    ).toBeNull();
  });

  it("does not show forbidden configuration or technical terms", async () => {
    renderPage();
    await screen.findByRole("heading", { name: /Plăți angajați/i });
    const bodyText = document.body.textContent ?? "";
    for (const term of FORBIDDEN_TERMS) {
      expect(bodyText.toLowerCase()).not.toContain(term.toLowerCase());
    }
  });
});

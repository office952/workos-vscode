import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";
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
  status: "unpaid" | "partial" | "paid" | "missing_base" = "unpaid",
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
    history: [],
  };
}

function employeeRow(
  partial: Partial<EmployeePaymentEmployeeDTO> &
    Pick<EmployeePaymentEmployeeDTO, "employee_id" | "employee_name" | "salary_monthly">,
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
    employees: [
      employeeRow({
        employee_id: 7,
        employee_name: "Andrei Goghi",
        salary_monthly: 8000,
        slots: { "15": slot("15", 4000), "30": slot("30", 4000) },
      }),
      employeeRow({
        employee_id: 99,
        employee_name: "Zero Suma",
        salary_monthly: null,
        slots: {
          "15": slot("15", 0, 0, "missing_base"),
          "30": slot("30", 0, 0, "missing_base"),
        },
      }),
    ],
    ...overrides,
  };
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={["/employee-payments"]}>
      <Routes>
        <Route path="/employee-payments" element={<EmployeePayments />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("EmployeePayments design-system badges", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetSituation.mockResolvedValue(baseSituation());
    mockCreatePayment.mockResolvedValue({ id: 99 });
  });

  it("renders SourceBadge with Live DB on successful live fixture", async () => {
    renderPage();
    const badge = await screen.findByText("Live DB");
    expect(badge).toHaveAttribute("data-source", "db");
    expect(badge).toHaveAttribute("data-source-tone", "emerald");
  });

  it("renders unpaid and partial payment statuses with preserved Romanian labels", async () => {
    mockGetSituation.mockResolvedValue(
      baseSituation({
        employees: [
          employeeRow({
            employee_id: 7,
            employee_name: "Andrei Goghi",
            salary_monthly: 8000,
            slots: {
              "15": slot("15", 4000, 1000, "partial"),
              "30": slot("30", 4000),
            },
          }),
          employeeRow({
            employee_id: 8,
            employee_name: "Chirila Cristian",
            salary_monthly: 7000,
            slots: { "15": slot("15", 3500), "30": slot("30", 3500) },
          }),
        ],
      }),
    );

    renderPage();
    const list = await screen.findByRole("region", { name: /Lista angajați tranșă/i });
    const andreiRow = within(list).getByRole("button", { name: /Andrei Goghi/i });
    const partialBadge = within(andreiRow).getByText("Parțial");
    expect(partialBadge).toHaveAttribute("data-status-domain", "payment");
    expect(partialBadge).toHaveAttribute("data-status-tone", "orange");

    const chirilaRow = within(list).getByRole("button", { name: /Chirila Cristian/i });
    const unpaidBadge = within(chirilaRow).getByText("Neplătit");
    expect(unpaidBadge).toHaveAttribute("data-status-tone", "amber");
  });

  it("shows missing salary warning without crash and keeps save action for valid employee", async () => {
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: /Zero Suma/i }));
    expect(
      screen.getByText(/Lipsește suma lunară în profilul angajatului/i),
    ).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: /Andrei Goghi/i }));
    const recordSection = screen.getByRole("region", { name: /Înregistrare plată/i });
    expect(
      within(recordSection).getByRole("button", { name: /Salvează plata/i }),
    ).toBeTruthy();
  });

  it("does not show mock/demo source badge on live fixture", async () => {
    renderPage();
    await screen.findByText("Live DB");
    expect(screen.queryByText("Mock Data")).toBeNull();
    expect(screen.queryByText("Demo")).toBeNull();
  });

  it("keeps displayed slot amounts unchanged in live fixture", async () => {
    renderPage();
    const list = await screen.findByRole("region", { name: /Lista angajați tranșă/i });
    expect(
      within(list).getByRole("button", { name: /Andrei Goghi.*Calculat 4\.000 RON/i }),
    ).toBeTruthy();
  });
});

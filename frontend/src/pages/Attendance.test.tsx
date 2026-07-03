import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";

const { mockLiveEmployees, mockSummary, mockCreateEvent } = vi.hoisted(() => ({
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
    ],
  },
  mockCreateEvent: vi.fn(),
}));

vi.mock("@/api/costEngine", () => ({
  employeesApi: {
    list: vi.fn().mockResolvedValue({ items: mockLiveEmployees, total: mockLiveEmployees.length }),
  },
}));

vi.mock("@/api/employeeAttendance", () => ({
  employeeAttendanceApi: {
    summary: vi.fn().mockResolvedValue(mockSummary),
    listEvents: vi.fn().mockResolvedValue([]),
    createEvent: mockCreateEvent,
    updateEvent: vi.fn(),
    deleteEvent: vi.fn(),
  },
}));

import Attendance from "./Attendance";

describe("Attendance page (events)", () => {
  beforeEach(() => {
    mockCreateEvent.mockReset();
    mockCreateEvent.mockResolvedValue({
      id: 1,
      employee_id: 1,
      start_date: "2026-06-15",
      end_date: "2026-06-19",
      event_type: "leave",
      event_status: "planned",
      source: "manual",
    });
  });

  it("afișează mesaj default present / excepții", async () => {
    render(
      <MemoryRouter initialEntries={["/attendance"]}>
        <Routes>
          <Route path="/attendance" element={<Attendance />} />
        </Routes>
      </MemoryRouter>
    );
    expect(await screen.findByRole("heading", { name: /^Pontaj$/i })).toBeTruthy();
    expect(screen.getByText("LIVE DB")).toBeTruthy();
    expect(
      screen.getByText(/considerați prezenți implicit conform programului standard/i)
    ).toBeTruthy();
    expect(screen.queryByText(/^DEMO$/)).toBeNull();
    expect(screen.queryByText(/payroll fiscal/i)).toBeNull();
  });

  it("empty state — nicio excepție", async () => {
    render(
      <MemoryRouter initialEntries={["/attendance"]}>
        <Routes>
          <Route path="/attendance" element={<Attendance />} />
        </Routes>
      </MemoryRouter>
    );
    expect(
      await screen.findByText(/Toți angajații activi sunt considerați prezenți conform programului standard/i)
    ).toBeTruthy();
  });

  it("form are start date, end date și status", async () => {
    render(
      <MemoryRouter initialEntries={["/attendance"]}>
        <Routes>
          <Route path="/attendance" element={<Attendance />} />
        </Routes>
      </MemoryRouter>
    );
    await screen.findByText("Andrei Goghi");
    fireEvent.click(screen.getAllByRole("button", { name: /Adaugă eveniment/i })[0]);
    expect(screen.getByText("Dată start")).toBeTruthy();
    expect(screen.getByText("Dată finală")).toBeTruthy();
    expect(screen.getByText("Status")).toBeTruthy();
  });

  it("leave trimite range și status planned", async () => {
    render(
      <MemoryRouter initialEntries={["/attendance"]}>
        <Routes>
          <Route path="/attendance" element={<Attendance />} />
        </Routes>
      </MemoryRouter>
    );
    await screen.findByText("Andrei Goghi");
    fireEvent.click(screen.getAllByRole("button", { name: /Adaugă eveniment/i })[0]);
    fireEvent.change(screen.getByLabelText(/Tip eveniment/i) || screen.getAllByRole("combobox")[0], {
      target: { value: "leave" },
    });
    const selects = document.querySelectorAll("select");
    fireEvent.change(selects[1], { target: { value: "leave" } });
    fireEvent.change(selects[2], { target: { value: "planned" } });
    const dateInputs = document.querySelectorAll('input[type="date"]');
    fireEvent.change(dateInputs[0], { target: { value: "2026-06-15" } });
    fireEvent.change(dateInputs[1], { target: { value: "2026-06-19" } });
    fireEvent.click(screen.getByRole("button", { name: /^Salvează$/i }));
    await waitFor(() => expect(mockCreateEvent).toHaveBeenCalled());
    const payload = mockCreateEvent.mock.calls[0][0];
    expect(payload.event_type).toBe("leave");
    expect(payload.event_status).toBe("planned");
    expect(payload.start_date).toBe("2026-06-15");
    expect(payload.end_date).toBe("2026-06-19");
  });

  it("overtime form afișează câmp delta", async () => {
    render(
      <MemoryRouter initialEntries={["/attendance"]}>
        <Routes>
          <Route path="/attendance" element={<Attendance />} />
        </Routes>
      </MemoryRouter>
    );
    await screen.findByText("Andrei Goghi");
    fireEvent.click(screen.getAllByRole("button", { name: /Adaugă eveniment/i })[0]);
    const selects = document.querySelectorAll("select");
    fireEvent.change(selects[1], { target: { value: "overtime" } });
    expect(screen.getByPlaceholderText(/ore suplimentare/i)).toBeTruthy();
  });
});

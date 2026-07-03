import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import EmployeeAttendanceEffects from "./EmployeeAttendanceEffects";
import type {
  AttendanceEffectDTO,
  AttendanceEffectGenerationCandidateDTO,
} from "@/api/employeeAttendance";

const mockFetch = vi.fn();

const candidate: AttendanceEffectGenerationCandidateDTO = {
  employee_request_id: 10,
  employee_id: 5,
  employee_name: "Ion Popescu",
  request_type: "leave",
  status: "approved",
  title: "Concediu",
  start_date: "2026-07-01",
  end_date: "2026-07-05",
  has_effect: false,
};

const pendingEffect: AttendanceEffectDTO = {
  id: 1,
  employee_request_id: 10,
  employee_id: 5,
  request_type: "leave",
  effect_type: "leave_range",
  status: "pending",
  date_start: "2026-07-01",
  date_end: "2026-07-05",
  generated_by_user_id: "gen-user",
  source: "employee_request",
};

const appliedEffect: AttendanceEffectDTO = {
  ...pendingEffect,
  id: 2,
  status: "applied",
  applied_at: "2026-06-14T10:00:00+00:00",
};

const conflictEffect: AttendanceEffectDTO = {
  ...pendingEffect,
  id: 3,
  status: "conflict",
  conflict_reason: "overlap:sick",
};

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

beforeEach(() => {
  vi.stubGlobal("fetch", mockFetch);
  mockFetch.mockReset();
  vi.stubGlobal("confirm", vi.fn(() => true));
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("EmployeeAttendanceEffects console", () => {
  it("renders generation candidates section on De generat tab", async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse([candidate]));

    render(
      <MemoryRouter>
        <EmployeeAttendanceEffects />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("attendance-effects-candidates-section")).toBeInTheDocument();
    });
    expect(screen.getByText(/Generarea pregătește efectul de pontaj/)).toBeInTheDocument();
    expect(screen.getByTestId("attendance-effect-generate-10")).toBeInTheDocument();
  });

  it("generate button calls API and does not call apply", async () => {
    mockFetch
      .mockResolvedValueOnce(jsonResponse([candidate]))
      .mockResolvedValueOnce(jsonResponse({ ...pendingEffect, already_exists: false }, 201))
      .mockResolvedValueOnce(jsonResponse([]))
      .mockResolvedValueOnce(jsonResponse([pendingEffect]));

    render(
      <MemoryRouter>
        <EmployeeAttendanceEffects />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("attendance-effect-generate-10")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("attendance-effect-generate-10"));

    await waitFor(() => {
      expect(screen.getByTestId("attendance-effects-success")).toHaveTextContent(/Efect generat/);
    });

    const postCalls = mockFetch.mock.calls.filter(
      (call) => (call[1] as RequestInit | undefined)?.method === "POST",
    );
    expect(postCalls).toHaveLength(1);
    expect(String(postCalls[0][0])).toContain("/effects/generate");
    expect(String(postCalls[0][0])).not.toContain("/apply");
  });

  it("shows apply button only for pending effects on Efecte tab", async () => {
    mockFetch
      .mockResolvedValueOnce(jsonResponse([]))
      .mockResolvedValueOnce(jsonResponse([pendingEffect, appliedEffect, conflictEffect]));

    render(
      <MemoryRouter>
        <EmployeeAttendanceEffects />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("attendance-effects-tab-effects")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("attendance-effects-tab-effects"));

    await waitFor(() => {
      expect(screen.getByTestId("attendance-effects-list")).toBeInTheDocument();
    });

    expect(screen.getByTestId("attendance-effect-apply-1")).toBeInTheDocument();
    expect(screen.queryByTestId("attendance-effect-apply-2")).not.toBeInTheDocument();
    expect(screen.queryByTestId("attendance-effect-apply-3")).not.toBeInTheDocument();
  });

  it("refreshes list after successful apply", async () => {
    mockFetch
      .mockResolvedValueOnce(jsonResponse([]))
      .mockResolvedValueOnce(jsonResponse([pendingEffect]))
      .mockResolvedValueOnce(
        jsonResponse({
          effect_id: 1,
          employee_id: 5,
          effect_status: "applied",
          attendance_event_id: 99,
          already_applied: false,
        }),
      )
      .mockResolvedValueOnce(jsonResponse([appliedEffect]));

    render(
      <MemoryRouter>
        <EmployeeAttendanceEffects />
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByTestId("attendance-effects-tab-effects"));

    await waitFor(() => {
      expect(screen.getByTestId("attendance-effect-apply-1")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("attendance-effect-apply-1"));

    await waitFor(() => {
      expect(screen.getByTestId("attendance-effects-success")).toHaveTextContent(/Efect aplicat/);
    });
  });

  it("shows forbidden message on 403 candidates error", async () => {
    mockFetch.mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: "Forbidden" }), { status: 403 }),
    );

    render(
      <MemoryRouter>
        <EmployeeAttendanceEffects />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("attendance-effects-error")).toHaveTextContent(/Acces refuzat/);
    });
  });

  it("shows human message on generate 422", async () => {
    mockFetch
      .mockResolvedValueOnce(jsonResponse([candidate]))
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: "Only approved employee requests" }), {
          status: 422,
        }),
      );

    render(
      <MemoryRouter>
        <EmployeeAttendanceEffects />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("attendance-effect-generate-10")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("attendance-effect-generate-10"));

    await waitFor(() => {
      expect(screen.getByTestId("attendance-effects-error")).toHaveTextContent(
        /nu poate genera efect/i,
      );
    });
  });
});

describe("Employee Mobile PWA manifest", () => {
  it("keeps start_url at /employee-app", () => {
    const manifestPath = resolve(process.cwd(), "public/manifest.webmanifest");
    const manifest = JSON.parse(readFileSync(manifestPath, "utf-8")) as { start_url?: string };
    expect(manifest.start_url).toBe("/employee-app");
  });
});

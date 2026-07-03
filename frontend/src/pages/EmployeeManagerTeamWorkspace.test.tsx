import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import EmployeeManagerTeamWorkspace from "./EmployeeManagerTeamWorkspace";

const mockFetch = vi.fn();

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function renderTeam(path = "/employee-app/team") {
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/employee-app/team" element={<EmployeeManagerTeamWorkspace />} />
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  vi.stubGlobal("fetch", mockFetch);
  mockFetch.mockReset();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("EmployeeManagerTeamWorkspace", () => {
  it("renders manager workspace with read-only guard", async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse([]));

    renderTeam();

    expect(screen.getByTestId("employee-manager-team-workspace")).toBeInTheDocument();
    expect(screen.getByText("Echipa mea")).toBeInTheDocument();
    expect(screen.getByTestId("employee-manager-team-subtitle")).toHaveTextContent(
      /raportează direct/i,
    );
    expect(screen.getByTestId("employee-manager-team-readonly-guard")).toHaveTextContent(
      /doar pentru vizualizare/i,
    );
    expect(screen.getByTestId("employee-manager-team-tab-attendance")).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByTestId("employee-manager-team-attendance-empty")).toBeInTheDocument();
    });
  });

  it("shows read-only badge on attendance tab", async () => {
    mockFetch.mockResolvedValueOnce(
      jsonResponse([
        {
          id: 1,
          employee_id: 2,
          employee_name: "Worker One",
          start_date: "2026-06-10",
          end_date: "2026-06-10",
          event_type: "leave",
          event_status: "approved",
          source: "manual",
        },
      ]),
    );

    renderTeam();

    await waitFor(() => {
      expect(screen.getByTestId("employee-manager-team-attendance-list")).toBeInTheDocument();
    });
    expect(screen.getByText("Read-only")).toBeInTheDocument();
    expect(screen.queryByText(/Șterge/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Adaugă/i)).not.toBeInTheDocument();
  });

  it("loads team requests on requests tab", async () => {
    mockFetch
      .mockResolvedValueOnce(jsonResponse([]))
      .mockResolvedValueOnce(
        jsonResponse([
          {
            id: 5,
            employee_id: 3,
            employee_name: "Worker Two",
            request_type: "leave",
            status: "submitted",
            title: "Concediu",
            start_date: "2026-06-01",
            end_date: "2026-06-05",
            employee_status: "active",
          },
        ]),
      );

    renderTeam();
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalled();
    });

    fireEvent.click(screen.getByTestId("employee-manager-team-tab-requests"));

    await waitFor(() => {
      expect(screen.getByTestId("employee-manager-team-requests-list")).toBeInTheDocument();
    });
    expect(screen.getByText("Worker Two")).toBeInTheDocument();
    expect(screen.getByTestId("employee-manager-team-request-review-5")).toHaveAttribute(
      "href",
      "/employee-app/review",
    );
  });

  it("shows human 403 message", async () => {
    mockFetch.mockResolvedValueOnce(
      jsonResponse(
        {
          detail: {
            error: "manager_team_reader_required",
            message: "Manager team workspace requires role 'admin' or 'manager'.",
          },
        },
        403,
      ),
    );

    renderTeam();

    await waitFor(() => {
      expect(screen.getByTestId("employee-manager-team-attendance-error")).toHaveTextContent(
        /Nu ai acces la vizualizarea echipei sau contul tău nu este configurat ca manager/i,
      );
    });
  });

  it("shows empty requests state", async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse([])).mockResolvedValueOnce(jsonResponse([]));

    renderTeam();
    fireEvent.click(screen.getByTestId("employee-manager-team-tab-requests"));

    await waitFor(() => {
      expect(screen.getByTestId("employee-manager-team-requests-empty")).toHaveTextContent(
        /Nu ai angajați alocați ca raportare directă/i,
      );
    });
  });
});

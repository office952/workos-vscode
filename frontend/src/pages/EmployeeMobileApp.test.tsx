import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import EmployeeMobileApp, { EMPLOYEE_MOBILE_SECTIONS } from "./EmployeeMobileApp";
import {
  buildEmployeeRequestCreatePayload,
  type EmployeeRequestDTO,
} from "@/api/employeeMobileRequests";

const authMock = vi.hoisted(() => ({
  user: {
    name: "Angajat Test",
    email: "angajat@workos.local",
    role: "employee_mobile",
  },
  loading: false,
  isAuthenticated: true,
  authState: "authenticated" as const,
  canAccessProtectedApi: true,
  devAuthEnabled: false,
  logout: vi.fn(),
  login: vi.fn(),
}));

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: () => authMock,
}));

const mockFetch = vi.fn();

function renderShell(initialPath = "/employee-app") {
  render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route path="/employee-app/*" element={<EmployeeMobileApp />} />
      </Routes>
    </MemoryRouter>,
  );
}

function clickTaskCard(taskId: string) {
  const cta = screen.queryByTestId(`employee-mobile-task-card-cta-${taskId}`);
  fireEvent.click(cta ?? screen.getByTestId(`employee-mobile-task-card-${taskId}`));
}

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function mockPipelineBlueprint() {
  return {
    order_id: 1,
    order_label: "ORD-1781201059-1",
    client_label: "E2E Commercial Spine Client",
    summary: {
      total_tasks: 4,
      my_tasks: 2,
      my_done: 0,
      overall_progress_percent: 9,
      my_progress_percent: 0,
      blocked: 0,
      in_progress: 0,
    },
    current_task_id: "T-004",
    tasks: [
      {
        task_id: "T-003",
        name: "Modelare canturi litere volumetrice",
        status_display: "Neatribuit",
        is_mine: false,
        is_current: false,
        stage_label: "Pregătire / Canturi",
        has_documents: true,
        has_instructions: true,
        readiness_status: "unassigned",
        readiness_label: "Neatribuit",
        is_startable: false,
        blocking_tasks: [],
      },
      {
        task_id: "T-004",
        name: "Lipire canturi pe fețele literelor",
        status_display: "În lucru",
        is_mine: true,
        is_current: true,
        is_eligible_for_me: true,
        stage_label: "Asamblare",
        has_documents: true,
        has_instructions: true,
        readiness_status: "in_progress",
        readiness_label: "În lucru",
        is_startable: false,
        dependency_warning: "A pornit înainte de finalizarea dependențelor",
        blocking_tasks: [{ task_id: "T-003", name: "Modelare canturi litere volumetrice" }],
      },
      {
        task_id: "T-006",
        name: "Montaj LED",
        status_display: "Alocat",
        is_mine: true,
        is_current: false,
        stage_label: "Asamblare",
        has_documents: true,
        has_instructions: false,
        readiness_status: "waiting_predecessor",
        readiness_label: "Așteaptă task anterior",
        is_startable: false,
        blocking_tasks: [{ task_id: "T-005", name: "Debitare spate Forex" }],
        material_hints: [
          {
            name: "Module LED",
            category: "project_critical",
            label: "Verifică material",
            display_note: "Verifică disponibilitatea modulelor LED înainte de montaj.",
          },
        ],
      },
    ],
  };
}

function mockSanduPipelineTasks() {
  return [
    {
      task_id: "T-004",
      order_id: 1,
      order_code: "ORD-1781201059-1",
      title: "Lipire canturi pe fețele literelor",
      status: "in_progress",
      readiness_status: "in_progress",
      dependency_warning: "A pornit înainte de finalizarea dependențelor",
      blocking_tasks: [{ task_id: "T-003", name: "Modelare canturi litere volumetrice" }],
    },
    {
      task_id: "T-006",
      order_id: 1,
      order_code: "ORD-1781201059-1",
      title: "Montaj LED",
      status: "assigned",
      readiness_status: "waiting_predecessor",
      readiness_label: "Așteaptă task anterior",
      is_startable: false,
      blocking_tasks: [{ task_id: "T-005", name: "Debitare spate Forex" }],
    },
  ];
}

const submittedLeave: EmployeeRequestDTO = {
  id: 1,
  employee_id: 10,
  request_type: "leave",
  status: "submitted",
  title: "Concediu vară",
  start_date: "2026-07-01",
  end_date: "2026-07-05",
  submitted_at: "2026-06-13T10:00:00+00:00",
};

const approvedAdvance: EmployeeRequestDTO = {
  id: 2,
  employee_id: 10,
  request_type: "advance",
  status: "approved",
  title: "Avans iunie",
  amount: 500,
  currency: "RON",
};

beforeEach(() => {
  vi.stubGlobal("fetch", mockFetch);
  mockFetch.mockReset();
  mockFetch.mockImplementation(() => Promise.resolve(jsonResponse([])));
  authMock.user = {
    name: "Angajat Test",
    email: "angajat@workos.local",
    role: "employee_mobile",
  };
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("EmployeeMobileApp shell", () => {
  it("renders standalone shell markers without desktop sidebar test ids", async () => {
    mockFetch
      .mockResolvedValueOnce(jsonResponse([]))
      .mockResolvedValueOnce(jsonResponse([]));

    renderShell();

    expect(screen.getByTestId("employee-mobile-shell")).toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-bottom-nav")).toBeInTheDocument();
    expect(screen.queryByTestId("workos-sidebar")).not.toBeInTheDocument();
    expect(screen.queryByTestId("workos-desktop-shell")).not.toBeInTheDocument();
  });

  it("renders compact header, operational home, secondary cards, and simplified bottom nav", async () => {
    renderShell();

    expect(screen.getByTestId("employee-mobile-shell")).toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-header")).toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-subtitle")).toHaveTextContent(
      /Producție/i,
    );
    expect(screen.queryByTestId("employee-mobile-same-account-hint")).not.toBeInTheDocument();
    expect(screen.queryByText("WorkOS Employee")).not.toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-bottom-nav")).toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-nav-home")).toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-nav-tasks")).toHaveAttribute(
      "href",
      "/employee-app/tasks",
    );
    expect(screen.getByTestId("employee-mobile-nav-personal")).toHaveAttribute(
      "href",
      "/employee-app/personal",
    );
    expect(screen.queryByTestId("employee-mobile-nav-requests")).not.toBeInTheDocument();
    expect(screen.queryByTestId("employee-mobile-nav-attendance")).not.toBeInTheDocument();
    expect(screen.queryByTestId("employee-mobile-nav-review")).not.toBeInTheDocument();
    expect(screen.queryByTestId("employee-mobile-dashboard-requests")).not.toBeInTheDocument();
    expect(screen.queryByTestId("employee-mobile-dashboard-attendance")).not.toBeInTheDocument();
    expect(screen.queryByTestId("employee-mobile-dashboard-review")).not.toBeInTheDocument();
    expect(screen.queryByTestId("employee-mobile-install-card")).not.toBeInTheDocument();
    expect(screen.queryByTestId("employee-mobile-account-panel")).not.toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-home-hero")).toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-home-module-grid")).toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-home-secondary")).toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-home-module-personal")).toHaveAttribute(
      "href",
      "/employee-app/personal",
    );
    expect(screen.getByTestId("employee-mobile-home-info")).toHaveAttribute(
      "href",
      "/employee-app/info",
    );
    expect(screen.queryByTestId("employee-mobile-home-admin")).not.toBeInTheDocument();
    expect(screen.queryByTestId("employee-mobile-home-intro")).not.toBeInTheDocument();
    expect(screen.queryByTestId("employee-mobile-home-today")).not.toBeInTheDocument();
    expect(screen.queryByTestId("employee-mobile-home-orders-empty")).not.toBeInTheDocument();
  });

  it("shows minimal now card with assigned task on home", async () => {
    mockFetch.mockImplementation((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/employee-mobile/tasks")) {
        return Promise.resolve(
          jsonResponse([
            {
              task_id: "T-001",
              order_id: 1,
              order_code: "ORD-1",
              title: "Tăiere CNC",
              status: "assigned",
              assigned_employee_id: 1,
            },
          ]),
        );
      }
      return Promise.resolve(jsonResponse([]));
    });

    renderShell();

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-home-hero-task")).toBeInTheDocument();
    });
    expect(screen.queryByText("Recomandat acum")).not.toBeInTheDocument();
    expect(screen.queryByText("Pe scurt")).not.toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-home-hero-status")).toHaveTextContent("Pregătit");
    expect(screen.getByTestId("employee-mobile-home-hero-task")).toHaveTextContent("Tăiere CNC");
    expect(screen.getByTestId("employee-mobile-home-hero-cta")).toHaveAttribute(
      "href",
      "/employee-app/tasks?view=all&taskId=T-001&orderId=1",
    );
    expect(screen.getByTestId("employee-mobile-home-module-tasks")).toHaveAttribute(
      "href",
      "/employee-app/tasks?view=all",
    );
    expect(screen.getByTestId("employee-mobile-home-module-pipeline")).toHaveAttribute(
      "href",
      "/employee-app/tasks?view=pipeline",
    );
    expect(screen.getByTestId("employee-mobile-home-module-documents")).toHaveAttribute(
      "href",
      "/employee-app/tasks/orders/1/blueprint",
    );
  });

  it("renders compact tasks workspace with tabs from query view", async () => {
    mockFetch.mockImplementation((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/employee-mobile/tasks")) {
        return Promise.resolve(
          jsonResponse([
            {
              task_id: "T-001",
              order_id: 1,
              title: "Tăiere CNC",
              status: "assigned",
            },
          ]),
        );
      }
      return Promise.resolve(jsonResponse([]));
    });

    renderShell("/employee-app/tasks?view=blocked");

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-tasks-tabs")).toBeInTheDocument();
    });
    expect(screen.queryByTestId("employee-mobile-tasks-tabs-secondary")).not.toBeInTheDocument();
    expect(screen.queryByTestId("employee-mobile-tasks-view-description")).not.toBeInTheDocument();
    expect(screen.queryByTestId("employee-mobile-tasks-summary")).not.toBeInTheDocument();
    fireEvent.click(screen.getByTestId("employee-mobile-tasks-tab-more"));
    expect(screen.getByTestId("employee-mobile-tasks-tab-blocked")).toBeInTheDocument();
  });

  it("hides empty instruction and document sections in task detail", async () => {
    mockFetch.mockImplementation((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/employee-mobile/tasks")) {
        return Promise.resolve(
          jsonResponse([
            {
              task_id: "T-001",
              order_id: 1,
              title: "Montaj LED",
              status: "assigned",
            },
          ]),
        );
      }
      return Promise.resolve(jsonResponse([]));
    });

    renderShell("/employee-app/tasks?view=all");

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-task-card-T-001")).toBeInTheDocument();
    });

    clickTaskCard("T-001");

    expect(screen.queryByTestId("employee-mobile-task-instructions")).not.toBeInTheDocument();
    expect(screen.queryByTestId("employee-mobile-task-documents")).not.toBeInTheDocument();
  });

  it("shows documents list with open link only when url exists", async () => {
    mockFetch.mockImplementation((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/employee-mobile/tasks")) {
        return Promise.resolve(
          jsonResponse([
            {
              task_id: "T-006",
              order_id: 1,
              title: "Montaj LED",
              status: "assigned",
              instructions: "Verifică polaritatea LED.",
              documents: [
                {
                  id: "doc-1",
                  name: "Schiță LED",
                  type: "pdf",
                  url: "https://example.com/sketch.pdf",
                  source: "task",
                },
                {
                  id: "doc-2",
                  name: "Plan fără URL",
                  type: "metadata",
                  source: "dev_fixture",
                },
              ],
            },
          ]),
        );
      }
      return Promise.resolve(jsonResponse([]));
    });

    renderShell("/employee-app/tasks?view=all");

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-task-card-T-006")).toBeInTheDocument();
    });

    clickTaskCard("T-006");

    expect(screen.getByTestId("employee-mobile-task-instructions-content")).toHaveTextContent(
      /Verifică polaritatea LED/,
    );
    expect(screen.getByTestId("employee-mobile-task-documents-list")).toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-task-document-open-doc-1")).toHaveAttribute(
      "href",
      "https://example.com/sketch.pdf",
    );
    expect(screen.queryByTestId("employee-mobile-task-document-open-doc-2")).not.toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-task-document-meta-doc-2")).toHaveTextContent(
      /fără link mobil momentan/i,
    );
  });

  it("rejects empty clarification message before submit", async () => {
    mockFetch.mockImplementation((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/employee-mobile/tasks")) {
        return Promise.resolve(
          jsonResponse([
            {
              task_id: "T-006",
              order_id: 1,
              title: "Montaj LED",
              status: "assigned",
            },
          ]),
        );
      }
      return Promise.resolve(jsonResponse([]));
    });

    renderShell("/employee-app/tasks?view=all");

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-task-card-T-006")).toBeInTheDocument();
    });
    clickTaskCard("T-006");
    fireEvent.click(screen.getByTestId("employee-mobile-task-clarification-open-form"));

    expect(screen.getByTestId("employee-mobile-task-clarification-submit")).toBeDisabled();

    fireEvent.change(screen.getByTestId("employee-mobile-task-clarification-message"), {
      target: { value: "   " },
    });
    expect(screen.getByTestId("employee-mobile-task-clarification-submit")).toBeDisabled();
  });

  it("shows clarification panel and submits request", async () => {
    mockFetch.mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes("/employee-mobile/tasks/T-006/clarification-requests") && init?.method === "POST") {
        return Promise.resolve(
          jsonResponse({
            id: 7,
            order_id: 1,
            task_id: "T-006",
            employee_id: 4,
            message: "Schița nu este clară.",
            status: "open",
          }),
        );
      }
      if (url.includes("/employee-mobile/tasks")) {
        return Promise.resolve(
          jsonResponse([
            {
              task_id: "T-006",
              order_id: 1,
              title: "Montaj LED",
              status: "assigned",
            },
          ]),
        );
      }
      return Promise.resolve(jsonResponse([]));
    });

    renderShell("/employee-app/tasks?view=all");

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-task-card-T-006")).toBeInTheDocument();
    });
    clickTaskCard("T-006");

    expect(screen.getByTestId("employee-mobile-task-clarification")).toBeInTheDocument();
    fireEvent.click(screen.getByTestId("employee-mobile-task-clarification-open-form"));
    fireEvent.change(screen.getByTestId("employee-mobile-task-clarification-message"), {
      target: { value: "Schița nu este clară." },
    });
    fireEvent.click(screen.getByTestId("employee-mobile-task-clarification-submit"));

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-task-clarification-success")).toHaveTextContent(
        /Solicitarea a fost trimisă/i,
      );
    });
  });

  it("shows open clarification status in task detail", async () => {
    mockFetch.mockImplementation((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/employee-mobile/tasks")) {
        return Promise.resolve(
          jsonResponse([
            {
              task_id: "T-006",
              order_id: 1,
              title: "Montaj LED",
              status: "assigned",
              clarification_request: {
                id: 3,
                order_id: 1,
                task_id: "T-006",
                employee_id: 4,
                message: "Lipsește documentul.",
                status: "open",
              },
            },
          ]),
        );
      }
      return Promise.resolve(jsonResponse([]));
    });

    renderShell("/employee-app/tasks?view=all");

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-task-card-T-006")).toBeInTheDocument();
    });
    clickTaskCard("T-006");

    expect(screen.getByTestId("employee-mobile-task-clarification-open")).toHaveTextContent(
      /Solicitare de informații trimisă/i,
    );
    expect(
      screen.queryByTestId("employee-mobile-task-clarification-open-form"),
    ).not.toBeInTheDocument();
  });

  it("shows intake work file document with Deschide link", async () => {
    mockFetch.mockImplementation((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/employee-mobile/tasks")) {
        return Promise.resolve(
          jsonResponse([
            {
              task_id: "T-006",
              order_id: 1,
              title: "Montaj LED",
              status: "assigned",
              documents: [
                {
                  id: "sandu-sketch-001",
                  name: "Schiță litere volumetrice.svg",
                  type: "svg",
                  source: "intake_work_file",
                  url: "/api/v1/employee-mobile/orders/1/work-files/sandu-sketch-001/download",
                  downloadable: true,
                },
              ],
            },
          ]),
        );
      }
      return Promise.resolve(jsonResponse([]));
    });

    renderShell("/employee-app/tasks?view=all");

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-task-card-T-006")).toBeInTheDocument();
    });

    clickTaskCard("T-006");

    expect(screen.getByTestId("employee-mobile-task-documents-list")).toBeInTheDocument();
    expect(screen.getByText(/Fișier comandă/)).toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-task-document-open-sandu-sketch-001")).toHaveAttribute(
      "href",
      "/api/v1/employee-mobile/orders/1/work-files/sandu-sketch-001/download",
    );
  });

  it("renders compact today tasks list without duplicating home now card", async () => {
    mockFetch.mockImplementation((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/employee-mobile/orders/1/my-blueprint")) {
        return Promise.resolve(jsonResponse(mockPipelineBlueprint()));
      }
      if (url.includes("/employee-mobile/tasks")) {
        return Promise.resolve(jsonResponse(mockSanduPipelineTasks()));
      }
      return Promise.resolve(jsonResponse([]));
    });

    renderShell("/employee-app/tasks");

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-tasks-list")).toBeInTheDocument();
    });
    expect(screen.queryByTestId("employee-mobile-tasks-now-now")).not.toBeInTheDocument();
    expect(screen.queryByText("Ce am de făcut acum")).not.toBeInTheDocument();
    expect(screen.queryByTestId("employee-mobile-tasks-summary")).not.toBeInTheDocument();
    expect(screen.queryByTestId("employee-mobile-tasks-view-description")).not.toBeInTheDocument();
    expect(screen.queryByTestId("employee-mobile-tasks-full-flow-link")).not.toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-tasks-tab-today")).toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-tasks-tab-pipeline")).toBeInTheDocument();
    expect(screen.queryByTestId("employee-mobile-pipeline-task-list")).not.toBeInTheDocument();
  });

  it("renders full order flow with active order card and numbered steps", async () => {
    mockFetch.mockImplementation((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/employee-mobile/orders/1/my-blueprint")) {
        return Promise.resolve(jsonResponse(mockPipelineBlueprint()));
      }
      if (url.includes("/employee-mobile/tasks")) {
        return Promise.resolve(jsonResponse(mockSanduPipelineTasks()));
      }
      return Promise.resolve(jsonResponse([]));
    });

    renderShell("/employee-app/tasks?view=pipeline");

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-pipeline-order-card")).toBeInTheDocument();
    });
    expect(screen.getByTestId("employee-mobile-pipeline-expand-toggle")).toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-pipeline-task-list")).toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-pipeline-task-number-T-004")).toHaveTextContent("2");
    expect(screen.getByTestId("employee-mobile-pipeline-marker-T-004")).toHaveTextContent("Acum");
    expect(
      screen.getByTestId("employee-mobile-pipeline-dependency-warning-T-004"),
    ).toHaveTextContent(/dependențelor/i);
    expect(screen.getByTestId("employee-mobile-pipeline-marker-T-006")).toHaveTextContent(
      /Așteaptă task anterior/i,
    );
    expect(screen.getByTestId("employee-mobile-pipeline-material-hints-T-006")).toHaveTextContent(
      /Module LED/i,
    );
    expect(
      screen.queryByTestId("employee-mobile-pipeline-T-006-start"),
    ).not.toBeInTheDocument();
    expect(screen.queryByTestId("employee-mobile-pipeline-task-T-003")).not.toBeInTheDocument();
    fireEvent.click(screen.getByTestId("employee-mobile-pipeline-expand-toggle"));
    expect(screen.getByTestId("employee-mobile-pipeline-task-T-003")).toHaveTextContent(
      /Alt post/i,
    );
    expect(screen.getByTestId("employee-mobile-tasks-tab-pipeline")).toBeInTheDocument();
    expect(screen.queryByTestId("employee-mobile-pipeline-other-employee-name")).not.toBeInTheDocument();
  });

  it("does not expose commercial fields in pipeline material hints", async () => {
    mockFetch.mockImplementation((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/employee-mobile/orders/1/my-blueprint")) {
        return Promise.resolve(jsonResponse(mockPipelineBlueprint()));
      }
      if (url.includes("/employee-mobile/tasks")) {
        return Promise.resolve(jsonResponse(mockSanduPipelineTasks()));
      }
      return Promise.resolve(jsonResponse([]));
    });

    renderShell("/employee-app/tasks?view=pipeline");

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-pipeline-material-hints-T-006")).toBeInTheDocument();
    });
    const root = screen.getByTestId("employee-mobile-order-pipeline");
    const text = root.textContent?.toLowerCase() ?? "";
    for (const forbidden of ["preț", "price", "cost", "marjă", "margin", "payroll"]) {
      expect(text).not.toContain(forbidden);
    }
  });

  it("shows waiting_material badge without start button when material blocks task", async () => {
    mockFetch.mockImplementation((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/employee-mobile/orders/1/my-blueprint")) {
        return Promise.resolve(
          jsonResponse({
            ...mockPipelineBlueprint(),
            tasks: [
              ...mockPipelineBlueprint().tasks.filter((task) => task.task_id !== "T-006"),
              {
                task_id: "T-006",
                name: "Montaj LED",
                status_display: "Alocat",
                is_mine: true,
                is_current: false,
                stage_label: "LED / Electric",
                has_documents: true,
                has_instructions: false,
                readiness_status: "waiting_material",
                readiness_label: "Așteaptă material",
                is_startable: false,
                blocking_tasks: [],
                material_hints: [
                  {
                    name: "Module LED",
                    category: "project_critical",
                    label: "Așteaptă confirmare achiziție",
                    status: "awaiting_advance",
                  },
                ],
                material_status_label: "Așteaptă confirmare achiziție",
              },
            ],
          }),
        );
      }
      if (url.includes("/employee-mobile/tasks")) {
        return Promise.resolve(jsonResponse(mockSanduPipelineTasks()));
      }
      return Promise.resolve(jsonResponse([]));
    });

    renderShell("/employee-app/tasks?view=pipeline");

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-pipeline-marker-T-006")).toHaveTextContent(
        /Așteaptă material/i,
      );
    });
    expect(
      screen.queryByTestId("employee-mobile-pipeline-T-006-start"),
    ).not.toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-bottom-nav")).toBeInTheDocument();
  });

  it("keeps blueprint page functional with shared pipeline list", async () => {
    mockFetch.mockImplementation((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/employee-mobile/orders/1/my-blueprint")) {
        return Promise.resolve(jsonResponse(mockPipelineBlueprint()));
      }
      if (url.includes("/employee-mobile/tasks")) {
        return Promise.resolve(jsonResponse(mockSanduPipelineTasks()));
      }
      return Promise.resolve(jsonResponse([]));
    });

    renderShell("/employee-app/tasks/orders/1/blueprint");

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-blueprint-task-list")).toBeInTheDocument();
    });
    expect(screen.getByTestId("employee-mobile-pipeline-marker-T-004")).toHaveTextContent("Acum");
    expect(
      screen.getByTestId("employee-mobile-pipeline-dependency-warning-T-004"),
    ).toHaveTextContent(/dependențelor/i);
    expect(screen.getByTestId("employee-mobile-pipeline-marker-T-006")).toHaveTextContent(
      /Așteaptă task anterior/i,
    );
    expect(screen.getByTestId("employee-mobile-blueprint-title")).toHaveTextContent(
      "Tot fluxul comenzii",
    );
  });

  it("hides horizontal filter scrollbar styling on tasks tabs", async () => {
    mockFetch.mockImplementation((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/employee-mobile/tasks")) {
        return Promise.resolve(jsonResponse(mockSanduPipelineTasks()));
      }
      if (url.includes("/employee-mobile/orders/1/my-blueprint")) {
        return Promise.resolve(jsonResponse(mockPipelineBlueprint()));
      }
      return Promise.resolve(jsonResponse([]));
    });

    renderShell("/employee-app/tasks");

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-tasks-tabs")).toBeInTheDocument();
    });
    expect(screen.getByTestId("employee-mobile-tasks-tabs").className).toMatch(
      /scrollbar-width:none|\[-ms-overflow-style:none\]/,
    );
  });

  it("hides Team card for employee_mobile without manager team access", async () => {
    renderShell("/employee-app/personal");

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-personal-hub")).toBeInTheDocument();
    });
    expect(screen.queryByTestId("employee-mobile-dashboard-team")).not.toBeInTheDocument();
    expect(screen.queryByText("Echipa mea")).not.toBeInTheDocument();
  });

  it("hides Review nav and dashboard card for employee_mobile", async () => {
    renderShell();

    expect(screen.queryByTestId("employee-mobile-nav-review")).not.toBeInTheDocument();
    expect(screen.queryByTestId("employee-mobile-dashboard-review")).not.toBeInTheDocument();
    expect(screen.queryByText("Review cereri")).not.toBeInTheDocument();
  });

  it("renders personal hub with Cereri, Pontaj, and Profil", async () => {
    renderShell("/employee-app/personal");

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-personal-requests")).toBeInTheDocument();
    });
    expect(screen.getByTestId("employee-mobile-personal-attendance")).toHaveAttribute(
      "href",
      "/employee-app/attendance",
    );
    expect(screen.getByTestId("employee-mobile-personal-profile")).toBeInTheDocument();
    expect(screen.queryByTestId("employee-mobile-dashboard-review")).not.toBeInTheDocument();
  });

  it("renders info and access page with account panel and install card", async () => {
    renderShell("/employee-app/info");

    expect(screen.getByTestId("employee-mobile-info-access")).toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-account-panel")).toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-account-access-summary")).toHaveTextContent(
      /self-only/i,
    );
    expect(screen.getByTestId("employee-mobile-install-card")).toBeInTheDocument();
  });

  it("blocks employee_mobile deep link to review without manager UI", async () => {
    renderShell("/employee-app/review");

    expect(screen.getByTestId("employee-mobile-route-blocked")).toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-route-blocked")).toHaveAttribute(
      "data-route-key",
      "review",
    );
    expect(screen.queryByTestId("employee-mobile-section-review")).not.toBeInTheDocument();
    expect(screen.queryByTestId("employee-mobile-review-panel")).not.toBeInTheDocument();
    expect(screen.queryByTestId("employee-mobile-requests-tabs")).not.toBeInTheDocument();
    expect(mockFetch).not.toHaveBeenCalled();
  });

  it("blocks employee_mobile deep link to team without manager UI", async () => {
    renderShell("/employee-app/team");

    expect(screen.getByTestId("employee-mobile-route-blocked")).toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-route-blocked")).toHaveAttribute(
      "data-route-key",
      "team",
    );
    expect(screen.queryByTestId("employee-manager-team-workspace")).not.toBeInTheDocument();
    expect(mockFetch).not.toHaveBeenCalled();
  });

  it("allows admin deep link to review route", async () => {
    authMock.user = {
      name: "Admin Test",
      email: "admin@workos.local",
      role: "admin",
    };
    mockFetch.mockImplementation(() => Promise.resolve(jsonResponse([])));

    renderShell("/employee-app/review");
    expect(screen.queryByTestId("employee-mobile-route-blocked")).not.toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-section-review")).toBeInTheDocument();
  });

  it("allows admin deep link to team route", async () => {
    authMock.user = {
      name: "Admin Test",
      email: "admin@workos.local",
      role: "admin",
    };
    mockFetch.mockImplementation(() => Promise.resolve(jsonResponse([])));

    renderShell("/employee-app/team");
    expect(screen.queryByTestId("employee-mobile-route-blocked")).not.toBeInTheDocument();
    expect(screen.getByTestId("employee-manager-team-workspace")).toBeInTheDocument();
  });

  it("shows Review nav and dashboard card for manager role", async () => {
    authMock.user = {
      name: "Manager Test",
      email: "manager@workos.local",
      role: "manager",
    };

    mockFetch.mockImplementation(() => Promise.resolve(jsonResponse([])));

    renderShell("/employee-app/personal");

    expect(screen.getByTestId("employee-mobile-nav-review")).toHaveAttribute(
      "href",
      "/employee-app/review",
    );
    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-dashboard-review")).toBeInTheDocument();
    });
  });

  it("shows Review nav for admin role on info page", async () => {
    authMock.user = {
      name: "Admin Test",
      email: "admin@workos.local",
      role: "admin",
    };

    mockFetch.mockImplementation(() => Promise.resolve(jsonResponse([])));

    renderShell("/employee-app/info");

    expect(screen.getByTestId("employee-mobile-nav-review")).toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-account-admin-note")).toBeInTheDocument();
  });

  it("shows Team card for manager role and renders team workspace route", async () => {
    authMock.user = {
      name: "Manager Test",
      email: "manager@workos.local",
      role: "manager",
    };

    mockFetch.mockImplementation(() => Promise.resolve(jsonResponse([])));

    renderShell("/employee-app/personal");

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-dashboard-team")).toBeInTheDocument();
    });
    expect(screen.getByText("Echipa mea")).toBeInTheDocument();

    fireEvent.click(screen.getByTestId("employee-mobile-dashboard-team"));

    await waitFor(() => {
      expect(screen.getByTestId("employee-manager-team-workspace")).toBeInTheDocument();
    });
  });

  it("exposes blueprint section routes without cluttering home dashboard", () => {
    expect(EMPLOYEE_MOBILE_SECTIONS.some((s) => s.id === "tasks")).toBe(true);
    expect(EMPLOYEE_MOBILE_SECTIONS.some((s) => s.status === "Self-only live")).toBe(true);
  });

  it("renders self attendance panel on attendance section with read-only badge", async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse([]));

    renderShell("/employee-app/attendance");

    expect(screen.getByTestId("employee-mobile-section-attendance")).toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-attendance-panel")).toBeInTheDocument();
    expect(screen.getByText("Pontajul meu")).toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-attendance-readonly-badge")).toHaveTextContent(
      /Read-only/,
    );
    expect(screen.queryByText(/fără date reale în acest shell/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /adaugă/i })).not.toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-attendance-empty")).toBeInTheDocument();
    });
  });
});

describe("EmployeeMobileApp requests section", () => {
  it("displays Cereri section with self-only badge", async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse([]));
    renderShell("/employee-app/requests");

    expect(screen.getByTestId("employee-mobile-requests-panel")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Cererile mele" })).toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-requests-self-badge")).toHaveTextContent(
      /Self-only/,
    );
    expect(screen.getByTestId("employee-mobile-requests-no-employee-id")).toHaveTextContent(
      /Cererile sunt legate automat de contul tău/,
    );

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-requests-empty")).toBeInTheDocument();
    });
  });

  it("shows requests on list success", async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse([submittedLeave]));
    renderShell("/employee-app/requests");

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-requests-list")).toBeInTheDocument();
    });
    expect(screen.getByText("Concediu vară")).toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-request-item-1")).toHaveTextContent(
      /În așteptare/,
    );
  });

  it("shows empty state when no requests", async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse([]));
    renderShell("/employee-app/requests");

    await waitFor(() => {
      expect(screen.getByText("Nu ai nicio cerere încă.")).toBeInTheDocument();
    });
  });

  it("shows status filter controls on self requests", async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse([submittedLeave]));
    renderShell("/employee-app/requests");

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-requests-status-filters")).toBeInTheDocument();
    });
    expect(screen.getByTestId("employee-mobile-requests-filter-all")).toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-requests-filter-submitted")).toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-requests-refresh")).toBeInTheDocument();
  });

  it("refresh button re-fetches self requests list", async () => {
    mockFetch
      .mockResolvedValueOnce(jsonResponse([submittedLeave]))
      .mockResolvedValueOnce(jsonResponse([submittedLeave, approvedAdvance]));

    renderShell("/employee-app/requests");

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-requests-refresh")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("employee-mobile-requests-refresh"));

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(2);
    });
    expect(String(mockFetch.mock.calls[0][0])).toContain("/api/v1/employee-mobile/requests");
    expect(String(mockFetch.mock.calls[1][0])).toContain("/api/v1/employee-mobile/requests");
  });

  it("shows employee link missing message on self 403", async () => {
    mockFetch.mockResolvedValueOnce(
      jsonResponse({ detail: { error: "employee_link_missing" } }, 403),
    );
    renderShell("/employee-app/requests");

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-requests-error")).toHaveTextContent(
        /Contul tău nu este legat încă de un profil de angajat/,
      );
    });
  });

  it("shows contextual empty state when filter has no matches", async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse([approvedAdvance]));
    renderShell("/employee-app/requests");

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-requests-filter-rejected")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("employee-mobile-requests-filter-rejected"));

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-requests-empty")).toHaveTextContent(
        /Nicio cerere în filtrul selectat/,
      );
    });
  });

  it("submit create sends payload without employee_id or status", async () => {
    mockFetch
      .mockResolvedValueOnce(jsonResponse([]))
      .mockResolvedValueOnce(
        jsonResponse({ ...submittedLeave, id: 3, title: "Cerere nouă" }, 201),
      )
      .mockResolvedValueOnce(jsonResponse([{ ...submittedLeave, id: 3, title: "Cerere nouă" }]));

    renderShell("/employee-app/requests");

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-request-submit")).toBeInTheDocument();
    });

    fireEvent.change(screen.getByTestId("employee-mobile-request-title"), {
      target: { value: "Cerere nouă" },
    });
    fireEvent.change(screen.getByTestId("employee-mobile-request-start-date"), {
      target: { value: "2026-07-01" },
    });
    fireEvent.click(screen.getByTestId("employee-mobile-request-submit"));

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(3);
    });

    const postCall = mockFetch.mock.calls.find(
      (call) => (call[1] as RequestInit | undefined)?.method === "POST",
    );
    expect(postCall).toBeDefined();
    const body = JSON.parse(String((postCall?.[1] as RequestInit).body));
    expect(body).not.toHaveProperty("employee_id");
    expect(body).not.toHaveProperty("status");
    expect(body).not.toHaveProperty("submitted_at");
    expect(body).not.toHaveProperty("reviewed_by_user_id");
    expect(body.request_type).toBe("leave");
    expect(body.title).toBe("Cerere nouă");
  });

  it("includes advance amount only when valid", () => {
    const payload = buildEmployeeRequestCreatePayload({
      request_type: "advance",
      title: "Avans",
      description: "",
      reason: "",
      start_date: "",
      end_date: "",
      amount: "750",
      currency: "RON",
    });
    expect(payload.amount).toBe(750);
    expect(payload).not.toHaveProperty("employee_id");

    const invalid = buildEmployeeRequestCreatePayload({
      request_type: "advance",
      title: "Avans",
      description: "",
      reason: "",
      start_date: "",
      end_date: "",
      amount: "",
      currency: "RON",
    });
    expect(invalid.amount).toBeUndefined();
  });

  it("shows cancel only for draft or submitted requests", async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse([submittedLeave, approvedAdvance]));
    renderShell("/employee-app/requests");

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-request-cancel-1")).toBeInTheDocument();
    });
    expect(screen.queryByTestId("employee-mobile-request-cancel-2")).not.toBeInTheDocument();
  });

  it("cancel uses self-only PATCH endpoint", async () => {
    mockFetch
      .mockResolvedValueOnce(jsonResponse([submittedLeave]))
      .mockResolvedValueOnce(
        jsonResponse({ ...submittedLeave, status: "cancelled" }),
      )
      .mockResolvedValueOnce(jsonResponse([]));

    renderShell("/employee-app/requests");

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-request-cancel-1")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("employee-mobile-request-cancel-1"));

    await waitFor(() => {
      expect(mockFetch.mock.calls.length).toBeGreaterThanOrEqual(2);
    });

    const patchCall = mockFetch.mock.calls.find(
      (call) => (call[1] as RequestInit | undefined)?.method === "PATCH",
    );
    expect(String(patchCall?.[0])).toContain("/api/v1/employee-mobile/requests/1/cancel");
  });

  it("shows error state on API error", async () => {
    mockFetch.mockResolvedValueOnce(
      jsonResponse({ detail: { error: "employee_self_role_required" } }, 403),
    );
    renderShell("/employee-app/requests");

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-requests-error")).toBeInTheDocument();
    });
    expect(screen.getByTestId("employee-mobile-requests-error")).toHaveTextContent(
      /Rolul tău nu permite accesul la aplicația personală/,
    );
  });
});

const reviewItem = {
  id: 42,
  employee_id: 10,
  request_type: "leave",
  status: "submitted",
  title: "Concediu Ion",
  employee_name: "Ion Popescu",
  employee_status: "active",
  start_date: "2026-07-01",
  end_date: "2026-07-05",
  submitted_at: "2026-06-13T10:00:00+00:00",
};

describe("EmployeeMobileApp manager review section", () => {
  beforeEach(() => {
    authMock.user = {
      name: "Manager Test",
      email: "manager@workos.local",
      role: "manager",
    };
  });

  it("shows Review manager tab on review route", async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse([]));
    renderShell("/employee-app/review");

    expect(screen.getByTestId("employee-mobile-requests-tabs")).toBeInTheDocument();
    expect(screen.getByText("Review manager")).toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-review-panel")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-review-empty")).toBeInTheDocument();
    });
  });

  it("lists review requests on success", async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse([reviewItem]));
    renderShell("/employee-app/review");

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-review-list")).toBeInTheDocument();
    });
    expect(screen.getByText("Concediu Ion")).toBeInTheDocument();
    expect(screen.getByText(/Ion Popescu/)).toBeInTheDocument();
    expect(screen.queryByText(/cost_lunar/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/salary/i)).not.toBeInTheDocument();
  });

  it("shows empty review inbox message for default submitted filter", async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse([]));
    renderShell("/employee-app/review");

    await waitFor(() => {
      expect(screen.getByText("Nu există cereri trimise pentru review.")).toBeInTheDocument();
    });
    expect(screen.getByTestId("employee-mobile-review-filter-submitted")).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });

  it("review refresh button re-fetches list endpoint", async () => {
    mockFetch
      .mockResolvedValueOnce(jsonResponse([reviewItem]))
      .mockResolvedValueOnce(jsonResponse([reviewItem]));

    renderShell("/employee-app/review");

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-review-refresh")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("employee-mobile-review-refresh"));

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(2);
    });
    expect(String(mockFetch.mock.calls[0][0])).toContain("/api/v1/employee-requests/review");
  });

  it("blocks employee_mobile from review route before API call", async () => {
    authMock.user = {
      name: "Angajat Test",
      email: "angajat@workos.local",
      role: "employee_mobile",
    };
    renderShell("/employee-app/review");

    expect(screen.getByTestId("employee-mobile-route-blocked")).toBeInTheDocument();
    expect(screen.queryByTestId("employee-mobile-review-panel")).not.toBeInTheDocument();
    expect(screen.queryByTestId("employee-mobile-review-list")).not.toBeInTheDocument();
    expect(mockFetch).not.toHaveBeenCalled();
  });

  it("approve sends PATCH with review_note only", async () => {
    mockFetch
      .mockResolvedValueOnce(jsonResponse([reviewItem]))
      .mockResolvedValueOnce(jsonResponse(reviewItem))
      .mockResolvedValueOnce(jsonResponse({ ...reviewItem, status: "approved" }))
      .mockResolvedValueOnce(jsonResponse([]));

    renderShell("/employee-app/review");

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-review-item-42")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("employee-mobile-review-item-42"));

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-review-approve")).toBeInTheDocument();
    });

    fireEvent.change(screen.getByTestId("employee-mobile-review-note"), {
      target: { value: "Aprobat echipa" },
    });
    fireEvent.click(screen.getByTestId("employee-mobile-review-approve"));

    await waitFor(() => {
      expect(mockFetch.mock.calls.length).toBeGreaterThanOrEqual(3);
    });

    const approveCall = mockFetch.mock.calls.find(
      (call) =>
        (call[1] as RequestInit | undefined)?.method === "PATCH" &&
        String(call[0]).includes("/api/v1/employee-requests/review/42/approve"),
    );
    expect(approveCall).toBeDefined();
    const body = JSON.parse(String((approveCall?.[1] as RequestInit).body));
    expect(body).toEqual({ review_note: "Aprobat echipa" });
    expect(body).not.toHaveProperty("employee_id");
    expect(body).not.toHaveProperty("attendance");
    expect(body).not.toHaveProperty("payment");
  });

  it("reject uses PATCH reject endpoint", async () => {
    mockFetch
      .mockResolvedValueOnce(jsonResponse([reviewItem]))
      .mockResolvedValueOnce(jsonResponse(reviewItem))
      .mockResolvedValueOnce(jsonResponse({ ...reviewItem, status: "rejected" }))
      .mockResolvedValueOnce(jsonResponse([]));

    renderShell("/employee-app/review");

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-review-item-42")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("employee-mobile-review-item-42"));

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-review-reject")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("employee-mobile-review-reject"));

    await waitFor(() => {
      const rejectCall = mockFetch.mock.calls.find(
        (call) =>
          (call[1] as RequestInit | undefined)?.method === "PATCH" &&
          String(call[0]).includes("/api/v1/employee-requests/review/42/reject"),
      );
      expect(rejectCall).toBeDefined();
    });
  });

  it("hides approve/reject when detail status is not submitted", async () => {
    mockFetch
      .mockResolvedValueOnce(jsonResponse([reviewItem]))
      .mockResolvedValueOnce(jsonResponse({ ...reviewItem, status: "approved" }));

    renderShell("/employee-app/review");

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-review-item-42")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("employee-mobile-review-item-42"));

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-review-not-reviewable")).toBeInTheDocument();
    });
    expect(screen.queryByTestId("employee-mobile-review-approve")).not.toBeInTheDocument();
    expect(screen.queryByTestId("employee-mobile-review-reject")).not.toBeInTheDocument();
  });

  it("shows self-review forbidden message on approve 403", async () => {
    mockFetch
      .mockResolvedValueOnce(jsonResponse([reviewItem]))
      .mockResolvedValueOnce(jsonResponse(reviewItem))
      .mockResolvedValueOnce(
        jsonResponse({ detail: { error: "self_review_forbidden" } }, 403),
      );

    renderShell("/employee-app/review");

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-review-item-42")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("employee-mobile-review-item-42"));
    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-review-approve")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("employee-mobile-review-approve"));

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-review-action-error")).toHaveTextContent(
        /Nu poți aproba sau respinge propria cerere/,
      );
    });
  });

  it("shows conflict message on approve 409", async () => {
    mockFetch
      .mockResolvedValueOnce(jsonResponse([reviewItem]))
      .mockResolvedValueOnce(jsonResponse(reviewItem))
      .mockResolvedValueOnce(
        jsonResponse({ detail: { error: "invalid_status_transition" } }, 409),
      );

    renderShell("/employee-app/review");

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-review-item-42")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("employee-mobile-review-item-42"));
    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-review-approve")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("employee-mobile-review-approve"));

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-review-action-error")).toHaveTextContent(
        /Cererea a fost deja procesată sau nu mai poate fi modificată/,
      );
    });
  });

  it("disables approve/reject buttons while action is pending", async () => {
    let resolveApprove: (value: Response) => void;
    const approvePromise = new Promise<Response>((resolve) => {
      resolveApprove = resolve;
    });

    mockFetch
      .mockResolvedValueOnce(jsonResponse([reviewItem]))
      .mockResolvedValueOnce(jsonResponse(reviewItem))
      .mockImplementationOnce(() => approvePromise);

    renderShell("/employee-app/review");

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-review-item-42")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("employee-mobile-review-item-42"));
    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-review-approve")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("employee-mobile-review-approve"));

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-review-approve")).toBeDisabled();
      expect(screen.getByTestId("employee-mobile-review-reject")).toBeDisabled();
    });

    resolveApprove!(jsonResponse({ ...reviewItem, status: "approved" }));
  });

  it("review filter hides requests that do not match", async () => {
    const approvedReviewItem = { ...reviewItem, id: 43, status: "approved", title: "Aprobat" };
    mockFetch.mockResolvedValueOnce(jsonResponse([reviewItem, approvedReviewItem]));
    renderShell("/employee-app/review");

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-review-item-42")).toBeInTheDocument();
    });
    expect(screen.queryByTestId("employee-mobile-review-item-43")).not.toBeInTheDocument();

    fireEvent.click(screen.getByTestId("employee-mobile-review-filter-approved"));

    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-review-item-43")).toBeInTheDocument();
    });
    expect(screen.queryByTestId("employee-mobile-review-item-42")).not.toBeInTheDocument();
  });
});

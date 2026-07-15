import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import EmployeeMobileV2App from "./EmployeeMobileV2App";
import { buildTruthResponseFromSections } from "@/components/workos/employee-mobile-v2/EmployeeMobileV2TaskTruthPanels";
import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";
import { BLOCKER_FIXTURE_TASKS } from "@/lib/employeeMobileV2BlockerFixtures";

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

function renderV2(initialPath = "/employee-app-v2") {
  render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route path="/employee-app-v2/*" element={<EmployeeMobileV2App />} />
      </Routes>
    </MemoryRouter>,
  );
}

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const sampleTasks = [
  {
    task_id: "T-004",
    order_id: 1,
    order_code: "ORD-1",
    title: "Lipire canturi",
    status: "in_progress",
    client: "Vetro",
    product: "Litere volumetrice",
    is_startable: false,
  },
  {
    task_id: "T-006",
    order_id: 1,
    order_code: "ORD-1",
    title: "Montaj LED",
    status: "assigned",
    client: "Vetro",
    is_startable: false,
  },
];

const sampleAvailableTasks = [
  {
    task_id: "T-AVAIL",
    order_id: 2,
    order_code: "ORD-2",
    title: "Printare colant",
    status: "assigned",
    client: "Client Nou",
    is_startable: true,
    claimable: true,
  },
];

function truthFor(assigned: EmployeeMobileTaskDTO[], available: EmployeeMobileTaskDTO[] = sampleAvailableTasks) {
  return buildTruthResponseFromSections(assigned, available);
}

describe("EmployeeMobileV2App", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", mockFetch);
    mockFetch.mockImplementation(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes("/api/v1/employee-mobile/tasks/truth")) {
        return jsonResponse(truthFor(sampleTasks, sampleAvailableTasks));
      }
      if (
        url.includes("/start-from-available") &&
        init?.method === "POST"
      ) {
        return jsonResponse({
          status: "ok",
          action: "start",
          task_id: "T-AVAIL",
          order_id: 2,
          timestamp: "2026-06-16T10:00:00+00:00",
        });
      }
      if (
        url.includes("/api/v1/employee-mobile/tasks") &&
        url.includes("/claim") &&
        init?.method === "POST"
      ) {
        return jsonResponse({
          status: "ok",
          action: "claim",
          task_id: "T-AVAIL",
          order_id: 2,
          assigned_employee_id: 99,
        });
      }
      if (url.includes("/api/v1/employee-mobile/tasks") && !url.includes("/start") && !url.includes("/truth")) {
        return jsonResponse(sampleTasks);
      }
      if (url.includes("/api/v1/employee-mobile/order-blueprint")) {
        return jsonResponse({
          order_id: 1,
          order_label: "ORD-1",
          client_label: "Vetro",
          tasks: [],
        });
      }
      if (url.includes("/api/v1/employee-mobile/requests")) {
        return jsonResponse([]);
      }
      if (url.includes("/api/v1/employee-mobile/attendance")) {
        return jsonResponse([]);
      }
      if (url.includes("/api/v1/employee-mobile/self-link")) {
        return jsonResponse({ linked: true, employee_name: "Angajat Test" });
      }
      return jsonResponse({}, 404);
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    mockFetch.mockReset();
  });

  it("mounts home with Card Acum and six module tiles", async () => {
    renderV2();
    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-v2-home")).toBeInTheDocument();
    });
    expect(screen.getByTestId("employee-mobile-v2-home-hero-now")).toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-v2-home-module-grid")).toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-v2-home-module-tasks")).toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-v2-home-module-pipeline")).toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-v2-home-module-documents")).toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-v2-home-module-blocked")).toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-v2-home-module-upcoming")).toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-v2-home-module-personal")).toBeInTheDocument();
  });

  it("renders bottom nav with exactly three items", async () => {
    renderV2();
    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-v2-bottom-nav")).toBeInTheDocument();
    });
    expect(screen.getByTestId("employee-mobile-v2-nav-home")).toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-v2-nav-tasks")).toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-v2-nav-personal")).toBeInTheDocument();
    expect(screen.queryByTestId("employee-mobile-v2-nav-pontaj")).not.toBeInTheDocument();
    expect(screen.queryByTestId("employee-mobile-v2-nav-documents")).not.toBeInTheDocument();
  });

  it("does not show Quick Stats or Pontaj-dominant home CTA", async () => {
    renderV2();
    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-v2-home-hero-cta")).toBeInTheDocument();
    });
    expect(screen.queryByText(/Rezumat azi/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Pornește pontajul/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Pe scurt/i)).not.toBeInTheDocument();
  });

  it("loads task list from API on tasks route", async () => {
    renderV2("/employee-app-v2/tasks");
    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-v2-tasks-list")).toBeInTheDocument();
    });
    expect(screen.getByTestId("employee-mobile-v2-in-progress-row-T-004")).toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-v2-task-row-T-006")).toBeInTheDocument();
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/employee-mobile/tasks/truth"),
      expect.anything(),
    );
  });

  it("renders Taskuri disponibile with Poți începe acum and start-from-available flow", async () => {
    renderV2("/employee-app-v2/tasks");
    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-v2-available-tasks")).toBeInTheDocument();
    });
    expect(screen.getByText("Disponibile")).toBeInTheDocument();
    expect(screen.getByText("Poți începe acum")).toBeInTheDocument();
    expect(screen.queryByText("Preiau taskul")).not.toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-v2-available-startable-list")).toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-v2-available-start-T-AVAIL")).toHaveTextContent(
      "Încep lucrul",
    );

    fireEvent.click(screen.getByTestId("employee-mobile-v2-available-start-T-AVAIL"));

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/v1/employee-mobile/tasks/T-AVAIL/start-from-available"),
        expect.objectContaining({ method: "POST" }),
      );
    });
  });

  it("shows waiting available tasks without active start button", async () => {
    mockFetch.mockImplementation(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes("/api/v1/employee-mobile/tasks/truth")) {
        return jsonResponse(
          truthFor([], [
            {
              task_id: "T-WAIT",
              order_id: 2,
              order_code: "ORD-2",
              title: "Montaj LED",
              status: "assigned",
              client: "Client",
              is_startable: false,
              readiness_status: "waiting_predecessor",
              readiness_label: "Așteaptă task anterior",
            },
            ...sampleAvailableTasks,
          ]),
        );
      }
      if (url.includes("/api/v1/employee-mobile/tasks") && !url.includes("/start") && !url.includes("/truth")) {
        return jsonResponse([]);
      }
      return jsonResponse({}, 404);
    });

    renderV2("/employee-app-v2/tasks");
    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-v2-available-waiting-section")).toBeInTheDocument();
    });
    expect(screen.getByText("În așteptare")).toBeInTheDocument();
    expect(
      screen.getByTestId("employee-mobile-v2-available-waiting-reason-T-WAIT"),
    ).toHaveTextContent("Așteaptă task anterior");
    expect(
      screen.queryByTestId("employee-mobile-v2-available-start-T-WAIT"),
    ).not.toBeInTheDocument();
  });

  it("does not show removed grouping or scope controls on tasks page", async () => {
    renderV2("/employee-app-v2/tasks");
    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-v2-tasks-list")).toBeInTheDocument();
    });
    expect(screen.queryByTestId("employee-mobile-v2-tasks-grouping-mode")).not.toBeInTheDocument();
    expect(screen.queryByTestId("employee-mobile-v2-tasks-scope-filter")).not.toBeInTheDocument();
    expect(screen.queryByText("Operație")).not.toBeInTheDocument();
    expect(screen.queryByText("Prioritate")).not.toBeInTheDocument();
    expect(screen.queryByText("Afișez:")).not.toBeInTheDocument();
  });

  it("shows fixed task sections including available and recent done history", async () => {
    mockFetch.mockImplementation(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes("/api/v1/employee-mobile/tasks/truth")) {
        return jsonResponse(
          truthFor([
            ...sampleTasks,
            {
              task_id: "T-DONE",
              order_id: 1,
              order_code: "ORD-1",
              title: "Debitare față",
              status: "done",
              client: "Vetro",
              completed_at: "2026-06-14T08:00:00Z",
              is_startable: false,
            },
          ]),
        );
      }
      if (url.includes("/api/v1/employee-mobile/tasks") && !url.includes("/start") && !url.includes("/truth")) {
        return jsonResponse([
          ...sampleTasks,
          {
            task_id: "T-DONE",
            order_id: 1,
            order_code: "ORD-1",
            title: "Debitare față",
            status: "done",
            client: "Vetro",
            completed_at: "2026-06-14T08:00:00Z",
            is_startable: false,
          },
        ]);
      }
      if (url.includes("/api/v1/employee-mobile/order-blueprint")) {
        return jsonResponse({
          order_id: 1,
          order_label: "ORD-1",
          client_label: "Vetro",
          tasks: [],
        });
      }
      return jsonResponse({}, 404);
    });

    renderV2("/employee-app-v2/tasks");
    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-v2-tasks-list")).toBeInTheDocument();
    });
    expect(screen.getByText("Taskurile mele")).toBeInTheDocument();
    expect(screen.getByText("Poți începe acum")).toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-v2-recent-done-section")).toBeInTheDocument();
    expect(screen.getByText("Finalizate")).toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-v2-recent-done-row-T-DONE")).toBeInTheDocument();
    expect(screen.queryByTestId("employee-mobile-v2-task-row-T-DONE")).not.toBeInTheDocument();
  });

  it("keeps blockers report form hidden by default", async () => {
    renderV2("/employee-app-v2/blockers");
    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-v2-blockers")).toBeInTheDocument();
    });
    expect(screen.queryByTestId("employee-mobile-v2-blockers-form")).not.toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-v2-blockers-report-open")).toBeInTheDocument();
  });

  it("shows future modules section without backend", async () => {
    renderV2();
    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-v2-future-modules")).toBeInTheDocument();
    });
    expect(screen.getByTestId("employee-mobile-v2-future-modules-montaje")).toBeInTheDocument();
  });

  it("hides raw process slugs on task detail", async () => {
    mockFetch.mockImplementation(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/api/v1/employee-mobile/tasks/truth")) {
        return jsonResponse(
          truthFor([
            {
              ...sampleTasks[0],
              process_type: "volumetric_letter_assembly",
              operation_label: "Asamblare litere volumetrice",
              machine_type: "ASSEMBLY_TABLE",
            },
          ]),
        );
      }
      if (url.includes("/orders/1/tasks/T-004")) {
        return jsonResponse({
          ...sampleTasks[0],
          process_type: "volumetric_letter_assembly",
          operation_label: "Asamblare litere volumetrice",
          machine_type: "ASSEMBLY_TABLE",
        });
      }
      if (url.includes("/api/v1/employee-mobile/tasks") && !url.includes("/start") && !url.includes("/truth")) {
        return jsonResponse([
          {
            ...sampleTasks[0],
            process_type: "volumetric_letter_assembly",
            operation_label: "Asamblare litere volumetrice",
            machine_type: "ASSEMBLY_TABLE",
          },
        ]);
      }
      if (url.includes("/my-blueprint")) {
        return jsonResponse({
          order_id: 1,
          order_label: "ORD-1",
          client_label: "Vetro",
          summary: {
            total_tasks: 0,
            my_tasks: 0,
            my_done: 0,
            overall_progress_percent: 0,
            my_progress_percent: 0,
            blocked: 0,
            in_progress: 0,
          },
          tasks: [{ task_id: "T-004", name: "Lipire canturi" }],
        });
      }
      return jsonResponse({}, 404);
    });

    renderV2("/employee-app-v2/tasks/T-004");
    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-v2-work-room")).toBeInTheDocument();
    });
    expect(screen.getByTestId("employee-mobile-v2-task-detail")).toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-v2-detail-operation")).toHaveTextContent(
      "Asamblare litere volumetrice",
    );
    expect(screen.getByTestId("employee-mobile-v2-work-room-actions")).toBeInTheDocument();
    expect(screen.queryByText("volumetric_letter_assembly")).not.toBeInTheDocument();
    expect(screen.queryByText("ASSEMBLY_TABLE")).not.toBeInTheDocument();
  });

  it("does not duplicate waiting detail on upcoming list", async () => {
    mockFetch.mockImplementation(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/api/v1/employee-mobile/tasks/truth")) {
        return jsonResponse(
          truthFor([
            sampleTasks[0],
            {
              ...sampleTasks[1],
              blocking_tasks: [{ task_id: "T-005", name: "Debitare spate Forex" }],
              readiness_label: "Așteaptă task anterior",
            },
          ]),
        );
      }
      if (url.includes("/api/v1/employee-mobile/tasks") && !url.includes("/start") && !url.includes("/truth")) {
        return jsonResponse([
          sampleTasks[0],
          {
            ...sampleTasks[1],
            blocking_tasks: [{ task_id: "T-005", name: "Debitare spate Forex" }],
            readiness_label: "Așteaptă task anterior",
          },
        ]);
      }
      return jsonResponse({}, 404);
    });

    renderV2("/employee-app-v2/upcoming");
    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-v2-upcoming-list")).toBeInTheDocument();
    });
    const row = screen.getByTestId("employee-mobile-v2-task-row-T-006");
    expect(row.textContent).toMatch(/Debitare spate Forex/);
    expect(screen.getByTestId("employee-mobile-v2-task-row-T-006-status").textContent).not.toMatch(
      /Debitare spate Forex.*Debitare spate Forex/,
    );
  });

  it("keeps pipeline context only in page header", async () => {
    mockFetch.mockImplementation(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/api/v1/employee-mobile/tasks/truth")) {
        return jsonResponse(truthFor(sampleTasks));
      }
      if (url.includes("/api/v1/employee-mobile/tasks") && !url.includes("/start") && !url.includes("/truth")) {
        return jsonResponse(sampleTasks);
      }
      if (url.includes("/my-blueprint")) {
        return jsonResponse({
          order_id: 1,
          order_label: "ORD-1",
          client_label: "Vetro",
          summary: {
            total_tasks: 2,
            my_tasks: 2,
            my_done: 0,
            overall_progress_percent: 0,
            my_progress_percent: 0,
            blocked: 0,
            in_progress: 1,
          },
          tasks: [
            { task_id: "T-004", name: "Lipire canturi", status_display: "În lucru" },
            { task_id: "T-006", name: "Montaj LED", status_display: "Atribuit" },
          ],
        });
      }
      return jsonResponse({}, 404);
    });

    renderV2("/employee-app-v2/pipeline");
    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-v2-pipeline-timeline")).toBeInTheDocument();
    });
    expect(screen.queryByTestId("employee-mobile-pipeline-context")).not.toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-v2-pipeline-header")).toHaveTextContent("2 pași");
    expect(screen.queryByText("Așteaptă task anterior")).not.toBeInTheDocument();
  });

  it("shows vertical pipeline axis markers with legend and center waiting context", async () => {
    mockFetch.mockImplementation(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/api/v1/employee-mobile/tasks/truth")) {
        return jsonResponse(
          truthFor([
            {
              task_id: "T-004",
              order_id: 1,
              title: "Lipire canturi",
              status: "in_progress",
              is_startable: false,
              dependency_warning: "A pornit înainte de finalizarea dependențelor",
            },
            {
              task_id: "T-006",
              order_id: 1,
              title: "Montaj LED",
              status: "assigned",
              readiness_status: "waiting_predecessor",
              is_startable: false,
              blocking_tasks: [{ task_id: "T-005", name: "Debitare spate Forex" }],
            },
          ]),
        );
      }
      if (url.includes("/api/v1/employee-mobile/tasks") && !url.includes("/start") && !url.includes("/truth")) {
        return jsonResponse([
          {
            task_id: "T-004",
            order_id: 1,
            title: "Lipire canturi",
            status: "in_progress",
            is_startable: false,
            dependency_warning: "A pornit înainte de finalizarea dependențelor",
          },
          {
            task_id: "T-006",
            order_id: 1,
            title: "Montaj LED",
            status: "assigned",
            readiness_status: "waiting_predecessor",
            is_startable: false,
            blocking_tasks: [{ name: "Debitare spate Forex" }],
          },
        ]);
      }
      if (url.includes("/my-blueprint")) {
        return jsonResponse({
          order_id: 1,
          order_label: "ORD-1",
          client_label: "Vetro",
          tasks: [
            {
              task_id: "T-001",
              name: "Verificare grafică",
              status_display: "În lucru",
              is_mine: false,
            },
            {
              task_id: "T-002",
              name: "Debitare față plexiglas",
              status_display: "Finalizat",
              is_mine: false,
            },
            {
              task_id: "T-004",
              name: "Lipire canturi",
              status_display: "În lucru",
              is_mine: true,
            },
            {
              task_id: "T-006",
              name: "Montaj LED",
              status_display: "Atribuit",
              is_mine: true,
              readiness_status: "waiting_predecessor",
            },
          ],
        });
      }
      return jsonResponse({}, 404);
    });

    renderV2("/employee-app-v2/pipeline");
    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-v2-pipeline-legend")).toBeInTheDocument();
    });

    const legend = screen.getByTestId("employee-mobile-v2-pipeline-legend");
    expect(legend).toHaveTextContent("În lucru acum");
    expect(legend).toHaveTextContent("Blocat");
    expect(legend).toHaveTextContent("Așteaptă");
    expect(legend).toHaveTextContent("Urmează");
    expect(legend).toHaveTextContent("Alt post");
    expect(legend).toHaveTextContent("Finalizat");

    const timeline = screen.getByTestId("employee-mobile-v2-pipeline-timeline");
    expect(timeline.className).toMatch(/rounded-2xl/);

    const completedRow = screen.getByTestId("employee-mobile-pipeline-task-T-002");
    expect(completedRow).toHaveAttribute("data-pipeline-state", "completed");
    const completedButton = completedRow.querySelector("button");
    expect(completedButton?.className).toMatch(/border-b/);
    expect(completedButton?.className).toMatch(/bg-emerald-950\/25/);
    expect(completedButton?.className).not.toMatch(/rounded-xl/);
    expect(completedButton?.querySelector("svg.lucide-chevron-right")).toBeNull();
    expect(
      screen.getByTestId("employee-mobile-pipeline-axis-marker-T-002").querySelector("svg.lucide-check"),
    ).toBeTruthy();
    expect(screen.getByTestId("employee-mobile-pipeline-task-number-T-002")).toHaveTextContent(
      "Pas 2",
    );

    const currentRow = screen.getByTestId("employee-mobile-pipeline-task-T-004");
    expect(currentRow).toHaveAttribute("data-pipeline-state", "current");
    expect(currentRow.querySelector("button")?.querySelector("svg.lucide-chevron-right")).toBeTruthy();
    expect(screen.getByTestId("employee-mobile-pipeline-axis-marker-T-004")).toHaveAttribute(
      "data-pipeline-axis-pulse",
      "true",
    );
    expect(screen.getByTestId("employee-mobile-pipeline-axis-pulse-T-004")).toBeInTheDocument();
    expect(screen.queryByTestId("employee-mobile-pipeline-axis-pulse-T-006")).not.toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-pipeline-axis-marker-T-004")).toBeInTheDocument();
    expect(screen.queryByTestId("employee-mobile-pipeline-marker-T-004")).not.toBeInTheDocument();

    const waitingRow = screen.getByTestId("employee-mobile-pipeline-task-T-006");
    expect(waitingRow).toHaveAttribute("data-pipeline-state", "waiting");
    expect(screen.getByTestId("employee-mobile-pipeline-axis-marker-T-006")).toBeInTheDocument();

    const altPostRow = screen.getByTestId("employee-mobile-pipeline-task-T-001");
    expect(altPostRow).toHaveAttribute("data-pipeline-state", "alt-post");
    expect(altPostRow.querySelector("button")?.querySelector("svg.lucide-chevron-right")).toBeNull();
    expect(screen.getByTestId("employee-mobile-pipeline-axis-marker-T-001")).toBeInTheDocument();
    expect(screen.queryByTestId("employee-mobile-pipeline-marker-T-001")).not.toBeInTheDocument();

    expect(screen.getByTestId("employee-mobile-pipeline-status-context-T-006")).toHaveTextContent(
      /Așteaptă: Debitare spate Forex/,
    );
    expect(screen.getByTestId("employee-mobile-pipeline-dependency-warning-T-004")).toHaveTextContent(
      /Atenție: dependențe active/,
    );
    expect(screen.getByTestId("employee-mobile-pipeline-open-T-004")).toBeInTheDocument();
  });

  it("resolves task detail by orderId + taskId for available preview without start", async () => {
    const ownedT003 = {
      task_id: "T-003",
      order_id: 99904,
      order_code: "ORD-99904",
      title: "Colantare fețe litere vechi",
      status: "assigned",
      instructions: "Aplică autocolantul pe fețele literelor, nu pe cant.",
      is_startable: true,
    };
    const previewT003 = {
      task_id: "T-003",
      order_id: 99905,
      order_code: "ORD-99905",
      title: "Colantare fețe litere",
      status: "assigned",
      instructions:
        "Colantezi fețele din plexiglas ale literelor cu autocolantul selectat.\nLungime pregătire: 0,80 ml",
      is_startable: true,
      claimable: true,
      preview_only: true,
      access_mode: "available_preview",
    };

    mockFetch.mockImplementation(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes("/orders/99905/tasks/T-003")) {
        return jsonResponse(previewT003);
      }
      if (url.includes("/api/v1/employee-mobile/tasks/truth")) {
        return jsonResponse(truthFor([ownedT003], [previewT003]));
      }
      if (url.includes("/start-from-available") && init?.method === "POST") {
        return jsonResponse({ status: "ok" });
      }
      if (url.includes("/api/v1/employee-mobile/tasks") && !url.includes("/start") && !url.includes("/truth")) {
        return jsonResponse([ownedT003]);
      }
      return jsonResponse({}, 404);
    });

    renderV2("/employee-app-v2/tasks/T-003?orderId=99905");
    await waitFor(() => {
      expect(screen.getByTestId("employee-mobile-v2-work-room")).toHaveAttribute(
        "data-preview-only",
        "true",
      );
    });
    expect(screen.getByTestId("employee-mobile-v2-work-room-context")).toHaveTextContent(
      "ORD-99905",
    );
    expect(screen.getByTestId("employee-mobile-v2-work-room-preview-instructions")).toHaveTextContent(
      "Colantezi fețele din plexiglas",
    );
    expect(screen.queryByText("nu pe cant")).not.toBeInTheDocument();
    expect(screen.getByTestId("employee-mobile-v2-available-preview-start")).toBeInTheDocument();
    expect(mockFetch).not.toHaveBeenCalledWith(
      expect.stringContaining("/start-from-available"),
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("shows Vezi detalii on available task cards", async () => {
    mockFetch.mockImplementation(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/api/v1/employee-mobile/tasks/truth")) {
        return jsonResponse(
          truthFor([], [
            {
              task_id: "T-003",
              order_id: 99905,
              order_code: "ORD-99905",
              title: "Colantare fețe litere",
              status: "assigned",
              is_startable: true,
              claimable: true,
            },
          ]),
        );
      }
      if (url.includes("/api/v1/employee-mobile/tasks") && !url.includes("/start") && !url.includes("/truth")) {
        return jsonResponse([]);
      }
      return jsonResponse({}, 404);
    });

    renderV2("/employee-app-v2/tasks");
    await waitFor(() => {
      expect(
        screen.getByTestId("employee-mobile-v2-available-details-T-003-99905"),
      ).toBeInTheDocument();
    });
  });

  describe("MOBILE-T03 blocker and readiness visibility", () => {
    it("shows production block badge and manager escalation on list card", async () => {
      mockFetch.mockImplementation(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/api/v1/employee-mobile/tasks/truth")) {
          return jsonResponse(truthFor([BLOCKER_FIXTURE_TASKS.productionBlocked], []));
        }
        if (url.includes("/api/v1/employee-mobile/tasks") && !url.includes("/truth")) {
          return jsonResponse([BLOCKER_FIXTURE_TASKS.productionBlocked]);
        }
        return jsonResponse({}, 404);
      });

      renderV2("/employee-app-v2/tasks");
      await waitFor(() => {
        expect(
          screen.getByTestId("employee-mobile-v2-task-row-fixture-production-blocked-production-badge"),
        ).toHaveTextContent("Producție blocată");
      });
      expect(
        screen.getByTestId("employee-mobile-v2-task-row-fixture-production-blocked-manager-escalation"),
      ).toHaveTextContent("Necesită rezolvare de către manager");
    });

    it("shows structured detail sections with manager escalation and disabled start", async () => {
      mockFetch.mockImplementation(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/api/v1/employee-mobile/orders/23099/tasks/fixture-production-blocked")) {
          return jsonResponse(BLOCKER_FIXTURE_TASKS.productionBlocked);
        }
        if (url.includes("/api/v1/employee-mobile/tasks/truth")) {
          return jsonResponse(truthFor([BLOCKER_FIXTURE_TASKS.productionBlocked], []));
        }
        if (url.includes("/api/v1/employee-mobile/tasks") && !url.includes("/truth")) {
          return jsonResponse([BLOCKER_FIXTURE_TASKS.productionBlocked]);
        }
        return jsonResponse({}, 404);
      });

      renderV2("/employee-app-v2/tasks/fixture-production-blocked?orderId=23099");
      await waitFor(() => {
        expect(screen.getByTestId("employee-mobile-v2-detail-can-start")).toBeInTheDocument();
      });
      expect(screen.getByTestId("employee-mobile-v2-detail-startable")).toHaveTextContent("Nu");
      expect(screen.getByTestId("employee-mobile-v2-detail-manager-escalation")).toHaveTextContent(
        /manager în WorkOS desktop/,
      );
      await waitFor(() => {
        expect(screen.getByTestId("employee-mobile-v2-work-room-start-blocked")).toBeDisabled();
      });
    });

    it("shows ready state without production block", async () => {
      mockFetch.mockImplementation(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/api/v1/employee-mobile/tasks/truth")) {
          return jsonResponse(truthFor([BLOCKER_FIXTURE_TASKS.readyAssigned], []));
        }
        if (url.includes("/api/v1/employee-mobile/tasks") && !url.includes("/truth")) {
          return jsonResponse([BLOCKER_FIXTURE_TASKS.readyAssigned]);
        }
        return jsonResponse({}, 404);
      });

      renderV2("/employee-app-v2/tasks");
      await waitFor(() => {
        expect(
          screen.getByTestId("employee-mobile-v2-task-row-fixture-ready-readiness-badge"),
        ).toHaveTextContent("Pregătit");
      });
      expect(
        screen.queryByTestId("employee-mobile-v2-task-row-fixture-ready-production-badge"),
      ).not.toBeInTheDocument();
    });

    it("maps contract error distinctly from valid empty tasks", async () => {
      mockFetch.mockImplementation(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/api/v1/employee-mobile/tasks/truth")) {
          return jsonResponse(
            { detail: { code: "MOBILE_V2_TASK_ENVELOPE_MISSING", message: "missing" } },
            409,
          );
        }
        return jsonResponse({}, 404);
      });

      renderV2("/employee-app-v2/tasks");
      await waitFor(() => {
        expect(screen.getByTestId("employee-mobile-v2-tasks-error")).toBeInTheDocument();
      });
      expect(screen.getByTestId("employee-mobile-v2-tasks-error")).toHaveTextContent(
        /Planul de execuție V2/,
      );
    });

    it("maps employee-link error distinctly", async () => {
      mockFetch.mockImplementation(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/api/v1/employee-mobile/tasks/truth")) {
          return jsonResponse({ detail: { code: "employee_link_missing", message: "x" } }, 403);
        }
        return jsonResponse({}, 404);
      });

      renderV2("/employee-app-v2/tasks");
      await waitFor(() => {
        expect(screen.getByTestId("employee-mobile-v2-tasks-error")).toBeInTheDocument();
      });
      expect(screen.getByTestId("employee-mobile-v2-tasks-error")).toHaveTextContent(/profil de angajat/);
    });
  });
});

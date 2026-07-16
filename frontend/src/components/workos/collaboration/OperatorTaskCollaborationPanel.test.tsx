import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import OperatorTaskCollaborationPanel from "@/components/workos/collaboration/OperatorTaskCollaborationPanel";
import type { TaskCollaborationReadDTO } from "@/api/collaboration";

vi.mock("@/api/collaboration", async () => {
  const actual = await vi.importActual<typeof import("@/api/collaboration")>(
    "@/api/collaboration",
  );
  return {
    ...actual,
    createOperatorHelpRequest: vi.fn(),
    cancelOperatorHelpRequest: vi.fn(),
  };
});

vi.mock("@/api/operationalRegistry", () => ({
  operationalRegistryApi: {
    listEmployees: vi.fn(async () => ({ items: [], total: 0 })),
  },
}));

function baseTask(
  overrides: Partial<TaskCollaborationReadDTO> = {},
): TaskCollaborationReadDTO {
  return {
    task_id: "T-1",
    display_name: "Test",
    optional_principal: {
      optional_principal_employee_id: 10,
      optional_principal_employee_name: "Principal",
    },
    helper_memberships: [],
    active_workers: [],
    open_help_requests: [],
    has_open_help: false,
    operation_completed: false,
    can_request_help: false,
    can_cancel_help: false,
    can_complete_operation: false,
    ...overrides,
  };
}

describe("OperatorTaskCollaborationPanel", () => {
  it("shows request help only when can_request_help", () => {
    render(
      <OperatorTaskCollaborationPanel
        orderId={1}
        task={baseTask({ can_request_help: true })}
        onChanged={async () => undefined}
      />,
    );
    expect(screen.getByTestId("operator-collab-request-help")).toBeInTheDocument();
  });

  it("hides request help when capability false", () => {
    render(
      <OperatorTaskCollaborationPanel
        orderId={1}
        task={baseTask({ can_request_help: false })}
        onChanged={async () => undefined}
      />,
    );
    expect(screen.queryByTestId("operator-collab-request-help")).not.toBeInTheDocument();
  });

  it("separates authorized helpers from active workers", () => {
    render(
      <OperatorTaskCollaborationPanel
        orderId={1}
        task={baseTask({
          helper_memberships: [
            {
              employee_id: 20,
              employee_name: "Helper A",
              status: "active",
              joined_at: "2026-07-16T10:00:00Z",
            },
          ],
          active_workers: [
            {
              employee_id: 20,
              employee_name: "Helper A",
              session_count: 1,
              active_session_count: 1,
              has_active_session: true,
            },
          ],
        })}
        onChanged={async () => undefined}
      />,
    );
    expect(screen.getByText(/Helpers autorizați/i)).toBeInTheDocument();
    expect(screen.getByText(/Lucrători activi/i)).toBeInTheDocument();
    expect(screen.getByText(/autorizat, nu neapărat în lucru/i)).toBeInTheDocument();
  });

  it("shows cancel when can_cancel_help and open help exists", () => {
    render(
      <OperatorTaskCollaborationPanel
        orderId={1}
        task={baseTask({
          can_cancel_help: true,
          has_open_help: true,
          open_help_requests: [
            {
              help_request_id: 9,
              order_id: 1,
              task_id: "T-1",
              requested_by_employee_id: 10,
              status: "OPEN",
              created_at: "2026-07-16T10:00:00Z",
              updated_at: "2026-07-16T10:00:00Z",
              is_broadcast: true,
            },
          ],
        })}
        onChanged={async () => undefined}
      />,
    );
    expect(screen.getByTestId("operator-collab-cancel-help")).toBeInTheDocument();
  });
});

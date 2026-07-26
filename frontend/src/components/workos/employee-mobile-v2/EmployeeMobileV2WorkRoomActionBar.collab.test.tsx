import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";
import EmployeeMobileV2WorkRoomActionBar from "@/components/workos/employee-mobile-v2/EmployeeMobileV2WorkRoomActionBar";
import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";
import { FLEX_COLLAB_UI_FLAG } from "@/lib/flexCollabUiFlag";

vi.mock("@/hooks/useEmployeeMobileV2StartAction", () => ({
  useEmployeeMobileV2StartAction: () => ({
    startTask: vi.fn(),
    isPending: () => false,
    error: null,
    clearError: vi.fn(),
  }),
}));

vi.mock("@/hooks/useEmployeeMobileV2RuntimeAction", () => ({
  useEmployeeMobileV2RuntimeAction: () => ({
    completeTask: vi.fn(),
    isPending: () => false,
    error: null,
    clearError: vi.fn(),
  }),
}));

vi.mock("@/hooks/useEmployeeMobileV2ClaimAction", () => ({
  useEmployeeMobileV2ClaimAction: () => ({
    claimTask: vi.fn(),
    isPending: () => false,
    error: null,
    clearError: vi.fn(),
  }),
}));

vi.mock("@/api/collaboration", async () => {
  const actual = await vi.importActual<typeof import("@/api/collaboration")>(
    "@/api/collaboration",
  );
  return {
    ...actual,
    startMobileHelperSession: vi.fn(),
    stopMobileHelperSession: vi.fn(),
  };
});

function helperTask(
  overrides: Partial<EmployeeMobileTaskDTO> = {},
): EmployeeMobileTaskDTO {
  return {
    task_id: "T-H",
    order_id: 1,
    status: "assigned",
    visible_as_helper: true,
    visible_as_principal: false,
    can_start_helper_work: true,
    can_stop_own_session: false,
    can_complete_operation: false,
    can_claim: false,
    can_complete: false,
    ...overrides,
  };
}

describe("EmployeeMobileV2WorkRoomActionBar helper collaboration", () => {
  const prev = import.meta.env[FLEX_COLLAB_UI_FLAG];

  beforeEach(() => {
    (import.meta.env as Record<string, string>)[FLEX_COLLAB_UI_FLAG] = "true";
  });

  afterEach(() => {
    if (prev === undefined) {
      delete (import.meta.env as Record<string, string | undefined>)[FLEX_COLLAB_UI_FLAG];
    } else {
      (import.meta.env as Record<string, string>)[FLEX_COLLAB_UI_FLAG] = String(prev);
    }
  });

  it("shows helper start and hides complete for helper-only", () => {
    render(
      <EmployeeMobileV2WorkRoomActionBar
        task={helperTask()}
        onActionComplete={async () => undefined}
      />,
    );
    expect(screen.getByTestId("employee-mobile-v2-work-room-helper-start")).toBeInTheDocument();
    expect(screen.queryByTestId("employee-mobile-v2-work-room-complete")).not.toBeInTheDocument();
    expect(screen.queryByTestId("employee-mobile-v2-work-room-claim")).not.toBeInTheDocument();
  });

  it("shows helper stop when can_stop_own_session", () => {
    render(
      <EmployeeMobileV2WorkRoomActionBar
        task={helperTask({
          can_start_helper_work: false,
          can_stop_own_session: true,
          status: "in_progress",
        })}
        onActionComplete={async () => undefined}
      />,
    );
    expect(screen.getByTestId("employee-mobile-v2-work-room-helper-stop")).toBeInTheDocument();
  });

  it("does not show helper stop for principal-only active session", () => {
    render(
      <EmployeeMobileV2WorkRoomActionBar
        task={helperTask({
          visible_as_helper: false,
          visible_as_principal: true,
          can_start_helper_work: false,
          can_stop_own_session: true,
          can_complete_operation: true,
          status: "in_progress",
        })}
        onActionComplete={async () => undefined}
      />,
    );
    expect(screen.queryByTestId("employee-mobile-v2-work-room-helper-stop")).not.toBeInTheDocument();
  });
});

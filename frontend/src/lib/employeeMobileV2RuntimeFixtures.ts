import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";

function baseTask(overrides: Partial<EmployeeMobileTaskDTO>): EmployeeMobileTaskDTO {
  return {
    task_id: "fixture-runtime",
    order_id: 23099,
    order_code: "ORD-FIXTURE",
    title: "Task fixture",
    display_label: "Task fixture",
    status: "assigned",
    is_assigned_to_current_employee: true,
    is_available_for_claim: false,
    is_startable: false,
    can_start: false,
    ...overrides,
  };
}

export const runtimeFixtureInProgress = baseTask({
  task_id: "fixture-runtime-in-progress",
  title: "Lipire LED",
  status: "in_progress",
  is_startable: false,
  can_start: false,
  can_complete: true,
  readiness_status: "in_progress",
  readiness_label: "În lucru",
  started_at: "2026-07-15T08:00:00+03:00",
});

export const runtimeFixtureCompleted = baseTask({
  task_id: "fixture-runtime-completed",
  title: "Montaj LED",
  status: "done",
  can_complete: false,
  can_start: false,
  started_at: "2026-07-15T07:00:00+03:00",
  completed_at: "2026-07-15T09:30:00+03:00",
});

export const runtimeFixtureNoSession = baseTask({
  task_id: "fixture-runtime-no-session",
  title: "Printare colant",
  status: "assigned",
  can_complete: false,
  can_start: true,
  is_startable: true,
});

export const runtimeFixtureOtherOwner = baseTask({
  task_id: "fixture-runtime-other",
  title: "Tăiere CNC",
  status: "in_progress",
  is_assigned_to_current_employee: false,
  can_complete: false,
  started_at: "2026-07-15T08:00:00+03:00",
});

export const RUNTIME_FIXTURE_TASKS = {
  inProgress: runtimeFixtureInProgress,
  completed: runtimeFixtureCompleted,
  noSession: runtimeFixtureNoSession,
  otherOwner: runtimeFixtureOtherOwner,
};

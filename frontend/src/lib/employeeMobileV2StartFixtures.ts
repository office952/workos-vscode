import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";
import { BLOCKER_FIXTURE_TASKS } from "@/lib/employeeMobileV2BlockerFixtures";

function baseTask(overrides: Partial<EmployeeMobileTaskDTO>): EmployeeMobileTaskDTO {
  return {
    task_id: "fixture-start",
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

export const startFixtureReadyAssigned = baseTask({
  task_id: "fixture-start-ready",
  title: "Lipire canturi",
  is_startable: true,
  can_start: true,
  readiness_status: "eligible",
  readiness_label: "Eligibil acum",
  production_release_blocked: false,
});

export const startFixtureProductionBlocked = {
  ...BLOCKER_FIXTURE_TASKS.productionBlocked,
  can_start: false,
  is_assigned_to_current_employee: true,
};

export const startFixtureReadinessBlocked = baseTask({
  task_id: "fixture-start-readiness",
  title: "Printare colant",
  readiness_status: "waiting_predecessor",
  readiness_label: "Așteaptă task anterior",
  can_start: false,
});

export const startFixtureAvailableStartable = baseTask({
  task_id: "fixture-start-available",
  title: "Finisare",
  is_assigned_to_current_employee: false,
  is_available_for_claim: true,
  can_claim: true,
  is_startable: true,
  can_start: true,
  can_start_from_available: true,
  readiness_status: "eligible",
});

export const startFixtureInProgress = {
  ...BLOCKER_FIXTURE_TASKS.inProgress,
  can_start: false,
  can_complete: true,
};

export const START_FIXTURE_TASKS = {
  readyAssigned: startFixtureReadyAssigned,
  productionBlocked: startFixtureProductionBlocked,
  readinessBlocked: startFixtureReadinessBlocked,
  availableStartable: startFixtureAvailableStartable,
  inProgress: startFixtureInProgress,
};

import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";

function baseTask(overrides: Partial<EmployeeMobileTaskDTO>): EmployeeMobileTaskDTO {
  return {
    task_id: "fixture-task",
    order_id: 23099,
    order_code: "ORD-FIXTURE",
    title: "Task fixture",
    display_label: "Task fixture",
    status: "assigned",
    is_assigned_to_current_employee: true,
    is_available_for_claim: false,
    is_startable: false,
    ...overrides,
  };
}

export const blockerFixtureReadyAssigned = baseTask({
  task_id: "fixture-ready",
  title: "Lipire canturi",
  is_startable: true,
  readiness_status: "eligible",
  readiness_label: "Eligibil acum",
  production_release_blocked: false,
});

export const blockerFixtureProductionBlocked = baseTask({
  task_id: "fixture-production-blocked",
  title: "Montaj panou",
  production_release_blocked: true,
  production_blocker_summary:
    "Productie blocata (OWNER_DECISION_UNRESOLVED). Rezolvare pe desktop.",
  is_startable: false,
  readiness_status: "eligible",
  readiness_label: "Eligibil acum",
});

export const blockerFixturePredecessorBlocked = baseTask({
  task_id: "fixture-predecessor",
  title: "Printare colant",
  readiness_status: "waiting_predecessor",
  readiness_label: "Așteaptă task anterior",
  readiness_reasons: [
    {
      code: "predecessor_not_done",
      label: "Așteaptă task anterior",
      task_name: "Vector Prep",
    },
  ],
  blocking_tasks: [{ task_id: "node:root:op1", name: "Vector Prep" }],
  blocking_task_ids: ["node:root:op1"],
  dependency_warning: "Așteaptă finalizarea unui task anterior.",
});

export const blockerFixtureMaterialBlocked = baseTask({
  task_id: "fixture-material",
  title: "Aplicare folie",
  readiness_status: "waiting_material",
  readiness_label: "Așteaptă material",
  material_warning: "Material lipsă: ACM 3mm",
  readiness_reasons: [
    {
      code: "material_procurement_block",
      label: "Așteaptă material",
      message: "ACM 3mm neconfirmat",
    },
  ],
});

export const blockerFixtureOwnedByOther = baseTask({
  task_id: "fixture-other-owner",
  title: "Tăiere CNC",
  is_assigned_to_current_employee: false,
  assigned_employee_id: 99,
  employee_name: "Ion Popescu",
  readiness_status: "assigned_not_mine",
  readiness_label: "Alt post",
});

export const blockerFixtureAvailableNotStartable = baseTask({
  task_id: "fixture-available-wait",
  title: "Finisare",
  is_assigned_to_current_employee: false,
  is_available_for_claim: true,
  can_claim: true,
  is_startable: false,
  readiness_status: "waiting_file",
  readiness_label: "Așteaptă pregătire fișiere/vectori",
});

export const blockerFixtureInProgress = baseTask({
  task_id: "fixture-in-progress",
  title: "Lipire LED",
  status: "in_progress",
  is_startable: false,
  readiness_status: "in_progress",
  readiness_label: "În lucru",
  started_at: "2026-07-15T08:00:00Z",
  can_complete: true,
});

export const blockerFixtureCompleted = baseTask({
  task_id: "fixture-completed",
  title: "Ambalare",
  status: "done",
  is_startable: false,
  readiness_status: "done",
  readiness_label: "Finalizat",
  completed_at: "2026-07-14T16:00:00Z",
});

export const BLOCKER_FIXTURE_TASKS = {
  readyAssigned: blockerFixtureReadyAssigned,
  productionBlocked: blockerFixtureProductionBlocked,
  predecessorBlocked: blockerFixturePredecessorBlocked,
  materialBlocked: blockerFixtureMaterialBlocked,
  ownedByOther: blockerFixtureOwnedByOther,
  availableNotStartable: blockerFixtureAvailableNotStartable,
  inProgress: blockerFixtureInProgress,
  completed: blockerFixtureCompleted,
};

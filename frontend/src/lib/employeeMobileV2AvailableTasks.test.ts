import { describe, expect, it } from "vitest";
import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";
import {
  countStartableAvailableTasks,
  partitionAvailableTasks,
  resolveAvailableTaskWaitingLabel,
  sortAvailableTasksByPlan,
} from "./employeeMobileV2AvailableTasks";

function task(partial: Partial<EmployeeMobileTaskDTO> & Pick<EmployeeMobileTaskDTO, "task_id">): EmployeeMobileTaskDTO {
  return {
    order_id: 1,
    status: "assigned",
    ...partial,
  };
}

describe("employeeMobileV2AvailableTasks", () => {
  it("partitions startable vs waiting", () => {
    const { startable, waiting } = partitionAvailableTasks([
      task({ task_id: "T-002", is_startable: false, readiness_status: "waiting_predecessor" }),
      task({ task_id: "T-001", is_startable: true, plan_sequence: 0 } as EmployeeMobileTaskDTO),
    ]);
    expect(startable.map((t) => t.task_id)).toEqual(["T-001"]);
    expect(waiting.map((t) => t.task_id)).toEqual(["T-002"]);
  });

  it("sorts by plan sequence not alphabetically", () => {
    const sorted = sortAvailableTasksByPlan([
      task({ task_id: "T-010", title: "Z last alpha" }),
      task({ task_id: "T-003", title: "Colantare" }),
    ]);
    expect(sorted.map((t) => t.task_id)).toEqual(["T-003", "T-010"]);
  });

  it("maps waiting reasons to Romanian labels", () => {
    expect(
      resolveAvailableTaskWaitingLabel(
        task({ task_id: "T-5", readiness_status: "waiting_predecessor" }),
      ),
    ).toBe("Așteaptă task anterior");
    expect(
      resolveAvailableTaskWaitingLabel(task({ task_id: "T-6", readiness_status: "waiting_file" })),
    ).toBe("Așteaptă fișierul/vectorul");
    expect(resolveAvailableTaskWaitingLabel(task({ task_id: "T-7" }))).toBe(
      "Taskul nu este încă pregătit",
    );
  });

  it("counts startable tasks", () => {
    expect(
      countStartableAvailableTasks([
        task({ task_id: "T-1", is_startable: true }),
        task({ task_id: "T-2", is_startable: false }),
      ]),
    ).toBe(1);
  });
});

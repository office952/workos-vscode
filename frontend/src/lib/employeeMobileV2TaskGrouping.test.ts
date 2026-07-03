import { describe, expect, it } from "vitest";
import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";
import {
  buildTaskRowContextLine,
  filterActiveMyTasks,
  filterRecentDoneTasks,
  getTaskInProgressNote,
  getTaskWaitingReason,
  groupTasksByOrder,
  sortActiveMyTasks,
  suppressDuplicateWaitingDetail,
} from "@/lib/employeeMobileV2TaskGrouping";
import { resolveEmployeeMobileV2StatusPresentation } from "@/lib/employeeMobileV2Status";

function task(partial: Partial<EmployeeMobileTaskDTO> & Pick<EmployeeMobileTaskDTO, "task_id" | "order_id" | "status">): EmployeeMobileTaskDTO {
  return {
    is_startable: false,
    ...partial,
  } as EmployeeMobileTaskDTO;
}

describe("employeeMobileV2TaskGrouping", () => {
  describe("filterActiveMyTasks", () => {
    it("excludes done tasks", () => {
      const rows = filterActiveMyTasks([
        task({ task_id: "T-1", order_id: 1, status: "in_progress" }),
        task({ task_id: "T-2", order_id: 1, status: "done" }),
      ]);
      expect(rows.map((row) => row.task_id)).toEqual(["T-1"]);
    });
  });

  describe("filterRecentDoneTasks", () => {
    it("returns done tasks newest first with limit", () => {
      const rows = filterRecentDoneTasks(
        [
          task({ task_id: "T-1", order_id: 1, status: "done", completed_at: "2026-06-10T10:00:00Z" }),
          task({ task_id: "T-2", order_id: 1, status: "done", completed_at: "2026-06-12T10:00:00Z" }),
          task({ task_id: "T-3", order_id: 1, status: "in_progress" }),
        ],
        1,
      );
      expect(rows.map((row) => row.task_id)).toEqual(["T-2"]);
    });
  });

  describe("sortActiveMyTasks", () => {
    it("sorts in_progress before assigned", () => {
      const rows = sortActiveMyTasks([
        task({ task_id: "T-2", order_id: 1, status: "assigned", title: "B" }),
        task({ task_id: "T-1", order_id: 1, status: "in_progress", title: "A" }),
      ]);
      expect(rows.map((row) => row.task_id)).toEqual(["T-1", "T-2"]);
    });
  });

  describe("groupTasksByOrder", () => {
    it("groups by order_id and computes progress", () => {
      const groups = groupTasksByOrder([
        task({ task_id: "T-1", order_id: 1, status: "in_progress", order_code: "ORD-1", client: "Vetro" }),
        task({ task_id: "T-2", order_id: 1, status: "done", order_code: "ORD-1" }),
        task({ task_id: "T-3", order_id: 2, status: "assigned", is_startable: true }),
      ]);

      expect(groups).toHaveLength(2);
      expect(groups[0].orderLabel).toBe("ORD-1");
      expect(groups[0].doneCount).toBe(1);
      expect(groups[0].totalCount).toBe(2);
      expect(groups[0].inProgressCount).toBe(1);
      expect(groups[1].orderLabel).toBe("Comandă #2");
    });
  });

  describe("getTaskWaitingReason", () => {
    it("uses blocking task name", () => {
      expect(
        getTaskWaitingReason(
          task({
            task_id: "T-1",
            order_id: 1,
            status: "assigned",
            blocking_tasks: [{ task_id: "T-0", name: "Debitare spate Forex" }],
          }),
        ),
      ).toBe("Așteaptă: Debitare spate Forex");
    });

    it("returns null for in_progress tasks", () => {
      expect(
        getTaskWaitingReason(
          task({
            task_id: "T-1",
            order_id: 1,
            status: "in_progress",
            blocking_tasks: [{ task_id: "T-0", name: "Modelare canturi" }],
          }),
        ),
      ).toBeNull();
    });

    it("uses dependency warning", () => {
      expect(
        getTaskWaitingReason(
          task({
            task_id: "T-1",
            order_id: 1,
            status: "assigned",
            dependency_warning: "A pornit înainte de finalizarea dependențelor",
          }),
        ),
      ).toContain("A pornit");
    });

    it("shortens readiness label", () => {
      expect(
        getTaskWaitingReason(
          task({
            task_id: "T-1",
            order_id: 1,
            status: "assigned",
            readiness_label: "Așteaptă task anterior",
          }),
        ),
      ).toBe("task anterior");
    });

    it("falls back safely", () => {
      expect(
        getTaskWaitingReason(
          task({
            task_id: "T-1",
            order_id: 1,
            status: "assigned",
            is_startable: false,
          }),
        ),
      ).toBe("depinde de alt pas");
    });
  });

  describe("getTaskInProgressNote", () => {
    it("uses attention note for dependency warning", () => {
      expect(
        getTaskInProgressNote(
          task({
            task_id: "T-4",
            order_id: 1,
            status: "in_progress",
            dependency_warning: "A pornit înainte de finalizarea dependențelor",
          }),
        ),
      ).toBe("Atenție: dependență pornită înainte de finalizare");
    });

    it("uses blocker name as note", () => {
      expect(
        getTaskInProgressNote(
          task({
            task_id: "T-4",
            order_id: 1,
            status: "in_progress",
            blocking_tasks: [{ task_id: "T-3", name: "Modelare canturi litere volumetrice" }],
          }),
        ),
      ).toMatch(/^Notă: dependență cu Modelare canturi/);
    });
  });

  describe("buildTaskRowContextLine", () => {
    it("does not show Așteaptă for in_progress tasks", () => {
      const line = buildTaskRowContextLine(
        task({
          task_id: "T-4",
          order_id: 1,
          status: "in_progress",
          order_code: "ORD-1",
          product: "Litere volumetrice",
          blocking_tasks: [{ task_id: "T-3", name: "Modelare canturi" }],
        }),
      );

      expect(line).not.toMatch(/^Așteaptă:/);
      expect(line).not.toContain("Așteaptă:");
      expect(line).toMatch(/^Notă: dependență cu Modelare canturi/);
    });

    it("shows waiting reason for assigned waiting tasks", () => {
      const line = buildTaskRowContextLine(
        task({
          task_id: "T-6",
          order_id: 1,
          status: "assigned",
          order_code: "ORD-1",
          blocking_tasks: [{ task_id: "T-5", name: "Debitare spate Forex" }],
        }),
      );

      expect(line).toBe("Așteaptă: Debitare spate Forex");
    });
  });

  describe("suppressDuplicateWaitingDetail", () => {
    it("hides status detail when context already explains waiting", () => {
      const waitingTask = task({
        task_id: "T-6",
        order_id: 1,
        status: "assigned",
        is_startable: false,
        readiness_status: "waiting_predecessor",
        blocking_tasks: [{ task_id: "T-5", name: "Debitare spate Forex" }],
      });
      const presentation = resolveEmployeeMobileV2StatusPresentation(waitingTask);
      const adjusted = suppressDuplicateWaitingDetail(
        presentation,
        "Așteaptă: Debitare spate Forex",
      );
      expect(adjusted.detailLine).toBeNull();
      expect(adjusted.shortLabel).toBe("Așteaptă");
    });
  });
});

import { describe, expect, it } from "vitest";
import {
  sortTasksByDependencyDisplayOrder,
  type OpsGraphOrderableTask,
} from "./opsGraphDisplayOrder";

function task(
  id: string,
  seq: number,
  deps: string[] = [],
): OpsGraphOrderableTask {
  return {
    task_id: id,
    sequence_index: seq,
    depends_on_task_ids: deps,
  };
}

describe("sortTasksByDependencyDisplayOrder", () => {
  it("orders by dependency so prerequisites precede dependents even when SEQ is higher", () => {
    // SEQ gap style: packaging SEQ=14 depends on qc SEQ=13, but also include
    // a high-SEQ branch that must wait on early work.
    const tasks = [
      task("pack", 14, ["qc"]),
      task("qc", 13, ["cut"]),
      task("late_branch", 29, ["prep"]),
      task("cut", 2, ["prep"]),
      task("prep", 1, []),
    ];

    const ordered = sortTasksByDependencyDisplayOrder(tasks).map((t) => t.task_id);
    expect(ordered).toEqual(["prep", "cut", "qc", "pack", "late_branch"]);
  });

  it("does not remap sequence_index values on tasks", () => {
    const tasks = [task("b", 24, ["a"]), task("a", 10, [])];
    const ordered = sortTasksByDependencyDisplayOrder(tasks);
    expect(ordered.map((t) => t.sequence_index)).toEqual([10, 24]);
    expect(ordered[0].sequence_index).toBe(10);
    expect(ordered[1].sequence_index).toBe(24);
  });

  it("tie-breaks independent roots by original SEQ", () => {
    const tasks = [task("z", 5, []), task("a", 1, []), task("m", 3, [])];
    const ordered = sortTasksByDependencyDisplayOrder(tasks).map((t) => t.task_id);
    expect(ordered).toEqual(["a", "m", "z"]);
  });

  it("ignores dependency ids outside the task set", () => {
    const tasks = [task("child", 2, ["missing_parent"]), task("solo", 1, [])];
    const ordered = sortTasksByDependencyDisplayOrder(tasks).map((t) => t.task_id);
    expect(ordered).toEqual(["solo", "child"]);
  });

  it("appends cycle members by SEQ without inventing new indexes", () => {
    const tasks = [
      task("a", 1, ["b"]),
      task("b", 2, ["a"]),
      task("free", 3, []),
    ];
    const ordered = sortTasksByDependencyDisplayOrder(tasks);
    expect(ordered.map((t) => t.task_id)[0]).toBe("free");
    expect(ordered.map((t) => t.sequence_index).sort((x, y) => x! - y!)).toEqual([
      1, 2, 3,
    ]);
  });
});

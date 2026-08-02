import { describe, expect, it } from "vitest";
import { operatorTaskPresentationKey } from "./operatorTaskPresentationKey";

describe("operatorTaskPresentationKey", () => {
  it("distinguishes same task_id on different jobs", () => {
    const a = operatorTaskPresentationKey({
      jobId: "JOB-973019",
      id: "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:electrical_wiring",
    });
    const b = operatorTaskPresentationKey({
      jobId: "JOB-21099",
      id: "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:electrical_wiring",
    });
    expect(a).not.toBe(b);
    expect(a).toContain("JOB-973019");
    expect(b).toContain("JOB-21099");
  });

  it("keeps task_id segment for same-job uniqueness", () => {
    const key = operatorTaskPresentationKey({
      jobId: "JOB-21",
      id: "node:x:INSTALL_LED_MODULES",
    });
    expect(key).toBe("JOB-21::node:x:INSTALL_LED_MODULES");
  });
});

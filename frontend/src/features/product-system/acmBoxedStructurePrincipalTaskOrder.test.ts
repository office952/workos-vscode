import { describe, expect, it } from "vitest";
import { ACM_BOXED_PRINCIPAL_TASK_CHAIN } from "./acmBoxedStructurePrincipalTaskOrder";

describe("acmBoxedStructurePrincipalTaskOrder", () => {
  it("is strictly ordered 1..10 with unique ids", () => {
    expect(ACM_BOXED_PRINCIPAL_TASK_CHAIN.map((t) => t.order)).toEqual([
      1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
    ]);
    expect(new Set(ACM_BOXED_PRINCIPAL_TASK_CHAIN.map((t) => t.id)).size).toBe(10);
  });

  it("starts with ArtCAM prep and ends with pack", () => {
    expect(ACM_BOXED_PRINCIPAL_TASK_CHAIN[0]!.id).toBe("prep_artcam");
    expect(ACM_BOXED_PRINCIPAL_TASK_CHAIN[0]!.labelRo).toMatch(/ArtCAM/i);
    expect(ACM_BOXED_PRINCIPAL_TASK_CHAIN.at(-1)!.id).toBe("pack_product");
  });
});

import { describe, expect, it } from "vitest";
import {
  paginateWorkIntakeList,
  WORK_INTAKE_LIST_PAGE_SIZE,
} from "./workIntakeListPagination";

describe("paginateWorkIntakeList", () => {
  const items = Array.from({ length: 39 }, (_, i) => `REQ-${i + 1}`);

  it("uses default page size 10", () => {
    expect(WORK_INTAKE_LIST_PAGE_SIZE).toBe(10);
    const page1 = paginateWorkIntakeList(items, 1);
    expect(page1.items).toHaveLength(10);
    expect(page1.items[0]).toBe("REQ-1");
    expect(page1.items[9]).toBe("REQ-10");
    expect(page1.rangeLabel).toBe("1–10 din 39");
    expect(page1.pageLabel).toBe("Pagina 1 din 4");
  });

  it("returns second page subset", () => {
    const page2 = paginateWorkIntakeList(items, 2);
    expect(page2.items).toHaveLength(10);
    expect(page2.items[0]).toBe("REQ-11");
    expect(page2.rangeLabel).toBe("11–20 din 39");
    expect(page2.pageLabel).toBe("Pagina 2 din 4");
  });

  it("returns partial last page", () => {
    const page4 = paginateWorkIntakeList(items, 4);
    expect(page4.items).toHaveLength(9);
    expect(page4.items[0]).toBe("REQ-31");
    expect(page4.rangeLabel).toBe("31–39 din 39");
  });

  it("clamps page below 1 and above totalPages", () => {
    expect(paginateWorkIntakeList(items, 0).page).toBe(1);
    expect(paginateWorkIntakeList(items, 99).page).toBe(4);
  });

  it("handles empty list", () => {
    const empty = paginateWorkIntakeList([], 1);
    expect(empty.items).toHaveLength(0);
    expect(empty.rangeLabel).toBe("0 din 0");
    expect(empty.pageLabel).toBe("Pagina 1 din 1");
  });
});

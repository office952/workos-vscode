import { describe, it, expect } from "vitest";
import {
  intakeBreadcrumb,
  intakeDetailBreadcrumb,
  quotesBreadcrumb,
  quoteDetailBreadcrumb,
  ordersBreadcrumb,
  orderDetailBreadcrumb,
  productionBreadcrumb,
  executionBreadcrumb,
  reportsBreadcrumb,
  shopFloorBreadcrumb,
  operatorBreadcrumb,
} from "./FlowBreadcrumb";

describe("FlowBreadcrumb helpers", () => {
  it("intakeBreadcrumb returns single active item", () => {
    const items = intakeBreadcrumb();
    expect(items).toHaveLength(1);
    expect(items[0].label).toBe("Cereri");
    expect(items[0].active).toBe(true);
  });

  it("intakeDetailBreadcrumb includes parent link and active detail", () => {
    const items = intakeDetailBreadcrumb("R-042");
    expect(items).toHaveLength(2);
    expect(items[0].to).toBe("/intake");
    expect(items[0].active).toBeUndefined();
    expect(items[1].label).toContain("R-042");
    expect(items[1].active).toBe(true);
  });

  it("intakeDetailBreadcrumb without id uses default label", () => {
    const items = intakeDetailBreadcrumb();
    expect(items[1].label).toBe("Detaliu Cerere");
  });

  it("quotesBreadcrumb links back to intake", () => {
    const items = quotesBreadcrumb();
    expect(items).toHaveLength(2);
    expect(items[0].to).toBe("/intake");
    expect(items[1].label).toBe("Oferte");
    expect(items[1].active).toBe(true);
  });

  it("quoteDetailBreadcrumb has 3 levels", () => {
    const items = quoteDetailBreadcrumb("Q-007");
    expect(items).toHaveLength(3);
    expect(items[0].to).toBe("/intake");
    expect(items[1].to).toBe("/quotes");
    expect(items[2].label).toContain("Q-007");
    expect(items[2].active).toBe(true);
  });

  it("ordersBreadcrumb has 3 levels", () => {
    const items = ordersBreadcrumb();
    expect(items).toHaveLength(3);
    expect(items[2].label).toBe("Comenzi");
    expect(items[2].active).toBe(true);
  });

  it("orderDetailBreadcrumb has 4 levels", () => {
    const items = orderDetailBreadcrumb("CMD-001");
    expect(items).toHaveLength(4);
    expect(items[2].to).toBe("/orders");
    expect(items[3].label).toContain("CMD-001");
    expect(items[3].active).toBe(true);
  });

  it("productionBreadcrumb links to orders", () => {
    const items = productionBreadcrumb();
    expect(items).toHaveLength(2);
    expect(items[0].to).toBe("/orders");
    expect(items[1].label).toBe("Producție");
    expect(items[1].active).toBe(true);
  });

  it("executionBreadcrumb has 3 levels", () => {
    const items = executionBreadcrumb();
    expect(items).toHaveLength(3);
    expect(items[0].to).toBe("/orders");
    expect(items[1].to).toBe("/execution");
    expect(items[2].label).toBe("Realitate Execuție");
    expect(items[2].active).toBe(true);
  });

  it("reportsBreadcrumb links to production", () => {
    const items = reportsBreadcrumb();
    expect(items).toHaveLength(2);
    expect(items[0].to).toBe("/execution");
    expect(items[1].label).toBe("Rapoarte");
    expect(items[1].active).toBe(true);
  });

  it("shopFloorBreadcrumb links to production", () => {
    const items = shopFloorBreadcrumb();
    expect(items).toHaveLength(2);
    expect(items[0].to).toBe("/execution");
    expect(items[1].label).toBe("Shop Floor");
    expect(items[1].active).toBe(true);
  });

  it("operatorBreadcrumb links to production", () => {
    const items = operatorBreadcrumb();
    expect(items).toHaveLength(2);
    expect(items[0].to).toBe("/execution");
    expect(items[1].label).toBe("Operator");
    expect(items[1].active).toBe(true);
  });

  it("all breadcrumbs have exactly one active item (the last)", () => {
    const allCrumbs = [
      intakeBreadcrumb(),
      intakeDetailBreadcrumb("X"),
      quotesBreadcrumb(),
      quoteDetailBreadcrumb("X"),
      ordersBreadcrumb(),
      orderDetailBreadcrumb("X"),
      productionBreadcrumb(),
      executionBreadcrumb(),
      reportsBreadcrumb(),
      shopFloorBreadcrumb(),
      operatorBreadcrumb(),
    ];
    for (const crumbs of allCrumbs) {
      const activeItems = crumbs.filter((c) => c.active);
      expect(activeItems).toHaveLength(1);
      expect(crumbs[crumbs.length - 1].active).toBe(true);
    }
  });

  it("multi-level breadcrumbs: non-active items always have a 'to' link", () => {
    const multiLevel = [
      intakeDetailBreadcrumb("X"),
      quotesBreadcrumb(),
      quoteDetailBreadcrumb("X"),
      ordersBreadcrumb(),
      orderDetailBreadcrumb("X"),
      productionBreadcrumb(),
      executionBreadcrumb(),
      reportsBreadcrumb(),
      shopFloorBreadcrumb(),
      operatorBreadcrumb(),
    ];
    for (const crumbs of multiLevel) {
      for (const item of crumbs) {
        if (!item.active) {
          expect(item.to).toBeDefined();
          expect(item.to!.startsWith("/")).toBe(true);
        }
      }
    }
  });
});
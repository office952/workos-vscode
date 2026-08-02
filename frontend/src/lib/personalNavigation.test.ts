import { describe, expect, it } from "vitest";
import { findPersonalNavItem, personalNavItems } from "./personalNavigation";

describe("personalNavigation", () => {
  it("links Angajați to /employees (operational, not HR demo)", () => {
    const item = findPersonalNavItem("Angajați");
    expect(item?.to).toBe("/employees");
  });

  it("links Evidență HR to /employees-records", () => {
    const item = findPersonalNavItem("Evidență HR");
    expect(item?.to).toBe("/employees-records");
  });

  it("links Plăți to /employee-payments", () => {
    const item = findPersonalNavItem("Plăți");
    expect(item?.to).toBe("/employee-payments");
  });

  it("does not point Angajați at the HR records route", () => {
    const item = findPersonalNavItem("Angajați");
    expect(item?.to).not.toBe("/employees-records");
  });

  it("lists operational Angajați before Evidență HR", () => {
    const labels = personalNavItems.map((item) => item.label);
    expect(labels.indexOf("Angajați")).toBeLessThan(labels.indexOf("Evidență HR"));
  });

  it("drops registry chrome from labels", () => {
    for (const item of personalNavItems) {
      expect(item.label.toLowerCase()).not.toContain("registry");
    }
  });
});

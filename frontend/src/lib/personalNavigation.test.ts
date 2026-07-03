import { describe, expect, it } from "vitest";
import { findPersonalNavItem, personalNavItems } from "./personalNavigation";

describe("personalNavigation", () => {
  it("links Angajați operaționali to /employees", () => {
    const item = findPersonalNavItem("Angajați operaționali");
    expect(item?.to).toBe("/employees");
  });

  it("links Evidență internă HR to /employees-records", () => {
    const item = findPersonalNavItem("Evidență internă HR");
    expect(item?.to).toBe("/employees-records");
  });

  it("links Plăți angajați to /employee-payments", () => {
    const item = findPersonalNavItem("Plăți angajați");
    expect(item?.to).toBe("/employee-payments");
  });

  it("does not expose a generic Angajați label pointing at demo HR", () => {
    const generic = personalNavItems.find((item) => item.label === "Angajati" || item.label === "Angajați");
    expect(generic).toBeUndefined();
  });

  it("lists operational registry before HR demo", () => {
    const labels = personalNavItems.map((item) => item.label);
    expect(labels.indexOf("Angajați operaționali")).toBeLessThan(
      labels.indexOf("Evidență internă HR")
    );
  });
});

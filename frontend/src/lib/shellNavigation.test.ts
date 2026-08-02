import { describe, expect, it } from "vitest";
import { projectNavSectionsForRole, projectedNavLabels, SHELL_NAV_SECTIONS } from "./shellNavigation";
import type { Role } from "./rbac";

describe("shellNavigation — Romanian-first role projection", () => {
  it("defines expected IA group titles", () => {
    const titles = SHELL_NAV_SECTIONS.map((s) => s.title);
    expect(titles).toEqual([
      "Lucrări",
      "Producție",
      "Oameni",
      "Resurse",
      "Relații",
      "Management",
      "Administrare",
      "DEV tooling",
    ]);
  });

  it("never exposes (registry) in labels", () => {
    for (const section of SHELL_NAV_SECTIONS) {
      for (const item of section.items) {
        expect(item.label.toLowerCase()).not.toContain("registry");
      }
    }
  });

  it("viewer sees only Control producție", () => {
    const labels = projectedNavLabels("viewer");
    expect(labels).toEqual(["Control producție"]);
  });

  it("operator primary ops home is Atelier + shop surfaces (no Cereri/Oferte)", () => {
    const labels = projectedNavLabels("operator");
    expect(labels).toContain("Atelier");
    expect(labels).toContain("Shop Floor");
    expect(labels).toContain("Operator");
    expect(labels).toContain("Control producție");
    expect(labels).not.toContain("Cereri");
    expect(labels).not.toContain("Oferte");
    expect(labels).not.toContain("Prețuri");
    expect(labels).not.toContain("Guvernanță");
  });

  it("sales sees Lucrări/Relații without HR money or Administrare", () => {
    const labels = projectedNavLabels("sales");
    expect(labels).toContain("Cereri");
    expect(labels).toContain("Produse");
    expect(labels).toContain("Oferte");
    expect(labels).toContain("Clienți");
    expect(labels).toContain("Planificare");
    expect(labels).not.toContain("Ops-Graph");
    expect(labels).not.toContain("Angajați");
    expect(labels).not.toContain("Plăți");
    expect(labels).not.toContain("Prețuri");
    expect(labels).not.toContain("Setări");
    expect(labels).not.toContain("Harta");
  });

  it("manager sees Ops-Graph and HR but not Prețuri/Avansuri/Administrare", () => {
    const labels = projectedNavLabels("manager");
    expect(labels).toContain("Ops-Graph");
    expect(labels).toContain("Angajați");
    expect(labels).toContain("Evidență HR");
    expect(labels).toContain("Plăți");
    expect(labels).not.toContain("Prețuri");
    expect(labels).not.toContain("Avansuri");
    expect(labels).not.toContain("Setări");
    expect(labels).not.toContain("Guvernanță");
  });

  it("admin sees Prețuri, Avansuri, Administrare", () => {
    const labels = projectedNavLabels("admin");
    expect(labels).toContain("Prețuri");
    expect(labels).toContain("Avansuri");
    expect(labels).toContain("Harta");
    expect(labels).toContain("Guvernanță");
    expect(labels).toContain("Setări");
  });

  it("hides empty sections after projection", () => {
    const sections = projectNavSectionsForRole("viewer");
    expect(sections).toHaveLength(1);
    expect(sections[0].id).toBe("productie");
  });

  it("keeps stable route URLs for core items", () => {
    const byLabel = new Map<string, string>();
    for (const section of SHELL_NAV_SECTIONS) {
      for (const item of section.items) {
        byLabel.set(item.label, item.to);
      }
    }
    expect(byLabel.get("Cereri")).toBe("/intake");
    expect(byLabel.get("Produse")).toBe("/product-system/products");
    expect(byLabel.get("Planificare")).toBe("/execution");
    expect(byLabel.get("Atelier")).toBe("/tablet");
    expect(byLabel.get("Control producție")).toBe("/dashboard");
    expect(byLabel.get("Prețuri")).toBe("/inventory/pricing");
  });

  it.each(["viewer", "operator", "sales", "manager", "admin"] as Role[])(
    "role %s projection is deterministic",
    (role) => {
      expect(projectedNavLabels(role)).toEqual(projectedNavLabels(role));
    },
  );
});

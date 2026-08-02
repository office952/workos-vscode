import { describe, expect, it } from "vitest";
import {
  CANONICAL_PRODUCTION_HOME,
  getRoleHomePath,
  pathAllowedForRole,
  projectNavSectionsForRole,
  projectedNavLabels,
  SHELL_NAV_SECTIONS,
} from "./shellNavigation";
import type { Role } from "./rbac";

describe("shellNavigation — U7 role projection + production home", () => {
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

  it("canonical production home is shop-floor Atelier", () => {
    expect(CANONICAL_PRODUCTION_HOME).toBe("/shop-floor");
    const atelier = SHELL_NAV_SECTIONS.flatMap((s) => s.items).find(
      (i) => i.label === "Atelier",
    );
    expect(atelier?.to).toBe("/shop-floor");
    expect(atelier?.productionPrimary).toBe(true);
  });

  it("Control producție lives under Management (not peer production home)", () => {
    const management = SHELL_NAV_SECTIONS.find((s) => s.id === "management");
    expect(management?.items.some((i) => i.label === "Control producție")).toBe(
      true,
    );
    const productie = SHELL_NAV_SECTIONS.find((s) => s.id === "productie");
    expect(productie?.items.some((i) => i.label === "Control producție")).toBe(
      false,
    );
  });

  it("never exposes (registry) in labels", () => {
    for (const section of SHELL_NAV_SECTIONS) {
      for (const item of section.items) {
        expect(item.label.toLowerCase()).not.toContain("registry");
      }
    }
  });

  it("viewer sees only Control producție under Management", () => {
    const labels = projectedNavLabels("viewer");
    expect(labels).toEqual(["Control producție"]);
    const sections = projectNavSectionsForRole("viewer");
    expect(sections).toHaveLength(1);
    expect(sections[0].id).toBe("management");
  });

  it("operator primary ops home is Atelier without Control/Cereri/Oferte", () => {
    const labels = projectedNavLabels("operator");
    expect(labels).toContain("Atelier");
    expect(labels).toContain("Acțiune task");
    expect(labels).toContain("Stații");
    expect(labels).not.toContain("Control producție");
    expect(labels).not.toContain("Shop Floor");
    expect(labels).not.toContain("Cereri");
    expect(labels).not.toContain("Oferte");
    expect(labels).not.toContain("Prețuri");
    expect(labels).not.toContain("Guvernanță");
    expect(getRoleHomePath("operator")).toBe("/shop-floor");
  });

  it("sales home is Oferte; Lucrări without HR money or Administrare", () => {
    const labels = projectedNavLabels("sales");
    expect(labels).toContain("Cereri");
    expect(labels).toContain("Produse");
    expect(labels).toContain("Oferte");
    expect(labels).toContain("Clienți");
    expect(labels).toContain("Planificare");
    expect(labels).toContain("Control producție");
    expect(labels).not.toContain("Ops-Graph");
    expect(labels).not.toContain("Angajați");
    expect(labels).not.toContain("Plăți");
    expect(labels).not.toContain("Prețuri");
    expect(labels).not.toContain("Setări");
    expect(getRoleHomePath("sales")).toBe("/quotes");
  });

  it("manager sees Ops-Graph and HR but not Prețuri/Avansuri/Administrare", () => {
    const labels = projectedNavLabels("manager");
    expect(labels).toContain("Atelier");
    expect(labels).toContain("Ops-Graph");
    expect(labels).toContain("Angajați");
    expect(labels).toContain("Evidență HR");
    expect(labels).toContain("Plăți");
    expect(labels).toContain("Control producție");
    expect(labels).not.toContain("Prețuri");
    expect(labels).not.toContain("Avansuri");
    expect(labels).not.toContain("Setări");
    expect(labels).not.toContain("Guvernanță");
    expect(getRoleHomePath("manager")).toBe("/shop-floor");
  });

  it("admin sees Prețuri, Avansuri, Administrare; home is Control", () => {
    const labels = projectedNavLabels("admin");
    expect(labels).toContain("Prețuri");
    expect(labels).toContain("Avansuri");
    expect(labels).toContain("Harta");
    expect(labels).toContain("Guvernanță");
    expect(labels).toContain("Setări");
    expect(labels).toContain("Atelier");
    expect(getRoleHomePath("admin")).toBe("/dashboard");
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
    expect(byLabel.get("Atelier")).toBe("/shop-floor");
    expect(byLabel.get("Stații")).toBe("/tablet");
    expect(byLabel.get("Acțiune task")).toBe("/operator");
    expect(byLabel.get("Control producție")).toBe("/dashboard");
    expect(byLabel.get("Prețuri")).toBe("/inventory/pricing");
  });

  it("pathAllowedForRole blocks pricing for operator and allows atelier", () => {
    expect(pathAllowedForRole("operator", "/shop-floor")).toBe(true);
    expect(pathAllowedForRole("operator", "/operator")).toBe(true);
    expect(pathAllowedForRole("operator", "/inventory/pricing")).toBe(false);
    expect(pathAllowedForRole("operator", "/dashboard")).toBe(false);
    expect(pathAllowedForRole("admin", "/inventory/pricing")).toBe(true);
    expect(pathAllowedForRole("sales", "/execution/880041")).toBe(true);
    expect(pathAllowedForRole("operator", "/execution/880041")).toBe(false);
  });

  it("pathAllowedForRole allows Intake V6 for intake roles, not demos-only", () => {
    expect(pathAllowedForRole("sales", "/intake-v6/operator")).toBe(true);
    expect(pathAllowedForRole("manager", "/intake-v6/ws-1/operator")).toBe(true);
    expect(pathAllowedForRole("admin", "/intake-v6/operator")).toBe(true);
    expect(pathAllowedForRole("operator", "/intake-v6/operator")).toBe(false);
    expect(pathAllowedForRole("viewer", "/intake-v6/operator")).toBe(false);
    // /demo remains demos-gated
    expect(pathAllowedForRole("sales", "/demo/foo")).toBe(false);
  });

  it("does not expose Intake V6 (diag) under DEV tooling", () => {
    const labels = projectedNavLabels("admin");
    expect(labels).not.toContain("Intake V6 (diag)");
  });

  it.each(["viewer", "operator", "sales", "manager", "admin"] as Role[])(
    "role %s projection is deterministic",
    (role) => {
      expect(projectedNavLabels(role)).toEqual(projectedNavLabels(role));
      expect(getRoleHomePath(role)).toBeTruthy();
    },
  );
});

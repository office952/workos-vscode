import { describe, expect, it } from "vitest";
import {
  isContractError,
  isEmployeeLinkError,
  mapMobileTaskErrorMessage,
} from "@/lib/employeeMobileV2TaskErrors";

describe("employeeMobileV2TaskErrors", () => {
  it("maps production_release_blocked distinctly", () => {
    expect(
      mapMobileTaskErrorMessage({ code: "production_release_blocked", message: "raw" }),
    ).toContain("Producția este blocată");
  });

  it("maps contract errors distinctly from empty state", () => {
    const err = { code: "MOBILE_V2_TASK_ENVELOPE_MISSING", message: "x" };
    expect(mapMobileTaskErrorMessage(err)).toContain("Planul de execuție V2");
    expect(isContractError(err)).toBe(true);
  });

  it("maps employee-link error distinctly from no tasks", () => {
    const err = { code: "employee_link_missing", message: "x" };
    expect(mapMobileTaskErrorMessage(err)).toContain("profil de angajat");
    expect(isEmployeeLinkError(err)).toBe(true);
  });

  it("maps network failure distinctly", () => {
    expect(mapMobileTaskErrorMessage(new TypeError("Failed to fetch"))).toContain("serverul");
  });

  it("maps order and task not found", () => {
    expect(mapMobileTaskErrorMessage({ code: "order_not_found" })).toContain("Comanda");
    expect(mapMobileTaskErrorMessage({ code: "task_not_found" })).toContain("Taskul");
  });
});

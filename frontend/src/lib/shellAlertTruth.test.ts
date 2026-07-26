import { describe, expect, it } from "vitest";
import { resolveShellCriticalCount } from "@/lib/shellAlertTruth";

describe("resolveShellCriticalCount", () => {
  it("hides critical count when mock mode is off", () => {
    expect(
      resolveShellCriticalCount(false, [{ severity: "critical", resolvedAt: null }]),
    ).toBe(0);
  });

  it("counts unresolved critical only in explicit mock mode", () => {
    expect(
      resolveShellCriticalCount(true, [
        { severity: "critical", resolvedAt: null },
        { severity: "critical", resolvedAt: "2026-07-01" },
        { severity: "warning", resolvedAt: null },
      ]),
    ).toBe(1);
  });
});

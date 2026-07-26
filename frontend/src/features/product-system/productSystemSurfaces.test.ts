import { describe, expect, it } from "vitest";
import {
  PS_SURFACE_INSET,
  PS_SURFACE_INPUT,
  PS_SURFACE_PANEL,
  PS_SURFACE_QUIET,
  PS_SURFACE_ROW,
} from "./productSystemSurfaces";

describe("productSystemSurfaces — WorkOS token aliases", () => {
  it("uses opaque WorkOS content surface for L1 panels", () => {
    expect(PS_SURFACE_PANEL).toContain("bg-wo-surface-raised");
    expect(PS_SURFACE_PANEL).toContain("border-wo-border-subtle");
    expect(PS_SURFACE_PANEL).not.toMatch(/\/70|\/50/);
  });

  it("keeps L2 inset as inset wash, not a third black well", () => {
    expect(PS_SURFACE_INSET).toContain("bg-wo-surface-inset");
    expect(PS_SURFACE_ROW).toContain("bg-transparent");
    expect(PS_SURFACE_ROW).not.toContain("#0A0F1A");
    expect(PS_SURFACE_ROW).not.toContain("#0D1321");
  });

  it("maps inputs to WorkOS input fill", () => {
    expect(PS_SURFACE_INPUT).toContain("bg-wo-surface-input");
    expect(PS_SURFACE_QUIET).toContain("bg-wo-surface-inset");
    expect(PS_SURFACE_QUIET).not.toContain("#0B1220");
  });
});

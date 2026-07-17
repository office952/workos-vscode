import { describe, expect, it } from "vitest";
import {
  ALL_FINISH_MOUNTING_OWNERSHIP_SETTINGS,
  BAR_MOUNTING_METHODS,
  deriveMetalSupportRequiredAlias,
  diagnoseMountingOwnershipConflicts,
  FINISH_OWNERSHIP_SUMMARY_RO,
  LETTERS_OWNERSHIP_OWNER_GATES,
  MOUNTING_FIELD_MODEL_V1,
  MOUNTING_OWNERSHIP_SUMMARY_RO,
} from "@/lib/lettersFinishMountingOwnership";

describe("lettersFinishMountingOwnership", () => {
  it("keeps mounting_system as canonical V1 method and mounting_method as TARGET name only", () => {
    expect(MOUNTING_FIELD_MODEL_V1.mounting_system.status).toBe("CURRENT");
    expect(MOUNTING_FIELD_MODEL_V1.mounting_system.role).toBe("canonical_mounting_method");
    expect(MOUNTING_FIELD_MODEL_V1.mounting_method.status).toBe("TARGET");
    expect(MOUNTING_FIELD_MODEL_V1.metal_support_required.status).toBe("COMPATIBILITY_ALIAS");
    expect(MOUNTING_FIELD_MODEL_V1.mounting_scope.status).toBe("CURRENT");
    expect(MOUNTING_FIELD_MODEL_V1.mounting_solution.status).toBe("CURRENT");
  });

  it("marks sold FINISH/MOUNTING blocked and owner gates not approved", () => {
    const finishSold = ALL_FINISH_MOUNTING_OWNERSHIP_SETTINGS.find((r) => r.id === "finish.sold_module");
    const mountingSold = ALL_FINISH_MOUNTING_OWNERSHIP_SETTINGS.find((r) => r.id === "mounting.sold_module");
    expect(finishSold?.runtime_status).toBe("BLOCKED");
    expect(mountingSold?.runtime_status).toBe("BLOCKED");
    expect(LETTERS_OWNERSHIP_OWNER_GATES.every((g) => g.status === "NOT_APPROVED")).toBe(true);
    expect(FINISH_OWNERSHIP_SUMMARY_RO.soldStatusRo).toMatch(/Activare neaprobată/);
    expect(MOUNTING_OWNERSHIP_SUMMARY_RO.soldStatusRo).toMatch(/blocat/);
  });

  it("separates CURRENT vs TARGET ownership rows", () => {
    const targets = ALL_FINISH_MOUNTING_OWNERSHIP_SETTINGS.filter((r) => r.current_or_target === "TARGET");
    const currents = ALL_FINISH_MOUNTING_OWNERSHIP_SETTINGS.filter((r) => r.current_or_target === "CURRENT");
    expect(targets.length).toBeGreaterThan(0);
    expect(currents.length).toBeGreaterThan(0);
    expect(targets.every((r) => r.runtime_status === "TARGET" || r.noteRo.length > 0)).toBe(true);
  });

  it("assigns RETURN Oracal/RAL to COMPONENT and face vinyl intent to MODULE FINISH target", () => {
    const ret = ALL_FINISH_MOUNTING_OWNERSHIP_SETTINGS.find((r) => r.id === "finish.return_oracal_ral");
    const face = ALL_FINISH_MOUNTING_OWNERSHIP_SETTINGS.find((r) => r.id === "finish.face_intent");
    expect(ret?.canonical_owner).toBe("COMPONENT");
    expect(ret?.ownerDetailRo).toMatch(/RETURN-CANT/);
    expect(face?.canonical_owner).toBe("MODULE");
    expect(face?.current_or_target).toBe("TARGET");
  });

  it("keeps metal_support_required as derived alias with warnings only", () => {
    expect(deriveMetalSupportRequiredAlias({ mounting_system: "steel_bars" })).toBe(true);
    expect(deriveMetalSupportRequiredAlias({ mounting_system: "direct_wall" })).toBe(false);
    expect(BAR_MOUNTING_METHODS).toContain("steel_bars");
    const diags = diagnoseMountingOwnershipConflicts({
      mounting_system: "direct_wall",
      metal_support_required: true,
    });
    expect(diags[0]?.severity).toBe("compatibility_warning");
    expect(diags[0]?.canonicalWins).toBe(true);
  });

  it("documents mounting map narrowing as not approved", () => {
    const mapRow = ALL_FINISH_MOUNTING_OWNERSHIP_SETTINGS.find((r) => r.id === "mounting.runtime_map");
    expect(mapRow?.activation_gate).toBe("MOUNTING_MAP_NARROWING_OWNER_GATE");
    expect(mapRow?.noteRo).toMatch(/aprobată|neschimbată/i);
  });
});

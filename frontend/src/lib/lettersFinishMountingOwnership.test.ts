import { describe, expect, it } from "vitest";
import {
  ALL_FINISH_MOUNTING_OWNERSHIP_SETTINGS,
  BAR_MOUNTING_METHODS,
  deriveMetalSupportRequiredAlias,
  diagnoseMountingOwnershipConflicts,
  FINISH_OWNERSHIP_SUMMARY_RO,
  FINISH_RUNTIME_MAP,
  LETTERS_OWNERSHIP_OWNER_GATES,
  MOUNTING_FIELD_MODEL_V1,
  MOUNTING_OWNERSHIP_SUMMARY_RO,
  MOUNTING_RUNTIME_MAP_NARROWED,
  RUNTIME_RESPONSIBILITY_CODES,
  SNAPSHOT_WRITER_VERSION,
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

  it("marks sold FINISH/MOUNTING blocked; narrowing gates approved", () => {
    const finishSold = ALL_FINISH_MOUNTING_OWNERSHIP_SETTINGS.find((r) => r.id === "finish.sold_module");
    const mountingSold = ALL_FINISH_MOUNTING_OWNERSHIP_SETTINGS.find((r) => r.id === "mounting.sold_module");
    expect(finishSold?.runtime_status).toBe("BLOCKED");
    expect(mountingSold?.runtime_status).toBe("BLOCKED");
    expect(LETTERS_OWNERSHIP_OWNER_GATES.find((g) => g.id === "SOLD_CHIP_ACTIVATION_OWNER_GATE")?.status).toBe(
      "NOT_APPROVED",
    );
    expect(LETTERS_OWNERSHIP_OWNER_GATES.find((g) => g.id === "MOUNTING_MAP_NARROWING_OWNER_GATE")?.status).toBe(
      "APPROVED",
    );
    expect(LETTERS_OWNERSHIP_OWNER_GATES.find((g) => g.id === "MINI_MODULE_SPLIT_OWNER_GATE")?.status).toBe(
      "APPROVED",
    );
    expect(FINISH_OWNERSHIP_SUMMARY_RO.soldStatusRo).toMatch(/Activare neaprobată/);
    expect(MOUNTING_OWNERSHIP_SUMMARY_RO.soldStatusRo).toMatch(/blocat/);
  });

  it("documents narrowed mounting map and precise runtime codes", () => {
    expect([...MOUNTING_RUNTIME_MAP_NARROWED]).toEqual(["structura_suport", "sablon_montaj"]);
    expect([...FINISH_RUNTIME_MAP]).toEqual(["finisaje"]);
    expect(RUNTIME_RESPONSIBILITY_CODES.packaging).toBe("ambalare_livrare_montaj");
    expect(SNAPSHOT_WRITER_VERSION).toBe("active_scope_snapshot/v2");
    const mapRow = ALL_FINISH_MOUNTING_OWNERSHIP_SETTINGS.find((r) => r.id === "mounting.runtime_map");
    expect(mapRow?.noteRo).toMatch(/APROBAT|îngust/i);
  });

  it("assigns RETURN Oracal/RAL to COMPONENT and face vinyl to SURFACE_FINISH", () => {
    const ret = ALL_FINISH_MOUNTING_OWNERSHIP_SETTINGS.find((r) => r.id === "finish.return_oracal_ral");
    const face = ALL_FINISH_MOUNTING_OWNERSHIP_SETTINGS.find((r) => r.id === "finish.face_intent");
    expect(ret?.canonical_owner).toBe("COMPONENT");
    expect(ret?.ownerDetailRo).toMatch(/RETURN-CANT/);
    expect(face?.canonical_owner).toBe("MODULE");
    expect(face?.responsibility).toBe("SURFACE_FINISH");
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
});

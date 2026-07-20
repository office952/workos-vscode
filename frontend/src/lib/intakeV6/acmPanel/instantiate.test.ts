import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { analyzeSvgString } from "@/lib/svgAnalyzer";
import { confirmAllSuggestedLayerRoles } from "../intakeV6LayerRoleBridge";
import {
  buildAtomicAcmPanelInstantiationPatch,
  buildAtomicAcmPanelClearPatch,
} from "./instantiate";
import { assertNoAutoMountRelations } from "./relations";
import { mergeLetterLogoBindingsPreservingAcmPanelDomain } from "./preserve";

const ACM = path.join(
  process.env.USERPROFILE || process.env.HOME || "",
  "Desktop",
  "fisiere-teste-svg",
  "litere-cu-fundal-acm-segmentat.svg",
);

const bindables = [
  {
    component_template_code: "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
    owner_label: "Panou Alucobond casetat",
    geometry_role: "SUPPORT_CONTOUR",
    available: true,
  },
  {
    component_template_code: "TPL-VOLUMETRIC-FACE_v1",
    geometry_role: "LETTER_VECTOR_SET",
    available: true,
  },
] as never;

describe("AcmPanel atomic instantiation", () => {
  it("upserts proposed association/technical without confirming composition or selection", () => {
    const text = readFileSync(ACM, "utf8");
    const { report } = analyzeSvgString(text, "litere-cu-fundal-acm-segmentat.svg", text.length);
    const confirmed = confirmAllSuggestedLayerRoles(report.layerRoleConfirmation, report);

    const result = buildAtomicAcmPanelInstantiationPatch({
      report,
      confirmation: confirmed,
      finishSetup: null,
      bindables,
      svgSourceHash: "test-hash",
    });

    expect(result.ok).toBe(true);
    expect(result.finishPatch?.acm_panel_domain_action).toBe("upsert");
    expect(result.instance?.role_status).toBe("confirmed");
    expect(result.instance?.association_status).toBe("proposed");
    expect(result.instance?.technical_configuration_status).toBe("proposed");
    expect(result.instance?.composition_status).toBe("unconfirmed");

    const selection = result.finishPatch?.svg_support_selection as {
      status?: string;
      acm_panel_instance?: { component_instance_id?: string };
      component_relations?: unknown[];
    };
    expect(selection?.status).toBe("proposed");
    expect(selection?.status).not.toBe("confirmed");
    expect(selection?.acm_panel_instance?.component_instance_id).toBeTruthy();
    expect((selection?.component_relations ?? []).length).toBeGreaterThan(0);

    expect(result.finishPatch?.mounting_solution).toBeTruthy();
    expect(
      (result.finishPatch?.svg_component_bindings as { geometry_role?: string }[])?.some(
        (b) => b.geometry_role === "SUPPORT_CONTOUR",
      ),
    ).toBe(true);

    const seg = result.finishPatch?.segmented_background as {
      status?: string;
      panels?: unknown[];
    };
    expect(seg?.status).toBe("PROPOSED");
    expect((seg?.panels ?? []).length).toBeGreaterThanOrEqual(2);

    const auth = (selection as { field_authority?: Record<string, string> }).field_authority;
    expect(auth?.acm_thickness_mm).toBe("catalog_default");
    expect(auth?.fold_count).toBe("catalog_default");
    expect(auth?.panel_geometry).toBe("detected");

    expect(assertNoAutoMountRelations(result.instance?.relations ?? [])).toBe(true);
    expect(
      result.instance?.relations.every(
        (r) => r.relation_type !== "mounts_on" || r.provenance === "operator",
      ),
    ).toBe(true);
  });

  it("clear action removes ACM shell", () => {
    const cleared = buildAtomicAcmPanelClearPatch({ finishSetup: null });
    expect(cleared.acm_panel_domain_action).toBe("clear");
    expect(cleared.acm_panel_instance).toBeNull();
    expect(cleared.mounting_solution).toBeNull();
  });

  it("preserve merge keeps SUPPORT when letter sync runs", () => {
    const finish = {
      svg_support_selection: { schema: "svg_support_selection_v1", status: "proposed" },
      mounting_solution: { template_code: "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1" },
      acm_panel_instance: { schema: "acm_panel_component_instance_v1" },
      svg_component_bindings: [
        {
          schema: "svg_component_bindings_v1",
          binding_id: "bind_support_x",
          geometry_role: "SUPPORT_CONTOUR",
          component_template_code: "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
          status: "DRAFT",
        },
      ],
    };
    const merged = mergeLetterLogoBindingsPreservingAcmPanelDomain({
      letterLogoBindings: [
        {
          schema: "svg_component_bindings_v1",
          binding_id: "bind_letters",
          geometry_role: "LETTER_VECTOR_SET",
          component_template_code: "TPL-VOLUMETRIC-FACE_v1",
          status: "CONFIRMED",
        } as never,
      ],
      finishSetup: finish,
      supportRoleStillConfirmed: true,
    });
    expect(merged.acm_panel_domain_action).toBe("preserve");
    expect(merged.svg_component_bindings.some((b) => b.geometry_role === "SUPPORT_CONTOUR")).toBe(
      true,
    );
    expect(merged.svg_support_selection).toBeTruthy();
    expect(merged.mounting_solution).toBeTruthy();
  });
});

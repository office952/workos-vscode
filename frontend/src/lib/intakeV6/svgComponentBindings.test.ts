import { describe, expect, it } from "vitest";
import {
  bindingFromSupportSelection,
  buildLayerRoleComponentBindings,
  filterBindableForUi,
  letterBinding,
  ownerFacingComponentProductLabel,
  readSvgComponentBindings,
  upsertBinding,
} from "./svgComponentBindings";
import { emptySvgSupportSelection } from "@/lib/svgAnalyzer";

describe("svgComponentBindings", () => {
  it("builds letter binding with LETTER_VECTOR_SET", () => {
    const b = letterBinding({
      layerIds: ["layer-a"],
      sourceSvgHash: "h1",
      componentCode: "TPL-VOLUMETRIC-FACE_v1",
      selectionMode: "LAYER_OR_GROUP",
    });
    expect(b.geometry_role).toBe("LETTER_VECTOR_SET");
    expect(b.status).toBe("CONFIRMED");
    expect(b.selected_geometry.layer_ids).toEqual(["layer-a"]);
  });

  it("syncs support selection into SUPPORT_CONTOUR binding", () => {
    const sel = {
      ...emptySvgSupportSelection(),
      status: "confirmed" as const,
      role: "ALUCOBOND_CASED_PANEL" as const,
      contour_id: "cc_60db6024",
      geometry_hash: "60db6024",
      svg_source_hash: "abc",
      casing_profile: {
        fold_count: 2 as const,
        l1_mm: 60,
        l2_mm: 25,
        finished_depth_mm: 60,
      },
      service_corner: "TOP_RIGHT" as const,
      internal_frame_enabled: true,
    };
    const b = bindingFromSupportSelection(sel);
    expect(b?.component_template_code).toBe("TPL-ACM-BOXED-MOUNTING-SUPPORT_v1");
    expect(b?.geometry_role).toBe("SUPPORT_CONTOUR");
  });

  it("filters stale bond and reads bindings from finish", () => {
    const filtered = filterBindableForUi([
      {
        component_template_code: "TPL-BOND-CASETAT",
        owner_label: "stale",
        accepted_geometry_roles: ["SUPPORT_CONTOUR"],
        selection_mode: "CLOSED_CONTOUR",
        cardinality: "MAX_ONE",
        required: false,
        available: true,
        active: false,
        active_by_default: false,
      },
      {
        component_template_code: "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
        owner_label: "Panou Alucobond casetat",
        accepted_geometry_roles: ["SUPPORT_CONTOUR"],
        selection_mode: "CLOSED_CONTOUR",
        cardinality: "MAX_ONE",
        required: false,
        available: true,
        active: false,
        active_by_default: false,
      },
    ]);
    expect(filtered.map((c) => c.component_template_code)).toEqual([
      "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
    ]);
    const finish = {
      svg_component_bindings: [
        letterBinding({
          layerIds: ["a"],
          sourceSvgHash: "h",
          componentCode: "TPL-VOLUMETRIC-FACE_v1",
          selectionMode: "LAYER_OR_GROUP",
        }),
      ],
    };
    expect(readSvgComponentBindings(finish)).toHaveLength(1);
    const next = upsertBinding(finish.svg_component_bindings, {
      ...finish.svg_component_bindings[0],
      binding_id: "bind_letters_a",
    });
    expect(next).toHaveLength(1);
  });

  it("builds layer-role bindings and keeps distinct product labels", () => {
    expect(
      ownerFacingComponentProductLabel({
        component_template_code: "TPL-VOLUMETRIC-FACE_v1",
        owner_label: "Vector litere",
      }),
    ).toBe("Față litere volumetrice");

    const next = buildLayerRoleComponentBindings({
      confirmation: {
        layers: [
          { layerKey: "L1", confirmedRole: "face", confirmationState: "confirmed" },
          { layerKey: "L2", confirmedRole: "printed_artwork", confirmationState: "confirmed" },
        ],
      },
      bindables: [
        {
          component_template_code: "TPL-VOLUMETRIC-FACE_v1",
          owner_label: "Vector litere",
          accepted_geometry_roles: ["LETTER_VECTOR_SET"],
          selection_mode: "LAYER_OR_GROUP",
          cardinality: "MULTI",
          required: true,
          available: true,
          active: true,
          active_by_default: true,
        },
        {
          component_template_code: "TPL-VOLUMETRIC-LOGO_v1",
          owner_label: "Vector logo",
          accepted_geometry_roles: ["LOGO_VECTOR_SET"],
          selection_mode: "LAYER_OR_GROUP",
          cardinality: "MULTI",
          required: false,
          available: true,
          active: false,
          active_by_default: false,
        },
      ],
      sourceSvgHash: "h",
      previous: [
        bindingFromSupportSelection({
          ...emptySvgSupportSelection(),
          status: "confirmed",
          role: "ALUCOBOND_CASED_PANEL",
          contour_id: "cc_1",
          geometry_hash: "g1",
          svg_source_hash: "h",
        })!,
      ],
    });
    expect(next.map((b) => b.geometry_role).sort()).toEqual([
      "LETTER_VECTOR_SET",
      "LOGO_VECTOR_SET",
      "SUPPORT_CONTOUR",
    ]);
  });

  it("allows multiple ACM face-treatment bindings without XOR by component code", () => {
    const support = bindingFromSupportSelection({
      ...emptySvgSupportSelection(),
      status: "confirmed",
      role: "ALUCOBOND_CASED_PANEL",
      contour_id: "cc_1",
      geometry_hash: "g1",
      svg_source_hash: "h",
    })!;
    const cutout = {
      ...support,
      binding_id: "bind_cutout_1",
      geometry_role: "CUTOUT_TEXT" as const,
      face_treatment_code: "FACE-TREATMENT-ROUTED-BACKLIT-CUTOUT",
      selected_geometry: {
        layer_ids: ["cut"],
        group_ids: [],
        element_ids: ["el_cut"],
        geometry_hashes: ["hc"],
        source_svg_hash: "h",
      },
    };
    const insert = {
      ...support,
      binding_id: "bind_insert_1",
      geometry_role: "ACRYLIC_INSERT" as const,
      face_treatment_code: "FACE-TREATMENT-ACRYLIC-INSERT",
      selected_geometry: {
        layer_ids: ["ins"],
        group_ids: [],
        element_ids: ["el_ins"],
        geometry_hashes: ["hi"],
        source_svg_hash: "h",
      },
    };
    let next = upsertBinding([], support);
    next = upsertBinding(next, cutout);
    next = upsertBinding(next, insert);
    expect(next).toHaveLength(3);
    expect(next.map((b) => b.geometry_role).sort()).toEqual([
      "ACRYLIC_INSERT",
      "CUTOUT_TEXT",
      "SUPPORT_CONTOUR",
    ]);
  });
});

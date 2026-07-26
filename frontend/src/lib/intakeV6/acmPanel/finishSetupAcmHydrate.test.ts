import { describe, expect, it } from "vitest";
import {
  hydrateAcmPanelFinishFields,
  mergeAcmPanelFinishHydrate,
} from "./finishSetupAcmHydrate";

describe("finishSetupAcmHydrate", () => {
  const measuredInstance = {
    schema: "acm_panel_component_instance_v1",
    component_instance_id: "acm_qa_double_fold_2000x300",
    production_geometry: {
      schema: "acm_panel_production_geometry_bundle_v1",
      attachments: [
        {
          attachment_id: "att_golden",
          measurement_status: "measured",
          metrics_snapshot: { cut_length_ml: 5.499412 },
        },
      ],
    },
  };

  it("hydrates acm_panel_instance and support selection from finish_setup", () => {
    const hydrated = hydrateAcmPanelFinishFields({
      face_finish_type: "oracal_651",
      return_depth_mm: 60,
      acm_panel_instance: measuredInstance,
      svg_support_selection: { status: "confirmed", role: "SUPPORT_CONTOUR" },
      segmented_background: { status: "CONFIRMED", panels: [] },
    });
    expect(hydrated.acm_panel_instance?.component_instance_id).toBe(
      "acm_qa_double_fold_2000x300",
    );
    expect(
      (hydrated.acm_panel_instance?.production_geometry as { attachments?: unknown[] })
        ?.attachments?.[0],
    ).toMatchObject({ measurement_status: "measured" });
    expect(hydrated.svg_support_selection).toMatchObject({ status: "confirmed" });
    expect(hydrated.segmented_background).toMatchObject({ status: "CONFIRMED" });
  });

  it("merge keeps unrelated finish fields while restoring AcmPanel shell", () => {
    const draft = {
      face_finish_type: "oracal_651",
      return_depth_mm: 60,
      illuminated: true,
      lighting_system_type: "led_modules",
      confirmed: true,
    };
    const merged = mergeAcmPanelFinishHydrate(draft, {
      face_finish_type: "should_not_override_via_helper",
      acm_panel_instance: measuredInstance,
      svg_support_selection: { status: "confirmed" },
    });
    expect(merged.face_finish_type).toBe("oracal_651");
    expect(merged.return_depth_mm).toBe(60);
    expect(merged.illuminated).toBe(true);
    expect(merged.lighting_system_type).toBe("led_modules");
    expect(merged.confirmed).toBe(true);
    expect(merged.acm_panel_instance?.component_instance_id).toBe(
      "acm_qa_double_fold_2000x300",
    );
  });

  it("round-trip: form hydrated from payload would include instance in autosave body", () => {
    const payloadFinish = {
      face_finish_type: "oracal_651",
      return_depth_mm: 100,
      acm_panel_instance: measuredInstance,
      svg_support_selection: { status: "confirmed" },
    };
    // Simulate Review draft that previously dropped acm on hydrate.
    const incompleteAutosaveBody = {
      face_finish_type: payloadFinish.face_finish_type,
      return_depth_mm: payloadFinish.return_depth_mm,
      illuminated: true,
      confirmed: true,
    };
    const fixedBody = mergeAcmPanelFinishHydrate(incompleteAutosaveBody, payloadFinish);
    expect(fixedBody.acm_panel_instance).toEqual(measuredInstance);
    expect(fixedBody.face_finish_type).toBe("oracal_651");
    expect(fixedBody.return_depth_mm).toBe(100);
  });
});

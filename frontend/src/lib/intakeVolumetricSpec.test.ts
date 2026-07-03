import { describe, expect, it } from "vitest";
import {
  deriveVectorMetadataFromFilename,
  suggestWorkTitleFromVectorFilename,
  inferVectorFileType,
  intakeFaceFinishToQuoteCostingType,
  legacyMountingToCanonical,
  normalizeVolumetricIntakeSpecForSave,
  resolveIntakeFaceFinishType,
  resolveIntakeMountingSystem,
} from "./intakeVolumetricSpec";
import { mapProductSpecToVolumetricQuotePrefill } from "./volumetricQuoteInput";

describe("intakeVolumetricSpec", () => {
  it("maps legacy face finish oracal_8500 to costing oracal_651", () => {
    expect(resolveIntakeFaceFinishType({ face_finish: "oracal_8500_translucent" })).toBe(
      "oracal_8500"
    );
    expect(intakeFaceFinishToQuoteCostingType("oracal_8500")).toBe("oracal_651");
  });

  it("maps aluminum premount from legacy metal_structure", () => {
    expect(
      legacyMountingToCanonical({
        mounting_type: "premounted",
        premounting_type: "metal_structure",
        premount_bar_material: "aluminum",
      })
    ).toBe("aluminum_bars");
  });

  it("persists intake_input_pathway on save", () => {
    expect(
      normalizeVolumetricIntakeSpecForSave({
        intake_input_pathway: "vector",
        width_mm: 1000,
      })
    ).toMatchObject({
      intake_input_pathway: "vector",
      width_mm: 1000,
    });
  });

  it("normalizes canonical intake spec with legacy sync", () => {
    expect(
      normalizeVolumetricIntakeSpecForSave({
        face_finish_type: "oracal_651",
        mounting_system: "steel_bars",
        mounting_bar_profile: "30x30x1.5",
        paint_ral_code: "RAL 9005",
        back_bevel_enabled: true,
      })
    ).toMatchObject({
      face_finish_type: "oracal_651",
      face_finish: "oracal_651",
      mounting_system: "steel_bars",
      mounting_type: "premounted",
      premounting_type: "metal_structure",
      premount_bar_material: "steel",
      paint_ral_code: "RAL 9005",
      ral_color: "RAL 9005",
      backing_chamfer: true,
      back_bevel_enabled: true,
    });
  });
});

describe("intake prefill alignment", () => {
  it("prefills Oracal 651 metadata to QuoteWizard", () => {
    expect(
      mapProductSpecToVolumetricQuotePrefill({
        face_finish_type: "oracal_651",
        face_vinyl_color_code: "070",
        face_vinyl_roll_width_mm: 1260,
        return_depth_mm: 60,
      })
    ).toMatchObject({
      face_finish_type: "oracal_651",
      face_vinyl_color_code: "070",
      face_vinyl_roll_width_mm: "1260",
      return_depth_mm: "60",
    });
  });

  it("prefills Oracal 8500 with subtype and costing path", () => {
    expect(
      mapProductSpecToVolumetricQuotePrefill({
        face_finish_type: "oracal_8500",
        face_vinyl_color_code: "731",
        face_vinyl_roll_width_mm: 1000,
      })
    ).toMatchObject({
      face_finish_type: "oracal_651",
      face_finish_subtype: "oracal_8500",
      face_vinyl_color_code: "731",
      face_vinyl_roll_width_mm: "1000",
    });
  });

  it("prefills RAL and steel bars with profile", () => {
    expect(
      mapProductSpecToVolumetricQuotePrefill({
        volume_finish: "paint_after_face_miter_bond",
        paint_ral_code: "RAL 3020",
        paint_tube_count: 3,
        mounting_system: "steel_bars",
        mounting_bar_profile: "30x30x1.5",
        mounting_bar_count: 2,
        width_mm: 4800,
      })
    ).toMatchObject({
      paint_ral_code: "RAL 3020",
      paint_tube_count: "3",
      mounting_system: "steel_bars",
      mounting_bar_profile: "30x30x1.5",
      mounting_bar_count: "2",
      width_mm: "4800",
    });
  });

  it("maps forex template flag without forex mounting_system", () => {
    expect(
      mapProductSpecToVolumetricQuotePrefill({
        mounting_template_enabled: true,
        mounting_system: "direct_wall",
      })
    ).toEqual({
      mounting_system: "direct_wall",
      mounting_template_enabled: "true",
    });
  });

  it("does not fake missing geometry", () => {
    const prefill = mapProductSpecToVolumetricQuotePrefill({
      face_finish_type: "none",
      mounting_system: "direct_wall",
    });
    expect(prefill.letter_face_area_m2).toBeUndefined();
    expect(prefill.letter_perimeter_m).toBeUndefined();
    expect(prefill.letter_count).toBeUndefined();
  });

  it("resolves canonical mounting_system over legacy", () => {
    expect(
      resolveIntakeMountingSystem({
        mounting_system: "aluminum_bars",
        mounting_type: "premounted",
        premounting_type: "metal_structure",
      })
    ).toBe("aluminum_bars");
  });

  it("infers vector file type from extension", () => {
    expect(inferVectorFileType("litere.dwg")).toBe("dwg");
    expect(inferVectorFileType("contur.svg")).toBe("svg");
    expect(inferVectorFileType("paths.dxf")).toBe("dxf");
  });

  it("derives vector metadata without inventing geometry", () => {
    const derived = deriveVectorMetadataFromFilename({}, "litere_fata.dwg");
    expect(derived.vector_file_present).toBe(true);
    expect(derived.vector_file_type).toBe("dwg");
    expect(derived.vector_analysis_status).toBe("attached_unanalyzed");
    expect(derived.letter_face_area_m2).toBeUndefined();
    expect(derived.text).toBe("litere fata");
  });

  it("suggests work title from vector filename and skips generic stems", () => {
    expect(suggestWorkTitleFromVectorFilename("HOTELEXIA.svg")).toBe("HOTELEXIA");
    expect(suggestWorkTitleFromVectorFilename("logo.svg")).toBeUndefined();
    expect(suggestWorkTitleFromVectorFilename("a.svg")).toBeUndefined();
  });

  it("does not overwrite explicit work title when deriving vector metadata", () => {
    const derived = deriveVectorMetadataFromFilename(
      { text: "DEDEMAN" },
      "HOTELEXIA.svg"
    );
    expect(derived.text).toBe("DEDEMAN");
  });

  it("normalizes manual vector review approval", () => {
    expect(
      normalizeVolumetricIntakeSpecForSave({
        vector_file_name: "litere.dwg",
        vector_file_type: "dwg",
        vector_manual_review_approved: true,
        vector_manual_review_notes: "Verificat prepress",
      })
    ).toMatchObject({
      vector_file_name: "litere.dwg",
      vector_file_type: "dwg",
      vector_manual_review_approved: true,
      vector_analysis_status: "manual_review_approved",
      vector_manual_review_notes: "Verificat prepress",
    });
  });

  it("persists svg letter groups and finish assignments on save", () => {
    expect(
      normalizeVolumetricIntakeSpecForSave({
        vector_file_name: "publi-cadru-fx.svg",
        svgLetterGroups: [
          {
            groupId: "fill-e31e24",
            sourceLayerName: "Litere_x0020_volumetrice",
            sourceFillColor: "#E31E24",
            visualLabel: "Grup #E31E24",
            elementIds: ["p1"],
            status: "suggested",
          },
        ],
        letterGroupFinishAssignments: [
          {
            groupId: "fill-e31e24",
            face: { finishType: "oracal" },
            returnCant: { finishType: "white_aluminum" },
            confirmedByOperator: false,
          },
        ],
      })
    ).toMatchObject({
      svgLetterGroups: [{ groupId: "fill-e31e24", sourceFillColor: "#E31E24" }],
      letterGroupFinishAssignments: [{ groupId: "fill-e31e24" }],
    });
  });
});

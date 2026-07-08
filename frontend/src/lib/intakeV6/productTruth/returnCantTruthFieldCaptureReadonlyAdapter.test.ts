import { describe, expect, it } from "vitest"

import { mapReturnCantTruthFieldCaptureReadonlyAdapter } from "./returnCantTruthFieldCaptureReadonlyAdapter"

function entryByKey(
  model: ReturnType<typeof mapReturnCantTruthFieldCaptureReadonlyAdapter>,
  key: string,
) {
  const entry = model.vector_entries.find((candidate) => candidate.source_row_key === key)
  if (!entry) throw new Error(`Missing entry ${key}`)
  return entry
}

describe("mapReturnCantTruthFieldCaptureReadonlyAdapter", () => {
  it("maps Vector Litere Alb 60 mm to stock_color without finish extra pricing key", () => {
    const model = mapReturnCantTruthFieldCaptureReadonlyAdapter({
      letter_group_finishes: [
        {
          group_key: "pseudo:maria",
          layer_name: "maria",
          return_finish_type: "white_aluminum",
          return_depth_mm: 60,
          confirmed: true,
        },
      ],
    })

    const entry = entryByKey(model, "pseudo:maria")
    expect(entry.vector_type).toBe("Vector Litere")
    expect(entry.corrected_semantic_variant).toBe("stock_color")
    expect(entry.stock_color_label).toBe("Alb")
    expect(entry.pricing_keys_required).toEqual(
      expect.arrayContaining([
        "MAT-PROFIL-LATERAL-LITERE-60MM",
        "RETURN_PROFILE_MACHINE_FORMING",
        "RETURN_PROFILE_FACE_BONDING",
      ]),
    )
    expect(entry.pricing_keys_required).not.toContain("MAT-VOPSEA-RAL")
    expect(entry.pricing_keys_required).not.toContain("MAT-ORACAL-651")
    expect(entry.pricing_keys_status).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          slot: "finish_extra",
          key: null,
          status: "not_applicable",
        }),
        expect.objectContaining({
          slot: "material_profile_width",
          key: "MAT-PROFIL-LATERAL-LITERE-60MM",
          status: "present",
        }),
      ]),
    )
  })

  it("creates a separate Vector Logo instance for Alb 60 mm", () => {
    const model = mapReturnCantTruthFieldCaptureReadonlyAdapter({
      artwork_finishes: [
        {
          layer_key: "logo-1",
          layer_name: "Logo 1",
          return_finish_type: "white_aluminum",
          return_depth_mm: 60,
          confirmed: true,
        },
      ],
      layerEvidence: {
        stepOneConfirmedArtworkKeys: ["logo-1"],
      },
    })

    const entry = entryByKey(model, "logo-1")
    expect(entry.vector_type).toBe("Vector Logo")
    expect(entry.corrected_semantic_variant).toBe("stock_color")
    expect(entry.target_component_truth_path_base).toBe("components.return_cant.instances.logo-1")
    expect(entry.confirmation_gap).toBe("STEP_ONE_CONFIRMATION_IS_NOT_COMPONENT_CONFIRMATION")
    expect(entry.warnings).toContain("STEP_ONE_CONFIRMATION_NOT_PROMOTED_TO_COMPONENT_TRUTH")
  })

  it("maps stock color depth variants to the audited Pricing keys and keeps labor generic", () => {
    const depths = [30, 60, 80, 100] as const

    for (const depth of depths) {
      const model = mapReturnCantTruthFieldCaptureReadonlyAdapter({
        letter_group_finishes: [
          {
            group_key: `depth-${depth}`,
            return_finish_type: "black_aluminum",
            return_depth_mm: depth,
          },
        ],
      })
      const entry = entryByKey(model, `depth-${depth}`)
      expect(entry.pricing_keys_status).toEqual(
        expect.arrayContaining([
          expect.objectContaining({
            slot: "material_profile_width",
            key: `MAT-PROFIL-LATERAL-LITERE-${depth}MM`,
            status: "present",
          }),
          expect.objectContaining({
            slot: "labor_machine_forming",
            key: "RETURN_PROFILE_MACHINE_FORMING",
            status: "present",
          }),
          expect.objectContaining({
            slot: "labor_face_bonding",
            key: "RETURN_PROFILE_FACE_BONDING",
            status: "present",
          }),
        ]),
      )
    }
  })

  it("requires Oracal code, marks reusable catalog boundary, and reports pricing alignment blocker", () => {
    const model = mapReturnCantTruthFieldCaptureReadonlyAdapter({
      letter_group_finishes: [
        {
          group_key: "pseudo:oracal",
          return_finish_type: "oracal_wrapped",
          return_depth_mm: 60,
          return_oracal_code: null,
          return_oracal_name: null,
        },
      ],
    })

    const entry = entryByKey(model, "pseudo:oracal")
    expect(entry.corrected_semantic_variant).toBe("oracal")
    expect(entry.catalog_source).toBe("reusable_oracal_catalog")
    expect(entry.catalog_boundary_status).toBe("reusable_finish_catalog_required")
    expect(entry.blockers).toEqual(
      expect.arrayContaining([
        "RETURN_CANT_ORACAL_CODE_MISSING",
        "ORACAL_651_CANT_PRICING_ALIGNMENT_REQUIRED",
      ]),
    )
    expect(entry.warnings).toContain("REUSABLE_ORACAL_CATALOG_BOUNDARY_REQUIRED")
    expect(entry.pricing_keys_status).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          slot: "finish_extra",
          key: "MAT-ORACAL-651",
          status: "alignment_required",
        }),
      ]),
    )
  })

  it("requires RAL code and paint_target, keeps quote geometry as context only, and stores no numeric pricing fields", () => {
    const model = mapReturnCantTruthFieldCaptureReadonlyAdapter({
      artwork_finishes: [
        {
          layer_key: "logo-ral",
          return_finish_type: "ral_paint",
          return_depth_mm: 80,
          return_oracal_code: "RAL 3020",
          return_oracal_name: "Traffic red",
        },
      ],
      quoteGeometry: {
        letter_perimeter_m: 18.5,
        geometry_source: "nest2_face_parts_outer",
        confirmed: true,
      },
    })

    const entry = entryByKey(model, "logo-ral")
    expect(entry.corrected_semantic_variant).toBe("ral_paint")
    expect(entry.ral_code).toBe("RAL 3020")
    expect(entry.blockers).toEqual(
      expect.arrayContaining([
        "RETURN_CANT_PAINT_TARGET_FIELD_MISSING",
        "RETURN_CANT_RAL_PAINT_PRICING_ALIGNMENT_REQUIRED",
        "RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED",
      ]),
    )
    expect(entry.warnings).toContain("REUSABLE_RAL_CATALOG_BOUNDARY_REQUIRED")
    expect(model.global_warnings).toContain("QUOTE_GEOMETRY_LETTER_PERIMETER_CONTEXT_ONLY")
    expect(model.overall_readiness).toBe("blocked")
    expect(entry.catalog_reference).toEqual(
      expect.objectContaining({
        stores_price: false,
        stores_cost: false,
      }),
    )
    expect(Object.keys(entry.catalog_reference ?? {})).not.toEqual(
      expect.arrayContaining(["price", "cost"]),
    )
    expect(model.formula).toMatchObject({
      pricing_values_source: "/inventory/pricing",
      component_stores_price: false,
      component_stores_cost: false,
      catalog_stores_price: false,
      catalog_stores_cost: false,
    })
  })
})
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
  it("maps Vector Litere Alb 60 mm to stock_color with the final stock label and no finish application pricing keys", () => {
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
    expect(entry.user_facing_finish_label).toBe("Culoare Stoc")
    expect(entry.stock_color_label).toBe("Alb")
    expect(entry.vinyl).toBeNull()
    expect(entry.paint).toBeNull()
    expect(entry.pricing_keys_required).toEqual(
      expect.arrayContaining([
        "MAT-PROFIL-LATERAL-LITERE-60MM",
        "RETURN_PROFILE_MACHINE_FORMING",
        "RETURN_PROFILE_FACE_BONDING",
      ]),
    )
    expect(entry.pricing_keys_required).not.toContain("MAT-ORACAL-651")
    expect(entry.pricing_keys_status).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          slot: "vinyl_material",
          key: null,
          status: "not_applicable",
        }),
        expect.objectContaining({
          slot: "vinyl_application_labor",
          key: null,
          status: "not_applicable",
        }),
        expect.objectContaining({
          slot: "ral_paint_material_by_width",
          key: null,
          status: "not_applicable",
        }),
        expect.objectContaining({
          slot: "ral_paint_labor",
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
    expect(entry.user_facing_finish_label).toBe("Culoare Stoc")
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

  it("maps Oracal 651 to vinyl_application and exposes reusable vinyl pricing references without numeric pricing", () => {
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
    expect(entry.corrected_semantic_variant).toBe("vinyl_application")
    expect(entry.user_facing_finish_label).toBe("Folie autocolanta")
    expect(entry.catalog_source).toBe("reusable_vinyl_catalog")
    expect(entry.catalog_boundary_status).toBe("reusable_finish_catalog_required")
    expect(entry.vinyl).toEqual(
      expect.objectContaining({
        material_family: "vinyl_color_catalog",
        series: "651",
        color_code: null,
      }),
    )
    expect(entry.blockers).toEqual(
      expect.arrayContaining([
        "RETURN_CANT_VINYL_COLOR_CODE_MISSING",
      ]),
    )
    expect(entry.warnings).toContain("REUSABLE_VINYL_CATALOG_BOUNDARY_REQUIRED")
    expect(entry.pricing_keys_status).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          slot: "vinyl_material",
          key: "MAT-ORACAL-651",
          status: "present",
        }),
        expect.objectContaining({
          slot: "vinyl_application_labor",
          key: "RETURN_CANT_VINYL_APPLICATION_LABOR",
          status: "present",
        }),
      ]),
    )
    expect(entry.target_paths).toEqual(
      expect.arrayContaining([
        "components.return_cant.instances.pseudo:oracal.finish_variant.vinyl.material_family",
        "components.return_cant.instances.pseudo:oracal.finish_variant.vinyl.series",
        "components.return_cant.instances.pseudo:oracal.finish_variant.vinyl.color_code",
        "components.return_cant.instances.pseudo:oracal.pricing_keys.vinyl_material",
        "components.return_cant.instances.pseudo:oracal.pricing_keys.vinyl_application_labor",
      ]),
    )
  })

  it("maps Vopsit RAL to paint_application, keeps quote geometry context-only, and stores no numeric pricing fields", () => {
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
    expect(entry.corrected_semantic_variant).toBe("paint_application")
    expect(entry.user_facing_finish_label).toBe("Vopsit RAL")
    expect(entry.paint).toEqual(
      expect.objectContaining({
        system: "RAL",
        ral_code: "RAL 3020",
      }),
    )
    expect(entry.blockers).toEqual(
      expect.arrayContaining([
        "RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED",
      ]),
    )
    expect(entry.warnings).toContain("REUSABLE_PAINT_CATALOG_BOUNDARY_REQUIRED")
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
    expect(entry.pricing_keys_status).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          slot: "ral_paint_material_by_width",
          key: "MAT-VOPSEA-RAL-CANT-80MM",
          status: "present",
        }),
        expect.objectContaining({
          slot: "ral_paint_labor",
          key: "RETURN_CANT_RAL_PAINT_LABOR",
          status: "present",
        }),
      ]),
    )
    expect(model.formula).toMatchObject({
      quantity_basis: "component_specific",
      vinyl_material_quantity_formula: "perimetru_ml x latime_cant_m",
      vinyl_labor_quantity_formula: "perimetru_ml",
      paint_material_quantity_formula: "pricing_target_by_width",
      paint_labor_quantity_formula: "perimetru_ml",
      pricing_values_source: "/inventory/pricing",
      component_stores_price: false,
      component_stores_cost: false,
      catalog_stores_price: false,
      catalog_stores_cost: false,
    })
  })

  it("keeps Oracal 641 as reusable contract support pending direct current runtime expression", () => {
    const model = mapReturnCantTruthFieldCaptureReadonlyAdapter({
      letter_group_finishes: [
        {
          group_key: "pseudo:runtime-651-only",
          return_finish_type: "oracal_wrapped",
          return_depth_mm: 30,
          return_oracal_code: "070",
          return_oracal_name: "Black",
        },
      ],
    })

    const entry = entryByKey(model, "pseudo:runtime-651-only")
    expect(entry.vinyl?.series).toBe("651")
    expect(entry.pricing_keys_required).not.toContain("MAT-ORACAL-641")
    expect(model.formula.vinyl_material_quantity_formula).toBe("perimetru_ml x latime_cant_m")
  })

  it("stays blocked for vinyl when required final pricing refs are missing from runtime evidence", () => {
    const model = mapReturnCantTruthFieldCaptureReadonlyAdapter({
      letter_group_finishes: [
        {
          group_key: "pseudo:vinyl-missing-pricing",
          return_finish_type: "oracal_wrapped",
          return_depth_mm: 60,
          return_oracal_code: "070",
          return_oracal_name: "Black",
        },
      ],
      pricingRegistryEvidence: {
        vinyl651LiveKeyPresent: false,
        vinylApplicationLaborKeyPresent: false,
      },
    })

    const entry = entryByKey(model, "pseudo:vinyl-missing-pricing")
    expect(entry.blockers).toEqual(
      expect.arrayContaining([
        "RETURN_CANT_VINYL_MATERIAL_PRICING_KEY_MISSING",
        "RETURN_CANT_VINYL_APPLICATION_LABOR_PRICING_KEY_MISSING",
      ]),
    )
    expect(entry.pricing_keys_status).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          slot: "vinyl_material",
          key: "MAT-ORACAL-651",
          status: "missing",
        }),
        expect.objectContaining({
          slot: "vinyl_application_labor",
          key: "RETURN_CANT_VINYL_APPLICATION_LABOR",
          status: "missing",
        }),
      ]),
    )
    expect(model.overall_readiness).toBe("blocked")
  })

  it("stays blocked for RAL when required final pricing refs are missing from runtime evidence", () => {
    const model = mapReturnCantTruthFieldCaptureReadonlyAdapter({
      artwork_finishes: [
        {
          layer_key: "logo-ral-missing-pricing",
          return_finish_type: "ral_paint",
          return_depth_mm: 80,
          return_oracal_code: "RAL 3020",
          return_oracal_name: "Traffic red",
        },
      ],
      pricingRegistryEvidence: {
        ralPaintMaterialByWidthPresent: { 80: false },
        ralPaintLaborKeyPresent: false,
      },
    })

    const entry = entryByKey(model, "logo-ral-missing-pricing")
    expect(entry.blockers).toEqual(
      expect.arrayContaining([
        "RETURN_CANT_RAL_PAINT_PRICING_KEY_MISSING",
        "RETURN_CANT_RAL_PAINT_LABOR_PRICING_KEY_MISSING",
      ]),
    )
    expect(entry.pricing_keys_status).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          slot: "ral_paint_material_by_width",
          key: "MAT-VOPSEA-RAL-CANT-80MM",
          status: "missing",
        }),
        expect.objectContaining({
          slot: "ral_paint_labor",
          key: "RETURN_CANT_RAL_PAINT_LABOR",
          status: "missing",
        }),
      ]),
    )
    expect(model.overall_readiness).toBe("blocked")
  })
})
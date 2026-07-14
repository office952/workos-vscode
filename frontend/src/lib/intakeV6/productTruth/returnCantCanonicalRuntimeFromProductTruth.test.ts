import { describe, expect, it } from "vitest"
import { buildReturnCantCanonicalRuntimeFromPayload } from "./returnCantCanonicalRuntimeFromProductTruth"
import { mapReturnCantTruthFieldsReadonly } from "./returnCantTruthFieldsReadonlyMapper"
import { buildProductTruthDraft } from "./productTruthDraftBuilder"
import { gradiCuratCompleteReviewLikeFixture } from "./productTruthFixtures"

describe("buildReturnCantCanonicalRuntimeFromProductTruth", () => {
  it("maps confirmed product_truth instances to canonical runtime fields", () => {
    const runtime = buildReturnCantCanonicalRuntimeFromPayload({
      product_truth: {
        components: {
          return_cant: {
            instances: {
              "letter_group:pseudo:maria": {
                confirmation_state: "confirmed",
                operator_blockers: [],
                layer_group_ids: ["pseudo:maria"],
                material_profile: { width_mm: 60 },
                finish_variant: { type: "stock_color", stock_color_label: "Alb" },
                pricing_keys: { material_profile_width: "MAT-PROFIL-LATERAL-LITERE-60MM" },
              },
            },
          },
        },
      },
    })

    expect(runtime?.return_cant?.depth_mm).toMatchObject({ value: 60, sourceState: "confirmed" })
    expect(runtime?.return_cant?.material_profile?.value).toBe("MAT-PROFIL-LATERAL-LITERE-60MM")
    expect(runtime?.return_cant?.layer_group_ids?.value).toEqual(["pseudo:maria"])
    expect(runtime?.return_cant?.finish_type?.value).toBe("white_aluminum")
  })
})

describe("return cant readonly mapper with product_truth runtime", () => {
  it("clears operator blockers for stock-color cant when canonical runtime is wired", () => {
    const draft = buildProductTruthDraft(gradiCuratCompleteReviewLikeFixture)
    const model = mapReturnCantTruthFieldsReadonly({
      productTruthDraft: draft,
      canonicalRuntime: buildReturnCantCanonicalRuntimeFromPayload({
        product_truth: {
          components: {
            return_cant: {
              instances: {
                "letter_group:pseudo:maria": {
                  confirmation_state: "confirmed",
                  operator_blockers: [],
                  layer_group_ids: ["pseudo:maria"],
                  material_profile: { width_mm: 60 },
                  finish_variant: { type: "stock_color", stock_color_label: "Alb" },
                  pricing_keys: { material_profile_width: "MAT-PROFIL-LATERAL-LITERE-60MM" },
                },
              },
            },
          },
        },
      }),
    })

    expect(model.operator_readiness).toBe("ready")
    expect(model.operator_blockers).not.toContain("RETURN_CANT_MATERIAL_MISSING")
    expect(model.operator_blockers).not.toContain("RETURN_CANT_LAYER_GROUP_SOURCE_MISSING")
  })
})

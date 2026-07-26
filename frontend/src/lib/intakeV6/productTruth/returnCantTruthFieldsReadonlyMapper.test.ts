import { describe, expect, it } from "vitest"
import { buildProductTruthDraft } from "./productTruthDraftBuilder"
import {
  gradiCuratCompleteReviewLikeFixture,
  gradiCuratUnconfirmedFixture,
} from "./productTruthFixtures"
import { mapReturnCantTruthFieldsReadonly } from "./returnCantTruthFieldsReadonlyMapper"

function fieldByKey(model: ReturnType<typeof mapReturnCantTruthFieldsReadonly>, key: string) {
  const field = model.fields.find((entry) => entry.field_key === key)
  if (!field) throw new Error(`Missing field ${key}`)
  return field
}

function dependencyByKey(model: ReturnType<typeof mapReturnCantTruthFieldsReadonly>, key: string) {
  const dependency = model.dependencies.find((entry) => entry.dependency_key === key)
  if (!dependency) throw new Error(`Missing dependency ${key}`)
  return dependency
}

describe("mapReturnCantTruthFieldsReadonly", () => {
  it("reports missing canonical fields as blockers", () => {
    const draft = buildProductTruthDraft(gradiCuratCompleteReviewLikeFixture)
    const model = mapReturnCantTruthFieldsReadonly({
      productTruthDraft: draft,
      quoteGeometry: {
        letter_perimeter_m: 21.1675,
        geometry_source: "nest2_face_parts_outer",
        confirmed: true,
      },
    })

    expect(model.operator_readiness).toBe("blocked")
    expect(model.operator_blockers).toEqual(
      expect.arrayContaining([
        "RETURN_CANT_MATERIAL_MISSING",
        "RETURN_CANT_LAYER_GROUP_SOURCE_MISSING",
      ]),
    )
    expect(model.technical_blockers.length).toBeGreaterThan(0)
  })

  it("treats quote_geometry.letter_perimeter_m as context_only, not confirmed dependency", () => {
    const draft = buildProductTruthDraft(gradiCuratCompleteReviewLikeFixture)
    const model = mapReturnCantTruthFieldsReadonly({
      productTruthDraft: draft,
      quoteGeometry: {
        letter_perimeter_m: 18.5,
        geometry_source: "nest2_face_parts_outer",
        confirmed: true,
      },
    })

    expect(fieldByKey(model, "return_cant.perimeter_source")).toMatchObject({
      current_runtime_path: "quote_geometry.letter_perimeter_m",
      classification: "context_only",
      readiness: "blocked",
    })
    expect(dependencyByKey(model, "face_confirmed_perimeter")).toMatchObject({
      current_runtime_path: "quote_geometry.letter_perimeter_m",
      classification: "context_only",
      readiness: "blocked",
      blocker_if_missing: "RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED",
    })
  })

  it("keeps return depth as hydrated_only when it comes from a noncanonical runtime path", () => {
    const draft = buildProductTruthDraft({
      ...gradiCuratCompleteReviewLikeFixture,
      finishSetup: {
        ...gradiCuratCompleteReviewLikeFixture.finishSetup,
        confirmed: false,
      },
    })
    const model = mapReturnCantTruthFieldsReadonly({
      productTruthDraft: draft,
    })

    expect(fieldByKey(model, "return_cant.depth_mm")).toMatchObject({
      current_runtime_path: "components.returnCant.depthMm",
      classification: "hydrated_only",
      readiness: "ready",
      blocker_if_missing: "RETURN_CANT_HEIGHT_CONFIRMATION_REQUIRED",
    })
    expect(model.operator_readiness).toBe("blocked")
  })

  it("produces the face perimeter blocker when canonical dependency is missing", () => {
    const draft = buildProductTruthDraft(gradiCuratUnconfirmedFixture)
    const model = mapReturnCantTruthFieldsReadonly({
      productTruthDraft: draft,
    })

    expect(dependencyByKey(model, "face_confirmed_perimeter")).toMatchObject({
      classification: "dependency_missing",
      readiness: "blocked",
      blocker_if_missing: "RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED",
    })
    expect(model.blockers).toContain("RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED")
  })

  it("blocks when confirmation_state is not confirmed even if the other canonical fields are supplied", () => {
    const draft = buildProductTruthDraft(gradiCuratCompleteReviewLikeFixture)
    const model = mapReturnCantTruthFieldsReadonly({
      productTruthDraft: draft,
      quoteGeometry: {
        letter_perimeter_m: 18.5,
        geometry_source: "nest2_face_parts_outer",
        confirmed: true,
      },
      selectedLayerRefs: ["pseudo:maria", "pseudo:ana"],
      canonicalRuntime: {
        return_cant: {
          depth_mm: { currentRuntimePath: "components.return_cant.depth_mm", value: 60, sourceState: "confirmed" },
          material_profile: { currentRuntimePath: "components.return_cant.material_profile", value: "aluminum_profile_60", sourceState: "confirmed" },
          finish_type: { currentRuntimePath: "components.return_cant.finish_type", value: "white_aluminum", sourceState: "confirmed" },
          layer_group_ids: { currentRuntimePath: "components.return_cant.layer_group_ids", value: ["pseudo:maria", "pseudo:ana"], sourceState: "confirmed" },
          confirmation_state: { currentRuntimePath: "components.return_cant.confirmation_state", value: "pending", sourceState: "hydrated" },
          perimeter_source: { currentRuntimePath: "components.return_cant.perimeter_source", value: "components.face.confirmed_perimeter", sourceState: "confirmed" },
        },
        face: {
          confirmed_perimeter: {
            currentRuntimePath: "components.face.confirmed_perimeter.value",
            sourcePath: "components.face.confirmed_perimeter",
            value: 18.5,
            unit: "m",
            sourceState: "confirmed",
            layerGroupIds: ["pseudo:maria", "pseudo:ana"],
            confirmationState: "confirmed",
          },
        },
      },
    })

    expect(fieldByKey(model, "return_cant.confirmation_state")).toMatchObject({
      classification: "hydrated_only",
      readiness: "blocked",
    })
    expect(model.operator_readiness).toBe("ready")
    expect(model.technical_blockers).toContain("RETURN_CANT_SOURCE_STATE_NOT_CONFIRMED")
  })

  it("does not report ready when canonical requirements are missing", () => {
    const draft = buildProductTruthDraft(gradiCuratCompleteReviewLikeFixture)
    const model = mapReturnCantTruthFieldsReadonly({ productTruthDraft: draft })

    expect(model.overall_readiness).toBe("blocked")
    expect(model.fields.some((field) => field.readiness === "ready")).toBe(true)
    expect(model.fields.every((field) => field.canonical_product_truth_path.length > 0)).toBe(true)
  })
})
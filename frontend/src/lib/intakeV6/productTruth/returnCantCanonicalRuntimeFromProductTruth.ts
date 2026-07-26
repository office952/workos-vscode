import type { ReturnCantTruthFieldsReadonlyMapperInput } from "./returnCantTruthFieldsReadonlyMapper"

type ProductTruthPayload = {
  components?: {
    return_cant?: {
      instances?: Record<string, ReturnCantInstancePayload>
    }
  }
}

type ReturnCantInstancePayload = {
  confirmation_state?: string | null
  operator_blockers?: string[] | null
  technical_blockers?: string[] | null
  layer_group_ids?: string[] | null
  material_profile?: { width_mm?: number | null } | null
  finish_variant?: {
    type?: string | null
    stock_color_label?: string | null
    vinyl?: { color_code?: string | null } | null
    paint?: { ral_code?: string | null } | null
  } | null
  pricing_keys?: { material_profile_width?: string | null } | null
}

const DEPTH_TO_PROFILE_KEY: Record<number, string> = {
  30: "MAT-PROFIL-LATERAL-LITERE-30MM",
  60: "MAT-PROFIL-LATERAL-LITERE-60MM",
  80: "MAT-PROFIL-LATERAL-LITERE-80MM",
  100: "MAT-PROFIL-LATERAL-LITERE-100MM",
}

function runtimeField<T>(path: string, value: T | null | undefined, sourceState: string) {
  return {
    currentRuntimePath: path,
    value: value ?? null,
    sourceState,
  }
}

function finishTypeFromVariant(instance: ReturnCantInstancePayload): string | null {
  const variant = instance.finish_variant
  if (!variant?.type) return null
  if (variant.type === "stock_color") {
    const label = variant.stock_color_label?.trim().toLowerCase()
    if (label === "alb") return "white_aluminum"
    if (label === "negru") return "black_aluminum"
    if (label === "auriu") return "gold_aluminum"
    if (label === "argintiu") return "mirror_silver"
    return "white_aluminum"
  }
  if (variant.type === "vinyl_application") return "oracal_wrapped"
  if (variant.type === "paint_application") return "ral_paint"
  return null
}

export function buildReturnCantCanonicalRuntimeFromPayload(
  payload: Record<string, unknown> | null | undefined,
): ReturnCantTruthFieldsReadonlyMapperInput["canonicalRuntime"] | undefined {
  const productTruth = payload?.product_truth as ProductTruthPayload | undefined
  const instances = productTruth?.components?.return_cant?.instances
  if (!instances || Object.keys(instances).length === 0) return undefined

  const rows = Object.values(instances).filter((row): row is ReturnCantInstancePayload => !!row)
  if (rows.length === 0) return undefined

  const layerGroupIds = [
    ...new Set(
      rows.flatMap((row) => (Array.isArray(row.layer_group_ids) ? row.layer_group_ids.filter(Boolean) : [])),
    ),
  ]
  const depths = rows
    .map((row) => row.material_profile?.width_mm)
    .filter((depth): depth is number => typeof depth === "number" && Number.isFinite(depth))
  const depthMm = depths.length > 0 ? Math.max(...depths) : null
  const materialProfile =
    rows.map((row) => row.pricing_keys?.material_profile_width).find(Boolean) ??
    (depthMm != null ? DEPTH_TO_PROFILE_KEY[depthMm] ?? null : null)
  const finishType = rows.map(finishTypeFromVariant).find(Boolean) ?? null

  const allConfirmed = rows.every((row) => row.confirmation_state === "confirmed")
  const anyOperatorBlocker = rows.some((row) => (row.operator_blockers?.length ?? 0) > 0)
  const sourceState = allConfirmed && !anyOperatorBlocker ? "confirmed" : "blocked"

  const oracalCode = rows
    .map((row) => row.finish_variant?.vinyl?.color_code ?? null)
    .find((code) => typeof code === "string" && code.trim().length > 0)
  const ralCode = rows
    .map((row) => row.finish_variant?.paint?.ral_code ?? null)
    .find((code) => typeof code === "string" && code.trim().length > 0)

  return {
    return_cant: {
      depth_mm: runtimeField("components.return_cant.depth_mm", depthMm, sourceState),
      material_profile: runtimeField("components.return_cant.material_profile", materialProfile, sourceState),
      finish_type: runtimeField("components.return_cant.finish_type", finishType, sourceState),
      layer_group_ids: runtimeField("components.return_cant.layer_group_ids", layerGroupIds, sourceState),
      confirmation_state: runtimeField(
        "components.return_cant.confirmation_state",
        allConfirmed ? "confirmed" : "blocked",
        sourceState,
      ),
      color_target: {
        oracal_code: runtimeField(
          "components.return_cant.color_target.oracal_code",
          oracalCode ?? null,
          oracalCode ? sourceState : "not_applicable",
        ),
        ral_code: runtimeField(
          "components.return_cant.color_target.ral_code",
          ralCode ?? null,
          ralCode ? sourceState : "not_applicable",
        ),
        paint_target: runtimeField(
          "components.return_cant.color_target.paint_target",
          ralCode ?? null,
          ralCode ? sourceState : "not_applicable",
        ),
      },
      perimeter_source: runtimeField("components.return_cant.perimeter_source", null, "blocked"),
    },
  }
}

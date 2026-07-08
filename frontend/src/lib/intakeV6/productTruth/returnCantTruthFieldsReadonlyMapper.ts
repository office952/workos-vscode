import type { IntakeV4QuoteGeometry } from "../intakeV4QuoteGeometry"
import type { ProductTruthDraft, ProductTruthField, ProductTruthState } from "./productTruthTypes"

const ROOT_TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"
const ROOT_TYPE = "product_template"
const QUOTE_MODE = "product_total"
const COMPONENT_SCOPE = "return_cant"

export type ReturnCantReadonlyClassification =
  | "component_truth_confirmed"
  | "component_truth_missing"
  | "fallback_only"
  | "hydrated_only"
  | "context_only"
  | "dependency_missing"
  | "dependency_unconfirmed"
  | "product_definition_derived_only"
  | "svg_suggestion_only"

export type ReturnCantReadonlyReadiness = "ready" | "blocked"

export interface ReturnCantReadonlyRuntimeField<T> {
  currentRuntimePath?: string | null
  value?: T | null
  sourceState?: string | null
}

export interface ReturnCantReadonlyFacePerimeterRuntime {
  currentRuntimePath?: string | null
  value?: number | null
  unit?: string | null
  sourceState?: string | null
  sourcePath?: string | null
  layerGroupIds?: string[] | null
  confirmationState?: string | null
  confirmedAt?: string | null
  confirmedBy?: string | null
}

export interface ReturnCantTruthFieldsReadonlyMapperInput {
  templateCode?: string | null
  rootType?: string | null
  quoteMode?: string | null
  productTruthDraft?: ProductTruthDraft | null
  quoteGeometry?: Pick<IntakeV4QuoteGeometry, "letter_perimeter_m" | "geometry_source" | "confirmed"> | null
  selectedLayerRefs?: string[] | null
  canonicalRuntime?: {
    return_cant?: {
      depth_mm?: ReturnCantReadonlyRuntimeField<number>
      material_profile?: ReturnCantReadonlyRuntimeField<string>
      finish_type?: ReturnCantReadonlyRuntimeField<string>
      color_target?: {
        oracal_code?: ReturnCantReadonlyRuntimeField<string>
        ral_code?: ReturnCantReadonlyRuntimeField<string>
        paint_target?: ReturnCantReadonlyRuntimeField<string>
      } | null
      layer_group_ids?: ReturnCantReadonlyRuntimeField<string[]>
      confirmation_state?: ReturnCantReadonlyRuntimeField<string>
      perimeter_source?: ReturnCantReadonlyRuntimeField<string>
    } | null
    face?: {
      confirmed_perimeter?: ReturnCantReadonlyFacePerimeterRuntime | null
    } | null
  } | null
}

export interface ReturnCantTruthFieldReadonlyRow {
  field_key: string
  canonical_product_truth_path: string
  current_runtime_path: string | null
  current_value: unknown
  source_state: string
  classification: ReturnCantReadonlyClassification
  owner: string
  required_for_mapper: boolean
  required_for_preview_later: boolean
  blocker_if_missing: string
  readiness: ReturnCantReadonlyReadiness
}

export interface ReturnCantTruthDependencyReadonlyRow {
  dependency_key: string
  canonical_dependency_path: string
  current_runtime_path: string | null
  current_value: unknown
  source_state: string
  classification: ReturnCantReadonlyClassification
  readiness: ReturnCantReadonlyReadiness
  blocker_if_missing: string
}

export interface ReturnCantTruthFieldsReadonlyModel {
  component_scope: "return_cant"
  root_template: string
  root_type: string
  quote_mode: string
  fields: ReturnCantTruthFieldReadonlyRow[]
  dependencies: ReturnCantTruthDependencyReadonlyRow[]
  blockers: string[]
  warnings: string[]
  overall_readiness: ReturnCantReadonlyReadiness
}

function lower(value: unknown): string {
  return String(value ?? "").trim().toLowerCase()
}

function nonEmptyString(value: unknown): string | null {
  if (typeof value !== "string") return null
  const trimmed = value.trim()
  return trimmed.length > 0 ? trimmed : null
}

function uniquePush(target: string[], value: string | null | undefined) {
  if (!value) return
  if (!target.includes(value)) target.push(value)
}

function legacyClassification(state: ProductTruthState | null | undefined): ReturnCantReadonlyClassification {
  if (state === "fallback") return "fallback_only"
  if (state === "hydrated" || state === "manual" || state === "confirmed") return "hydrated_only"
  if (state === "suggested") return "svg_suggestion_only"
  if (state === "warning") return "context_only"
  return "component_truth_missing"
}

function canonicalClassification(sourceState: string | null | undefined): ReturnCantReadonlyClassification {
  const normalized = lower(sourceState)
  if (normalized === "confirmed") return "component_truth_confirmed"
  if (normalized === "fallback") return "fallback_only"
  if (normalized === "hydrated" || normalized === "manual") return "hydrated_only"
  if (normalized === "suggested") return "svg_suggestion_only"
  if (normalized === "warning") return "context_only"
  if (normalized === "product_definition_derived") return "product_definition_derived_only"
  return "component_truth_missing"
}

function isConfirmedState(sourceState: string | null | undefined): boolean {
  return lower(sourceState) === "confirmed"
}

function finishRequiresOracal(finishType: string | null): boolean {
  return lower(finishType).includes("oracal")
}

function finishRequiresRal(finishType: string | null): boolean {
  return lower(finishType).includes("ral")
}

function finishRequiresPaint(finishType: string | null): boolean {
  const token = lower(finishType)
  return token.includes("paint") || token.includes("vop")
}

function readyFromClassification(classification: ReturnCantReadonlyClassification, sourceState: string): ReturnCantReadonlyReadiness {
  return classification === "component_truth_confirmed" && isConfirmedState(sourceState) ? "ready" : "blocked"
}

function fieldFromDraft<T>(field: ProductTruthField<T> | undefined, path: string): ReturnCantReadonlyRuntimeField<T> | null {
  if (!field) return null
  return {
    currentRuntimePath: path,
    value: field.value,
    sourceState: field.state,
  }
}

function buildCanonicalFieldRow(args: {
  fieldKey: string
  canonicalPath: string
  owner: string
  blocker: string
  requiredForPreviewLater?: boolean
  canonicalField?: ReturnCantReadonlyRuntimeField<unknown> | null
  legacyField?: ReturnCantReadonlyRuntimeField<unknown> | null
  allowMissingAsReady?: boolean
  missingClassification?: ReturnCantReadonlyClassification
}): ReturnCantTruthFieldReadonlyRow {
  const requiredForPreviewLater = args.requiredForPreviewLater ?? true
  if (args.canonicalField) {
    const sourceState = nonEmptyString(args.canonicalField.sourceState) ?? "missing"
    const classification = canonicalClassification(sourceState)
    return {
      field_key: args.fieldKey,
      canonical_product_truth_path: args.canonicalPath,
      current_runtime_path: args.canonicalField.currentRuntimePath ?? args.canonicalPath,
      current_value: args.canonicalField.value ?? null,
      source_state: sourceState,
      classification,
      owner: args.owner,
      required_for_mapper: true,
      required_for_preview_later: requiredForPreviewLater,
      blocker_if_missing: args.blocker,
      readiness: readyFromClassification(classification, sourceState),
    }
  }
  if (args.legacyField) {
    const sourceState = nonEmptyString(args.legacyField.sourceState) ?? "missing"
    const classification = legacyClassification(args.legacyField.sourceState as ProductTruthState | null | undefined)
    return {
      field_key: args.fieldKey,
      canonical_product_truth_path: args.canonicalPath,
      current_runtime_path: args.legacyField.currentRuntimePath ?? null,
      current_value: args.legacyField.value ?? null,
      source_state: sourceState,
      classification,
      owner: args.owner,
      required_for_mapper: true,
      required_for_preview_later: requiredForPreviewLater,
      blocker_if_missing: args.blocker,
      readiness: "blocked",
    }
  }
  return {
    field_key: args.fieldKey,
    canonical_product_truth_path: args.canonicalPath,
    current_runtime_path: null,
    current_value: null,
    source_state: "missing",
    classification: args.missingClassification ?? "component_truth_missing",
    owner: args.owner,
    required_for_mapper: true,
    required_for_preview_later: requiredForPreviewLater,
    blocker_if_missing: args.blocker,
    readiness: args.allowMissingAsReady ? "ready" : "blocked",
  }
}

function buildDependencyRow(
  input: ReturnCantTruthFieldsReadonlyMapperInput,
  warnings: string[],
): ReturnCantTruthDependencyReadonlyRow {
  const facePerimeter = input.canonicalRuntime?.face?.confirmed_perimeter
  if (facePerimeter) {
    const sourceState = nonEmptyString(facePerimeter.sourceState) ?? "missing"
    const confirmed =
      facePerimeter.value != null &&
      isConfirmedState(sourceState) &&
      lower(facePerimeter.confirmationState) === "confirmed"
    return {
      dependency_key: "face_confirmed_perimeter",
      canonical_dependency_path: "components.face.confirmed_perimeter",
      current_runtime_path:
        facePerimeter.currentRuntimePath ?? facePerimeter.sourcePath ?? "components.face.confirmed_perimeter",
      current_value: facePerimeter.value ?? null,
      source_state: sourceState,
      classification: confirmed ? "component_truth_confirmed" : "dependency_unconfirmed",
      readiness: confirmed ? "ready" : "blocked",
      blocker_if_missing: "RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED",
    }
  }

  if (input.quoteGeometry?.letter_perimeter_m != null) {
    uniquePush(warnings, "ROOT_GEOMETRY_CONTEXT_ONLY")
    return {
      dependency_key: "face_confirmed_perimeter",
      canonical_dependency_path: "components.face.confirmed_perimeter",
      current_runtime_path: "quote_geometry.letter_perimeter_m",
      current_value: input.quoteGeometry.letter_perimeter_m,
      source_state: input.quoteGeometry.confirmed ? "confirmed" : "hydrated",
      classification: "context_only",
      readiness: "blocked",
      blocker_if_missing: "RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED",
    }
  }

  return {
    dependency_key: "face_confirmed_perimeter",
    canonical_dependency_path: "components.face.confirmed_perimeter",
    current_runtime_path: null,
    current_value: null,
    source_state: "missing_explicit_dependency",
    classification: "dependency_missing",
    readiness: "blocked",
    blocker_if_missing: "RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED",
  }
}

function buildLayerGroupField(
  input: ReturnCantTruthFieldsReadonlyMapperInput,
  warnings: string[],
): ReturnCantTruthFieldReadonlyRow {
  const canonicalField = input.canonicalRuntime?.return_cant?.layer_group_ids
  if (canonicalField) {
    return buildCanonicalFieldRow({
      fieldKey: "return_cant.layer_group_ids",
      canonicalPath: "components.return_cant.layer_group_ids",
      owner: "return_cant",
      blocker: "RETURN_CANT_LAYER_GROUP_SOURCE_MISSING",
      canonicalField,
    })
  }

  if (input.selectedLayerRefs && input.selectedLayerRefs.length > 0) {
    uniquePush(warnings, "SELECTED_LAYER_REFS_NOT_MAPPED_TO_RETURN_CANT")
    return {
      field_key: "return_cant.layer_group_ids",
      canonical_product_truth_path: "components.return_cant.layer_group_ids",
      current_runtime_path: "svg.selected_layer_refs[]",
      current_value: input.selectedLayerRefs,
      source_state: "confirmed",
      classification: "context_only",
      owner: "return_cant",
      required_for_mapper: true,
      required_for_preview_later: true,
      blocker_if_missing: "RETURN_CANT_LAYER_GROUP_SOURCE_MISSING",
      readiness: "blocked",
    }
  }

  const draft = input.productTruthDraft
  const confirmedLayerKeys =
    draft?.layers
      .filter((layer) => layer.confirmedRole.state === "confirmed" && layer.confirmationState.value === "confirmed")
      .map((layer) => layer.layerKey) ?? []
  if (confirmedLayerKeys.length > 0) {
    uniquePush(warnings, "LAYER_CONFIRMATION_EXISTS_BUT_COMPONENT_MAPPING_MISSING")
    return {
      field_key: "return_cant.layer_group_ids",
      canonical_product_truth_path: "components.return_cant.layer_group_ids",
      current_runtime_path: "layer_role_setup.layers[].confirmed_role",
      current_value: confirmedLayerKeys,
      source_state: "confirmed",
      classification: "context_only",
      owner: "return_cant",
      required_for_mapper: true,
      required_for_preview_later: true,
      blocker_if_missing: "RETURN_CANT_LAYER_GROUP_SOURCE_MISSING",
      readiness: "blocked",
    }
  }

  return buildCanonicalFieldRow({
    fieldKey: "return_cant.layer_group_ids",
    canonicalPath: "components.return_cant.layer_group_ids",
    owner: "return_cant",
    blocker: "RETURN_CANT_LAYER_GROUP_SOURCE_MISSING",
  })
}

function buildConfirmationStateField(input: ReturnCantTruthFieldsReadonlyMapperInput, warnings: string[]): ReturnCantTruthFieldReadonlyRow {
  const canonicalField = input.canonicalRuntime?.return_cant?.confirmation_state
  if (canonicalField) {
    return buildCanonicalFieldRow({
      fieldKey: "return_cant.confirmation_state",
      canonicalPath: "components.return_cant.confirmation_state",
      owner: "return_cant",
      blocker: "RETURN_CANT_SOURCE_STATE_NOT_CONFIRMED",
      canonicalField,
    })
  }

  uniquePush(warnings, "GLOBAL_FINISH_CONFIRMATION_NOT_COMPONENT_TRUTH")
  return {
    field_key: "return_cant.confirmation_state",
    canonical_product_truth_path: "components.return_cant.confirmation_state",
    current_runtime_path: null,
    current_value: null,
    source_state: "missing_component_field",
    classification: "component_truth_missing",
    owner: "return_cant",
    required_for_mapper: true,
    required_for_preview_later: true,
    blocker_if_missing: "RETURN_CANT_SOURCE_STATE_NOT_CONFIRMED",
    readiness: "blocked",
  }
}

function buildPerimeterSourceField(input: ReturnCantTruthFieldsReadonlyMapperInput, warnings: string[]): ReturnCantTruthFieldReadonlyRow {
  const canonicalField = input.canonicalRuntime?.return_cant?.perimeter_source
  if (canonicalField) {
    return buildCanonicalFieldRow({
      fieldKey: "return_cant.perimeter_source",
      canonicalPath: "components.return_cant.perimeter_source",
      owner: "return_cant",
      blocker: "RETURN_CANT_PERIMETER_MISSING",
      canonicalField,
    })
  }

  if (input.quoteGeometry?.letter_perimeter_m != null) {
    uniquePush(warnings, "ROOT_GEOMETRY_CONTEXT_ONLY")
    return {
      field_key: "return_cant.perimeter_source",
      canonical_product_truth_path: "components.return_cant.perimeter_source",
      current_runtime_path: "quote_geometry.letter_perimeter_m",
      current_value: input.quoteGeometry.letter_perimeter_m,
      source_state: input.quoteGeometry.confirmed ? "confirmed" : "hydrated",
      classification: "context_only",
      owner: "return_cant",
      required_for_mapper: true,
      required_for_preview_later: true,
      blocker_if_missing: "RETURN_CANT_PERIMETER_MISSING",
      readiness: "blocked",
    }
  }

  return buildCanonicalFieldRow({
    fieldKey: "return_cant.perimeter_source",
    canonicalPath: "components.return_cant.perimeter_source",
    owner: "return_cant",
    blocker: "RETURN_CANT_PERIMETER_MISSING",
  })
}

function buildColorField(args: {
  fieldKey: string
  canonicalPath: string
  blocker: string
  canonicalField?: ReturnCantReadonlyRuntimeField<string> | null
  legacyField?: ReturnCantReadonlyRuntimeField<string> | null
  required: boolean
}): ReturnCantTruthFieldReadonlyRow {
  return buildCanonicalFieldRow({
    fieldKey: args.fieldKey,
    canonicalPath: args.canonicalPath,
    owner: "return_cant",
    blocker: args.blocker,
    canonicalField: args.canonicalField,
    legacyField: args.legacyField,
    allowMissingAsReady: !args.required,
  })
}

function rowByKey(rows: ReturnCantTruthFieldReadonlyRow[], key: string): ReturnCantTruthFieldReadonlyRow {
  const row = rows.find((entry) => entry.field_key === key)
  if (!row) {
    throw new Error(`Missing readonly mapper field row: ${key}`)
  }
  return row
}

export function mapReturnCantTruthFieldsReadonly(
  input: ReturnCantTruthFieldsReadonlyMapperInput,
): ReturnCantTruthFieldsReadonlyModel {
  const warnings: string[] = []
  const draft = input.productTruthDraft

  const depthLegacy = fieldFromDraft(draft?.components.returnCant.depthMm, "components.returnCant.depthMm")
  const finishLegacy = fieldFromDraft(draft?.components.returnCant.finishType, "components.returnCant.finishType")
  const colorLegacy = fieldFromDraft(draft?.components.returnCant.colorCode, "components.returnCant.colorCode")

  const fields: ReturnCantTruthFieldReadonlyRow[] = []
  fields.push(
    buildCanonicalFieldRow({
      fieldKey: "return_cant.depth_mm",
      canonicalPath: "components.return_cant.depth_mm",
      owner: "return_cant",
      blocker: depthLegacy?.currentRuntimePath ? "RETURN_CANT_HEIGHT_CONFIRMATION_REQUIRED" : "RETURN_CANT_DEPTH_MISSING",
      canonicalField: input.canonicalRuntime?.return_cant?.depth_mm,
      legacyField: depthLegacy,
    }),
  )
  fields.push(
    buildCanonicalFieldRow({
      fieldKey: "return_cant.material_profile",
      canonicalPath: "components.return_cant.material_profile",
      owner: "return_cant",
      blocker: "RETURN_CANT_MATERIAL_MISSING",
      canonicalField: input.canonicalRuntime?.return_cant?.material_profile,
    }),
  )
  fields.push(
    buildCanonicalFieldRow({
      fieldKey: "return_cant.finish_type",
      canonicalPath: "components.return_cant.finish_type",
      owner: "return_cant",
      blocker: "RETURN_CANT_FINISH_MISSING",
      canonicalField: input.canonicalRuntime?.return_cant?.finish_type,
      legacyField: finishLegacy,
    }),
  )

  const finishTypeForColor = nonEmptyString(input.canonicalRuntime?.return_cant?.finish_type?.value) ?? nonEmptyString(finishLegacy?.value)
  fields.push(
    buildColorField({
      fieldKey: "return_cant.color_target.oracal_code",
      canonicalPath: "components.return_cant.color_target.oracal_code",
      blocker: "RETURN_CANT_COLOR_TARGET_MISSING",
      canonicalField: input.canonicalRuntime?.return_cant?.color_target?.oracal_code,
      legacyField: colorLegacy,
      required: finishRequiresOracal(finishTypeForColor),
    }),
  )
  fields.push(
    buildColorField({
      fieldKey: "return_cant.color_target.ral_code",
      canonicalPath: "components.return_cant.color_target.ral_code",
      blocker: "RETURN_CANT_COLOR_TARGET_MISSING",
      canonicalField: input.canonicalRuntime?.return_cant?.color_target?.ral_code,
      required: finishRequiresRal(finishTypeForColor),
    }),
  )
  fields.push(
    buildColorField({
      fieldKey: "return_cant.color_target.paint_target",
      canonicalPath: "components.return_cant.color_target.paint_target",
      blocker: "RETURN_CANT_COLOR_TARGET_MISSING",
      canonicalField: input.canonicalRuntime?.return_cant?.color_target?.paint_target,
      required: finishRequiresPaint(finishTypeForColor),
    }),
  )

  fields.push(buildLayerGroupField(input, warnings))
  fields.push(buildConfirmationStateField(input, warnings))
  fields.push(buildPerimeterSourceField(input, warnings))

  const dependencies = [buildDependencyRow(input, warnings)]

  const blockers: string[] = []
  const requiredFieldKeys = new Set([
    "return_cant.depth_mm",
    "return_cant.material_profile",
    "return_cant.finish_type",
    "return_cant.layer_group_ids",
    "return_cant.confirmation_state",
    "return_cant.perimeter_source",
  ])

  for (const field of fields) {
    const isRequired = requiredFieldKeys.has(field.field_key)
    const needsOracal = field.field_key === "return_cant.color_target.oracal_code" && finishRequiresOracal(finishTypeForColor)
    const needsRal = field.field_key === "return_cant.color_target.ral_code" && finishRequiresRal(finishTypeForColor)
    const needsPaint = field.field_key === "return_cant.color_target.paint_target" && finishRequiresPaint(finishTypeForColor)
    if ((isRequired || needsOracal || needsRal || needsPaint) && field.readiness !== "ready") {
      uniquePush(blockers, field.blocker_if_missing)
    }
  }

  for (const dependency of dependencies) {
    if (dependency.readiness !== "ready") {
      uniquePush(blockers, dependency.blocker_if_missing)
    }
  }

  const depthField = rowByKey(fields, "return_cant.depth_mm")
  if (depthField.classification === "fallback_only") {
    uniquePush(warnings, "RETURN_DEPTH_FALLBACK_DOES_NOT_UNLOCK_READINESS")
  }
  if (depthField.classification === "hydrated_only") {
    uniquePush(warnings, "RETURN_DEPTH_HYDRATED_DOES_NOT_UNLOCK_READINESS")
  }

  return {
    component_scope: COMPONENT_SCOPE,
    root_template: nonEmptyString(input.templateCode) ?? nonEmptyString(draft?.metadata.templateCode.value) ?? ROOT_TEMPLATE,
    root_type: nonEmptyString(input.rootType) ?? ROOT_TYPE,
    quote_mode: nonEmptyString(input.quoteMode) ?? QUOTE_MODE,
    fields,
    dependencies,
    blockers,
    warnings,
    overall_readiness: blockers.length === 0 ? "ready" : "blocked",
  }
}
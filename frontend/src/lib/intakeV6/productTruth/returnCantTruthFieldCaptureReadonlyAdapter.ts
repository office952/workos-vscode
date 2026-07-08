import type {
  IntakeV4ArtworkFinish,
  IntakeV4LetterGroupFinish,
} from "../intakeV4Api"
import type { IntakeV4QuoteGeometry } from "../intakeV4QuoteGeometry"
import {
  artworkToReturnCant,
  letterGroupToReturnCant,
} from "../intakeV6ReturnCantBridge"

const ROOT_TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"
const ROOT_TYPE = "product_template"
const QUOTE_MODE = "product_total"
const COMPONENT_SCOPE = "return_cant"

const DEPTH_TO_PROFILE_KEY: Record<number, string> = {
  30: "MAT-PROFIL-LATERAL-LITERE-30MM",
  60: "MAT-PROFIL-LATERAL-LITERE-60MM",
  80: "MAT-PROFIL-LATERAL-LITERE-80MM",
  100: "MAT-PROFIL-LATERAL-LITERE-100MM",
}

const GENERIC_LABOR_KEYS = [
  "RETURN_PROFILE_MACHINE_FORMING",
  "RETURN_PROFILE_FACE_BONDING",
] as const

export type ReturnCantSemanticVariant = "stock_color" | "oracal" | "ral_paint"

export interface ReturnCantReadonlyCatalogReference {
  family: "stock_color" | "oracal" | "ral_paint"
  reference: string | null
  display_label: string | null
  stores_price: false
  stores_cost: false
}

export interface ReturnCantReadonlyPricingKeyStatus {
  slot: "material_profile_width" | "finish_extra" | "labor_machine_forming" | "labor_face_bonding"
  key: string | null
  status: "present" | "missing" | "alignment_required" | "not_applicable"
  source: "/inventory/pricing" | "shared_edge_cant_rules" | "not_applicable"
  blocker?: string | null
  warning?: string | null
}

export interface ReturnCantTruthFieldCaptureReadonlyVectorEntry {
  vector_type: "Vector Litere" | "Vector Logo"
  source_row_key: string
  source_structure: "letter_group_finishes" | "artwork_finishes"
  label: string
  current_return_depth_mm: number | null
  current_raw_finish_option: string | null
  corrected_semantic_variant: ReturnCantSemanticVariant | null
  stock_color_label: string | null
  oracal_code: string | null
  ral_code: string | null
  paint_target: string | null
  catalog_reference: ReturnCantReadonlyCatalogReference | null
  catalog_source: string
  catalog_boundary_status: "reference_only" | "reusable_finish_catalog_required"
  target_component_truth_path_base: string
  target_paths: string[]
  pricing_keys_required: string[]
  pricing_keys_status: ReturnCantReadonlyPricingKeyStatus[]
  source_state: string
  confirmation_gap: string
  blockers: string[]
  warnings: string[]
}

export interface ReturnCantTruthFieldCaptureReadonlyAdapterFormula {
  quantity_basis: "ml"
  quantity_formula: "confirmed_perimeter_m"
  material_quantity_ml: "components.face.confirmed_perimeter.value"
  labor_quantity_ml: "components.face.confirmed_perimeter.value"
  pricing_values_source: "/inventory/pricing"
  catalog_values_source: "reusable_finish_catalog_future"
  component_stores_price: false
  component_stores_cost: false
  catalog_stores_price: false
  catalog_stores_cost: false
}

export interface ReturnCantTruthFieldCaptureReadonlyAdapterOutput {
  component_scope: "return_cant"
  root_template: string
  root_type: string
  quote_mode: string
  vector_entries: ReturnCantTruthFieldCaptureReadonlyVectorEntry[]
  formula: ReturnCantTruthFieldCaptureReadonlyAdapterFormula
  global_blockers: string[]
  global_warnings: string[]
  overall_readiness: "ready" | "blocked"
}

export interface ReturnCantTruthFieldCaptureReadonlyPricingRegistryEvidence {
  depthMaterialKeyPresent?: Partial<Record<30 | 60 | 80 | 100, boolean>>
  laborMachineFormingPresent?: boolean
  laborFaceBondingPresent?: boolean
  oracal651LiveKeyPresent?: boolean
  oracal651CantAlignmentClear?: boolean
  ralPaintKeyPresent?: boolean
  ralPaintAlignmentClear?: boolean
}

export interface ReturnCantTruthFieldCaptureReadonlyCatalogEvidence {
  stockColorBoundaryClear?: boolean
  oracalBoundaryClear?: boolean
  ralBoundaryClear?: boolean
}

export interface ReturnCantTruthFieldCaptureReadonlyLayerEvidence {
  letterGroupIdsBySourceKey?: Record<string, string[]>
  artworkLayerIdsBySourceKey?: Record<string, string[]>
  stepOneConfirmedArtworkKeys?: string[]
}

export interface ReturnCantTruthFieldCaptureReadonlyFacePerimeterEvidence {
  value?: number | null
  source_path?: string | null
  source_state?: string | null
  confirmation_state?: string | null
}

export interface ReturnCantTruthFieldCaptureReadonlyAdapterInput {
  templateCode?: string | null
  rootType?: string | null
  quoteMode?: string | null
  letter_group_finishes?: IntakeV4LetterGroupFinish[] | null
  artwork_finishes?: IntakeV4ArtworkFinish[] | null
  quoteGeometry?: Pick<IntakeV4QuoteGeometry, "letter_perimeter_m" | "geometry_source" | "confirmed"> | null
  layerEvidence?: ReturnCantTruthFieldCaptureReadonlyLayerEvidence | null
  pricingRegistryEvidence?: ReturnCantTruthFieldCaptureReadonlyPricingRegistryEvidence | null
  catalogEvidence?: ReturnCantTruthFieldCaptureReadonlyCatalogEvidence | null
  faceConfirmedPerimeter?: ReturnCantTruthFieldCaptureReadonlyFacePerimeterEvidence | null
}

interface ResolvedSemanticVariant {
  corrected_semantic_variant: ReturnCantSemanticVariant | null
  current_raw_finish_option: string | null
  stock_color_label: string | null
  oracal_code: string | null
  ral_code: string | null
  paint_target: string | null
  catalog_reference: ReturnCantReadonlyCatalogReference | null
  catalog_source: string
  catalog_boundary_status: "reference_only" | "reusable_finish_catalog_required"
  blockers: string[]
  warnings: string[]
}

function uniquePush(target: string[], value: string | null | undefined) {
  if (!value) return
  if (!target.includes(value)) target.push(value)
}

function nonEmptyString(value: unknown): string | null {
  if (typeof value !== "string") return null
  const trimmed = value.trim()
  return trimmed.length > 0 ? trimmed : null
}

function lower(value: unknown): string {
  return String(value ?? "").trim().toLowerCase()
}

function defaultPricingEvidence(): Required<ReturnCantTruthFieldCaptureReadonlyPricingRegistryEvidence> {
  return {
    depthMaterialKeyPresent: {
      30: true,
      60: true,
      80: true,
      100: true,
    },
    laborMachineFormingPresent: true,
    laborFaceBondingPresent: true,
    oracal651LiveKeyPresent: true,
    oracal651CantAlignmentClear: false,
    ralPaintKeyPresent: true,
    ralPaintAlignmentClear: false,
  }
}

function defaultCatalogEvidence(): Required<ReturnCantTruthFieldCaptureReadonlyCatalogEvidence> {
  return {
    stockColorBoundaryClear: false,
    oracalBoundaryClear: false,
    ralBoundaryClear: false,
  }
}

function buildTargetPaths(instanceKey: string): string[] {
  const base = `components.return_cant.instances.${instanceKey}`
  return [
    `${base}.vector_type`,
    `${base}.depth_mm`,
    `${base}.finish_variant.type`,
    `${base}.finish_variant.stock_color_label`,
    `${base}.finish_variant.oracal_code`,
    `${base}.finish_variant.ral_code`,
    `${base}.finish_variant.paint_target`,
    `${base}.finish_variant.catalog_reference`,
    `${base}.layer_group_ids`,
    `${base}.confirmation_state`,
    `${base}.perimeter_source`,
    `${base}.perimeter_dependency.face_confirmed_perimeter.*`,
    `${base}.pricing_keys.material_profile_width`,
    `${base}.pricing_keys.finish_extra`,
  ]
}

function resolveLayerGroupIds(args: {
  sourceStructure: "letter_group_finishes" | "artwork_finishes"
  sourceRowKey: string
  layerEvidence: ReturnCantTruthFieldCaptureReadonlyLayerEvidence | null | undefined
}): string[] {
  if (args.sourceStructure === "letter_group_finishes") {
    return args.layerEvidence?.letterGroupIdsBySourceKey?.[args.sourceRowKey] ?? [args.sourceRowKey]
  }
  return args.layerEvidence?.artworkLayerIdsBySourceKey?.[args.sourceRowKey] ?? [args.sourceRowKey]
}

function buildSourceState(args: {
  rowConfirmed: boolean
  sourceStructure: "letter_group_finishes" | "artwork_finishes"
  sourceRowKey: string
  layerEvidence: ReturnCantTruthFieldCaptureReadonlyLayerEvidence | null | undefined
}): string {
  const stepOneConfirmed =
    args.sourceStructure === "artwork_finishes" &&
    !!args.layerEvidence?.stepOneConfirmedArtworkKeys?.includes(args.sourceRowKey)
  if (stepOneConfirmed) return "step_one_confirmed_only"
  if (args.rowConfirmed) return "row_confirmed_only"
  return "hydrated_row_only"
}

function buildConfirmationGap(args: {
  rowConfirmed: boolean
  sourceStructure: "letter_group_finishes" | "artwork_finishes"
  sourceRowKey: string
  layerEvidence: ReturnCantTruthFieldCaptureReadonlyLayerEvidence | null | undefined
}): string {
  const stepOneConfirmed =
    args.sourceStructure === "artwork_finishes" &&
    !!args.layerEvidence?.stepOneConfirmedArtworkKeys?.includes(args.sourceRowKey)
  if (stepOneConfirmed) return "STEP_ONE_CONFIRMATION_IS_NOT_COMPONENT_CONFIRMATION"
  if (args.rowConfirmed) return "ROW_CONFIRMATION_IS_NOT_COMPONENT_CONFIRMATION"
  return "INSTANCE_CONFIRMATION_STATE_MISSING"
}

function resolveSemanticVariant(args: {
  finishType: string | undefined
  colorCode: string | undefined
  colorName: string | undefined
  catalogEvidence: Required<ReturnCantTruthFieldCaptureReadonlyCatalogEvidence>
}): ResolvedSemanticVariant {
  const token = lower(args.finishType)

  if (token === "white_aluminum") {
    return buildStockColorVariant("Alb", args.catalogEvidence.stockColorBoundaryClear)
  }
  if (token === "black_aluminum") {
    return buildStockColorVariant("Negru", args.catalogEvidence.stockColorBoundaryClear)
  }
  if (token === "gold_aluminum") {
    return buildStockColorVariant("Auriu", args.catalogEvidence.stockColorBoundaryClear)
  }
  if (token === "mirror_silver" || token === "standard_aluminum") {
    const variant = buildStockColorVariant("Argintiu", args.catalogEvidence.stockColorBoundaryClear)
    if (token === "standard_aluminum") {
      uniquePush(variant.warnings, "LEGACY_STANDARD_ALUMINUM_NORMALIZED_TO_STOCK_COLOR")
    }
    return variant
  }
  if (token === "oracal_wrapped" || token === "oracal_651" || token === "vinyl") {
    const warnings: string[] = []
    if (!args.catalogEvidence.oracalBoundaryClear) {
      uniquePush(warnings, "REUSABLE_ORACAL_CATALOG_BOUNDARY_REQUIRED")
    }
    return {
      corrected_semantic_variant: "oracal",
      current_raw_finish_option: "Oracal 651",
      stock_color_label: null,
      oracal_code: nonEmptyString(args.colorCode) ?? null,
      ral_code: null,
      paint_target: null,
      catalog_reference: {
        family: "oracal",
        reference: nonEmptyString(args.colorCode) ?? null,
        display_label: nonEmptyString(args.colorName) ?? nonEmptyString(args.colorCode) ?? "Oracal 651",
        stores_price: false,
        stores_cost: false,
      },
      catalog_source: "reusable_oracal_catalog",
      catalog_boundary_status: args.catalogEvidence.oracalBoundaryClear
        ? "reference_only"
        : "reusable_finish_catalog_required",
      blockers:
        nonEmptyString(args.colorCode) == null
          ? ["RETURN_CANT_ORACAL_CODE_MISSING"]
          : [],
      warnings,
    }
  }
  if (token === "ral_paint" || token === "painted" || token === "paint") {
    const warnings: string[] = []
    if (!args.catalogEvidence.ralBoundaryClear) {
      uniquePush(warnings, "REUSABLE_RAL_CATALOG_BOUNDARY_REQUIRED")
    }
    return {
      corrected_semantic_variant: "ral_paint",
      current_raw_finish_option: "Vopsit RAL",
      stock_color_label: null,
      oracal_code: null,
      ral_code: nonEmptyString(args.colorCode) ?? null,
      paint_target: null,
      catalog_reference: {
        family: "ral_paint",
        reference: nonEmptyString(args.colorCode) ?? null,
        display_label: nonEmptyString(args.colorName) ?? nonEmptyString(args.colorCode) ?? "Vopsit RAL",
        stores_price: false,
        stores_cost: false,
      },
      catalog_source: "reusable_ral_catalog",
      catalog_boundary_status: args.catalogEvidence.ralBoundaryClear
        ? "reference_only"
        : "reusable_finish_catalog_required",
      blockers: [
        ...(nonEmptyString(args.colorCode) == null ? ["RETURN_CANT_RAL_CODE_MISSING"] : []),
        "RETURN_CANT_PAINT_TARGET_FIELD_MISSING",
      ],
      warnings,
    }
  }

  return {
    corrected_semantic_variant: null,
    current_raw_finish_option: nonEmptyString(args.finishType),
    stock_color_label: null,
    oracal_code: null,
    ral_code: null,
    paint_target: null,
    catalog_reference: null,
    catalog_source: "reusable_finish_catalog_required",
    catalog_boundary_status: "reusable_finish_catalog_required",
    blockers: ["RETURN_CANT_FINISH_VARIANT_UNSUPPORTED"],
    warnings: ["RETURN_CANT_FINISH_VARIANT_REQUIRES_OWNER_MAPPING"],
  }
}

function buildStockColorVariant(
  stockColorLabel: string,
  stockColorBoundaryClear: boolean,
): ResolvedSemanticVariant {
  return {
    corrected_semantic_variant: "stock_color",
    current_raw_finish_option: stockColorLabel,
    stock_color_label: stockColorLabel,
    oracal_code: null,
    ral_code: null,
    paint_target: null,
    catalog_reference: {
      family: "stock_color",
      reference: stockColorLabel,
      display_label: stockColorLabel,
      stores_price: false,
      stores_cost: false,
    },
    catalog_source: stockColorBoundaryClear
      ? "reusable_finish_catalog_required"
      : "stock_color_catalog_future",
    catalog_boundary_status: stockColorBoundaryClear
      ? "reference_only"
      : "reusable_finish_catalog_required",
    blockers: [],
    warnings: stockColorBoundaryClear ? [] : ["REUSABLE_FINISH_CATALOG_BOUNDARY_REQUIRED"],
  }
}

function buildPricingKeyStatuses(args: {
  depthMm: number | null
  semanticVariant: ReturnCantSemanticVariant | null
  pricingEvidence: Required<ReturnCantTruthFieldCaptureReadonlyPricingRegistryEvidence>
}): ReturnCantReadonlyPricingKeyStatus[] {
  const statuses: ReturnCantReadonlyPricingKeyStatus[] = []
  const depthKey = args.depthMm == null ? null : DEPTH_TO_PROFILE_KEY[args.depthMm]
  const depthKeyPresent =
    args.depthMm != null &&
    (args.pricingEvidence.depthMaterialKeyPresent[args.depthMm as 30 | 60 | 80 | 100] ?? false)

  statuses.push({
    slot: "material_profile_width",
    key: depthKey,
    status: depthKey == null ? "missing" : depthKeyPresent ? "present" : "missing",
    source: "/inventory/pricing",
    blocker: depthKey == null || !depthKeyPresent ? "RETURN_CANT_DEPTH_PRICING_KEY_MISSING" : null,
  })

  statuses.push({
    slot: "labor_machine_forming",
    key: GENERIC_LABOR_KEYS[0],
    status: args.pricingEvidence.laborMachineFormingPresent ? "present" : "missing",
    source: "/inventory/pricing",
    blocker: args.pricingEvidence.laborMachineFormingPresent ? null : "RETURN_CANT_LABOR_PRICING_KEY_MISSING",
  })

  statuses.push({
    slot: "labor_face_bonding",
    key: GENERIC_LABOR_KEYS[1],
    status: args.pricingEvidence.laborFaceBondingPresent ? "present" : "missing",
    source: "/inventory/pricing",
    blocker: args.pricingEvidence.laborFaceBondingPresent ? null : "RETURN_CANT_LABOR_PRICING_KEY_MISSING",
  })

  if (args.semanticVariant === "stock_color") {
    statuses.push({
      slot: "finish_extra",
      key: null,
      status: "not_applicable",
      source: "not_applicable",
    })
    return statuses
  }

  if (args.semanticVariant === "oracal") {
    statuses.push({
      slot: "finish_extra",
      key: args.pricingEvidence.oracal651LiveKeyPresent ? "MAT-ORACAL-651" : null,
      status: args.pricingEvidence.oracal651CantAlignmentClear ? "present" : "alignment_required",
      source: args.pricingEvidence.oracal651CantAlignmentClear ? "/inventory/pricing" : "shared_edge_cant_rules",
      blocker: args.pricingEvidence.oracal651CantAlignmentClear
        ? null
        : "ORACAL_651_CANT_PRICING_ALIGNMENT_REQUIRED",
      warning: args.pricingEvidence.oracal651CantAlignmentClear
        ? null
        : "REUSABLE_ORACAL_CATALOG_BOUNDARY_REQUIRED",
    })
    return statuses
  }

  if (args.semanticVariant === "ral_paint") {
    statuses.push({
      slot: "finish_extra",
      key: args.pricingEvidence.ralPaintKeyPresent ? "MAT-VOPSEA-RAL" : null,
      status: args.pricingEvidence.ralPaintAlignmentClear ? "present" : "alignment_required",
      source: "/inventory/pricing",
      blocker: args.pricingEvidence.ralPaintAlignmentClear
        ? null
        : "RETURN_CANT_RAL_PAINT_PRICING_ALIGNMENT_REQUIRED",
    })
  }

  return statuses
}

function buildPricingKeysRequired(statuses: ReturnCantReadonlyPricingKeyStatus[]): string[] {
  const required: string[] = []
  for (const status of statuses) {
    uniquePush(required, status.key)
  }
  return required
}

function buildGlobalPerimeterState(input: ReturnCantTruthFieldCaptureReadonlyAdapterInput, target: string[]) {
  if (
    input.faceConfirmedPerimeter?.value != null &&
    lower(input.faceConfirmedPerimeter.source_state) === "confirmed" &&
    lower(input.faceConfirmedPerimeter.confirmation_state) === "confirmed"
  ) {
    return
  }

  uniquePush(target, "RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED")
  if (input.quoteGeometry?.letter_perimeter_m != null) {
    uniquePush(target, "QUOTE_GEOMETRY_LETTER_PERIMETER_CONTEXT_ONLY")
  }
}

function buildEntry(args: {
  vectorType: "Vector Litere" | "Vector Logo"
  sourceStructure: "letter_group_finishes" | "artwork_finishes"
  sourceRowKey: string
  label: string
  finishType: string | undefined
  colorCode: string | undefined
  colorName: string | undefined
  depthMm: number | undefined
  rowConfirmed: boolean
  input: ReturnCantTruthFieldCaptureReadonlyAdapterInput
  pricingEvidence: Required<ReturnCantTruthFieldCaptureReadonlyPricingRegistryEvidence>
  catalogEvidence: Required<ReturnCantTruthFieldCaptureReadonlyCatalogEvidence>
}): ReturnCantTruthFieldCaptureReadonlyVectorEntry {
  const semantic = resolveSemanticVariant({
    finishType: args.finishType,
    colorCode: args.colorCode,
    colorName: args.colorName,
    catalogEvidence: args.catalogEvidence,
  })

  const pricing_keys_status = buildPricingKeyStatuses({
    depthMm: args.depthMm ?? null,
    semanticVariant: semantic.corrected_semantic_variant,
    pricingEvidence: args.pricingEvidence,
  })
  const pricing_keys_required = buildPricingKeysRequired(pricing_keys_status)
  const blockers = [...semantic.blockers]
  const warnings = [...semantic.warnings]

  if (args.depthMm == null || !(args.depthMm in DEPTH_TO_PROFILE_KEY)) {
    uniquePush(blockers, "RETURN_CANT_DEPTH_PRICING_KEY_MISSING")
  }
  if (pricing_keys_status.some((status) => status.blocker)) {
    for (const status of pricing_keys_status) {
      uniquePush(blockers, status.blocker)
      uniquePush(warnings, status.warning)
    }
  }

  uniquePush(blockers, "RETURN_CANT_MATERIAL_MISSING")
  uniquePush(blockers, "RETURN_CANT_SOURCE_STATE_NOT_CONFIRMED")
  uniquePush(blockers, "RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED")

  if (args.input.faceConfirmedPerimeter == null || args.input.faceConfirmedPerimeter.value == null) {
    uniquePush(blockers, "RETURN_CANT_PERIMETER_MISSING")
  }
  if (args.input.quoteGeometry?.letter_perimeter_m != null) {
    uniquePush(warnings, "QUOTE_GEOMETRY_LETTER_PERIMETER_CONTEXT_ONLY")
  }
  if (
    args.sourceStructure === "artwork_finishes" &&
    args.input.layerEvidence?.stepOneConfirmedArtworkKeys?.includes(args.sourceRowKey)
  ) {
    uniquePush(warnings, "STEP_ONE_CONFIRMATION_NOT_PROMOTED_TO_COMPONENT_TRUTH")
  }

  const target_component_truth_path_base = `components.return_cant.instances.${args.sourceRowKey}`
  return {
    vector_type: args.vectorType,
    source_row_key: args.sourceRowKey,
    source_structure: args.sourceStructure,
    label: args.label,
    current_return_depth_mm: args.depthMm ?? null,
    current_raw_finish_option: semantic.current_raw_finish_option,
    corrected_semantic_variant: semantic.corrected_semantic_variant,
    stock_color_label: semantic.stock_color_label,
    oracal_code: semantic.oracal_code,
    ral_code: semantic.ral_code,
    paint_target: semantic.paint_target,
    catalog_reference: semantic.catalog_reference,
    catalog_source: semantic.catalog_source,
    catalog_boundary_status: semantic.catalog_boundary_status,
    target_component_truth_path_base,
    target_paths: buildTargetPaths(args.sourceRowKey),
    pricing_keys_required,
    pricing_keys_status,
    source_state: buildSourceState({
      rowConfirmed: args.rowConfirmed,
      sourceStructure: args.sourceStructure,
      sourceRowKey: args.sourceRowKey,
      layerEvidence: args.input.layerEvidence,
    }),
    confirmation_gap: buildConfirmationGap({
      rowConfirmed: args.rowConfirmed,
      sourceStructure: args.sourceStructure,
      sourceRowKey: args.sourceRowKey,
      layerEvidence: args.input.layerEvidence,
    }),
    blockers: dedupe(blockers),
    warnings: dedupe([
      ...warnings,
      resolveLayerGroupIds({
        sourceStructure: args.sourceStructure,
        sourceRowKey: args.sourceRowKey,
        layerEvidence: args.input.layerEvidence,
      }).length > 0
        ? "LAYER_GROUP_IDS_CAPTURED_AS_ROW_ID_EVIDENCE_ONLY"
        : "RETURN_CANT_LAYER_GROUP_SOURCE_MISSING",
    ]),
  }
}

function dedupe(values: string[]): string[] {
  return [...new Set(values)]
}

export function mapReturnCantTruthFieldCaptureReadonlyAdapter(
  input: ReturnCantTruthFieldCaptureReadonlyAdapterInput,
): ReturnCantTruthFieldCaptureReadonlyAdapterOutput {
  const pricingEvidence = {
    ...defaultPricingEvidence(),
    ...input.pricingRegistryEvidence,
    depthMaterialKeyPresent: {
      ...defaultPricingEvidence().depthMaterialKeyPresent,
      ...input.pricingRegistryEvidence?.depthMaterialKeyPresent,
    },
  }
  const catalogEvidence = {
    ...defaultCatalogEvidence(),
    ...input.catalogEvidence,
  }

  const vector_entries: ReturnCantTruthFieldCaptureReadonlyVectorEntry[] = []

  for (const group of input.letter_group_finishes ?? []) {
    const cant = letterGroupToReturnCant(group)
    vector_entries.push(
      buildEntry({
        vectorType: "Vector Litere",
        sourceStructure: "letter_group_finishes",
        sourceRowKey: group.group_key,
        label: nonEmptyString(group.layer_name) ?? group.group_key,
        finishType: cant.finishType,
        colorCode: cant.colorCode,
        colorName: cant.colorName,
        depthMm: cant.depthMm,
        rowConfirmed: !!group.confirmed,
        input,
        pricingEvidence,
        catalogEvidence,
      }),
    )
  }

  for (const row of input.artwork_finishes ?? []) {
    const cant = artworkToReturnCant(row)
    vector_entries.push(
      buildEntry({
        vectorType: "Vector Logo",
        sourceStructure: "artwork_finishes",
        sourceRowKey: row.layer_key,
        label: nonEmptyString(row.layer_name) ?? row.layer_key,
        finishType: cant.finishType,
        colorCode: cant.colorCode,
        colorName: cant.colorName,
        depthMm: cant.depthMm,
        rowConfirmed: !!row.confirmed,
        input,
        pricingEvidence,
        catalogEvidence,
      }),
    )
  }

  const global_blockers = dedupe(vector_entries.flatMap((entry) => entry.blockers))
  const global_warnings = dedupe(vector_entries.flatMap((entry) => entry.warnings))

  if (!vector_entries.length) {
    uniquePush(global_blockers, "RETURN_CANT_VECTOR_ROWS_MISSING")
  }
  buildGlobalPerimeterState(input, global_blockers)
  if (input.quoteGeometry?.letter_perimeter_m != null) {
    uniquePush(global_warnings, "QUOTE_GEOMETRY_LETTER_PERIMETER_CONTEXT_ONLY")
  }

  return {
    component_scope: COMPONENT_SCOPE,
    root_template: nonEmptyString(input.templateCode) ?? ROOT_TEMPLATE,
    root_type: nonEmptyString(input.rootType) ?? ROOT_TYPE,
    quote_mode: nonEmptyString(input.quoteMode) ?? QUOTE_MODE,
    vector_entries,
    formula: {
      quantity_basis: "ml",
      quantity_formula: "confirmed_perimeter_m",
      material_quantity_ml: "components.face.confirmed_perimeter.value",
      labor_quantity_ml: "components.face.confirmed_perimeter.value",
      pricing_values_source: "/inventory/pricing",
      catalog_values_source: "reusable_finish_catalog_future",
      component_stores_price: false,
      component_stores_cost: false,
      catalog_stores_price: false,
      catalog_stores_cost: false,
    },
    global_blockers,
    global_warnings,
    overall_readiness: global_blockers.length > 0 ? "blocked" : "ready",
  }
}
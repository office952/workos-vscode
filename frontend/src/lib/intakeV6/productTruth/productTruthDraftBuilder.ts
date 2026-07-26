import { evaluateProductTruthDraftReadiness } from "./productTruthReadiness";
import type {
  ProductTruthAuditEntry,
  ProductTruthDraft,
  ProductTruthDraftBuilderInput,
  ProductTruthField,
  ProductTruthIssue,
  ProductTruthLayer,
  ProductTruthLayerRoleInputLayer,
  ProductTruthSourceKind,
  ProductTruthSourceRef,
  ProductTruthState,
} from "./productTruthTypes";

const BAR_MOUNTING_SYSTEMS = new Set(["steel_bars", "aluminum_bars"]);
const SUPPORT_LAYER_ROLES = new Set(["support_panel", "frame"]);

function sourceRef(
  sourceArea: string,
  sourcePath: string,
  fieldPath: string,
  state: ProductTruthState,
  note?: string,
  sourceKind: ProductTruthSourceKind = "unknown",
): ProductTruthSourceRef {
  return { sourceKind, sourceArea, sourcePath, fieldPath, state, note };
}

function field<T>(value: T, state: ProductTruthState, refs: ProductTruthSourceRef[], blockers: string[] = [], warnings: string[] = []): ProductTruthField<T> {
  return { value, state, sourceRefs: refs, blockers, warnings };
}

function stringOrNull(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

function numberOrNull(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function setupState(input: ProductTruthDraftBuilderInput, fieldName: string, fallbackUsed = false): ProductTruthState {
  if (fallbackUsed) return "fallback";
  if (!input.finishSetup || !(fieldName in input.finishSetup)) return "unknown";
  return input.finishSetup.confirmed === true ? "confirmed" : "hydrated";
}

function sourceKindForState(state: ProductTruthState): ProductTruthSourceKind {
  if (state === "fallback") return "owner_default";
  if (state === "hydrated") return "hydrated";
  if (state === "manual") return "manual";
  if (state === "confirmed") return "operator";
  if (state === "suggested") return "analyzer";
  if (state === "unknown") return "unknown";
  return "existing_form";
}

function setupRef(fieldPath: string, state: ProductTruthState, note?: string): ProductTruthSourceRef {
  return sourceRef("Intake V6 Review finish setup", "finish_setup", fieldPath, state, note, sourceKindForState(state));
}

function layerKey(layer: ProductTruthLayerRoleInputLayer): string {
  return stringOrNull(layer.layer_key) ?? stringOrNull(layer.layerKey) ?? "unknown_layer";
}

function layerName(layer: ProductTruthLayerRoleInputLayer): string {
  return stringOrNull(layer.layer_name) ?? stringOrNull(layer.layerName) ?? layerKey(layer);
}

function autoRole(layer: ProductTruthLayerRoleInputLayer): string | null {
  return stringOrNull(layer.auto_role) ?? stringOrNull(layer.autoRole);
}

function confirmedRole(layer: ProductTruthLayerRoleInputLayer): string | null {
  return stringOrNull(layer.confirmed_role) ?? stringOrNull(layer.confirmedRole);
}

function confirmationState(layer: ProductTruthLayerRoleInputLayer): "pending" | "confirmed" | "ignored" {
  return layer.confirmation_state ?? layer.confirmationState ?? "pending";
}

function operatorDecision(layer: ProductTruthLayerRoleInputLayer): "printed" | "artwork_only" | "ignored" | null {
  return layer.operator_decision ?? layer.operatorDecision ?? null;
}

function makeIssue(
  code: string,
  severity: "blocker" | "warning",
  component: ProductTruthIssue["component"],
  gates: ProductTruthIssue["gates"],
  message: string,
  refs: ProductTruthSourceRef[],
): ProductTruthIssue {
  const primaryRef = refs[0];
  return {
    code,
    severity,
    component,
    affectedComponent: component,
    affectedField: primaryRef?.fieldPath ?? component,
    source: primaryRef?.sourceKind ?? "unknown",
    quoteBlocker: gates.includes("commercial_proposal") || gates.includes("quote_snapshot"),
    orderBlocker: gates.includes("order_snapshot") || gates.includes("product_aggregate") || gates.includes("execution_plan"),
    executionBlocker: gates.includes("execution_plan"),
    gates,
    message,
    sourceRefs: refs,
  };
}

function buildLayers(input: ProductTruthDraftBuilderInput): ProductTruthLayer[] {
  return (input.layerRoleSetup?.layers ?? []).map((item) => {
    const key = layerKey(item);
    const name = layerName(item);
    const state = confirmationState(item);
    const auto = autoRole(item);
    const confirmed = confirmedRole(item);
    const decision = operatorDecision(item);
    const baseState = state === "confirmed" || state === "ignored" ? "confirmed" : "suggested";
    const base = sourceRef(
      "SVG Analyzer layer role setup",
      "layer_role_setup.layers",
      key,
      baseState,
      decision ? `Operator decision: ${decision}` : undefined,
      state === "pending" ? "analyzer" : "operator",
    );
    const role = state === "ignored" || decision === "ignored" ? "ignore" : confirmed;
    return {
      layerKey: key,
      layerName: name,
      autoRole: field(auto, auto ? "suggested" : "unknown", [base]),
      confirmedRole: field(role, state === "confirmed" || state === "ignored" ? "confirmed" : "blocked", [base], state === "pending" ? ["LAYER_ROLE_NOT_CONFIRMED"] : []),
      confirmationState: field(state, state === "pending" ? "blocked" : "confirmed", [base], state === "pending" ? ["LAYER_ROLE_NOT_CONFIRMED"] : []),
    };
  });
}

function deriveOracalSeries(faceFinishType: string | null): string | null {
  if (!faceFinishType) return null;
  const match = faceFinishType.match(/oracal[_-](641|651|8500)/i);
  return match ? match[1] : null;
}

function deriveArtworkPrintRequired(executionType: string | null): boolean | null {
  if (!executionType) return null;
  if (executionType === "print_laminate" || executionType === "print" || executionType === "print_on_vinyl_laminated") return true;
  if (executionType === "vinyl_cut" || executionType === "ignore") return false;
  return null;
}

function deriveArtworkLaminationRequired(executionType: string | null): boolean | null {
  if (!executionType) return null;
  if (executionType === "print_laminate" || executionType === "print_on_vinyl_laminated") return true;
  if (executionType === "print" || executionType === "vinyl_cut" || executionType === "ignore") return false;
  return null;
}

function isFinishActive(finishType: string | null): boolean {
  const token = String(finishType ?? "").trim().toLowerCase();
  return token.length > 0 && token !== "none" && token !== "no_finish";
}

function isReturnActive(finishType: string | null | undefined): boolean {
  const token = String(finishType ?? "").trim().toLowerCase();
  return token.length > 0 && token !== "none" && token !== "no_return" && token !== "without_return";
}

function commercialArtworkLayers(layers: ProductTruthLayer[]): ProductTruthLayer[] {
  return layers.filter((item) => item.confirmedRole.value === "printed_artwork" || item.autoRole.value === "printed_artwork");
}

export function buildProductTruthDraft(input: ProductTruthDraftBuilderInput): ProductTruthDraft {
  const blockers: ProductTruthIssue[] = [];
  const warnings: ProductTruthIssue[] = [];
  const audit: ProductTruthAuditEntry[] = [];
  const generatedAt = input.generatedAt ?? new Date(0).toISOString();
  const finish = input.finishSetup ?? {};
  const layers = buildLayers(input);
  const layerConfirmationStatus = input.layerRoleSetup?.confirmation_status ?? input.layerRoleSetup?.confirmationStatus ?? "missing";

  const metadataSource = sourceRef("Intake V6 workspace", "workspace", "metadata", "hydrated");
  const missingMetadataRefs = [metadataSource];
  if (!input.workspaceId) {
    blockers.push(makeIssue("WORKSPACE_ID_MISSING", "blocker", "metadata", ["review", "internal_draft"], "Workspace id is required for traceable Product Truth draft.", missingMetadataRefs));
  }
  if (!input.templateCode) {
    blockers.push(makeIssue("TEMPLATE_CODE_MISSING", "blocker", "metadata", ["review", "internal_draft"], "Template code is required for volumetric letters Product Truth.", missingMetadataRefs));
  }

  const svgRefs = [sourceRef("SVG source", "svg_source", "file_name", input.svgSource?.fileName ? "hydrated" : "blocked")];
  if (!input.svgSource?.fileName) {
    blockers.push(makeIssue("SVG_SOURCE_MISSING", "blocker", "source_svg", ["review", "internal_draft"], "SVG source file is missing.", svgRefs));
  }

  const layerRefs = [sourceRef("SVG Analyzer layer role setup", "layer_role_setup", "confirmation_status", layerConfirmationStatus === "complete" ? "confirmed" : "blocked")];
  if (layerConfirmationStatus !== "complete" || layers.some((item) => item.confirmationState.value === "pending")) {
    blockers.push(makeIssue("LAYER_ROLES_INCOMPLETE", "blocker", "layers", ["review", "internal_draft", "commercial_proposal"], "Layer/group roles are not fully operator-confirmed.", layerRefs));
  }

  const geometry = input.quoteGeometry ?? {};
  const geometryRefs = [sourceRef("Intake V6 quote geometry", "quote_geometry", "geometry", geometry.confirmed ? "confirmed" : "hydrated", undefined, geometry.confirmed ? "operator" : "hydrated")];
  if (numberOrNull(geometry.letter_count) == null || numberOrNull(geometry.face_area_m2) == null) {
    blockers.push(makeIssue("QUOTE_GEOMETRY_INCOMPLETE", "blocker", "geometry", ["review", "internal_draft", "commercial_proposal"], "Quote geometry needs letter count and face area for the draft.", geometryRefs));
  }

  const faceGroupRefs = layers
    .filter((item) => item.confirmedRole.value === "face" || (item.confirmedRole.value == null && item.autoRole.value === "face"))
    .map((item) => item.layerKey);
  const faceMaterialValue = stringOrNull(finish.face_material_family) ?? "plexiglas_opal";
  const faceMaterialState: ProductTruthState = finish.face_material_confirmed === true ? "confirmed" : "fallback";
  const faceThicknessValue = numberOrNull(finish.face_thickness_mm) ?? 3;
  const faceThicknessState: ProductTruthState = finish.face_thickness_confirmed === true ? "confirmed" : "fallback";
  const faceDefaultRefs = [setupRef("face.material_family", faceMaterialState, "Owner-approved default; explicit runtime control is not implemented yet.")];
  if (faceMaterialState !== "confirmed") {
    blockers.push(makeIssue("FACE_MATERIAL_FALLBACK_REQUIRES_CONFIRMATION", "blocker", "face", ["commercial_proposal"], "Face material is owner-approved fallback and still needs canonical confirmation before downstream use.", faceDefaultRefs));
  }
  if (faceThicknessState !== "confirmed") {
    blockers.push(makeIssue("FACE_THICKNESS_FALLBACK_REQUIRES_CONFIRMATION", "blocker", "face", ["commercial_proposal"], "Face thickness is owner-approved fallback and still needs canonical confirmation before downstream use.", faceDefaultRefs));
  }

  const backingMode = finish.backing_mode ?? "forex_10_no_bevel";
  const backingFallbackUsed = finish.backing_mode == null;
  const backingState = setupState(input, "backing_mode", backingFallbackUsed);
  const backBevel = finish.back_bevel_enabled ?? backingMode === "forex_10_with_bevel";
  const backBevelState: ProductTruthState = finish.back_bevel_enabled === true && finish.confirmed !== true ? "manual" : backingState;
  const returnDepthExplicit = numberOrNull(finish.return_depth_mm);
  const returnDepth = returnDepthExplicit ?? 60;
  const returnDepthState = setupState(input, "return_depth_mm", finish.return_depth_mm == null);
  const faceFinishState = setupState(input, "face_finish_type", finish.face_finish_type == null);
  const faceFinishType = stringOrNull(finish.face_finish_type);
  const finishTarget = finish.finish_target ?? null;
  const finishTargetRefs = [setupRef("finish_target", finishTarget ? setupState(input, "finish_target") : "blocked", "Existing UI implies target by zone; canonical field is explicit in this draft only when supplied.")];
  if (isFinishActive(faceFinishType) && !finishTarget) {
    blockers.push(makeIssue("FINISH_TARGET_MISSING", "blocker", "finish", ["commercial_proposal"], "Finish is active but canonical finish target is missing.", finishTargetRefs));
  }
  if (isReturnActive(finish.return_finish_type) && returnDepthExplicit == null) {
    blockers.push(makeIssue("RETURN_CANT_DEPTH_MISSING", "blocker", "return_cant", ["commercial_proposal", "order_snapshot", "execution_plan"], "Return/cant finish is active but depth is not explicitly present.", [setupRef("return_depth_mm", "blocked")]));
  }
  const oracalSeries = deriveOracalSeries(faceFinishType);
  const mountingSystem = stringOrNull(finish.mounting_system) ?? "direct_wall";
  const mountingSystemState = setupState(input, "mounting_system", finish.mounting_system == null);
  const mountingScope = finish.mounting_scope ?? null;
  const mountingScopeRef = setupRef(
    "mounting_scope",
    finish.mounting_scope ? setupState(input, "mounting_scope") : "blocked",
    "Commercial mounting scope from Intake V6 Montaj tab.",
  );
  if (!finish.mounting_scope) {
    blockers.push(makeIssue("MOUNTING_SCOPE_MISSING", "blocker", "mounting", ["commercial_proposal"], "Mounting scope is not explicitly set.", [mountingScopeRef]));
  }

  const supportLayerEvidence = layers.some((item) => SUPPORT_LAYER_ROLES.has(item.confirmedRole.value ?? item.autoRole.value ?? ""));
  const barMountingEvidence = BAR_MOUNTING_SYSTEMS.has(mountingSystem);
  const supportWarningRefs = [setupRef("mounting_system", "warning", "Bridge evidence only; mounting is not confirmed support truth.")];
  let supportRequired: "yes" | "no" | "suggested" | "unknown" = finish.support_required ?? "unknown";
  let supportState: ProductTruthState = finish.support_required === "yes" || finish.support_required === "no" ? setupState(input, "support_required") : "unknown";
  let supportType: string | null = finish.support_type ?? null;
  let supportSource: string | null = finish.support_source ?? null;
  if (!finish.support_required && (supportLayerEvidence || barMountingEvidence)) {
    supportRequired = "suggested";
    supportState = "suggested";
    supportType = barMountingEvidence ? mountingSystem : null;
    supportSource = supportLayerEvidence ? "detected_svg" : "mounting_bridge";
    warnings.push(makeIssue("SUPPORT_MOUNTING_BRIDGE_NOT_CANONICAL", "warning", "support", ["commercial_proposal", "order_snapshot", "execution_plan"], "Support remains separate from mounting; current bridge evidence is not confirmed support truth.", supportWarningRefs));
  } else if (!finish.support_required) {
    warnings.push(makeIssue("SUPPORT_REQUIRED_UNKNOWN", "warning", "support", ["commercial_proposal"], "No first-class support_required field exists yet; absence of support is not confirmed truth.", supportWarningRefs));
  }
  if (supportRequired === "yes" && !supportType) {
    blockers.push(makeIssue("SUPPORT_TYPE_MISSING", "blocker", "support", ["commercial_proposal", "order_snapshot", "execution_plan"], "Support is required but support type is missing.", [setupRef("support_type", "blocked")]));
  }

  const groupFinishes = (finish.letter_group_finishes ?? []).map((group) => {
    const groupState: ProductTruthState = group.confirmed === true ? "confirmed" : "hydrated";
    const ref = setupRef(`letter_group_finishes.${group.group_key}`, groupState);
    return {
      groupKey: group.group_key,
      layerName: group.layer_name ?? null,
      faceFinishType: field(group.face_finish_type ?? faceFinishType, groupState, [ref]),
      faceOracalCode: field(group.face_oracal_code ?? null, group.face_oracal_code ? groupState : "unknown", [ref]),
      returnFinishType: field(group.return_finish_type ?? finish.return_finish_type ?? null, groupState, [ref]),
      returnDepthMm: field(numberOrNull(group.return_depth_mm) ?? returnDepth, groupState, [ref]),
      faceVinylRollWidthMm: field(numberOrNull(group.face_vinyl_roll_width_mm) ?? numberOrNull(finish.face_vinyl_roll_width_mm), groupState, [ref]),
      confirmed: field(group.confirmed === true, group.confirmed === true ? "confirmed" : "hydrated", [ref], group.confirmed === true ? [] : ["GROUP_FINISH_NOT_CONFIRMED"]),
    };
  });

  const artworkItems = (finish.artwork_finishes ?? []).map((artwork) => {
    const artworkDecision = artwork.artwork_decision ?? (artwork.execution_type === "ignore" ? "ignored" : null);
    const artworkState: ProductTruthState = artwork.confirmed === true ? "confirmed" : artworkDecision ? "manual" : "hydrated";
    const ref = setupRef(`artwork_finishes.${artwork.layer_key}`, artworkState, "Encoded artwork execution is split into print and lamination draft fields.");
    const executionType = stringOrNull(artwork.execution_type);
    const printRequired = artwork.print_required ?? (artworkDecision === "artwork_only" || artworkDecision === "ignored" ? false : deriveArtworkPrintRequired(executionType));
    const laminationRequired = artwork.lamination_required ?? (artworkDecision === "artwork_only" || artworkDecision === "ignored" ? false : deriveArtworkLaminationRequired(executionType));
    if (executionType === "print_laminate") {
      warnings.push(makeIssue("PRINT_LAMINATION_ENCODED_NOT_CANONICAL", "warning", "artwork", ["commercial_proposal"], "Current artwork execution encodes print and lamination together; draft separates them but does not persist new booleans.", [ref]));
    }
    if (printRequired === false && laminationRequired === true) {
      warnings.push(makeIssue("LAMINATION_WITHOUT_PRINT", "warning", "finish", ["commercial_proposal", "order_snapshot"], "Lamination is selected without print; operator/policy review is required.", [ref]));
    }
    return {
      layerKey: artwork.layer_key,
      layerName: artwork.layer_name ?? null,
      artworkDecision: field(artworkDecision ?? (printRequired === true ? "printed" : "needs_decision"), artworkDecision ? artworkState : "unknown", [ref], artworkDecision || printRequired === true ? [] : ["ARTWORK_DECISION_MISSING"]),
      executionType: field(executionType, artworkState, [ref]),
      printRequired: field(printRequired, printRequired == null ? "unknown" : artworkState, [ref], printRequired == null ? ["PRINT_REQUIRED_UNKNOWN"] : []),
      laminationRequired: field(laminationRequired, laminationRequired == null ? "unknown" : artworkState, [ref], laminationRequired == null ? ["LAMINATION_REQUIRED_UNKNOWN"] : []),
      materialCode: field(artwork.material_code ?? null, artwork.material_code ? artworkState : "unknown", [ref]),
      estimatedAreaM2: field(numberOrNull(artwork.estimated_area_m2), numberOrNull(artwork.estimated_area_m2) == null ? "unknown" : artworkState, [ref]),
      confirmed: field(artwork.confirmed === true, artwork.confirmed === true ? "confirmed" : "hydrated", [ref], artwork.confirmed === true ? [] : ["ARTWORK_FINISH_NOT_CONFIRMED"]),
    };
  });
  const artworkDecisionKeys = new Set(artworkItems.map((item) => item.layerKey));
  for (const artworkLayer of commercialArtworkLayers(layers)) {
    if (artworkLayer.confirmationState.value === "pending") continue;
    if (!artworkDecisionKeys.has(artworkLayer.layerKey)) {
      blockers.push(makeIssue("ARTWORK_DECISION_MISSING", "blocker", "artwork", ["commercial_proposal", "order_snapshot", "execution_plan"], "Confirmed printed artwork layer requires explicit printed/artwork-only/ignored decision.", [sourceRef("SVG Analyzer layer role setup", "layer_role_setup.layers", artworkLayer.layerKey, "blocked", undefined, "operator")]));
    }
  }

  const printRequiredValues = artworkItems.map((item) => item.printRequired.value).filter((value): value is boolean => value != null);
  const laminationRequiredValues = artworkItems.map((item) => item.laminationRequired.value).filter((value): value is boolean => value != null);
  const hasPrintedArtworkSuggestion = layers.some((item) => item.autoRole.value === "printed_artwork" || item.confirmedRole.value === "printed_artwork");
  if (finish.extra_cable_or_site_details && !finish.extra_cable_quote_scope) {
    warnings.push(makeIssue("ELECTRICAL_SITE_DETAILS_ORDER_EXECUTION_ONLY", "warning", "electrical", ["order_snapshot", "execution_plan"], "Extra cable, site details, and PSU placement stay order/execution-only unless explicitly marked as quote scope.", [setupRef("electrical.extra_cable_or_site_details", "manual")]));
  }
  if (finish.psu_placement && !finish.extra_cable_quote_scope) {
    warnings.push(makeIssue("PSU_PLACEMENT_ORDER_EXECUTION_ONLY", "warning", "electrical", ["order_snapshot", "execution_plan"], "PSU placement is captured for later order/execution planning and is not Product Truth for quote scope by default.", [setupRef("electrical.psu_placement", "manual")]));
  }

  const draftWithoutReadiness: Omit<ProductTruthDraft, "readiness"> = {
    metadata: {
      schemaVersion: "product_truth_draft_v1",
      workspaceId: field(input.workspaceId ?? null, input.workspaceId ? "hydrated" : "blocked", [metadataSource]),
      workspaceCode: field(input.workspaceCode ?? null, input.workspaceCode ? "hydrated" : "unknown", [metadataSource]),
      intakeId: field(input.intakeId ?? null, input.intakeId ? "hydrated" : "unknown", [metadataSource]),
      templateCode: field(input.templateCode ?? null, input.templateCode ? "hydrated" : "blocked", [metadataSource]),
      productFamily: field(input.productFamily ?? null, input.productFamily ? "hydrated" : "unknown", [metadataSource]),
      generatedAt: field(generatedAt, "manual", [sourceRef("Phase 3A builder input", "generatedAt", "generatedAt", "manual", undefined, "manual")]),
      previewOnly: field(true, "not_applicable", [sourceRef("Phase 3A builder", "productTruthDraftBuilder", "previewOnly", "not_applicable", "No persistence or downstream unlock.", "product_rule")]),
    },
    sourceSvg: {
      fileName: field(input.svgSource?.fileName ?? null, input.svgSource?.fileName ? "hydrated" : "blocked", svgRefs),
      sourceHash: field(input.svgSource?.sourceHash ?? null, input.svgSource?.sourceHash ? "hydrated" : "unknown", [sourceRef("SVG source", "svg_source", "source_hash", input.svgSource?.sourceHash ? "hydrated" : "unknown", undefined, "svg")]),
      analysisStatus: field(input.svgSource?.analysisStatus ?? null, input.svgSource?.analysisStatus ? "hydrated" : "unknown", [sourceRef("SVG Analyzer", "svg_analysis", "analysis_status", input.svgSource?.analysisStatus ? "hydrated" : "unknown", undefined, "analyzer")]),
    },
    geometry: {
      widthMm: field(numberOrNull(geometry.width_mm), numberOrNull(geometry.width_mm) == null ? "unknown" : "hydrated", geometryRefs),
      heightMm: field(numberOrNull(geometry.height_mm), numberOrNull(geometry.height_mm) == null ? "unknown" : "hydrated", geometryRefs),
      letterCount: field(numberOrNull(geometry.letter_count), numberOrNull(geometry.letter_count) == null ? "blocked" : "hydrated", geometryRefs),
      faceAreaM2: field(numberOrNull(geometry.face_area_m2), numberOrNull(geometry.face_area_m2) == null ? "blocked" : "hydrated", geometryRefs),
      returnMaterialPerimeterMl: field(numberOrNull(geometry.return_material_perimeter_ml), numberOrNull(geometry.return_material_perimeter_ml) == null ? "unknown" : "hydrated", geometryRefs),
      geometrySource: field(geometry.geometry_source ?? null, geometry.geometry_source ? "hydrated" : "unknown", geometryRefs),
      confirmed: field(geometry.confirmed === true, geometry.confirmed === true ? "confirmed" : "hydrated", geometryRefs),
    },
    layers,
    components: {
      face: {
        materialFamily: field(faceMaterialValue, faceMaterialState, faceDefaultRefs, faceMaterialState === "confirmed" ? [] : ["FACE_MATERIAL_FALLBACK_REQUIRES_CONFIRMATION"]),
        thicknessMm: field(faceThicknessValue, faceThicknessState, faceDefaultRefs, faceThicknessState === "confirmed" ? [] : ["FACE_THICKNESS_FALLBACK_REQUIRES_CONFIRMATION"]),
        groupRefs: field(faceGroupRefs, faceGroupRefs.length > 0 ? "suggested" : "blocked", layerRefs, faceGroupRefs.length > 0 ? [] : ["FACE_LAYER_NOT_FOUND"]),
      },
      back: {
        backingMode: field(backingMode, backingState, [setupRef("backing_mode", backingState)]),
        material: field("forex_10", backingState, [setupRef("backing_mode", backingState)]),
        bevelEnabled: field(backBevel, backBevelState, [setupRef("back_bevel_enabled", backBevelState)]),
      },
      returnCant: {
        depthMm: field(returnDepth, returnDepthState, [setupRef("return_depth_mm", returnDepthState)]),
        finishType: field(finish.return_finish_type ?? null, setupState(input, "return_finish_type", finish.return_finish_type == null), [setupRef("return_finish_type", setupState(input, "return_finish_type", finish.return_finish_type == null))]),
        colorCode: field(finish.return_oracal_code ?? null, finish.return_oracal_code ? setupState(input, "return_oracal_code") : "unknown", [setupRef("return_oracal_code", finish.return_oracal_code ? setupState(input, "return_oracal_code") : "unknown")]),
      },
      finish: {
        faceFinishType: field(faceFinishType, faceFinishState, [setupRef("face_finish_type", faceFinishState)]),
        oracalSeries: field(oracalSeries, oracalSeries ? faceFinishState : "not_applicable", [setupRef("face_finish_type", faceFinishState)]),
        oracalColor: field(null, "unknown", [setupRef("face_oracal_code", "unknown", "Global face Oracal color is currently per group or missing.")]),
        rollWidthMm: field(numberOrNull(finish.face_vinyl_roll_width_mm), numberOrNull(finish.face_vinyl_roll_width_mm) == null ? "unknown" : setupState(input, "face_vinyl_roll_width_mm"), [setupRef("face_vinyl_roll_width_mm", numberOrNull(finish.face_vinyl_roll_width_mm) == null ? "unknown" : setupState(input, "face_vinyl_roll_width_mm"))]),
        printRequired: field(printRequiredValues.length > 0 ? printRequiredValues.some(Boolean) : null, printRequiredValues.length > 0 ? "hydrated" : "unknown", [setupRef("artwork_finishes.execution_type", printRequiredValues.length > 0 ? "hydrated" : "unknown")]),
        laminationRequired: field(laminationRequiredValues.length > 0 ? laminationRequiredValues.some(Boolean) : null, laminationRequiredValues.length > 0 ? "hydrated" : "unknown", [setupRef("artwork_finishes.execution_type", laminationRequiredValues.length > 0 ? "hydrated" : "unknown")]),
        finishTarget: field(finishTarget, finishTarget ? setupState(input, "finish_target") : "blocked", finishTargetRefs, finishTarget ? [] : ["FINISH_TARGET_MISSING"]),
        groupFinishes,
      },
      artwork: {
        items: artworkItems,
        hasPrintedArtworkSuggestion: field(hasPrintedArtworkSuggestion, hasPrintedArtworkSuggestion ? "suggested" : "not_applicable", layerRefs),
      },
      lighting: {
        illuminated: field(finish.illuminated ?? null, setupState(input, "illuminated", finish.illuminated == null), [setupRef("illuminated", setupState(input, "illuminated", finish.illuminated == null))]),
        lightingSystemType: field(finish.lighting_system_type ?? null, setupState(input, "lighting_system_type", finish.lighting_system_type == null), [setupRef("lighting_system_type", setupState(input, "lighting_system_type", finish.lighting_system_type == null))]),
        lightColor: field(finish.light_color ?? null, setupState(input, "light_color", finish.light_color == null), [setupRef("light_color", setupState(input, "light_color", finish.light_color == null))]),
      },
      electrical: {
        ledModulePowerW: field(numberOrNull(finish.led_module_power_w), numberOrNull(finish.led_module_power_w) == null ? "unknown" : setupState(input, "led_module_power_w"), [setupRef("led_module_power_w", numberOrNull(finish.led_module_power_w) == null ? "unknown" : setupState(input, "led_module_power_w"))]),
        selectedPsuWatts: field(numberOrNull(finish.selected_psu_watts), numberOrNull(finish.selected_psu_watts) == null ? "unknown" : setupState(input, "selected_psu_watts"), [setupRef("selected_psu_watts", numberOrNull(finish.selected_psu_watts) == null ? "unknown" : setupState(input, "selected_psu_watts"))]),
        cableDefaults: field({ perLetterCableM: 1, finalFeedCableM: 5, perLetterCableType: "2x0.75", finalFeedCableType: "2x1.5" }, "fallback", [setupRef("electrical.cable_defaults", "fallback", "Owner-approved included commercial defaults; not site planning truth.")]),
        extraCableOrSiteDetails: field(finish.extra_cable_or_site_details ?? null, finish.extra_cable_or_site_details ? "manual" : "unknown", [setupRef("electrical.extra_cable_or_site_details", finish.extra_cable_or_site_details ? "manual" : "unknown", finish.extra_cable_quote_scope ? "Special commercial quote scope requested." : "Order/execution detail unless special commercial scope is requested.")], [], finish.extra_cable_or_site_details && !finish.extra_cable_quote_scope ? ["ELECTRICAL_SITE_DETAILS_ORDER_EXECUTION_ONLY"] : []),
        psuPlacement: field(finish.psu_placement ?? null, finish.psu_placement ? "manual" : "unknown", [setupRef("electrical.psu_placement", finish.psu_placement ? "manual" : "unknown", finish.psu_placement ? "Order/execution planning detail unless special quote scope is requested." : "Future order/execution field; not captured in current Review form.")], finish.psu_placement ? [] : ["PSU_PLACEMENT_MISSING"], finish.psu_placement && !finish.extra_cable_quote_scope ? ["PSU_PLACEMENT_ORDER_EXECUTION_ONLY"] : []),
      },
      support: {
        supportRequired: field(supportRequired, supportState, supportWarningRefs, [], supportState === "suggested" ? ["SUPPORT_MOUNTING_BRIDGE_NOT_CANONICAL"] : supportState === "unknown" ? ["SUPPORT_REQUIRED_UNKNOWN"] : []),
        supportType: field(supportType, supportType ? "suggested" : "unknown", supportWarningRefs),
        supportSource: field(supportSource, supportSource ? "suggested" : "unknown", supportWarningRefs),
        supportQuoteRelevant: field(finish.support_quote_relevant ?? null, finish.support_quote_relevant == null ? "unknown" : setupState(input, "support_quote_relevant"), supportWarningRefs),
      },
      mounting: {
        mountingScope: field(mountingScope, finish.mounting_scope ? setupState(input, "mounting_scope") : "blocked", [mountingScopeRef], finish.mounting_scope ? [] : ["MOUNTING_SCOPE_MISSING"]),
        mountingSystem: field(mountingSystem, mountingSystemState, [setupRef("mounting_system", mountingSystemState)]),
        mountingTemplateRequired: field(finish.mounting_template_enabled ?? null, setupState(input, "mounting_template_enabled", finish.mounting_template_enabled == null), [setupRef("mounting_template_enabled", setupState(input, "mounting_template_enabled", finish.mounting_template_enabled == null))]),
        mountingTemplateAreaM2: field(numberOrNull(finish.mounting_template_area_m2), numberOrNull(finish.mounting_template_area_m2) == null ? "unknown" : setupState(input, "mounting_template_area_m2"), [setupRef("mounting_template_area_m2", numberOrNull(finish.mounting_template_area_m2) == null ? "unknown" : setupState(input, "mounting_template_area_m2"))]),
        mountingSurface: field(null, "unknown", [setupRef("mounting_surface", "unknown", "Future site/order/execution field.")]),
      },
      pricingBoundary: {
        commercialPreviewStatus: field("preview_only", "not_applicable", [sourceRef("Commercial/pricing boundary", "Phase 3A", "pricing_boundary", "not_applicable", "Pricing follows Product Truth later and is not called here.", "product_rule")]),
      },
    },
    blockers,
    warnings,
    audit,
  };

  audit.push({
    code: "PRODUCT_TRUTH_DRAFT_BUILT_IN_MEMORY",
    message: "Pure Phase 3A builder created a canonical Product Truth draft without API calls, persistence, or downstream unlock.",
    sourceRefs: [sourceRef("Phase 3A builder", "productTruthDraftBuilder", "buildProductTruthDraft", "not_applicable", undefined, "product_rule")],
  });

  return {
    ...draftWithoutReadiness,
    readiness: evaluateProductTruthDraftReadiness(draftWithoutReadiness),
  };
}
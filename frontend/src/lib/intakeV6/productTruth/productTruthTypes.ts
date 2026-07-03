export type ProductTruthState =
  | "suggested"
  | "confirmed"
  | "fallback"
  | "hydrated"
  | "manual"
  | "blocked"
  | "warning"
  | "not_applicable"
  | "unknown";

export type ProductTruthSeverity = "blocker" | "warning" | "info";

export type ProductTruthSourceKind =
  | "analyzer"
  | "operator"
  | "owner_default"
  | "existing_form"
  | "fallback"
  | "hydrated"
  | "svg"
  | "product_rule"
  | "manual"
  | "unknown";

export type ProductTruthGate =
  | "review"
  | "internal_draft"
  | "commercial_proposal"
  | "quote_snapshot"
  | "order_snapshot"
  | "product_aggregate"
  | "execution_plan";

export interface ProductTruthSourceRef {
  sourceKind: ProductTruthSourceKind;
  sourceArea: string;
  sourcePath: string;
  fieldPath: string;
  state: ProductTruthState;
  note?: string;
}

export interface ProductTruthField<T> {
  value: T;
  state: ProductTruthState;
  sourceRefs: ProductTruthSourceRef[];
  blockers: string[];
  warnings: string[];
}

export interface ProductTruthIssue {
  code: string;
  severity: ProductTruthSeverity;
  component: ProductTruthComponentKey | "metadata" | "source_svg" | "layers" | "geometry" | "readiness";
  affectedComponent: ProductTruthComponentKey | "metadata" | "source_svg" | "layers" | "geometry" | "readiness";
  affectedField: string;
  source: ProductTruthSourceKind;
  quoteBlocker: boolean;
  orderBlocker: boolean;
  executionBlocker: boolean;
  gates: ProductTruthGate[];
  message: string;
  sourceRefs: ProductTruthSourceRef[];
}

export interface ProductTruthAuditEntry {
  code: string;
  message: string;
  sourceRefs: ProductTruthSourceRef[];
}

export interface ProductTruthMetadata {
  schemaVersion: "product_truth_draft_v1";
  workspaceId: ProductTruthField<string | null>;
  workspaceCode: ProductTruthField<string | null>;
  intakeId: ProductTruthField<string | null>;
  templateCode: ProductTruthField<string | null>;
  productFamily: ProductTruthField<string | null>;
  generatedAt: ProductTruthField<string>;
  previewOnly: ProductTruthField<true>;
}

export interface ProductTruthSvgSource {
  fileName: ProductTruthField<string | null>;
  sourceHash: ProductTruthField<string | null>;
  analysisStatus: ProductTruthField<string | null>;
}

export interface ProductTruthGeometry {
  widthMm: ProductTruthField<number | null>;
  heightMm: ProductTruthField<number | null>;
  letterCount: ProductTruthField<number | null>;
  faceAreaM2: ProductTruthField<number | null>;
  returnMaterialPerimeterMl: ProductTruthField<number | null>;
  geometrySource: ProductTruthField<string | null>;
  confirmed: ProductTruthField<boolean>;
}

export interface ProductTruthLayer {
  layerKey: string;
  layerName: string;
  autoRole: ProductTruthField<string | null>;
  confirmedRole: ProductTruthField<string | null>;
  confirmationState: ProductTruthField<"pending" | "confirmed" | "ignored">;
}

export interface ProductTruthGroupFinish {
  groupKey: string;
  layerName: string | null;
  faceFinishType: ProductTruthField<string | null>;
  faceOracalCode: ProductTruthField<string | null>;
  returnFinishType: ProductTruthField<string | null>;
  returnDepthMm: ProductTruthField<number | null>;
  faceVinylRollWidthMm: ProductTruthField<number | null>;
  confirmed: ProductTruthField<boolean>;
}

export interface ProductTruthArtworkItem {
  layerKey: string;
  layerName: string | null;
  artworkDecision: ProductTruthField<"printed" | "artwork_only" | "ignored" | "needs_decision" | null>;
  executionType: ProductTruthField<string | null>;
  printRequired: ProductTruthField<boolean | null>;
  laminationRequired: ProductTruthField<boolean | null>;
  materialCode: ProductTruthField<string | null>;
  estimatedAreaM2: ProductTruthField<number | null>;
  confirmed: ProductTruthField<boolean>;
}

export type ProductTruthComponentKey =
  | "face"
  | "back"
  | "return_cant"
  | "finish"
  | "artwork"
  | "lighting"
  | "electrical"
  | "support"
  | "mounting"
  | "pricing_boundary";

export interface ProductTruthComponents {
  face: {
    materialFamily: ProductTruthField<string>;
    thicknessMm: ProductTruthField<number>;
    groupRefs: ProductTruthField<string[]>;
  };
  back: {
    backingMode: ProductTruthField<string>;
    material: ProductTruthField<string>;
    bevelEnabled: ProductTruthField<boolean>;
  };
  returnCant: {
    depthMm: ProductTruthField<number | null>;
    finishType: ProductTruthField<string | null>;
    colorCode: ProductTruthField<string | null>;
  };
  finish: {
    faceFinishType: ProductTruthField<string | null>;
    oracalSeries: ProductTruthField<string | null>;
    oracalColor: ProductTruthField<string | null>;
    rollWidthMm: ProductTruthField<number | null>;
    printRequired: ProductTruthField<boolean | null>;
    laminationRequired: ProductTruthField<boolean | null>;
    finishTarget: ProductTruthField<"face" | "cant" | "artwork" | "back" | "all" | null>;
    groupFinishes: ProductTruthGroupFinish[];
  };
  artwork: {
    items: ProductTruthArtworkItem[];
    hasPrintedArtworkSuggestion: ProductTruthField<boolean>;
  };
  lighting: {
    illuminated: ProductTruthField<boolean | null>;
    lightingSystemType: ProductTruthField<string | null>;
    lightColor: ProductTruthField<string | null>;
  };
  electrical: {
    ledModulePowerW: ProductTruthField<number | null>;
    selectedPsuWatts: ProductTruthField<number | null>;
    cableDefaults: ProductTruthField<{
      perLetterCableM: number;
      finalFeedCableM: number;
      perLetterCableType: string;
      finalFeedCableType: string;
    }>;
    extraCableOrSiteDetails: ProductTruthField<string | null>;
    psuPlacement: ProductTruthField<string | null>;
  };
  support: {
    supportRequired: ProductTruthField<"yes" | "no" | "suggested" | "unknown">;
    supportType: ProductTruthField<string | null>;
    supportSource: ProductTruthField<string | null>;
    supportQuoteRelevant: ProductTruthField<boolean | null>;
  };
  mounting: {
    mountingScope: ProductTruthField<"no_mounting" | "mounting_included" | "mounting_external" | "to_be_decided">;
    mountingSystem: ProductTruthField<string | null>;
    mountingTemplateRequired: ProductTruthField<boolean | null>;
    mountingTemplateAreaM2: ProductTruthField<number | null>;
    mountingSurface: ProductTruthField<string | null>;
  };
  pricingBoundary: {
    commercialPreviewStatus: ProductTruthField<"not_product_truth" | "preview_only">;
  };
}

export interface ProductTruthReadinessFlag {
  ready: boolean;
  state: ProductTruthState;
  blockers: string[];
  warnings: string[];
  blockerIssues: ProductTruthIssue[];
  warningIssues: ProductTruthIssue[];
  notes: string[];
}

export interface ProductTruthReadiness {
  readyForReview: ProductTruthReadinessFlag;
  productTruthDraftComplete: ProductTruthReadinessFlag;
  readyForInternalDraft: ProductTruthReadinessFlag;
  readyForCommercialProposal: ProductTruthReadinessFlag;
  readyForQuoteSnapshot: ProductTruthReadinessFlag;
  readyForOrderSnapshot: ProductTruthReadinessFlag;
  readyForProductAggregate: ProductTruthReadinessFlag;
  readyForExecutionPlan: ProductTruthReadinessFlag;
}

export interface ProductTruthDraft {
  metadata: ProductTruthMetadata;
  sourceSvg: ProductTruthSvgSource;
  geometry: ProductTruthGeometry;
  layers: ProductTruthLayer[];
  components: ProductTruthComponents;
  readiness: ProductTruthReadiness;
  blockers: ProductTruthIssue[];
  warnings: ProductTruthIssue[];
  audit: ProductTruthAuditEntry[];
}

export interface ProductTruthLayerRoleInputLayer {
  layer_key?: string | null;
  layerKey?: string | null;
  layer_name?: string | null;
  layerName?: string | null;
  auto_role?: string | null;
  autoRole?: string | null;
  confirmed_role?: string | null;
  confirmedRole?: string | null;
  confirmation_state?: "pending" | "confirmed" | "ignored" | null;
  confirmationState?: "pending" | "confirmed" | "ignored" | null;
  operator_decision?: "printed" | "artwork_only" | "ignored" | null;
  operatorDecision?: "printed" | "artwork_only" | "ignored" | null;
}

export interface ProductTruthLayerRoleInput {
  confirmation_status?: "missing" | "partial" | "complete" | null;
  confirmationStatus?: "missing" | "partial" | "complete" | null;
  layers?: ProductTruthLayerRoleInputLayer[] | null;
  warnings?: string[] | null;
}

export interface ProductTruthFinishSetupInput {
  face_finish_type?: string | null;
  face_material_family?: string | null;
  face_material_confirmed?: boolean | null;
  face_thickness_mm?: number | null;
  face_thickness_confirmed?: boolean | null;
  face_vinyl_roll_width_mm?: number | null;
  finish_target?: "face" | "cant" | "artwork" | "back" | "all" | null;
  return_finish_type?: string | null;
  return_oracal_code?: string | null;
  return_oracal_name?: string | null;
  return_depth_mm?: number | null;
  illuminated?: boolean | null;
  lighting_system_type?: string | null;
  light_color?: string | null;
  led_module_power_w?: number | null;
  selected_psu_watts?: number | null;
  letter_group_finishes?: ProductTruthLetterGroupFinishInput[] | null;
  artwork_finishes?: ProductTruthArtworkFinishInput[] | null;
  backing_mode?: "none" | "forex_10_no_bevel" | "forex_10_with_bevel" | null;
  back_bevel_enabled?: boolean | null;
  mounting_template_enabled?: boolean | null;
  mounting_template_area_m2?: number | null;
  mounting_template_material_type?: "forex" | "paper" | null;
  mounting_system?: "direct_wall" | "steel_bars" | "aluminum_bars" | "acm_panel" | string | null;
  mounting_scope?: "no_mounting" | "mounting_included" | "mounting_external" | "to_be_decided" | null;
  mounting_bar_profile?: string | null;
  support_required?: "yes" | "no" | "suggested" | "unknown" | null;
  support_type?: string | null;
  support_source?: string | null;
  support_quote_relevant?: boolean | null;
  psu_placement?: string | null;
  extra_cable_or_site_details?: string | null;
  extra_cable_quote_scope?: boolean | null;
  confirmed?: boolean | null;
}

export interface ProductTruthLetterGroupFinishInput {
  group_key: string;
  layer_name?: string | null;
  face_finish_type?: string | null;
  face_oracal_code?: string | null;
  face_oracal_name?: string | null;
  return_finish_type?: string | null;
  return_oracal_code?: string | null;
  return_oracal_name?: string | null;
  return_depth_mm?: number | null;
  face_vinyl_roll_width_mm?: number | null;
  confirmed?: boolean | null;
}

export interface ProductTruthArtworkFinishInput {
  layer_key: string;
  layer_name?: string | null;
  artwork_decision?: "printed" | "artwork_only" | "ignored" | "needs_decision" | null;
  execution_type?: string | null;
  print_required?: boolean | null;
  lamination_required?: boolean | null;
  finish_target?: "face" | "cant" | "artwork" | "back" | "all" | null;
  material_code?: string | null;
  estimated_area_m2?: number | null;
  confirmed?: boolean | null;
}

export interface ProductTruthGeometryInput {
  width_mm?: number | null;
  height_mm?: number | null;
  letter_count?: number | null;
  face_area_m2?: number | null;
  return_material_perimeter_ml?: number | null;
  geometry_source?: string | null;
  confirmed?: boolean | null;
}

export interface ProductTruthDraftBuilderInput {
  workspaceId?: string | null;
  workspaceCode?: string | null;
  intakeId?: string | null;
  templateCode?: string | null;
  productFamily?: string | null;
  generatedAt?: string | null;
  svgSource?: {
    fileName?: string | null;
    sourceHash?: string | null;
    analysisStatus?: string | null;
  } | null;
  quoteGeometry?: ProductTruthGeometryInput | null;
  layerRoleSetup?: ProductTruthLayerRoleInput | null;
  finishSetup?: ProductTruthFinishSetupInput | null;
}
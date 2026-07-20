/**
 * Single AcmPanel UI read model — only translator from domain/payload to operator language.
 * Components must not invent Confirmat / Ready / Complete independently.
 */

import { resolveAcmPanelInstance, type AcmPanelInstanceSource } from "./resolveInstance";
import type {
  AcmFieldAuthority,
  AcmFieldClass,
  AcmLifecycleStatus,
  AcmPanelCapability,
  AcmPanelComponentInstance,
  ComponentRelation,
} from "./types";
import { ACM_PANEL_TEMPLATE_CODE } from "./types";

export type AcmOperatorTone = "ok" | "pending" | "blocker" | "muted" | "info";

export type AcmOperatorLabel =
  | "Detectat"
  | "Propus"
  | "Necesită confirmare"
  | "Confirmat de operator"
  | "Incomplet"
  | "Blocat"
  | "Neaplicabil"
  | "Propunere din catalog"
  | "Compoziție propusă"
  | "Confirmată de operator"
  | "Inconsistență stare";

export type AcmPanelIssueSeverity = "blocker" | "warning" | "observation";

export type AcmPanelIssue = {
  id: string;
  severity: AcmPanelIssueSeverity;
  sectionId:
    | "summary"
    | "geometry"
    | "construction"
    | "segments"
    | "material"
    | "structure"
    | "relations"
    | "technical";
  fieldTestId: string | null;
  message: string;
};

export type AcmCompositionHonesty = {
  productCompositionConfirmed: boolean;
  instanceCompositionStatus: AcmLifecycleStatus | null;
  hasAcmInRecommendation: boolean;
  /** Operator-facing product badge — never Confirmed when Acm instance unconfirmed. */
  productBadgeLabel: AcmOperatorLabel;
  productBadgeTone: AcmOperatorTone;
  showConfirmCta: boolean;
  inconsistency: boolean;
  inconsistencyMessage: string | null;
};

export type AcmPanelUiReadModel = {
  exists: boolean;
  instance: AcmPanelComponentInstance | null;
  source: AcmPanelInstanceSource;
  inconsistentProjection: boolean;
  inconsistencyNotes: string[];
  label: string;
  templateCode: string | null;
  dimensionsSummary: string | null;
  segmentCount: number;
  segmentedStatus: string | null;
  segmentedLabel: AcmOperatorLabel;
  role: { raw: AcmLifecycleStatus | null; label: AcmOperatorLabel; tone: AcmOperatorTone };
  association: { raw: AcmLifecycleStatus | null; label: AcmOperatorLabel; tone: AcmOperatorTone };
  technical: { raw: AcmLifecycleStatus | null; label: AcmOperatorLabel; tone: AcmOperatorTone };
  composition: { raw: AcmLifecycleStatus | null; label: AcmOperatorLabel; tone: AcmOperatorTone };
  primaryStatus: { label: AcmOperatorLabel; tone: AcmOperatorTone };
  activeCapabilities: AcmPanelCapability[];
  inactiveCapabilities: AcmPanelCapability[];
  unresolvedConfirmations: string[];
  issues: AcmPanelIssue[];
  compositionHonesty: AcmCompositionHonesty;
  geometryRelations: ComponentRelation[];
  mountingRelations: ComponentRelation[];
  criticalFieldsOperatorConfirmed: boolean;
  technicalReady: boolean;
  fieldAuthority: Record<string, AcmFieldAuthority>;
  fieldClass: Record<string, AcmFieldClass>;
};

const GEOMETRY_RELATION_TYPES = new Set([
  "positioned_on",
  "contained_by",
  "contains",
  "belongs_to_assembly",
]);

const MOUNTING_RELATION_TYPES = new Set(["mounts_on", "attached_to_structure"]);

const CRITICAL_FIELD_KEYS = [
  "panel_geometry",
  "fold_count",
  "l1_mm",
  "l2_mm",
  "acm_thickness_mm",
  "finished_depth_mm",
] as const;

function asRecord(value: unknown): Record<string, unknown> | null {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

export function lifecycleToOperator(
  status: AcmLifecycleStatus | string | null | undefined,
): { label: AcmOperatorLabel; tone: AcmOperatorTone } {
  const raw = String(status ?? "").toLowerCase();
  if (raw === "confirmed") {
    return { label: "Confirmat de operator", tone: "ok" };
  }
  if (raw === "proposed") {
    return { label: "Propus", tone: "pending" };
  }
  if (raw === "unconfirmed") {
    return { label: "Necesită confirmare", tone: "pending" };
  }
  if (raw === "unknown") {
    return { label: "Incomplet", tone: "muted" };
  }
  return { label: "Neaplicabil", tone: "muted" };
}

export function authorityToOperator(
  authority: AcmFieldAuthority | string | null | undefined,
): { label: AcmOperatorLabel; tone: AcmOperatorTone } {
  const raw = String(authority ?? "").toLowerCase();
  if (raw === "operator_confirmed") {
    return { label: "Confirmat de operator", tone: "ok" };
  }
  if (raw === "catalog_default") {
    return { label: "Propunere din catalog", tone: "pending" };
  }
  if (raw === "detected") {
    return { label: "Detectat", tone: "info" };
  }
  if (raw === "proposed") {
    return { label: "Propus", tone: "pending" };
  }
  return { label: "Neaplicabil", tone: "muted" };
}

function segmentedToOperator(status: string | null): { label: AcmOperatorLabel; tone: AcmOperatorTone } {
  const st = String(status ?? "").toUpperCase();
  if (st === "CONFIRMED") return { label: "Confirmat de operator", tone: "ok" };
  if (st === "PROPOSED") return { label: "Propus", tone: "pending" };
  if (st === "REJECTED") return { label: "Neaplicabil", tone: "muted" };
  if (st === "INACTIVE" || st === "SINGLE_PANEL" || !st) {
    return { label: "Neaplicabil", tone: "muted" };
  }
  return { label: "Incomplet", tone: "pending" };
}

function recommendationHasAcm(payload: Record<string, unknown> | null): boolean {
  const rec = asRecord(payload?.product_composition_recommendation);
  const items = Array.isArray(rec?.composition_items) ? rec.composition_items : [];
  return items.some((raw) => {
    const item = asRecord(raw);
    if (!item) return false;
    return (
      item.component_role === "support_panel" ||
      String(item.template_code ?? "") === ACM_PANEL_TEMPLATE_CODE
    );
  });
}

function buildCompositionHonesty(args: {
  payload: Record<string, unknown> | null;
  instance: AcmPanelComponentInstance | null;
  hasAcm: boolean;
}): AcmCompositionHonesty {
  const confirmedRaw = asRecord(args.payload?.product_composition_confirmed);
  const productCompositionConfirmed = confirmedRaw?.confirmed === true;
  const instanceCompositionStatus = args.instance?.composition_status ?? null;
  const hasAcmInRecommendation = args.hasAcm || Boolean(args.instance);

  let inconsistency = false;
  let inconsistencyMessage: string | null = null;

  if (
    productCompositionConfirmed &&
    hasAcmInRecommendation &&
    instanceCompositionStatus &&
    instanceCompositionStatus !== "confirmed"
  ) {
    inconsistency = true;
    inconsistencyMessage =
      "Compoziția produsului este marcată confirmată, dar panoul Alucobond nu are composition_status=confirmed pe instanță.";
  }

  if (!productCompositionConfirmed) {
    return {
      productCompositionConfirmed: false,
      instanceCompositionStatus,
      hasAcmInRecommendation,
      productBadgeLabel: "Compoziție propusă",
      productBadgeTone: "pending",
      showConfirmCta: true,
      inconsistency,
      inconsistencyMessage,
    };
  }

  if (inconsistency) {
    return {
      productCompositionConfirmed: true,
      instanceCompositionStatus,
      hasAcmInRecommendation,
      productBadgeLabel: "Inconsistență stare",
      productBadgeTone: "blocker",
      showConfirmCta: false,
      inconsistency,
      inconsistencyMessage,
    };
  }

  return {
    productCompositionConfirmed: true,
    instanceCompositionStatus,
    hasAcmInRecommendation,
    productBadgeLabel: "Confirmată de operator",
    productBadgeTone: "ok",
    showConfirmCta: false,
    inconsistency: false,
    inconsistencyMessage: null,
  };
}

function criticalConfirmed(instance: AcmPanelComponentInstance | null): boolean {
  if (!instance) return false;
  const auth = instance.configuration?.field_authority ?? {};
  return CRITICAL_FIELD_KEYS.every((key) => {
    if (key === "panel_geometry") {
      const a = auth.panel_geometry;
      return a === "operator_confirmed" || a === "detected";
    }
    if (key === "l2_mm" && instance.configuration.fold_count === 1) {
      return true;
    }
    return auth[key] === "operator_confirmed";
  });
}

function buildIssues(args: {
  instance: AcmPanelComponentInstance | null;
  segmentedStatus: string | null;
  compositionHonesty: AcmCompositionHonesty;
  criticalOk: boolean;
}): AcmPanelIssue[] {
  const issues: AcmPanelIssue[] = [];
  const { instance } = args;
  if (!instance) return issues;

  if (instance.association_status !== "confirmed") {
    issues.push({
      id: "assoc-unconfirmed",
      severity: "warning",
      sectionId: "summary",
      fieldTestId: "intake-v6-acm-summary-association",
      message: "Asocierea panoului este propusă — necesită confirmare operator.",
    });
  }

  const auth = instance.configuration.field_authority ?? {};
  for (const key of CRITICAL_FIELD_KEYS) {
    if (key === "l2_mm" && instance.configuration.fold_count === 1) continue;
    if (key === "panel_geometry" && (auth.panel_geometry === "detected" || auth.panel_geometry === "operator_confirmed")) {
      continue;
    }
    if (auth[key] === "catalog_default" || auth[key] === "proposed") {
      issues.push({
        id: `auth-${key}`,
        severity: "blocker",
        sectionId: "construction",
        fieldTestId: `intake-v6-acm-field-${key}`,
        message: `Câmp critic ${key}: ${authorityToOperator(auth[key]).label} — confirmă explicit.`,
      });
    }
  }

  const seg = String(args.segmentedStatus ?? "").toUpperCase();
  if (seg === "PROPOSED") {
    issues.push({
      id: "segmented-proposed",
      severity: "blocker",
      sectionId: "segments",
      fieldTestId: "intake-v6-segmented-background-panel",
      message: "Segmentarea multi-panou este propusă — confirmă sau respinge.",
    });
  }

  if (args.compositionHonesty.inconsistency && args.compositionHonesty.inconsistencyMessage) {
    issues.push({
      id: "composition-inconsistency",
      severity: "blocker",
      sectionId: "summary",
      fieldTestId: "intake-v6-product-composition-panel",
      message: args.compositionHonesty.inconsistencyMessage,
    });
  } else if (
    args.compositionHonesty.hasAcmInRecommendation &&
    !args.compositionHonesty.productCompositionConfirmed
  ) {
    issues.push({
      id: "composition-unconfirmed",
      severity: "warning",
      sectionId: "summary",
      fieldTestId: "intake-v6-confirm-product-composition",
      message: "Compoziția produsului necesită confirmare explicită (separat de configurația tehnică).",
    });
  }

  for (const rel of instance.relations ?? []) {
    if (MOUNTING_RELATION_TYPES.has(rel.relation_type) && rel.status !== "confirmed") {
      issues.push({
        id: `rel-${rel.relation_id}`,
        severity: "observation",
        sectionId: "relations",
        fieldTestId: `intake-v6-acm-relation-${rel.relation_id}`,
        message: `Relație montaj ${rel.relation_type}: ${lifecycleToOperator(rel.status).label}.`,
      });
    }
  }

  if (!args.criticalOk && instance.technical_configuration_status === "confirmed") {
    issues.push({
      id: "technical-vs-critical",
      severity: "blocker",
      sectionId: "construction",
      fieldTestId: "intake-v6-acm-confirm-technical",
      message: "Starea tehnică apare confirmată, dar câmpuri critice nu sunt confirmate de operator.",
    });
  }

  return issues;
}

export type BuildAcmPanelUiReadModelArgs = {
  finishSetup?: unknown;
  /** Full workspace payload (for composition recommendation / confirmed). */
  payload?: Record<string, unknown> | null;
};

export function buildAcmPanelUiReadModel(
  args: BuildAcmPanelUiReadModelArgs,
): AcmPanelUiReadModel {
  const payload = args.payload ?? null;
  const finish =
    args.finishSetup ??
    asRecord(payload)?.finish_setup ??
    null;

  const resolved = resolveAcmPanelInstance(finish);
  const instance = resolved.instance;
  const finishRec = asRecord(finish);
  const segmented = asRecord(finishRec?.segmented_background);
  const segmentedStatus =
    typeof segmented?.status === "string" ? segmented.status : null;
  const segOp = segmentedToOperator(segmentedStatus);

  const hasAcm =
    Boolean(instance) ||
    recommendationHasAcm(payload) ||
    String(asRecord(finishRec?.mounting_solution)?.template_code ?? "") ===
      ACM_PANEL_TEMPLATE_CODE;

  const compositionHonesty = buildCompositionHonesty({
    payload,
    instance,
    hasAcm,
  });

  const role = lifecycleToOperator(instance?.role_status);
  const association = lifecycleToOperator(instance?.association_status);
  const technical = lifecycleToOperator(instance?.technical_configuration_status);
  const composition = lifecycleToOperator(instance?.composition_status);

  const criticalFieldsOperatorConfirmed = criticalConfirmed(instance);
  const technicalReady =
    criticalFieldsOperatorConfirmed &&
    instance?.technical_configuration_status === "confirmed" &&
    (String(segmentedStatus ?? "").toUpperCase() !== "PROPOSED");

  const issues = buildIssues({
    instance,
    segmentedStatus,
    compositionHonesty,
    criticalOk: criticalFieldsOperatorConfirmed,
  });

  const blockerCount = issues.filter((i) => i.severity === "blocker").length;
  let primaryStatus = association;
  if (!instance) {
    primaryStatus = { label: "Neaplicabil", tone: "muted" };
  } else if (blockerCount > 0) {
    primaryStatus = { label: "Blocat", tone: "blocker" };
  } else if (technicalReady && compositionHonesty.productBadgeTone === "ok") {
    primaryStatus = { label: "Confirmat de operator", tone: "ok" };
  } else if (instance.technical_configuration_status !== "confirmed") {
    primaryStatus = { label: "Necesită confirmare", tone: "pending" };
  }

  const w = instance?.geometry?.width_mm;
  const h = instance?.geometry?.height_mm;
  const dimensionsSummary =
    w != null && h != null ? `${Math.round(w)} × ${Math.round(h)} mm` : null;

  const panels = instance?.geometry?.panels ?? [];
  const segmentCount =
    panels.length > 0
      ? panels.length
      : Array.isArray(segmented?.panels)
        ? segmented.panels.length
        : 0;

  const unresolvedConfirmations: string[] = [];
  if (instance?.association_status === "proposed") {
    unresolvedConfirmations.push("Asociere panou");
  }
  if (!criticalFieldsOperatorConfirmed) {
    unresolvedConfirmations.push("Câmpuri critice construcție");
  }
  if (String(segmentedStatus ?? "").toUpperCase() === "PROPOSED") {
    unresolvedConfirmations.push("Segmentare multi-panou");
  }
  if (
    compositionHonesty.hasAcmInRecommendation &&
    !compositionHonesty.productCompositionConfirmed
  ) {
    unresolvedConfirmations.push("Compoziție produs");
  }

  const relations = instance?.relations ?? [];
  const geometryRelations = relations.filter((r) =>
    GEOMETRY_RELATION_TYPES.has(r.relation_type),
  );
  const mountingRelations = relations.filter((r) =>
    MOUNTING_RELATION_TYPES.has(r.relation_type),
  );

  return {
    exists: Boolean(instance),
    instance,
    source: resolved.source,
    inconsistentProjection: resolved.inconsistent,
    inconsistencyNotes: resolved.inconsistencyNotes,
    label: "Panou Alucobond casetat",
    templateCode: instance?.component_template_code ?? null,
    dimensionsSummary,
    segmentCount,
    segmentedStatus,
    segmentedLabel: segOp.label,
    role: { raw: instance?.role_status ?? null, ...role },
    association: { raw: instance?.association_status ?? null, ...association },
    technical: { raw: instance?.technical_configuration_status ?? null, ...technical },
    composition: { raw: instance?.composition_status ?? null, ...composition },
    primaryStatus,
    activeCapabilities: instance?.capabilities?.active ?? [],
    inactiveCapabilities: instance?.capabilities?.inactive ?? [],
    unresolvedConfirmations,
    issues,
    compositionHonesty,
    geometryRelations,
    mountingRelations,
    criticalFieldsOperatorConfirmed,
    technicalReady,
    fieldAuthority: instance?.configuration?.field_authority ?? {},
    fieldClass: instance?.configuration?.field_class ?? {},
  };
}

export function authorityHintForField(
  model: AcmPanelUiReadModel,
  fieldKey: string,
): { label: AcmOperatorLabel; tone: AcmOperatorTone } {
  return authorityToOperator(model.fieldAuthority[fieldKey]);
}

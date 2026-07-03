/**
 * Work Intake detail — action map / next-step guidance (UI only, no policy changes).
 */

import type { IntakeProductSpec } from "@/lib/intakeProductSpec";
import type { IntakeSiteAuditJson } from "@/lib/intakeSiteAudit";
import {
  evaluateIntakeReadyPrerequisites,
  type IntakeReadinessInput,
} from "@/lib/intakeReadiness";
import {
  filterReadinessMissingForDisplay,
  terrainProgressLabel,
} from "@/lib/intakeDeliverySemantics";
import {
  buildIntakeReadinessStages,
  type IntakeReadinessStageId,
  type StagedMissingGroup,
} from "@/lib/intakeReadinessStages";
import { isUnresolvedIntakeProductFamily } from "@/lib/intakeProductFamilyDisplay";
import type { IntakeStatus } from "@/lib/mockData";
import { TPL_VOLUMETRIC_LETTERS } from "@/lib/volumetricQuoteInput";

export type IntakeSectionAnchor =
  | "template"
  | "product-spec"
  | "terrain"
  | "ready-actions";

export const INTAKE_SECTION_IDS: Record<IntakeSectionAnchor, string> = {
  template: "intake-section-template",
  "product-spec": "intake-section-product-spec",
  terrain: "intake-section-terrain",
  "ready-actions": "intake-section-ready-actions",
};

export type PrimaryActionKind =
  | "confirm_template"
  | "complete_spec"
  | "mark_ready"
  | "open_preliminary_quote"
  | "complete_analysis"
  | "none";

export interface IntakeActionSummaryModel {
  templateLabel: string;
  templateOk: boolean;
  productSpecLabel: string;
  productSpecOk: boolean;
  terrainLabel: string;
  terrainOk: boolean | null;
  intakeStatusLabel: string;
  intakeReady: boolean;
  primaryAction: PrimaryActionKind;
  primaryActionLabel: string;
  primaryDisabled: boolean;
  primaryDisabledReason?: string;
  showPreliminaryQuote: boolean;
  readinessMissing: string[];
  /** Staged readiness — display only */
  readinessStage: IntakeReadinessStageId;
  readinessStageLabel: string;
  canSimulate: boolean;
  stagedMissingGroups: StagedMissingGroup[];
}

function hasStructuredVolumetricEnvelope(
  spec: IntakeProductSpec | null | undefined
): boolean {
  if (!spec) return false;
  const width = spec.width_mm;
  const height = spec.height_mm ?? spec.letter_height_mm;
  const depth = spec.depth_mm ?? spec.return_depth_mm;
  return (
    width != null &&
    width > 0 &&
    height != null &&
    height > 0 &&
    depth != null &&
    depth > 0
  );
}

export function buildIntakeActionSummary(input: {
  status: IntakeStatus;
  productFamily?: string | null;
  confirmedTemplateCode?: string | null;
  productSpec?: IntakeProductSpec | null;
  showVolumetricForm: boolean;
  readinessInput: IntakeReadinessInput;
  requiresInstallAudit: boolean;
}): IntakeActionSummaryModel {
  const confirmed = (input.confirmedTemplateCode ?? "").trim();
  const templateOk = confirmed.length > 0;
  const templateLabel = templateOk ? confirmed : "Neconfirmat";

  const specHasData =
    !!input.productSpec && Object.keys(input.productSpec).length > 0;
  const specEnvelopeOk = hasStructuredVolumetricEnvelope(input.productSpec);
  const productSpecOk = input.showVolumetricForm
    ? specHasData && specEnvelopeOk
    : specHasData;
  const productSpecLabel = productSpecOk
    ? "Completă"
    : specHasData
      ? "Incompletă"
      : "Nesalvată";

  const terrain = terrainProgressLabel(
    input.readinessInput.siteAudit,
    input.requiresInstallAudit
  );

  const readiness = evaluateIntakeReadyPrerequisites(input.readinessInput);
  const readinessMissing = filterReadinessMissingForDisplay(
    readiness.missing,
    input.requiresInstallAudit
  );
  const intakeReady = input.status === "ready_for_quote";

  const stages = buildIntakeReadinessStages({
    productFamily: input.productFamily,
    status: input.status,
    confirmedTemplateCode: input.confirmedTemplateCode,
    showVolumetricForm: input.showVolumetricForm,
    readinessInput: input.readinessInput,
    requiresInstallAudit: input.requiresInstallAudit,
  });

  const isStage0 = isUnresolvedIntakeProductFamily(input.productFamily);

  let primaryAction: PrimaryActionKind = "none";
  let primaryActionLabel = "—";
  let primaryDisabled = true;
  let primaryDisabledReason: string | undefined;

  const showPreliminaryQuote =
    input.showVolumetricForm &&
    (stages.canSimulate || intakeReady || templateOk);

  if (!templateOk) {
    primaryAction = "confirm_template";
    primaryActionLabel = "Confirmă template";
    primaryDisabled = false;
  } else if (input.showVolumetricForm && !productSpecOk) {
    primaryAction = "complete_spec";
    primaryActionLabel = "Completează specificația";
    primaryDisabled = false;
  } else if (!intakeReady && readiness.canMarkReady) {
    primaryAction = "mark_ready";
    primaryActionLabel = "Marchează Gata pt. Ofertă";
    primaryDisabled = false;
  } else if (!intakeReady && !readiness.canMarkReady) {
    if (input.status === "new") {
      primaryAction = "complete_analysis";
      primaryActionLabel = "Completează analiza";
      primaryDisabled = false;
    } else {
      primaryAction = "mark_ready";
      primaryActionLabel = "Marchează Gata pt. Ofertă";
      primaryDisabled = true;
      primaryDisabledReason =
        readinessMissing.length > 0
          ? readinessMissing.join("; ")
          : "Condiții neîndeplinite";
    }
  } else if (stages.canSimulate && showPreliminaryQuote && !intakeReady) {
    primaryAction = "open_preliminary_quote";
    primaryActionLabel = "Simulare preliminară";
    primaryDisabled = false;
  } else if (intakeReady && showPreliminaryQuote) {
    primaryAction = "open_preliminary_quote";
    primaryActionLabel = "Deschide ofertare preliminară";
    primaryDisabled = false;
  } else if (intakeReady) {
    primaryAction = "open_preliminary_quote";
    primaryActionLabel = "Mergi la Oferte";
    primaryDisabled = false;
  }

  const intakeStatusLabel = isStage0
    ? "Alege tip lucrare"
    : intakeReady
      ? "Gata pt. Ofertă (comercial)"
      : stages.stageLabel;

  return {
    templateLabel,
    templateOk,
    productSpecLabel,
    productSpecOk,
    terrainLabel: terrain.label,
    terrainOk: terrain.ok,
    intakeStatusLabel,
    intakeReady,
    primaryAction,
    primaryActionLabel,
    primaryDisabled,
    primaryDisabledReason,
    showPreliminaryQuote,
    readinessMissing,
    readinessStage: stages.workingStage,
    readinessStageLabel: stages.stageLabel,
    canSimulate: stages.canSimulate,
    stagedMissingGroups: stages.grouped,
  };
}

export function isVolumetricConfirmedTemplate(
  confirmedTemplateCode: string | null | undefined
): boolean {
  return (confirmedTemplateCode ?? "").trim() === TPL_VOLUMETRIC_LETTERS;
}

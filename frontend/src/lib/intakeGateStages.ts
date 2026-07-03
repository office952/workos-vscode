/**
 * Intake-to-quote gate stages (display/routing only — readiness policy unchanged).
 *
 * Stage 0 — Unresolved / no work type
 *   product_family empty, no confirmed template.
 *   Show client context + "Alege tip lucrare"; hide product/terrain/fiscal/quote gates.
 *
 * Stage 1 — Work type selected, template/form not complete
 *   product_family known or template selected; not ready for quote.
 *   Show relevant workspace, spec editor, conditional terrain if install delivery.
 *
 * Stage 2 — Quote estimate ready
 *   Enough quote-critical inputs exist; preliminary simulation allowed.
 *
 * Stage 3 — Commercial quote ready
 *   Final quote requirements met; commercial quote creation gate.
 */

import { requiresTerrainAudit } from "@/lib/intakeDeliverySemantics";
import { isUnresolvedIntakeProductFamily } from "@/lib/intakeProductFamilyDisplay";
import {
  evaluateIntakeReadyPrerequisites,
  type IntakeReadinessInput,
} from "@/lib/intakeReadiness";
import type { IntakeStatus } from "@/lib/mockData";

export type IntakeGateStage = 0 | 1 | 2 | 3;

export interface IntakeGateStageInput {
  productFamily: string | null | undefined;
  confirmedTemplateCode?: string | null;
  status: IntakeStatus;
  showVolumetricForm: boolean;
  readinessInput: IntakeReadinessInput;
}

export function isIntakeGateStage0(
  productFamily: string | null | undefined
): boolean {
  return isUnresolvedIntakeProductFamily(productFamily);
}

/** Terrain gates: Stage 1+ and delivery includes install. */
export function intakeTerrainGatesActive(
  productFamily: string | null | undefined,
  deliveryType: string | null | undefined
): boolean {
  return requiresTerrainAudit({ productFamily, deliveryType });
}

export function resolveIntakeGateStage(input: IntakeGateStageInput): IntakeGateStage {
  if (isIntakeGateStage0(input.productFamily)) {
    return 0;
  }

  const readiness = evaluateIntakeReadyPrerequisites(input.readinessInput);
  const intakeReady = input.status === "ready_for_quote";

  if (intakeReady) {
    return input.showVolumetricForm ? 2 : 3;
  }

  if (readiness.canMarkReady) {
    return 2;
  }

  return 1;
}

export const STAGE0_WORK_TYPE_GUIDANCE =
  "Alege tipul lucrării pentru a deschide formularul și verificările relevante.";

export const STAGE0_SPEC_MESSAGE =
  "Alege tipul lucrării pentru a începe specificația.";

export { STAGE0_INSTALL_NEUTRAL_NOTE } from "@/lib/intakeDeliverySemantics";

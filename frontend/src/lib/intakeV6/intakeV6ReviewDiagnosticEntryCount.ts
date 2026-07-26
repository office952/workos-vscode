import { buildFormSystemBackboneAwarenessModel } from "./formSystemBackboneAwareness";
import type {
  IntakeV6ProductTruthPromotionPlannerResponse,
  IntakeV6RuntimeCaptureReadModelResponse,
} from "./intakeV6Api";
import type { FormSystemBackboneContract } from "./intakeV6ModularFormContractTypes";
import type { FormSystemRuntimeStateOverlayInput } from "./formSystemBackboneRuntimeStateOverlay";
import { asBlockerCodeList } from "./intakeV6OperatorBlockerBannerDisplay";

export const INTAKE_V6_REVIEW_DIAGNOSTIC_SECTION_TITLE = "Detalii tehnice și diagnostic";

export type ReviewDiagnosticEntryCountInput = {
  runtimeModel?: IntakeV6RuntimeCaptureReadModelResponse | null;
  plannerModel?: IntakeV6ProductTruthPromotionPlannerResponse | null;
  backbone?: FormSystemBackboneContract | null;
  runtimeState?: FormSystemRuntimeStateOverlayInput | null;
};

function addCodes(target: Set<string>, codes: unknown): void {
  for (const code of asBlockerCodeList(codes)) {
    target.add(code);
  }
}

/** Display-only count of technical diagnostic entries (raw codes / blocked fields). */
export function buildReviewDiagnosticEntryCount(input: ReviewDiagnosticEntryCountInput): number {
  const codes = new Set<string>();

  for (const field of input.runtimeModel?.fields ?? []) {
    addCodes(codes, field.blockers);
  }
  for (const row of input.runtimeModel?.blockers ?? []) {
    addCodes(codes, row.blockers);
  }
  for (const row of input.plannerModel?.blockers ?? []) {
    addCodes(codes, row.blockers);
  }
  for (const entry of input.plannerModel?.blocked_entries ?? []) {
    addCodes(codes, entry.blockers);
  }

  const backboneModel = buildFormSystemBackboneAwarenessModel(
    input.backbone ?? null,
    input.runtimeState ?? null,
  );
  for (const row of backboneModel.blockerRows) {
    if (row.blockerCode.trim()) codes.add(row.blockerCode.trim());
  }

  if (codes.size > 0) return codes.size;

  const runtimeFields = input.runtimeModel?.fields.length ?? 0;
  const plannerEntries =
    (input.plannerModel?.blocked_entries.length ?? 0) +
    (input.plannerModel?.blockers.length ?? 0);
  const backboneFields = backboneModel.available ? backboneModel.fields.length : 0;

  return runtimeFields + plannerEntries + backboneFields;
}

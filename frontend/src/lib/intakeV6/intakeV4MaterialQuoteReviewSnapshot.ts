import type { IntakeV4SheetQuoteMaterialCandidates } from "./intakeV4Api";
import type { IntakeV4SheetFootprintOverride } from "./intakeV4SheetFootprintOverride";
import {
  formatManualReviewReasons,
  resolveSheetQuoteReviewStatus,
  SHEET_QUOTE_REVIEW_STATUS_LABELS,
} from "./intakeV4SheetQuoteReviewDisplay";
import { formatSqmDisplay } from "@/lib/intake-shared/materialReviewCopy";
import {
  computeOperatorSheetFootprintAreaSqm,
  readSheetFootprintOverrideHeightCm,
  readSheetFootprintOverrideWidthCm,
} from "./intakeV4SheetFootprintOverride";

export interface IntakeV4MaterialQuoteReviewSnapshot {
  intake_id: string;
  template: string;
  material_review: {
    selected_current: {
      source: string;
      area_sqm: number | null;
      is_applied_to_quote: boolean;
    };
    recommended_auto: {
      source: string;
      area_sqm: number | null;
      confidence: string;
    };
    operator_override: {
      enabled: boolean;
      area_sqm: number | null;
      note: string | null;
      width_cm?: number | null;
      height_cm?: number | null;
    };
    manual_review: {
      required: boolean;
      reasons: string[];
    };
  };
}

export function buildMaterialQuoteReviewSnapshot(input: {
  intakeId: string;
  template?: string | null;
  candidates: IntakeV4SheetQuoteMaterialCandidates;
  sheetQuoteOverride?: IntakeV4SheetFootprintOverride | null;
}): IntakeV4MaterialQuoteReviewSnapshot {
  const { intakeId, template, candidates, sheetQuoteOverride } = input;
  const overrideWidth = readSheetFootprintOverrideWidthCm(sheetQuoteOverride);
  const overrideHeight = readSheetFootprintOverrideHeightCm(sheetQuoteOverride);
  const overrideAreaFromPanel =
    overrideWidth != null && overrideHeight != null
      ? computeOperatorSheetFootprintAreaSqm(overrideWidth, overrideHeight)
      : null;
  const operatorOverride = candidates.operator_override;
  const overrideEnabled =
    sheetQuoteOverride?.enabled === true ||
    operatorOverride?.enabled === true ||
    overrideAreaFromPanel != null;
  const overrideArea =
    overrideAreaFromPanel ??
    sheetQuoteOverride?.areaSqm ??
    sheetQuoteOverride?.area_sqm ??
    operatorOverride?.area_sqm ??
    null;
  const overrideNote =
    sheetQuoteOverride?.reason?.trim() ||
    operatorOverride?.note?.trim() ||
    null;

  return {
    intake_id: intakeId,
    template: template ?? "TPL-VOLUMETRIC-LETTERS",
    material_review: {
      selected_current: {
        source:
          candidates.selection?.selected_source ??
          candidates.selected_quote_sheet_area_source ??
          "eligible_area_floor",
        area_sqm:
          candidates.selection?.final_area_sqm ??
          candidates.selected_quote_sheet_area_sqm ??
          null,
        is_applied_to_quote: candidates.selection?.is_applied_to_quote === true,
      },
      recommended_auto: {
        source: candidates.recommended_auto_candidate?.source ?? "child_part_bbox_sum_with_buffer",
        area_sqm: candidates.recommended_auto_candidate?.area_sqm ?? null,
        confidence: candidates.recommended_auto_candidate?.confidence ?? "low",
      },
      operator_override: {
        enabled: overrideEnabled,
        area_sqm: overrideArea,
        note: overrideNote,
        width_cm: overrideWidth ?? operatorOverride?.width_cm ?? null,
        height_cm: overrideHeight ?? operatorOverride?.height_cm ?? null,
      },
      manual_review: {
        required: candidates.requires_manual_review === true,
        reasons: formatManualReviewReasons(candidates.manual_review_reason),
      },
    },
  };
}

export function formatMaterialQuoteReviewSnapshotText(
  snapshot: IntakeV4MaterialQuoteReviewSnapshot,
  label?: string | null,
): string {
  const { material_review: review } = snapshot;
  const title = label?.trim() || snapshot.intake_id;
  const status = review.manual_review.required
    ? SHEET_QUOTE_REVIEW_STATUS_LABELS.review_required
    : SHEET_QUOTE_REVIEW_STATUS_LABELS.ok_auto;
  const lines = [
    `Material review — ${title}`,
    `Template: ${snapshot.template}`,
    `Status: ${status}`,
    `Selected current: ${formatSqmDisplay(review.selected_current.area_sqm)} (${review.selected_current.source})`,
    `Recommended auto: ${formatSqmDisplay(review.recommended_auto.area_sqm)} (${review.recommended_auto.confidence})`,
  ];
  if (review.operator_override.enabled) {
    const dims =
      review.operator_override.width_cm != null && review.operator_override.height_cm != null
        ? ` ${review.operator_override.width_cm} × ${review.operator_override.height_cm} cm`
        : "";
    lines.push(
      `Manual Corel:${dims} ${formatSqmDisplay(review.operator_override.area_sqm)}`,
    );
    if (review.operator_override.note) {
      lines.push(`Notă operator: ${review.operator_override.note}`);
    }
  } else {
    lines.push("Manual Corel: —");
  }
  lines.push(`Applied to quote: ${review.selected_current.is_applied_to_quote}`);
  if (review.manual_review.reasons.length > 0) {
    lines.push("Motive review:");
    for (const reason of review.manual_review.reasons) {
      lines.push(`- ${reason}`);
    }
  }
  return lines.join("\n");
}

export function formatMaterialQuoteReviewStatusLine(
  candidates: IntakeV4SheetQuoteMaterialCandidates,
): string {
  const status = resolveSheetQuoteReviewStatus(candidates);
  return SHEET_QUOTE_REVIEW_STATUS_LABELS[status];
}

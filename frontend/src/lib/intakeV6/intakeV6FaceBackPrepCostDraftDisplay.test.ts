import { describe, expect, it } from "vitest";

import type { IntakeV6FaceBackPrepCostDraftResponse } from "@/lib/intakeV6/intakeV6Api";
import {
  FACE_BACK_PREP_CNC_UNAVAILABLE_LABEL,
  FACE_BACK_PREP_OPERATOR_STATUS_NEEDS_VERIFICATION,
  needsFaceBackPrepPerimeterVerification,
  resolveFaceBackPrepCncPerimeterM,
  resolveFaceBackPrepDisplayCncCost,
  resolveFaceBackPrepDisplayTotalInternal,
  resolveFaceBackPrepIgnoredRawCncCost,
  resolveFaceBackPrepOperatorStatusLabel,
} from "./intakeV6FaceBackPrepCostDraftDisplay";

function baseDraft(
  overrides: Partial<IntakeV6FaceBackPrepCostDraftResponse> = {},
): IntakeV6FaceBackPrepCostDraftResponse {
  return {
    workspace_id: "ws-1",
    template_key: "TPL-VOLUMETRIC-FACE-BACK-PREP",
    version: "v1-cnc-only",
    preview_only: true,
    currency: "EUR",
    materials: [],
    operations: [
      {
        operation_key: "cnc_cut_face_plexi",
        label: "Debitare CNC față",
        component: "FACE_PLEXI",
        task_key: "CUT_FACE_PLEXI",
        quantity: 26.747,
        unit: "ml",
        unit_price: 1.5,
        pass_count: 1,
        currency: "EUR",
        price_source: "fixed_rule",
        cost: 40.12,
        status: "calculated",
        perimeter_source: "cnc_cutting_perimeter_ml",
        perimeter_confidence: "high",
        is_vector_perimeter_source: true,
      },
    ],
    task_drafts: [],
    totals: {
      material_cost: 43.2,
      operation_cost: 75.06,
      total_internal_cost: 118.26,
      currency: "EUR",
    },
    missing_prices: [],
    manual_inputs_required: [],
    warnings: [],
    creates_real_tasks: false,
    consumes_stock: false,
    creates_quote: false,
    cnc_rate_eur_per_ml: 1.5,
    ...overrides,
  };
}

describe("intakeV6FaceBackPrepCostDraftDisplay", () => {
  it("treats vector perimeter warning as verification required even with raw CNC cost", () => {
    const draft = baseDraft({
      totals: { material_cost: 43.2, operation_cost: 75.06, total_internal_cost: null, currency: "EUR" },
      operations: baseDraft().operations.map((row) => ({
        ...row,
        cost: null,
        status: "manual_required",
      })),
      warnings: [
        {
          code: "vector_perimeter_missing_or_low_confidence",
          message: "Perimetru vectorial CNC față lipsă",
          severity: "warning",
        },
      ],
    });

    expect(needsFaceBackPrepPerimeterVerification(draft)).toBe(true);
    expect(resolveFaceBackPrepOperatorStatusLabel(draft)).toBe(
      FACE_BACK_PREP_OPERATOR_STATUS_NEEDS_VERIFICATION,
    );
    expect(resolveFaceBackPrepDisplayCncCost(draft)).toBeNull();
    expect(resolveFaceBackPrepDisplayTotalInternal(draft)).toBeNull();
    expect(resolveFaceBackPrepIgnoredRawCncCost(draft)).toBeCloseTo(75.06);
    expect(resolveFaceBackPrepCncPerimeterM(draft)).toBeNull();
  });

  it("exposes CNC perimeter and costs when perimeter is valid", () => {
    const draft = baseDraft();
    expect(needsFaceBackPrepPerimeterVerification(draft)).toBe(false);
    expect(resolveFaceBackPrepCncPerimeterM(draft)).toBeCloseTo(26.747);
    expect(resolveFaceBackPrepDisplayCncCost(draft)).toBeCloseTo(75.06);
    expect(resolveFaceBackPrepDisplayTotalInternal(draft)).toBeCloseTo(118.26);
    expect(resolveFaceBackPrepIgnoredRawCncCost(draft)).toBeNull();
  });

  it("uses manual_required operations without warning as verification required", () => {
    const draft = baseDraft({
      operations: baseDraft().operations.map((row) => ({
        ...row,
        status: "manual_required" as const,
        cost: null,
      })),
      totals: { material_cost: 43.2, operation_cost: 75.06, total_internal_cost: null, currency: "EUR" },
    });
    expect(needsFaceBackPrepPerimeterVerification(draft)).toBe(true);
    expect(resolveFaceBackPrepDisplayCncCost(draft)).toBeNull();
    expect(FACE_BACK_PREP_CNC_UNAVAILABLE_LABEL).toContain("indisponibil");
  });
});
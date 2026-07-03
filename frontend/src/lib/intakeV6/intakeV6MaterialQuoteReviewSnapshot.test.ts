import { describe, expect, it } from "vitest";
import type { IntakeV6SheetQuoteMaterialCandidates } from "./intakeV6Api";
import {
	buildMaterialQuoteReviewSnapshot,
	formatMaterialQuoteReviewSnapshotText,
} from "./intakeV6MaterialQuoteReviewSnapshot";

function baseCandidates(
	overrides: Partial<IntakeV6SheetQuoteMaterialCandidates> = {},
): IntakeV6SheetQuoteMaterialCandidates {
	return {
		eligible_face_area_sqm: 1.2638,
		requires_manual_review: true,
		manual_review_reason: "stale_orphan_defs_split_placement",
		selected_quote_sheet_area_sqm: 1.2638,
		selected_quote_sheet_area_source: "eligible_area_floor",
		selection: {
			selected_source: "eligible_area_floor",
			final_area_sqm: 1.2638,
			is_applied_to_quote: false,
		},
		recommended_auto_candidate: {
			source: "child_part_bbox_sum_with_buffer",
			area_sqm: 1.2638,
			confidence: "low",
			buffer_percent: 5,
		},
		operator_override: {
			enabled: true,
			width_cm: 192.67,
			height_cm: 143.389,
			area_sqm: 2.7627,
			note: "Măsurat în Corel",
		},
		...overrides,
	} as IntakeV6SheetQuoteMaterialCandidates;
}

describe("intakeV6MaterialQuoteReviewSnapshot", () => {
	it("builds snapshot DTO with selected, recommended, override, manual review", () => {
		const snapshot = buildMaterialQuoteReviewSnapshot({
			intakeId: "2aeda68b-09e0-46af-ba1e-31b0a47482d7",
			template: "TPL-VOLUMETRIC-LETTERS",
			candidates: baseCandidates(),
		});
		expect(snapshot.intake_id).toBe("2aeda68b-09e0-46af-ba1e-31b0a47482d7");
		expect(snapshot.material_review.selected_current.area_sqm).toBe(1.2638);
		expect(snapshot.material_review.selected_current.is_applied_to_quote).toBe(false);
		expect(snapshot.material_review.recommended_auto.confidence).toBe("low");
		expect(snapshot.material_review.operator_override.enabled).toBe(true);
		expect(snapshot.material_review.operator_override.area_sqm).toBe(2.7627);
		expect(snapshot.material_review.manual_review.required).toBe(true);
	});

	it("formats human-readable export text", () => {
		const snapshot = buildMaterialQuoteReviewSnapshot({
			intakeId: "ws-ana",
			template: "TPL-VOLUMETRIC-LETTERS",
			candidates: baseCandidates(),
		});
		const text = formatMaterialQuoteReviewSnapshotText(snapshot, "Ana Maria");
		expect(text).toContain("Material review — Ana Maria");
		expect(text).toContain("Selected current: 1.2638 m²");
		expect(text).toContain("Recommended auto:");
		expect(text).toContain("Manual Corel:");
		expect(text).toContain("Applied to quote: false");
		expect(text).toContain("Măsurat în Corel");
	});
});
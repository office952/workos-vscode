import { describe, expect, it } from "vitest";
import type { IntakeV6SheetQuoteMaterialCandidates } from "./intakeV6Api";
import {
	formatActiveManualReviewReasons,
	formatManualReviewReasons,
	isFreshSvgSnapshotAfterReanalysis,
	isStaleSvgSnapshotReview,
	resolveSheetQuoteReviewStatus,
	SHEET_QUOTE_REVIEW_STATUS_LABELS,
} from "./intakeV6SheetQuoteReviewDisplay";

function baseCandidates(
	overrides: Partial<IntakeV6SheetQuoteMaterialCandidates> = {},
): IntakeV6SheetQuoteMaterialCandidates {
	return {
		eligible_face_area_sqm: 1.2638,
		placement_footprint_face_sqm: 1.1469,
		requires_manual_review: false,
		selected_quote_sheet_area_sqm: 1.2638,
		selected_quote_sheet_area_source: "eligible_area_floor",
		selection: {
			selected_source: "eligible_area_floor",
			final_area_sqm: 1.2638,
			is_applied_to_quote: false,
		},
		...overrides,
	} as IntakeV6SheetQuoteMaterialCandidates;
}

describe("intakeV6SheetQuoteReviewDisplay", () => {
	it("maps requires_manual_review to review_required status", () => {
		const status = resolveSheetQuoteReviewStatus(baseCandidates({ requires_manual_review: true }));
		expect(status).toBe("review_required");
		expect(SHEET_QUOTE_REVIEW_STATUS_LABELS[status]).toBe("Verificare operator obligatorie");
	});

	it("maps low confidence to review_recommended", () => {
		const status = resolveSheetQuoteReviewStatus(
			baseCandidates({
				recommended_auto_candidate: { area_sqm: 1.3, confidence: "low", buffer_percent: 5 },
			}),
		);
		expect(status).toBe("review_recommended");
	});

	it("humanizes manual review reason tokens", () => {
		const reasons = formatManualReviewReasons(
			"stale_orphan_defs_split_placement;pseudo_layer_or_unlayered_complexity",
		);
		expect(reasons.length).toBe(2);
		expect(reasons[0]).toContain("orphan defs");
		expect(reasons[1]).toContain("pseudo-layer");
	});

	it("detects stale svg snapshot review signals from orphan defs metric", () => {
		expect(
			isStaleSvgSnapshotReview(
				baseCandidates({
					orphan_defs_split_placement_sqm: 2.32,
					manual_review_reason: "stale_orphan_defs_split_placement",
				}),
			),
		).toBe(true);
		expect(isStaleSvgSnapshotReview(baseCandidates())).toBe(false);
	});

	it("filters stale orphan reasons after fresh reanalysis state", () => {
		const fresh = baseCandidates({
			orphan_defs_split_placement_sqm: null,
			requires_manual_review: true,
			manual_review_reason:
				"stale_orphan_defs_split_placement;orphan_defs_parts_in_analysis;pseudo_layer_or_unlayered_complexity",
		});
		expect(isFreshSvgSnapshotAfterReanalysis(fresh)).toBe(true);
		const reasons = formatActiveManualReviewReasons(fresh.manual_review_reason, fresh);
		expect(reasons).toHaveLength(1);
		expect(reasons[0]).toContain("pseudo-layer");
	});
});
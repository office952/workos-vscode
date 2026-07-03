import type {
	ArtworkComplexityAssessment,
	ArtworkComplexityReport,
	ArtworkRecommendedApplication,
} from "@/lib/svgAnalyzer/analyzer/artworkComplexityAssessment";
import type { IntakeV4ArtworkComplexityDecision as IntakeV6ArtworkComplexityDecision } from "@/lib/intakeV6/intakeV4Api";

export type { IntakeV6ArtworkComplexityDecision };

export const ARTWORK_APPLICATION_LABELS: Record<ArtworkRecommendedApplication, string> = {
	vinyl_cut: "Colantare decupată (Oracal / vinyl cut)",
	print_on_vinyl_laminated: "Imprimare pe autocolant + laminare",
	manual_review: "Review manual",
};

export function formatArtworkSourceType(
	value: ArtworkComplexityAssessment["source_element_type"],
): string {
	if (value === "image") return "Raster / imagine";
	if (value === "vector") return "Vector";
	if (value === "mixed") return "Mixt";
	return "—";
}

export function artworkComplexityFromReport(
	report: { artworkComplexity?: ArtworkComplexityReport } | null | undefined,
): ArtworkComplexityReport | null {
	return report?.artworkComplexity ?? null;
}

export function artworkComplexityDecisionsFromPayload(
	payload: Record<string, unknown> | undefined,
): IntakeV6ArtworkComplexityDecision[] {
	const raw = payload?.finish_setup;
	if (raw == null || typeof raw !== "object" || Array.isArray(raw)) return [];
	const setup = raw as Record<string, unknown>;
	const rows = setup.artwork_complexity_decisions;
	if (!Array.isArray(rows)) return [];
	return rows.filter(
		(row): row is IntakeV6ArtworkComplexityDecision =>
			row != null &&
			typeof row === "object" &&
			typeof (row as IntakeV6ArtworkComplexityDecision).artwork_id === "string",
	);
}

export function mergeArtworkComplexityDecisions(
	existing: IntakeV6ArtworkComplexityDecision[] | null | undefined,
	assessments: ArtworkComplexityAssessment[],
): IntakeV6ArtworkComplexityDecision[] {
	const byId = new Map((existing ?? []).map((row) => [row.artwork_id, row]));
	const merged: IntakeV6ArtworkComplexityDecision[] = [];
	for (const assessment of assessments) {
		const prior = byId.get(assessment.artwork_id);
		merged.push(
			prior ?? {
				artwork_id: assessment.artwork_id,
				operator_application: assessment.recommended_application,
				accepted_system_recommendation: false,
				override_manual_vinyl_cut: false,
			},
		);
	}
	return merged;
}

export function decisionForArtwork(
	artworkId: string,
	decisions: IntakeV6ArtworkComplexityDecision[],
): IntakeV6ArtworkComplexityDecision | undefined {
	return decisions.find((row) => row.artwork_id === artworkId);
}

import type { IntakeV4ArtworkFinish } from "./intakeV4ArtworkFinish";
import type { IntakeV4LetterGroupFinish } from "./intakeV4LetterGroups";
import { faceFinishNeedsColorPicker } from "./intakeV6FaceFinishOptions";
import { resolveIntakeV6ReturnFinishUiOption } from "./intakeV6ReturnFinishOptions";

/** True when required product fields are present — independent of legacy `confirmed` flags. */
export function isLetterGroupProductConfigured(group: IntakeV4LetterGroupFinish): boolean {
	if (faceFinishNeedsColorPicker(group.face_finish_type) && !group.face_oracal_code?.trim()) {
		return false;
	}
	const ui = resolveIntakeV6ReturnFinishUiOption(group.return_finish_type);
	if ((ui === "ral_paint" || ui === "oracal_wrapped") && !group.return_oracal_code?.trim()) {
		return false;
	}
	if (!group.return_finish_type?.trim()) return false;
	if (group.return_depth_mm == null || group.return_depth_mm <= 0) return false;
	return true;
}

/** True when artwork execution mode is decided — `confirmed=false` does not block. */
export function isArtworkFinishProductConfigured(row: IntakeV4ArtworkFinish): boolean {
	const execution = String(row.execution_type ?? "").trim();
	if (!execution || execution === "needs_decision") return false;
	return true;
}

export function countIncompleteLetterGroups(groups: readonly IntakeV4LetterGroupFinish[]): number {
	return groups.filter((group) => !isLetterGroupProductConfigured(group)).length;
}

export function countIncompleteArtworkFinishes(rows: readonly IntakeV4ArtworkFinish[]): number {
	return rows.filter((row) => !isArtworkFinishProductConfigured(row)).length;
}

export function countConfiguredArtworkFinishes(rows: readonly IntakeV4ArtworkFinish[]): number {
	return rows.filter((row) => isArtworkFinishProductConfigured(row)).length;
}

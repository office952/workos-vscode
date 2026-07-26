import { describe, expect, it } from "vitest";
import type { IntakeV4ArtworkFinish } from "./intakeV4ArtworkFinish";
import type { IntakeV4LetterGroupFinish } from "./intakeV4LetterGroups";
import {
	countConfiguredArtworkFinishes,
	countIncompleteArtworkFinishes,
	countIncompleteLetterGroups,
	isArtworkFinishProductConfigured,
	isLetterGroupProductConfigured,
} from "./intakeV6ProductFinishCompleteness";

const letterGroup = (overrides: Partial<IntakeV4LetterGroupFinish> = {}): IntakeV4LetterGroupFinish => ({
	group_key: "pseudo:maria",
	layer_name: "maria",
	face_finish_type: "oracal_651",
	face_oracal_code: "056",
	return_finish_type: "white_aluminum",
	return_depth_mm: 60,
	confirmed: false,
	...overrides,
});

const artworkRow = (overrides: Partial<IntakeV4ArtworkFinish> = {}): IntakeV4ArtworkFinish => ({
	layer_key: "logo-stanga",
	layer_name: "logo stanga",
	execution_type: "print_laminate",
	color_mode: "polychrome",
	print_transparency: "standard",
	confirmed: false,
	...overrides,
});

describe("intakeV6ProductFinishCompleteness", () => {
	it("treats valid letter group values as configured even when confirmed=false", () => {
		expect(isLetterGroupProductConfigured(letterGroup())).toBe(true);
		expect(countIncompleteLetterGroups([letterGroup()])).toBe(0);
	});

	it("flags missing cant depth as incomplete", () => {
		expect(isLetterGroupProductConfigured(letterGroup({ return_depth_mm: null }))).toBe(false);
	});

	it("treats print_laminate artwork as configured when confirmed=false", () => {
		expect(isArtworkFinishProductConfigured(artworkRow())).toBe(true);
		expect(countConfiguredArtworkFinishes([artworkRow()])).toBe(1);
		expect(countIncompleteArtworkFinishes([artworkRow()])).toBe(0);
	});

	it("flags needs_decision artwork as incomplete", () => {
		expect(isArtworkFinishProductConfigured(artworkRow({ execution_type: "needs_decision" }))).toBe(false);
	});
});

import { describe, expect, it } from "vitest";
import { ALL_COLOR_REGISTRY_ITEMS, filterColorRegistry } from "@/lib/colorRegistry/colorRegistry";
import {
	faceFinishNeedsV6ColorPicker,
	faceFinishRollWidthOptions,
	normalizeFaceVinylRollWidthMm,
	oracalColorPaletteSeriesForV6Face,
	oracalSeriesForV6Face,
	PRINT_LAMINATION_ROLL_WIDTHS_MM,
	PRINT_LAMINATION_SIDE_RETRACTION_MM,
	PRINT_LAMINATION_TOTAL_RETRACTION_MM,
} from "./intakeV6FaceFinishOptions";

describe("intakeV6FaceFinishOptions", () => {
	it("shows color picker for Oracal 641 and 651", () => {
		expect(faceFinishNeedsV6ColorPicker("oracal_641")).toBe(true);
		expect(faceFinishNeedsV6ColorPicker("oracal_651")).toBe(true);
	});

	it("uses the same color palette for Oracal 641 and 651", () => {
		expect(oracalColorPaletteSeriesForV6Face("oracal_641")).toBe("651");
		expect(oracalColorPaletteSeriesForV6Face("oracal_651")).toBe("651");

		const palette641 = filterColorRegistry(ALL_COLOR_REGISTRY_ITEMS, {
			system: "ORACAL",
			series: oracalColorPaletteSeriesForV6Face("oracal_641"),
			usageScope: "face_vinyl",
		});
		const palette651 = filterColorRegistry(ALL_COLOR_REGISTRY_ITEMS, {
			system: "ORACAL",
			series: oracalColorPaletteSeriesForV6Face("oracal_651"),
			usageScope: "face_vinyl",
		});
		expect(palette641.map((item) => item.code)).toEqual(palette651.map((item) => item.code));
	});

	it("preserves persisted series for pricing identity", () => {
		expect(oracalSeriesForV6Face("oracal_641")).toBe("641");
		expect(oracalSeriesForV6Face("oracal_651")).toBe("651");
	});

	it("defaults Oracal face vinyl roll width to 1000 mm", () => {
		expect(normalizeFaceVinylRollWidthMm("oracal_641", null)).toBe(1000);
		expect(normalizeFaceVinylRollWidthMm("oracal_651", undefined)).toBe(1000);
		expect(normalizeFaceVinylRollWidthMm("oracal_8500", null)).toBe(1000);
		expect(normalizeFaceVinylRollWidthMm("oracal_651", 1260)).toBe(1260);
		expect(normalizeFaceVinylRollWidthMm("oracal_651", 1050)).toBe(1000);
		expect(normalizeFaceVinylRollWidthMm("none", 1000)).toBeNull();
	});

	it("uses print and lamination roll widths with 20 mm side retractions", () => {
		expect(PRINT_LAMINATION_ROLL_WIDTHS_MM).toEqual([1050, 1320, 1500]);
		expect(PRINT_LAMINATION_SIDE_RETRACTION_MM).toBe(20);
		expect(PRINT_LAMINATION_TOTAL_RETRACTION_MM).toBe(40);
		expect(faceFinishRollWidthOptions("print_laminate").map((option) => option.value)).toEqual([
			1050,
			1320,
			1500,
		]);
		expect(normalizeFaceVinylRollWidthMm("print_laminate", null)).toBe(1050);
		expect(normalizeFaceVinylRollWidthMm("print_laminate", 1320)).toBe(1320);
		expect(normalizeFaceVinylRollWidthMm("print_laminate", 1000)).toBe(1050);
	});
});
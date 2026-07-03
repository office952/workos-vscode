import { describe, expect, it } from "vitest";
import { ALL_COLOR_REGISTRY_ITEMS, filterColorRegistry } from "@/lib/colorRegistry/colorRegistry";
import {
	faceFinishNeedsV6ColorPicker,
	normalizeFaceVinylRollWidthMm,
	oracalColorPaletteSeriesForV6Face,
	oracalSeriesForV6Face,
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
		expect(normalizeFaceVinylRollWidthMm("none", 1000)).toBeNull();
	});
});
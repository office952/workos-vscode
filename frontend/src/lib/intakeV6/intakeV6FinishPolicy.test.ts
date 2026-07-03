import { describe, expect, it } from "vitest";
import { faceFinishNeedsV6Vinyl } from "./intakeV6FaceFinishOptions";
import { shouldHideGlobalFinishSettings } from "./intakeV6ReturnCantBridge";

describe("intakeV6ReturnCantBridge", () => {
	it("hides global finish when per-layer groups exist", () => {
		expect(shouldHideGlobalFinishSettings({ letterGroupCount: 2, artworkCount: 0 })).toBe(true);
		expect(shouldHideGlobalFinishSettings({ letterGroupCount: 0, artworkCount: 1 })).toBe(true);
		expect(shouldHideGlobalFinishSettings({ letterGroupCount: 0, artworkCount: 0 })).toBe(false);
	});
});

describe("intakeV6FaceFinishOptions", () => {
	it("treats none as no vinyl consumption", () => {
		expect(faceFinishNeedsV6Vinyl("none")).toBe(false);
		expect(faceFinishNeedsV6Vinyl("oracal_651")).toBe(true);
	});
});
import { describe, expect, it } from "vitest";
import {
	formatIntakeV6EdgeCantPreviewSource,
	formatIntakeV6EdgeCantQuantity,
} from "./intakeV6EdgeCantDryRunDisplay";

describe("intakeV6EdgeCantDryRunDisplay", () => {
	it("formats edge cant quantity in m not ml", () => {
		expect(formatIntakeV6EdgeCantQuantity(13.62, "m")).toContain("13.62 m");
		expect(formatIntakeV6EdgeCantQuantity(13.62, "linear_meter")).toContain("13.62 m");
		expect(formatIntakeV6EdgeCantQuantity(13.62, "m")).not.toContain("ml");
	});

	it("formats preview source label", () => {
		expect(formatIntakeV6EdgeCantPreviewSource("shared_edge_cant_rules")).toBe(
			"shared_edge_cant_rules",
		);
	});
});
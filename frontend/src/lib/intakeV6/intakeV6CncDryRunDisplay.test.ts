import { describe, expect, it } from "vitest";

import {
	formatIntakeV6CncPreviewSource,
	formatIntakeV6CncPricingStatus,
	formatIntakeV6CncQuantity,
} from "./intakeV6CncDryRunDisplay";

describe("intakeV6CncDryRunDisplay", () => {
	it("formats ml quantity for operator display", () => {
		expect(formatIntakeV6CncQuantity(13.6211, "linear_meter")).toBe("13.62 m");
	});

	it("shows missing-rate label instead of zero cost wording", () => {
		expect(formatIntakeV6CncPricingStatus("missing_rate")).toContain("Preț operație neconfigurat");
		expect(formatIntakeV6CncPricingStatus("missing_rate")).not.toContain("0");
	});

	it("shows operation_rows debug source label", () => {
		expect(formatIntakeV6CncPreviewSource("operation_rows")).toBe("operation_rows (debug)");
	});
});
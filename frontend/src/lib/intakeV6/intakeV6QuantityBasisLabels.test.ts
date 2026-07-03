import { describe, expect, it } from "vitest";
import { formatIntakeV6QuantityBasisLabel } from "./intakeV6QuantityBasisLabels";

describe("formatIntakeV6QuantityBasisLabel", () => {
	it("maps perimeter_with_waste to operator cant/volum label", () => {
		expect(formatIntakeV6QuantityBasisLabel("perimeter_with_waste")).toBe(
			"Cant / volum pentru preț (+20% pierdere)",
		);
	});

	it("maps LED and PSU basis tokens", () => {
		expect(formatIntakeV6QuantityBasisLabel("led_modules_perimeter_pitch_estimate")).toBe(
			"Module LED — estimare după perimetru",
		);
		expect(formatIntakeV6QuantityBasisLabel("psu_configuration_quote_estimate")).toBe(
			"Sursă LED — estimare ofertă",
		);
	});

	it("does not return raw technical tokens for known nesting keys", () => {
		expect(formatIntakeV6QuantityBasisLabel("sheet_nesting_role_split_quote_estimate")).toBe(
			"Nesting placă — estimare ofertă",
		);
		expect(formatIntakeV6QuantityBasisLabel("unknown_custom_quote_estimate")).toBe(
			"Estimare ofertă",
		);
	});
});
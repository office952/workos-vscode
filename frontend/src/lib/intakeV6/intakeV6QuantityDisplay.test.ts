import { describe, expect, it } from "vitest";
import {
	formatIntakeV6PricingQuantity,
	formatIntakeV6Quantity,
} from "./intakeV6QuantityDisplay";

describe("intakeV6QuantityDisplay", () => {
	it("formats discrete units without decimals", () => {
		expect(formatIntakeV6Quantity(47, "buc")).toBe("47 buc");
		expect(formatIntakeV6Quantity(1, "buc")).toBe("1 buc");
	});

	it("keeps ml precision", () => {
		expect(formatIntakeV6Quantity(9.4, "ml")).toBe("9.40 m");
	});

	it("formats pricing quantity with waste label", () => {
		expect(formatIntakeV6PricingQuantity(15.47, 18.56, "ml", 20)).toBe(
			"18.56 m (+20% pierdere)",
		);
	});
});
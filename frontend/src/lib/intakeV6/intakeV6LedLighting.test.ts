import { describe, expect, it } from "vitest";

import {
	computeIntakeV6LedLoadWatts,
	computeIntakeV6LedModuleCount,
	INTAKE_V6_LED_PITCH_MM,
	normalizeIntakeV6LedModuleWattage,
	proposeIntakeV6PsuConfiguration,
} from "./intakeV6LedLighting";
import { syncIntakeV6FinishLighting } from "./intakeV6FinishLighting";

const PBL_LED_PERIMETER_M = 11.6139;

describe("intakeV6LedLighting", () => {
	it("counts modules at 250 mm pitch", () => {
		expect(computeIntakeV6LedModuleCount(PBL_LED_PERIMETER_M)).toBe(47);
		expect(INTAKE_V6_LED_PITCH_MM).toBe(250);
	});

	it("normalizes wattage options and legacy 0.72 W", () => {
		expect(normalizeIntakeV6LedModuleWattage(1.44)).toBe(1.44);
		expect(normalizeIntakeV6LedModuleWattage(0.72)).toBe(0.75);
		expect(normalizeIntakeV6LedModuleWattage(99)).toBe(0.75);
	});

	it("computes PBL load watts for each module wattage", () => {
		expect(
			computeIntakeV6LedLoadWatts({
				letterPerimeterM: PBL_LED_PERIMETER_M,
				modulePowerW: 1.44,
			}),
		).toBe(67.68);
		expect(
			computeIntakeV6LedLoadWatts({
				letterPerimeterM: PBL_LED_PERIMETER_M,
				modulePowerW: 1,
			}),
		).toBe(47);
		expect(
			computeIntakeV6LedLoadWatts({
				letterPerimeterM: PBL_LED_PERIMETER_M,
				modulePowerW: 0.75,
			}),
		).toBe(35.25);
	});

	it("proposes PSU with 30% reserve", () => {
		const at144 = proposeIntakeV6PsuConfiguration(67.68);
		expect(at144.requiredPsuWatts).toBe(87.98);
		expect(at144.psuConfiguration).toEqual([100]);

		const at100 = proposeIntakeV6PsuConfiguration(47);
		expect(at100.requiredPsuWatts).toBe(61.1);
		expect(at100.psuConfiguration).toEqual([100]);

		const at075 = proposeIntakeV6PsuConfiguration(35.25);
		expect(at075.requiredPsuWatts).toBe(45.83);
		expect(at075.psuConfiguration).toEqual([60]);
	});
});

describe("syncIntakeV6FinishLighting wattage selection", () => {
	it("recalculates preview when module wattage changes", () => {
		const base = syncIntakeV6FinishLighting(
			{
				illuminated: true,
				lighting_system_type: "led_modules",
				led_module_power_w: 1.44,
			},
			PBL_LED_PERIMETER_M,
		);
		expect(base.led_module_count).toBe(47);
		expect(base.estimated_led_watts).toBe(67.68);
		expect(base.required_psu_watts).toBe(87.98);

		const at100 = syncIntakeV6FinishLighting(
			{ ...base, led_module_power_w: 1, psu_configuration: [] },
			PBL_LED_PERIMETER_M,
		);
		expect(at100.estimated_led_watts).toBe(47);
		expect(at100.required_psu_watts).toBe(61.1);

		const at075 = syncIntakeV6FinishLighting(
			{ ...base, led_module_power_w: 0.75, psu_configuration: [] },
			PBL_LED_PERIMETER_M,
		);
		expect(at075.estimated_led_watts).toBe(35.25);
		expect(at075.required_psu_watts).toBe(45.83);
		expect(at075.psu_configuration).toEqual([60]);
	});

	it("defaults new previews to 0.75 W modules", () => {
		const synced = syncIntakeV6FinishLighting(
			{
				illuminated: true,
				lighting_system_type: "led_modules",
			},
			PBL_LED_PERIMETER_M,
		);
		expect(synced.led_module_power_w).toBe(0.75);
		expect(synced.estimated_led_watts).toBe(35.25);
		expect(synced.psu_configuration).toEqual([60]);
	});
});
import { describe, expect, it } from "vitest";
import {
	syncIntakeV6FinishLighting,
	syncIntakeV6FinishLightingForLayerState,
} from "./intakeV6FinishLighting";

describe("syncIntakeV6FinishLighting", () => {
	it("clears LED fields when illumination disabled", () => {
		const result = syncIntakeV6FinishLighting(
			{
				illuminated: false,
				estimated_led_watts: 100,
				required_psu_watts: 120,
				psu_configuration: [160],
				psu_allocation_status: "ok",
			},
			18,
		);
		expect(result.estimated_led_watts).toBeNull();
		expect(result.required_psu_watts).toBeNull();
		expect(result.psu_configuration).toEqual([]);
	});

	it("proposes PSU from letter perimeter", () => {
		const result = syncIntakeV6FinishLighting(
			{
				illuminated: true,
				lighting_system_type: "led_modules",
				led_module_power_w: 1.44,
			},
			11.6139,
		);
		expect(result.led_module_count).toBe(47);
		expect(result.estimated_led_watts).toBe(67.68);
		expect((result.required_psu_watts ?? 0) > 0).toBe(true);
		expect(result.psu_configuration?.length).toBeGreaterThan(0);
	});

	it("recalculates watts and PSU for emblem area_lit totals", () => {
		const result = syncIntakeV6FinishLighting(
			{
				illuminated: true,
				lighting_system_type: "led_modules",
				led_module_power_w: 1.44,
				emblem_lighting_mode: "area_lit",
				estimated_led_watts: 67.68,
				required_psu_watts: 87.98,
				psu_configuration: [100],
			},
			11.6299,
			{
				areaM2: 0.1976,
				boxes: [{ width_mm: 585.8, height_mm: 337.3, area_m2: 0.1976 }],
				depthMm: 60,
			},
		);
		expect(result.letter_led_module_count).toBe(47);
		expect(result.emblem_led_module_count).toBe(15);
		expect(result.total_led_module_count).toBe(62);
		expect(result.estimated_led_watts).toBe(89.28);
		expect(result.required_psu_watts).toBeCloseTo(116.06, 1);
		expect(result.estimated_led_watts).not.toBe(67.68);
	});

	it("keeps led strip as continuous length instead of module count", () => {
		const result = syncIntakeV6FinishLighting(
			{
				illuminated: true,
				lighting_system_type: "led_strip",
				led_strip_power_w_per_ml: 5,
				emblem_lighting_mode: "area_lit",
				led_module_count: 47,
			},
			10,
			{ areaM2: 0.2, depthMm: 60 },
		);
		expect(result.letter_led_module_count).toBeNull();
		expect(result.emblem_led_module_count).toBeNull();
		expect(result.led_module_count).toBeNull();
		expect(result.letter_led_strip_length_m).toBe(10);
		expect(result.emblem_led_strip_length_m).toBe(5);
		expect(result.total_led_strip_length_m).toBe(15);
		expect(result.estimated_led_watts).toBe(75);
	});

	it("keeps letter LED on perimeter while emblem modules follow emblem return depth", () => {
		const common = {
			finish: {
				illuminated: true,
				lighting_system_type: "led_modules",
				led_module_power_w: 1.44,
				emblem_lighting_mode: "area_lit" as const,
				return_depth_mm: 60,
			},
			letterPerimeterM: 10,
			emblemAreaM2: 1,
			artworkBoxes: [{ layer_key: "logo", width_mm: 1000, height_mm: 1000, area_m2: 1 }],
			letterGroups: [
				{
					group_key: "letters",
					layer_name: "Letters",
					face_finish_type: "none",
					return_finish_type: "white_aluminum",
					return_depth_mm: 60,
					confirmed: false,
				},
			],
		};

		const at60 = syncIntakeV6FinishLightingForLayerState({
			...common,
			artworkFinishes: [
				{
					layer_key: "logo",
					layer_name: "Logo",
					execution_type: "print_laminate",
					color_mode: "polychrome",
					return_finish_type: "white_aluminum",
					return_depth_mm: 60,
					confirmed: false,
				},
			],
		});
		const at80 = syncIntakeV6FinishLightingForLayerState({
			...common,
			artworkFinishes: [
				{
					layer_key: "logo",
					layer_name: "Logo",
					execution_type: "print_laminate",
					color_mode: "polychrome",
					return_finish_type: "white_aluminum",
					return_depth_mm: 80,
					confirmed: false,
				},
			],
		});
		const at100 = syncIntakeV6FinishLightingForLayerState({
			...common,
			artworkFinishes: [
				{
					layer_key: "logo",
					layer_name: "Logo",
					execution_type: "print_laminate",
					color_mode: "polychrome",
					return_finish_type: "white_aluminum",
					return_depth_mm: 100,
					confirmed: false,
				},
			],
		});

		expect(at60.letter_led_module_count).toBe(40);
		expect(at80.letter_led_module_count).toBe(40);
		expect(at100.letter_led_module_count).toBe(40);
		expect(at60.emblem_led_module_count).toBe(80);
		expect(at80.emblem_led_module_count).toBe(63);
		expect(at100.emblem_led_module_count).toBe(56);
		expect(at60.total_led_module_count).toBe(120);
		expect(at80.total_led_module_count).toBe(103);
		expect(at100.total_led_module_count).toBe(96);
	});
});
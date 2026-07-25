import { describe, expect, it } from "vitest";
import { buildIntakeV6LiveMaterialsUsedRows } from "./intakeV6LiveMaterialsUsedDisplay";
import type {
	IntakeV6CncOperationRow,
	IntakeV6MaterialBreakdownResponse,
	IntakeV6MaterialQuantityRow,
} from "./intakeV6Api";

function materialRow(
	partial: Partial<IntakeV6MaterialQuantityRow> & Pick<IntakeV6MaterialQuantityRow, "material_key" | "display_name">,
): IntakeV6MaterialQuantityRow {
	const quantity = partial.quantity ?? partial.base_quantity ?? 0;
	const quantityWithWaste = partial.quantity_with_waste ?? partial.priced_quantity ?? quantity;
	const unitPrice = partial.unit_price ?? null;
	const estimatedCost =
		partial.estimated_cost ?? (unitPrice != null ? unitPrice * (partial.priced_quantity ?? quantityWithWaste) : null);

	return {
		category: partial.category ?? "material",
		quantity,
		unit: partial.unit ?? "m2",
		quantity_source: partial.quantity_source ?? "test",
		quantity_quality: partial.quantity_quality ?? "calculated",
		quantity_with_waste: quantityWithWaste,
		currency: partial.currency ?? "EUR",
		material_cost: partial.material_cost ?? estimatedCost,
		estimated_cost: estimatedCost,
		price_source: partial.price_source ?? "test",
		warnings: [],
		...partial,
	};
}

function operationRow(
	partial: Partial<IntakeV6CncOperationRow> & Pick<IntakeV6CncOperationRow, "key" | "display_name">,
): IntakeV6CncOperationRow {
	return {
		operation_type: partial.operation_type ?? "cutting",
		quantity: partial.quantity ?? partial.operation_equivalent_quantity ?? 0,
		unit: partial.unit ?? "ml",
		operation_equivalent_quantity: partial.operation_equivalent_quantity ?? partial.quantity ?? 0,
		operation_equivalent_unit: partial.operation_equivalent_unit ?? partial.unit ?? "ml",
		pricing_status: partial.pricing_status ?? "test",
		...partial,
	};
}

function breakdown(args: {
	materialRows?: IntakeV6MaterialQuantityRow[];
	consumableRows?: IntakeV6MaterialQuantityRow[];
	operationRows?: IntakeV6CncOperationRow[];
	edgeCantOperationRows?: IntakeV6CncOperationRow[];
} = {}): IntakeV6MaterialBreakdownResponse {
	return {
		workspace_id: "ws-1",
		template_code: "TPL-VOLUMETRIC-LETTERS",
		breakdown_scope: "review",
		nesting_rows: [],
		material_rows: args.materialRows ?? [],
		consumable_rows: args.consumableRows ?? [],
		operation_rows: args.operationRows ?? [],
		edge_cant_operation_rows: args.edgeCantOperationRows ?? [],
		totals: {
			material_cost_total: 0,
			estimated_cost_total: 0,
			currency: "EUR",
			contains_estimates: false,
			contains_missing_prices: false,
		},
		warnings: [],
	};
}

describe("buildIntakeV6LiveMaterialsUsedRows", () => {
	it("returns no rows without a live breakdown", () => {
		expect(buildIntakeV6LiveMaterialsUsedRows({ breakdown: null })).toEqual([]);
	});

	it("groups shared plexiglas under one inventory identity even when letters and logo both consume it", () => {
		const rows = buildIntakeV6LiveMaterialsUsedRows({
			breakdown: breakdown({
				materialRows: [
					materialRow({
						material_key: "plexiglas_face",
						display_name: "plexiglas 3mm PMMA - opal",
						registry_code: "MAT-ACP-FATA-LITERE",
						base_quantity: 2,
						quantity: 2,
						priced_quantity: 2,
						quantity_with_waste: 2,
						unit_price: 16,
					}),
					materialRow({
						material_key: "artwork_logo_1_plexiglas_face",
						display_name: "Plexiglas față emblemă — Logo 1",
						registry_code: "MAT-ACP-FATA-LITERE",
						base_quantity: 0.5,
						quantity: 0.5,
						priced_quantity: 0.5,
						quantity_with_waste: 0.5,
						unit_price: 16,
					}),
				],
			}),
			letterGroups: [{ group_key: "letters", face_area_m2: 1.5 }],
			artworkFinishes: [{ layer_key: "logo", estimated_area_m2: 0.5 }],
		});

		expect(rows.find((item) => item.groupKey === "plexi")?.label).toBe("plexiglas 3mm PMMA - opal");
		expect(rows.find((item) => item.groupKey === "plexi")?.quantityText).toContain("2.500 m");
		expect(rows.find((item) => item.groupKey === "plexi")?.costText).toBe("40.00 EUR");
		expect(rows.find((item) => item.groupKey === "plexi")?.technicalDetails).toContain("Sursă: plexiglas 3mm PMMA - opal");
		expect(rows.find((item) => item.groupKey === "plexi")?.technicalDetails).toContain("Sursă: Plexiglas față emblemă — Logo 1");
	});

	it("keeps a single plexiglas row when emblem split data is unavailable", () => {
		const rows = buildIntakeV6LiveMaterialsUsedRows({
			breakdown: breakdown({
				materialRows: [
					materialRow({
						material_key: "plexiglas_face",
						display_name: "plexiglas 3mm PMMA - opal",
						base_quantity: 1.264,
						quantity: 1.264,
						priced_quantity: 2.5238,
						quantity_with_waste: 2.5238,
						unit_price: 16,
					}),
				],
			}),
		});

		expect(rows.find((item) => item.groupKey === "plexi")?.quantityText).toContain("2.524 m");
		expect(rows.find((item) => item.groupKey === "plexi")?.costText).toBe("40.38 EUR");
		expect(rows.find((item) => item.groupKey === "plexi")?.label).toBe("plexiglas 3mm PMMA - opal");
	});

	it("separates Oracal face vinyl series and cant vinyl with their own prices", () => {
		const rows = buildIntakeV6LiveMaterialsUsedRows({
			breakdown: breakdown({
				materialRows: [
					materialRow({
						material_key: "face_vinyl_651",
						display_name: "Vinil fata Oracal 651",
						base_quantity: 0.8369,
						quantity: 0.8369,
						unit_price: 9,
					}),
					materialRow({
						material_key: "face_vinyl_8500",
						display_name: "Vinil fata Oracal 8500",
						base_quantity: 0.7742,
						quantity: 0.7742,
						unit_price: 20,
					}),
					materialRow({
						material_key: "edge_cant_oracal_651",
						display_name: "Oracal 651 / cant volum",
						base_quantity: 0.4965,
						quantity: 0.4965,
						unit_price: 9,
					}),
				],
			}),
		});

		expect(rows.find((item) => item.groupKey === "oracal_651")?.label).toBe("Oracal 651");
		expect(rows.find((item) => item.groupKey === "oracal_651")?.costText).toBe("7.53 EUR");
		expect(rows.find((item) => item.groupKey === "oracal_8500")?.label).toBe("Oracal 8500");
		expect(rows.find((item) => item.groupKey === "oracal_8500")?.costText).toBe("15.48 EUR");
		expect(rows.find((item) => item.groupKey === "oracal_cant_651")?.label).toBe("Oracal 651 / cant volum");
		expect(rows.find((item) => item.groupKey === "oracal_cant_651")?.costText).toBe("4.47 EUR");
		expect(rows.some((item) => item.groupKey === "oracal")).toBe(false);
	});

	it("shows RAL paint spray as a separate cant material", () => {
		const rows = buildIntakeV6LiveMaterialsUsedRows({
			breakdown: breakdown({
				materialRows: [
					materialRow({
						material_key: "ral_paint_spray",
						display_name: "Vopsea RAL spray / cant volum",
						base_quantity: 1.08,
						quantity: 2,
						priced_quantity: 2,
						quantity_with_waste: 2,
						unit: "buc",
						unit_price: 10,
					}),
				],
			}),
		});

		expect(rows.find((item) => item.groupKey === "ral_paint_spray")?.label).toBe("Vopsea RAL spray / cant volum");
		expect(rows.find((item) => item.groupKey === "ral_paint_spray")?.quantityText).toBe("2 buc");
		expect(rows.find((item) => item.groupKey === "ral_paint_spray")?.costText).toBe("20.00 EUR");
	});

	it("shows print material, lamination, and print service as separate priced rows", () => {
		const rows = buildIntakeV6LiveMaterialsUsedRows({
			breakdown: breakdown({
				materialRows: [
					materialRow({
						material_key: "artwork_logo_print_vinyl",
						display_name: "Print fata - logo",
						base_quantity: 0.4,
						quantity: 0.48,
						priced_quantity: 0.48,
						unit_price: 1.5,
					}),
					materialRow({
						material_key: "artwork_logo_laminated_vinyl",
						display_name: "Laminare print - logo",
						base_quantity: 0.4,
						quantity: 0.48,
						priced_quantity: 0.48,
						unit_price: 5,
					}),
				],
				operationRows: [
					operationRow({
						key: "artwork_logo_print_service",
						display_name: "Serviciu print autocolant - logo",
						operation_type: "print_vinyl",
						quantity: 0.48,
						unit: "m2",
						operation_equivalent_quantity: 0.48,
						operation_equivalent_unit: "m2",
						estimated_cost: 4.08,
					}),
				],
			}),
		});

		expect(rows.find((item) => item.groupKey === "print_vinyl")?.quantityText).toContain("0.400 m");
		expect(rows.find((item) => item.groupKey === "print_vinyl")?.costText).toBe("0.72 EUR");
		expect(rows.find((item) => item.groupKey === "lamination_material")?.quantityText).toContain("0.400 m");
		expect(rows.find((item) => item.groupKey === "lamination_material")?.costText).toBe("2.40 EUR");
		expect(rows.find((item) => item.groupKey === "print_service")?.quantityText).toContain("0.480 m");
		expect(rows.find((item) => item.groupKey === "print_service")?.costText).toBe("4.08 EUR");
	});

	it("groups same cant resource identity across letters and logo while preserving technical sources", () => {
		const rows = buildIntakeV6LiveMaterialsUsedRows({
			breakdown: breakdown({
				materialRows: [
					materialRow({
						material_key: "return_material",
						display_name: "Cant / volum litere",
						base_quantity: 26.7472,
						quantity: 32.0966,
						priced_quantity: 32.0966,
						unit: "m",
						unit_price: 3,
					}),
					materialRow({
						material_key: "artwork_return_logo-stanga",
						display_name: "Cant / volum emblema - logo stanga",
						base_quantity: 2.4455,
						quantity: 2.9346,
						priced_quantity: 2.9346,
						unit: "m",
						unit_price: 3,
					}),
					materialRow({
						material_key: "artwork_return_logo-dreapta",
						display_name: "Cant / volum emblema - logo dreapta",
						base_quantity: 2.4455,
						quantity: 2.9346,
						priced_quantity: 2.9346,
						unit: "m",
						unit_price: 3,
					}),
				],
			}),
		});

		expect(rows.find((item) => item.groupKey === "cant_profile")?.label).toBe("Cant / volum");
		expect(rows.find((item) => item.groupKey === "cant_profile")?.quantityText).toBe("31.64 m");
		expect(rows.find((item) => item.groupKey === "cant_profile")?.costText).toBe("113.90 EUR");
		expect(rows.find((item) => item.groupKey === "cant_profile")?.technicalDetails).toContain("Sursă: Cant / volum litere");
		expect(rows.find((item) => item.groupKey === "cant_profile")?.technicalDetails).toContain("Sursă: Cant / volum emblema - logo stanga");
	});

	it("includes LED modules and mounting accessories as separate consumables", () => {
		const rows = buildIntakeV6LiveMaterialsUsedRows({
			breakdown: breakdown({
				consumableRows: [
					materialRow({
						category: "consumable",
						material_key: "led_modules",
						display_name: "Module LED (0.75 W / buc)",
						base_quantity: 145,
						quantity: 174,
						priced_quantity: 174,
						unit: "buc",
						unit_price: 0.5,
					}),
					materialRow({
						category: "consumable",
						material_key: "mounting_accessories_percent",
						display_name: "Accesorii montaj / conectori (5% cost confectie)",
						base_quantity: 1,
						quantity: 1,
						unit: "job",
						estimated_cost: 31.35,
					}),
				],
			}),
		});

		expect(rows.find((item) => item.groupKey === "led_modules")?.quantityText).toBe("145 buc");
		expect(rows.find((item) => item.groupKey === "led_modules")?.costText).toBe("87.00 EUR");
		expect(rows.find((item) => item.groupKey === "mounting_accessories_percent")?.costText).toBe("31.35 EUR");
	});

	it("uses backend estimated_cost instead of recalculating rounded unit prices in the UI", () => {
		const rows = buildIntakeV6LiveMaterialsUsedRows({
			breakdown: breakdown({
				consumableRows: [
					materialRow({
						category: "consumable",
						material_key: "adhesive_return_to_face",
						display_name: "Adeziv lipire cant pe fete litere",
						base_quantity: 63.276,
						quantity: 63.276,
						priced_quantity: 63.276,
						unit: "ml",
						unit_price: 0.0845,
						estimated_cost: 6.29,
					}),
				],
			}),
		});

		expect(rows.find((item) => item.groupKey === "adhesive_return_to_face")?.costText).toBe("6.29 EUR");
	});

	it("shows CNC and missing edge operation prices from operation rows", () => {
		const rows = buildIntakeV6LiveMaterialsUsedRows({
			breakdown: breakdown({
				operationRows: [
					operationRow({
						key: "cnc_face_cutting_plexiglas_3mm",
						display_name: "Debitare CNC față plexiglas 3mm PMMA - opal",
						quantity: 24.6488,
						operation_equivalent_quantity: 24.6488,
						operation_equivalent_unit: "ml-pass",
						estimated_cost: 36.97,
					}),
					operationRow({
						key: "cnc_backing_cutting_forex_10mm",
						display_name: "Debitare CNC spate Forex 10 mm",
						quantity: 24.6488,
						operation_equivalent_quantity: 123.244,
						operation_equivalent_unit: "ml-pass",
						estimated_cost: 184.87,
					}),
					operationRow({
						key: "cnc_backing_bevel_forex_10mm",
						display_name: "Sanfren CNC spate Forex 10 mm",
						quantity: 24.6488,
						operation_equivalent_quantity: 24.6488,
						operation_equivalent_unit: "ml-pass",
						estimated_cost: 36.97,
					}),
				],
				edgeCantOperationRows: [
					operationRow({
						key: "edge_cant_oracal_wrap",
						display_name: "Aplicare Oracal 651 pe cant / volum",
						operation_type: "vinyl_application",
						quantity: 31.6382,
						unit: "m",
						estimated_cost: null,
						pricing_status: "missing_rate",
					}),
					operationRow({
						key: "edge_cant_bond_to_face",
						display_name: "Lipire cant / volum pe fata litere",
						operation_type: "assembly",
						quantity: 31.6382,
						unit: "m",
						operation_equivalent_quantity: 31.6382,
						operation_equivalent_unit: "m",
						unit_price: 5,
						estimated_cost: 158.19,
						pricing_status: "owner_rate",
					}),
				],
			}),
		});

		expect(rows.find((item) => item.groupKey === "cnc_face")?.quantityText).toContain("24.65 ml-pass");
		expect(rows.find((item) => item.groupKey === "cnc_face")?.costText).toBe("36.97 EUR");
		expect(rows.find((item) => item.groupKey === "cnc_backing")?.quantityText).toContain("123.24 ml-pass");
		expect(rows.find((item) => item.groupKey === "cnc_backing")?.costText).toBe("184.87 EUR");
		expect(rows.find((item) => item.groupKey === "cnc_backing_bevel")?.costText).toBe("36.97 EUR");
		expect(rows.find((item) => item.groupKey === "edge_bond")?.label).toBe("Lipire cant / volum");
		expect(rows.find((item) => item.groupKey === "edge_bond")?.quantityText).toBe("31.64 m");
		expect(rows.find((item) => item.groupKey === "edge_bond")?.costText).toBe("158.19 EUR");
		expect(rows.find((item) => item.groupKey === "edge_oracal_application")?.costText).toBe("tarif lipsă");
	});

	it("does not include informational-only consumables", () => {
		const rows = buildIntakeV6LiveMaterialsUsedRows({
			breakdown: breakdown({
				consumableRows: [
					materialRow({
						category: "consumable",
						material_key: "led_total_watts",
						display_name: "Consum LED total",
						quantity: 108.75,
						unit: "W",
						price_source: "informational_only",
					}),
				],
			}),
		});

		expect(rows).toEqual([]);
	});
});
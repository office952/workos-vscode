import { describe, expect, it } from "vitest";
import {
	INTAKE_V6_STEP_ORDER,
	INTAKE_V6_VISIBLE_PROGRESS_STEPS,
	INTAKE_V6_VISIBLE_STEP_COUNT,
	intakeV6VisibleStepIndex,
	resolveIntakeV6VisibleProgressStep,
} from "./intakeV6OperatorProgressSteps";

describe("intakeV6OperatorProgressSteps", () => {
	it("exposes three visible steps including Confirmare", () => {
		expect(INTAKE_V6_VISIBLE_STEP_COUNT).toBe(3);
		expect(INTAKE_V6_VISIBLE_PROGRESS_STEPS.map((step) => step.label)).toEqual([
			"Straturi",
			"Configurare",
			"Confirmare",
		]);
	});

	it("maps internal confirm step to visible confirm index", () => {
		expect(resolveIntakeV6VisibleProgressStep("confirm")).toBe("confirm");
		expect(intakeV6VisibleStepIndex("confirm")).toBe(2);
	});

	it("preserves canonical step order through confirm", () => {
		expect(INTAKE_V6_STEP_ORDER).toEqual(["layers", "review", "confirm"]);
	});
});

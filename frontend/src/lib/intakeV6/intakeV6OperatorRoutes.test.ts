import { describe, expect, it } from "vitest";

import {
	buildIntakeV6OperatorBootstrapPath,
	buildIntakeV6OperatorPath,
	resolveIntakeV6OperatorBasePath,
} from "./intakeV6OperatorRoutes";

describe("intakeV6OperatorRoutes", () => {
	it("resolves standalone base for intake-v6-app paths", () => {
		expect(resolveIntakeV6OperatorBasePath("/intake-v6-app/operator")).toBe("/intake-v6-app");
		expect(resolveIntakeV6OperatorBasePath("/intake-v6-app/abc/operator")).toBe("/intake-v6-app");
	});

	it("resolves shell base for intake-v6 paths", () => {
		expect(resolveIntakeV6OperatorBasePath("/intake-v6/operator")).toBe("/intake-v6");
		expect(resolveIntakeV6OperatorBasePath("/intake-v6/abc/operator")).toBe("/intake-v6");
		expect(resolveIntakeV6OperatorBasePath("/somewhere-else")).toBe("/intake-v6");
	});

	it("builds operator path preserving standalone prefix", () => {
		expect(buildIntakeV6OperatorPath("ws-1", "/intake-v6-app/operator")).toBe(
			"/intake-v6-app/ws-1/operator",
		);
		expect(buildIntakeV6OperatorPath("ws-1", "/intake-v6/operator")).toBe(
			"/intake-v6/ws-1/operator",
		);
	});

	it("builds bootstrap path for each V6 shell", () => {
		expect(buildIntakeV6OperatorBootstrapPath("/intake-v6-app/operator")).toBe(
			"/intake-v6-app/operator",
		);
		expect(buildIntakeV6OperatorBootstrapPath("/intake-v6/operator")).toBe(
			"/intake-v6/operator",
		);
	});
});

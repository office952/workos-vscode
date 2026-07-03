import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import { analyzeSvgFileForIntakeV6Client } from "./intakeV6ClientSvgImport";

const fixtureDir = dirname(fileURLToPath(import.meta.url));

describe("analyzeSvgFileForIntakeV6Client", () => {
	it("rejects non-SVG files with explicit message", async () => {
		const txt = new File(["hello"], "notes.txt", { type: "text/plain" });
		const result = await analyzeSvgFileForIntakeV6Client(txt);
		expect(result.ok).toBe(false);
		if (result.ok === false) {
			expect(result.kind).toBe("not_svg");
			expect(result.message).toContain("notes.txt");
		}
	});

	it("accepts SVG with empty MIME when extension is .svg (Windows)", async () => {
		const source = readFileSync(join(fixtureDir, "../svgAnalyzer/fixtures/pbl-complex.svg"), "utf8");
		const file = new File([source], "pbl-complex.svg", { type: "" });
		const result = await analyzeSvgFileForIntakeV6Client(file);
		expect(result.ok).toBe(true);
		if (result.ok) {
			expect(result.report.layers.length).toBeGreaterThan(0);
			expect(result.previewSource).toContain("<svg");
		}
	});

	it("returns preview even when parse errors exist (nest2 parity)", async () => {
		const source =
			'<svg xmlns="http://www.w3.org/2000/svg"><rect width="10" height="10"/></svg>';
		const file = new File([source], "minimal.svg", { type: "image/svg+xml" });
		const result = await analyzeSvgFileForIntakeV6Client(file);
		expect(result.ok).toBe(true);
		if (result.ok) {
			expect(result.previewSource).toContain("<svg");
		}
	});
});

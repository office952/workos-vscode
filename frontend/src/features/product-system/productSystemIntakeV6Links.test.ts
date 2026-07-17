import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

describe("productSystemIntakeV6Links", () => {
  it("retargets Product System operator links to /intake-v6", () => {
    const generalTab = readFileSync(
      resolve(__dirname, "TemplateGeneralTabPanel.tsx"),
      "utf8",
    );
    const productSystemPage = readFileSync(
      resolve(__dirname, "../../pages/ProductSystem.tsx"),
      "utf8",
    );
    expect(generalTab).toMatch(/to="\/intake-v6"/);
    expect(generalTab).not.toMatch(/to="\/intake"/);
    expect(productSystemPage).toMatch(/to="\/intake-v6"/);
    // Allow comments / docs mentioning legacy /intake, but no operator Link target.
    expect(productSystemPage).not.toMatch(/to=["']\/intake["']/);
  });

  it("keeps Dossier CTA on the canonical blueprint-dossier route", () => {
    const detail = readFileSync(
      resolve(__dirname, "ProductSystemTemplateDetailPanel.tsx"),
      "utf8",
    );
    expect(detail).toMatch(/to="\/product-system\/blueprint-dossier"/);
    expect(detail).toMatch(/product-system-template-detail-dossier-cta/);
  });
});

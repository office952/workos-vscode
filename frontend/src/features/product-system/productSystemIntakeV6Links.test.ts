import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

describe("productSystemIntakeV6Links", () => {
  it("uses canonical /intake-v6/operator — no bare /intake-v6 Link targets", () => {
    const generalTab = readFileSync(
      resolve(__dirname, "TemplateGeneralTabPanel.tsx"),
      "utf8",
    );
    const productSystemPage = readFileSync(
      resolve(__dirname, "../../pages/ProductSystem.tsx"),
      "utf8",
    );
    const finishMounting = readFileSync(
      resolve(__dirname, "FinishMountingOwnershipPanel.tsx"),
      "utf8",
    );
    const channels = readFileSync(
      resolve(__dirname, "ProductSystemOfferCostChannels.tsx"),
      "utf8",
    );

    expect(generalTab).toMatch(/to="\/intake-v6\/operator"/);
    expect(generalTab).not.toMatch(/to="\/intake-v6"/);
    expect(productSystemPage).toMatch(/to="\/intake-v6\/operator"/);
    expect(productSystemPage).not.toMatch(/to=["']\/intake-v6["']/);
    expect(productSystemPage).not.toMatch(/to=["']\/intake["']/);
    expect(finishMounting).toMatch(/to="\/intake-v6\/operator"/);
    expect(finishMounting).not.toMatch(/to="\/intake-v6"/);
    expect(channels).toMatch(/INTAKE_V6_OPERATOR_PATH/);
    const vocab = readFileSync(
      resolve(__dirname, "productTemplateModulesVocabulary.ts"),
      "utf8",
    );
    expect(vocab).toMatch(/INTAKE_V6_OPERATOR_PATH = "\/intake-v6\/operator"/);
  });

  it("keeps Dossier CTA on the canonical blueprint-dossier route when present", () => {
    const detail = readFileSync(
      resolve(__dirname, "ProductSystemTemplateDetailPanel.tsx"),
      "utf8",
    );
    expect(detail).toMatch(/product-system-template-detail-dossier-cta/);
    expect(detail).toMatch(/product-system\/blueprint-dossier/);
  });
});

import { describe, expect, it } from "vitest";

import {
  filterActiveTemplatesForQuote,
  filterArchivedExperimentalTemplates,
  isActiveTemplateForQuote,
  isOwnerValidActiveTemplate,
  OWNER_VALID_ACTIVE_TEMPLATE_CODE,
} from "./activeTemplateScope";

describe("activeTemplateScope", () => {
  it("identifies the current owner-valid root offerable template", () => {
    expect(isOwnerValidActiveTemplate(OWNER_VALID_ACTIVE_TEMPLATE_CODE)).toBe(true);
    expect(isOwnerValidActiveTemplate("TPL-VOLUMETRIC-LOGO_v1")).toBe(false);
    expect(isOwnerValidActiveTemplate("TPL-VOLUM-ALUMINIU_v1")).toBe(false);
    expect(isOwnerValidActiveTemplate("TPL-METAL-PREMOUNT-STRUCTURE_v1")).toBe(false);
  });

  it("keeps only the current owner-valid root template active for quote scope", () => {
    const templates = [
      { template_code: OWNER_VALID_ACTIVE_TEMPLATE_CODE, active: true },
      { template_code: "TPL-METAL-PREMOUNT-STRUCTURE_v1", active: true },
      { template_code: "TPL-VOLUM-ALUMINIU_v1", active: true },
      { template_code: "TPL-VOLUMETRIC-LOGO_v1", active: true },
      { template_code: "TPL-LEGACY-EXPERIMENT", active: true },
    ];

    expect(filterActiveTemplatesForQuote(templates)).toEqual([
      { template_code: OWNER_VALID_ACTIVE_TEMPLATE_CODE, active: true },
    ]);
    expect(filterArchivedExperimentalTemplates(templates)).toEqual([
      { template_code: "TPL-METAL-PREMOUNT-STRUCTURE_v1", active: true },
      { template_code: "TPL-VOLUM-ALUMINIU_v1", active: true },
      { template_code: "TPL-VOLUMETRIC-LOGO_v1", active: true },
      { template_code: "TPL-LEGACY-EXPERIMENT", active: true },
    ]);
  });

  it("marks non-root templates as archived/experimental in the frontend guard", () => {
    expect(
      isActiveTemplateForQuote({
        template_code: "TPL-ACM-CASSETTED-PANEL",
        active: true,
      }),
    ).toBe(false);
  });
});

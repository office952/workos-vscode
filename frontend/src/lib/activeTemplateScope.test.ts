import { describe, expect, it } from "vitest";

import {
  filterActiveTemplatesForQuote,
  filterArchivedExperimentalTemplates,
  isActiveTemplateForQuote,
} from "./activeTemplateScope";

describe("activeTemplateScope", () => {
  it("keeps the modular volum aluminum template active for quote scope", () => {
    expect(
      isActiveTemplateForQuote({
        template_code: "TPL-VOLUM-ALUMINIU_v1",
        active: true,
      }),
    ).toBe(true);
  });

  it("does not classify the modular volum aluminum template as archived", () => {
    const templates = [
      { template_code: "TPL-VOLUM-ALUMINIU_v1", active: true },
      { template_code: "TPL-LEGACY-EXPERIMENT", active: true },
    ];

    expect(filterActiveTemplatesForQuote(templates)).toEqual([
      { template_code: "TPL-VOLUM-ALUMINIU_v1", active: true },
    ]);
    expect(filterArchivedExperimentalTemplates(templates)).toEqual([
      { template_code: "TPL-LEGACY-EXPERIMENT", active: true },
    ]);
  });
});import { describe, expect, it } from "vitest";
import {
  filterActiveTemplatesForQuote,
  filterArchivedExperimentalTemplates,
  isActiveTemplateForQuote,
  isOwnerValidActiveTemplate,
  OWNER_VALID_ACTIVE_TEMPLATE_CODE,
} from "./activeTemplateScope";

describe("activeTemplateScope", () => {
  it("identifies owner-valid active template", () => {
    expect(isOwnerValidActiveTemplate(OWNER_VALID_ACTIVE_TEMPLATE_CODE)).toBe(true);
    expect(isOwnerValidActiveTemplate("TPL-BANNER-STANDARD")).toBe(false);
  });

  it("filters active quote templates", () => {
    const rows = [
      { template_code: OWNER_VALID_ACTIVE_TEMPLATE_CODE, active: true },
      { template_code: "TPL-ACM-CASSETTED-PANEL", active: false },
      { template_code: "TPL-BANNER-STANDARD", active: true },
    ];
    const active = filterActiveTemplatesForQuote(rows);
    expect(active).toHaveLength(1);
    expect(active[0].template_code).toBe(OWNER_VALID_ACTIVE_TEMPLATE_CODE);
  });

  it("filters archived experimental templates", () => {
    const rows = [
      { template_code: OWNER_VALID_ACTIVE_TEMPLATE_CODE, active: true },
      { template_code: "TPL-ACM-CASSETTED-PANEL", active: false },
      { template_code: "TPL-BANNER-STANDARD", active: true },
    ];
    const archived = filterArchivedExperimentalTemplates(rows);
    expect(archived).toHaveLength(2);
    expect(isActiveTemplateForQuote(rows[0])).toBe(true);
    expect(isActiveTemplateForQuote(rows[1])).toBe(false);
  });
});

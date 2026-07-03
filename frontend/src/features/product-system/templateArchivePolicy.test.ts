import { describe, it, expect } from "vitest";
import { OWNER_VALID_ACTIVE_TEMPLATE_CODE } from "@/lib/activeTemplateScope";
import { getTemplateArchivePolicy } from "@/features/product-system/templateArchivePolicy";

describe("templateArchivePolicy", () => {
  it("blocks archiving the only active quote template", () => {
    const policy = getTemplateArchivePolicy(
      { template_code: OWNER_VALID_ACTIVE_TEMPLATE_CODE, active: true },
      1
    );
    expect(policy.canArchive).toBe(false);
    expect(policy.blockReason).toMatch(/ultimul șablon activ/i);
  });

  it("allows archive when multiple active quote templates exist", () => {
    const policy = getTemplateArchivePolicy(
      { template_code: OWNER_VALID_ACTIVE_TEMPLATE_CODE, active: true },
      2
    );
    expect(policy.canArchive).toBe(true);
  });

  it("treats inactive owner template as already archived", () => {
    const policy = getTemplateArchivePolicy(
      { template_code: OWNER_VALID_ACTIVE_TEMPLATE_CODE, active: false },
      1
    );
    expect(policy.isArchivedForQuote).toBe(true);
    expect(policy.canArchive).toBe(false);
  });
});

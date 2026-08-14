import { describe, expect, it } from "vitest";
import {
  WORKOS_BOUNDED_EXCEPTION_BODY_RO,
  WORKOS_REFERENCE_FREEZE_BODY_RO,
  WORKOS_REFERENCE_FREEZE_CODE,
  WORKOS_REFERENCE_FREEZE_STATUS,
} from "./workosReferenceFreezePresentation";

describe("workosReferenceFreezePresentation", () => {
  it("states the repo freeze without inventing an unfreeze", () => {
    expect(WORKOS_REFERENCE_FREEZE_STATUS).toBe("ON");
    expect(WORKOS_REFERENCE_FREEZE_CODE).toBe("CURRENT_WORKOS_FROZEN_AS_REFERENCE = ON");
    expect(WORKOS_REFERENCE_FREEZE_BODY_RO).toMatch(/referință înghețată/i);
    expect(WORKOS_REFERENCE_FREEZE_BODY_RO).toMatch(/valuri delimitate/i);
    expect(WORKOS_BOUNDED_EXCEPTION_BODY_RO).toMatch(
      /excepții delimitate, autorizate explicit de owner/i,
    );
    expect(WORKOS_BOUNDED_EXCEPTION_BODY_RO).toMatch(/nu reprezintă o dezghețare generală/i);
    expect(WORKOS_BOUNDED_EXCEPTION_BODY_RO).not.toMatch(/S1[–-]S[0-9]/);
  });
});

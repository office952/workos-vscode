import { describe, expect, it } from "vitest";

import {
  formatNeutralLogoInstanceId,
  isNeutralLogoInstanceId,
  isPositionalLogoIdentity,
  nextNeutralLogoInstanceId,
  stableLayerInstanceKey,
} from "./layerInstanceIdentity";

describe("layerInstanceIdentity", () => {
  it("detects positional logo identities", () => {
    expect(isPositionalLogoIdentity("logo-stanga")).toBe(true);
    expect(isPositionalLogoIdentity("logo-dreapta")).toBe(true);
    expect(isPositionalLogoIdentity("logo_instance_001")).toBe(false);
  });

  it("formats neutral sequential logo instance ids", () => {
    expect(formatNeutralLogoInstanceId(1)).toBe("logo_instance_001");
    expect(formatNeutralLogoInstanceId(2)).toBe("logo_instance_002");
    expect(isNeutralLogoInstanceId("logo_instance_002")).toBe(true);
  });

  it("allocates next neutral logo instance id", () => {
    expect(nextNeutralLogoInstanceId(["logo_instance_001"])).toBe("logo_instance_002");
  });

  it("prefers stable non-positional layer id over positional layer key", () => {
    expect(
      stableLayerInstanceKey({
        layerId: "logo_instance_001",
        layerKey: "logo-stanga",
        layerName: "Logo 1",
      }),
    ).toBe("logo_instance_001");
  });
});

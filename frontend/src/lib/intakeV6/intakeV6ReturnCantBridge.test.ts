import { describe, expect, it } from "vitest";

import { INTAKE_V6_DEFAULT_RETURN_FINISH_TYPE } from "./intakeV6ReturnFinishOptions";
import {
  artworkToReturnCant,
  letterGroupToReturnCant,
} from "./intakeV6ReturnCantBridge";

describe("intakeV6ReturnCantBridge", () => {
  it("defaults missing return finish to white_aluminum", () => {
    const cant = letterGroupToReturnCant({
      return_finish_type: undefined as unknown as string,
      return_depth_mm: 60,
      return_oracal_code: null,
      return_oracal_name: null,
    });
    expect(cant.finishType).toBe(INTAKE_V6_DEFAULT_RETURN_FINISH_TYPE);
  });

  it("preserves persisted oracal_wrapped on hydration", () => {
    const cant = letterGroupToReturnCant({
      return_finish_type: "oracal_wrapped",
      return_depth_mm: 60,
      return_oracal_code: "010",
      return_oracal_name: "White",
    });
    expect(cant.finishType).toBe("oracal_wrapped");
    expect(cant.materialCode).toBe("651");
    expect(cant.colorCode).toBe("010");
  });

  it("preserves mirror_silver legacy without resetting to white", () => {
    const cant = artworkToReturnCant({
      return_finish_type: "mirror_silver",
      return_depth_mm: 60,
      return_oracal_code: null,
      return_oracal_name: null,
    });
    expect(cant.finishType).toBe("mirror_silver");
  });
});
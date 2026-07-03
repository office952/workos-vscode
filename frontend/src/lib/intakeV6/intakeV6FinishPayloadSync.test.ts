import { describe, expect, it } from "vitest";

import {
  finishSetupIdentityKey,
  syncIntakeV6FinishPayloadFromLayerFinishes,
} from "./intakeV6FinishPayloadSync";

describe("syncIntakeV6FinishPayloadFromLayerFinishes", () => {
  it("syncs job-level finish from per-layer groups", () => {
    const synced = syncIntakeV6FinishPayloadFromLayerFinishes(
      {
        face_finish_type: "oracal_651",
        return_finish_type: "oracal_wrapped",
        return_depth_mm: 40,
        illuminated: true,
      },
      [
        {
          group_key: "g1",
          layer_name: "G1",
          face_finish_type: "none",
          return_finish_type: "standard_aluminum",
          return_depth_mm: 60,
          confirmed: false,
        },
      ],
      [],
    );
    expect(synced.face_finish_type).toBe("none");
    expect(synced.return_finish_type).toBe("standard_aluminum");
    expect(synced.return_depth_mm).toBe(60);
  });

  it("syncs default Oracal roll width from per-layer face finish", () => {
    const synced = syncIntakeV6FinishPayloadFromLayerFinishes(
      { face_finish_type: "none", illuminated: true },
      [
        {
          group_key: "g1",
          layer_name: "G1",
          face_finish_type: "oracal_651",
          return_finish_type: "standard_aluminum",
          confirmed: false,
        },
      ],
      [],
    );

    expect(synced.face_finish_type).toBe("oracal_651");
    expect(synced.face_vinyl_roll_width_mm).toBe(1000);
  });

  it("finishSetupIdentityKey changes when layer finish changes", () => {
    const base = finishSetupIdentityKey({
      form: { illuminated: true },
      letterGroups: [
        {
          group_key: "g1",
          layer_name: "G1",
          face_finish_type: "none",
          return_finish_type: "standard_aluminum",
          confirmed: false,
        },
      ],
      artworkFinishes: [],
    });
    const changed = finishSetupIdentityKey({
      form: { illuminated: true },
      letterGroups: [
        {
          group_key: "g1",
          layer_name: "G1",
          face_finish_type: "oracal_651",
          return_finish_type: "standard_aluminum",
          confirmed: false,
        },
      ],
      artworkFinishes: [],
    });
    expect(base).not.toBe(changed);
  });
});
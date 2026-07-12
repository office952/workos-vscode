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

  it("strips global backing when any layer owns backing_mode", () => {
    const synced = syncIntakeV6FinishPayloadFromLayerFinishes(
      {
        illuminated: true,
        backing_mode: "forex_10_no_bevel",
        back_bevel_enabled: false,
      },
      [
        {
          group_key: "g1",
          layer_name: "G1",
          face_finish_type: "oracal_651",
          return_finish_type: "standard_aluminum",
          backing_mode: "forex_10_with_bevel",
          confirmed: false,
        },
        {
          group_key: "g2",
          layer_name: "G2",
          face_finish_type: "oracal_651",
          return_finish_type: "standard_aluminum",
          confirmed: false,
        },
      ],
      [],
    );
    expect(synced.backing_mode).toBeUndefined();
    expect(synced.back_bevel_enabled).toBeUndefined();
    expect(synced.letter_group_finishes?.[0]?.backing_mode).toBe("forex_10_with_bevel");
    expect(synced.letter_group_finishes?.[1]?.backing_mode).toBe("forex_10_no_bevel");
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

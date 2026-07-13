import { describe, expect, it } from "vitest";

import {
  INTAKE_V6_PENDING_SAVE_BANNER,
  intakeV6PersistedReviewRefetchKey,
  isIntakeV6SelectorStatePendingSave,
  savedBackingModeFromPayload,
  savedEmblemLightingFromPayload,
  savedReturnFinishFromPayload,
} from "./intakeV6FinishHydration";

describe("intakeV6FinishHydration", () => {
  const payload = {
    finish_setup: {
      backing_mode: "forex_10_with_bevel",
      emblem_lighting_mode: "area_lit",
      return_finish_type: "white_aluminum",
      illuminated: true,
      lighting_system_type: "led_modules",
      light_color: "warm",
      led_module_power_w: 1.44,
      confirmed: true,
      letter_group_finishes: [
        {
          group_key: "g1",
          layer_name: "Grup A",
          face_finish_type: "oracal_651",
          return_finish_type: "white_aluminum",
          return_depth_mm: 60,
          confirmed: false,
        },
      ],
      artwork_finishes: [
        {
          layer_key: "logo",
          layer_name: "Logo",
          execution_type: "print_laminate",
          color_mode: "polychrome",
          print_transparency: "standard",
          return_finish_type: "white_aluminum",
          return_depth_mm: 60,
          confirmed: false,
        },
      ],
    },
  } as Record<string, unknown>;

  const letterGroups = [
    {
      group_key: "g1",
      layer_name: "Grup A",
      face_finish_type: "oracal_651",
      return_finish_type: "white_aluminum",
      return_depth_mm: 60,
      confirmed: false,
    },
  ];

  const artworkFinishes = [
    {
      layer_key: "logo",
      layer_name: "Logo",
      execution_type: "print_laminate",
      color_mode: "polychrome",
      print_transparency: "standard",
      return_finish_type: "white_aluminum",
      return_depth_mm: 60,
      confirmed: false,
    },
  ];

  it("reads saved selector values from payload", () => {
    expect(savedBackingModeFromPayload(payload)).toBe("forex_10_with_bevel");
    expect(savedEmblemLightingFromPayload(payload)).toBe("area_lit");
    expect(savedReturnFinishFromPayload(payload)).toBe("white_aluminum");
  });

  it("exposes pending save banner copy", () => {
    expect(INTAKE_V6_PENDING_SAVE_BANNER).toContain("automat");
  });

  it("detects pending save when form diverges from payload", () => {
    expect(
      isIntakeV6SelectorStatePendingSave(
        {
          backing_mode: "none",
          emblem_lighting_mode: "needs_decision",
          return_finish_type: "white_aluminum",
        },
        payload,
        letterGroups,
        artworkFinishes,
      ),
    ).toBe(true);
    expect(
      isIntakeV6SelectorStatePendingSave(
        {
          backing_mode: "forex_10_with_bevel",
          emblem_lighting_mode: "area_lit",
          return_finish_type: "white_aluminum",
          illuminated: true,
          lighting_system_type: "led_modules",
          light_color: "warm",
          led_module_power_w: 1.44,
          confirmed: true,
        },
        payload,
        letterGroups,
        artworkFinishes,
      ),
    ).toBe(false);
  });

  it("detects pending save when finish setup is not persisted yet", () => {
    expect(
      isIntakeV6SelectorStatePendingSave(
        {
          backing_mode: "none",
          emblem_lighting_mode: "needs_decision",
          return_finish_type: "white_aluminum",
        },
        {},
        letterGroups,
        artworkFinishes,
      ),
    ).toBe(true);
  });

  it("detects pending save for letter group cant changes", () => {
    expect(
      isIntakeV6SelectorStatePendingSave(
        {
          backing_mode: "forex_10_with_bevel",
          emblem_lighting_mode: "area_lit",
          return_finish_type: "white_aluminum",
        },
        payload,
        [
          {
            ...letterGroups[0]!,
            return_depth_mm: 80,
          },
        ],
        artworkFinishes,
      ),
    ).toBe(true);
  });

  it("detects pending save for artwork policromie transparency", () => {
    expect(
      isIntakeV6SelectorStatePendingSave(
        {
          backing_mode: "forex_10_with_bevel",
          emblem_lighting_mode: "area_lit",
          return_finish_type: "white_aluminum",
        },
        payload,
        letterGroups,
        [
          {
            ...artworkFinishes[0]!,
            print_transparency: "translucent",
          },
        ],
      ),
    ).toBe(true);
  });

  it("detects pending save when mounting scope diverges from payload", () => {
    expect(
      isIntakeV6SelectorStatePendingSave(
        {
          backing_mode: "forex_10_with_bevel",
          emblem_lighting_mode: "area_lit",
          return_finish_type: "white_aluminum",
          illuminated: true,
          lighting_system_type: "led_modules",
          light_color: "warm",
          led_module_power_w: 1.44,
          mounting_scope: "preparation_and_site_installation",
          confirmed: true,
        },
        payload,
        letterGroups,
        artworkFinishes,
      ),
    ).toBe(true);
  });

  it("keeps the legacy compat refetch key stable for non-ReviewStep callers", () => {
    expect(
      intakeV6PersistedReviewRefetchKey({
        workspaceUpdatedAt: "2026-06-24T12:00:00Z",
        footprintOverrideRevision: 2,
      }),
    ).toBe("2026-06-24T12:00:00Z:2");
  });
});
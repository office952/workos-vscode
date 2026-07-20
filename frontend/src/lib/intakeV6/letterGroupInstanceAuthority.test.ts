import { describe, expect, it } from "vitest";
import {
  attachLetterAuthorityToFinishBody,
  authorityRowsFromFinishSetup,
  mergeLetterGroupsPreservingAuthority,
  projectInstanceToLegacyFinish,
  readLetterGroupInstances,
  workspaceLightingFromFinish,
  type LetterGroupFinishWithAuthority,
} from "./letterGroupInstanceAuthority";
import type { IntakeV4LetterGroupFinish } from "./intakeV4LetterGroups";

function row(groupKey: string, overrides: Partial<LetterGroupFinishWithAuthority> = {}): LetterGroupFinishWithAuthority {
  return {
    group_key: groupKey,
    layer_name: groupKey,
    source_fill_color: "#111111",
    face_area_m2: 0.1,
    perimeter_m: 1,
    element_count: 2,
    face_finish_type: "oracal_651",
    face_oracal_code: "030",
    face_oracal_name: "Dark Red",
    return_finish_type: "oracal_651",
    return_depth_mm: 60,
    backing_mode: "closed_back",
    confirmed: false,
    ...overrides,
  };
}

describe("letterGroupInstanceAuthority", () => {
  it("hydrates legacy once with stable UUID on reload", () => {
    const finish = {
      illuminated: true,
      letter_led_module_count: 6,
      letter_group_finishes: [row("pseudo:a"), row("pseudo:b")],
    };
    const first = authorityRowsFromFinishSetup(finish);
    expect(first).toHaveLength(2);
    expect(first[0].instance_id).toBeTruthy();
    expect(first[0].lighting?.illuminated).toBe(true);
    expect(first[0].lighting?.led_module_count).toBeNull();
    expect(workspaceLightingFromFinish(finish).illuminated).toBe(true);

    const attached = attachLetterAuthorityToFinishBody({ ...finish }, first, {
      finish_setup: finish,
      svg_source: { file_hash: "hash1" },
    });
    const ids = attached.letter_group_instances.map((i) => i.instance_id);
    const again = authorityRowsFromFinishSetup(attached);
    expect(again.map((r) => r.instance_id)).toEqual(ids);
  });

  it("preserves UUID across reorder", () => {
    const prior = [
      row("pseudo:a", { instance_id: "11111111-1111-1111-1111-111111111111" }),
      row("pseudo:b", { instance_id: "22222222-2222-2222-2222-222222222222" }),
    ];
    const derived: IntakeV4LetterGroupFinish[] = [row("pseudo:b"), row("pseudo:a")];
    const merged = mergeLetterGroupsPreservingAuthority(derived, prior);
    expect(merged.find((r) => r.group_key === "pseudo:a")?.instance_id).toBe(prior[0].instance_id);
    expect(merged.find((r) => r.group_key === "pseudo:b")?.instance_id).toBe(prior[1].instance_id);
  });

  it("preserves confirmed finishes across fill drift and records internal drift", () => {
    const prior = [
      row("pseudo:a", {
        instance_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        confirmed: true,
        face_oracal_code: "030",
        source_fill_color: "#111111",
      }),
    ];
    const derived = [row("pseudo:a", { source_fill_color: "#abcdef", face_oracal_code: null })];
    const merged = mergeLetterGroupsPreservingAuthority(derived, prior);
    expect(merged[0].face_oracal_code).toBe("030");
    expect(merged[0].confirmed).toBe(true);
    expect(merged[0].instance_id).toBe(prior[0].instance_id);
    expect(merged[0].geometry_drift).toContain("source_fill_changed");
  });

  it("keeps confirmed orphan when group_key leaves analysis", () => {
    const prior = [
      row("pseudo:keep", { instance_id: "k", confirmed: true }),
      row("pseudo:gone", { instance_id: "g", confirmed: true }),
    ];
    const merged = mergeLetterGroupsPreservingAuthority([row("pseudo:keep")], prior);
    expect(merged.map((r) => r.group_key).sort()).toEqual(["pseudo:gone", "pseudo:keep"]);
    expect(merged.find((r) => r.group_key === "pseudo:gone")?.instance_id).toBe("g");
  });

  it("mints new UUID for actual new group_key", () => {
    const prior = [row("pseudo:a", { instance_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa" })];
    const merged = mergeLetterGroupsPreservingAuthority(
      [row("pseudo:a"), row("pseudo:new")],
      prior,
    );
    expect(merged.find((r) => r.group_key === "pseudo:a")?.instance_id).toBe(prior[0].instance_id);
    expect(merged.find((r) => r.group_key === "pseudo:new")?.instance_id).not.toBe(prior[0].instance_id);
  });

  it("projects legacy without authority-only fields", () => {
    const finish = {
      letter_group_finishes: [row("pseudo:a", { confirmed: true })],
    };
    const attached = attachLetterAuthorityToFinishBody({ illuminated: true }, authorityRowsFromFinishSetup(finish), {
      finish_setup: finish,
    });
    const legacy = attached.letter_group_finishes[0] as Record<string, unknown>;
    expect(legacy.group_key).toBe("pseudo:a");
    expect(legacy.instance_id).toBeUndefined();
    expect(legacy.lighting).toBeUndefined();
    expect(legacy.geometry_drift).toBeUndefined();
    expect(readLetterGroupInstances(attached)).toHaveLength(1);
  });

  it("instance lighting differs across groups; global only seeds hydrate", () => {
    const finish = {
      illuminated: true,
      letter_led_module_count: 10,
      letter_group_instances: [
        {
          schema: "volumetric_letter_group_instance_v1",
          instance_id: "a1",
          group_key: "pseudo:a",
          layer_name: "a",
          source_layer_ids: ["pseudo:a"],
          artwork_reference: { layer_key: "pseudo:a", source_svg_hash: null, binding_id: null },
          geometry: { face_area_m2: 0.1, perimeter_m: 1, element_count: 1, source_fill_color: null },
          construction: { return_depth_mm: 60 },
          materials: {
            face_finish_type: "oracal_651",
            face_oracal_code: null,
            face_oracal_name: null,
            face_vinyl_roll_width_mm: null,
            return_finish_type: "oracal_651",
            return_oracal_code: null,
            return_oracal_name: null,
            backing_mode: null,
          },
          finish: { face_finish_type: "oracal_651", return_finish_type: "oracal_651", backing_mode: null },
          lighting: {
            illuminated: true,
            lighting_system_type: "led_modules",
            light_color: null,
            led_module_count: 3,
            selected_psu_watts: null,
          },
          confirmed: true,
          provenance: { source: "instance", geometry_drift: null },
        },
        {
          schema: "volumetric_letter_group_instance_v1",
          instance_id: "b1",
          group_key: "pseudo:b",
          layer_name: "b",
          source_layer_ids: ["pseudo:b"],
          artwork_reference: { layer_key: "pseudo:b", source_svg_hash: null, binding_id: null },
          geometry: { face_area_m2: 0.1, perimeter_m: 1, element_count: 1, source_fill_color: null },
          construction: { return_depth_mm: 60 },
          materials: {
            face_finish_type: "oracal_651",
            face_oracal_code: null,
            face_oracal_name: null,
            face_vinyl_roll_width_mm: null,
            return_finish_type: "oracal_651",
            return_oracal_code: null,
            return_oracal_name: null,
            backing_mode: null,
          },
          finish: { face_finish_type: "oracal_651", return_finish_type: "oracal_651", backing_mode: null },
          lighting: {
            illuminated: false,
            lighting_system_type: null,
            light_color: null,
            led_module_count: null,
            selected_psu_watts: null,
          },
          confirmed: true,
          provenance: { source: "instance", geometry_drift: null },
        },
      ],
    };
    const rows = authorityRowsFromFinishSetup(finish);
    expect(rows[0].lighting?.led_module_count).toBe(3);
    expect(rows[1].lighting?.illuminated).toBe(false);
    expect(finish.letter_led_module_count).toBe(10);
    expect(workspaceLightingFromFinish(finish).illuminated).toBe(true);
  });

  it("placement defaults to acm_panel when acm instance present", () => {
    const rows = [row("pseudo:a", { instance_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa" })];
    const attached = attachLetterAuthorityToFinishBody(
      {
        acm_panel_instance: { component_instance_id: "acm-xyz" },
      },
      rows,
      {},
    );
    expect(attached.component_placements[0].target_kind).toBe("acm_panel");
    expect(attached.component_placements[0].target_instance_id).toBe("acm-xyz");
  });

  it("legacy projection strips instance_id from finishes", () => {
    const inst = attachLetterAuthorityToFinishBody({}, [row("pseudo:a", { instance_id: "id-1" })], {});
    const projected = projectInstanceToLegacyFinish(inst.letter_group_instances[0]);
    expect((projected as { instance_id?: string }).instance_id).toBeUndefined();
  });
});

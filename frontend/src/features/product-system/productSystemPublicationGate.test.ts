import { describe, expect, it } from "vitest";
import type { ProductTemplatePublicationState } from "@/api/productTemplatePublication";
import { resolvePublishUiGate } from "./productSystemPublicationGate";

function publication(
  overrides: Partial<ProductTemplatePublicationState> = {},
): ProductTemplatePublicationState {
  return {
    template_code: "TPL-VOLUMETRIC-LETTERS_v2",
    template_id: 1,
    db_active: true,
    publication_status: null,
    effective_status: "LEGACY_UNSPECIFIED",
    legacy_unspecified: true,
    offerability_gate: "legacy_unspecified_keeps_prior_policy",
    publish_allowed: true,
    publish_blockers: [],
    allowed_actions: ["enter_draft", "publish"],
    active_is_not_published: true,
    contract_version: "product_template_publication_v1",
    ...overrides,
  };
}

describe("resolvePublishUiGate", () => {
  it("fail-closes when publication GET allows publish but readiness is BLOCKED (VL)", () => {
    const gate = resolvePublishUiGate(publication({ publish_allowed: true, publish_blockers: [] }), {
      verdict: "BLOCKED",
      e2eReady: false,
      knownConflicts: ["required_inactive_child"],
      findings: [
        {
          blocking: true,
          message: "Required child inactive: TPL-VOLUM-ALUMINIU_v1",
        },
      ],
    });
    expect(gate.publishEnabled).toBe(false);
    expect(gate.primaryBlockerRo).toMatch(/Aluminiu/i);
    expect(gate.secondaryCode).toMatch(/TPL-VOLUM-ALUMINIU/i);
    expect(gate.disabledReasonRo).toMatch(/Publică dezactivat/i);
  });

  it("fail-closes when readiness signal is missing even if publish_allowed is true", () => {
    const gate = resolvePublishUiGate(
      publication({ publish_allowed: true, last_e2e_verdict: null }),
      null,
    );
    expect(gate.publishEnabled).toBe(false);
    expect(gate.primaryBlockerRo).toMatch(/Pregătire E2E|Verifică traseul/i);
  });

  it("keeps publish disabled when API returns blockers", () => {
    const gate = resolvePublishUiGate(
      publication({
        publish_allowed: false,
        publish_blockers: ["known_conflict:TPL-VOLUM-ALUMINIU_v1", "readiness_verdict_BLOCKED"],
      }),
      { verdict: "BLOCKED", e2eReady: false },
    );
    expect(gate.publishEnabled).toBe(false);
    expect(gate.primaryBlockerRo).toMatch(/Aluminiu/i);
  });

  it("does not invent a READY path for VL — only enables on real publishable verdict", () => {
    const gate = resolvePublishUiGate(publication({ publish_allowed: true }), {
      verdict: "STATIC_READY",
      e2eReady: true,
      knownConflicts: [],
      findings: [],
    });
    expect(gate.publishEnabled).toBe(true);
    expect(gate.primaryBlockerRo).toBeNull();
  });

  it("allows publish for STATIC_READY_WITH_WARNINGS even when e2e_ready is false", () => {
    const gate = resolvePublishUiGate(publication({ publish_allowed: true }), {
      verdict: "STATIC_READY_WITH_WARNINGS",
      e2eReady: false,
      knownConflicts: ["TEMPLATE_IDENTITY"],
      findings: [],
    });
    expect(gate.publishEnabled).toBe(true);
  });
});

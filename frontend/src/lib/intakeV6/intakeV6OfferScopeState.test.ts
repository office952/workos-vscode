import { describe, expect, it } from "vitest";

import {
  isOfferScopeStateDirty,
  normalizeSoldModules,
  readPersistedOfferScope,
  serializeOfferScopeState,
  shouldPersistOfferScope,
} from "./intakeV6OfferScopeState";

describe("intakeV6OfferScopeState", () => {
  it("normalizes sold_modules to canonical order", () => {
    expect(normalizeSoldModules(["BACK", "FACE", "RETURN-CANT"])).toEqual([
      "FACE",
      "RETURN-CANT",
      "BACK",
    ]);
  });

  it("treats legacy workspaces without offer_scope as unconfirmed full product", () => {
    const persisted = readPersistedOfferScope({});
    expect(persisted.mode).toBe("full_product");
    expect(persisted.confirmed).toBe(false);
    expect(persisted.serialized).toBe("full_product");
  });

  it("does not persist when local state equals persisted state", () => {
    const persisted = readPersistedOfferScope({
      offer_scope: { mode: "full_product", sold_modules: [] },
      offer_scope_confirmed: { confirmed: true },
    });
    expect(
      shouldPersistOfferScope({ mode: "full_product", soldModules: [] }, persisted),
    ).toBe(false);
  });

  it("does not persist empty subset selection", () => {
    const persisted = readPersistedOfferScope({});
    expect(
      shouldPersistOfferScope({ mode: "component_subset", soldModules: [] }, persisted),
    ).toBe(false);
  });

  it("detects dirty subset changes", () => {
    const persisted = readPersistedOfferScope({
      offer_scope: { mode: "component_subset", sold_modules: ["FACE"] },
      offer_scope_confirmed: { confirmed: true },
    });
    expect(
      isOfferScopeStateDirty({ mode: "component_subset", soldModules: ["FACE", "BACK"] }, persisted),
    ).toBe(true);
    expect(serializeOfferScopeState("component_subset", ["FACE", "BACK"])).toBe(
      "component_subset:FACE|BACK",
    );
  });
});

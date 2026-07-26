import { describe, expect, it } from "vitest";
import { resolveIntakeV6ReviewTabs } from "./intakeV6ProductPlugin";
import {
  domainSelectionToTabState,
  expandReviewTabsToDomains,
  resolveReviewDomainFromTab,
} from "./intakeV6ReviewDomainNav";

describe("intakeV6ReviewDomainNav", () => {
  it("expands montaj into panou/carcasă and montaj comercial", () => {
    const domains = expandReviewTabsToDomains(
      resolveIntakeV6ReviewTabs("TPL-VOLUMETRIC-LETTERS_v2"),
    );
    expect(domains.map((d) => d.id)).toEqual([
      "finisaje",
      "iluminare",
      "panou_carcasa",
      "montaj_comercial",
    ]);
  });

  it("maps domain selection back to canonical montaj tab", () => {
    expect(domainSelectionToTabState("panou_carcasa")).toEqual({
      tab: "montaj",
      montajDomain: "panou_carcasa",
    });
    expect(domainSelectionToTabState("montaj_comercial")).toEqual({
      tab: "montaj",
      montajDomain: "montaj_comercial",
    });
    expect(domainSelectionToTabState("finisaje").tab).toBe("finisaje");
  });

  it("resolves active domain from tab + montaj subdomain", () => {
    const domains = expandReviewTabsToDomains(
      resolveIntakeV6ReviewTabs("TPL-VOLUMETRIC-LETTERS_v2"),
    );
    expect(resolveReviewDomainFromTab("montaj", "montaj_comercial", domains)).toBe(
      "montaj_comercial",
    );
    expect(resolveReviewDomainFromTab("finisaje", "panou_carcasa", domains)).toBe("finisaje");
  });
});

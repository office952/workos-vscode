import { describe, expect, it } from "vitest";
import {
  filterRegistryItems,
  product001ExpectedCodes,
  confidenceBadgeLabel,
  validateMaterialEditPayload,
  validateWorkcenterEditPayload,
  buildMaterialPatchPayload,
  buildWorkcenterPatchPayload,
  buildDetailPanelModel,
  rowCurrencyDiffersFromBase,
  CURRENCY_MISMATCH_WARNING,
  buildTemplateList,
  buildProblemQueue,
  computeTemplateStats,
  filterTemplatesForPicker,
  formatProblemBanner,
  groupItemsForCoverageStack,
  itemsForTemplate,
  pushRecentTemplate,
  quoteImpactLabel,
  statusDisplayText,
} from "./pricingRegistry";
import type { PricingRegistryItem } from "@/api/pricingRegistry";

const sampleItem = (
  overrides: Partial<PricingRegistryItem>
): PricingRegistryItem => ({
  pricing_code: "MAT-LED-MODULE",
  display_name: "LED Module",
  pricing_kind: "material",
  registry_category: "LED / electrice",
  unit: "buc",
  base_cost: 0.5,
  currency: "EUR",
  status: "active",
  confidence: "owner_confirmed",
  used_by_templates: ["TPL-VOLUMETRIC-LETTERS"],
  affects_quote_calculation: true,
  technical_source: "inventory_materials",
  ...overrides,
});

describe("pricingRegistry", () => {
  it("filters by template code", () => {
    const items = [
      sampleItem({ pricing_code: "MAT-LED-MODULE" }),
      sampleItem({
        pricing_code: "MAT-ACM-BOND-3MM",
        used_by_templates: ["TPL-ACM-CASSETTED-PANEL"],
        registry_category: "Plăci",
      }),
    ];
    const filtered = filterRegistryItems(items, {
      templateCode: "TPL-VOLUMETRIC-LETTERS_v2",
      section: "materials",
    });
    expect(filtered).toHaveLength(1);
    expect(filtered[0].pricing_code).toBe("MAT-LED-MODULE");
  });

  it("filters verification section", () => {
    const items = [
      sampleItem({ confidence: "owner_confirmed", status: "active" }),
      sampleItem({
        pricing_code: "MAT-VOPSEA-RAL",
        confidence: "estimated",
        status: "needs_review",
      }),
    ];
    const filtered = filterRegistryItems(items, { section: "verification" });
    expect(filtered).toHaveLength(1);
    expect(filtered[0].pricing_code).toBe("MAT-VOPSEA-RAL");
  });

  it("labels owner-confirmed confidence", () => {
    expect(confidenceBadgeLabel("owner_confirmed")).toBe("Owner-confirmed");
  });

  it("lists Product 001 expected codes", () => {
    expect(product001ExpectedCodes()).toContain("MAT-LED-MODULE");
    expect(product001ExpectedCodes()).toContain("RETURN_PROFILE_MACHINE_FORMING");
  });

  it("requires change_reason for material edit", () => {
    expect(
      validateMaterialEditPayload({
        unit_cost: "1.5",
        currency: "EUR",
        vat_percent: "",
        valid_from: "",
        status: "active",
        source_review_status: "",
        source_notes: "",
        change_reason: "",
      })
    ).toMatch(/obligatoriu/i);
  });

  it("rejects owner-confirmed without source notes", () => {
    expect(
      validateMaterialEditPayload({
        unit_cost: "1.5",
        currency: "EUR",
        vat_percent: "",
        valid_from: "",
        status: "active",
        source_review_status: "accepted_override",
        source_notes: "",
        change_reason: "test update",
      })
    ).toMatch(/note sursă/i);
  });

  it("builds material patch with change_reason", () => {
    const payload = buildMaterialPatchPayload({
      unit_cost: "2.5",
      currency: "EUR",
      vat_percent: "19",
      valid_from: "",
      status: "active",
      source_review_status: "",
      source_notes: "",
      change_reason: "pricing smoke test",
    });
    expect(payload.change_reason).toBe("pricing smoke test");
    expect(payload.unit_cost).toBe(2.5);
    expect(payload.snapshot_source).toBe("pricing_registry_edit");
  });

  it("requires change_reason for workcenter edit", () => {
    expect(
      validateWorkcenterEditPayload({
        rate_per_hour: "",
        rate_per_linear_meter: "5",
        rate_basis: "per_linear_meter",
        currency: "EUR",
        status: "active",
        notes: "",
        change_reason: "",
      })
    ).toMatch(/obligatoriu/i);
  });

  it("builds workcenter patch with audit note", () => {
    const payload = buildWorkcenterPatchPayload(
      {
        rate_per_hour: "",
        rate_per_linear_meter: "7",
        rate_basis: "per_linear_meter",
        currency: "EUR",
        status: "active",
        notes: "",
        change_reason: "rate adjustment",
      },
      "existing note"
    );
    expect(payload.notes).toContain("[Pricing] rate adjustment");
    expect(payload.rate_per_linear_meter).toBe(7);
  });
});

describe("pricingRegistry V2 spacious helpers", () => {
  const sampleItems = [
    {
      pricing_code: "MAT-LED-MODULE",
      display_name: "LED Module",
      pricing_kind: "material" as const,
      registry_category: "LED / electrice",
      unit: "buc",
      base_cost: 0.5,
      currency: "EUR",
      status: "active",
      confidence: "owner_confirmed",
      used_by_templates: ["TPL-VOLUMETRIC-LETTERS"],
      affects_quote_calculation: true,
      technical_source: "inventory_materials",
    },
    {
      pricing_code: "MAT-VOPSEA-RAL",
      display_name: "Vopsea RAL",
      pricing_kind: "material" as const,
      registry_category: "Consumabile",
      unit: "set",
      base_cost: 8,
      currency: "EUR",
      status: "needs_review",
      confidence: "estimated",
      used_by_templates: ["TPL-VOLUMETRIC-LETTERS"],
      affects_quote_calculation: true,
      technical_source: "inventory_materials",
    },
    {
      pricing_code: "RETURN_PROFILE_MACHINE_FORMING",
      display_name: "Formare cant",
      pricing_kind: "operation_rate" as const,
      registry_category: "Operații / Rate",
      unit: "EUR/ml",
      base_cost: 5,
      currency: "EUR",
      status: "active",
      confidence: "owner_confirmed",
      used_by_templates: ["TPL-VOLUMETRIC-LETTERS"],
      affects_quote_calculation: true,
      technical_source: "workcenter_rates",
    },
    {
      pricing_code: "MAT-ACM-BOND-4MM",
      display_name: "ACM 4mm",
      pricing_kind: "material" as const,
      registry_category: "Plăci",
      unit: "mp",
      base_cost: null,
      currency: "EUR",
      status: "missing_price",
      confidence: "missing",
      used_by_templates: ["TPL-ACM-CASSETTED-PANEL"],
      affects_quote_calculation: true,
      technical_source: "inventory_materials",
    },
  ];

  it("computes template stats and readiness", () => {
    const tplItems = itemsForTemplate(sampleItems, "TPL-VOLUMETRIC-LETTERS_v2");
    const stats = computeTemplateStats(tplItems);
    expect(stats.ownerConfirmed).toBe(2);
    expect(stats.estimated).toBe(1);
    expect(stats.readiness).toBe("partial");
  });

  it("builds problem queue with severities", () => {
    const queue = buildProblemQueue(
      itemsForTemplate(sampleItems, "TPL-VOLUMETRIC-LETTERS")
    );
    const viaAliasQueue = buildProblemQueue(
      itemsForTemplate(sampleItems, "TPL-VOLUMETRIC-LETTERS_v2")
    );
    expect(queue.length).toBe(1);
    expect(queue[0].severity).toBe("warn");
    expect(formatProblemBanner(queue)).toMatch(/estimare/i);
    expect(viaAliasQueue).toHaveLength(queue.length);
  });

  it("maps quote impact labels", () => {
    expect(quoteImpactLabel(sampleItems[0])).toBe("În calcul ofertă");
    expect(quoteImpactLabel(sampleItems[1])).toBe("Preliminar — review");
    expect(quoteImpactLabel(sampleItems[3])).toBe("Blochează calcul complet");
  });

  it("groups coverage stack by material and machine operation sections", () => {
    const tplItems = itemsForTemplate(sampleItems, "TPL-VOLUMETRIC-LETTERS_v2");
    const sections = groupItemsForCoverageStack(tplItems, []);
    expect(sections.some((s) => s.key === "materials")).toBe(true);
    expect(sections.some((s) => s.key === "machine_operations")).toBe(true);
    const ledGroup = sections
      .find((s) => s.key === "materials")
      ?.subgroups.find((g) => g.label === "LED / electrice");
    expect(ledGroup?.items[0].pricing_code).toBe("MAT-LED-MODULE");
  });

  it("omits verification section from coverage stack by default", () => {
    const tplItems = itemsForTemplate(sampleItems, "TPL-VOLUMETRIC-LETTERS_v2");
    const sections = groupItemsForCoverageStack(tplItems, []);
    expect(sections.some((s) => s.key === "verification")).toBe(false);
    const withVerify = groupItemsForCoverageStack(tplItems, [], { includeVerification: true });
    expect(withVerify.some((s) => s.key === "verification")).toBe(true);
  });

  it("flags currency mismatch against base currency", () => {
    expect(rowCurrencyDiffersFromBase(sampleItem({ currency: "EUR" }), "RON")).toBe(true);
    expect(rowCurrencyDiffersFromBase(sampleItem({ currency: "EUR" }), "EUR")).toBe(false);
    const model = buildDetailPanelModel(sampleItem({ currency: "EUR" }), {
      baseCurrency: "RON",
    });
    expect(model?.currencyMismatchWarning).toBe(CURRENCY_MISMATCH_WARNING);
  });

  it("builds safe detail panel model with fallbacks", () => {
    expect(buildDetailPanelModel(null)).toBeNull();
    expect(buildDetailPanelModel(undefined)).toBeNull();
    const model = buildDetailPanelModel(sampleItems[0]);
    expect(model?.code).toBe("MAT-LED-MODULE");
    expect(model?.isMaterial).toBe(true);
    expect(model?.impact).toBe("În calcul ofertă");
    expect(model?.status).toEqual(statusDisplayText(sampleItems[0]));
  });

  it("maps missing price items without crashing", () => {
    const model = buildDetailPanelModel(sampleItems[3]);
    expect(model?.value).toBe("Lipsă");
    expect(model?.impact).toBe("Blochează calcul complet");
    expect(model?.status.severity).toBe("bad");
  });

  it("filters templates for scalable picker", () => {
    const list = buildTemplateList([
      {
        template_code: "TPL-VOLUMETRIC-LETTERS",
        material_codes: ["MAT-LED-MODULE"],
        workcenter_codes: [],
      },
      {
        template_code: "TPL-ACM-CASSETTED-PANEL",
        material_codes: ["MAT-ACM-BOND-3MM"],
        workcenter_codes: [],
      },
    ]);
    const filtered = filterTemplatesForPicker(list, { search: "ACM" });
    expect(filtered).toHaveLength(1);
    expect(filtered[0].template_code).toBe("TPL-ACM-CASSETTED-PANEL");
  });

  it("tracks recent templates", () => {
    expect(pushRecentTemplate([], "TPL-ACM-CASSETTED-PANEL")).toEqual([
      "TPL-ACM-CASSETTED-PANEL",
    ]);
    expect(
      pushRecentTemplate(["TPL-ACM-CASSETTED-PANEL"], "TPL-VOLUMETRIC-LETTERS")
    ).toEqual(["TPL-VOLUMETRIC-LETTERS_v2", "TPL-ACM-CASSETTED-PANEL"]);
  });
});

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import ProductTruthPromotionPlannerPanel from "./ProductTruthPromotionPlannerPanel";
import type { IntakeV6ProductTruthPromotionPlannerResponse } from "@/lib/intakeV6/intakeV6Api";

const model: IntakeV6ProductTruthPromotionPlannerResponse = {
  read_only: true,
  workspace_id: "product-truth-planner-workspace",
  workspace_record_id: "product-truth-planner-workspace",
  workspace_code: "IV6-PRODUCT-TRUTH-PLANNER",
  root_template_code: "TPL-VOLUMETRIC-LETTERS_v2",
  product_binding_template_code: "TPL-VOLUMETRIC-LETTERS_v2",
  planner_version: "v1",
  eligible_entries: [
    {
      entry_key: "finish.finish_target",
      field_key: "finish.finish_target",
      runtime_source: "finish_setup.finish_target",
      product_truth_path: "components.finish.target",
      state: "confirmed",
      value_status: "explicit_confirmed",
      promotion_allowed: true,
      reason: "Field value is explicitly persisted and confirmed.",
      blockers: [],
    },
  ],
  blocked_entries: [
    {
      entry_key: "support.support_type",
      field_key: "support.support_type",
      runtime_source: "finish_setup.support_type",
      product_truth_path: "components.support.supportType",
      state: "suggested",
      value_status: "evidence_only",
      promotion_allowed: false,
      reason: "Support evidence exists, but explicit confirmed support type is still missing.",
      blockers: ["SUPPORT_TYPE_MISSING"],
    },
  ],
  blockers: [
    {
      field_key: "support.support_type",
      blockers: ["SUPPORT_TYPE_MISSING"],
      state: "suggested",
    },
  ],
  downstream_write_intent: {
    product_truth_write: false,
    pricing_write: false,
    quote_write: false,
    order_write: false,
    product_definition_write: false,
    product_aggregate_write: false,
    task_graph_write: false,
    execution_runtime_write: false,
    inventory_movement: false,
    db_write: false,
  },
  notes: ["Read-only planner only."],
};

describe("ProductTruthPromotionPlannerPanel", () => {
  it("renders planner metadata, counts, and read-only write-intent status without edit controls", () => {
    const { container } = render(
      <ProductTruthPromotionPlannerPanel model={model} loading={false} error={null} />,
    );

    expect(screen.getByTestId("product-truth-promotion-planner-panel")).toHaveAttribute("data-read-only", "true");
    expect(screen.getByTestId("product-truth-promotion-planner-version")).toHaveTextContent("v1");
    expect(screen.getByTestId("product-truth-promotion-planner-read-only")).toHaveTextContent("true");
    expect(screen.getByTestId("product-truth-promotion-planner-root-template")).toHaveTextContent(
      "TPL-VOLUMETRIC-LETTERS_v2",
    );
    expect(screen.getByTestId("product-truth-promotion-planner-binding-template")).toHaveTextContent(
      "TPL-VOLUMETRIC-LETTERS_v2",
    );
    expect(screen.getByTestId("product-truth-promotion-planner-eligible-count")).toHaveTextContent("1");
    expect(screen.getByTestId("product-truth-promotion-planner-blocked-count")).toHaveTextContent("1");
    expect(screen.getByTestId("product-truth-promotion-planner-eligible-list")).toHaveTextContent(
      "finish.finish_target",
    );
    expect(screen.getByTestId("product-truth-promotion-planner-blocked-list")).toHaveTextContent(
      "support.support_type",
    );
    expect(screen.getByTestId("product-truth-promotion-planner-blocked-list")).toHaveTextContent(
      "SUPPORT_TYPE_MISSING",
    );
    expect(screen.getByTestId("product-truth-promotion-planner-write-intent-summary")).toHaveTextContent(
      "10/10 write flags sunt false.",
    );
    expect(screen.getByTestId("product-truth-promotion-planner-write-intent-safe")).toHaveTextContent(
      "All downstream write flags are false.",
    );
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
    expect(container.querySelector("input")).toBeNull();
    expect(container.querySelector("textarea")).toBeNull();
    expect(container.querySelector("select")).toBeNull();
    expect(container.querySelector("[contenteditable]")).toBeNull();
  });

  it("surfaces a controlled non-blocking error state and explicit zero eligible entries", () => {
    render(<ProductTruthPromotionPlannerPanel model={null} loading={false} error="Request failed (500)" />);

    expect(screen.getByTestId("product-truth-promotion-planner-error")).toHaveTextContent("indisponibil");
    expect(screen.getByTestId("product-truth-promotion-planner-error")).toHaveTextContent("Request failed (500)");
    expect(screen.getByTestId("product-truth-promotion-planner-summary")).toHaveTextContent(
      "Product truth promotion planner unavailable",
    );
    expect(screen.getByTestId("product-truth-promotion-planner-eligible-list-empty")).toHaveTextContent(
      "0 eligible entries",
    );
  });
});
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import FormSystemRuntimeCaptureReadModelPanel from "./FormSystemRuntimeCaptureReadModelPanel";
import type { IntakeV6RuntimeCaptureReadModelResponse } from "@/lib/intakeV6/intakeV6Api";

const model: IntakeV6RuntimeCaptureReadModelResponse = {
  read_only: true,
  workspace_id: "runtime-capture-read-model-workspace",
  workspace_record_id: "runtime-capture-read-model-workspace",
  workspace_code: "IV6-RUNTIME-CAPTURE-READ-MODEL",
  root_template_code: "TPL-VOLUMETRIC-LETTERS_v2",
  product_binding_template_code: "TPL-VOLUMETRIC-LETTERS_v2",
  read_model_version: "v1",
  fields: [
    {
      field_key: "svg.selected_layer_refs[]",
      runtime_source: "svg.selected_layer_refs[]",
      product_truth_path: "svg.selected_layer_refs[]",
      state: "confirmed",
      confirmation_rule: "Persisted selected layer refs require confirmation.",
      blockers: [],
      ready_for_product_truth: true,
    },
    {
      field_key: "support.support_type",
      runtime_source: "finish_setup.support_type",
      product_truth_path: "components.support.supportType",
      state: "blocked",
      confirmation_rule: "Explicit persisted support type required.",
      blockers: ["SUPPORT_TYPE_MISSING"],
      ready_for_product_truth: false,
    },
  ],
  blockers: [
    {
      field_key: "support.support_type",
      blockers: ["SUPPORT_TYPE_MISSING"],
      state: "blocked",
    },
  ],
  downstream_write_intent: {
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
  notes: ["Minimal runtime capture read model only."],
};

describe("FormSystemRuntimeCaptureReadModelPanel", () => {
  it("renders read-only field state rows without edit controls", () => {
    render(<FormSystemRuntimeCaptureReadModelPanel model={model} loading={false} error={null} />);

    expect(screen.getByTestId("runtime-capture-read-model-panel")).toHaveAttribute("data-read-only", "true");
    expect(screen.getByTestId("runtime-capture-read-model-summary")).toHaveTextContent("IV6-RUNTIME-CAPTURE-READ-MODEL");
    expect(screen.getByTestId("runtime-capture-read-model-summary")).toHaveTextContent("2 fields");
    expect(screen.getByTestId("runtime-capture-read-model-summary")).toHaveTextContent("1 blocked");
    expect(screen.getByTestId("runtime-capture-read-model-fields")).toHaveTextContent("svg.selected_layer_refs[]");
    expect(screen.getByTestId("runtime-capture-read-model-fields")).toHaveTextContent("support.support_type");
    expect(screen.getByTestId("runtime-capture-read-model-fields")).toHaveTextContent("confirmed");
    expect(screen.getByTestId("runtime-capture-read-model-fields")).toHaveTextContent("blocked");
    expect(screen.getByTestId("runtime-capture-read-model-fields")).toHaveTextContent("ready for product truth");
    expect(screen.getByTestId("runtime-capture-read-model-fields")).toHaveTextContent("not ready");
    expect(screen.getByTestId("runtime-capture-read-model-fields")).toHaveTextContent("SUPPORT_TYPE_MISSING");
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
  });

  it("surfaces a controlled non-blocking error state", () => {
    render(<FormSystemRuntimeCaptureReadModelPanel model={null} loading={false} error="Request failed (500)" />);

    expect(screen.getByTestId("runtime-capture-read-model-error")).toHaveTextContent("indisponibil");
    expect(screen.getByTestId("runtime-capture-read-model-error")).toHaveTextContent("Request failed (500)");
    expect(screen.getByTestId("runtime-capture-read-model-empty")).toHaveTextContent("Niciun camp runtime capture disponibil inca.");
  });
});
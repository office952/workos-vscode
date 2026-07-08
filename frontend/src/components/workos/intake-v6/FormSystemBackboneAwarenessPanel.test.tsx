import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import FormSystemBackboneAwarenessPanel from "./FormSystemBackboneAwarenessPanel";
import type { FormSystemBackboneContract } from "@/lib/intakeV6/intakeV6ModularFormContractTypes";
import type { FormSystemRuntimeStateOverlayInput } from "@/lib/intakeV6/formSystemBackboneRuntimeStateOverlay";

const backbone: FormSystemBackboneContract = {
  read_only: true,
  root: {
    canonical_code: "TPL-VOLUMETRIC-LETTERS_v2",
    root_type: "product_template",
    quote_mode: "product_total",
    allowed: true,
    blocked: false,
    canonical_alias_resolution: true,
  },
  components: [
    { component_key: "face", label: "Face", coverage: "covered" },
    { component_key: "back", label: "Back", coverage: "partial" },
    { component_key: "electrical", label: "Electrical", coverage: "future" },
  ],
  fields: [
    {
      field_key: "svg.layer_group_role",
      owning_component: "svg_layer_roles",
      source_type: "svg_suggested",
      state: "suggested",
      product_truth_path: "svg.layer_roles[].suggested_role",
      required_for: ["quote_preview"],
      blocker_code: "LAYER_ROLES_INCOMPLETE",
    },
    {
      field_key: "return.depth_mm",
      owning_component: "return_cant",
      source_type: "hydrated",
      state: "hydrated",
      product_truth_path: "components.return.depth_mm",
      required_for: ["quote_preview"],
      blocker_code: "RETURN_CANT_HEIGHT_CONFIRMATION_REQUIRED",
    },
    {
      field_key: "lighting.type",
      owning_component: "lighting_led",
      source_type: "fallback",
      state: "fallback",
      product_truth_path: "components.lighting.illumination_type",
      required_for: ["quote_preview"],
      blocker_code: "LIGHTING_MODE_CONFIRMATION_REQUIRED",
    },
  ],
  blockers: [
    { field_key: "svg.layer_group_role", blocker_code: "LAYER_ROLES_INCOMPLETE", owning_component: "svg_layer_roles", message: "Confirm roles" },
    { field_key: "readiness.product_truth_blockers", blocker_code: "PRODUCT_TRUTH_INCOMPLETE", owning_component: "readiness", message: "Readiness summarizes missing required truth." },
  ],
  downstream_write_intent: {
    pricing_write: false,
    quote_write: false,
    order_write: false,
    execution_runtime_write: false,
    db_write: false,
  },
};

const runtimeState: FormSystemRuntimeStateOverlayInput = {
  layerRoleSetup: {
    confirmation_status: "complete",
    layers: [
      {
        layer_key: "face-1",
        layer_id: "face-1",
        layer_name: "Face 1",
        auto_role: "face",
        auto_confidence: "high",
        confirmed_role: "face",
        confirmation_state: "confirmed",
      },
    ],
    warnings: [],
  },
};

describe("FormSystemBackboneAwarenessPanel", () => {
  it("renders collapsed by default with compact summary", () => {
    render(<FormSystemBackboneAwarenessPanel backbone={backbone} />);

    expect(screen.getByTestId("form-system-backbone-awareness-panel")).toHaveAttribute("data-read-only", "true");
    expect(screen.getByText("Form System Backbone")).toBeInTheDocument();
    expect(screen.getByTestId("form-system-backbone-summary")).toHaveTextContent("TPL-VOLUMETRIC-LETTERS_v2");
    expect(screen.getByTestId("form-system-backbone-summary")).toHaveTextContent("3 fields");
    expect(screen.getByTestId("form-system-backbone-summary")).toHaveTextContent("2 blockers");
    expect(screen.getByTestId("form-system-backbone-toggle")).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryByTestId("form-system-backbone-details")).not.toBeInTheDocument();
  });

  it("expands and collapses diagnostic details", () => {
    render(<FormSystemBackboneAwarenessPanel backbone={backbone} />);

    fireEvent.click(screen.getByTestId("form-system-backbone-toggle"));

    expect(screen.getByTestId("form-system-backbone-toggle")).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByTestId("form-system-backbone-details")).toBeInTheDocument();
    expect(screen.getByText("TPL-VOLUMETRIC-LETTERS_v2")).toBeInTheDocument();
    expect(screen.getByText("alias normalized")).toBeInTheDocument();
    expect(screen.getByTestId("form-system-backbone-component-coverage")).toHaveTextContent("covered 1");
    expect(screen.getByTestId("form-system-backbone-component-coverage")).toHaveTextContent("partial 1");
    expect(screen.getByTestId("form-system-backbone-fields")).toHaveTextContent("svg.layer_group_role");
    expect(screen.getByTestId("form-system-backbone-fields")).toHaveTextContent("svg_suggested / suggested");
    expect(screen.getByTestId("form-system-backbone-state-warnings")).toHaveTextContent("Suggested values are not confirmed");
    expect(screen.getByTestId("form-system-backbone-state-warnings")).toHaveTextContent("Fallback/hydrated values are not confirmed");
    expect(screen.getByTestId("form-system-backbone-blockers")).toHaveTextContent("LAYER_ROLES_INCOMPLETE");
    expect(screen.getByTestId("form-system-backbone-read-only-safety")).toHaveTextContent("does not price");

    fireEvent.click(screen.getByTestId("form-system-backbone-toggle"));

    expect(screen.getByTestId("form-system-backbone-toggle")).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryByTestId("form-system-backbone-details")).not.toBeInTheDocument();
  });

  it("does not render pricing, quote, order or execution CTAs", () => {
    render(<FormSystemBackboneAwarenessPanel backbone={backbone} />);

    expect(screen.getByTestId("form-system-backbone-toggle")).toBeInTheDocument();
    expect(screen.queryByText(/Creeaz/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Preț oficial/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/RON|EUR|TVA/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    expect(screen.queryByRole("checkbox")).not.toBeInTheDocument();
  });

  it("renders relaxed field-level blockers without hiding the row", () => {
    render(<FormSystemBackboneAwarenessPanel backbone={backbone} runtimeState={runtimeState} />);

    fireEvent.click(screen.getByTestId("form-system-backbone-toggle"));

    expect(screen.getByTestId("form-system-backbone-blockers")).toHaveTextContent("LAYER_ROLES_INCOMPLETE");
    expect(screen.getByTestId("form-system-backbone-blockers")).toHaveTextContent("Resolved by runtime confirmation; kept for backbone audit.");
  });

  it("keeps broad blockers active without relaxed presentation", () => {
    render(<FormSystemBackboneAwarenessPanel backbone={backbone} runtimeState={runtimeState} />);

    fireEvent.click(screen.getByTestId("form-system-backbone-toggle"));

    expect(screen.getByTestId("form-system-backbone-blockers")).toHaveTextContent("PRODUCT_TRUTH_INCOMPLETE");
    expect(screen.getAllByTestId("form-system-backbone-blocker-relaxed")).toHaveLength(1);
  });

  it("surfaces broad blockers explicitly when the visible blocker slice is full", () => {
    const crowdedBackbone: FormSystemBackboneContract = {
      ...backbone,
      blockers: [
        { field_key: "svg.layer_group_role", blocker_code: "LAYER_ROLES_INCOMPLETE", owning_component: "svg_layer_roles", message: "Confirm roles" },
        { field_key: "svg.selected_layer_group", blocker_code: "SELECTED_FACE_LAYER_MISSING", owning_component: "svg_layer_roles", message: "Select face layer" },
        { field_key: "face.material", blocker_code: "FACE_MATERIAL_MISSING", owning_component: "face", message: "Face material missing" },
        { field_key: "face.finish_artwork_target", blocker_code: "FACE_FINISH_TARGET_MISSING", owning_component: "finish_artwork", message: "Finish target missing" },
        { field_key: "readiness.product_truth_blockers", blocker_code: "PRODUCT_TRUTH_INCOMPLETE", owning_component: "readiness", message: "Readiness summarizes missing required truth." },
      ],
    };

    render(<FormSystemBackboneAwarenessPanel backbone={crowdedBackbone} runtimeState={runtimeState} />);

    fireEvent.click(screen.getByTestId("form-system-backbone-toggle"));

    expect(screen.getByTestId("form-system-backbone-blockers")).toHaveTextContent("Readiness / blockers (5)");
    expect(screen.getByTestId("form-system-backbone-global-blockers")).toHaveTextContent("PRODUCT_TRUTH_INCOMPLETE");
    expect(screen.getByTestId("form-system-backbone-global-blockers")).toHaveTextContent("Product Truth blockers");
  });

  it("handles missing backbone compactly without crashing", () => {
    render(<FormSystemBackboneAwarenessPanel backbone={null} />);

    expect(screen.getByTestId("form-system-backbone-summary")).toHaveTextContent("diagnostic unavailable");
    expect(screen.queryByTestId("form-system-backbone-details")).not.toBeInTheDocument();

    fireEvent.click(screen.getByTestId("form-system-backbone-toggle"));

    expect(screen.getByTestId("form-system-backbone-details")).toHaveTextContent("diagnostic unavailable");
    expect(screen.getByTestId("form-system-backbone-details")).toHaveTextContent("Review flow remains unchanged");
  });
});
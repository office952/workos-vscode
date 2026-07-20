import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { TemplateRuntimePreviewPanel } from "./TemplateRuntimePreviewPanel";

vi.mock("@/api/productDefinitionPreview", () => ({
  getProductDefinitionPreview: vi.fn(async () => ({
    preview_version: "v1",
    template_code: "TPL-VOLUMETRIC-LETTERS_v2",
    source_context: {
      template_code: "TPL-VOLUMETRIC-LETTERS_v2",
      source_payload_type: "template_only",
    },
    selected_modules: [{ module_code: "MOD-A", module_name: "A", activation_kind: "required", state: "active", missing_fields: [] }],
    optional_modules: [],
    inactive_modules: [],
    components: [{ component_id: "c1", module_active: true, provenance: "template" }],
    material_roles: [{ material_code: "MAT-1", module_active: true, provenance: "template" }],
    operation_roles: [{ operation_code: "OP-1", module_active: true, is_geometry_gate: false, is_priced: false, provenance: "template" }],
    canonical_values: {},
    geometry_inputs: {},
    validation: {
      readiness_status: "partial",
      missing_required_fields: [],
      invalid_combinations: [],
      unresolved_warnings: [],
    },
    provenance: [{ key: "template", source: "product_system", detail: "template-only" }],
    warnings: [],
    notes: [],
    composition: null,
  })),
}));

describe("TemplateRuntimePreviewPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders human summary first and collapsed diagnostics for PD preview", async () => {
    render(<TemplateRuntimePreviewPanel templateCode="TPL-VOLUMETRIC-LETTERS_v2" />);
    await waitFor(() => {
      expect(screen.getByTestId("runtime-preview-body")).toBeTruthy();
    });
    expect(screen.getByTestId("runtime-preview-human-summary")).toHaveTextContent(/Rezumat operator/i);
    expect(screen.getByTestId("runtime-preview-human-summary")).toHaveTextContent(/Parțial/);
    expect(screen.getByTestId("runtime-preview-modules")).toHaveTextContent(/MOD-A/);
    expect(screen.getByTestId("runtime-preview-materials")).toHaveTextContent(/Materials/);
  });
});


import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import IntakeContractFieldRenderer from "./IntakeContractFieldRenderer";
import type { IntakeV6ModularFormFieldBinding } from "@/lib/intakeV6/intakeV6ModularFormContractTypes";

function field(partial: Partial<IntakeV6ModularFormFieldBinding>): IntakeV6ModularFormFieldBinding {
  return {
    canonical_key: "sample_field",
    workspace_path: "finish_setup.sample_field",
    label_ro: "Câmp exemplu",
    ...partial,
  };
}

describe("IntakeContractFieldRenderer", () => {
  it("renders select options from contract without product-specific keys in component logic", () => {
    const onChange = vi.fn();
    render(
      <IntakeContractFieldRenderer
        field={field({
          field_type: "select",
          options: [
            { value: "a", label_ro: "Opțiunea A" },
            { value: "b", label_ro: "Opțiunea B" },
          ],
        })}
        value="a"
        onChange={onChange}
      />,
    );
    expect(screen.getByText("Câmp exemplu")).toBeInTheDocument();
    expect(screen.getByText("Opțiunea A")).toBeInTheDocument();
    fireEvent.change(screen.getByTestId("intake-contract-field-sample_field-input"), {
      target: { value: "b" },
    });
    expect(onChange).toHaveBeenCalledWith("b");
  });

  it("surfaces unsupported field types visibly", () => {
    render(
      <IntakeContractFieldRenderer
        field={field({ field_type: "geometry_svg_blob" })}
        value={null}
        onChange={() => undefined}
      />,
    );
    expect(screen.getByTestId("intake-contract-field-sample_field-unsupported")).toHaveTextContent(
      "nesuportat",
    );
  });

  it("renders boolean and number controls", () => {
    const onBool = vi.fn();
    const { rerender } = render(
      <IntakeContractFieldRenderer
        field={field({ canonical_key: "flag", field_type: "boolean", label_ro: "Activ" })}
        value={false}
        onChange={onBool}
      />,
    );
    fireEvent.click(screen.getByTestId("intake-contract-field-flag-input"));
    expect(onBool).toHaveBeenCalledWith(true);

    const onNum = vi.fn();
    rerender(
      <IntakeContractFieldRenderer
        field={field({
          canonical_key: "area",
          field_type: "number",
          unit: "m2",
          label_ro: "Arie",
        })}
        value={1.5}
        onChange={onNum}
      />,
    );
    fireEvent.change(screen.getByTestId("intake-contract-field-area-input"), {
      target: { value: "2.25" },
    });
    expect(onNum).toHaveBeenCalledWith(2.25);
  });
});

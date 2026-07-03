import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import WorkOsSvgFilePicker from "./WorkOsSvgFilePicker";
import {
  processWorkOsSvgFilePickerSelection,
  resolveWorkOsSvgFilePickerBlockMessage,
} from "./workOsSvgFilePickerLogic";

describe("workOsSvgFilePickerLogic", () => {
  it("returns block message when not ready", () => {
    expect(
      resolveWorkOsSvgFilePickerBlockMessage({ ready: false, busy: false, notReadyMessage: "Wait" }),
    ).toBe("Wait");
  });

  it("blocks selection when busy without calling pick", () => {
    const file = new File(["<svg/>"], "a.svg", { type: "image/svg+xml" });
    const result = processWorkOsSvgFilePickerSelection([file], { ready: true, busy: true });
    expect(result.blocked).toBe(true);
    expect(result.file).toBeNull();
  });
});

describe("WorkOsSvgFilePicker", () => {
  it("never disables the file input", () => {
    render(
      <WorkOsSvgFilePicker
        ready={false}
        busy
        testId="picker"
        onFileSelected={vi.fn()}
      />,
    );
    expect(screen.getByTestId("picker-input")).not.toBeDisabled();
  });

  it("uses a label trigger with hidden input (nest2 pattern)", () => {
    render(<WorkOsSvgFilePicker ready testId="picker" onFileSelected={vi.fn()} />);
    const label = screen.getByTestId("picker-button");
    const input = screen.getByTestId("picker-input") as HTMLInputElement;
    expect(label.tagName).toBe("LABEL");
    expect(label).toContainElement(input);
    expect(input.hidden).toBe(true);
    expect(input).not.toHaveClass("opacity-0");
  });

  it("calls onBlocked when file selected while not ready", async () => {
    const onBlocked = vi.fn();
    const onFileSelected = vi.fn();
    render(
      <WorkOsSvgFilePicker
        ready={false}
        notReadyMessage="Workspace loading"
        testId="picker"
        onBlocked={onBlocked}
        onFileSelected={onFileSelected}
      />,
    );
    const file = new File(["<svg/>"], "a.svg", { type: "image/svg+xml" });
    fireEvent.change(screen.getByTestId("picker-input"), { target: { files: [file] } });
    await waitFor(() => {
      expect(onBlocked).toHaveBeenCalledWith("Workspace loading");
    });
    expect(onFileSelected).not.toHaveBeenCalled();
  });

  it("delivers valid SVG to onFileSelected when ready", async () => {
    const onFileSelected = vi.fn();
    render(
      <WorkOsSvgFilePicker ready testId="picker" onFileSelected={onFileSelected} />,
    );
    const file = new File(["<svg/>"], "a.svg", { type: "image/svg+xml" });
    fireEvent.change(screen.getByTestId("picker-input"), { target: { files: [file] } });
    await waitFor(() => {
      expect(onFileSelected).toHaveBeenCalledTimes(1);
      expect(onFileSelected).toHaveBeenCalledWith(file);
    });
  });

  it("reports invalid file via onValidationError", async () => {
    const onValidationError = vi.fn();
    const onFileSelected = vi.fn();
    render(
      <WorkOsSvgFilePicker
        ready
        testId="picker"
        onValidationError={onValidationError}
        onFileSelected={onFileSelected}
      />,
    );
    const file = new File(["hello"], "notes.txt", { type: "text/plain" });
    fireEvent.change(screen.getByTestId("picker-input"), { target: { files: [file] } });
    await waitFor(() => {
      expect(onValidationError).toHaveBeenCalledWith("Please select a valid SVG file.");
    });
    expect(onFileSelected).not.toHaveBeenCalled();
  });

  it("allows selecting the same filename again after input reset", async () => {
    const onFileSelected = vi.fn();
    render(<WorkOsSvgFilePicker ready testId="picker" onFileSelected={onFileSelected} />);
    const input = screen.getByTestId("picker-input") as HTMLInputElement;
    const file = new File(["<svg/>"], "a.svg", { type: "image/svg+xml" });
    fireEvent.change(input, { target: { files: [file] } });
    await waitFor(() => expect(onFileSelected).toHaveBeenCalledTimes(1));
    fireEvent.change(input, { target: { files: [file] } });
    await waitFor(() => expect(onFileSelected).toHaveBeenCalledTimes(2));
  });

  it("dropzone variant delivers dropped SVG once", async () => {
    const onFileSelected = vi.fn();
    render(
      <WorkOsSvgFilePicker variant="dropzone" ready testId="picker" onFileSelected={onFileSelected}>
        Drop here
      </WorkOsSvgFilePicker>,
    );
    const file = new File(["<svg/>"], "drop.svg", { type: "image/svg+xml" });
    fireEvent.drop(screen.getByTestId("picker-dropzone"), {
      dataTransfer: { files: [file] },
    });
    await waitFor(() => {
      expect(onFileSelected).toHaveBeenCalledTimes(1);
      expect(onFileSelected).toHaveBeenCalledWith(file);
    });
  });

  it("resets input value after selection", async () => {
    render(<WorkOsSvgFilePicker ready testId="picker" onFileSelected={vi.fn()} />);
    const input = screen.getByTestId("picker-input") as HTMLInputElement;
    const file = new File(["<svg/>"], "a.svg", { type: "image/svg+xml" });
    fireEvent.change(input, { target: { files: [file] } });
    await waitFor(() => expect(input.value).toBe(""));
  });

  it("dropzone variant wraps content in label", () => {
    render(
      <WorkOsSvgFilePicker
        variant="dropzone"
        testId="picker"
        dropzoneTestId="picker-dropzone"
        onFileSelected={vi.fn()}
      >
        <span>Browse here</span>
      </WorkOsSvgFilePicker>,
    );
    expect(screen.getByTestId("picker-dropzone").tagName).toBe("LABEL");
    expect(screen.getByText("Browse here")).toBeInTheDocument();
  });
});

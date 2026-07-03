import { useCallback, useId, useRef, useState, type DragEvent, type ReactNode } from "react";
import {
  DEFAULT_SVG_ACCEPT,
  processWorkOsSvgFilePickerSelection,
  type WorkOsSvgFilePickerGuardState,
} from "./workOsSvgFilePickerLogic";

export type WorkOsSvgFilePickerVariant = "button" | "overlay" | "dropzone";

export interface WorkOsSvgFilePickerProps extends WorkOsSvgFilePickerGuardState {
  variant?: WorkOsSvgFilePickerVariant;
  label?: string;
  busyLabel?: string;
  accept?: string;
  className?: string;
  buttonClassName?: string;
  overlayClassName?: string;
  dropzoneClassName?: string;
  testId?: string;
  inputTestId?: string;
  buttonTestId?: string;
  overlayTestId?: string;
  dropzoneTestId?: string;
  children?: ReactNode;
  onFileSelected: (file: File) => void | Promise<void>;
  onBlocked?: (message: string) => void;
  onValidationError?: (message: string) => void;
  onPickWarning?: (message: string) => void;
}

export function useWorkOsSvgFilePicker({
  ready = true,
  busy = false,
  notReadyMessage,
  busyMessage,
  onFileSelected,
  onBlocked,
  onValidationError,
  onPickWarning,
}: Pick<
  WorkOsSvgFilePickerProps,
  | "ready"
  | "busy"
  | "notReadyMessage"
  | "busyMessage"
  | "onFileSelected"
  | "onBlocked"
  | "onValidationError"
  | "onPickWarning"
>) {
  const inputRef = useRef<HTMLInputElement>(null);

  const processFiles = useCallback(
    async (files: FileList | File[] | null | undefined) => {
      const result = processWorkOsSvgFilePickerSelection(files, {
        ready,
        busy,
        notReadyMessage,
        busyMessage,
      });

      if (result.blocked) {
        if (result.error) onBlocked?.(result.error);
        return;
      }
      if (!result.file) {
        if (result.error) onValidationError?.(result.error);
        return;
      }
      if (result.warning) onPickWarning?.(result.warning);
      await onFileSelected(result.file);
    },
    [busy, busyMessage, notReadyMessage, onBlocked, onFileSelected, onPickWarning, onValidationError, ready],
  );

  const handleChange = useCallback(
    async (event: React.ChangeEvent<HTMLInputElement>) => {
      const input = event.currentTarget;
      await processFiles(input.files);
      input.value = "";
    },
    [processFiles],
  );

  return { inputRef, handleChange, processFiles };
}

export default function WorkOsSvgFilePicker({
  variant = "button",
  ready = true,
  busy = false,
  label = "Load SVG",
  busyLabel = "Procesez…",
  notReadyMessage,
  busyMessage,
  accept = DEFAULT_SVG_ACCEPT,
  className,
  buttonClassName,
  overlayClassName,
  dropzoneClassName,
  testId = "workos-svg-file-picker",
  inputTestId,
  buttonTestId,
  overlayTestId,
  dropzoneTestId,
  children,
  onFileSelected,
  onBlocked,
  onValidationError,
  onPickWarning,
}: WorkOsSvgFilePickerProps) {
  const autoId = useId();
  const inputId = `${testId}-input-${autoId}`;
  const { inputRef, handleChange, processFiles } = useWorkOsSvgFilePicker({
    ready,
    busy,
    notReadyMessage,
    busyMessage,
    onFileSelected,
    onBlocked,
    onValidationError,
    onPickWarning,
  });

  const [dragActive, setDragActive] = useState(false);

  const displayLabel = busy ? busyLabel : label;
  const visuallyDisabled = !ready || busy;

  const handleDragEnter = useCallback(
    (event: DragEvent) => {
      event.preventDefault();
      event.stopPropagation();
      if (!visuallyDisabled) setDragActive(true);
    },
    [visuallyDisabled],
  );

  const handleDragLeave = useCallback((event: DragEvent) => {
    event.preventDefault();
    event.stopPropagation();
    setDragActive(false);
  }, []);

  const handleDragOver = useCallback((event: DragEvent) => {
    event.preventDefault();
    event.stopPropagation();
  }, []);

  const handleDrop = useCallback(
    (event: DragEvent) => {
      event.preventDefault();
      event.stopPropagation();
      setDragActive(false);
      void processFiles(event.dataTransfer.files);
    },
    [processFiles],
  );

  // nest2 SVG Analyzer: label + hidden file input (no opacity-0 overlay — breaks browse in Chrome/Edge)
  const input = (
    <input
      ref={inputRef}
      id={inputId}
      type="file"
      accept={accept}
      hidden
      data-testid={inputTestId ?? `${testId}-input`}
      onChange={(event) => void handleChange(event)}
    />
  );

  if (variant === "dropzone") {
    return (
      <label
        className={`${dropzoneClassName ?? ""} block cursor-pointer ${
          visuallyDisabled ? "opacity-60" : dragActive ? "border-sky-500/60 bg-sky-500/10" : ""
        } ${className ?? ""}`}
        data-testid={dropzoneTestId ?? `${testId}-dropzone`}
        aria-disabled={visuallyDisabled || undefined}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
        {children}
        {input}
      </label>
    );
  }

  if (variant === "overlay") {
    return (
      <label
        className={`${overlayClassName ?? buttonClassName ?? ""} inline-flex cursor-pointer items-center gap-2 ${
          visuallyDisabled ? "opacity-50" : ""
        } ${className ?? ""}`}
        data-testid={overlayTestId ?? `${testId}-overlay`}
        aria-disabled={visuallyDisabled || undefined}
      >
        {children ?? displayLabel}
        {input}
      </label>
    );
  }

  return (
    <label
      className={`${buttonClassName ?? ""} inline-flex cursor-pointer items-center ${
        visuallyDisabled ? "opacity-50" : ""
      } ${className ?? ""}`}
      data-testid={buttonTestId ?? `${testId}-button`}
      aria-disabled={visuallyDisabled || undefined}
    >
      {children ?? displayLabel}
      {input}
    </label>
  );
}

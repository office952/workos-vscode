import { useRef, type ChangeEvent } from "react";

interface IntakeV6Nest2SvgUploaderProps {
  label?: string;
  busyLabel?: string;
  busy?: boolean;
  disabled?: boolean;
  buttonClassName?: string;
  inputTestId?: string;
  buttonTestId?: string;
  onFileSelected: (file: File) => void | Promise<void>;
}

/**
 * Literal nest2 SvgUploader — label + hidden input, no overlay/guards on the input.
 * Guards belong in the import handler, not on the DOM control.
 */
export default function IntakeV6Nest2SvgUploader({
  label = "Load SVG",
  busyLabel = "Analizez…",
  busy = false,
  disabled = false,
  buttonClassName = "",
  inputTestId = "intake-v6-svg-input",
  buttonTestId = "intake-v6-svg-select-button",
  onFileSelected,
}: IntakeV6Nest2SvgUploaderProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    if (disabled || busy) {
      event.currentTarget.value = "";
      return;
    }
    const file = event.target.files?.[0];
    event.currentTarget.value = "";
    if (!file) {
      return;
    }
    void onFileSelected(file);
  };

  return (
    <label
      className={`inline-flex items-center ${buttonClassName} ${busy || disabled ? "opacity-70 cursor-not-allowed" : "cursor-pointer"}`}
      data-testid={buttonTestId}
      aria-disabled={disabled || busy}
    >
      {busy ? busyLabel : label}
      <input
        ref={inputRef}
        type="file"
        accept=".svg,image/svg+xml"
        hidden
        disabled={disabled || busy}
        data-testid={inputTestId}
        onChange={handleChange}
      />
    </label>
  );
}




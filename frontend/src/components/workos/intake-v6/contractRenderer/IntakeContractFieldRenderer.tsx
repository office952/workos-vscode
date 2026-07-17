import type { IntakeV6ModularFormFieldBinding } from "@/lib/intakeV6/intakeV6ModularFormContractTypes";
import {
  REVIEW_FIELD_BLOCK_CLASS,
  REVIEW_FIELD_LABEL_CLASS,
  REVIEW_SELECT_CLASS,
} from "../reviewFieldLayout";

const SUPPORTED_TYPES = new Set([
  "text",
  "number",
  "integer",
  "boolean",
  "select",
  "multiselect",
  "readonly",
]);

export interface IntakeContractFieldRendererProps {
  field: IntakeV6ModularFormFieldBinding;
  value: unknown;
  error?: string | null;
  onChange: (next: unknown) => void;
  disabled?: boolean;
}

function labelWithUnit(field: IntakeV6ModularFormFieldBinding): string {
  const label = field.label_ro?.trim() || field.canonical_key;
  const unit = field.unit?.trim();
  return unit ? `${label} (${unit})` : label;
}

function optionsFor(field: IntakeV6ModularFormFieldBinding): { value: string; label: string }[] {
  if (Array.isArray(field.options) && field.options.length > 0) {
    return field.options.map((opt) => ({
      value: String(opt.value),
      label: opt.label_ro || String(opt.value),
    }));
  }
  if (Array.isArray(field.option_values) && field.option_values.length > 0) {
    return field.option_values.map((value) => ({
      value: String(value),
      label: String(value),
    }));
  }
  return [];
}

export default function IntakeContractFieldRenderer({
  field,
  value,
  error,
  onChange,
  disabled = false,
}: IntakeContractFieldRendererProps) {
  const fieldType = (field.field_type || "").trim().toLowerCase();
  const readOnly = Boolean(field.read_only) || fieldType === "readonly";
  const testId = `intake-contract-field-${field.canonical_key}`;

  if (!SUPPORTED_TYPES.has(fieldType)) {
    return (
      <label className={REVIEW_FIELD_BLOCK_CLASS} data-testid={testId}>
        <span className={REVIEW_FIELD_LABEL_CLASS}>{labelWithUnit(field)}</span>
        <p className="text-[11px] text-amber-300" data-testid={`${testId}-unsupported`}>
          Tip de câmp nesuportat de rendererul generic: {field.field_type || "lipsa"}
        </p>
      </label>
    );
  }

  if (fieldType === "boolean") {
    return (
      <label className={`${REVIEW_FIELD_BLOCK_CLASS} flex items-center gap-2`} data-testid={testId}>
        <input
          type="checkbox"
          className="h-4 w-4"
          checked={Boolean(value)}
          disabled={disabled || readOnly}
          onChange={(event) => onChange(event.target.checked)}
          data-testid={`${testId}-input`}
        />
        <span className={REVIEW_FIELD_LABEL_CLASS}>
          {labelWithUnit(field)}
          {field.required ? " *" : ""}
        </span>
        {error ? <span className="text-[11px] text-red-300">{error}</span> : null}
      </label>
    );
  }

  if (fieldType === "select") {
    const options = optionsFor(field);
    const stringValue = value == null || value === "" ? "" : String(value);
    const hasCurrent = !stringValue || options.some((opt) => opt.value === stringValue);
    return (
      <label className={REVIEW_FIELD_BLOCK_CLASS} data-testid={testId}>
        <span className={REVIEW_FIELD_LABEL_CLASS}>
          {labelWithUnit(field)}
          {field.required ? " *" : ""}
        </span>
        <select
          className={REVIEW_SELECT_CLASS}
          value={stringValue}
          disabled={disabled || readOnly}
          onChange={(event) => {
            const next = event.target.value;
            if (next === "") {
              onChange(null);
              return;
            }
            // Numeric select values when unit implies a number.
            if (field.unit === "W" || field.unit === "mm" || field.unit === "m2") {
              const parsed = Number(next);
              onChange(Number.isFinite(parsed) ? parsed : next);
              return;
            }
            onChange(next);
          }}
          data-testid={`${testId}-input`}
        >
          <option value="">—</option>
          {!hasCurrent && stringValue ? (
            <option value={stringValue}>{stringValue} (compatibilitate)</option>
          ) : null}
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        {error ? <span className="mt-1 block text-[11px] text-red-300">{error}</span> : null}
      </label>
    );
  }

  if (fieldType === "number" || fieldType === "integer") {
    const numeric =
      value == null || value === ""
        ? ""
        : typeof value === "number"
          ? String(value)
          : String(value);
    return (
      <label className={REVIEW_FIELD_BLOCK_CLASS} data-testid={testId}>
        <span className={REVIEW_FIELD_LABEL_CLASS}>
          {labelWithUnit(field)}
          {field.required ? " *" : ""}
        </span>
        <input
          type="number"
          className={REVIEW_SELECT_CLASS}
          value={numeric}
          disabled={disabled || readOnly}
          min={field.min_value ?? undefined}
          max={field.max_value ?? undefined}
          step={fieldType === "integer" ? 1 : "any"}
          onChange={(event) => {
            const raw = event.target.value;
            if (raw === "") {
              onChange(null);
              return;
            }
            const parsed = fieldType === "integer" ? Number.parseInt(raw, 10) : Number(raw);
            onChange(Number.isFinite(parsed) ? parsed : null);
          }}
          data-testid={`${testId}-input`}
        />
        {error ? <span className="mt-1 block text-[11px] text-red-300">{error}</span> : null}
      </label>
    );
  }

  // text + readonly
  return (
    <label className={REVIEW_FIELD_BLOCK_CLASS} data-testid={testId}>
      <span className={REVIEW_FIELD_LABEL_CLASS}>
        {labelWithUnit(field)}
        {field.required ? " *" : ""}
      </span>
      <input
        type="text"
        className={REVIEW_SELECT_CLASS}
        value={value == null ? "" : String(value)}
        disabled={disabled || readOnly}
        readOnly={readOnly}
        onChange={(event) => onChange(event.target.value)}
        data-testid={`${testId}-input`}
      />
      {error ? <span className="mt-1 block text-[11px] text-red-300">{error}</span> : null}
    </label>
  );
}

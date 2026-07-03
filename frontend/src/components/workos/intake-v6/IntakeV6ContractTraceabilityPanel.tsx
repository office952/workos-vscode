import type { IntakeV6ModularFormContractResponse } from "@/lib/intakeV6/intakeV6ModularFormContractTypes";
import { v6 } from "./atoms/intakeV6Presentation";

function isPlainRecord(value: unknown): value is Record<string, unknown> {
  return value != null && typeof value === "object" && !Array.isArray(value);
}

function resolvePathValue(source: Record<string, unknown> | null | undefined, path: string): unknown {
  if (!source || !path) return undefined;
  const parts = path.split(".").filter(Boolean);
  let current: unknown = source;
  for (const part of parts) {
    if (!isPlainRecord(current)) return undefined;
    current = current[part];
  }
  return current;
}

function resolveBindingDisplayValue(
  contract: IntakeV6ModularFormContractResponse | null,
  source: Record<string, unknown> | null | undefined,
  binding: {
    canonical_key: string;
    workspace_path: string;
  },
): unknown {
  const directValue = resolvePathValue(source, binding.workspace_path);
  if (directValue != null && directValue !== "") {
    return directValue;
  }

  const canonicalValues = contract?.evaluation?.canonical_values;
  if (canonicalValues && typeof canonicalValues === "object") {
    const canonicalValue = (canonicalValues as Record<string, unknown>)[binding.canonical_key];
    if (canonicalValue != null && canonicalValue !== "") {
      return canonicalValue;
    }
  }

  return directValue;
}

function formatValue(value: unknown): string {
  if (value == null || value === "") return "Lipsă";
  if (typeof value === "boolean") return value ? "Da" : "Nu";
  if (typeof value === "number") return Number.isInteger(value) ? String(value) : value.toFixed(2);
  if (typeof value === "string") return value;
  if (Array.isArray(value)) return `${value.length} item`;
  if (isPlainRecord(value)) return "Setat";
  return String(value);
}

function isRelevantBinding(binding: {
  field_role?: string | null;
  module_codes?: string[];
  required?: boolean;
}): boolean {
  if (!Array.isArray(binding.module_codes) || binding.module_codes.length === 0) return false;
  return (
    binding.required === true ||
    binding.field_role === "geometry_input" ||
    binding.field_role === "module_activation" ||
    binding.field_role === "module_configuration" ||
    binding.field_role === "derived_quote_input"
  );
}

function resolveInactiveModuleCodes(contract: IntakeV6ModularFormContractResponse | null): Set<string> {
  const inactive = new Set<string>();
  const evaluationStates = Array.isArray(contract?.evaluation?.module_states)
    ? contract.evaluation?.module_states
    : [];

  for (const module of evaluationStates) {
    if (module.state === "inactive" || module.state === "future_reserved") {
      inactive.add(module.module_code);
    }
  }

  const inactiveCodes = Array.isArray(contract?.evaluation?.inactive_module_codes)
    ? contract.evaluation.inactive_module_codes
    : [];
  for (const moduleCode of inactiveCodes) {
    if (typeof moduleCode === "string" && moduleCode.trim()) {
      inactive.add(moduleCode);
    }
  }

  const previewInactive = Array.isArray(contract?.product_definition_preview?.inactive_modules)
    ? contract.product_definition_preview.inactive_modules
    : [];
  for (const module of previewInactive) {
    if (module.state === "inactive" || module.state === "future_reserved") {
      inactive.add(module.module_code);
    }
  }

  return inactive;
}

function shouldDisplayBinding(
  binding: {
    module_codes?: string[];
  },
  inactiveModuleCodes: Set<string>,
): boolean {
  const moduleCodes = Array.isArray(binding.module_codes) ? binding.module_codes.filter(Boolean) : [];
  if (moduleCodes.length === 0) return true;
  return !moduleCodes.every((moduleCode) => inactiveModuleCodes.has(moduleCode));
}

export interface IntakeV6ContractTraceabilityPanelProps {
  contract: IntakeV6ModularFormContractResponse | null;
  loading: boolean;
  error: string | null;
  templateCode?: string | null;
  source: Record<string, unknown> | null | undefined;
  variant?: "review" | "confirm";
}

export default function IntakeV6ContractTraceabilityPanel({
  contract,
  loading,
  error,
  templateCode,
  source,
  variant = "review",
}: IntakeV6ContractTraceabilityPanelProps) {
  const inactiveModuleCodes = resolveInactiveModuleCodes(contract);
  const bindings = Array.isArray(contract?.field_bindings)
    ? contract.field_bindings
        .filter(isRelevantBinding)
        .filter((binding) => shouldDisplayBinding(binding, inactiveModuleCodes))
    : [];
  const downstream = Array.isArray(contract?.downstream_linkages) ? contract.downstream_linkages : [];

  return (
    <div
      className={`${v6.cardCompact} ${variant === "confirm" ? "" : "mb-4"}`}
      data-testid={`intake-v6-contract-traceability-${variant}`}
    >
      <div className="mb-2">
        <h3 className={v6.sectionTitle}>Trasabilitate contract</h3>
        <p className={v6.sectionDesc}>
          {variant === "confirm"
            ? "Verifică valorile confirmate și impactul lor înainte de draftul intern."
            : "Arată ce valori confirmate alimentează contractul modular și ce impact downstream pregătesc."}
        </p>
        {templateCode ? <p className={`${v6.helper} mt-1`}>Șablon urmărit: {templateCode}</p> : null}
      </div>

      {loading ? (
        <p className={v6.helper} data-testid={`intake-v6-contract-traceability-loading-${variant}`}>
          Încarc trasabilitatea contractului…
        </p>
      ) : null}

      {error ? (
        <p className="text-[11px] text-red-300" data-testid={`intake-v6-contract-traceability-error-${variant}`}>
          {error}
        </p>
      ) : null}

      {contract ? (
        <div className="space-y-2" data-testid={`intake-v6-contract-traceability-body-${variant}`}>
          {bindings.map((binding) => {
            const value = resolveBindingDisplayValue(contract, source, binding);
            const impactedLinks = downstream.filter((link) =>
              Array.isArray(binding.module_codes) && binding.module_codes.includes(link.module_code),
            );
            const inventoryCount = impactedLinks.reduce(
              (sum, link) => sum + (link.inventory_material_roles?.length ?? 0),
              0,
            );
            const pricingCount = impactedLinks.reduce(
              (sum, link) => sum + (link.pricing_inputs?.length ?? 0),
              0,
            );
            const executionCount = impactedLinks.reduce(
              (sum, link) => sum + (link.execution_task_outputs?.length ?? 0),
              0,
            );

            return (
              <div
                key={`${binding.workspace_path}-${binding.canonical_key}`}
                className="rounded border border-[#2A3548] bg-[#0A0F1A] px-3 py-2"
                data-testid={`intake-v6-contract-traceability-row-${binding.canonical_key}`}
              >
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div className="min-w-0">
                    <p className="text-[11px] font-semibold text-slate-200">
                      {binding.label_ro ?? binding.canonical_key}
                    </p>
                    <p className="text-[10px] text-slate-500">{binding.workspace_path}</p>
                  </div>
                  <span
                    className={`rounded border px-2 py-0.5 text-[10px] ${
                      value == null || value === ""
                        ? "border-amber-500/30 bg-amber-500/10 text-amber-200"
                        : "border-emerald-500/30 bg-emerald-500/10 text-emerald-200"
                    }`}
                    data-testid={`intake-v6-contract-traceability-value-${binding.canonical_key}`}
                  >
                    {formatValue(value)}
                  </span>
                </div>

                <div className="mt-2 flex flex-wrap gap-2 text-[10px] text-slate-400">
                  <span>module: {(binding.module_codes ?? []).join(", ")}</span>
                  <span>pricing: {pricingCount}</span>
                  <span>taskuri: {executionCount}</span>
                  <span>inventar: {inventoryCount}</span>
                </div>

                {binding.derivation_rule ? (
                  <p className="mt-2 text-[10px] text-sky-200">Derivare: {binding.derivation_rule}</p>
                ) : null}
              </div>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}
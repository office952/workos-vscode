import type {
  IntakeV6ModularFormContractResponse,
  IntakeV6ModularFormFieldBinding,
  IntakeV6RenderSection,
} from "@/lib/intakeV6/intakeV6ModularFormContractTypes";
import { evaluateVisibilityRule } from "@/lib/intakeV6/contractRenderer/visibilityRules";
import {
  finishSetupKeyFromPath,
  getByWorkspacePath,
  type WorkspacePathRoot,
} from "@/lib/intakeV6/contractRenderer/workspacePathAccess";
import IntakeV6ReviewSectionShell from "../atoms/IntakeV6ReviewSectionShell";
import IntakeContractFieldRenderer from "./IntakeContractFieldRenderer";

export interface IntakeContractSectionRendererProps {
  section: IntakeV6RenderSection;
  contract: IntakeV6ModularFormContractResponse;
  /** Workspace-shaped root used for path reads and visibility (e.g. { finish_setup: form }). */
  valueRoot: WorkspacePathRoot;
  onFieldChange: (workspacePath: string, value: unknown) => void;
  errors?: Record<string, string | null | undefined>;
  disabled?: boolean;
  compact?: boolean;
}

function bindingMap(
  contract: IntakeV6ModularFormContractResponse,
): Map<string, IntakeV6ModularFormFieldBinding> {
  const map = new Map<string, IntakeV6ModularFormFieldBinding>();
  for (const binding of contract.field_bindings ?? []) {
    if (binding.canonical_key) {
      map.set(binding.canonical_key, binding);
    }
  }
  return map;
}

export default function IntakeContractSectionRenderer({
  section,
  contract,
  valueRoot,
  onFieldChange,
  errors = {},
  disabled = false,
  compact = true,
}: IntakeContractSectionRendererProps) {
  if (!evaluateVisibilityRule(section.visibility, valueRoot)) {
    return null;
  }

  const bindings = bindingMap(contract);
  const fields = (section.field_keys ?? [])
    .map((key) => bindings.get(key))
    .filter((field): field is IntakeV6ModularFormFieldBinding => Boolean(field));

  return (
    <IntakeV6ReviewSectionShell
      title={section.title_ro}
      description={section.description_ro ?? undefined}
      testId={`intake-contract-section-${section.section_key}`}
      compact={compact}
    >
      <div className="grid gap-3 sm:grid-cols-2" data-testid={`intake-contract-section-fields-${section.section_key}`}>
        {fields.map((field) => {
          if (!evaluateVisibilityRule(field.visibility, valueRoot)) {
            return null;
          }
          const access = getByWorkspacePath(valueRoot, field.workspace_path);
          const value = access.ok ? access.value : undefined;
          const finishKey = finishSetupKeyFromPath(field.workspace_path);
          const error = errors[field.canonical_key] ?? (finishKey ? errors[finishKey] : null);
          return (
            <IntakeContractFieldRenderer
              key={field.canonical_key}
              field={field}
              value={value}
              error={error}
              disabled={disabled}
              onChange={(next) => onFieldChange(field.workspace_path, next)}
            />
          );
        })}
      </div>
    </IntakeV6ReviewSectionShell>
  );
}

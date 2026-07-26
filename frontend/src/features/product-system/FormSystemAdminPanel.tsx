import { AlertTriangle, ClipboardList, Eye, FileText, Layers, ShieldAlert } from "lucide-react";
import type { ProductDefinitionPreview } from "@/api/productDefinitionPreview";
import type { IntakeV6ModularFormContractResponse } from "@/lib/intakeV6/intakeV6ModularFormContractTypes";
import { useFormSystemAdminData } from "@/features/product-system/useFormSystemAdminData";
import { CostBomPreviewPanel } from "@/features/product-system/CostBomPreviewPanel";

function readinessBadgeClass(status: string): string {
  switch (status) {
    case "ready":
      return "bg-emerald-900/20 text-emerald-300 border-emerald-700/40";
    case "blocked":
      return "bg-red-900/20 text-red-300 border-red-700/40";
    default:
      return "bg-amber-900/20 text-amber-300 border-amber-700/40";
  }
}

function moduleStateClass(state: string): string {
  switch (state) {
    case "always_on":
    case "active":
    case "conditional_active":
      return "text-emerald-300";
    case "inactive":
    case "future_reserved":
      return "text-wo-text-muted";
    default:
      return "text-amber-300";
  }
}

function ReadOnlyBanner() {
  return (
    <div
      className="flex items-start gap-2 rounded-lg border border-sky-800/40 bg-sky-900/15 px-3 py-2.5 text-[11px] text-sky-200"
      data-testid="form-system-read-only-banner"
    >
      <Eye className="w-4 h-4 shrink-0 mt-0.5" />
      <div>
        <p className="font-semibold">Form System — read-only (Step 6 / 7D)</p>
        <p className="text-sky-300/80 mt-0.5">
          Product Compiler · Definiție (preview) · nu este preț final · nu generează taskuri · nu creează order
        </p>
      </div>
    </div>
  );
}

function FormContractSummary({
  formContract,
  preview,
}: {
  formContract: IntakeV6ModularFormContractResponse | null;
  preview: ProductDefinitionPreview | null;
}) {
  if (!formContract) {
    return (
      <div className="rounded-lg border border-slate-700/40 bg-slate-900/30 px-3 py-2 text-[11px] text-wo-text-muted">
        Form contract indisponibil pentru acest template.
      </div>
    );
  }
  const orphanCount = formContract.orphan_fields_audit?.length ?? 0;
  const warningCount = (formContract.summary.warnings?.length ?? 0) + (preview?.warnings.length ?? 0);
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-2" data-testid="form-system-contract-summary">
      <div className="rounded-lg border border-wo-border-subtle bg-wo-surface-raised px-3 py-2">
        <p className="text-[9px] uppercase text-wo-text-muted font-bold">Bindings</p>
        <p className="text-[14px] font-bold text-wo-text-primary">{formContract.summary.field_binding_count}</p>
      </div>
      <div className="rounded-lg border border-wo-border-subtle bg-wo-surface-raised px-3 py-2">
        <p className="text-[9px] uppercase text-wo-text-muted font-bold">Module ACTIVE</p>
        <p className="text-[14px] font-bold text-wo-text-primary">{formContract.summary.active_module_count}</p>
      </div>
      <div className="rounded-lg border border-wo-border-subtle bg-wo-surface-raised px-3 py-2">
        <p className="text-[9px] uppercase text-wo-text-muted font-bold">Orphans</p>
        <p className="text-[14px] font-bold text-wo-text-primary">{orphanCount}</p>
      </div>
      <div className="rounded-lg border border-wo-border-subtle bg-wo-surface-raised px-3 py-2">
        <p className="text-[9px] uppercase text-wo-text-muted font-bold">Warnings</p>
        <p className="text-[14px] font-bold text-amber-300">{warningCount}</p>
      </div>
    </div>
  );
}

function FieldBindingsTable({ formContract }: { formContract: IntakeV6ModularFormContractResponse | null }) {
  if (!formContract?.field_bindings?.length) return null;
  return (
    <div className="space-y-2" data-testid="form-system-field-bindings">
      <div className="flex items-center gap-2">
        <FileText className="w-4 h-4 text-purple-400" />
        <h4 className="text-[13px] font-bold text-wo-text-primary">Field bindings</h4>
      </div>
      <div className="overflow-x-auto rounded-lg border border-wo-border-subtle">
        <table className="w-full text-[10px]">
          <thead className="bg-wo-surface-raised text-wo-text-muted uppercase">
            <tr>
              <th className="text-left px-2 py-1.5 font-bold">Key</th>
              <th className="text-left px-2 py-1.5 font-bold">Module</th>
              <th className="text-left px-2 py-1.5 font-bold">Req</th>
              <th className="text-left px-2 py-1.5 font-bold">PD key</th>
              <th className="text-left px-2 py-1.5 font-bold">Derived</th>
            </tr>
          </thead>
          <tbody>
            {formContract.field_bindings.map((row) => (
              <tr key={row.canonical_key} className="border-t border-wo-border-subtle text-wo-text-secondary">
                <td className="px-2 py-1.5 font-mono">{row.canonical_key}</td>
                <td className="px-2 py-1.5">{row.module_codes.join(", ") || "—"}</td>
                <td className="px-2 py-1.5">{row.required ? "da" : "nu"}</td>
                <td className="px-2 py-1.5 font-mono text-[9px]">
                  {row.product_definition_keys.join(", ") || "—"}
                </td>
                <td className="px-2 py-1.5">
                  {row.field_role === "derived_quote_input"
                    ? row.derived_from ?? "derived"
                    : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ModuleActivationMap({ preview }: { preview: ProductDefinitionPreview | null }) {
  if (!preview) return null;
  const all = [
    ...preview.selected_modules.map((m) => ({ ...m, bucket: "selected" })),
    ...preview.optional_modules.map((m) => ({ ...m, bucket: "optional" })),
    ...preview.inactive_modules.map((m) => ({ ...m, bucket: "inactive" })),
  ];
  const seen = new Set<string>();
  const unique = all.filter((m) => {
    if (seen.has(m.module_code)) return false;
    seen.add(m.module_code);
    return true;
  });

  return (
    <div className="space-y-2" data-testid="form-system-module-activation">
      <div className="flex items-center gap-2">
        <Layers className="w-4 h-4 text-violet-400" />
        <h4 className="text-[13px] font-bold text-wo-text-primary">Module activation map</h4>
      </div>
      <div className="space-y-1">
        {unique.map((mod) => (
          <div
            key={mod.module_code}
            className="flex flex-wrap items-center gap-x-2 gap-y-1 rounded-lg border border-wo-border-subtle bg-wo-surface-inset px-3 py-2 text-[11px]"
          >
            <span className="font-mono font-bold text-wo-text-primary">{mod.module_code}</span>
            <span className="text-wo-text-muted">·</span>
            <span className="text-wo-text-muted">{mod.activation_kind}</span>
            <span className="text-wo-text-muted">·</span>
            <span className={`font-semibold ${moduleStateClass(mod.state)}`}>{mod.state}</span>
            <span className="text-wo-text-muted">·</span>
            <span className="text-wo-text-muted">{mod.bucket}</span>
            {mod.missing_fields.length > 0 ? (
              <span className="text-amber-300">missing: {mod.missing_fields.join(", ")}</span>
            ) : null}
          </div>
        ))}
      </div>
    </div>
  );
}

function ProductDefinitionPreviewSection({ preview }: { preview: ProductDefinitionPreview | null }) {
  if (!preview) return null;
  return (
    <div className="space-y-3" data-testid="form-system-pd-preview">
      <div className="flex items-center gap-2">
        <ClipboardList className="w-4 h-4 text-emerald-400" />
        <h4 className="text-[13px] font-bold text-wo-text-primary">Product Compiler · Definiție</h4>
        <span className="text-[10px] text-wo-text-muted">intern: ProductDefinition preview</span>
        <span
          className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded border ${readinessBadgeClass(preview.validation.readiness_status)}`}
          data-testid="form-system-readiness-status"
        >
          {preview.validation.readiness_status}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-2 text-[10px]">
        <div className="rounded border border-wo-border-subtle bg-wo-surface-raised px-2 py-1.5">
          <span className="text-wo-text-muted">Componente · </span>
          <span className="text-wo-text-primary font-bold">{preview.components.length}</span>
        </div>
        <div className="rounded border border-wo-border-subtle bg-wo-surface-raised px-2 py-1.5">
          <span className="text-wo-text-muted">Materiale · </span>
          <span className="text-wo-text-primary font-bold">{preview.material_roles.length}</span>
        </div>
        <div className="rounded border border-wo-border-subtle bg-wo-surface-raised px-2 py-1.5">
          <span className="text-wo-text-muted">Operații · </span>
          <span className="text-wo-text-primary font-bold">{preview.operation_roles.length}</span>
        </div>
      </div>

      {preview.validation.missing_required_fields.length > 0 ? (
        <div className="rounded-lg border border-amber-700/40 bg-amber-900/10 px-3 py-2 text-[11px] text-amber-200">
          <p className="font-bold flex items-center gap-1.5">
            <ShieldAlert className="w-3.5 h-3.5" /> Missing required fields
          </p>
          <p className="mt-1 font-mono text-[10px]">{preview.validation.missing_required_fields.join(", ")}</p>
        </div>
      ) : null}

      {preview.warnings.length > 0 ? (
        <div className="space-y-1">
          <p className="text-[10px] font-bold uppercase text-wo-text-muted">Warnings</p>
          {preview.warnings.slice(0, 8).map((w) => (
            <div
              key={w}
              className="rounded border border-amber-700/30 bg-amber-900/10 px-2 py-1 text-[10px] text-amber-200"
            >
              {w}
            </div>
          ))}
        </div>
      ) : null}

      {preview.provenance.length > 0 ? (
        <div className="space-y-1">
          <p className="text-[10px] font-bold uppercase text-wo-text-muted">Provenance</p>
          {preview.provenance.map((p) => (
            <div key={p.key} className="text-[10px] text-wo-text-muted font-mono">
              {p.key}: {p.detail}
            </div>
          ))}
        </div>
      ) : null}

      <details className="rounded-lg border border-wo-border-subtle bg-wo-surface-inset">
        <summary className="cursor-pointer px-3 py-2 text-[11px] font-semibold text-wo-text-secondary">
          Canonical values (JSON)
        </summary>
        <pre className="px-3 pb-3 text-[9px] text-wo-text-muted overflow-x-auto max-h-48">
          {JSON.stringify(preview.canonical_values, null, 2)}
        </pre>
      </details>
    </div>
  );
}

export function FormSystemAdminPanel({ templateCode }: { templateCode: string }) {
  const { preview, formContract, status, error, isLoading } = useFormSystemAdminData(templateCode);

  if (isLoading) {
    return <div className="text-[11px] text-wo-text-muted">Se încarcă Form System…</div>;
  }

  if (status === "unavailable") {
    return (
      <div className="space-y-3">
        <ReadOnlyBanner />
        <div className="rounded-lg border border-amber-700/40 bg-amber-900/10 px-3 py-2 text-[11px] text-amber-200">
          <AlertTriangle className="w-4 h-4 inline mr-1.5" />
          {error ?? "Form System indisponibil pentru acest template."}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4" data-testid="form-system-admin-panel">
      <ReadOnlyBanner />
      <FormContractSummary formContract={formContract} preview={preview} />
      <FieldBindingsTable formContract={formContract} />
      <ModuleActivationMap preview={preview} />
      <ProductDefinitionPreviewSection preview={preview} />
      <CostBomPreviewPanel templateCode={templateCode} />
    </div>
  );
}

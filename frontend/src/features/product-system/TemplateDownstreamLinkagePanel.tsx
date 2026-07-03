import { useModularFormContract } from "@/lib/intakeV6/useModularFormContract";
import {
  OWNER_VALID_ACTIVE_TEMPLATE_CODE,
  isOwnerValidActiveTemplate,
  resolveRuntimeTemplateCode,
} from "@/lib/activeTemplateScope";

function isSvgAnalyzerBinding(binding: {
  canonical_key: string;
  workspace_path: string;
  field_role?: string | null;
  module_codes?: string[];
}): boolean {
  if (binding.field_role === "geometry_input") return true;
  if (binding.workspace_path.startsWith("svg_source.")) return true;
  return Boolean(binding.module_codes?.includes("geometry_svg"));
}

function statusLabel(status: string | null | undefined): string {
  switch (status) {
    case "linked":
      return "linked";
    case "partial":
      return "partial";
    case "post_materialization_only":
      return "post-materialize";
    case "future":
      return "future";
    default:
      return "n/a";
  }
}

function statusClass(status: string | null | undefined): string {
  switch (status) {
    case "linked":
      return "border-emerald-500/30 bg-emerald-500/10 text-emerald-300";
    case "partial":
      return "border-amber-500/30 bg-amber-500/10 text-amber-300";
    case "post_materialization_only":
      return "border-sky-500/30 bg-sky-500/10 text-sky-300";
    case "future":
      return "border-slate-500/30 bg-slate-500/10 text-slate-300";
    default:
      return "border-slate-700/40 bg-slate-900/40 text-slate-500";
  }
}

function definitionReadinessClass(status: string | null | undefined): string {
  switch (status) {
    case "ready":
      return "border-emerald-500/30 bg-emerald-500/10 text-emerald-300";
    case "blocked":
      return "border-red-500/30 bg-red-500/10 text-red-300";
    default:
      return "border-amber-500/30 bg-amber-500/10 text-amber-300";
  }
}

function moduleStateClass(state: string | null | undefined): string {
  switch (state) {
    case "always_on":
    case "active":
    case "conditional_active":
      return "border-emerald-500/30 bg-emerald-500/10 text-emerald-300";
    case "pending":
      return "border-amber-500/30 bg-amber-500/10 text-amber-300";
    case "inactive":
      return "border-slate-500/30 bg-slate-500/10 text-slate-300";
    case "future_reserved":
      return "border-sky-500/30 bg-sky-500/10 text-sky-300";
    default:
      return "border-slate-700/40 bg-slate-900/40 text-slate-500";
  }
}

export function TemplateDownstreamLinkagePanel({
  templateCode,
  workspaceId,
  variant = "product-system",
  contractOverride,
  loadingOverride,
  errorOverride,
}: {
  templateCode: string | null | undefined;
  workspaceId?: string | null;
  variant?: "product-system" | "pricing" | "intake-v6";
  contractOverride?: ReturnType<typeof useModularFormContract>["contract"];
  loadingOverride?: boolean;
  errorOverride?: string | null;
}) {
  const runtimeTemplateCode = resolveRuntimeTemplateCode(templateCode);
  const canLoad = isOwnerValidActiveTemplate(runtimeTemplateCode);
  const contractTemplateCode = canLoad
    ? runtimeTemplateCode
    : variant === "intake-v6"
      ? OWNER_VALID_ACTIVE_TEMPLATE_CODE
      : null;
  const effectiveWorkspaceId = variant === "intake-v6" ? workspaceId ?? null : null;
  const hookState = useModularFormContract(contractTemplateCode, effectiveWorkspaceId);
  const contract = contractOverride ?? hookState.contract;
  const loading = loadingOverride ?? hookState.loading;
  const error = errorOverride ?? hookState.error;
  const modules = Array.isArray(contract?.modules) ? contract.modules : [];
  const downstreamLinkages = Array.isArray(contract?.downstream_linkages)
    ? contract.downstream_linkages
    : [];
  const fieldBindings = Array.isArray(contract?.field_bindings) ? contract.field_bindings : [];
  const svgAnalyzerBindings = fieldBindings.filter(isSvgAnalyzerBinding);
  const triggerAlignments = Array.isArray(contract?.trigger_alignments)
    ? contract.trigger_alignments
    : [];
  const evaluation = contract?.evaluation ?? null;
  const evaluationModuleStates = Array.isArray(evaluation?.module_states) ? evaluation.module_states : [];
  const evaluationStateByModule = new Map(
    evaluationModuleStates.map((module) => [module.module_code, module]),
  );
  const definitionPreview = contract?.product_definition_preview ?? null;
  const definitionSelectedModules = Array.isArray(definitionPreview?.selected_modules)
    ? definitionPreview.selected_modules
    : [];
  const definitionComponents = Array.isArray(definitionPreview?.components)
    ? definitionPreview.components
    : [];
  const definitionMaterials = Array.isArray(definitionPreview?.material_roles)
    ? definitionPreview.material_roles
    : [];
  const definitionOperations = Array.isArray(definitionPreview?.operation_roles)
    ? definitionPreview.operation_roles
    : [];
  const definitionValidation = definitionPreview?.validation;
  const summary = contract?.summary ?? {
    template_code: contractTemplateCode ?? runtimeTemplateCode,
    active_module_count: modules.length,
  };

  if (!contractTemplateCode) return null;

  return (
    <section
      className="rounded-xl border border-[#1E293B] bg-[#0D1321]/80 p-4"
      data-testid={`template-downstream-linkage-${variant}`}
    >
      <div className="mb-3">
        <h3 className="text-[12px] font-bold uppercase tracking-wide text-slate-200">
          Linkage downstream template
        </h3>
        <p className="mt-1 text-[11px] text-slate-400">
          {variant === "intake-v6"
            ? "Contractul modular folosit in Pasul 1 pentru SVG analyzer si pentru propagarea controlata catre inventar, pricing, taskuri, angajati si utilaje."
            : "Contract read-only intre Intake V6, inventar, pricing, taskuri, angajati si utilaje pentru template-ul activ."}
        </p>
      </div>

      {loading ? <p className="text-[11px] text-slate-500">Incarc linkage modular...</p> : null}
      {error ? <p className="text-[11px] text-red-300">{error}</p> : null}

      {contract ? (
        <div className="space-y-3">
          <p className="text-[10px] text-slate-500" data-testid={`template-downstream-linkage-summary-${variant}`}>
            Template runtime: {summary.template_code} · module active: {summary.active_module_count ?? modules.length}
            {!canLoad && variant === "intake-v6" ? " · fallback pilot scope" : ""}
          </p>

          {evaluation ? (
            <div
              className="rounded-lg border border-sky-500/20 bg-sky-500/5 px-3 py-2"
              data-testid={`template-downstream-linkage-contract-evaluation-${variant}`}
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="text-[11px] font-semibold text-sky-200">Contract evaluat</p>
                <span
                  className={`rounded border px-2 py-0.5 text-[10px] ${definitionReadinessClass(
                    evaluation.readiness_status,
                  )}`}
                >
                  {evaluation.readiness_status ?? "partial"}
                </span>
              </div>
              <p className="mt-1 text-[10px] text-slate-300">
                module selectate {evaluation.selected_module_codes?.length ?? 0} · opționale {evaluation.optional_module_codes?.length ?? 0} · inactive {evaluation.inactive_module_codes?.length ?? 0}
              </p>
              <p className="mt-1 text-[10px] text-slate-400">
                sursă {evaluation.source_payload_type ?? "template_only"}
                {evaluation.workspace_id ? ` · workspace ${evaluation.workspace_id}` : ""}
                {evaluation.missing_required_fields?.length
                  ? ` · lipsă ${evaluation.missing_required_fields.length} câmpuri canonice`
                  : " · contract evaluat fără lipsuri canonice"}
              </p>
            </div>
          ) : null}

          {definitionPreview ? (
            <div
              className="rounded-lg border border-emerald-500/20 bg-emerald-500/5 px-3 py-2"
              data-testid={`template-downstream-linkage-product-definition-${variant}`}
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="text-[11px] font-semibold text-emerald-200">ProductDefinition v1</p>
                <span
                  className={`rounded border px-2 py-0.5 text-[10px] ${definitionReadinessClass(
                    definitionValidation?.readiness_status,
                  )}`}
                >
                  {definitionValidation?.readiness_status ?? "partial"}
                </span>
              </div>
              <p className="mt-1 text-[10px] text-slate-300">
                module selectate {definitionSelectedModules.length} · componente {definitionComponents.length} · materiale {definitionMaterials.length} · operații {definitionOperations.length}
              </p>
              <p className="mt-1 text-[10px] text-slate-400">
                sursă {definitionPreview.source_context?.source_payload_type ?? "template_only"}
                {definitionPreview.source_context?.workspace_id
                  ? ` · workspace ${definitionPreview.source_context.workspace_id}`
                  : ""}
                {definitionValidation?.missing_required_fields?.length
                  ? ` · lipsă ${definitionValidation.missing_required_fields.length} câmpuri cerute`
                  : " · fără lipsuri critice în preview"}
              </p>
            </div>
          ) : null}

          {variant === "intake-v6" ? (
            <div
              className="rounded-lg border border-cyan-500/20 bg-cyan-500/5 px-3 py-2"
              data-testid="template-downstream-linkage-svg-bindings-intake-v6"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="text-[11px] font-semibold text-cyan-200">Pasul 1 · SVG analyzer contract</p>
                <span className="text-[10px] text-cyan-300">
                  {svgAnalyzerBindings.length} binding{svgAnalyzerBindings.length === 1 ? "" : "-uri"} geometry/svg
                </span>
              </div>
              <div className="mt-2 flex flex-wrap gap-2">
                {svgAnalyzerBindings.map((binding) => (
                  <span
                    key={binding.canonical_key}
                    className="rounded border border-cyan-500/20 bg-[#0D1321] px-2 py-1 text-[10px] text-slate-200"
                    data-testid={`template-downstream-linkage-svg-binding-${binding.canonical_key}`}
                  >
                    {binding.label_ro ?? binding.canonical_key}
                  </span>
                ))}
              </div>

              {triggerAlignments.length > 0 ? (
                <div className="mt-3 space-y-2">
                  {triggerAlignments.map((alignment) => (
                    <div
                      key={`${alignment.module_code}-${alignment.module_link_trigger_field}`}
                      className="rounded border border-amber-500/20 bg-amber-500/5 px-2 py-2 text-[10px] text-amber-100"
                      data-testid={`template-downstream-linkage-trigger-${alignment.module_code}`}
                    >
                      <span className="font-semibold text-amber-200">{alignment.module_code}</span>
                      {" · "}
                      trigger DB <span className="font-mono">{alignment.module_link_trigger_field}</span>
                      {" <- "}
                      Intake <span className="font-mono">{alignment.canonical_intake_field}</span>
                      {alignment.module_code === "structura_suport" ? (
                        <p className="mt-1 text-[10px] leading-snug text-amber-100/90">
                          Support and mounting are separate decisions. Current template link uses mounting_system as support trigger; contract needs alignment before Product Truth payload.
                        </p>
                      ) : null}
                    </div>
                  ))}
                </div>
              ) : null}
            </div>
          ) : null}

          <div className="space-y-2">
            {downstreamLinkages.map((link) => (
              (() => {
                const evaluatedModule = evaluationStateByModule.get(link.module_code);
                return (
              <div
                key={link.module_code}
                className="rounded-lg border border-[#243044] bg-[#111827]/70 px-3 py-2"
                data-testid={`template-downstream-linkage-row-${link.module_code}`}
              >
                <div className="flex flex-wrap items-center gap-2 justify-between">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="text-[11px] font-semibold text-slate-200">{link.module_code}</p>
                      {evaluatedModule ? (
                        <span className={`rounded border px-2 py-0.5 text-[10px] ${moduleStateClass(evaluatedModule.state)}`}>
                          {evaluatedModule.state}
                        </span>
                      ) : null}
                    </div>
                    <p className="text-[10px] text-slate-500">
                      inventar {link.inventory_material_roles?.length ?? 0} · pricing {link.pricing_inputs?.length ?? 0} · taskuri {link.execution_task_outputs?.length ?? 0}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    <span className={`rounded border px-2 py-0.5 text-[10px] ${statusClass(link.workcenter_routing_status)}`}>
                      WC {statusLabel(link.workcenter_routing_status)}
                    </span>
                    <span className={`rounded border px-2 py-0.5 text-[10px] ${statusClass(link.machine_linkage_status)}`}>
                      utilaje {statusLabel(link.machine_linkage_status)}
                    </span>
                    <span className={`rounded border px-2 py-0.5 text-[10px] ${statusClass(link.employee_assignment_status)}`}>
                      angajati {statusLabel(link.employee_assignment_status)}
                    </span>
                  </div>
                </div>
                {link.linkage_notes && link.linkage_notes.length > 0 ? (
                  <p className="mt-2 text-[10px] text-slate-400">
                    {link.linkage_notes[0]}
                    {evaluatedModule?.missing_fields?.length
                      ? ` · lipsă ${evaluatedModule.missing_fields.join(", ")}`
                      : ""}
                  </p>
                ) : null}
              </div>
                );
              })()
            ))}
          </div>
        </div>
      ) : null}
    </section>
  );
}
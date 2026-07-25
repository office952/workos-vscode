import {
  buildVolumetricCantProductionModules,
  isVolumetricCantLateralComponent,
  VOLUMETRIC_COMPONENT_PRODUCTION_HINTS,
  VOLUMETRIC_PRODUCTION_RULES,
  getVolumetricOperationalContractBadges,
} from "@/features/product-system/volumetricLettersProduction";
import type { ProductTemplateComponent } from "@/lib/api";

export const VOLUMETRIC_PRODUCTION_FLOW_ONE_LINE =
  "față plexiglas 3mm PMMA - opal → volum aluminiu → capac Forex → LED → finisaj";

/** One-line flux summary for the structure editor — full rules live in Informații generale. */
export function VolumetricProductionFlowSummary() {
  return (
    <div className="rounded-lg border border-blue-800/25 bg-blue-950/15 px-3 py-2">
      <p className="text-[10px] text-slate-400 leading-relaxed">
        <span className="font-bold uppercase tracking-wide text-blue-300/90">Flux: </span>
        {VOLUMETRIC_PRODUCTION_FLOW_ONE_LINE}
      </p>
    </div>
  );
}

export function VolumetricProductionGuidancePanel({ compact = false }: { compact?: boolean }) {
  const dependencyBadges = getVolumetricOperationalContractBadges();

  return (
    <div
      className={
        compact
          ? "rounded-lg border border-blue-800/30 bg-blue-950/20 px-3 py-2.5 space-y-2"
          : "rounded-xl border border-blue-800/30 bg-blue-950/15 px-4 py-3 space-y-3"
      }
    >
      <div>
        <p className="text-[10px] font-bold uppercase tracking-wide text-blue-300">
          Flux producție · litere volumetrice
        </p>
        {!compact && (
          <p className="text-[9px] text-slate-500 mt-0.5 leading-relaxed">
            Referință operator — valorile concrete (651, 8500, RAL) se iau din specificația intake / ofertă.
          </p>
        )}
      </div>
      <ul className="space-y-2">
        {VOLUMETRIC_PRODUCTION_RULES.map((rule) => (
          <li key={rule.title} className="text-[10px] leading-relaxed">
            <span className="font-semibold text-slate-200">{rule.title}: </span>
            <span className="text-slate-400">{rule.body}</span>
          </li>
        ))}
      </ul>

      <div className="pt-1 border-t border-blue-900/30" data-testid="volumetric-operational-contract-badges">
        <p className="text-[9px] font-semibold uppercase tracking-wide text-blue-300/80">
          Ancore contract operațional
        </p>
        <div className="mt-1 flex flex-wrap gap-1">
          {dependencyBadges.map((badge) => (
            <span
              key={badge}
              className="px-1.5 py-0.5 rounded border border-blue-900/50 bg-blue-950/30 text-[9px] text-blue-200/90"
            >
              {badge}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

export function VolumetricComponentProductionHint({
  componentId,
}: {
  componentId: string;
}) {
  const hint = VOLUMETRIC_COMPONENT_PRODUCTION_HINTS[componentId];
  if (!hint) return null;
  return (
    <p className="text-[10px] text-blue-300/90 leading-relaxed px-1 pb-1 border-b border-[#1E293B]/80 mb-2">
      {hint}
    </p>
  );
}

function moduleStatusTone(status: "covered" | "partial" | "missing"): string {
  switch (status) {
    case "covered":
      return "border-emerald-700/40 bg-emerald-950/15 text-emerald-300";
    case "partial":
      return "border-amber-700/40 bg-amber-950/15 text-amber-300";
    default:
      return "border-rose-700/40 bg-rose-950/15 text-rose-300";
  }
}

function moduleStatusLabel(status: "covered" | "partial" | "missing"): string {
  switch (status) {
    case "covered":
      return "Acoperit";
    case "partial":
      return "Parțial";
    default:
      return "Lipsă";
  }
}

export function VolumetricCantProductionModulesPanel({
  component,
  components,
}: {
  component: Pick<ProductTemplateComponent, "component_id" | "name">;
  components: readonly Pick<
    ProductTemplateComponent,
    "component_id" | "name" | "operations" | "materials"
  >[];
}) {
  if (!isVolumetricCantLateralComponent(component)) return null;

  const modules = buildVolumetricCantProductionModules(components);

  return (
    <div className="rounded-lg border border-cyan-900/40 bg-cyan-950/10 px-3 py-3 space-y-2">
      <div>
        <p className="text-[10px] font-bold uppercase tracking-wide text-cyan-300">
          Modularitate producere cant
        </p>
        <p className="mt-1 text-[10px] leading-relaxed text-slate-400">
          Audit live pe traseele de cant pentru șablonul volumetric, derivat din operațiile și materialele deja definite în template.
        </p>
      </div>

      <div className="space-y-2">
        {modules.map((module) => (
          <div
            key={module.key}
            className="rounded-lg border border-[#1E293B] bg-[#0A0F1C] px-3 py-2.5"
            data-testid={`volumetric-cant-module-${module.key}`}
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-[11px] font-semibold text-slate-100">{module.title}</p>
                <p className="mt-0.5 text-[10px] leading-relaxed text-slate-400">
                  {module.appliesWhen}
                </p>
              </div>
              <span
                className={`shrink-0 rounded-full border px-2 py-0.5 text-[9px] font-bold uppercase tracking-wide ${moduleStatusTone(module.status)}`}
              >
                {moduleStatusLabel(module.status)}
              </span>
            </div>

            <p className="mt-2 text-[10px] leading-relaxed text-slate-300">
              <span className="font-semibold text-slate-200">Secvență:</span> {module.sequencing}
            </p>

            <div className="mt-2 grid gap-2 sm:grid-cols-2">
              <div>
                <p className="text-[9px] font-semibold uppercase tracking-wide text-slate-500">
                  Operații cerute
                </p>
                <p className="mt-1 text-[10px] text-slate-300 font-mono break-words">
                  {module.operationCodes.join(", ")}
                </p>
              </div>
              <div>
                <p className="text-[9px] font-semibold uppercase tracking-wide text-slate-500">
                  Materiale cerute
                </p>
                <p className="mt-1 text-[10px] text-slate-300 font-mono break-words">
                  {module.materialCodes.join(", ")}
                </p>
              </div>
            </div>

            {module.missingOperationCodes.length > 0 || module.missingMaterialCodes.length > 0 ? (
              <div className="mt-2 rounded border border-amber-800/30 bg-amber-950/10 px-2.5 py-2 text-[10px] text-amber-200/90">
                {module.missingOperationCodes.length > 0 ? (
                  <p>
                    Operații lipsă: <span className="font-mono">{module.missingOperationCodes.join(", ")}</span>
                  </p>
                ) : null}
                {module.missingMaterialCodes.length > 0 ? (
                  <p>
                    Materiale lipsă: <span className="font-mono">{module.missingMaterialCodes.join(", ")}</span>
                  </p>
                ) : null}
              </div>
            ) : null}
          </div>
        ))}
      </div>
    </div>
  );
}

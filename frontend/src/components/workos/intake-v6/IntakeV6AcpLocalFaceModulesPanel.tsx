/**
 * Minimal Step 2 operator surface for ACP local face modules.
 * Readiness + owner gates only — no plexi/LED calculators, no BOM, no tasks.
 */
import {
  ownerGeometryLabel,
  readSvgComponentBindings,
  type SvgComponentBinding,
} from "@/lib/intakeV6/svgComponentBindings";

const MODULE_LABELS: Record<string, string> = {
  "ACP-LOCAL-MODULE-ROUTED-BACKLIT": "Decupaj iluminat (plexiglas pe spate)",
  "ACP-LOCAL-MODULE-ACRYLIC-INSERT": "Insert plexiglas",
  "ACP-LOCAL-MODULE-PLAIN-DECORATIVE": "Zonă decorativă",
  "ACP-APPLIED-COMPONENT-INTERFACE": "Interfață componente aplicate",
};

function moduleFromBinding(binding: SvgComponentBinding): {
  code: string;
  readiness: string;
  gates: Array<{ path: string; status: string }>;
  status: string;
} | null {
  const mod = binding.local_module_configuration;
  if (mod && typeof mod === "object" && mod.module_code) {
    const readiness =
      typeof mod.readiness === "object" && mod.readiness
        ? String(mod.readiness.overall || "—")
        : String(binding.local_configuration_status || "—");
    const gates =
      typeof mod.readiness === "object" && Array.isArray(mod.readiness?.gates)
        ? (mod.readiness.gates as Array<{ path: string; status: string }>)
        : [];
    return {
      code: String(mod.module_code),
      readiness,
      gates,
      status: String(mod.status || binding.status || "ACTIVE"),
    };
  }
  const treatment = String(binding.face_treatment_code || "");
  if (!treatment || treatment === "NOT_APPLICABLE") return null;
  if (treatment.includes("ROUTED")) {
    return {
      code: "ACP-LOCAL-MODULE-ROUTED-BACKLIT",
      readiness: String(binding.local_configuration_status || "LOCAL_CONFIGURATION_REQUIRED"),
      gates: [],
      status: binding.status === "INACTIVE" ? "INACTIVE" : "ACTIVE",
    };
  }
  if (treatment.includes("ACRYLIC-INSERT")) {
    return {
      code: "ACP-LOCAL-MODULE-ACRYLIC-INSERT",
      readiness: String(binding.local_configuration_status || "LOCAL_CONFIGURATION_REQUIRED"),
      gates: [],
      status: binding.status === "INACTIVE" ? "INACTIVE" : "ACTIVE",
    };
  }
  if (treatment.includes("APPLIED")) {
    return {
      code: "ACP-APPLIED-COMPONENT-INTERFACE",
      readiness: String(binding.local_configuration_status || "LOCAL_CONFIGURATION_REQUIRED"),
      gates: [],
      status: binding.status === "INACTIVE" ? "INACTIVE" : "ACTIVE",
    };
  }
  return null;
}

export default function IntakeV6AcpLocalFaceModulesPanel({
  finish,
  onPatchBindings,
  disabled,
}: {
  finish: Record<string, unknown> | null | undefined;
  onPatchBindings: (next: SvgComponentBinding[]) => void;
  disabled?: boolean;
}) {
  const bindings = readSvgComponentBindings(finish);
  const electrical = (finish?.acp_electrical_configuration || null) as Record<string, unknown> | null;

  const activeModules = bindings
    .map((binding) => {
      const module = moduleFromBinding(binding);
      if (!module || module.status === "INACTIVE") return null;
      return { binding, module };
    })
    .filter((row): row is { binding: SvgComponentBinding; module: NonNullable<ReturnType<typeof moduleFromBinding>> } =>
      Boolean(row),
    );

  if (!activeModules.length && !electrical) {
    return null;
  }

  return (
    <div
      className="mt-3 rounded border border-emerald-500/30 bg-emerald-950/15 px-3 py-3 space-y-3"
      data-testid="intake-v6-acp-local-face-modules"
    >
      <div>
        <p className="text-[11px] font-semibold text-emerald-100">Fata și module locale ACP</p>
        <p className="text-[10px] text-slate-400">
          Module component-owned pe panoul ACP. Shell / cadru / prindere rămân separate. Fără cantități
          inventate, fără preț, fără taskuri.
        </p>
      </div>

      {activeModules.length === 0 ? (
        <p className="text-[10px] text-slate-500" data-testid="intake-v6-acp-local-modules-empty">
          Niciun modul local activ. Selectează text/logo decupat sau insert în Pasul 1.
        </p>
      ) : (
        <ul className="space-y-2">
          {activeModules.map(({ binding, module }) => (
            <li
              key={binding.binding_id}
              className="rounded border border-[#2A3548] bg-[#0A0F1A]/80 px-2.5 py-2 space-y-1.5"
              data-testid={`intake-v6-acp-local-module-${binding.geometry_role}`}
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <p className="text-[11px] font-medium text-slate-100">
                    {MODULE_LABELS[module.code] || module.code}
                  </p>
                  <p className="text-[10px] text-slate-400">
                    {ownerGeometryLabel(binding.geometry_role)} · {binding.face_treatment_code}
                  </p>
                  <p className="text-[10px] text-emerald-200/90" data-testid="intake-v6-acp-module-readiness">
                    Readiness: {module.readiness}
                  </p>
                </div>
                <button
                  type="button"
                  disabled={disabled}
                  className="rounded border border-slate-600 px-2 py-1 text-[10px] text-slate-300 hover:bg-slate-800 disabled:opacity-50"
                  data-testid={`intake-v6-acp-module-deactivate-${binding.geometry_role}`}
                  onClick={() => {
                    const next = bindings.map((row) =>
                      row.binding_id === binding.binding_id
                        ? {
                            ...row,
                            status: "INACTIVE" as const,
                            confirmation_status: "INACTIVE",
                            local_module_configuration: row.local_module_configuration
                              ? { ...row.local_module_configuration, status: "INACTIVE" }
                              : row.local_module_configuration,
                          }
                        : row,
                    );
                    onPatchBindings(next);
                  }}
                >
                  Dezactivează
                </button>
              </div>
              {module.gates.length > 0 ? (
                <div data-testid="intake-v6-acp-module-owner-gates">
                  <p className="text-[10px] text-amber-200">Owner gates (nu sunt defaults):</p>
                  <ul className="mt-0.5 list-disc pl-4 text-[10px] text-amber-100/80">
                    {module.gates.slice(0, 8).map((gate) => (
                      <li key={`${gate.path}-${gate.status}`}>
                        {gate.path}: {gate.status}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : (
                <p className="text-[10px] text-slate-500">
                  Configurație tehnică detaliată rămâne owner-gated (plexiglas / LED / toleranțe).
                </p>
              )}
            </li>
          ))}
        </ul>
      )}

      {electrical && typeof electrical === "object" ? (
        <div
          className="rounded border border-cyan-500/25 bg-cyan-950/20 px-2.5 py-2 space-y-1"
          data-testid="intake-v6-acp-electrical-readiness"
        >
          <p className="text-[11px] font-medium text-cyan-100">Iluminare și electric (shell comun)</p>
          <p className="text-[10px] text-slate-400">
            Ownership: {String(electrical.ownership_mode || "SHELL_COMMON_WITH_ZONE_INTENTS")} — intenții
            pe zonă, LED/PSU/cablare pe shell. Fără cantități inventate.
          </p>
          <p className="text-[10px] text-cyan-100/90">
            Zone cu iluminare:{" "}
            {Array.isArray(electrical.zone_intents) ? electrical.zone_intents.length : 0}
            {" · "}
            LED: {String(electrical.led_configuration_status || "OWNER_GATE_REQUIRED")}
            {" · "}
            PSU: {String(electrical.psu_configuration_status || "OWNER_GATE_REQUIRED")}
          </p>
        </div>
      ) : null}
    </div>
  );
}

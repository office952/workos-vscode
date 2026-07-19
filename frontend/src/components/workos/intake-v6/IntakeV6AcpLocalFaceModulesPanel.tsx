/**
 * Minimal Step 2 operator surface for ACP local face modules.
 * Primary UI uses Romanian vocabulary; raw tokens stay under advanced disclosure.
 */
import {
  ownerGeometryLabel,
  readSvgComponentBindings,
  type SvgComponentBinding,
} from "@/lib/intakeV6/svgComponentBindings";
import {
  isOwnerDecisionStatus,
  operatorGatePathLabelRo,
  operatorGateStatusLabelRo,
  operatorReadinessLabelRo,
  operatorStatusSemanticRo,
} from "@/lib/intakeV6/intakeV6OperatorVocabulary";
import IntakeV6TechnicalDetailsAccordion from "./atoms/IntakeV6TechnicalDetailsAccordion";

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
        <p className="text-[11px] font-semibold text-emerald-100">Față și module locale ACP</p>
        <p className="text-[10px] text-slate-400">
          Module pe panoul ACP. Carcasa, cadrul și prinderea rămân separate. Fără cantități inventate,
          fără preț, fără taskuri.
        </p>
      </div>

      {activeModules.length === 0 ? (
        <p className="text-[10px] text-slate-500" data-testid="intake-v6-acp-local-modules-empty">
          Niciun modul local activ. Selectează text/logo decupat sau insert în Pasul 1.
        </p>
      ) : (
        <ul className="space-y-2">
          {activeModules.map(({ binding, module }) => {
            const readinessRo = operatorReadinessLabelRo(module.readiness);
            const ownerDecision = isOwnerDecisionStatus(module.readiness);
            return (
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
                      {ownerGeometryLabel(binding.geometry_role)}
                    </p>
                    <p
                      className={`text-[10px] ${
                        ownerDecision ? "text-amber-200/90" : "text-emerald-200/90"
                      }`}
                      data-testid="intake-v6-acp-module-readiness"
                      data-readiness-raw={module.readiness}
                    >
                      Stare: {readinessRo}
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
                    <p className="text-[10px] text-amber-200">
                      {operatorStatusSemanticRo("owner_decision")} (nu sunt valori implicite):
                    </p>
                    <ul className="mt-0.5 list-disc pl-4 text-[10px] text-amber-100/80">
                      {module.gates.slice(0, 8).map((gate) => (
                        <li key={`${gate.path}-${gate.status}`}>
                          {operatorGatePathLabelRo(gate.path)}:{" "}
                          {operatorGateStatusLabelRo(gate.status)}
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : (
                  <p className="text-[10px] text-slate-500">
                    Detaliile tehnice (plexiglas / LED / toleranțe) necesită confirmarea
                    administratorului.
                  </p>
                )}
                <IntakeV6TechnicalDetailsAccordion
                  title="Detalii tehnice modul"
                  hint="Identificatori interni"
                  defaultOpen={false}
                  testId={`intake-v6-acp-module-advanced-${binding.geometry_role}`}
                  className="mt-1"
                >
                  <p className="font-mono text-[10px] text-slate-400">
                    module_code: {module.code}
                  </p>
                  <p className="font-mono text-[10px] text-slate-400">
                    face_treatment: {binding.face_treatment_code || "—"}
                  </p>
                  <p className="font-mono text-[10px] text-slate-400">
                    readiness_raw: {module.readiness}
                  </p>
                  {module.gates.map((gate) => (
                    <p
                      key={`raw-${gate.path}-${gate.status}`}
                      className="font-mono text-[10px] text-slate-500"
                    >
                      gate {gate.path}={gate.status}
                    </p>
                  ))}
                </IntakeV6TechnicalDetailsAccordion>
              </li>
            );
          })}
        </ul>
      )}

      {electrical && typeof electrical === "object" ? (
        <div
          className="rounded border border-cyan-500/25 bg-cyan-950/20 px-2.5 py-2 space-y-1"
          data-testid="intake-v6-acp-electrical-readiness"
        >
          <p className="text-[11px] font-medium text-cyan-100">Iluminare pe carcasă (comună)</p>
          <p className="text-[10px] text-slate-400">
            Intenții pe zonă; LED și sursa pe shell. Fără cantități inventate.
          </p>
          <p className="text-[10px] text-cyan-100/90" data-testid="intake-v6-acp-electrical-status-ro">
            Zone cu iluminare:{" "}
            {Array.isArray(electrical.zone_intents) ? electrical.zone_intents.length : 0}
            {" · "}
            LED:{" "}
            {operatorReadinessLabelRo(
              String(electrical.led_configuration_status || "OWNER_GATE_REQUIRED"),
            )}
            {" · "}
            Sursă:{" "}
            {operatorReadinessLabelRo(
              String(electrical.psu_configuration_status || "OWNER_GATE_REQUIRED"),
            )}
          </p>
          <IntakeV6TechnicalDetailsAccordion
            title="Detalii tehnice electrice shell"
            hint="Valori interne"
            defaultOpen={false}
            testId="intake-v6-acp-electrical-advanced"
            className="mt-1"
          >
            <p className="font-mono text-[10px] text-slate-500">
              ownership_mode: {String(electrical.ownership_mode || "—")}
            </p>
            <p className="font-mono text-[10px] text-slate-500">
              led_configuration_status:{" "}
              {String(electrical.led_configuration_status || "OWNER_GATE_REQUIRED")}
            </p>
            <p className="font-mono text-[10px] text-slate-500">
              psu_configuration_status:{" "}
              {String(electrical.psu_configuration_status || "OWNER_GATE_REQUIRED")}
            </p>
          </IntakeV6TechnicalDetailsAccordion>
        </div>
      ) : null}
    </div>
  );
}

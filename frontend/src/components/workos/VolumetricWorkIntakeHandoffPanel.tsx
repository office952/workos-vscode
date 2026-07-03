import type { IntakeProductSpec } from "@/lib/intakeProductSpec";
import { INTAKE_MOUNTING_SYSTEM_OPTIONS } from "@/lib/intakeVolumetricSpec";
import {
  LED_MODULE_POWER_OPTIONS,
  LED_STRIP_DENSITY_OPTIONS,
  LIGHTING_SYSTEM_OPTIONS,
} from "@/lib/volumetricFrontlitIntake";
import {
  effectiveReturnDepthMm,
  TPL_VOLUMETRIC_LETTERS,
} from "@/lib/volumetricQuoteInput";
import { formatVolumetricFinishSummary } from "@/lib/volumetricFinishDisplay";
import {
  buildVolumetricLightingSnapshot,
  formatVolumetricPsuConfiguration,
} from "@/lib/volumetricLightingSnapshot";
import VolumetricFinishDisplayPanel from "./VolumetricFinishDisplayPanel";

function fmt(value: number | string | undefined | null, suffix = ""): string {
  if (value == null || value === "") return "—";
  return `${value}${suffix}`;
}

function mountingLabel(system: string | undefined): string {
  if (!system) return "—";
  return (
    INTAKE_MOUNTING_SYSTEM_OPTIONS.find((o) => o.value === system)?.label ?? system
  );
}

function lightingSystemLabel(type: string | undefined): string {
  if (!type) return "—";
  const normalized =
    type === "led_module" ? "led_modules" : type;
  return (
    LIGHTING_SYSTEM_OPTIONS.find((o) => o.value === normalized)?.label ??
    type
  );
}

function ledVariantLabel(spec: IntakeProductSpec): string {
  const system = spec.lighting_system_type;
  if (system === "led_strip") {
    const density = spec.led_strip_density ?? "60_led_per_m";
    return (
      LED_STRIP_DENSITY_OPTIONS.find((o) => o.value === density)?.label ?? density
    );
  }
  const power = spec.led_module_power_w ?? spec.led_module_wattage ?? 1.44;
  return (
    LED_MODULE_POWER_OPTIONS.find((o) => o.value === power)?.label ??
    `${power} W / modul`
  );
}

export interface VolumetricWorkIntakeHandoffPanelProps {
  spec: IntakeProductSpec;
  intakeRequestId?: string;
  templateCode?: string;
  textLabel?: string;
}

/**
 * Read-only technical snapshot from the source intake handoff — commercial quote mode.
 */
export default function VolumetricWorkIntakeHandoffPanel({
  spec,
  intakeRequestId,
  templateCode = TPL_VOLUMETRIC_LETTERS,
  textLabel,
}: VolumetricWorkIntakeHandoffPanelProps) {
  const depth = effectiveReturnDepthMm(spec);
  const lighting = buildVolumetricLightingSnapshot(spec);
  const finishSummary = formatVolumetricFinishSummary(spec);
  const psuConfig = lighting.psu_configuration ?? [];
  const psuPlanText = psuConfig.length
    ? formatVolumetricPsuConfiguration(psuConfig)
    : lighting.selected_psu_watts
      ? `${lighting.selected_psu_watts} W`
      : "—";
  const compatiblePsu =
    lighting.selected_psu_watts ?? (psuConfig.length ? Math.max(...psuConfig) : undefined);

  return (
    <section
      className="rounded-lg border border-emerald-800/35 bg-emerald-950/10 p-4 space-y-4"
      data-testid="volumetric-handoff-spec-panel"
    >
      <div>
        <h2 className="text-[14px] font-semibold text-emerald-100">
          Specificație confirmată în intake-ul sursă
        </h2>
        <p className="text-[10px] text-slate-500 mt-1">
          Snapshot tehnic preluat la handoff — modificările se fac în workspace-ul sursă sau prin
          Advanced override.
        </p>
      </div>

      <dl className="grid grid-cols-2 md:grid-cols-3 gap-x-4 gap-y-3 text-[11px]">
        <HandoffRow label="Cerere" value={intakeRequestId ?? "—"} mono />
        <HandoffRow label="Template" value={templateCode} mono />
        <HandoffRow label="Text / denumire" value={textLabel ?? spec.text?.trim() ?? "—"} />
        <HandoffRow
          label="Dimensiuni (mm)"
          value={`${fmt(spec.width_mm)} × ${fmt(spec.height_mm ?? spec.letter_height_mm)} × ${fmt(depth)}`}
        />
        <HandoffRow
          label="Geometrie"
          value={`P ${fmt(spec.letter_perimeter_m)} m · A ${fmt(spec.letter_face_area_m2)} m² · ${fmt(spec.letter_count)} litere`}
        />
        <HandoffRow
          label="Layer principal litere"
          value={spec.vector_primary_letters_layer_name ?? "—"}
        />
        {spec.vector_file_name && (
          <HandoffRow label="Fișier vector" value={spec.vector_file_name} mono />
        )}
        <HandoffRow
          label="Șanfren vizual față"
          value={spec.visual_chamfer_included ? "Inclus obligatoriu" : "—"}
        />
        <HandoffRow
          label="Șanfren spate Forex"
          value={
            spec.back_bevel_enabled === true || spec.backing_chamfer === true
              ? "Da"
              : "Nu"
          }
        />
        <HandoffRow label="Sistem montaj" value={mountingLabel(spec.mounting_system)} />
        <HandoffRow
          label="Șablon montaj Forex"
          value={
            spec.mounting_template_enabled
              ? `Activ${spec.mounting_template_area_m2 != null ? ` · ${spec.mounting_template_area_m2.toFixed(2)} m²` : ""}`
              : "Nu"
          }
        />
        {(spec.mounting_system === "steel_bars" ||
          spec.mounting_system === "aluminum_bars") && (
          <HandoffRow
            label="Bare premontaj"
            value={`${spec.mounting_bar_count ?? 2} buc · ${spec.mounting_bar_profile ?? "30x30x1.5"}`}
          />
        )}
        <HandoffRow
          label="Iluminare"
          value={`${lightingSystemLabel(spec.lighting_system_type)} · ${spec.light_color ?? "—"}`}
        />
        <HandoffRow label="Variantă LED" value={ledVariantLabel(spec)} />
      </dl>

      <div
        className="rounded-md border border-[#2A3548] bg-[#0A0F1A]/50 p-3 space-y-2"
        data-testid="volumetric-handoff-psu-plan"
      >
        <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">
          Plan PSU / surse
        </p>
        <p className="text-[14px] font-semibold text-emerald-300/90">{psuPlanText}</p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-[10px]">
          <div>
            <span className="text-slate-600">Consum LED</span>
            <p className="text-[12px] font-semibold text-slate-100">
              {fmt(lighting.total_led_watts, " W")}
            </p>
          </div>
          <div>
            <span className="text-slate-600">Necesar</span>
            <p className="text-[12px] font-semibold text-slate-100">
              {fmt(lighting.required_psu_watts, " W")}
            </p>
          </div>
          <div>
            <span className="text-slate-600">Total capacitate</span>
            <p className="text-[12px] font-semibold text-emerald-300/90">
              {fmt(lighting.psu_total_capacity_watts, " W")}
            </p>
          </div>
          <div>
            <span className="text-slate-600">Rezervă</span>
            <p className="text-[12px] font-semibold text-slate-100">
              {lighting.psu_reserve_margin_watts != null
                ? `${lighting.psu_reserve_margin_watts} W`
                : "—"}
            </p>
          </div>
        </div>
        {psuConfig.length > 1 && compatiblePsu != null && (
          <p
            className="text-[10px] text-amber-300/80 border-t border-[#1E293B]/80 pt-2"
            data-testid="volumetric-handoff-psu-costengine-note"
          >
            Notă internă: pricing folosește momentan valoarea compatibilă selected_psu_watts (
            {compatiblePsu} W); multi-PSU costing complet este build separat.
          </p>
        )}
      </div>

      <VolumetricFinishDisplayPanel spec={spec} testId="volumetric-handoff-finish-display" />

      {finishSummary.warnings.length > 0 && (
        <ul className="text-[10px] text-slate-500 space-y-0.5">
          {finishSummary.warnings.map((w) => (
            <li key={w}>{w}</li>
          ))}
        </ul>
      )}
    </section>
  );
}

function HandoffRow({
  label,
  value,
  mono,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div>
      <dt className="text-[9px] uppercase tracking-wide text-slate-500">{label}</dt>
      <dd
        className={`font-medium text-slate-200 truncate ${mono ? "font-mono text-blue-300/90" : ""}`}
      >
        {value}
      </dd>
    </div>
  );
}

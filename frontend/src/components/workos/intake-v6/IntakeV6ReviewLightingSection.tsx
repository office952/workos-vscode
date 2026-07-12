import type { IntakeV6EmblemLightingMode } from "@/lib/intakeV6/intakeV6BackingMode";
import {
  normalizeIntakeV6LedModuleWattage,
} from "@/lib/intakeV6/intakeV6LedLighting";
import type { TemplateFormOption } from "@/lib/intakeV6/useTemplateFormContract";
import {
  formatLedAreaDensity,
  ledAreaDensityModulesPerSqm,
  ledAreaLayoutRuleLabel,
  ledStripAreaLayoutRuleLabel,
} from "@/lib/intakeV6/sharedLedLightingDensity";
import { Lightbulb, Power } from "lucide-react";
import IntakeV6TechnicalDetailsAccordion from "./atoms/IntakeV6TechnicalDetailsAccordion";
import { v6 } from "./atoms/intakeV6Presentation";
import {
  REVIEW_FIELD_BLOCK_CLASS,
  REVIEW_FIELD_LABEL_CLASS,
  REVIEW_SELECT_CLASS,
} from "./reviewFieldLayout";

function lightColorLabel(value: string | undefined): string {
  if (value === "neutral") return "Neutral white";
  if (value === "cool") return "Cool white";
  return "Warm white";
}

function formatMl(value: number | null | undefined): string {
  return value != null ? `${value.toFixed(3)} ml` : "-";
}

export default function IntakeV6ReviewLightingSection({
  illuminated,
  onIlluminatedChange,
  lightingSystemType,
  onLightingSystemTypeChange,
  lightColor,
  onLightColorChange,
  ledModulePowerW,
  onLedModulePowerWChange,
  ledDisplayPerimeterM,
  emblemLightingMode,
  onEmblemLightingChange,
  showEmblemLighting,
  isLedModules,
  ledModuleCount,
  emblemOutboxAreaM2,
  emblemLedModuleCount,
  emblemLightingModeNormalized,
  totalLedModuleCount,
  letterLedStripLengthM,
  emblemLedStripLengthM,
  totalLedStripLengthM,
  ledStripPowerWPerMl,
  returnDepthMm,
  estimatedLedWatts,
  requiredPsuWatts,
  psuLabel,
  psuAllocationStatus,
  psuReservePercent,
  selectedPsuWatts,
  onSelectedPsuChange,
  allowedPsuWatts,
  showLightingFields = true,
  showElectricalFields = true,
  allowedLightingSystems,
  allowedLightColors,
  allowedLedModulePowerW,
  allowedEmblemLightingModes,
  compact = true,
}: {
  illuminated: boolean;
  onIlluminatedChange: (value: boolean) => void;
  lightingSystemType: string;
  onLightingSystemTypeChange: (value: string) => void;
  lightColor: string;
  onLightColorChange: (value: string) => void;
  ledModulePowerW: number;
  onLedModulePowerWChange: (value: number) => void;
  ledDisplayPerimeterM: number | null;
  emblemLightingMode: IntakeV6EmblemLightingMode;
  onEmblemLightingChange: (mode: IntakeV6EmblemLightingMode) => void;
  showEmblemLighting: boolean;
  isLedModules: boolean;
  ledModuleCount: number | null;
  emblemOutboxAreaM2: number | null;
  emblemLedModuleCount: number | null | undefined;
  emblemLightingModeNormalized: IntakeV6EmblemLightingMode;
  totalLedModuleCount: number | null;
  letterLedStripLengthM: number | null | undefined;
  emblemLedStripLengthM: number | null | undefined;
  totalLedStripLengthM: number | null | undefined;
  ledStripPowerWPerMl: number;
  returnDepthMm: number | null;
  estimatedLedWatts: number | null | undefined;
  requiredPsuWatts: number | null | undefined;
  psuLabel: string;
  psuAllocationStatus: string | null | undefined;
  psuReservePercent: number;
  selectedPsuWatts: number | null | undefined;
  onSelectedPsuChange: (watts: number) => void;
  allowedPsuWatts: readonly number[];
  showLightingFields?: boolean;
  showElectricalFields?: boolean;
  allowedLightingSystems: readonly TemplateFormOption[];
  allowedLightColors: readonly TemplateFormOption[];
  allowedLedModulePowerW: readonly TemplateFormOption[];
  allowedEmblemLightingModes: readonly TemplateFormOption[];
  compact?: boolean;
}) {
  const fallbackDensity = ledAreaDensityModulesPerSqm(returnDepthMm ?? undefined);
  const shellClass = compact ? `${v6.cardCompact} !p-3` : `${v6.card} mb-4`;
  const showAnyLedScope = showLightingFields || showElectricalFields;

  return (
    <div className={shellClass} data-testid="intake-v6-review-lighting-section">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <div className="min-w-0">
          <p className={compact ? v6.zoneTitle : v6.sectionTitle}>Iluminare LED</p>
          {illuminated && ledDisplayPerimeterM != null ? (
            <p className="mt-0.5 text-[10px] text-slate-500">
              Perimetru litere:{" "}
              <span className="font-semibold tabular-nums text-slate-300" data-testid="intake-v6-led-letters-perimeter">
                {ledDisplayPerimeterM.toFixed(3)} m
              </span>
            </p>
          ) : null}
        </div>
        <label
          className={[
            "group flex min-w-[180px] cursor-pointer items-center gap-2 rounded border px-2.5 py-1.5 transition",
            illuminated
              ? "border-cyan-400/60 bg-cyan-400/10 text-cyan-50"
              : "border-[#2A3548] bg-[#0A0F1A] text-slate-400 hover:border-cyan-400/30 hover:text-slate-200",
          ].join(" ")}
        >
          <input
            type="checkbox"
            className="sr-only"
            checked={illuminated}
            onChange={(event) => onIlluminatedChange(event.target.checked)}
            data-testid="intake-v6-illuminated"
          />
          <span
            className={[
              "flex h-7 w-7 shrink-0 items-center justify-center rounded border transition",
              illuminated
                ? "border-cyan-300/70 bg-cyan-300 text-slate-950"
                : "border-slate-600 bg-slate-900 text-slate-500 group-hover:text-cyan-200",
            ].join(" ")}
          >
            {illuminated ? <Lightbulb className="h-3.5 w-3.5" /> : <Power className="h-3.5 w-3.5" />}
          </span>
          <span className="min-w-0 flex-1">
            <span className="block text-[10px] font-semibold">
              {illuminated ? "LED activ" : "LED oprit"}
            </span>
          </span>
          <span
            aria-hidden="true"
            className={[
              "relative h-4 w-8 rounded-full border transition",
              illuminated ? "border-cyan-300 bg-cyan-300/80" : "border-slate-600 bg-slate-800",
            ].join(" ")}
          >
            <span
              className={[
                "absolute top-0.5 h-2.5 w-2.5 rounded-full bg-white transition",
                illuminated ? "left-4" : "left-0.5",
              ].join(" ")}
            />
          </span>
        </label>
      </div>

      {!illuminated ? (
        <p className="text-[10px] text-slate-500">Fără iluminare LED.</p>
      ) : !showAnyLedScope ? (
        <p className="text-[10px] text-slate-500">Iluminare / electrică nu sunt în scope-ul ofertei.</p>
      ) : (
        <div className="space-y-3" data-testid="intake-v6-lighting-fields">
          {showLightingFields ? (
            <section className="space-y-2.5" data-testid="intake-v6-lighting-subsection">
              <p className="text-[11px] font-semibold text-cyan-200">Iluminare</p>
              <div className="grid gap-2 sm:grid-cols-2">
                <label className={REVIEW_FIELD_BLOCK_CLASS}>
                  <span className={REVIEW_FIELD_LABEL_CLASS}>Sistem LED</span>
                  <select
                    className={REVIEW_SELECT_CLASS}
                    value={lightingSystemType}
                    onChange={(event) => onLightingSystemTypeChange(event.target.value)}
                    data-testid="intake-v6-lighting-system"
                  >
                    {allowedLightingSystems.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </label>

                <label className={REVIEW_FIELD_BLOCK_CLASS}>
                  <span className={REVIEW_FIELD_LABEL_CLASS}>Culoare lumina</span>
                  <select
                    className={REVIEW_SELECT_CLASS}
                    value={lightColor}
                    onChange={(event) => onLightColorChange(event.target.value)}
                    data-testid="intake-v6-light-color"
                  >
                    {allowedLightColors.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </label>

                {isLedModules ? (
                  <label className={`${REVIEW_FIELD_BLOCK_CLASS} sm:col-span-2`}>
                    <span className={REVIEW_FIELD_LABEL_CLASS}>Putere modul</span>
                    <select
                      className={REVIEW_SELECT_CLASS}
                      value={String(ledModulePowerW)}
                      onChange={(event) =>
                        onLedModulePowerWChange(normalizeIntakeV6LedModuleWattage(Number(event.target.value)))
                      }
                      data-testid="intake-v6-led-module-wattage"
                    >
                      {allowedLedModulePowerW.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </label>
                ) : null}

                {showEmblemLighting ? (
                  <label className={`${REVIEW_FIELD_BLOCK_CLASS} sm:col-span-2`}>
                    <span className={REVIEW_FIELD_LABEL_CLASS}>Iluminare emblemă</span>
                    <select
                      className={REVIEW_SELECT_CLASS}
                      value={emblemLightingMode}
                      onChange={(event) =>
                        onEmblemLightingChange(event.target.value as IntakeV6EmblemLightingMode)
                      }
                      data-testid="intake-v6-emblem-lighting-mode"
                    >
                      {allowedEmblemLightingModes.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </label>
                ) : null}
              </div>

              <p className="text-[10px] text-slate-500">
                {isLedModules ? "Module LED" : "Banda LED"} · {lightColorLabel(lightColor)} ·{" "}
                {isLedModules
                  ? `${ledModulePowerW.toFixed(2)} W/modul`
                  : `${ledStripPowerWPerMl.toFixed(1)} W/ml`}
                {totalLedModuleCount != null ? (
                  <>
                    {" "}
                    · module total{" "}
                    <span className="font-medium tabular-nums text-slate-300" data-testid="intake-v6-led-total-modules-inline">
                      {totalLedModuleCount} buc
                    </span>
                  </>
                ) : null}
              </p>
            </section>
          ) : null}

          {!showLightingFields && totalLedModuleCount != null ? (
            <p className="text-[10px] text-slate-500" data-testid="intake-v6-led-calc-readout">
              Module LED (calc):{" "}
              <span className="font-medium tabular-nums text-slate-300">{totalLedModuleCount} buc</span>
              {estimatedLedWatts != null ? (
                <>
                  {" "}
                  · consum{" "}
                  <span className="font-medium tabular-nums text-slate-300">
                    {estimatedLedWatts.toFixed(2)} W
                  </span>
                </>
              ) : null}
            </p>
          ) : null}

          {showElectricalFields ? (
            <section className="space-y-2.5" data-testid="intake-v6-electrical-subsection">
              <p className="text-[11px] font-semibold text-amber-200">Electrică</p>
              <div className="grid gap-2 sm:grid-cols-2">
                <label className={REVIEW_FIELD_BLOCK_CLASS}>
                  <span className={REVIEW_FIELD_LABEL_CLASS}>Sursa LED template</span>
                  <select
                    className={REVIEW_SELECT_CLASS}
                    value={selectedPsuWatts ?? ""}
                    onChange={(event) => {
                      const raw = event.target.value;
                      if (raw) onSelectedPsuChange(Number(raw));
                    }}
                    data-testid="intake-v6-selected-psu-watts"
                  >
                    <option value="">-</option>
                    {allowedPsuWatts.map((watts) => (
                      <option key={watts} value={watts}>
                        {watts}W
                      </option>
                    ))}
                  </select>
                </label>
              </div>

              <p className="text-[10px] text-slate-500" data-testid="intake-v6-electrical-readout">
                PSU (+{psuReservePercent}%):{" "}
                <span className="font-medium tabular-nums text-slate-300">
                  {requiredPsuWatts != null ? `${requiredPsuWatts.toFixed(2)} W` : "-"}
                </span>
                {" · "}
                surse: <span className="font-medium text-slate-300">{psuLabel}</span>
                {psuAllocationStatus && psuAllocationStatus !== "ok" ? (
                  <span className="text-amber-200"> · PSU: {psuAllocationStatus}</span>
                ) : null}
              </p>
            </section>
          ) : null}

          <IntakeV6TechnicalDetailsAccordion
            title="Detalii calcul LED"
            testId="intake-v6-led-calculation-details"
          >
            <div className="space-y-1 text-[10px] text-slate-400">
              {showLightingFields && isLedModules ? (
                <>
                  <p data-testid="intake-v6-led-letters-modules">
                    Module litere:{" "}
                    <strong className="text-slate-200">
                      {ledModuleCount != null ? `${ledModuleCount} buc` : "-"}
                    </strong>
                  </p>
                  <p data-testid="intake-v6-led-emblem-area">
                    Arie emblemă:{" "}
                    <strong className="text-slate-200">
                      {emblemOutboxAreaM2 != null ? `${emblemOutboxAreaM2.toFixed(4)} m2` : "-"}
                    </strong>
                  </p>
                  <p data-testid="intake-v6-led-emblem-depth">
                    Adâncime calcul emblemă:{" "}
                    <strong className="text-slate-200">
                      {returnDepthMm != null ? `${returnDepthMm} mm` : "-"}
                    </strong>
                  </p>
                  <p data-testid="intake-v6-led-emblem-density">
                    Regulă emblemă:{" "}
                    <strong className="text-slate-200">{ledAreaLayoutRuleLabel(returnDepthMm)}</strong>
                  </p>
                  <p data-testid="intake-v6-led-emblem-density-fallback">
                    Fallback arie:{" "}
                    <strong className="text-slate-200">{formatLedAreaDensity(fallbackDensity)}</strong>
                  </p>
                  <p data-testid="intake-v6-led-emblem-modules">
                    Module emblemă:{" "}
                    <strong className="text-slate-200">
                      {emblemLightingModeNormalized === "area_lit"
                        ? emblemLedModuleCount != null
                          ? `${emblemLedModuleCount} buc`
                          : "-"
                        : emblemLightingModeNormalized === "excluded"
                          ? "neincluse"
                          : "-"}
                    </strong>
                  </p>
                  <p data-testid="intake-v6-led-total-modules">
                    Module total:{" "}
                    <strong className="text-slate-200">
                      {totalLedModuleCount != null ? `${totalLedModuleCount} buc` : "-"}
                    </strong>
                  </p>
                </>
              ) : showLightingFields ? (
                <>
                  <p data-testid="intake-v6-led-strip-rule">
                    Regulă bandă emblemă:{" "}
                    <strong className="text-slate-200">{ledStripAreaLayoutRuleLabel()}</strong>
                  </p>
                  <p data-testid="intake-v6-led-strip-letters">
                    Banda litere: <strong className="text-slate-200">{formatMl(letterLedStripLengthM)}</strong>
                  </p>
                  <p data-testid="intake-v6-led-strip-emblem">
                    Bandă emblemă:{" "}
                    <strong className="text-slate-200">
                      {emblemLightingModeNormalized === "area_lit"
                        ? formatMl(emblemLedStripLengthM)
                        : emblemLightingModeNormalized === "excluded"
                          ? "neincluse"
                          : "-"}
                    </strong>
                  </p>
                  <p data-testid="intake-v6-led-strip-total">
                    Banda total: <strong className="text-slate-200">{formatMl(totalLedStripLengthM)}</strong>
                  </p>
                </>
              ) : null}
              <p>
                Consum LED:{" "}
                <strong className="text-slate-200">
                  {estimatedLedWatts != null ? `${estimatedLedWatts.toFixed(2)} W` : "-"}
                </strong>
              </p>
              {showElectricalFields ? (
                <>
                  <p>
                    PSU (+{psuReservePercent}%):{" "}
                    <strong className="text-slate-200">
                      {requiredPsuWatts != null ? `${requiredPsuWatts.toFixed(2)} W` : "-"}
                    </strong>
                  </p>
                  <p>
                    Surse: <strong className="text-slate-200">{psuLabel}</strong>
                  </p>
                  {psuAllocationStatus && psuAllocationStatus !== "ok" ? (
                    <p className="text-amber-200">PSU: {psuAllocationStatus}</p>
                  ) : null}
                </>
              ) : null}
            </div>
          </IntakeV6TechnicalDetailsAccordion>
        </div>
      )}
    </div>
  );
}

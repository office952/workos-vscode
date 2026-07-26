import type { ReactNode } from "react";
import type { IntakeV6ConfirmSummaryViewModel } from "@/lib/intakeV6/intakeV6ConfirmSummary";
import {
  INTAKE_V6_CANT_VOLUM_LABEL,
  INTAKE_V6_CANT_VOLUM_LABEL_LOWER,
  INTAKE_V6_CANT_VOLUM_LETTERS_LABEL,
} from "@/lib/intakeV6/intakeV6ReturnFinishOptions";
import {
  formatConfirmSummaryM,
  formatConfirmSummaryM2,
} from "@/lib/intakeV6/intakeV6ConfirmSummary";
import { formatEdgeCantDepthMm, formatEdgeCantMl } from "@/lib/intakeV6/intakeV6EdgeCantDisplay";
import IntakeV6TechnicalDetailsAccordion from "./atoms/IntakeV6TechnicalDetailsAccordion";
import IntakeV6OperatorWorkSummaryTechnicalDetails from "./IntakeV6OperatorWorkSummaryTechnicalDetails";
import { v6 } from "./atoms/intakeV6Presentation";
import { INTAKE_V6_OWNER_ROLE_LABEL_LETTERS, INTAKE_V6_OWNER_ROLE_LABEL_LOGO } from "@/lib/intakeV6/intakeV6LayerRoleOptions";

function SummaryRow({
  label,
  value,
  testId,
  hint,
}: {
  label: string;
  value: string;
  testId?: string;
  hint?: string;
}) {
  return (
    <div className="flex justify-between gap-4 border-b border-wo-border-strong py-2">
      <dt className="text-slate-500" title={hint}>
        {label}
      </dt>
      <dd className={`${v6.mono} max-w-[72%] break-words text-right text-wo-text-primary`} data-testid={testId}>
        {value}
      </dd>
    </div>
  );
}

function SummarySection({
  title,
  testId,
  children,
}: {
  title: string;
  testId: string;
  children: ReactNode;
}) {
  return (
    <div className={`${v6.card} mb-4`} data-testid={testId}>
      <h3 className={`mb-2 ${v6.sectionTitle}`}>{title}</h3>
      <dl className="grid gap-0 text-[12px]">{children}</dl>
    </div>
  );
}

function formatLayerRollWidth(value: number | null | undefined): string {
  return value != null && Number.isFinite(value) && value > 0 ? `rola ${Math.round(value)} mm` : "rola n/a";
}

function formatDepth(value: number | null | undefined): string {
  return formatEdgeCantDepthMm(value);
}

function edgeCantScopeLabel(scope: "letters" | "artwork" | "mixed"): string {
  if (scope === "letters") return "Litere";
  if (scope === "artwork") return "Emblemă";
  return "Mixt";
}

function normalizeForTextMatch(value: string): string {
  return value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
}

function formatSummaryCount(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return "n/a";
  return String(value);
}

function formatLetterWorkStatus(summary: IntakeV6ConfirmSummaryViewModel): string {
  return `${formatSummaryCount(summary.structure.realLettersCount)} - ${
    summary.lighting.illuminated ? "luminoase" : "neluminoase"
  }`;
}

function resolveEmblemLightingStatus(summary: IntakeV6ConfirmSummaryViewModel): string {
  if (!summary.lighting.illuminated) return "neluminoase";
  const label = normalizeForTextMatch(summary.lighting.emblemLightingLabel);
  if (label.includes("luminoasa")) return "luminoase";
  if (label.includes("neluminoasa") || label.includes("neincluse")) return "neluminoase";
  return "decizie iluminare";
}

function formatEmblemWorkStatus(summary: IntakeV6ConfirmSummaryViewModel): string {
  return `${formatSummaryCount(summary.structure.artworkCount)} - ${resolveEmblemLightingStatus(summary)}`;
}

function formatEmblemLedModuleFallback(label: string): string {
  const normalized = normalizeForTextMatch(label);
  if (normalized.includes("neluminoasa") || normalized.includes("neincluse")) return "neluminoasă";
  if (normalized.includes("decizie")) return "decizie iluminare";
  return "n/a";
}

export default function IntakeV6ConfirmOperationalSummary({
  summary,
  variant = "full",
  acmPanelOnly = false,
}: {
  summary: IntakeV6ConfirmSummaryViewModel;
  variant?: "operator" | "technical" | "full";
  /** ACM panel-alone: hide VL letter / cant / adhesive teaching blocks. */
  acmPanelOnly?: boolean;
}) {
  const showOperator = variant === "operator" || variant === "full";
  const showTechnical = variant === "technical" || variant === "full";
  const operatorEdgeCantOnly = variant === "operator";
  const psuProposal =
    summary.lighting.psuConfiguration.length > 0
      ? summary.lighting.psuConfiguration.map((w) => `${w} W`).join(" + ")
      : "—";

  if (acmPanelOnly) {
    return (
      <div className="space-y-3" data-testid="intake-v6-confirm-acm-panel-only-root">
        <SummarySection title="Rezumat — panou ACM" testId="intake-v6-confirm-acm-panel-only">
          <SummaryRow
            label="Produs ofertat"
            value="Panou Alucobond casetat"
            testId="intake-v6-confirm-acm-product"
          />
          <SummaryRow
            label="Litere / cant / adeziv"
            value="În afara ofertei — nu se cere"
            testId="intake-v6-confirm-acm-letter-out-of-scope"
          />
          <SummaryRow
            label="Layere SVG"
            value={String(summary.structure.layerCount)}
            testId="intake-v6-confirm-layers"
          />
        </SummarySection>
        <p
          className="rounded border border-cyan-500/20 bg-cyan-500/5 px-2.5 py-2 text-[11px] leading-relaxed text-slate-400"
          data-testid="intake-v6-confirm-acm-panel-only-hint"
        >
          Prețul panoului vine din liniile ACM (CUT / V-groove / față / asamblare). Nu din adeziv cant
          litere.
        </p>
      </div>
    );
  }

  return (
    <>
      {showOperator ? (
        <>
      <SummarySection title="Rezumat lucrare" testId="intake-v6-confirm-structure">
        <SummaryRow
          label={INTAKE_V6_OWNER_ROLE_LABEL_LETTERS}
          value={formatLetterWorkStatus(summary)}
          testId="intake-v6-confirm-volumetric-letters"
          hint="Layere confirmate ca litere volumetrice in lucrare."
        />
        <SummaryRow
          label={INTAKE_V6_OWNER_ROLE_LABEL_LOGO}
          value={formatEmblemWorkStatus(summary)}
          testId="intake-v6-confirm-emblem-count"
          hint="Elemente confirmate ca emblemă/logo, cu statusul iluminării."
        />
        <SummaryRow
          label="Piese plasate în layout"
          value={summary.structure.childPartsCount != null ? String(summary.structure.childPartsCount) : "—"}
          testId="intake-v6-confirm-layout-parts"
          hint="Total piese luate în calcul pentru preview: piese producție + artwork."
        />
        <SummaryRow
          label="Layere SVG"
          value={String(summary.structure.layerCount)}
          testId="intake-v6-confirm-layers"
        />
      </SummarySection>

      <SummarySection title="Finish / Material" testId="intake-v6-confirm-finish">
        {summary.finish.letterRows.length > 0 ? (
          summary.finish.letterRows.map((row) => (
            <SummaryRow
              key={row.groupKey}
              label={`Litere ${row.layerName}`}
              value={[
                `față ${row.faceLabel}`,
                formatLayerRollWidth(row.faceRollWidthMm),
                `${INTAKE_V6_CANT_VOLUM_LABEL_LOWER} ${row.returnLabel}`,
                formatDepth(row.returnDepthMm),
                formatConfirmSummaryM(row.perimeterM),
              ].join(" · ")}
              testId={`intake-v6-confirm-letter-finish-${row.groupKey}`}
            />
          ))
        ) : (
          <>
            <SummaryRow
              label="Față litere"
              value={summary.finish.letterFaceLabel}
              testId="intake-v6-confirm-letter-face"
            />
            <SummaryRow
              label={INTAKE_V6_CANT_VOLUM_LETTERS_LABEL}
              value={summary.finish.letterReturnLabel}
              testId="intake-v6-confirm-letter-return"
            />
          </>
        )}
        {summary.finish.artworkRows.map((row) => (
          <SummaryRow
            key={row.layerKey}
            label={`${INTAKE_V6_OWNER_ROLE_LABEL_LOGO} ${row.layerName}`}
            value={[
              row.executionLabel,
              row.printTransparencyLabel,
              `${INTAKE_V6_CANT_VOLUM_LABEL_LOWER} ${row.returnLabel}`,
              formatDepth(row.returnDepthMm),
              formatConfirmSummaryM2(row.areaM2),
            ].join(" · ")}
            testId={`intake-v6-confirm-artwork-finish-${row.layerKey}`}
          />
        ))}
        <SummaryRow label="Vinil față" value={summary.finish.vinylFace} testId="intake-v6-confirm-vinyl" />
        <SummaryRow
          label="Print / Laminare"
          value={summary.finish.printLaminate}
          testId="intake-v6-confirm-print"
        />
        <SummaryRow label="Backing / Forex" value={summary.finish.backingForex} testId="intake-v6-confirm-backing" />
        <SummaryRow
          label="Șanfren față"
          value={summary.finish.faceBevelMandatory}
          testId="intake-v6-confirm-face-bevel"
        />
        <SummaryRow
          label="Șanfren spate"
          value={summary.finish.backBevelLabel}
          testId="intake-v6-confirm-back-bevel"
        />
      </SummarySection>

      <SummarySection title="Geometrie ofertare" testId="intake-v6-confirm-geometry-block">
        <SummaryRow
          label="Arie brută față / gross"
          value={formatConfirmSummaryM2(summary.geometry.grossFaceAreaM2)}
          testId="intake-v6-confirm-gross-area"
        />
        <SummaryRow
          label="Arie plexiglas ofertabilă / nesting"
          value={formatConfirmSummaryM2(summary.geometry.quoteablePlexiglasM2)}
          testId="intake-v6-confirm-plexiglas-area"
        />
        <SummaryRow
          label="Perimetru LED litere / exterior"
          value={formatConfirmSummaryM(summary.geometry.ledPerimeterM)}
          testId="intake-v6-confirm-led-perimeter"
        />
        <SummaryRow
          label="Perimetru CNC față"
          value={formatConfirmSummaryM(summary.geometry.cncPerimeterM)}
          testId="intake-v6-confirm-cnc-perimeter"
        />
        <SummaryRow
          label="Perimetru cant total"
          value={formatConfirmSummaryM(summary.geometry.returnPerimeterM)}
          testId="intake-v6-confirm-return-perimeter"
        />
      </SummarySection>

      <SummarySection title={INTAKE_V6_CANT_VOLUM_LABEL} testId="intake-v6-confirm-edge-cant">
        <SummaryRow
          label="Finisaj cant / volum"
          value={summary.edgeCant.finishLabel}
          testId="intake-v6-confirm-edge-cant-finish"
        />
        <SummaryRow
          label="Perimetru cant total"
          value={formatConfirmSummaryM(summary.edgeCant.realPerimeterM)}
          testId="intake-v6-confirm-edge-cant-calculated"
        />
        {summary.edgeCant.groups.map((group) => (
          <SummaryRow
            key={group.key}
            label={`${edgeCantScopeLabel(group.scope)} · ${formatDepth(group.depthMm)} · ${group.finishLabel}`}
            value={`${formatConfirmSummaryM(group.perimeterM)} · ${group.layerCount} layer${
              group.layerCount === 1 ? "" : "e"
            }`}
            testId={`intake-v6-confirm-edge-cant-group-${group.key}`}
          />
        ))}
        <SummaryRow
          label="Cant pentru preț"
          value={formatConfirmSummaryM(summary.edgeCant.pricedCantM)}
          testId="intake-v6-confirm-edge-cant-priced"
        />
        <SummaryRow
          label="Pierdere ofertare"
          value={
            summary.edgeCant.wastePercent != null
              ? `+${summary.edgeCant.wastePercent.toFixed(0)}%`
              : "n/a"
          }
          testId="intake-v6-confirm-edge-cant-waste"
        />
        <SummaryRow
          label="Adeziv cant"
          value={formatEdgeCantMl(summary.edgeCant.adhesiveMl)}
          testId="intake-v6-confirm-edge-cant-adhesive"
        />
        {!operatorEdgeCantOnly ? (
          <>
            <SummaryRow
              label="Cant calculat backend"
              value={formatConfirmSummaryM(summary.edgeCant.calculatedCantM)}
              testId="intake-v6-confirm-edge-cant-backend-calculated"
            />
            {summary.edgeCant.oracalAreaM2 != null ? (
              <SummaryRow
                label="Oracal 651 / cant volum — suprafață"
                value={formatConfirmSummaryM2(summary.edgeCant.oracalAreaM2)}
                testId="intake-v6-confirm-edge-cant-oracal-area"
              />
            ) : (
              <SummaryRow
                label="Oracal 651 / cant volum"
                value="n/a — finisaj cant nu este Oracal 651"
                testId="intake-v6-confirm-edge-cant-oracal-absent"
              />
            )}
            {summary.edgeCant.oracalCost != null ? (
              <SummaryRow
                label="Oracal 651 — cost estimat material"
                value={`${summary.edgeCant.oracalCost.toFixed(2)} ${summary.edgeCant.oracalCurrency}`}
                testId="intake-v6-confirm-edge-cant-oracal-cost"
              />
            ) : null}
            {summary.edgeCant.operations.length > 0 ? (
              summary.edgeCant.operations.map((op) => (
                <SummaryRow
                  key={op.key}
                  label={`Operație preview: ${op.label}`}
                  value={`${op.quantity.toFixed(2)} ${op.unit === "linear_meter" ? "m" : op.unit}`}
                  testId={`intake-v6-confirm-edge-cant-op-${op.key}`}
                />
              ))
            ) : (
              <SummaryRow
                label="Operații preview cant / volum"
                value="calcul indisponibil"
                testId="intake-v6-confirm-edge-cant-ops-missing"
              />
            )}
          </>
        ) : null}
      </SummarySection>

      {summary.lighting.illuminated ? (
        <SummarySection title="Iluminare" testId="intake-v6-confirm-lighting">
          <SummaryRow
            label="LED litere — module"
            value={
              summary.lighting.letterLedModules != null
                ? String(summary.lighting.letterLedModules)
                : "—"
            }
            testId="intake-v6-confirm-led-letters-modules"
          />
          <SummaryRow
            label="LED emblemă - arie"
            value={formatConfirmSummaryM2(summary.lighting.emblemOutboxAreaM2)}
            testId="intake-v6-confirm-led-emblem-area"
          />
          <SummaryRow
            label="LED emblemă — status"
            value={summary.lighting.emblemLightingLabel}
            testId="intake-v6-confirm-led-emblem-status"
          />
          <SummaryRow
            label="LED emblemă — module"
            value={
              summary.lighting.emblemLedModules != null
                ? String(summary.lighting.emblemLedModules)
                : formatEmblemLedModuleFallback(summary.lighting.emblemLightingLabel)
            }
            testId="intake-v6-confirm-led-emblem-modules"
          />
          <SummaryRow
            label="LED total — module"
            value={
              summary.lighting.totalLedModules != null
                ? String(summary.lighting.totalLedModules)
                : "—"
            }
            testId="intake-v6-confirm-led-total-modules"
          />
          <SummaryRow
            label="Putere modul"
            value={
              summary.lighting.moduleWattageW != null
                ? `${summary.lighting.moduleWattageW.toFixed(2)} W / modul`
                : "—"
            }
            testId="intake-v6-confirm-module-wattage"
          />
          <SummaryRow
            label="Consum LED total"
            value={
              summary.lighting.totalLedWatts != null
                ? `${summary.lighting.totalLedWatts.toFixed(2)} W`
                : "—"
            }
            testId="intake-v6-confirm-led-watts"
          />
          <SummaryRow
            label="PSU necesar +30%"
            value={
              summary.lighting.requiredPsuWatts != null
                ? `${summary.lighting.requiredPsuWatts.toFixed(2)} W`
                : "—"
            }
            testId="intake-v6-confirm-psu-required"
          />
          <SummaryRow label="Surse propuse" value={psuProposal} testId="intake-v6-confirm-psu-config" />
        </SummarySection>
      ) : null}
        </>
      ) : null}

      {showTechnical ? (
        <>
      <IntakeV6TechnicalDetailsAccordion
        testId="intake-v6-confirm-operational-technical-details"
        title="Detalii tehnice"
      >
        <IntakeV6OperatorWorkSummaryTechnicalDetails
          counts={{ productionParts: summary.structure.realLettersCount }}
          testId="intake-v6-confirm-work-summary-technical"
        />
        <SummarySection title="Counters tehnici" testId="intake-v6-confirm-technical-structure">
          <SummaryRow
            label="Child parts (alias tehnic)"
            value={summary.structure.childPartsCount != null ? String(summary.structure.childPartsCount) : "—"}
            testId="intake-v6-confirm-child-parts"
          />
          <SummaryRow
            label="real_letters_count (alias tehnic)"
            value={summary.structure.realLettersCount != null ? String(summary.structure.realLettersCount) : "—"}
            testId="intake-v6-confirm-real-letters"
          />
          <SummaryRow
            label="Nesting mode"
            value={summary.nesting.previewOnly ? "preview only" : "live"}
            testId="intake-v6-confirm-nesting-mode"
          />
          <SummaryRow
            label="Layout activ"
            value={summary.nesting.activeLayout ? "da" : "nu"}
            testId="intake-v6-confirm-nesting-active"
          />
          <SummaryRow
            label="Piese nestable"
            value={summary.nesting.nestableParts != null ? String(summary.nesting.nestableParts) : "—"}
            testId="intake-v6-confirm-nestable-parts"
          />
          <SummaryRow
            label="Artwork parts"
            value={summary.nesting.artworkParts != null ? String(summary.nesting.artworkParts) : "—"}
            testId="intake-v6-confirm-nesting-artwork"
          />
          <SummaryRow
            label="Stoc consumat"
            value={summary.nesting.stockConsumed ? "da" : "nu"}
            testId="intake-v6-confirm-stock-consumed"
          />
        </SummarySection>
      </IntakeV6TechnicalDetailsAccordion>

      {summary.warnings.length > 0 ? (
        <div className={`${v6.card} mb-4`} data-testid="intake-v6-confirm-warnings">
          <h3 className={`mb-2 ${v6.sectionTitle} text-amber-200`}>
            Warnings / blockers
          </h3>
          <ul className="space-y-2 text-[11px] text-amber-200">
            {summary.warnings.map((warning) => (
              <li key={warning.code} data-testid={`intake-v6-confirm-warning-${warning.code}`}>
                • {warning.message}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
        </>
      ) : null}
    </>
  );
}




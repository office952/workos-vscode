import { useState } from "react";
import { Link } from "react-router-dom";
import {
  CheckCircle2,
  AlertTriangle,
  Save,
  X,
  Package,
  Cog,
  Box,
  ChevronDown,
  ChevronRight,
  ChevronsUpDown,
  ArrowLeft,
  ExternalLink,
} from "lucide-react";
import { StatusBadge } from "@/components/workos/design-system";
import type {
  InventoryMaterialEntity,
  ProductTemplateComponent,
  ProductTemplateMaterial,
  ProductTemplateOperation,
} from "@/lib/api";
import type { DerivedConstructionStage } from "@/features/product-system/templateConstructionStages";
import {
  CALIBRATION_DURATION_TOOLTIP,
  formatComponentDisplayName,
  formatInternalComponentMinutes,
  formatMaterialQuantityLabel,
  formatOperationCalibrationLabel,
  hasFormulaLineMetadata,
} from "@/features/product-system/templateCalibrationDisplay";
export interface StudioValidationRule {
  key: string;
  label: string;
  ok: boolean;
}

export interface StudioDraftCounts {
  components: number;
  operations: number;
  materials: number;
}

export interface ConstructionStageStyle {
  icon: React.ReactNode;
  color: string;
  bgColor: string;
  borderColor: string;
}

export function TemplateEditorCommandBar({
  templateCode,
  displayName,
  active,
  isNew,
  counts,
  passedCount,
  totalValidation,
  canSave,
  saving,
  onSave,
  onCancel,
  onChangeTemplate,
  onBackToLibrary,
  pricingHref,
  changeTemplateLabel = "Schimbă template",
  readOnly = false,
}: {
  templateCode: string;
  displayName: string;
  active: boolean;
  isNew: boolean;
  counts: StudioDraftCounts;
  passedCount: number;
  totalValidation: number;
  canSave: boolean;
  saving: boolean;
  onSave: () => void;
  onCancel: () => void;
  onChangeTemplate?: () => void;
  onBackToLibrary?: () => void;
  pricingHref?: string;
  changeTemplateLabel?: string;
  readOnly?: boolean;
}) {
  const codeLabel = templateCode.trim() || (isNew ? "Șablon nou" : "—");
  const metricsLine = [
    `${counts.components} componente`,
    `${counts.operations} operații`,
    `${counts.materials} materiale`,
  ].join(" · ");

  const saveEnabled = canSave && !readOnly;

  return (
    <header className="flex flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3 bg-[#111827] border-b border-[#1E293B] shrink-0">
      {onBackToLibrary ? (
        <button
          type="button"
          onClick={onBackToLibrary}
          disabled={saving}
          className="flex items-center gap-1.5 px-2.5 py-1.5 text-[11px] font-semibold text-slate-400 hover:text-slate-200 border border-transparent hover:border-slate-600 rounded-lg transition-colors shrink-0"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Înapoi la șabloane
        </button>
      ) : null}
      <div className="flex items-center gap-2.5 min-w-0 flex-1 basis-[200px]">
        <Package className="w-5 h-5 text-purple-400 shrink-0" />
        <div className="min-w-0">
          <h2 className="text-[14px] font-bold text-slate-100 font-mono truncate">{codeLabel}</h2>
          {displayName ? (
            <p className="text-[12px] text-slate-300 truncate">{displayName}</p>
          ) : null}
        </div>
        <StatusBadge
          domain="productSystem"
          status={active ? "active" : "archived"}
          label={active ? "Activ" : "Arhivat"}
          className="shrink-0 text-[9px] uppercase rounded-full"
        />
      </div>

      <p className="text-[10px] text-slate-500 shrink-0 hidden lg:block">{metricsLine}</p>

      <div
        className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[10px] font-semibold border shrink-0 ${
          canSave
            ? "bg-emerald-900/15 text-emerald-400/90 border-emerald-700/25"
            : "bg-amber-900/15 text-amber-400/90 border-amber-700/25"
        }`}
        title="Validare design-time pentru salvare"
      >
        {canSave ? (
          <CheckCircle2 className="w-3.5 h-3.5" />
        ) : (
          <AlertTriangle className="w-3.5 h-3.5" />
        )}
        Validare {passedCount}/{totalValidation}
      </div>

      <div className="flex items-center gap-2 shrink-0 ml-auto">
        {onChangeTemplate ? (
          <button
            type="button"
            onClick={onChangeTemplate}
            disabled={saving}
            className="flex items-center gap-1.5 px-3 py-2 bg-[#0D1321] hover:bg-slate-800 text-slate-300 border border-[#1E293B] hover:border-slate-600 rounded-lg text-[11px] font-semibold transition-colors disabled:opacity-50"
          >
            <ChevronsUpDown className="w-3.5 h-3.5" /> {changeTemplateLabel}
          </button>
        ) : null}
        {pricingHref ? (
          <Link
            to={pricingHref}
            className="flex items-center gap-1.5 px-3 py-2 bg-cyan-950/30 hover:bg-cyan-900/40 text-cyan-300 border border-cyan-800/40 rounded-lg text-[11px] font-semibold transition-colors"
          >
            <ExternalLink className="w-3.5 h-3.5" /> Pricing
          </Link>
        ) : null}
        <button
          type="button"
          onClick={onCancel}
          disabled={saving}
          className="flex items-center gap-1.5 px-3 py-2 bg-transparent hover:bg-slate-800 text-slate-400 hover:text-slate-200 rounded-lg text-[12px] font-medium transition-colors disabled:opacity-50 border border-transparent hover:border-slate-700"
        >
          <X className="w-3.5 h-3.5" /> Anulează
        </button>
        {!readOnly ? (
          <button
            type="button"
            onClick={onSave}
            disabled={!saveEnabled || saving}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-[12px] font-bold transition-colors ${
              saveEnabled && !saving
                ? "bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-900/30"
                : "bg-slate-700/60 text-slate-500 cursor-not-allowed"
            }`}
          >
            <Save className="w-3.5 h-3.5" /> {saving ? "Salvare..." : "Salvează"}
          </button>
        ) : null}
      </div>

      <p className="w-full text-[10px] text-slate-500 lg:hidden">{metricsLine}</p>
    </header>
  );
}

export function TemplateConstructionStageRow({
  stages,
  selectedIndex,
  onSelectStage,
  getStageStyle,
  collapsible = true,
}: {
  stages: DerivedConstructionStage[];
  selectedIndex: number | null;
  onSelectStage: (componentIndex: number) => void;
  getStageStyle: (stage: DerivedConstructionStage) => ConstructionStageStyle;
  collapsible?: boolean;
}) {
  const [expanded, setExpanded] = useState(true);

  if (stages.length === 0) return null;

  const chips = (
    <div className="flex items-center gap-1 overflow-x-auto pb-0.5 scrollbar-thin">
      {stages.map((stage, i) => {
        const style = getStageStyle(stage);
        const isSelected = selectedIndex === stage.componentIndex;
        return (
          <div key={stage.code + "_" + i} className="flex items-center shrink-0">
            <button
              type="button"
              onClick={() => onSelectStage(stage.componentIndex)}
              className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border transition-all duration-200 ${
                isSelected
                  ? `${style.bgColor} ${style.borderColor} ${style.color} ring-1 ring-purple-500/40`
                  : `${style.bgColor} ${style.borderColor} ${style.color} opacity-80 hover:opacity-100`
              }`}
              title={stage.label}
            >
              <span className="flex h-4 w-4 items-center justify-center shrink-0 [&>svg]:h-3.5 [&>svg]:w-3.5">
                {style.icon}
              </span>
              <span className="text-[10px] font-semibold whitespace-nowrap">
                {stage.chipLabel}
              </span>
            </button>
            {i < stages.length - 1 ? (
              <ChevronRight className="w-3.5 h-3.5 mx-0.5 shrink-0 text-slate-600" />
            ) : null}
          </div>
        );
      })}
    </div>
  );

  if (!collapsible) {
    return chips;
  }

  return (
    <div>
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="flex items-center gap-1.5 text-[10px] text-slate-500 uppercase tracking-wide font-bold mb-2 hover:text-slate-400 transition-colors"
      >
        <ChevronDown
          className={`w-3.5 h-3.5 transition-transform ${expanded ? "rotate-0" : "-rotate-90"}`}
        />
        Etape construcție (orientativ)
      </button>
      {expanded ? chips : null}
    </div>
  );
}

function getComponentValidationItems(
  component: ProductTemplateComponent,
  materialsByCode: Map<string, InventoryMaterialEntity>
): { label: string; ok: boolean }[] {
  const typed =
    component._legacy !== true &&
    component.name.trim().length > 0 &&
    component.component_id.trim().length > 0;
  const hasOps =
    component.operations.length > 0 &&
    component.operations.every(
      (op) => op.code.trim().length > 0 && op.name.trim().length > 0
    );
  const hasMats =
    component.materials.length > 0 &&
    component.materials.every(
      (m) => m.materialCode.trim().length > 0 && materialsByCode.has(m.materialCode)
    );
  return [
    { label: "Identitate componentă completă", ok: typed },
    { label: "Operații definite", ok: hasOps },
    { label: "Materiale în registru", ok: hasMats },
  ];
}

export function ComponentDetailInsightPanel({
  selectedComponent,
  selectedIndex,
  typeDisplayLabel,
  templateCode,
  validation,
  preview,
  materialsByCode,
}: {
  selectedComponent: ProductTemplateComponent | null;
  selectedIndex: number | null;
  typeDisplayLabel: string;
  templateCode: string;
  validation: StudioValidationRule[];
  preview: React.ReactNode;
  materialsByCode: Map<string, InventoryMaterialEntity>;
}) {
  const [validationExpanded, setValidationExpanded] = useState(false);
  const [previewExpanded, setPreviewExpanded] = useState(false);
  const [calibrationExpanded, setCalibrationExpanded] = useState(false);
  const passedCount = validation.filter((v) => v.ok).length;

  const componentValidation =
    selectedComponent !== null
      ? getComponentValidationItems(selectedComponent, materialsByCode)
      : [];

  const totalMinutes =
    selectedComponent?.operations.reduce(
      (a, op) => a + (op.estimatedMinutes || 0),
      0
    ) ?? 0;
  const internalMinutesLabel = formatInternalComponentMinutes(totalMinutes);

  return (
    <aside className="w-full h-full flex flex-col min-h-0 bg-[#0D1321] overflow-y-auto scrollbar-thin">
      {selectedComponent === null || selectedIndex === null ? (
        <section className="p-6 flex flex-col items-center justify-center text-center min-h-[200px]">
          <LayersPlaceholder />
          <p className="text-[12px] text-slate-400 mt-3 leading-relaxed max-w-[220px]">
            Selectează o componentă pentru materiale, operații și validare.
          </p>
        </section>
      ) : (
        <>
          <section className="p-4 border-b border-[#1E293B]">
            <p className="text-[10px] font-bold text-purple-400 uppercase tracking-wide mb-1">
              #{selectedIndex + 1} · {typeDisplayLabel}
            </p>
            <h3 className="text-[14px] font-bold text-slate-100 leading-snug">
              {formatComponentDisplayName(selectedComponent.name) || "Fără nume"}
            </h3>
            <p className="text-[10px] text-slate-500 font-mono mt-1">
              {selectedComponent.component_id}
            </p>
            {internalMinutesLabel ? (
              <button
                type="button"
                onClick={() => setCalibrationExpanded((v) => !v)}
                className="text-[9px] text-slate-600 mt-2 hover:text-slate-500 transition-colors text-left"
                title={CALIBRATION_DURATION_TOOLTIP}
              >
                {internalMinutesLabel}
                <span className="ml-1 text-slate-700">· calibrare</span>
              </button>
            ) : null}
            {calibrationExpanded && internalMinutesLabel ? (
              <p className="text-[9px] text-slate-600 mt-1 leading-relaxed">{CALIBRATION_DURATION_TOOLTIP}</p>
            ) : null}
          </section>

          <section className="p-4 border-b border-[#1E293B]">
            <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wide mb-2 flex items-center gap-1">
              <Box className="w-3 h-3" /> Materiale ({selectedComponent.materials.length})
            </h4>
            {selectedComponent.materials.length === 0 ? (
              <p className="text-[11px] text-slate-500 italic">Niciun material definit.</p>
            ) : (
              <ul className="space-y-1.5">
                {selectedComponent.materials.map((m, i) => {
                  const inRegistry = materialsByCode.has(m.materialCode);
                  return (
                    <li
                      key={m.materialCode + "_" + i}
                      className="text-[11px] px-2 py-1.5 rounded-lg border border-[#1E293B] bg-[#111827]"
                    >
                      <p className="font-mono text-emerald-300/90 text-[10px]">
                        {m.materialCode || "—"}
                      </p>
                      <p className="text-slate-300 truncate">{m.name || "—"}</p>
                      <p className="text-[9px] text-slate-500 mt-0.5">
                        {formatMaterialQuantityLabel(m)}
                        {!inRegistry && m.materialCode ? (
                          <span className="text-red-400 ml-1">· lipsă din registru</span>
                        ) : null}
                      </p>
                      {hasFormulaLineMetadata(m) ? (
                        <p className="text-[9px] text-purple-400/80 mt-0.5">Cantitate: din formulă / Pricing Registry</p>
                      ) : null}
                    </li>
                  );
                })}
              </ul>
            )}
          </section>

          <section className="p-4 border-b border-[#1E293B]">
            <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wide mb-2 flex items-center gap-1">
              <Cog className="w-3 h-3" /> Operații ({selectedComponent.operations.length})
            </h4>
            {selectedComponent.operations.length === 0 ? (
              <p className="text-[11px] text-slate-500 italic">Nicio operație definită.</p>
            ) : (
              <ul className="space-y-1.5">
                {selectedComponent.operations.map((op, i) => (
                  <li
                    key={op.code + "_" + i}
                    className="text-[11px] px-2 py-1.5 rounded-lg border border-[#1E293B] bg-[#111827]"
                  >
                    <p className="font-mono text-blue-300/90 text-[10px]">{op.code || "—"}</p>
                    <p className="text-slate-300">{op.name || "—"}</p>
                    <p
                      className="text-[9px] text-slate-600 mt-0.5"
                      title={CALIBRATION_DURATION_TOOLTIP}
                    >
                      {formatOperationCalibrationLabel(op)}
                      {op.workcenter ? ` · ${op.workcenter}` : ""}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section className="p-4 border-b border-[#1E293B]">
            <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wide mb-2">
              Validare componentă
            </h4>
            <ul className="space-y-1">
              {componentValidation.map((item) => (
                <li
                  key={item.label}
                  className={`flex items-center gap-2 text-[10px] px-2 py-1 rounded ${
                    item.ok ? "text-emerald-400/90" : "text-amber-400/90"
                  }`}
                >
                  {item.ok ? (
                    <CheckCircle2 className="w-3 h-3 shrink-0" />
                  ) : (
                    <AlertTriangle className="w-3 h-3 shrink-0" />
                  )}
                  {item.label}
                </li>
              ))}
            </ul>
          </section>
        </>
      )}

      <section className="p-4 border-b border-[#1E293B]">
        <button
          type="button"
          onClick={() => setValidationExpanded((v) => !v)}
          className="w-full flex items-center justify-between text-[10px] font-bold text-slate-400 uppercase tracking-wide hover:text-slate-300 transition-colors"
        >
          <span>Detalii validare șablon</span>
          <span className="flex items-center gap-1.5 normal-case font-semibold">
            <span
              className={`px-1.5 py-0.5 rounded text-[9px] ${
                passedCount === validation.length
                  ? "text-emerald-400 bg-emerald-900/25"
                  : "text-amber-400 bg-amber-900/25"
              }`}
            >
              {passedCount}/{validation.length}
            </span>
            <ChevronDown
              className={`w-3.5 h-3.5 transition-transform ${validationExpanded ? "rotate-180" : ""}`}
            />
          </span>
        </button>
        {validationExpanded ? (
          <ul className="space-y-1.5 mt-2">
            {validation.map((v) => (
              <li
                key={v.key}
                className={`flex items-start gap-2 text-[10px] px-2 py-1.5 rounded-lg border ${
                  v.ok
                    ? "text-emerald-300/90 border-emerald-800/25 bg-emerald-900/10"
                    : "text-red-300/90 border-red-800/25 bg-red-900/10"
                }`}
              >
                {v.ok ? (
                  <CheckCircle2 className="w-3 h-3 shrink-0 mt-0.5" />
                ) : (
                  <AlertTriangle className="w-3 h-3 shrink-0 mt-0.5" />
                )}
                <span>{v.label}</span>
              </li>
            ))}
          </ul>
        ) : null}
      </section>

      <section className="p-4">
        <button
          type="button"
          onClick={() => setPreviewExpanded((v) => !v)}
          className="w-full flex items-center justify-between text-[10px] font-bold text-slate-500 uppercase tracking-wide hover:text-slate-400 transition-colors mb-2"
        >
          <span>Previzualizare orientativă</span>
          <ChevronDown
            className={`w-3.5 h-3.5 transition-transform ${previewExpanded ? "rotate-180" : ""}`}
          />
        </button>
        {previewExpanded ? (
          <div className="opacity-90 scale-[0.92] origin-top">{preview}</div>
        ) : null}
        {!previewExpanded && selectedComponent ? (
          <p className="text-[9px] text-slate-600 italic">
            Stratificare vizuală — nu e randare tehnică ({templateCode})
          </p>
        ) : null}
      </section>
    </aside>
  );
}

function LayersPlaceholder() {
  return (
    <svg
      className="w-10 h-10 text-slate-600"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
    >
      <path d="M12 2L2 7l10 5 10-5-10-5z" />
      <path d="M2 17l10 5 10-5" />
      <path d="M2 12l10 5 10-5" />
    </svg>
  );
}

export function ComponentTimelineWrap({
  index,
  isLast,
  children,
}: {
  index: number;
  isLast: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="flex gap-3">
      <div className="flex flex-col items-center w-9 shrink-0 pt-3">
        <span className="w-7 h-7 flex items-center justify-center rounded-full bg-purple-500/15 border border-purple-500/35 text-[11px] font-bold text-purple-300">
          {index + 1}
        </span>
        {!isLast ? <div className="w-px flex-1 min-h-[12px] bg-[#2A3548] mt-1" /> : null}
      </div>
      <div className="flex-1 min-w-0 pb-1">{children}</div>
    </div>
  );
}

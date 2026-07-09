import { useMemo, useState } from "react";
import { Layers } from "lucide-react";
import type { ProductTemplateAvailabilityItem, ProductTemplateEntity } from "@/lib/api";
import {
  assessComponentFirstContractDrift,
  componentFirstContractCheckLabel,
  componentFirstContractCheckTone,
  componentFirstDriftLabel,
  componentFirstSourceDescription,
  componentFirstSourceLabel,
  componentFirstSourceTone,
  COMPONENT_FIRST_COMPOSER_TEMPLATE_CODE,
  normalizeComponentFirstTemplateCode,
  type ComponentFirstTemplateCode,
} from "./componentFirstReadonlyCompleteness";
import {
  assessComponentFirstDossierAlignment,
  COMPONENT_FIRST_DOSSIER_CONTRACT_FIXTURE,
  componentFirstDossierRuntimeLinkLabel,
  componentFirstOverallAlignmentLabel,
  componentFirstOverallAlignmentTone,
  type ComponentFirstDossierContractEntry,
  type ComponentFirstDossierForbiddenNow,
} from "./componentFirstReadonlyDossierAlignment";
import {
  buildComponentFirstOwnerSummary,
  componentFirstOwnerStatusTone,
} from "./componentFirstReadonlyOwnerSummary";
import {
  assessComponentFirstFormSystemReadiness,
  componentFirstFormReadinessLabel,
  componentFirstFormReadinessTone,
  componentFirstFormRuntimeLinkLabel,
  type ComponentFirstFormReadinessEntry,
} from "./componentFirstReadonlyFormSystemReadiness";
import {
  assessComponentFirstProductTruthMapping,
  COMPONENT_FIRST_PRODUCT_TRUTH_COMPACT_PATH_SUMMARIES,
  componentFirstProductTruthMappingLabel,
  componentFirstProductTruthMappingTone,
  componentFirstProductTruthRuntimeLinkLabel,
  type ComponentFirstProductTruthMappingEntry,
} from "./componentFirstReadonlyProductTruthMapping";
import {
  assessComponentFirstProductDefinitionReadiness,
  componentFirstProductDefinitionReadinessLabel,
  componentFirstProductDefinitionReadinessTone,
  componentFirstProductDefinitionRuntimeLinkLabel,
} from "./componentFirstReadonlyProductDefinitionReadiness";
import {
  buildComponentFirstReadonlySetModel,
  type ComponentFirstReadonlyComponent,
  type ComponentFirstReadonlySetModel,
} from "./componentFirstReadonlySetModel";
import {
  ComponentFirstReadonlySettingsSheet,
  componentFirstDisplayName,
  ComponentFirstSemanticLabel,
  dossierEntryForTemplate,
  isComponentFirstComposer,
  type ComponentFirstSettingsTarget,
  truthOwnerLabel,
} from "./ComponentFirstReadonlySettingsSheet";
import {
  ComponentFirstStatusStrip,
  ReadonlyCardFooter,
  ReadonlyCardShell,
  ReadonlyLinkButton,
  ReadonlyStatusChip,
} from "./componentFirstReadonlyUiShared";
import { getProductTemplateIconConfig } from "./productTemplateIconRegistry";

export type ComponentFirstCandidateTab =
  | "overview"
  | "components"
  | "dossier"
  | "form-system"
  | "product-truth"
  | "guards-audit";

const CANDIDATE_TABS: Array<{ id: ComponentFirstCandidateTab; label: string; testId: string }> = [
  { id: "overview", label: "Overview", testId: "product-system-component-first-tab-overview" },
  { id: "components", label: "Components", testId: "product-system-component-first-tab-components" },
  { id: "dossier", label: "Dossier", testId: "product-system-component-first-tab-dossier" },
  { id: "form-system", label: "Form System", testId: "product-system-component-first-tab-form-system" },
  { id: "product-truth", label: "Product Truth", testId: "product-system-component-first-tab-product-truth" },
  { id: "guards-audit", label: "Guards / Audit", testId: "product-system-component-first-tab-guards-audit" },
];

export type ComponentFirstDetailPanelSection = "overview" | "components" | "dossier" | "guards-audit";

const DETAIL_PANEL_TABS: Array<{ id: ComponentFirstDetailPanelSection; label: string; testId: string }> = [
  { id: "overview", label: "Overview", testId: "product-system-component-first-tab-overview" },
  { id: "components", label: "Components", testId: "product-system-component-first-tab-components" },
  { id: "dossier", label: "Dossier", testId: "product-system-component-first-tab-dossier" },
  { id: "guards-audit", label: "Guards", testId: "product-system-component-first-tab-guards-audit" },
];

const DOSSIER_FORBIDDEN_LABELS: Record<ComponentFirstDossierForbiddenNow, string> = {
  task_materialization: "No task materialization",
  execution_plan: "No ExecutionPlan",
  product_aggregate_runtime: "No ProductAggregate",
  pricing: "No Pricing",
  quote_order: "No Quote / Order",
  work_intake_exposure: "No Work Intake exposure",
};

function productTruthPrefixForTemplate(templateCode: string): string | null {
  const label = componentFirstDisplayName(templateCode);
  const summary = COMPONENT_FIRST_PRODUCT_TRUTH_COMPACT_PATH_SUMMARIES.find(
    (entry) => entry.label === label.toUpperCase() || entry.label === label
  );
  return summary?.pathPrefix ?? null;
}

function formEntryForComponent(
  templateCode: string,
  entries: ComponentFirstFormReadinessEntry[]
): ComponentFirstFormReadinessEntry | undefined {
  return entries.find(
    (entry) => normalizeComponentFirstTemplateCode(entry.templateCode) === normalizeComponentFirstTemplateCode(templateCode)
  );
}

function groupProductTruthByTemplate(
  entries: ComponentFirstProductTruthMappingEntry[]
): Map<string, ComponentFirstProductTruthMappingEntry[]> {
  const map = new Map<string, ComponentFirstProductTruthMappingEntry[]>();
  for (const entry of entries) {
    const key = normalizeComponentFirstTemplateCode(entry.templateCode);
    const list = map.get(key) ?? [];
    list.push(entry);
    map.set(key, list);
  }
  return map;
}

function TemplateIcon({ templateCode, compact }: { templateCode: string; compact?: boolean }) {
  const iconConfig = getProductTemplateIconConfig(
    templateCode,
    isComponentFirstComposer(templateCode) ? "candidate_product" : "internal_module"
  );
  const Icon = iconConfig.Icon;
  const size = compact ? "h-9 w-9" : "h-11 w-11";
  const inner = compact ? "h-5 w-5" : "h-6 w-6";

  return (
    <div
      className={`${size} flex shrink-0 items-center justify-center rounded-xl border`}
      style={{
        color: iconConfig.color,
        backgroundColor: iconConfig.backgroundColor,
        borderColor: iconConfig.borderColor,
      }}
    >
      {iconConfig.iconUrl ? (
        <span
          aria-hidden="true"
          className={`${inner} block`}
          style={{
            backgroundColor: "currentColor",
            mask: `url(${iconConfig.iconUrl}) center / contain no-repeat`,
            WebkitMask: `url(${iconConfig.iconUrl}) center / contain no-repeat`,
          }}
        />
      ) : Icon ? (
        <Icon aria-hidden="true" className={inner} />
      ) : null}
    </div>
  );
}

function ComponentFirstForbiddenSummary({ compact = false }: { compact?: boolean }) {
  return (
    <div
      data-testid="product-system-component-first-forbidden-summary"
      className="rounded-lg border border-slate-800/90 bg-[#0D1321]/90 px-3 py-2 text-[10px] text-slate-300"
    >
      <p className="font-bold uppercase tracking-wide text-slate-400">Forbidden capabilities (candidate set)</p>
      {compact ? (
        <p className="mt-1">
          Not exposed in Work Intake · No Pricing / Quote / Order / Execution · No ProductDefinition runtime /
          ProductAggregate / TaskGraph / ExecutionPlan · Owner GO required
        </p>
      ) : (
        <ul className="mt-1.5 space-y-0.5">
          <li>Not exposed in Work Intake</li>
          <li>No Pricing / Quote / Order / Execution</li>
          <li>No ProductDefinition runtime / ProductAggregate / TaskGraph / ExecutionPlan</li>
          <li>No task materialization · No Product Truth write · Activation requires owner GO</li>
        </ul>
      )}
    </div>
  );
}

function ComponentFirstProductComposerCard({
  model,
  variant,
  onViewProductSettings,
  onViewProductDossier,
  onViewComponents,
}: {
  model: ComponentFirstReadonlySetModel;
  variant: "overview" | "compact";
  onViewProductSettings: () => void;
  onViewProductDossier: () => void;
  onViewComponents: () => void;
}) {
  const testId =
    variant === "overview"
      ? "product-system-component-first-product-card"
      : "product-system-component-first-composer-card";

  return (
    <ReadonlyCardShell
      testId={testId}
      className="border-purple-800/40 bg-[#111827] hover:border-purple-600/40 hover:bg-[#131B2E]"
    >
      <div className="flex min-h-[5rem] items-start gap-3">
        <TemplateIcon templateCode={model.composerTemplateCode} compact={variant === "compact"} />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-[13px] font-bold text-slate-100">
              {variant === "overview" ? "Litere volumetrice component-first" : model.composerTemplateCode}
            </p>
            <ReadonlyStatusChip label="Product Template / Composer" tone="purple" />
          </div>
          <p className="mt-0.5 font-mono text-[11px] font-bold text-slate-200">{model.composerTemplateCode}</p>
          {variant === "overview" ? (
            <p className="mt-0.5 text-[12px] text-slate-400">Component-first letters candidate composer</p>
          ) : null}
          <div className="mt-2 flex flex-wrap gap-1">
            <ReadonlyStatusChip label="INACTIVE" tone="cyan" />
            <ReadonlyStatusChip label="CANDIDATE" tone="cyan" />
            <ReadonlyStatusChip label="READONLY" tone="cyan" />
            <ReadonlyStatusChip label="NOT OFFERABLE" tone="rose" />
          </div>
          {variant === "overview" ? (
            <>
              <ComponentFirstSemanticLabel />
              <p
                data-testid="product-system-component-first-completeness-count"
                className="mt-2 text-[11px] font-bold text-slate-300"
              >
                Live rows: {model.foundRowCount}/{model.expectedRowCount} · {model.components.length} components · Work
                Intake: no · Owner GO required
              </p>
              <details className="mt-2 text-[10px] text-slate-400">
                <summary className="cursor-pointer font-semibold text-slate-300">Composer details</summary>
                <div className="mt-1 grid gap-1 text-slate-300">
                  <p>Role: compune componentele</p>
                  <p>Owns material truth: no · Owns operation truth: no</p>
                  <p>Pricing / Quote / Order / Execution: no</p>
                </div>
              </details>
            </>
          ) : (
            <p className="mt-2 text-[10px] text-slate-400">
              Composer — coordinates components only · does not own material truth · does not own operation truth ·
              no module links: {String(model.noModuleLinks)}
            </p>
          )}
        </div>
      </div>
      <ReadonlyCardFooter>
        <ReadonlyLinkButton
          label="View product settings"
          testId="product-system-component-first-view-product-settings"
          onClick={onViewProductSettings}
        />
        <ReadonlyLinkButton
          label="View product dossier"
          testId="product-system-component-first-view-product-dossier"
          onClick={onViewProductDossier}
        />
        <ReadonlyLinkButton
          label="View components"
          testId="product-system-component-first-view-components"
          onClick={onViewComponents}
        />
      </ReadonlyCardFooter>
    </ReadonlyCardShell>
  );
}

function ComponentFirstComponentEntityCard({
  component,
  dossierEntry,
  formEntry,
  productTruthPrefix,
  onViewComponentSettings,
  onViewComponentDossier,
}: {
  component: ComponentFirstReadonlyComponent;
  dossierEntry?: ComponentFirstDossierContractEntry;
  formEntry?: ComponentFirstFormReadinessEntry;
  productTruthPrefix: string | null;
  onViewComponentSettings: () => void;
  onViewComponentDossier: () => void;
}) {
  const displayName = componentFirstDisplayName(component.templateCode);
  const fieldGroups =
    formEntry && formEntry.role === "component_template" ? formEntry.fieldGroups.join(", ") : null;
  const blockerCount = component.blockers.length;
  const dependencySummary = component.dependencies.length
    ? `${component.dependencies.length} dependencies`
    : "no dependencies";

  return (
    <ReadonlyCardShell testId={`product-system-component-first-component-${component.templateCode}`}>
      <div className="flex min-h-[4.5rem] items-start gap-2.5">
        <TemplateIcon templateCode={component.templateCode} compact />
        <div className="min-w-0 flex-1">
          <p className="text-[13px] font-bold text-slate-100">{displayName}</p>
          <p className="font-mono text-[11px] font-bold text-slate-200">{component.templateCode}</p>
          <div className="mt-1.5 flex flex-wrap gap-1">
            <ReadonlyStatusChip label="Component Template" tone="slate" />
            <ReadonlyStatusChip label="INACTIVE · READONLY · CANDIDATE" tone="cyan" />
          </div>
          <p className="mt-2 text-[11px] text-slate-300">
            <span data-testid={`product-system-component-first-truth-owner-${component.templateCode}`}>
              {truthOwnerLabel(dossierEntry?.expectedTruthOwner ?? "component_owned_truth")}
            </span>
            {dossierEntry ? (
              <>
                {" · "}
                <span data-testid={`product-system-component-first-dossier-role-${component.templateCode}`}>
                  dossier: {dossierEntry.expectedDossierRole}
                </span>
              </>
            ) : null}
            {productTruthPrefix ? (
              <>
                {" · "}
                <span
                  data-testid={`product-system-component-first-pt-prefix-${component.templateCode}`}
                  className="font-mono text-cyan-200/85"
                >
                  Product Truth prefix: {productTruthPrefix}
                </span>
              </>
            ) : null}
          </p>
          <p className="mt-1 text-[10px] text-slate-400">
            Live/fallback: {component.liveRowPresent ? "live inactive row" : "contract fallback row"} ·{" "}
            <span className="font-semibold text-amber-200/90">
              {blockerCount} blockers · {dependencySummary}
            </span>
          </p>
          <details className="mt-2 text-[10px] text-slate-400">
            <summary className="cursor-pointer font-semibold text-slate-300">Component details</summary>
            <div className="mt-1 space-y-1 text-slate-300">
              <p className="text-slate-500">{component.componentId}</p>
              {fieldGroups ? (
                <p data-testid={`product-system-component-first-field-groups-${component.templateCode}`}>
                  Field groups: {fieldGroups}
                </p>
              ) : null}
              {component.blockers.length > 0 ? (
                <p className="font-mono text-amber-200/80">Blockers: {component.blockers.join(", ")}</p>
              ) : null}
              {component.dependencies.length > 0 ? (
                <p className="font-mono text-slate-400">Dependencies: {component.dependencies.join(", ")}</p>
              ) : null}
            </div>
          </details>
        </div>
      </div>
      <ReadonlyCardFooter>
        <ReadonlyLinkButton
          label="View component settings"
          testId={`product-system-component-first-view-component-settings-${component.templateCode}`}
          onClick={onViewComponentSettings}
        />
        <ReadonlyLinkButton
          label="View dossier"
          testId={`product-system-component-first-view-dossier-${component.templateCode}`}
          onClick={onViewComponentDossier}
        />
      </ReadonlyCardFooter>
    </ReadonlyCardShell>
  );
}

function ComponentFirstCandidateSetCard({
  model,
  ownerSummary,
  onViewCandidate,
}: {
  model: ComponentFirstReadonlySetModel;
  ownerSummary: ReturnType<typeof buildComponentFirstOwnerSummary>;
  onViewCandidate: () => void;
}) {
  return (
    <ReadonlyCardShell
      testId="product-system-component-first-candidate-set-card"
      className="border-cyan-800/50 bg-cyan-950/10 hover:border-cyan-700/50"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex min-w-0 items-start gap-3">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-cyan-800/40 bg-cyan-950/30 text-cyan-300">
            <Layers className="h-5 w-5" />
          </div>
          <div className="min-w-0">
            <h3 className="text-[13px] font-bold text-cyan-100">Component-first Letters Candidate</h3>
            <p className="mt-0.5 font-mono text-[10px] text-cyan-200/85">
              {COMPONENT_FIRST_COMPOSER_TEMPLATE_CODE} · Template set 7/7
            </p>
            <ComponentFirstSemanticLabel />
            <div className="mt-2 flex flex-wrap gap-1 text-[9px] font-bold">
              <span className="rounded border border-cyan-700/40 bg-cyan-950/40 px-1.5 py-0.5 text-cyan-200">
                INACTIVE
              </span>
              <span className="rounded border border-cyan-700/40 bg-cyan-950/40 px-1.5 py-0.5 text-cyan-200">
                CANDIDATE
              </span>
              <span className="rounded border border-cyan-700/40 bg-cyan-950/40 px-1.5 py-0.5 text-cyan-200">
                READONLY
              </span>
              <span className="rounded border border-rose-700/40 bg-rose-900/20 px-1.5 py-0.5 text-rose-200">
                NOT OFFERABLE
              </span>
            </div>
            <div className="mt-2 space-y-0.5 text-[10px] text-slate-300">
              <p data-testid="product-system-component-first-completeness-count">
                Live rows: {model.foundRowCount}/{model.expectedRowCount}
              </p>
              <p>Work Intake: no</p>
              <p>Pricing / Quote / Order / Execution: no</p>
              <p>Owner GO required · Status: {ownerSummary.statusTitle}</p>
            </div>
          </div>
        </div>
        <ReadonlyLinkButton
          label="View candidate readonly"
          testId="product-system-component-first-view-candidate"
          onClick={onViewCandidate}
        />
      </div>
    </ReadonlyCardShell>
  );
}

function ComponentFirstOverviewPanel({
  model,
  ownerSummary,
  driftAssessment,
  onViewProductSettings,
  onViewProductDossier,
  onViewComponents,
}: {
  model: ComponentFirstReadonlySetModel;
  ownerSummary: ReturnType<typeof buildComponentFirstOwnerSummary>;
  driftAssessment: ReturnType<typeof assessComponentFirstContractDrift>;
  onViewProductSettings: () => void;
  onViewProductDossier: () => void;
  onViewComponents: () => void;
}) {
  const blocked = ownerSummary.statusLevel === "BLOCKED";

  return (
    <div data-testid="product-system-component-first-panel-overview" className="space-y-3">
      <ComponentFirstStatusStrip />

      {blocked ? (
        <p className="rounded border border-rose-700/40 bg-rose-900/20 px-3 py-2 text-[11px] font-bold text-rose-200">
          BLOCKED — review Guards / Audit before treating this set as safe readonly catalog truth.
        </p>
      ) : null}

      <ComponentFirstProductComposerCard
        model={model}
        variant="overview"
        onViewProductSettings={onViewProductSettings}
        onViewProductDossier={onViewProductDossier}
        onViewComponents={onViewComponents}
      />

      <article
        data-testid="product-system-component-first-owner-review"
        className="rounded-lg border border-slate-700/80 bg-slate-950/60 px-3 py-3"
      >
        <p className="text-[11px] font-bold uppercase tracking-wide text-slate-200">Owner review (compact)</p>
        <div className="mt-2 flex flex-wrap items-center gap-2">
          <span
            data-testid="product-system-component-first-owner-status-title"
            className={`rounded border px-2 py-0.5 text-[11px] font-bold ${componentFirstOwnerStatusTone(ownerSummary.statusLevel)}`}
          >
            Status: {ownerSummary.statusTitle}
          </span>
          <span
            data-testid="product-system-component-first-source-label"
            className={`rounded border px-2 py-0.5 text-[10px] font-bold ${componentFirstSourceTone(model.sourceMode)}`}
          >
            {componentFirstSourceLabel(model.sourceMode)}
          </span>
        </div>
        <p
          data-testid="product-system-component-first-owner-summary"
          className="mt-2 text-[11px] leading-relaxed text-slate-200"
        >
          {ownerSummary.oneSentenceSummary}
        </p>
        <ul
          data-testid="product-system-component-first-owner-checks"
          className="mt-2 space-y-1 text-[10px] text-slate-300"
        >
          {ownerSummary.ownerVisibleChecks.map((check) => (
            <li key={check.label}>
              <span className="text-slate-400">{check.label}:</span>{" "}
              <span className="font-semibold text-slate-100">{check.value}</span>
            </li>
          ))}
        </ul>
        <p className="mt-2 text-[10px] text-slate-400">
          Drift/completeness summary: live {model.foundRowCount}/{model.expectedRowCount} · contract check in Guards /
          Audit
        </p>
        <p
          data-testid="product-system-component-first-owner-next-step"
          className="mt-1 text-[10px] font-mono text-cyan-200/85"
        >
          Next owner decision: {ownerSummary.nextOwnerDecisionNeeded.replaceAll("_", " ").toLowerCase()}
        </p>
        <p
          data-testid="product-system-component-first-owner-guard"
          className="mt-1 text-[10px] font-mono text-slate-400"
        >
          Cannot use in Work Intake; cannot price; cannot create quote/order; cannot materialize tasks.
        </p>
      </article>

      <ComponentFirstForbiddenSummary compact />

      <p className="text-[10px] text-cyan-300/75">{componentFirstSourceDescription(model.sourceMode)}</p>
      {model.missingTemplateCodes.length > 0 ? (
        <p
          data-testid="product-system-component-first-missing-rows"
          className="text-[10px] font-mono text-orange-200/90"
        >
          Missing live rows: {model.missingTemplateCodes.join(", ")}
        </p>
      ) : null}
      {model.invalidActiveTemplateCodes.length > 0 ? (
        <p
          data-testid="product-system-component-first-invalid-active-rows"
          className="text-[10px] font-mono text-rose-200/90"
        >
          Invalid active rows: {model.invalidActiveTemplateCodes.join(", ")}
        </p>
      ) : null}
      {driftAssessment.metadataUnavailableWarnings.length > 0 ? (
        <p className="text-[10px] font-mono text-slate-400">
          Metadata warnings present — see Guards / Audit.
        </p>
      ) : null}
    </div>
  );
}

function ComponentFirstComponentsPanel({
  model,
  formReadiness,
  onViewProductSettings,
  onViewProductDossier,
  onViewComponentSettings,
  onViewComponentDossier,
  compactList = false,
}: {
  model: ComponentFirstReadonlySetModel;
  formReadiness: ReturnType<typeof assessComponentFirstFormSystemReadiness>;
  onViewProductSettings: () => void;
  onViewProductDossier: () => void;
  onViewComponentSettings: (templateCode: string) => void;
  onViewComponentDossier: (templateCode: string) => void;
  compactList?: boolean;
}) {
  return (
    <div data-testid="product-system-component-first-panel-components" className="space-y-3">
      <ComponentFirstProductComposerCard
        model={model}
        variant="compact"
        onViewProductSettings={onViewProductSettings}
        onViewProductDossier={onViewProductDossier}
        onViewComponents={() => undefined}
      />

      <section
        data-testid="product-system-component-first-components-list"
        className="rounded-lg border border-slate-800 bg-slate-950/40 p-3"
      >
        <div className="flex items-center justify-between gap-2">
          <h4 className="text-[11px] font-bold uppercase tracking-wide text-slate-100">Component templates</h4>
          <span className="rounded border border-slate-700 bg-slate-900 px-2 py-0.5 text-[11px] font-bold text-slate-300">
            {model.components.length} components
          </span>
        </div>
        <ComponentFirstSemanticLabel />
        {compactList ? (
          <div
            data-testid="product-system-component-first-components-table"
            className="mt-3 overflow-hidden rounded-lg border border-slate-800"
          >
            <div className="grid grid-cols-[minmax(0,0.8fr)_minmax(0,1.2fr)_auto] gap-2 border-b border-slate-800 bg-slate-950/40 px-2.5 py-1.5 text-[11px] font-bold uppercase text-slate-500">
              <span>Name</span>
              <span>Template code</span>
              <span>Blockers</span>
            </div>
            {model.components.map((component) => (
              <div
                key={component.templateCode}
                data-testid={`product-system-component-first-component-row-${component.templateCode}`}
                className="grid grid-cols-[minmax(0,0.8fr)_minmax(0,1.2fr)_auto] gap-2 border-b border-slate-800/60 px-2.5 py-2 text-[12px] text-slate-200 last:border-b-0"
              >
                <span className="font-bold">{componentFirstDisplayName(component.templateCode)}</span>
                <span className="font-mono text-[11px] text-slate-300">{component.templateCode}</span>
                <div className="flex flex-wrap items-center gap-1">
                  <span className="text-[11px] text-amber-200">{component.blockers.length} blockers</span>
                  <button
                    type="button"
                    data-testid={`product-system-component-first-view-component-settings-${component.templateCode}`}
                    onClick={() => onViewComponentSettings(component.templateCode)}
                    className="rounded border border-slate-700 bg-slate-900 px-1.5 py-0.5 text-[10px] font-bold text-cyan-200"
                  >
                    Settings
                  </button>
                  <button
                    type="button"
                    data-testid={`product-system-component-first-view-dossier-${component.templateCode}`}
                    onClick={() => onViewComponentDossier(component.templateCode)}
                    className="rounded border border-slate-700 bg-slate-900 px-1.5 py-0.5 text-[10px] font-bold text-cyan-200"
                  >
                    Dossier
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="mt-3 grid gap-3 xl:grid-cols-2">
            {model.components.map((component) => (
              <ComponentFirstComponentEntityCard
                key={component.templateCode}
                component={component}
                dossierEntry={dossierEntryForTemplate(component.templateCode)}
                formEntry={formEntryForComponent(component.templateCode, formReadiness.contractEntries)}
                productTruthPrefix={productTruthPrefixForTemplate(component.templateCode)}
                onViewComponentSettings={() => onViewComponentSettings(component.templateCode)}
                onViewComponentDossier={() => onViewComponentDossier(component.templateCode)}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function ComponentFirstDossierPanel({
  dossierAlignment,
  dossierFocus,
  onViewSettings,
  onFocusComponent,
}: {
  dossierAlignment: ReturnType<typeof assessComponentFirstDossierAlignment>;
  dossierFocus: string | null;
  onViewSettings: (templateCode: string) => void;
  onFocusComponent: (templateCode: string) => void;
}) {
  const composerEntry = dossierAlignment.contractEntries.find((entry) =>
    isComponentFirstComposer(entry.templateCode)
  );
  const componentEntries = dossierAlignment.contractEntries.filter(
    (entry) => !isComponentFirstComposer(entry.templateCode)
  );

  return (
    <section data-testid="product-system-component-first-panel-dossier" className="space-y-3">
      <div
        data-testid="product-system-component-first-dossier-workspace"
        className="rounded-lg border border-slate-700/80 bg-slate-950/60 px-3 py-3"
      >
        <h4 className="text-[11px] font-bold uppercase tracking-wide text-slate-200">Dossier workspace (readonly)</h4>
        <div
          data-testid="product-system-component-first-dossier-section"
          className="mt-2 space-y-2"
        >
          <div
            data-testid="product-system-component-first-dossier-alignment"
            className="flex flex-wrap items-center gap-2 text-[10px] font-bold"
          >
            <span
              data-testid="product-system-component-first-dossier-contract-count"
              className="rounded border border-slate-700 bg-slate-900 px-2 py-0.5 text-slate-300"
            >
              Dossier contract: {dossierAlignment.dossierContractCount}/{dossierAlignment.expectedCount}
            </span>
            <span
              data-testid="product-system-component-first-dossier-runtime-link"
              className="rounded border border-slate-700 bg-slate-900 px-2 py-0.5 text-slate-400"
            >
              {componentFirstDossierRuntimeLinkLabel(dossierAlignment.dossierRuntimeLinkState)}
            </span>
            <span
              data-testid="product-system-component-first-dossier-alignment-state"
              className={`rounded border px-2 py-0.5 ${componentFirstOverallAlignmentTone(dossierAlignment.overallAlignmentState)}`}
            >
              Alignment: {componentFirstOverallAlignmentLabel(dossierAlignment.overallAlignmentState)}
            </span>
          </div>
          <p
            data-testid="product-system-component-first-dossier-truth-ownership"
            className="text-[10px] text-slate-300"
          >
            Truth ownership: Composer = product orchestration only; Components = component-owned truth
          </p>
          <div
            data-testid="product-system-component-first-dossier-global-forbidden"
            className="rounded border border-rose-900/40 bg-rose-950/20 px-2 py-1.5 text-[10px] text-rose-200/90"
          >
            <span data-testid="product-system-component-first-dossier-guard">
              No task materialization · No ProductAggregate runtime · No TaskGraph / ExecutionPlan · No Pricing /
              Quote / Order / Execution · No Work Intake exposure
            </span>
          </div>
        </div>
      </div>

      {composerEntry ? (
        <article
          data-testid="product-system-component-first-dossier-composer-card"
          data-focused={dossierFocus === composerEntry.templateCode ? "true" : "false"}
          className={`rounded-lg border p-3 ${
            dossierFocus === composerEntry.templateCode
              ? "border-purple-500/60 bg-purple-950/30 ring-2 ring-purple-500/40 shadow-[0_0_0_1px_rgba(168,85,247,0.25)]"
              : "border-purple-800/50 bg-purple-950/10"
          }`}
        >
          {dossierFocus === composerEntry.templateCode ? (
            <p
              data-testid="product-system-component-first-dossier-focused-label"
              className="mb-2 inline-flex rounded border border-purple-500/50 bg-purple-900/40 px-2 py-0.5 text-[9px] font-bold uppercase tracking-wide text-purple-100"
            >
              Focused dossier
            </p>
          ) : null}
          <p className="text-[10px] font-bold uppercase tracking-wide text-purple-200">Product Composer Dossier</p>
          <p className="mt-1 font-mono text-[10px] font-bold text-cyan-200">{composerEntry.templateCode}</p>
          <div className="mt-2 space-y-1 text-[10px] text-slate-300">
            <p>Entity type: Product Composer</p>
            <p>Dossier role: {composerEntry.expectedDossierRole}</p>
            <p>Truth owner: {truthOwnerLabel(composerEntry.expectedTruthOwner)}</p>
            <p>Future metadata: {composerEntry.futureAllowedMetadata.join(", ")}</p>
          </div>
          <div className="mt-2 flex flex-wrap gap-1 text-[9px] font-bold">
            {composerEntry.forbiddenNow.map((item) => (
              <span
                key={item}
                className="rounded border border-rose-800/40 bg-rose-950/30 px-1.5 py-0.5 text-rose-200"
              >
                {DOSSIER_FORBIDDEN_LABELS[item]}
              </span>
            ))}
          </div>
          <div className="mt-2 flex flex-wrap gap-1.5">
            <ReadonlyLinkButton
              label="View settings"
              testId="product-system-component-first-dossier-view-settings-composer"
              onClick={() => onViewSettings(composerEntry.templateCode)}
            />
          </div>
        </article>
      ) : null}

      <div data-testid="product-system-component-first-dossier-cards" className="grid gap-3 xl:grid-cols-2">
        {componentEntries.map((entry) => {
          const isFocused = dossierFocus === entry.templateCode;
          return (
          <article
            key={entry.templateCode}
            data-testid={`product-system-component-first-dossier-card-${entry.templateCode}`}
            data-focused={isFocused ? "true" : "false"}
            className={`rounded-lg border bg-[#0D1321]/90 p-3 ${
              isFocused
                ? "border-cyan-500/60 ring-2 ring-cyan-500/40 shadow-[0_0_0_1px_rgba(34,211,238,0.25)]"
                : "border-slate-800/90"
            }`}
          >
            {isFocused ? (
              <p
                data-testid={`product-system-component-first-dossier-focused-label-${entry.templateCode}`}
                className="mb-2 inline-flex rounded border border-cyan-500/50 bg-cyan-950/50 px-2 py-0.5 text-[9px] font-bold uppercase tracking-wide text-cyan-100"
              >
                Focused dossier
              </p>
            ) : null}
            <p className="font-mono text-[10px] font-bold text-cyan-200">{entry.templateCode}</p>
            <p className="text-[10px] text-slate-400">
              {componentFirstDisplayName(entry.templateCode)} · Component Template
            </p>
            <div className="mt-2 space-y-1 text-[10px] text-slate-300">
              <p>
                <span className="text-slate-500">Dossier role:</span> {entry.expectedDossierRole}
              </p>
              <p>
                <span className="text-slate-500">Truth owner:</span> {truthOwnerLabel(entry.expectedTruthOwner)}
              </p>
              <p>
                <span className="text-slate-500">Future metadata:</span> {entry.futureAllowedMetadata.join(", ")}
              </p>
            </div>
            <div className="mt-2 flex flex-wrap gap-1 text-[9px] font-bold">
              {entry.forbiddenNow.map((item) => (
                <span
                  key={item}
                  className="rounded border border-rose-800/40 bg-rose-950/30 px-1.5 py-0.5 text-rose-200"
                >
                  {DOSSIER_FORBIDDEN_LABELS[item]}
                </span>
              ))}
            </div>
            <div className="mt-2 flex flex-wrap gap-1.5">
              <ReadonlyLinkButton
                label="View settings"
                testId={`product-system-component-first-dossier-view-settings-${entry.templateCode}`}
                onClick={() => onViewSettings(entry.templateCode)}
              />
              <ReadonlyLinkButton
                label="Focus component"
                testId={`product-system-component-first-dossier-focus-${entry.templateCode}`}
                onClick={() => onFocusComponent(entry.templateCode)}
              />
            </div>
          </article>
          );
        })}
      </div>
    </section>
  );
}

function ComponentFirstFormSystemPanel({
  formReadiness,
}: {
  formReadiness: ReturnType<typeof assessComponentFirstFormSystemReadiness>;
}) {
  return (
    <article
      data-testid="product-system-component-first-panel-form-system"
      className="rounded-lg border border-slate-700/80 bg-slate-950/60 px-3 py-3"
    >
      <div data-testid="product-system-component-first-form-system-readiness">
        <p className="text-[11px] font-bold uppercase tracking-wide text-slate-200">Form System readiness</p>
        <div className="mt-2 flex flex-wrap items-center gap-2 text-[10px] font-bold">
          <span
            data-testid="product-system-component-first-form-readiness-contract-count"
            className="rounded border border-slate-700 bg-slate-900 px-2 py-0.5 text-slate-300"
          >
            Readiness contract: {formReadiness.readinessContractEntries}/{formReadiness.expectedComponents}
          </span>
          <span
            data-testid="product-system-component-first-form-runtime-link"
            className="rounded border border-slate-700 bg-slate-900 px-2 py-0.5 text-slate-400"
          >
            {componentFirstFormRuntimeLinkLabel(formReadiness.runtimeFormSystemLinkState)}
          </span>
          <span
            data-testid="product-system-component-first-form-readiness-state"
            className={`rounded border px-2 py-0.5 ${componentFirstFormReadinessTone(formReadiness.overallFormReadinessState)}`}
          >
            State: {componentFirstFormReadinessLabel(formReadiness.overallFormReadinessState)}
          </span>
        </div>
        <p
          data-testid="product-system-component-first-form-field-ownership"
          className="mt-2 text-[10px] text-slate-300"
        >
          Field ownership: Composer = coordinates sections only; Components = own future fields
        </p>
        <ul
          data-testid="product-system-component-first-form-compact-fields"
          className="mt-3 space-y-2 text-[10px] text-slate-400"
        >
          {formReadiness.contractEntries.map((entry) => (
            <li key={entry.templateCode} className="rounded border border-slate-800/80 bg-[#0D1321]/60 px-2 py-1.5">
              <span className="font-mono font-bold text-slate-200">{entry.templateCode}</span>
              {entry.role === "component_template" ? (
                <span className="ml-2 text-slate-300">— {entry.fieldGroups.join(", ")}</span>
              ) : (
                <span className="ml-2 text-slate-300">— coordinates: {entry.coordinates.join(", ")}</span>
              )}
            </li>
          ))}
        </ul>
        <p
          data-testid="product-system-component-first-form-guard"
          className="mt-2 text-[10px] font-mono text-cyan-200/80"
        >
          Guard: no runtime form activation; no Work Intake exposure; no Product Truth write; no Pricing / Quote /
          Order / Execution
        </p>
        {formReadiness.unsafeSignals.length > 0 ? (
          <p
            data-testid="product-system-component-first-form-unsafe-signals"
            className="mt-1 text-[10px] font-mono text-rose-200/90"
          >
            Unsafe signals: {formReadiness.unsafeSignals.join(", ")}
          </p>
        ) : null}
      </div>
    </article>
  );
}

function ComponentFirstProductTruthPanel({
  productTruthMapping,
}: {
  productTruthMapping: ReturnType<typeof assessComponentFirstProductTruthMapping>;
}) {
  const grouped = useMemo(
    () => groupProductTruthByTemplate(productTruthMapping.contractEntries),
    [productTruthMapping.contractEntries]
  );

  return (
    <article
      data-testid="product-system-component-first-panel-product-truth"
      className="rounded-lg border border-slate-700/80 bg-slate-950/60 px-3 py-3"
    >
      <div data-testid="product-system-component-first-product-truth-mapping">
        <p className="text-[11px] font-bold uppercase tracking-wide text-slate-200">Product Truth mapping</p>
        <div className="mt-2 flex flex-wrap items-center gap-2 text-[10px] font-bold">
          <span
            data-testid="product-system-component-first-product-truth-mapping-count"
            className="rounded border border-slate-700 bg-slate-900 px-2 py-0.5 text-slate-300"
          >
            Mapping contract: {productTruthMapping.mappingContractEntriesCount}/
            {productTruthMapping.expectedMappingEntriesCount}
          </span>
          <span
            data-testid="product-system-component-first-product-truth-runtime-link"
            className="rounded border border-slate-700 bg-slate-900 px-2 py-0.5 text-slate-400"
          >
            {componentFirstProductTruthRuntimeLinkLabel(productTruthMapping.runtimeProductTruthLinkState)}
          </span>
          <span
            data-testid="product-system-component-first-product-truth-mapping-state"
            className={`rounded border px-2 py-0.5 ${componentFirstProductTruthMappingTone(productTruthMapping.overallMappingState)}`}
          >
            State: {componentFirstProductTruthMappingLabel(productTruthMapping.overallMappingState)}
          </span>
        </div>
        <p
          data-testid="product-system-component-first-product-truth-write-policy"
          className="mt-2 text-[10px] text-slate-300"
        >
          Write policy: no Product Truth write
        </p>
        <p
          data-testid="product-system-component-first-product-truth-state-policy"
          className="mt-1 text-[10px] font-mono text-slate-400"
        >
          State policy: suggested != confirmed; fallback/hydrated/manual draft != confirmed; operator confirmation
          required later; no confirmed values created
        </p>
        <ul
          data-testid="product-system-component-first-product-truth-compact-paths"
          className="mt-3 space-y-2 text-[10px] text-slate-400"
        >
          {[...grouped.entries()].map(([templateCode, entries]) => (
            <li key={templateCode} className="rounded border border-slate-800/80 bg-[#0D1321]/60 px-2 py-1.5">
              <p className="font-mono font-bold text-slate-200">{templateCode}</p>
              <ul className="mt-1 space-y-0.5 font-mono text-cyan-200/80">
                {entries.map((entry) => (
                  <li key={entry.fieldGroup}>
                    {entry.fieldGroup} → {entry.futureProductTruthPath}
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ul>
        <p
          data-testid="product-system-component-first-product-truth-guard"
          className="mt-2 text-[10px] font-mono text-cyan-200/80"
        >
          Guard: readonly mapping only; no confirmed Product Truth values created; no Intake V6 write path
        </p>
        {productTruthMapping.writeEnabledEntries.length > 0 ? (
          <p
            data-testid="product-system-component-first-product-truth-write-leak"
            className="mt-1 text-[10px] font-mono text-rose-200/90"
          >
            Write leak entries: {productTruthMapping.writeEnabledEntries.join(", ")}
          </p>
        ) : null}
      </div>
    </article>
  );
}

function ComponentFirstGuardsAuditPanel({
  model,
  driftAssessment,
  dossierAlignment,
  productDefinitionReadiness,
  formReadiness,
  productTruthMapping,
  includeReadinessSections = false,
}: {
  model: ComponentFirstReadonlySetModel;
  driftAssessment: ReturnType<typeof assessComponentFirstContractDrift>;
  dossierAlignment: ReturnType<typeof assessComponentFirstDossierAlignment>;
  productDefinitionReadiness: ReturnType<typeof assessComponentFirstProductDefinitionReadiness>;
  formReadiness?: ReturnType<typeof assessComponentFirstFormSystemReadiness>;
  productTruthMapping?: ReturnType<typeof assessComponentFirstProductTruthMapping>;
  includeReadinessSections?: boolean;
}) {
  return (
    <div data-testid="product-system-component-first-panel-guards-audit" className="space-y-3">
      <div
        data-testid="product-system-component-first-drift-guard"
        className="rounded-lg border border-slate-800/90 bg-[#0D1321]/90 px-3 py-2"
      >
        <p className="text-[10px] font-bold uppercase tracking-wide text-slate-300">Completeness & drift</p>
        <div className="mt-1 flex flex-wrap items-center gap-2 text-[10px] font-bold">
          <span
            data-testid="product-system-component-first-contract-check"
            className={`rounded border px-2 py-0.5 ${componentFirstContractCheckTone(driftAssessment.contractCheckStatus)}`}
          >
            {componentFirstContractCheckLabel(driftAssessment.contractCheckStatus)}
          </span>
          <span className="rounded border border-slate-700 bg-slate-900 px-2 py-0.5 text-slate-300">
            expected rows: {driftAssessment.completeness.expectedRowCount}
          </span>
          <span className="rounded border border-slate-700 bg-slate-900 px-2 py-0.5 text-slate-300">
            live rows: {driftAssessment.completeness.foundRowCount}/{driftAssessment.completeness.expectedRowCount}
          </span>
          <span className="rounded border border-slate-700 bg-slate-900 px-2 py-0.5 text-slate-300">
            drift: {componentFirstDriftLabel(driftAssessment.driftState)}
          </span>
        </div>
        {driftAssessment.liveRowDriftIssues.length > 0 ? (
          <p
            data-testid="product-system-component-first-drift-warnings"
            className="mt-1 text-[10px] font-mono text-amber-200/90"
          >
            Drift warnings: {driftAssessment.liveRowDriftIssues.join(", ")}
          </p>
        ) : null}
        {driftAssessment.liveExtraFamilyRows.length > 0 ? (
          <p className="mt-1 text-[10px] font-mono text-amber-200/90">
            Extra family rows: {driftAssessment.liveExtraFamilyRows.join(", ")}
          </p>
        ) : null}
        {driftAssessment.fallbackContractIssues.length > 0 ? (
          <p className="mt-1 text-[10px] font-mono text-rose-200/90">
            Fallback contract issues: {driftAssessment.fallbackContractIssues.join(", ")}
          </p>
        ) : null}
        {driftAssessment.metadataUnavailableWarnings.length > 0 ? (
          <p
            data-testid="product-system-component-first-metadata-warnings"
            className="mt-1 text-[10px] font-mono text-slate-400"
          >
            Metadata unavailable: {driftAssessment.metadataUnavailableWarnings.join(", ")}
          </p>
        ) : null}
      </div>

      <article
        data-testid="product-system-component-first-product-definition-readiness"
        className="rounded-lg border border-slate-700/80 bg-slate-950/60 px-3 py-3"
      >
        <p className="text-[11px] font-bold uppercase tracking-wide text-slate-200">ProductDefinition readiness</p>
        <div className="mt-2 flex flex-wrap items-center gap-2 text-[10px] font-bold">
          <span
            data-testid="product-system-component-first-product-definition-paths-count"
            className="rounded border border-slate-700 bg-slate-900 px-2 py-0.5 text-slate-300"
          >
            Consumption contract: {productDefinitionReadiness.mappedPathsCount}/
            {productDefinitionReadiness.requiredPathsCount} paths
          </span>
          <span
            data-testid="product-system-component-first-product-definition-runtime-link"
            className="rounded border border-slate-700 bg-slate-900 px-2 py-0.5 text-slate-400"
          >
            {componentFirstProductDefinitionRuntimeLinkLabel(
              productDefinitionReadiness.runtimeProductDefinitionLinkState
            )}
          </span>
          <span
            data-testid="product-system-component-first-product-definition-readiness-state"
            className={`rounded border px-2 py-0.5 ${componentFirstProductDefinitionReadinessTone(productDefinitionReadiness.overallProductDefinitionReadinessState)}`}
          >
            State:{" "}
            {componentFirstProductDefinitionReadinessLabel(
              productDefinitionReadiness.overallProductDefinitionReadinessState
            )}
          </span>
        </div>
        <p
          data-testid="product-system-component-first-product-definition-missing-behavior"
          className="mt-2 text-[10px] text-slate-300"
        >
          Missing truth behavior: report missing truth; do not invent; do not price; do not create aggregate/tasks
        </p>
        <p
          data-testid="product-system-component-first-product-definition-state-policy"
          className="mt-1 text-[10px] font-mono text-slate-400"
        >
          State policy: suggested/fallback/hydrated/manual draft are not ProductDefinition truth; confirmed truth
          required later
        </p>
        <ul
          data-testid="product-system-component-first-product-definition-compact-paths"
          className="mt-2 space-y-0.5 text-[10px] text-slate-400"
        >
          {productDefinitionReadiness.compactPathSummaries.map((summary) => (
            <li key={summary.label}>
              <span className="font-semibold text-slate-300">{summary.label} required paths:</span> {summary.paths}
            </li>
          ))}
        </ul>
        <p
          data-testid="product-system-component-first-product-definition-guard"
          className="mt-2 text-[10px] font-mono text-cyan-200/80"
        >
          Guard: no invent; no price; no quote/order; no ProductAggregate; no TaskGraph/ExecutionPlan; no task
          materialization
        </p>
      </article>

      <details className="rounded-lg border border-violet-800/40 bg-violet-950/10 p-3">
        <summary className="cursor-pointer text-[11px] font-bold uppercase tracking-wide text-violet-100">
          Dependency graph (audit detail)
        </summary>
        <section data-testid="product-system-component-first-dependency-graph" className="mt-2">
          <div className="grid gap-1 text-[10px] text-violet-200/85">
            {model.dependencyGraph.map((edge) => (
              <p key={`${edge.from}-${edge.to}`} className="font-mono">
                {edge.from} -&gt; {edge.to}
              </p>
            ))}
          </div>
        </section>
      </details>

      <div className="grid gap-2 md:grid-cols-3 text-[10px] text-slate-200">
        <div className="rounded-lg border border-slate-800/90 bg-[#0D1321]/90 px-3 py-2">
          Inert flags: WI={String(model.noWorkIntakeExposure)} Pricing={String(model.noPricingActivation)} PD=
          {String(model.noProductDefinitionActivation)}
        </div>
        <div className="rounded-lg border border-slate-800/90 bg-[#0D1321]/90 px-3 py-2">
          Runtime wiring: PA={String(model.noProductAggregateRuntimeWiring)} ops={String(model.noExecutableOperations)}
        </div>
        <div className="rounded-lg border border-slate-800/90 bg-[#0D1321]/90 px-3 py-2">
          BOM={String(model.noExecutableBom)} · catalog status={model.composerCatalogStatus}
        </div>
      </div>

      {dossierAlignment.runtimeActivationLeakIssues.length > 0 ? (
        <p className="text-[10px] font-mono text-rose-200/90">
          Dossier activation leaks: {dossierAlignment.runtimeActivationLeakIssues.join(", ")}
        </p>
      ) : null}

      {includeReadinessSections && formReadiness ? (
        <div data-testid="product-system-component-first-guards-form-system-section" className="space-y-3">
          <ComponentFirstFormSystemPanel formReadiness={formReadiness} />
        </div>
      ) : null}

      {includeReadinessSections && productTruthMapping ? (
        <div data-testid="product-system-component-first-guards-product-truth-section" className="space-y-3">
          <ComponentFirstProductTruthPanel productTruthMapping={productTruthMapping} />
        </div>
      ) : null}
    </div>
  );
}

export function ComponentFirstReadonlyCandidatePanel({
  templates,
  availabilityItems,
  selectedTemplateCode,
  variant = "catalog",
  detailSection = "overview",
  onDetailSectionChange,
}: {
  templates: ProductTemplateEntity[];
  availabilityItems: ProductTemplateAvailabilityItem[];
  selectedTemplateCode: string;
  variant?: "catalog" | "inline" | "detail-panel";
  detailSection?: ComponentFirstDetailPanelSection;
  onDetailSectionChange?: (section: ComponentFirstDetailPanelSection) => void;
}) {
  const isDetailPanel = variant === "detail-panel";
  const [detailOpen, setDetailOpen] = useState(variant === "inline");
  const [internalTab, setInternalTab] = useState<ComponentFirstCandidateTab>("overview");
  const [settingsTarget, setSettingsTarget] = useState<ComponentFirstSettingsTarget | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [dossierFocus, setDossierFocus] = useState<string | null>(null);

  const activeTab: ComponentFirstCandidateTab | ComponentFirstDetailPanelSection = isDetailPanel
    ? detailSection
    : internalTab;

  const setActiveTab = (tab: ComponentFirstCandidateTab | ComponentFirstDetailPanelSection) => {
    if (isDetailPanel) {
      onDetailSectionChange?.(tab as ComponentFirstDetailPanelSection);
      return;
    }
    setInternalTab(tab as ComponentFirstCandidateTab);
  };

  const model = buildComponentFirstReadonlySetModel(templates, availabilityItems, selectedTemplateCode);
  const driftAssessment = assessComponentFirstContractDrift(templates);
  const dossierAlignment = assessComponentFirstDossierAlignment(templates, { drift: driftAssessment });
  const ownerSummary = buildComponentFirstOwnerSummary(
    driftAssessment.completeness,
    driftAssessment,
    dossierAlignment
  );
  const formReadiness = assessComponentFirstFormSystemReadiness(
    driftAssessment.completeness,
    dossierAlignment,
    ownerSummary,
    { drift: driftAssessment, liveTemplates: templates }
  );
  const productTruthMapping = assessComponentFirstProductTruthMapping(formReadiness, ownerSummary);
  const productDefinitionReadiness = assessComponentFirstProductDefinitionReadiness(
    productTruthMapping,
    formReadiness,
    ownerSummary,
    { liveTemplates: templates }
  );

  const openSettings = (target: ComponentFirstSettingsTarget) => {
    setSettingsTarget(target);
    setSettingsOpen(true);
  };

  const openProductSettings = () => openSettings({ kind: "product" });
  const openComponentSettings = (templateCode: string) => openSettings({ kind: "component", templateCode });

  const openProductDossier = () => {
    setActiveTab("dossier");
    setDossierFocus(COMPONENT_FIRST_COMPOSER_TEMPLATE_CODE);
  };

  const openComponentDossier = (templateCode: string) => {
    setActiveTab("dossier");
    setDossierFocus(templateCode);
  };

  const openComponentsTab = () => setActiveTab("components");

  if (!model) {
    return null;
  }

  if (variant === "catalog" && !detailOpen) {
    return (
      <ComponentFirstCandidateSetCard
        model={model}
        ownerSummary={ownerSummary}
        onViewCandidate={() => setDetailOpen(true)}
      />
    );
  }

  const sectionTabs = isDetailPanel ? DETAIL_PANEL_TABS : CANDIDATE_TABS;

  return (
    <>
      <section
        data-testid="product-system-component-first-letters-set"
        className={isDetailPanel ? "space-y-3" : "rounded-xl border border-cyan-800/40 bg-cyan-950/10 p-3"}
      >
        {!isDetailPanel ? (
          <div className="flex flex-wrap items-start justify-between gap-3 border-b border-cyan-900/40 pb-3">
            <div>
              <h3 className="text-[13px] font-bold text-cyan-100">Component-first Letters Candidate</h3>
              <p className="mt-0.5 text-[11px] text-cyan-200/75">
                Parallel readonly candidate set — does not replace TPL-VOLUMETRIC-LETTERS_v2 and does not activate anything.
              </p>
              <ComponentFirstSemanticLabel />
            </div>
            <div className="flex flex-wrap gap-1.5 text-[10px] font-bold">
              <span className="rounded border border-slate-700 bg-slate-900 px-2 py-0.5 text-slate-300">
                active = {String(model.composerActive)}
              </span>
              <span className="rounded border border-slate-700 bg-slate-900 px-2 py-0.5 text-slate-300">
                catalog status = {model.composerCatalogStatus}
              </span>
            </div>
          </div>
        ) : (
          <div>
            <h3 className="text-[15px] font-bold text-cyan-100">Component-first Letters Candidate</h3>
            <p className="mt-0.5 text-[12px] text-cyan-200/75">
              Candidate readonly · NOT OFFERABLE · 1 Product Composer + 6 Component Templates
            </p>
            <p
              data-testid="product-system-component-first-detail-meta"
              className="mt-1 text-[11px] font-mono text-slate-400"
            >
              active = {String(model.composerActive)} · catalog status = {model.composerCatalogStatus}
            </p>
            <ComponentFirstSemanticLabel />
          </div>
        )}

        <div
          className={`${isDetailPanel ? "" : "mt-3 "}flex flex-wrap gap-1.5`}
          role="tablist"
          aria-label="Component-first candidate sections"
        >
          {sectionTabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={activeTab === tab.id}
              data-testid={tab.testId}
              onClick={() => setActiveTab(tab.id)}
              className={`rounded-md border px-2.5 py-1 text-[11px] font-bold transition-colors ${
                activeTab === tab.id
                  ? "border-cyan-500/50 bg-cyan-500/10 text-cyan-100"
                  : "border-slate-700 bg-slate-900 text-slate-400 hover:text-slate-200"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className={isDetailPanel ? "mt-2" : "mt-3"}>
          {activeTab === "overview" ? (
            <ComponentFirstOverviewPanel
              model={model}
              ownerSummary={ownerSummary}
              driftAssessment={driftAssessment}
              onViewProductSettings={openProductSettings}
              onViewProductDossier={openProductDossier}
              onViewComponents={openComponentsTab}
            />
          ) : null}
          {activeTab === "components" ? (
            <ComponentFirstComponentsPanel
              model={model}
              formReadiness={formReadiness}
              onViewProductSettings={openProductSettings}
              onViewProductDossier={openProductDossier}
              onViewComponentSettings={openComponentSettings}
              onViewComponentDossier={openComponentDossier}
              compactList={isDetailPanel}
            />
          ) : null}
          {activeTab === "dossier" ? (
            <ComponentFirstDossierPanel
              dossierAlignment={dossierAlignment}
              dossierFocus={dossierFocus}
              onViewSettings={(templateCode) =>
                isComponentFirstComposer(templateCode)
                  ? openProductSettings()
                  : openComponentSettings(templateCode)
              }
              onFocusComponent={(templateCode) => {
                setDossierFocus(templateCode);
              }}
            />
          ) : null}
          {!isDetailPanel && activeTab === "form-system" ? (
            <ComponentFirstFormSystemPanel formReadiness={formReadiness} />
          ) : null}
          {!isDetailPanel && activeTab === "product-truth" ? (
            <ComponentFirstProductTruthPanel productTruthMapping={productTruthMapping} />
          ) : null}
          {activeTab === "guards-audit" ? (
            <ComponentFirstGuardsAuditPanel
              model={model}
              driftAssessment={driftAssessment}
              dossierAlignment={dossierAlignment}
              productDefinitionReadiness={productDefinitionReadiness}
              formReadiness={formReadiness}
              productTruthMapping={productTruthMapping}
              includeReadinessSections={isDetailPanel}
            />
          ) : null}
        </div>
      </section>

      <ComponentFirstReadonlySettingsSheet
        open={settingsOpen}
        onOpenChange={setSettingsOpen}
        target={settingsTarget}
        model={model}
        formEntries={formReadiness.contractEntries}
        truthEntries={productTruthMapping.contractEntries}
        dossierRuntimeLinkState={componentFirstDossierRuntimeLinkLabel(dossierAlignment.dossierRuntimeLinkState)}
      />
    </>
  );
}

/** @deprecated Use ComponentFirstReadonlyCandidatePanel — kept for editor imports */
export const ComponentFirstReadonlyStatusPanel = ComponentFirstReadonlyCandidatePanel;

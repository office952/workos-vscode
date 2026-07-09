import { useMemo, useState } from "react";
import type { ProductTemplateAvailabilityItem, ProductTemplateEntity } from "@/lib/api";
import {
  assessComponentFirstContractDrift,
  componentFirstContractCheckLabel,
  componentFirstContractCheckTone,
  componentFirstDriftLabel,
  componentFirstSourceDescription,
  componentFirstSourceLabel,
  componentFirstSourceTone,
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
  getComponentFirstFormReadinessEntry,
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

const DOSSIER_FORBIDDEN_LABELS: Record<ComponentFirstDossierForbiddenNow, string> = {
  task_materialization: "No task materialization",
  execution_plan: "No ExecutionPlan",
  product_aggregate_runtime: "No ProductAggregate",
  pricing: "No Pricing",
  quote_order: "No Quote / Order",
  work_intake_exposure: "No Work Intake exposure",
};

const COMPONENT_DISPLAY_LABEL: Partial<Record<ComponentFirstTemplateCode, string>> = {
  "TPL-COMP-LETTER-FACE_v1": "Face",
  "TPL-COMP-LETTER-BACK_v1": "Back",
  "TPL-COMP-LETTER-RETURN-CANT_v1": "Return/Cant",
  "TPL-COMP-LETTER-LED_v1": "LED",
  "TPL-COMP-LETTER-FINISH_v1": "Finish",
  "TPL-COMP-LETTER-MOUNTING_v1": "Mounting",
};

function truthOwnerLabel(owner: "product_composer" | "component_owned_truth"): string {
  return owner === "product_composer" ? "Product composer orchestration" : "Component-owned truth";
}

function productTruthPrefixForTemplate(templateCode: string): string | null {
  const label = COMPONENT_DISPLAY_LABEL[templateCode as ComponentFirstTemplateCode];
  if (!label) return null;
  const summary = COMPONENT_FIRST_PRODUCT_TRUTH_COMPACT_PATH_SUMMARIES.find(
    (entry) => entry.label === label.toUpperCase() || entry.label === label
  );
  return summary?.pathPrefix ?? null;
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

function dossierEntryForTemplate(
  templateCode: string,
  contract: readonly ComponentFirstDossierContractEntry[] = COMPONENT_FIRST_DOSSIER_CONTRACT_FIXTURE
): ComponentFirstDossierContractEntry | undefined {
  return contract.find(
    (entry) => normalizeComponentFirstTemplateCode(entry.templateCode) === normalizeComponentFirstTemplateCode(templateCode)
  );
}

function formEntryForComponent(
  templateCode: string,
  entries: ComponentFirstFormReadinessEntry[]
): ComponentFirstFormReadinessEntry | undefined {
  return entries.find(
    (entry) => normalizeComponentFirstTemplateCode(entry.templateCode) === normalizeComponentFirstTemplateCode(templateCode)
  );
}

function ComponentFirstForbiddenSummary() {
  return (
    <div
      data-testid="product-system-component-first-forbidden-summary"
      className="rounded-lg border border-slate-800/90 bg-[#0D1321]/90 px-3 py-2 text-[10px] text-slate-300"
    >
      <p className="font-bold uppercase tracking-wide text-slate-400">Forbidden capabilities (candidate set)</p>
      <ul className="mt-1.5 space-y-0.5">
        <li>Not exposed in Work Intake</li>
        <li>No Pricing / Quote / Order / Execution</li>
        <li>No ProductDefinition runtime / ProductAggregate / TaskGraph / ExecutionPlan</li>
        <li>No task materialization · No Product Truth write · Activation requires owner GO</li>
      </ul>
    </div>
  );
}

function ComponentFirstOverviewPanel({
  model,
  ownerSummary,
  driftAssessment,
}: {
  model: ComponentFirstReadonlySetModel;
  ownerSummary: ReturnType<typeof buildComponentFirstOwnerSummary>;
  driftAssessment: ReturnType<typeof assessComponentFirstContractDrift>;
}) {
  const blocked = ownerSummary.statusLevel === "BLOCKED";

  return (
    <div data-testid="product-system-component-first-panel-overview" className="space-y-3">
      <div className="flex flex-wrap gap-1.5 text-[10px] font-bold">
        <span className="rounded border border-cyan-700/40 bg-cyan-950/40 px-2 py-0.5 text-cyan-200">INACTIVE</span>
        <span className="rounded border border-cyan-700/40 bg-cyan-950/40 px-2 py-0.5 text-cyan-200">CANDIDATE</span>
        <span className="rounded border border-cyan-700/40 bg-cyan-950/40 px-2 py-0.5 text-cyan-200">READONLY</span>
        <span
          data-testid="product-system-component-first-not-offerable"
          className="rounded border border-rose-700/40 bg-rose-900/20 px-2 py-0.5 text-rose-200"
        >
          NOT OFFERABLE
        </span>
        <span className="rounded border border-slate-700 bg-slate-900 px-2 py-0.5 text-slate-300">
          Not exposed in Work Intake
        </span>
      </div>

      {blocked ? (
        <p className="rounded border border-rose-700/40 bg-rose-900/20 px-3 py-2 text-[11px] font-bold text-rose-200">
          BLOCKED — review Guards / Audit before treating this set as safe readonly catalog truth.
        </p>
      ) : null}

      <article
        data-testid="product-system-component-first-owner-review"
        className="rounded-lg border border-slate-700/80 bg-slate-950/60 px-3 py-3"
      >
        <p className="text-[11px] font-bold uppercase tracking-wide text-slate-200">Owner review</p>
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
          <span
            data-testid="product-system-component-first-completeness-count"
            className="rounded border border-slate-700 bg-slate-900 px-2 py-0.5 text-[10px] font-bold text-slate-300"
          >
            Live rows: {model.foundRowCount}/{model.expectedRowCount}
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
        <p
          data-testid="product-system-component-first-owner-next-step"
          className="mt-2 text-[10px] font-mono text-cyan-200/85"
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

      <ComponentFirstForbiddenSummary />

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

function ComponentFirstComponentEntityCard({
  component,
  dossierEntry,
  formEntry,
  productTruthPrefix,
}: {
  component: ComponentFirstReadonlyComponent;
  dossierEntry?: ComponentFirstDossierContractEntry;
  formEntry?: ComponentFirstFormReadinessEntry;
  productTruthPrefix: string | null;
}) {
  const fieldGroups =
    formEntry && formEntry.role === "component_template" ? formEntry.fieldGroups.join(", ") : null;

  return (
    <article
      data-testid={`product-system-component-first-component-${component.templateCode}`}
      className="rounded-lg border border-slate-800/90 bg-[#0D1321]/90 p-3"
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="font-mono text-[10px] font-bold text-cyan-200">{component.templateCode}</p>
          <p className="mt-0.5 text-[11px] font-bold text-slate-100">{component.componentId}</p>
        </div>
        <div className="flex flex-wrap gap-1.5 text-[9px] font-bold">
          <span className="rounded border border-slate-700 bg-slate-900 px-1.5 py-0.5 text-slate-300">
            {component.componentKind}
          </span>
          <span className="rounded border border-slate-700 bg-slate-900 px-1.5 py-0.5 text-slate-300">
            active = {String(component.active)}
          </span>
          <span className="rounded border border-amber-700/40 bg-amber-900/20 px-1.5 py-0.5 text-amber-300">
            {component.readinessState}
          </span>
          {!component.liveRowPresent ? (
            <span className="rounded border border-orange-700/40 bg-orange-900/20 px-1.5 py-0.5 text-orange-300">
              contract fallback row
            </span>
          ) : (
            <span className="rounded border border-emerald-700/40 bg-emerald-900/20 px-1.5 py-0.5 text-emerald-300">
              live inactive row
            </span>
          )}
        </div>
      </div>

      <div className="mt-2 grid gap-1.5 text-[10px] text-slate-300">
        <p>
          <span className="text-slate-500">Role:</span> {component.roleLabel}
        </p>
        {dossierEntry ? (
          <p data-testid={`product-system-component-first-dossier-role-${component.templateCode}`}>
            <span className="text-slate-500">Dossier role:</span> {dossierEntry.expectedDossierRole}
          </p>
        ) : null}
        <p data-testid={`product-system-component-first-truth-owner-${component.templateCode}`}>
          <span className="text-slate-500">Truth ownership:</span>{" "}
          {truthOwnerLabel(dossierEntry?.expectedTruthOwner ?? "component_owned_truth")}
        </p>
        {fieldGroups ? (
          <p data-testid={`product-system-component-first-field-groups-${component.templateCode}`}>
            <span className="text-slate-500">Future field groups:</span> {fieldGroups}
          </p>
        ) : null}
        {productTruthPrefix ? (
          <p
            data-testid={`product-system-component-first-pt-prefix-${component.templateCode}`}
            className="font-mono text-cyan-200/85"
          >
            Product Truth prefix: {productTruthPrefix}
          </p>
        ) : null}
        <p className="font-mono text-cyan-200/85">{component.targetProductTruthPath}</p>
      </div>

      <details className="mt-2 text-[10px] text-slate-400">
        <summary className="cursor-pointer font-semibold text-slate-300">Blockers & guards</summary>
        <p className="mt-1">Dependencies: {component.dependencies.join(", ") || "none"}</p>
        <p className="mt-1 font-mono text-amber-200/85">Blockers: {component.blockers.join(", ") || "none"}</p>
        <p className="mt-1">Activation guard: {component.activationGuard}</p>
      </details>
    </article>
  );
}

function ComponentFirstComponentsPanel({
  model,
  formReadiness,
}: {
  model: ComponentFirstReadonlySetModel;
  formReadiness: ReturnType<typeof assessComponentFirstFormSystemReadiness>;
}) {
  return (
    <div data-testid="product-system-component-first-panel-components" className="space-y-3">
      <article
        data-testid="product-system-component-first-composer-card"
        className="rounded-lg border border-slate-800 bg-slate-950/40 p-3"
      >
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <p className="text-[12px] font-bold text-slate-100">{model.composerTemplateCode}</p>
            <p className="mt-0.5 text-[10px] text-cyan-200">Composer — coordinates components only</p>
          </div>
          <div className="flex flex-wrap gap-1.5 text-[9px] font-bold">
            <span className="rounded border border-slate-700 bg-slate-900 px-1.5 py-0.5 text-slate-300">
              readiness: {model.composerReadiness}
            </span>
            <span className="rounded border border-amber-700/40 bg-amber-900/20 px-1.5 py-0.5 text-amber-300">
              guard: {model.composerActivationGuard}
            </span>
          </div>
        </div>
        <div className="mt-2 grid gap-2 md:grid-cols-2 text-[10px] text-slate-200">
          <div className="rounded-lg border border-slate-800/90 bg-[#0D1321]/90 px-3 py-2">
            <p className="font-bold uppercase tracking-wide text-slate-400">Composer boundary</p>
            <p className="mt-1">does not own material truth</p>
            <p className="mt-0.5">does not own operation truth</p>
            <p className="mt-0.5">
              no module links: <span className="font-bold text-cyan-200">{String(model.noModuleLinks)}</span>
            </p>
          </div>
          <div className="rounded-lg border border-slate-800/90 bg-[#0D1321]/90 px-3 py-2">
            <p className="font-bold uppercase tracking-wide text-slate-400">Blockers</p>
            <p className="mt-1 font-mono text-amber-200/85">{model.composerBlockers.join(", ") || "OWNER_GO_REQUIRED"}</p>
          </div>
        </div>
        <div className="mt-3 overflow-hidden rounded-lg border border-slate-800/90 bg-[#0D1321]/90">
          <div className="grid grid-cols-[minmax(0,0.9fr)_minmax(0,0.95fr)_minmax(0,0.75fr)_minmax(0,1fr)] gap-2 border-b border-slate-800 px-3 py-2 text-[9px] font-bold uppercase tracking-wide text-slate-500">
            <span>Composition list</span>
            <span>Template</span>
            <span>Kind</span>
            <span>Product Truth target</span>
          </div>
          <div className="divide-y divide-slate-800/80">
            {model.compositionList.map((entry) => (
              <div
                key={entry.componentTemplateCode}
                className="grid grid-cols-[minmax(0,0.9fr)_minmax(0,0.95fr)_minmax(0,0.75fr)_minmax(0,1fr)] gap-2 px-3 py-2 text-[10px]"
              >
                <div>
                  <p className="font-bold text-slate-100">{entry.role.toUpperCase()}</p>
                  <p className="mt-0.5 font-mono text-[9px] text-slate-500">{entry.componentId}</p>
                </div>
                <p className="font-mono text-cyan-200/85">{entry.componentTemplateCode}</p>
                <p className="text-slate-300">{entry.kind}</p>
                <p className="font-mono text-slate-300">{entry.targetProductTruthPath}</p>
              </div>
            ))}
          </div>
        </div>
      </article>

      <section
        data-testid="product-system-component-first-components-list"
        className="rounded-lg border border-slate-800 bg-slate-950/40 p-3"
      >
        <div className="flex items-center justify-between gap-2">
          <h4 className="text-[11px] font-bold uppercase tracking-wide text-slate-100">Component templates</h4>
          <span className="rounded border border-slate-700 bg-slate-900 px-2 py-0.5 text-[9px] font-bold text-slate-300">
            {model.components.length} components
          </span>
        </div>
        <div className="mt-3 grid gap-3 xl:grid-cols-2">
          {model.components.map((component) => (
            <ComponentFirstComponentEntityCard
              key={component.templateCode}
              component={component}
              dossierEntry={dossierEntryForTemplate(component.templateCode)}
              formEntry={formEntryForComponent(component.templateCode, formReadiness.contractEntries)}
              productTruthPrefix={productTruthPrefixForTemplate(component.templateCode)}
            />
          ))}
        </div>
      </section>
    </div>
  );
}

function ComponentFirstDossierPanel({
  dossierAlignment,
}: {
  dossierAlignment: ReturnType<typeof assessComponentFirstDossierAlignment>;
}) {
  return (
    <section data-testid="product-system-component-first-panel-dossier" className="space-y-3">
      <div
        data-testid="product-system-component-first-dossier-section"
        className="rounded-lg border border-slate-700/80 bg-slate-950/60 px-3 py-3"
      >
        <h4 className="text-[11px] font-bold uppercase tracking-wide text-slate-200">Dossier contract (readonly)</h4>
        <div
          data-testid="product-system-component-first-dossier-alignment"
          className="mt-2 space-y-2"
        >
          <div className="flex flex-wrap items-center gap-2 text-[10px] font-bold">
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
          <p
            data-testid="product-system-component-first-dossier-guard"
            className="text-[10px] font-mono text-cyan-200/80"
          >
            Guard: No task materialization; No ProductAggregate runtime; No ProductDefinition activation; No Pricing /
            Quote / Order / Execution; No Work Intake exposure
          </p>
          {dossierAlignment.runtimeActivationLeakIssues.length > 0 ? (
            <p
              data-testid="product-system-component-first-dossier-activation-leak"
              className="text-[10px] font-mono text-rose-200/90"
            >
              Activation leak signals: {dossierAlignment.runtimeActivationLeakIssues.join(", ")}
            </p>
          ) : null}
        </div>
      </div>

      <div
        data-testid="product-system-component-first-dossier-cards"
        className="grid gap-3 xl:grid-cols-2"
      >
        {dossierAlignment.contractEntries.map((entry) => (
          <article
            key={entry.templateCode}
            data-testid={`product-system-component-first-dossier-card-${entry.templateCode}`}
            className="rounded-lg border border-slate-800/90 bg-[#0D1321]/90 p-3"
          >
            <p className="font-mono text-[10px] font-bold text-cyan-200">{entry.templateCode}</p>
            <div className="mt-2 space-y-1 text-[10px] text-slate-300">
              <p>
                <span className="text-slate-500">Dossier role:</span> {entry.expectedDossierRole}
              </p>
              <p>
                <span className="text-slate-500">Truth owner:</span> {truthOwnerLabel(entry.expectedTruthOwner)}
              </p>
              <p>
                <span className="text-slate-500">Kind:</span> {entry.expectedKind}
              </p>
              <p>
                <span className="text-slate-500">Future metadata:</span>{" "}
                {entry.futureAllowedMetadata.join(", ")}
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
          </article>
        ))}
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
}: {
  model: ComponentFirstReadonlySetModel;
  driftAssessment: ReturnType<typeof assessComponentFirstContractDrift>;
  dossierAlignment: ReturnType<typeof assessComponentFirstDossierAlignment>;
  productDefinitionReadiness: ReturnType<typeof assessComponentFirstProductDefinitionReadiness>;
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
    </div>
  );
}

export function ComponentFirstReadonlyCandidatePanel({
  templates,
  availabilityItems,
  selectedTemplateCode,
}: {
  templates: ProductTemplateEntity[];
  availabilityItems: ProductTemplateAvailabilityItem[];
  selectedTemplateCode: string;
}) {
  const [activeTab, setActiveTab] = useState<ComponentFirstCandidateTab>("overview");

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

  if (!model) {
    return null;
  }

  return (
    <section
      data-testid="product-system-component-first-letters-set"
      className="rounded-xl border border-cyan-800/40 bg-cyan-950/10 p-3"
    >
      <div className="flex flex-wrap items-start justify-between gap-3 border-b border-cyan-900/40 pb-3">
        <div>
          <h3 className="text-[13px] font-bold text-cyan-100">Component-first Letters Candidate</h3>
          <p className="mt-0.5 text-[11px] text-cyan-200/75">
            Parallel readonly candidate set — does not replace TPL-VOLUMETRIC-LETTERS_v2 and does not activate anything.
          </p>
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

      <div
        className="mt-3 flex flex-wrap gap-1.5"
        role="tablist"
        aria-label="Component-first candidate sections"
      >
        {CANDIDATE_TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={activeTab === tab.id}
            data-testid={tab.testId}
            onClick={() => setActiveTab(tab.id)}
            className={`rounded-md border px-2.5 py-1 text-[10px] font-bold transition-colors ${
              activeTab === tab.id
                ? "border-cyan-500/50 bg-cyan-500/10 text-cyan-100"
                : "border-slate-700 bg-slate-900 text-slate-400 hover:text-slate-200"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="mt-3">
        {activeTab === "overview" ? (
          <ComponentFirstOverviewPanel
            model={model}
            ownerSummary={ownerSummary}
            driftAssessment={driftAssessment}
          />
        ) : null}
        {activeTab === "components" ? (
          <ComponentFirstComponentsPanel model={model} formReadiness={formReadiness} />
        ) : null}
        {activeTab === "dossier" ? <ComponentFirstDossierPanel dossierAlignment={dossierAlignment} /> : null}
        {activeTab === "form-system" ? <ComponentFirstFormSystemPanel formReadiness={formReadiness} /> : null}
        {activeTab === "product-truth" ? (
          <ComponentFirstProductTruthPanel productTruthMapping={productTruthMapping} />
        ) : null}
        {activeTab === "guards-audit" ? (
          <ComponentFirstGuardsAuditPanel
            model={model}
            driftAssessment={driftAssessment}
            dossierAlignment={dossierAlignment}
            productDefinitionReadiness={productDefinitionReadiness}
          />
        ) : null}
      </div>
    </section>
  );
}

/** @deprecated Use ComponentFirstReadonlyCandidatePanel — kept for editor imports */
export const ComponentFirstReadonlyStatusPanel = ComponentFirstReadonlyCandidatePanel;

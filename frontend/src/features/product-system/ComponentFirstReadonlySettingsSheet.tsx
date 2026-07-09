import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import type { ReactNode } from "react";
import type { ComponentFirstDossierContractEntry } from "./componentFirstReadonlyDossierAlignment";
import {
  COMPONENT_FIRST_DOSSIER_CONTRACT_FIXTURE,
  componentFirstDossierRuntimeLinkLabel,
} from "./componentFirstReadonlyDossierAlignment";
import type { ComponentFirstFormReadinessEntry } from "./componentFirstReadonlyFormSystemReadiness";
import type { ComponentFirstProductTruthMappingEntry } from "./componentFirstReadonlyProductTruthMapping";
import type { ComponentFirstReadonlyComponent, ComponentFirstReadonlySetModel } from "./componentFirstReadonlySetModel";
import {
  COMPONENT_FIRST_COMPOSER_TEMPLATE_CODE,
  normalizeComponentFirstTemplateCode,
} from "./componentFirstReadonlyCompleteness";
import {
  componentFirstDisplayName,
  ComponentFirstSemanticLabel,
  ComponentFirstStatusStrip,
  isComponentFirstComposer,
  ReadonlyDrawerBanner,
  truthOwnerLabel,
} from "./componentFirstReadonlyUiShared";

export type ComponentFirstSettingsTarget =
  | { kind: "product" }
  | { kind: "component"; templateCode: string };

type ProductSettingsContext = {
  model: ComponentFirstReadonlySetModel;
  dossierEntry?: ComponentFirstDossierContractEntry;
  composerFormEntry?: ComponentFirstFormReadinessEntry;
  composerTruthEntries: ComponentFirstProductTruthMappingEntry[];
  dossierRuntimeLinkState: string;
};

type ComponentSettingsContext = {
  component: ComponentFirstReadonlyComponent;
  dossierEntry?: ComponentFirstDossierContractEntry;
  formEntry?: ComponentFirstFormReadinessEntry;
  truthEntries: ComponentFirstProductTruthMappingEntry[];
  dossierRuntimeLinkState: string;
};

function SettingsSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-lg border border-slate-800/90 bg-[#0D1321]/70 px-3 py-2.5">
      <h4 className="text-[10px] font-bold uppercase tracking-wide text-slate-400">{title}</h4>
      <div className="mt-2 space-y-1 text-[11px] text-slate-200">{children}</div>
    </section>
  );
}

function ForbiddenNowList({ items }: { items: string[] }) {
  return (
    <ul className="mt-1 space-y-0.5 text-[10px] text-rose-200/90">
      {items.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  );
}

function ProductSettingsBody({ ctx }: { ctx: ProductSettingsContext }) {
  const { model, dossierEntry, composerFormEntry, composerTruthEntries } = ctx;

  return (
    <div className="space-y-3 px-1 pb-6">
      <ComponentFirstStatusStrip showWorkIntake={false} testIdPrefix="product-system-component-first-settings" />
      <SettingsSection title="Overview">
        <p>
          <span className="text-slate-500">Title:</span> Litere volumetrice component-first
        </p>
        <p>
          <span className="text-slate-500">Template code:</span> {model.composerTemplateCode}
        </p>
        <p>
          <span className="text-slate-500">Type:</span> Product Template / Composer
        </p>
        <p>
          <span className="text-slate-500">Readiness:</span> {model.composerReadiness}
        </p>
        <p>
          <span className="text-slate-500">Activation guard:</span> {model.composerActivationGuard}
        </p>
        <p>
          <span className="text-slate-500">Readonly boundary:</span> inactive candidate set; no Work Intake; no
          commercial path
        </p>
      </SettingsSection>
      <SettingsSection title="Composition">
        <p className="text-[10px] text-slate-400">Composer coordinates {model.components.length} component templates.</p>
        <ul className="mt-1 space-y-1 text-[10px] font-mono text-cyan-200/85">
          {model.compositionList.map((entry) => (
            <li key={entry.componentTemplateCode}>
              {entry.role} → {entry.componentTemplateCode}
            </li>
          ))}
        </ul>
        <p className="mt-2 text-[10px] text-slate-400">
          No module links: <span className="font-bold text-slate-200">{String(model.noModuleLinks)}</span>
        </p>
        <details className="mt-2 text-[10px] text-slate-400">
          <summary className="cursor-pointer font-semibold text-slate-300">Dependency summary</summary>
          <ul className="mt-1 space-y-0.5 font-mono">
            {model.dependencyGraph.map((edge) => (
              <li key={`${edge.from}-${edge.to}`}>
                {edge.from} → {edge.to}
              </li>
            ))}
          </ul>
        </details>
      </SettingsSection>
      <SettingsSection title="Product Dossier">
        <p>
          <span className="text-slate-500">Dossier role:</span> {dossierEntry?.expectedDossierRole ?? "composer_orchestration"}
        </p>
        <p>
          <span className="text-slate-500">Truth owner:</span>{" "}
          {truthOwnerLabel(dossierEntry?.expectedTruthOwner ?? "product_composer")}
        </p>
        <p>
          <span className="text-slate-500">Future metadata:</span>{" "}
          {dossierEntry?.futureAllowedMetadata.join(", ") ?? "technical_fields, validations, calculation_readiness"}
        </p>
        <p className="text-slate-500">Forbidden now:</p>
        <ForbiddenNowList
          items={[
            "No task materialization",
            "No ProductAggregate runtime",
            "No ExecutionPlan",
            "No Pricing / Quote / Order / Execution",
            "No Work Intake exposure",
          ]}
        />
      </SettingsSection>
      <SettingsSection title="Form System readiness">
        {composerFormEntry && composerFormEntry.role === "product_composer" ? (
          <>
            <p>Composer coordinates sections only.</p>
            <p>
              <span className="text-slate-500">Coordinates:</span> {composerFormEntry.coordinates.join(", ")}
            </p>
            <p>
              <span className="text-slate-500">ownsTruth:</span> false
            </p>
          </>
        ) : (
          <p>Composer coordinates: selected components, component compatibility, overall readiness</p>
        )}
      </SettingsSection>
      <SettingsSection title="Product Truth mapping">
        <ul className="space-y-0.5 font-mono text-[10px] text-cyan-200/85">
          {composerTruthEntries.map((entry) => (
            <li key={entry.fieldGroup}>
              {entry.fieldGroup} → {entry.futureProductTruthPath}
            </li>
          ))}
        </ul>
        <p className="mt-2 text-[10px] text-slate-400">Write policy: readonly mapping only; no confirmed values created</p>
      </SettingsSection>
      <SettingsSection title="Guards">
        <ForbiddenNowList
          items={[
            `Work Intake exposure: ${model.noWorkIntakeExposure ? "no" : "leak"}`,
            `Pricing: ${model.noPricingActivation ? "no" : "leak"}`,
            "Quote / Order / Execution: no",
            `ProductAggregate runtime: ${model.noProductAggregateRuntimeWiring ? "no" : "leak"}`,
            "TaskGraph / ExecutionPlan: no",
            "Product Truth write: no",
          ]}
        />
      </SettingsSection>
    </div>
  );
}

function ComponentSettingsBody({ ctx }: { ctx: ComponentSettingsContext }) {
  const { component, dossierEntry, formEntry, truthEntries } = ctx;
  const displayName = componentFirstDisplayName(component.templateCode);
  const fieldGroups =
    formEntry && formEntry.role === "component_template" ? formEntry.fieldGroups.join(", ") : "—";

  return (
    <div className="space-y-3 px-1 pb-6">
      <ComponentFirstStatusStrip showWorkIntake={false} testIdPrefix="product-system-component-first-settings" />
      <SettingsSection title="Overview">
        <p>
          <span className="text-slate-500">Display name:</span> {displayName}
        </p>
        <p>
          <span className="text-slate-500">Template code:</span> {component.templateCode}
        </p>
        <p>
          <span className="text-slate-500">Type:</span> Component Template
        </p>
        <p>
          <span className="text-slate-500">Truth owner:</span>{" "}
          {truthOwnerLabel(dossierEntry?.expectedTruthOwner ?? "component_owned_truth")}
        </p>
        <p>
          <span className="text-slate-500">Role label:</span> {component.roleLabel}
        </p>
        <p>
          <span className="text-slate-500">Component kind:</span> {component.componentKind}
        </p>
        <p>
          <span className="text-slate-500">Readiness state:</span> {component.readinessState}
        </p>
        <p>
          <span className="text-slate-500">active:</span> {String(component.active)}
        </p>
        <p>
          <span className="text-slate-500">Live row:</span>{" "}
          {component.liveRowPresent ? "live inactive row" : "contract fallback row"}
        </p>
      </SettingsSection>
      <SettingsSection title="Dossier">
        <p>
          <span className="text-slate-500">Dossier role:</span> {dossierEntry?.expectedDossierRole ?? "—"}
        </p>
        <p>
          <span className="text-slate-500">Future metadata:</span>{" "}
          {dossierEntry?.futureAllowedMetadata.join(", ") ?? "—"}
        </p>
        <p>
          <span className="text-slate-500">Runtime dossier link:</span> {ctx.dossierRuntimeLinkState}
        </p>
        <p className="text-slate-500">Forbidden now:</p>
        <ForbiddenNowList
          items={[
            "No component root",
            "No component quote",
            "No task materialization",
            "No ExecutionPlan",
            "No Pricing / Quote / Order / Execution",
            "No Work Intake exposure",
          ]}
        />
      </SettingsSection>
      <SettingsSection title="Fields / Form readiness">
        <p>
          <span className="text-slate-500">Field groups:</span> {fieldGroups}
        </p>
        {formEntry && formEntry.role === "component_template" ? (
          <>
            <p>
              <span className="text-slate-500">Possible sources:</span> {formEntry.possibleSources.join(", ")}
            </p>
            <p>
              <span className="text-slate-500">State policy:</span> {formEntry.requiredStatePolicy.join("; ")}
            </p>
          </>
        ) : null}
      </SettingsSection>
      <SettingsSection title="Product Truth paths">
        <p className="font-mono text-[10px] text-cyan-200/85">{component.targetProductTruthPath}</p>
        <ul className="mt-1 space-y-0.5 font-mono text-[10px] text-cyan-200/80">
          {truthEntries.map((entry) => (
            <li key={entry.fieldGroup}>
              {entry.fieldGroup} → {entry.futureProductTruthPath}
            </li>
          ))}
        </ul>
        <p className="mt-2 text-[10px] text-slate-400">
          suggested / fallback / hydrated / manual draft ≠ confirmed
        </p>
      </SettingsSection>
      <SettingsSection title="Future calculation readiness">
        <p>
          <span className="text-slate-500">Readiness:</span> {component.readinessState} (planned)
        </p>
        <p>
          <span className="text-slate-500">Activation guard:</span> {component.activationGuard}
        </p>
        <details className="mt-1 text-[10px] text-amber-200/90">
          <summary className="cursor-pointer font-semibold text-slate-300">
            Blockers ({component.blockers.length})
          </summary>
          <p className="mt-1 font-mono">{component.blockers.join(", ") || "none"}</p>
        </details>
      </SettingsSection>
      <SettingsSection title="Guards">
        <ForbiddenNowList
          items={[
            "No component root",
            "No component quote",
            "No task materialization",
            "No ExecutionPlan",
          ]}
        />
      </SettingsSection>
    </div>
  );
}

export function ComponentFirstReadonlySettingsSheet({
  open,
  onOpenChange,
  target,
  model,
  formEntries,
  truthEntries,
  dossierRuntimeLinkState,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  target: ComponentFirstSettingsTarget | null;
  model: ComponentFirstReadonlySetModel;
  formEntries: ComponentFirstFormReadinessEntry[];
  truthEntries: ComponentFirstProductTruthMappingEntry[];
  dossierRuntimeLinkState: string;
}) {
  if (!target) return null;

  const dossierEntry = (templateCode: string) =>
    COMPONENT_FIRST_DOSSIER_CONTRACT_FIXTURE.find(
      (entry) => normalizeComponentFirstTemplateCode(entry.templateCode) === normalizeComponentFirstTemplateCode(templateCode)
    );

  const formEntry = (templateCode: string) =>
    formEntries.find(
      (entry) => normalizeComponentFirstTemplateCode(entry.templateCode) === normalizeComponentFirstTemplateCode(templateCode)
    );

  const truthFor = (templateCode: string) =>
    truthEntries.filter(
      (entry) => normalizeComponentFirstTemplateCode(entry.templateCode) === normalizeComponentFirstTemplateCode(templateCode)
    );

  const title =
    target.kind === "product"
      ? `Product Settings — ${COMPONENT_FIRST_COMPOSER_TEMPLATE_CODE}`
      : `Component Settings — ${componentFirstDisplayName(target.templateCode)} — ${target.templateCode}`;

  const component =
    target.kind === "component"
      ? model.components.find(
          (entry) => normalizeComponentFirstTemplateCode(entry.templateCode) === normalizeComponentFirstTemplateCode(target.templateCode)
        )
      : undefined;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="right"
        data-testid="product-system-component-first-settings-sheet"
        className="w-full overflow-y-auto border-[#1E293B] bg-[#0A0F1A] sm:max-w-lg"
      >
        <SheetHeader className="space-y-2 border-b border-slate-800 pb-3">
          <ReadonlyDrawerBanner />
          <SheetTitle className="text-left text-[13px] font-bold text-slate-100">{title}</SheetTitle>
          <SheetDescription className="text-left text-[11px] text-slate-400">
            Readonly contract view — no save, no edit, no activation.
          </SheetDescription>
        </SheetHeader>
        {target.kind === "product" ? (
          <ProductSettingsBody
            ctx={{
              model,
              dossierEntry: dossierEntry(COMPONENT_FIRST_COMPOSER_TEMPLATE_CODE),
              composerFormEntry: formEntry(COMPONENT_FIRST_COMPOSER_TEMPLATE_CODE),
              composerTruthEntries: truthFor(COMPONENT_FIRST_COMPOSER_TEMPLATE_CODE),
              dossierRuntimeLinkState,
            }}
          />
        ) : component ? (
          <ComponentSettingsBody
            ctx={{
              component,
              dossierEntry: dossierEntry(component.templateCode),
              formEntry: formEntry(component.templateCode),
              truthEntries: truthFor(component.templateCode),
              dossierRuntimeLinkState,
            }}
          />
        ) : null}
      </SheetContent>
    </Sheet>
  );
}

export function dossierEntryForTemplate(
  templateCode: string,
  contract: readonly ComponentFirstDossierContractEntry[] = COMPONENT_FIRST_DOSSIER_CONTRACT_FIXTURE
): ComponentFirstDossierContractEntry | undefined {
  return contract.find(
    (entry) => normalizeComponentFirstTemplateCode(entry.templateCode) === normalizeComponentFirstTemplateCode(templateCode)
  );
}

export { isComponentFirstComposer, componentFirstDisplayName, ComponentFirstSemanticLabel, truthOwnerLabel };

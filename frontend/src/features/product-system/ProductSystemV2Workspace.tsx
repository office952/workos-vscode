/**
 * Product System V2 — blank workspace from zero (IA/structure).
 * Primary experience for /product-system/products[/:templateCode].
 * Structură produs reuses the classic editor visual language (chips + timeline).
 * Legacy catalog remains available via ?ps_legacy=1.
 */
import { useEffect, useMemo, useState } from "react";
import {
  parseTemplateComponentsWithLegacy,
  type ProductTemplateAvailabilityItem,
  type ProductTemplateEntity,
} from "@/lib/api";
import { normalizeTemplateCode } from "@/lib/activeTemplateScope";
import { templateEntityForAvailability } from "./productSystemCanonicalCatalogModel";
import { ModuleModelDeferredNotice } from "@/components/workos/design-system";
import { ProductCompilerDisplayShell } from "./ProductCompilerDisplayShell";
import { ProductSystemOfferCostChannels } from "./ProductSystemOfferCostChannels";
import { ProductSystemSpineBand } from "./ProductSystemSpineBand";
import { ProductSystemSurfaceTruthChips } from "./ProductSystemSurfaceTruthChips";
import { ProductSystemStructureReadonlyPanel } from "./ProductSystemStructureReadonlyPanel";
import { ProductE2EReadinessPanel } from "./ProductE2EReadinessPanel";
import { PS_SURFACE_INSET, PS_SURFACE_PANEL } from "./productSystemSurfaces";
import {
  PRODUCT_COMPILER_NO_PRICE_HELP,
  PRODUCT_TEMPLATE_LABEL,
} from "./productTemplateModulesVocabulary";
import { isVolumetricLettersTemplate } from "./componentTypeDisplay";
import {
  buildProductSystemV2List,
  findV2ListItem,
  partitionProductModulesForDisplay,
  type ProductSystemV2ModuleRow,
} from "./productSystemV2WorkspaceModel";

export type ProductSystemV2WorkspaceProps = {
  templates: ProductTemplateEntity[];
  availabilityItems: ProductTemplateAvailabilityItem[];
  loading: boolean;
  search: string;
  onSearchChange: (value: string) => void;
  requestedTemplateCode?: string | null;
  onRequestedTemplateCodeChange?: (code: string | null) => void;
  onOpenTemplate?: (template: ProductTemplateEntity) => void;
};

function OptionalSupportRow({ row }: { row: ProductSystemV2ModuleRow }) {
  return (
    <li
      className={`${PS_SURFACE_INSET} px-3 py-2.5`}
      data-testid={`product-system-v2-module-${row.moduleCode}`}
    >
      <div className="flex items-baseline justify-between gap-2">
        <span className="truncate text-[13px] font-semibold text-wo-text-primary">{row.roleLabel}</span>
        <span className="shrink-0 text-[10px] text-wo-text-muted">{row.statusLabel}</span>
      </div>
      {row.uiHint ? (
        <p className="mt-0.5 text-[12px] leading-snug text-wo-text-muted">{row.uiHint}</p>
      ) : null}
      <p className="mt-1 truncate font-mono text-[10px] text-wo-text-dim">{row.moduleCode}</p>
    </li>
  );
}

export function ProductSystemV2Workspace({
  templates,
  availabilityItems,
  loading,
  search,
  onSearchChange,
  requestedTemplateCode,
  onRequestedTemplateCodeChange,
  onOpenTemplate,
}: ProductSystemV2WorkspaceProps) {
  const items = useMemo(
    () => buildProductSystemV2List({ templates, availabilityItems, search }),
    [templates, availabilityItems, search],
  );

  const selected = useMemo(
    () => findV2ListItem(items, requestedTemplateCode),
    [items, requestedTemplateCode],
  );

  useEffect(() => {
    if (loading || items.length === 0) return;
    if (requestedTemplateCode && findV2ListItem(items, requestedTemplateCode)) return;
    if (requestedTemplateCode && !findV2ListItem(items, requestedTemplateCode)) {
      return;
    }
    if (!requestedTemplateCode && items[0]) {
      onRequestedTemplateCodeChange?.(items[0].templateCode);
    }
  }, [loading, items, requestedTemplateCode, onRequestedTemplateCodeChange]);

  const availability = selected?.product.availability ?? null;
  const template =
    selected && availability
      ? templateEntityForAvailability(availability, templates)
      : null;
  const layers = availability ? partitionProductModulesForDisplay(availability) : null;
  const hasClassicStructure = useMemo(() => {
    if (!template) return false;
    return parseTemplateComponentsWithLegacy(
      template.components_json,
      template.operations_json,
      template.required_materials_json,
    ).some((c) => c._legacy !== true);
  }, [template]);
  // Letters: keep structure pure — ACM/premount attach later via contract/Composer, not here.
  const showOptionalSupports =
    !!layers &&
    layers.optional.length > 0 &&
    !isVolumetricLettersTemplate(selected?.templateCode);
  const [adminOpen, setAdminOpen] = useState(false);

  return (
    <div
      className="space-y-4"
      data-testid="product-system-v2-workspace"
      data-workspace="v2-blank"
    >
      <header data-testid="product-system-v2-header" className="space-y-2">
        <ProductSystemSpineBand compact testId="product-system-v2-spine" />
        <ProductSystemSurfaceTruthChips testId="product-system-v2-surface-truth-chips" />
        <ModuleModelDeferredNotice compact />
      </header>

      <div className="grid gap-4 lg:grid-cols-[minmax(16rem,20rem)_minmax(0,1fr)]">
        <aside
          className={`${PS_SURFACE_PANEL} flex min-h-[22rem] flex-col p-3`}
          data-testid="product-system-v2-product-rail"
        >
          <label className="sr-only" htmlFor="product-system-v2-search">
            Caută produs
          </label>
          <input
            id="product-system-v2-search"
            type="search"
            value={search}
            onChange={(event) => onSearchChange(event.target.value)}
            placeholder="Caută Product Template…"
            data-testid="product-system-v2-search"
            className="w-full rounded-md border border-wo-border-strong bg-wo-surface-input px-2.5 py-2 text-sm text-wo-text-primary outline-none placeholder:text-wo-text-dim focus:border-wo-info/50"
          />
          <p className="mt-2 text-[10px] font-semibold uppercase tracking-wide text-wo-text-dim">
            Product Templates
          </p>
          <ul
            className="mt-1.5 flex-1 space-y-1 overflow-y-auto"
            data-testid="product-system-v2-product-list"
          >
            {loading ? (
              <li className="px-2 py-6 text-center text-[12px] text-wo-text-muted">Se încarcă…</li>
            ) : items.length === 0 ? (
              <li className="px-2 py-6 text-center text-[12px] text-wo-text-muted">
                Niciun Product Template vizibil.
              </li>
            ) : (
              items.map((item) => {
                const active =
                  normalizeTemplateCode(item.templateCode) ===
                  normalizeTemplateCode(requestedTemplateCode ?? "");
                return (
                  <li key={item.templateCode}>
                    <button
                      type="button"
                      data-testid={`product-system-v2-product-${item.templateCode}`}
                      data-active={active ? "true" : "false"}
                      onClick={() => onRequestedTemplateCodeChange?.(item.templateCode)}
                      className={`w-full rounded-md border px-2.5 py-2 text-left transition-colors ${
                        active
                          ? "border-sky-300 bg-sky-50 dark:border-sky-700/50 dark:bg-sky-950/30"
                          : "border-transparent hover:border-wo-border-strong hover:bg-wo-hover"
                      }`}
                    >
                      <span className="block truncate text-[13px] font-medium text-wo-text-primary">
                        {item.displayName}
                      </span>
                      <span className="mt-0.5 block truncate font-mono text-[10px] text-wo-text-dim">
                        {item.templateCode}
                      </span>
                    </button>
                  </li>
                );
              })
            )}
          </ul>
        </aside>

        <main className="min-h-[22rem] space-y-4" data-testid="product-system-v2-main">
          {!selected || !availability ? (
            <div
              className={`${PS_SURFACE_PANEL} flex min-h-[22rem] flex-col items-start justify-center gap-3 px-6 py-8`}
              data-testid="product-system-v2-empty"
            >
              <p className="text-sm font-semibold text-wo-text-primary">Alege un Product Template</p>
              <p className="max-w-md text-[12px] leading-relaxed text-wo-text-muted">
                Structura produsului apare aici — ca în editorul clasic, doar pentru citire.
              </p>
              {requestedTemplateCode ? (
                <p
                  className="font-mono text-[11px] text-amber-300/90"
                  data-testid="product-system-v2-unknown-template"
                >
                  Template necunoscut în listă: {requestedTemplateCode}
                </p>
              ) : null}
            </div>
          ) : (
            <>
              <section
                className={`${PS_SURFACE_PANEL} px-4 py-3`}
                data-testid="product-system-v2-template-center"
              >
                <p className="text-[10px] font-bold uppercase tracking-wide text-wo-text-muted">
                  {PRODUCT_TEMPLATE_LABEL}
                </p>
                <div className="mt-1 flex flex-wrap items-baseline gap-x-3 gap-y-1">
                  <h3 className="text-xl font-semibold text-wo-text-primary">{selected.displayName}</h3>
                  <span className="font-mono text-xs text-wo-text-muted">{selected.templateCode}</span>
                </div>
              </section>

              {hasClassicStructure && template ? (
                <ProductSystemStructureReadonlyPanel template={template} />
              ) : (
                <section
                  className={`${PS_SURFACE_PANEL} px-4 py-4`}
                  data-testid="product-system-v2-modules-center"
                >
                  <p
                    className="text-[14px] font-bold text-wo-text-primary"
                    data-testid="product-system-v2-structure-title"
                  >
                    Structură produs
                  </p>
                  <p
                    className="mt-2 text-[12px] text-wo-text-muted"
                    data-testid="product-system-v2-modules-empty"
                  >
                    Acest template nu are încă componente în structura clasică.
                  </p>
                </section>
              )}

              {showOptionalSupports ? (
                <section
                  className={`${PS_SURFACE_PANEL} space-y-2 px-4 py-3`}
                  data-testid="product-system-v2-modules-optional"
                >
                  <p className="text-[12px] font-semibold text-wo-text-secondary">
                    În plus, dacă e nevoie ({layers!.optional.length})
                  </p>
                  <p className="text-[11px] text-wo-text-muted">
                    Suporturi / montaje opționale — nu înlocuiesc structura de mai sus.
                  </p>
                  <ul className="mt-1 grid gap-2 sm:grid-cols-2">
                    {layers!.optional.map((row) => (
                      <OptionalSupportRow key={row.key} row={row} />
                    ))}
                  </ul>
                </section>
              ) : null}

              <details
                className={`${PS_SURFACE_PANEL} px-4 py-3`}
                data-testid="product-system-v2-compiler-readiness-row"
              >
                <summary className="cursor-pointer select-none text-[12px] font-medium text-wo-text-muted hover:text-wo-text-primary">
                  Product Compiler / Pregătire
                </summary>
                <div className="mt-3 grid gap-3 lg:grid-cols-2">
                  <div data-testid="product-system-v2-compiler">
                    <ProductCompilerDisplayShell stage="both" compact />
                    <p className="mt-2 px-1 text-[10px] text-wo-text-dim">
                      {PRODUCT_COMPILER_NO_PRICE_HELP}
                    </p>
                  </div>
                  <section
                    className={`${PS_SURFACE_INSET} px-4 py-3`}
                    data-testid="product-system-v2-readiness"
                  >
                    <p className="text-[10px] font-bold uppercase tracking-wide text-sky-300/90">
                      Pregătire
                    </p>
                    <p className="mt-1 text-[13px] font-medium text-wo-text-primary">
                      {selected.rollupLabel}
                    </p>
                    <p className="mt-1 text-[12px] leading-relaxed text-wo-text-muted">
                      {selected.blockerCount > 0
                        ? `${selected.blockerCount} blocaje structurale — verifică înainte de publicare.`
                        : "Fără blocaje structurale în rollup-ul curent."}
                    </p>
                  </section>
                </div>
              </details>

              <details
                className={`${PS_SURFACE_PANEL} px-4 py-3`}
                data-testid="product-system-v2-downstream"
              >
                <summary className="cursor-pointer select-none text-[12px] font-medium text-wo-text-muted hover:text-wo-text-primary">
                  Alte sisteme — Cost / Ofertă / Execution
                </summary>
                <div className="mt-3">
                  <ProductSystemOfferCostChannels testId="product-system-v2-downstream-channels" />
                </div>
              </details>

              <details
                className={`${PS_SURFACE_PANEL} px-4 py-3`}
                data-testid="product-system-v2-admin-drawer"
                open={adminOpen}
                onToggle={(event) => setAdminOpen((event.target as HTMLDetailsElement).open)}
              >
                <summary
                  className="cursor-pointer select-none text-[12px] font-medium text-wo-text-muted hover:text-wo-text-secondary"
                  data-testid="product-system-v2-admin-summary"
                >
                  Detalii tehnice (opțional)
                </summary>
                <div className="mt-3 space-y-3" data-testid="product-system-v2-admin-body">
                  {layers && layers.contracts.length > 0 ? (
                    <div data-testid="product-system-v2-shared-contracts">
                      <p className="text-[11px] font-semibold text-wo-text-secondary">
                        Verificare internă pe aceleași piese
                      </p>
                      <p className="mt-0.5 text-[11px] leading-relaxed text-wo-text-muted">
                        Nu sunt piese noi — e același produs, văzut pentru audit.
                      </p>
                      <ul className="mt-2 space-y-1.5">
                        {layers.contracts.map((contract) => (
                          <li
                            key={contract.component_key}
                            className={`${PS_SURFACE_INSET} px-2.5 py-2`}
                            data-testid={`product-system-v2-contract-${contract.component_key}`}
                          >
                            <div className="flex flex-wrap items-baseline justify-between gap-2">
                              <span className="text-[12px] font-medium text-wo-text-primary">
                                {contract.display_name}
                              </span>
                              <span className="text-[10px] uppercase tracking-wide text-wo-text-muted">
                                {contract.confidence}
                              </span>
                            </div>
                            <p className="mt-0.5 font-mono text-[10px] text-wo-text-dim">
                              {contract.module_template_code}
                            </p>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                  <ProductE2EReadinessPanel templateCode={selected.templateCode} />
                  {template && onOpenTemplate ? (
                    <button
                      type="button"
                      data-testid="product-system-v2-admin-open-editor"
                      onClick={() => onOpenTemplate(template)}
                      className="rounded border border-slate-700 px-2.5 py-1.5 text-[11px] font-medium text-wo-text-secondary hover:bg-slate-900/60"
                    >
                      Laborator vechi (editor șablon)
                    </button>
                  ) : null}
                </div>
              </details>
            </>
          )}
        </main>
      </div>
    </div>
  );
}

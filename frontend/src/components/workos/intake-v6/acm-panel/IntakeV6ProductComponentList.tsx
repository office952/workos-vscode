/**
 * Sibling product component list for Configurare.
 * Consumes uiReadModel for AcmPanel — no raw payload interpretation.
 */

import {
  buildAcmPanelUiReadModel,
  type AcmPanelUiReadModel,
} from "@/lib/intakeV6/acmPanel/uiReadModel";
import { intakeV6ShowOperatorConfigStatusBadges } from "@/lib/intakeV6/intakeV6OperatorConfigStatusChrome";
import type { IntakeV6ProductComponentId } from "@/lib/intakeV6/useIntakeV6ProductComponentSelection";

export type ProductComponentListItem = {
  id: IntakeV6ProductComponentId;
  title: string;
  typeLabel: string;
  statusLabel: string;
  statusTone: "ok" | "pending" | "blocker" | "muted" | "info";
  summary: string;
  issueCount: number;
  available: boolean;
};

function toneClass(tone: ProductComponentListItem["statusTone"]): string {
  if (tone === "ok") return "border-emerald-500/30 bg-emerald-500/10 text-emerald-200";
  if (tone === "blocker") return "border-rose-500/30 bg-rose-500/10 text-rose-200";
  if (tone === "pending") return "border-amber-500/30 bg-amber-500/10 text-amber-200";
  if (tone === "info") return "border-sky-500/30 bg-sky-500/10 text-sky-200";
  return "border-slate-600/40 bg-slate-800/40 text-slate-400";
}

export function buildProductComponentListItems(args: {
  payload: Record<string, unknown> | null | undefined;
  finishSetup: unknown;
  hasLetters: boolean;
  hasLogo: boolean;
  acmModel?: AcmPanelUiReadModel;
}): ProductComponentListItem[] {
  const acm =
    args.acmModel ??
    buildAcmPanelUiReadModel({
      finishSetup: args.finishSetup,
      payload: args.payload ?? null,
    });

  const items: ProductComponentListItem[] = [];
  if (args.hasLetters) {
    items.push({
      id: "letters",
      title: "Litere volumetrice",
      typeLabel: "Componentă produs",
      statusLabel: "Configurare finisaje",
      statusTone: "info",
      summary: "Față · Cant · Spate",
      issueCount: 0,
      available: true,
    });
  }
  if (args.hasLogo) {
    items.push({
      id: "logo",
      title: "Vector Logo",
      typeLabel: "Componentă produs",
      statusLabel: "Configurare finisaje",
      statusTone: "info",
      summary: "Emblemă / artwork",
      issueCount: 0,
      available: true,
    });
  }
  if (acm.exists) {
    items.push({
      id: "acm_panel",
      title: acm.label,
      typeLabel: "Componentă produs",
      statusLabel: acm.primaryStatus.label,
      statusTone: acm.primaryStatus.tone,
      summary: [acm.dimensionsSummary, acm.segmentCount > 1 ? `${acm.segmentCount} segmente` : null]
        .filter(Boolean)
        .join(" · "),
      issueCount: acm.issues.filter((i) => i.severity !== "observation").length,
      available: true,
    });
  }
  return items;
}

export default function IntakeV6ProductComponentList({
  items,
  selectedId,
  onSelect,
}: {
  items: ProductComponentListItem[];
  selectedId: IntakeV6ProductComponentId | null;
  onSelect: (id: IntakeV6ProductComponentId) => void;
}) {
  if (!items.length) return null;

  return (
    <section
      className="rounded-md border border-wo-border-strong/70 bg-wo-surface-raised/45 p-2"
      data-testid="intake-v6-product-component-list"
    >
      <p className="mb-1.5 px-1 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
        Componente produs
      </p>
      <ul className="flex flex-col gap-1">
        {items.map((item) => {
          const selected = selectedId === item.id;
          return (
            <li key={item.id}>
              <button
                type="button"
                disabled={!item.available}
                onClick={() => onSelect(item.id)}
                data-testid={`intake-v6-product-component-row-${item.id}`}
                data-selected={selected ? "true" : "false"}
                className={`flex w-full items-start gap-2 rounded border px-2.5 py-2 text-left transition ${
                  selected
                    ? "border-blue-500/55 bg-blue-50 dark:bg-blue-950/40"
                    : "border-wo-border-strong/50 bg-wo-surface-inset/40 hover:border-blue-500/30"
                }`}
              >
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-1.5">
                    <span className="text-[12px] font-semibold text-wo-text-primary">{item.title}</span>
                    {intakeV6ShowOperatorConfigStatusBadges() ? (
                      <span
                        className={`rounded border px-1.5 py-0.5 text-[10px] font-semibold ${toneClass(item.statusTone)}`}
                      >
                        {item.statusLabel}
                      </span>
                    ) : null}
                    {item.issueCount > 0 ? (
                      <span className="text-[10px] text-amber-200">{item.issueCount} probleme</span>
                    ) : null}
                  </div>
                  <p className="mt-0.5 text-[10px] text-slate-500">{item.typeLabel}</p>
                  {item.summary ? (
                    <p className="mt-0.5 truncate text-[11px] text-slate-400">{item.summary}</p>
                  ) : null}
                </div>
              </button>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

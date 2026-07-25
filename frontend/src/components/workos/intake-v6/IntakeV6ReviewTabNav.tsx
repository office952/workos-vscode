import {
  resolveIntakeV6ReviewTabs,
  type IntakeV6ReviewTabDefinition,
  type IntakeV6ReviewTabId,
} from "@/lib/intakeV6/intakeV6ProductPlugin";
import {
  expandReviewTabsToDomains,
  type IntakeV6ReviewDomainDefinition,
  type IntakeV6ReviewDomainId,
} from "@/lib/intakeV6/intakeV6ReviewDomainNav";

export type { IntakeV6ReviewTabId, IntakeV6ReviewDomainId };

function joinClassNames(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(" ");
}

export default function IntakeV6ReviewTabNav({
  active,
  onChange,
  templateCode,
  pendingFinisaje = 0,
  tabs: tabsOverride = null,
  domains: domainsOverride = null,
  compositionAuthority = false,
  orientation = "horizontal",
}: {
  /** Active workbench domain (or legacy tab id when horizontal). */
  active: IntakeV6ReviewDomainId | IntakeV6ReviewTabId;
  onChange: (domain: IntakeV6ReviewDomainId) => void;
  /** Workspace template code — drives product plugin review tabs (fallback). */
  templateCode?: string | null;
  pendingFinisaje?: number;
  /** Build 2: tabs composed from modular form contract when present. */
  tabs?: IntakeV6ReviewTabDefinition[] | null;
  /** Pre-expanded domains; when null, derived from tabs. */
  domains?: IntakeV6ReviewDomainDefinition[] | null;
  compositionAuthority?: boolean;
  orientation?: "horizontal" | "vertical";
  /** @deprecated LED state is shown in tab content; ON pill removed (badge noise reduction). */
  illuminated?: boolean;
}) {
  const baseTabs = tabsOverride?.length ? tabsOverride : resolveIntakeV6ReviewTabs(templateCode);
  const domains = domainsOverride?.length
    ? domainsOverride
    : expandReviewTabsToDomains(baseTabs);
  const vertical = orientation === "vertical";

  return (
    <div
      className={
        vertical
          ? "flex flex-col gap-0.5 p-1.5"
          : "flex w-full flex-nowrap gap-0.5 overflow-x-auto p-1"
      }
      role="tablist"
      aria-label="Secțiuni formular"
      aria-orientation={vertical ? "vertical" : "horizontal"}
      data-testid="intake-v6-review-tabs"
      data-orientation={orientation}
      data-composition-authority={compositionAuthority ? "contract" : "plugin-fallback"}
      data-tabs-own-form="true"
    >
      {domains.map((tab) => {
        const selected = active === tab.id;
        const TabIcon = tab.icon;
        return (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={selected}
            title={tab.hint}
            className={joinClassNames(
              vertical
                ? "relative flex w-full flex-col rounded-md border px-2 py-1.5 text-left transition"
                : "relative flex min-w-[5.5rem] flex-1 flex-col items-center rounded-md border px-2 py-1 text-center transition",
              selected
                ? vertical
                  ? "border-cyan-500/35 bg-cyan-500/10 text-slate-100"
                  : "border-cyan-500/35 bg-cyan-500/10 text-slate-100"
                : "border-transparent text-slate-500 hover:bg-[#111827]/50 hover:text-slate-300",
            )}
            onClick={() => onChange(tab.id)}
            data-testid={`intake-v6-review-tab-${tab.id}`}
          >
            <span
              className={joinClassNames(
                "inline-flex items-center gap-1.5 font-semibold",
                vertical ? "text-[12px]" : "justify-center text-[11px]",
              )}
            >
              <TabIcon className="h-3 w-3 shrink-0 opacity-80" aria-hidden />
              {tab.label}
              {tab.id === "finisaje" && pendingFinisaje > 0 ? (
                <span
                  className="inline-flex h-4 min-w-4 items-center justify-center rounded-full bg-amber-500/20 px-1 text-[11px] font-bold text-amber-200"
                  data-testid="intake-v6-review-tab-finisaje-pending"
                >
                  {pendingFinisaje}
                </span>
              ) : null}
            </span>
            {vertical ? (
              <span className="mt-0.5 truncate text-[10px] font-normal text-slate-500">
                {tab.hint}
              </span>
            ) : (
              <span className="mt-0.5 hidden max-w-full truncate text-[9px] font-normal text-slate-500 sm:block">
                {tab.hint}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}

import {
  resolveIntakeV6ReviewTabs,
  type IntakeV6ReviewTabDefinition,
  type IntakeV6ReviewTabId,
} from "@/lib/intakeV6/intakeV6ProductPlugin";

export type { IntakeV6ReviewTabId };

function joinClassNames(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(" ");
}

export default function IntakeV6ReviewTabNav({
  active,
  onChange,
  templateCode,
  pendingFinisaje = 0,
  tabs: tabsOverride = null,
  compositionAuthority = false,
}: {
  active: IntakeV6ReviewTabId;
  onChange: (tab: IntakeV6ReviewTabId) => void;
  /** Workspace template code — drives product plugin review tabs (fallback). */
  templateCode?: string | null;
  pendingFinisaje?: number;
  /** Build 2: tabs composed from modular form contract when present. */
  tabs?: IntakeV6ReviewTabDefinition[] | null;
  compositionAuthority?: boolean;
  /** @deprecated LED state is shown in tab content; ON pill removed (badge noise reduction). */
  illuminated?: boolean;
}) {
  const tabs = tabsOverride?.length ? tabsOverride : resolveIntakeV6ReviewTabs(templateCode);

  return (
    <div
      className="mb-0 flex flex-wrap gap-0.5 pb-0"
      role="tablist"
      aria-label="Secțiuni formular"
      data-testid="intake-v6-review-tabs"
      data-composition-authority={compositionAuthority ? "contract" : "plugin-fallback"}
      data-tabs-own-form="true"
    >
      {tabs.map((tab) => {
        const selected = active === tab.id;
        const TabIcon = tab.icon;
        return (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={selected}
            className={joinClassNames(
              "relative -mb-px flex min-w-[4.75rem] flex-col rounded-t-md border px-2.5 py-1.5 text-left transition",
              selected
                ? "border-[#2A3548]/90 border-b-[#0B1220] bg-[#0B1220] text-slate-100"
                : "border-transparent text-slate-500 hover:bg-[#111827]/50 hover:text-slate-300",
            )}
            onClick={() => onChange(tab.id)}
            data-testid={`intake-v6-review-tab-${tab.id}`}
          >
            <span className="inline-flex items-center gap-1.5 text-[12px] font-semibold">
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
            <span className="mt-0.5 truncate text-[10px] font-normal text-slate-500">{tab.hint}</span>
          </button>
        );
      })}
    </div>
  );
}

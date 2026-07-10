import {
  resolveIntakeV6ReviewTabs,
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
}: {
  active: IntakeV6ReviewTabId;
  onChange: (tab: IntakeV6ReviewTabId) => void;
  /** Workspace template code — drives product plugin review tabs. */
  templateCode?: string | null;
  pendingFinisaje?: number;
  /** @deprecated LED state is shown in tab content; ON pill removed (badge noise reduction). */
  illuminated?: boolean;
}) {
  const tabs = resolveIntakeV6ReviewTabs(templateCode);

  return (
    <div
      className="mb-3 flex flex-wrap gap-1 border-b border-[#2A3548]/80 pb-0"
      role="tablist"
      aria-label="Secțiuni review"
      data-testid="intake-v6-review-tabs"
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
              "relative -mb-px flex min-w-[5.5rem] flex-col rounded-t-md border px-2.5 py-1.5 text-left transition",
              selected
                ? "border-[#2A3548] border-b-[#111827] bg-[#111827] text-slate-100"
                : "border-transparent text-slate-500 hover:text-slate-300",
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
            <span className="mt-0.5 truncate text-[11px] font-normal text-slate-500">{tab.hint}</span>
          </button>
        );
      })}
    </div>
  );
}

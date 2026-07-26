import { useMemo, useState } from "react";
import { Search, Package, Clock, History, Star } from "lucide-react";
import type { ProductTemplateEntity } from "@/lib/api";
import {
  filterActiveTemplatesForQuote,
  filterArchivedExperimentalTemplates,
  isActiveTemplateForQuote,
} from "@/lib/activeTemplateScope";
import {
  getMostUsedTemplateIds,
  getRecentTemplateIds,
} from "@/features/product-system/templateSelectionStorage";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";

type PickerTab = "active" | "archived" | "recent" | "most_used" | "latest";

function formatDate(value: string | undefined): string | null {
  if (!value) return null;
  try {
    return new Date(value).toLocaleDateString("ro-RO");
  } catch {
    return null;
  }
}

function TemplatePickerRow({
  template,
  selected,
  onSelect,
}: {
  template: ProductTemplateEntity;
  selected: boolean;
  onSelect: () => void;
}) {
  const quoteActive = isActiveTemplateForQuote(template);
  const created = formatDate(template.created_at);
  const updated = formatDate(template.updated_at);

  return (
    <button
      type="button"
      onClick={onSelect}
      className={`w-full text-left rounded-xl border px-3 py-2.5 transition-all ${
        selected
          ? "border-purple-500/50 bg-purple-900/15 ring-1 ring-purple-500/30"
          : "border-wo-border-subtle bg-wo-surface-raised hover:border-slate-500 hover:bg-wo-surface-raised"
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-[12px] font-mono font-bold text-purple-300 truncate">
            {template.template_code}
          </p>
          <p className="text-[11px] text-wo-text-secondary truncate mt-0.5">
            {template.family_name || "—"}
          </p>
        </div>
        <span
          className={`shrink-0 px-2 py-0.5 text-[8px] font-bold uppercase rounded-full border ${
            quoteActive
              ? "bg-emerald-900/30 text-emerald-400 border-emerald-700/40"
              : "bg-slate-800/60 text-wo-text-muted border-slate-600/40"
          }`}
        >
          {quoteActive ? "Activ" : "Arhivat"}
        </span>
      </div>
      {(created || updated) && (
        <p className="text-[9px] text-wo-text-dim mt-1.5">
          {created ? `Creat: ${created}` : null}
          {created && updated ? " · " : null}
          {updated ? `Actualizat: ${updated}` : null}
        </p>
      )}
    </button>
  );
}

export function TemplateSelectorSheet({
  open,
  onOpenChange,
  templates,
  selectedId,
  onSelect,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  templates: ProductTemplateEntity[];
  selectedId: number | null;
  onSelect: (template: ProductTemplateEntity) => void;
}) {
  const [tab, setTab] = useState<PickerTab>("active");
  const [search, setSearch] = useState("");

  const activeTemplates = useMemo(
    () => filterActiveTemplatesForQuote(templates),
    [templates]
  );
  const archivedTemplates = useMemo(
    () => filterArchivedExperimentalTemplates(templates),
    [templates]
  );

  const tabTemplates = useMemo(() => {
    const byId = new Map(templates.map((t) => [t.id, t]));
    switch (tab) {
      case "active":
        return activeTemplates;
      case "archived":
        return archivedTemplates;
      case "recent":
        return getRecentTemplateIds()
          .map((id) => byId.get(id))
          .filter((t): t is ProductTemplateEntity => t != null);
      case "most_used":
        return getMostUsedTemplateIds()
          .map((id) => byId.get(id))
          .filter((t): t is ProductTemplateEntity => t != null);
      case "latest":
        return [...templates].sort((a, b) => {
          const ta = a.created_at ? Date.parse(a.created_at) : 0;
          const tb = b.created_at ? Date.parse(b.created_at) : 0;
          return tb - ta;
        });
      default:
        return templates;
    }
  }, [tab, templates, activeTemplates, archivedTemplates]);

  const filtered = useMemo(() => {
    if (!search.trim()) return tabTemplates;
    const q = search.toLowerCase();
    return tabTemplates.filter(
      (t) =>
        t.template_code.toLowerCase().includes(q) ||
        (t.family_name || "").toLowerCase().includes(q) ||
        (t.description || "").toLowerCase().includes(q)
    );
  }, [tabTemplates, search]);

  const tabs: { id: PickerTab; label: string; count: number; hint?: string }[] = [
    { id: "active", label: "Active", count: activeTemplates.length },
    { id: "archived", label: "Arhivate", count: archivedTemplates.length },
    { id: "recent", label: "Recente", count: getRecentTemplateIds().length },
    {
      id: "most_used",
      label: "Deschise des",
      count: getMostUsedTemplateIds().length,
      hint: "local",
    },
    { id: "latest", label: "Ultimele create", count: templates.length },
  ];

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="left"
        className="w-full sm:max-w-md bg-wo-surface-inset border-wo-border-subtle text-wo-text-primary p-0 flex flex-col"
      >
        <SheetHeader className="px-4 pt-5 pb-3 border-b border-wo-border-subtle text-left space-y-1">
          <SheetTitle className="text-wo-text-primary text-[15px]">Alege șablon</SheetTitle>
          <SheetDescription className="text-[11px] text-wo-text-muted">
            Caută după cod, familie sau descriere. {templates.length} șabloane în registru.
          </SheetDescription>
        </SheetHeader>

        <div className="px-4 py-3 border-b border-wo-border-subtle space-y-3">
          <div className="flex items-center gap-2 bg-wo-surface-raised border border-wo-border-subtle rounded-lg px-3 py-2 focus-within:border-purple-500/50">
            <Search className="w-4 h-4 text-wo-text-muted shrink-0" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Caută template_code, familie…"
              className="bg-transparent text-[13px] text-wo-text-primary placeholder:text-wo-text-dim outline-none w-full"
            />
          </div>

          <div className="flex flex-wrap gap-1">
            {tabs.map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => setTab(t.id)}
                className={`px-2 py-1 rounded-md text-[10px] font-bold border transition-colors ${
                  tab === t.id
                    ? "bg-purple-600/25 text-purple-200 border-purple-500/40"
                    : "bg-slate-800/40 text-wo-text-muted border-slate-700 hover:text-wo-text-secondary"
                }`}
              >
                {t.label} ({t.count})
                {t.hint ? (
                  <span className="ml-1 text-[8px] text-wo-text-dim uppercase">{t.hint}</span>
                ) : null}
              </button>
            ))}
          </div>

          {tab === "most_used" ? (
            <p className="text-[9px] text-wo-text-dim flex items-center gap-1">
              <Star className="w-3 h-3" />
              Bazat pe deschideri locale în browser — nu metrici backend.
            </p>
          ) : null}
          {tab === "recent" ? (
            <p className="text-[9px] text-wo-text-dim flex items-center gap-1">
              <History className="w-3 h-3" />
              Șabloane deschise recent în această sesiune / browser.
            </p>
          ) : null}
          {tab === "latest" ? (
            <p className="text-[9px] text-wo-text-dim flex items-center gap-1">
              <Clock className="w-3 h-3" />
              Sortate după data creării din registru.
            </p>
          ) : null}
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-3 space-y-2 scrollbar-thin">
          {filtered.length === 0 ? (
            <div className="text-center py-10">
              <Package className="w-8 h-8 text-wo-text-dim mx-auto mb-2" />
              <p className="text-[12px] text-wo-text-muted">
                {search.trim() ? "Niciun șablon pentru căutarea curentă." : "Niciun șablon în această listă."}
              </p>
            </div>
          ) : (
            filtered.map((t) => (
              <TemplatePickerRow
                key={t.id}
                template={t}
                selected={selectedId === t.id}
                onSelect={() => {
                  onSelect(t);
                  onOpenChange(false);
                }}
              />
            ))
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}

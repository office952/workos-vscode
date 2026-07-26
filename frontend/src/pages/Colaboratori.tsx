import { useState } from "react";
import { useColaboratoriData } from "@/hooks/useColaboratoriData";
import { BoundaryBadge } from "@/components/workos/design-system";
import { suppliersApi } from "@/lib/api";
import {
  type ExternalCollaborator,
  type CollabCategory,
  type CollabStatus,
} from "@/lib/mockData";
import {
  Handshake,
  Search,
  ChevronRight,
  Star,
  Phone,
  Mail,
  MapPin,
  Package,
  Wrench,
  Clock,
  TrendingUp,
  FileText,
  Building2,
  Database,
  Loader2,
  Plus,
  X,
  AlertTriangle,
} from "lucide-react";

type CollaboratorFormState = {
  code: string;
  name: string;
  category: string;
  leadTimeDays: string;
  rating: string;
};

const COLLABORATOR_CATEGORY_OPTIONS = [
  { value: "serviciu", label: "Serviciu" },
  { value: "produs", label: "Produs" },
  { value: "echipamente", label: "Echipamente" },
  { value: "consumabile", label: "Consumabile" },
];

function buildCollaboratorCode() {
  return `SUP-${Date.now().toString(36).toUpperCase()}`;
}

const categoryConfig: Record<CollabCategory, { label: string; cls: string; icon: React.ReactNode }> = {
  produs: { label: "Produs", cls: "bg-indigo-900/40 text-indigo-300 border-indigo-700", icon: <Package className="w-3 h-3" /> },
  serviciu: { label: "Serviciu", cls: "bg-teal-50 dark:bg-teal-900/40 text-teal-700 dark:text-teal-300 border-teal-200 dark:border-teal-700", icon: <Wrench className="w-3 h-3" /> },
};

const statusConfig: Record<CollabStatus, { label: string; cls: string }> = {
  activ: { label: "Activ", cls: "text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/30 border-emerald-700" },
  inactiv: { label: "Inactiv", cls: "text-muted-foreground bg-muted/60 border-slate-600" },
  preferat: { label: "★ Preferat", cls: "text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-900/30 border-amber-700" },
};

function CategoryBadge({ category }: { category: CollabCategory }) {
  const cfg = categoryConfig[category];
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 text-[11px] font-semibold rounded border ${cfg.cls}`}>
      {cfg.icon}
      {cfg.label}
    </span>
  );
}

function StatusBadge({ status }: { status: CollabStatus }) {
  const cfg = statusConfig[status];
  return (
    <span className={`inline-flex items-center px-2 py-0.5 text-[10px] font-semibold rounded border ${cfg.cls}`}>
      {cfg.label}
    </span>
  );
}

function StarRating({ rating }: { rating: number }) {
  return (
    <div className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((i) => (
        <Star
          key={i}
          className={`w-3 h-3 ${i <= rating ? "text-amber-500 dark:text-amber-400 fill-amber-500 dark:fill-amber-400" : "text-wo-text-dim"}`}
        />
      ))}
    </div>
  );
}

function DataSourceBadge({ source }: { source: "db" | "mock" | "empty" | "error" | "loading" }) {
  if (source === "loading") return null;
  const isLive = source === "db";
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-semibold rounded-full border ${
        isLive
          ? "bg-emerald-50 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-700"
          : "bg-amber-50 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-700"
      }`}
    >
      <Database className="w-3 h-3" />
      {isLive ? "Live DB" : source === "mock" ? "Mock Data" : "No Data"}
    </span>
  );
}

export default function Colaboratori() {
  const { collaborators, loading, error, source, refresh } = useColaboratoriData();
  const [searchQuery, setSearchQuery] = useState("");
  const [filterCategory, setFilterCategory] = useState<CollabCategory | "all">("all");
  const [filterStatus, setFilterStatus] = useState<CollabStatus | "all">("all");
  const [selected, setSelected] = useState<ExternalCollaborator | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState<CollaboratorFormState>({
    code: buildCollaboratorCode(),
    name: "",
    category: "serviciu",
    leadTimeDays: "7",
    rating: "3",
  });
  const canCreateCollaborator = source === "db" || source === "empty";

  const prodCount = collaborators.filter((c) => c.category === "produs").length;
  const servCount = collaborators.filter((c) => c.category === "serviciu").length;
  const preferatCount = collaborators.filter((c) => c.status === "preferat").length;

  const filtered = collaborators.filter((c) => {
    if (filterCategory !== "all" && c.category !== filterCategory) return false;
    if (filterStatus !== "all" && c.status !== filterStatus) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        c.companyName.toLowerCase().includes(q) ||
        c.specializations.some((s) => s.toLowerCase().includes(q)) ||
        c.city.toLowerCase().includes(q)
      );
    }
    return true;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-6 h-6 text-teal-600 dark:text-teal-400 animate-spin" />
        <span className="ml-2 text-muted-foreground text-sm">Se încarcă colaboratorii...</span>
      </div>
    );
  }

  const resetCreateState = () => {
    setCreateOpen(false);
    setCreateError(null);
    setSubmitting(false);
    setForm({
      code: buildCollaboratorCode(),
      name: "",
      category: "serviciu",
      leadTimeDays: "7",
      rating: "3",
    });
  };

  const handleCreateCollaborator = async () => {
    if (!form.name.trim()) {
      setCreateError("Numele colaboratorului este obligatoriu.");
      return;
    }

    setSubmitting(true);
    setCreateError(null);
    try {
      await suppliersApi.create({
        code: form.code.trim(),
        name: form.name.trim(),
        category: form.category,
        lead_time_days: Number(form.leadTimeDays) || 0,
        rating: Number(form.rating) || 0,
        active_orders: 0,
        last_delivery: undefined,
      });
      await refresh();
      resetCreateState();
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : "Eroare la crearea colaboratorului.");
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Boundary notice — HUB extern */}
      <BoundaryBadge
        domain="collaborators"
        detail="Nu este HR/Pontaj, nu este Pricing Registry, nu conduce oferta client."
      />

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Handshake className="w-5 h-5 text-teal-600 dark:text-teal-400" />
          <h1 className="text-[18px] font-bold text-foreground">Colaboratori Externi</h1>
          <span className="text-[10px] text-muted-foreground bg-muted px-2 py-0.5 rounded-full ml-1">
            {collaborators.length} parteneri
          </span>
          <DataSourceBadge source={source} />
        </div>
        <button
          onClick={() => setCreateOpen(true)}
          disabled={!canCreateCollaborator}
          className="flex items-center gap-1.5 px-3 py-2 bg-teal-600 hover:bg-teal-500 disabled:bg-slate-700 disabled:text-muted-foreground disabled:cursor-not-allowed text-white rounded-lg text-[12px] font-bold transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          Adaugă colaborator
        </button>
      </div>

      {error && source !== "mock" && (
        <div className="flex items-start gap-2 px-3 py-2 bg-red-900/20 border border-red-800/40 rounded-lg">
          <AlertTriangle className="w-4 h-4 text-red-600 dark:text-red-400 mt-0.5 shrink-0" />
          <p className="text-[12px] text-red-600 dark:text-red-300">
            Lista colaboratorilor nu a putut fi încărcată din backend: {error}
          </p>
        </div>
      )}

      {!canCreateCollaborator && (
        <div className="flex items-start gap-2 px-3 py-2 bg-amber-900/15 border border-amber-800/30 rounded-lg">
          <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 mt-0.5 shrink-0" />
          <p className="text-[11px] text-amber-700 dark:text-amber-300/90">
            Crearea colaboratorilor este disponibilă doar pe sursa backend live.
          </p>
        </div>
      )}

      {createOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-wo-surface-inset border border-wo-border-strong rounded-xl shadow-2xl w-full max-w-xl overflow-hidden">
            <div className="flex items-center justify-between px-5 py-3 border-b border-wo-border-strong">
              <div className="flex items-center gap-2">
                <Plus className="w-4 h-4 text-teal-600 dark:text-teal-400" />
                <h2 className="text-[14px] font-bold text-foreground">Colaborator Nou</h2>
              </div>
              <button onClick={resetCreateState} className="text-muted-foreground hover:text-foreground transition-colors" aria-label="Închide">
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="p-5 space-y-4">
              <p className="text-[12px] text-muted-foreground">
                Creează un colaborator extern real în backend-ul suppliers. Formularul expune doar câmpurile susținute de contractul backend curent.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <label className="space-y-1">
                  <span className="text-[11px] text-muted-foreground">Cod</span>
                  <input
                    value={form.code}
                    onChange={(e) => setForm((prev) => ({ ...prev, code: e.target.value }))}
                    className="w-full bg-card border border-border rounded-lg px-3 py-2 text-[12px] text-foreground outline-none focus:border-blue-500/50"
                  />
                </label>
                <label className="space-y-1">
                  <span className="text-[11px] text-muted-foreground">Categorie</span>
                  <select
                    value={form.category}
                    onChange={(e) => setForm((prev) => ({ ...prev, category: e.target.value }))}
                    className="w-full bg-card border border-border rounded-lg px-3 py-2 text-[12px] text-foreground outline-none focus:border-blue-500/50"
                  >
                    {COLLABORATOR_CATEGORY_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </select>
                </label>
              </div>

              <label className="space-y-1 block">
                <span className="text-[11px] text-muted-foreground">Nume colaborator</span>
                <input
                  value={form.name}
                  onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
                  placeholder="Ex: Atelier Montaj Sud"
                  className="w-full bg-card border border-border rounded-lg px-3 py-2 text-[12px] text-foreground outline-none focus:border-blue-500/50"
                />
              </label>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <label className="space-y-1">
                  <span className="text-[11px] text-muted-foreground">Lead time (zile)</span>
                  <input
                    type="number"
                    min="0"
                    value={form.leadTimeDays}
                    onChange={(e) => setForm((prev) => ({ ...prev, leadTimeDays: e.target.value }))}
                    className="w-full bg-card border border-border rounded-lg px-3 py-2 text-[12px] text-foreground outline-none focus:border-blue-500/50"
                  />
                </label>
                <label className="space-y-1">
                  <span className="text-[11px] text-muted-foreground">Rating</span>
                  <input
                    type="number"
                    min="0"
                    max="5"
                    value={form.rating}
                    onChange={(e) => setForm((prev) => ({ ...prev, rating: e.target.value }))}
                    className="w-full bg-card border border-border rounded-lg px-3 py-2 text-[12px] text-foreground outline-none focus:border-blue-500/50"
                  />
                </label>
              </div>

              {createError && (
                <div className="flex items-start gap-2 px-3 py-2 bg-red-900/20 border border-red-800/40 rounded-lg">
                  <AlertTriangle className="w-4 h-4 text-red-600 dark:text-red-400 mt-0.5 shrink-0" />
                  <p className="text-[12px] text-red-600 dark:text-red-300">{createError}</p>
                </div>
              )}
            </div>
            <div className="flex items-center justify-end gap-2 px-5 py-3 border-t border-wo-border-strong bg-background">
              <button onClick={resetCreateState} className="px-3 py-2 text-[12px] font-semibold text-muted-foreground hover:text-foreground transition-colors">
                Anulează
              </button>
              <button
                onClick={handleCreateCollaborator}
                disabled={submitting || !form.name.trim()}
                className="px-3 py-2 bg-teal-600 hover:bg-teal-500 disabled:bg-slate-700 disabled:text-muted-foreground disabled:cursor-not-allowed text-white rounded-lg text-[12px] font-bold transition-colors"
              >
                {submitting ? "Se creează..." : "Creează colaborator"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div
          onClick={() => setFilterCategory(filterCategory === "produs" ? "all" : "produs")}
          className={`bg-wo-surface-raised border rounded-lg p-3 cursor-pointer transition-all ${
            filterCategory === "produs" ? "border-indigo-500/50 ring-1 ring-indigo-500/30" : "border-wo-border-strong hover:border-slate-500"
          }`}
        >
          <div className="flex items-center gap-2 mb-1">
            <Package className="w-3.5 h-3.5 text-indigo-400" />
            <span className="text-[12px] font-semibold text-foreground">Produse</span>
          </div>
          <p className="text-[24px] font-bold text-foreground">{prodCount}</p>
          <p className="text-[10px] text-muted-foreground">Firme care confecționează</p>
        </div>
        <div
          onClick={() => setFilterCategory(filterCategory === "serviciu" ? "all" : "serviciu")}
          className={`bg-wo-surface-raised border rounded-lg p-3 cursor-pointer transition-all ${
            filterCategory === "serviciu" ? "border-teal-500/50 ring-1 ring-teal-500/30" : "border-wo-border-strong hover:border-slate-500"
          }`}
        >
          <div className="flex items-center gap-2 mb-1">
            <Wrench className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" />
            <span className="text-[12px] font-semibold text-foreground">Servicii</span>
          </div>
          <p className="text-[24px] font-bold text-foreground">{servCount}</p>
          <p className="text-[10px] text-muted-foreground">Firme care prestează</p>
        </div>
        <div
          onClick={() => setFilterStatus(filterStatus === "preferat" ? "all" : "preferat")}
          className={`bg-wo-surface-raised border rounded-lg p-3 cursor-pointer transition-all ${
            filterStatus === "preferat" ? "border-amber-500/50 ring-1 ring-amber-500/30" : "border-wo-border-strong hover:border-slate-500"
          }`}
        >
          <div className="flex items-center gap-2 mb-1">
            <Star className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />
            <span className="text-[12px] font-semibold text-foreground">Preferați</span>
          </div>
          <p className="text-[24px] font-bold text-foreground">{preferatCount}</p>
          <p className="text-[10px] text-muted-foreground">Parteneri de încredere</p>
        </div>
        <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-3">
          <div className="flex items-center gap-2 mb-1">
            <TrendingUp className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
            <span className="text-[12px] font-semibold text-foreground">Valoare Totală</span>
          </div>
          <p className="text-[24px] font-bold text-foreground">
            {Math.round(collaborators.reduce((sum, c) => sum + c.totalValueRON, 0) / 1000)}k
          </p>
          <p className="text-[10px] text-muted-foreground">RON externalizat</p>
        </div>
      </div>

      {/* Search + Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-2 bg-card border border-border rounded-lg px-3 py-2 flex-1 max-w-md focus-within:border-blue-500/50">
          <Search className="w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Caută firmă, specializare, oraș..."
            className="bg-transparent text-[13px] text-foreground placeholder:text-wo-text-dim outline-none w-full"
          />
        </div>
        {(filterCategory !== "all" || filterStatus !== "all") && (
          <button
            onClick={() => { setFilterCategory("all"); setFilterStatus("all"); }}
            className="text-[11px] text-muted-foreground hover:text-foreground transition-colors"
          >
            Resetează filtre
          </button>
        )}
        <span className="text-[11px] text-muted-foreground ml-auto">{filtered.length} rezultate</span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* List */}
        <div className="lg:col-span-2 space-y-2">
          {filtered.map((col) => (
            <div
              key={col.id}
              onClick={() => setSelected(col)}
              className={`bg-card border rounded-lg p-3 cursor-pointer transition-all ${
                selected?.id === col.id ? "border-blue-500/50 ring-1 ring-blue-500/30" : "border-border hover:border-slate-500"
              }`}
            >
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${
                  col.category === "produs" ? "bg-indigo-900/40" : "bg-teal-900/40"
                }`}>
                  {col.category === "produs"
                    ? <Package className="w-4 h-4 text-indigo-400" />
                    : <Wrench className="w-4 h-4 text-teal-600 dark:text-teal-400" />
                  }
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-[13px] font-semibold text-foreground">{col.companyName}</span>
                    <CategoryBadge category={col.category} />
                    <StatusBadge status={col.status} />
                  </div>
                  <p className="text-[11px] text-muted-foreground truncate">{col.specializations.join(" • ")}</p>
                  <div className="flex items-center gap-3 mt-1 text-[10px] text-muted-foreground">
                    <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{col.city}</span>
                    <span>•</span>
                    <StarRating rating={col.qualityRating} />
                    <span>•</span>
                    <span>{col.totalOrdersCompleted} comenzi</span>
                    <span>•</span>
                    <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{col.avgDeliveryDays}z livrare</span>
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-wo-text-dim shrink-0" />
              </div>
            </div>
          ))}
          {filtered.length === 0 && (
            <div className="bg-card border border-border rounded-lg p-8 text-center text-muted-foreground text-[13px]">
              Niciun colaborator găsit.
            </div>
          )}
        </div>

        {/* Detail Panel */}
        <div className="space-y-4">
          {selected ? (
            <>
              <div className="bg-card border border-border rounded-lg p-4">
                <div className="flex items-center gap-3 mb-4">
                  <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                    selected.category === "produs" ? "bg-indigo-900/40" : "bg-teal-900/40"
                  }`}>
                    {selected.category === "produs"
                      ? <Package className="w-5 h-5 text-indigo-400" />
                      : <Wrench className="w-5 h-5 text-teal-600 dark:text-teal-400" />
                    }
                  </div>
                  <div>
                    <h3 className="text-[16px] font-bold text-foreground">{selected.companyName}</h3>
                    <div className="flex items-center gap-2 mt-0.5">
                      <CategoryBadge category={selected.category} />
                      <StatusBadge status={selected.status} />
                    </div>
                  </div>
                </div>

                <div className="space-y-3">
                  <div>
                    <p className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1">Descriere</p>
                    <p className="text-[12px] text-muted-foreground leading-relaxed">{selected.description}</p>
                  </div>

                  <div>
                    <p className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1">Specializări</p>
                    <div className="flex flex-wrap gap-1">
                      {selected.specializations.map((s) => (
                        <span key={s} className={`px-2 py-0.5 text-[10px] rounded border ${
                          selected.category === "produs"
                            ? "bg-indigo-900/20 text-indigo-300 border-indigo-800"
                            : "bg-teal-900/20 text-teal-600 dark:text-teal-300 border-teal-800"
                        }`}>
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <p className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1 flex items-center gap-1">
                        <Building2 className="w-3 h-3" /> CUI
                      </p>
                      <p className="text-[12px] text-muted-foreground font-mono">{selected.cui}</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1 flex items-center gap-1">
                        <MapPin className="w-3 h-3" /> Oraș
                      </p>
                      <p className="text-[12px] text-muted-foreground">{selected.city}</p>
                    </div>
                  </div>

                  <div>
                    <p className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1">Contact</p>
                    <p className="text-[12px] text-muted-foreground">{selected.contactPerson}</p>
                    <div className="flex items-center gap-3 mt-1 text-[11px] text-muted-foreground">
                      <span className="flex items-center gap-1"><Phone className="w-3 h-3" />{selected.phone}</span>
                      <span className="flex items-center gap-1"><Mail className="w-3 h-3" />{selected.email}</span>
                    </div>
                  </div>

                  <div>
                    <p className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1">Rating Calitate</p>
                    <StarRating rating={selected.qualityRating} />
                  </div>

                  {selected.notes && (
                    <div className="bg-wo-surface-raised rounded-lg p-3">
                      <p className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1 flex items-center gap-1">
                        <FileText className="w-3 h-3" /> Note
                      </p>
                      <p className="text-[12px] text-muted-foreground">{selected.notes}</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Stats */}
              <div className="bg-card border border-border rounded-lg p-4">
                <div className="flex items-center gap-2 mb-3">
                  <TrendingUp className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                  <span className="text-[13px] font-bold text-foreground">Istoric Colaborare</span>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-wo-surface-raised rounded-lg p-2 text-center">
                    <p className="text-[18px] font-bold text-foreground">{selected.totalOrdersCompleted}</p>
                    <p className="text-[9px] text-muted-foreground uppercase">Comenzi</p>
                  </div>
                  <div className="bg-wo-surface-raised rounded-lg p-2 text-center">
                    <p className="text-[18px] font-bold text-foreground">{(selected.totalValueRON / 1000).toFixed(0)}k</p>
                    <p className="text-[9px] text-muted-foreground uppercase">RON Total</p>
                  </div>
                  <div className="bg-wo-surface-raised rounded-lg p-2 text-center">
                    <p className="text-[18px] font-bold text-foreground">{selected.avgDeliveryDays}z</p>
                    <p className="text-[9px] text-muted-foreground uppercase">Avg Livrare</p>
                  </div>
                  <div className="bg-wo-surface-raised rounded-lg p-2 text-center">
                    <p className="text-[14px] font-bold text-foreground">{new Date(selected.lastOrderDate).toLocaleDateString("ro-RO")}</p>
                    <p className="text-[9px] text-muted-foreground uppercase">Ultima Cmd</p>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="bg-card border border-border rounded-lg p-8 text-center">
              <Handshake className="w-8 h-8 text-wo-text-dim mx-auto mb-2" />
              <p className="text-[13px] text-muted-foreground">Selectează un colaborator pentru detalii</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}